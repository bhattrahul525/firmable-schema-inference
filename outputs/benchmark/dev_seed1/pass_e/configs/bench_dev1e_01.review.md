# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0105, 47.28s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_01/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.90 | 100.0% | **0.90** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.80 | 100.0% | **0.80** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(%d/%m/%Y) | W | 0.85 | 100.0% | **0.85** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.90 | 100.0% | **0.90** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: Auditor's name on the ASIC register of approved auditors; individual auditor, mapped as legal name per rule 4.
2. `entity.abn` ← `SMSF_PERSON_ABN`: Column name says person ABN; 11-digit values pass checksum.
3. `entity.status` ← `SMSF_STATUS`: Register status values seen in profile (Registered, Suspended).
4. `entity.date_registered` ← `SMSF_REG_DT`: Column name says registration date.
5. `address.locality` ← `SMSF_LOCALITY`: Locality column.
6. `address.postcode` ← `SMSF_POST_CODE`: Postcode column.
7. `address.state` ← `SMSF_STATE`: State column.

## Left unmapped (not guessed)

- `SMSF_NUM`: ASIC auditor registration number; not an ACN or ABN.
- `REGISTER_NAME`: constant label 'SMSF Auditor'
- `SMSF_CAPACITY_FIRM_NAME`: audit firm the auditor is a member of; not the entity's own name
- `SMSF_ATTRIBUTE_TYPE`: row type discriminator (Condition/Capacity)
- `SMSF_CAPACITY`: capacity detail for the auditor
- `SMSF_CAPACITY_START_DT`: capacity start date
- `SMSF_CONDITION`: condition detail
- `SMSF_CONDITION_DTL`: condition long text
- `SMSF_CONDITION_NUMBER`: condition identifier
- `SMSF_CONDITION_START_DT`: condition start date
- `SMSF_SUSP_START_DT`: suspension start date; not mapped to keep claims conservative
- `SMSF_SUSP_END_DT`: suspension end date; not mapped

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in the examples. The main open question is whether SMSF_NAME is labelled as a registered name, which affects whether it can be legal_name under rule 5. The status mapping, date parsing, state and postcode mappings, and the ABN handling match the rows shown. The remaining points are advisory: the envelope valid_from choice, the duplicate condition-level rows, and the unmapped suspension dates.
  - [advisory] `entity.legal_name<-SMSF_NAME`: SMSF_NAME is not labelled as a registered, licensee or supplier name. Rule 5 maps a name to legal_name only when the data says it is the registered name. The register does list these people as approved auditors, so legal_name may be defensible under rule 4, but the mapping rests on an inference from the register's purpose rather than a stated label. (suggested: Confirm against the ASIC register field definitions that SMSF_NAME is the registered auditor name. If it is not clearly labelled that way, map it to entity.trading_name at confidence 0.6 or lower.)
  - [advisory] `entity.status<-SMSF_STATUS`: The map_values transform covers only 'Registered' and 'Suspended'. The profile may contain other status values, which would be left unmapped without comment. (suggested: Check the full distinct-value profile of SMSF_STATUS and add mappings for any other values that can be interpreted with confidence, leaving the rest unmapped.)
  - [advisory] `observation.valid_from`: The envelope sets valid_from equal to the SMSF_REG_DT registration date. Rule 10 allows valid_from only where the source states when the licence or status started. A registration date is close to that, but the envelope treats it as the start of the claim without the source saying so. (suggested: Either justify in the config that the registration date is the start of registration status, or leave valid_from null and keep the registration date only in entity.date_registered.)
  - [advisory] `record_id`: Rows are one per auditor condition, so the same auditor appears on several rows with identical entity observations. hash_row yields distinct IDs per condition row, so the same auditor's claims are duplicated. SMSF_NUM is a stable auditor identifier but is not unique per row. (suggested: Document that each row is a condition-level copy of the same auditor claims, or deduplicate observations per SMSF_NUM. Consider keeping SMSF_NUM as a traceable source key in the record ID.)
  - [advisory] `unmapped:SMSF_SUSP_START_DT, SMSF_SUSP_END_DT`: Suspension dates are left unmapped to stay conservative. The status is mapped to suspended, but when the suspension began and ended is not recorded, so a suspended claim has no time bounds. (suggested: Keep the exclusion if preferred, but note that the suspended status observation has no validity window. Alternatively map the suspension dates to valid_from and valid_to on the status observation if the source states them.)
  - [advisory] `unmapped:SMSF_CAPACITY_FIRM_NAME`: The audit firm the auditor belongs to is a real organisation that could be a related entity. It is left unmapped with a reason that is accurate but loses a possible entity link. (suggested: Keep it unmapped for now, and consider a relationship or link mapping in a later iteration.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `Alissa Hodge` → `Alissa Hodge`; `Yingshu Zhang` → `Yingshu Zhang`; `Adrian Miles` → `Adrian Miles`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `entity.date_registered<-SMSF_REG_DT`: `10/02/2016` → `2016-02-10`; `15/02/2016` → `2016-02-15`; `12/03/2013` → `2013-03-12`
- `address.locality<-SMSF_LOCALITY`: `Launceston` → `Launceston`; `Blackburn` → `Blackburn`; `Mayfield` → `Mayfield`
- `address.postcode<-SMSF_POST_CODE`: `7250` → `7250`; `3130` → `3130`; `2304` → `2304`
- `address.state<-SMSF_STATE`: `TAS` → `TAS`; `VIC` → `VIC`; `NSW` → `NSW`
- `entity.abn<-SMSF_PERSON_ABN`: `39006078326` → `39006078326`; `32128564060` → `32128564060`; `76114458058` → `76114458058`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
