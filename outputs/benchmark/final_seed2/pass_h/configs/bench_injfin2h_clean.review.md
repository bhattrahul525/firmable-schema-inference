# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0083, 40.72s (download and human waits excluded). Trace: `logs/agent_runs/bench_injfin2h_clean/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate: 0 hard failures, 480 observations, 0 rejected on 80 held-out rows; record_id Licence No has 0 duplicates over 160 rows; ABN parse 100%. Dataset licence not stated in source; flagged as unknown.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `Licence No` — 0 duplicate / blank keys of 160 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Licence No | Business Name | ABN | Suburb | State | Postcode | Licence Status | Notes
2. LIC00001 | Electrical Services 1 Pty Ltd | 19200000013 | Richmond | VIC | 3121 | Current | ∅
3. LIC00002 | Roofing Services 2 Pty Ltd | 34200000026 | Fortitude Valley | QLD | 4006 | Current | ∅
4. LIC00003 | Concreting Services 3 Pty Ltd | 49200000039 | Fremantle | WA | 6160 | Current | ∅
5. LIC00004 | Carpentry Services 4 Pty Ltd | 59200000052 | Glenelg | SA | 5045 | Current | ∅
6. LIC00005 | Painting Services 5 Pty Ltd | 74200000065 | Sandy Bay | TAS | 7005 | Current | ∅
7. LIC00006 | Tiling Services 6 Pty Ltd | 89200000078 | Parramatta | NSW | 2150 | Current | ∅
8. LIC00007 | Landscaping Services 7 Pty Ltd | 10200000091 | Richmond | VIC | 3121 | Current | renewal pending
9. LIC00008 | Plumbing Services 8 Pty Ltd | 91200000104 | Fortitude Valley | QLD | 4006 | Current | ∅
10. LIC00009 | Electrical Services 9 Pty Ltd | 17200000117 | Fremantle | WA | 6160 | Expired | ∅
11. LIC00010 | Roofing Services 10 Pty Ltd | 27200000130 | Glenelg | SA | 5045 | Current | ∅
12. LIC00011 | Concreting Services 11 Pty Ltd | 42200000143 | Sandy Bay | TAS | 7005 | Current | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 2 | `ABN` | `entity.abn` | abn | W | held_out | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `Postcode` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Business Name`: Column labelled 'Business Name' in a licence register; not explicitly the registered or licensee name, so mapped as trading name at reduced confidence. Values end in 'Pty Ltd', so the name may be the registered name, but the register does not label it as such.
2. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated.
3. `address.locality` ← `Suburb`: Suburb column.
4. `address.state` ← `State`: State code column.
5. `address.postcode` ← `Postcode`: Postcode column.

## Left unmapped (not guessed)

- `Licence No`: Used as record_id.
- `Licence Status`: Status of the licence, not of the entity; entity.status would be a misinterpretation.
- `Notes`: Free-text notes, sparse.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN, locality, state and postcode mappings are consistent with the rows shown. The main problem is that 'Business Name' is mapped to legal_name, which the rules reserve for registered or licensee names, and the column label points to trading name. Other points are advisory: confidence and reliability fields are missing, and the envelope licence is not stated.
  - [blocking] `entity.legal_name<-Business Name`: The source column is literally labelled 'Business Name', and rule 5 names 'business name' as the marker for trading_name. The config maps it to legal_name on the strength of the register context alone. Rule 5b only permits legal_name for a holder-of-licence register at confidence 0.7 or lower, and the config states no such confidence. The mapping therefore asserts a registered name the source does not state. (suggested: Map 'Business Name' to entity.trading_name at confidence 0.6 or lower. If the team wants legal_name, it needs a column that is labelled as the licensee or registered name, or a documented 5b mapping at confidence 0.7 or lower with the holder basis stated.)
  - [advisory] `entity.legal_name<-Business Name`: No mapping_confidence or source_reliability is given for the name claim, and the 5b holder basis is only implied by the reason text. (suggested: Add mapping_confidence and source_reliability with a basis for the claim kind, and state explicitly that the register lists the row's subject as the licence holder.)
  - [advisory] `observation.licence`: The config does not record the dataset licence, so the envelope cannot be completed from the mapping. (suggested: Take the licence from the CKAN metadata, or record 'unknown' and flag it as a finding.)
- Critique: The mapping is largely sound: the ABN, suburb, state and postcode columns match their meanings, and Licence Status, Notes and Licence No are handled correctly. No blocking meaning errors appear in the examples. The main caveat is that 'Business Name' values carry a 'Pty Ltd' registered-company form, so the trading_name claim should carry reduced confidence. The envelope also needs a licence value and confirmed record_id uniqueness.
  - [advisory] `entity.trading_name<-Business Name`: The sample names all end in 'Pty Ltd', a registered company form. That suggests these may be registered names held by a licence holder, so trading_name may understate them. Rule 5b only allows legal_name with an explicit label, so trading_name is the defensible choice, but mapping_confidence should be 0.6 or lower and the caveat should be recorded. (suggested: Keep trading_name, set mapping_confidence to 0.6 or lower, and note in the reason that the 'Pty Ltd' suffix suggests the registered name and that the register does not label the column as the licensee name.)
  - [advisory] `observation.licence`: The config does not show a licence value for the dataset, and the envelope requires one. Nothing in the config states whether the source licence is known. (suggested: Add the dataset licence from the CKAN metadata, or record 'unknown' and flag it as a finding.)
  - [advisory] `record_id`: Licence No is used as the record_id, but the config does not show check_unique or a uniqueness check. Its uniqueness across rows is assumed, not shown. (suggested: Confirm uniqueness of Licence No across the resource with check_unique, or fall back to hash_row=true if duplicates exist.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Business Name`: `Carpentry Services 12 Pty Ltd` → `Carpentry Services 12 Pty Ltd`; `Tiling Services 14 Pty Ltd` → `Tiling Services 14 Pty Ltd`; `Plumbing Services 16 Pty Ltd` → `Plumbing Services 16 Pty Ltd`
- `entity.abn<-ABN`: `57200000156` → `57200000156`; `82200000182` → `82200000182`; `89200000208` → `89200000208`
- `address.locality<-Suburb`: `Parramatta` → `Parramatta`; `Fortitude Valley` → `Fortitude Valley`; `Glenelg` → `Glenelg`
- `address.state<-State`: `NSW` → `NSW`; `QLD` → `QLD`; `SA` → `SA`
- `address.postcode<-Postcode`: `2150` → `2150`; `4006` → `4006`; `5045` → `5045`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
