"""Vault maintenance: concept blocks, related links, index.md, Source Catalog.md, link check."""
import json
import re
from collections import defaultdict

from . import config
from .markdown import heading_anchor, headings, render_frontmatter, split_frontmatter, wiki_links

RELATED_START, RELATED_END = "<!-- related:start -->", "<!-- related:end -->"


# ---------- catalog (machine copy lives in data/, human copy in the vault) ----------

def load_catalog():
    return json.loads(config.CATALOG.read_text()) if config.CATALOG.exists() else {}


def save_catalog(catalog):
    config.DATA.mkdir(exist_ok=True)
    config.CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")


# ---------- concept notes: one block per contributing source ----------

def _block_re(sid):
    return re.compile(rf"<!-- from:{re.escape(sid)} -->\n.*?<!-- /from:{re.escape(sid)} -->\n?", re.S)


def notes_with_block(sid):
    return [p for p in config.WIKI.rglob("*.md") if f"<!-- from:{sid} -->" in p.read_text()]


def remove_block(path, sid):
    path.write_text(_block_re(sid).sub("", path.read_text()))


def upsert_concept(path, title, folder, definition, sid, line, stamp):
    """Create the concept note if new (definition written once), then add this source's block."""
    block = f"<!-- from:{sid} -->\n{line}\n<!-- /from:{sid} -->\n"
    if path.exists():
        text = _block_re(sid).sub("", path.read_text())
        text = text.replace("## In my projects\n\n", "## In my projects\n\n" + block, 1)
    else:
        meta = {"type": "tool" if folder == "Tools" else "concept",
                "description": definition.split(". ")[0].rstrip(".") + ".", **stamp}
        text = (render_frontmatter(meta) + f"# {title}\n\n{definition}\n\n"
                f"## In my projects\n\n{block}\n## Source\n\n"
                "Each line above links to the section of the original document it came from. "
                "See [[Source Catalog]].\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def delete_empty_concepts():
    """A generated concept no source contributes to any more is removed (unless reviewed)."""
    for p in config.WIKI.rglob("*.md"):
        if p.parent.name == "Projects":
            continue
        meta, body = split_frontmatter(p.read_text())
        if "<!-- from:" not in body and meta.get("reviewed") is not True:
            p.unlink()


# ---------- derived pages ----------

def _notes():
    out = []
    for p in sorted(config.WIKI.rglob("*.md")):
        meta, body = split_frontmatter(p.read_text())
        out.append({"path": p, "title": p.stem, "folder": p.parent.name, "meta": meta, "body": body})
    return out


def finalize(catalog):
    """Recompute cross-project links, then index.md and Source Catalog.md."""
    notes = _notes()
    projects = {n["title"]: n for n in notes if n["folder"] == "Projects"}
    uses = defaultdict(set)              # concept title -> project titles that link it
    for n in notes:
        if n["folder"] == "Projects":
            continue
        for target, _ in wiki_links(n["body"]):
            if target in projects:
                uses[n["title"]].add(target)
    for pt, pn in projects.items():
        shared = defaultdict(list)       # other project -> concepts in common
        for concept, users in uses.items():
            if pt in users:
                for other in users - {pt}:
                    shared[other].append(concept)
        lines = [f"- [[{o}]]: also uses " + ", ".join(f"[[{c}]]" for c in sorted(cs))
                 for o, cs in sorted(shared.items())]
        section = (f"{RELATED_START}\n## Related projects\n\n" + "\n".join(lines) + f"\n{RELATED_END}"
                   if lines else f"{RELATED_START}\n{RELATED_END}")
        text = pn["path"].read_text()
        text = re.sub(re.escape(RELATED_START) + ".*?" + re.escape(RELATED_END), section, text, flags=re.S)
        pn["path"].write_text(text)
    write_index(_notes())
    write_catalog_md(catalog)


def write_index(notes):
    groups = [("Projects", "Projects", "What I built for each class assignment."),
              ("Concepts", "Concepts", "Ideas and techniques the projects rely on."),
              ("Tools", "Tools", "Software, libraries and services used.")]
    out = ["# Personal Wiki: Agentic AI Class Projects", "",
           "Start here. Each note was drafted by a local Gemma model from an original document "
           "in `raw/`, then checked against that document. Every note links back to the exact "
           "source section it came from.", ""]
    for folder, label, blurb in groups:
        items = [n for n in notes if n["folder"] == folder]
        if not items:
            continue
        out += [f"## {label}", "", blurb, ""]
        out += [f"- [[{n['title']}]]: {n['meta'].get('description', '')}" for n in items]
        out.append("")
    out += ["## Sources", "",
            "- [[Source Catalog]]: the original documents, their checksums, and which notes came from each.",
            ""]
    config.INDEX_MD.write_text("\n".join(out))


def write_catalog_md(catalog):
    out = ["# Source Catalog", "",
           "Original documents in `raw/` are never edited. Machine IDs and checksums live here "
           "and in note properties, not in filenames.", "",
           "| Source | Source ID | SHA-256 | Size | Ingested | Notes generated |",
           "|---|---|---|---|---|---|"]
    for sid, e in sorted(catalog.items()):
        stem = e["raw_file"].removeprefix("raw/").rsplit(".", 1)[0]
        notes = [e["project_note"]] + e.get("concept_notes", [])
        links = ", ".join(f"[[{n.rsplit('/', 1)[-1].removesuffix('.md')}]]" for n in notes)
        out.append(f"| [[{stem}]] | `{sid}` | `{e['sha256'][:12]}` | {e['bytes']:,} B | "
                   f"{e['ingested_at'][:16].replace('T', ' ')} | {links} |")
    out += ["", "Back to [[index]].", ""]
    config.CATALOG_MD.write_text("\n".join(out))


# ---------- link check ----------

def check_links():
    """Every [[link]] in the vault must resolve to exactly one note, and every #heading
    must exist in that note. Returns a list of problems."""
    files = [p for p in config.VAULT.rglob("*.md") if ".obsidian" not in p.parts]
    by_name = defaultdict(list)
    for p in files:
        by_name[p.stem].append(p)
    problems = []
    for p in files:
        if config.RAW in p.parents:
            continue                     # originals are evidence, not ours to fix
        for target, heading in wiki_links(p.read_text()):
            hits = by_name.get(target, [])
            where = str(p.relative_to(config.VAULT))
            if not hits:
                problems.append(f"{where}: [[{target}]] has no matching note")
            elif len(hits) > 1:
                problems.append(f"{where}: [[{target}]] is ambiguous ({len(hits)} files)")
            elif heading and heading_anchor(heading) not in map(heading_anchor, headings(hits[0].read_text())):
                problems.append(f"{where}: [[{target}#{heading}]] heading not found")
    return problems


def rename_note(old, new):
    """Rename a wiki note and rewrite every incoming [[link]], the H1 and the catalog.
    Machine IDs (source_id, sha256) stay in properties; only the readable name changes."""
    matches = [p for p in config.WIKI.rglob("*.md") if p.stem == old]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one wiki note named '{old}', found {len(matches)}")
    src = matches[0]
    dst = src.with_name(f"{new}.md")
    case_only = dst.exists() and dst.samefile(src)      # macOS: case-insensitive filesystem
    if dst.exists() and not case_only:
        raise ValueError(f"'{dst.relative_to(config.VAULT)}' already exists; merge by hand instead")
    link = re.compile(r"\[\[" + re.escape(old) + r"(?=[\]#|])")
    changed = 0
    for p in config.VAULT.rglob("*.md"):
        if config.RAW in p.parents or ".obsidian" in p.parts:
            continue
        text = p.read_text()
        new_text = link.sub("[[" + new, text)
        if p == src:
            new_text = new_text.replace(f"\n# {old}\n", f"\n# {new}\n", 1)
        if new_text != text:
            p.write_text(new_text)
            changed += 1
    if case_only:
        tmp = src.with_name(f".renaming-{new}.md")
        src.rename(tmp)
        tmp.rename(dst)
    else:
        src.rename(dst)
    catalog = load_catalog()
    old_rel, new_rel = str(src.relative_to(config.VAULT)), str(dst.relative_to(config.VAULT))
    for e in catalog.values():
        if e.get("project_note") == old_rel:
            e.update(project_note=new_rel, project_title=new)
        e["concept_notes"] = [new_rel if n == old_rel else n for n in e.get("concept_notes", [])]
    save_catalog(catalog)
    return new_rel, changed
