# Review packet: qld_health_contracts_2023_24 (config v1)

**Dataset:** System Procurement_Contract Disclosure Report — Queensland Health  
**Page:** https://www.data.qld.gov.au/dataset/system_procurement_contract-disclosure-report  
**Licence:** Creative Commons Attribution 4.0  
**File:** `sp_contract-disclosure-report-2023-24.csv` (sha256 `5fc64ed16718…`)  
**What the agent says it is:** Queensland Health system procurement contract disclosure report for 2023-24, listing contracts with supplier names, addresses, values and procurement details.  
**One row is:** one contract award line from the Queensland Health procurement disclosure report (multi-supplier contracts list several suppliers in one cell).

## How this was produced

- Model `claude-haiku-5-5`; 4 LLM calls; 61,752 input + 24,377 output tokens; cost $0.0182 (computed from list prices); LLM time 111.6s.
- Revision rounds: 0. Tested on 105 held-out rows the model never saw.
- Reader: `{'format': 'csv', 'encoding': 'utf-8', 'delimiter': ',', 'header_row': 1}`. Record id: `{'hash_row': True}` — Contract reference number is 97% filled but has 181 distinct values across 210 rows, and Supplier name and Supplier ABN repeat across rows and can hold several suppliers per cell, so no column set was verified as unique. Row hash used instead.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.6, 'address': 0.5, 'classification': 0.3, 'contact': 0.4}` — Statutory-style government procurement disclosure published by Queensland Health, so the publisher is authoritative about which supplier and ABN were contracted. Supplier identifiers and names are self-reported by agencies and show typos, mixed separators and placeholder values, so identity is moderate. Supplier addresses are often incomplete or placeholder, so address is lower. Contract categories are procurement labels rather than supplier classifications, so classification is low. No contact fields are present.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier name` | `entity.legal_name` | split(;) → clean_whitespace | 0.90 | 100.0% (ok 261, rejected 0) | **0.90** | agreed | `C4U Nursing Agency Pty Ltd` → `C4U Nursing Agency Pty Ltd`<br>`Affinity Nursing Recruitment Pty Ltd ATF The Affin` → `Affinity Nursing Recruitment Pty Ltd ATF The Affinity Trust`<br>`The Trustee for Faulkner Family Trust` → `The Trustee for Faulkner Family Trust` |
| 2 | `Supplier ABN` | `entity.abn` | split(;) → abn | 0.90 | 96.8% (ok 119, rejected 4) | **0.90** | agreed | `47 628 295 134` → `47628295134`<br>`17 526 203 210` → `17526203210`<br>`23 419 640 068` → `23419640068` |
| 3 | `Supplier name` | `entity.entity_type` | entity_type_from_suffix | 0.70 | 100.0% (ok 105, rejected 0) | **0.70** | agreed | `C4U Nursing Agency Pty Ltd` → `company`<br>`Affinity Nursing Recruitment Pty Ltd ATF The Affin` → `unknown`<br>`The Trustee for Faulkner Family Trust` → `unknown` |
| 4 | `Supplier address` | `address.full` | split(;) → clean_whitespace | 0.80 | 99.2% (ok 118, rejected 1) | **0.80** | agreed | `23  Riverpark Drive, Nerang QLD 4211` → `23 Riverpark Drive, Nerang QLD 4211`<br>`Suite 4, 1933 Logan Road, Upper Mount Gravatt, QLD` → `Suite 4, 1933 Logan Road, Upper Mount Gravatt, QLD 4122`<br>`5/2 Magnolia Drive, Brookwater QLD 4300` → `5/2 Magnolia Drive, Brookwater QLD 4300` |
| 5 | `Supplier address` | `address.postcode` | split(;) → regex_extract(\b(?:QLD|NSW|VIC|WA|SA|TAS|ACT|NT)\s+(\d{4})\b) → postcode | 0.70 | 96.8% (ok 91, rejected 3) | **0.70** | agreed | `23  Riverpark Drive, Nerang QLD 4211` → `4211`<br>`Suite 4, 1933 Logan Road, Upper Mount Gravatt, QLD` → `4122`<br>`5/2 Magnolia Drive, Brookwater QLD 4300` → `4300` |
| 6 | `Supplier address` | `address.state` | split(;) → regex_extract(\b(QLD|NSW|VIC|WA|SA|TAS|ACT|NT)\b) → state_code | 0.70 | 97.0% (ok 96, rejected 3) | **0.70** | agreed | `23  Riverpark Drive, Nerang QLD 4211` → `QLD`<br>`Suite 4, 1933 Logan Road, Upper Mount Gravatt, QLD` → `QLD`<br>`5/2 Magnolia Drive, Brookwater QLD 4300` → `QLD` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column is the contracted supplier name, which is the entity this row is about. Multi-supplier cells are split on ';' only, because the ABN and address lists use the same ';' separator. Some names embed a t/a trading name and some cells use commas; see needs_transform.
2. `entity.abn` ← `Supplier ABN`: Supplier ABN, split on ';' to align with supplier names, then checksum-validated. Values are mostly 11 digits with or without spaces. Labelled ABN/ACN tokens and comma-separated lists are not handled here.
3. `entity.entity_type` ← `Supplier name`: No explicit entity-type column exists, so the rule is applied to the supplier name suffix per rule 7. Names ending in Pty Ltd, Pty. Limited or Limited become company; everything else becomes unknown.
4. `address.full` ← `Supplier address`: Supplier address, which is the supplier's address and not the government agency's. Split on ';' to align with the supplier list. The placeholder value 0 and comma-separated multi-address cells are not handled here.
5. `address.postcode` ← `Supplier address`: Postcode is taken from the state-abbreviation-plus-4-digit pattern, which is anchored to the state so that street numbers are not picked up. Confidence is reduced because comma-separated multi-address cells would yield only the first match.
6. `address.state` ← `Supplier address`: State abbreviation taken from the supplier address. Confidence is reduced for the same comma-separated multi-address reason as postcode.

