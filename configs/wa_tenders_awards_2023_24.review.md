# Review packet: wa_tenders_awards_2023_24 (config v3)

**Dataset:** Tenders WA Contract Award Details 2023-24 Financial Year — Department of Treasury and Finance  
**Page:** https://data.gov.au/data/dataset/tenders-wa-contract-award-details-2023-24-financial-year  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `tenders-wa-contract-award-details-2023-24-financial-year.csv` (sha256 `a6e9859f99ba…`)  
**What the agent says it is:** Western Australian government tender contract award register for the 2023-24 financial year, listing public authority procurements with awarded suppliers and UNSPSC classifications.  
**One row is:** One tender or contract award (procurement reference) made by a WA public authority.

## How this was produced

- Model `claude-haiku-5-5`; 7 LLM calls; 129,895 input + 42,758 output tokens; cost $0.0317 (computed from list prices); LLM time 176.5s.
- Revision rounds: 2. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'csv', 'encoding': 'utf-8', 'delimiter': ',', 'header_row': 1}`. Record id: `{'hash_row': True}` — Reference_Number has 4919 distinct values across 5817 rows, so it is not unique. No verified unique column set exists, so the row is hashed.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `{'source': 'Commencement_Date', 'transforms': [{'name': 'parse_date', 'arg': '%d/%m/%Y'}]}`. valid_to: `{'source': 'Final_Expiry_Date', 'transforms': [{'name': 'parse_date', 'arg': '%d/%m/%Y'}]}`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.7, 'address': 0.6, 'classification': 0.4, 'contact': 0.5}` — WA Government statutory tender-award disclosure, published by the Department of Treasury and Finance. Strong for the fact that a contract was awarded to a named supplier. Supplier names and addresses are as entered by buying agencies (inconsistent casing, 'Trading (Legal)' mixes), so identity and address are rated below a statutory company register. Classification (UNSPSC) describes goods or services rather than supplier industry and is weak for entity classification. Contact is not provided by the source, so 0.5 is used as an uninformed default.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier_Address` | `address.full` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `Level 7, 68 Harrington St, The Rocks, 2000` → `Level 7, 68 Harrington St, The Rocks, 2000`<br>`727-729 High Rd, London, N120BP` → `727-729 High Rd, London, N120BP`<br>`GPO Box 3868, Sydney, 2001` → `GPO Box 3868, Sydney, 2001` |
| 2 | `Supplier_Address` | `address.postcode` | clean_whitespace → regex_extract((\d{4})\s*$) → postcode | 0.85 | 100.0% (ok 294, rejected 0) | **0.85** | agreed | `Level 7, 68 Harrington St, The Rocks, 2000` → `2000`<br>`GPO Box 3868, Sydney, 2001` → `2001`<br>`76 Heathcote Road, Moorebank, 2170` → `2170` |
| 3 | `Supplier_Name` | `entity.entity_type` | entity_type_from_suffix | 0.60 | 100.0% (ok 300, rejected 0) | **0.60** | resolved_by_revision | `Finity Consulting Pty Limited` → `company`<br>`Delivery Associates (Delivery Associates Limited)` → `company`<br>`Hays Specialist Recruitment (Australia) PL` → `unknown` |

Model's reasons per field (its words, not verified):

1. `address.full` ← `Supplier_Address`: Supplier_Address is the awarded supplier's address, and the column name and sample values agree.
2. `address.postcode` ← `Supplier_Address`: Every sample address ends with a 4-digit postcode, so the trailing 4 digits are extracted and normalised.
3. `entity.entity_type` ← `Supplier_Name`: The source has no explicit entity-type column, so the suffix rule applies per ontology rule 7. Names ending in Pty Ltd, Limited or Ltd give company; names ending in ')' or with no legal suffix give unknown. Confidence is moderate because a legal suffix is a proxy for entity type.

## Left unmapped (not guessed)

- `Public_Authority`: government buyer: the WA public authority is the buyer, not the supplier entity this row describes
- `Public_Authority_Address`: government buyer: address of the public authority, not the supplier
- `Title`: procurement title describing the contract; no ontology field for contract or tender descriptions
- `Reference_Number`: procurement reference, not unique across rows (4919 distinct / 5817 rows), so it cannot be record_id; no ontology field for it
- `Description`: free-text procurement description; no ontology field
- `Type_of_Work`: procurement category (Goods & Services / Works); no ontology field
- `Procurement_Method`: procurement process method; no ontology field
- `Associated_With_Tender`: reference to a related tender; no ontology field
- `UNSPSC_Code_1`: UNSPSC code describes the goods or services procured under the contract, not the supplier's industry, so it is not mapped to entity.industry_code (which is ANZSIC-oriented)
- `UNSPSC_Title_1`: UNSPSC description of the procured goods or services, not supplier industry
- `UNSPSC_Percent_1`: share of contract allocated to UNSPSC_Code_1; no ontology field
- `UNSPSC_Code_2`: UNSPSC code of the procured goods or services, not supplier industry
- `UNSPSC_Title_2`: UNSPSC description of the procured goods or services, not supplier industry
- `UNSPSC_Percent_2`: share of contract allocated to UNSPSC_Code_2; no ontology field
- `UNSPSC_Code_3`: UNSPSC code of the procured goods or services, not supplier industry
- `UNSPSC_Title_3`: UNSPSC description of the procured goods or services, not supplier industry
- `UNSPSC_Percent_3`: share of contract allocated to UNSPSC_Code_3; no ontology field
- `Gascoyne`: regional delivery flag; no ontology field
- `Goldfields_Esperance`: regional delivery flag; no ontology field
- `Great_Southern`: regional delivery flag; no ontology field
- `Kimberley`: regional delivery flag; no ontology field
- `Mid_West`: regional delivery flag; no ontology field
- `Peel`: regional delivery flag; no ontology field
- `Perth_Metropolitan`: regional delivery flag; no ontology field
- `Pilbara`: regional delivery flag; no ontology field
- `South_West`: regional delivery flag; no ontology field
- `Wheatbelt`: regional delivery flag; no ontology field
- `State_Wide`: regional delivery flag; no ontology field
- `Interstate`: delivery scope flag; not a supplier address state, so it is not mapped to address.state
- `International`: delivery scope flag; no ontology field
- `Number_of_Submissions`: count of tender submissions; no ontology field
- `Panel_Contract`: panel-contract flag; no ontology field
- `Contract_Term`: contract term type; no ontology field
- `Closing_Date`: tender closing date; no ontology field
- `Award_Date`: date of award; the ontology has no award date and date_registered applies only to entity registration
- `Initial_Expiry_Date`: initial contract expiry; no ontology field, and valid_to uses Final_Expiry_Date
- `Original_Contract_Value`: contract value; no ontology field
- `Original_Contract_Value_Type`: contract value basis (estimate or fixed price); no ontology field
- `CUA_Number`: common use arrangement reference; no ontology field

## Needs a transform the engine does not have

- `Supplier_Name`: Supplier_Name does not reliably carry the registered name. About 44% of values have no brackets (e.g. 'Peoplebank Australia Limited', 'Shorewater Marine'), and in bracketed values the Pty Ltd registered name may sit outside the brackets (e.g. 'Thermo Fisher Australia Pty Ltd (Thermo Fisher Scientific Australia Pty Ltd)'). Deciding which part is the registered name, and which is the trading name, needs a transform that identifies the registered name from the text. No such transform exists, so entity.legal_name and entity.trading_name are not mapped from this column.

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 2, only-2 1; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

Most mappings are sound: the buyer and government columns are correctly excluded, the address and postcode mappings are correct, and the 'Trading (Legal)' convention holds in most rows. The main meaning errors are the regex failure on names with nested parentheses (producing a corrupted legal name for Jones Lang Lasalle), the entity_type output that contradicts the documented rule, and contract dates being applied as entity validity dates across all observations.
- `entity.legal_name and entity.trading_name (Supplier_Name regex_extract)`: The patterns use a lazy prefix that stops at the first '(', so names containing their own parentheses are split wrongly. 'Jones Lang Lasalle (WA) (Jones Lang Lasalle (WA) Pty Ltd)' yields legal_name 'WA) (Jones Lang Lasalle (WA) Pty Ltd' (a corrupted registered name) and trading_name 'Jones Lang Lasalle' (missing '(WA)'). (suggested: Anchor on the last parenthetical with a greedy prefix, e.g. legal_name '^(.+)\s*\(([^()]+)\)\s*$' taking group 2 and trading_name taking group 1, or exclude nested parentheses explicitly. Re-test on rows with parentheses inside the name, and lower mapping_confidence until the convention is verified on those rows.)
- `entity.entity_type`: The config reason says parenthetical 'Trading (Legal)' cells end in ')' and return 'unknown'. The observations contradict this: Integrity Executive, Dale Alcock Homes, Multicam, Hays, Talent International and Jones Lang Lasalle all emit 'company', while Marty Grant and Mediquip emit 'unknown'. The stated rule and the actual output do not match, so the classification cannot be trusted as documented. (suggested: Decide explicitly whether the suffix test runs on the raw cell or on the extracted legal name. If it is the legal name, correct the reason text and keep the mapping only where the legal name is a company suffix. Otherwise return 'unknown' for parenthetical rows as documented. Lower mapping_confidence accordingly.)
- `envelope.valid_to (Final_Expiry_Date) and envelope.valid_from (Commencement_Date)`: These are contract dates, but the envelope applies them to every observation in the row, including entity.legal_name, trading_name, entity_type and address. For example, the legal-name claim for Multicam carries valid_to 2023-12-06, which reads as the entity's validity end, not the contract's. Rule 10 allows valid_from/valid_to only for when a licence or status started or ended. (suggested: Do not use contract commencement and expiry as the validity of entity or address observations. Either leave valid_from/valid_to empty, or scope the dates to a contract-relationship observation type that the ontology supports, and record in the reason that they describe the contract term.)

## What changed during revision

**r1**
- Added entity.entity_type from Supplier_Name via entity_type_from_suffix (mapping_confidence 0.6). — Proposal 2 mapped this on evidence from its own sample rows. The source has no explicit entity-type column, so rule 7 permits the suffix rule. Parenthetical cells return unknown, so the change does not over-claim.
- Kept entity.legal_name and entity.trading_name regex extraction unchanged. — Both proposals agreed on the 'Trading (Legal)' regex pattern. The pattern is consistent in the samples. The two proposals differed only in coverage, not in the regex itself, so no change is justified.
- Kept all other fields, unmapped entries, needs_transform, observed_at, valid_from, valid_to, record_id and source reliability unchanged. — The held-out report raises no evidence against them. The report's findings concern only the entity-type and name-extraction coverage.
**human_1**
- Removed the entity.legal_name mapping from Supplier_Name (regex_extract of the parenthetical). — Reviewer found the bracketed text is not always the registered name: the Pty Ltd name can sit outside the brackets, and 44% of names have no brackets. The parenthetical rule therefore assigns the wrong claim to legal_name. Rule 5 requires a consistent pattern before extracting, and none exists.
- Removed the entity.trading_name mapping from Supplier_Name (regex_extract of text before the parenthetical). — Same defect: the text before the brackets is not reliably a trading name. Mapping it would publish a wrong trading name for many rows.
- Rewrote the needs_transform entry for Supplier_Name. — The gap is no longer only the missing fallback for unbracketed names. The registered name cannot be identified from the text with the available transforms, so the column is needs_transform, not mapped.
- Kept entity.entity_type (entity_type_from_suffix), address.full, address.postcode, record_id, observed_at, valid_from, valid_to, and all unmapped entries unchanged. — The reviewer did not flag these. The entity_type rule depends only on the suffix test, which remains valid for unbracketed names; bracketed names return unknown, which is the conservative default.

## Three sample rows, raw

- `{'Public_Authority': 'Building and Construction Industry Training Board', 'Public_Authority_Address': '104 Belgravia Street, Belmont, 6104', 'Title': 'Actuary Services 2024 Statutory Review of the BCIT Fund and Levy Collection Act 1990', 'Reference_Number': 'CTF2024010', 'Description': 'The Customer is seeking offers for the provision of Actuary services to assist in the 2024 Statutory…', 'Type_of_Work': 'Goods & Services', 'Procurement_Method': 'Limited Sourcing', 'Associated_With_Tender': 'Actuary Services ? 2024 Statutory Review of the Building and Construction Industry Training Fund and…', 'UNSPSC_Code_1': '80101500', 'UNSPSC_Title_1': 'Business and corporate management consultation services', 'UNSPSC_Percent_1': '100', 'Gascoyne': 'No', 'Goldfields_Esperance': 'No', 'Great_Southern': 'No', 'Kimberley': 'No', 'Mid_West': 'No', 'Peel': 'No', 'Perth_Metropolitan': 'Yes', 'Pilbara': 'No', 'South_West': 'No', 'Wheatbelt': 'No', 'State_Wide': 'No', 'Interstate': 'No', 'International': 'No', 'Number_of_Submissions': '1', 'Panel_Contract': 'No', 'Contract_Term': 'One Off Contract', 'Closing_Date': '21/02/2024', 'Award_Date': '31/03/2024', 'Original_Contract_Value': '88000', 'Original_Contract_Value_Type': 'Fixed Price', 'Supplier_Name': 'Finity Consulting Pty Limited', 'Supplier_Address': 'Level 7, 68 Harrington St, The Rocks, 2000'}`
- `{'Public_Authority': 'Department of Communities', 'Public_Authority_Address': '5 Newman Court, Fremantle, 6000', 'Title': 'Delivery Planning Support Services for Family and Domestic Violence Taskforce', 'Reference_Number': 'DOC202413869', 'Description': 'The Department of Communities (Communities) has a requirement for the Contractor to finalise a Famil…', 'Type_of_Work': 'Goods & Services', 'Procurement_Method': 'Limited Sourcing', 'Associated_With_Tender': 'Delivery Planning Support Services for Family and Domestic Violence Taskforce (DOC202413869)', 'UNSPSC_Code_1': '80101600', 'UNSPSC_Title_1': 'Project management', 'UNSPSC_Percent_1': '100', 'Gascoyne': 'No', 'Goldfields_Esperance': 'No', 'Great_Southern': 'No', 'Kimberley': 'No', 'Mid_West': 'No', 'Peel': 'No', 'Perth_Metropolitan': 'Yes', 'Pilbara': 'No', 'South_West': 'No', 'Wheatbelt': 'No', 'State_Wide': 'No', 'Interstate': 'No', 'International': 'No', 'Number_of_Submissions': '2', 'Panel_Contract': 'No', 'Contract_Term': 'One Off Contract', 'Closing_Date': '15/03/2024', 'Award_Date': '12/04/2024', 'Commencement_Date': '12/04/2024', 'Initial_Expiry_Date': '31/07/2024', 'Final_Expiry_Date': '31/07/2024', 'Original_Contract_Value': '180000', 'Original_Contract_Value_Type': 'Fixed Price', 'Supplier_Name': 'Delivery Associates (Delivery Associates Limited)', 'Supplier_Address': '727-729 High Rd, London, N120BP'}`
- `{'Public_Authority': 'Department of Primary Industries and Regional Development', 'Public_Authority_Address': 'Gordon Stephenson House, 140 Williams Street, Perth, 6000', 'Title': 'Assistant Accountant', 'Reference_Number': 'DPIRD2024011', 'Description': 'Assistant Accountant', 'Type_of_Work': 'Goods & Services', 'Procurement_Method': 'CUA', 'UNSPSC_Code_1': '84111508', 'UNSPSC_Title_1': 'Export administration and accounting service', 'UNSPSC_Percent_1': '100', 'Gascoyne': 'No', 'Goldfields_Esperance': 'No', 'Great_Southern': 'No', 'Kimberley': 'No', 'Mid_West': 'No', 'Peel': 'No', 'Perth_Metropolitan': 'Yes', 'Pilbara': 'No', 'South_West': 'No', 'Wheatbelt': 'No', 'State_Wide': 'No', 'Interstate': 'No', 'International': 'No', 'Number_of_Submissions': '1', 'Panel_Contract': 'No', 'Contract_Term': 'One Off Contract', 'Closing_Date': '17/07/2023', 'Award_Date': '17/07/2023', 'Commencement_Date': '17/07/2023', 'Initial_Expiry_Date': '31/03/2024', 'Final_Expiry_Date': '31/03/2024', 'Original_Contract_Value': '53831', 'Original_Contract_Value_Type': 'Estimate', 'CUA_Number': 'CUATPS2019 - Temporary Personnel Services Common Use Arrangement (CUA)', 'Supplier_Name': 'Hays Specialist Recruitment (Australia) PL', 'Supplier_Address': 'GPO Box 3868, Sydney, 2001'}`

---
To review: `python -m src.part2_agent.approve wa_tenders_awards_2023_24`
