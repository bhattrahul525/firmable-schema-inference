# Review packet (round-2 agent): partial_config

**Dataset:** Victorian State Schools-Voluntary Parent Payments — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv113-vicstateschparentcommunitypayments2013.xlsx` (sha256 `1b4fa5a769eb…`)

## How this ended

- Outcome **partial_config**.
- 10 model turns, 10 tool calls, $0.0057, 32.16s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_09/trace.jsonl`.
- Evidence the agent gave at finish (its words): Single sheet 'data lrf', 1,520 rows, unique School No key. Columns: School No, School Name, and per-year dollar payment totals for 2011-2013. No ABN, ACN, address, status or industry columns. Critique blocking issue c-35a1cc89 concerned legal_name mapping; accepted and removed.
- Reason: The file is a list of government schools with payment totals. It has no identifiers or claims that map to the ontology's entity fields beyond a school name, which the source does not state is a registered name. The config therefore carries no mapped fields; the rows are retained with a record id.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|

The model's reasons per field (its words, not verified):


## Left unmapped (not guessed)

- `School No`: Department school number; used as record id, no ontology field.
- `School Name`: Name of the government school as published; the source does not say it is the registered legal name, so not mapped to entity.legal_name.
- `2011`: Voluntary parent payment total in dollars for 2011; no ontology field.
- `2012`: Voluntary parent payment total in dollars for 2012; no ontology field.
- `2013`: Voluntary parent payment total in dollars for 2013; no ontology field.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-School Name`: Schools are named in a departmental list without any statement that the name is a registered legal name; critique flagged this as blocking. Left out.

## Checks

- Critique: The main problem is that School Name is mapped to entity.legal_name, a registered-name field, without support from the source. The observed_at source and the envelope need checking, and the default entity_type observations should be marked clearly or dropped.
  - [blocking] `entity.legal_name<-School Name`: The ontology defines entity.legal_name as the name as registered, but the source is a list of Victorian government schools with a name and a department school number. Nothing in the source says these names are registered legal names. The config's reason asserts that the school is the entity, which the source does not state. Values such as 'Ashwood School' or 'Mansfield Secondary College' are operational names, and the registered legal entity behind a government school is more likely the Department or a government body. (suggested: Remove the legal_name mapping. Emit School Name as an observation for a trading_name or as a source-stated name with a description that says it is the school name as published, not a registered name. Map the entity only if the source supports it. The school's entity_type is unknown until a source states otherwise.)
  - [advisory] `observed_at`: observed_at is set from resource_last_modified in the metadata, but the example envelopes show observed_at as 2026-11-11T03:38:25, which looks like the ingest run time rather than the metadata date. The ontology says observed_at is when the source stated the claim, and ingested_at is when it was read, so these may be conflated. (suggested: Check that observed_at actually takes the resource_last_modified value and that ingested_at holds the run time. Record which metadata field was used in the config notes.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the examples, and the licence is not shown for this dataset. (suggested: Confirm that every emitted observation carries all required envelope fields. Take the licence from the CKAN metadata, or record 'unknown' and flag it.)
  - [advisory] `entity.entity_type`: Every example emits entity_type 'unknown' with from null. This is the ontology default and is acceptable, but it adds a noise observation to every row with no source claim behind it. (suggested: Either omit the default observation or mark it explicitly as an engine default with derivation_level and field_confidence so it cannot be mistaken for a source statement.)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
