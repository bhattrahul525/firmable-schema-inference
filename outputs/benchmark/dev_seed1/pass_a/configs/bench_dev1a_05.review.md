# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 14 model turns, 14 tool calls, $0.0105, 47.82s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_05/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | acn | W | 0.95 | 99.3% | **0.95** |
| 3 | `Licensee Name` | `entity.entity_type` | entity_type_from_suffix | W | 0.70 | 100.0% | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the licensee's name on the register
2. `entity.acn` ← `A.C.N`: A.C.N column, checksummed; N/A values are skipped
3. `entity.entity_type` ← `Licensee Name`: No explicit entity-type column; suffix rule on name

## Left unmapped (not guessed)

- `Licence Number`: Licence number of the individual licence; no ontology field
- `Occupation`: Trade licence category, not an ANZSIC industry code
- `Occupation Class`: Licence class, no ontology field
- `Licence Conditions/Endorsement`: Licence condition detail, no ontology field
- `Action Type`: Regulatory action type; licence suspensions kept as regulatory actions, not entity.status
- `Action Date`: Used as valid_from (date the regulatory action took effect)
- `Action End Date`: Used as valid_to
- `Circumstances/Reasons`: Free-text reasons; no ontology field
- `Action under review by the ACAT`: Review status, no ontology field
- `Period licensee can apply to ACAT for review expired`: Review status, no ontology field
- `Applicant has applied to ACAT for review and the review is incomplete`: Review status, no ontology field
- `Partnership details (Partnerships only)`: Mostly N/A; no ontology field
- `Compliance with Rectification Order`: Compliance detail, no ontology field
- `Related licensees`: Related persons/directors text, no ontology field
- `Licence Expiry Date`: Licence expiry, not the action validity; no ontology field
- `Date stop work notice lifted`: Not in ontology
- `Reason stop work notice lifted`: Not in ontology

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in the examples: legal names, ACNs and entity types match their source columns, and the N/A and individual-name cases are handled correctly. The remaining points are advisory, mainly the incomplete envelope, the observed_at source, the missing derivation level, and the use of Action Date as valid_from.
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The ontology marks source_id, source_record_id, ingested_at, licence and extractor_version as required on every record, and none appear in the examples. (suggested: Confirm the emitted records carry all required envelope fields, and show them in the examples: source_id, source_record_id (from the hash_row key), ingested_at, licence (from CKAN metadata, or 'unknown' with a flag) and extractor_version.)
  - [advisory] `observed_at`: The config takes observed_at from resource_last_modified, but every example shows the same timestamp, 2026-09-30T16:25:43.332780, which looks like the run time rather than the metadata date. (suggested: Check that observed_at is populated from resource_last_modified and that ingested_at is recorded separately as the read time.)
  - [advisory] `entity.entity_type<-Licensee Name`: Company types are inferred from the 'Pty Ltd' suffix, which is a deterministic L1 derivation, but the examples do not record a derivation_level. 'Jason Harwood' and 'Morris Construction Corporation' correctly come out as unknown. (suggested: Record derivation_level L1 for suffix-derived entity_type values and keep unknown as the default for names without a recognised suffix.)
  - [advisory] `valid_from<-Action Date`: Action Date is the date a regulatory action was taken, not the date a status became true in the world. It is used as valid_from for the suspension and rectification observations, so these observations are timed by the regulator's action rather than by any stated status change. (suggested: Keep Action Date as valid_from only if you treat it as the date the regulatory claim took effect, and say so in the mapping notes. Otherwise leave valid_from empty for these records.)
  - [advisory] `entity.status`: Action Type 'Automatic Suspension' is not mapped to entity.status, so these suspension records give no status observation even though the source states a suspension. The licence suspension is a licence action, not necessarily an entity status, so leaving status unmapped is defensible. (suggested: Keep status unmapped unless the source defines a link to the entity status, and note in the mapping that licence suspensions are kept as an unmapped regulatory action rather than entity status.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `Worldwide Solutions Pty Ltd` → `Worldwide Solutions Pty Ltd`; `UNITED TRADE LINKS PTY LTD` → `UNITED TRADE LINKS PTY LTD`; `LIPACON PTY LTD` → `LIPACON PTY LTD`
- `entity.acn<-A.C.N`: `646158581` → `646158581`; `152 596 337` → `152596337`; `626 540 065` → `626540065`
- `entity.entity_type<-Licensee Name`: `Worldwide Solutions Pty Ltd` → `company`; `UNITED TRADE LINKS PTY LTD` → `company`; `LIPACON PTY LTD` → `company`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
