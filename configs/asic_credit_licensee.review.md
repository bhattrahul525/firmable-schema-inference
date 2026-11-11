# Review packet: asic_credit_licensee (config v2)

**Dataset:** ASIC – Credit Licensee Dataset — Australian Securities and Investments Commission (ASIC)  
**Page:** https://data.gov.au/data/dataset/asic-credit-licensee  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `credit_lic_202611.tsv` (sha256 `74fc2f5f73e6…`)  
**What the agent says it is:** ASIC register extract of current Australian credit licensees, one row per credit licence with licensee name, ABN/ACN, licence status and address.  
**One row is:** one credit licence held by a licensee (an Australian Credit Licence), as listed on the ASIC credit licensee register

## How this was produced

- Model `claude-haiku-5-5`; 5 LLM calls; 67,665 input + 18,157 output tokens; cost $0.0136 (computed from list prices); LLM time 77.9s.
- Revision rounds: 1. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'tsv', 'encoding': 'utf-8', 'delimiter': '\t', 'header_row': 1}`. Record id: `{'from': ['CRED_LIC_NUM']}` — CRED_LIC_NUM is distinct across all 4313 rows (distinct 4313 = row count), so it uniquely identifies each credit licence record.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `{'source': 'CRED_LIC_START_DT', 'transforms': [{'name': 'parse_date', 'arg': ['%d/%m/%Y']}]}`. valid_to: `{'source': 'CRED_LIC_END_DT', 'transforms': [{'name': 'parse_date', 'arg': ['%d/%m/%Y']}]}`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.9, 'address': 0.85, 'classification': 0.75, 'contact': 0.5}` — ASIC is the statutory regulator that maintains the credit licensee register, so its identity claims (legal name, ABN/ACN, licence holder) are highly reliable. Address is the registered licence address and is generally current but may be an agent or service address. Classification is less certain because the derived entity type is inferred from name suffixes. There is no contact data, so contact is set to a neutral 0.5.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `CRED_LIC_NAME` | `entity.legal_name` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `CABOT SQUARE ACCOUNTING PTY LTD` → `CABOT SQUARE ACCOUNTING PTY LTD`<br>`YOUR FINANCE EXPERT PTY LTD` → `YOUR FINANCE EXPERT PTY LTD`<br>`FLA GROUP PTY LTD` → `FLA GROUP PTY LTD` |
| 2 | `CRED_LIC_BN` | `entity.trading_name` | clean_whitespace | 0.85 | 100.0% (ok 107, rejected 0) | **0.85** | agreed | `LANSDOWNE LOANS` → `LANSDOWNE LOANS`<br>`CAR FINANCE BROKER` → `CAR FINANCE BROKER`<br>`SURELEND` → `SURELEND` |
| 3 | `CRED_LIC_ABN_ACN` | `entity.abn` | abn | 0.90 | 100.0% (ok 270, rejected 0) | **0.90** | agreed | `22137291699` → `22137291699`<br>`53621418228` → `53621418228`<br>`75657432132` → `75657432132` |
| 4 | `CRED_LIC_ABN_ACN` | `entity.acn` | acn | 0.80 | 100.0% (ok 28, rejected 0) | **0.80** | agreed | `138043704` → `138043704`<br>`616185105` → `616185105`<br>`118852270` → `118852270` |
| 5 | `CRED_LIC_NAME` | `entity.entity_type` | entity_type_from_suffix | 0.60 | 100.0% (ok 300, rejected 0) | **0.60** | agreed | `CABOT SQUARE ACCOUNTING PTY LTD` → `company`<br>`YOUR FINANCE EXPERT PTY LTD` → `company`<br>`FLA GROUP PTY LTD` → `company` |
| 6 | `CRED_LIC_LOCALITY` | `address.locality` | clean_whitespace | 0.95 | 100.0% (ok 300, rejected 0) | **0.95** | agreed | `SYDNEY` → `SYDNEY`<br>`OATLEY` → `OATLEY`<br>`MELBOURNE` → `MELBOURNE` |
| 7 | `CRED_LIC_STATE` | `address.state` | state_code | 0.95 | 100.0% (ok 300, rejected 0) | **0.95** | agreed | `NSW` → `NSW`<br>`VIC` → `VIC`<br>`WA` → `WA` |
| 8 | `CRED_LIC_PCODE` | `address.postcode` | postcode | 0.95 | 100.0% (ok 300, rejected 0) | **0.95** | agreed | `2000` → `2000`<br>`2223` → `2223`<br>`3004` → `3004` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `CRED_LIC_NAME`: CRED_LIC_NAME is the licensee's name as recorded on the credit licence register, which is the registered name. Sample values are company names with suffixes and some individual names, all consistent with a registered licensee name.
2. `entity.trading_name` ← `CRED_LIC_BN`: CRED_LIC_BN is a business name, i.e. a name traded under, which maps to trading_name. It is blank for about 66% of rows.
3. `entity.abn` ← `CRED_LIC_ABN_ACN`: The column holds 11-digit ABNs for about 89% of rows. The abn transform validates the checksum and skips non-11-digit values such as the '0' placeholders.
4. `entity.acn` ← `CRED_LIC_ABN_ACN`: The same column holds 9-digit values for about 8% of rows, which are probably ACNs. Mapped a second time with the acn checksum transform, which skips non-9-digit values.
5. `entity.entity_type` ← `CRED_LIC_NAME`: There is no explicit entity-type column, so the type is derived from the name suffix. Names ending in Pty Ltd, Limited or Ltd give company, and everything else (including individual names) gives unknown.
6. `address.locality` ← `CRED_LIC_LOCALITY`: Locality/suburb of the licensee address; sample values are suburb names.
7. `address.state` ← `CRED_LIC_STATE`: Two-letter Australian state codes (NSW, VIC, QLD, etc.) that match the ontology state enum.
8. `address.postcode` ← `CRED_LIC_PCODE`: 4-digit Australian postcode; the postcode transform restores any dropped leading zero.

