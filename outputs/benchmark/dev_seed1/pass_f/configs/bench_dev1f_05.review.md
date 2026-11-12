# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `b632452fc20a…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0087, 47.33s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_05/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Licensee Name | Licence Number  | Occupation | Occupation Class | Licence Conditions/Endorsement | A.C.N | Action Type | Action Date | Action End Date | Circumstances/Reasons | Action under review by the ACAT | Period licensee can apply to ACAT for re | Applicant has applied to ACAT for review | Partnership details (Partnerships only) | Compliance with Rectification Order
2. KEGGINS INDUSTRIAL PTY LTD | 20151154 | Builder | Class B | Nil | 607 387 208 | Automatic Suspension | 25/09/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
3. Galaxy Builders Pty Ltd | 2020459 | Builder | Class C | Nil | 638 184 040 | Automatic Suspension | 26/09/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
4. Worldwide Solutions Pty Ltd | 2023658 | Electrician | Electrical Contractor | Nil | 646158581 | Automatic Suspension | 07/10/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
5. BGIS PTY LTD | 20181152 | Electrician | Unrestricted | Nil | 064 638 197 | Automatic Suspension | 17/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
6. UNITED TRADE LINKS PTY LTD | 2018832 | Builder | Class B | Nil | 152 596 337 | Automatic Suspension | 17/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
7. CAPCON DEVELOPERS PTY LTD | 20201278 | Builder | Class C | Nil | 637 391 167 | Automatic Suspension | 17/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
8. LIPACON PTY LTD | 2021186 | Builder | Class B | Nil | 626 540 065 | Automatic Suspension | 21/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
9. POLYGON ENERGY PTY LTD | 2021893 | Electrician | Electrical Contractor | Nil | 064 638 197 | Automatic Suspension | 21/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
10. FEATURE BUILDING AND DESIGN CONCEPTS PTY | 2015411 | Builder | Class B | Nil | 604 425 210 | Automatic Suspension | 27/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
11. HATTRIX HOMES PTY LTD | 20161075 | Builder | Class C | Nil | 164 235 527 | Automatic Suspension | 27/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A
12. STRUCTURE BUILDING GROUP PTY LTD | 2016557 | Builder | Class C | Nil | 611 984 180 | Automatic Suspension | 27/11/2025 | N/A | Automatic suspension under section 50A o | N/A | N/A | N/A | N/A | N/A

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | acn | W | held_out | 0.90 | 100.0% | **0.90** |
| 3 | `Licensee Name` | `entity.entity_type` | entity_type_from_suffix | W | held_out | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Labelled Licensee Name in a licensing register; the row subject is the licence holder.
2. `entity.acn` ← `A.C.N`: Column labelled A.C.N; N/A and non-9-digit values are skipped by checksum transform.
3. `entity.entity_type` ← `Licensee Name`: No explicit entity-type column; suffix rule only.

## Left unmapped (not guessed)

- `Licence Number`: Licence number has no ontology field.
- `Occupation`: Licence occupation has no ontology field.
- `Occupation Class`: Licence class has no ontology field.
- `Licence Conditions/Endorsement`: No ontology field.
- `Action Type`: Regulatory action type; describes the licence rather than the entity, no ontology field.
- `Action Date`: Date of an event (the action), not when the entity's registration or licence status started; not mapped to valid_from.
- `Action End Date`: Date of an event, not a licence start or end.
- `Circumstances/Reasons`: Free text about the action.
- `Action under review by the ACAT`: No ontology field.
- `Period licensee can apply to ACAT for review expired`: No ontology field.
- `Applicant has applied to ACAT for review and the review is incomplete`: No ontology field.
- `Partnership details (Partnerships only)`: No ontology field.
- `Compliance with Rectification Order`: No ontology field.
- `Related licensees`: No ontology field.
- `Licence Expiry Date`: Expiry of the licence, not the entity's registration; left out of valid_to to stay conservative.
- `Date stop work notice lifted`: Event date; no ontology field.
- `Reason stop work notice lifted`: Free text; no ontology field.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in the examples. Licensee Name is correctly treated as the licence holder's legal name under rule 5b, the ACN column is checksummed, and entity_type comes from the suffix rule. The remaining points are advisory: the treatment of individual licensees without a business identifier, the unmapped licence expiry date as a possible valid_to, the unmapped suspension action as a possible status, and the missing licence metadata.
  - [advisory] `entity.legal_name<-Licensee Name`: The 'EL-HELOU, Paul' row is an individual licence holder with no ABN or ACN in the row. Rule 18 treats individuals without a business identifier as no_business_entities, but the mapping still emits a legal_name and entity_type for them. Rule 4 does allow registrants to be mapped the same way, so this is a judgement call rather than a clear error. (suggested: Confirm whether individual licence holders without a business identifier should count as business entities under this dataset's rules. If not, exclude rows lacking an ABN/ACN, or record a note on the observation.)
  - [advisory] `valid_to`: 'Licence Expiry Date' is unmapped with the reason that there is no ontology field for licence validity end. Rule 10 does allow valid_to from a column stating when the entity's own licence ended, and the ontology describes valid_to as covering licence or status end. The envelope sets valid_to to null on every row, so the expiry date is discarded. (suggested: Consider mapping 'Licence Expiry Date' to valid_to (parse with dd/mm/yyyy after checking with try_transform), at least for the observation describing the licence, and state the basis. Otherwise keep it unmapped with the reason recorded.)
  - [advisory] `entity.status`: Action Type values such as 'Automatic Suspension' and 'Rectification Order' describe the licence status, and the mapping leaves status unmapped. The reason given is that the action type is not an entity status value. The status enum includes 'suspended', so some rows could support a status claim, although the source describes the licence rather than the entity. (suggested: Either keep status unmapped and state that the regulatory action describes the licence rather than the entity, or map 'Automatic Suspension' to suspended with a caveat that it refers to the licence. Do not map the other action types.)
  - [advisory] `observation.licence`: The config does not record the dataset licence, and the observation envelope requires it. The licence should be taken from CKAN metadata rather than left blank or guessed. (suggested: Add the licence from the dataset metadata, or record 'unknown' and flag it as a finding.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `PM BUILDQ GROUP PTY LTD` → `PM BUILDQ GROUP PTY LTD`; `DATAVOICE COMMUNICATIONS PTY LTD` → `DATAVOICE COMMUNICATIONS PTY LTD`; `DYNAFLOW PTY LTD` → `DYNAFLOW PTY LTD`
- `entity.acn<-A.C.N`: `646 274 633` → `646274633`; `008 624 593` → `008624593`; `008 493 178` → `008493178`
- `entity.entity_type<-Licensee Name`: `PM BUILDQ GROUP PTY LTD` → `company`; `DATAVOICE COMMUNICATIONS PTY LTD` → `company`; `DYNAFLOW PTY LTD` → `company`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
