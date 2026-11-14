# Live demo runbook

Source of the design: ARCHITECTURE.md sections f and g (v2.15). Measured numbers carry their source file. "Target" is a
goal from ARCHITECTURE.md; "not measured" means nobody timed it yet, so time it in the rehearsal and write it here.

## Before the call
- Model: Haiku (`claude-haiku-5-5`). Reason (reviews/step9_results.md): Sonnet validated 6 datasets to Haiku's 7 and both
  passed the injection case. Haiku mean $0.0061 and 28.6 s agent time per run; Sonnet $0.076 and 19.4 s (same file, 15 runs each).
- Check `.env` has the key and `pytest -q -x --tb=line -p no:warnings 2>&1 | tail -15` is green.
- Pick dataset A (should contain registered companies) and dataset B (no businesses) from `outputs/benchmark/final_seed2/compare.md`.
  That table gives outcomes only (for example `sa:corrosion-environment-areas` json: `no_business_entities` on both models).
  Whether an A candidate holds REGISTERED companies is not recorded anywhere: run it once beforehand.
- Keep `data/reference/asic_business_names_trimmed.csv` (committed). For a brand-new source also keep the full register
  zip at `data/raw/reference/business_names_202611.zip` (151 MB of register zips in all, ARCHITECTURE.md section f).

## Where it runs
| Case | Works | Degrades |
|---|---|---|
| My machine, internet | Everything | Nothing |
| My machine, no internet | Extract, resolve, rescore, profiles, trace replay | No LLM, so no onboarding of a new dataset. Phone hotspot is the backup |
| Their machine, internet | Onboarding with their key and model access | Register-confirmed profiles need the registers on disk; sandbox weaker on macOS/Windows (level G is not built, so no effect today) |
| Their machine, no internet | Tests and committed outputs | A walkthrough only |

## Steps
| # | Command | Time | Fallback |
|---|---|---|---|
| 1 Onboard | `python -m src.part2_agent.onboard <url, nsw:dataset-name or file> --max-dollars 0.5` | Target 4 min excluding download. Measured: 40-83 s per source on the six re-onboards (reviews/step5_summary.md); 28.6 s mean over 15 unseen datasets (reviews/step9_results.md); 200.3 s for the 72 MB register incl. download (reviews/step6_summary.md) | Run the same command again: it replays `logs/agent_runs/<id>/trace.jsonl` with no model call. If the portal is down, onboard a local file. If the file is unreadable, `could_not_read` is a valid, honest outcome (two datasets ended this way in the final draw because of a host error and an HTML-only dataset, reviews/step9_results.md). No key or internet: show the committed traces |
| 2 Review | open `configs/<source_id>.review.md` | 1-2 min, human (target) | If the outcome is `needs_review`, code has already abstained the fields with open blocking issues; show them. `approve` refuses it unless `--allow-needs-review` is passed |
| 3 Approve | `python -m src.part2_agent.approve <source_id>` | 1 min (target) | Never hand-edit the config. If wrong, fix the agent or re-onboard |
| 4 Extract | `python -m src.engine.extract <source_id>` | Target under 10 s. Not measured | Refuses an unapproved or changed config; approve again. Show `outputs/observations/` from a six-source run |
| 5 Resolve | `python -m src.part3_resolve.run`, then `python -m src.part3_resolve.graph` | Not measured as a whole. Parts: register row filter 16.9 s; IDF token cache 15.5 s once, 0.3 s afterwards (docs/runbook.md) | Without the full register zip the new source links by identifier and name only; say so. Offline: show `outputs/part3/summary.json` |
| 6 Profile | `python -m src.part4_profiles.profiles` (reads the graph from step 5), then `python -m src.part4_profiles.show <source_id>` | `show` target under 2 s. Not measured; the build step is not measured either | Show `outputs/profiles/graph_profiles.jsonl` for a committed source |

Resolve needs `data/raw/reference/business_names_202611.zip` (it stops with an error naming it). Resolve, profiles and show take no flags: `--help` runs them.

Dataset B stops after step 1 with `no_business_entities` and the evidence the agent cited.

## Things to say out loud
- Costs and timings above are from the logs, not estimates (`logs/llm_calls.jsonl`, `outputs/benchmark/final_seed2/`).
- A `single_source_register_confirmed` profile rests on one register match, not a second source. Its band
  (`accepted` or `loose`) is on the profile. Loose links are lower trust: the T3 register-name tier was 4 right, 5 wrong,
  1 unsure on a tiny sample (reviews/step8_results.md).
- Human hand check of the final benchmark (`handcheck/benchmark_review_fin2{h,s}.csv`, field level only): Haiku 20 of 22 fields right, Sonnet 21 of 24. Every wrong field is on `asic-smsf` (a register of SMSF auditors: a person-level status and registration date mapped to the entity). Mapping rule 20 was added afterwards to fix this and was NOT re-measured. "Outcome correct?" and "key field missed?" were not labelled.

## If something fails
- API error: transient errors retry 3 times (2 s, then 4 s) and show as `api_retry` in the trace; any other error ends
  the run, and a re-run resumes from the trace (ARCHITECTURE.md section b).
- Budget: 40 turns, $1.00 and 4 minutes of agent time end a run as `partial_config` or `incomplete`; neither is hidden.
- Prompt injection in a cell: the benchmark's injection case passed on both models (nothing followed, reviews/step9_results.md).
- QBCC and other live registers change between downloads; committed outputs are the reference.
