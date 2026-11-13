# Review packet (round-2 agent): validated_config

**Dataset:** Tenders WA Contract Award Details 2023-24 Financial Year — Department of Treasury and Finance  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `tenders-wa-contract-award-details-2023-24-financial-year.csv` (sha256 `a6e9859f99ba…`)

## How this ended

- Outcome **validated_config**.
- 16 model turns, 16 tool calls, $0.0186, 81.55s (download and human waits excluded). Trace: `logs/agent_runs/wa_tenders_awards_2023_24/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `Reference_Number, Supplier_Name, Public_Authority, Award_Date, Title` — 0 duplicate / blank keys of 5817 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Public_Authority | Public_Authority_Address | Title | Reference_Number | Description | Type_of_Work | Procurement_Method | Associated_With_Tender | UNSPSC_Code_1 | UNSPSC_Title_1 | UNSPSC_Percent_1 | UNSPSC_Code_2 | UNSPSC_Title_2 | UNSPSC_Percent_2 | UNSPSC_Code_3
2. Art Gallery of Western Australia | AGWA Administration, 47 James Street, Pe | Offsite storage services for part of the | 2022E2AGWA | The Art Gallery of WA requires the provi | Goods & Services | Direct Sourcing | ∅ | 78131800 | Specialized warehousing and storage | 100 | ∅ | ∅ | ∅ | ∅
3. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Internal Audit Services | CUAAFA201815062023AC | Provision of Internal Audit Services, in | Goods & Services | CUA | ∅ | 84111603 | Internal audits | 100 | ∅ | ∅ | ∅ | ∅
4. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Electricity Services | CUAELC201213102023AC | Provision of electricity services to thr | Goods & Services | CUA | ∅ | 83101800 | Electric utilities | 100 | ∅ | ∅ | ∅ | ∅
5. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Technical Support for Automated Fly Syst | E11102023ACT | The Arts and Culture Trust was seeking a | Goods & Services | Direct Sourcing | ∅ | 72150000 | Specialized trade construction and maint | 100 | ∅ | ∅ | ∅ | ∅
6. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Design and Project Management of House L | E19022024MYR0601ACT | The Arts and Culture Trust (ACT) is seek | Goods & Services | Direct Sourcing | Design and Project Management of House L | 81101508 | Architectural engineering | 80 | 80101600 | Project management | 20 | ∅
7. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Supply of Bronze Box Lighting at State T | E28032024ACT | The Arts and Culture Trust (ACT) was see | Goods & Services | Direct Sourcing | ∅ | 39111500 | Interior lighting fixtures and accessori | 100 | ∅ | ∅ | ∅ | ∅
8. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Supply and Installation of Step Lights ( | E28032024ACTGAC | The Arts and Culture Trust (ACT) was see | Goods & Services | Direct Sourcing | ∅ | 39111500 | Interior lighting fixtures and accessori | 60 | 72151500 | Electrical system services | 40 | ∅
9. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Provision of Property Management Service | R21032023ACT | The Arts and Culture Trust is seeking a  | Goods & Services | Open Advertisement | Provision of Property Management Service | 80130000 | Real estate services | 100 | ∅ | ∅ | ∅ | ∅
10. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Christmas Lights Trail 2023 | RFQ01112023ACTPCC | To engage a supplier on a rental agreeme | Goods & Services | Direct Sourcing | ∅ | 39111910 | Festive or christmas tree lighting | 100 | ∅ | ∅ | ∅ | ∅
11. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Gardening Services for PCC | RFQ08012024ACTPCC | Gardening services to maintain and impro | Goods & Services | Direct Sourcing | ∅ | 72102905 | Exterior grounds maintenance | 100 | ∅ | ∅ | ∅ | ∅
12. Arts and Culture Trust | 825 Hay Street, Perth, 6000 | Design of Switchboard | RFQ09052024ACTSACHMT | The Arts and Culture Trust (ACT) is seek | Goods & Services | Direct Sourcing | ∅ | 80100000 | Management advisory services | 100 | ∅ | ∅ | ∅ | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier_Name` | `entity.legal_name` | clean_whitespace [when {"column": "Supplier_Name", "matches": "^[^(]*$"}] | P | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `Supplier_Address` | `address.full` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier_Name`: Supplier_Name without a parenthesised part is the contracted supplier's name as the agency entered it.
2. `address.full` ← `Supplier_Address`: Supplier_Address is the supplier's address (Supplier_ prefix), not the buyer's address.

## Left unmapped (not guessed)

- `Public_Authority`: government buyer; the entity is the supplier
- `Public_Authority_Address`: address of the government buyer, not the entity
- `Title`: contract title, not an entity attribute
- `Description`: contract description
- `Type_of_Work`: procurement category of the contract
- `Procurement_Method`: procurement method of the contract
- `Associated_With_Tender`: tender cross-reference
- `UNSPSC_Code_1`: product classification of the contract, not an entity industry code
- `UNSPSC_Title_1`: product classification of the contract
- `UNSPSC_Percent_1`: contract classification share
- `UNSPSC_Code_2`: contract classification
- `UNSPSC_Title_2`: contract classification
- `UNSPSC_Percent_2`: contract classification share
- `UNSPSC_Code_3`: contract classification
- `UNSPSC_Title_3`: contract classification
- `UNSPSC_Percent_3`: contract classification share
- `Gascoyne`: contract region flag
- `Goldfields_Esperance`: contract region flag
- `Great_Southern`: contract region flag
- `Kimberley`: contract region flag
- `Mid_West`: contract region flag
- `Peel`: contract region flag
- `Perth_Metropolitan`: contract region flag
- `Pilbara`: contract region flag
- `South_West`: contract region flag
- `Wheatbelt`: contract region flag
- `State_Wide`: contract region flag
- `Interstate`: contract region flag
- `International`: contract region flag
- `Number_of_Submissions`: tender statistic
- `Panel_Contract`: contract flag
- `Contract_Term`: contract term
- `Closing_Date`: tender event date, not an entity status date
- `Award_Date`: contract award event date; not when the supplier's registration or status began
- `Commencement_Date`: contract date, not entity validity
- `Initial_Expiry_Date`: contract date
- `Final_Expiry_Date`: contract date
- `Original_Contract_Value`: contract value, not an entity attribute
- `Original_Contract_Value_Type`: contract value type
- `CUA_Number`: common use arrangement reference

## Needs a transform the engine does not have

- `Supplier_Name`: For cells of form 'Outer name (Registered name)' the parenthesised part should be legal_name and the outer part trading_name; the engine has no conditional split-by-pattern extraction into two canonical fields yet. Parenthesised rows currently get no legal_name.

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-Supplier_Name (parenthesised rows)`: Cells of the form 'Outer name (Registered name)' cannot be split into legal_name and trading_name by the current transforms without mapping two canonical fields from one column; left unmapped and listed in needs_transform.

