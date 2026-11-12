# Review packet (round-2 agent): validated_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0054, 23.86s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_09/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "xlsx", "sheet": "data lrf", "header_rows": 1, "skip_rows": 1, "encoding": "utf-8-sig"}`
- layout: column names from raw row 2; data starts at raw row 3.
- `record_id`: from `School No` — 0 duplicate / blank keys of 1520 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Parent Voluntary Contributions 2011 to 2 | ∅ | ∅ | ∅ | ∅
2. School No | School Name | 2011 | 2012 | 2013
3. 1 | Alberton Primary School | 42107.92997000001 | 28139.260009000005 | 32505.109976
4. 3 | Allansford and District Primary School | 87156.91001199998 | 74318.82998300002 | 93871.350003
5. 4 | Avoca Primary School | 57923.99999500002 | 63689.900008000004 | 54976.910042999996
6. 8 | Avenel Primary School | 90685.32999 | 91047.92993999997 | 121691.37999699998
7. 12 | Warrandyte Primary School | 210669.61000800002 | 246498.91001500003 | 246070.05996200006
8. 26 | Belmont Primary School | 96124.210016 | 108339.430054 | 122312.090005
9. 28 | Bacchus Marsh Primary School | 378926.60004200006 | 346736.2100450001 | 410779.85999100003
10. 33 | Ballarat Primary School (Dana Street) | 46027.990026000014 | 55589.89003500001 | 101322.70992499999
11. 37 | Wodonga Primary School | 261877.04994199995 | 191959.820028 | 229292.53005599993
12. 40 | Berwick Primary School | 278472.30003100005 | 295598.60003200005 | 421684.73998

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `School Name` | `entity.trading_name` | clean_whitespace | W | held_out | 0.50 | 100.0% | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `School Name`: School name of a government body; the column is not labelled as a registered, licensee or supplier name, so it is mapped as trading name at low confidence per rule 5.

## Left unmapped (not guessed)

- `School No`: Internal school number, not an ABN/ACN; used only as record_id (checked unique across 1,220 training rows, 0 repeats).
- `2011`: Yearly parent voluntary payment total; a measurement, not an entity attribute.
- `2012`: Yearly parent voluntary payment total; a measurement, not an entity attribute.
- `2013`: Yearly parent voluntary payment total; a measurement, not an entity attribute.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1520, 'key': ['School No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is broadly sound. School Name goes to trading_name at low confidence, which rule 5 allows, and entity_type is correctly left unknown. The three yearly payment columns are correctly unmapped as measurements. No blocking meaning errors appear in the examples. The remaining points concern missing confidence, uniqueness, reliability and reader details.
  - [advisory] `entity.trading_name<-School Name`: The column is labelled 'School Name' and has no registered or licensee label. Rule 5 allows this mapping to trading_name, but only at 0.6 or lower. The config gives 'low confidence' in its reason but no numeric mapping_confidence, so the confidence level is not recorded. (suggested: Set an explicit mapping_confidence of 0.6 or lower on this mapping and record it in the config.)
  - [advisory] `record_id`: record_id is set from 'School No' but the config does not show a check_unique result or a statement that the column is unique across rows. Rule 15 requires that. (suggested: Confirm School No is unique across the sheet, or use hash_row=true.)
  - [advisory] `source_reliability`: The config has no source_reliability value or basis for the claims. Rule 16 requires one per claim kind. (suggested: Add source_reliability per claim kind with a short basis, for example noting that this is a government education dataset.)
  - [advisory] `reader`: The config sets header_rows 1 and skip_rows 1 on sheet 'data lrf'. The examples show clean headers, so the skipped row is not visible here. The reader settings should be checked against the file. (suggested: Verify the skipped row and header row against the raw sheet, and document why one row is skipped.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-School Name`: `Beaufort Primary School` → `Beaufort Primary School`; `Cheltenham Primary School` → `Cheltenham Primary School`; `Campbells Creek Primary School` → `Campbells Creek Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
