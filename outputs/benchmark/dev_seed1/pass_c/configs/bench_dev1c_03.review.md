# Review packet (round-2 agent): validated_config

**Dataset:** Victorian Government Schools ABNs — Department of Education  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `dv183-schoolABNdetails.xlsx` (sha256 `a588fe5aa23d…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0074, 40.12s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_03/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `SchoolName` | `entity.trading_name` | clean_whitespace | W | 0.60 | 100.0% | **0.60** |
| 2 | `ABN` | `entity.abn` | clean_whitespace → abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `SchoolName`: School name is the operating name of the school; the file does not state a registered name, so it is held as a trading-name claim.
2. `entity.abn` ← `ABN`: Column named ABN, 11-digit values with valid checksum.

## Left unmapped (not guessed)

- `Fin_Period`: Single constant financial period code; not a claim about the entity.
- `LoadDate`: Load timestamp of the publisher's extract, not a statement of the entity's status.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-SchoolName`: File does not state the registered name; held as trading_name instead.
- `entity.entity_type`: No explicit entity-type column in the source; left as the engine default.

## Checks

- Duplicate record ids in held-out rows: {'rows': 1540, 'key': ['SchoolNumber'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN mapping is consistent with the examples, but the legal_name mapping rests on an assumption the config itself concedes is unsupported, so it should not be emitted as a registered name. The envelope timing and required metadata fields need checking before this mapping is trusted.
  - [blocking] `entity.legal_name<-SchoolName`: The config maps SchoolName to entity.legal_name, but the ontology defines legal_name as the name as registered, and the config's own reason admits the file does not say the name is registered. School names are often trading or operating names, so this asserts a meaning the source does not support. (suggested: Do not map SchoolName to entity.legal_name. Map it to entity.trading_name, or hold it as an unverified name claim until a registry source confirms the registered name.)
  - [advisory] `observation.observed_at`: The config says observed_at comes from resource_last_modified, but every example envelope carries the same observed_at value (2026-11-10T03:54:44), which looks like the ingestion time rather than the source's statement time. LoadDate values from 2015 are also not reflected anywhere. (suggested: Check that observed_at is populated from resource_last_modified and that ingested_at holds the read time. Confirm the envelope builder is not reusing the ingest timestamp for observed_at.)
  - [advisory] `observation.licence`: The example envelopes show no licence, source_id, source_record_id, or extractor_version, all of which the ontology marks as required on every observation. (suggested: Confirm these envelope fields are populated for each emitted observation, taking the licence from the dataset metadata or recording 'unknown' and flagging it.)
- Critique: The ABN mapping looks sound: the example ABN 61834093182 passes the ABN checksum and the field is correctly named. The main concerns are the observed_at timestamp, which appears to be the ingest time rather than the source-stated time, and the default entity_type observations that are emitted with no source backing. The trading_name mapping is defensible but should be caveated. No issue is clearly a value in the wrong field, so none is marked blocking.
  - [advisory] `observed_at`: The envelope observed_at is 2026-11-10T03:54:44 on every row, which looks like the ingest/run time rather than the time the source stated the claim. The config sets observed_at from resource_last_modified, but the rows carry LoadDate values in 2015. Either the envelope is not using the configured source, or the observed_at value is the ingest time mislabelled. (suggested: Confirm that observed_at is populated from resource_last_modified and not from the run clock, and check that resource_last_modified is actually present in the CKAN metadata. Keep ingested_at separate and set it to the run time.)
  - [advisory] `entity.entity_type`: Every row emits an entity_type observation of 'unknown' with from: null. This is a default the engine invented, not a claim from the source. It is consistent with the ontology's 'default to unknown' rule, but it is emitted as an observation that looks like source evidence. (suggested: Either omit the default entity_type observation or mark it explicitly as a defaulted value, with derivation_level and field_confidence reflecting that no source stated it.)
  - [advisory] `entity.trading_name<-SchoolName`: School names are held as trading names because the file has no registered name. For Victorian government schools the school name is probably the name under which the school is registered, so legal_name may be missing. The config's reasoning is defensible, but the mapping is a judgement call that could hide a legal_name the source does imply. (suggested: Note in the config that no legal_name is asserted, and that the trading_name claim comes from the school name only. Consider a documented caveat or a lower field_confidence on this mapping.)
  - [advisory] `observation envelope`: The example envelopes show only observed_at, valid_from and valid_to. The required observation fields source_id, ingested_at, licence and extractor_version are absent from the examples, and the config does not show a licence value or a source_id. (suggested: Show the complete envelope on each emitted observation, with licence taken from the CKAN dataset metadata (or recorded as 'unknown' and flagged), plus source_id, ingested_at and extractor_version.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-SchoolName`: `Berwick Primary School` → `Berwick Primary School`; `Beaufort Primary School` → `Beaufort Primary School`; `Cheltenham Primary School` → `Cheltenham Primary School`
- `entity.abn<-ABN`: `61834093182` → `61834093182`; `57463155273` → `57463155273`; `69873393662` → `69873393662`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
