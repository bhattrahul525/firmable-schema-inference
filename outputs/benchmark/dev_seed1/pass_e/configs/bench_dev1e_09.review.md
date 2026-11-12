# Review packet (round-2 agent): validated_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0054, 22.91s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_09/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `School Name` | `entity.trading_name` | clean_whitespace | W | 0.55 | 100.0% | **0.55** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `School Name`: School name, not labelled as registered name; mapped to trading_name at low confidence per rule 5.

## Left unmapped (not guessed)

- `School No`: Internal Department school number, not an ABN/ACN; no ontology field. Used as record_id (unique across 1,520 rows).
- `2011`: Voluntary parent payment total in dollars under a year header; no ontology field for payments.
- `2012`: Voluntary parent payment total in dollars under a year header; no ontology field for payments.
- `2013`: Voluntary parent payment total in dollars under a year header; no ontology field for payments.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1520, 'key': ['School No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping follows rule 5 for school names, and the schools are correctly treated as entities with entity_type left unknown. The remaining points are advisory: record_id uniqueness is unverified, the low-confidence caveat is not recorded in the config, and the payment-column meaning rests on the header rather than on anything visible in the rows. No blocking meaning errors are visible in the examples.
  - [advisory] `record_id`: The config sets record_id from School No but does not show a check_unique result, and the examples do not confirm that School No is unique across all rows. (suggested: Confirm School No is unique over the whole sheet (check_unique) and fall back to hash_row=true if it is not.)
  - [advisory] `entity.trading_name<-School Name`: Mapping school names to trading_name at low confidence follows rule 5, but the config gives no mapping_confidence value, so the caveat is not recorded in the config itself. (suggested: Add mapping_confidence at 0.6 or lower for this field and note that the column is not labelled as a registered name.)
  - [advisory] `unmapped`: The reasons for the 2011, 2012 and 2013 columns say they hold voluntary parent payment totals. The rows shown contain only numbers under year headers, so that meaning comes from outside the sample and is not visible in the examples. (suggested: Cite the sheet's column definition in the reason, or state that the meaning is inferred from the header and not confirmed by the data.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-School Name`: `Avoca Primary School` → `Avoca Primary School`; `Cudgee Primary School` → `Cudgee Primary School`; `Newport Lakes Primary School` → `Newport Lakes Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
