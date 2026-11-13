# Review packet (round-2 agent): validated_config

**Dataset:** Victorian liquor licences by location — Liquor Control Victoria  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `Current_Victorian_Licences_By_Location_30_September_2026.xlsx` (sha256 `382364f5ccca…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0082, 44.36s (download and human waits excluded). Trace: `logs/agent_runs/vic_liquor_licences/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "xlsx", "header_rows": 1, "skip_rows": 4}`
- layout: column names from raw row 5; data starts at raw row 6.
- `record_id`: from `Licence Number` — 0 duplicate / blank keys of 23169 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | 
GPO Box 4356, Melbourne VIC 3001
1300 1 | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
2. ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
3. Current Victorian Liquor Licences as of  | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
4. ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
5. Licence Number | Licensee | Trading As | Licence Category | Trading Hours | Patron Capacity (if applicable) | Street Address | ∅ | ∅ | Suburb | Postcode | Council | Region | ∅ | ∅
6. 31100099 | ARNOLD BRUCE | UNIVERSITY SKI CLUB | BYO Permit | BYO Permit | ∅ | U S C LODGE ALLOTMENTS 15 & 16 ALPINE VI | ∅ | ∅ | MT BULLER | 3723 | MANSFIELD SHIRE COUNCIL | Hume | ∅ | ∅
7. 31100138 | C S I R SKI CLUB | C S I R SKI CLUB | BYO Permit | BYO Permit | ∅ | SITE 65 1 SCHUSS STREET | ∅ | ∅ | FALLS CREEK | 3699 | ALPINE SHIRE COUNCIL | Hume | ∅ | ∅
8. 31100154 | SKILIB ALPINE CLUB | SKILIB ALPINE CLUB | BYO Permit | BYO Permit | ∅ | 2 GOAL POSTS RD | ∅ | ∅ | MT BULLER | 3723 | MANSFIELD SHIRE COUNCIL | Hume | ∅ | ∅
9. 31100269 | THEODOR HERZL SOCIAL CLUB | THEODOR HERZL SOCIAL CLUB | BYO Permit | BYO Permit | ∅ | 222 BALACLAVA RD | ∅ | ∅ | CAULFIELD | 3162 | GLEN EIRA CITY COUNCIL | Metro South | ∅ | ∅
10. 31100277 | GREYTHORN PARK TENNIS CLUB INC | GREYTHORN PARK TENNIS CLUB | BYO Permit | BYO Permit | ∅ | FRANK AVE NORTH | ∅ | ∅ | BALWYN NORTH | 3104 | BOROONDARA CITY COUNCIL | Metro East | ∅ | ∅
11. 31100609 | OLOS CO-OPERATIVE SOCIETY LTD | SKI CLUB | BYO Permit | BYO Permit | ∅ | 51 STIRLING | ∅ | ∅ | MT BULLER | 3723 | MANSFIELD SHIRE COUNCIL | Hume | ∅ | ∅
12. 31100722 | MELBOURNE WALKING CLUB INC | MELBOURNE WALKING CLUB INC | BYO Permit | BYO Permit | ∅ | MT BULLER ALPINE VILLAGE | ∅ | ∅ | MOUNT BULLER | 3722 | MANSFIELD SHIRE COUNCIL | Hume | ∅ | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee` | `entity.legal_name` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `Trading As` | `entity.trading_name` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 3 | `Street Address` | `address.full` | clean_whitespace | W | held_out | 0.70 | 100.0% | **0.70** |
| 4 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `Postcode` | `address.postcode` | postcode | W | held_out | 0.90 | 97.9% | **0.90** |
| 6 | `Licence Number` | `address.state` | constant(VIC) | P | asserted | 0.70 | 100.0% | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee`: Column labelled Licensee; the regulator register lists the licence holder, so this is the holder's name.
2. `entity.trading_name` ← `Trading As`: Trading As column is the name traded under.
3. `address.full` ← `Street Address`: Licensed premises street address (e.g. shopping centre tenancies), not the licensee's registered or head-office address.
4. `address.locality` ← `Suburb`: Suburb of the licensed premises.
5. `address.postcode` ← `Postcode`: Postcode of the licensed premises; placeholder '0' values are rejected by the transform.
6. `address.state` ← `Licence Number`: Dataset title 'Current Victorian Liquor Licences' states the jurisdiction covers every row; the anchor is a filled identifier column used only to carry the constant.

`address.state<-Licence Number` is **asserted**: a fixed value stated by the config, not read from the source (L3, confidence capped at 0.5). Basis given: Dataset title 'Current Victorian Liquor Licences' states the jurisdiction covers every row; the anchor is a filled identifier column used only to carry the constant.

## Left unmapped (not guessed)

- `Licence Category`: Licence type, not an entity type or industry code.
- `Trading Hours`: Operating hours, no ontology field.
- `Patron Capacity (if applicable)`: Premises attribute, no ontology field.
- `Council`: Local government area, no ontology field.
- `Region`: Region, no ontology field.
- `Metro/Regional`: Region class, no ontology field.
- `Latitude`: Geo coordinate, no ontology field.
- `Longitude`: Geo coordinate, no ontology field.
- `Postal Address`: Postal address of licensee, not premises; no ontology field.
- `Postal Suburb`: Postal suburb, no ontology field.
- `Postal Postcode`: Postal postcode, no ontology field.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 23169, 'key': ['Licence Number'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The sample rows support the legal name, trading name, premises address, suburb and postcode mappings, and the postal and geo columns are correctly left unmapped. I found no blocking meaning errors. The remaining points are advisory: the constant state basis, the premises-versus-registered address caveat, and the uniqueness check for record_id.
  - [advisory] `address.state<-Licence Number`: The constant VIC is anchored to the Licence Number column, which is an identifier and says nothing about state. The anchor is filled on every sample row, so it meets the rule, but the basis for 'every row is in Victoria' rests only on the config's reason text quoting the title, which the sample rows do not show. (suggested: Keep the constant only if the dataset title or metadata is confirmed to cover Victoria only, and record that basis in reason. Consider anchoring to a clearly filled jurisdictional-type column if one exists, or note in the reason that the anchor is arbitrary.)
  - [advisory] `address.full<-Street Address`: Street Address is the licensed premises address (e.g. 'TENANCY FB 184, CHADSTONE SHOPPING CENTRE', 'SHOP W03 199 WILLIAM STREET'), not the entity's registered or head-office address. The mapping states it as the entity's address without qualification. (suggested: Lower mapping_confidence and state in the reason that this is the licensed premises address, not a registered address for the licensee.)
  - [advisory] `record_id`: Licence Number is used as record_id, but the mapping does not show a check that it is unique across rows. Licence Number is also a licence identifier, not an entity identifier. (suggested: Confirm uniqueness with check_unique on Licence Number, or hash the row if duplicates appear.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee`: `MELGT PTY LTD` → `MELGT PTY LTD`; `FORTUNE HOUSE PTY LTD` → `FORTUNE HOUSE PTY LTD`; `CONRAD JOSEPH MUTHUKUMARU` → `CONRAD JOSEPH MUTHUKUMARU`
- `entity.trading_name<-Trading As`: `QQ DUMPLING` → `QQ DUMPLING`; `FORTUNE HOUSE` → `FORTUNE HOUSE`; `CORLAM KITCHEN` → `CORLAM KITCHEN`
- `address.full<-Street Address`: `152 STATION STREET` → `152 STATION STREET`; `272 BLACKBURN ROAD` → `272 BLACKBURN ROAD`; `252 BLACKBURN ROAD` → `252 BLACKBURN ROAD`
- `address.locality<-Suburb`: `FAIRFIELD` → `FAIRFIELD`; `DONCASTER EAST` → `DONCASTER EAST`; `GLEN WAVERLEY` → `GLEN WAVERLEY`
- `address.postcode<-Postcode`: `3078` → `3078`; `3109` → `3109`; `3150` → `3150`
- `address.state<-Licence Number`: `31237375` → `VIC`; `31261560` → `VIC`; `31271395` → `VIC`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
