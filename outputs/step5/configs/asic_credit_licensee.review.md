# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Credit Licensee Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `credit_lic_202611.tsv` (sha256 `74fc2f5f73e6…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0099, 42.67s (download and human waits excluded). Trace: `logs/agent_runs/asic_credit_licensee/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "delimiter": "\t", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `CRED_LIC_NUM` — 0 duplicate / blank keys of 4313 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)
- `valid_from`: from `CRED_LIC_START_DT` (parse_date); held-out parse rate 100.0%; evidence **held_out**

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. REGISTER_NAME | CRED_LIC_NUM | CRED_LIC_NAME | CRED_LIC_START_DT | CRED_LIC_END_DT | CRED_LIC_STATUS | CRED_LIC_ABN_ACN | CRED_LIC_AFSL_NUM | CRED_LIC_STATUS_HISTORY | CRED_LIC_LOCALITY | CRED_LIC_STATE | CRED_LIC_PCODE | CRED_LIC_LAT | CRED_LIC_LNG | CRED_LIC_EDRS
2. Credit Licence | 219612 | RELI CAPITAL LTD | 04/10/2010 | ∅ | APPR | 80005443292 | 219612 | ∅ | LEONGATHA | VIC | 3953 | -38.4761569 | 145.9458605 | AFCA
3. Credit Licence | 222213 | LA TROBE FINANCIAL ASSET MANAGEMENT LIMI | 16/03/2011 | ∅ | APPR | 27007332363 | 222213 | ∅ | MELBOURNE | VIC | 3000 | -37.8142454 | 144.9631732 | AFCA
4. Credit Licence | 222640 | GLOBAL MUTUAL FUNDS PTY LTD | 14/12/2010 | ∅ | APPR | 20090555436 | 222640 | ∅ | MASCOT | NSW | 2020 | -33.9289562 | 151.1951782 | AFCA
5. Credit Licence | 222835 | PLANNING PARTNERS PTY. LTD. | 28/02/2011 | ∅ | APPR | 64090069239 | 222835 | ∅ | CAMBERWELL | VIC | 3124 | -37.8384623 | 145.0740767 | AFCA~FOS
6. Credit Licence | 223246 | RMBL INVESTMENTS LIMITED | 03/03/2011 | ∅ | APPR | 19004493789 | 223246 | ∅ | DANDENONG | VIC | 3175 | -37.98749 | 145.2147923 | AFCA
7. Credit Licence | 224543 | FYG PLANNERS PTY LTD | 21/02/2011 | ∅ | APPR | 55094972540 | 224543 | ∅ | CAIRNS | QLD | 4870 | -16.9206657 | 145.7721854 | AFCA
8. Credit Licence | 224900 | MELMAIN INVESTMENTS LIMITED | 21/04/2011 | ∅ | APPR | 86090021462 | 224900 | ∅ | COBRAM | VIC | 3644 | -35.9197782 | 145.6484379 | FOS
9. Credit Licence | 225216 | HNW PLANNING PTY LTD | 10/02/2011 | ∅ | APPR | 42083745055 | 225216 | ∅ | ERINA | NSW | 2250 | -33.44 | 151.3927778 | AFCA~FOS
10. Credit Licence | 225759 | LUNAWAVE PTY. LIMITED | 01/01/2011 | ∅ | APPR | 33003565080 | 225759 | ∅ | SYDNEY | NSW | 2000 | -33.8698439 | 151.2082848 | AFCA
11. Credit Licence | 226238 | PROFILE FINANCIAL SERVICES PTY LTD | 15/04/2011 | ∅ | APPR | 32090146802 | 226238 | ∅ | PARRAMATTA | NSW | 2150 | -33.8139843 | 151.002666 | AFCA
12. Credit Licence | 227673 | STACKS MANAGED INVESTMENTS LIMITED | 01/01/2011 | ∅ | APPR | 81085843125 | 227673 | ∅ | TAREE | NSW | 2430 | -31.912864 | 152.4608481 | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `CRED_LIC_NAME` | `entity.legal_name` | clean_whitespace | W | held_out | 0.70 | 100.0% | **0.70** |
| 2 | `CRED_LIC_ABN_ACN` | `entity.abn` | abn [when {"column": "CRED_LIC_ABN_ACN", "matches": "^\\d{11}$"}] | P | held_out | 0.90 | 100.0% | **0.90** |
| 3 | `CRED_LIC_ABN_ACN` | `entity.acn` | acn [when {"column": "CRED_LIC_ABN_ACN", "matches": "^\\d{9}$"}] | P | held_out | 0.85 | 100.0% | **0.85** |
| 4 | `CRED_LIC_BN` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 5 | `CRED_LIC_LOCALITY` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `CRED_LIC_STATE` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |
| 7 | `CRED_LIC_PCODE` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `CRED_LIC_NAME`: Regulator register (ASIC credit licences); the row's subject is the licence holder listed by name. No explicit 'registered' label, so confidence capped under rule 5b.
2. `entity.abn` ← `CRED_LIC_ABN_ACN`: 11-digit values are ABNs (checksum validated).
3. `entity.acn` ← `CRED_LIC_ABN_ACN`: 9-digit values are ACNs (checksum validated).
4. `entity.trading_name` ← `CRED_LIC_BN`: Business name column, a name traded under; not the registered name.
5. `address.locality` ← `CRED_LIC_LOCALITY`: Locality of the licensee.
6. `address.state` ← `CRED_LIC_STATE`: State of the licensee.
7. `address.postcode` ← `CRED_LIC_PCODE`: Postcode of the licensee.

