# Review packet (round-2 agent): validated_config

**Dataset:** ASIC - Business Names Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `business_names_202611.zip` (sha256 `1f50cb2271c1…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0092, 178.74s (download and human waits excluded). Trace: `logs/agent_runs/asic_business_names/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "archive": "zip", "member": "BUSINESS_NAMES_202611.csv", "encoding": "utf-8-sig", "delimiter": "\t", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. REGISTER_NAME | BN_NAME | BN_STATUS | BN_REG_DT | BN_CANCEL_DT | BN_STATE_NUM | BN_STATE_OF_REG | BN_ABN
2. BUSINESS NAMES |   ATTENTION TO D'TILE | Registered | 18/11/2020 | ∅ | ∅ | ∅ | 36817347826
3. BUSINESS NAMES |   Educational Fidget Therapy | Registered | 15/11/2024 | ∅ | ∅ | ∅ | 65163692266
4. BUSINESS NAMES |   Felden Aware | Deregistered | 04/05/2023 | 27/01/2026 | ∅ | ∅ | ∅
5. BUSINESS NAMES |   MORTAR LIFE BRICKLAYING | Registered | 12/03/2009 | ∅ | B2167404E | VIC | ∅
6. BUSINESS NAMES |   OSCAR REAL ESTATE | Deregistered | 22/01/2013 | 11/03/2026 | ∅ | ∅ | ∅
7. BUSINESS NAMES |   TOK early intervention and educational | Registered | 13/07/2024 | ∅ | ∅ | ∅ | 56678071737
8. BUSINESS NAMES |  1-66807814919 | Deregistered | 03/04/2025 | 07/04/2026 | ∅ | ∅ | ∅
9. BUSINESS NAMES |  1-69796833179 | Registered | 08/08/2025 | ∅ | ∅ | ∅ | 83299482097
10. BUSINESS NAMES |  3 JARS FULL | Registered | 02/10/2019 | ∅ | ∅ | ∅ | 52135084368
11. BUSINESS NAMES |  A MAX HOMECARE GROUP | Registered | 30/08/2024 | ∅ | ∅ | ∅ | 82670937363
12. BUSINESS NAMES |  A MAX PRODUCTS GROUP | Registered | 29/08/2024 | ∅ | ∅ | ∅ | 82670937363

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `BN_NAME` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 2 | `BN_ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `BN_NAME`: Registered business name; a name traded under, not the registered legal name of the holder
2. `entity.abn` ← `BN_ABN`: ABN of the registrant of the business name, checksum validated

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant value BUSINESS NAMES
- `BN_STATE_NUM`: state business name registration number; not an ABN, ACN or entity identifier in the ontology
- `BN_STATUS`: status of the business name registration, not of the registrant entity; not mapped to entity.status to avoid asserting holder status
- `BN_REG_DT`: business name registration date, not stated as the entity's own registration date (rule 10)
- `BN_CANCEL_DT`: business name cancellation date, not the entity's own registration end (rule 10)
- `BN_STATE_OF_REG`: state where the business name is registered, not the holder's address

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 3312255, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The trading_name, ABN and record mapping follow the rules. The address.state mapping is blocking because the source column records where the business name is registered, not the holder's address. The status and date mappings are caveats that should be documented or lowered in confidence.
  - [blocking] `address.state<-BN_STATE_OF_REG`: BN_STATE_OF_REG is the state where the business name is registered, which the config's own reason says is not the holder's address. The ontology's address.state describes the entity's address, so the mapping states something the source does not support. The example row for NUMBER ONE CLEANING SERVICE emits address.state NSW as if it were the entity's location. (suggested: Remove this mapping from address.state. Leave BN_STATE_OF_REG unmapped with the reason that it is the business name registration state, not the holder's address.)
  - [advisory] `entity.status<-BN_STATUS`: BN_STATUS describes the status of the business name registration, not the status of the registrant entity. Mapping 'Registered' to entity.status 'active' asserts something about the holder that the column does not state, since the holder could be deregistered or in liquidation. (suggested: Keep the mapping but lower mapping_confidence, or note in the config reason that the status applies to the business name registration. Consider a name-registration-specific field if the ontology has one.)
  - [advisory] `valid_from`: BN_REG_DT records when the business name was registered, not when the entity's own registration started. Rule 10 allows valid_from only from a column stating the entity's own registration start, so this date may be read as the entity's registration date. (suggested: Confirm that the business name registration date is an acceptable proxy for the entity's registration, or document this caveat in the config reason. Consider leaving valid_from unmapped if the policy is strict.)
  - [advisory] `valid_to`: BN_CANCEL_DT is the cancellation date of the business name registration, not the end of the entity's own registration or status. The same caveat as valid_from applies. (suggested: Document that valid_to refers to the business name registration ending, or leave it unmapped under the strict reading of rule 10.)
  - [advisory] `observation.licence`: The config has no licence entry for the envelope, and the ontology requires one. The config does not show whether the dataset's licence was read from metadata. (suggested: Add the licence from the dataset metadata, or record 'unknown' and flag it as a finding.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-BN_NAME`: `18 SUMMERS PORTRAITURE` → `18 SUMMERS PORTRAITURE`; `AA. Absolute Tiling & Bathroom renovations` → `AA. Absolute Tiling & Bathroom renovations`; `Acert Civil` → `Acert Civil`
- `entity.abn<-BN_ABN`: `77649272924` → `77649272924`; `18649410624` → `18649410624`; `41357101950` → `41357101950`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
