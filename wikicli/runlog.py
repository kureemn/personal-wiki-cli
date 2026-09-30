"""Saved outputs: every command appends a JSON record under runs/ so results can be
inspected later without rerunning the model."""
import datetime as dt
import json
import platform
import socket

from . import config


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def internet_status():
    """Probe the internet (not the local model) so each record shows online/offline state."""
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            socket.create_connection((host, port), timeout=2).close()
            return "reachable"
        except OSError:
            continue
    return "unreachable"


def environment():
    return {
        "time": now(),
        "execution": "local",
        "model": config.MODEL,
        "embed_model": config.EMBED_MODEL,
        "ollama_url": config.OLLAMA_URL,
        "internet": internet_status(),
        "host": platform.platform(),
    }


def save(mode, record):
    """Append one record to runs/<date>/<mode>.jsonl and return its path."""
    day = dt.date.today().isoformat()
    folder = config.RUNS / day
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{mode}.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps({"mode": mode, **record}, ensure_ascii=False) + "\n")
    return path
