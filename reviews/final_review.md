# Final review before the seed 2 benchmark (Opus 5.5, high, read-only)

Scope: b058541 (merge of round2-unattended) to d2c2ff8, plus the uncommitted tree (.gitignore, chain/, run_chain.sh).
Serena permission was denied, so the review used Grep/Read. The benchmark was not run. .env and seed 2 were not touched.

## BLOCKING

1. src/benchmark/run.py:127: `main` exits unless `draw["seed"] == 1`, so the final draw cannot run at all. tests/test_benchmark.py:174 asserts
   this refusal and will need to change with the fix.
2. src/benchmark/run.py:131 and :81: source ids and the review sheet are hard-coded to `dev1`. Final runs become `bench_dev1<pass>_NN` in
   logs/agent_runs/ and `handcheck/benchmark_review_dev1<pass>.csv`, and injection runs become `bench_inj<pass>_*` (:100). If a pass label
   a-t is reused, the run either collides with dev traces (TraceMismatch, so the outcome is wrong) or overwrites dev review sheets. Fix:
   take the draw name from the seed (e.g. `fin2`) and refuse a source id whose run dir already exists.
3. DECISION. src/benchmark/draw.py:112/127/34: `make_draw` builds only the dev shape (6 shortlist + one pool dataset for each of 5 format
   classes). ARCHITECTURE.md:348 and reviews/step9_plan.md:4 require 8 shortlist + 7 pool "one from the no-tabular group". The 5 classes
   plus no-tabular make 6 pool slots, so the 7th slot (xml? a second csv?) is not defined anywhere. This must be decided before code is
   written. The seed 1 path must stay byte-identical (tests/test_benchmark.py:119). Rank 38 is already excluded via EXTRA_EXCLUDED.
4. DECISION. Frozen conditions (step9_plan.md:9, "tree must be clean, commit hash recorded") cannot be met as chained. The tree is dirty
   now (.gitignore modified; chain/ and run_chain.sh untracked). run_chain.sh stage 2 edits code and stage 4 runs the benchmark with no
   commit in between, because git is forbidden to the chain. Either stop after stage 2 so the owner can commit, or amend the plan to accept
   "HEAD + recorded code.patch".

## SHOULD FIX

5. DECISION. src/benchmark/run.py:118 and src/part2_agent/guard.py:74: the dev passes ran at $0.50 per run, and the plan sets $0.30. The
   system prompt tells the model "$1.00" whatever the cap is. Final conditions therefore differ from the dev rate published beside them.
   Either keep $0.50 or state the change.
6. src/benchmark/run.py:116: `--baseline` is typed by hand. A wrong value shifts the $3 session limit. The final script should compute it
   with `llm.spend_summary(..., 2)` right before the first run and record it.
7. src/part3_resolve/labels.py:26: `load_labels` reads only the round-1 CSVs. The 18 step 8 labels (handcheck/step8_key.csv, including
   5 N on T3_register_name) are not seen by the rescore gate or by graph `human_label`, so "an N is never promoted" is not enforced for them.
8. src/engine/extract.py:87 and :213: when `when.matches` hits a regex timeout, the row is counted as a `when_not_met` skip. ARCHITECTURE
   section c says a timeout is `Reject("regex_timeout")`, and the skip hides the failure from the parse rate (both the engine and
   try_transform do this).
9. ARCHITECTURE.md:298 says "T1r (not built)", but src/part3_resolve/score.py:124 builds it (one-sided confirmation, 0.95, accepted).
   T1_register_abn (0.98) and the 0.79 unverified-ABN cap (score.py:97) are missing from the tier table. Line 287 still says "offline
   fallback = the two ASIC registers", against v2.15. Line 311-312 list `renamed_to`, `trustee_for` and trust nodes without "not built".
   Steps 7a-7e2 changed the design with no version bump or change-log row (CLAUDE.md architecture rule).
10. .gitignore:32 (uncommitted): `chain/STOP.txtchain/out/` is a malformed line (harmless). The ignores cover only dev_seed1/pass_*, so
    final pass configs/ and logs/ (console output with sample values) will show as untracked. Decide whether to commit or ignore them.
11. src/part3_resolve/handcheck.py:281: the default (no arg) `make`, and `step8`, overwrite the labelled sheets (part3_link_check.csv,
    step8_sheet.csv) without a guard. These labels feed the rescore gate. They are in git, so they are recoverable.

## NOTES

12. Seed 2 is safe: draw.py:165 refuses seed 2 without `--final` (tested at tests/test_benchmark.py:112). No seed 2 draw file exists in
    the repo, outputs/, logs/, handcheck/ or /tmp; the only `"seed": 2` is a temporary test fixture.
13. Secrets: .env is git-ignored and untracked. Only `load_dotenv` reads it (src/llm.py:26). Every log and trace line goes through
    `dumps_redacted` (llm.py:110). `LLM_MODEL` can change `llm.DEFAULT_MODEL` (llm.py:32), but run.py always passes `--model` and the
    critique uses the run's model (agent_hooks.py:596).
14. The held-out split is seeded by source_id (src/part2_agent/agent_table.py:120), and every run downloads live. So Haiku and Sonnet see
    different held-out rows, and possibly different file versions, of the same dataset. State this as a confound in the model agreement;
    record the download sha per run.
15. src/benchmark/report.py:164 and :196: `except Exception: pass` blanks the review examples silently. The sheet should say
    "examples unavailable".
16. DECISION. The m2.0 link precision rests on 18 new labels (reviews/step8_results.md) plus the round-1 labels that carried over. The
    brief asks for 50 at a stated threshold, so the write-up must say this plainly. The loose band is 4 Y / 5 N (0.44).
17. DECISION. The "skip a component with more than one ABN" item in DECISIONS.md (7d) is still open. It is moot after 7e2
    (graph_checks.json has 0 offenders), but it has not been closed.
18. src/part3_resolve/registers.py:100: route 2 stops at the first name that hits the register, even if that hit is refused, so later
    trading names are never tried. This costs recall only, not precision.
19. Step 4a and the finish gate match ARCHITECTURE v2.13/2.14: the regex timer nests and restores, constant is capped at 0.5 with
    evidence `asserted`, `when` is part of `field_def`, blocking refusals do not count toward "refused twice", and approve refuses
    `needs_review` unless `--allow-needs-review` is passed. The tests exercise each rule (test_step4a, test_finish_rules,
    test_step5_approve). The benchmark counts only `validated_config` as validated (report.py:236), so `needs_review` is not inflated.

Safe to run final benchmark: N
