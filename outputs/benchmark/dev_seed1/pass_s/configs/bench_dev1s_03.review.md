# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0631, 21.93s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_03/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SchoolName` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `SchoolName`: school name
2. `entity.abn` ← `ABN`: ABN

## Left unmapped (not guessed)

- `Fin_Period`: financial period
- `LoadDate`: load timestamp

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. Names and ABNs are carried through faithfully with traceable record IDs, and nothing is clearly wrong. The caveats are that a school name may not be the legal name of the ABN holder and that observed_at is taken from file metadata rather than the row's load date.
  - [advisory] `entity.legal_name<-SchoolName`: The source column is a school name, which is likely a trading or operating name rather than the registered legal name of the ABN holder (the ABN is likely held by the Victorian Department of Education or the school council). Mapping it to legal_name asserts something the source does not state. One example is also truncated at source ('Dandenong Valley Special Developmental S'). (suggested: Consider mapping SchoolName to trading_name, or keep legal_name with lower field_confidence. Flag the truncated names as possibly cut off at source.)
  - [advisory] `entity.entity_type`: entity_type is always 'unknown', although every record is a government school. The source does not state an entity type, though, so the default is defensible. (suggested: Leave as unknown, or add a documented dataset-level rule for 'government' with a lower confidence.)
  - [advisory] `observed_at`: observed_at is the resource_last_modified metadata (2026-11-10) and is identical for all rows. The raw LoadDate (2015-07) and Fin_Period (201506) are left unmapped, even though they better indicate when the source stated each claim. (suggested: Use LoadDate as observed_at, or at least record Fin_Period as the period the claim relates to.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-SchoolName`: `Warrandyte Primary School` → `Warrandyte Primary School`; `Bacchus Marsh Primary School` → `Bacchus Marsh Primary School`; `Cavendish Primary School` → `Cavendish Primary School`
- `entity.abn<-ABN`: `89340494951` → `89340494951`; `61829351598` → `61829351598`; `11644956677` → `11644956677`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
