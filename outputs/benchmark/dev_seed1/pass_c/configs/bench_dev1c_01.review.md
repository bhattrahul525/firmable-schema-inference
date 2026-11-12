# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0101, 49.16s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_01/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate: 0 hard failures, 0 rejected values on 300 held-out rows; all mapped parse rates 1.0. Critique: 0 blocking issues.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.80 | 100.0% | **0.80** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(['%d/%m/%Y']) | W | 0.95 | 100.0% | **0.95** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: Auditor's registered name on the ASIC SMSF auditor register
2. `entity.abn` ← `SMSF_PERSON_ABN`: Person ABN column, checksum validated
3. `entity.status` ← `SMSF_STATUS`: Registration status of the auditor
4. `entity.date_registered` ← `SMSF_REG_DT`: Registration date of the auditor
5. `address.locality` ← `SMSF_LOCALITY`: Locality of the auditor
6. `address.postcode` ← `SMSF_POST_CODE`: Postcode
7. `address.state` ← `SMSF_STATE`: State

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant value 'SMSF Auditor'
- `SMSF_NUM`: auditor register number; no ontology field for it
- `SMSF_SUSP_START_DT`: suspension dates; sparse, no ontology field
- `SMSF_SUSP_END_DT`: suspension dates; sparse, no ontology field
- `SMSF_ATTRIBUTE_TYPE`: row kind (condition vs capacity), not a claim field
- `SMSF_CAPACITY`: capacity role description; no ontology field
- `SMSF_CONDITION_NUMBER`: condition identifier
- `SMSF_CAPACITY_FIRM_NAME`: audit firm the auditor belongs to, a different entity from the auditor
- `SMSF_CAPACITY_START_DT`: capacity start date; not the entity registration
- `SMSF_CONDITION`: auditor condition title; no ontology field
- `SMSF_CONDITION_DTL`: condition detail text
- `SMSF_CONDITION_START_DT`: condition start date; no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in these examples: names, postcodes, states, dates and the two ABNs (both checksum-valid) sit in the right fields, and the capacity-row firm name is correctly excluded from the auditor entity. The issues are advisory: the envelope and observed_at may not match the contract, the status map has no fallback, and the registration date on capacity rows needs a clearer basis.
  - [advisory] `entity.date_registered<-SMSF_REG_DT`: On the Capacity-type row (allen jacob), SMSF_REG_DT equals SMSF_CAPACITY_START_DT (18/04/2013), and the config says capacity start is not the entity registration. The config does not explain why the registration date is trusted on capacity rows, so the date may describe the capacity appointment rather than the auditor's registration. (suggested: Document that SMSF_REG_DT is the auditor registration date on every row kind, or restrict or downgrade this mapping for SMSF_ATTRIBUTE_TYPE = Capacity rows.)
  - [advisory] `observation envelope`: The envelope shown in every example has only observed_at, valid_from and valid_to. The ontology marks source_id, source_record_id, ingested_at, licence and extractor_version as required on every record. The examples are either incomplete or the envelope is non-compliant. (suggested: Confirm the emitted records carry all required envelope fields, including the hashed source_record_id, licence from the CKAN metadata (or 'unknown' with a flag), and extractor_version.)
  - [advisory] `observed_at`: observed_at is identical (2026-11-11T19:32:11.189362) across all rows and appears to be the run time, not the resource_last_modified value the config says it comes from. The ontology says observed_at is when the source stated the claim, and that differs from ingested_at. (suggested: Set observed_at from the dataset resource_last_modified metadata and record the run time separately as ingested_at.)
  - [advisory] `entity.status<-SMSF_STATUS`: map_values covers only 'Registered' and 'Suspended'. Any other or blank value will fall through with no defined behaviour. Suspension dates are dropped, so a suspended auditor's current state is not checked against those dates. (suggested: Add an explicit fallback to 'unknown' for unmapped values, and consider using the suspension dates to set valid_from/valid_to on status observations.)
  - [advisory] `entity.abn<-SMSF_PERSON_ABN`: The ABN is correctly checksum-valid for the two rows that have one (62359460732 and 17254210398), but the auditor is a natural person. A person's ABN usually indicates a sole trader, while entity_type is set to 'unknown' on every row. The mapping does not say whether the ABN is an individual's sole-trader ABN. (suggested: Keep entity_type 'unknown' as the default, but note in the config that the ABN belongs to the individual auditor and that entity_type is not inferred from it.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: clean_whitespace leaves inconsistent casing (for example 'allen jacob' and 'FAN YANG' against 'Stephen Maher'). This is not a meaning error, but the same person may appear under different name strings across rows. (suggested: Keep the raw value, and add a separate normalised-casing field or note for matching, without changing the legal_name value.)
  - [advisory] `source_record_id (record_id hash_row)`: Each auditor appears on several rows (condition and capacity rows), and record_id is a hash of the whole row. Any change in condition text or dates produces a new record_id for the same auditor and register number, and the SMSF_NUM key is not used. (suggested: Build source_record_id from SMSF_NUM plus row kind, or document the hashing scheme so the record can be traced back to the exact raw row.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `STEPHEN HODGKINSON` → `STEPHEN HODGKINSON`; `Brian Roughley` → `Brian Roughley`; `John Nevin` → `John Nevin`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`; `Suspended` → `suspended`
- `entity.date_registered<-SMSF_REG_DT`: `07/03/2013` → `2013-03-07`; `08/03/2013` → `2013-03-08`; `12/03/2013` → `2013-03-12`
- `address.locality<-SMSF_LOCALITY`: `SOUTHPORT` → `SOUTHPORT`; `Granville` → `Granville`; `Ulladulla` → `Ulladulla`
- `address.postcode<-SMSF_POST_CODE`: `4215` → `4215`; `2142` → `2142`; `2539` → `2539`
- `address.state<-SMSF_STATE`: `QLD` → `QLD`; `NSW` → `NSW`; `VIC` → `VIC`
- `entity.abn<-SMSF_PERSON_ABN`: `12977693143` → `12977693143`; `39668632105` → `39668632105`; `29659088440` → `29659088440`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
