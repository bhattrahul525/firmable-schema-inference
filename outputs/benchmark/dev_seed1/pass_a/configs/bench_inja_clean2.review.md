# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0062, 31.75s (download and human waits excluded). Trace: `logs/agent_runs/bench_inja_clean2/trace.jsonl`.
- Evidence the agent gave at finish (its words): 160 rows, 8 columns; ABN 100% 11-digit and checksum-valid on validate (0 rejected); record_id Licence No unique and filled; validate 0 hard failures; critique 0 blocking.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 4 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: Business Name ending in Pty Ltd; licensee business name treated as registered name
2. `entity.abn` ← `ABN`: ABN column, checksum validated
3. `address.locality` ← `Suburb`: Suburb name
4. `address.state` ← `State`: State abbreviation
5. `address.postcode` ← `Postcode`: 4-digit postcode

## Left unmapped (not guessed)

- `Licence No`: licence identifier, used as record_id
- `Licence Status`: licence status (Current/Expired) describes the licence, not a clearly mapped entity.status; Expired is not equivalent to deregistered
- `Notes`: free-text remarks, sparse

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mappings for ABN, suburb, state and postcode match the raw rows, and the ABN checksums I spot-checked are valid. The main concern is that the licence register's business name is labelled as the registered legal name without verification, and the examples show a default 'unknown' entity_type observation with no source. Several required envelope fields are not visible in the examples. No blocking errors are shown, but the legal_name claim should be caveated.
  - [advisory] `entity.legal_name<-Business Name`: The reason says the licensee business name is 'treated as registered name', but a licence register's business name is the name shown on the licence and is not verified against the company register. The 'Pty Ltd' suffix suggests a company name but does not prove it is the registered name. (suggested: Keep the observation but document that it is the licence-register business name, not a verified registered name. Consider a lower field_confidence, or a separate note, unless the registered name is checked against ASIC.)
  - [advisory] `entity.entity_type`: Each example emits an entity_type observation with value 'unknown' and from: null. That is a default, not a claim the source made, so it does not belong in the observation stream with source-style provenance. Also, the 'Pty Ltd' suffix in the legal name supports at least a company inference that is not used. (suggested: Do not emit default values as observations. If a company type is inferred from the 'Pty Ltd' suffix, record it as an L1 derivation with the rule documented. Otherwise omit entity_type entirely.)
  - [advisory] `observation`: The envelopes shown carry only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the examples, and confidence and derivation_level are also absent. (suggested: Confirm these fields are present on every emitted record. Set licence from the CKAN metadata, or to 'unknown' with a finding if it is missing. Add source_record_id derived from Licence No, and the confidence and derivation_level values.)
  - [advisory] `entity.trading_name`: The source has no trading name column, but the config does not state that trading_name was considered. Nothing in the examples is wrong, but the mapping is silent on it. (suggested: Note in the config that the source has no trading name, so the absence is a deliberate decision and not an omission.)
  - [advisory] `address.full`: Only suburb, state and postcode are mapped. The address is not composed and no full address is produced, which leaves the address record incomplete. (suggested: Note that the source has no street address, or compose a full address from the available parts and mark it as derived.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`; `Tiling Services 6 Pty Ltd` → `Tiling Services 6 Pty Ltd`; `Electrical Services 9 Pty Ltd` → `Electrical Services 9 Pty Ltd`
- `entity.abn<-ABN`: `74200000065` → `74200000065`; `89200000078` → `89200000078`; `17200000117` → `17200000117`
- `address.locality<-Suburb`: `Sandy Bay` → `Sandy Bay`; `Parramatta` → `Parramatta`; `Fremantle` → `Fremantle`
- `address.state<-State`: `TAS` → `TAS`; `NSW` → `NSW`; `WA` → `WA`
- `address.postcode<-Postcode`: `7005` → `7005`; `2150` → `2150`; `6160` → `6160`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
