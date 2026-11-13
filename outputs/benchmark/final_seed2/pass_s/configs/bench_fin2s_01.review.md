# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1309, 38.87s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_01/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1, "delimiter": "\t"}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)
- `valid_from`: from `SMSF_REG_DT` (parse_date); held-out parse rate 100.0%; evidence **held_out**

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. REGISTER_NAME | SMSF_NUM | SMSF_NAME | SMSF_STATUS | SMSF_PERSON_ABN | SMSF_REG_DT | SMSF_SUSP_START_DT | SMSF_SUSP_END_DT | SMSF_LOCALITY | SMSF_POST_CODE | SMSF_STATE | SMSF_ATTRIBUTE_TYPE | SMSF_CAPACITY | SMSF_CONDITION_NUMBER | SMSF_CAPACITY_FIRM_NAME
2. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070460 | ∅
3. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070459 | ∅
4. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070458 | ∅
5. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070457 | ∅
6. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070456 | ∅
7. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070455 | ∅
8. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Condition | ∅ | 1-19616070454 | ∅
9. SMSF Auditor | 100263447 | Benjamin Jenkins | Registered | ∅ | 10/02/2016 | ∅ | ∅ | West Bathurst | 2795 | NSW | Capacity | Member (Partner) of Audit firm | ∅ | GPP Audit Pty Limited
10. SMSF Auditor | 100263312 | Alissa Hodge | Registered | ∅ | 10/02/2016 | ∅ | ∅ | Launceston | 7250 | TAS | Condition | ∅ | 1-19615990662 | ∅
11. SMSF Auditor | 100263312 | Alissa Hodge | Registered | ∅ | 10/02/2016 | ∅ | ∅ | Launceston | 7250 | TAS | Condition | ∅ | 1-19615990661 | ∅
12. SMSF Auditor | 100263312 | Alissa Hodge | Registered | ∅ | 10/02/2016 | ∅ | ∅ | Launceston | 7250 | TAS | Condition | ∅ | 1-19615990640 | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | held_out | 0.70 | 100.0% | **0.70** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | held_out | 0.85 | 100.0% | **0.85** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | P | held_out | 0.90 | 100.0% | **0.90** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(['%d/%m/%Y']) | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: Regulator register; holder of auditor registration
2. `entity.abn` ← `SMSF_PERSON_ABN`: auditor ABN
3. `entity.status` ← `SMSF_STATUS`: registration status
4. `entity.date_registered` ← `SMSF_REG_DT`: registration date
5. `address.locality` ← `SMSF_LOCALITY`: locality
6. `address.postcode` ← `SMSF_POST_CODE`: postcode
7. `address.state` ← `SMSF_STATE`: state

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant register label
- `SMSF_NUM`: auditor number, no ontology field
- `SMSF_SUSP_START_DT`: suspension dates not mapped
- `SMSF_SUSP_END_DT`: suspension dates not mapped
- `SMSF_ATTRIBUTE_TYPE`: row type
- `SMSF_CAPACITY`: no field
- `SMSF_CONDITION_NUMBER`: no field
- `SMSF_CAPACITY_FIRM_NAME`: employer firm, not the entity
- `SMSF_CAPACITY_START_DT`: no field
- `SMSF_CONDITION`: no field
- `SMSF_CONDITION_DTL`: no field
- `SMSF_CONDITION_START_DT`: no field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. The register lists the individual auditors who hold the registration, so legal_name from SMSF_NAME follows rule 5b. The ABN is mapped with the abn transform and is absent on some rows, which is fine. Entity type is left unknown, and the date formats match the sample rows. Only advisory issues remain.
  - [advisory] `valid_from`: valid_from is mapped from SMSF_REG_DT, the same column as entity.date_registered. The column does state when the auditor's registration started, so this is supported, but it duplicates date_registered. Registration start is not necessarily when the name, ABN or address became true. (suggested: Keep it if registration start is accepted as valid_from. Otherwise drop valid_from and keep only entity.date_registered.)
  - [advisory] `entity.status<-SMSF_STATUS`: map_values covers only Registered and Suspended. Other values the register may hold (e.g. Removed, Disqualified, Cancelled) are unmapped and would be lost. (suggested: Add mappings for every status value in the profile that has a clear meaning, e.g. a cancelled or removed status mapped to deregistered.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: Under rule 5b a regulator register without an explicit label for the name column should have mapping_confidence of 0.7 or lower. The reason cites a regulator register and holder of auditor registration, but SMSF_NAME carries no explicit registered-name label. (suggested: Set mapping_confidence to 0.7 or lower for SMSF_NAME.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `RIMAL PRASAD` → `RIMAL PRASAD`; `Xin Li` → `Xin Li`; `Hao Yang` → `Hao Yang`
- `entity.abn<-SMSF_PERSON_ABN`: `26487720933` → `26487720933`; `84616150252` → `84616150252`; `31876470368` → `31876470368`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `entity.date_registered<-SMSF_REG_DT`: `11/02/2016` → `2016-02-11`; `12/03/2013` → `2013-03-12`; `08/03/2013` → `2013-03-08`
- `address.locality<-SMSF_LOCALITY`: `Aspley` → `Aspley`; `Hurstville` → `Hurstville`; `Kellyville` → `Kellyville`
- `address.postcode<-SMSF_POST_CODE`: `4034` → `4034`; `2220` → `2220`; `2155` → `2155`
- `address.state<-SMSF_STATE`: `QLD` → `QLD`; `NSW` → `NSW`; `VIC` → `VIC`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
