# Review packet (round-2 agent): validated_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0686, 18.53s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_09/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `School Name` | `entity.legal_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `School Name`: School name; registered name not explicitly stated

## Left unmapped (not guessed)

- `School No`: school identifier used as record id
- `2011`: payment amount, no ontology field
- `2012`: payment amount
- `2013`: payment amount

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1520, 'key': ['School No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is mostly safe: it emits only the school name and a conservative unknown entity_type, and the payment columns are properly left unmapped. The remaining concerns are advisory: the legal_name provenance, the observed_at date, and the unknown entity_type.
  - [advisory] `entity.legal_name<-School Name`: The school name is a common, publicly known name for a Victorian government school, not necessarily the registered legal name. The config's own reason says the registered name is not explicitly stated, yet the value is emitted as legal_name (the ontology says 'As registered'). (suggested: Keep the mapping but lower field_confidence, or note in the reason that this is the school's operating name as published by the source, not a confirmed registered name.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, yet the example envelope shows 2026-11-11, which looks like the ingestion time rather than the source's stated date. The data covers payments for 2011-2013, so that date does not describe when the source made the claim. (suggested: Check that resource_last_modified is really populated. If it is missing, record the fallback explicitly or leave observed_at null rather than silently using the ingest time.)
  - [advisory] `entity.entity_type`: The entity_type 'unknown' observation is emitted for every row with no source column. The rows are schools, and the source appears to be a government-funded payments list, so the actual entity may be a government school or a government funding recipient. Calling it unknown is safe but uninformative. (suggested: Leave as unknown unless the dataset metadata states that these are government schools. If it does, consider mapping to government with a documented reason.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-School Name`: `Avenel Primary School` → `Avenel Primary School`; `Warrandyte Primary School` → `Warrandyte Primary School`; `Cavendish Primary School` → `Cavendish Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
