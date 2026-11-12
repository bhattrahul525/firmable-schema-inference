# Review packet (round-2 agent): partial_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **partial_config**.
- 15 model turns, 15 tool calls, $0.0164, 166.97s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded iplord_2001_2005.csv (one slice of nine resources). 675,929 rows, one per party per financial year; (lord_party_id, financial_year) is unique. 197,520 rows have lord_party_id_type=abn, whose id is an 11-digit ABN stored as float; abn checksum applied. Party names are IP applicant names, sometimes hash-like. Other slices and the 1901-2020 full file were not onboarded.
- Reason: Only the ABN, address fields are mapped with confidence. The party name could not be justified as a registered legal name. The config was validated and critiqued; the blocking legal_name issue was fixed by removal. Other year-slice files were not processed.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})\.0$) → abn | W | 0.85 | 96.8% | **0.85** |
| 2 | `state_code` | `address.state` | state_code | W | 0.85 | 93.9% | **0.85** |
| 3 | `post_code` | `address.postcode` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 4 | `country_code` | `address.country` | upper | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: Rows with lord_party_id_type=abn hold an 11-digit ABN stored as a float; the abn checksum filters bad values.
2. `address.state` ← `state_code`: Australian state codes; foreign region names are rejected by the enum.
3. `address.postcode` ← `post_code`: Postcode of the party address.
4. `address.country` ← `country_code`: ISO country code of party address.

## Left unmapped (not guessed)

