#!/usr/bin/env bash
# Final seed 2 benchmark. Run once from the repo root: bash chain/final_cmds.sh
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=outputs/benchmark/final_seed2

# Refuse to start if this directory already holds a draw or any pass (never re-run an outcome).
if [ -e "$OUT/draw.json" ] || ls -d "$OUT"/pass_* >/dev/null 2>&1; then
  echo "refusing: $OUT already holds run results" >&2; exit 1
fi
mkdir -p "$OUT"

# Record the code state the final draw runs against.
git rev-parse HEAD > "$OUT/commit.txt"
git status --short > "$OUT/status.txt"
git diff HEAD > "$OUT/code.patch"
{ python --version; pip freeze; } > "$OUT/versions.txt" 2>&1

# Draw seed 2 once, never adjusted.
python -m src.benchmark.draw --seed 2 --out "$OUT/draw.json" --final

# One run per model on the same draw (run.py includes the injection case). Baseline is computed automatically.
# Pass h = Haiku, pass s = Sonnet. Note: --session-limit applies per run.py call (each computes its own baseline).
python -m src.benchmark.run --draw "$OUT/draw.json" --pass h --model claude-haiku-5-5 --per-run-dollars 0.50 --session-limit 3.0
python -m src.benchmark.run --draw "$OUT/draw.json" --pass s --model claude-sonnet-5-5 --per-run-dollars 0.50 --session-limit 3.0

# Blank review sheets are written by run.py per pass; this builds the compare table.
python -m src.benchmark.report --dir "$OUT" --passes h s
