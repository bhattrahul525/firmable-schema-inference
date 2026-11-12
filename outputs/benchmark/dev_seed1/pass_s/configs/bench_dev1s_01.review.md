# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1271, 38.68s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_01/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.90 | 100.0% | **0.90** |
| 3 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(['%d/%m/%Y']) | W | 0.85 | 100.0% | **0.85** |
| 4 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.90 | 100.0% | **0.90** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.90 | 100.0% | **0.90** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: registered auditor name
2. `entity.abn` ← `SMSF_PERSON_ABN`: ABN
3. `entity.date_registered` ← `SMSF_REG_DT`: registration date
4. `entity.status` ← `SMSF_STATUS`: status
5. `address.locality` ← `SMSF_LOCALITY`: locality
6. `address.postcode` ← `SMSF_POST_CODE`: postcode
7. `address.state` ← `SMSF_STATE`: state

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant register name
- `SMSF_NUM`: auditor number, no ontology field
- `SMSF_SUSP_START_DT`: sparse suspension dates
- `SMSF_SUSP_END_DT`: sparse
- `SMSF_ATTRIBUTE_TYPE`: row type
- `SMSF_CAPACITY`: no field
- `SMSF_CONDITION_NUMBER`: no field
- `SMSF_CAPACITY_FIRM_NAME`: firm employer, not mapped
- `SMSF_CAPACITY_START_DT`: no field
- `SMSF_CONDITION`: no field
- `SMSF_CONDITION_DTL`: no field
- `SMSF_CONDITION_START_DT`: no field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: The mapping is largely sound and conservative: names, dates, addresses and the status mapping are consistent with the examples, and entity_type is left as unknown. Only advisory caveats remain, mainly about the person-versus-business meaning of the fields and the multi-row structure.
  - [advisory] `entity.date_registered<-SMSF_REG_DT`: The envelope valid_from appears to be filled with the registration date, which is a reasonable reading but is not stated as such by the source. The date is registration as an approved SMSF auditor, not registration of a business entity. (suggested: Keep it, but note in the reason that this is the date of registration as an SMSF auditor, not the date the business entity was registered.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The reason says 'registered auditor name', but the values are individual people's names (e.g. RIMAL PRASAD, Katie Timms). The source gives no support for calling these a registered legal name of a business entity, and the ABN column is a personal ABN. The entity_type is correctly left unknown, so the impact is limited. (suggested: Reword the reason to say it is an individual auditor's name as listed on the register. Keep entity_type unknown, since the source does not say whether the person is a sole trader.)
  - [advisory] `entity.status<-SMSF_STATUS`: The map_values only covers Registered and Suspended. Other statuses in the full data, such as ceased or disqualified, would be unmapped. The 'active' value comes from 'Registered' on an auditor register, which says the person is a registered auditor, not that a business is trading. (suggested: Confirm the full set of status values in the data and map them explicitly or leave them unknown. Document that 'active' means currently registered as an SMSF auditor.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The raw data contains multiple rows per auditor (SMSF_ATTRIBUTE_TYPE is Condition or Capacity). The same person can be emitted several times with identical claims. The row-hash record_id also differs per attribute row, which does not identify the auditor. (suggested: Consider using SMSF_NUM in the record key, or dedupe the observations per auditor. Document the multi-row structure.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `RIMAL PRASAD` → `RIMAL PRASAD`; `Hai Nguyen` → `Hai Nguyen`; `George Pampacos` → `George Pampacos`
- `entity.abn<-SMSF_PERSON_ABN`: `26487720933` → `26487720933`; `39941540890` → `39941540890`; `84267792579` → `84267792579`
- `entity.date_registered<-SMSF_REG_DT`: `11/02/2016` → `2016-02-11`; `25/08/2016` → `2016-08-25`; `12/03/2013` → `2013-03-12`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`; `Suspended` → `suspended`
- `address.locality<-SMSF_LOCALITY`: `Aspley` → `Aspley`; `Heidelberg West` → `Heidelberg West`; `PERTH` → `PERTH`
- `address.postcode<-SMSF_POST_CODE`: `4034` → `4034`; `3081` → `3081`; `6000` → `6000`
- `address.state<-SMSF_STATE`: `QLD` → `QLD`; `VIC` → `VIC`; `WA` → `WA`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