- `party_name`: IP applicant/owner name; source does not state it is the registered legal name, and values include hash-like strings. Not mapped to legal_name or trading_name.
- `lord_party_id`: Internal party id when type is party_id; used only as record key.
- `lord_party_id_type`: Flag saying whether lord_party_id is an ABN or internal id.
- `financial_year`: Reporting year of the counts; not a statement date for the entity.
- `d_enforceable_class_scope`: IP activity metadata.
- `d_enforceable_count`: IP activity count.
- `d_enforceable_modal_class`: IP activity metadata.
- `d_enforceable_weighted_count`: IP activity count.
- `d_filed_class_scope`: IP activity metadata.
- `d_filed_count`: IP activity count.
- `d_filed_modal_class`: IP activity metadata.
- `d_filed_weighted_count`: IP activity count.
- `d_first_earliest_filed_financial_year`: Longitudinal statistic.
- `d_first_gained_enforceable_status_financial_year`: Longitudinal statistic.
- `d_granted_class_scope`: IP activity metadata.
- `d_granted_count`: IP activity count.
- `d_granted_modal_class`: IP activity metadata.
- `d_granted_weighted_count`: IP activity count.
- `d_retired_class_scope`: IP activity metadata.
- `d_retired_count`: IP activity count.
- `d_retired_weighted_count`: IP activity count.
- `pbr_enforceable_class_scope`: IP activity metadata.
- `pbr_enforceable_count`: IP activity count.
- `pbr_enforceable_modal_class`: IP activity metadata.
- `pbr_enforceable_weighted_count`: IP activity count.
- `pbr_filed_class_scope`: IP activity metadata.
- `pbr_filed_count`: IP activity count.
- `pbr_filed_modal_class`: IP activity metadata.
- `pbr_filed_weighted_count`: IP activity count.
- `pbr_first_earliest_filed_financial_year`: Longitudinal statistic.
- `pbr_first_gained_enforceable_status_financial_year`: Longitudinal statistic.
- `pbr_granted_class_scope`: IP activity metadata.
- `pbr_granted_count`: IP activity count.
- `pbr_granted_modal_class`: IP activity metadata.
- `pbr_granted_weighted_count`: IP activity count.
- `pbr_retired_class_scope`: IP activity metadata.
- `pbr_retired_count`: IP activity count.
- `pbr_retired_modal_class`: IP activity metadata.
- `pbr_retired_weighted_count`: IP activity count.
- `tm_enforceable_class_scope`: IP activity metadata.
- `tm_enforceable_count`: IP activity count.
- `tm_enforceable_weighted_count`: IP activity count.
- `tm_filed_class_scope`: IP activity metadata.
- `tm_filed_count`: IP activity count.
- `tm_filed_weighted_count`: IP activity count.
- `tm_first_earliest_filed_financial_year`: Longitudinal statistic.
- `tm_first_gained_enforceable_status_financial_year`: Longitudinal statistic.
- `tm_granted_class_scope`: IP activity metadata.
- `tm_granted_count`: IP activity count.
- `tm_granted_weighted_count`: IP activity count.
- `tm_retired_class_scope`: IP activity metadata.
- `tm_retired_count`: IP activity count.
- `tm_retired_weighted_count`: IP activity count.
- `tm_services_enforceable_class_scope`: IP activity metadata.
- `tm_services_enforceable_count`: IP activity count.
- `tm_services_enforceable_weighted_count`: IP activity count.
- `tm_services_filed_class_scope`: IP activity metadata.
- `tm_services_filed_count`: IP activity count.
- `tm_services_filed_weighted_count`: IP activity count.
- `tm_services_granted_class_scope`: IP activity metadata.
- `tm_services_granted_count`: IP activity count.
- `tm_services_granted_weighted_count`: IP activity count.
- `tm_services_retired_class_scope`: IP activity metadata.
- `tm_services_retired_count`: IP activity count.
- `tm_services_retired_weighted_count`: IP activity count.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-party_name`: Source names are IP filing applicant/owner names, not stated as registered names; some are hash-like strings.
- `entity.trading_name<-party_name`: Source does not say the name is a trading name.

## Checks

- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The state, postcode, country and ABN mappings look sound: the sample ABN 35118437755 passes the checksum, and the ABN regex extract does not falsely match the party_id rows. The main problems are that party_name is mapped to the registered legal_name field without support, and that the envelope is missing several required fields on every observation. Those two need fixing before the output can be used.
  - [blocking] `entity.legal_name<-party_name`: party_name is an IP filing applicant/owner name, and the config itself says it is not labelled as registered. The ontology defines legal_name as the registered name, so this maps a claim the source does not make. The example 'tb12f486a1f25d910ea322ef708a01486' is a hash-like string, not a name at all, and is emitted as legal_name. (suggested: Do not emit entity.legal_name from party_name. Emit it as an applicant/owner name observation under a non-legal field, or map to trading_name with a low field_confidence, and drop or quarantine hash-like values.)
  - [blocking] `observation envelope`: The envelope shown for each observation carries only observed_at, valid_from and valid_to. The ontology requires source_id, source_record_id, observed_at, ingested_at, licence and extractor_version on every record, with no exceptions. source_id, source_record_id, ingested_at, licence and extractor_version are missing from the examples and the config does not define them. (suggested: Add source_id, a deterministic source_record_id built from lord_party_id, financial_year and the row position, ingested_at, licence (from CKAN metadata, or 'unknown' and flagged) and extractor_version to every emitted observation.)
  - [advisory] `entity.abn<-lord_party_id`: The ABN transform does not check lord_party_id_type=abn, even though the config says the flag is what distinguishes ABNs from internal ids. The regex only restricts the value to 11 digits before the '.0', so an internal id that happens to be 11 digits would pass to the checksum and rely on the checksum alone to reject it. The type flag is listed as unmapped, so it is never used. (suggested: Gate the entity.abn transform on lord_party_id_type == 'abn' before applying the regex and checksum, and use the type flag explicitly rather than unmapping it.)
  - [advisory] `entity.entity_type`: entity_type 'unknown' is emitted with from: null on every row. That is a default, not a source claim, yet it is written as an observation with a null source column, which could be mistaken for a sourced value. (suggested: Either omit the observation when there is no source value, or mark it explicitly as a defaulted value (for example derivation_level L1 with a note that it is a default), so it is not read as a statement from the source.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified (2023-08-29) while the counts describe financial years 2003 to 2005. The ontology says observed_at is when the source stated the claim, and the metadata date is when the file was last changed, which is a different thing. (suggested: Keep the metadata timestamp, but document in the config that it is the publication date, and consider recording financial_year as a separate reporting-period field so the observation time is not read as the time the party was observed.)
  - [advisory] `confidence`: No confidence fields (source_reliability, field_confidence, link_confidence) are set on the examples. The ABN-to-entity claim and the free-text name claim carry very different reliability, and the name claim is not checked at all. (suggested: Set source_reliability per publisher, field_confidence per field (lower for party_name, higher for checksum-validated ABNs), and leave link_confidence unset unless the record is linked to an entity.)
  - [advisory] `entity.legal_name<-party_name`: Some values are abbreviated or informal, such as 'quality innovations p/l' and 'five hats wine co'. Even where the name is a real business name, it is not the registered form (for example 'Pty Ltd' in place of 'p/l'). (suggested: If any legal-name-like field is kept, normalise known suffixes (p/l to Pty Ltd, pty. limited to Pty Ltd) and record the raw value, with the normalisation at derivation_level L1.)

## Examples (raw → value, held-out rows)

- `address.country<-country_code`: `de` → `DE`; `au` → `AU`; `fr` → `FR`
- `entity.abn<-lord_party_id`: `13099309912.0` → `13099309912`; `13104536361.0` → `13104536361`; `13402954752.0` → `13402954752`
- `address.state<-state_code`: `vic` → `VIC`; `sa` → `SA`; `wa` → `WA`
- `address.postcode<-post_code`: `3550` → `3550`; `5007` → `5007`; `6011` → `6011`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
