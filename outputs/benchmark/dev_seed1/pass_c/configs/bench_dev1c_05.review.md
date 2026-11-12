# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0084, 41.27s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_05/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | acn | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the licensed party's name; company names carry Pty Ltd suffix; individuals are also licensees
2. `entity.acn` ← `A.C.N`: A.C.N column, checksum-validated; N/A and blanks skipped

## Left unmapped (not guessed)

- `Licence Number`: licence identifier issued by regulator, not an ABN/ACN/NZBN
- `Occupation`: licence occupation category (Builder/Electrician), not ANZSIC
- `Occupation Class`: licence class, not an industry code
- `Licence Conditions/Endorsement`: licence conditions text
- `Action Type`: regulatory action type, not entity status
- `Action Date`: action date; not applied as valid_from because it describes the regulatory action, not when the name or ACN became true
- `Action End Date`: mostly N/A; not mapped to valid_to in this version
- `Circumstances/Reasons`: free-text reasons for the action
- `Action under review by the ACAT`: review status flag, no canonical field
- `Period licensee can apply to ACAT for review expired`: review status flag, no canonical field
- `Applicant has applied to ACAT for review and the review is incomplete`: review status flag, no canonical field
- `Partnership details (Partnerships only)`: no canonical field for partnership details
- `Compliance with Rectification Order`: no canonical field
- `Related licensees`: no canonical field
- `Licence Expiry Date`: licence expiry, not an entity field; mostly blank
- `Date stop work notice lifted`: no canonical field
- `Reason stop work notice lifted`: no canonical field

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `observation.valid_to`: Action End Date is mostly N/A; not mapped in this version.

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The ACN checksum mapping is sound on the rows checked (638 184 040 and 088 384 427 both validate), and Action Type is correctly kept out of status. The main meaning error is the envelope's valid_from being applied to name and ACN observations, which the source does not support. The remaining points are advisory: the default entity_type observation, unparsed individual names, an unused Action End Date, and an incomplete envelope in the examples.
  - [blocking] `observation.valid_from`: The envelope applies valid_from (the regulatory Action Date) to every observation, including entity.legal_name and entity.acn. The action date is when the licence action took effect, not when the registered legal name or ACN became true. For example, 'Galaxy Builders Pty Ltd' gets valid_from 2025-09-26 because of a suspension, which the source does not support. (suggested: Set valid_from only on observations that describe the regulatory action. Leave valid_from null on entity.legal_name and entity.acn, or source it from a field that actually states when the name or ACN took effect.)
  - [advisory] `entity.entity_type`: An entity_type 'unknown' observation is emitted for every row with from: null, so it has no source field. The 'Occupation' and 'Occupation Class' columns do not state entity type, so this is a default rather than a source claim, and it adds an observation the source never made. (suggested: Either omit the default observation or mark it explicitly as a system default (derivation_level L1 with no source) so it is not read as a sourced claim.)
  - [advisory] `entity.legal_name<-Licensee Name`: Individual licensees such as 'AZZI, Daniel' and 'SACCHINELLI, Gregorio' are mapped to legal_name in 'Surname, Given' form with no normalisation. The config's own reason says individuals are licensees, so the field holds a person's name, not a registered company name. (suggested: Keep the raw value, but add a parsing step or note that individual names are not registered legal names, and consider a separate handling path for sole traders.)
  - [advisory] `observation.valid_to`: valid_to is always null, yet several rows carry an Action End Date (for example EDGE PLUMBING ACT PTY LTD, end 10/03/2026, and AZZI, Daniel, end 19/11/2025). The config says these are not safely parseable, but the values in the examples are plain dd/mm/yyyy dates. (suggested: Parse Action End Date where it is a valid date and map it to valid_to on the action observation, keeping N/A as null. Record the parsing as an L1 derivation.)
  - [advisory] `observation`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible, so the envelope cannot be checked against the ontology's required list. (suggested: Show a complete envelope in the examples. Confirm licence is taken from the CKAN metadata, and that source_record_id is the documented row hash.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `Galaxy Builders Pty Ltd` → `Galaxy Builders Pty Ltd`; `BGIS PTY LTD` → `BGIS PTY LTD`; `LIPACON PTY LTD` → `LIPACON PTY LTD`
- `entity.acn<-A.C.N`: `638 184 040` → `638184040`; `064 638 197` → `064638197`; `626 540 065` → `626540065`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
