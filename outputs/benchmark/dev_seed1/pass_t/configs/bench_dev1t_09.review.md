# Review packet (round-2 agent): validated_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0641, 18.5s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_09/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `_blank_1` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `_blank_1`: school name

## Left unmapped (not guessed)

- `_blank_2`: payment amount
- `_blank_3`: payment amount
- `_blank_4`: payment amount

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1521, 'key': ['Parent Voluntary Contributions 2011 to 2013'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is broadly sensible: school names go to legal_name and the payment columns are unmapped. The header-row mishandling produces a bogus 'School Name' entity and a garbled record_id column name, so both need fixing, but neither states anything unsupported about a real entity.
  - [advisory] `entity.legal_name<-_blank_1`: The header row was not consumed as a header. The first record is the real header row (School No, School Name, 2011...), so it is emitted as an entity with legal_name 'School Name'. That value is not an entity name. (suggested: Set header_rows to 2 or skip_rows to 1 so the 'School Name' row is not treated as data.)
  - [advisory] `record_id`: The record_id column is School No, but its header is garbled as 'Parent Voluntary Contributions 2011 to 2013'. The header row also yields the non-unique, non-ID value 'School No'. Uniqueness was not shown to be checked. (suggested: Fix header handling so the column is named School No, run check_unique on it, and fall back to hash_row if it is not unique.)
  - [advisory] `entity.legal_name<-_blank_1`: The mapping treats the school name as the registered legal name, though the source only says it is a school name. This is reasonable for a school list, but the source does not state it is the registered name. (suggested: Keep the mapping with moderate mapping_confidence. Optionally add entity_type_from_suffix or leave entity_type as unknown.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-_blank_1`: `School Name` → `School Name`; `Avenel Primary School` → `Avenel Primary School`; `Bacchus Marsh Primary School` → `Bacchus Marsh Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
