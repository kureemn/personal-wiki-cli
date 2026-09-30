"""Markdown helpers: frontmatter, headings, wiki links, and passage chunking."""
import re

from . import config

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")


# ---------- frontmatter (tiny YAML subset: scalars and lists of scalars) ----------

def split_frontmatter(text):
    """Return (meta dict, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta, key = {}, None
    for line in text[4:end].splitlines():
        if line.startswith("  - ") and key:
            meta.setdefault(key, []).append(_unquote(line[4:]))
        elif ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            meta[key] = _unquote(value) if value else []
    return meta, text[end + 5:]


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    if v in ("true", "false"):
        return v == "true"
    return v


def _quote(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    return '"' + s.replace('"', '\\"') + '"' if re.search(r"[:#\[\]{}\"',]|^\s|\s$", s) or s == "" else s


def render_frontmatter(meta):
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines += [f"  - {_quote(x)}" for x in v]
        else:
            lines.append(f"{k}: {_quote(v)}")
    lines.append("---\n")
    return "\n".join(lines)


# ---------- headings and links ----------

def iter_lines_outside_code(text):
    """Yield (line_no, line, in_code) so headings inside ``` fences are ignored."""
    in_code = False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            yield i, line, True
            continue
        yield i, line, in_code


def headings(text):
    """All heading texts (without #), in order, outside code fences."""
    out = []
    for _, line, in_code in iter_lines_outside_code(text):
        m = None if in_code else HEADING_RE.match(line)
        if m:
            out.append(clean_heading(m.group(2)))
    return out


def clean_heading(h):
    """Obsidian heading-link form: markdown emphasis/code removed."""
    return re.sub(r"[*_`]", "", h).strip()


def heading_anchor(h):
    """Heading as written after # in an Obsidian link: characters Obsidian does not allow
    in links (# | ^ : % [ ] \\) become spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[#|^:%\[\]\\]", " ", h)).strip()


def wiki_links(text):
    """[(target, heading or None)] for every [[link]] in text."""
    return [(m.group(1).strip(), (m.group(2) or "").strip() or None) for m in LINK_RE.finditer(text)]


# ---------- chunking ----------

def chunk_markdown(text, source_path, kind, title=None):
    """Split a Markdown document into passages that keep their section and line numbers.

    Sections are cut at headings; a section longer than CHUNK_CHARS is split at blank
    lines (paragraph/table boundaries), and an oversized paragraph at line boundaries.
    """
    meta, body = split_frontmatter(text)
    offset = text[: len(text) - len(body)].count("\n")  # frontmatter lines skipped
    lines = body.splitlines()
    doc_title = title or meta.get("title")
    stack = []       # heading path
    sections = []    # (heading_path, start_line, [lines])
    current = ([], 1, [])
    for i, line, in_code in iter_lines_outside_code(body):
        m = None if in_code else HEADING_RE.match(line)
        if m:
            if any(l.strip() for l in current[2]):
                sections.append(current)
            level, h = len(m.group(1)), clean_heading(m.group(2))
            stack = [s for s in stack if s[0] < level] + [(level, h)]
            if level == 1 and not doc_title:
                doc_title = h
            current = ([s[1] for s in stack], i, [line])
        else:
            current[2].append(line)
    if any(l.strip() for l in current[2]):
        sections.append(current)

    chunks = []
    for path, start, sec_lines in sections:
        for a, b in _split_block(sec_lines):
            passage = "\n".join(sec_lines[a:b]).strip()
            if len(passage) < 40:      # skip empty headings / separators
                continue
            first, last = start + a + offset, start + b - 1 + offset
            chunks.append({
                "id": f"{source_path}#L{first}-{last}",
                "kind": kind,                      # "raw" (original) or "wiki" (generated note)
                "path": source_path,               # relative to vault/
                "title": doc_title or source_path,
                "section": path[-1] if path else "",
                "heading_path": " > ".join(path),
                "line_start": first,
                "line_end": last,
                "text": passage,
            })
    return chunks


def _split_block(lines):
    """Yield (start, end) index ranges of at most ~CHUNK_CHARS characters."""
    limit = config.CHUNK_CHARS
    # paragraph units: runs of lines separated by blank lines
    units, start = [], 0
    for i, line in enumerate(lines + [""]):
        if not line.strip():
            if i > start:
                units.append((start, i))
            start = i + 1
    # break a single oversized unit (e.g. a long table) at line boundaries
    fine = []
    for a, b in units:
        size, s = 0, a
        for i in range(a, b):
            size += len(lines[i]) + 1
            if size > limit and i > s:
                fine.append((s, i))
                s, size = i, len(lines[i]) + 1
        fine.append((s, b))
    # greedily merge small units up to the limit
    merged = []
    for a, b in fine:
        if merged and sum(len(l) + 1 for l in lines[merged[-1][0]:b]) <= limit:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged
