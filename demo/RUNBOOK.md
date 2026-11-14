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
| 1 Onboard | `python -m src.part2_agent.onboard <url, nsw:dataset-name or file> --max-dollars 0.5` | Target 4 min excluding download. Measured on the 121-row sample: 31-45 s, $0.007 (re-onboard after a rejection 31 s). Earlier: 40-83 s per source on the six re-onboards (reviews/step5_summary.md); 28.6 s mean over 15 unseen datasets (reviews/step9_results.md); 200.3 s for the 72 MB register incl. download (reviews/step6_summary.md) | Run the same command again: it replays `logs/agent_runs/<id>/trace.jsonl` with no model call. If the portal is down, onboard a local file. If the file is unreadable, `could_not_read` is a valid, honest outcome (two datasets ended this way in the final draw because of a host error and an HTML-only dataset, reviews/step9_results.md). No key or internet: show the committed traces |
| 2 Review | open `configs/<source_id>.review.md` | 1-2 min, human (target) | If the outcome is `needs_review`, code has already abstained the fields with open blocking issues; show them. `approve` refuses it unless `--allow-needs-review` is passed |
| 3 Approve | `python -m src.part2_agent.approve <source_id>` | 1 min (target) | Never hand-edit the config. If wrong, fix the agent or re-onboard |
| 4 Extract | `python -m src.engine.extract <source_id>` | Measured 0.08 s (121-row sample) | Refuses an unapproved or changed config; approve again. Show `outputs/observations/` from a six-source run |
| 5 Resolve | `python -m src.part3_resolve.run`, then `python -m src.part3_resolve.graph` | Measured on the 121-row sample: resolve 0.8 s, graph 0.3 s, row filter 17 s. Parts: register row filter 16.9 s; IDF token cache 15.5 s once, 0.3 s afterwards (docs/runbook.md) | Without the full register zip the new source links by identifier and name only; say so. Offline: show `outputs/part3/summary.json` |
| 6 Profile | `python -m src.part4_profiles.profiles` (reads the graph from step 5), then `python -m src.part4_profiles.show <source_id>` | Measured: profiles 0.2 s, `show` 0.03 s | Show `outputs/profiles/graph_profiles.jsonl` for a committed source |

Resolve needs `data/raw/reference/business_names_202611.zip` (it stops with an error naming it). Resolve, profiles and show take no flags: `--help` runs them.

Dataset B stops after step 1 with `no_business_entities` and the evidence the agent cited.

## Demo command sequence (new source, end to end)
```bash
python -m src.part2_agent.onboard <file, URL or portal:dataset> --source-id <id> --max-dollars 0.5
python -m src.part2_agent.approve <id>
python -m src.engine.extract <id>                      # resolve only reads approved AND extracted sources
python -m src.engine.row_filter asic_business_names --out data/reference/demo_trimmed.csv   # needs the full register zip
export BN_TRIMMED=data/reference/demo_trimmed.csv      # resolve, graph, profiles read this instead of the tracked file
python -m src.part3_resolve.run                        # prints "sources (N): ..." first: check your id is listed
python -m src.part3_resolve.graph
python -m src.part4_profiles.profiles
python -m src.part4_profiles.show <id>
```
Timings (MacBook, Haiku 5.5 agent, 121-row Australian modern slavery sample, 2026-11-15): onboard 31-45 s ($0.007); re-onboard after a rejection 31 s ($0.007); extract 0.08 s; register row filter 17 s (streams the full register zip once); resolve 0.8 s; graph 0.3 s; profiles 0.2 s; show 0.03 s. Machine time for the whole path is about one minute; the approval step is human time. Resolve, graph and profiles read every approved, extracted source (six base sources plus
others; `src/part3_resolve/sources.py`); reference registers are excluded. Without extra sources the six-source results are
unchanged. Skip `--out` and `BN_TRIMMED` to overwrite the tracked trimmed file (the default). Re-running resolve with a new
source also shifts the name-rarity counts, so existing links can move; commit the outputs only if you mean to.

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
