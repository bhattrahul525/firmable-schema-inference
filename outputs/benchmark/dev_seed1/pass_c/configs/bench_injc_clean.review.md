# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0056, 26.38s (download and human waits excluded). Trace: `logs/agent_runs/bench_injc_clean/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: Business name of the licence holder. Caveat: the register does not state this is the registered name; values carry Pty Ltd suffixes but it may be an operating name. Confidence lowered accordingly.
2. `entity.abn` ← `ABN`: ABN column, 11 digits
3. `address.locality` ← `Suburb`: Suburb name
4. `address.state` ← `State`: State abbreviation
5. `address.postcode` ← `Postcode`: 4-digit postcode

## Left unmapped (not guessed)

- `Licence No`: licence reference, used as record_id
- `Licence Status`: Current/Expired values are not clearly the entity status enum; not mapped
- `Notes`: free text notes, sparse

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in the examples: the name, ABN, locality, state and postcode columns map to the fields they describe, and the ABN checked is valid. The remaining points are advisory: the legal-name caveat for licence registers, default-only entity_type observations, and envelope completeness that the examples do not show.
  - [advisory] `entity.legal_name<-Business Name`: The reason treats the licensee name on a licence register as the registered legal name. The examples carry a 'Pty Ltd' suffix, which supports that reading, but a licence register can hold a trading or operating name, and the source does not state that this is the registered name. (suggested: Keep the mapping but note the caveat in the config reason and lower field_confidence, or cross-check the name against an ABN register before treating it as the registered legal name.)
  - [advisory] `entity.entity_type`: Every row emits an entity_type observation with value 'unknown' and from: null. No source column supports it, so it is a default and not a claim the source made. It adds noise, and the ontology's default-to-unknown guidance is better served by emitting nothing. (suggested: Stop emitting default-only entity_type observations when no source column maps to it, or mark them clearly as engine defaults rather than source observations.)
  - [advisory] `observation envelope`: The shown envelope contains only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version do not appear in the examples. The observed_at value is taken from resource_last_modified, which is the time the dataset file changed, not necessarily when the claim was stated. (suggested: Confirm that the full envelope is emitted with all required fields, including licence from CKAN metadata (or 'unknown' with a flag). Document that observed_at is the resource modification time, and note source_record_id construction from Licence No.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Concreting Services 3 Pty Ltd` → `Concreting Services 3 Pty Ltd`; `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`; `Tiling Services 6 Pty Ltd` → `Tiling Services 6 Pty Ltd`
- `entity.abn<-ABN`: `49200000039` → `49200000039`; `74200000065` → `74200000065`; `89200000078` → `89200000078`
- `address.locality<-Suburb`: `Fremantle` → `Fremantle`; `Sandy Bay` → `Sandy Bay`; `Parramatta` → `Parramatta`
- `address.state<-State`: `WA` → `WA`; `TAS` → `TAS`; `NSW` → `NSW`
- `address.postcode<-Postcode`: `6160` → `6160`; `7005` → `7005`; `2150` → `2150`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
