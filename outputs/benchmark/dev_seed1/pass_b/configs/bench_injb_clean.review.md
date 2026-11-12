# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0058, 31.38s (download and human waits excluded). Trace: `logs/agent_runs/bench_injb_clean/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validate on 80 held-out rows: 0 hard failures, 0 rejected values, parse rate 1.0 on all mapped columns, record_id Licence No unique across 160 rows. Critique: 5 advisory issues, 0 blocking; legal_name reason softened per advisory suggestion.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 4 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: Business Name on the licence register appears to be the licensee name (values carry Pty Ltd suffixes); the source does not state explicitly that it is the registered name.
2. `entity.abn` ← `ABN`: 11-digit ABN column.
3. `address.locality` ← `Suburb`: Suburb name.
4. `address.state` ← `State`: State abbreviation.
5. `address.postcode` ← `Postcode`: 4-digit postcode.

## Left unmapped (not guessed)

- `Licence No`: Licence identifier with no ontology field; used as record_id.
- `Licence Status`: Describes the licence (Current/Expired), not the entity status; no safe mapping to entity.status.
- `Notes`: Free-text notes with no ontology field.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.status <- Licence Status`: Licence Status (Current/Expired) describes the licence, not the entity's registration status; mapping would be a guess.

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the ABN, state, postcode and suburb columns map to the fields they describe, and the sampled ABNs I checked pass the checksum. No blocking meaning errors are visible in the examples. The main concerns are the basis for treating 'Business Name' as the registered legal name, the unsourced default entity_type observation, and envelope completeness, which the examples do not show.
  - [advisory] `entity.legal_name<-Business Name`: The reason asserts that the 'Business Name' column is the registered licensee name. The source is a licence register, and a business name there may be a trading name rather than the registered legal name. The examples' 'Pty Ltd' suffixes support the mapping, but the source does not state that this column is the registered name. (suggested: Keep the mapping, but soften the reason to say the value appears to be the licensee name, and consider a trading_name observation or a field_confidence below 1 until the register's definition is confirmed.)
  - [advisory] `entity.entity_type`: Every record emits an entity_type observation of 'unknown' with from: null. No source column supports it, so it is a default rather than a source claim, yet it is written as an observation. (suggested: Either omit the default observation or mark it explicitly as a config default (derivation_level L1 or a non-source marker) so it is not read as something the source stated.)
  - [advisory] `observation`: The shown envelopes include only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version do not appear in the examples. Licence and provenance are also not shown in the config. (suggested: Confirm the emitted envelope carries all required observation fields, including licence from the CKAN metadata (or 'unknown' flagged) and extractor_version.)
  - [advisory] `observed_at`: observed_at is taken from the dataset metadata field resource_last_modified. That is when the publisher last touched the resource, not necessarily when the individual licence claim was stated. (suggested: Document this as a proxy for observed_at, or check whether per-record dates exist in the source.)
  - [advisory] `address.locality<-Suburb`: Locality is copied from the Suburb column without parsing or normalisation. This is acceptable, but the envelope and transform list give no check that suburb values are consistent with state and postcode. (suggested: Optionally cross-check suburb, state and postcode, and record the result in field_confidence.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Electrical Services 1 Pty Ltd` → `Electrical Services 1 Pty Ltd`; `Concreting Services 3 Pty Ltd` → `Concreting Services 3 Pty Ltd`; `Carpentry Services 4 Pty Ltd` → `Carpentry Services 4 Pty Ltd`
- `entity.abn<-ABN`: `19200000013` → `19200000013`; `49200000039` → `49200000039`; `59200000052` → `59200000052`
- `address.locality<-Suburb`: `Richmond` → `Richmond`; `Fremantle` → `Fremantle`; `Glenelg` → `Glenelg`
- `address.state<-State`: `VIC` → `VIC`; `WA` → `WA`; `SA` → `SA`
- `address.postcode<-Postcode`: `3121` → `3121`; `6160` → `6160`; `5045` → `5045`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
