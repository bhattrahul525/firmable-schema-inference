# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0103, 54.99s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_01/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "tsv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
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
| 1 | `SMSF_PERSON_ABN` | `entity.abn` | abn | W | held_out | 0.90 | 96.2% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `SMSF_PERSON_ABN`: Person ABN, checksum validated; blank for most rows, so only rows with their own ABN yield an entity claim

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant label 'SMSF Auditor'
- `SMSF_NUM`: auditor number; not a business identifier and not unique per row (one auditor has several condition rows); row key is hashed
- `SMSF_NAME`: individual auditor name; rows without their own ABN are individuals with no business identifier, so the name is not emitted as an entity claim
- `SMSF_STATUS`: registration status; not emitted because the rows without an ABN are not entities
- `SMSF_REG_DT`: registration date; not emitted because the rows without an ABN are not entities (used only as valid_from)
- `SMSF_SUSP_START_DT`: suspension dates; no canonical field
- `SMSF_SUSP_END_DT`: suspension dates; no canonical field
- `SMSF_LOCALITY`: address of individual auditors; not emitted without a business identifier
- `SMSF_POST_CODE`: address of individual auditors; not emitted without a business identifier
- `SMSF_STATE`: address of individual auditors; not emitted without a business identifier
- `SMSF_ATTRIBUTE_TYPE`: row kind (condition/capacity) only
- `SMSF_CAPACITY`: auditor capacity detail; no canonical field
- `SMSF_CONDITION_NUMBER`: condition id; no canonical field
- `SMSF_CAPACITY_FIRM_NAME`: audit firm named in capacity; not the subject entity
- `SMSF_CAPACITY_START_DT`: capacity start date; event of the attribute
- `SMSF_CONDITION`: condition title; no canonical field
- `SMSF_CONDITION_DTL`: condition text; no canonical field
- `SMSF_CONDITION_START_DT`: condition start date; no canonical field

## Needs a transform the engine does not have

- none

## Checks

- ⚠️ **identifier_checksum_abn**: 2 of 52 judged values mapped to entity.abn (4%) fail the checksum. A genuine column rarely fails that often, so it may mix real identifiers with look-alikes (internal ids of the same length). About 1 in 89 look-alikes passes the checksum by chance, so some values read as valid may not be. Use a type column or a stricter pattern to keep only the real identifiers, or say why the column is kept as it is.  
  Agent's answer: *kept*: The abn transform rejects checksum failures rather than emitting them.
- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: The date, postcode, state and locality mappings and the checksum-validated ABN mapping are sound. The main problem is that every row is mapped as a business entity, although most rows are individual auditors with no ABN, so the entity claims are not supported for those rows. The remaining issues are advisory.
  - [blocking] `entity.legal_name<-SMSF_NAME`: The register lists individual approved SMSF auditors. Most rows have a blank SMSF_PERSON_ABN, and the example rows without an ABN (e.g. Bradley Donnelly, Richard Wytkin) are mapped as entity.legal_name with entity_type unknown. Rule 18 says a person-like name is an entity only when it has its own valid ABN. Rows with no business identifier belong in no_business_entities, so the source does not support treating them as business entities. (suggested: Gate the entity claims on a valid SMSF_PERSON_ABN, or route rows with no ABN to no_business_entities. Keep the address and status claims only where the row is a valid entity, and document the rule.)
  - [advisory] `record_id`: Each row is one condition attached to an auditor, so one auditor can appear on several rows. SMSF_NUM is therefore not unique per row, and hash_row=true is the correct choice. The unmapped reason for SMSF_NUM should say it is not a unique row key, so the choice is not read as a judgement about the number itself. (suggested: Keep hash_row=true. Reword the SMSF_NUM unmapped reason to say the auditor number is not unique per row and is not a business identifier.)
  - [advisory] `entity.status<-SMSF_STATUS`: The map covers only 'Registered' and 'Suspended'. The profile for the full dataset is not shown, so other status values may exist and be silently dropped. Each condition row also carries its own status, so the status claim may describe the auditor rather than the condition. (suggested: Confirm the full set of SMSF_STATUS values in the profile and map any others explicitly or leave them unmapped. Confirm the status describes the auditor's registration, not the condition.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The legal_name mapping relies on the register-holder rule (5b). The column label SMSF_NAME does not itself say registered or licensee name, so the mapping_confidence for this claim should be 0.7 or lower unless the register label is read as the holder. (suggested: Set mapping_confidence at or below 0.7 for this claim and keep the holder reason in the config.)

## Examples (raw → value, held-out rows)

- `entity.abn<-SMSF_PERSON_ABN`: `39006078326` → `39006078326`; `83188391332` → `83188391332`; `87903171422` → `87903171422`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
