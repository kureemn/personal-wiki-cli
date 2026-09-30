"""The harness: mode behavior, prompt assembly, model calls, citation checks, logging.

  ask   question -> retrieve raw passages -> research rules + passages -> Gemma -> check citations
  chat  message  -> router decides if notes are needed -> (retrieve) -> persona + history -> Gemma
  search is retrieval only (see cli.cmd_search); it never calls the language model.
"""
import re
import time

from . import config, llm, runlog
from .markdown import wiki_links
from .retrieval import Index, fit_to_budget

CITE_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
INSUFFICIENT = "INSUFFICIENT EVIDENCE"
ASK_MIN_COSINE = 0.30


def load_prompt(name):
    path = config.PROMPTS / name
    if not path.exists():
        raise FileNotFoundError(f"Missing instruction file: {path}")
    return path.read_text()


# ---------- shared helpers ----------

def format_passages(hits):
    """Numbered evidence block. Each passage keeps its file, lines and section."""
    blocks = []
    for n, h in enumerate(hits, 1):
        blocks.append(f"[{n}] source: {h['path']} (lines {h['line_start']}-{h['line_end']}, "
                      f"section: \"{h['section']}\")\n{h['text']}")
    return "\n\n".join(blocks)


def cited_numbers(text):
    out = []
    for m in CITE_RE.finditer(text):
        out += [int(x) for x in m.group(1).split(",")]
    return out


def check_citations(answer, hits):
    """Mechanical checks a reader would otherwise do by hand. They catch citations to
    passages that were never retrieved, factual sentences with no citation, and numbers
    that appear in none of the passages a sentence cites. They cannot prove meaning."""
    n = len(hits)
    cited = cited_numbers(answer)
    report = {
        "cited": sorted(set(cited)),
        "invalid_citations": sorted({c for c in cited if not 1 <= c <= n}),
        "uncited_sentences": [],
        "unsupported_numbers": [],
    }
    body = "\n".join(l for l in answer.splitlines()
                     if not l.strip().startswith(("NOT IN SOURCES", INSUFFICIENT)))
    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z*])|\n+", body):
        s = sent.strip(" -*")
        if len(s) < 25:
            continue
        refs = [c for c in cited_numbers(s) if 1 <= c <= n]
        if not refs:
            report["uncited_sentences"].append(s)
            continue
        evidence = " ".join(hits[c - 1]["text"] for c in refs).replace(",", "")
        for num in NUM_RE.findall(CITE_RE.sub("", s)):
            if num.replace(",", "") not in evidence:
                report["unsupported_numbers"].append(num)
    report["ok"] = not (report["invalid_citations"] or report["uncited_sentences"]
                        or report["unsupported_numbers"])
    return report


def reading_order(hits):
    """Present the selected passages grouped by source (best-ranked source first) and in
    document order within each source. Added after the final-code rerun of test 3, where the
    same evidence in a shuffled rank order made Gemma miss a value in a table (see README)."""
    first_rank = {}
    for rank, h in enumerate(hits):
        first_rank.setdefault(h["path"], rank)
    return sorted(hits, key=lambda h: (first_rank[h["path"]], h["line_start"]))


def passage_record(h):
    keep = ("id", "kind", "path", "section", "line_start", "line_end", "score", "bm25",
            "cosine", "method", "text")
    return {k: h.get(k) for k in keep}


# ---------- ask: standalone factual RAG ----------

CHECK_SCHEMA = {
    "type": "object",
    "properties": {"question_asks_for": {"type": "string"}, "answer_provides": {"type": "string"},
                   "verdict": {"type": "string",
                               "enum": ["answers it", "answers part of it", "does not answer it"]}},
    "required": ["question_asks_for", "answer_provides", "verdict"],
}


def answer_check(question, answer):
    """Second, passage-free Gemma call: does the draft supply what was asked, or a related
    fact of a different kind? (Added after dev run 1, where a grade question was answered
    with a score.)"""
    import json
    raw, stats = llm.chat(
        [{"role": "system", "content": load_prompt("answer-check.md")},
         {"role": "user", "content": f"QUESTION: {question}\n\nDRAFT ANSWER: {answer}"}],
        temperature=0.0, fmt=CHECK_SCHEMA)
    try:
        result = json.loads(raw)
    except ValueError:
        result = {"verdict": "unparsed", "raw": raw[:300]}
    result["seconds"] = stats["wall_seconds"]
    return result


