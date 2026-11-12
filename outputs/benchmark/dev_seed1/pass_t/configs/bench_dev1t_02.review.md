# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0633, 20.06s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_02/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: name of successful company
2. `entity.abn` ← `ABN`: ABN

## Left unmapped (not guessed)

- `Commissioners allocation $`: credit amount, no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 46, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. Name is mapped to legal_name and ABN uses the abn transform, with ABN as record_id. The allocation amount is correctly left unmapped. The only gap is that entity_type could have been derived from the name suffix.
  - [advisory] `entity.entity_type`: Every example name ends in 'Limited' or 'Ltd', so entity_type_from_suffix would have supported 'company'. Because the config has no entity_type mapping, every row is recorded as 'unknown'. (suggested: Add entity_type_from_suffix on the Name column. Rule 7 allows this because the source has no explicit entity type column.)
  - [advisory] `observed_at`: The sheet is a 2018-19 allocation list, but observed_at is the resource's last-modified date (2024-07-11). This may not be when the source stated the claim. Using it is acceptable under the rules. (suggested: Keep from_metadata. Note the discrepancy in the source reliability basis, or use a statement date if the source provides one.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Accelerate Resources Limited` → `Accelerate Resources Limited`; `Alloy Resources Limited` → `Alloy Resources Limited`; `Apollo Consolidated Limited` → `Apollo Consolidated Limited`
- `entity.abn<-ABN`: `33617821771` → `33617821771`; `20109361195` → `20109361195`; `13102084917` → `13102084917`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