## Left unmapped (not guessed)

- `REGISTER_NAME`: Constant register label 'Credit Licence'.
- `CRED_LIC_END_DT`: Empty in all rows.
- `CRED_LIC_STATUS`: Licence approval status (APPR/SUSP) describes the credit licence, not the entity; not mapped to entity.status.
- `CRED_LIC_STATUS_HISTORY`: Free-text status history; no canonical field.
- `CRED_LIC_AFSL_NUM`: Duplicate of CRED_LIC_NUM; no AFSL field in ontology.
- `CRED_LIC_EDRS`: External dispute resolution scheme; no canonical field.
- `CRED_LIC_LAT`: Geocode; no canonical field.
- `CRED_LIC_LNG`: Geocode; no canonical field.
- `CRED_LIC_AUTHORISATIONS`: Long licence authorisation text; no canonical field.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 4313, 'key': ['CRED_LIC_NUM'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The name, ABN/ACN split, locality, state and postcode mappings follow the rules. The main problem is that the licence approval status is written to the entity's own status, which the register does not support. Several confidence values and the status value coverage also need to be added or confirmed.
  - [blocking] `entity.status<-CRED_LIC_STATUS`: CRED_LIC_STATUS records the status of the credit licence (APPR = approved licence, SUSP = suspended licence), but the mapping writes it to entity.status, which describes the entity itself. The source does not state that the company is active or suspended; a licence can be suspended while the entity is still trading, and the reverse is also possible. (suggested: Remove the entity.status mapping for this column, or map it to a licence-status claim if the ontology has one. If the ontology must keep entity.status here, record the licence status only as an advisory caveat and do not state it as the entity's status.)
  - [advisory] `entity.status<-CRED_LIC_STATUS`: The map_values transform covers only APPR and SUSP. Rule 8 requires every raw value visible in the profile to be considered, and the config does not show whether other codes (for example cancelled or expired) exist in the column or were deliberately left unmapped. (suggested: Confirm the full set of CRED_LIC_STATUS values in the profile and state explicitly how any remaining codes are handled.)
  - [advisory] `entity.legal_name<-CRED_LIC_NAME`: The mapping is justified under rule 5b, since this is a regulator's register and the row's subject is the licence holder. The config gives no mapping_confidence, and rule 5b requires 0.7 or lower without an explicit label. The column header CRED_LIC_NAME does not itself say 'licensee' or 'registered name'. (suggested: Set mapping_confidence to 0.7 or lower for entity.legal_name, citing the register-holder basis, or add an explicit confidence value.)
  - [advisory] `entity.trading_name<-CRED_LIC_BN`: CRED_LIC_BN is a business name, so trading_name is the right target. The config gives no mapping_confidence, and rule 5 caps non-registered name columns at 0.6 or lower. (suggested: Add mapping_confidence of 0.6 or lower to this field.)
  - [advisory] `record_id`: record_id is CRED_LIC_NUM, but the config does not show that it was checked for uniqueness. Rule 15 requires check_unique or hash_row. (suggested: Confirm CRED_LIC_NUM is unique across rows, or fall back to hash_row=true.)
  - [advisory] `valid_from`: valid_from uses CRED_LIC_START_DT, which is the licence start date. That fits rule 10 for the licence, but it is applied to every observation in the row, including name and address claims, which the licence start date does not describe. (suggested: Note in the config that valid_from relates to the licence, or restrict it to the licence-related observations.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-CRED_LIC_NAME`: `FIRST MORTGAGE MANAGED INVESTMENTS LIMITED` → `FIRST MORTGAGE MANAGED INVESTMENTS LIMITED`; `AIA AUSTRALIA LIMITED` → `AIA AUSTRALIA LIMITED`; `PERPETUAL TRUSTEE COMPANY LIMITED` → `PERPETUAL TRUSTEE COMPANY LIMITED`
- `entity.abn<-CRED_LIC_ABN_ACN`: `39089507899` → `39089507899`; `79004837861` → `79004837861`; `42000001007` → `42000001007`
- `address.locality<-CRED_LIC_LOCALITY`: `BURLEIGH HEADS` → `BURLEIGH HEADS`; `MELBOURNE` → `MELBOURNE`; `SYDNEY` → `SYDNEY`
- `address.state<-CRED_LIC_STATE`: `QLD` → `QLD`; `VIC` → `VIC`; `NSW` → `NSW`
- `address.postcode<-CRED_LIC_PCODE`: `4220` → `4220`; `3004` → `3004`; `2000` → `2000`
- `entity.trading_name<-CRED_LIC_BN`: `AIA AUSTRALIA` → `AIA AUSTRALIA`; `PERPETUAL FUNDS MANAGEMENT` → `PERPETUAL FUNDS MANAGEMENT`; `BFG FINANCIAL SERVICES` → `BFG FINANCIAL SERVICES`
- `entity.acn<-CRED_LIC_ABN_ACN`: `107895652` → `107895652`; `108548750` → `108548750`; `123131957` → `123131957`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
