# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0055, 26.21s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_02/trace.jsonl`.
- Evidence the agent gave at finish (its words): Workbook has 9 sheets, one per financial year (2017-18 to 2024-25) plus a version sheet. Config reads only the 2024-25 sheet (31 rows, 3 columns: Name, ABN, Commissioners allocation $). ABN passes checksum for all sampled rows and is unique. Validation: 0 hard failures, 45 observations, 0 rejected values.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 2 | `Name` | `entity.trading_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: Column is labelled ABN; values are 11-digit and pass checksum.
2. `entity.trading_name` ← `Name`: Company name of the allocation recipient. Values carry suffixes such as Limited/Ltd and look like registered names, but the column is not labelled as registered name, so mapped to trading_name per rule 5 at 0.6; downstream reconciliation may treat it as possibly legal name.

## Left unmapped (not guessed)

- `Commissioners allocation $`: Credit amount allocated; no ontology field for grant or allocation amounts.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking meaning errors. The ABN is mapped to entity.abn, the recipient name is mapped to trading_name as rule 5 requires, and the allocation amount is correctly left unmapped. The remaining points are advisory: the name caveat and the missing mapping_confidence and source_reliability.
  - [advisory] `entity.trading_name<-Name`: The Name values carry company suffixes such as 'Limited' and 'Ltd' and read like registered names. The config follows rule 5 correctly, since the column is not labelled as a registered name, but the caveat that it may be the legal name is not recorded anywhere. (suggested: Keep the trading_name mapping. Record mapping_confidence at 0.6 or lower and note in the config that the values look like registered names, so downstream reconciliation can weigh them.)
  - [advisory] `entity.trading_name<-Name`: The config has no mapping_confidence and no source_reliability for this claim, though rule 14 and rule 16 call for both. (suggested: Add mapping_confidence (about 0.5 to 0.6, since the column meaning is inferred) and a source_reliability with a short basis, such as a government allocation register being reliable on who was allocated funds but not on how names are registered.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `96107118678` → `96107118678`; `17653132828` → `17653132828`; `40119031864` → `40119031864`
- `entity.trading_name<-Name`: `Bmg Resources Limited` → `Bmg Resources Limited`; `Cosmo Metals Limited` → `Cosmo Metals Limited`; `Dreadnought Resources Limited` → `Dreadnought Resources Limited`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