## Left unmapped (not guessed)

- `REGISTER_NAME`: Constant value 'Credit Licence' on every row (distinct 1). It identifies the register type, not an entity claim.
- `CRED_LIC_STATUS`: Licence status, not entity status. APPR and SUSP describe the credit licence, which can be approved or suspended while the legal entity is deregistered or in liquidation. No ontology field for licence status, so not mapped to entity.status.
- `CRED_LIC_AFSL_NUM`: Australian Financial Services Licence number. No ontology field exists for it. Mostly '0' (no AFSL), and it is not mapped to any canonical field.
- `CRED_LIC_STATUS_HISTORY`: Free-text history of licence suspensions and conditions. No ontology field, and the ontology status enum is not used for it.
- `CRED_LIC_LAT`: Latitude of the licensee address. No ontology field for coordinates, and address.full is not derived from it.
- `CRED_LIC_LNG`: Longitude of the licensee address. No ontology field for coordinates.
- `CRED_LIC_EDRS`: External dispute resolution scheme membership (AFCA, COSL, FOS). No ontology field.
- `CRED_LIC_AUTHORISATIONS`: Long free-text list of credit activities the licence authorises, semicolon-delimited. No ontology field for licence scope, and splitting it would not map it to any canonical field.

## Needs a transform the engine does not have

- `—`: none

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 0, only-2 0; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

