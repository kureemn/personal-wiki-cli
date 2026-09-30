#!/bin/bash
# Offline demonstration: run with the internet DISCONNECTED (turn Wi-Fi off first).
#   ./scripts/offline_demo.sh
# Everything printed is saved to evidence/offline/<label>-<timestamp>/transcript.txt, and the
# four ask-mode evidence cards to .../ask/.  Takes about 5-8 minutes on an M1 Pro.
#
# Variant used for a sandboxed run (network blocked by macOS for the CLI AND the Ollama server):
#   LABEL=sandbox-no-network sandbox-exec -f scripts/no-internet.sb ./scripts/offline_demo.sh
set -u
cd "$(dirname "$0")/.."
LABEL="${LABEL:-wifi-off}"
OUT="evidence/offline/${LABEL}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
exec > >(tee "$OUT/transcript.txt") 2>&1
section() { echo; echo "════════ $* ════════"; }
run() { echo "\$ $*"; "$@"; }

section "0. Device and network state"
date; sw_vers | tr '\n' ' '; echo
echo "chip: $(sysctl -n machdep.cpu.brand_string), RAM: $(( $(sysctl -n hw.memsize) / 1073741824 )) GB"
networksetup -getairportpower en0 2>/dev/null || true
if curl -sS -m 5 -o /dev/null https://www.google.com 2>/dev/null; then
  echo "!! INTERNET IS REACHABLE. Turn Wi-Fi off / unplug Ethernet and rerun."; exit 1
else
  echo "internet check: https://www.google.com is UNREACHABLE (expected for this demo)"
fi

section "1. Restart the local Ollama server (weights load from local disk only)"
pkill -f "ollama serve" 2>/dev/null; sleep 2
( ollama serve > "$OUT/ollama-server.log" 2>&1 & )
for i in $(seq 1 30); do curl -s -m 1 localhost:11434/api/version >/dev/null && break; sleep 1; done
run ollama --version
run ollama list

section "2. Help (a fresh CLI process for every command)"
run ./wiki --help

section "3. Status: model, runtime, device"
run ./wiki status

section "4. Ingest all sources (unchanged -> no duplicates, no model call)"
run ./wiki ingest vault/raw

section "5. Ingest one source with local Gemma (reviewed note -> draft goes to review queue)"
run ./wiki ingest "vault/raw/Berkeley Network Tracker README.md" --force

section "6. Vault check: links, headings, unchanged originals"
run ./wiki check

section "7. The four ask-mode tests (evidence cards -> $OUT/ask)"
run ./wiki eval --out "$OUT/ask"

section "8. Search mode: original passages only, no generated answer"
run ./wiki search "row level security policies" -k 3
run ./wiki search "how long did training take" --scope raw -k 3

section "9. Chat mode checks"
printf '%s\n' \
  "what can we do?" \
  "what can you help me with?" \
  "Draft a short plan for how I should prepare my next class assignment README." \
  "make that shorter" \
  "What did my Pac-Man project change about replay capacity, and why?" \
  "By the way, I got an A+ on the Pac-Man assignment." \
  "/exit" | ./wiki chat

section "10. Ask after chat: the A+ claim made in chat is NOT evidence"
run ./wiki ask "What grade did I receive for the Ms. Pac-Man DQN assignment?"

section "11. Measured memory after the run"
run ./wiki status

section "done"
echo "saved: $OUT/transcript.txt and $OUT/ask/"
date
