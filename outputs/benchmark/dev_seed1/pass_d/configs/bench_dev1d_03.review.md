# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0080, 49.04s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1d_03/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SchoolName` | `entity.trading_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |
| 2 | `ABN` | `entity.abn` | clean_whitespace → abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `SchoolName`: SchoolName is the operating name of the school; the source does not state it is the registered name, so it is mapped as trading name, not legal_name
2. `entity.abn` ← `ABN`: ABN column of 11-digit identifiers, checksum validated

## Left unmapped (not guessed)

- `SchoolNumber`: internal school number; used as part of record_id
- `Fin_Period`: financial period code; used as part of record_id, not a claim start date
- `LoadDate`: system load timestamp, not a statement date; observed_at uses resource metadata

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber', 'Fin_Period'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN mapping and the entity_type default of unknown are sound, and schools are valid business entities under rule 18. The main problem is the legal_name mapping from SchoolName, which the config itself says is not labelled as the registered name, so it breaks rule 5 and should be blocked or remapped to trading_name. Record uniqueness and observation period handling are advisory gaps.
  - [blocking] `entity.legal_name<-SchoolName`: SchoolName is mapped to entity.legal_name, but the source does not say it is the registered name. The config's own reason admits it is 'not explicitly labelled as registered name'. Rule 5 allows legal_name only when the data says the name is registered, licensee or supplier name, so this claim is not supported by the source. (suggested: Remove the legal_name mapping, or map SchoolName to entity.trading_name if it is treated as the name the school operates under. Keep it as legal_name only if the source documentation confirms it is the registered name.)
  - [advisory] `record_id`: record_id is built from SchoolNumber and Fin_Period, but the config does not show a check_unique result or hash_row fallback. Rule 15 requires one of these to be confirmed. (suggested: Verify that the SchoolNumber and Fin_Period combination is unique across all rows, and record that check in the config.)
  - [advisory] `observed_at`: observed_at comes from resource_last_modified, which is reasonable because LoadDate is a system timestamp. The Fin_Period value (e.g. 201506) states which financial period the figures relate to, but it is not carried into any envelope or claim field, so the period the claim refers to is lost. (suggested: Consider recording Fin_Period as a statement-period attribute on the observation (not as valid_from) so the period is traceable to the claim.)
  - [advisory] `entity.abn<-ABN`: The ABN mapping is consistent with the examples (11-digit values through the abn transform). The examples do not show whether any ABN fails the checksum, so the transform's pass or fail behaviour is not visible here. (suggested: Confirm that rows failing the abn checksum are dropped or flagged rather than emitted as valid ABNs.)
- Critique: No blocking meaning errors are visible in the examples. SchoolName is correctly kept out of legal_name, the ABN is correctly checksum-validated, LoadDate is correctly excluded from observed_at, and entity_type is correctly left unknown. The remaining points are caveats about whether the ABN belongs to the school, the uniqueness of the composite record_id, and an observed_at value in the envelope that does not match the config's metadata source.
  - [advisory] `entity.trading_name<-SchoolName`: The mapping is reasonable, but the source does not say SchoolName is a name the school trades under. It is the school's name as listed, and the reason text only argues it is not the registered name. The trading-name claim rests on that reading. (suggested: Keep trading_name, but state in the reason that the column is the school's public/operating name as listed, not a trading-as or business-name claim. Consider lowering mapping_confidence to reflect this.)
  - [advisory] `entity.abn<-ABN`: The ABN column is presented as the school's own ABN. The source does not say whose ABN it is. Public schools are often under a controlling body or department, so the identifier may belong to that body rather than the school. The checksum validates format only, not ownership. (suggested: Keep the abn mapping, since the checksum transform applies, but record in the reason that ownership is not stated by the source. Consider a lower mapping_confidence and a note in source_reliability_basis. Optionally check the ABNs against the ABR before relying on them as school identifiers.)
  - [advisory] `record_id`: record_id is built from SchoolNumber plus Fin_Period, but check_unique is not stated. Fin_Period is constant (201506) across every example row, so uniqueness depends entirely on SchoolNumber. If the file ever holds multiple rows per school for one period, the id will collide. (suggested: Confirm uniqueness of the composite key across the full file with check_unique and record the result, or fall back to hash_row if it fails.)
  - [advisory] `observed_at`: The config says observed_at comes from resource_last_modified, but every example envelope shows observed_at as 2026-11-10T03:54:44, which looks like an ingest time, not the resource metadata date. Either the envelope is wrong or the metadata value is not what the config intends. (suggested: Check that the engine resolves resource_last_modified from the CKAN metadata and that the envelope observed_at matches it. Keep ingested_at separate and record the true ingest time there.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-SchoolName`: `Avoca Primary School` → `Avoca Primary School`; `Warrandyte Primary School` → `Warrandyte Primary School`; `St Andrews Primary School` → `St Andrews Primary School`
- `entity.abn<-ABN`: `39744336864` → `39744336864`; `89340494951` → `89340494951`; `79546163588` → `79546163588`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
