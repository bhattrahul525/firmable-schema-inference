# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**.
- 12 model turns, 12 tool calls, $0.0115, 62.19s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r1_1/trace.jsonl`.
- Evidence the agent gave at finish (its words): 3,306 rows, 21 columns; 1-Dec-20 snapshot of NSW gaming venues (hotels and clubs). Validation: 0 hard failures, 0 unaccounted columns, hash_row record id unique on 3,306 rows. Licence No is near-unique but has one duplicate, so hash_row was used. Licence is unknown (flagged).
- Reason: The dataset describes gaming venues, not registered entities, and its name column cannot be assigned to legal_name or trading_name without an unsupported claim. Only the venue address and observation dates are mapped.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|

The model's reasons per field (its words, not verified):


## Left unmapped (not guessed)

- `Licence Name`: Venue/club name on a gaming licence; the source does not say it is a registered name, so it is not mapped to legal_name or trading_name
- `Data as of`: used as observed_at
- `Start Date`: used as valid_from (licence start, not a name or address start)
- `Trading Status`: venue trading activity, not registered entity status; no mapping
- `Licence No`: licence number, not an ABN/ACN
- `Type`: hotel/club venue type; no ontology field
- `Latitude`: no ontology field
- `Longitude`: no ontology field
- `Filter Category`: licence category; no ontology field
- `SA2 Name`: statistical area; no ontology field
- `SA2 Band`: gaming band; no ontology field
- `Subject to Cap`: regulatory flag; no ontology field
- `LGA`: no ontology field
- `Region`: no ontology field
- `GME`: gaming machine entitlement count
- `PMP`: gaming machine count
- `Auth Total`: entitlement count
- `Unfulfilled Quota`: entitlement count
- `GMT`: entitlement count
- `EGMs`: machine count
- `Venue Address`: abstained by the harness (failed validation or an unanswered critique issue) (address.full)

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name / entity.trading_name <- Licence Name`: Licence Name is a venue or club name on a gaming licence (e.g. 'Royal Hotel', 'Sporties Tuncurry', some with 'Ltd'/'Limited' suffixes). The source does not state it is registered or trading under a name, and critique blocked both mappings. Left out pending a source that states the entity name.
- `entity.status <- Trading Status`: Describes venue trading activity, not registered entity status; not mapped.
- `address.locality / address.postcode`: Locality is embedded in the all-caps venue address; not parsed in this config.
- `observation.valid_from`: critique issue unanswered: Start Date is the licence start date, which is used as valid_from for all observations. It does not necessarily say when the entity or name became true, since a licence can be transferred or re-issued to a different operator.
- `address.full<-Venue Address`: critique issue unanswered: The venue address is kept as one string with locality in capitals (e.g. 'The Fairway TURA BEACH', '99 Mortimer St MUDGEE'). Locality and postcode are not parsed out, and state is not set even though the licence prefix and LGA point to NSW.
- `address.locality`: critique issue unanswered: The locality appears in the Venue Address in capitals (e.g. 'WEST RYDE', 'MUDGEE', 'BONDI JUNCTION'). The config maps the whole string to address.full and does not parse out the locality or postcode, so the richer address fields are left empty.
- `observation.valid_from`: critique issue unanswered: Start Date is the licence start, not the date the trading-name or address claim became true. Using it as valid_from on every observation ties the licence date to the name and address claims, which the source does not say.
- `observation envelope`: critique issue unanswered: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown. The licence must come from CKAN metadata, and 'unknown' must be recorded if it is absent.

## Checks

- Critique: The mapping has one blocking problem: Licence Name is a venue or trading name, but it is mapped to the registered legal_name field. The status mapping conflates venue trading status with entity status and should be lowered. The valid_from and address parsing points are advisory.
  - [blocking] `entity.legal_name<-Licence Name`: The source column is a licence name, and the examples show venue or trading names such as 'The Eastern', 'Laughing Buddha Bar', 'Australia Hotel' and 'Tura Beach Country Club'. The ontology defines legal_name as the registered name, not the trading name. The source does not state a registered name, so the reason given ('treated as the licensee's name') is an assumption the data does not support. (suggested: Remove the entity.legal_name<-Licence Name mapping, or map it to a trading_name observation (one per record), and leave legal_name unmapped for this source.)
  - [advisory] `entity.status<-Trading Status`: The source column describes current trading activity at a venue ('Trading', 'Temporarily ceased trading'), not the registered status of the entity. Mapping 'Trading' to active and a temporary cessation to suspended treats a venue operating fact as an entity registry status. The 'suspended' mapping is also not shown in any example row, so it is untested. (suggested: Keep the raw value, or lower confidence and document that it is a venue trading status, not the entity status. Check the 'Temporarily ceased trading' rule against real rows before relying on it.)
  - [advisory] `observation.valid_from`: Start Date is the licence start date, which is used as valid_from for all observations. It does not necessarily say when the entity or name became true, since a licence can be transferred or re-issued to a different operator. (suggested: Scope valid_from to the licence claim, or document that it applies only to the licence and not to the entity's legal_name or status.)
  - [advisory] `address.full<-Venue Address`: The venue address is kept as one string with locality in capitals (e.g. 'The Fairway TURA BEACH', '99 Mortimer St MUDGEE'). Locality and postcode are not parsed out, and state is not set even though the licence prefix and LGA point to NSW. (suggested: Parse locality out of the trailing capitalised token, and consider deriving state (NSW) with a derivation_level of L1 and a field_confidence reflecting the inference.)
- Critique: The observed_at parse and the Venue Address to address.full mapping look correct. The main problem is that Licence Name is emitted as entity.trading_name, a claim the source does not support and that the config's own reason admits is inference, so that mapping should be blocked or re-targeted. The rest are advisory: the locality is not parsed, Start Date is used as validity for the name and address claims, and the required envelope fields are not visible in the examples.
  - [blocking] `entity.trading_name<-Licence Name`: The config maps Licence Name to trading_name while its own reason says the value is not stated as a registered name. The examples include legal-form suffixes such as 'Limited' and 'Ltd' (e.g. 'Mudgee Soldiers Club Limited', 'Fraternity Bowling & Recreation Club Ltd', 'Ryde - Parramatta Golf Club Limited'), which suggests registered entity names. The source supports a venue or licence name, not a trading-name claim about the entity, so this mapping states more than the source does. (suggested: Either drop this mapping, or map it to a neutral venue or licence-name observation outside entity.trading_name, with a note that the value may be a registered name. Do not emit it as trading_name without a source that says so.)
  - [advisory] `address.locality`: The locality appears in the Venue Address in capitals (e.g. 'WEST RYDE', 'MUDGEE', 'BONDI JUNCTION'). The config maps the whole string to address.full and does not parse out the locality or postcode, so the richer address fields are left empty. (suggested: Parse the trailing capitalised locality into address.locality, and state the ALL-CAPS normalisation as a deterministic L1 transform. Leave state unset unless a source states it, since the licence prefix does not state the state.)
  - [advisory] `observation.valid_from`: Start Date is the licence start, not the date the trading-name or address claim became true. Using it as valid_from on every observation ties the licence date to the name and address claims, which the source does not say. (suggested: Keep the licence start, but record that it refers to the licence and not to the name or address. Consider noting the basis in the observation or config reason.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown. The licence must come from CKAN metadata, and 'unknown' must be recorded if it is absent. (suggested: Confirm that every emitted observation carries all required envelope fields, including the licence from the dataset metadata and the record_id from hash_row, and check the shown examples are not truncated.)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
