# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2020.zip` (sha256 `0cd7982b375f…`)

## How this ended

- Outcome **validated_config**.
- 15 model turns, 15 tool calls, $0.0175, 162.4s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1d_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validated on held-out rows (call 4): 0 hard failures, record_id unique over 675,929 rows; the only remaining unaccounted columns were covered by unmapped entries. Critique blocking issues on entity.legal_name were fixed by removing that mapping; the change only removes fields so no new critique was required.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id` | `entity.abn` | regex_extract(^(\d{11})\.0$) → abn | W | 0.90 | 96.7% | **0.90** |
| 2 | `state_code` | `address.state` | state_code | W | 0.85 | 95.6% | **0.85** |
| 3 | `post_code` | `address.postcode` | postcode | W | 0.85 | 95.6% | **0.85** |
| 4 | `country_code` | `address.country` | upper | W | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id`: lord_party_id_type=abn rows hold the ABN as a float-formatted 11-digit value (e.g. 11000002568.0); checksum applied via abn transform; party_id rows do not match the regex
2. `address.state` ← `state_code`: Australian state abbreviation of the party
3. `address.postcode` ← `post_code`: postcode of the party
4. `address.country` ← `country_code`: ISO country code of the party

## Left unmapped (not guessed)

- `party_name`: IP applicant/owner name; the dataset does not state it is the registered name, and party_id rows carry opaque hash strings, so it is not mapped to entity.legal_name
- `lord_party_id_type`: id type flag used only to interpret lord_party_id
- `lord_party_id`: used only via the abn field; non-ABN party ids are internal ids
- `financial_year`: year of the count, used only in record_id; not a claim start date
- `d_first_earliest_filed_financial_year`: IP statistics
- `pbr_first_earliest_filed_financial_year`: IP statistics
- `tm_first_earliest_filed_financial_year`: IP statistics
- `d_first_gained_enforceable_status_financial_year`: IP statistics
- `pbr_first_gained_enforceable_status_financial_year`: IP statistics
- `tm_first_gained_enforceable_status_financial_year`: IP statistics
- `d_enforceable_class_scope`: IP statistics
- `d_enforceable_count`: IP statistics
- `d_enforceable_modal_class`: IP statistics
- `d_enforceable_weighted_count`: IP statistics
- `d_filed_class_scope`: IP statistics
- `d_filed_count`: IP statistics
- `d_filed_modal_class`: IP statistics
- `d_filed_weighted_count`: IP statistics
- `d_granted_class_scope`: IP statistics
- `d_granted_count`: IP statistics
- `d_granted_modal_class`: IP statistics
- `d_granted_weighted_count`: IP statistics
- `d_retired_class_scope`: IP statistics
- `d_retired_count`: IP statistics
- `d_retired_weighted_count`: IP statistics
- `pbr_enforceable_class_scope`: IP statistics
- `pbr_enforceable_count`: IP statistics
- `pbr_enforceable_modal_class`: IP statistics
- `pbr_enforceable_weighted_count`: IP statistics
- `pbr_filed_class_scope`: IP statistics
- `pbr_filed_count`: IP statistics
- `pbr_filed_modal_class`: IP statistics
- `pbr_filed_weighted_count`: IP statistics
- `pbr_granted_class_scope`: IP statistics
- `pbr_granted_count`: IP statistics
- `pbr_granted_modal_class`: IP statistics
- `pbr_granted_weighted_count`: IP statistics
- `pbr_retired_class_scope`: IP statistics
- `pbr_retired_count`: IP statistics
- `pbr_retired_modal_class`: IP statistics
- `pbr_retired_weighted_count`: IP statistics
- `tm_enforceable_class_scope`: IP statistics
- `tm_enforceable_count`: IP statistics
- `tm_enforceable_weighted_count`: IP statistics
- `tm_filed_class_scope`: IP statistics
- `tm_filed_count`: IP statistics
- `tm_filed_weighted_count`: IP statistics
- `tm_granted_class_scope`: IP statistics
- `tm_granted_count`: IP statistics
- `tm_granted_weighted_count`: IP statistics
- `tm_retired_class_scope`: IP statistics
- `tm_retired_count`: IP statistics
- `tm_retired_weighted_count`: IP statistics
- `tm_services_enforceable_class_scope`: IP statistics
- `tm_services_enforceable_count`: IP statistics
- `tm_services_enforceable_weighted_count`: IP statistics
- `tm_services_filed_class_scope`: IP statistics
- `tm_services_filed_count`: IP statistics
- `tm_services_filed_weighted_count`: IP statistics
- `tm_services_granted_class_scope`: IP statistics
- `tm_services_granted_count`: IP statistics
- `tm_services_granted_weighted_count`: IP statistics
- `tm_services_retired_class_scope`: IP statistics
- `tm_services_retired_count`: IP statistics
- `tm_services_retired_weighted_count`: IP statistics

