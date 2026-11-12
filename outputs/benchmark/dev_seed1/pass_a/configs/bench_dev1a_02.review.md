# Review packet (round-2 agent): partial_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **partial_config**.
- 10 model turns, 10 tool calls, $0.0059, 31.83s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_02/trace.jsonl`.
- Evidence the agent gave at finish (its words): Workbook has 9 sheets, one per year, all small. Sheet 2024-25: 31 rows, 3 columns (Name, ABN, Commissioners allocation $). ABN is unique and filled (16 training rows checked); validate passed with 0 failures on 15 held-out rows, ABN parse rate 1.0.
- Reason: Only the 2024-25 sheet is covered by this single-sheet config; the other eight year sheets are not mapped.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: Recipient company name as published in the allocation list (ends in Limited/Ltd); should be checked against ABR before treating as the registered legal name
2. `entity.abn` ← `ABN`: Column is ABN, 11 digits, checksum validated

## Left unmapped (not guessed)

- `Commissioners allocation $`: Dollar credit allocation amount; no ontology field for grants or allocations

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-Name (2017-18 to 2023-24 sheets)`: The reader takes one sheet per config; this config covers only the 2024-25 sheet. The other eight year sheets (2017-18 through 2023-24, including 2022-23 which has a different layout) are not mapped and need their own configs or a multi-sheet reader.
- `observed_at / valid_from`: observed_at uses file modification time as a proxy; the financial-year label (2024-25) is not parsed into valid_from because the sheet itself does not state start/end dates.

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN mapping and the unmapped allocation column are sound, and the ABN checksum holds for the first example row. The main concerns are the unverified 'registered name' claim for Name and an incomplete observation envelope. None of these clearly states something the source does not support, so no blocking issue is raised.
  - [advisory] `entity.legal_name<-Name`: The reason asserts that the allocation recipient name is the registered company name, but nothing in the source supports that. The Name column is a recipient label in a grants/allocation list and could be a trading or short name. The mapping is plausible for these rows (they end in Limited/Ltd) but the claim is unverified. (suggested: Soften the reason to say the value is the recipient name as published, and check it against the ABR register by ABN before treating it as the registered legal name.)
  - [advisory] `observation envelope`: The emitted observations show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are absent from the examples, and the config does not define them. The licence in particular must come from the CKAN metadata. (suggested: Confirm the engine attaches all required envelope fields to every observation, and show them in the examples. Record the licence from CKAN, or 'unknown' with a flag if none is given.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, which is when the file was last changed, not necessarily when the source stated the claim. The sheet is labelled 2024-25, which suggests the allocations relate to a financial year that the envelope does not capture. (suggested: Keep resource_last_modified as observed_at only if documented as a proxy. Consider setting valid_from from the financial-year label (for example 2024-07-01) if the source supports it.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Ausmon Resources Limited` → `Ausmon Resources Limited`; `Bmg Resources Limited` → `Bmg Resources Limited`; `Eastern Metals Ltd` → `Eastern Metals Ltd`
- `entity.abn<-ABN`: `88134358964` → `88134358964`; `96107118678` → `96107118678`; `29643902943` → `29643902943`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
