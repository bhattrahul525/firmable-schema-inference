# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.1810, 109.51s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_06/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `party_name` | `entity.legal_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |
| 2 | `state_code` | `address.state` | state_code | W | 0.80 | 92.4% | **0.80** |
| 3 | `post_code` | `address.postcode` | postcode | W | 0.80 | 92.4% | **0.80** |
| 4 | `country_code` | `address.country` | upper | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `party_name`: party name of IP rights holder/applicant
2. `address.state` ← `state_code`: state
3. `address.postcode` ← `post_code`: postcode
4. `address.country` ← `country_code`: ISO country

## Left unmapped (not guessed)

- `lord_party_id`: party id or ABN depending on type
- `lord_party_id_type`: id type
- `financial_year`: period
- `d_first_earliest_filed_financial_year`: IP metric
- `pbr_first_earliest_filed_financial_year`: IP metric
- `tm_first_earliest_filed_financial_year`: IP metric
- `d_first_gained_enforceable_status_financial_year`: IP metric
- `pbr_first_gained_enforceable_status_financial_year`: IP metric
- `tm_first_gained_enforceable_status_financial_year`: IP metric
- `d_filed_count`: IP metric
- `pbr_filed_count`: IP metric
- `tm_filed_count`: IP metric
- `d_granted_count`: IP metric
- `pbr_granted_count`: IP metric
- `tm_granted_count`: IP metric
- `d_retired_count`: IP metric
- `pbr_retired_count`: IP metric
- `tm_retired_count`: IP metric
- `d_enforceable_count`: IP metric
- `pbr_enforceable_count`: IP metric
- `tm_enforceable_count`: IP metric
- `tm_services_filed_count`: IP metric
- `tm_services_granted_count`: IP metric
- `tm_services_retired_count`: IP metric
- `tm_services_enforceable_count`: IP metric
- `d_filed_weighted_count`: IP metric
- `pbr_filed_weighted_count`: IP metric
- `tm_filed_weighted_count`: IP metric
- `d_granted_weighted_count`: IP metric
- `pbr_granted_weighted_count`: IP metric
- `tm_granted_weighted_count`: IP metric
- `d_retired_weighted_count`: IP metric
- `pbr_retired_weighted_count`: IP metric
- `tm_retired_weighted_count`: IP metric
- `d_enforceable_weighted_count`: IP metric
- `pbr_enforceable_weighted_count`: IP metric
- `tm_enforceable_weighted_count`: IP metric
- `d_filed_class_scope`: IP metric
- `d_filed_modal_class`: IP metric
- `d_granted_class_scope`: IP metric
- `d_granted_modal_class`: IP metric
- `d_retired_class_scope`: IP metric
- `d_retired_modal_class`: IP metric
- `d_enforceable_class_scope`: IP metric
- `d_enforceable_modal_class`: IP metric
- `pbr_filed_class_scope`: IP metric
- `pbr_filed_modal_class`: IP metric
- `pbr_granted_class_scope`: IP metric
- `pbr_granted_modal_class`: IP metric
- `pbr_retired_class_scope`: IP metric
- `pbr_retired_modal_class`: IP metric
- `pbr_enforceable_class_scope`: IP metric
- `pbr_enforceable_modal_class`: IP metric
- `tm_filed_class_scope`: IP metric
- `tm_filed_modal_class`: IP metric
- `tm_granted_class_scope`: IP metric
- `tm_granted_modal_class`: IP metric
- `tm_retired_class_scope`: IP metric
- `tm_retired_modal_class`: IP metric
- `tm_enforceable_class_scope`: IP metric
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
- Critique: The mapping is largely sound and nothing in it is blocking. The name, state, postcode and country mappings are correct, and entity_type is correctly left as unknown. The remaining points are advisory: hashed placeholder names, the unused ABN identifier, and the loss of foreign state values.
  - [advisory] `entity.legal_name<-party_name`: Some party_name values are hashed placeholders (e.g. 'ta57f5531260dc9c620e39d8186866334', 't9a96fb196ce01c7bdadcdb947ea2fb45') rather than real names, so they are emitted as legal_name claims that carry no usable name. Names are also lowercased in the source. (suggested: Keep the mapping but note that anonymised hash-like names exist in the source. Downstream, treat such values as low-quality and lower field confidence or filter them out.)
  - [advisory] `lord_party_id`: lord_party_id is unmapped, yet when lord_party_id_type is 'abn' (e.g. 39010587498.0) it holds an 11-digit ABN. The rules say to use the abn transform for ABNs, so a usable identifier is being dropped. The column mixes ABNs with internal party_ids, and the values carry a '.0' float suffix. (suggested: If the engine supports conditional mapping on lord_party_id_type, map ABN rows with the abn transform. Otherwise list it under needs_transform, with the reason that the identifier type depends on another column.)
  - [advisory] `address.state<-state_code`: Non-Australian state values such as 'tortola' (country VG) and 'oh' (country US) are not valid values in the AU state enum, so they are dropped with no observation. Foreign state information is lost. (suggested: Accept the dropping as expected, but note that the state enum covers only Australia and NZ. Optionally keep the foreign state value in a free-text field.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-party_name`: `provent holdings ltd.` → `provent holdings ltd.`; `3610398068` → `3610398068`; `celtainer ltd.` → `celtainer ltd.`
- `address.country<-country_code`: `vg` → `VG`; `gb` → `GB`; `au` → `AU`
- `address.state<-state_code`: `sa` → `SA`; `nsw` → `NSW`; `vic` → `VIC`
- `address.postcode<-post_code`: `5000` → `5000`; `2044` → `2044`; `2000` → `2000`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
