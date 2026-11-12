# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**, ended by the harness: finish refused 2 times in a row.
- 14 model turns, 14 tool calls, $0.0179, 92.03s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|

The model's reasons per field (its words, not verified):


## Left unmapped (not guessed)

- `Start Date`: licence start date; not mapped to valid_from because it dates the liquor licence, not the venue name or entity claim
- `Trading Status`: describes venue trading state, not licensee entity status; not mapped to entity.status
- `Licence No`: NSW liquor licence identifier; not an ABN/ACN; not unique (one duplicate), so record_id uses row hash
- `Latitude`: geocode, no canonical field
- `Longitude`: geocode, no canonical field
- `Type`: hotel/club venue type, not entity_type
- `Filter Category`: internal gaming category, not ANZSIC
- `SA2 Name`: statistical area, no canonical field
- `SA2 Band`: policy band, no canonical field
- `Subject to Cap`: regulatory flag, no canonical field
- `LGA`: local government area, no canonical field
- `Region`: metro/country flag, no canonical field
- `GME`: gaming machine entitlement count
- `PMP`: entitlement count
- `Auth Total`: entitlement count
- `Unfulfilled Quota`: entitlement count
- `GMT`: entitlement count
- `EGMs`: machine count
- `Licence Name`: abstained by the harness (failed validation or an unanswered critique issue) (entity.trading_name)
- `Venue Address`: abstained by the harness (failed validation or an unanswered critique issue) (address.full)

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.trading_name<-Licence Name`: critique issue unanswered: Several Licence Name values are registered-style company names, not venue or trading names. Examples: 'Mulwala Water Ski Club Ltd', 'Panania East Hills RSL Club Limited', 'Branxton Golf Club Co-operative Limited', 'Tumbarumba Bowling Club Limited'. The config reason says these are mostly trading names, but the examples carry legal-entity suffixes (Ltd, Limited, Co-operative Limited). Mapping them to trading_name risks mislabelling registered names as trading names, and legal_name is never populated from this source.
- `address.full<-Venue Address`: critique issue unanswered: Some Venue Address values are not full street addresses. 'Marrickville & Illawarra Rds MARRICKVILLE' is an intersection and 'Maitland Rd MAYFIELD' and 'Caroline St BENDEMEER' have no house number. Mapping them to address.full overstates their completeness, and the field is not parsed into locality, state or postcode.

## Checks

- Critique: The mapping has meaning errors in the name and status fields: venue names are treated as legal names, and venue trading status is treated as entity status. The observed_at value does not match the documented snapshot date, valid_from draws on an unlisted column, and the envelope lacks required fields. The entitlement and geocode columns are sensibly left unmapped.
  - `entity.legal_name<-Licence Name`: Most Licence Name values are venue or trading names, not registered legal names. Examples: 'The Glebe Hotel', 'Marrickville Tavern', 'Coffs Harbour Hotel', 'Post Office Hotel', 'Beauford Hotel', 'Bendemeer Hotel'. The config reason admits only 'some values are registered company names', so mapping the whole column to legal_name asserts a legal name the source does not give. (suggested: Map Licence Name to entity.trading_name. Map to entity.legal_name only where the value is verifiably a registered company name (e.g. a 'Ltd'/'Limited' entity), or leave legal_name unmapped and let reconciliation decide.)
  - `entity.status<-Trading Status`: Trading Status describes whether the venue is trading, not the registration status of the licensee entity. Mapping it to entity.status makes a venue operating claim look like an entity legal status (active/deregistered/in_liquidation). (suggested: Do not map to entity.status. Carry it as a venue-level or other observation field, or map it to entity.status only with a documented caveat and a low field_confidence, and note that the venue, not the entity, is the subject.)
  - `observed_at`: observed_at is taken from resource_last_modified, which gives 2020-12-10T00:53:09 in every example. The raw 'Data as of' value is 01-Dec-20, and the unmapped reason says the snapshot date is used. The config and the output disagree, and the observed_at value is not the time the source stated the claim. (suggested: Parse 'Data as of' (01-Dec-20 → 2020-12-01) as observed_at, or change the unmapped reason to match what is actually done. Keep resource_last_modified only as provenance metadata, and record ingested_at separately.)
  - `envelope.valid_from`: valid_from values (e.g. 1982-12-10, 1959-01-05) come from 'Start Date', which appears in neither the fields list nor the unmapped list, so the derivation is undocumented. It is also a licence start date, not the date the claim became true for the entity or venue, so it is semantically unclear. (suggested: Add 'Start Date' to the config with an explicit mapping and reason, e.g. to valid_from documented as licence start date, or to date_registered if that is the meaning. Add it to the unmapped list if it is not used.)
  - `entity.entity_type`: Observations for entity_type are emitted with value 'unknown' and from: null. These are not claims any source made, so they break the rule that every observation traces to a source. (suggested: Stop emitting source-less default observations. Leave entity_type absent, or emit it with a documented derivation level and the source that justified the default.)
  - `observation envelope (licence, source_id, source_record_id, ingested_at, extractor_version)`: The example envelopes contain only observed_at, valid_from and valid_to. The required envelope fields licence, source_id, source_record_id, ingested_at and extractor_version are missing, so the output would fail the envelope contract. (suggested: Populate all required envelope fields. Take licence from the CKAN dataset metadata, or set it to 'unknown' and flag it. Set extractor_version to the config and engine version, and record ingested_at and source_record_id as the row hash.)
- Critique: The field mappings are mostly sound: Licence Name to trading_name, Venue Address to address.full, Data as of to observed_at, and the unmapped entitlement and geocode columns are reasonable. The main meaning problems are that corporate-looking names are never emitted as legal_name, that the stable Licence No is discarded in favour of a row hash, and that default unknown entity_type observations with no source are emitted. The envelope also looks incomplete against the required fields.
  - `entity.trading_name<-Licence Name`: Several Licence Name values read like registered corporate names, not venue names, e.g. 'Mulwala Water Ski Club Ltd', 'Panania East Hills RSL Club Limited', 'Branxton Golf Club Co-operative Limited'. They are stored only as trading_name and entity.legal_name is never emitted, so the legal/trading distinction is lost for the licensee. (suggested: Add a rule or review step for names carrying legal suffixes (Ltd, Limited, Co-operative Limited, Pty Ltd) and emit them as entity.legal_name at a lower field_confidence, keeping venue names as trading_name. Document that the licensee's legal name is not in this source if that is the case.)
  - `observation.source_record_id`: The source has a stable key, Licence No (e.g. LIQC300200213), which is listed as unmapped. The config uses a row hash for record_id instead, which is traceable only to the raw row content and changes if any field is edited. (suggested: Use Licence No as source_record_id (it is traceable to the exact record), and keep the row hash as a secondary content hash.)
  - `entity.entity_type`: An observation with value 'unknown' and from: null is emitted for every row. No source supplied it, so it is a fabricated observation with no provenance, not a claim the source made. (suggested: Do not emit default-valued observations. Leave entity_type absent unless the source states it, or mark it explicitly as a derived default and not as a source observation.)
  - `observation.valid_from`: valid_from is taken from Start Date, which is the liquor licence start date, but it is attached to the entity.trading_name claim as if it were when that name became true. The Start Date is not mapped in the config at all, so its use is undocumented. (suggested: Document the Start Date source in the config and note that it dates the licence, not the name. Alternatively set valid_from only for licence-related claims.)
  - `observation envelope`: The envelope shows only observed_at, valid_from and valid_to. The required fields source_id, ingested_at, licence and extractor_version are missing from the emitted examples. (suggested: Confirm the engine stamps source_id, ingested_at, licence (from CKAN metadata, or 'unknown' with a flag) and extractor_version on every observation.)
- Critique: The mapping is mostly sound: the date parse of 'Data as of' is correct, Trading Status is correctly kept off entity.status, and entity_type defaulting to unknown matches the ontology. The main meaning risk is that the Licence Name column is mapped to trading_name even though many examples look like registered company names. Address completeness is a secondary concern.
  - `entity.trading_name<-Licence Name`: Several Licence Name values are registered-style company names, not venue or trading names. Examples: 'Mulwala Water Ski Club Ltd', 'Panania East Hills RSL Club Limited', 'Branxton Golf Club Co-operative Limited', 'Tumbarumba Bowling Club Limited'. The config reason says these are mostly trading names, but the examples carry legal-entity suffixes (Ltd, Limited, Co-operative Limited). Mapping them to trading_name risks mislabelling registered names as trading names, and legal_name is never populated from this source. (suggested: Check a sample of Licence Name values against the register. Map entity-suffixed names to entity.legal_name (or emit both, with low field_confidence on the uncertain side) and keep venue names such as 'The Glebe Hotel' as trading_name. Correct the reason text so it does not claim the column is mostly trading names.)
  - `address.full<-Venue Address`: Some Venue Address values are not full street addresses. 'Marrickville & Illawarra Rds MARRICKVILLE' is an intersection and 'Maitland Rd MAYFIELD' and 'Caroline St BENDEMEER' have no house number. Mapping them to address.full overstates their completeness, and the field is not parsed into locality, state or postcode. (suggested: Keep the raw value in address.full but record a lower field_confidence for rows without a street number, or add a parsing step that splits out locality. Do not present these values as complete addresses.)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
