#!/bin/bash
# Samples system memory (wired + active + compressed pages) and the Ollama runner processes
# every second while a command runs. Usage: scripts/measure_memory.sh <command...>
set -u
cd "$(dirname "$0")/.."
PAGE=$(sysctl -n hw.pagesize)
used_mb() { vm_stat | awk -v p=$PAGE '/Pages active/{a=$3}/Pages wired down/{w=$4}/occupied by compressor/{c=$5}END{printf "%d", (a+w+c)*p/1048576}'; }
runner_mb() { local t=0; for pid in $(pgrep -f "ollama/llama-server"); do r=$(ps -o rss= -p $pid); t=$((t + r)); done; echo $((t / 1024)); }
BASE=$(used_mb); PEAK=$BASE; RPEAK=0
"$@" & CMD=$!
while kill -0 $CMD 2>/dev/null; do
  u=$(used_mb); r=$(runner_mb)
  [ "$u" -gt "$PEAK" ] && PEAK=$u
  [ "$r" -gt "$RPEAK" ] && RPEAK=$r
  sleep 1
done
wait $CMD
echo "memory: system used before=${BASE} MB, peak=${PEAK} MB (delta +$((PEAK - BASE)) MB); Ollama runners peak RSS=${RPEAK} MB"
