"""The retrieval tool: a local BM25 keyword index over passages. No model needed.

build_index() chunks every raw source plus every wiki note listed in index.md and writes
data/chunks.jsonl. search() loads that file and ranks passages with Okapi BM25.
"""
import hashlib
import json
import math
import re
from collections import Counter

from . import config, llm
from .llm import ModelUnavailable
from .markdown import chunk_markdown, wiki_links

STOPWORDS = set("""a an and are as at be been but by can did do does for from had has have
how i if in into is it its me my of on or our so than that the their them then there these
they this to was we were what when where which who why will with you your yours about get got
""".split())

K1, B = 1.5, 0.75
HEADING_WEIGHT = 2   # words of the passage's own section heading count this many extra times
DIVERSITY_WINDOW = 2  # a source ranked within the top k*2 is guaranteed one of the k slots
RRF_K = 60           # reciprocal-rank-fusion constant


def tokenize(text):
    # "pac-man" -> pac, man ; "auth.user_id" -> auth, user, id ; drop "s"/"t" from "can't"
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words
            if w not in STOPWORDS and (len(w) > 1 or w.isdigit())]


def _stem(w):
    """Very light stemmer so 'contacts'/'contact' and 'policies'/'policy' match."""
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


# ---------- building ----------

def wiki_pages_from_index():
    """Wiki pages that index.md links to (the retrieval code's entry point to the wiki)."""
    if not config.INDEX_MD.exists():
        return []
    by_name = {p.stem: p for p in config.WIKI.rglob("*.md")}
    pages = []
    for target, _ in wiki_links(config.INDEX_MD.read_text()):
        p = by_name.get(target)
        if p and p not in pages:
            pages.append(p)
    return pages


