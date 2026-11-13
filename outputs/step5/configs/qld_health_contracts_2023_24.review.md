# Review packet (round-2 agent): validated_config

**Dataset:** System Procurement_Contract Disclosure Report — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `sp_contract-disclosure-report-2023-24.csv` (sha256 `5fc64ed16718…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0146, 77.14s (download and human waits excluded). Trace: `logs/agent_runs/qld_health_contracts_2023_24/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate call 2: 0 hard failures, 210 rows, 327 observations on held-out rows, legal_name and address parse 100%, ABN parse 98.96%. Critique: 0 blocking issues remaining.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "cp1252", "skip_rows": 0, "header_rows": 1}`
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
| 1 | `Supplier name` | `entity.legal_name` | split(;) → clean_whitespace [when {"column": "Supplier ABN", "matches": "^\\s*\\d{2}\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}\\s*$"}] | P | held_out | 0.70 | 100.0% | **0.70** |
| 2 | `Supplier ABN` | `entity.abn` | abn [when {"column": "Supplier ABN", "matches": "^\\s*\\d{2}\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}\\s*$"}] | P | held_out | 0.90 | 99.0% | **0.90** |
| 3 | `Supplier address` | `address.full` | regex_extract(^(.*[A-Za-z].*)$) → clean_whitespace [when {"column": "Supplier ABN", "matches": "^\\s*\\d{2}\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}\\s*$"}] | P | held_out | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column is named Supplier name on a government contract disclosure; the supplier is the contracted entity. Only mapped on rows with a single supplier ABN so names and ABNs stay aligned.
2. `entity.abn` ← `Supplier ABN`: Supplier ABN column; checksum validated. Only single-ABN rows so it aligns with the supplier name.
3. `address.full` ← `Supplier address`: Supplier address column; only on single-ABN rows so it belongs to the same supplier. Placeholder values without letters (e.g. '0') are dropped.

## Left unmapped (not guessed)

- `_id`: empty column
- `Agency (Dept or Stat Body)`: government buyer, not the supplier
- `Agency address`: government buyer address
- `Contract description/name`: contract description, no entity field
- `Award contract date`: date of a transaction, not when the entity's registration started
- `Contract value`: contract value, no ontology field
- `Variation to contract (Yes/No)`: contract attribute
- `Specific confidentiality provision used`: contract attribute
- `Procurement method`: contract attribute
- `Justification (if limited tender)`: contract attribute
- `Form of contract`: contract attribute
- `Number of offers sought`: contract attribute
- `Evaluation criteria and weightings`: contract attribute
- `Deliverables`: contract attribute
- `Contract milestones`: contract attribute
- `Contract performance management`: contract attribute
- `Contract reference number`: contract identifier, not an entity identifier
- `Contract category group`: contract attribute
- `Parent contract number/SOA`: contract identifier
- `Commence date`: contract start date, a transaction date not entity status
- `Finish date`: contract end date, a transaction date not entity status

## Needs a transform the engine does not have

- `Supplier ABN`: Multi-supplier rows (several ';'-separated names and ABNs) are excluded; aligned split of name, ABN and address needs a grouped split the config cannot yet guarantee because comma-separated names also occur.

## Checks

- Duplicate record ids in held-out rows: {'rows': 210, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the single-ABN when-clause correctly excludes multi-supplier cells, agency and contract columns are correctly left unmapped, and entity_type stays unknown. The main defect is the placeholder "0" in Supplier address being emitted as a real address (blocking). The remaining points are advisory caveats on name type and address parsing.
  - [blocking] `address.full<-Supplier address`: On the ADITS NQ PTY LTD row the Supplier address is the placeholder value "0", which the engine emitted as address.full = "0". The source does not state an address, so this claims an address the source does not support. The Supplier ABN on that row is single and unspaced, so the when-clause matches and the placeholder passes through. (suggested: Add a transform or when-condition that drops placeholder values such as "0" (or any value without letters) before mapping to address.full. Do not map a bare "0" as an address.)
  - [advisory] `entity.legal_name<-Supplier name`: Names such as "Core Connect" and "MAX STOCK'S" read like trading names rather than registered names. The supplier column supports legal_name as the contracted supplier, but the names may not be the registered entity names. (suggested: Keep legal_name for the supplier column, but set mapping_confidence at or below 0.8 for these rows, or cross-check the ABN against a registry before treating the name as registered.)
  - [advisory] `address.full<-Supplier address`: Supplier addresses such as "Level 13, 2 Park Street Sydney, NSW 2000" contain a state and postcode that could be parsed into address.state and address.postcode. Only the full string is mapped. (suggested: Optionally parse state and postcode from the address with a deterministic regex transform, and map them to address.state and address.postcode.)
- Critique: No blocking meaning errors found in the shown examples: supplier name, ABN and address are mapped from the supplier columns, the government buyer and contract attributes are correctly unmapped, and placeholder addresses such as '0' are dropped. The remaining issues are advisory: the split on supplier names is inert because of the single-ABN condition, and multi-supplier rows produce no observations at all.
  - [advisory] `entity.legal_name<-Supplier name`: The split on ';' is never exercised because the when-condition only admits rows with a single Supplier ABN, and multi-supplier rows (e.g. the Cleanaway and ALPENGLOW rows) are dropped entirely. The split transform is therefore inert in this config. (suggested: Keep the when-condition only if the multi-supplier rows are deliberately excluded and documented. Otherwise, split Supplier name, Supplier ABN (abn transform) and Supplier address on ';' in one group so the items line up by position, per rule 12.)
  - [advisory] `entity.abn<-Supplier ABN`: Multi-ABN rows yield zero observations, so every supplier in those rows is lost, not only the ones the when-condition excludes. The config records the reason but gives no path to recover the suppliers. (suggested: Add a split-based mapping for multi-ABN rows in the same group as the names and addresses, or record these rows as needing a transform so the gap is visible downstream.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name`: `THE UNITING CHURCH IN AUSTRALIA PROPERTY TRUST (Q.` → `THE UNITING CHURCH IN AUSTRALIA PROPERTY TRUST (Q.)`; `Ceccato Builders Pty Ltd` → `Ceccato Builders Pty Ltd`; `Becton Dickinson Pty Ltd` → `Becton Dickinson Pty Ltd`
- `entity.abn<-Supplier ABN`: `25 548 385 225` → `25548385225`; `94 132 990 400` → `94132990400`; `82 005 914 796` → `82005914796`
- `address.full<-Supplier address`: `Suite1, 4 Mylne Street, Toowoomba, QLD 4350` → `Suite1, 4 Mylne Street, Toowoomba, QLD 4350`; `168  Robertson Street, Fortitude Valley QLD 4006` → `168 Robertson Street, Fortitude Valley QLD 4006`; `23  Riverpark Drive, Nerang QLD 4211` → `23 Riverpark Drive, Nerang QLD 4211`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
