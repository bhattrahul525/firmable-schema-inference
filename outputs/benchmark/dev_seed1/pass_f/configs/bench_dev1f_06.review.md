# Review packet (round-2 agent): validated_config

**Dataset:** Intellectual Property Longitudinal Research Data (IPLORD) — IP Australia  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `iplord_2001_2005.csv` (sha256 `de1c5c0ff640…`)

## How this ended

- Outcome **validated_config**.
- 18 model turns, 17 tool calls, $0.0284, 226.62s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded iplord_2001_2005.csv (one yearly slice of the IPLORD IP research panel). 675,929 rows, 77 columns; rows are party-by-financial-year with unique key (lord_party_id, lord_party_id_type, financial_year). Party IDs are either anonymised party_id values or ABNs (type 'abn', stored as float text e.g. 11000002568.0). The validated config maps ABN (type-gated, checksum-validated), filer name as trading name at confidence 0.5 with hashed IDs excluded, country, state and postcode. All other columns are unmapped with reasons. Validation on held-out rows: 0 hard failures, 0 unaccounted columns. Critique (2 runs): the blocking issues (ABN not gated on type, hash names emitted) were fixed; remaining issues are advisory: some filers are individuals without an ABN (rule 18 caveat), and the trading name is an unlabelled filer name.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `lord_party_id, lord_party_id_type, financial_year` — 0 duplicate / blank keys of 675929 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. lord_party_id | lord_party_id_type | party_name | country_code | state_code | post_code | d_first_earliest_filed_financial_year | pbr_first_earliest_filed_financial_year | tm_first_earliest_filed_financial_year | d_first_gained_enforceable_status_financ | pbr_first_gained_enforceable_status_fina | tm_first_gained_enforceable_status_finan | financial_year | d_filed_count | pbr_filed_count
2. 1.0 | party_id | bacoz developments pty ltd | au | vic | 3214 | 1995.0 | ∅ | 1990.0 | ∅ | ∅ | 1992.0 | 2002 | 1 | 0
3. 1.0 | party_id | bacoz developments pty ltd | au | vic | 3214 | 1995.0 | ∅ | 1990.0 | ∅ | ∅ | 1992.0 | 2003 | 0 | 0
4. 1.0 | party_id | bacoz developments pty ltd | au | vic | 3214 | 1995.0 | ∅ | 1990.0 | ∅ | ∅ | 1992.0 | 2005 | 0 | 0
5. 1.0 | party_id | bacoz developments pty ltd | au | vic | 3214 | 1995.0 | ∅ | 1990.0 | ∅ | ∅ | 1992.0 | 2004 | 0 | 0
6. 2.0 | party_id | kureha chemical industry co. ltd. | jp | tokyo | 103-8552 | 2005.0 | ∅ | 1985.0 | ∅ | ∅ | 1988.0 | 2003 | 0 | 0
7. 2.0 | party_id | kureha chemical industry co. ltd. | jp | tokyo | 103-8552 | 2005.0 | ∅ | 1985.0 | ∅ | ∅ | 1988.0 | 2004 | 0 | 0
8. 2.0 | party_id | kureha chemical industry co. ltd. | jp | tokyo | 103-8552 | 2005.0 | ∅ | 1985.0 | ∅ | ∅ | 1988.0 | 2005 | 1 | 0
9. 2.0 | party_id | kureha chemical industry co. ltd. | jp | tokyo | 103-8552 | 2005.0 | ∅ | 1985.0 | ∅ | ∅ | 1988.0 | 2002 | 0 | 0
10. 4.0 | party_id | t251a087231c9c3a345b1226b0adb543d | au | act | 2615 | 1990.0 | ∅ | 1999.0 | ∅ | ∅ | 2001.0 | 2002 | 0 | 0
11. 4.0 | party_id | t251a087231c9c3a345b1226b0adb543d | au | act | 2615 | 1990.0 | ∅ | 1999.0 | ∅ | ∅ | 2001.0 | 2003 | 0 | 0
12. 4.0 | party_id | t251a087231c9c3a345b1226b0adb543d | au | act | 2615 | 1990.0 | ∅ | 1999.0 | ∅ | ∅ | 2001.0 | 2004 | 0 | 0

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `lord_party_id_type+lord_party_id` | `entity.abn` | join_nonempty(:) → regex_extract(^abn:(\d{11})\.0$) → abn | W | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `party_name` | `entity.trading_name` | clean_whitespace → regex_extract(^(?!t?[0-9a-f]{32}$)(.+)$) | W | held_out | 0.50 | 100.0% | **0.50** |
| 3 | `country_code` | `address.country` | upper | W | held_out | 0.80 | 100.0% | **0.80** |
| 4 | `state_code` | `address.state` | clean_whitespace → state_code | W | held_out | 0.80 | 95.9% | **0.80** |
| 5 | `post_code` | `address.postcode` | postcode | W | held_out | 0.80 | 94.9% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `lord_party_id_type+lord_party_id`: Gated on lord_party_id_type=abn: only those rows carry 11-digit ABNs stored as float text (e.g. 11000002568.0); the checksum is applied.
2. `entity.trading_name` ← `party_name`: IP register filer name, not labelled as registered name, so trading name at low confidence. Anonymised 32-hex party hashes are excluded.
3. `address.country` ← `country_code`: ISO-style country code of the filer.
4. `address.state` ← `state_code`: Australian state code; overseas regions are rejected by the engine.
5. `address.postcode` ← `post_code`: Postcode of the filer.