## Left unmapped (not guessed)

- `_id`: Completely empty column, ignored.
- `Agency (Dept or Stat Body)`: Government buyer, not the supplier entity. Not mapped per rule 4. Contains typos such as Queensl;and Health and QLD Health Services.
- `Agency address`: Government buyer address, not the supplier. Not mapped per rule 4.
- `Contract description/name`: Describes the contract, with no matching ontology field. Some values embed a [MULTI] or site code.
- `Award contract date`: Date of contract award. It is not a date_registered and not an entity status or licence start, so per rule 10 it is not mapped to valid_from.
- `Contract value`: Contract monetary value, with no ontology field. Contains non-numeric values such as the text '$10,000 or more' and '-'.
- `Variation to contract (Yes/No)`: Contract attribute with no ontology field. Mixed casing and stray values such as 1 and 2.
- `Specific confidentiality provision used`: Contract attribute with no ontology field.
- `Procurement method`: Contract attribute with no ontology field.
- `Justification (if limited tender)`: Free-text contract justification with no ontology field.
- `Form of contract`: Contract attribute with no ontology field.
- `Number of offers sought`: Contract attribute with no ontology field. Mixed content.
- `Evaluation criteria and weightings`: Contract attribute with no ontology field. Mixed content.
- `Deliverables`: Contract attribute with no ontology field. Mostly the placeholder 0.
- `Contract milestones`: Contract attribute with no ontology field. Only the placeholder 0.
- `Contract performance management`: Contract attribute with no ontology field. Mostly the placeholder 0.
- `Contract reference number`: Contract identifier, not unique per row, so not used as record_id. No ontology field.
- `Contract category group`: Procurement category of the contract, not the supplier's industry. Mapping it to entity.industry_code would misclassify the supplier, so it is not mapped.
- `Parent contract number/SOA`: Contract hierarchy identifier with no ontology field.
- `Commence date`: Contract period start, not a licence or status start and not a registration date. Not used for valid_from per rule 10.
- `Finish date`: Contract period end, not a licence or status end. Not used for valid_to per rule 10.

## Needs a transform the engine does not have

- `Supplier address`: Placeholder value 0 appears in about 15 rows and is not a real address. No transform blanks it, and map_values cannot safely map it to absent.
- `Supplier name`: Some multi-supplier cells are comma-separated, for example Slade Health Pty Ltd, Wesley Pharmacy Pty Ltd, Baxter Healthcare Pty Ltd. A split on ',' is unsafe because addresses contain commas, so these cells stay unsplit and misaligned.
- `Supplier name`: Trading names are embedded as '(t/a ...)', for example heyCKW Pty Ltd (t/a HeyProcurement). Only one sample is visible, so the pattern is not yet confirmed as consistent enough for regex_extract into trading_name.
- `Supplier ABN`: Some cells use labelled tokens such as ABN and ACN with '/' separators (Major Medical Equipment Framework row), and some use comma-separated lists (Slade row). The ACN values need a label-aware extraction and are not mapped to entity.acn.
- `Supplier address`: Comma-separated multi-address cells (Slade row) are not split on ';', so their items cannot be aligned with the supplier list.

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 105}
- Proposal disagreements (two independent proposals): only-1 0, only-2 0; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

