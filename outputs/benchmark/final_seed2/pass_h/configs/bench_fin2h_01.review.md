# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Self-Managed Super Fund Auditor Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `smsf_auditor_202611.csv` (sha256 `f0ea51dddf54…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0098, 44.58s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_01/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

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
| 1 | `SMSF_PERSON_ABN` | `entity.abn` | abn [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.95 | 100.0% | **0.95** |
| 2 | `SMSF_NAME` | `entity.legal_name` | clean_whitespace [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.60 | 100.0% | **0.60** |
| 3 | `SMSF_STATUS` | `entity.status` | map_values({'Registered': 'active', 'Suspended': 'suspended'}) [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.85 | 100.0% | **0.85** |
| 4 | `SMSF_REG_DT` | `entity.date_registered` | parse_date(['%d/%m/%Y']) [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.80 | 100.0% | **0.80** |
| 5 | `SMSF_LOCALITY` | `address.locality` | clean_whitespace [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `SMSF_POST_CODE` | `address.postcode` | postcode [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.90 | 100.0% | **0.90** |
| 7 | `SMSF_STATE` | `address.state` | state_code [when {"column": "SMSF_PERSON_ABN", "matches": "^\\d{11}$"}] | P | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `SMSF_PERSON_ABN`: Column holds the auditor's own 11-digit ABN, checksum validated; blank for most rows.
2. `entity.legal_name` ← `SMSF_NAME`: Under rule 5b: name of the individual who holds the ASIC SMSF auditor approval. No explicit registered-name label. Restricted to rows with their own ABN because rule 18 only treats individuals with a business identifier as entities.
3. `entity.status` ← `SMSF_STATUS`: Registration status of the auditor on the register.
4. `entity.date_registered` ← `SMSF_REG_DT`: Date the auditor was registered on the register.
5. `address.locality` ← `SMSF_LOCALITY`: Locality of the auditor.
6. `address.postcode` ← `SMSF_POST_CODE`: Postcode of the auditor.
7. `address.state` ← `SMSF_STATE`: State of the auditor.

## Left unmapped (not guessed)

- `REGISTER_NAME`: Constant 'SMSF Auditor'.
- `SMSF_NUM`: ASIC auditor registration number, not an ABN/ACN; no ontology field.
- `SMSF_SUSP_START_DT`: Suspension dates apply to suspension events, not to the entity's registration start.
- `SMSF_SUSP_END_DT`: Suspension end date; not a registration start/end.
- `SMSF_ATTRIBUTE_TYPE`: Register line type (Condition/Capacity).
- `SMSF_CAPACITY`: Auditor capacity detail; no ontology field.
- `SMSF_CONDITION_NUMBER`: Condition identifier; no ontology field.
- `SMSF_CAPACITY_FIRM_NAME`: Audit firm name the auditor is a partner of; not the registered name of the holder.
- `SMSF_CAPACITY_START_DT`: Capacity start date; event not entity start.
- `SMSF_CONDITION`: Condition text; no ontology field.
- `SMSF_CONDITION_DTL`: Condition detail text; no ontology field.
- `SMSF_CONDITION_START_DT`: Condition start date; not entity start.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 28048, 'key': 'hash_row', 'duplicate_rows': 24, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in the examples: the column-to-field mappings for name, ABN, status, registration date and address match their source labels, and unmapped columns are correctly excluded. The remaining points are advisory: the rule 5b confidence cap is not recorded, the ABN-only restriction on the name is unexplained, and entity observations repeat across condition rows.
  - [advisory] `entity.legal_name<-SMSF_NAME`: Under rule 5b the name is the register holder's name, but the config gives no mapping_confidence. Without an explicit registered-name label, rule 5b caps confidence at 0.7 or lower, and the config does not show that cap. (suggested: Set mapping_confidence to 0.7 or lower for entity.legal_name<-SMSF_NAME and state in the reason that the name is the approval holder's name under rule 5b.)
  - [advisory] `entity.legal_name<-SMSF_NAME`: The `when` clause restricts the legal name to rows with a valid 11-digit SMSF_PERSON_ABN. The register subject is the auditor whether or not an ABN is present, so auditors without an ABN lose their name with no stated reason. (suggested: Either justify the ABN restriction in the reason or map the name on every row that has a SMSF_NAME, keeping the abn field restricted to ABN rows.)
  - [advisory] `record_id`: Each auditor has one row per condition or capacity line, and the entity-level columns repeat on each. The Yibo Wang example yields two rows with identical entity observations (abn, legal_name, status, date_registered, address), so the same claim is emitted more than once. (suggested: Consider deduplicating entity-level observations on SMSF_NUM or SMSF_PERSON_ABN, or document that repeated rows are intentional, so the same claim is not counted twice.)

## Examples (raw → value, held-out rows)

- `entity.abn<-SMSF_PERSON_ABN`: `12977693143` → `12977693143`; `39668632105` → `39668632105`; `70204225185` → `70204225185`
- `entity.legal_name<-SMSF_NAME`: `FAIZAL AJMAT` → `FAIZAL AJMAT`; `joanna kunicka` → `joanna kunicka`; `Jeffrey McKee` → `Jeffrey McKee`
- `entity.status<-SMSF_STATUS`: `Registered` → `active`
- `entity.date_registered<-SMSF_REG_DT`: `08/04/2013` → `2013-04-08`; `03/12/2014` → `2014-12-03`; `09/04/2013` → `2013-04-09`
- `address.locality<-SMSF_LOCALITY`: `Sydney` → `Sydney`; `Mount Gravatt East` → `Mount Gravatt East`; `Castle Hill` → `Castle Hill`
- `address.postcode<-SMSF_POST_CODE`: `2000` → `2000`; `4122` → `4122`; `2154` → `2154`
- `address.state<-SMSF_STATE`: `NSW` → `NSW`; `QLD` → `QLD`; `VIC` → `VIC`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
