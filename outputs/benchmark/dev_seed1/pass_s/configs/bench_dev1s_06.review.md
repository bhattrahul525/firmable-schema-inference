# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **validated_config**.
- 16 model turns, 16 tool calls, $0.3306, 196.94s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_06/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})(?:\.0)?$) → abn | W | 0.80 | 98.8% | **0.80** |
| 2 | `party_name` | `entity.legal_name` | regex_extract(^(?!t[0-9a-f]{32}$)(.+)$) → clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 3 | `state_code` | `address.state` | state_code | W | 0.80 | 96.0% | **0.80** |
| 4 | `post_code` | `address.postcode` | postcode | W | 0.80 | 94.3% | **0.80** |
| 5 | `country_code` | `address.country` | upper | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: id is ABN when id_type is abn
2. `entity.legal_name` ← `party_name`: party name; anonymised hash tokens excluded
3. `address.state` ← `state_code`: state
4. `address.postcode` ← `post_code`: postcode
5. `address.country` ← `country_code`: country

## Left unmapped (not guessed)

- `lord_party_id_type`: id type flag
- `financial_year`: period of counts
- `d_first_earliest_filed_financial_year`: IP metric
- `pbr_first_earliest_filed_financial_year`: IP metric
- `tm_first_earliest_filed_financial_year`: IP metric
- `d_first_gained_enforceable_status_financial_year`: IP metric
- `pbr_first_gained_enforceable_status_financial_year`: IP metric
- `tm_first_gained_enforceable_status_financial_year`: IP metric
- `d_filed_count`: IP metric
- `d_granted_count`: IP metric
- `d_retired_count`: IP metric
- `d_enforceable_count`: IP metric
- `pbr_filed_count`: IP metric
- `pbr_granted_count`: IP metric
- `pbr_retired_count`: IP metric
- `pbr_enforceable_count`: IP metric
- `tm_filed_count`: IP metric
- `tm_granted_count`: IP metric
- `tm_retired_count`: IP metric
- `tm_enforceable_count`: IP metric
- `tm_services_filed_count`: IP metric
- `tm_services_granted_count`: IP metric
- `tm_services_retired_count`: IP metric
- `tm_services_enforceable_count`: IP metric
- `d_filed_weighted_count`: IP metric
- `d_granted_weighted_count`: IP metric
- `d_retired_weighted_count`: IP metric
- `d_enforceable_weighted_count`: IP metric
- `pbr_filed_weighted_count`: IP metric
- `pbr_granted_weighted_count`: IP metric
- `pbr_retired_weighted_count`: IP metric
- `pbr_enforceable_weighted_count`: IP metric
- `tm_filed_weighted_count`: IP metric
- `tm_granted_weighted_count`: IP metric
- `tm_retired_weighted_count`: IP metric
- `tm_enforceable_weighted_count`: IP metric
- `d_filed_class_scope`: IP metric
- `d_granted_class_scope`: IP metric
- `d_retired_class_scope`: IP metric
- `d_enforceable_class_scope`: IP metric
- `pbr_filed_class_scope`: IP metric
- `pbr_granted_class_scope`: IP metric
- `pbr_retired_class_scope`: IP metric
- `pbr_enforceable_class_scope`: IP metric
- `tm_filed_class_scope`: IP metric
- `tm_granted_class_scope`: IP metric
- `tm_retired_class_scope`: IP metric
- `tm_enforceable_class_scope`: IP metric
- `d_filed_modal_class`: IP metric
- `d_granted_modal_class`: IP metric
- `d_retired_modal_class`: IP metric
- `d_enforceable_modal_class`: IP metric
- `pbr_filed_modal_class`: IP metric
- `pbr_granted_modal_class`: IP metric
- `pbr_retired_modal_class`: IP metric
- `pbr_enforceable_modal_class`: IP metric
- `tm_filed_modal_class`: IP metric
- `tm_granted_modal_class`: IP metric
- `tm_retired_modal_class`: IP metric
- `tm_enforceable_modal_class`: IP metric
- `tm_services_enforceable_class_scope`: IP metric
- `tm_services_enforceable_weighted_count`: IP metric
- `tm_services_filed_class_scope`: IP metric
- `tm_services_filed_weighted_count`: IP metric
- `tm_services_granted_class_scope`: IP metric
- `tm_services_granted_weighted_count`: IP metric
- `tm_services_retired_class_scope`: IP metric
- `tm_services_retired_weighted_count`: IP metric

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound: ABNs are only extracted where the id type is abn, and the party_id rows are correctly not mapped to ABN. The blocking problem is that hash-token party names are emitted as legal names.
  - [blocking] `entity.legal_name<-party_name`: Some party_name values are anonymised hash tokens (e.g. 'tee389f85ef3c708c9ec5f1d9a8fefea2', 't6b0a08d7d80f8d5d88e8ef18eaafca56', 'td530a0a7c69ab8c38e323c66d88abbd7'), not registered names. Mapping them to legal_name states a name the source does not give. (suggested: Drop legal_name when party_name matches a hash-like pattern, such as ^t[0-9a-f]{32,33}$, or flag it as redacted.)
  - [advisory] `entity.legal_name<-party_name`: Names are lowercased in the source. The mapping keeps this casing, and the dataset is IP Australia's party-level data, not a registry, so the name is as the IP source records it. (suggested: Treat the value as a source-stated name and optionally normalise the case downstream.)
  - [advisory] `entity.entity_type`: entity_type is always 'unknown' even though names include 'pty ltd', 'inc' and 'ag'. This is safe but loses information. (suggested: Optionally derive entity_type from name suffixes at a lower derivation level, or leave as unknown.)
  - [advisory] `address.country<-country_code`: Non-AU country codes (US, DE) are emitted. This is correct, but the address state and postcode are absent for these rows, and no address.full or locality exists. (suggested: None required; consider validating country codes against ISO 3166.)
