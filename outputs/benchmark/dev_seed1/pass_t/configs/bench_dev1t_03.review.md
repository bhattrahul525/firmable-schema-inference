# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0696, 17.34s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_03/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SchoolName` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SchoolName`: school name
2. `entity.abn` ← `ABN`: ABN

## Left unmapped (not guessed)

- `Fin_Period`: financial period
- `LoadDate`: load timestamp

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. SchoolName maps to legal_name and ABN uses the abn transform, with SchoolNumber as the record_id. All columns are accounted for. The remaining points are advisory only.
  - [advisory] `entity.entity_type`: Every row is a school, and schools are organisations (in Victoria, government schools). The source has no explicit entity type column, and the names carry no company suffix, so the engine records 'unknown'. This follows rules 7 and 18, but the type stays unknown. (suggested: Leave it unmapped, as the rules require. Optionally note in the reason that the dataset appears to hold only government schools, but do not guess the type.)
  - [advisory] `Fin_Period`: Fin_Period (e.g. 201506) states the financial period the data covers. It could inform observed_at or valid_from/valid_to, but it is listed as unmapped. That is acceptable under the rules. (suggested: Keep it unmapped. Optionally use LoadDate as a per-row statement date for observed_at, if the metadata timestamp is judged less reliable.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SchoolName`: `Warrandyte Primary School` → `Warrandyte Primary School`; `Bacchus Marsh Primary School` → `Bacchus Marsh Primary School`; `Cudgee Primary School` → `Cudgee Primary School`
- `entity.abn<-ABN`: `89340494951` → `89340494951`; `61829351598` → `61829351598`; `42294705386` → `42294705386`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
