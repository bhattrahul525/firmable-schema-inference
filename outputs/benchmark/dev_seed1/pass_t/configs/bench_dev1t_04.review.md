# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1148, 31.67s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_04/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `col_7` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `col_8` | `address.full` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 3 | `col_22` | `entity.abn` | regex_extract(^([\d ]+)$) → abn | W | 0.70 | n/a | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `col_7`: supplier/party name
2. `address.full` ← `col_8`: supplier address
3. `entity.abn` ← `col_22`: party identifier, ABN where present

## Left unmapped (not guessed)

- `col_1`: blank
- `col_2`: government buyer
- `col_3`: government buyer address
- `col_4`: contract title
- `col_5`: contract date
- `col_6`: contract value
- `col_9`: flag
- `col_10`: flag
- `col_11`: procurement method
- `col_12`: contract type
- `col_13`: flag
- `col_14`: flag
- `col_15`: flag
- `col_16`: flag
- `col_17`: flag
- `col_18`: tender number
- `col_19`: category
- `col_20`: contract ref

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 49, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. Government buyer columns (col_2, col_3) are correctly excluded, and the supplier name (col_7) and address (col_8) are correctly mapped. Entity type is left as unknown with no suffix guess. The remaining concerns are advisory: the ABN column is unverified, and col_21 is not accounted for.
  - [advisory] `entity.abn<-col_22`: No example row contains col_22, so the ABN mapping cannot be checked against real values. The reason given ('party identifier, ABN where present') is vague. The regex only accepts digits and spaces, so any 9-digit ACN values in the column would be dropped silently. (suggested: Confirm col_22 holds ABNs from the profile. If it mixes 11-digit and 9-digit identifiers, also map it with the acn transform. Otherwise lower mapping_confidence.)
  - [advisory] `col_21`: col_21 appears in a raw row (value '`') but is not in fields or unmapped, so rule 3 (account for every column) is not met. col_22 is mapped, but col_21 is not accounted for. (suggested: Add col_21 to unmapped with the reason 'stray/junk character'.)
  - [advisory] `col_5`: The contract date (col_5) is left unmapped. It states when the contract started, which could arguably feed valid_from, but it does not describe the entity's name or address claims. Leaving it out is defensible. (suggested: Leave it unmapped, or document the choice in the reason.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-col_7`: `Bidfood Cairns ` → `Bidfood Cairns`; `Taylor Made Enterprises Pty Ltd ` → `Taylor Made Enterprises Pty Ltd`; `Maxwells H20 Services Pty Ltd ` → `Maxwells H20 Services Pty Ltd`
- `address.full<-col_8`: `38 Redden Street, Cairns` → `38 Redden Street, Cairns`; `121 Enmore Street, Manoora QLD ` → `121 Enmore Street, Manoora QLD`; `5 Commercial Place, Cairns QLD ` → `5 Commercial Place, Cairns QLD`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
