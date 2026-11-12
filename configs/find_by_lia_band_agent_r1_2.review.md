# Review packet (round-2 agent): partial_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **partial_config**.
- 12 model turns, 12 tool calls, $0.0122, 63.4s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r1_2/trace.jsonl`.
- Evidence the agent gave at finish (its words): 3,306 rows, 21 columns; Licence No unique except one duplicate (hash_row used); Start Date parses 100% as dd/mm/yyyy; Venue Address parses 100%. Licence Name semantics ambiguous (venue names, some with 'Limited'). Trading Status has 'Temporarily ceased trading' not in the status enum.
- Reason: The register has useful venue addresses and licence start dates, but the name column cannot be assigned to legal_name or trading_name with confidence, and the operating-status column has no safe enum mapping. The config maps address and valid_from only.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `address.full` ← `Venue Address`: Venue street address

## Left unmapped (not guessed)

- `Licence Name`: Venue/premises name; the source does not say whether it is the registered legal name or a trading name, so neither entity.legal_name nor entity.trading_name is asserted
- `Data as of`: snapshot date; observed_at uses resource_last_modified
- `Licence No`: licence number; not unique across the file (one duplicate), so record_id is hashed
- `Type`: venue type (hotel/club) is not an entity type; not mapped
- `Trading Status`: liquor licence operating state, not registration status; no safe enum mapping
- `Latitude`: no ontology field
- `Longitude`: no ontology field
- `Filter Category`: gaming category, no ontology field
- `SA2 Name`: statistical area, no ontology field
- `SA2 Band`: gaming policy band
- `Subject to Cap`: gaming policy flag
- `LGA`: no ontology field
- `Region`: no ontology field
- `GME`: entitlement count
- `PMP`: entitlement count
- `Auth Total`: entitlement count
- `Unfulfilled Quota`: entitlement count
- `GMT`: entitlement count
- `EGMs`: entitlement count

## Needs a transform the engine does not have

- `Trading Status`: needs a licence-operating-state field; no ontology field fits

## Abstentions (fields removed, with reasons)

- `entity.legal_name / entity.trading_name <- Licence Name`: Column holds venue/premises names, some with company suffixes; source does not state whether it is the registered name, so no name mapping is asserted.
- `entity.status <- Trading Status`: Liquor-licence operating state ('Trading', 'Temporarily ceased trading') does not map safely to the registration status enum.
- `observation.valid_from`: critique issue unanswered: The envelope sets valid_from from 'Start Date', but the config neither maps nor lists Start Date (it appears in neither fields nor unmapped). The date is the licence start date, not a date on which the name or the active status became true, so using it as valid_from for these claims overstates what the source says. It may be closer to date_registered.

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main problem is that the venue name column is mapped to legal_name, which the source does not support; it should be a trading name. The status mapping and the valid_from and observed_at envelope choices need explicit documentation, and the envelope's licence and source_id need confirming.
  - [blocking] `entity.legal_name<-Licence Name`: The source column holds the venue or premises name (e.g. 'Glenmore Hotel', 'Garden Hotel', 'Public House Albury', 'Cassilis Bowling Club'), not a registered legal name. The config's own reason calls it the 'licensed venue/operator' name. The ontology defines legal_name as the name as registered, not the trading name, and nothing in the source says these are registered names. Several rows are clearly trading-style names, so mapping them to legal_name asserts something the source does not support. (suggested: Map 'Licence Name' to entity.trading_name (one observation per row), and do not emit entity.legal_name from this column. Only emit legal_name from a source that states a registered name, such as a company register.)
  - [advisory] `entity.status<-Trading Status`: 'Trading' is a liquor-licence operating state for a venue, not the registration status the ontology's status enum describes. Only 'Trading' is mapped, so any other value in the Trading Status column will fall through without a documented result. The config does not say what happens to unmapped values. (suggested: Document the mapping as a licence trading state, consider a field that records that meaning, and state explicitly how other Trading Status values are handled (for example, unknown with a note) rather than leaving them implicit.)
  - [advisory] `observation.valid_from`: The envelope sets valid_from from 'Start Date', but the config neither maps nor lists Start Date (it appears in neither fields nor unmapped). The date is the licence start date, not a date on which the name or the active status became true, so using it as valid_from for these claims overstates what the source says. It may be closer to date_registered. (suggested: Add Start Date to the config explicitly. Either map it to date_registered (if licence start is accepted as the venue's registration date) or document why it is used as valid_from and what it does and does not mean. Also list it in unmapped if it is not used.)
  - [advisory] `observation.observed_at`: observed_at is 2020-12-10, taken from resource_last_modified, while the file's 'Data as of' column says 01-Dec-20. The ontology says observed_at is when the source stated the claim, and the snapshot date is the better match for that. (suggested: Derive observed_at from the 'Data as of' value (2020-12-01) or document why the metadata timestamp is used and that it may be later than the snapshot date.)
  - [advisory] `observation.source_id, observation.licence, observation.source_record_id`: The config does not show the required envelope values for source_id or licence. Licence has to come from the dataset metadata and is required; it is not visible here, so it may be missing or unknown without a flag. (suggested: Confirm source_id is set, pull the licence from the CKAN metadata (record 'unknown' and flag it if none), and document the hashed record_id construction for source_record_id.)
  - [advisory] `address.state`: The address observation has only the street-style venue address. Locality, postcode and state are not mapped, although the dataset is NSW-only and the LGA and SA2 columns could support parsing. (suggested: Consider deriving address.state as NSW from the dataset context and recording it at a lower derivation level, and parse locality and postcode from the address text where the source supports it.)
- Critique: The mapping is mostly sound: dates parse correctly (dd/mm/yyyy to ISO, including single-digit days and months), the address mapping matches the venue address, and the unmapped gaming and statistical columns are reasonably justified. The main concern is that Licence Name is asserted to be a trading name when some values look like registered legal names, which the source does not support. Advisory points cover the meaning of valid_from and the missed address parsing.
  - [blocking] `entity.trading_name<-Licence Name`: The config maps 'Licence Name' to entity.trading_name and says it is a premises name, not a registered legal name. The source does not state that. Several values look like registered company names, e.g. 'Kurnell Community Sports and Recreation Club Limited' and 'Sussex Inlet Golf Club Limited' (the 'Limited' suffix). Those may be legal names, so the claim that this is a trading name is not supported by the source. (suggested: Keep the observation but do not assert its meaning as trading_name without support. Either map it to a neutral licence-name field if one exists, or record it with lower field_confidence and a note that it may be the registered legal name. Flag the 'Limited' suffix cases for review.)
  - [advisory] `valid_from`: valid_from is set from 'Start Date', which is the liquor licence start date. That is when the licence began, not necessarily when the entity or its trading name became true. (suggested: Document that valid_from here means licence start, or move the licence-level date into a note on the observation so it is not read as entity registration.)
  - [advisory] `address.full<-Venue Address`: Venue Address is mapped in full with only whitespace cleaning. The source contains a locality in uppercase (e.g. 'KURNELL', 'THE ROCKS') that is not split out. Every row is in NSW, but address.state and address.country are not set, and no postcode is available. (suggested: Optionally parse the trailing locality into address.locality and set address.country to AU. Consider address.state = NSW only if the source is documented as NSW-only. Keep address.full as the raw address.)
  - [advisory] `entity.entity_type`: Each example emits entity_type 'unknown' with no source field. This is consistent with the default-to-unknown rule, but the 'Type' column (club/hotel) is the venue type, not an entity type, so the 'unknown' is the correct outcome and not a finding in itself. (suggested: No change needed. Consider noting in the config that venue Type was deliberately not used for entity_type, so the reason is visible to later reviewers.)

## Examples (raw → value, held-out rows)

- `address.full<-Venue Address`: `Captain Cook Dr KURNELL` → `Captain Cook Dr KURNELL`; `3 Evesham Pl THURGOONA` → `3 Evesham Pl THURGOONA`; `Stonecutters Dr COLEBEE` → `Stonecutters Dr COLEBEE`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
