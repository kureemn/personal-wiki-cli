"""wiki: command-line interface to the personal wiki harness."""
import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from . import config, harness, llm, runlog, vault
from .llm import ModelUnavailable
from .retrieval import Index, build_index

TTY = sys.stdout.isatty()


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if TTY else text


def dim(t): return c(t, "2")
def bold(t): return c(t, "1")
def warn(t): return c(t, "33")
def good(t): return c(t, "32")


def header(mode):
    net = runlog.internet_status()
    print(dim(f"── {mode} · local · model {config.MODEL} · embed {config.EMBED_MODEL} · "
              f"internet: {net} ──"))


def show_passage(n, h, full=False, width=100):
    score = f"score {h['score']}"
    if h.get("bm25") is not None:
        score += f" · bm25 {h['bm25']}"
    if h.get("cosine") is not None:
        score += f" · cos {h['cosine']}"
    print(bold(f"[{n}] {h['path']}") + f"  lines {h['line_start']}-{h['line_end']}  "
          + c(f"§ {h['section']}", "36") + dim(f"  ({h['method']} {score})"))
    lines = h["text"].splitlines()
    if not full and len(lines) > 8:
        lines = lines[:8] + [dim(f"... ({len(h['text'].splitlines()) - 8} more lines; --full to show)")]
    for line in lines:
        print("    " + line[: width * 2])
    print()


# ---------- commands ----------

def cmd_search(a):
    header("search")
    index = Index.load()
    hits = index.search(a.query, k=a.k, scope=a.scope, method=a.method)
    if hits and hits[0]["method"] == "bm25" and a.method == "hybrid":
        print(warn("(embedding model unavailable: showing keyword BM25 results only)"))
    if not hits:
        print("No matching passages.")
    for n, h in enumerate(hits, 1):
        show_passage(n, h, full=a.full)
    print(dim("search returns original passages only; no answer is generated."))
    runlog.save("search", {**runlog.environment(), "query": a.query, "scope": a.scope,
                           "passages": [harness.passage_record(h) for h in hits]})


def cmd_ask(a):
    require_local(a)
    header("ask")
    print(bold("Q: ") + a.question + "\n")
    print(dim("retrieving passages, calling local Gemma, then checking the answer..."))
    r = harness.ask(a.question, k=a.k)
    print(bold("A: ") + r["answer"] + "\n")
    chk = r.get("answer_check")
    if chk:
        print(dim(f"answer check: {chk.get('verdict')} (asks for: {chk.get('question_asks_for')}; "
                  f"answer gives: {chk.get('answer_provides')})"))
    if r.get("draft_answer"):
        print(dim("rejected draft: " + r["draft_answer"]))
    print_citations(r)
    if a.show_passages:
        print(bold("Retrieved passages:"))
        for n, h in enumerate(r["passages"], 1):
            show_passage(n, h, full=True)
    s = r.get("llm_stats") or {}
    print(dim(f"status: {r['status']} · {r['total_seconds']}s total"
              + (f" · {s.get('prompt_tokens')} prompt tok · {s.get('output_tokens')} output tok · "
                 f"{s.get('generation_tokens_per_s')} tok/s" if s else " · model not called")
              + f" · saved to {os.path.relpath(r['log'], config.ROOT)}"))
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))


def print_citations(r):
    hits, checks = r["passages"], r["checks"]
    cited = [n for n in checks.get("cited", []) if 1 <= n <= len(hits)]
    if cited:
        print(bold("Citations:"))
        for n in cited:
            h = hits[n - 1]
            print(f"  [{n}] {h['path']}  lines {h['line_start']}-{h['line_end']}  § {h['section']}")
    uncited = [n for n in range(1, len(hits) + 1) if n not in cited]
    if uncited:
        print(dim("  retrieved but not cited: " + ", ".join(
            f"[{n}] {hits[n-1]['path'].removeprefix('raw/')} § {hits[n-1]['section'][:40]}" for n in uncited)))
    if r["status"] == "insufficient":
        print(warn("Citation check: insufficient-evidence response (no claims to verify)."))
    elif checks.get("ok"):
        print(good("Citation check: every factual sentence cites a retrieved passage; "
                   "all numbers appear in the cited passages."))
    else:
        for k, label in (("invalid_citations", "cites passages that were not retrieved"),
                         ("uncited_sentences", "sentence without a citation"),
                         ("unsupported_numbers", "number not found in its cited passage(s)")):
            for item in checks.get(k, []):
                print(warn(f"  ⚠ {label}: {item}"))
    print()


