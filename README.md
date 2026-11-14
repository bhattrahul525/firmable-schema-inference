# Schema inference and agentic ingestion (Firmable take-home, round 2)

A tool-using agent onboards a dataset it has never seen (URL, CKAN id or file) into a mapping config. One generic,
config-driven engine extracts observations from it. A matcher links records that are the same business, using ASIC
Business Names as bridge evidence, and the links feed profiles. A human approves every config before it runs.

Read next: [ARCHITECTURE.md](ARCHITECTURE.md) (design, v2.15) · [docs/write_up.md](docs/write_up.md) (round-2 write-up)
· [demo/RUNBOOK.md](demo/RUNBOOK.md) (live demo) · [WRITEUP.md](WRITEUP.md) (round-1 write-up) · [DECISIONS.md](DECISIONS.md)
· [docs/runbook.md](docs/runbook.md) (measured timings) · [TIMELOG.md](TIMELOG.md)

## What it does
1. **Onboard** (`src/part2_agent/`): the agent picks its own tools (fetch, sniff, read_table, profile, try_transform,
   validate, critique, ...). Code enforces held-out validation, a critique gate, budgets and the human gate.
   Outcomes: `validated_config`, `needs_review`, `partial_config`, `no_business_entities`, `could_not_read`, `incomplete`.
2. **Extract** (`src/engine/`): generic readers (csv/tsv, xlsx, xls, json/ndjson, zip, gz) plus whitelisted and parametric
   transforms. Generated Python (level G) is designed but not built (see docs/write_up.md).
3. **Resolve** (`src/part3_resolve/`): matcher m2.0 (ABN/ACN checksums, rarity-weighted names, register bridging),
   link table, graph edges, unlinked queue with reasons. `rescore` re-runs a matcher over stored evidence only.
4. **Profiles** (`src/part4_profiles/`): per-field value, confidence and provenance, conflicts shown.
5. **Benchmark** (`src/benchmark/`): seeded draws of unseen datasets, run on Haiku and Sonnet, with an injection case.

Three confidences are never blended: `source_reliability`, `field_confidence`, `link_confidence`.

## Setup (Python 3.10+)
```bash
uv venv --python 3.13 && source .venv/bin/activate      # or: python -m venv .venv
uv pip install -r requirements.txt
cp .env.example .env                                     # put ANTHROPIC_API_KEY in .env (never commit it)
pytest -q -x --tb=line -p no:warnings 2>&1 | tail -15    # full suite; no key or network needed
```
Everything under `outputs/` is committed, so results can be read without running anything. Raw data is git-ignored.

## Onboard an unseen dataset (needs the API key; model is the `LLM_MODEL` setting in `src/llm.py`)
`--mode agent` (the round-2 agent) is the default and the flag is optional. `--mode pipeline` runs the round-1 fixed pipeline.
```bash
python -m src.part2_agent.onboard nsw:find-by-lia-band --source-id find_by_lia_band_demo   # <portal>:<ckan dataset name>
python -m src.part2_agent.onboard https://data.gov.au/...   # a URL, or a local file path
python -m src.part2_agent.onboard my_data.csv --source-id my_data --max-dollars 0.5
```
Useful flags: `--resource-index N` (pin a resource), `--model`, `--max-turns` (default 40), `--max-dollars` (default 1.00),
`--overwrite` (replace an approved config). If `approve` rejects fields, it prints the exact command to re-run: the
reviewer comments go into the new run's task, and the old trace is kept as `trace.round<N>.jsonl` (nothing is replayed). The trace is `logs/agent_runs/<source_id>/trace.jsonl`; running the same
command again replays it without model calls. The config and review packet are written to `configs/<source_id>.yaml`
and `.review.md`.

