# Review packet (round-2 agent): validated_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **validated_config**.
- 15 model turns, 15 tool calls, $0.0108, 56.51s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_09/trace.jsonl`.
- Evidence the agent gave at finish (its words): Single sheet 'data lrf', 1,520 school rows after skipping a title row and using the 'School No' row as header. School No is unique and filled. School Name is filled and maps to trading_name with 100% parse rate on held-out rows. Payment columns 2011-2013 are unmapped. Validation: 0 hard failures, 600 observations on 300 held-out rows.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `School Name` | `entity.trading_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `School Name`: The source gives a school name and does not state a registered legal name, so it is mapped as trading name rather than legal_name.

## Left unmapped (not guessed)

- `School No`: Department school number; used as record_id, not an ontology field.
- `2011`: Payment amount for 2011; no ontology field for voluntary payment totals.
- `2012`: Payment amount for 2012; no ontology field.
- `2013`: Payment amount for 2013; no ontology field.

## Needs a transform the engine does not have

- `2011`: Per-year payment totals need a canonical field for school payment amounts, which the ontology lacks.

## Checks

- Duplicate record ids in held-out rows: {'rows': 1520, 'key': ['School No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main problem is the legal_name mapping: the source gives a school name, and the config presents it as a registered legal name, which the ontology reserves for registration. The entity_type default and the envelope completeness are secondary points. The unmapped payment columns are reasonable as they stand.
  - [blocking] `entity.legal_name<-School Name`: The config maps 'School Name' to entity.legal_name and justifies it as the school's official name. The ontology defines legal_name as the name as registered, and nothing in the source says these names are registered legal names. The rows only give the name of a publicly run school, so the mapping states a registration fact the source does not support. (suggested: Either drop the legal_name mapping, or map the school name to trading_name (or a source-scoped observation) and record that it is the name the school is known by, not a registered name. Add a note that the source does not state a registration basis.)
  - [advisory] `entity.entity_type`: Every example emits entity.entity_type as 'unknown'. That is consistent with the default, but the rows describe government-run schools, so the source does support a more specific reading. Emitting nothing, or 'unknown', without a note loses that context. (suggested: Keep 'unknown' as the default, and optionally add a derivation note or a government-sector observation that cites the source's description of the schools as publicly run, at a lower derivation level.)
  - [advisory] `observation`: The shown envelopes include observed_at, valid_from and valid_to, but not the other required envelope fields: source_id, source_record_id, ingested_at, licence and extractor_version. The config also has no licence entry, so licence would have to be recorded as 'unknown' and flagged. (suggested: Confirm that every emitted observation carries source_id, source_record_id (built from School No), ingested_at, licence (from the CKAN metadata, or 'unknown' with a finding) and extractor_version. Show these in the examples.)
  - [advisory] `observed_at`: observed_at is set from resource_last_modified, which is the publisher's metadata date. The examples show it as 2026-11-11T03:38:25, which looks like the ingestion time rather than the date the source stated. That may be a meaning mismatch between observed_at and ingested_at. (suggested: Confirm that resource_last_modified is the time the source states the data, and record it as observed_at. Keep ingested_at as the time the row was read, and check that the two are not the same value.)
- Critique: No blocking meaning errors are visible in the examples: the school name is mapped to trading_name, which is a defensible choice, and entity_type is left as unknown rather than guessed. The remaining issues concern unsupported justification wording, possible missed richness, and envelope fields that the examples do not show.
  - [advisory] `entity.trading_name<-School Name`: The stated reason claims the school 'operates under' this name, which the source does not say. The column is only a school name, so the trading_name mapping is defensible, but the justification overstates what the source supports. (suggested: Reword the reason to say only that the source gives a school name and does not state a registered legal name, so it is mapped as trading_name.)
  - [advisory] `entity.entity_type`: Every example emits entity_type 'unknown' with no source value. The rows are all public schools, so 'government' may be supportable, but the source does not state an entity type, so 'unknown' is the safe default and the omission is only a missed opportunity. (suggested: Keep 'unknown' unless the publisher's metadata states the payee type; optionally note in the config that the schools are government-run only if the source says so.)
  - [advisory] `observed_at`: observed_at is configured from resource_last_modified, but the example envelopes show 2026-11-11T03:38:25, which looks like an ingestion time rather than the source's stated modification time. The examples cannot confirm which value was used. (suggested: Verify that observed_at takes the CKAN resource_last_modified value and that ingested_at is recorded separately as the read time.)
  - [advisory] `observation.licence`: The examples show no licence, source_id, source_record_id, ingested_at or extractor_version, all of which are required envelope fields. The config also does not state where the licence comes from. (suggested: Confirm the emitted observations carry all required envelope fields, taking licence from the CKAN metadata or recording 'unknown' and flagging it.)
  - [advisory] `unmapped.2011`: The reason describes the 2011–2013 columns as 'voluntary payment totals', but the headers are only bare years and the amounts are not labelled in the examples. The meaning is asserted rather than shown in the data. (suggested: Cite the dataset's column documentation for the meaning of these columns, or describe them only as per-year amounts without the 'voluntary' label.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-School Name`: `Belmont Primary School` → `Belmont Primary School`; `Beaufort Primary School` → `Beaufort Primary School`; `Newport Lakes Primary School` → `Newport Lakes Primary School`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
