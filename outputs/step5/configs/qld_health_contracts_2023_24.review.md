# Review packet (round-2 agent): validated_config

**Dataset:** System Procurement_Contract Disclosure Report — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `sp_contract-disclosure-report-2023-24.csv` (sha256 `5fc64ed16718…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0136, 63.38s (download and human waits excluded). Trace: `logs/agent_runs/qld_health_contracts_2023_24/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "cp1252", "header_rows": 1, "skip_rows": 0}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. _id | Agency (Dept or Stat Body) | Agency address | Contract description/name | Award contract date |   Contract value   | Supplier name | Supplier address | Variation to contract (Yes/No) | Specific confidentiality provision used | Procurement method | Justification (if limited tender) | Form of contract | Number of offers sought | Evaluation criteria and weightings
2. ∅ | QLD Health | 41 O'Connell Terrace, Bowen Hills | Cytotoxic Pharmaceuticals (including Mon | 2/01/2018 | $313,200,000.00 | Slade Health Pty Ltd, Wesley Pharmacy Pt | Unit 11, 210 Robinson Road East, Geebung | Yes | No | Extension | N/A | Standing Offer Arrangement (SOA) | ∅ | ∅
3. ∅ | QLD Health Services | 41 O'Connell Terrace, Bowen Hills | Service Maintenance [Tissue Processors]  | 8/03/2018 | $2,318,000.00 | EVIDENT AUSTRALIA PTY LTD | Level 4, 97 Waterloo Rd, McQuarie Park N | Yes | No | Price Increase | ∅ | Standing Offer Arrangement (SOA) | 0 | 0
4. ∅ | QLD Health Services | 41 O'Connell Terrace, Bowen Hills | Service Maintenance[Qiagen][Purifiers/An | 18/04/2019 | $3,495,100.62 | QIAGEN PTY LTD | 1894 Dandenong Rd, Clayton VIC 3168 | YES | No | Adding Equipment | N/A | Standing Offer Arrangement (SOA) | 0 | 0
5. ∅ | Queensland Health | 33 Charlotte Street, Brisbane | Mobile Dental Clinics, Single Surgery [S | 25/09/2020 | $6,274,277.00 | Traymark Industrial Caravans Pty Ltd | ∅ | YES | ∅ | SOA | N/A | SOA | ∅ | ∅
6. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Automated Molecular Systems | 27/02/2020 | $15,641,804.00 | Hologic Pty Ltd | Level 3, 2 Lyon Park Road, Macquarie Par | Yes | No | SOA | N/A | Chage Notice | 3 | 0
7. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Panel for Clinical Contingent Workforce | 29/11/2022 | $1,460,000,000.00 | 1 Medical PTY LTD; ACM Recruitment PTY L | Level 15, 1 Castlereagh Street, SydneyNS | No | No | Open tender | N/A | PSP | ∅ | Capability, capacity and experience; Can
8. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Opthalmic Surgical Implants & Consumable | 5/01/2023 | $172,156,697.00 | ABBOTT MEDICAL AUSTRALIA PTY LTD; B BRAU | 299 Lane Cove Rd, MACQUARIE PARK NSW 211 | Yes | No | Extension/Variation | Current agreement extension | Extension #3 with new expiry 30/06/2026 | Deed of Variation | 0
9. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Specialist Orthopaedic Implants & Access | 7/10/2023 | $58,339,484.00 | Akva Surgical; Arthrex Australia; CONMED | Suite 26, 574 Plummer St, PORT MELBOURNE | Yes | No | Extension/Variation | Current agreement extension | Extension  with new expiry 30/09/2026 | Deed of Variation | 0
10. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Urogenital and General Miscellaneous Imp | 7/10/2023 | $24,649,023.00 | 3D Matrix Medical Technology P/L; ALLIAN | Level 12 Melbourne Central Tower, 360 El | Yes | No | Extension/Variation | Current agreement extension | Extension  with new expiry 31/10/2026 | Deed of Variation | 0
11. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Bone Graft Substitutes, Bone Cement and  | 1/11/2023 | $20,194,842.00 | DEVICE TECHNOLIGIES AUSTRALIA PTY LTD; H | 6-8 Compark Circuit, MULGRAVE VIC 3170;  | No | No | Open Tender | ∅ | Standing Offer Arrangement (SOA) | ∅ | 0
12. ∅ | Queensland Health | 41 O'Connell Terrace, Bowen Hills | Relocation of Dental/BreastSCreen Vans | 3/07/2023 | $200,000.00 | Clayton's Towing Service Pty Ltd, Harvey | 563 Bli Bli Road Nambour QLD 4560, 3820- | No | No | Open   | N/A | SOA | 5 | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier name` | `entity.legal_name` | clean_whitespace [when {"column": "Supplier ABN", "matches": "^\\s*\\d{2} ?\\d{3} ?\\d{3} ?\\d{3}\\s*$"}] | P | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `Supplier ABN` | `entity.abn` | regex_replace({'pattern': ' ', 'repl': ''}) → abn | P | held_out | 0.90 | 99.0% | **0.90** |
| 3 | `Supplier address` | `address.full` | regex_extract(^(.*[A-Za-z].*)$) → clean_whitespace [when {"column": "Supplier ABN", "matches": "^\\s*\\d{2} ?\\d{3} ?\\d{3} ?\\d{3}\\s*$"}] | P | held_out | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column is the supplier name on the contract; supplier is the contracted entity. Only mapped where a single supplier is listed (see when).
2. `entity.abn` ← `Supplier ABN`: Supplier ABN column; spaces removed and checksum validated. Multi-supplier cells are skipped by the transform.
3. `address.full` ← `Supplier address`: Supplier address for the supplier; only single-supplier rows; placeholder values without letters (e.g. '0') are skipped.

## Left unmapped (not guessed)

- `Agency (Dept or Stat Body)`: government buyer, not the supplier entity
- `Agency address`: address of the government buyer, not the supplier
- `_id`: blank in the source
- `Contract description/name`: contract description; no ontology field
- `Award contract date`: date of the contract event, not when the entity's status began
- `Contract value`: contract value; no ontology field
- `Variation to contract (Yes/No)`: contract attribute; no ontology field
- `Specific confidentiality provision used`: contract attribute
- `Procurement method`: contract attribute
- `Justification (if limited tender)`: contract attribute
- `Form of contract`: contract attribute
- `Number of offers sought`: contract attribute
- `Evaluation criteria and weightings`: contract attribute
- `Deliverables`: contract attribute
- `Contract milestones`: contract attribute
- `Contract performance management`: contract attribute
- `Contract reference number`: contract identifier, not unique enough to be record id
- `Contract category group`: contract category; no ontology field
- `Parent contract number/SOA`: contract identifier
- `Commence date`: contract date, not entity registration
- `Finish date`: contract date, not entity status

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name / entity.abn / address.full (multi-supplier rows)`: Cells listing several suppliers are deliberately not mapped: supplier and ABN lists use mixed separators (', ' and '; ') so positional alignment is unreliable. These rows (about 6%) yield no supplier observations. Advisory critique suggested split; not applied to avoid misaligned suppliers.

## Checks

- Duplicate record ids in held-out rows: {'rows': 210, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound: supplier name and ABN are mapped to the contracted supplier, agency fields are correctly excluded as government buyer, and contract dates are correctly left unmapped. One blocking issue: a placeholder "0" in the supplier address is emitted as a real address for the ADITS NQ row. Advisory points cover the lost multi-supplier rows and the unparsed state and postcode.
  - [blocking] `address.full<-Supplier address`: For the ADITS NQ PTY LTD row the Supplier address cell is the placeholder "0", and the mapping emits it as address.full = "0". The row's Supplier ABN is a single 11-digit ABN, so the `when` clause passes and the placeholder is mapped as a real address. The source does not support an address here. (suggested: Add a rule that rejects non-address placeholder values such as "0" (for example a regex requiring at least one letter, or a value exclusion list), or treat "0" as null, and re-check the rows where this column holds placeholders.)
  - [advisory] `entity.abn<-Supplier ABN`: The multi-supplier rows (for example the Cleanaway/Ace Waste row and the ALPENGLOW row) produce no entity observations at all. Rule 12 says aligned columns should be split on ';' within one group so items line up by position. The config instead skips these rows entirely, so their suppliers are lost. (suggested: Add split on ';' to Supplier name, Supplier ABN and Supplier address in a shared group, so each supplier is emitted as its own entity observation, with the `when` restriction removed or applied per item.)
  - [advisory] `address.state`: The Supplier address cells often contain a state (for example "Newcastle West, NSW, 2302" or "Chapel Hill QLD 4069"), but the config maps only address.full. The state and postcode are not parsed out, though they are present in the source text. (suggested: Consider a parse step that extracts the state and postcode from the Supplier address into address.state and address.postcode, with a note that this is L1 parsing and that the field_confidence should reflect it.)
- Critique: No blocking meaning errors found. The legal name, ABN and address mappings follow the stated rules for single-supplier rows, the contract dates and other contract attributes are correctly left unmapped, and the government agency is correctly excluded. The remaining points are completeness issues: multi-supplier cells are dropped rather than split in a group, the ABN guard is implicit, and the envelope metadata is not visible in the config.
  - [advisory] `entity.legal_name<-Supplier name`: Multi-supplier cells (for example the Cleanaway/Ace Waste and ALPENGLOW rows) produce no entity observations at all. Rule 12 asks for split on every aligned column in one group so that items line up by position. The config skips these rows instead, so the listed suppliers and their ABNs are lost even though the source holds them. (suggested: Add split (';') to Supplier name, Supplier ABN and Supplier address in one shared group, with the when condition applied per item, so each supplier in a multi-supplier cell is emitted. Alternatively, record in the config why these rows are deliberately excluded.)
  - [advisory] `entity.abn<-Supplier ABN`: The reason says the abn transform skips multi-supplier cells, but the transform is applied to the whole cell after spaces are stripped. The skip is therefore a property of the engine's behaviour, not something the config enforces. The config does not state this clearly, and no when condition guards this field the way it guards the name and address fields. (suggested: Add the same single-ABN when condition used on Supplier name to entity.abn<-Supplier ABN, so that the guard is explicit in the config rather than resting on transform behaviour.)
  - [advisory] `observation envelope`: The config does not show the envelope fields that are required by the ontology (licence, source_reliability, extractor_version, source_id). The sample output shows observed_at only. The licence in particular has no value in the config, and the source is a government contracts dataset whose licence is not stated here. (suggested: Confirm that licence is taken from the CKAN metadata (or recorded as 'unknown' and flagged), and that source_reliability and extractor_version are set and documented, with a basis for the reliability judgement.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name`: `THE UNITING CHURCH IN AUSTRALIA PROPERTY TRUST (Q.` → `THE UNITING CHURCH IN AUSTRALIA PROPERTY TRUST (Q.)`; `Ceccato Builders Pty Ltd` → `Ceccato Builders Pty Ltd`; `Becton Dickinson Pty Ltd` → `Becton Dickinson Pty Ltd`
- `entity.abn<-Supplier ABN`: `25 548 385 225` → `25548385225`; `94 132 990 400` → `94132990400`; `82 005 914 796` → `82005914796`
- `address.full<-Supplier address`: `Suite1, 4 Mylne Street, Toowoomba, QLD 4350` → `Suite1, 4 Mylne Street, Toowoomba, QLD 4350`; `168  Robertson Street, Fortitude Valley QLD 4006` → `168 Robertson Street, Fortitude Valley QLD 4006`; `23  Riverpark Drive, Nerang QLD 4211` → `23 Riverpark Drive, Nerang QLD 4211`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
