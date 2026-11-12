# Review packet (round-2 agent): validated_config

**Dataset:** Junior Minerals Exploration Incentive credit allocations — Australian Taxation Office  
**Licence:** Creative Commons Attribution 2.5 Australia  
**File:** `jmei_allocation-2017-25.xlsx` (sha256 `62ae9333abd0…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0056, 27.45s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_02/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Name`: Name column lists company names with Limited/Ltd suffixes; the grant is made to the applicant company
2. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated

## Left unmapped (not guessed)

- `Commissioners allocation $`: Dollar credit amount; no ontology field for grant amounts

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.legal_name / entity.abn for sheets 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24`: Workbook holds one sheet per financial year; this config reads only the latest 2024-25 sheet because the reader takes a single sheet. Other years are not ingested by this config (2022-23 has a different 6-column layout).
- `valid_from / valid_to`: The sheet states the financial year but not when the allocation started or ended in a per-row form; not mapped.
- `entity.entity_type`: Not mapped; entity_type_from_suffix not applied to avoid guessing from names.

## Checks

- Duplicate record ids in held-out rows: {'rows': 31, 'key': ['ABN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking meaning errors are visible in these examples. The name and ABN mappings match their source columns, and the unmapped grant amount is correctly left out of the ontology. The remaining points are about provenance of the legal name, record-key uniqueness, the meaning of observed_at, and envelope completeness.
  - [advisory] `entity.legal_name<-Name`: The config justifies this mapping only by the suffix (Limited/Ltd) and the grant recipient role. Nothing in the source shows these names are the registered legal names rather than trading names. The ontology says legal_name is 'as registered', so the claim is not fully supported. (suggested: Cross-check a sample of Name values against the ABN register, or record a field_confidence below 1 and a note that the name is the applicant name as stated in the grant sheet.)
  - [advisory] `record_id`: The source_record_id is built from ABN alone. If one company receives several allocations in the 2024-25 sheet, the key will collide and the records cannot be traced back to their exact raw rows. (suggested: Build source_record_id from the sheet name plus the row number (or ABN plus row index) and document the construction, as the ontology requires for keyless sources.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, which is the publication or file-modified date, not a date the source stated for the allocation. The ontology asks for the time the source stated the claim. (suggested: Keep resource_last_modified but document it as a proxy, or record the financial year (2024-25) as valid_from or valid_to where the grant period is known.)
  - [advisory] `observation envelope`: The examples show only observed_at, valid_from and valid_to. The required envelope fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the output, and no licence has been recorded for this dataset. (suggested: Confirm the emitted observations carry all required envelope fields. Take licence from the CKAN metadata, or record 'unknown' and flag it.)
  - [advisory] `entity.abn<-ABN`: The config says the ABN is checksum-validated, but the examples do not show which values passed or failed. The output does not evidence the checksum step. (suggested: Add a check or log showing the number of ABNs that failed the checksum, and route failures to a flagged state rather than emitting them as valid.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Name`: `Ausmon Resources Limited` → `Ausmon Resources Limited`; `Barton Gold Holdings Limited` → `Barton Gold Holdings Limited`; `Eastern Metals Ltd` → `Eastern Metals Ltd`
- `entity.abn<-ABN`: `88134358964` → `88134358964`; `36633442618` → `36633442618`; `29643902943` → `29643902943`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
