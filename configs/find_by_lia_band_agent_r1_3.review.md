# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**.
- 12 model turns, 12 tool calls, $0.0104, 50.04s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r1_3/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate call 3: 0 hard failures, record_id hash_row unique over 3306 rows, parse rates 1.0 for address and 0.9467 for status (the 5.3% 'Temporarily ceased trading' rows are not interpreted). Critique c-0879ddc7 (blocking: Licence Name as legal_name) addressed by removing the mapping. Critique advisories on observed_at, envelope and address parsing were not acted on; observed_at uses resource metadata per the snapshot-register rule.
- Reason: The file is a venue-level gaming licence register with no ABN/ACN and names that are venue/licensee names, so no reliable legal_name mapping exists. Only venue address, venue trading status and licence start date were mapped.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|

The model's reasons per field (its words, not verified):


## Left unmapped (not guessed)

- `Licence Name`: Licensee/venue name; not stated as registered legal name; not mapped to legal_name
- `Data as of`: Snapshot date
- `Licence No`: LIQC licence number, not ABN/ACN
- `Start Date`: Used as valid_from
- `Type`: Venue type
- `Filter Category`: Internal category
- `Latitude`: geo
- `Longitude`: geo
- `SA2 Name`: statistical area
- `SA2 Band`: gaming band
- `Subject to Cap`: gaming cap flag
- `LGA`: no canonical locality field
- `Region`: metro/country flag
- `GME`: gaming count
- `PMP`: gaming count
- `Auth Total`: gaming count
- `Unfulfilled Quota`: gaming count
- `GMT`: gaming count
- `EGMs`: gaming count
- `Trading Status`: abstained by the harness (failed validation or an unanswered critique issue) (entity.status)
- `Venue Address`: abstained by the harness (failed validation or an unanswered critique issue) (address.full)

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-Licence Name`: Licence holder/venue names (e.g. 'Imperial Hotel') are not stated as registered names; mapping them to legal_name would be a wrong claim. No ABN/ACN in the file to confirm.
- `observation.observed_at`: critique issue unanswered: observed_at is taken from resource_last_modified (2020-12-10T00:53:09), but the source states 'Data as of 01-Dec-20' in every row. The envelope should reflect what the source stated, and the snapshot date is currently discarded.
- `observation`: critique issue unanswered: The envelope shown in the examples omits required fields: source_id, ingested_at, licence, and extractor_version. The source_record_id is hash_row, which is deterministic but not tied to the stable Licence No column that is available.
- `entity.entity_type`: critique issue unanswered: Every row emits an entity.entity_type observation of 'unknown' with from: null. This is a default filler, not a claim the source made, yet it is emitted as an observation.
- `address.full<-Venue Address`: critique issue unanswered: Venue Address is mapped whole, but several values are incomplete or include venue names, e.g. 'Wodonga Pl ALBURY' and 'The Portico TOONGABBIE'. Postcode and state are not extracted, even though the register is NSW-only and the source contains enough to parse part of the address.
- `valid_from<-Start Date`: critique issue unanswered: Start Date is the date the venue licence started, not the date the licensee entity or company was registered. It is applied to every observation as valid_from, including the status observation, which broadens its meaning.
- `entity.status<-Trading Status`: critique issue unanswered: Mapping 'Trading' to active is reasonable, but the config says 'Temporarily ceased trading' is not interpreted. The examples only show 'Trading', so the mapping is not tested on the other values. The source status also describes the venue's trading, not the legal entity's status.

## Checks

- Critique: The Licence Name to legal_name mapping is the main meaning error: venue names such as 'Imperial Hotel' are presented as registered legal names. The date parsing (dd/mm/yyyy to valid_from) and the Trading to active mapping check out. The remaining issues are envelope completeness, the observed_at source, and a default-unknown observation with no source.
  - [blocking] `entity.legal_name<-Licence Name`: The source column is a licence holder name, and several examples are venue names rather than registered names: 'Imperial Hotel', 'Toongabbie Hotel', 'Tydvil Hotel', 'Astor Hotel', 'The Crescent Hotel'. The ontology says legal_name is as registered and not the trading name, and the source does not state a registered name, so these values should not be emitted as legal_name. (suggested: Stop mapping Licence Name to entity.legal_name. Emit it as a trading_name observation (venue name) instead, or keep it as an unmapped licensee-name claim. Only map to legal_name where the source states a registered company name, such as the 'Ltd' or 'Limited' clubs, and even then record it as licensee name with a lower field_confidence.)
  - [advisory] `observation.observed_at`: observed_at is taken from resource_last_modified (2020-12-10T00:53:09), but the source states 'Data as of 01-Dec-20' in every row. The envelope should reflect what the source stated, and the snapshot date is currently discarded. (suggested: Set observed_at to 2020-12-01 from the 'Data as of' column, or keep the metadata timestamp as a separate field and document the difference.)
  - [advisory] `observation`: The envelope shown in the examples omits required fields: source_id, ingested_at, licence, and extractor_version. The source_record_id is hash_row, which is deterministic but not tied to the stable Licence No column that is available. (suggested: Populate all required envelope fields in every observation. Consider source_record_id from 'Licence No' (plus a hash fallback) so records stay traceable to the exact raw row, and document how the key is built.)
  - [advisory] `entity.entity_type`: Every row emits an entity.entity_type observation of 'unknown' with from: null. This is a default filler, not a claim the source made, yet it is emitted as an observation. (suggested: Do not emit default-value observations with no source column. Leave entity_type absent, or flag it clearly as a default rather than a source observation.)
  - [advisory] `address.full<-Venue Address`: Venue Address is mapped whole, but several values are incomplete or include venue names, e.g. 'Wodonga Pl ALBURY' and 'The Portico TOONGABBIE'. Postcode and state are not extracted, even though the register is NSW-only and the source contains enough to parse part of the address. (suggested: Keep address.full as is, but parse locality where it is cleanly present (e.g. the trailing uppercase suburb), and consider address.state = NSW as a documented L1 derivation from the dataset scope. Flag addresses that lack a street number or road type.)
  - [advisory] `valid_from<-Start Date`: Start Date is the date the venue licence started, not the date the licensee entity or company was registered. It is applied to every observation as valid_from, including the status observation, which broadens its meaning. (suggested: Document that valid_from here means licence start. Consider limiting it to the licence-related observations or to a licence-specific field rather than the entity-level claims.)
  - [advisory] `entity.status<-Trading Status`: Mapping 'Trading' to active is reasonable, but the config says 'Temporarily ceased trading' is not interpreted. The examples only show 'Trading', so the mapping is not tested on the other values. The source status also describes the venue's trading, not the legal entity's status. (suggested: Keep the map, but state in the reason that this describes venue trading status, not entity registration status. Add a test for the ceased-trading value and confirm unmapped values are dropped rather than defaulted.)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
