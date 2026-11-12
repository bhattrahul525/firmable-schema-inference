# Review packet (round-2 agent): partial_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_1991_2000.csv` (sha256 `026226216093…`)

## How this ended

- Outcome **partial_config**.
- 15 model turns, 15 tool calls, $0.0168, 180.42s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_06/trace.jsonl`.
- Reason: The dataset is a research extract of IP applicant activity. Only the ABN (for ABN-typed party ids), address and country fields are supported as entity claims; the applicant name is not a registered name.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})\.0$) → abn | W | 0.85 | 94.8% | **0.85** |
| 2 | `state_code` | `address.state` | upper → state_code | W | 0.85 | 93.4% | **0.85** |
| 3 | `post_code` | `address.postcode` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 4 | `country_code` | `address.country` | upper | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: where lord_party_id_type is abn the id is an 11-digit ABN stored as a float string; checksum validated; party_id rows do not match the regex
2. `address.state` ← `state_code`: Australian state code of the applicant; foreign regions are rejected
3. `address.postcode` ← `post_code`: applicant postcode
4. `address.country` ← `country_code`: ISO country code of applicant

## Left unmapped (not guessed)

- `party_name`: applicant name as filed with IP office; not stated to be the registered name, so not mapped to legal_name; contains placeholder hashes and descriptors
- `lord_party_id_type`: internal flag: party_id vs abn
- `lord_party_id`: used only for record_id and abn
- `financial_year`: activity period, not a claim start/end date; used only for record_id
- `d_first_earliest_filed_financial_year`: first-activity year statistic
- `pbr_first_earliest_filed_financial_year`: first-activity year statistic
- `tm_first_earliest_filed_financial_year`: first-activity year statistic
- `d_first_gained_enforceable_status_financial_year`: IP status statistic
- `pbr_first_gained_enforceable_status_financial_year`: IP status statistic
- `tm_first_gained_enforceable_status_financial_year`: IP status statistic
- `d_filed_count`: IP activity count
- `pbr_filed_count`: IP activity count
- `tm_filed_count`: IP activity count
- `d_granted_count`: IP activity count
- `pbr_granted_count`: IP activity count
- `tm_granted_count`: IP activity count
- `d_retired_count`: IP activity count
- `pbr_retired_count`: IP activity count
- `tm_retired_count`: IP activity count
- `d_enforceable_count`: IP activity count
- `pbr_enforceable_count`: IP activity count
- `tm_enforceable_count`: IP activity count
- `tm_services_filed_count`: IP activity count
- `tm_services_granted_count`: IP activity count
- `tm_services_retired_count`: IP activity count
- `tm_services_enforceable_count`: IP activity count
- `d_filed_weighted_count`: weighted IP activity measure
- `pbr_filed_weighted_count`: weighted IP activity measure
- `tm_filed_weighted_count`: weighted IP activity measure
- `d_granted_weighted_count`: weighted IP activity measure
- `pbr_granted_weighted_count`: weighted IP activity measure
- `tm_granted_weighted_count`: weighted IP activity measure
- `d_retired_weighted_count`: weighted IP activity measure
- `pbr_retired_weighted_count`: weighted IP activity measure
- `tm_retired_weighted_count`: weighted IP activity measure
- `d_enforceable_weighted_count`: weighted IP activity measure
- `pbr_enforceable_weighted_count`: weighted IP activity measure
- `tm_enforceable_weighted_count`: weighted IP activity measure
- `tm_services_filed_weighted_count`: weighted IP activity measure
- `tm_services_granted_weighted_count`: weighted IP activity measure
- `tm_services_enforceable_weighted_count`: weighted IP activity measure
- `tm_services_retired_weighted_count`: weighted IP activity measure
- `d_enforceable_class_scope`: IP classification scope code
- `d_filed_class_scope`: IP classification scope code
- `d_filed_modal_class`: IP classification code
- `d_granted_class_scope`: IP classification scope code
- `d_retired_class_scope`: IP classification scope code
- `pbr_enforceable_class_scope`: IP classification scope code
- `pbr_enforceable_modal_class`: IP classification code
- `pbr_filed_class_scope`: IP classification scope code
- `pbr_filed_modal_class`: IP classification code
- `pbr_granted_class_scope`: IP classification scope code
- `pbr_granted_modal_class`: IP classification code
- `pbr_retired_class_scope`: IP classification scope code
- `pbr_retired_modal_class`: IP classification code
- `tm_enforceable_class_scope`: IP classification scope code
- `tm_filed_class_scope`: IP classification scope code
- `tm_granted_class_scope`: IP classification scope code
- `tm_retired_class_scope`: IP classification scope code
- `tm_services_enforceable_class_scope`: IP classification scope code
- `tm_services_filed_class_scope`: IP classification scope code
- `tm_services_granted_class_scope`: IP classification scope code
- `tm_services_retired_class_scope`: IP classification scope code

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-party_name`: IP applicant name is not stated to be the registered name; critique flagged placeholder hashes and descriptors
- `entity.entity_type<-party_name`: no explicit entity-type column; suffix inference would be a guess, so the engine records unknown

