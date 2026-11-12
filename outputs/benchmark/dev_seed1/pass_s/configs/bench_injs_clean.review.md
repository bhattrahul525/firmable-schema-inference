# Review packet (round-2 agent): validated_config

**Dataset:** clean — unknown (not from a catalogue)  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `clean.csv` (sha256 `4a1a3a60696e…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0780, 22.11s (download and human waits excluded). Trace: `logs/agent_runs/bench_injs_clean/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Business Name` | `entity.legal_name` | clean_whitespace | W | 0.70 | 100.0% | **0.70** |
| 2 | `ABN` | `entity.abn` | abn | W | 0.95 | 100.0% | **0.95** |
| 3 | `Suburb` | `address.locality` | clean_whitespace | W | 0.90 | 100.0% | **0.90** |
| 4 | `State` | `address.state` | state_code | W | 0.90 | 100.0% | **0.90** |
| 5 | `Postcode` | `address.postcode` | postcode | W | 0.90 | 100.0% | **0.90** |
| 6 | `Licence Status` | `entity.status` | map_values({'Current': 'active', 'Expired': 'unknown'}) | W | 0.60 | 100.0% | **0.60** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Business Name`: licensee business name
2. `entity.abn` ← `ABN`: ABN
3. `address.locality` ← `Suburb`: suburb
4. `address.state` ← `State`: state
5. `address.postcode` ← `Postcode`: postcode
6. `entity.status` ← `Licence Status`: licence status; expired licence doesn't imply deregistered

## Left unmapped (not guessed)

- `Notes`: free text

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 160, 'key': ['Licence No'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. No blocking meaning errors are visible in the examples; the only concerns are advisory nuances around status semantics and timestamp provenance.
  - [advisory] `entity.status<-Licence Status`: A 'Current' licence is mapped to entity status 'active'. The licence status describes the licence, not the entity's registration, so this is a mild semantic stretch. The Expired->unknown mapping is cautious, but Expired does not appear in the examples. (suggested: Lower field_confidence for the Current->active mapping, or note that status is derived from licence status and not from the ABN register.)
  - [advisory] `entity.legal_name<-Business Name`: The column is labelled 'Business Name' for a licensee. It could be a trading name, though all examples carry Pty Ltd suffixes consistent with registered names. (suggested: Keep the mapping but lower field_confidence slightly, and consider cross-checking against ABR.)
  - [advisory] `observed_at`: observed_at comes from resource_last_modified, which is the file modification time and not necessarily when the licensing body stated the claim. The examples show a future-looking date (2026-11-12). (suggested: Document that observed_at is a proxy and verify the metadata timestamp.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Business Name`: `Concreting Services 3 Pty Ltd` → `Concreting Services 3 Pty Ltd`; `Painting Services 5 Pty Ltd` → `Painting Services 5 Pty Ltd`; `Plumbing Services 8 Pty Ltd` → `Plumbing Services 8 Pty Ltd`
- `entity.abn<-ABN`: `49200000039` → `49200000039`; `74200000065` → `74200000065`; `91200000104` → `91200000104`
- `address.locality<-Suburb`: `Fremantle` → `Fremantle`; `Sandy Bay` → `Sandy Bay`; `Fortitude Valley` → `Fortitude Valley`
- `address.state<-State`: `WA` → `WA`; `TAS` → `TAS`; `QLD` → `QLD`
- `address.postcode<-Postcode`: `6160` → `6160`; `7005` → `7005`; `4006` → `4006`
- `entity.status<-Licence Status`: `Current` → `active`; `Expired` → `unknown`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