## Checks

- Duplicate record ids in held-out rows: {'rows': 5817, 'key': ['Reference_Number', 'Supplier_Name', 'Public_Authority', 'Award_Date', 'Title'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The address and buyer-exclusion mappings are sound, and Supplier_Name is a legitimate supplier-name source for legal_name. The main problem is that the parenthesised Supplier_Name cells are mapped whole to legal_name, which mixes a trading-style name into the registered name. This should be split or left unmapped until a split transform exists. The remaining issues are advisory.
  - [blocking] `entity.legal_name<-Supplier_Name`: Supplier_Name cells often hold two names: an outer name and a parenthesised registered name, e.g. 'My Home Care (MyHomecare Pty Ltd)', 'Programmed Property Services (Programmed Property Services Pty Ltd)' and 'DFP Recruitment Services (DFP Recruitment Services Pty Ltd ATF The DFP Business Trust)'. The whole cell is mapped as legal_name, which claims the outer trading-style name is part of the registered name. The source does not support that. The outer name belongs in entity.trading_name at most, and the registered name is only the parenthesised part. (suggested: Split the cell on the parentheses: map the parenthesised registered name to entity.legal_name and the outer name to entity.trading_name, or add a split/extract transform if one exists. If no such transform exists, list the column under needs_transform rather than mapping the whole string as legal_name. Keep mapping_confidence at or below 0.7 until this is done.)
  - [advisory] `address.full<-Supplier_Address`: One row reads 'Level 5, 25 Walters Drive, Osborne Park, OSBORNE PARK, 6017', with the locality repeated. Clean_whitespace does not remove this duplication, so the address is kept as the source has it. (suggested: Leave as is, since rule 1 forbids cleaning beyond the transforms. Optionally note the duplicated locality as a data-quality caveat.)
  - [advisory] `record_id`: Reference_Number is not unique across agencies in general, and the record_id list names five columns without showing that the combination is checked as unique. Several rows share generic values, so the key may not reliably trace back to the exact raw row. (suggested: Confirm with check_unique that the combined key is unique across the file, or fall back to hash_row=true.)
  - [advisory] `observation.licence / observation.source_id`: The config does not show the envelope fields source_id or licence. These are required on every observation. (suggested: Add source_id as a stable dataset identifier and take the licence from the CKAN metadata, recording 'unknown' with a flag if none is given.)
- Critique: No blocking meaning errors found in the examples: Supplier_Name is the contracted supplier's name, Supplier_Address is the supplier's address rather than the buyer's, and the government buyer columns are correctly left unmapped. The main weakness is that parenthesised supplier rows lose both their registered and trading names, which is a coverage gap already flagged in needs_transform. The remaining points are advisory: a column listed as both mapped and unmapped, an unverified record_id key, and missing per-field mapping_confidence.
  - [advisory] `entity.legal_name<-Supplier_Name`: The when-clause restricts legal_name to rows without parentheses, so every parenthesised supplier row (e.g. 'Programmed Property Services (Programmed Property Services Pty Ltd)', 'My Home Care (MyHomecare Pty Ltd)') gets no legal_name observation at all. The registered name in the brackets is lost, and the outer name is not kept as trading_name either. This is a coverage gap rather than a wrong claim, and the needs_transform entry already records it. (suggested: Until a conditional split exists, consider a provisional trading_name mapping of the outer part at confidence 0.6 or lower, and track the parenthesised registered name as a pending needs_transform item.)
  - [advisory] `entity.legal_name<-Supplier_Name`: Supplier_Name appears both as a mapped source (entity.legal_name<-Supplier_Name) and in the unmapped list with the reason that parenthesised rows are not mapped. The column is therefore accounted for twice in contradictory ways. (suggested: Remove Supplier_Name from unmapped and describe the partial coverage in the field's reason or in needs_transform.)
  - [advisory] `record_id`: record_id is a composite of five columns, including Title and Public_Authority, with no check_unique evidence shown. Reference_Number looks like the natural key, but the config does not show it is unique on its own. (suggested: Confirm uniqueness of Reference_Number with check_unique; if it holds, use it alone, otherwise state the composite key's uniqueness check.)
  - [advisory] `entity.trading_name`: The config has no trading_name mapping, although the parenthesised cells (e.g. 'West to West Indigenous', 'Talent International', 'Datacom Systems') hold a trading-style outer name in the Supplier_Name column that the rules allow to map to trading_name at 0.6 or lower. (suggested: Consider mapping the outer part of parenthesised Supplier_Name cells to entity.trading_name at confidence 0.6 or lower, using split/regex on the same column.)
  - [advisory] `entity.legal_name<-Supplier_Name mapping_confidence`: No mapping_confidence is shown for the legal_name or address.full fields. Rule 14 requires one per mapped field, and the review cannot check whether 0.9 or above is justified. (suggested: State mapping_confidence per field: legal_name from 'Supplier_Name' (supplier name, non-parenthesised rows) and address.full from 'Supplier_Address' (supplier-prefixed column).)

## Examples (raw → value, held-out rows)

- `address.full<-Supplier_Address`: `168 Abernethy Road, Belmont, 6104` → `168 Abernethy Road, Belmont, 6104`; `4/10 Salisbury Rd, Castle Hill, 2154` → `4/10 Salisbury Rd, Castle Hill, 2154`; `Ground Floor, 999 Hay St, Perth, 6000` → `Ground Floor, 999 Hay St, Perth, 6000`
- `entity.legal_name<-Supplier_Name`: `LECO Australia Pty Ltd` → `LECO Australia Pty Ltd`; `OCS Services Pty Ltd` → `OCS Services Pty Ltd`; `Environdata Weather Stations Pty Ltd` → `Environdata Weather Stations Pty Ltd`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
