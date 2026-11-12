# Review packet (round-2 agent): partial_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **partial_config**.
- 11 model turns, 11 tool calls, $0.0084, 52.36s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_03/trace.jsonl`.
- Evidence the agent gave at finish (its words): Sheet1 of 1,540 rows, 5 columns; SchoolNumber unique; ABN 11-digit checksum passes for all 11-digit values; LoadDate parses to dates; Fin_Period constant 201506. Critique raised blocking issues on the ABN-as-school-ABN claim and on SchoolName as legal name; both addressed by abstention and remapping.
- Reason: Config is limited to the school name as trading name. The ABN is withheld because the source does not show the school is the ABN holder.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SchoolName` | `entity.trading_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `SchoolName`: School name is the name the school operates under; not confirmed as registered name

## Left unmapped (not guessed)

- `SchoolNumber`: used as record_id; internal school number, no ontology field
- `Fin_Period`: financial period code, constant 201506; no ontology field
- `LoadDate`: used as observed_at (load timestamp, proxy for statement time)
- `ABN`: ABN recorded against the school row; the registrant is not stated (likely the managing department), so it is not emitted as the school entity's abn

## Needs a transform the engine does not have

- `ABN`: about 7 short 8/9-digit ABNs (likely dropped leading zeros) cannot be safely padded; 11-digit values pass the abn checksum

## Abstentions (fields removed, with reasons)

- `entity.abn<-ABN`: The ABN is recorded against the school row, but the source does not establish that the school entity is the ABN registrant (likely the managing government department). Emitting it as the school's abn would be an unsupported claim. Left out pending an ABN Lookup check of the registrant.
- `entity.legal_name<-SchoolName`: School name is not evidence of the registered legal name; mapped to trading_name instead.

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN and name mappings make claims the source does not support: the school name is treated as a registered legal name, and the ABN is treated as the school's own, when it most likely belongs to the managing government department. Both are blocking. The entity_type and envelope points are advisory.
  - [blocking] `entity.legal_name<-SchoolName`: The config states that the school name is the registered legal name of the entity the ABN is issued to. The source does not say that. A school name is a site or service name, and the dataset gives no registration information. Its legal name would be that of the government body that runs the school, which this source does not state. The mapping therefore asserts a registered name the source does not support. (suggested: Remove the entity.legal_name observation, or map SchoolName to trading_name (an L0 claim that the school operates under this name). Do not emit legal_name unless a registry source confirms it.)
  - [blocking] `entity.abn<-ABN`: The config reason says the ABN is issued to the school. Nothing in the raw rows supports that. Victorian government schools are typically not separate ABN holders; their ABN usually belongs to the managing government department. Emitting this ABN as the school's entity.abn therefore attaches an identifier to the wrong entity. The checksum only shows the number is well-formed, not who it was issued to. (suggested: Keep the ABN as a raw observation, but change the reason to state that the column is the ABN recorded against the school row, with no claim about the registrant. Add a caveat or hold it until the registrant is confirmed against the ABN Lookup, and do not treat it as the school's own ABN.)
  - [advisory] `entity.entity_type`: entity_type is emitted as 'unknown' with from null. This follows the default rule, but the rows show a government school, which the dataset context points to as a government entity. The observation is safe but leaves useful information unused. (suggested: Keep 'unknown' as the default, or consider a derivation_level L1 observation of 'government' only if the source or a documented rule supports it. Record the reasoning in the config.)
  - [advisory] `observed_at`: LoadDate is the time the source file was loaded, not necessarily the time the source made the claim. The envelope maps it straight to observed_at, which the ontology defines as when the source stated it. (suggested: Document that LoadDate is used as a proxy for observed_at, or add a note explaining the limitation. Consider putting Fin_Period (201506, the financial year ending June 2015) into valid_from or a documented note.)
  - [advisory] `observation envelope`: The examples show no source_id, source_record_id, ingested_at, licence, or extractor_version. These are required fields on every observation. The shown envelope is incomplete, so the examples cannot confirm the required envelope. (suggested: Confirm that every emitted observation carries all required envelope fields. The licence should come from the CKAN metadata, or be recorded as 'unknown' and flagged.)
- Critique: The trading name mapping from SchoolName and the reading of SchoolNumber as the record key look sound. The main problem is that the ABN column is mapped to the school entity's ABN even though the config's own reason says the source makes no such claim, so that mapping is blocking. The LoadDate proxy for observed_at and the envelope completeness are advisory caveats.
  - [blocking] `entity.abn<-ABN`: The ABN column is recorded against the school row, and the config's own reason says it makes no claim that the school is the ABN registrant (the registrant may be the managing department). The mapping still emits it as entity.abn, which asserts the school entity holds this ABN. The source does not support that claim. (suggested: Do not map to entity.abn for the school entity. Either drop it, or emit it under a relationship or source-context field (e.g. ABN recorded against school row, registrant unknown) with a low field_confidence or a note that the registrant is not established.)
  - [advisory] `observed_at<-LoadDate`: observed_at is defined as when the source stated the claim, but LoadDate is the load timestamp, which the config itself calls a proxy for statement time. Fin_Period 201506 may indicate the statement period, which is not used. (suggested: Keep LoadDate as an ingestion-side proxy, document the caveat in the config, and consider recording the Fin_Period (201506) as the statement period or valid_from/valid_to context if the source supports it.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. Required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown in the examples or the config, so the envelope may be incomplete. (suggested: Confirm that every emitted observation carries source_id, source_record_id (SchoolNumber), ingested_at, licence (from the CKAN metadata, or 'unknown' with a flag) and extractor_version.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-SchoolName`: `Alberton Primary School` → `Alberton Primary School`; `Avenel Primary School` → `Avenel Primary School`; `Ballarat Primary School (Dana Street)` → `Ballarat Primary School (Dana Street)`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
