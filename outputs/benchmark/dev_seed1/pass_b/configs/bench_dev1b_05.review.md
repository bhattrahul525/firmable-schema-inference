# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 12 model turns, 12 tool calls, $0.0093, 49.34s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_05/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate call 2: 0 hard failures, parse rate 100% legal_name and 99.3% ACN; the full-row record hash has 1 duplicate row in 393. Critique: 0 blocking issues.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | acn | W | 0.95 | 99.3% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the licensee on the construction licence; registered-style names for companies and individuals.
2. `entity.acn` ← `A.C.N`: Column is labelled A.C.N and holds 9-digit values; N/A values are skipped by the checksum transform.

## Left unmapped (not guessed)

- `Licence Number`: Licence number of the occupation licence; no canonical field for it.
- `Occupation`: Licence occupation type; no canonical classification field.
- `Occupation Class`: Licence class; no canonical field.
- `Licence Conditions/Endorsement`: Licence conditions; no canonical field.
- `Action Type`: Type of regulatory action; not an entity status, so not mapped to entity.status.
- `Action Date`: Date of the regulatory action; not a registration or licence-validity date, so not mapped to valid_from.
- `Action End Date`: End date of the action; not mapped.
- `Circumstances/Reasons`: Free-text reasons for the action; no canonical field.
- `Action under review by the ACAT`: Review status; no canonical field.
- `Period licensee can apply to ACAT for review expired`: Review status; no canonical field.
- `Applicant has applied to ACAT for review and the review is incomplete`: Review status; no canonical field.
- `Partnership details (Partnerships only)`: Partnership detail; no canonical field.
- `Compliance with Rectification Order`: Compliance detail; no canonical field.
- `Related licensees`: Related persons; no canonical field.
- `Licence Expiry Date`: Licence expiry; not mapped.
- `Date stop work notice lifted`: Stop work notice detail; not mapped.
- `Reason stop work notice lifted`: Stop work notice detail; not mapped.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible. The ACN and legal name mappings are supported by the rows shown, and the unmapped regulatory fields are correctly excluded from status and valid_from. The remaining points are advisory: individual licensees under legal_name, a conservative entity_type that could be derived from the Pty Ltd suffix, an observed_at value that may be the ingest time, and an envelope that is not fully shown.
  - [advisory] `entity.legal_name<-Licensee Name`: Licensee Name is used as legal_name for rows that are individuals, not companies (e.g. 'ASSI, Mohamad Baker' and 'Jason Harwood'). The ontology says legal_name is the registered name, and a person's licence name is not a registered entity name. The 'ASSI, Mohamad Baker' row also keeps the surname-first order from the source. (suggested: Keep the mapping, since the name is what the licensee is called, but document that the column mixes companies and individuals. Consider a note or a separate observation flag for individual licensees, and do not let the name imply an entity type.)
  - [advisory] `entity.entity_type`: Every example is emitted as 'unknown', which is the conservative default. Some rows do support a more specific value at L1 from the source text: 'PTY LTD' or 'PTY LIMITED' in the name, and 'The company was automatically suspended' in Circumstances/Reasons (e.g. DETLEV'S ELECTRICAL, Fortun8, Five Rivers). Individual names are consistent with sole_trader but do not establish it. (suggested: Optionally derive entity_type=company at derivation_level L1 from the Pty Ltd/Limited suffix and the 'company was suspended' wording. Leave individuals as unknown. Being richer here is optional; the current output is not wrong.)
  - [advisory] `observed_at`: The config sets observed_at from resource_last_modified, but the envelope shows the same ingest-like timestamp (2026-09-30T16:25:43.332780) on every record. That looks like the time of reading, not the time the source stated it. (suggested: Confirm that resource_last_modified is actually being read, and check that the envelope value is not the ingested_at value copied into observed_at.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible. record_id uses hash_row, which is deterministic but depends on row position and is not documented. (suggested: Show the full envelope in the examples. Document how source_record_id is built from the row hash, and confirm that the licence comes from the CKAN metadata or is recorded as 'unknown' and flagged.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `CAPCON DEVELOPERS PTY LTD` → `CAPCON DEVELOPERS PTY LTD`; `LIPACON PTY LTD` → `LIPACON PTY LTD`; `FEATURE BUILDING AND DESIGN CONCEPTS PTY LTD` → `FEATURE BUILDING AND DESIGN CONCEPTS PTY LTD`
- `entity.acn<-A.C.N`: `637 391 167` → `637391167`; `626 540 065` → `626540065`; `604 425 210` → `604425210`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
