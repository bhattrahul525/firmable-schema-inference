# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **validated_config**.
- 13 model turns, 13 tool calls, $0.0167, 147.04s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded iplord_2001_2005.csv (675,929 rows, 77 columns); record key lord_party_id+financial_year unique; ABN-type ids parsed via regex and abn checksum; validate passed with 0 unaccounted columns on second call.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})\.0$) → abn | W | 0.85 | 100.0% | **0.85** |
| 2 | `state_code` | `address.state` | clean_whitespace → state_code | W | 0.80 | 94.2% | **0.80** |
| 3 | `post_code` | `address.postcode` | clean_whitespace → postcode | W | 0.70 | 92.9% | **0.70** |
| 4 | `country_code` | `address.country` | upper | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: rows with lord_party_id_type=abn carry an 11-digit ABN stored as a float string; party_id-type rows are internal ids and are skipped by the regex
2. `address.state` ← `state_code`: Australian state code of the party; foreign regions are rejected
3. `address.postcode` ← `post_code`: postcode of the party address; foreign codes are rejected
4. `address.country` ← `country_code`: two-letter ISO country code of the party

## Left unmapped (not guessed)

- `party_name`: IP applicant name, not stated as registered name; some values are opaque hash tokens, so not emitted as legal_name
- `lord_party_id_type`: tells internal party_id versus ABN; used only for interpretation
- `lord_party_id`: internal party_id numbers for party_id-type rows; ABN part mapped separately
- `financial_year`: reporting year of the counts, not a statement date of the claim; no valid_from/valid_to
- `d_first_earliest_filed_financial_year`: IP statistics, no ontology field
- `pbr_first_earliest_filed_financial_year`: IP statistics, no ontology field
- `tm_first_earliest_filed_financial_year`: IP statistics, no ontology field
- `d_first_gained_enforceable_status_financial_year`: IP statistics, no ontology field
- `pbr_first_gained_enforceable_status_financial_year`: IP statistics, no ontology field
- `tm_first_gained_enforceable_status_financial_year`: IP statistics, no ontology field
- `d_filed_count`: IP count, no ontology field
- `pbr_filed_count`: IP count, no ontology field
- `tm_filed_count`: IP count, no ontology field
- `d_granted_count`: IP count, no ontology field
- `pbr_granted_count`: IP count, no ontology field
- `tm_granted_count`: IP count, no ontology field
- `d_retired_count`: IP count, no ontology field
- `pbr_retired_count`: IP count, no ontology field
- `tm_retired_count`: IP count, no ontology field
- `d_enforceable_count`: IP count, no ontology field
- `pbr_enforceable_count`: IP count, no ontology field
- `tm_enforceable_count`: IP count, no ontology field
- `tm_services_filed_count`: IP count, no ontology field
- `tm_services_granted_count`: IP count, no ontology field
- `tm_services_retired_count`: IP count, no ontology field
- `tm_services_enforceable_count`: IP count, no ontology field
- `d_filed_weighted_count`: IP weighted count, no ontology field
- `pbr_filed_weighted_count`: IP weighted count, no ontology field
- `tm_filed_weighted_count`: IP weighted count, no ontology field
- `d_granted_weighted_count`: IP weighted count, no ontology field
- `pbr_granted_weighted_count`: IP weighted count, no ontology field
- `tm_granted_weighted_count`: IP weighted count, no ontology field
- `d_retired_weighted_count`: IP weighted count, no ontology field
- `pbr_retired_weighted_count`: IP weighted count, no ontology field
- `tm_retired_weighted_count`: IP weighted count, no ontology field
- `d_enforceable_weighted_count`: IP weighted count, no ontology field
- `pbr_enforceable_weighted_count`: IP weighted count, no ontology field
- `d_enforceable_class_scope`: IP class-scope attribute, no ontology field
- `d_enforceable_modal_class`: IP class attribute, no ontology field
- `d_filed_class_scope`: IP class-scope attribute, no ontology field
- `d_filed_modal_class`: IP class attribute, no ontology field
- `d_granted_class_scope`: IP class-scope attribute, no ontology field
- `d_granted_modal_class`: IP class attribute, no ontology field
- `d_retired_class_scope`: IP class-scope attribute, no ontology field
- `pbr_enforceable_class_scope`: IP class-scope attribute, no ontology field
- `pbr_enforceable_modal_class`: IP class attribute, no ontology field
- `pbr_filed_class_scope`: IP class-scope attribute, no ontology field
- `pbr_filed_modal_class`: IP class attribute, no ontology field
- `pbr_granted_class_scope`: IP class-scope attribute, no ontology field
- `pbr_granted_modal_class`: IP class attribute, no ontology field
- `pbr_retired_class_scope`: IP class-scope attribute, no ontology field
- `pbr_retired_modal_class`: IP class attribute, no ontology field
- `tm_enforceable_class_scope`: IP class-scope attribute, no ontology field
- `tm_enforceable_weighted_count`: IP weighted count, no ontology field
- `tm_filed_class_scope`: IP class-scope attribute, no ontology field
- `tm_granted_class_scope`: IP class-scope attribute, no ontology field
- `tm_retired_class_scope`: IP class-scope attribute, no ontology field
- `tm_services_enforceable_class_scope`: IP class-scope attribute, no ontology field
- `tm_services_enforceable_weighted_count`: IP weighted count, no ontology field
- `tm_services_filed_class_scope`: IP class-scope attribute, no ontology field
- `tm_services_filed_weighted_count`: IP weighted count, no ontology field
- `tm_services_granted_class_scope`: IP class-scope attribute, no ontology field
- `tm_services_granted_weighted_count`: IP weighted count, no ontology field
- `tm_services_retired_class_scope`: IP class-scope attribute, no ontology field
- `tm_services_retired_weighted_count`: IP weighted count, no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN, state, postcode and country mappings check out against the examples, and the ABN values I spot-checked pass the checksum. The main problem is that an opaque hash-like token is emitted as a legal name. The legal_name source is also weaker than the ontology's 'as registered' definition, and the envelope examples do not show the required fields.
  - [blocking] `entity.legal_name<-party_name`: The record 'ta7f4232145720493d14bcd1584bf767e' is a 32-character hex-like token, not a business name, yet it is emitted as entity.legal_name. The mapping states a registered legal name the source does not support. (suggested: Add a rule that rejects party_name values matching a hash or opaque-token pattern (for example 32 hex characters with no words) and emits no legal_name observation for them, and record the skip in the extractor notes.)
  - [advisory] `entity.legal_name<-party_name`: party_name is an IP applicant/owner name, and the config itself says it is not labelled as a registered name. The ontology defines legal_name as 'as registered', so the mapping assumes a meaning the source does not state. Some values also carry descriptors that a registry would not use, such as 'optio software llc a delaware limited liability company' and 'compaq computer corporation incorporated in delaware'. (suggested: Keep the observation but lower field_confidence, or emit it under a name-as-claimed-by-IP-source label. Note that jurisdiction descriptors are not stripped, so the value is not a clean registered name.)
  - [advisory] `entity.entity_type`: Every record emits entity.entity_type = unknown with from: null. No source column supports it. It is a default rather than a source claim, and it is not in the config. This is consistent with the ontology's default-to-unknown rule, but it is presented as an observation. (suggested: Either drop default-valued observations from the output or mark them explicitly as engine defaults (derivation_level L1 or a null source) so they are not read as a source claim.)
  - [advisory] `observation`: The envelope shown for each record has only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are absent from the examples. The config also has no licence handling, although the ontology requires it and says to record 'unknown' and flag it if no licence is clear. (suggested: Confirm the emitted envelope carries all required fields. Pull licence from the CKAN metadata, or record 'unknown' and flag it. Document the record_id construction (lord_party_id plus financial_year) in source_record_id.)

## Examples (raw → value, held-out rows)

- `address.state<-state_code`: `qld` → `QLD`; `nsw` → `NSW`; `wa` → `WA`
- `address.postcode<-post_code`: `4215` → `4215`; `2022` → `2022`; `6000` → `6000`
- `address.country<-country_code`: `au` → `AU`; `us` → `US`; `gb` → `GB`
- `entity.abn<-lord_party_id`: `11009285287.0` → `11009285287`; `11010117049.0` → `11010117049`; `12004251423.0` → `12004251423`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
