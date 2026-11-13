# Review packet (round-2 agent): validated_config

**Dataset:** Tenders WA Contract Award Details 2023-24 Financial Year — Department of Treasury and Finance  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `tenders-wa-contract-award-details-2023-24-financial-year.csv` (sha256 `a6e9859f99ba…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0103, 46.08s (download and human waits excluded). Trace: `logs/agent_runs/wa_tenders_awards_2023_24/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded resource 0 (CSV, 5,817 rows, 43 columns). Supplier_Name and Supplier_Address are filled on 100% of rows. No ABN or ACN column exists, so no identifiers are mapped. Reference_Number+Supplier_Name is not unique, so record_id uses hash_row. Validate on held-out rows: 0 hard failures, 0 rejected values, parse rate 1.0 for both mapped fields.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
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
| 1 | `Supplier_Name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 2 | `Supplier_Address` | `address.full` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier_Name`: Column is the awarded supplier's name in a tender award register; it is the supplier's name as the source records it. Parenthetical text is left as published.
2. `address.full` ← `Supplier_Address`: Supplier address column, same row as Supplier_Name.

## Left unmapped (not guessed)

- `Public_Authority`: government buyer; not the supplier entity
- `Public_Authority_Address`: address of the government buyer, not the supplier
- `Title`: contract description
- `Reference_Number`: tender reference
- `Description`: contract description
- `Type_of_Work`: procurement type
- `Procurement_Method`: procurement process attribute
- `Associated_With_Tender`: related tender text
- `UNSPSC_Code_1`: contract goods/services code, not supplier ANZSIC
- `UNSPSC_Title_1`: contract classification
- `UNSPSC_Percent_1`: share of contract
- `UNSPSC_Code_2`: contract classification
- `UNSPSC_Title_2`: contract classification
- `UNSPSC_Percent_2`: share of contract
- `UNSPSC_Code_3`: contract classification
- `UNSPSC_Title_3`: contract classification
- `UNSPSC_Percent_3`: share of contract
- `Gascoyne`: delivery region flag
- `Goldfields_Esperance`: delivery region flag
- `Great_Southern`: delivery region flag
- `Kimberley`: delivery region flag
- `Mid_West`: delivery region flag
- `Peel`: delivery region flag
- `Perth_Metropolitan`: delivery region flag
- `Pilbara`: delivery region flag
- `South_West`: delivery region flag
- `Wheatbelt`: delivery region flag
- `State_Wide`: delivery region flag
- `Interstate`: delivery region flag
- `International`: delivery region flag
- `Number_of_Submissions`: tender statistic
- `Panel_Contract`: contract attribute
- `Contract_Term`: contract attribute
- `Closing_Date`: tender event date
- `Award_Date`: contract event date
- `Commencement_Date`: contract term date
- `Initial_Expiry_Date`: contract term date
- `Final_Expiry_Date`: contract term date
- `Original_Contract_Value`: contract value
- `Original_Contract_Value_Type`: contract value type
- `CUA_Number`: common use arrangement reference

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 5817, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The core mapping is sound: Supplier_Name is the awarded supplier, Supplier_Address is the supplier's address, government buyer columns are correctly left unmapped, and entity_type is correctly not mapped. I found no blocking meaning errors in the examples. The advisory points concern the parenthetical and trustee forms in legal names, abbreviations, and a duplicated locality in addresses, which should be recorded as caveats.
  - [advisory] `entity.legal_name<-Supplier_Name`: Several Supplier_Name values pair a trading-style name with a parenthetical registered-style name, e.g. 'Programmed Property Services (Programmed Property Services Pty Ltd)', 'My Home Care (MyHomecare Pty Ltd)' and 'Talent International (Talent International Pty Ltd)'. The whole string is mapped to legal_name, so the outer name is presented as the registered name. The source does not say which part is registered. (suggested: Keep the mapping (the column is the awarded supplier's name, which rule 5 allows), but record a caveat that the value may combine a trading name and a registered name. If the split is needed later, add a transform that splits the parenthetical, or map the outer part to trading_name at 0.6 or lower after such a transform exists (needs_transform).)
  - [advisory] `entity.legal_name<-Supplier_Name`: Some values are abbreviated or carry a trustee designation rather than a plain registered name, e.g. 'Progenesis Holdings P/L' and 'DFP Recruitment Services (DFP Recruitment Services Pty Ltd ATF The DFP Business Trust)'. 'ATF' means the company acts as trustee, so the trust is not the supplier itself. (suggested: Keep the mapping as published, since the source does not give a registered form. Add a note that 'P/L' is an abbreviation and that 'ATF' indicates a trustee capacity, and do not infer entity_type from these strings.)
  - [advisory] `address.full<-Supplier_Address`: The raw value 'Level 5, 25 Walters Drive, Osborne Park, OSBORNE PARK, 6017' repeats the locality, and clean_whitespace does not address this. The mapping keeps the duplication as published. (suggested: This is acceptable under the rule against cleaning beyond the transforms. Note the duplicated locality as a known quirk. Do not remove it unless a transform for that exists.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier_Name`: `Programmed Property Services (Programmed Property ` → `Programmed Property Services (Programmed Property Services P`; `LECO Australia Pty Ltd` → `LECO Australia Pty Ltd`; `TechnologyOne (Technology One Limited)` → `TechnologyOne (Technology One Limited)`
- `address.full<-Supplier_Address`: `168 Abernethy Road, Belmont, 6104` → `168 Abernethy Road, Belmont, 6104`; `4/10 Salisbury Rd, Castle Hill, 2154` → `4/10 Salisbury Rd, Castle Hill, 2154`; `Ground Floor, 999 Hay St, Perth, 6000` → `Ground Floor, 999 Hay St, Perth, 6000`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
