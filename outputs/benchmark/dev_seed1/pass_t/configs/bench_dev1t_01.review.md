# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1279, 36.85s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_01/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.90 | 100.0% | **0.90** |
| 3 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(['%d/%m/%Y']) | W | 0.90 | 100.0% | **0.90** |
| 4 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.90 | 100.0% | **0.90** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.90 | 100.0% | **0.90** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: registered auditor name (individual)
2. `entity.abn` ← `SMSF_PERSON_ABN`: ABN
3. `entity.date_registered` ← `SMSF_REG_DT`: registration date
4. `entity.status` ← `SMSF_STATUS`: status
5. `address.locality` ← `SMSF_LOCALITY`: locality
6. `address.postcode` ← `SMSF_POST_CODE`: postcode
7. `address.state` ← `SMSF_STATE`: state

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant register name
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
- Critique: The mapping is largely sound. Individual auditors are mapped to legal_name, the employer firm is correctly left unmapped, and entity_type is left unknown. Only advisory caveats remain.
  - [advisory] `entity.abn<-SMSF_PERSON_ABN`: The config maps SMSF_PERSON_ABN, but none of the example raw rows contains that column and no abn observations appear, so the mapping cannot be checked against the data. The column is probably empty or absent in the sample. (suggested: Confirm that SMSF_PERSON_ABN exists in the source and carries ABNs. If it does not, drop the mapping or move the column to unmapped.)
  - [advisory] `valid_from`: The envelope valid_from equals SMSF_REG_DT (the registration date) in every example, but the config declares no valid_from. It appears to have been derived from date_registered, and the rows are Capacity or Condition rows with their own start dates. Registration date and validity of the claim may not be the same thing. (suggested: Declare valid_from explicitly, or leave it null if the source does not state when the status began.)
  - [advisory] `entity.status<-SMSF_STATUS`: The map_values transform covers only Registered and Suspended. Other raw values, such as cancelled or disqualified, would be unmapped. The suspension start and end dates are left unmapped. (suggested: Add mappings for any other values seen in the profile. Consider using the suspension dates for valid_from and valid_to when the status is suspended.)
  - [advisory] `record_id`: The register has multiple rows per auditor (Capacity and Condition attribute rows), so SMSF_NUM is not unique per row. Hash_row is acceptable, but the repeated rows produce duplicate observations for the same auditor. (suggested: Keep hash_row, or use SMSF_NUM with the attribute columns as a composite key. Note that duplicate observations will occur.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `Shirley Schaefer` → `Shirley Schaefer`; `Justin Woods` → `Justin Woods`; `Tanveer Khan` → `Tanveer Khan`
- `entity.date_registered<-SMSF_REG_DT`: `12/03/2013` → `2013-03-12`; `08/03/2013` → `2013-03-08`; `07/03/2013` → `2013-03-07`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `address.locality<-SMSF_LOCALITY`: `ADELAIDE` → `ADELAIDE`; `Sydney` → `Sydney`; `Beverly Hills` → `Beverly Hills`
- `address.postcode<-SMSF_POST_CODE`: `5000` → `5000`; `2000` → `2000`; `2209` → `2209`
- `address.state<-SMSF_STATE`: `SA` → `SA`; `NSW` → `NSW`; `QLD` → `QLD`
- `entity.abn<-SMSF_PERSON_ABN`: `55397353122` → `55397353122`; `69685464865` → `69685464865`; `74538475354` → `74538475354`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
