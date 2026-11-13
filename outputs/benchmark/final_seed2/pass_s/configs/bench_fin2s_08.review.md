# Review packet (round-2 agent): validated_config

**Dataset:** ICT Contract Usage Guidelines — Department of the Premier and Cabinet  
**Licence:** Creative Commons Attribution  
**File:** `qictstrategicsourcingcmgpublicdatasetssagovtictcontracts08012015.csv` (sha256 `b81874ea6aa9…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1088, 35.34s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_08/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
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
| 1 | `Contract` | `entity.trading_name` | clean_whitespace [when {"column": "Contract", "matches": "^(?!Software Suppliers$).+"}] | P | held_out | 0.50 | 100.0% | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Contract`: short supplier name; generic category rows excluded

## Left unmapped (not guessed)

- `Segment`: contract category
- `Guideline`: guideline text
- `CDContractSummary`: contract title
- `Commencement Date`: contract event date
- `OriginalExpiryDate`: contract event date
- `Completion Date`: contract event date
- `ExtnComments`: comments
- `Contract Value`: contract value

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 77, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: Mapping Contract to trading_name is unsupported. It is a label that is sometimes a category rather than an entity name, so that field should be removed. The unmapped columns are reasonable.
  - [blocking] `entity.trading_name<-Contract`: The Contract column is not a trading-as name. In the first row it holds a generic category ('Software Suppliers'), which is not any entity's name. Other rows hold short supplier names such as 'Oracle' and 'Hewlett-Packard'. The CDContractSummary column holds the fuller supplier legal names (e.g. 'Acer Computer Australia Pty Ltd'). Mapping Contract to trading_name therefore asserts a name the source does not state as a trading name, and for the category row it names no entity at all. (suggested: Remove the trading_name mapping for Contract, or restrict it to rows where it is a supplier name. Put Contract in unmapped with the reason 'short supplier label, sometimes a category'.)
  - [advisory] `entity.legal_name`: CDContractSummary embeds the supplier's full legal name (e.g. 'Optus Networks Pty Limited', 'Lenovo Australia & New Zealand Pty Ltd'), but the mapping neither extracts it nor flags it. Parsing it would need a transform that does not exist. (suggested: List CDContractSummary under needs_transform, noting that a supplier name is embedded in the title text.)
  - [advisory] `record_id`: hash_row is used with no uniqueness check. The rows are fairly distinct, but the same supplier recurs (e.g. Microsoft, Hewlett-Packard), so a stable record key would be better if one exists. (suggested: Keep hash_row, or use a combination such as Contract plus CDContractSummary if check_unique passes.)
- Critique: The mapping is sound. It maps the supplier (not the government buyer) as trading_name, excludes the generic category row, and leaves contract dates unmapped as event dates. I found no blocking problems, only advisory notes on richer name data.
  - [advisory] `entity.trading_name<-Contract`: The Contract column holds short supplier names such as Hewlett-Packard, Microsoft and Oracle. These are not labelled as registered names, so trading_name is the correct and conservative target under rule 5. The mapping does not state anything the source does not support. The full legal names (e.g. 'Acer Computer Australia Pty Ltd') appear only inside CDContractSummary, which is unmapped. (suggested: No change needed. A future version could parse the legal name out of CDContractSummary if a suitable transform exists, otherwise list it under needs_transform.)
  - [advisory] `entity.trading_name<-Contract`: The rows have no explicit entity_type column, and the suffix-based transform cannot apply to short names, so entity_type is correctly left as unknown. The row with Contract='Software Suppliers' is correctly excluded as a generic category rather than a supplier. (suggested: No action needed.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Contract`: `Hewlett-Packard` → `Hewlett-Packard`; `Data#3` → `Data#3`; `Microsoft` → `Microsoft`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
