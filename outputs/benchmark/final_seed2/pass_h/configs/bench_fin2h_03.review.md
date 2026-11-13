# Review packet (round-2 agent): validated_config

**Dataset:** Queensland government arrangements directory—supplier procurement arrangements — Housing and Public Works  
**Licence:** Creative Commons Attribution 4.0  
**File:** `overnment-arrangements-directorysupplier-procurement-arrangements-14.10.2026.csv` (sha256 `a66a5359d35a…`)

## How this ended

- Outcome **validated_config**.
- 12 model turns, 12 tool calls, $0.0105, 57.04s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_03/trace.jsonl`.
- Evidence the agent gave at finish (its words): 269 rows x 23 columns, utf-8-sig CSV. Arrangement Number unique in the training rows. Validate on held-out rows: 0 hard failures, 34 legal-name observations from 134 rows. Critique: 0 blocking, 7 advisory (comma-separated supplier lists not captured, list-marker prefixes, truncated cells, non-company suppliers dropped, ABN not mapped, record_id uniqueness, Categories unmapped).

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `Arrangement Number` — 0 duplicate / blank keys of 269 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Arrangement Number | Arrangement Name | State | Categories | Subcategories | Product and Service Groups | Start Date | Expiry Date | Status | Contact Name | Contact Email | Contact Phone | Department | Section | Suppliers
2. QH122690 | Total Parenteral Nutrition | Published | Medical | Medical Equipment. & Supplies | ∅ | 01/04/2024 | 01/04/2027 | Active | Lucy Geijskes | MedicalConsumables-sps@health.qld.gov.au | 07 2100 9905 | Queensland Health | Medical Consumables Category Team | Fresenius Kabi Australia Pty Ltd, 
ABN: 
3. GGS0125-25 | Provision of Legal Services | Published | General Goods & Services | Legal Services | Legal Services | 01/10/2026 | 30/09/2030 | Active | Jill Petrie | Panel.Manager@justice.qld.gov.au | 07 3738 9841 | Department of Justice | Legal Services Coordination Unit | TBA
4. QH4872022 | Hand Hygiene, Surface Wipes and Pre-Op S | Published | Medical | Medical Equipment. & Supplies | ∅ | 01/11/2022 | 31/10/2027 | Active | Lucy Geijskes | MedicalConsumables-sps@health.qld.gov.au | 07 2100 9905 | Queensland Health | Medical Consumables Category Team | Anaeron Pty Ltd, 
EBOS Healthcare Ecolab
5. DET 65864 | Classroom Resources | Published | General Goods & Services | Music, Game, Toy, Art, Craft & Edu | Arts & Crafts Equipment & Accessories &  | 01/10/2017 | 31/12/2026 | Active | SOA Manager | procurement.ggs@qed.qld.gov.au | 1300 366 612 | Department of Education | Procurement and Facilities Services - Ge | Bedrock Books, 
Box of Books, 
Campion E
6. TMRICT(SOA)17023 | UImprove Consultation, Facilitation & Tr | Published | General Goods & Services | Training & Development | ∅ | 17/10/2017 | 16/10/2026 | Active | Wendy Li | ict.procurement@tmr.qld.gov.au | 0730666033 | Department of Transport and Main Roads | ∅ | UIC
7. TMRICTSOA25194 | Identity and Access Management (IDAM) | Published | Information and Communication Technology | IT & Telecomms | Services - Security Management | 28/09/2026 | 19/06/2031 | Active | ICT Contract Management  | ict_contract_management@tmr.qld.gov.au | 07 3066 8610 | Department of Transport and Main Roads | ICT Contract Management  | CyberCX Pty Ltd, 
Scyne Advisory Pty Ltd
8. ZZ-RP113795 | Relocation of Dental/BreastScreen Vans | Published | General Goods & Services | Transport, Freight, Logistics | Vehicle Towing Services | 03/07/2023 | 30/06/2027 | Active | SOA Procurement Officer - Medical Stream | sp-servicedelivery@health.qld.gov.au | 07 2100 9909 | Queensland Health | Customer & Procurement Services, Corpora | Clayton's Towing Services Pty Ltd, 
Harv
9. HSQ83528 | Maintenance of Pneumatic Tube and Teleli | Published | Building Construction and Maintenance | Mechanical Plant, Equip, Services | Pneumatic Machinery, Equipment, Parts &  | 09/04/2018 | 31/03/2027 | Active | Procurement Officer | SP-ServiceDelivery@health.qld.gov.au | 07 2100 9845 | Queensland Health | System Procurement - Service Delivery | Lamson Concepts Pty Ltd
10. TMRPR1481 | Pavement Investigation and Testing Servi | Published | General Goods & Services | Engineer, Research, Tech services | ∅ | 20/06/2024 | 30/06/2028 | Active | Philip Pearson | Philip.I.Pearson@tmr.qld.gov.au | 0730667694  | Department of Transport and Main Roads | Engineering and Technology | Pavement Investigations Panel, 
•	 Aussi
11. SOA372 (HSQ101690) | Intravenous (IV) & Large Volume Sterile  | Published | Medical | Drugs & Pharmaceutical Products | Drugs & Pharmaceutical Products | 01/04/2025 | 28/02/2027 | Active | Sam De Beer | pharmaceuticals-sps@health.qld.gov.au | 07 2100 9933 | Queensland Health | System Procurement | B.Braun Australia Pty Ltd (Expiry 28/02/
12. ICTSS.2109 | ICTSS.2109 – Workplace Health and Safety | Published | Information and Communication Technology | IT & Telecomms | ∅ | 25/10/2022 | 25/10/2027 | Active | ICT Category Management and Sourcing  | ICTCMS@chde.qld.gov.au | 07 3640 4863 | Department of Customer Services, Open Da | ICT Category Management and Sourcing  | Integrum Management Systems Pty Ltd

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Suppliers` | `entity.legal_name` | split(
) → regex_extract(^\s*([^,\n]+?(?:Pty Ltd|Pty\. Ltd\.?|Limited|Ltd))\s*,?\s*$) → clean_whitespace | P | held_out | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Suppliers`: Supplier cell lists supplier names; only newline-separated lines ending in a company legal suffix are taken, other lines (ABN, phone, address) are skipped. Partial coverage by design.

## Left unmapped (not guessed)

- `Arrangement Name`: names the arrangement (a category of goods/services), not a supplier entity
- `State`: holds publication status (Published), not a geographic state
- `Categories`: procurement category, not an industry code; recorded only as a procurement classification
- `Subcategories`: procurement subcategory
- `Product and Service Groups`: procurement product groups
- `Start Date`: arrangement start date, not the supplier's own registration date
- `Expiry Date`: arrangement expiry date, not the supplier's own status end
- `Status`: arrangement status, not supplier entity status
- `Contact Name`: government contact person
- `Contact Email`: government contact
- `Contact Phone`: government contact
- `Department`: government buyer
- `Section`: government buyer unit

## Needs a transform the engine does not have

- `Suppliers`: Supplier ABNs and addresses are present but not aligned by position to names; an aligned-split transform is needed. Comma-separated supplier lists are also not captured.

## Abstentions (fields removed, with reasons)

- `entity.abn<-Suppliers`: Supplier ABNs are not aligned to supplier names in the free-text cell; no aligned-split transform exists.
- `entity.legal_name<-Suppliers (comma-separated and non-company names)`: Coverage is deliberately limited to newline-separated company names with Pty Ltd/Limited/Ltd suffixes; other supplier names are not captured.

## Checks

- Duplicate record ids in held-out rows: {'rows': 269, 'key': ['Arrangement Number'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking meaning errors: the government buyer, arrangement status, dates and contacts are correctly excluded, and the one clear supplier observation (Abbott Australasia Pty Ltd, Microsoft Ireland Operations Ltd) is a supplier name in the right field. The main problems are coverage: comma-separated and truncated supplier cells yield nothing or partial names, the dash/bullet prefixes are not stripped, and supplier ABNs are unmapped. All are advisory.
  - [advisory] `entity.legal_name<-Suppliers`: The split is on newline, but the sample Suppliers cells separate suppliers with commas (e.g. 'Adsorb Pty Ltd, APT Project Solutions Pty Ltd, ...', '- Sonoray Pty Ltd, - Medilink Pty Ltd'). The regex excludes commas, so these multi-supplier cells produce no observations at all, and the mapping does not say so. (suggested: Confirm the real delimiter in the Suppliers column. If it is ', ' or a bullet/dash-separated list, split on that delimiter, or document that comma-separated cells are unmapped. Record the coverage gap explicitly.)
  - [advisory] `entity.legal_name<-Suppliers`: Dash and bullet prefixes ('- Sonoray Pty Ltd', '• Axis Health Pty Ltd') are not stripped. The capture group would keep the leading '- ' or '• ' if a line did match, so the legal name would carry list punctuation. (suggested: Add a regex_replace step that removes leading list markers (-, •) before regex_extract, using only removal, not addition.)
  - [advisory] `entity.legal_name<-Suppliers`: Cells are truncated with an ellipsis ('…'), e.g. 'Assa Abloy Entrance Systems Australia Pty L…' and 'Dalcr…'. The last supplier name is cut off, so a name ending in a suffix can be missed or partially captured. The stated 'partial coverage by design' does not cover this case. (suggested: Note that the source truncates the cell, and treat observations from truncated final items as incomplete or skip them.)
  - [advisory] `entity.legal_name<-Suppliers`: Suppliers without a company suffix are silently dropped, e.g. 'CS Energy' and 'AcademyGlobal, UQ Skills'. Some are probably real legal entities, and 'Limited' and 'Ltd' are the only suffixes covered. (suggested: Accept this as deliberate partial coverage, and list which legal forms are excluded (e.g. Pty. Ltd variants, Inc., trusts, universities) so the gap is visible.)
  - [advisory] `entity.abn`: The config has a needs_transform note saying per-supplier ABNs are not aligned by position, but no abn field is mapped and no aligned-split transform exists. The ABN information in the source is therefore not captured at all. (suggested: Keep this in needs_transform, and record that supplier ABNs are present in the source but unusable until an aligned-split transform is available.)
  - [advisory] `record_id`: Arrangement Number is used as the record key without a check_unique confirmation. Values like 'QH 152' and 'OIR 045_2223' contain spaces and inconsistent formats, so uniqueness is not established. (suggested: Run check_unique on Arrangement Number, and use hash_row=true if duplicates appear.)
  - [advisory] `industry_code`: Categories and Subcategories are listed as unmapped as procurement categories. This is defensible, but they are the only descriptive classification in the source, and the reason given does not explain why they cannot be recorded even as raw description. (suggested: Consider whether Categories should be recorded as a raw industry description, with a note that it is a procurement category and not ANZSIC, or keep it unmapped with that reason stated.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Suppliers`: `Assetnote Pty Ltd` → `Assetnote Pty Ltd`; `Abbott Australasia Pty Ltd` → `Abbott Australasia Pty Ltd`; `GH Varley Pty Limited` → `GH Varley Pty Limited`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
