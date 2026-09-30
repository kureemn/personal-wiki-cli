"""Paths and settings. Everything the harness reads or writes is located from here."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The Obsidian vault: only human-facing Markdown lives here.
VAULT = ROOT / "vault"
RAW = VAULT / "raw"                 # original sources, never modified
WIKI = VAULT / "wiki"               # generated + reviewed notes
INDEX_MD = VAULT / "index.md"       # human landing page (also read by the indexer)
CATALOG_MD = VAULT / "Source Catalog.md"
WIKI_FOLDERS = ("Projects", "Concepts", "Tools")

# Machine files: kept outside the vault.
DATA = ROOT / "data"
CHUNKS = DATA / "chunks.jsonl"      # retrieval passages (the local index)
EMBEDDINGS = DATA / "embeddings.json"  # passage vectors keyed by text hash
CATALOG = DATA / "catalog.json"     # source_id -> file, hash, generated notes
PROMPTS = ROOT / "prompts"
RUNS = ROOT / "runs"                # every ask/search/chat/ingest is logged here
DRAFTS = ROOT / "drafts"            # chat replies saved with /save (never indexed)
EVALS = ROOT / "evals"
EVIDENCE = ROOT / "evidence"

# Local model (Ollama). Override with env vars, e.g. WIKI_MODEL=gemma4:e2b-it-q4_K_M
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = "http://" + OLLAMA_URL
MODEL = os.environ.get("WIKI_MODEL", "gemma4:e4b-it-q4_K_M")
EMBED_MODEL = os.environ.get("WIKI_EMBED_MODEL", "embeddinggemma:300m")

# Context budgets (Gemma 4 E4B supports 128K tokens; we use far less to save memory/time).
NUM_CTX_ANSWER = 8192        # ask, chat, router and answer check: one size, because Ollama reloads the model when num_ctx changes
NUM_CTX_INGEST = 24576       # one whole source document per ingest call
MAX_INGEST_CHARS = 70_000    # hard cap on source text sent during ingest

# Retrieval
CHUNK_CHARS = 1200           # target passage size (~300 tokens)
ASK_TOP_K = 8
CHAT_TOP_K = 4
MAX_CONTEXT_CHARS = 9000     # total passage text passed to Gemma per answer
ASK_MIN_SCORE = 4.0          # below this best BM25 score, ask reports insufficient evidence
CHAT_HISTORY_MESSAGES = 10   # recent messages kept in chat context
CHAT_HISTORY_CHARS = 6000
