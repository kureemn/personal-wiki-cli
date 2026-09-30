"""Ingestion: original source -> local Gemma -> reviewed-style wiki notes + indexes.

One Gemma call per source returns JSON (schema below). The harness, not the model, writes
the Markdown: filenames, headings, links and source references are all built here, so they
stay stable and readable no matter how the model phrases things.
"""
import difflib
import hashlib
import json
import re
import time
from pathlib import Path

from . import config, llm, runlog, vault
from .harness import load_prompt
from .markdown import heading_anchor, headings, render_frontmatter, split_frontmatter

SCHEMA = {
    "type": "object",
    "properties": {
        "project": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "summary": {"type": "string"},
                "key_facts": {"type": "array", "items": {
                    "type": "object",
                    "properties": {"fact": {"type": "string"}, "section": {"type": "string"}},
                    "required": ["fact", "section"]}},
            },
            "required": ["title", "description", "summary", "key_facts"],
        },
        "concepts": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "folder": {"type": "string", "enum": ["Concepts", "Tools"]},
                "definition": {"type": "string"},
                "how_used": {"type": "string"},
                "section": {"type": "string"},
            },
            "required": ["title", "folder", "definition", "how_used", "section"]}},
    },
    "required": ["project", "concepts"],
}

MAX_CONCEPTS = 5


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def norm_key(title):
    """Key used to detect that two titles name the same note ('Row-Level Security' == 'Row Level Security')."""
    k = re.sub(r"[^a-z0-9]", "", title.lower())
    return k[:-1] if k.endswith("s") and len(k) > 4 else k


