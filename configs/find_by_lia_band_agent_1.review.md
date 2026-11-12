# Review packet (round-2 agent): validated_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0137, 71.39s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_1/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licence Name` | `entity.trading_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Licence Name`: Licence Name holds the venue or licensee-given hotel/club name (e.g. 'Royal Hotel', 'Forbes Inn'); the source does not state it is the registered name, so it is mapped as a trading name, not legal_name.
2. `address.full` ← `Venue Address`: Venue street address of the licensed premises.

## Left unmapped (not guessed)

- `Licence No`: Gaming licence number, not an ABN/ACN; no ontology field.
- `Start Date`: Gaming licence commencement date; not a registration date of the entity and not a clear valid_from for the entity claim; left out.
- `Trading Status`: Venue operating status (Trading / Temporarily ceased trading), not the legal entity's registration status; left out.
- `Latitude`: No ontology field for coordinates.
- `Longitude`: No ontology field for coordinates.
- `Type`: Hotel/club venue type; not an entity_type value (no explicit entity-type column).
- `Filter Category`: Licence size/category label; not an ANZSIC code.
- `SA2 Name`: Statistical area name; no ontology field.
- `SA2 Band`: Regulatory band; no ontology field.
- `Subject to Cap`: Regulatory flag; no ontology field.
- `LGA`: Local government area; no address.locality equivalent.
- `Region`: Metropolitan/Country; no ontology field.
- `GME`: Gaming machine entitlement count; no ontology field.
- `PMP`: Poker machine permit count; no ontology field.
- `Auth Total`: Authorised total EGM count; no ontology field.
- `Unfulfilled Quota`: Quota count; no ontology field.
- `GMT`: Gaming machine threshold count; no ontology field.
- `EGMs`: Installed EGM count; no ontology field.
- `Data as of`: Used for observed_at.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': ['Licence No', 'Venue Address', 'Licence Name'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound on address and the status values, but the legal_name claim is not supported by the source. The source header does not say the name is registered, and several examples look like venue trading names. Envelope completeness and the undocumented valid_from rule also need work before this mapping can be relied on.
  - [blocking] `entity.legal_name<-Licence Name`: The config reason says Licence Name is the registered licensee name, but the source does not say that. Examples such as "Matraville Hotel", "Forbes Inn" and "Riverview Hotel" read as venue or trading names, and the ontology requires legal_name to be as registered, not the trading name. (suggested: Do not map Licence Name to legal_name on the basis of this source. Map it to trading_name, or hold it as an unverified name observation, and correct the reason text so it no longer claims the source states registration.)
  - [advisory] `entity.status<-Trading Status`: Trading Status describes whether a licensed venue is operating, not the registration status of the legal entity. Mapping "Trading" to entity.status 'active' is a stretch, and the source does not say that the entity itself is active. (suggested: Keep the mapping only as a venue-operating-status observation, state that scope in the reason, or drop the entity.status mapping and record the raw value elsewhere.)
  - [advisory] `observation.valid_from`: The examples show valid_from taken from Start Date (for example 9/12/1983 becomes 1983-12-09), but the config has no Start Date mapping. The date is a gaming licence start date, not the date the legal name became true in the world, so the claim is also overstated. (suggested: Add an explicit, documented envelope rule for Start Date, or remove valid_from. Describe it as licence commencement if it is kept.)
  - [advisory] `observation envelope`: The example observations show only observed_at, valid_from and valid_to. Required envelope fields (licence, source_id, source_record_id, ingested_at, extractor_version) are not visible or configured. The config also has no licence entry, although the ontology says the licence comes from CKAN metadata and 'unknown' must be recorded if it is missing. (suggested: Emit all required envelope fields on every observation. Take licence from the CKAN dataset metadata, or record 'unknown' and flag it.)
  - [advisory] `entity.entity_type`: Every example emits an entity_type observation of 'unknown' with from: null. This is a default with no source claim behind it, so it adds an observation the source does not make. (suggested: Do not emit observations for defaults with no source field. Leave entity_type absent, or keep it only as a documented default outside the observation set.)
  - [advisory] `observation.observed_at`: observed_at is set from resource_last_modified (2020-12-10), but the data itself states 'Data as of' 01-Dec-20. The ontology says observed_at is when the source stated the claim, so the snapshot date in the data is the closer match. (suggested: Use the 'Data as of' value for observed_at, or record both and explain which one is used.)
  - [advisory] `address.full<-Venue Address`: The venue address carries a locality and sometimes a state-level context (for example '479 Coast Rd POTTSVILLE'), but address.locality, address.state (NSW) and address.postcode are not produced. Other fields in the set are unused, so the address is less complete than it could be. (suggested: Parse the trailing locality token into address.locality and consider state NSW with country AU, marking the derivation and its field_confidence. Keep address.full as the raw street string.)
