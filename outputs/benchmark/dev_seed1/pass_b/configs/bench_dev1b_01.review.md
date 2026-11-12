# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0100, 50.67s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_01/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validate call 2: 0 structural errors, 28,048 rows, 24 duplicate hash rows, ABN parse rate 0.979, all other fields 1.0. Critique: 4 advisory issues, 0 blocking (envelope fields are added downstream; entity_type default; status interpretation; personal-name legal_name noted).
- Reason: The file is a tab-delimited ASIC register of approved SMSF auditors in long format (one row per condition/capacity). Auditor identity, ABN, status, registration date and address are mapped; condition and firm-capacity columns are unmapped.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | 0.95 | 97.9% | **0.95** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) | W | 0.85 | 100.0% | **0.85** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(%d/%m/%Y) | W | 0.90 | 100.0% | **0.90** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |
| 7 | `SMSF_STATE` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SMSF_NAME`: Registered auditor name in the register; individual names, not trading names
2. `entity.abn` ← `SMSF_PERSON_ABN`: Person ABN, checksum-validated
3. `entity.status` ← `SMSF_STATUS`: Registration status of the auditor
4. `entity.date_registered` ← `SMSF_REG_DT`: Registration date of the auditor
5. `address.locality` ← `SMSF_LOCALITY`: Locality
6. `address.postcode` ← `SMSF_POST_CODE`: Postcode
7. `address.state` ← `SMSF_STATE`: State

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant value 'SMSF Auditor'
- `SMSF_NUM`: ASIC auditor registration number; no ontology field for it
- `SMSF_ATTRIBUTE_TYPE`: row type indicator (Condition/Capacity)
- `SMSF_CAPACITY`: role of auditor in audit firm; no ontology field
- `SMSF_CAPACITY_FIRM_NAME`: audit firm the auditor is linked to; not the registered name of the entity
- `SMSF_CAPACITY_START_DT`: start of capacity; no ontology field
- `SMSF_CONDITION_NUMBER`: condition identifier
- `SMSF_CONDITION`: condition text; no ontology field
- `SMSF_CONDITION_DTL`: condition detail text; no ontology field
- `SMSF_CONDITION_START_DT`: condition start date; no ontology field
- `SMSF_SUSP_START_DT`: suspension start; sparse, not mapped
- `SMSF_SUSP_END_DT`: suspension end; sparse, not mapped

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.entity_type`: No explicit source column; rows are individual auditors, so the engine records unknown. Not mapped.
- `valid_from/valid_to`: SMSF_REG_DT is registration date, not a stated licence start for the claim; left out conservatively.

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: The core field mappings are largely sound: the ABN 66062870868 passes the ABN checksum, the state, postcode and date parse look right, and the unmapped capacity and condition columns are correctly left out. The problems are mostly advisory: the envelope is incomplete, entity_type 'unknown' is emitted without a source, and the status and legal_name mappings need documentation of their interpretation. I found no value placed in a field it does not mean, so no blocking issues.
  - [advisory] `observation envelope`: Every example envelope shows only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are absent from the emitted observations, although the ontology says every record carries them. (suggested: Confirm these fields are added downstream of the examples, or emit them in the observations. Set licence to the CKAN metadata value or 'unknown' with a flag, and check that observed_at comes from resource_last_modified as configured.)
  - [advisory] `entity.entity_type`: Each example emits entity_type 'unknown' with from: null. No source field supports it, so this is a default written as an observation rather than a claim the source made. The rows are individual auditors, so the source does not say whether the registered entity is a person, a sole trader or something else. (suggested: Do not emit a sourceless entity_type observation. If a default is needed, keep it out of the observation stream or mark it as a default with derivation_level L1 and no source value.)
  - [advisory] `entity.status<-SMSF_STATUS`: The source value 'Registered' is mapped to 'active'. The register says the auditor is registered, which is close to active but is not the same claim. The mapping also has no entry for deregistered or other values the register may hold. (suggested: Keep the mapping but note the interpretation, or record the raw value alongside it. Add explicit handling for other status values, or route unmapped values to 'unknown' and flag them.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The source is an individual auditor's personal name, not a registered company or entity name. Storing it as legal_name is defensible, but the ontology's legal_name note assumes a registered entity, and the mapping does not record that the subject is a person. (suggested: Keep the mapping, and add a note in the config that SMSF_NAME is the auditor's personal name. Consider whether the entity type should be recorded as a person-type claim rather than left unknown.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SMSF_NAME`: `Yingshu Zhang` → `Yingshu Zhang`; `Andrew Tripepi` → `Andrew Tripepi`; `Gavin Ma` → `Gavin Ma`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `entity.date_registered<-SMSF_REG_DT`: `15/02/2016` → `2016-02-15`; `12/03/2013` → `2013-03-12`; `08/03/2013` → `2013-03-08`
- `address.locality<-SMSF_LOCALITY`: `Blackburn` → `Blackburn`; `Essendon` → `Essendon`; `Bentleigh` → `Bentleigh`
- `address.postcode<-SMSF_POST_CODE`: `3130` → `3130`; `3040` → `3040`; `3204` → `3204`
- `address.state<-SMSF_STATE`: `VIC` → `VIC`; `NSW` → `NSW`; `TAS` → `TAS`
- `entity.abn<-SMSF_PERSON_ABN`: `53269837610` → `53269837610`; `12885627916` → `12885627916`; `31812454513` → `31812454513`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
