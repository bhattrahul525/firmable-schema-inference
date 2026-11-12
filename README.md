# Schema inference and agentic ingestion (Firmable take-home)

One generic extraction engine, an agent that writes the mapping config for each new source, a link table that
decides which records are the same business, and 50 transparent company profiles. Written answers are in
[WRITEUP.md](WRITEUP.md); decisions and their reasons are in [DECISIONS.md](DECISIONS.md); ideas for later are in
[NEXT.md](NEXT.md); the time log is [TIMELOG.md](TIMELOG.md).

## Run it from a clean checkout (about 8 minutes, no API key needed)

Needs Python 3.10+ and [uv](https://docs.astral.sh/uv/) (or plain `python -m venv`).

```bash
uv venv --python 3.13 && source .venv/bin/activate
uv pip install -r requirements.txt
python -m unittest discover tests                       # 37 tests, under a second

python -m src.part1_triage.download                     # fetches the 6 source files (~140 MB, 1-3 min)

# Part 2: run the generic engine over the six APPROVED, agent-written configs in configs/
for pair in asic_credit_licensee:10000 qld_health_contracts_2023_24:10000 wa_tenders_awards_2023_24:10000 \
            vic_liquor_licences:5000 qbcc_licensed_contractors:5000 act_notifiable_invoices:5000; do
  python -m src.engine.extract ${pair%%:*} --limit ${pair##*:}
done

python -m src.part3_resolve.run                         # links, unlinked queue, entities
python -m src.part3_resolve.rescore --to m1.1           # re-score the links with a newer matcher (no sources read)
python -m src.part4_profiles.build                      # 50 profiles + source-deletion test
```

Everything in `outputs/` is already committed, so you can read the results without running anything.
Re-running the commands above regenerates them (the engine is deterministic for identical inputs; see the caveat below).

**Reproducibility caveat (measured):** the QBCC register is live. A fresh download on 2026-11-12 had 206,595 rows against
206,548 when we onboarded, so a clean re-run gave 268 accepted links / 41 entities instead of 266 / 40 (47 of the 50
hand-checked links still appear). `download` prints a WARNING when a file differs from `outputs/part1_sources_manifest.json`
and leaves that committed manifest unchanged (`--refresh-manifest` overwrites it). Every observation also carries a fresh
`ingested_at`, so those files differ line by line. **The committed outputs are the reference.** The whole sequence above
ran in 24 seconds on a clean clone.

### The agent (needs `ANTHROPIC_API_KEY` in `.env`; costs cents)

```bash
cp .env.example .env   # then put your key in .env (never commit it)
python -m src.part2_agent.onboard nsw:find-by-lia-band      # an UNSEEN dataset: <portal>:<ckan dataset name>
python -m src.part2_agent.onboard --file my_data.csv        # or a local file (licence recorded as 'unknown', flagged)
python -m src.part2_agent.approve find_by_lia_band          # the human gate; rejected fields are revised on the next onboard
python -m src.engine.extract find_by_lia_band               # only works once approved
```

**Warning:** `onboard` on an already-approved source overwrites its config and resets its approval. Do not re-run it on
the six unless you intend to re-review them. The model is set in `src/llm.py` (`LLM_MODEL` env var, default Haiku).

## What is where

| Part | Code | Main outputs |
|---|---|---|
| 1 Discovery and triage (deterministic, no LLM) | `src/part1_triage/` | `outputs/part1_shortlist.csv` (50 ranked), `handcheck/part1_fp_result.json` |
| 2 Engine | `src/engine/` (readers, 12 whitelisted transforms, config + approval lock, extractor) | `outputs/observations/*.jsonl`, `outputs/rejects/*.jsonl` |
| 2 Agent | `src/part2_agent/` (inspect, profile, propose x2, validate, revise, critique, packet, approve) | `configs/*.yaml` (agent-written), `configs/*.review.md`, `configs/*.approval.json`, `logs/agent_runs/` |
| 3 Entity identification | `src/part3_resolve/` | `outputs/part3/links.jsonl`, `unlinked_queue.jsonl`, `entities.jsonl`, `handcheck/part3_link_result.json` |
| 4 Profiles | `src/part4_profiles/` | `outputs/profiles/profiles.jsonl`, `outputs/profiles/summary.json` |
| LLM calls | `src/llm.py` (the only file that imports `anthropic`) | `logs/llm_calls.jsonl` (model, tokens, cost, seconds per call) |
| Hand-check materials | `handcheck/` | the sheets exactly as labelled, plus result JSON |

The six sources are listed in `sources.yaml` (which files, not how to map them). `outputs/part1_sources_manifest.json`
records the licence, dates and SHA-256 of each downloaded file. Raw data is git-ignored (`data/raw/`).

## Headline numbers (all measured; details and caveats in WRITEUP.md)

- Part 1: 2,440 de-duplicated datasets from 5 portals, 50 shortlisted. Hand-checked 20 at random: **14 yes, 5 no, 1 unsure,
  false positive rate 26.3%** (30% if the unsure one counts as wrong).
- Part 2: 6 configs written by the agent, 4-7 LLM calls and $0.009-0.032 each (Haiku 5.5). 41 field verdicts across all
  review rounds, 2 wrong (both WA name fields). Total API spend for the whole project: **$0.17** (computed from list prices).
- Part 3: 266 accepted links (40 businesses) and 119 looser links. Hand-checked 50 (one per distinct business and source pair):
  accepted 23 yes / 0 no / 7 unsure of 30; looser 20 / 0 / 0 of 20. **Precision at the 0.80 threshold: 100% if unsure is
  excluded (95% interval 86-100%), 76.7% if unsure counts as wrong.** The sample is narrow (see WRITEUP.md).
- Part 4: 50 profiles; 9 have an unresolved legal name (shown, not guessed).

## Known issues and honest limits

- **Configs were made with Haiku 5.5, not Sonnet.** Re-running on Sonnet would mean re-reviewing all six; not done.
- **WA Tenders has no usable name or ID**, so none of its records can be linked (all 5,817 are in the unlinked queue).
- Agent output varies between runs (two ASIC runs differed on date mapping; VIC lost `address.full` in the regenerated run).
  The approval hash pins the exact config that was reviewed.
- Part 3 evidence is narrow: 42 of the 50 hand-checked links are ACT invoices against QLD Health contracts.
- Source reliability numbers are model judgements, not measurements.
- Source licences: five are Creative Commons; the ACT dataset's licence is "Other" and is **flagged** on every one of its
  observations. We used all six for this assignment only; check terms before reuse.
- `outputs/observations/` is about 67 MB. If `git push` fails with HTTP 400, run `git config http.postBuffer 524288000`.