def ask(question, *, k=None, on_token=None):
    """Answer one question from retrieved raw evidence. No chat history, no persona."""
    env = runlog.environment()
    started = time.time()
    index = Index.load()
    hits = index.search(question, k=k or config.ASK_TOP_K, scope="raw")
    hits = reading_order(fit_to_budget(hits, config.MAX_CONTEXT_CHARS))
    result = {**env, "question": question, "passages": [passage_record(h) for h in hits]}

    best_bm25 = max((h.get("bm25") or 0 for h in hits), default=0)
    best_cos = max((h.get("cosine") or 0 for h in hits), default=0)
    if not hits or (best_bm25 < config.ASK_MIN_SCORE and best_cos < ASK_MIN_COSINE):
        # Nothing remotely relevant: refuse without spending a model call.
        answer, stats = (f"{INSUFFICIENT}: no passage in the wiki matches this question "
                         f"(best BM25 {best_bm25:.1f}, best cosine {best_cos:.2f})."), None
    else:
        llm.check_model()
        messages = [
            {"role": "system", "content": load_prompt("wiki-instructions.md")},
            {"role": "user", "content":
                f"PASSAGES:\n\n{format_passages(hits)}\n\nQUESTION: {question}\n\n"
                "Answer using only the passages, citing them as [n]."},
        ]
        answer, stats = llm.chat(messages, temperature=0.0, on_token=on_token)
        result["prompt_chars"] = sum(len(m["content"]) for m in messages)
    answer = answer.strip()
    if stats and not answer.upper().startswith(INSUFFICIENT):
        check = answer_check(question, answer)
        result["answer_check"] = check
        if check.get("verdict") == "does not answer it":
            result["draft_answer"] = answer
            answer = (f"{INSUFFICIENT}: the retrieved passages do not state what the question "
                      "asks for. The draft answer offered related information of a different "
                      "kind instead, so it was withheld (see the answer check).")
    status = ("insufficient" if answer.upper().startswith(INSUFFICIENT) else
              "partial" if "NOT IN SOURCES" in answer
              or result.get("answer_check", {}).get("verdict") == "answers part of it"
              else "answered")
    checks = check_citations(answer, hits) if status != "insufficient" else {
        "cited": sorted(set(cited_numbers(answer))), "ok": True, "note": "insufficient-evidence response"}
    result.update(answer=answer, status=status, checks=checks, llm_stats=stats,
                  model_called=stats is not None,
                  memory=llm.process_memory() if stats else None,
                  total_seconds=round(time.time() - started, 2))
    result["log"] = str(runlog.save("ask", result))
    return result


# ---------- chat: personal assistant with optional retrieval ----------

class ChatSession:
    def __init__(self):
        self.history = []        # [{"role", "content"}] -- conversation, not evidence
        self.index = Index.load()
        self.env = runlog.environment()
        self.system = self._system_prompt()

    def _system_prompt(self):
        titles = []
        if config.INDEX_MD.exists():
            titles = list(dict.fromkeys(t for t, _ in wiki_links(config.INDEX_MD.read_text())))
        return (load_prompt("persona.md")
                + "\n\n## Notes currently in the wiki (titles only)\n"
                + (", ".join(titles) or "(the wiki is empty; suggest running `wiki ingest`)"))

    def route(self, text):
        """Ask Gemma (small, deterministic call) whether this turn needs the notes."""
        context = ""
        if self.history:
            last = self.history[-1]["content"][:400]
            context = f"Previous assistant message (for context only):\n{last}\n\n"
        schema = {"type": "object",
                  "properties": {"needs_notes": {"type": "boolean"}, "query": {"type": "string"}},
                  "required": ["needs_notes", "query"]}
        raw, stats = llm.chat(
            [{"role": "system", "content": load_prompt("router.md")},
             {"role": "user", "content": f"{context}User message: {text}"}],
            temperature=0.0, fmt=schema)
        try:
            import json
            decision = json.loads(raw)
        except ValueError:
            decision = {"needs_notes": False, "query": "", "error": raw[:200]}
        decision["router_seconds"] = stats["wall_seconds"]
        return decision

    def _trimmed_history(self):
        msgs, used = [], 0
        for m in reversed(self.history[-config.CHAT_HISTORY_MESSAGES:]):
            used += len(m["content"])
            if used > config.CHAT_HISTORY_CHARS and msgs:
                break
            msgs.insert(0, m)
        return msgs

    def turn(self, text, *, force_query=None, on_token=None, on_route=None):
        started = time.time()
        decision = ({"needs_notes": True, "query": force_query, "forced": True}
                    if force_query else self.route(text))
        hits = []
        if decision.get("needs_notes") and decision.get("query"):
            hits = fit_to_budget(self.index.search(decision["query"], k=config.CHAT_TOP_K),
                                 config.MAX_CONTEXT_CHARS)
        if on_route:
            on_route(decision, hits)
        user_content = text
        if hits:
            user_content = (f"{text}\n\n---\nNOTES RETRIEVED FOR THIS TURN (cite as [n]):\n\n"
                            f"{format_passages(hits)}")
        messages = ([{"role": "system", "content": self.system}] + self._trimmed_history()
                    + [{"role": "user", "content": user_content}])
        reply, stats = llm.chat(messages, temperature=0.6, on_token=on_token)
        reply = reply.strip()
        checks = check_citations(reply, hits) if hits else {
            "cited": cited_numbers(reply), "ok": not cited_numbers(reply),
            "note": "no notes retrieved; any [n] here would be an unsupported citation"}
        # History keeps what was said plus which sources backed it, never the raw passages.
        stored = reply
        if hits:
            stored += "\n\n(Sources for that reply: " + "; ".join(
                f"[{n}] {h['path']} §{h['section']}" for n, h in enumerate(hits, 1)) + ")"
        self.history += [{"role": "user", "content": text},
                         {"role": "assistant", "content": stored}]
        record = {**self.env, "time": runlog.now(), "user": text, "route": decision,
                  "passages": [passage_record(h) for h in hits], "reply": reply,
                  "checks": checks, "history_messages_sent": len(messages) - 2,
                  "llm_stats": stats, "total_seconds": round(time.time() - started, 2)}
        runlog.save("chat", record)
        return record
