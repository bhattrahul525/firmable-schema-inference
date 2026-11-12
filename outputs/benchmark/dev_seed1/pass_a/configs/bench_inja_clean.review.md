# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0052, 24.02s (download and human waits excluded). Trace: `logs/agent_runs/bench_inja_clean/trace.jsonl`.
- Evidence the agent gave at finish (its words): Read 160 rows x 8 columns (utf-8, comma). Record_id Licence No unique, no blanks. ABN 100% 11-digit; abn transform, state_code, postcode parse 100% on 80 held-out rows with 0 rejects.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 2 | `Suburb` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 3 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 4 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated
2. `address.locality` ← `Suburb`: Suburb
3. `address.state` ← `State`: State code
4. `address.postcode` ← `Postcode`: Postcode

## Left unmapped (not guessed)

- `Licence No`: licence identifier of the register, used as record_id; not an entity identifier
- `Business Name`: licensee name as shown in the register; the source does not state it is the registered legal name, so not mapped to entity.legal_name (critique c-08e9e6fe)
- `Licence Status`: licence status (Current/Expired) describes the licence, not the entity status enum; left unmapped
- `Notes`: free-text remarks, not mappable

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping of Suburb, State, Postcode and ABN looks consistent with the rows shown. The main meaning error is that Business Name is emitted as the registered legal_name, which the source does not state. The envelope and confidence fields are not visible in the examples and need to be shown to confirm they are complete.
  - [blocking] `entity.legal_name<-Business Name`: The ontology defines entity.legal_name as the name 'As registered'. The config's own reason says the licence register does not explicitly state registered status. Every example emits Business Name as legal_name (e.g. 'Roofing Services 2 Pty Ltd'), so the mapping asserts a registered legal name that the source does not support. (suggested: Remove the legal_name mapping for Business Name, or map it to a non-registered field or a lower-confidence observation that records it as the licensee name as shown in the register, without claiming it is the registered legal name.)
  - [advisory] `observation`: The shown envelopes contain only observed_at, valid_from and valid_to. The required observation fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the examples, so the envelope cannot be confirmed as complete. (suggested: Show the full envelope in the examples, including source_id, source_record_id (built from Licence No), ingested_at, the licence from CKAN metadata (or 'unknown' with a flag), and extractor_version.)
  - [advisory] `confidence`: No confidence values (source_reliability, field_confidence) appear in the example observations, so it is unclear whether the ABN checksum validation and the postcode/state parsing were scored. (suggested: Emit field_confidence per mapped field, reflecting whether the abn checksum passed, and source_reliability for the licence register, kept separate.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `34200000026` → `34200000026`; `49200000039` → `49200000039`; `59200000052` → `59200000052`
- `address.locality<-Suburb`: `Fortitude Valley` → `Fortitude Valley`; `Fremantle` → `Fremantle`; `Glenelg` → `Glenelg`
- `address.state<-State`: `QLD` → `QLD`; `WA` → `WA`; `SA` → `SA`
- `address.postcode<-Postcode`: `4006` → `4006`; `6160` → `6160`; `5045` → `5045`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