## Left unmapped (not guessed)

- `lord_party_id_type`: Used only to gate lord_party_id as ABN; not a canonical field.
- `financial_year`: Reporting period of the count; not a claim start/end date for the entity.
- `d_first_earliest_filed_financial_year`: Year of first filing, not a registration date.
- `pbr_first_earliest_filed_financial_year`: Year of first filing, not a registration date.
- `tm_first_earliest_filed_financial_year`: Year of first filing, not a registration date.
- `d_first_gained_enforceable_status_financial_year`: IP enforceability year, not an entity status.
- `pbr_first_gained_enforceable_status_financial_year`: IP enforceability year, not an entity status.
- `tm_first_gained_enforceable_status_financial_year`: IP enforceability year, not an entity status.
- `d_filed_count`: IP activity count; no ontology field.
- `pbr_filed_count`: IP activity count; no ontology field.
- `tm_filed_count`: IP activity count; no ontology field.
- `d_granted_count`: IP activity count; no ontology field.
- `pbr_granted_count`: IP activity count; no ontology field.
- `tm_granted_count`: IP activity count; no ontology field.
- `d_retired_count`: IP activity count; no ontology field.
- `pbr_retired_count`: IP activity count; no ontology field.
- `tm_retired_count`: IP activity count; no ontology field.
- `d_enforceable_count`: IP activity count; no ontology field.
- `pbr_enforceable_count`: IP activity count; no ontology field.
- `tm_enforceable_count`: IP activity count; no ontology field.
- `tm_services_filed_count`: IP activity count; no ontology field.
- `tm_services_granted_count`: IP activity count; no ontology field.
- `tm_services_retired_count`: IP activity count; no ontology field.
- `tm_services_enforceable_count`: IP activity count; no ontology field.
- `d_filed_weighted_count`: IP activity measure; no ontology field.
- `pbr_filed_weighted_count`: IP activity measure; no ontology field.
- `tm_filed_weighted_count`: IP activity measure; no ontology field.
- `d_granted_weighted_count`: IP activity measure; no ontology field.
- `pbr_granted_weighted_count`: IP activity measure; no ontology field.
- `tm_granted_weighted_count`: IP activity measure; no ontology field.
- `d_retired_weighted_count`: IP activity measure; no ontology field.
- `pbr_retired_weighted_count`: IP activity measure; no ontology field.
- `tm_retired_weighted_count`: IP activity measure; no ontology field.
- `d_enforceable_weighted_count`: IP activity measure; no ontology field.
- `pbr_enforceable_weighted_count`: IP activity measure; no ontology field.
- `d_enforceable_class_scope`: IP classification scope; no ontology field.
- `d_enforceable_modal_class`: IP classification detail; no ontology field.
- `d_filed_class_scope`: IP classification scope; no ontology field.
- `d_filed_modal_class`: IP classification detail; no ontology field.
- `d_granted_class_scope`: IP classification scope; no ontology field.
- `d_granted_modal_class`: IP classification detail; no ontology field.
- `d_retired_class_scope`: IP classification scope; no ontology field.
- `pbr_enforceable_class_scope`: IP classification scope; no ontology field.
- `pbr_enforceable_modal_class`: IP classification detail; no ontology field.
- `pbr_filed_class_scope`: IP classification scope; no ontology field.
- `pbr_filed_modal_class`: IP classification detail; no ontology field.
- `pbr_granted_class_scope`: IP classification scope; no ontology field.
- `pbr_granted_modal_class`: IP classification detail; no ontology field.
- `pbr_retired_class_scope`: IP classification scope; no ontology field.
- `pbr_retired_modal_class`: IP classification detail; no ontology field.
- `tm_enforceable_class_scope`: IP classification scope; no ontology field.
- `tm_enforceable_weighted_count`: IP activity measure; no ontology field.
- `tm_filed_class_scope`: IP classification scope; no ontology field.
- `tm_granted_class_scope`: IP classification scope; no ontology field.
- `tm_retired_class_scope`: IP classification scope; no ontology field.
- `tm_services_enforceable_class_scope`: IP classification scope; no ontology field.
- `tm_services_enforceable_weighted_count`: IP activity measure; no ontology field.
- `tm_services_filed_class_scope`: IP classification scope; no ontology field.
- `tm_services_filed_weighted_count`: IP activity measure; no ontology field.
- `tm_services_granted_class_scope`: IP classification scope; no ontology field.
- `tm_services_granted_weighted_count`: IP activity measure; no ontology field.
- `tm_services_retired_class_scope`: IP classification scope; no ontology field.
- `tm_services_retired_weighted_count`: IP activity measure; no ontology field.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 675929, 'key': ['lord_party_id', 'lord_party_id_type', 'financial_year'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound for the country, state and postcode fields. The main problems are that the ABN mapping does not enforce the abn type filter it claims to use, and that hashed party identifiers are emitted as trading names. Both need fixing before the mapping is trusted.
  - [blocking] `entity.trading_name<-party_name`: Some party_name values are anonymised hashes (for example 'tde4084c80e515ae77542c13d29cf7430'), not names. Mapping them as the entity's trading name states a trading name the source does not support. (suggested: Do not map values that are hex hashes or placeholders to entity.trading_name. Add a rule that drops them, or leave them unmapped with a reason.)
  - [blocking] `entity.abn<-lord_party_id`: The config says only rows with lord_party_id_type=abn carry ABNs, but the regex and checksum do not check the type column. A party_id value that is 11 digits with a '.0' suffix and a valid checksum would be emitted as an ABN, which the source does not state. (suggested: Gate the entity.abn mapping on lord_party_id_type == 'abn' (a conditional or pre-filter transform), not only on the regex and checksum.)
  - [advisory] `entity.trading_name<-party_name`: Rows such as 'francesca garreffa' are person names with only an anonymised party_id and no business identifier. Rule 18 says these should be no_business_entities, but the config maps them as business entities. (suggested: Consider flagging individual filers without an ABN as non-entity rows, or document that the IP register lists individuals as filers.)
  - [advisory] `entity.trading_name<-party_name`: party_name is an IP register filer name that the data does not label as registered or licensee. Mapping it to trading_name is correct under rule 5, but the mapping_confidence should be stated at 0.6 or lower. (suggested: Set mapping_confidence to 0.6 or lower for this column and record that it is an unlabelled filer name.)
- Critique: The mapping is largely sound: ABN is gated on lord_party_id_type=abn and checksummed, state and country codes are normalised correctly, the 32-hex party hashes are excluded by the regex, and all other columns are accounted for as unmapped with reasons. The issues are advisory, mainly about person-like IP filers being treated as entities and the confidence and uniqueness checks not being stated. I found no value placed in a field whose meaning the source does not support, so no blocking issue.
  - [advisory] `entity.trading_name<-party_name`: The row for 'francesca garreffa' (party_id type, no ABN) is mapped as an entity trading name. Rule 18 treats individuals with no business identifier as not business entities. The party_name is a person-like name with no business identifier, so the mapping does not say the person is an entity. (suggested: Gate the entity-level trading_name observation on the row having a business identifier (abn type), or record a caveat that party_id-type person filers are IP registrants, not confirmed business entities.)
  - [advisory] `entity.trading_name<-party_name`: party_name is an IP register filer name that is not labelled as the registered name, so it is mapped to trading_name. The config gives no mapping_confidence, and the rule requires 0.6 or lower for such a column. (suggested: State mapping_confidence at 0.6 or lower for this claim and set source_reliability_basis to explain that the IP register filer name is not a registered name.)
  - [advisory] `record_id`: record_id is built from lord_party_id, lord_party_id_type and financial_year without a stated check_unique. Each row is a party for one financial year, so the composite is probably unique, but the config does not say it was verified. (suggested: Run check_unique on the composite key and record the result, or switch to hash_row=true if duplicates appear.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-party_name`: `prime grain pty ltd` → `prime grain pty ltd`; `ensign laboratories pty ltd` → `ensign laboratories pty ltd`; `fss trustee corporation` → `fss trustee corporation`
- `address.country<-country_code`: `au` → `AU`; `nz` → `NZ`; `nl` → `NL`
- `address.state<-state_code`: `qld` → `QLD`; `vic` → `VIC`; `nsw` → `NSW`
- `address.postcode<-post_code`: `4356` → `4356`; `3170` → `3170`; `2000` → `2000`
- `entity.abn<-lord_party_id_type+lord_party_id`: `['abn', '11004395242.0']` → `11004395242`; `['abn', '11118202672.0']` → `11118202672`; `['abn', '12084100872.0']` → `12084100872`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
