"""Minimal client for the local Ollama server (stdlib only).

The model never reads files itself: every call below receives the exact messages the
harness assembled, and returns text plus timing/token statistics.
"""
import json
import time
import urllib.error
import urllib.request

from . import config


class ModelUnavailable(RuntimeError):
    """Raised with a user-facing fix when the local model cannot be used."""


def _request(path, payload=None, timeout=600):
    url = config.OLLAMA_URL + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if e.code == 404 and "not found" in body:
            raise ModelUnavailable(
                f"Model '{config.MODEL}' is not downloaded.\n"
                f"  Fix (while online): ollama pull {config.MODEL}") from None
        raise ModelUnavailable(f"Ollama returned HTTP {e.code}: {body[:300]}") from None
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ModelUnavailable(
            f"Cannot reach the local Ollama server at {config.OLLAMA_URL} ({e}).\n"
            "  Fix: start it with `ollama serve` (or `brew services start ollama`).") from None


def check_model():
    """Fail fast with a helpful message if the server is down or the model is missing."""
    with _request("/api/tags", timeout=5) as r:
        names = [m["name"] for m in json.load(r).get("models", [])]
    if config.MODEL not in names:
        raise ModelUnavailable(
            f"Model '{config.MODEL}' is not in the local Ollama store (found: {names or 'none'}).\n"
            f"  Fix (while online): ollama pull {config.MODEL}")


def chat(messages, *, temperature=0.2, num_ctx=None, fmt=None, on_token=None):
    """Send messages to Gemma. Streams tokens to on_token if given. Returns (text, stats)."""
    payload = {
        "model": config.MODEL,
        "messages": messages,
        "stream": True,
        "think": False,
        "keep_alive": "30m",
        "options": {"temperature": temperature, "seed": 42,
                    "num_ctx": num_ctx or config.NUM_CTX_ANSWER},
    }
    if fmt is not None:
        payload["format"] = fmt
    started = time.time()
    parts, final, first_token_at = [], {}, None
    with _request("/api/chat", payload) as r:
        for line in r:
            if not line.strip():
                continue
            msg = json.loads(line)
            if "error" in msg:
                raise ModelUnavailable(f"Ollama error: {msg['error']}")
            piece = msg.get("message", {}).get("content", "")
            if piece:
                first_token_at = first_token_at or time.time()
                parts.append(piece)
                if on_token:
                    on_token(piece)
            if msg.get("done"):
                final = msg
    wall = time.time() - started
    ns = 1e9
    stats = {
        "model": config.MODEL,
        "wall_seconds": round(wall, 2),
        "time_to_first_token_s": round((first_token_at or time.time()) - started, 2),
        "prompt_tokens": final.get("prompt_eval_count"),
        "output_tokens": final.get("eval_count"),
        "load_seconds": round(final.get("load_duration", 0) / ns, 2),
        "prompt_eval_seconds": round(final.get("prompt_eval_duration", 0) / ns, 2),
        "generation_tokens_per_s": round(
            final.get("eval_count", 0) / (final.get("eval_duration", 1) / ns), 1)
        if final.get("eval_duration") else None,
    }
    return "".join(parts), stats


def loaded_models():
    """What Ollama currently holds in memory (bytes), for measured memory use."""
    try:
        with _request("/api/ps", timeout=5) as r:
            return [{"name": m["name"], "size_bytes": m.get("size"),
                     "size_vram_bytes": m.get("size_vram"),
                     "context_length": m.get("context_length")}
                    for m in json.load(r).get("models", [])]
    except ModelUnavailable:
        return []


def version():
    try:
        with _request("/api/version", timeout=5) as r:
            return json.load(r).get("version")
    except ModelUnavailable:
        return None


def embed(texts, model=None):
    """Unit-length embedding vectors for texts, from the local embedding model."""
    model = model or config.EMBED_MODEL
    with _request("/api/embed", {"model": model, "input": texts, "keep_alive": "30m"}) as r:
        return json.load(r)["embeddings"]


def process_memory():
    """Measured memory of Ollama's model runner processes. rss_mb = resident memory including
    the memory-mapped weights; footprint_mb = private/dirty memory (context + compute buffers,
    macOS `footprint`). Ollama's own /api/ps size is unreliable for gemma4 in 0.34.4."""
    import re
    import subprocess
    out = []
    try:
        pids = subprocess.run(["pgrep", "-f", "ollama/llama-server"], capture_output=True,
                              text=True).stdout.split()
        for pid in pids:
            fp = subprocess.run(["footprint", "-p", pid], capture_output=True, text=True).stdout
            m = re.search(r"phys_footprint:\s+([\d.]+)\s+(KB|MB|GB)", fp)
            rss = subprocess.run(["ps", "-o", "rss=", "-p", pid], capture_output=True, text=True).stdout
            model = re.search(r"--model \S*sha256-(\w{12})", subprocess.run(
                ["ps", "-o", "args=", "-p", pid], capture_output=True, text=True).stdout)
            if rss.strip():
                mb = (float(m.group(1)) * {"KB": 1 / 1024, "MB": 1, "GB": 1024}[m.group(2)]
                      if m else None)          # footprint is not permitted inside a sandbox
                out.append({"pid": int(pid), "blob": model.group(1) if model else None,
                            "rss_mb": round(int(rss) / 1024),
                            "footprint_mb": round(mb) if mb is not None else None})
    except OSError:
        pass
    return sorted(out, key=lambda r: -r["rss_mb"])
