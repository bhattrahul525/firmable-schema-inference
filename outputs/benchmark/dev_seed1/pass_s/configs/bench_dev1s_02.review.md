# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0641, 17.46s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_02/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: name of successful applicant
2. `entity.abn` ← `ABN`: ABN

## Left unmapped (not guessed)

- `Commissioners allocation $`: credit amount, no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. Name and ABN map to the right fields, and the allocation amount is correctly left unmapped. The only points are advisory.
  - [advisory] `entity.entity_type`: Every row is emitted as entity_type 'unknown' with no source column, although all names end in 'Limited' or 'Ltd', which suggests a company. The default is safe under the ontology, but the mapping carries no richer signal. (suggested: Optionally derive 'company' from a Limited/Ltd suffix as a flagged L1 derivation. Otherwise keep 'unknown'.)
  - [advisory] `entity.legal_name<-Name`: The source is a list of successful grant applicants. The Name column may be the name the applicant used, not necessarily the registered legal name. The examples show registered-style names, so this is only a caveat. (suggested: Lower the field_confidence for legal_name, or confirm the name against ABN lookup data later.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Ausmon Resources Limited` → `Ausmon Resources Limited`; `Barton Gold Holdings Limited` → `Barton Gold Holdings Limited`; `Bmg Resources Limited` → `Bmg Resources Limited`
- `entity.abn<-ABN`: `88134358964` → `88134358964`; `36633442618` → `36633442618`; `96107118678` → `96107118678`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
