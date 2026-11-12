# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **validated_config**.
- 15 model turns, 15 tool calls, $0.0160, 182.7s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Training rows: 675,629 party-year rows; lord_party_id is an 11-digit ABN (float-formatted, e.g. 11000002568.0) where lord_party_id_type=abn, and an internal id otherwise. (party_id, abn) key unique. Validation on held-out rows: ABN parse 90.9%, state 92.6%, postcode 92.1%, country 100%. Party names include pseudonymised tokens, so trading_name was withdrawn per critique c-c42ab59b.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})\.0$) → abn | W | 0.80 | 90.9% | **0.80** |
| 2 | `state_code` | `address.state` | state_code | W | 0.80 | 92.5% | **0.80** |
| 3 | `post_code` | `address.postcode` | postcode | W | 0.80 | 92.1% | **0.80** |
| 4 | `country_code` | `address.country` | upper | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: Where lord_party_id_type is 'abn' the id is an 11-digit ABN stored as a float string; checksum-validated; regex only matches 11-digit float-formatted values
2. `address.state` ← `state_code`: Australian state abbreviation of the party address
3. `address.postcode` ← `post_code`: Postcode of the party address
4. `address.country` ← `country_code`: ISO country code of the party address

## Left unmapped (not guessed)

- `party_name`: Applicant name column mixes real names with pseudonymised hash-like tokens (e.g. t17b3a...); no transform can exclude tokens, so no name observation is emitted
- `lord_party_id_type`: identifier type flag, not a business field
- `lord_party_id`: used only as ABN via abn field and record_id
- `financial_year`: reporting period of the counts, not a claim start date
- `d_first_earliest_filed_financial_year`: IP filing statistic
- `pbr_first_earliest_filed_financial_year`: IP filing statistic
- `tm_first_earliest_filed_financial_year`: IP filing statistic
- `d_first_gained_enforceable_status_financial_year`: IP statistic
- `pbr_first_gained_enforceable_status_financial_year`: IP statistic
- `tm_first_gained_enforceable_status_financial_year`: IP statistic
- `d_enforceable_class_scope`: IP statistic
- `d_enforceable_count`: IP statistic
- `d_enforceable_modal_class`: IP statistic
- `d_enforceable_weighted_count`: IP statistic
- `d_filed_class_scope`: IP statistic
- `d_filed_count`: IP statistic
- `d_filed_modal_class`: IP statistic
- `d_filed_weighted_count`: IP statistic
- `d_granted_class_scope`: IP statistic
- `d_granted_count`: IP statistic
- `d_granted_modal_class`: IP statistic
- `d_granted_weighted_count`: IP statistic
- `d_retired_class_scope`: IP statistic
- `d_retired_count`: IP statistic
- `d_retired_weighted_count`: IP statistic
- `pbr_enforceable_class_scope`: IP statistic
- `pbr_enforceable_count`: IP statistic
- `pbr_enforceable_modal_class`: IP statistic
- `pbr_enforceable_weighted_count`: IP statistic
- `pbr_filed_class_scope`: IP statistic
- `pbr_filed_count`: IP statistic
- `pbr_filed_modal_class`: IP statistic
- `pbr_filed_weighted_count`: IP statistic
- `pbr_granted_class_scope`: IP statistic
- `pbr_granted_count`: IP statistic
- `pbr_granted_modal_class`: IP statistic
- `pbr_granted_weighted_count`: IP statistic
- `pbr_retired_class_scope`: IP statistic
- `pbr_retired_modal_class`: IP statistic
- `pbr_retired_count`: IP statistic
- `pbr_retired_weighted_count`: IP statistic
- `tm_enforceable_class_scope`: IP statistic
- `tm_enforceable_modal_class`: IP statistic
- `tm_enforceable_weighted_count`: IP statistic
- `tm_enforceable_count`: IP statistic
- `tm_filed_class_scope`: IP statistic
- `tm_filed_modal_class`: IP statistic
- `tm_filed_count`: IP statistic
- `tm_filed_weighted_count`: IP statistic
- `tm_granted_class_scope`: IP statistic
- `tm_granted_modal_class`: IP statistic
- `tm_granted_count`: IP statistic
- `tm_granted_weighted_count`: IP statistic
- `tm_retired_class_scope`: IP statistic
- `tm_retired_modal_class`: IP statistic
- `tm_retired_count`: IP statistic
- `tm_retired_weighted_count`: IP statistic
- `tm_services_enforceable_count`: IP statistic
- `tm_services_enforceable_class_scope`: IP statistic
- `tm_services_enforceable_weighted_count`: IP statistic
- `tm_services_filed_count`: IP statistic
- `tm_services_filed_class_scope`: IP statistic
- `tm_services_filed_weighted_count`: IP statistic
- `tm_services_granted_count`: IP statistic
- `tm_services_granted_class_scope`: IP statistic
- `tm_services_granted_weighted_count`: IP statistic
- `tm_services_retired_count`: IP statistic
- `tm_services_retired_class_scope`: IP statistic
- `tm_services_retired_weighted_count`: IP statistic

