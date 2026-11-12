# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0055, 30.01s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_03/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "xlsx", "sheet": "Sheet1", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `SchoolNumber, Fin_Period` — 0 duplicate / blank keys of 1540 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. SchoolNumber | SchoolName | Fin_Period | LoadDate | ABN
2. 1 | Alberton Primary School | 201506 | 2015-07-14 06:30:43 | 35954747085
3. 3 | Allansford and District Primary School | 201506 | 2015-07-14 06:30:43.863000 | 37051817052
4. 4 | Avoca Primary School | 201506 | 2015-07-07 06:36:29.823000 | 39744336864
5. 8 | Avenel Primary School | 201506 | 2015-07-02 06:30:42.930000 | 88819505004
6. 12 | Warrandyte Primary School | 201506 | 2015-07-02 06:30:43.760000 | 89340494951
7. 26 | Belmont Primary School | 201506 | 2015-07-14 06:30:44.730000 | 62403505329
8. 28 | Bacchus Marsh Primary School | 201506 | 2015-07-14 06:30:45.510000 | 61829351598
9. 33 | Ballarat Primary School (Dana Street) | 201506 | 2015-07-14 06:30:46.543000 | 30126215434
10. 37 | Wodonga Primary School | 201506 | 2015-07-02 06:30:44.597000 | 30751949495
11. 40 | Berwick Primary School | 201506 | 2015-07-17 06:30:48.790000 | 61834093182
12. 60 | Beaufort Primary School | 201506 | 2015-07-07 06:36:30.583000 | 57463155273

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |
| 2 | `SchoolName` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: Column labelled ABN holding 11-digit Australian Business Numbers; checksum validated.
2. `entity.trading_name` ← `SchoolName`: School name; the source does not label it as a registered name, so mapped to trading_name at low confidence.

## Left unmapped (not guessed)

- `SchoolNumber`: Internal school number; used only as part of the record key.
- `Fin_Period`: Financial period code of the extract; not a registration or status date. Used as part of the record key.
- `LoadDate`: Internal load timestamp of the extract, not a statement by the source about the entity.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber', 'Fin_Period'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the ABN and school-name columns are mapped to fields they describe, the status and dates are correctly left unmapped, and the internal columns are reasonably excluded. The issues raised are advisory caveats about record-key uniqueness, whether the ABN belongs to the school or a parent body, and the missing confidence on the name mapping. None shows a value placed in a field the source does not support, so no blocking issue was found.
  - [advisory] `record_id`: The record_id is a composite of SchoolNumber and Fin_Period, but the config does not show a check_unique result. The examples show distinct school numbers within one period, yet uniqueness across the whole extract is not demonstrated. (suggested: Run check_unique on the composite key over the full extract, or fall back to hash_row=true if duplicates appear.)
  - [advisory] `entity.abn<-ABN`: The ABN column is mapped as the school's own identifier. Government schools often hold ABNs registered to a parent education department rather than to the individual school. The examples do not show which entity the ABN belongs to, so the claim that this ABN identifies the school is not confirmed by the source. (suggested: Check a sample of ABNs against the ABR to see whether they belong to the school or to a parent government body. If they belong to the parent, record the link at lower confidence or note the caveat in source_reliability_basis.)
  - [advisory] `entity.trading_name<-SchoolName`: The config gives no mapping_confidence for this mapping. Rule 5 requires confidence of 0.6 or lower for a name the data does not label as registered. The school name is a reasonable reading of trading_name, but the source does not say it is a registered or trading name. (suggested: Set mapping_confidence to 0.6 or lower and record that the SchoolName column carries no registered-name label.)
  - [advisory] `observed_at`: observed_at uses resource_last_modified, which is a publication timestamp for the file. The LoadDate column is an internal load stamp and is correctly unmapped, but the config gives no reason for choosing the metadata date over the period in Fin_Period. (suggested: Keep resource_last_modified and add a short note that Fin_Period is a period code, not a statement date.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `11644956677` → `11644956677`; `45672106108` → `45672106108`; `89499300463` → `89499300463`
- `entity.trading_name<-SchoolName`: `Cavendish Primary School` → `Cavendish Primary School`; `Doncaster Primary School` → `Doncaster Primary School`; `Echuca Primary School` → `Echuca Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
