# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**.
- 11 model turns, 11 tool calls, $0.0120, 63.15s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r2_1/trace.jsonl`.
- Evidence the agent gave at finish (its words): 3,306 rows, 21 columns read as UTF-8 CSV. Licence No is not unique (one duplicate), so record_id is hash_row. Start Date parses 100% with %d/%m/%Y. Trading Status has only 'Trading' and 'Temporarily ceased trading'. The file has no ABN/ACN column. Licence is unknown; flagged.
- Reason: The dataset lists gaming-licensed hotels and clubs. Only the venue address is mapped with confidence; the name's role (registered vs trading) is not stated by the source, so no entity name is emitted. The licence is unknown and is flagged.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `address.full` ← `Venue Address`: Venue street address with locality in capitals.

## Left unmapped (not guessed)

- `Licence Name`: Licensee/venue name; the source does not say whether it is the registered name or a trading name, so no entity name is mapped
- `Licence No`: Gaming licence number (LIQC/LIQH), not an ABN/ACN; no canonical field
- `Start Date`: Gaming licence start date; not the entity's registration date, so no valid_from
- `Trading Status`: Venue trading state under the licence; not the entity's registered status
- `Latitude`: coordinates; no canonical field
- `Longitude`: coordinates; no canonical field
- `Type`: hotel/club venue type; not a legal entity type
- `Filter Category`: venue category; no canonical field
- `SA2 Name`: statistical area; no canonical field
- `SA2 Band`: policy band; no canonical field
- `Subject to Cap`: policy flag; no canonical field
- `LGA`: local government area; no canonical field
- `Region`: region; no canonical field
- `GME`: gaming machine entitlement count; no canonical field
- `PMP`: poker machine permit count; no canonical field
- `Auth Total`: authorised machine total; no canonical field
- `Unfulfilled Quota`: machine quota count; no canonical field
- `GMT`: gaming machine threshold count; no canonical field
- `EGMs`: gaming machine count; no canonical field
- `Data as of`: snapshot date; observed_at taken from resource metadata instead

## Needs a transform the engine does not have

- `Venue Address`: locality and state/postcode are embedded in the address string; engine cannot split them yet

## Abstentions (fields removed, with reasons)

- `entity.legal_name / entity.trading_name <- Licence Name`: Values carry legal-form suffixes (e.g. 'Ltd', 'Limited') suggesting registered licensee names, but the source does not state it; the critique flagged both legal and trading mapping as unconfirmed. Left out rather than guessed. Status and valid_from also left out (venue licence state and licence start date are not entity claims).
- `valid_from`: blocking critique issue unanswered: The envelope valid_from values (e.g. 1982-03-15 from Start Date 15/03/1982) come from the 'Start Date' column, which does not appear in the config fields or the unmapped list. The column is the licence commencement date, not a statement of when the entity's claim became true, and the mapping is undocumented.

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping has three blocking problems: a licensee or trading name is mapped to legal_name, venue trading status is mapped to the entity's status, and Start Date (a licence date) is used as valid_from without being declared. The remaining points concern trading names, address parsing, the observed_at choice, record keys and the envelope, and are advisory.
  - [blocking] `entity.legal_name<-Licence Name`: The ontology defines legal_name as the registered name, but the source is a liquor/gaming licence holder list. Several examples are venue or trading-style names (e.g. 'The Courts @ East', 'Newmarket Hotel', 'Batlow Hotel'), and the config's own reason admits the name is 'not confirmed as registered name'. The mapping therefore asserts a registered legal name the source does not support. (suggested: Remove the legal_name mapping, or map it to a licensee/holder observation with a distinct field and low field_confidence. Emit venue names as trading_name observations instead.)
  - [blocking] `entity.status<-Trading Status`: 'Trading Status' describes whether the venue is trading under its liquor/gaming licence, not the registered status of the legal entity. Mapping 'Trading' to entity.status 'active' and 'Temporarily ceased trading' to 'suspended' claims something about the company that the source does not state. The Wyong Race Club row shows this: a venue pausing trade is not a suspended entity. (suggested: Do not map to entity.status. Keep the venue trading state as a source-specific observation, or map it only under a venue-level field that exists in the ontology.)
  - [blocking] `valid_from`: The envelope valid_from values (e.g. 1982-03-15 from Start Date 15/03/1982) come from the 'Start Date' column, which does not appear in the config fields or the unmapped list. The column is the licence commencement date, not a statement of when the entity's claim became true, and the mapping is undocumented. (suggested: Remove valid_from derived from Start Date, or document it as licence_start_date with a note that it is not the entity's start date. Add Start Date to the config or the unmapped list so the mapping is traceable.)
  - [advisory] `entity.trading_name`: Venue names such as 'The Courts @ East' and 'Newmarket Hotel' are the trading names the ontology wants captured, but no trading_name mapping exists, so this information is lost. (suggested: Add a trading_name mapping from Licence Name (once legal_name is removed) and emit one observation per name.)
  - [advisory] `address.full<-Venue Address`: The locality is embedded in upper case at the end of the address (e.g. 'SA2 ... STANMORE'), and no locality, state or postcode is parsed out. The address schema has those fields, and the source does not carry a state column, so the mapping is incomplete. (suggested: Parse the trailing capitalised locality into address.locality. Leave state unmapped unless it can be derived deterministically, and record that choice. Keep the raw string in address.full.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified (2020-12-10), while the 'Data as of' column (01-Dec-20) is the snapshot date the source states. The config drops the stated date and keeps the publication timestamp instead. (suggested: Keep the stated snapshot date as an observation field, or document why the publication timestamp is preferred over the source's own 'Data as of'.)
  - [advisory] `observation.source_record_id`: The record_id is a row hash, which is not stable across re-publications. The source supplies a Licence No (LIQC/LIQH identifiers) that could serve as a stable key, and it is listed as unmapped. (suggested: Use Licence No as the source_record_id, with the row hash as a fallback, and document the construction.)
  - [advisory] `entity.status<-Trading Status`: The map_values transform has no default for other Trading Status values, so unexpected values would pass through or fail silently. (suggested: Add a default of unknown for unmatched values and log them.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at and valid dates. Required fields such as source_id, source_record_id, ingested_at, licence and extractor_version are not shown, so it cannot be confirmed that they are populated. (suggested: Show the full envelope in the examples. Set licence from the dataset metadata, or 'unknown' with a flag if none is given.)
- Critique: The unmapped list is sound: Licence No, Start Date, Trading Status, Type and the statistical and machine-count columns correctly have no canonical target, and observed_at from resource metadata is defensible. The main meaning error is Licence Name going to trading_name when its values look like registered legal names; that should be fixed before the field is trusted. The address mapping is acceptable but under-parsed, and the envelope needs confirming.
  - [blocking] `entity.trading_name<-Licence Name`: Licence Name values carry legal-form suffixes such as 'Cyprus Community of NSW Limited', 'Ballina RSL Club Limited', 'East Maitland Bowling Club Ltd' and 'Wyong Race Club Limited'. These read as registered legal names of the licensee, not trading names, and the config's own reason describes it as a venue-style name. Mapping it to trading_name asserts something the source does not state. (suggested: Map Licence Name to entity.legal_name, or leave it unmapped until the source's definition of 'Licence Name' (licensee versus venue) is confirmed. Only map to trading_name if a separate venue name field exists.)
  - [advisory] `entity.entity_type`: An entity_type observation of 'unknown' is emitted for every row with from: null. The source states nothing about entity type, so this is a default being recorded as an observation rather than a source claim. (suggested: Drop the default observation, or keep it only as an explicit engine default flagged as derived and not sourced.)
  - [advisory] `address.full<-Venue Address`: The venue address is mapped whole, with the locality left in capitals inside the string (e.g. '58-76 Stanmore Road STANMORE'). The config notes locality is capitalised but does not parse it, and state and postcode are not extracted even though the dataset is state-specific (NSW licences). (suggested: Parse the trailing locality into address.locality and set address.state to NSW (or the relevant state) with a derivation level noting it is inferred from the dataset. Keep the raw string in address.full.)
  - [advisory] `observation envelope`: The example envelopes show observed_at, valid_from and valid_to but not source_id, source_record_id, ingested_at, licence or extractor_version. Those are required by the ontology and may be set elsewhere, but the examples do not show them. (suggested: Confirm each emitted observation carries all required envelope fields, including the CKAN licence (or 'unknown' with a flag) and the hash-based source_record_id.)

## Examples (raw → value, held-out rows)

- `address.full<-Venue Address`: `58-76 Stanmore Road STANMORE` → `58-76 Stanmore Road STANMORE`; `320 Devonshire Rd KEMPS CREEK` → `320 Devonshire Rd KEMPS CREEK`; `51A-55 King St ASHBURY` → `51A-55 King St ASHBURY`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