CHAT_HELP = """Commands: /notes <question> force a notes lookup · /save save last reply to drafts/
          /clear reset conversation · /history show context size · /help · /exit"""


def cmd_chat(a):
    require_local(a)
    llm.check_model()
    session = harness.ChatSession()
    header("chat")
    print(bold("Pip") + " (local Gemma personal assistant). " + dim(CHAT_HELP) + "\n")
    last = None
    while True:
        try:
            text = input(c("you ▸ ", "35")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if not sys.stdin.isatty():
            print(text)                      # scripted session: show the input in the transcript
        if text in ("/exit", "/quit"):
            break
        if text == "/help":
            print(dim(CHAT_HELP))
            continue
        if text == "/clear":
            session.history.clear()
            print(dim("(conversation cleared)"))
            continue
        if text == "/history":
            print(dim(f"({len(session.history)} messages in context, "
                      f"{sum(len(m['content']) for m in session.history)} chars)"))
            continue
        if text == "/save":
            if not last:
                print(dim("(nothing to save yet)"))
                continue
            config.DRAFTS.mkdir(exist_ok=True)
            path = config.DRAFTS / f"draft-{runlog.now()[:19].replace(':', '')}.md"
            path.write_text(f"<!-- chat draft, generated by {config.MODEL}; not source evidence -->\n\n"
                            f"**Prompt:** {last['user']}\n\n{last['reply']}\n")
            print(dim(f"(saved to {os.path.relpath(path, config.ROOT)}; drafts are never indexed)"))
            continue
        force = text[len("/notes"):].strip() if text.startswith("/notes") else None
        if force == "":
            print(dim("usage: /notes <question>"))
            continue

        def on_route(decision, hits):
            if hits:
                srcs = ", ".join(f"[{n}] {h['path']} § {h['section'][:30]}" for n, h in enumerate(hits, 1))
                why = "forced by /notes" if decision.get("forced") else f"router query: \"{decision['query']}\""
                print(dim(f"  ↳ notes lookup ({why}): {srcs}"))
            else:
                print(dim("  ↳ no notes lookup (conversation only)"))
            print(c("Pip ▸ ", "36"), end="", flush=True)

        try:
            last = session.turn(force or text, force_query=force, on_route=on_route,
                                on_token=lambda t: print(t, end="", flush=True))
        except ModelUnavailable as e:
            print(warn(f"\n{e}"))
            continue
        print()
        if last["checks"].get("cited") and not last["passages"]:
            print(warn("  ⚠ reply contains [n] citations but no notes were retrieved this turn"))
        elif last["passages"] and not last["checks"].get("ok"):
            for item in last["checks"].get("invalid_citations", []):
                print(warn(f"  ⚠ cites [{item}], which was not retrieved"))
        print(dim(f"  ({last['total_seconds']}s)") + "\n")


def cmd_ingest(a):
    from .ingest import ingest
    print(dim(f"── ingest · local · model {config.MODEL} · internet: {runlog.internet_status()} ──"))
    ingest(Path(a.path), force=a.force, overwrite_reviewed=a.overwrite_reviewed)


def cmd_rename(a):
    new_rel, changed = vault.rename_note(a.old, a.new)
    vault.finalize(vault.load_catalog())
    build_index()
    print(f"renamed to {new_rel}; rewrote links in {changed} file(s); index + retrieval rebuilt")
    problems = vault.check_links()
    print("link check: " + ("ok" if not problems else f"{len(problems)} problem(s), run `wiki check`"))


def cmd_reindex(a):
    vault.finalize(vault.load_catalog())
    chunks = build_index(embed=not a.no_embed)
    print(f"rebuilt index.md, Source Catalog.md and {len(chunks)} retrieval passages")


def cmd_check(a):
    problems = vault.check_links()
    notes = list(config.WIKI.rglob("*.md"))
    raw = list(config.RAW.glob("*"))
    print(f"vault: {len(raw)} raw sources, {len(notes)} wiki notes")
    catalog = vault.load_catalog()
    from .ingest import sha256
    for sid, e in catalog.items():
        p = config.VAULT / e["raw_file"]
        ok = p.exists() and sha256(p) == e["sha256"]
        print(f"  ✓ {e['raw_file']} unchanged since ingest (sha256 {e['sha256'][:12]})" if ok
              else warn(f"  ✗ {e['raw_file']} missing or modified since ingest"))
    for n in notes:
        first = n.read_text().split("\n# ", 1)
        if len(first) < 2 or first[1].split("\n", 1)[0].strip() != n.stem:
            problems.append(f"{n.relative_to(config.VAULT)}: first heading does not match filename")
    print("links: " + ("all internal links and #headings resolve" if not problems else ""))
    for p in problems:
        print(warn("  ✗ " + p))
    sys.exit(1 if problems else 0)


def cmd_status(a):
    print(bold("Model / runtime"))
    print(f"  ollama server {config.OLLAMA_URL}: version {llm.version() or 'NOT RUNNING'}")
    try:
        llm.check_model()
        print(f"  {config.MODEL}: available locally")
    except ModelUnavailable as e:
        print(warn("  " + str(e)))
    for m in llm.loaded_models():
        print(f"  loaded: {m['name']}, context {m['context_length']}")
    for m in llm.process_memory():
        print(f"  model runner pid {m['pid']} (blob {m['blob']}): resident {m['rss_mb']:,} MB, "
              f"private footprint {m['footprint_mb'] if m['footprint_mb'] is not None else 'n/a'} MB")
    print(bold("Device"))
    for label, cmd in (("chip", ["sysctl", "-n", "machdep.cpu.brand_string"]),
                       ("memory bytes", ["sysctl", "-n", "hw.memsize"]),
                       ("macOS", ["sw_vers", "-productVersion"])):
        try:
            print(f"  {label}: {subprocess.run(cmd, capture_output=True, text=True).stdout.strip()}")
        except OSError:
            pass
    print(f"  internet: {runlog.internet_status()}")


def cmd_eval(a):
    """Run the fixed ask-mode test set and write one evidence card per test."""
    tests = json.loads(Path(a.questions).read_text())["tests"]
    assessments_path = config.EVALS / "assessments.json"
    assessments = json.loads(assessments_path.read_text()) if assessments_path.exists() else {}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.rerender:
        # Re-render saved results (e.g. after writing assessments); no model calls.
        records = json.loads((out / "results.json").read_text())
        for rec in records:
            t = rec["test"]
            (out / f"{t['id']}.md").write_text(render_card(t, rec["result"], assessments.get(t["id"])))
        print(f"re-rendered {len(records)} evidence cards in {out} (no model calls)")
        return
    records = []
    for t in tests:
        print(bold(f"{t['id']}: ") + t["question"])
        r = harness.ask(t["question"])
        print("  " + r["answer"].replace("\n", "\n  ") + "\n")
        records.append({"test": t, "result": r})
        (out / f"{t['id']}.md").write_text(render_card(t, r, assessments.get(t["id"])))
    (out / "results.json").write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"wrote {len(records)} evidence cards to {out}")