The mapping matches every example row. Legal names, ABNs (11 digits, with or without spaces), supplier addresses, postcodes and states are mapped to the right fields. Government buyer and agency columns are correctly excluded, and entity_type is 'company' only where the name ends in Pty Ltd or Limited, otherwise 'unknown'. The Core Connect row correctly yields state NSW with no postcode, because the comma-separated address does not match the postcode pattern. No meaning errors are visible in the examples.

## What changed during revision

- No revisions were needed.

## Three sample rows, raw

- `{'Agency (Dept or Stat Body)': 'Queensland Health', 'Agency address': "41 O'Connell Terrace, Bowen Hills", 'Contract description/name': 'CSCSD111539 Deed of Variation to Preferred Supplier Panel for the Provision of Clinical Contingent W…', 'Award contract date': '29/11/2022', 'Contract value': '$10,000.00', 'Supplier name': 'C4U Nursing Agency Pty Ltd', 'Supplier address': '23 Riverpark Drive, Nerang QLD 4211', 'Variation to contract (Yes/No)': 'Yes', 'Specific confidentiality provision used': 'No', 'Procurement method': 'Variation', 'Justification (if limited tender)': 'Superannuation guarantee increase from 10.5% to 11% applicable 1/7/2023 5.75% in modern award applic…', 'Form of contract': 'Standing Offer Arrangement (SOA)', 'Contract reference number': 'CSCSD111539-38', 'Contract category group': 'Medical Services', 'Parent contract number/SOA': 'CSCSD111539', 'Commence date': '17/07/2023', 'Supplier ABN': '47 628 295 134', 'Finish date': '30/11/2027'}`
- `{'Agency (Dept or Stat Body)': 'Queensland Health', 'Agency address': "41 O'Connell Terrace, Bowen Hills", 'Contract description/name': 'CSCSD111539 Deed of Variation to Preferred Supplier Panel for the Provision of Clinical Contingent W…', 'Award contract date': '29/11/2022', 'Contract value': '$10,000.00', 'Supplier name': 'Affinity Nursing Recruitment Pty Ltd ATF The Affinity Trust', 'Supplier address': 'Suite 4, 1933 Logan Road, Upper Mount Gravatt, QLD 4122', 'Variation to contract (Yes/No)': 'Yes', 'Specific confidentiality provision used': 'No', 'Procurement method': 'Variation', 'Justification (if limited tender)': 'Change to Overtime Penalty Rates Schedule 2 clause 3.4', 'Form of contract': 'Standing Offer Arrangement (SOA)', 'Contract reference number': 'CSCSD111539-28', 'Contract category group': 'Medical Services', 'Parent contract number/SOA': 'CSCSD111539', 'Commence date': '31/07/2023', 'Supplier ABN': '17 526 203 210', 'Finish date': '30/11/2027'}`
- `{'Agency (Dept or Stat Body)': 'Queensland Health', 'Agency address': "41 O'Connell Terrace, Bowen Hills", 'Contract description/name': 'CSCSD111539 Deed of Variation to Preferred Supplier Panel for the Provision of Clinical Contingent W…', 'Award contract date': '29/11/2023', 'Contract value': '$10,000 or more', 'Supplier name': 'The Trustee for Faulkner Family Trust', 'Supplier address': '5/2 Magnolia Drive, Brookwater QLD 4300', 'Variation to contract (Yes/No)': 'Yes', 'Specific confidentiality provision used': 'No', 'Procurement method': 'Variation', 'Justification (if limited tender)': 'Superannuation guarantee increase from 10.5% to 11% applicable 1/7/2023 Change to Overtime Penalty R…', 'Form of contract': 'PSP', 'Contract reference number': 'CSCSD111539-63', 'Contract category group': 'Medical Services', 'Parent contract number/SOA': 'CSCSD111539', 'Commence date': '1/07/2023', 'Supplier ABN': '23 419 640 068', 'Finish date': '30/11/2027'}`

---
To review: `python -m src.part2_agent.approve qld_health_contracts_2023_24`
