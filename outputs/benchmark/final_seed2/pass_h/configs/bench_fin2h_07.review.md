# Review packet (round-2 agent): validated_config

**Dataset:** Temporary emissions licences (TEL) — Environment, Tourism, Science and Innovation  
**Licence:** Creative Commons Attribution 4.0  
**File:** `tel-register.xlsx` (sha256 `59eb4964d903…`)

## How this ended

- Outcome **validated_config**.
- 15 model turns, 15 tool calls, $0.0135, 71.94s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_07/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded tel-register.xlsx (213 rows, 8 columns, one sheet). hash_row record id validated with 0 duplicates. Holder column is the licensee on a regulator register. Critique flagged that some holder cells append site/mine names after ';'; this is recorded as an open limitation with reduced confidence (0.6) and a needs_transform entry rather than fixed.

## Reader and record settings

- reader: `{"format": "xlsx", "sheet": "TEL Register", "header_rows": 1, "encoding": "utf-8-sig", "skip_rows": 0}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

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
| 1 | `TEL Holder(s)` | `entity.legal_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `TEL Holder(s)`: Column is the TEL Holder on a Queensland regulator's licence register; the row's subject is the holder (rule 5b). Some cells append a site or mine name after ';' and are not split, so confidence is lowered.

## Left unmapped (not guessed)

- `TEL Reference`: Licence identifier, not an entity identifier.
- `Issued Date`: Issue date of the TEL, not the entity's registration date.
- `Commenced Date`: Licence start date; dates the licence, not the holder's name.
- `End Date`: Licence end date; dates the licence, not the holder's name.
- `Activities`: Environmental activity (ERA) descriptions, not an industry code.
- `Locations`: Site/lot locations covered by the licence.
- `Status`: Values Expired/Superseded/Granted describe the licence, not the entity.

## Needs a transform the engine does not have

- `TEL Holder(s)`: Engine needs to take only the holder item from a ';'-separated cell, excluding site or mine names, before legal_name is reliable.

## Checks

- ⚠️ **legal_name_multiple**: 6% of legal_name values contain ';': a cell may hold several entities. Consider `split`.  
  Agent's answer: *kept*: Splitting would also split site or mine names into legal_name; whole cell kept at reduced confidence and flagged in needs_transform.
- Duplicate record ids in held-out rows: {'rows': 213, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound: the holder column is correctly mapped to legal_name for real company and council holders, and the unmapped columns are justified. The main problem is that the ';' split feeds a mine name ('Mt Rawdon Mine') into legal_name, which the source does not support as a registered holder name. The valid_from from Commenced Date is defensible for the licence but should not be read as the name's start date.
  - [blocking] `entity.legal_name<-TEL Holder(s)`: The split on ';' turns the second holder item in row ENEL04614613 ('Mt Rawdon Mine') into a legal_name observation. That item is a mine name, a site the licence covers, not a registered holder. The source does not state it as a registered or licensee name, so mapping it to legal_name claims something the source does not support. (suggested: Do not map split items to legal_name when they name a site or mine. Map the holder column to legal_name only for the holder entity, or map any non-holder name to entity.trading_name at 0.6 or lower. Consider a `when` or a separate field so only the holder item becomes legal_name.)
  - [advisory] `valid_from`: Commenced Date dates when the licence (TEL) started, but the envelope applies it to the holder's legal_name observation as valid_from. That is the date the licence began, not when the holder's name became true. (suggested: Keep valid_from if the licence start is wanted as a licence claim, but note that it dates the licence, not the name. Alternatively, attach it to a licence-specific observation rather than the entity name.)
  - [advisory] `entity.legal_name<-TEL Holder(s)`: The holder column is a register of licence holders, so mapping it to legal_name is reasonable under rule 5b. No mapping_confidence is stated, and the column is mixed with sites and named projects in some rows, which lowers confidence. (suggested: State a mapping_confidence at or below 0.7 for this field, and say that the register is a licensing register and that rows can mix holders with site or mine names.)
- Critique: The mapping is mostly sound: TEL Holder(s) is a holder column on a licensing register (rule 5b), the unmapped licence dates and status are correctly excluded, and valid_from is correctly null. The one blocking problem is that holder cells holding a site or mine name after a semicolon are emitted whole as legal_name, so the site name becomes part of the registered name. Splitting or excluding those items would fix it. Confidence and reliability fields are missing and should be added.
  - [blocking] `entity.legal_name<-TEL Holder(s)`: The example row 'LGL MOUNT RAWDON OPERATIONS PTY LTD; Mt Rawdon Mine' is mapped whole to entity.legal_name. The source holds two items separated by ';': the holder, and a site/mine name. The mapping states that 'Mt Rawdon Mine' is part of the registered holder name, which the source does not support. The config's own reason acknowledges that some cells hold site or project names, but the mapping still emits them as the legal name. (suggested: Split the holder column on ';' (in one group, per rule 12) and keep only the item that is the licence holder as legal_name. Alternatively, drop the site/project items as non-entity text. Do not emit the combined string as legal_name. Re-check every cell in the column for similar site or project suffixes.)
  - [advisory] `entity.legal_name<-TEL Holder(s)`: The config has no mapping_confidence, and the lowered confidence mentioned in the reason is not written into the field. The rule 5b basis (regulator register, row subject is the holder) is stated only in prose. (suggested: Set an explicit mapping_confidence (at or below 0.7 under rule 5b, lower while site-name cells remain unsplit) and a source_reliability with basis for the entity.legal_name claim.)
  - [advisory] `entity.legal_name<-TEL Holder(s)`: Government-body holders such as 'Queensland Bulk Water Supply authority' and 'Rockhampton Regional Council' are mapped as legal_name with entity_type left unknown. That is consistent with rule 7, but the row subject is a government body and the config does not say so. (suggested: Leave entity_type as unknown (correct under rule 7). Optionally record in the config notes that government holders appear in this register and are not classified.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-TEL Holder(s)`: `ABERDARE COLLIERIES PROPRIETARY LIMITED` → `ABERDARE COLLIERIES PROPRIETARY LIMITED`; `Logan City Council` → `Logan City Council`; `HOLCIM (AUSTRALIA) PTY LTD` → `HOLCIM (AUSTRALIA) PTY LTD`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
