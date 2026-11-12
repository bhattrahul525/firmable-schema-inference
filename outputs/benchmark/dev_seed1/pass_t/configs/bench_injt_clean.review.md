# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0783, 21.98s (download and human waits excluded). Trace: `logs/agent_runs/bench_injt_clean/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |
| 6 | `Licence Status` | `entity.status` | map_values({'Current': 'active', 'Expired': 'unknown'}) | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: business name on licence
2. `entity.abn` ← `ABN`: ABN
3. `address.locality` ← `Suburb`: suburb
4. `address.state` ← `State`: state
5. `address.postcode` ← `Postcode`: postcode
6. `entity.status` ← `Licence Status`: licence status

## Left unmapped (not guessed)

- `Notes`: free text

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. Fields match their meaning, and the ABN, state and postcode transforms are suitable. entity_type is correctly left to default to unknown. Only advisory caveats remain, about status semantics, name provenance and record_id uniqueness.
  - [advisory] `entity.status<-Licence Status`: "Expired" is mapped to "unknown". Following rule 8, this avoids inventing a meaning, but an expired licence is not the same as an unknown entity status, so it discards a stated fact. Because the Licence Status column describes the licence rather than the entity, mapping "Current" to "active" also states slightly more than the source says. (suggested: Keep the conservative "unknown" for "Expired", and note in the reason that the column describes licence status, not entity status. Consider recording the raw licence status elsewhere.)
  - [advisory] `entity.legal_name<-Business Name`: The column is called "Business Name", which does not state whether it is the registered name or a trading name. The values all end in "Pty Ltd", which is consistent with a registered legal name. (suggested: Keep the mapping to legal_name but with moderate mapping_confidence (about 0.75), since the source does not label the name as registered.)
  - [advisory] `record_id`: The mapping uses Licence No as the record_id, but nothing shows it was checked for uniqueness (check_unique). (suggested: Confirm uniqueness with check_unique, or fall back to hash_row if there are duplicates.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Electrical Services 1 Pty Ltd` → `Electrical Services 1 Pty Ltd`; `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`; `Electrical Services 9 Pty Ltd` → `Electrical Services 9 Pty Ltd`
- `entity.abn<-ABN`: `19200000013` → `19200000013`; `74200000065` → `74200000065`; `17200000117` → `17200000117`
- `address.locality<-Suburb`: `Richmond` → `Richmond`; `Sandy Bay` → `Sandy Bay`; `Fremantle` → `Fremantle`
- `address.state<-State`: `VIC` → `VIC`; `TAS` → `TAS`; `WA` → `WA`
- `address.postcode<-Postcode`: `3121` → `3121`; `7005` → `7005`; `6160` → `6160`
- `entity.status<-Licence Status`: `Current` → `active`; `Expired` → `unknown`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