def clean_title(title, max_words=6):
    """Readable filename-safe title: no path/link characters, no 'README', <= max_words."""
    t = re.sub(r"\breadme\b", "", title, flags=re.I)
    t = re.sub(r"\.(?!\w)|(?<!\w)\.", " ", t)              # keep dots inside names: Next.js
    t = re.sub(r"[\\/:*?\"<>|#^\[\]{}(),;!]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -")
    words = t.split()
    return " ".join(words[:max_words]) if words else ""


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_source_text(text):
    """What Gemma sees: the source minus image embeds (useless to a text model), capped."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    if len(text) > config.MAX_INGEST_CHARS:
        text = text[: config.MAX_INGEST_CHARS] + "\n\n[... truncated for context budget ...]"
    return text


# ---------- entry point ----------

def ingest(target, *, force=False, overwrite_reviewed=False, log=print):
    target = target.resolve()
    if not target.exists():
        raise FileNotFoundError(f"No such file or folder: {target}")
    files = sorted(p for p in target.glob("*") if p.suffix in (".md", ".txt")) \
        if target.is_dir() else [target]
    raw_root = config.RAW.resolve()
    outside = [f for f in files if raw_root not in f.parents]
    if outside:
        raise ValueError(f"Sources must live in {config.RAW} (originals are kept there, "
                         f"unchanged). Copy them in first: {[str(f) for f in outside]}")
    if not files:
        raise FileNotFoundError(f"No .md or .txt sources found in {target}")

    catalog = vault.load_catalog()
    env = runlog.environment()
    summary = []
    for f in files:
        sid, digest = slug(f.stem), sha256(f)
        entry = catalog.get(sid, {})
        project_path = config.VAULT / entry["project_note"] if entry.get("project_note") else None
        up_to_date = (entry.get("sha256") == digest and project_path and project_path.exists())
        if up_to_date and not force:
            log(f"= {f.name}: unchanged (sha256 {digest[:12]}), notes up to date - no model call")
            summary.append({"source": f.name, "action": "unchanged"})
            continue
        reviewed = False
        if project_path and project_path.exists() and not overwrite_reviewed:
            reviewed = split_frontmatter(project_path.read_text())[0].get("reviewed") is True
        llm.check_model()
        log(f"+ {f.name}: sending {len(f.read_text()):,} chars to {config.MODEL} ...")
        started = time.time()
        data, stats = generate(f)
        if reviewed:
            # Never overwrite a human-reviewed note: stage the new draft for comparison.
            draft, dropped = render_project(f, sid, digest, data, entry, concept_lines=[
                f"- [[{clean_title(c.get('title', ''), 4)}]]: {c.get('how_used', '')}"
                for c in data.get("concepts", [])[:MAX_CONCEPTS]])
            review = config.DATA / "review" / Path(entry["project_note"]).name
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text(draft)
            secs = round(time.time() - started, 1)
            log(f"  {entry['project_note']} is marked reviewed: true, so it was NOT overwritten.\n"
                f"  New draft ({secs}s, same filename, no new notes) saved for comparison: "
                f"{review.relative_to(config.ROOT)}\n  (rerun with --overwrite-reviewed to replace it)")
            summary.append({"source": f.name, "action": "staged-for-review", "seconds": secs,
                            "llm_stats": stats, "draft": str(review), "dropped": dropped,
                            "memory": llm.process_memory()})
            continue
        written, dropped = write_notes(f, sid, digest, data, entry)
        catalog[sid] = {**written, "sha256": digest, "raw_file": f"raw/{f.name}",
                        "bytes": f.stat().st_size, "ingested_at": runlog.now(),
                        "model": config.MODEL}
        vault.save_catalog(catalog)
        secs = round(time.time() - started, 1)
        log(f"  wrote {written['project_note']} + {len(written['concept_notes'])} concept/tool "
            f"notes in {secs}s ({stats['prompt_tokens']} prompt tokens, "
            f"{stats['output_tokens']} output tokens)")
        for d in dropped:
            log(f"  dropped (failed check): {d}")
        summary.append({"source": f.name, "action": "generated", "seconds": secs,
                        "llm_stats": stats, "notes": written, "dropped": dropped,
                        "memory": llm.process_memory()})

    vault.finalize(catalog)
    from .retrieval import build_index
    chunks = build_index(log=log)
    log(f"  index.md, Source Catalog.md and retrieval index rebuilt ({len(chunks)} passages)")
    problems = vault.check_links()
    log("  link check: " + ("all internal links and source references resolve"
                            if not problems else f"{len(problems)} problem(s) - run `wiki check`"))
    runlog.save("ingest", {**env, "target": str(target), "force": force, "results": summary,
                           "link_problems": problems})
    return summary


# ---------- model call ----------

def generate(path):
    text = path.read_text()
    heads = headings(text)
    existing = sorted(p.stem for p in config.WIKI.rglob("*.md"))
    prompt = (f"EXISTING NOTE TITLES (reuse the exact title if a concept matches):\n"
              f"{', '.join(existing) or '(none yet)'}\n\n"
              f"HEADINGS IN THIS SOURCE:\n" + "\n".join(f"- {h}" for h in heads) +
              f"\n\nSOURCE FILE: raw/{path.name}\n\n<<<SOURCE\n{prepare_source_text(text)}\nSOURCE>>>")
    raw, stats = llm.chat(
        [{"role": "system", "content": load_prompt("ingest-instructions.md")},
         {"role": "user", "content": prompt}],
        temperature=0.0, num_ctx=config.NUM_CTX_INGEST, fmt=SCHEMA)
    try:
        return json.loads(raw), stats
    except ValueError as e:
        raise RuntimeError(f"Gemma returned invalid JSON for {path.name}: {e}\n{raw[:500]}")


# ---------- writing notes ----------

def _match_heading(section, heads):
    if not section:
        return None
    s = re.sub(r"[*_`#]", "", section).strip()
    if s in heads:
        return s
    close = difflib.get_close_matches(s, heads, n=1, cutoff=0.6)
    return close[0] if close else None


def _numbers_supported(fact, source_text):
    src = source_text.replace(",", "")
    return all(n.replace(",", "") in src for n in re.findall(r"\d[\d,]*(?:\.\d+)?", fact))


def _source_link(raw_stem, heading):
    return f"[[{raw_stem}#{heading_anchor(heading)}|{heading}]]" if heading else f"[[{raw_stem}]]"


def project_title(data, entry, path):
    """Pinned after first ingest so re-ingestion never renames or duplicates the note."""
    return (entry.get("project_title") or clean_title(data["project"].get("title", ""), 5)
            or clean_title(path.stem, 5))


def render_project(path, sid, digest, data, entry, concept_lines):
    """Markdown for the project note. Returns (text, dropped facts)."""
    text, raw_stem = path.read_text(), path.stem
    heads = headings(text)
    proj, dropped = data["project"], []
    title = project_title(data, entry, path)
    facts = []
    for kf in proj.get("key_facts", [])[:10]:
        fact = kf.get("fact", "").strip()
        if not fact:
            continue
        if not _numbers_supported(fact, text):
            dropped.append(f"fact with number not in source: {fact}")
            continue
        facts.append(f"- {fact} (source: {_source_link(raw_stem, _match_heading(kf.get('section'), heads))})")
    meta = {"type": "project", "description": proj.get("description", "").strip(),
            "source_id": sid, "source_file": f"raw/{path.name}", "source_sha256": digest,
            "generated_by": config.MODEL, "generated_at": runlog.now(), "reviewed": False}
    body = (f"# {title}\n\n{proj.get('summary', '').strip()}\n\n"
            f"## Key facts\n\n" + "\n".join(facts) + "\n\n"
            f"## Concepts and tools used\n\n" + "\n".join(concept_lines) + "\n\n"
            f"{vault.RELATED_START}\n{vault.RELATED_END}\n\n"
            f"## Source\n\n- Original document: [[{raw_stem}]] (`raw/{path.name}`, kept unchanged)\n"
            f"- All sources: [[Source Catalog]]\n")
    return render_frontmatter(meta) + body, dropped


def write_notes(path, sid, digest, data, entry):
    """Write the project note and this source's blocks in concept notes.
    Returns (catalog fields, dropped items)."""
    text, raw_stem = path.read_text(), path.stem
    heads = headings(text)
    dropped = []
    stamp = {"generated_by": config.MODEL, "generated_at": runlog.now(), "reviewed": False}
    title = project_title(data, entry, path)
    by_key = {norm_key(p.stem): p for p in config.WIKI.rglob("*.md")}

    # Concepts: reuse existing notes when the normalized title matches.
    for old in vault.notes_with_block(sid):          # clear this source's old contributions
        vault.remove_block(old, sid)
    concept_lines, concept_notes = [], []
    for c in data.get("concepts", [])[:MAX_CONCEPTS]:
        ctitle = clean_title(c.get("title", ""), 4)
        if not ctitle or norm_key(ctitle) == norm_key(title):
            dropped.append(f"concept with unusable title: {c.get('title')!r}")
            continue
        existing = by_key.get(norm_key(ctitle))
        if existing is not None and existing.parent.name == "Projects":
            dropped.append(f"concept title collides with a project: {ctitle}")
            continue
        folder = c.get("folder") if c.get("folder") in ("Concepts", "Tools") else "Concepts"
        cpath = existing or (config.WIKI / folder / f"{ctitle}.md")
        ctitle = cpath.stem
        heading = _match_heading(c.get("section"), heads)
        how = c.get("how_used", "").strip()
        block_line = f"- [[{title}]]: {how} (source: {_source_link(raw_stem, heading)})"
        vault.upsert_concept(cpath, ctitle, folder, c.get("definition", "").strip(),
                             sid, block_line, stamp)
        by_key[norm_key(ctitle)] = cpath
        concept_notes.append(str(cpath.relative_to(config.VAULT)))
        concept_lines.append(f"- [[{ctitle}]]: {how}")

    note, fact_drops = render_project(path, sid, digest, data, entry, concept_lines)
    dropped += fact_drops
    ppath = config.WIKI / "Projects" / f"{title}.md"
    old_note = config.VAULT / entry["project_note"] if entry.get("project_note") else None
    if old_note and old_note != ppath and old_note.exists():
        old_note.unlink()                          # renamed by hand in catalog: move, don't duplicate
    ppath.parent.mkdir(parents=True, exist_ok=True)
    ppath.write_text(note)
    vault.delete_empty_concepts()
    return ({"project_title": title, "project_note": str(ppath.relative_to(config.VAULT)),
             "concept_notes": concept_notes}, dropped)
