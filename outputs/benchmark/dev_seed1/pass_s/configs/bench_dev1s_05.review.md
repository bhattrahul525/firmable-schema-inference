# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.1006, 30.97s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_05/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 2 | `A.C.N` | `entity.acn` | acn | W | 0.80 | 99.3% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: licensee name
2. `entity.acn` ← `A.C.N`: ACN

## Left unmapped (not guessed)

- `Licence Number`: licence id, no ontology field
- `Occupation`: not ANZSIC
- `Occupation Class`: class
- `Licence Conditions/Endorsement`: n/a
- `Action Type`: n/a
- `Action End Date`: mostly N/A
- `Circumstances/Reasons`: free text
- `Action under review by the ACAT`: n/a
- `Period licensee can apply to ACAT for review expired`: n/a
- `Applicant has applied to ACAT for review and the review is incomplete`: n/a
- `Partnership details (Partnerships only)`: n/a
- `Compliance with Rectification Order`: n/a
- `Related licensees`: n/a
- `Licence Expiry Date`: n/a
- `Date stop work notice lifted`: n/a
- `Reason stop work notice lifted`: n/a

## Needs a transform the engine does not have

- `A.C.N`: spaced ACNs need space removal

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The ACN mapping is sound, with spaces stripped and N/A skipped. The main concern is that person names for individual licensees are emitted as legal_name. Other points are advisory: stray punctuation, validity dates and the suspension status.
  - [blocking] `entity.legal_name<-Licensee Name`: For individual licensees the Licensee Name is a person's name (e.g. 'JOHNSTONE, James', 'DARREN JOHN EDGE'), not a registered legal entity name. Mapping it to legal_name states a registration the source does not support. (suggested: Only emit legal_name for rows with an ACN or a company suffix (Pty Ltd). For individuals, skip or map to a person-name field; keep entity_type unknown or sole_trader only if stated.)
  - [advisory] `entity.legal_name<-Licensee Name`: Trailing punctuation is left in the name ('DYNAMIC PROJECTS (AUS) PTY LTD,'). Clean_whitespace does not strip it. (suggested: Add a transform to strip trailing commas and punctuation.)
  - [advisory] `valid_from`: The envelope valid_from is taken from Action Date, which is when a suspension/condition began, not when the name or ACN claim became true. Also valid_to stays null even where Action End Date is given (e.g. 02/02/2026, 18/06/2026, 04/12/2018), so the suspension is shown as still current. The config does not document this. (suggested: Document that valid_from is the action date, and populate valid_to from Action End Date when it is not N/A, or avoid presenting it as validity of the entity claims.)
  - [advisory] `status`: The dataset is a register of suspensions and conditions, but no status observation is emitted. Suspended licensee information is dropped, and Action Type is unmapped. (suggested: Consider mapping Action Type 'Automatic Suspension' to status=suspended (licence-level, so with caution), or flag it in a note.)
  - [advisory] `observed_at`: observed_at (2026-09-30) comes from the resource's last-modified metadata, and it is later than many action dates. This is a file-level timestamp and not necessarily when each record was stated. (suggested: Document that observed_at is the file modification time.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `KEGGINS INDUSTRIAL PTY LTD` → `KEGGINS INDUSTRIAL PTY LTD`; `Galaxy Builders Pty Ltd` → `Galaxy Builders Pty Ltd`; `BGIS PTY LTD` → `BGIS PTY LTD`
- `entity.acn<-A.C.N`: `607 387 208` → `607387208`; `638 184 040` → `638184040`; `064 638 197` → `064638197`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