- Critique: The mapping is sound. Names, ABNs, state, postcode and country are all mapped to the right fields, and hash-token names are suppressed. Only advisory points remain.
  - [advisory] `entity.legal_name<-party_name`: The anonymisation-token regex only matches 't' followed by exactly 32 hex characters. Two of the raw rows have tokens that do not fit this pattern: 'tee389f85ef3c708c9ec5f1d9a8fefea2' and 't6b0a08d7d80f8d5d88e8ef18eaafca56' (33 characters after the 't' in the second). Both were correctly dropped, but only because the pattern happens to match. The third token, 'td530a0a7c69ab8c38e323c66d88abbd7', was also dropped. The pattern's fit is fragile, so future hash tokens of a different length could leak through as legal names. (suggested: Loosen the exclusion to something like ^t[0-9a-f]{30,40}$ so hash tokens are reliably excluded.)
  - [advisory] `entity.abn<-lord_party_id`: ABN is only extracted when lord_party_id_type is 'abn', but the config does not condition on that column; it relies on the 11-digit regex plus the checksum. Rows with type party_id and an 11-digit id could be wrongly treated as an ABN. In the examples, party_id values are 12-13 digits, so this did not occur, but 908.0 style ids are not protected by the type flag. (suggested: Gate the extraction on lord_party_id_type == 'abn', or rely on the checksum and document that.)
  - [advisory] `entity.entity_type`: entity_type is always 'unknown', even where the name clearly indicates a type (e.g. 'pty ltd' suggests a company, 'inc' an incorporated association or US corporation). This is safe but not rich. (suggested: Optionally derive entity_type from the legal-name suffix at a lower derivation level, or leave as unknown.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-party_name`: `wholesome & hearty foods inc.` → `wholesome & hearty foods inc.`; `sony overseas sa` → `sony overseas sa`; `crocodiles not waterlilies international pty ltd` → `crocodiles not waterlilies international pty ltd`
- `address.country<-country_code`: `us` → `US`; `ch` → `CH`; `au` → `AU`
- `address.state<-state_code`: `nsw` → `NSW`; `vic` → `VIC`; `qld` → `QLD`
- `address.postcode<-post_code`: `2030` → `2030`; `3183` → `3183`; `4129` → `4129`
- `entity.abn<-lord_party_id`: `14061390538.0` → `14061390538`; `14081364776.0` → `14081364776`; `15007576141.0` → `15007576141`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
