# Review packet (round-2 agent): validated_config

**Dataset:** Find by LIA Band — Department of Customer Service  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0115, 56.93s (download and human waits excluded). Trace: `logs/agent_runs/find_by_lia_band_agent_r2_2/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validated on 300 held-out rows: 0 hard failures, parse rate 100% for name and address, record_id hash_row unique. Licence No has one duplicate across the file so it was not used as key. Critique blocking issue (legal_name from venue names) was fixed by remapping to trading_name; remaining issues are advisory.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licence Name` | `entity.trading_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `Venue Address` | `address.full` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Licence Name`: Licence Name is the name on the liquor licence; mostly venue names, so treated as a trading name, not the registered name
2. `address.full` ← `Venue Address`: Venue street address

## Left unmapped (not guessed)

- `Licence No`: licence number, not an ABN/ACN; used only as context
- `Data as of`: snapshot date 01-Dec-20; publication date used as observed_at via metadata
- `Start Date`: licence start date; used as valid_from, not entity date_registered
- `Trading Status`: describes venue trading operations, not entity registration status; no mapping
- `Latitude`: no canonical geo field
- `Longitude`: no canonical geo field
- `Type`: hotel/club venue type, not an entity type
- `Filter Category`: internal licence category, not ANZSIC
- `SA2 Name`: statistical area
- `SA2 Band`: gaming band
- `Subject to Cap`: gaming regulation flag
- `LGA`: no canonical field
- `Region`: no canonical field
- `GME`: gaming count
- `PMP`: gaming count
- `Auth Total`: gaming count
- `Unfulfilled Quota`: gaming count
- `GMT`: gaming count
- `EGMs`: gaming count

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 3306, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main problem is that Licence Name, which is largely venue trading names, is mapped to entity.legal_name, which the ontology defines as the registered name. That mapping is blocking. Other issues are advisory: the observed_at date does not match the stated 'Data as of' reason, Start Date describes the licence rather than the entity, and Trading Status and state are handled without caveats.
  - [blocking] `entity.legal_name<-Licence Name`: Licence Name is mapped to legal_name, but the ontology defines legal_name as the registered name, not a trading name. The config's own reason says many values are venue names, e.g. 'Carrington Hotel', 'Royal Hotel', 'Salisbury Hotel', 'Winners Circle Wallsend', 'Richmond Inn Hotel'. Those are trading names, and the source does not state a registered name. Only names with a company suffix such as 'Ltd' or 'Limited' could plausibly be registered names, and even those are the licence holder's name, not verified as registered. (suggested: Do not emit entity.legal_name from Licence Name. Emit it as a trading_name observation (venue name, L0), or hold it as a licence-name observation with a note that it is not a registered legal name. Leave legal_name unset until an ABN/ACN-bearing source supports it.)
  - [advisory] `observed_at`: The snapshot is 'Data as of' 01-Dec-20, and the unmapped reason says this is what observed_at captures. The emitted observed_at is 2020-12-10, which comes from resource_last_modified. The two do not match, so the stated reason for dropping 'Data as of' is not what the engine does. (suggested: Confirm whether observed_at should be the publication/last-modified date (10 Dec) or the snapshot date (1 Dec). Either keep resource_last_modified and fix the unmapped reason, or record 'Data as of' as observed_at and keep the publication date elsewhere.)
  - [advisory] `valid_from<-Start Date`: Start Date is the date the venue licence started. valid_from is meant to be when the claim became true in the world. The claim here is about the licence, not the entity or business. The dates also parse correctly, e.g. '2/02/1953' becomes 1953-02-02. (suggested: Keep the mapping but annotate it as licence start date, or record it under a licence-specific claim so it is not read as the business's date_registered.)
  - [advisory] `status<-Trading Status`: Trading Status is listed as unmapped with 'no clean canonical mapping', but its value 'Trading' is close to the status enum value 'active'. The mapping drops the signal without recording why, and 'Trading' describes the venue's operations, not the entity's registration status. (suggested: Either leave it unmapped and state explicitly that it describes venue trading rather than entity status, or map it to status only with a caveat and a lower field_confidence.)
  - [advisory] `address.state`: address.full is mapped, but state and postcode are not, and the source has no state column. Region ('Metropolitan'/'Country') is not a state. The records are NSW-only, which is inferable from the dataset context but not stated per row. (suggested: Leave state unset, or set it to NSW with derivation_level L1 or L0 and a note that it comes from the dataset scope rather than each row.)
- Critique: The mapping is mostly sound. Licence Name to trading_name and Venue Address to address.full match their source meanings, and the dates parse correctly with dd/mm ordering. The problems are caveats rather than wrong-field errors: valid_from as a proxy for the name claim, default entity_type observations with no source, legal-form names kept as trading names, a hash-based record key that ignores the stable Licence No, and envelope fields not visible in the examples.
  - [advisory] `observation.valid_from`: valid_from is set from the licence 'Start Date' (e.g. 'Bardwell Valley Golf Club' 1983-04-22). The source states when the liquor licence started, not when the Licence Name became the trading name, so the envelope implies a claim the source does not make. (suggested: Keep the licence start in a licence-specific note or leave valid_from null unless the name's start is known. If kept, document in the config that valid_from is the licence start, a proxy for the name claim.)
  - [advisory] `entity.entity_type`: Every example emits an 'entity.entity_type' = 'unknown' observation with from: null. The source says nothing about entity type, so this is a default being written out as a sourced observation rather than an absence of one. (suggested: Do not emit entity_type observations for rows where the source gives no entity signal. If a default is wanted, apply it at read time, not as an observation with a source record.)
  - [advisory] `entity.trading_name<-Licence Name`: Some Licence Names carry legal-form suffixes ('South Sydney Graphic Arts Club Limited', 'Croppa Creek Bowling Club Ltd', 'Humula Citizens Sports Club Limited'). These look closer to registered names than trading names, and legal_name is never mapped. (suggested: Keep the trading_name mapping for venue names, but note the suffix cases as possible legal names and flag them for review. Do not fabricate a legal_name from them without a registry match.)
  - [advisory] `observation.source_record_id`: record_id uses hash_row over the whole row, although 'Licence No' is a stable source key. Any change in a non-key column (for example gaming counts) would produce a new source_record_id for the same licence. (suggested: Build source_record_id deterministically from 'Licence No' (for example 'LIQC...' or 'LIQH...') and document the construction, as the ontology requires.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, ingested_at, licence (with 'unknown' flagged if absent) and extractor_version are not visible in the emitted observations. (suggested: Confirm that every emitted observation carries source_id, ingested_at, licence (from CKAN metadata, or 'unknown' plus a finding) and extractor_version.)
  - [advisory] `address.full<-Venue Address`: The venue address has no state or postcode, and address.state is not mapped. Region ('Metropolitan'/'Country') is not a state, so it must not be used for address.state. (suggested: Leave address.state unmapped. Optionally parse a postcode or state from the address text if one is present, recording the parsing at derivation level L1.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Licence Name`: `Bardwell Valley Golf Club` → `Bardwell Valley Golf Club`; `Callala RSL Country Club` → `Callala RSL Country Club`; `German-Austrian Society of Australia Ltd` → `German-Austrian Society of Australia Ltd`
- `address.full<-Venue Address`: `2A Hillcrest Ave BARDWELL VALLEY` → `2A Hillcrest Ave BARDWELL VALLEY`; `43 Callala Beach Rd CALLALA BEACH` → `43 Callala Beach Rd CALLALA BEACH`; `73-75 Curtin St CABRAMATTA` → `73-75 Curtin St CABRAMATTA`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
