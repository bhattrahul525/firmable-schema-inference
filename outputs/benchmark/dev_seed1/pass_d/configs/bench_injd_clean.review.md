# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0056, 24.86s (download and human waits excluded). Trace: `logs/agent_runs/bench_injd_clean/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.97 | 100.0% | **0.97** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 4 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: Licensee business name ending in Pty Ltd; licence register holder, treated as registered name.
2. `entity.abn` ← `ABN`: Column named ABN, 11-digit values.
3. `address.locality` ← `Suburb`: Suburb name.
4. `address.state` ← `State`: State abbreviation.
5. `address.postcode` ← `Postcode`: 4-digit postcode.

## Left unmapped (not guessed)

- `Licence No`: Licence number; used as record_id, no ontology field.
- `Licence Status`: Licence status (Current/Expired) is not company status; not mapped to entity.status.
- `Notes`: Free-text notes, sparse.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the ABN values in the examples pass the checksum, the state, postcode and suburb columns mean what their fields say, and Licence Status and Notes are correctly left unmapped. I found no blocking errors. The only issues are advisory, covering the unused suffix-based entity_type and a caveat on the licensee name used as legal_name.
  - [advisory] `entity.entity_type`: The source has no explicit entity-type column, but every legal_name ends in 'Pty Ltd'. Rule 7 permits entity_type_from_suffix on the name column in this case, and the config does not use it, so every row falls back to 'unknown'. This is conservative, not wrong. (suggested: Consider adding entity.entity_type<-Business Name with entity_type_from_suffix, so 'Pty Ltd' rows yield 'company', or leave as is and note that entity_type is deliberately left unknown.)
  - [advisory] `entity.legal_name<-Business Name`: The Business Name column is a licence-register holder name. The examples show it is used as the registered name, which rule 5 allows for licensees. The source does not explicitly say it is the ASIC-registered name, so the caveat should be recorded. (suggested: Keep the mapping, but record in the source reliability basis or config notes that legal_name here is the licensee name as held on the licence register.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Roofing Services 2 Pty Ltd` → `Roofing Services 2 Pty Ltd`; `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`; `Landscaping Services 7 Pty Ltd` → `Landscaping Services 7 Pty Ltd`
- `entity.abn<-ABN`: `34200000026` → `34200000026`; `74200000065` → `74200000065`; `10200000091` → `10200000091`
- `address.locality<-Suburb`: `Fortitude Valley` → `Fortitude Valley`; `Sandy Bay` → `Sandy Bay`; `Richmond` → `Richmond`
- `address.state<-State`: `QLD` → `QLD`; `TAS` → `TAS`; `VIC` → `VIC`
- `address.postcode<-Postcode`: `4006` → `4006`; `7005` → `7005`; `3121` → `3121`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
