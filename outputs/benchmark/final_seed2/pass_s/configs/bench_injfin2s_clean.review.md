# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0835, 22.74s (download and human waits excluded). Trace: `logs/agent_runs/bench_injfin2s_clean/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
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
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `Postcode` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `Licence Status` | `entity.status` | map_values({'Current': 'active', 'Expired': 'deregistered'}) | P | held_out | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: licence holder in register
2. `entity.abn` ← `ABN`: ABN
3. `address.locality` ← `Suburb`: suburb
4. `address.state` ← `State`: state
5. `address.postcode` ← `Postcode`: postcode
6. `entity.status` ← `Licence Status`: licence status

## Left unmapped (not guessed)

- `Notes`: free text notes

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: legal_name, abn, address fields and status are each supported by the source, and entity_type correctly falls back to unknown. Only advisory caveats were found, on the status wording and on confidence for legal_name.
  - [advisory] `entity.status<-Licence Status`: An 'Expired' licence is mapped to entity.status 'deregistered'. The source says only that the licence expired, not that the entity was deregistered. The mapping follows a rule-style status map, and 'Expired' (e.g. LIC00135) is the only evidence, so this is a nuance. (suggested: Keep the mapping but note that 'deregistered' reflects licence expiry rather than entity deregistration. Alternatively map 'Expired' to 'unknown' for a more conservative claim.)
  - [advisory] `entity.legal_name<-Business Name`: The column is labelled 'Business Name' rather than as a licence holder or registered name. Rule 5b allows legal_name for a regulator register's licence holder, but without an explicit label confidence should be 0.7 or lower. The config shows no mapping_confidence. (suggested: Set mapping_confidence to 0.7 or lower, with the basis that this is a licence register and the holder is the subject.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Plumbing Services 16 Pty Ltd` → `Plumbing Services 16 Pty Ltd`; `Roofing Services 18 Pty Ltd` → `Roofing Services 18 Pty Ltd`; `Painting Services 21 Pty Ltd` → `Painting Services 21 Pty Ltd`
- `entity.abn<-ABN`: `89200000208` → `89200000208`; `25200000234` → `25200000234`; `65200000273` → `65200000273`
- `address.locality<-Suburb`: `Glenelg` → `Glenelg`; `Parramatta` → `Parramatta`; `Fremantle` → `Fremantle`
- `address.state<-State`: `SA` → `SA`; `NSW` → `NSW`; `WA` → `WA`
- `address.postcode<-Postcode`: `5045` → `5045`; `2150` → `2150`; `6160` → `6160`
- `entity.status<-Licence Status`: `Current` → `active`; `Expired` → `deregistered`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
