# Review packet: qbcc_licensed_contractors (config v3)

**Dataset:** QBCC Licensed Contractors Register — Queensland Building and Construction Commission  
**Page:** https://www.data.qld.gov.au/dataset/qbcc-licensed-contractors-register  
**Licence:** Creative Commons Attribution 4.0  
**File:** `active_licensees.csv` (sha256 `dae86a9b27e1…`)  
**What the agent says it is:** QBCC register of licensed builders and contractors in Queensland, listing individual licensees with their licence numbers, identifiers and addresses.  
**One row is:** one licence-class authorisation held by a licensee (the same licensee appears on multiple rows, one per licence class).

## How this was produced

- Model `claude-haiku-5-5`; 6 LLM calls; 63,923 input + 20,544 output tokens; cost $0.0138 (computed from list prices); LLM time 88.5s.
- Revision rounds: 2. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'csv', 'encoding': 'utf-8', 'delimiter': ',', 'header_row': 1}`. Record id: `{'from': ['id']}` — id has 206548 distinct values across 206548 rows, so it uniquely identifies each licence-class row.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.9, 'address': 0.8, 'classification': 0.85, 'contact': 0.6}` — QBCC is the statutory licensing regulator for Queensland building and construction, so its register is high-trust for licence identity and classification (licence class, grade, financial category). Business addresses are self-reported by licensees, so address trust is lower. Contact details are not in the dataset, so contact is set low. Licensee names are as recorded by the regulator, which is good for identity but may vary in case and format across rows.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `SHAKAR PAINTING GROUP PTY LTD` → `SHAKAR PAINTING GROUP PTY LTD`<br>`Michael William Argus` → `Michael William Argus`<br>`CHRISTOPHER JAMES SYRON` → `CHRISTOPHER JAMES SYRON` |
| 2 | `ABN` | `entity.abn` | abn | 0.95 | 98.7% (ok 155, rejected 2) | **0.95** | agreed | `13 130 681 168` → `13130681168`<br>`70 293 844 644` → `70293844644`<br>`62 677 609 832` → `62677609832` |
| 3 | `ACN` | `entity.acn` | acn | 0.95 | 100.0% (ok 64, rejected 0) | **0.95** | agreed | `130 681 168` → `130681168`<br>`651 261 228` → `651261228`<br>`633 159 618` → `633159618` |
| 4 | `Licensee Business Address` | `address.full` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `14 ISAAC STREET WESTBROOK QLD 4350` → `14 ISAAC STREET WESTBROOK QLD 4350`<br>`26 SPINA CRES CARSELDINE QLD 4034` → `26 SPINA CRES CARSELDINE QLD 4034`<br>`370 St Vincent Road Nundah Queensland 4014` → `370 St Vincent Road Nundah Queensland 4014` |
| 5 | `Licensee Business Address` | `address.state` | regex_extract(\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\s+\d{4}\s*$) → state_code | 0.85 | 100.0% (ok 294, rejected 0) | **0.85** | agreed | `14 ISAAC STREET WESTBROOK QLD 4350` → `QLD`<br>`26 SPINA CRES CARSELDINE QLD 4034` → `QLD`<br>`6 Lovell Ct Worongary QLD 4213` → `QLD` |
| 6 | `Licensee Business Address` | `address.postcode` | regex_extract((\d{4})\s*$) → postcode | 0.85 | 100.0% (ok 300, rejected 0) | **0.85** | agreed | `14 ISAAC STREET WESTBROOK QLD 4350` → `4350`<br>`26 SPINA CRES CARSELDINE QLD 4034` → `4034`<br>`370 St Vincent Road Nundah Queensland 4014` → `4014` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the registered licensee name on the QBCC register. It holds person names for individuals and company names for companies, which rule 4 maps as legal_name. Mixed case is preserved, so no case normalisation is applied.
2. `entity.abn` ← `ABN`: Column is labelled ABN and all sampled values are 11 digits in grouped form (e.g. '51 166 281 223'). The abn transform performs the checksum. Engine must confirm it strips the internal spaces; if not, values will be rejected and shown back.
3. `entity.acn` ← `ACN`: Column is labelled ACN and profile shows 100% 9-digit values in grouped form (e.g. '166 281 223'). The acn transform performs the checksum. The column is only ~24% filled, which is expected for individual licensees.
4. `address.full` ← `Licensee Business Address`: Single free-text business address including street, locality, state and postcode. Kept whole as the full address.
5. `address.state` ← `Licensee Business Address`: State abbreviation sits immediately before the 4-digit postcode at the end of the address in all sampled rows. Some rows are NSW or SA, so the pattern covers all states and territories.
6. `address.postcode` ← `Licensee Business Address`: Trailing 4-digit number of the address is the postcode in all sampled rows. The postcode transform guards the format.

## Left unmapped (not guessed)

- `Licence Number`: Per-licence identifier. Ontology v0.1 has no licence-number field, and it is not an entity identifier, so it is not mapped.
- `Licence Type CODE`: Duplicate of Licence Type DESC (I/C codes). Carries the same Individual/Company split; the Company mapping is carried by Licence Type DESC, so this duplicate is not mapped.
- `Financial Category DESC`: Regulatory financial-category classification. Ontology v0.1 has no field for it.
- `Financial Category CODE`: Code form of Financial Category DESC. Ontology v0.1 has no field for it.
- `Licence Grade`: Licence grade (builder, trade contractor, supervisor, etc.) is a licence attribute, not an entity status or industry code. Ontology v0.1 has no field for it.
- `Licence Class Type`: Licence class (e.g. Carpentry, Builder - Open) is a regulatory authorisation category, not an ANZSIC industry code. Rule 9 forbids translating it, and the ontology has no licence-class field, so it is not mapped to industry_code.
- `Licence Type DESC`: abstained (entity.entity_type): still failing after 2 revision(s): parse rate 21% is below 90%