def build_index(embed=True, log=print):
    """Chunk raw sources + indexed wiki pages; embed new passages if the embedder is available."""
    chunks = []
    for path in sorted(config.RAW.glob("*.md")) + sorted(config.RAW.glob("*.txt")):
        chunks += chunk_markdown(path.read_text(), str(path.relative_to(config.VAULT)), "raw",
                                 title=path.stem)
    for path in wiki_pages_from_index():
        chunks += chunk_markdown(path.read_text(), str(path.relative_to(config.VAULT)), "wiki",
                                 title=path.stem)
    config.DATA.mkdir(exist_ok=True)
    with open(config.CHUNKS, "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    if embed:
        try:
            n_new = _update_embeddings(chunks)
            log(f"  embeddings: {n_new} new passages embedded with {config.EMBED_MODEL}")
        except ModelUnavailable as e:
            log(f"  embeddings skipped ({e.args[0].splitlines()[0]}); search will use BM25 only")
    return chunks


def _text_key(c):
    return hashlib.sha1((c["heading_path"] + "\n" + c["text"]).encode()).hexdigest()


def _load_embeddings():
    if config.EMBEDDINGS.exists():
        data = json.loads(config.EMBEDDINGS.read_text())
        if data.get("model") == config.EMBED_MODEL:
            return data["vectors"]
    return {}


def _update_embeddings(chunks):
    """Embed only passages whose text is new (keyed by text hash), drop stale vectors."""
    old = _load_embeddings()
    keys = [_text_key(c) for c in chunks]
    todo = [(k, c) for k, c in zip(keys, chunks) if k not in old]
    for i in range(0, len(todo), 16):
        batch = todo[i:i + 16]
        docs = [f"title: {c['title']} | text: {c['heading_path']}\n{c['text']}" for _, c in batch]
        for (k, _), v in zip(batch, llm.embed(docs)):
            old[k] = [round(x, 5) for x in v]
    vectors = {k: old[k] for k in keys}
    config.EMBEDDINGS.write_text(json.dumps({"model": config.EMBED_MODEL, "vectors": vectors}))
    return len(todo)


# ---------- searching ----------

class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tfs, self.lens = [], []
        df = Counter()
        for c in chunks:
            toks = (tokenize(c["text"]) + tokenize(c["section"]) * HEADING_WEIGHT
                    + tokenize(c["title"]))
            tf = Counter(toks)
            self.tfs.append(tf)
            self.lens.append(len(toks))
            df.update(tf.keys())
        n = len(chunks) or 1
        self.avgdl = sum(self.lens) / n if chunks else 0
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        vectors = _load_embeddings()
        self.vectors = [vectors.get(_text_key(c)) for c in chunks]

    @classmethod
    def load(cls):
        if not config.CHUNKS.exists():
            raise FileNotFoundError(
                f"No retrieval index at {config.CHUNKS}. Run `wiki ingest vault/raw` "
                "(or `wiki reindex` to rebuild it from existing files without the model).")
        with open(config.CHUNKS) as f:
            return cls([json.loads(line) for line in f if line.strip()])

    def bm25(self, query, scope="all"):
        """[(chunk index, score, matched terms)] for every passage sharing a query term."""
        q = list(dict.fromkeys(tokenize(query)))    # unique query terms, in order
        out = []
        for i, c in enumerate(self.chunks):
            if scope != "all" and c["kind"] != scope:
                continue
            tf, dl, score, matched = self.tfs[i], self.lens[i], 0.0, []
            for t in q:
                f = tf.get(t)
                if not f:
                    continue
                matched.append(t)
                score += self.idf[t] * f * (K1 + 1) / (f + K1 * (1 - B + B * dl / self.avgdl))
            if score > 0:
                out.append((i, score, matched))
        return sorted(out, key=lambda r: -r[1])

    def dense(self, query, scope="all"):
        """[(chunk index, cosine)] using local embeddings; [] if unavailable."""
        if not any(self.vectors):
            return []
        try:
            qv = llm.embed([f"task: search result | query: {query}"])[0]
        except ModelUnavailable:
            return []
        out = []
        for i, (c, v) in enumerate(zip(self.chunks, self.vectors)):
            if v is None or (scope != "all" and c["kind"] != scope):
                continue
            out.append((i, sum(a * b for a, b in zip(qv, v))))   # vectors are unit length
        return sorted(out, key=lambda r: -r[1])

    def search(self, query, k=5, scope="all", method="hybrid"):
        """Rank passages. hybrid = reciprocal-rank fusion of BM25 and embedding ranks."""
        lex = self.bm25(query, scope)
        sem = self.dense(query, scope) if method in ("hybrid", "dense") else []
        used = "hybrid" if (method == "hybrid" and sem) else ("dense" if method == "dense" else "bm25")
        info = {}
        for rank, (i, s, m) in enumerate(lex, 1):
            info[i] = {"bm25": round(s, 3), "bm25_rank": rank, "matched_terms": m}
        for rank, (i, cos) in enumerate(sem, 1):
            info.setdefault(i, {"bm25": 0.0, "bm25_rank": None, "matched_terms": []})
            info[i].update(cosine=round(cos, 4), dense_rank=rank)
        def fused(d):
            if used == "bm25":
                return d["bm25"]
            if used == "dense":
                return d.get("cosine", -1)
            return sum(1 / (RRF_K + r) for r in (d["bm25_rank"], d.get("dense_rank")) if r)
        ranked = [{**self.chunks[i], **d, "score": round(fused(d), 4), "method": used}
                  for i, d in sorted(info.items(), key=lambda kv: -fused(kv[1]))]
        return _diversify(ranked, k)


def _diversify(ranked, k):
    """Top-k by score, but give any source that ranks within the top k*WINDOW one slot,
    replacing the lowest-ranked passage of the most-represented source. This lets a
    question that spans two projects see both, without capping single-source questions."""
    top = ranked[:k]
    for cand in ranked[k:k * DIVERSITY_WINDOW]:
        paths = Counter(h["path"] for h in top)
        if cand["path"] in paths:
            continue
        crowded = paths.most_common(1)[0][0]
        if paths[crowded] < 2:
            break
        drop = max(i for i, h in enumerate(top) if h["path"] == crowded)
        top = top[:drop] + top[drop + 1:] + [cand]
    return top


def fit_to_budget(hits, max_chars):
    """Keep the best-ranked passages whose combined text fits the model context budget."""
    kept, used = [], 0
    for h in hits:
        if used + len(h["text"]) > max_chars and kept:
            continue
        kept.append(h)
        used += len(h["text"])
    return kept
