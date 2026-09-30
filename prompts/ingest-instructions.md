# Ingest rules: turn one source document into wiki notes

You convert ONE source document into structured notes for a personal Obsidian wiki.
Return JSON only, matching the provided schema.

## What to produce
- `project`: one note about the document's main subject.
  - `title`: 2–5 words, Title Case, the subject's natural name (e.g. "Ms Pac-Man DQN").
    No dates, no "README", no full sentences, no punctuation except hyphens.
  - `description`: one sentence (max 25 words) for the index.
  - `summary`: 2–4 sentences.
  - `key_facts`: 5–10 short factual statements copied closely from the source, each with
    `section` = the exact heading text (without #) under which the fact appears.
- `concepts`: 4–5 reusable entries the document relies on: 2–3 ideas/techniques
  (folder "Concepts", e.g. "Experience Replay", "Row Level Security") and 1–2 main
  software tools, libraries or services (folder "Tools", e.g. "PyTorch", "Next.js"). Each has:
  - `title`: 1–4 words, Title Case, the general name of the idea, not project-specific.
    If an entry in EXISTING NOTE TITLES means the same thing, reuse that exact title.
  - Prefer ideas that connect projects: if this document genuinely discusses a concept
    already in EXISTING NOTE TITLES (for example a hyperparameter it also tunes), include
    it with the exact existing title. Never include a concept the document does not discuss.
  - `folder`: "Concepts" for ideas/techniques, "Tools" for software, libraries, services.
  - `definition`: one or two neutral sentences defining the idea in general.
  - `how_used`: one sentence on how THIS document uses it, stated as in the source.
  - `section`: the exact heading text where the document discusses it.

## Rules
- Only state what the source says. No invented numbers, names or results.
- Copy numbers exactly. Keep every fact short (under 30 words).
- Headings must be copied exactly from the HEADINGS list provided.
