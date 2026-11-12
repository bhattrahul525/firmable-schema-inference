# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0050, 28.91s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_03/trace.jsonl`.
- Evidence the agent gave at finish (its words): 1,540 rows, key SchoolNumber+Fin_Period unique. ABN parse rate 100% on sampled rows (5 eight-digit values skipped as not 11 digits). Validate on 300 held-out rows: 0 hard failures, 0 rejected values.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: Column holds 11-digit ABNs; checksum validated.

## Left unmapped (not guessed)

- `SchoolName`: School name is not stated to be the registered legal name or a trading name; left out rather than guessed.
- `SchoolNumber`: Internal school number; used in record_id.
- `Fin_Period`: Financial period label; not a stated validity date of the claim.
- `LoadDate`: Load timestamp of the extract, not a per-row statement date.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber', 'Fin_Period'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN mapping and the unmapped-column reasoning look sound, but the legal_name mapping is blocking because the source does not state a registered name. The observed_at source and the required envelope fields need confirmation.
  - [blocking] `entity.legal_name<-SchoolName`: SchoolName is mapped to entity.legal_name, but the ontology defines legal_name as the name as registered. The config's own reason admits the school name is not explicitly stated as the registered name, so the mapping asserts a registered-name claim the source does not make. (suggested: Remove this mapping or map SchoolName to entity.trading_name (or a source-stated name field) instead. Only map to legal_name if the dataset explicitly states the registered name.)
  - [advisory] `observed_at`: The config says observed_at comes from resource_last_modified, but the emitted observed_at values (2026-11-10) do not match any such metadata and fall after the 2015 LoadDate values. They look like the engine run time, which belongs in ingested_at. (suggested: Confirm the source of observed_at against the CKAN resource metadata and record the actual resource_last_modified value. Keep the engine run time in ingested_at.)
  - [advisory] `observation envelope`: The example observations show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible, although the ontology requires them on every record. (suggested: Confirm that every emitted observation carries all required envelope fields. Set licence to 'unknown' and flag it if the dataset metadata has no clear licence.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `35954747085` → `35954747085`; `88819505004` → `88819505004`; `89340494951` → `89340494951`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
