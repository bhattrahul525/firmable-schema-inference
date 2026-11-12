# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0067, 30.58s (download and human waits excluded). Trace: `logs/agent_runs/bench_injc_clean2/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 2 | `Suburb` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 3 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 4 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: ABN column with 11-digit values
2. `address.locality` ← `Suburb`: Suburb column
3. `address.state` ← `State`: State abbreviation
4. `address.postcode` ← `Postcode`: 4-digit postcode

## Left unmapped (not guessed)

- `Licence No`: used as record_id
- `Business Name`: licensed business name; not stated to be the registered name, so not mapped to legal_name
- `Licence Status`: licence state, not a clear entity.status; not interpreted
- `Notes`: free-text remarks, not a mapped field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound for ABN, suburb, state and postcode. The main blocking problem is that the licence register's Business Name is mapped to legal_name, which the source does not support as a registered name. The remaining points are advisory, covering a default entity_type observation, envelope completeness, observed_at semantics and the unmapped licence status.
  - [blocking] `entity.legal_name<-Business Name`: The source is a licence register column called 'Business Name'. Nothing in the source states that it is the name as registered with ASIC or the ABR. The reason given ('register names look like registered names') is an assumption, and the ontology says legal_name must be the registered name, not a trading name. Several example rows also show names that look like trading names, so this claim is not supported by the source. (suggested: Map 'Business Name' to a trading_name observation, or to a separate licensed-name field, with a note that it is the name used on the licence. Only map it to legal_name if a registry-sourced name is confirmed for this dataset.)
  - [advisory] `entity.entity_type`: Every example emits an entity_type observation of 'unknown' with from: null. This is a default the engine filled in, not something the source said. Several names contain 'Pty Ltd', which hints at a company, but the mapping correctly does not guess. (suggested: Do not emit an observation for a default value. Leave entity_type absent, or record it as a derived default with a clear derivation note, so it is not mistaken for a source claim.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in these examples. The licence should come from the CKAN metadata, or be recorded as 'unknown' and flagged. (suggested: Confirm that every emitted observation carries all required envelope fields, including the licence from the dataset metadata (or 'unknown' with a flag) and the extractor_version.)
  - [advisory] `observed_at`: observed_at is set from resource_last_modified, which is when the publisher last changed the file. The ontology defines observed_at as when the source stated the claim. These can differ, and the mapping gives no note on this. (suggested: Document that observed_at is the resource last-modified time as a proxy, and consider recording the licence-status date separately if the dataset provides one.)
  - [advisory] `status`: Licence Status values such as 'Expired' are left unmapped, which is reasonable because a licence state is not an entity status. The mapping still loses a potentially useful claim about the licence. (suggested: Keep the field unmapped as documented, and consider a note or a licence-specific observation for future use so the information is not discarded.)
  - [advisory] `address.country`: The ontology default is country AU, but no country observation is emitted from the rows. The state values are all Australian, so the default could reasonably be applied. (suggested: Either apply the AU default explicitly with a note that it is a default, or leave country out. Be explicit about which.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `34200000026` → `34200000026`; `49200000039` → `49200000039`; `59200000052` → `59200000052`
- `address.locality<-Suburb`: `Fortitude Valley` → `Fortitude Valley`; `Fremantle` → `Fremantle`; `Glenelg` → `Glenelg`
- `address.state<-State`: `QLD` → `QLD`; `WA` → `WA`; `SA` → `SA`
- `address.postcode<-Postcode`: `4006` → `4006`; `6160` → `6160`; `5045` → `5045`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