## Needs a transform the engine does not have

- `Licensee Business Address`: Locality (suburb/town) is embedded in the free-text address with no delimiter before it. The street portion varies in format (e.g. 'Shed 2 58 Islander Rd Pialba', 'Torbanlea Torbanlea QLD 4662'), so no existing transform can isolate it reliably. Requires a locality-extraction transform before address.locality can be mapped.

## Checks

- No meaning warnings on held-out rows.
- ℹ️ Where one entity has both an ABN and an ACN (56 cases), the ACN equals the last 9 digits of the ABN in 95%. Reported as evidence only; not assumed anywhere.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 0, only-2 0; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: ['entity.entity_type<-Licence Type DESC']

## Critique step (reads raw rows next to output)

The mapping is largely sound: ABN and ACN are checksum-mapped, legal_name is correctly the licensee name, and address state and postcode extraction matches the samples. The main concern is that entity_type is removed wholesale, so explicit 'Company' rows lose a deterministic classification that could be mapped safely.
- `entity.entity_type`: The example for AMZ/SHAKAR-style company rows (e.g. SHAKAR PAINTING GROUP PTY LTD, Licence Type DESC 'Company') emits entity.entity_type = 'unknown' even though the source has an explicit column that identifies companies. The config drops the field entirely, so the engine's default is shown for rows where the source does state the entity type. This loses a usable, unambiguous signal for the Company rows. (suggested: Map Licence Type DESC via map_values, with {"Company": "company"} only, and leave "Individual" out so it is rejected and not guessed as sole_trader. Keep the Individual rows as unknown. This matches rule 7 and avoids the sole_trader guess.)

## What changed during revision

**r1**
- Removed the entity.entity_type field (map_values on Licence Type DESC) from fields. — Hard failure: parse rate 21% against a 90% minimum, with 236 Individual rejections. Individual has no ontology value that fits without guessing (rule 4 forbids inferring sole_trader), and mapping it to unknown would inflate the parse rate with a default rather than a real mapping.
- Moved Licence Type DESC from fields to unmapped with a reason. — Rule 2 and the failure instruction: a field that cannot be made to work is removed and its column listed under unmapped. Company alone would not clear the parse-rate threshold.
- Updated the Licence Type CODE unmapped reason. — The previous reason said DESC was mapped to entity_type, which is no longer true.
**critique**
- Added entity.entity_type field sourced from Licence Type DESC using map_values {"Company": "company"} only. — The source has an explicit entity-type column. Company rows are unambiguous and were previously left as the engine default 'unknown' although the source states the type. Rule 7 permits map_values on an explicit column.
- Removed Licence Type DESC from unmapped. — The column is now used in fields (entity.entity_type), so rule 3 is satisfied by the field mapping rather than an unmapped entry.
- Individual values are deliberately not in the map_values table. — Individual has no ontology equivalent for natural-person licensees; mapping it to sole_trader would be a guess (rule 4), and mapping it to unknown would count the engine default as a parsed value. Rejection leaves these rows as unknown.
- No other fields changed. — The reviewer raised only the entity_type issue; the remaining mappings, record_id, observed_at and reliability scores were not challenged by the report.

## Three sample rows, raw

- `{'id': '61525', 'Licence Number': '1151428', 'Licensee Name': 'SHAKAR PAINTING GROUP PTY LTD', 'ACN': '130 681 168', 'ABN': '13 130 681 168', 'Licensee Business Address': '14 ISAAC STREET WESTBROOK QLD 4350', 'Licence Type DESC': 'Company', 'Licence Type CODE': 'C', 'Financial Category DESC': 'Category 1', 'Financial Category CODE': '1', 'Licence Grade': 'Trade Contractor Licence', 'Licence Class Type': 'Painting and Decorating'}`
- `{'id': '115111', 'Licence Number': '15576933', 'Licensee Name': 'Michael William Argus', 'ABN': '70 293 844 644', 'Licensee Business Address': '26 SPINA CRES CARSELDINE QLD 4034', 'Licence Type DESC': 'Individual', 'Licence Type CODE': 'I', 'Financial Category DESC': 'Self Certification - Builder/Trade', 'Financial Category CODE': 'SC2', 'Licence Grade': 'Trade Contractor Licence', 'Licence Class Type': 'Sheds, Carports and Garages'}`
- `{'id': '181253', 'Licence Number': '732805', 'Licensee Name': 'CHRISTOPHER JAMES SYRON', 'ABN': '62 677 609 832', 'Licensee Business Address': '370 St Vincent Road Nundah Queensland 4014', 'Licence Type DESC': 'Individual', 'Licence Type CODE': 'I', 'Financial Category DESC': 'Self Certification - Builder/Trade', 'Financial Category CODE': 'SC2', 'Licence Grade': 'Trade Contractor Licence', 'Licence Class Type': 'Joinery'}`

---
To review: `python -m src.part2_agent.approve qbcc_licensed_contractors`
