# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**, ended by the harness: finish refused 2 times in a row.
- 13 model turns, 13 tool calls, $0.0148, 78.12s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_2/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 2 | `Trading Status` | `entity.status` | map_values({'Trading': 'active', 'Temporarily ceased trading': 'suspended'}) | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `address.full` ← `Venue Address`: Venue street address with locality
2. `entity.status` ← `Trading Status`: Trading status; 'Temporarily ceased trading' mapped to suspended as nearest enum value

## Left unmapped (not guessed)

- `Licence No`: Liquor/gaming licence number (LIQC...), not an ABN/ACN; no entity identifier
- `Data as of`: Constant snapshot date; observed_at comes from resource metadata
- `Type`: Hotel/club premises type; no entity_type mapping defined for premises
- `Filter Category`: Internal venue size/category band
- `Latitude`: Geocode not in ontology
- `Longitude`: Geocode not in ontology
- `SA2 Name`: Statistical area, not in ontology
- `SA2 Band`: Gaming policy band, not in ontology
- `Subject to Cap`: Gaming cap flag, not in ontology
- `LGA`: Local government area, not in ontology
- `Region`: Metropolitan/Country, not in ontology
- `GME`: Gaming machine entitlement count, not in ontology
- `PMP`: Poker machine entitlement count, not in ontology
- `Auth Total`: Authorised machine total, not in ontology
- `Unfulfilled Quota`: Gaming entitlement metric, not in ontology
- `GMT`: Gaming machine total, not in ontology
- `EGMs`: Electronic gaming machine count, not in ontology
- `Licence Name`: abstained by the harness (failed validation or an unanswered critique issue) (entity.trading_name)

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.trading_name<-Licence Name`: blocking critique issue unanswered: The mapping asserts that Licence Name is a venue name and so a trading name, but several rows carry registered-style corporate suffixes ('Charlestown Golf Club Ltd', 'Royal Motor Yacht Club of NSW Limited (Port Hacking Branch)', 'Forbes Services Memorial Club Limited'). The source does not state that these are trading names, so the mapping may be putting a legal name into trading_name.

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly careful, with most gaps correctly unmapped. The main problem is that Licence Name, a venue or premises name, is mapped to entity.legal_name, which the source does not support as a registered name. Status mappings are reasonable but carry caveats, and the envelope and locality parsing need confirmation or enrichment.
  - [blocking] `entity.legal_name<-Licence Name`: The source column is the name on the liquor/gaming licence for a venue, e.g. 'Milton Hotel', 'Wests Mayfield', 'Dangar Island Bowling Club'. Nothing in the source states it is the registered legal name. The ontology defines legal_name as 'As registered. Not the trading name', and the venue name reads as a trading or premises name. The reason's 'treated as the licensee's name' is an assumption the source does not support. (suggested: Do not map Licence Name to entity.legal_name. Map it to entity.trading_name (L0, as stated on the licence), or leave entity names unmapped and keep the licence name as a venue-level observation with a caveat that it is not a registered name.)
  - [advisory] `entity.status<-Trading Status`: 'Trading' is mapped to active. The source says the venue is currently trading, which is a narrower claim than the entity being an active registered company. The mapping also treats licence status as entity status. (suggested: Keep the mapping but note the caveat, or emit it as a venue-trading observation. Consider a separate field rather than entity.status if the ontology allows.)
  - [advisory] `entity.status<-Trading Status`: 'Temporarily ceased trading' is mapped to suspended. The source wording describes a trading state, not a regulatory suspension of the entity, so the nearest enum value is a judgement call. (suggested: Accept as nearest value, but record field_confidence below 1 and derivation_level L1 for this transform, or map to unknown if strictness is preferred.)
  - [advisory] `address.full<-Venue Address`: The locality (e.g. 'HILLSBOROUGH', 'BURRANEER') and the state are embedded in the free-text address and are not parsed. State is implied NSW by the dataset but not stated per row, and postcode is absent. (suggested: Add parsed locality as an L1 derivation from the trailing uppercase token. Set address.state to NSW only with a caveat that it comes from the dataset scope, not the row.)
  - [advisory] `observation.valid_from`: valid_from is taken from 'Start Date', which is the liquor/gaming licence start date for the venue, not the entity's date_registered or the start of the business. The examples show the licence date being used as the claim start. (suggested: Label the value as licence start in the reason, or map it only to a licence-scoped observation rather than to the entity-level envelope.)
  - [advisory] `observation envelope`: The example observation envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, licence, ingested_at and extractor_version are not visible. The record_id hash_row approach is also not described beyond the config key. (suggested: Confirm the emitted envelope carries all required fields. Set licence from the CKAN metadata, or 'unknown' with a flag if absent. Document the row-hash construction for source_record_id.)
  - [advisory] `entity.entity_type`: Every example emits entity_type 'unknown' with from null. This is the correct default under the ontology, but the Type column (club, hotel) and the 'Ltd' suffix in names are not used even as weak evidence. (suggested: Keep unknown as the default. Optionally record Type as a raw premises-type attribute (not entity_type) so it is preserved for later use.)
- Critique: The main meaning error is the status mapping of 'Temporarily ceased trading' to 'suspended', which states a legal status the source does not support. The rest is advisory: an undeclared Start Date used as valid_from, default entity_type observations with no source, a possibly incomplete required envelope, and unparsed address fields. The name, address and 'Trading' to active mappings look correct on these rows.
  - [blocking] `entity.status<-Trading Status`: The map_values rule sends 'Temporarily ceased trading' to 'suspended'. The source only says the venue has temporarily stopped trading. 'Suspended' is a stronger status, and the config's own reason calls it the 'nearest enum value', which means it is a stand-in rather than a meaning the source states. (suggested: Do not map 'Temporarily ceased trading' to 'suspended'. Map it to 'unknown' and keep the raw value, or add an advisory note that it describes a venue trading state, not an entity status.)
  - [advisory] `observation.valid_from`: In every example, valid_from is set from the 'Start Date' column, which is the liquor/gaming licence start date. The config does not declare this source, and the date is not the date the entity or venue name became true. Using it as valid_from is an undocumented mapping that could be read as the company's start date. (suggested: Declare Start Date in the config as a licence-date mapping, or leave valid_from null. If it is kept, note in the reason that it is the licence grant date.)
  - [advisory] `entity.entity_type`: An entity_type observation of 'unknown' is emitted for every row with from: null. This is a default and not a claim the source made. It adds noise rather than information. (suggested: Do not emit a default entity_type observation when no source value exists. Leave the field absent so the default is applied downstream.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown. Because the licence is required and the metadata may not be stated, it must be recorded (or set to 'unknown' and flagged). (suggested: Confirm the full envelope is emitted for every observation, including source_id, source_record_id (the hash_row key), ingested_at, licence from the CKAN metadata (or 'unknown' with a flag), and extractor_version.)
  - [advisory] `address.full<-Venue Address`: The venue address is kept as one string. The state is not in the source, though it is implied as NSW by the dataset. The postcode is absent, and the locality is embedded in the text (for example 'HILLSBOROUGH'). (suggested: Parse locality out of the address string where it is reliable, and set address.state from the dataset context with a documented derivation level, instead of leaving it empty.)
- Critique: The mapping is mostly sound for status and addresses, but the trading_name mapping for Licence Name is unsupported by the rows shown and is the main blocking concern. The remaining points are advisory: the valid_from meaning, the status fallback, envelope completeness and address parsing.
  - [blocking] `entity.trading_name<-Licence Name`: The mapping asserts that Licence Name is a venue name and so a trading name, but several rows carry registered-style corporate suffixes ('Charlestown Golf Club Ltd', 'Royal Motor Yacht Club of NSW Limited (Port Hacking Branch)', 'Forbes Services Memorial Club Limited'). The source does not state that these are trading names, so the mapping may be putting a legal name into trading_name. (suggested: Re-examine what Licence Name denotes (licensee versus venue). If it is the licensee's registered name, map it to entity.legal_name, or hold it as an unresolved observation until the source's meaning is confirmed. Do not rely on the reason text, which the rows do not support.)
  - [advisory] `observation.valid_from`: valid_from is derived from 'Start Date', which is the liquor/gaming licence start date for the venue. It is not stated as the date the entity or trading name became true, so it may not mean what the envelope field means. (suggested: Record the source as licence start date in the observation or a note, or leave valid_from null unless the source says when the claim became true.)
  - [advisory] `entity.status<-Trading Status`: The map_values rule covers only 'Trading' and 'Temporarily ceased trading'. Any other value will fall through unmapped, and 'Temporarily ceased trading' to suspended is a nearest-match judgement rather than a stated equivalence. (suggested: Add an explicit fallback to unknown for unmapped values and note in the config that the suspended mapping is an approximation.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the examples, so the envelope cannot be confirmed as complete. (suggested: Show the full envelope for each emitted observation, including the licence from dataset metadata (or 'unknown' with a flag) and the hash-based source_record_id.)
  - [advisory] `address.full<-Venue Address`: Venue addresses carry a locality and sometimes a postcode-less suburb in capitals (e.g. '1A Barker Ave HILLSBOROUGH'), but state and postcode are not parsed. The data is all NSW or regional NSW, which is derivable but not mapped. (suggested: Consider parsing locality from the address string and deriving state at L1 where the source supports it, keeping address.full as the raw value.)

## Examples (raw → value, held-out rows)

- `address.full<-Venue Address`: `1A Barker Ave HILLSBOROUGH` → `1A Barker Ave HILLSBOROUGH`; `205 Adams Rd LUDDENHAM` → `205 Adams Rd LUDDENHAM`; `3 Evesham Pl THURGOONA` → `3 Evesham Pl THURGOONA`
- `entity.status<-Trading Status`: `Trading` → `active`; `Temporarily ceased trading` → `suspended`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