def render_card(t, r, assessment):
    exp = set(t["expected_sources"])
    got = [h["path"] for h in r["passages"]]
    cited = [n for n in r["checks"].get("cited", []) if 1 <= n <= len(got)]
    cited_paths = {got[n - 1] for n in cited}
    s = r.get("llm_stats") or {}
    mem = "; ".join(f"runner {m['blob']}: resident {m['rss_mb']:,} MB, private {m['footprint_mb'] if m['footprint_mb'] is not None else 'n/a'} MB"
                    for m in (r.get("memory") or [])) or "n/a"
    ans = "\n".join("> " + l for l in r["answer"].splitlines())
    lines = [
        f"# {t['id'].title().replace('Test', 'Test ')}: {t['title']}", "",
        "| Field | Value |", "|---|---|",
        f"| Question | {t['question']} |",
        "| Interaction mode | `ask` (standalone, no chat history, no persona) |",
        "| Execution | local (Ollama on this Mac), no online fallback |",
        f"| Model | `{r['model']}` · embeddings `{r['embed_model']}` |",
        f"| Internet during run | **{r['internet']}** |",
        f"| Run at | {r['time']} |",
        f"| Status | `{r['status']}` |",
        f"| Response time | {r['total_seconds']} s total"
        + (f"; model {s.get('wall_seconds')} s, first token {s.get('time_to_first_token_s')} s, "
           f"{s.get('prompt_tokens')} prompt / {s.get('output_tokens')} output tokens, "
           f"{s.get('generation_tokens_per_s')} tok/s |" if s else "; model not called |"),
        f"| Memory (Ollama model runners: `ps` RSS incl. mapped weights; macOS `footprint` private) | {mem} |",
        f"| Raw log | `{os.path.relpath(r['log'], config.ROOT)}` |", "",
        "## Expected (written before the run)", "",
        f"- **Behavior:** {t['expected_behavior']}",
        f"- **Sources:** {', '.join(f'`{x}`' for x in t['expected_sources']) or 'none (unanswerable)'}",
        f"- **Passage:** {t['expected_passage']}", "",
        "## Actual answer (verbatim)", "", ans, "",
    ]
    chk = r.get("answer_check")
    if chk:
        lines += ["## Answer check (second local Gemma call, question + draft only)", "",
                  f"- Question asks for: {chk.get('question_asks_for')}",
                  f"- Draft provides: {chk.get('answer_provides')}",
                  f"- Verdict: **{chk.get('verdict')}** ({chk.get('seconds')} s)", ""]
    if r.get("draft_answer"):
        lines += ["Rejected draft (verbatim):", "", "\n".join("> " + l for l in r["draft_answer"].splitlines()), ""]
    lines += ["## Citations", ""]
    for n in cited:
        h = r["passages"][n - 1]
        lines.append(f"- [{n}] `{h['path']}` lines {h['line_start']}-{h['line_end']}, § {h['section']}")
    if not cited:
        lines.append("- (none)")
    exp_ranks = [i + 1 for i, p in enumerate(got) if p in exp]
    lines += ["", "## Automatic checks", "",
              f"- Expected source(s) retrieved: "
              + ("n/a" if not exp else ("yes" if exp <= set(got) else "**no**")
                 + f" (ranks {exp_ranks})"),
              f"- Expected source(s) cited: "
              + ("n/a" if not exp else ("yes" if exp <= cited_paths else "**no**")),
              f"- Citations to non-retrieved passages: {r['checks'].get('invalid_citations') or 'none'}",
              f"- Factual sentences without a citation: {len(r['checks'].get('uncited_sentences', []))}",
              f"- Numbers not found in cited passages: {r['checks'].get('unsupported_numbers') or 'none'}",
              f"- Contains expected keyword ({' / '.join(t['must_contain_any'])}): "
              + ("yes" if any(k.lower() in r['answer'].lower() for k in t['must_contain_any']) else "**no**"),
              "", "## Assessment (by hand, after opening the cited passages)", "",
              assessment or "_Not yet assessed._", "",
              "## Retrieved passages (in the order given to the model)", ""]
    for n, h in enumerate(r["passages"], 1):
        mark = " ← expected source" if h["path"] in exp else ""
        lines += [f"### [{n}] `{h['path']}` lines {h['line_start']}-{h['line_end']}, § {h['section']}{mark}",
                  f"score {h['score']} ({h['method']}; bm25 {h['bm25']}, cosine {h.get('cosine')})", "",
                  "````text", h["text"], "````", ""]
    return "\n".join(lines)


