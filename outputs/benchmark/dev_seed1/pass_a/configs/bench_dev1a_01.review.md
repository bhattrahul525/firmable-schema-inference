# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0092, 48.36s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_01/trace.jsonl`.
- Evidence the agent gave at finish (its words): Read 28,048 rows, 19 TSV columns; validate: 0 hard failures, 100% parse on mapped fields, 0 rejected values on 300 held-out rows. Profile: SMSF_STATUS = Registered/Suspended only; SMSF_PERSON_ABN 16% filled, all 11-digit.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.85 | 100.0% | **0.85** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(%d/%m/%Y) | W | 0.90 | 100.0% | **0.90** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: Name of the registered SMSF auditor (person or individual auditor).
2. `entity.abn` ← `SMSF_PERSON_ABN`: Column named person ABN, 11-digit values.
3. `entity.status` ← `SMSF_STATUS`: Register status of the auditor; 'Registered' read as active.
4. `entity.date_registered` ← `SMSF_REG_DT`: Registration date of the auditor on the register.
5. `address.locality` ← `SMSF_LOCALITY`: Locality.
6. `address.postcode` ← `SMSF_POST_CODE`: Postcode.
7. `address.state` ← `SMSF_STATE`: State.

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant value
- `SMSF_NUM`: ASIC auditor number; no ontology field for it
- `SMSF_SUSP_START_DT`: suspension dates, sparse; not mapped to valid_from/valid_to to stay conservative
- `SMSF_SUSP_END_DT`: suspension dates, sparse
- `SMSF_ATTRIBUTE_TYPE`: row type indicator (Condition or Capacity)
- `SMSF_CAPACITY`: role of auditor within audit firm; no ontology field
- `SMSF_CAPACITY_FIRM_NAME`: audit firm the auditor belongs to; a related entity, not the row's entity
- `SMSF_CAPACITY_START_DT`: capacity start date; no ontology field
- `SMSF_CONDITION_NUMBER`: condition identifier
- `SMSF_CONDITION`: condition text; not an ontology field
- `SMSF_CONDITION_DTL`: condition detail text
- `SMSF_CONDITION_START_DT`: condition start date; no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: the value transforms, the state, postcode and date parsing, and the default unknown entity_type look right. The main concern is that the observation envelope is incomplete, since required fields such as source_id, source_record_id, ingested_at, licence and extractor_version are absent and observed_at does not follow the configured metadata source. There is no clear case where a value sits in the wrong field, so no field needs removing, but several meaning-level caveats (person name as legal_name, the reading of 'Registered' as active, the unexercised ABN mapping) should be documented.
  - [blocking] `observation envelope`: The envelope shows only observed_at, valid_from and valid_to. The ontology requires source_id, source_record_id, ingested_at, licence and extractor_version on every record, and none of them appear. The observed_at value is identical across all ten rows and looks like the ingest time, not the resource_last_modified value the config specifies. (suggested: Emit the full required envelope on every record: source_id, a deterministic source_record_id (the row hash, or SMSF_NUM plus attribute type plus condition or capacity number), observed_at from resource_last_modified, ingested_at as the read time, the dataset licence (or 'unknown' with a flag), and extractor_version.)
  - [advisory] `entity.status<-SMSF_STATUS`: The source value 'Registered' is an auditor-register status meaning approved to audit. Mapping it to 'active' is a reasonable reading but is an interpretation the source does not state literally. (suggested: Keep the mapping but record in the config reason that 'Registered' on the ASIC auditor register is read as active, and consider deriving it at derivation_level L1 rather than L0.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The source names a natural person (individual auditor), not a registered legal entity. Mapping the person's name to legal_name is defensible but may mislead downstream entity matching. (suggested: Note in the config that SMSF_NAME is a person's name, and check that downstream logic treats it as an individual rather than a company legal name.)
  - [advisory] `entity.entity_type`: Every row defaults to 'unknown' even though the source clearly describes individual auditors. The default is conservative, but the config does not record that the source does state individual status. (suggested: Keep 'unknown' as the default, but record in the observation or config reason that the source describes individual auditors, so a later step can justify a sole_trader or other value.)
  - [advisory] `entity.abn<-SMSF_PERSON_ABN`: The config maps an ABN column that does not appear in any of the example raw rows, so the transform is not exercised here and no abn observation is shown. The ABN also belongs to the person, which may not match the entity the other fields describe. (suggested: Show an example row that contains SMSF_PERSON_ABN, confirm the checksum validation runs, and document that the ABN is the individual's ABN.)
  - [advisory] `entity.date_registered<-SMSF_REG_DT`: The registration date is the date of registration on the auditor register. The ontology has a valid_from field for when a claim became true, and this date could populate it, but valid_from is null in every envelope. (suggested: Consider setting observation valid_from to the registration date, or state explicitly in the config why it is kept only as date_registered.)
  - [advisory] `entity.legal_name<-SMSF_NAME (Capacity rows)`: For Capacity-type rows (e.g. Mark Carusi, Daniel Tai), the status and registration fields describe the auditor's register entry, but the row is about a capacity within a firm. The firm named in SMSF_CAPACITY_FIRM_NAME is correctly left unmapped, but the observations do not show that the row type was considered. (suggested: Confirm that status and date claims on Capacity rows refer to the individual's registration, and record the SMSF_ATTRIBUTE_TYPE value in the observation context.)
  - [advisory] `observation source_record_id`: SMSF_NUM is the ASIC auditor number, a stable identifier for the person, but it is listed as unmapped and is not used for source_record_id. The config uses a row hash, which changes whenever any text in the row changes. (suggested: Use SMSF_NUM (with attribute type and condition or capacity number) to build a deterministic source_record_id, and keep the row hash as a fallback.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `Robert Austin` → `Robert Austin`; `Darren Johnson` → `Darren Johnson`; `Tanveer Khan` → `Tanveer Khan`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `entity.date_registered<-SMSF_REG_DT`: `29/08/2016` → `2016-08-29`; `12/03/2013` → `2013-03-12`; `08/03/2013` → `2013-03-08`
- `address.locality<-SMSF_LOCALITY`: `Belconnen` → `Belconnen`; `Port Macquarie` → `Port Macquarie`; `Beverly Hills` → `Beverly Hills`
- `address.postcode<-SMSF_POST_CODE`: `2617` → `2617`; `2444` → `2444`; `2209` → `2209`
- `address.state<-SMSF_STATE`: `ACT` → `ACT`; `NSW` → `NSW`; `SA` → `SA`
- `entity.abn<-SMSF_PERSON_ABN`: `17213240587` → `17213240587`; `83605057998` → `83605057998`; `55397353122` → `55397353122`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