## Needs a transform the engine does not have

- `party_name`: needs a transform that drops pseudonymised hash tokens (^t[0-9a-f]{32}$) before mapping to entity.trading_name or legal_name

## Checks

- ⚠️ **identifier_checksum_abn**: 7 of 77 judged values mapped to entity.abn (9%) fail the checksum. A genuine column rarely fails that often, so it may mix real identifiers with look-alikes (internal ids of the same length). About 1 in 89 look-alikes passes the checksum by chance, so some values read as valid may not be. Use a type column or a stricter pattern to keep only the real identifiers, or say why the column is kept as it is.  
  Agent's answer: *kept*: Checksum failures are rejects for non-ABN party_id rows; ABN mapping restricted to abn-type rows by regex
- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound: the ABN regex and checksum path, state, postcode and country transforms, record_id, and the unmapped list all match the sample rows. The main problem is that hash-like placeholder tokens in party_name are being emitted as trading names, which the source does not support. The remaining points are advisory.
  - [blocking] `entity.trading_name<-party_name`: Some party_name values are opaque hash-like tokens (e.g. t17b3a216772440f58ed6d91c061e5b8f, t9495ea68ce67f0f7a325b494e84d084d), not business names. Mapping them to entity.trading_name states that these tokens are names the entity traded under, which the source does not support. (suggested: Exclude pseudonymised tokens from the trading_name mapping, for example with a pattern filter on ^t[0-9a-f]{32}$, or leave those rows without a name observation and record the reason.)
  - [advisory] `entity.abn<-lord_party_id`: The config reason says the ABN applies only where lord_party_id_type is 'abn', but the transform does not check that flag. It relies on the regex failing for 12- and 13-digit party_id values. This works on the sample rows but is fragile. (suggested: Add an explicit condition on lord_party_id_type == 'abn', or confirm that the regex cannot match party_id values in the full file.)
  - [advisory] `entity.trading_name<-party_name`: party_name is an IP applicant name with no registered-name label, so trading_name at low confidence is consistent with rule 5. The mapping does not record a mapping_confidence of 0.6 or lower, and the config does not show it. (suggested: Set mapping_confidence to 0.6 or lower for this field and note in the reason that the column is an unlabelled applicant name.)
  - [advisory] `entity.entity_type`: Names such as 'tecnol medical products inc a delaware corporation' and 'stanwich industries inc.' carry corporate suffixes. The mapping leaves entity_type unmapped, which is allowed under rule 7, so the engine records unknown. This is conservative but leaves information unused. (suggested: Leave as is, or consider entity_type_from_suffix on party_name, which rule 7 permits when the source has no entity_type column. Flag the choice as a caveat.)

## Examples (raw → value, held-out rows)

- `address.country<-country_code`: `ch` → `CH`; `au` → `AU`; `jp` → `JP`
- `entity.abn<-lord_party_id`: `11081881996.0` → `11081881996`; `12008001787.0` → `12008001787`; `14093420752.0` → `14093420752`
- `address.state<-state_code`: `qld` → `QLD`; `sa` → `SA`; `vic` → `VIC`
- `address.postcode<-post_code`: `4122` → `4122`; `5064` → `5064`; `3095` → `3095`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
