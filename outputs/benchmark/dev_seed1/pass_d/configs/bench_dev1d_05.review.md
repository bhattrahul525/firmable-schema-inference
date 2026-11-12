# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 13 model turns, 13 tool calls, $0.0099, 47.05s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1d_05/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate: 0 hard failures, 0 unaccounted columns, 534 observations, 0 rejected values on 196 held-out rows. Critique: 3 advisory issues, 0 blocking; valid_from/valid_to accounting and the status note were addressed in unmapped reasons. Licence in source is unknown (flagged).

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | acn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Licensee Name` | `entity.entity_type` | entity_type_from_suffix | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the licensee's name on the register; treated as the registered/licensee name per rule 5
2. `entity.acn` ← `A.C.N`: A.C.N column holds 9-digit company numbers (some with spaces); checksum-validated
3. `entity.entity_type` ← `Licensee Name`: No explicit entity-type column; suffix rule on the name

## Left unmapped (not guessed)

- `Licence Number`: licence number has no ontology field
- `Occupation`: licence occupation (Builder/Electrician), not an industry code
- `Occupation Class`: licence class, no ontology field
- `Licence Conditions/Endorsement`: licence conditions, no ontology field
- `Action Type`: regulatory action type; licence suspension is a licence-level regulatory state, not an entity status claim, so not mapped to entity.status
- `Action Date`: used for valid_from: the start date of the licence action (not the licence start)
- `Action End Date`: used for valid_to via regex extract; N/A and blanks become null
- `Circumstances/Reasons`: free-text reasons, no ontology field
- `Action under review by the ACAT`: regulatory review flag, no ontology field
- `Period licensee can apply to ACAT for review expired`: regulatory flag, no ontology field
- `Applicant has applied to ACAT for review and the review is incomplete`: regulatory flag, no ontology field
- `Partnership details (Partnerships only)`: mostly N/A, no ontology field
- `Compliance with Rectification Order`: regulatory flag, no ontology field
- `Related licensees`: names of individuals related to the licensee; not mapped
- `Licence Expiry Date`: licence expiry, no ontology field
- `Date stop work notice lifted`: no ontology field
- `Reason stop work notice lifted`: no ontology field

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.status`: Action Type describes licence actions, not entity status
- `entity.industry_code`: Occupation is a licence occupation, not an industry code

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The core name, ACN and entity_type mappings are consistent with rules 5, 6 and 7: the suffix-based entity_type returns company for PTY LTD names and unknown for person names and names without a suffix, and ACN is checksum-validated with N/A values dropped. The main gap is the date handling. The envelope valid_from and valid_to values come from Action Date and Action End Date, but the config neither maps them nor accounts for Action Date, and the unmapped reason for Action End Date is inconsistent with the config. No blocking meaning errors are visible in the examples.
  - [advisory] `valid_from`: The emitted envelope sets valid_from from the Action Date column (e.g. Galaxy Builders 2025-09-26), but the config has no fields entry or transform for it, and Action Date is not listed in unmapped. Rule 3 requires every column to be accounted for, and the emitted date has no config trace. (suggested: Add an explicit valid_from mapping from Action Date with parse_date '%d/%m/%Y' (confirm with try_transform), or list Action Date in unmapped with a reason. Note that it dates a licence action, so describe valid_from as the action start, not the licence start.)
  - [advisory] `valid_to`: The unmapped entry for Action End Date says 'used for valid_to', but no valid_to mapping appears in fields. The envelope still emits valid_to (e.g. Jensen Hughes 2026-03-26), so the config and the output disagree. (suggested: Either add a parse_date mapping from Action End Date to valid_to (with 'N/A' treated as null) or correct the unmapped reason. Keep the N/A-to-null handling explicit.)
  - [advisory] `entity.status`: Action Type values such as 'Automatic Suspension' and 'Suspension' describe a licence action, and the config correctly declines to map them to entity.status. The config does not explain that the current licence state is therefore not captured anywhere, which may hide a useful claim. (suggested: Keep entity.status unmapped, but record in the config notes that licence suspension is a licence-level regulatory state and is not an entity status claim. Consider a separate licence-status field if the ontology adds one.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `Galaxy Builders Pty Ltd` → `Galaxy Builders Pty Ltd`; `Worldwide Solutions Pty Ltd` → `Worldwide Solutions Pty Ltd`; `UNITED TRADE LINKS PTY LTD` → `UNITED TRADE LINKS PTY LTD`
- `entity.acn<-A.C.N`: `638 184 040` → `638184040`; `646158581` → `646158581`; `152 596 337` → `152596337`
- `entity.entity_type<-Licensee Name`: `Galaxy Builders Pty Ltd` → `company`; `Worldwide Solutions Pty Ltd` → `company`; `UNITED TRADE LINKS PTY LTD` → `company`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
