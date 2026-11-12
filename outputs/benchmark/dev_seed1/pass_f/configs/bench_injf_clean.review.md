# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0063, 28.89s (download and human waits excluded). Trace: `logs/agent_runs/bench_injf_clean/trace.jsonl`.

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
| 1 | `ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |
| 2 | `Business Name` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `Postcode` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated
2. `entity.trading_name` ← `Business Name`: Name of the business; not labelled as registered name, so treated as trading name at low confidence
3. `address.locality` ← `Suburb`: Suburb column
4. `address.state` ← `State`: State code column
5. `address.postcode` ← `Postcode`: 4-digit postcode

## Left unmapped (not guessed)

- `Licence Status`: Licence status describes the licence, not the entity status enum; no safe mapping
- `Notes`: Free-text notes, sparsely filled
- `Licence No`: Used as record_id

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.entity_type<-Business Name`: Not mapped; suffix rule could apply (all sampled names end Pty Ltd) but left out to keep the config conservative. Engine records unknown.
- `entity.status<-Licence Status`: Describes the licence rather than the entity; no safe mapping to entity status enum.

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking problems found: the ABN, locality, state and postcode mappings match their columns in every sample row, the ABN checksum holds for the first sampled value, and the observed_at and record_id choices fit a snapshot register. The remaining points are advisory: the holder-name mapping could state its confidence and role more explicitly, and entity_type could be derived from the 'Pty Ltd' suffix as rule 7 permits.
  - [advisory] `entity.trading_name<-Business Name`: This is a licence register, and the row's subject is the licence holder. Rule 5b allows the holder's name to map to legal_name at 0.7 or lower when the register does not label it as the licensee name. The config instead maps it to trading_name, which is the safer default under rule 5 and is not a misstatement, but the config records no mapping_confidence and the reasoning is not tied to the register's holder role. (suggested: Keep trading_name at 0.6 or lower, or consider legal_name at 0.7 or lower under rule 5b. Record mapping_confidence explicitly and note that the subject is the licence holder.)
  - [advisory] `entity.entity_type`: Business Name values end in 'Pty Ltd' on every sampled row. The source has no entity_type column, so rule 7 permits entity_type_from_suffix on the name column. The config leaves entity_type unmapped, so every entity is recorded as unknown, which is less rich than the source supports. (suggested: Consider mapping entity.entity_type with entity_type_from_suffix on Business Name, after checking the suffix rule on a wider sample of names.)
  - [advisory] `entity.status`: Licence Status (values such as 'Current') is unmapped because it describes the licence, not the entity. That is a reasonable call. The status enum is not otherwise populated, so the entity's status is left unobserved from this source. (suggested: Keep Licence Status unmapped unless the dataset defines whether a current licence implies an active entity; document the decision in the unmapped reason.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `97200000195` → `97200000195`; `10200000221` → `10200000221`; `25200000234` → `25200000234`
- `entity.trading_name<-Business Name`: `Landscaping Services 15 Pty Ltd` → `Landscaping Services 15 Pty Ltd`; `Electrical Services 17 Pty Ltd` → `Electrical Services 17 Pty Ltd`; `Roofing Services 18 Pty Ltd` → `Roofing Services 18 Pty Ltd`
- `address.locality<-Suburb`: `Fremantle` → `Fremantle`; `Sandy Bay` → `Sandy Bay`; `Parramatta` → `Parramatta`
- `address.state<-State`: `WA` → `WA`; `TAS` → `TAS`; `NSW` → `NSW`
- `address.postcode<-Postcode`: `6160` → `6160`; `7005` → `7005`; `2150` → `2150`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
