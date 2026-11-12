#!/bin/sh
# Repo cleanup audit (round2-unattended, 2026-11-13). NOT executed automatically. Review, then run by hand.
# Untracks generated/replay artifacts that the benchmark/agent code can recreate; does not delete any file
# on disk (--cached only). No commit command included — review the staged removal and commit yourself.
#
# NOT included here (marked UNSURE in the audit, needs a human decision, not untracked):
#   - logs/agent_runs/{act_notifiable_invoices,asic_credit_licensee,qbcc_licensed_contractors,
#     qld_health_contracts_2023_24,vic_liquor_licences,wa_tenders_awards_2023_24}/   (71 files) --
#     traces for the 6 real Part 2 onboarding runs; may be the only evidence for the
#     step-count/cost/wall-clock-per-source and checkpoint/resume claims in the write-up.
#   - logs/agent_runs/find_by_lia_band_agent*/ and find_by_lia_band/   (53 files) --
#     traces of the agent's revision rounds (round 0, r1, r2) behind configs/find_by_lia_band_agent*.yaml;
#     may be the only evidence of the self-validation/self-revision loop the brief requires.
#   - outputs/benchmark/dev_seed1/pass_*/{results.csv,results.jsonl,results.md,run_status.json,
#     injection.json}   (40 files) -- per-pass evidence tables; compare.md/csv/json already
#     aggregate all 8 passes, so keeping all 8 passes' raw tables too may be redundant, but
#     pruning to "keep only the latest pass" is a curation call, not a mechanical untrack.

# logs/agent_runs/bench_dev1*/ + bench_inj*/ : 505 files, UNTRACK
# Raw per-run traces (trace.jsonl, downloads.json, split.json, table_state.json, input.json) for
# 8 benchmark dev-draw passes (a-f, s, t) + their injection pairs. Superseded by
# outputs/benchmark/dev_seed1/{results.*,compare.*}; regenerable by re-running src/benchmark/run.py.
git rm -r --cached 'logs/agent_runs/bench_*'

# outputs/benchmark/dev_seed1/pass_*/configs/ : 144 files, UNTRACK
# Agent-proposed BENCHMARK configs (never the real configs/ used by the engine -- CLAUDE.md is explicit
# that benchmark configs never go to configs/). Regenerable by re-running the benchmark passes.
git rm -r --cached 'outputs/benchmark/dev_seed1/pass_*/configs/*'

# outputs/benchmark/dev_seed1/pass_*/logs/ : 106 files, UNTRACK
# Raw subprocess stdout/stderr per benchmark run. Regenerable by re-running the benchmark passes.
git rm -r --cached 'outputs/benchmark/dev_seed1/pass_*/logs/*'