def require_local(a):
    if getattr(a, "mode", "local") != "local":
        raise ModelUnavailable("Online mode is not configured in this project (optional extension). "
                               "Use --mode local (the default).")


# ---------- parser ----------

EPILOG = textwrap.dedent(f"""\
    modes:
      search  retrieval only: original passages + paths, never calls the language model
      ask     standalone factual answer from retrieved raw passages, with citations,
              or "INSUFFICIENT EVIDENCE" (no chat history, no persona)
      chat    personal assistant with conversation memory; looks up notes only when needed

    examples:
      wiki ingest vault/raw
      wiki search "row level security"
      wiki ask "What mean score did the trained Pac-Man agent get?"
      wiki chat
      wiki eval                 # run the 4 fixed ask-mode tests -> evidence/ask/
      wiki check                # verify links, headings and unchanged sources

    configuration (environment variables):
      WIKI_MODEL        chat/answer model   (default {config.MODEL})
      WIKI_EMBED_MODEL  embedding model     (default {config.EMBED_MODEL})
      OLLAMA_HOST       local Ollama server (default {config.OLLAMA_URL})

    required inputs: Ollama running locally with both models pulled (`ollama pull ...`);
    sources as .md/.txt files in vault/raw/. Instructions: prompts/*.md.""")


def build_parser():
    p = argparse.ArgumentParser(prog="wiki", description="Personal wiki CLI: a local Gemma "
                                "harness over your own notes (chat, ask, search, ingest).",
                                epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", metavar="command")

    s = sub.add_parser("ingest", help="read sources in vault/raw, generate linked wiki notes, rebuild indexes")
    s.add_argument("path", help="a source file or folder inside vault/raw")
    s.add_argument("--force", action="store_true", help="regenerate even if the source is unchanged")
    s.add_argument("--overwrite-reviewed", action="store_true",
                   help="also regenerate notes marked reviewed: true")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("search", help="show original matching passages (no model answer)")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=5, help="number of passages (default 5)")
    s.add_argument("--scope", choices=["all", "raw", "wiki"], default="all")
    s.add_argument("--method", choices=["hybrid", "bm25", "dense"], default="hybrid")
    s.add_argument("--full", action="store_true", help="print whole passages")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("ask", help="standalone cited answer from your sources")
    s.add_argument("question")
    s.add_argument("--mode", choices=["local", "online"], default="local")
    s.add_argument("-k", type=int, default=None, help=f"passages to retrieve (default {config.ASK_TOP_K})")
    s.add_argument("--show-passages", action="store_true", help="print the retrieved evidence")
    s.add_argument("--json", action="store_true", help="also print the full run record")
    s.set_defaults(func=cmd_ask)

    s = sub.add_parser("chat", help="personal assistant with conversation context")
    s.add_argument("--mode", choices=["local", "online"], default="local")
    s.set_defaults(func=cmd_chat)

    s = sub.add_parser("eval", help="run the fixed ask-mode tests and write evidence cards")
    s.add_argument("--questions", default=str(config.EVALS / "questions.json"))
    s.add_argument("--out", default=str(config.EVIDENCE / "ask"))
    s.add_argument("--rerender", action="store_true",
                   help="rebuild cards from OUT/results.json + evals/assessments.json without the model")
    s.set_defaults(func=cmd_eval)

    s = sub.add_parser("check", help="verify wiki links, headings and unchanged sources")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("rename", help="rename a wiki note and update every link to it")
    s.add_argument("old")
    s.add_argument("new")
    s.set_defaults(func=cmd_rename)

    s = sub.add_parser("reindex", help="rebuild index.md, catalog and retrieval index (no generation)")
    s.add_argument("--no-embed", action="store_true", help="BM25 only; do not call the embedder")
    s.set_defaults(func=cmd_reindex)

    s = sub.add_parser("status", help="model, runtime, memory and device information")
    s.set_defaults(func=cmd_status)
    return p


def main(argv=None):
    parser = build_parser()
    a = parser.parse_args(argv)
    if not a.command:
        parser.print_help()
        return 0
    try:
        a.func(a)
    except ModelUnavailable as e:
        print(warn(f"Local model unavailable:\n  {e}"), file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError) as e:
        print(warn(f"Error: {e}"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
