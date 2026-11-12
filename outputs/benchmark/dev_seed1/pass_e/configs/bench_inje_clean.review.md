# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0065, 31.49s (download and human waits excluded). Trace: `logs/agent_runs/bench_inje_clean/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.trading_name` | clean_whitespace | W | 0.50 | 100.0% | **0.50** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Licence Status` | `entity.status` | map_values({'Current': 'active', 'Expired': 'unknown'}) | W | 0.60 | 100.0% | **0.60** |
| 4 | `Suburb` | `address.locality` | clean_whitespace | W | 0.95 | 100.0% | **0.95** |
| 5 | `State` | `address.state` | state_code | W | 0.95 | 100.0% | **0.95** |
| 6 | `Postcode` | `address.postcode` | postcode | W | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Business Name`: Business Name is not labelled as registered or licensee name; mapped as trading name at low confidence per rule 5. Values carry a Pty Ltd suffix, so a registered name is possible; a reviewer could confirm against publisher documentation.
2. `entity.abn` ← `ABN`: ABN column, checksum validated.
3. `entity.status` ← `Licence Status`: Current maps to active; Expired is a licence state, not a confirmed deregistration, so mapped to unknown.
4. `address.locality` ← `Suburb`: Suburb name.
5. `address.state` ← `State`: State abbreviation.
6. `address.postcode` ← `Postcode`: Australian postcode.

## Left unmapped (not guessed)

- `Licence No`: Used as record_id; licence number is not an entity identifier.
- `Notes`: Free-text change notes (e.g. 'address updated', 'renewal pending') with no canonical field; not mapped.

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `entity.entity_type`: No explicit entity-type column; entity_type_from_suffix not applied, so the engine records unknown.

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking issues. The ABN checksum (19200000013 checks out), postcodes and state codes match the suburbs in the sampled rows, and the observed_at from resource_last_modified is consistent with a snapshot register. The remaining concerns are advisory: the Business Name column is mapped to trading_name, which follows rule 5 but sits uneasily with the 'Pty Ltd' registered-name form, the entity_type suffix inference is available but unused, and the Expired status is conservatively mapped to unknown.
  - [advisory] `entity.trading_name<-Business Name`: Every Business Name value ends in 'Pty Ltd', which is the form of a registered company name. The mapping follows rule 5 and records it as trading_name at low confidence, which is allowed, but the column may actually hold the registered name, so the trading_name claim is weaker than the values suggest. No mapping_confidence is stated in the config. (suggested: Keep the trading_name mapping per rule 5 and set mapping_confidence at 0.6 or lower. Note in the reason that the 'Pty Ltd' suffix suggests a registered name, so a reviewer can check whether a legal_name mapping is justified by the publisher's documentation.)
  - [advisory] `entity.entity_type`: The source has no explicit entity-type column, and every sampled name carries a 'Pty Ltd' suffix. Rule 7 allows entity_type_from_suffix on the name column in this case, but the config does not use it, so the engine records 'unknown' for every row. (suggested: Consider adding entity_type_from_suffix on Business Name so that 'Pty Ltd' yields company. If the team does not want that inference, record the decision in the config reason.)
  - [advisory] `entity.status<-Licence Status`: The map_values transform maps 'Expired' to 'unknown'. This is a conservative choice and does not state anything the source does not support, but it discards the fact that the licence has expired, which the source does state. Only 'Current' and 'Expired' are seen in the profile, so the mapping is complete for the observed values. (suggested: Keep 'Expired' as 'unknown' if the team does not accept that an expired licence means deregistration. Preserve the raw value 'Expired' in the observation so the licence state is still traceable.)
  - [advisory] `unmapped<-Notes`: The Notes column holds free text such as 'address updated', which is a claim about the record's address history. It is correctly listed as unmapped, but a reviewer may want to know it exists because it bears on address observations. (suggested: Keep the Notes column unmapped, and record in the reason that it carries free-text change notes that were not mapped, so later review can pick them up.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Business Name`: `Electrical Services 1 Pty Ltd` → `Electrical Services 1 Pty Ltd`; `Carpentry Services 4 Pty Ltd` → `Carpentry Services 4 Pty Ltd`; `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`
- `entity.abn<-ABN`: `19200000013` → `19200000013`; `59200000052` → `59200000052`; `74200000065` → `74200000065`
- `entity.status<-Licence Status`: `Current` → `active`; `Expired` → `unknown`
- `address.locality<-Suburb`: `Richmond` → `Richmond`; `Glenelg` → `Glenelg`; `Sandy Bay` → `Sandy Bay`
- `address.state<-State`: `VIC` → `VIC`; `SA` → `SA`; `TAS` → `TAS`
- `address.postcode<-Postcode`: `3121` → `3121`; `5045` → `5045`; `7005` → `7005`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
