# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0075, 41.63s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_02/trace.jsonl`.
- Evidence the agent gave at finish (its words): Workbook has 9 sheets, one per year (2017-18 to 2024-25) plus a 'JMEI version' sheet. This config maps only the 2024-25 sheet (31 rows, 3 columns: Name, ABN, Commissioners allocation $). Other year sheets were not mapped and are not covered; the 2022-23 sheet has a different column count. ABN parse rate 100% on training rows; 0 rejects on held-out validation. ABN unique across the sheet.

## Reader and record settings

- reader: `{"format": "xlsx", "sheet": "2024-25", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `ABN` — 0 duplicate / blank keys of 31 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Name | ABN | Commissioners allocation $
2. Ausmon Resources Limited | 88134358964 | 600000
3. Barton Gold Holdings Limited | 36633442618 | 1488500
4. Bmg Resources Limited | 96107118678 | 364250
5. Cosmo Metals Limited | 17653132828 | 960000
6. Dreadnought Resources Limited | 40119031864 | 1488500
7. Eastern Metals Ltd | 29643902943 | 910750
8. Encounter Resources Limited | 47109815796 | 1475000
9. Errawarra Resources Ltd | 95155472834 | 450000
10. Everest Metals Corporation Ltd | 48119978013 | 1170000
11. Godolphin Resources Limited | 13633779950 | 600000
12. Golden State Mining Limited | 52621105995 | 875000

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.trading_name` | clean_whitespace | W | held_out | 0.50 | 100.0% | **0.50** |
| 2 | `ABN` | `entity.abn` | abn | W | held_out | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Name`: Name column in a government allocation list of applicants; not labelled as registered/licensee/supplier name, so mapped to trading_name at 0.5 per rule 5.
2. `entity.abn` ← `ABN`: ABN column, checksum validated by abn transform (100% parse on sample).

## Left unmapped (not guessed)

- `Commissioners allocation $`: Monetary grant allocation, no ontology field.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.entity_type`: No explicit entity-type column; entity_type_from_suffix was not added because it could not be critiqued after the mapping change. Recorded as unknown.
- `entity.legal_name`: Name column is not labelled as registered name; rule 5 forbids legal_name here.

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN mapping and the unmapped grant column follow the rules. The main problem is that the applicant Name column is mapped to legal_name without any label saying it is the registered name, which rule 5 forbids. It should be remapped to trading_name at 0.6 or lower.
  - [blocking] `entity.legal_name<-Name`: The Name column is a government allocation list of applicants. Nothing in the data labels it as a registered, licensee or supplier name, so mapping it to entity.legal_name states something the source does not support. Rule 5 allows legal_name only when the data says so, and the 0.6 confidence does not change that. (suggested: Remove the entity.legal_name<-Name mapping and map Name to entity.trading_name at confidence 0.6 or lower, as rule 5 requires for an unlabelled name column.)
  - [advisory] `record_id`: record_id is set to ABN, but the config does not show that ABN was checked for uniqueness. Some rows could repeat an ABN if an applicant appears more than once. (suggested: Confirm with check_unique that ABN is unique across the sheet. If it is not, use hash_row=true or add a column that identifies the row.)
  - [advisory] `entity.abn<-ABN`: The sample ABNs in the observations pass through without visible checksum results. The config does not show whether any invalid ABN was rejected or flagged. (suggested: Report how many ABNs failed the checksum and confirm that failures are excluded or flagged rather than emitted as valid.)
- Critique: No blocking problems: the ABN is mapped with its checksum transform, the Name column is mapped to trading_name at the 0.5 confidence rule 5 allows, and the grant amount is correctly left unmapped. The remaining points are advisory: confidence and reliability are not stated explicitly, entity_type could be derived from the company suffix, and the observed_at source should be confirmed.
  - [advisory] `entity.trading_name<-Name`: The Name column is labelled only as 'Name' in a government allocation list. Under rule 5 it maps to trading_name at 0.5, which is permitted, but the values (e.g. 'Great Southern Mining Limited') look like registered company names. The observations therefore record these as trading names with more certainty about the label than the source gives. (suggested: Keep the trading_name mapping at confidence 0.5 or lower, and record a caveat that the column's meaning is inferred from its position and values rather than from a label. Do not map to legal_name unless the source labels the name as registered.)
  - [advisory] `entity.entity_type`: The source has no explicit entity-type column, and the sample names carry company suffixes ('Limited', 'Ltd'). Rule 7 permits entity_type_from_suffix on the name column, but the config maps nothing, so every row is recorded as unknown. (suggested: Consider adding entity.entity_type via entity_type_from_suffix on the Name column, which would give company for these rows. Otherwise leave it unknown and note that choice.)
  - [advisory] `entity.abn<-ABN`: The config states the abn checksum transform parsed 100% of the sample, but it gives no mapping_confidence or source_reliability for this claim. Rule 14 asks for an explicit confidence, and the config leaves it out. (suggested: State mapping_confidence (about 0.95 is justified, since the column name and 11-digit values agree) and a source_reliability with a basis for the government allocation list.)
  - [advisory] `observed_at`: observed_at comes from resource_last_modified via from_metadata. The sample envelope shows 2024-07-11 for every row, but the config gives no check that this is the date the allocations were stated, rather than a later upload date. (suggested: Confirm that resource_last_modified reflects when the allocation list was published. If it does not, record the caveat on observed_at.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Name`: `Great Southern Mining Limited` → `Great Southern Mining Limited`; `Investigator Resources Ltd` → `Investigator Resources Ltd`; `Itech Minerals Ltd` → `Itech Minerals Ltd`
- `entity.abn<-ABN`: `37148168825` → `37148168825`; `90115338979` → `90115338979`; `41648219050` → `41648219050`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