## Needs a transform the engine does not have

- none

## Checks

- ⚠️ **identifier_checksum_abn**: 3 of 92 judged values mapped to entity.abn (3%) fail the checksum. A genuine column rarely fails that often, so it may mix real identifiers with look-alikes (internal ids of the same length). About 1 in 89 look-alikes passes the checksum by chance, so some values read as valid may not be. Use a type column or a stricter pattern to keep only the real identifiers, or say why the column is kept as it is.  
  Agent's answer: *kept*: Values failing the ABN checksum are rejected by the abn transform and not emitted.
- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping has two blocking problems, both about entity.legal_name: party_name is mapped to the registered name without the dataset stating that, and opaque hash strings are emitted as business names. The ABN, state, postcode, country and suffix-based entity_type mappings are consistent with the examples, with advisory caveats about the implicit ABN type condition and the uniqueness of record_id.
  - [blocking] `entity.legal_name<-party_name`: The config's own reason admits the dataset does not state that party_name is the registered name, yet it is mapped to entity.legal_name. Rule 5 allows legal_name only when the data says the name is registered, licensee, or supplier. The examples therefore state a registered-name claim the source does not support, e.g. 'harris & company solicitors' and 'ergofurn pty ltd' become legal_name observations. (suggested: Remove the entity.legal_name<-party_name mapping. If the name must be kept, map it to a non-legal field or leave it unmapped with a reason such as 'IP applicant name; registered status not stated'.)
  - [blocking] `entity.legal_name<-party_name`: Rows with lord_party_id_type=party_id carry hashed or opaque strings in party_name, e.g. 'tc76c9daace7d48792f5a101de4a21518' and 't5d79be930b2d178def32c224115d76c8'. These are not business names, so mapping them as legal_name states something the source does not support. (suggested: Do not emit legal_name when party_name is a 32-character hex hash. Add a guard or a separate transform, or leave those rows unmapped for the name, with a reason stating the value is an opaque identifier.)
  - [advisory] `entity.abn<-lord_party_id`: The ABN mapping has no explicit condition on lord_party_id_type=abn. The examples show party_id rows are skipped, but only because their digit counts happen to fail the regex. An 11-digit party_id would pass the regex and rely on the checksum alone to be rejected. (suggested: Make the condition explicit in the config, filtering on lord_party_id_type == 'abn' before regex_extract and the abn transform.)
  - [advisory] `entity.entity_type<-party_name`: entity_type is derived from name suffixes (e.g. 'pty ltd' gives company). Rule 7 permits this when no explicit column exists, but the suffix is read from a name that is not stated to be registered, so the 'company' claim is weaker than the rule implies. (suggested: Keep the suffix rule as permitted, but record the caveat and consider lowering field_confidence or pairing it with the legal_name decision above.)
  - [advisory] `record_id`: record_id is built from lord_party_id and financial_year, but no check_unique result is shown. Uniqueness is not demonstrated for that pair. (suggested: Run check_unique on (lord_party_id, financial_year) across the full member, or set hash_row=true if duplicates appear.)

## Examples (raw → value, held-out rows)

- `entity.abn<-lord_party_id`: `11900743980.0` → `11900743980`; `14002341068.0` → `14002341068`; `14058410996.0` → `14058410996`
- `address.country<-country_code`: `us` → `US`; `au` → `AU`; `nl` → `NL`
- `address.state<-state_code`: `nsw` → `NSW`; `vic` → `VIC`; `qld` → `QLD`
- `address.postcode<-post_code`: `2747` → `2747`; `2037` → `2037`; `3168` → `3168`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
