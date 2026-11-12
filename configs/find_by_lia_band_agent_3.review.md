# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**.
- 10 model turns, 10 tool calls, $0.0126, 65.46s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_3/trace.jsonl`.
- Evidence the agent gave at finish (its words): 3,306 rows, 21 columns, utf-8 CSV. Licence Name is the venue name (e.g. 'Royal Hotel', 'Charlestown Golf Club Ltd'). Licence No is unique in the sample except one duplicate, so hash_row was used. No ABN or ACN column exists. Critique blocked the legal_name and status mappings; the config keeps only the trading_name and address mappings.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licence Name` | `entity.trading_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Licence Name`: Name of the licensed venue as shown on the gaming licence register; not stated as the registered name, so mapped to trading_name.
2. `address.full` ← `Venue Address`: Venue address for the licensed premises.

## Left unmapped (not guessed)

- `Data as of`: snapshot date; used as metadata context only
- `Licence No`: licence identifier, not an ABN/ACN; kept in raw record for traceability
- `Start Date`: licence start date; validity semantics not confirmed, left unmapped
- `Trading Status`: describes premises trading, not the legal entity's status; mapping to entity.status rejected in critique
- `Type`: club/hotel venue type, not an entity_type enum value
- `Filter Category`: internal venue category
- `Latitude`: no ontology field for coordinates
- `Longitude`: no ontology field for coordinates
- `SA2 Name`: statistical area name, no ontology field
- `SA2 Band`: gaming-machine policy band, no ontology field
- `Subject to Cap`: gaming regulation flag, no ontology field
- `LGA`: local government area, no ontology field
- `Region`: regional classification, no ontology field
- `GME`: gaming machine entitlement count, no ontology field
- `PMP`: gaming machine entitlement count, no ontology field
- `Auth Total`: authorised machine count, no ontology field
- `Unfulfilled Quota`: gaming quota count, no ontology field
- `GMT`: gaming machine count, no ontology field
- `EGMs`: installed EGM count, no ontology field

## Needs a transform the engine does not have

- `Trading Status`: needs a venue-level trading-status field, which the ontology does not have

## Abstentions (fields removed, with reasons)

