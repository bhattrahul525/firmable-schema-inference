# Submission review (read-only, 2026-11-14)

Reviewer stance: hiring reviewer deciding whether this is submission-worthy. Scope was sampled as briefed: README,
ARCHITECTURE, DECISIONS, docs/, demo/, CLAUDE.md, .gitignore, src/part2_agent core files, and the rest of src/ by
structure. No LLM calls and no onboarding or benchmark runs. Nothing was modified except this file.

State checked: branch `rehearsal-scratch` = `main` = `origin/main` = `d6f3073`. Untracked: `configs/rehearsal_*`,
`logs/agent_runs/rehearsal_*`. Modified: `logs/llm_calls.jsonl` (+37 lines).

## Summary of checks

| Check | Result |
|---|---|
| Secrets | Clean. `.env` was never tracked and is not in history. The only key-shaped string in history is the test fixture `sk-ant-api03-TESTSECRETKEY…` |
| Tests | **582 passed, 40 subtests passed, 0 skipped, 0 failed, 24.5 s** (one run, so flakiness was not tested) |
| Cost numbers | Match the log at HEAD: round 1 $0.166 / 60 calls, round 2 $5.558 / 1,769 calls, total $5.725 |
| Benchmark outcome numbers | Consistent across write_up, step9_results and RUNBOOK: 13 validated / 12 no_business_entities / 4 could_not_read / 1 partial (Haiku + Sonnet) |
| Benchmark hand check | Sheets hold it: Haiku 20 of 22 fields right, Sonnet 21 of 24. **No doc reports it** (see B5) |
| README CLI vs onboard `--help` | Match (`source` accepts `<portal>:<id>`, a URL or a file path; flags as listed) |
| Demo path onboard → show on a NEW dataset | **Breaks** at resolve and profile (B1–B3), and the rejection loop is broken (B4) |

---

## [BLOCKING]: fix before submitting

