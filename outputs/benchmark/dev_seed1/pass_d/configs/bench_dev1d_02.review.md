# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0050, 23.4s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1d_02/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: Company name of allocation recipient; names end in Limited/Ltd, treated as registered name
2. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated

## Left unmapped (not guessed)

- `Commissioners allocation $`: Credit allocation amount; no ontology field for it

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. Name maps to legal_name, ABN maps through the abn checksum transform, and the allocation amount is correctly left unmapped. The example ABN 88134358964 passes the checksum. The only concern is that the legal_name claim rests on the suffix of the name rather than an explicit registered-name label, which is advisory rather than blocking.
  - [advisory] `entity.legal_name<-Name`: The source column is headed only 'Name'. Nothing in the header says it is the registered name, and the stated reason rests on the Limited/Ltd suffix. Rule 5 requires the data to say the name is registered. The mapping is plausible, but the justification is an inference from the name's form. (suggested: Keep the mapping but record the basis as a suffix-based inference, lower mapping_confidence accordingly, and check the name against the ABN register if a registered-name claim is needed.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Ausmon Resources Limited` → `Ausmon Resources Limited`; `Barton Gold Holdings Limited` → `Barton Gold Holdings Limited`; `Eastern Metals Ltd` → `Eastern Metals Ltd`
- `entity.abn<-ABN`: `88134358964` → `88134358964`; `36633442618` → `36633442618`; `29643902943` → `29643902943`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
