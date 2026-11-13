#!/bin/bash
cd "$(dirname "$0")" || exit 1
START=${1:-1}
mkdir -p chain/out
[ "$START" -eq 1 ] && rm -f chain/STOP.txt
EFF=""
claude --help 2>&1 | grep -q -- '--effort' && EFF="--effort high"
DENY=("Bash(git add:*)" "Bash(git commit:*)" "Bash(git push:*)" "Bash(git reset:*)" "Bash(git checkout:*)" "Bash(git switch:*)" "Bash(git rm:*)" "Bash(git clean:*)" "Bash(git stash:*)" "Bash(git merge:*)" "Bash(git rebase:*)" "Bash(git restore:*)" "Read(./.env)" "Edit(./.env)")
check() { # n rc
  echo "stage $1 exit $2 $(date)" | tee -a chain/out/log.txt
  if [ "$2" -ne 0 ]; then echo "stage $1 failed, see chain/out" | tee chain/STOP.txt; exit "$2"; fi
  if [ -f chain/STOP.txt ]; then echo "stage $1 asked for a planning decision: see chain/STOP.txt"; exit 3; fi
}
run() { # n file model effort budget extra-deny
  [ "$1" -lt "$START" ] && return 0
  echo "== stage $1 $2 $(date)" | tee -a chain/out/log.txt
  claude -p "$(cat chain/$2.md)" --model "$3" $4 --permission-mode acceptEdits --max-budget-usd "$5" \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash" --disallowedTools "${DENY[@]}" $6 > "chain/out/$2.txt" 2>&1
  check "$1" $?
}
run 1 01_review claude-opus-5-5 "$EFF" 5 "Edit"
run 2 02_fixes claude-sonnet-5-5 "" 3 ""
run 3 03_cmds claude-sonnet-5-5 "" 1 ""
if [ "$START" -le 4 ]; then
  echo "== stage 4 final benchmark $(date)" | tee -a chain/out/log.txt
  bash chain/final_cmds.sh > chain/out/04_exec.txt 2>&1
  check 4 $?
fi
run 5 05_results claude-sonnet-5-5 "" 1 ""
run 6 06_drafts claude-sonnet-5-5 "" 3 ""
echo "chain finished $(date)" | tee -a chain/out/log.txt