## Checks

- Duplicate record ids in held-out rows: {'rows': 771203, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping has two blocking problems: party_name is mapped to legal_name ('as registered') even though the source is an applicant name and some values are hash placeholders, and entity_type is set to 'company' from name suffixes when the ontology says to default to unknown. The state, postcode, country and ABN checksums check out in the examples (53006970421 and 87154241960 both validate). The remaining points are advisory: the abn transform lacks the lord_party_id_type condition its reason describes, the envelope is incomplete in the examples, observed_at uses file last-modified time, and a jurisdiction descriptor remains in one name.
  - [blocking] `entity.legal_name<-party_name`: party_name is the applicant name as filed with the IP office, which the config's own reason says is not necessarily the registered name. The ontology defines legal_name as 'as registered', so the mapping asserts a claim the source does not support. Several examples also carry hashed placeholder strings (e.g. 't0ed1ab56...', 't48e937c...', 'tad4384f...') that are not names at all, yet they are emitted as legal_name. (suggested: Do not map party_name to entity.legal_name. Emit it as a non-registered applicant-name observation (or a trading-name-style claim with a distinct source field), and drop or quarantine placeholder hash values such as 32-character hex strings instead of emitting them as names.)
  - [blocking] `entity.entity_type<-party_name`: The suffix rule infers entity_type from the name, but the source does not state an entity type. The ontology says to default to unknown because guessing causes downstream harm. The example 'evergreen holdings ltd' (country GB) and 'associated newspapers limited' are emitted as 'company' purely from the suffix, and 'bio oils australia pty ltd' likewise. This is a value mapped to a meaning the source does not state, and no derivation level is recorded. (suggested: Emit entity_type as 'unknown' from the IP source, or, if the suffix rule is kept, record it as an L3-style name-inference with low field_confidence and a derivation_level set accordingly, rather than as a sourced company claim.)
  - [advisory] `entity.abn<-lord_party_id`: The config's reason says the transform applies only where lord_party_id_type is 'abn', but the field mapping has no condition on lord_party_id_type. Rows with lord_party_id_type 'party_id' rely only on the 11-digit regex to avoid emitting an ABN, so a party_id that happens to be 11 digits with a valid checksum would be wrongly emitted as an ABN. The example 'evergreen holdings ltd' (ABN 53006970421, country GB) also shows an Australian identifier attached to a non-Australian applicant, which is worth a note. (suggested: Gate the abn transform on lord_party_id_type == 'abn' explicitly. Add a note or a flag for ABN observations whose country_code is not AU.)
  - [advisory] `observation.envelope`: The envelope in the examples shows only observed_at, valid_from and valid_to. The required fields source_id, source_record_id (the record_id construction is in config but not shown on the observation), ingested_at, licence and extractor_version are not visible. The config also has no licence or source_id entry, and the licence should be recorded as 'unknown' and flagged if the CKAN metadata lacks one. (suggested: Confirm the emitted envelope includes all required observation fields, including licence (or 'unknown' with a finding) and extractor_version, and that source_record_id is documented as the lord_party_id plus financial_year construction.)
  - [advisory] `observation.observed_at`: observed_at is set from resource_last_modified (2023-08-29 for every row). That is when the dataset file was last changed, not when the source stated each claim, and it is the same for all rows regardless of financial_year. (suggested: Keep resource_last_modified only as a documented proxy, or derive observed_at from the financial_year, and record which basis was used.)
  - [advisory] `entity.legal_name<-party_name (descriptor suffix)`: The example 'western brands llc a california corporation' keeps the jurisdiction descriptor 'a california corporation' inside the name. clean_whitespace does not separate this from the name, so even after the legal_name issue is fixed the value would not be a clean registered name. (suggested: Strip or split trailing jurisdiction descriptors into a separate note or field, and do not treat the remainder as a registered name.)

## Examples (raw → value, held-out rows)

- `address.state<-state_code`: `vic` → `VIC`; `nsw` → `NSW`; `qld` → `QLD`
- `address.postcode<-post_code`: `3018` → `3018`; `2000` → `2000`; `3192` → `3192`
- `address.country<-country_code`: `au` → `AU`; `es` → `ES`; `gb` → `GB`
- `entity.abn<-lord_party_id`: `11000017596.0` → `11000017596`; `11116066329.0` → `11116066329`; `13109140838.0` → `13109140838`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
