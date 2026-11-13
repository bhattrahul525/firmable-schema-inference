# Final fixes (BLOCKING only)

1. FIXED run.py `main`: removed the seed == 1 refusal. Seed 2 is still gated by draw.py (`--final`), untouched.
2. FIXED run.py: draw name comes from the seed (`dev1` for seed 1, `fin<seed>` otherwise). It is used for source ids,
   the review sheet name (`collect`) and injection ids (`run_injection(draw_name=)`). Dev ids stay `bench_inj<pass>_*`.
   `main` now exits if any run dir for the draw already exists ("use a new --pass label").
3. NOT FIXED, DECISION (7th pool slot of the final draw). Reason in chain/STOP.txt.
4. NOT FIXED, DECISION (frozen conditions vs the dirty tree and the chain). Reason in chain/STOP.txt.

Files changed: src/benchmark/run.py, tests/test_benchmark.py (the seed-1-only test replaced by one test for the model
refusal and the taken-run-dir refusal), chain/STOP.txt, reviews/final_fixes.md.
Benchmark draw, seeds, prompts and configs: unchanged. Seed 2 and .env: not touched.
Tests: 2 for the changed rule (1 test with 2 cases); test_benchmark.py 36 passed; full suite 579 passed.