Most field mappings are consistent with the examples: legal name from CRED_LIC_NAME, trading name from CRED_LIC_BN, ABN and checksum handling, suffix-based entity type, locality, state and postcode. The main meaning error is that the licence status codes are mapped onto entity.status, which asserts entity-level status from a licence-level field. The valid_from output is also missing from the examples, which should be verified.
- `entity.status`: The CRED_LIC_STATUS values describe the credit licence (APPR = approved, SUSP = suspended), not the legal entity. The examples emit entity.status 'active' for every APPR row, which asserts the company is active. A licence can be approved while the company is deregistered or in liquidation, and a suspended licence does not make the entity 'suspended'. Mapping these onto entity.status is a meaning error, not just an interpretation. (suggested: Remove the entity.status map_values mapping (leave CRED_LIC_STATUS unmapped with reason 'licence status, not entity status'). If it must be kept, route it to a licence-status claim rather than entity.status, and do not map APPR to 'active'.)
- `valid_from`: The config maps CRED_LIC_START_DT to valid_from, but the example rows that have a start date (e.g. CABOT SQUARE ACCOUNTING, 12/03/2015) produce no valid_from observation. Either the mapping is not being applied or the output is incomplete, so the config and the emitted observations disagree. (suggested: Check that valid_from is emitted for rows with a parsable CRED_LIC_START_DT (format %d/%m/%Y) and confirm the observation envelope carries it. Also confirm that valid_from is documented as the licence start, not the entity registration date, so date_registered is not inferred from it.)

## What changed during revision

**critique**
- Removed the entity.status map_values field (APPR->active, SUSP->suspended). CRED_LIC_STATUS is now listed under unmapped with the reason 'licence status, not entity status'. — The values describe the credit licence, not the legal entity. Mapping APPR to 'active' asserts the company is active, which the source does not say, and SUSP does not make the entity suspended.

## Three sample rows, raw

- `{'REGISTER_NAME': 'Credit Licence', 'CRED_LIC_NUM': '472169', 'CRED_LIC_NAME': 'CABOT SQUARE ACCOUNTING PTY LTD', 'CRED_LIC_START_DT': '12/03/2015', 'CRED_LIC_STATUS': 'APPR', 'CRED_LIC_ABN_ACN': '22137291699', 'CRED_LIC_AFSL_NUM': '0', 'CRED_LIC_LOCALITY': 'SYDNEY', 'CRED_LIC_STATE': 'NSW', 'CRED_LIC_PCODE': '2000', 'CRED_LIC_LAT': '-33.8698439', 'CRED_LIC_LNG': '151.2082848', 'CRED_LIC_EDRS': 'FOS', 'CRED_LIC_AUTHORISATIONS': 'This licence authorises the licensee to:~Engage in credit activities other than as a credit provider…'}`
- `{'REGISTER_NAME': 'Credit Licence', 'CRED_LIC_NUM': '502087', 'CRED_LIC_NAME': 'YOUR FINANCE EXPERT PTY LTD', 'CRED_LIC_START_DT': '25/01/2018', 'CRED_LIC_STATUS': 'APPR', 'CRED_LIC_ABN_ACN': '53621418228', 'CRED_LIC_AFSL_NUM': '0', 'CRED_LIC_LOCALITY': 'OATLEY', 'CRED_LIC_STATE': 'NSW', 'CRED_LIC_PCODE': '2223', 'CRED_LIC_LAT': '-33.9815241', 'CRED_LIC_LNG': '151.0744354', 'CRED_LIC_EDRS': 'AFCA', 'CRED_LIC_AUTHORISATIONS': 'This licence authorises the licensee to:~Engage in credit activities other than as a credit provider…'}`
- `{'REGISTER_NAME': 'Credit Licence', 'CRED_LIC_NUM': '547274', 'CRED_LIC_NAME': 'FLA GROUP PTY LTD', 'CRED_LIC_START_DT': '04/08/2023', 'CRED_LIC_STATUS': 'APPR', 'CRED_LIC_ABN_ACN': '75657432132', 'CRED_LIC_AFSL_NUM': '0', 'CRED_LIC_LOCALITY': 'MELBOURNE', 'CRED_LIC_STATE': 'VIC', 'CRED_LIC_PCODE': '3004', 'CRED_LIC_LAT': '-37.8142454', 'CRED_LIC_LNG': '144.9631732', 'CRED_LIC_EDRS': 'AFCA', 'CRED_LIC_AUTHORISATIONS': 'This licence authorises the licensee to:~Engage in credit activities other than as a credit provider…'}`

---
To review: `python -m src.part2_agent.approve asic_credit_licensee`
