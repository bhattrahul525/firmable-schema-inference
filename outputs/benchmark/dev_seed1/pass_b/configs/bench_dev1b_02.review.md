# Review packet (round-2 agent): partial_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **partial_config**.
- 10 model turns, 10 tool calls, $0.0073, 40.69s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_02/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validate on the 2021-22 sheet: 0 hard failures, 34 rows, no duplicate or blank ABNs, ABN and name parse rates 1.0. Critique: 5 advisory issues, 0 blocking. Workbook has nine year sheets; only 2021-22 is covered.
- Reason: The engine reads one sheet per config, so only the 2021-22 allocations are mapped. The other eight year sheets need their own configs.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: Company name in a government allocation list; names carry Pty Ltd/Limited/NL suffixes, treated as registered name
2. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated

## Left unmapped (not guessed)

- `Commissioners allocation $`: Dollar credit allocation; no ontology field for grant amounts

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `all sheets except 2021-22`: Workbook has nine year sheets (2017-18 to 2024-25); this config reads only 2021-22. Other years are not mapped, and 2022-23 has a different layout with blank columns.
- `entity.legal_name<-Name`: Source does not state the names are registered names; mapped at 0.8 confidence with caveat.

## Checks

- Duplicate record ids in held-out rows: {'rows': 34, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ABN and name mappings look broadly sound: the sample ABN 34650766911 passes the checksum, and the unmapped grant amount is correctly excluded. The issues are caveats and config gaps rather than values in the wrong field. The main concerns are the unsupported 'registered name' claim, the observed_at proxy, and the incomplete envelope. None is blocking.
  - [advisory] `entity.legal_name<-Name`: The reason asserts the Name column is the registered name, but the source is a government allocation list, which doesn't say whether its names are registered or trading names. The Pty Ltd/Limited suffixes suggest registered names but don't prove it. (suggested: Keep the mapping but record the caveat in the reason, or set field_confidence below 1 for legal_name, and confirm against the ABN register if this matters downstream.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, which is when the file was last changed, not necessarily when the allocation was stated. The ontology asks for when the source stated it. (suggested: Document that observed_at is the dataset modification date used as a proxy, and consider whether the allocation year (2021-22) should inform valid_from or valid_to.)
  - [advisory] `observation envelope`: The example envelope shows only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not shown in the config or the example, and licence is not stated for this dataset. (suggested: Show the full envelope in the example, state the licence from the CKAN metadata (or record 'unknown' and flag it), and document how source_record_id is built from the ABN.)
  - [advisory] `entity.entity_type`: The example emits entity.entity_type = unknown, but no config entry produces it. The default is correct per the ontology, but the config does not declare it. (suggested: Add an explicit default entity_type of unknown to the config so the emitted observations match the declared mapping.)
  - [advisory] `reader`: The reader sets encoding utf-8-sig, which does not apply to an xlsx file. (suggested: Remove the encoding setting or make it apply only to CSV input.)
- Critique: The mapping is broadly sound: the name and ABN fields are plausibly mapped, the ABN is checksum-validated, and the unmapped dollar column is correctly excluded. The issues are about envelope completeness (licence, source identifiers), the observed_at and validity-period choices, and the strength of the legal-name assumption. None of them puts a value in the wrong field, so no blocking issues were found.
  - [advisory] `observation.licence`: The config and the example envelope do not show a licence for the observations. The ontology requires licence on every observation, and the spec says to record 'unknown' and flag it if none is clear. (suggested: Read the licence from the dataset metadata (CKAN) and attach it to every observation, or record 'unknown' and flag the source. Also confirm source_id and source_record_id appear in the emitted envelope.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, which is when the publisher last touched the file. The ontology defines observed_at as when the source stated the claim. For a 2021-22 allocation sheet these may differ a lot. (suggested: Keep resource_last_modified as the observed_at proxy only if documented. Consider recording the allocation period separately and noting the proxy in the extractor notes.)
  - [advisory] `valid_from`: The sheet is named '2021-22', which suggests the allocations describe a financial-year period. valid_from and valid_to are null in the example, so that period is not captured even though the source appears to state it. (suggested: If the sheet period is confirmed as the claim period, set valid_from and valid_to from it. Otherwise leave them null and state that the period is unverified.)
  - [advisory] `entity.legal_name<-Name`: Names in a government allocation list may carry trading or business names, not always the registered name. The reason asserts they are registered names based only on suffixes like Pty Ltd or Limited. (suggested: Lower the claimed confidence for legal_name in this source, or check a sample of names against ABN registry records before treating them as legal names.)
  - [advisory] `entity.acn`: ACN is not mapped. The ontology says it is often the last nine digits of the ABN, which would give a checksummed, derivable value for these rows. (suggested: Consider deriving ACN from the ABN as an L1 value, validated with the ACN checksum, and noting that it is derived and not stated by the source.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Minerals 260 Limited` → `Minerals 260 Limited`
- `entity.abn<-ABN`: `34650766911` → `34650766911`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