## Approve, extract, resolve, profile
```bash
python -m src.part2_agent.approve <source_id>            # the human gate; stores the config SHA-256
python -m src.engine.extract <source_id> [--limit N]     # default 1000 rows; refuses an unapproved config
python -m src.part3_resolve.run                          # links, unlinked queue -> outputs/part3/ (needs the full register zip, below)
python -m src.part3_resolve.graph                        # graph nodes/edges -> outputs/part3/ (profiles read these)
python -m src.part3_resolve.rescore --to m1.1            # re-score stored links only (no sources, no model)
python -m src.part4_profiles.profiles                    # builds outputs/profiles/graph_profiles.jsonl
python -m src.part4_profiles.show <source_id>            # profiles containing a mention from that source
```
Order: onboard, approve, extract, resolve, graph, profiles, show. `resolve`, `profiles` and `show` take no flags, so `--help`
runs them (and rewrites the committed outputs).
`approve` refuses a `needs_review` outcome unless `--allow-needs-review` is passed. `rescore` refuses to write if a
human-labelled Y would be demoted or an N promoted. `src.part4_profiles.build` is the round-1 profile builder and
does not read the m2.0 link shape; do not re-run it as is (DECISIONS.md, step 7d).

## Round-1 reproduction (no key needed)
```bash
python -m src.part1_triage.download      # six source files (~140 MB); warns if a file differs from the manifest
```
then `extract` on the six source ids in `configs/` (approved, agent-written). QBCC is a live register, so a fresh
download differs slightly from the committed one; the committed outputs are the reference (see WRITEUP.md).

## Business Names register (resolve needs it: it counts name-word rarity over the full register)
**`resolve` stops with an error if `data/raw/reference/business_names_202611.zip` is missing.** Download the ASIC Business
Names zip from https://data.gov.au/data/dataset/asic-business-names (CC BY 3.0 AU) and save it at that path.
`data/reference/asic_business_names_trimmed.csv` (committed, attribution in `data/reference/ATTRIBUTION.md`) is enough
for the six sources. For a NEW source, put the full register zip at the path in `configs/reference_sources.yaml`
(`data/raw/reference/business_names_202611.zip`) and run `python -m src.engine.row_filter asic_business_names`
(16.9 s measured, docs/runbook.md). Without it the matcher uses identifier and name evidence only.

## Benchmark (costs money; the final draw is run once, unchanged)
```bash
python -m src.benchmark.draw --seed 1 --out outputs/benchmark/dev_seed1                  # dev draw
python -m src.benchmark.run --draw outputs/benchmark/dev_seed1 --pass a --model claude-haiku-5-5
python -m src.benchmark.report --dir outputs/benchmark/dev_seed1 --passes a
```
Seed 2 is the final draw and is refused without `--final`. Results: `outputs/benchmark/final_seed2/compare.md` and
`reviews/step9_results.md`. Hand check: Haiku 20 of 22 fields right, Sonnet 21 of 24, all errors on `asic-smsf` (SMSF auditors: person-level status and date mapped to the entity). Rule 20 was added afterwards to fix it and was not re-measured.

## Where things are
| Area | Code | Outputs |
|---|---|---|
| Part 1 triage (no LLM) | `src/part1_triage/` | `outputs/part1_shortlist.csv` |
| Agent, engine | `src/part2_agent/`, `src/engine/` | `configs/`, `outputs/observations/`, `outputs/rejects/` |
| Resolve | `src/part3_resolve/` | `outputs/part3/` (`links.jsonl`, `unlinked_queue.jsonl`, `graph_*.jsonl`, `summary.json`) |
| Profiles | `src/part4_profiles/` | `outputs/profiles/graph_profiles.jsonl` |
| LLM calls | `src/llm.py` (the only file importing `anthropic`) | `logs/llm_calls.jsonl` (model, tokens, cost, seconds, `round`) |
| Hand checks | `handcheck/` | sheets as labelled, plus result files |

## Honest limits (numbers and sources in docs/write_up.md)
- m2.0 link precision rests on 18 new labels, with wide intervals; the loose band is weak. Labels are not independent.
- The final benchmark hand check is field-level only (20/22 Haiku, 21/24 Sonnet); rule 20 was added after it and not re-measured.
- Companies register, ABR lookup, `renamed_to` / `trustee_for` edges and the level-G sandbox are designed, not built.
- Sampled extraction (default 1,000 rows per source), not full files.
- Source licences: carried in each observation; an `unknown` licence is flagged. ACT's is "Other". Check terms before reuse.
- If `git push` fails on `outputs/observations/` (about 67 MB), run `git config http.postBuffer 524288000`.
