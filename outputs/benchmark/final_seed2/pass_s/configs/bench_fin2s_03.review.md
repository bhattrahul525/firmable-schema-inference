# Review packet (round-2 agent): validated_config

**Dataset:** Queensland government arrangements directory—supplier procurement arrangements — Housing and Public Works  
**Licence:** Creative Commons Attribution 4.0  
**File:** `overnment-arrangements-directorysupplier-procurement-arrangements-14.10.2026.csv` (sha256 `a66a5359d35a…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1494, 45.39s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_03/trace.jsonl`.

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
| 1 | `Suppliers` | `entity.abn` | regex_extract(ABN:?\s*(\d{11})\b) → abn | P | held_out | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `Suppliers`: ABN stated in supplier cell; only the first unspaced ABN is extracted

## Left unmapped (not guessed)

- `Start Date`: arrangement date
- `Expiry Date`: arrangement date
- `Arrangement Name`: arrangement not entity
- `State`: publication state
- `Categories`: arrangement category
- `Subcategories`: arrangement category
- `Product and Service Groups`: arrangement category
- `Status`: arrangement status
- `Contact Name`: government contact
- `Contact Email`: government contact
- `Contact Phone`: government contact
- `Department`: government buyer
- `Section`: government buyer

## Needs a transform the engine does not have

- `Suppliers`: names and multiple suppliers in one free-text cell cannot be split

## Checks

- Duplicate record ids in held-out rows: {'rows': 269, 'key': ['Arrangement Number'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The supplier-as-entity choice and the unmapped buyer columns are correct. However, the Suppliers column is not split in the output, so whole lists and contact text are emitted as a single legal_name. That is a blocking problem, and the mapping needs a working split plus cleanup.
  - [blocking] `entity.legal_name<-Suppliers`: The split transform (arg ",\n") does not separate suppliers in the produced observations. Each row yields one legal_name holding the whole multi-supplier list, e.g. "Arcomed Pty Ltd, B. Braun Australia Pty Ltd, Baxter Healthcare...". The source does not say that a list of many suppliers is one registered name, so the mapping states something the source does not support. (suggested: Use a split on the actual delimiter, such as ",\n" or ", ," or plain "," where cells have no commas inside names. Add a regex_replace to drop "Current Suppliers:" and the "Additional Suppliers will be onboarded..." boilerplate. Otherwise move Suppliers to needs_transform.)
  - [blocking] `entity.legal_name<-Suppliers`: The produced legal_name values contain non-name text: embedded "ABN: ...", phone, email and address fragments (the QH122519 row), "Current Suppliers:" and the onboarding boilerplate, and "- ABN 46003855561" suffixes. This is not a registered name, and valid ABNs that the source states go unmapped. (suggested: Strip the ABN, phone, email and address text with regex_replace. Map the ABNs to entity.abn with the abn transform, in the same split group. Otherwise list the column in needs_transform.)
  - [advisory] `entity.legal_name<-Suppliers`: Suppliers are named in a procurement arrangement, but the cell does not label them as registered names. Many values include trading names, "t/a", "formerly" and bracketed names such as "(Alpha First Aid)", so the legal-name claim is only partly right. No mapping_confidence is visible in the config. (suggested: Set mapping_confidence at about 0.7 or lower. Where a transform can separate "t/a X" or "trading as X" into entity.trading_name, do so.)
  - [advisory] `entity.abn`: Many Suppliers cells state 11-digit ABNs (e.g. "ABN: 32 939 127 868", "ABN 46003855561"), but no abn field is mapped. (suggested: Once the cell is split correctly, add an entity.abn mapping with the abn transform in the same group.)
- Critique: No blocking problems. The mapping states only ABNs that the source shows, and it correctly leaves the government buyer, contact and arrangement columns unmapped. The main weaknesses are incomplete coverage of multi-supplier cells and the lack of any supplier name field.
  - [advisory] `entity.abn<-Suppliers`: Suppliers cells hold several suppliers, but only the first ABN is extracted. In the Aurion row, Microsoft Ireland Operations Ltd and the other suppliers are dropped, so the claim covers only one supplier of the arrangement. Rows with no ABN pattern or with a spaced ABN (e.g. 'ABN: 32 939 127 868') produce no observation. (suggested: Record the first-ABN-only limitation as a caveat. Ideally add a split or a spaced-ABN extraction so every supplier ABN is captured.)
  - [advisory] `entity.abn<-Suppliers`: Supplier names (legal names) are in needs_transform, so no legal_name is emitted. Single-supplier rows such as 'OutSystems Software Pty Ltd' and 'Origin Energy Electricity Limited' are plain names that could have been mapped. The Suppliers column is the supplier field in contract data. (suggested: Keep the column in needs_transform for the multi-supplier cells. Optionally note that single-name rows could be mapped to legal_name at moderate confidence.)
  - [advisory] `entity.abn<-Suppliers`: The ABN is attributed to the whole cell. For Aurion the ABN belongs to the first supplier only, and the observation carries no name, so downstream it could be read as the ABN of the arrangement's other suppliers. (suggested: Note in the reason that the ABN applies only to the supplier it follows in the cell.)

## Examples (raw → value, held-out rows)

- `entity.abn<-Suppliers`: `Data#3 - ABN 31010545267, 
Digital Sense Hosting P` → `31010545267`; `Ciena Communications Inc - ABN 11934388437, 
D-Lin` → `11934388437`; `Name: Abbott, 
ABN: 95000180389, 
Phone: 1800 839 ` → `95000180389`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