- `entity.status<-Trading Status`: The column describes premises trading, not the legal entity's status, and the 'temporarily ceased' value has no ontology equivalent.
- `entity.legal_name<-Licence Name`: Not stated to be the registered name; mapped as trading_name only.

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main meaning error is that Licence Name, a venue or trading name, is mapped to entity.legal_name, which the ontology defines as the registered name. That mapping should be blocked and redirected to trading_name. The remaining points are advisory: venue trading status being applied to the entity, a sourceless 'unknown' observation being emitted, and the envelope and address parsing being incomplete. The unmapped columns (Start Date, Licence No, coordinates, counts) are handled reasonably.
  - [blocking] `entity.legal_name<-Licence Name`: The ontology defines legal_name as the name as registered, not the trading name. The config's own reason says Licence Name is a licensee/venue operator name and not explicitly the registered name. The examples are venue names ('Brighton Hotel', 'Leumeah Club Hotel', 'Commercial Hotel' appearing twice at different addresses), which read as trading names. Nothing in the source states a registered legal name. (suggested: Remove the legal_name mapping. Map Licence Name to trading_name (one observation per name), or hold it as a non-entity venue name, and only map legal_name from a source that states registered names.)
  - [advisory] `entity.status<-Trading Status`: The source states whether the venue (premises) is trading. The canonical status describes the legal entity. Mapping 'Trading' to entity status 'active' treats a premises-level claim as an entity-level one. 'Temporarily ceased trading' mapped to 'suspended' is also a loose fit. (suggested: Keep the mapping but record it as a venue-trading claim in the observation (e.g. note in the reason or a separate field), and lower field_confidence for the entity-level reading. Consider whether 'Temporarily ceased trading' should map to 'suspended' or stay unmapped.)
  - [advisory] `entity.entity_type`: Observations are emitted for entity_type with value 'unknown' and from: null, so no source claim is attached. This is a default, not an observation from any source, and it adds noise to every record. (suggested: Do not emit an observation for a default value. Let the downstream layer assume unknown when no observation exists.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown. observed_at is 2020-12-10 (the metadata last-modified date), while the 'Data as of' column says 01-Dec-20, which is the snapshot date the config treats as context only. (suggested: Confirm the full envelope is emitted with all required fields, including the licence from CKAN metadata (or 'unknown' with a flag). State explicitly how observed_at relates to 'Data as of'.)
  - [advisory] `address.full<-Venue Address`: Locality and postcode are embedded in the address string (e.g. 'The Fairway TURA BEACH', '408 Murray St HAY') and are not parsed out. The state enum is also not set, though the state is not stated explicitly in the source either. (suggested: Optionally parse locality from the trailing uppercase token as a derived (L1) value with a lower field_confidence. Do not infer state from LGA or Region without a stated source.)
- Critique: The venue-to-entity mapping of Trading Status is the main meaning error: the source describes premises trading, but the config maps it to the legal entity's status enum, and the 'suspended' mapping for 'Temporarily ceased trading' is not supported by the source. The envelope in the examples is incomplete, and several advisory points remain about observed_at, valid_from, address parsing and the default entity_type observations.
  - [blocking] `entity.status<-Trading Status`: The source column 'Trading Status' describes whether a licensed venue (premises) is trading. The config maps it to entity.status, which the ontology defines for the legal entity's registration state. The source does not state the entity's status, so 'active' asserts something about the company that the venue data does not support. (suggested: Do not map Trading Status to entity.status. Keep it as a premises-level observation under a venue-status field, or leave it unmapped and record it in the raw record.)
  - [blocking] `entity.status<-Trading Status`: The map_values entry 'Temporarily ceased trading' -> 'suspended' assigns a regulatory-sounding enum value to a trading state. Temporarily ceasing trading is not stated to be a licence or registration suspension, so the mapping adds a meaning the source does not state. (suggested: Remove this mapping. If the status is kept at all, map it to a venue-level value that preserves 'temporarily ceased trading' as written, or to unknown.)
  - [advisory] `entity.entity_type`: Every example emits an entity.entity_type observation with value 'unknown' and from: null. This is a default, not a claim any source made, so it sits oddly in an observations list whose purpose is to hold source claims. (suggested: Omit default-valued fields from the observation list, or mark them explicitly as defaults that are not source observations.)
  - [advisory] `observed_at`: The raw rows carry 'Data as of' = 01-Dec-20, the date the source states. The envelope observed_at is 2020-12-10T00:53:09, which looks like a processing or metadata timestamp rather than the time the source stated the claim. (suggested: Confirm that resource_last_modified is the intended basis. Consider recording the 'Data as of' snapshot date as observed_at, or keep both and document which one is used.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are absent, and the ontology says every record carries the envelope with no exceptions. The examples may be truncated, but as shown they are incomplete. (suggested: Show the full envelope in the examples. Confirm that licence is taken from CKAN metadata, or recorded as 'unknown' and flagged, and that source_record_id is built from the row hash.)
  - [advisory] `valid_from`: The 'Start Date' column is the licence start date, which can state when the licence claim became true. It is left unmapped and valid_from is null in every example. The stated reason, that the source does not clearly state validity, is debatable for a licence start date. (suggested: Consider mapping Start Date to the envelope valid_from for the licence-related observations, after parsing the dd/mm/yyyy format, or document why it should stay unmapped.)
  - [advisory] `address.full<-Venue Address`: The 'Venue Address' value is mapped as a single string, and address.state and address.postcode are left empty even though the 'Region' and 'LGA' columns and the address text contain partial location information. Some addresses (e.g. 'Callaghan Park' Loftus St TEMORA) carry quoting that is kept as-is. (suggested: Parse state and postcode where the source states them, otherwise leave them null. Keep the full string as the raw value and document that the quoting is preserved.)
  - [advisory] `entity.trading_name<-Licence Name`: Names such as 'Petersham RSL Club Limited' include a corporate suffix, which suggests the licence name may be a registered company name rather than a trading name. The config asserts it is not registered, but the examples do not show that. (suggested: Note the uncertainty in the config reason, or add a field_confidence value below 1 for names containing legal-form suffixes.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Licence Name`: `Tura Beach Country Club` → `Tura Beach Country Club`; `Del Rio Aquatic Club Limited` → `Del Rio Aquatic Club Limited`; `Czechoslovakian Country Club Limited` → `Czechoslovakian Country Club Limited`
- `address.full<-Venue Address`: `The Fairway TURA BEACH` → `The Fairway TURA BEACH`; `Riverside Drive WEBBS CREEK` → `Riverside Drive WEBBS CREEK`; `320 Devonshire Rd KEMPS CREEK` → `320 Devonshire Rd KEMPS CREEK`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
