# Review packet (round-2 agent): validated_config

**Dataset:** Temporary emissions licences (TEL) — Environment, Tourism, Science and Innovation  
**Licence:** Creative Commons Attribution 4.0  
**File:** `tel-register.xlsx` (sha256 `59eb4964d903…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0857, 24.59s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_07/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "xlsx", "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)
- `valid_from`: from `Commenced Date` (parse_date); held-out parse rate 100.0%; evidence **held_out**
- `valid_to`: from `End Date` (parse_date); held-out parse rate 100.0%; evidence **held_out**

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. TEL Reference | TEL Holder(s) | Issued Date | Commenced Date | End Date | Status | Activities | Locations
2. A-TEL-NEW-100172685 | SYNTECH RESOURCES PTY LTD | 2021-12-03 00:00:00 | ∅ | ∅ | Expired | Ancillary 31 - Mineral processing; Ancil | ML50233; ML50258; ML50259; ML50260; ML50
3. A-TEL-NEW-100213656 | TA Australia Security Agent Pty Ltd | 2022-03-03 00:00:00 | ∅ | ∅ | Superseded | Sch 3 ERA 16 mining gold ore | 4570; GYMPIE REGIONAL; ML50160 MONKLAND
4. A-TEL-NEW-100213656 | TA Australia Security Agent Pty Ltd | 2022-03-11 00:00:00 | ∅ | ∅ | Expired | Sch 3 ERA 16 mining gold ore | 4570; GYMPIE REGIONAL; ML50160 MONKLAND
5. A-TEL-NEW-100213898 | DGR GLOBAL LIMITED | 2022-03-03 00:00:00 | ∅ | ∅ | Expired | Sch 3 ERA 16 mining gold ore | ML3678; ML3741; ML3749; ML3752; ML3753; 
6. A-TEL-NEW-100214110 | BRISBANE CITY COUNCIL | 2022-03-03 00:00:00 | ∅ | ∅ | Superseded | ∅ | ∅
7. A-TEL-NEW-100214249 | Hanson Construction Materials Pty Ltd | 2022-03-02 00:00:00 | ∅ | ∅ | Expired | ∅ | ∅
8. A-TEL-NEW-100214374 | CENTRAL SEQ DISTRIBUTOR-RETAILER AUTHORI | 2022-03-03 00:00:00 | ∅ | ∅ | Superseded | ERA 63 - Sewage Treatment | 0/BUP5643; 0/SP107763; 0/SP153857; 0/SP1
9. A-TEL-NEW-100214374 | CENTRAL SEQ DISTRIBUTOR-RETAILER AUTHORI | 2022-03-04 00:00:00 | ∅ | ∅ | Superseded | ERA 63 - Sewage Treatment | 0/BUP5643; 0/SP107763; 0/SP153857; 0/SP1
10. A-TEL-NEW-100214374 | CENTRAL SEQ DISTRIBUTOR-RETAILER AUTHORI | 2022-06-03 00:00:00 | ∅ | ∅ | Expired | ERA 63 - Sewage Treatment | 0/BUP5643; 0/SP107763; 0/SP153857; 0/SP1
11. A-TEL-NEW-100214482 | ORORA LIMITED | 2022-03-03 00:00:00 | ∅ | ∅ | Superseded | ERA 36 - Pulp or paper manufacturing; ER | 107/SP309938; 2/SP309897; 2/SP318661; 3/
12. A-TEL-NEW-100214482 | ORORA LIMITED | 2022-03-08 00:00:00 | ∅ | ∅ | Expired | ERA 36 - Pulp or paper manufacturing; ER | 107/SP309938; 2/SP309897; 2/SP318661; 3/

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `TEL Holder(s)` | `entity.legal_name` | clean_whitespace | W | held_out | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `TEL Holder(s)`: Holder of licence on regulator register

## Left unmapped (not guessed)

- `TEL Reference`: licence number, not an entity identifier
- `Issued Date`: issue event date
- `Status`: licence status, not entity status
- `Activities`: ERA activities, not industry code
- `Locations`: lot/permit descriptors, not addresses

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 213, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the holder is correctly mapped to legal_name, entity_type is left unknown, and the date columns are used appropriately. Only advisory caveats remain.
  - [advisory] `entity.status<-Status`: Status (e.g. 'Expired') is left unmapped as licence status. Rule 8 says to map status only with map_values on visible raw values, and 'Expired' is a licence state, not entity status, so leaving it unmapped is defensible. The licence lifecycle is not captured anywhere. (suggested: Keep Status unmapped. Optionally note that licence expiry is covered by valid_to where End Date is present.)
  - [advisory] `valid_from<-Commenced Date`: Commenced Date and End Date are only filled on a few rows (e.g. the TEL1008... rows), so most rows have null valid_from/valid_to. For rows with 'Expired' status and only an Issued Date, the licence start is not captured. This is incompleteness, not an error. (suggested: Leave as is. Issued Date should stay unmapped because it is an issue event date, not a start date for the holder's licence.)
  - [advisory] `entity.legal_name<-TEL Holder(s)`: The mapping follows rule 5b (regulator register, licence holder), but no source column explicitly labels the value as the registered name, so confidence should be 0.7 or lower. Some holders are such as 'Queensland Urban Utilities' and may not be exact registered names. The mapping does not state a mapping_confidence. (suggested: Set mapping_confidence to 0.7 or lower for legal_name under rule 5b.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-TEL Holder(s)`: `ABERDARE COLLIERIES PROPRIETARY LIMITED` → `ABERDARE COLLIERIES PROPRIETARY LIMITED`; `Boral Resources (Qld) Pty. Limited` → `Boral Resources (Qld) Pty. Limited`; `HOLCIM (AUSTRALIA) PTY LTD` → `HOLCIM (AUSTRALIA) PTY LTD`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
