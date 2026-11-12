# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 13 model turns, 13 tool calls, $0.0088, 43.04s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_03/trace.jsonl`.
- Evidence the agent gave at finish (its words): Sheet1 of the xlsx: 1,540 rows, 5 columns. SchoolNumber is unique (record_id). ABN: 11-digit, abn transform 100% parse on 1000 rows. SchoolName is not labelled as registered name, so it maps to trading_name at 0.55. LoadDate parses 100% with the space-separated formats. Validation on 300 held-out rows: 0 hard failures, 0 rejected values, no unaccounted columns. observation.licence was not in the config: the resource metadata gives no licence, so the engine should record 'unknown' and flag it.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 2 | `SchoolName` | `entity.trading_name` | clean_whitespace | W | 0.55 | 100.0% | **0.55** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `ABN`: Column holds 11-digit ABNs; checksum validated.
2. `entity.trading_name` ← `SchoolName`: School name is not labelled as a registered name; mapped as trading name per rule 5. Parenthetical qualifiers such as '(interim name)' kept as observed.

## Left unmapped (not guessed)

- `SchoolNumber`: Internal school number; used as record_id.
- `Fin_Period`: Financial period code; constant 201506, not a claim date.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN and SchoolName mappings match the rules and the sample rows: the ABNs are 11-digit values with checksum handling, and the school names are correctly treated as trading names. The main problem is that observed_at does not carry the source date. The remaining points are advisory: confidence for the unlabelled name column, interim-name qualifiers, and the missing licence.
  - [blocking] `observed_at`: The envelope gives observed_at as 2026-11-10T03:54:44, which is the ingest-time value, not a source statement time. The rows' LoadDate values are in July 2015, so the claims are stamped about 11 years after the source date. The config's from_metadata resource_last_modified is not being resolved to the source date. (suggested: Resolve resource_last_modified from the CKAN metadata and use that as observed_at. Confirm the envelope shows the resource date, not the ingest time, and keep ingested_at separate.)
  - [advisory] `entity.trading_name<-SchoolName`: The mapping follows rule 5 for an unlabelled name column, but no mapping_confidence is set. Rule 5 requires 0.6 or lower for such a column, and the config does not record it. (suggested: Set mapping_confidence to 0.6 or lower for SchoolName -> entity.trading_name and say the column is not labelled as a registered name.)
  - [advisory] `entity.trading_name<-SchoolName`: Some school names carry status text, for example 'Rainbow P-12 College (interim name)'. That text is part of the observed value and may mislead downstream matching. (suggested: Keep the raw value as observed. Optionally note in the mapping that parenthetical qualifiers such as '(interim name)' are present and are not stripped.)
  - [advisory] `observation.licence`: The config has no licence for the envelope, although the observation schema requires it. The source licence is not recorded in the mapping. (suggested: Read the licence from the CKAN resource metadata. If none is clear, record 'unknown' and flag it.)
- Critique: The ABN mapping is sound: I checked 37051817052 and 15016745422 against the checksum and both pass. The SchoolName-to-trading_name mapping follows rule 5. The main problem is that the observed_at parse formats use a space separator while the sample LoadDate values use 'T', so the date transform as configured would not match the data. This is advisory because it is a parse issue, not a wrong claim. No blocking meaning errors are visible in the examples.
  - [advisory] `observed_at<-LoadDate`: The parse_date formats are space-separated ('%Y-%m-%d %H:%M:%S.%f' and '%Y-%m-%d %H:%M:%S'), but the sample LoadDate values use a 'T' separator (e.g. '2015-07-14T06:30:43.863000'). As written, the transform would not parse these values, yet the example envelopes show observed_at as a parsed date. The config and the output are inconsistent. (suggested: Check the format with try_transform against the real values. Add a 'T' variant such as '%Y-%m-%dT%H:%M:%S.%f' and '%Y-%m-%dT%H:%M:%S', or confirm the xlsx cells are actually stored as space-separated text.)
  - [advisory] `entity.trading_name<-SchoolName`: The name is mapped to trading_name at the rule-5 fallback, which is correct because the column is not labelled as a registered name. Values such as 'Rainbow P-12 College (interim name)' carry a parenthetical qualifier that is kept in the observed name, so the claim is not a clean trading name. (suggested: Keep the mapping at 0.6 or lower. Consider noting the qualifier as a caveat, or parsing it into a separate observation, rather than changing the field.)
  - [advisory] `entity.entity_type`: The examples show entity_type 'unknown' with no source column. These are all government schools, but the source does not state an entity type, so 'unknown' is the correct default. Nothing in the mapping is wrong here. (suggested: No change needed. Optionally record in the config notes that the schools are government bodies, without mapping entity_type.)

## Examples (raw → value, held-out rows)

- `entity.abn<-ABN`: `37051817052` → `37051817052`; `69873393662` → `69873393662`; `61907518640` → `61907518640`
- `entity.trading_name<-SchoolName`: `Allansford and District Primary School` → `Allansford and District Primary School`; `Cheltenham Primary School` → `Cheltenham Primary School`; `Castlemaine Primary School` → `Castlemaine Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
