# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0968, 30.29s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1t_05/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 2 | `A.C.N` | `entity.acn` | regex_extract(^(\d{3} ?\d{3} ?\d{3})$) → acn | W | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: licensee name
2. `entity.acn` ← `A.C.N`: ACN

## Left unmapped (not guessed)

- `Licence Number`: licence id, not an entity field
- `Occupation`: not industry code
- `Occupation Class`: licence class
- `Licence Conditions/Endorsement`: conditions
- `Action Type`: action
- `Circumstances/Reasons`: free text
- `Action under review by the ACAT`: review
- `Period licensee can apply to ACAT for review expired`: review
- `Applicant has applied to ACAT for review and the review is incomplete`: review
- `Partnership details (Partnerships only)`: free text
- `Compliance with Rectification Order`: compliance
- `Related licensees`: related
- `Licence Expiry Date`: licence expiry
- `Date stop work notice lifted`: event
- `Reason stop work notice lifted`: event

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The mapping is sound. Licensee Name maps to legal_name, including individuals, as rule 4 requires, and ACN is checksum-validated through the acn transform. No blocking meaning errors are visible. The advisory items cover the undocumented valid_from/valid_to mapping, the unused entity_type_from_suffix, and the unmapped Action Type.
  - [advisory] `valid_from/valid_to (Action Date, Action End Date)`: The envelope carries valid_from and valid_to taken from Action Date and Action End Date, but the config shown has no entry for them and does not list those columns as unmapped. The dates are in the output, so they are accounted for somewhere, but the config does not document the mapping. For a suspension or condition they describe the action period, not the licence or entity status. (suggested: Declare valid_from and valid_to explicitly in the config with parse_date format %d/%m/%Y. Note that they describe the disciplinary action period, not the entity's registration.)
  - [advisory] `entity.acn<-A.C.N`: The regex requires the ACN to be 9 digits in the form 'ddd ddd ddd' or unspaced. Placeholder values such as 'N/A' and 'Nil' are dropped as intended, so this works. The unspaced value '643369297' also parses correctly. (suggested: No change needed. Optionally document that N/A and Nil values are deliberately skipped.)
  - [advisory] `entity.status`: Action Type (Automatic Suspension, Suspension, Condition, Reprimand) is left unmapped. Suspension rows could support status=suspended, but the end dates and the mix of action types make the meaning ambiguous. This is a missed opportunity and not an error. (suggested: Consider mapping Action Type to entity.status with map_values only for clear values such as Suspension and Automatic Suspension. Alternatively leave it unmapped as now.)
  - [advisory] `entity.entity_type`: The source has no entity-type column, so rule 7 allows entity_type_from_suffix on Licensee Name. The config does not use it, so company names such as 'PTY LTD' come out as unknown. Person-like names must not be inferred as sole_trader, and none are. (suggested: Add entity_type_from_suffix on Licensee Name so company suffixes map to company. Leave names without a suffix as unknown.)
  - [advisory] `Related licensees`: Some rows hold related licensee or company names, for example 'GLOBAL ENTERPRISING PTY LTD T/as SA Solar4life'. This text carries a legal name and a trading name that are not captured. (suggested: Leave it unmapped, which is acceptable. Note in the unmapped reason that it holds other entities and trading names.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `KEGGINS INDUSTRIAL PTY LTD` → `KEGGINS INDUSTRIAL PTY LTD`; `Worldwide Solutions Pty Ltd` → `Worldwide Solutions Pty Ltd`; `UNITED TRADE LINKS PTY LTD` → `UNITED TRADE LINKS PTY LTD`
- `entity.acn<-A.C.N`: `607 387 208` → `607387208`; `646158581` → `646158581`; `152 596 337` → `152596337`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