- Critique: The mapping is largely sound. Licence Name and Venue Address are mapped to fields their wording supports, and the unmapped columns are reasonably justified. I found no clear case where a value is placed in a field the source contradicts, so no blocking issues. The main concerns are caveats: names that may be registered names, a synthetic entity_type observation with no source, the premises-versus-entity meaning of the address, and an incomplete required envelope in the examples.
  - [advisory] `entity.trading_name<-Licence Name`: Several Licence Name values carry legal-form suffixes ('Pottsville District Bowls & Sports Club Limited', 'Singleton Rugby Club Limited', 'Canowindra Golf Club Ltd'). These look more like registered names than trading names, and the config's own reason says the source does not state either way. Mapping them to trading_name is defensible for a venue name but is a judgement, not something the source says. (suggested: Keep the mapping but record in the reason that the field is a licensee/venue-given name of uncertain legal status, and lower field_confidence for names with Limited/Ltd/Pty suffixes. Do not present it as a verified trading name.)
  - [advisory] `entity.entity_type`: Every example emits an entity.entity_type 'unknown' observation with from: null. No config key produces it, and no source column supports it. It is a synthetic default, not a claim the source made, so it sits oddly with the rule that every observation traces to a source. (suggested: Either drop the default observation entirely or emit it explicitly as a derived default (derivation_level L1, source column null) and document that in the config. Do not present it as a source claim.)
  - [advisory] `address.full<-Venue Address`: The value is the address of the licensed premises (the venue), not the entity's registered or head-office address. The observation's meaning is narrower than address.full implies. The suburb is also left inside the free-text string, and state and postcode are not parsed out. (suggested: Document that this is the premises address. Consider parsing the trailing suburb into address.locality and noting that the state is implied by the dataset context (NSW) rather than stated in each row, with a lower field_confidence on any parsed parts.)
  - [advisory] `observation envelope (source_id, source_record_id, ingested_at, licence, extractor_version)`: The example envelopes show only observed_at, valid_from and valid_to. The ontology marks source_id, source_record_id, ingested_at, licence and extractor_version as required with no exceptions. The licence in particular is not in the config and should come from the CKAN metadata, or be recorded as 'unknown' and flagged. (suggested: Show the full envelope in the examples. Add the licence source (CKAN metadata, or 'unknown' with a finding), the ingested_at timestamp and the extractor_version.)
  - [advisory] `record_id`: record_id is built from three fields, including Venue Address and Licence Name, which can change between releases. Licence No is the stable key for a licence but is not used alone. The config does not say how the three values are combined into the deterministic source_record_id. (suggested: Use Licence No as the primary key, and document the exact concatenation and normalisation if a composite is kept as a fallback.)
  - [advisory] `observation.valid_from`: Start Date is left unmapped on the grounds that it is not a clear valid_from for the entity. It is, however, the date the gaming licence was granted, which may be the closest the source offers to when a claim became true. The examples also show valid_from null throughout. (suggested: Consider mapping Start Date to a licence-level validity claim with a note that it applies to the licence and not the entity, or record in the config why it is excluded.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Licence Name`: `Pottsville District Bowls & Sports Club Limited` → `Pottsville District Bowls & Sports Club Limited`; `Manly Warringah Football Club` → `Manly Warringah Football Club`; `Spring Ridge Country Club Limited` → `Spring Ridge Country Club Limited`
- `address.full<-Venue Address`: `479 Coast Rd POTTSVILLE` → `479 Coast Rd POTTSVILLE`; `101 South Creek Rd CROMER` → `101 South Creek Rd CROMER`; `Darby Rd SPRING RIDGE` → `Darby Rd SPRING RIDGE`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