**B1. `resolve` crashes on a clean clone: it needs the 72 MB register zip, which nothing downloads.**
`src/part3_resolve/idf.py:73` calls `raw.stat()` on `data/raw/reference/business_names_202611.zip` *before* it looks at
the cache. That file is git-ignored and `part1_triage.download` does not fetch it. Verified:
`register_counts(Path('missing.zip'))` raises `FileNotFoundError`. This contradicts README.md:66-69 ("the trimmed CSV
is enough for the six sources", "without it the matcher uses identifier and name evidence only") and the RUNBOOK
"Their machine" row (demo/RUNBOOK.md:21). The brief requires the README path to work from a clean checkout, or the
README must say it is broken.
*Fix:* commit `data/cache/bn_token_counts.json` (8.2 MB, derived from CC BY 3.0 AU data, attribution already present),
and in `register_counts` read the cache when the raw file is absent (check the stamp only when the raw file exists).
This keeps the IDF weights, and so `GENERIC_MIN_WEIGHT` 14.02, identical. Otherwise state the required download in
the README.

**B2. A newly onboarded source never reaches resolve, the graph or profiles.** The source list is hard-coded to the
six: `src/part3_resolve/run.py:29-30`, used by `run.py:104`, `graph.py:29,48,104`, `idf.py:60-63`,
`handcheck.py:33` and `src/engine/row_filter.py:27,58` (its docstring at row_filter.py:5 says "the six approved
sources"). So demo step 6, `show <new_source_id>`, prints "0 profile(s)" whatever the data holds. This contradicts
ARCHITECTURE.md:324 and :329 ("Profiles count ANY onboarded source"), ARCHITECTURE.md:403 ("For A it always shows at
least one profile"), and README.md:67-69 / RUNBOOK.md:31 ("for a NEW source run row_filter"). Nobody has run steps
4-6 on a new source: the rehearsal stopped at approve.
*Fix:* derive the list from data, e.g.
`SOURCES = sorted(p.stem for p in Path("outputs/observations").glob("*.jsonl") if p.stem not in reference_sources())`.
Say in DECISIONS that adding a source shifts the mention IDF counts, so existing links can move. Then rehearse
onboard → approve → extract → row_filter → resolve → graph → profiles → show once on a fresh file.

**B3. The graph step is missing from README and RUNBOOK, so profiles read a stale graph.**
`python -m src.part3_resolve.run` writes links, the queue and summary only. `run.py` never imports or calls `graph`,
yet README.md:49 says it writes the graph. `src/part4_profiles/profiles.py:144-145` reads `graph_nodes.jsonl` /
`graph_edges.jsonl`, which only `python -m src.part3_resolve.graph` (graph.py:188) writes.
*Fix:* add `python -m src.part3_resolve.graph` between resolve and profiles in README.md:49-51 and
demo/RUNBOOK.md:31-32, or call `graph.main()` at the end of `run.main()`.

**B4. In the default agent mode, a human rejection is lost and the printed next step fails.** (Known issues a and b,
confirmed, and worse than described.)
- (a) Only the round-1 pipeline reads `feedback_pending` (`src/part2_agent/onboard.py:235`). The agent path never
  reads it, and its packet hook deletes it on the next run (`src/part2_agent/agent_hooks.py:812`). **Reproduced in
  the rehearsal:** `configs/rehearsal_au.approval.json` round 1 rejected `entity.industry_code` with a comment. After
  the re-run, `feedback_pending` is gone, the status is `pending_review`, and `configs/rehearsal_au.yaml:56` still
  maps `entity.industry_code`.
- (b) `approve.py:70` prints `onboard <source_id>`. The trace header stores the original `reference`
  (`loop.py:322`), so this raises `TraceMismatch` (`loop.py:338`) for **every** agent source, CKAN ids and URLs as
  well as files. The exception is never caught, so it shows as a raw traceback. Re-running the *original* command
  instead replays the finished trace (`loop.py:260-264`) and revises nothing.
- The docs claim the loop works: approve.py:8-9 and DECISIONS.md:79 ("Rejection comments feed a human-feedback
  revise round on the next onboard run").

*Fix (about 15 lines):* in `onboard_agent`, if the approval holds `feedback_pending`, move the old trace to
`trace.round<N>.jsonl`, start a fresh run, and append the reviewer comments to the task inside a `<data>` block.
Store the reference in `approval.json` so `approve` prints the real command. The minimum alternative is to document
"agent mode: a rejection means re-onboarding from scratch; comments are recorded but not fed back" and fix the
printed command. A live reviewer is likely to say "mark field 3 wrong", so this path will probably be exercised.

**B5. The benchmark hand check is done, but every doc says it is not, and rule 20 was fitted to its errors without
disclosure in the write-up.**
- Stale claims: README.md:78 ("NOT yet filled") and :92, docs/write_up.md:74 and :106, demo/RUNBOOK.md:41,
  reviews/step9_results.md:3 and :42.
- What the sheets show (`handcheck/benchmark_review_fin2{h,s}.csv`):
  - Haiku: 20 of 22 fields right; 6 of 7 validated datasets have 0 wrong fields.
  - Sonnet: 21 of 24 fields right; 6 of 7 reviewed datasets have 0 wrong fields.
  - Every wrong field is on `datagovau:asic-smsf` (`SMSF_STATUS` → entity.status and `SMSF_REG_DT` →
    date_registered, plus `SMSF_REG_DT` → valid_from for Sonnet).
  - The "one of them is probably wrong" line (write_up.md:73-74, QLD supplier directory) is settled: neither
    mapping is marked wrong.
- Rule 20 (`agent_prompt.py:37`, commit d6f3073) was added *after* seeing exactly these errors and was not
  re-measured. DECISIONS.md:204 says so; write_up and README do not.
- The sheets have only a `wrong` column. "Outcome correct?" and "key field missed?" (ARCHITECTURE.md:362-367) were
  not labelled, so state them as not measured.

*Fix:* replace the stale lines with the numbers above, and add one line: "rule 20 was added after this review to fix
the asic-smsf errors; not re-measured".

---

## [SHOULD FIX]

**S1. No committed trace replays at the current code.** Rule 20 changed `agent_prompt.py` and `agent_hooks.py`,
which are part of `code_version` and the prompt hash (`onboard.py:354`). Every committed trace now differs: the six,
asic_business_names, all dev and final benchmark runs, and the injection cases. Only the untracked rehearsal traces
match. README.md:41-42 and RUNBOOK.md:27 ("Run the same command again: it replays") hold only for traces made at
today's code.
*Fix:* catch `TraceMismatch` in `onboard.main` and print its message. Add one README/RUNBOOK line: "traces made
before a prompt or code change refuse to replay by design; open them as files".

**S2. README's first onboard example overwrites a round-1 deliverable.** README.md:36 `onboard nsw:find-by-lia-band`
slugs to `find_by_lia_band`. Its committed config (`configs/find_by_lia_band.yaml`, the round-1 seventh-source test)
is `pending_review`, so the approved-config guard at onboard.py:351 does not protect it.
*Fix:* add `--source-id find_by_lia_band_demo` to the example.

**S3. The register config runs without approval.** `src/engine/row_filter.py:54` and `idf.py:78` use
`load_config_file`, not `load_approved_config`. `configs/asic_business_names` has no approval.json, and
reviews/step6_summary.md:8 says "Not approved". This contradicts README.md:5 ("A human approves every config before
it runs").
*Fix:* run `approve asic_business_names` and switch both call sites to `load_approved_config`, or state the
exception in the README.

**S4. ARCHITECTURE.md is out of sync, against the CLAUDE.md rule.** The last change-log row is 2.15. No row covers
7b-7e2, step 8/9, the default-mode switch (88bd72d) or rule 20 (d6f3073). Stale or contradicted lines:
- :298 says T1r is "(not built)", but it is built in a weaker form (DECISIONS.md:172; summary has 2 T1r links).
- :311-312 lists `renamed_to`, `trustee_for` and a `trust` node without "not built".
- :76 lists a `define_transform` tool that does not exist in src/.
- :209-210 and :248-266 describe level G and the sandbox without "not built".
- :412-414 lists `sandbox.py`, `custom.py`, `abr.py` and `docs/abr_terms.txt`; none exists.
- :331-332 says "expected 45 to 50 of 50 survive"; the actual figure is 2 (see S6).
- :362 names `handcheck/benchmark_review.csv`; the real files are `benchmark_review_fin2{h,s}.csv`.
- :482 says "`--mode` default stays pipeline"; the default is now agent.
- The file is 493 lines against the ~400-line rule.

*Fix:* add a v2.16 row and inline "(not built)" marks; move the step-3b detail in section b to module docstrings.

**S5. DECISIONS.md:8-9 says "Sonnet was never run".** Step 9 ran Sonnet ($1.14), and so did dev passes s, t and g.
*Fix:* scope the sentence to round 1.

**S6. write_up.md:100-102 ships an unresolved "2 vs 1 of 50; check this before quoting either".** Checked with
`labels.load_labels()`: 1 of the 50 round-1 labelled pairs is still a link, and 1 more (check 8, Cantel/Steris) is
refused and allow-listed. So 2 of 50 are scored by m2.0, and 1 of 50 survives as a link.
*Fix:* state exactly that.

**S7. resolve and profiles ignore argv (known issue c, confirmed).** `run.py:103` and `profiles.py:143` have no
argparse, so `--help` runs the whole job and rewrites the tracked `outputs/part3/*` and `outputs/profiles/*`.
`show.py:33` takes `--help` as a source id and prints "0 profile(s)".
*Fix:* `argparse.ArgumentParser(description=__doc__).parse_args()` as the first line of each `main()`; give `show` a
positional argument.

**S8. Rehearsal debris must not be committed.**
- `configs/rehearsal_*` and `logs/agent_runs/rehearsal_*` contain `/Users/rahulbhatt/Downloads/...` and a UK dataset
  with an unknown licence.
- If the modified `logs/llm_calls.jsonl` (+37 rehearsal lines) is committed, write_up §4 totals go stale.

*Fix:* leave them out, or add `configs/rehearsal_*` and `logs/agent_runs/rehearsal_*/` to `.gitignore`. Either revert
the log or re-sum §4.

---

## [NOTE]

- **N1 .gitignore:32** is malformed (`chain/STOP.txtchain/out/`: a missing newline, then duplicates). It works only
  because lines 31 and 33 cover both paths. *Fix:* delete line 32.
- **N2 Regex timer is Unix-only** (`src/engine/transforms.py:131`, `guard.py:97`). On Windows a model-written level-P
  regex is bounded only by the 200-character limit. RUNBOOK.md:21 says "level G is not built, so no effect today",
  which is wrong: P regexes are affected today. *Fix:* reword RUNBOOK.md:21.
- **N3 Budget text is hard-coded** in the harness prompt (`guard.py:6`, `:74`: "$1.00 / 40 turns / 4 minutes").
  `--max-dollars 0.5` (the demo command) caps at $0.50 while telling the model $1.00 (DECISIONS.md:203). The caps
  themselves are enforced in code (`guard.py:249`, checked before each turn; at most one turn plus one critique of
  overshoot). *Fix:* format the prompt from `Limits`.
- **N4 Error handling at the tool boundary is good.** Tool exceptions, malformed results and bad costs become error
  results (`loop.py:394`, `:495`, `:524`). The gaps are `TraceMismatch` (S1) and non-transient API errors, which
  propagate by design (documented).
- **N5 Dead path:** `python -m src.part4_profiles.build` still runs, although README.md:55-56 says not to (it would
  fail on register links). *Fix:* make its `main()` exit with that message (the module is still imported by
  profiles.py, so keep the functions).
- **N6 docs/write_up.md is 1,580 words** (round-1 WRITEUP.md is 1,184). If it is read as the Part 5 deliverable, it
  exceeds "2 pages max". *Fix:* label it a round-2 supplement, or trim §2.
- **N7 TIMELOG.md has no round-2 entries**, and README links it. *Fix:* add a summary row or a pointer to
  reviews/unattended_log.md.
- **N8 Tracked process files** (`CLAUDE.md`, `chain/`, `run_chain.sh`, `reviews/`) show that an unattended
  `claude -p` chain with `acceptEdits` built parts of this and ran the final benchmark. That is honest and arguably a
  plus for an Applied AI role, but keep it deliberately. CLAUDE.md:15 ("Time box: 6 hours") conflicts with
  ARCHITECTURE.md:10 ("no hour budget"). *Fix:* one README line on how AI tooling was used.
- **N9 configs/ mixes the six deliverables** with 10 `find_by_lia_band_agent_*` experiment configs. *Fix:* name the
  six in README (they are in the `run.py:29` list) or move the experiments.
- **N10 Two frozen benchmark logs hold a home-directory path**
  (`outputs/benchmark/final_seed2/pass_{h,s}/logs/bench_fin2{h,s}_05.txt`). Harmless; leave the frozen directory
  untouched.
- **N11 Limitations that are stated honestly:**
  - loose T3 at 0.444 (CI 0.189-0.733);
  - non-independent and partly model-assisted labels;
  - m2.0 precision rests on 18 labels, not the brief's 50;
  - sampled extraction;
  - G, Companies, ABR and renamed_to/trustee_for not built;
  - the Cantel/Steris recall loss.

  A reviewer will still hold "18, not 50" against the submission, but it is disclosed. Licence handling is good:
  CKAN licence carried per observation, `unknown` flagged, ASIC CC BY 3.0 AU attribution beside the trimmed file.
- **N12 Unused modules: none found.** Every src module is imported or is a `__main__` CLI. There are no
  TODO/FIXME markers.

---

## Verdict

**Submit after fixing the blocking items.** The engineering is careful: guards in code, honest measurement, 582
passing tests, cost well under target. But the round-2 headline is "ingest a random dataset live", and that path is
broken after extract. Resolve crashes on a clean clone (B1), ignores the new source (B2) and skips the graph build
(B3). The human-rejection loop silently drops the comment (B4). The docs also under-report the finished benchmark
review and omit that rule 20 was fitted to it (B5). B1-B3 and B5 are small; B4 is about 15 lines, or a doc change.
After fixing them, do one end-to-end rehearsal on a fresh file before the call.
