# Review packet (round-2 agent): validated_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **validated_config**.
- 12 model turns, 12 tool calls, $0.0122, 62.96s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r2_3/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licence Name` | `entity.trading_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Licence Name`: Licence name is the name of the licensed club or hotel premises; it is a name the venue trades under rather than a verified registered name
2. `address.full` ← `Venue Address`: Licensed venue street address with suburb

## Left unmapped (not guessed)

- `Data as of`: snapshot date; observed_at from metadata
- `Start Date`: used as valid_from (licence start date)
- `Licence No`: liquor licence number, not ABN/ACN; not unique across file so not used as record_id
- `Trading Status`: describes the licensed premises' trading state, not the legal entity's status; no venue-level status field in ontology, so not mapped
- `Type`: club/hotel venue type, not an entity_type enum value
- `Filter Category`: venue category, no canonical field
- `SA2 Name`: statistical area, no canonical field
- `SA2 Band`: licensing band, no canonical field
- `Subject to Cap`: gaming cap flag, no canonical field
- `LGA`: local government area, no canonical field
- `Region`: region classification, no canonical field
- `Latitude`: geo coordinate, no canonical field
- `Longitude`: geo coordinate, no canonical field
- `GME`: gaming machine entitlement count
- `PMP`: gaming machine entitlement count
- `Auth Total`: entitlement count
- `Unfulfilled Quota`: entitlement count
- `GMT`: entitlement count
- `EGMs`: gaming machine count

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-Licence Name`: Licence Name is a premises/licence name (e.g. 'Hunters Hill Hotel'), not verified as the registered entity name; mapped to trading_name instead.
- `entity.status<-Trading Status`: Describes the licensed venue's trading state, not the registered entity's status.

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound on status and address. The main problem is that Licence Name is mapped to entity.legal_name even though rows show venue names, which is a blocking meaning error. Several advisory points concern the validity dates, the venue address versus registered address, and the required envelope fields.
  - [blocking] `entity.legal_name<-Licence Name`: The source column is a liquor licence name, and the config's own reason concedes hotels may use a venue name. Rows such as 'Hunters Hill Hotel', 'Wolumla Hotel', 'Locomotive Hotel' and 'The Grafton Village Green' are venue or premises names, not registered legal names. Mapping them to entity.legal_name asserts a registered name the source does not support. (suggested: Do not emit entity.legal_name from Licence Name. Emit it as a trading-name-style or licence-name observation (for example entity.trading_name, with a note that it is the licence/venue name), or restrict legal_name to rows where the holder is verifiably a registered company, and set field_confidence accordingly.)
  - [advisory] `envelope.valid_from`: valid_from is taken from Start Date, which is the liquor licence start date. It is applied to every observation in the row, including the legal name and status claims, so it is not clearly when those claims became true of the entity. (suggested: Attach valid_from only to the licence-related observation, or document that it means licence start and not entity registration.)
  - [advisory] `entity.status<-Trading Status`: Trading Status 'Trading' is mapped to active. A liquor licence status describes the premises licence, not the legal entity's status. The map_values has no fallback for other values, so unseen statuses would be dropped or mis-mapped. (suggested: Keep the mapping but note it describes the licensed venue. Add an explicit fallback to unknown for any value other than 'Trading'.)
  - [advisory] `address.full<-Venue Address`: This is the premises address of the licensed venue, not necessarily the registered or head-office address of the entity. The address is also not parsed into locality, state or postcode, although the file is NSW-only and the suburb is present in the string. (suggested: Label the observation as a venue address. Consider parsing locality and postcode, and deriving state NSW from the source context at L1 with a documented method.)
  - [advisory] `entity.entity_type`: An entity_type observation of 'unknown' is emitted with from: null on every row. It carries no source claim, so it adds envelope noise without information. The source Type column (club/hotel) is unmapped, which is acceptable since it is not an entity_type value. (suggested: Omit the placeholder observation, or keep it with a note that it is a default and not a source claim.)
  - [advisory] `unmapped.Licence No`: The liquor licence number is a stable source identifier for the licence record, but it is dropped. The reason given (not unique across the file) does not rule it out as a source identifier for the observation. (suggested: Keep Licence No in the envelope as a licence reference, or in source_record_id combined with the row hash, so the observation can be traced back to the licence.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown on the emitted observations. (suggested: Confirm each emitted observation carries all required envelope fields, with licence set to the CKAN licence value or 'unknown' with a flag if absent.)
- Critique: The name, address, and licence-start mappings are broadly reasonable, but the entity.status mapping states a corporate status the venue trading flag does not support and should be removed or reworked. The remaining items are caveats and envelope completeness.
  - [blocking] `entity.status<-Trading Status`: The source column describes the licensed venue's trading state (the premises), not the registered entity's status. Mapping 'Trading' to entity.status 'active' states the company is active, which the source does not support. Several rows, such as Hunters Hill Hotel and Riverview Hotel, are venues whose operator's corporate status is not in the file. (suggested: Drop the entity.status mapping, or map it to a venue-level observation with the source's own wording preserved, and record that it refers to the premises licence rather than the entity.)
  - [advisory] `observation.valid_from`: Start Date is the liquor licence start date, which is a different claim from when the entity or venue became true in the world. The examples set valid_from from it without caveat. (suggested: Keep valid_from from Start Date only with a note that it is the licence start date, or record it as a licence-level claim.)
  - [advisory] `address.full<-Venue Address`: Venue Address is passed through as a single string with no state, postcode, or locality parsing. Examples such as 'Princes Hwy WOLUMLA' and 'Pound & Turf Sts GRAFTON' lack a street number and state, so the address is incomplete. (suggested: Parse locality and postcode where present, set address.state from the NSW licence context with a field_confidence reflecting that inference, and set country to AU.)
  - [advisory] `entity.trading_name<-Licence Name`: Some names carry corporate suffixes such as 'Ltd' or 'Limited', so the name may be closer to a registered legal name than a trading name. The config reason describes it as a trading name, so the label is uncertain. (suggested: Keep the mapping but record a lower field_confidence or note the ambiguity, and check against ABN/ACN data later before treating it as a trading name.)
  - [advisory] `observation envelope`: The examples show observed_at, valid_from, and valid_to only. The required envelope fields source_id, source_record_id, ingested_at, licence, and extractor_version are not visible, and the licence should be checked against the CKAN metadata. (suggested: Confirm each emitted record carries source_id, a documented source_record_id derived from the row hash, ingested_at, the CKAN licence (or 'unknown' with a flag), and extractor_version.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Licence Name`: `Canley Heights R S L & Sporting Club Ltd` → `Canley Heights R S L & Sporting Club Ltd`; `Clarence Town Bowling, Sport and Recreation Club L` → `Clarence Town Bowling, Sport and Recreation Club Limited`; `Building Workers Club Limited` → `Building Workers Club Limited`
- `address.full<-Venue Address`: `26 Humphries Rd WAKELEY` → `26 Humphries Rd WAKELEY`; `Prince & Durham Sts CLARENCE TOWN` → `Prince & Durham Sts CLARENCE TOWN`; `247 Woodstock Ave DHARRUK` → `247 Woodstock Ave DHARRUK`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
