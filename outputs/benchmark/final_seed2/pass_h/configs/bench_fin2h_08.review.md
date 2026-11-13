# Review packet (round-2 agent): validated_config

**Dataset:** ICT Contract Usage Guidelines — Department of the Premier and Cabinet  
**Licence:** Creative Commons Attribution  
**File:** `qictstrategicsourcingcmgpublicdatasetssagovtictcontracts08012015.csv` (sha256 `b81874ea6aa9…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0083, 46.86s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_08/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "cp1252", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Segment | Guideline | Contract | CDContractSummary | Commencement Date | OriginalExpiryDate | Completion Date | ExtnComments | Contract Value
2. ESRI Geographic Information Systems | Agencies wishing to subscribe need to ne | Software Suppliers | ∅ | 1/07/2013 | 30/06/2016 | 30/06/2016 | ∅ | 3000000
3. Distributed Computing Support Services ( | Server Management Support Services (SMSS | CSC | CSC Australia Pty Limited Distributed Co | 1/07/2014 | 30/06/2017 | 30/06/2017 | ∅ | ∅
4. Active Devices | All Active Devices MUST be purchased und | Hewlett-Packard | Hewlett Packard Australia PTY LTD Active | 1/11/2010 | 31/07/2012 | 31/07/2015 | State may extend with no less than 3 mon | 766890
5. Active Devices | All Active Devices MUST be purchased und | Alphawest | Alphawest Services Pty Ltd Active Device | 1/11/2010 | 31/07/2012 | 31/07/2015 | State may extend with no less than 3 mon | 700000
6. Software License Agreements |  Agencies seeking to buy software under  | Software Suppliers | Compuware Master License Agreement for A | 10/10/2008 | ∅ | ∅ | This is a MSLA and does not have a term, | 0
7. Software License Agreements |  Agencies seeking to buy software under  | Software Suppliers | SAP Master Licence Agreement | 30/09/2010 | ∅ | ∅ | Perpertual agreement  -30 days written n | 0
8. Active Devices | All Active Devices MUST be purchased und | NEC | NEC Australia PTY LTD Purchasing Agreeme | 1/11/2010 | 31/07/2012 | 31/07/2015 | State may extend term with no less than  | 2000000
9. Active Devices | All Active Devices MUST be purchased und | Data#3 | Data#3 Limited Operational Head Agreemen | 1/11/2010 | 31/07/2012 | 31/07/2015 | State may extend term with no less than  | 1040000
10. Active Devices | All Active Devices MUST be purchased und | Dimension Data | Dimension Data Australia Pty Ltd Active  | 1/11/2010 | 31/07/2012 | 31/07/2015 | State may extend with no less than 3 mon | 11000000
11. PABX Equipment & Services | Agencies that own and/or operate their o | NEC | NEC PABX Services and Equipment Purchasi | 20/02/2011 | 19/11/2012 | 19/11/2015 | Initial term is for 1 year and nine mont | 27760000
12. Software License Agreements |  Agencies seeking to buy software under  | Software Suppliers | CA Technology Pty Ltd CAM Management Sol | 23/03/2011 | ∅ | ∅ | Perpetual MLA | 0

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Contract` | `entity.trading_name` | clean_whitespace [when {"column": "Contract", "matches": "^(?!.*(Software Suppliers|Panel|Deed|Agreement|Arrangement|Suppliers)).+"}] | P | held_out | 0.50 | 100.0% | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Contract`: Short supplier name in the Contract column; not stated as the registered name, so mapped as trading_name at low confidence. Generic category and panel/deed/arrangement labels are excluded.

## Left unmapped (not guessed)

- `Segment`: ICT segment category, not an entity attribute
- `Guideline`: Guideline text about purchasing rules
- `CDContractSummary`: Contract title text mixing supplier name with product description; not cleanly a registered name
- `Commencement Date`: Date of the contract arrangement, not when the entity's registration or status began
- `OriginalExpiryDate`: Contract term date, not entity status
- `Completion Date`: Contract term date, not entity status
- `ExtnComments`: Free-text contract extension comments
- `Contract Value`: Contract financial value, not an entity attribute

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 77, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The Contract-to-trading_name mapping is mostly sound. Every column is accounted for, and the date and value columns are correctly excluded. One blocking problem: the eProjects Panel row maps a panel or deed name as a supplier trading name, which the source does not support. Two advisory points concern the Software Suppliers exclusion and the unmapped CDContractSummary legal-name candidate.
  - [blocking] `entity.trading_name<-Contract`: In the eProjects row, the Contract column holds 'eProjects Panel', which the CDContractSummary ('eProjects Panel Deed of Agreement Version 1') and the Guideline show is a panel or deed arrangement, not a supplier. The mapping states that 'eProjects Panel' is a trading name of the entity the row is about (the supplier), which the source does not support. (suggested: Exclude panel, deed and arrangement names from the Contract mapping, for example with a when-regex that also excludes values containing 'Panel', or leave the row unmapped for this field.)
  - [advisory] `entity.trading_name<-Contract`: Excluding only the literal 'Software Suppliers' drops supplier identity for the Adobe and Attachmate rows, where the supplier appears only in CDContractSummary. The mapping does not recover it. (suggested: Consider a richer rule for generic Contract values, or record the supplier name from CDContractSummary as a low-confidence trading name only where the leading organisation name is clear.)
  - [advisory] `entity.legal_name<-CDContractSummary`: CDContractSummary often begins with a full company name ending in 'Pty Ltd' (e.g. 'Hewlett-Packard Australia Pty Ltd'), which may be the registered name. The config leaves it unmapped, and the source does not label it as registered, so this is a judgement call rather than an error. (suggested: Keep it unmapped unless the dataset documents that the leading name is the registered supplier name. If it is later parsed, extract only the leading company name and map it at low confidence.)
- Critique: No blocking meaning errors found. The Contract column is a supplier name in every row that produces an observation, and the mapping is correctly kept low-confidence as trading_name. The remaining points are advisory: the exclusion regex is broad, and a legal name candidate exists in CDContractSummary but is unmapped. The entity_type unknown observations and the unmapped date and value columns are consistent with the rules.
  - [advisory] `entity.trading_name<-Contract`: The Contract column holds short supplier names such as Hewlett-Packard, Dell, Microsoft, AAPT and Nextgen Networks, which the source does not label as registered names. Mapping them to trading_name at low confidence follows rule 5, so this is not blocking. The exclusion regex is broad, though: it drops any row whose Contract value contains 'Agreement', 'Panel', 'Deed', 'Arrangement' or 'Suppliers', which would also drop a genuine supplier name containing one of those words. (suggested: Keep trading_name at 0.6 or lower. Consider anchoring the exclusion on the generic labels only (for example exact matches for 'Software Suppliers' and 'eProjects Panel') so that real supplier names are not silently skipped.)
  - [advisory] `entity.legal_name`: The CDContractSummary column often begins with a full corporate name such as 'Hewlett-Packard Australia Pty Ltd', 'Dell Australia Pty Ltd' and 'Nextgen Networks Pty Limited', which looks like a registered supplier name. It is unmapped because the source does not label it as the registered name, which is a defensible choice under rule 2. The 'Pty Ltd' suffix does show the name is a company name, so a candidate legal_name could be recorded later at low confidence. (suggested: Leave CDContractSummary unmapped for now, or record a low-confidence legal_name candidate only after a deterministic extraction of the leading company name before the product description. Document the extraction rule if you do this.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Contract`: `Hewlett-Packard` → `Hewlett-Packard`; `Internode` → `Internode`; `Data#3` → `Data#3`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
