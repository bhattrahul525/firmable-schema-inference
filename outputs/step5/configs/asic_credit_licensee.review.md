# Review packet (round-2 agent): validated_config

**Dataset:** ASIC – Credit Licensee Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `credit_lic_202611.tsv` (sha256 `74fc2f5f73e6…`)

## How this ended

- Outcome **validated_config**.
- 8 model turns, 8 tool calls, $0.0094, 39.18s (download and human waits excluded). Trace: `logs/agent_runs/asic_credit_licensee/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "tsv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
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
| 2 | `CRED_LIC_NAME` | `entity.entity_type` | entity_type_from_suffix | W | held_out | 0.60 | 100.0% | **0.60** |
| 3 | `CRED_LIC_ABN_ACN` | `entity.abn` | abn | W | held_out | 0.85 | 100.0% | **0.85** |
| 4 | `CRED_LIC_ABN_ACN` | `entity.acn` | acn | W | held_out | 0.80 | 100.0% | **0.80** |
| 5 | `CRED_LIC_BN` | `entity.trading_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 6 | `CRED_LIC_LOCALITY` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 7 | `CRED_LIC_STATE` | `address.state` | state_code | W | held_out | 0.90 | 100.0% | **0.90** |
| 8 | `CRED_LIC_PCODE` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `CRED_LIC_NAME`: Register of credit licence holders; the row subject is the licensee holding the licence (rule 5b), but the header does not itself label it as the licensee name, so confidence is capped at 0.7.
2. `entity.entity_type` ← `CRED_LIC_NAME`: No explicit entity type column; suffix rule on the licensee name.
3. `entity.abn` ← `CRED_LIC_ABN_ACN`: Column mixes 11-digit ABNs and 9-digit ACNs; the split is by digit length, with checksum validation via the abn transform.
4. `entity.acn` ← `CRED_LIC_ABN_ACN`: Split by digit length: 9-digit values are ACNs, checksum validated via the acn transform.
5. `entity.trading_name` ← `CRED_LIC_BN`: Business name column, a name traded under; not the registered name.
6. `address.locality` ← `CRED_LIC_LOCALITY`: Locality column.
7. `address.state` ← `CRED_LIC_STATE`: State column.
8. `address.postcode` ← `CRED_LIC_PCODE`: Postcode column.

## Left unmapped (not guessed)

- `CRED_LIC_STATUS`: Credit licence status (APPR/SUSP) describes the licence, not the entity's own status; no licence-status field in the ontology subset. Left out to avoid a wrong entity.status claim.
- `REGISTER_NAME`: Constant register label, carries no claim about the entity.
- `CRED_LIC_AFSL_NUM`: AFSL number duplicates the licence number in most rows; no canonical field for it.
- `CRED_LIC_END_DT`: Empty in all rows.
- `CRED_LIC_STATUS_HISTORY`: Free-text status history; no canonical field.
- `CRED_LIC_LAT`: Geocode; no canonical field.
- `CRED_LIC_LNG`: Geocode; no canonical field.
- `CRED_LIC_EDRS`: External dispute resolution scheme; no canonical field.
- `CRED_LIC_AUTHORISATIONS`: Licence authorisation text; no canonical field.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 4313, 'key': ['CRED_LIC_NUM'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main concern is entity.status: it maps a credit licence status (APPR/SUSP) onto the entity's own status, which the source does not support. The ABN/ACN split, the 5b legal_name mapping, and the trading name and address mappings are broadly sound but need confidence values and a few clarifications. The valid_from mapping from CRED_LIC_START_DT is acceptable because that column records when the licence started.
  - [blocking] `entity.status<-CRED_LIC_STATUS`: The source column CRED_LIC_STATUS holds the status of the credit licence (APPR = approved, SUSP = suspended), but the mapping writes it to entity.status as the status of the entity. Rows such as FIRST MORTGAGE MANAGED INVESTMENTS LIMITED therefore get the claim that the company is 'active', which the source does not state. (suggested: Remove the entity.status mapping, or record the licence status under a field that means licence status if the ontology has one. If it is kept, the reason must say it is licence status and not entity status.)
  - [advisory] `entity.abn / entity.acn`: CRED_LIC_ABN_ACN mixes 11-digit ABNs and 9-digit ACNs, and both fields read the same column. The config relies on the abn and acn transforms to split them by length, which is acceptable, but no mapping_confidence or note records that the split is by length alone. (suggested: Add a mapping_confidence and a reason that states the split is by digit length and checksum. No `when` clause is needed unless another column says which rows hold an ABN or ACN.)
  - [advisory] `entity.legal_name<-CRED_LIC_NAME`: The name is mapped to legal_name under rule 5b, which needs the source to label the name as the licensee or holder. The header CRED_LIC_NAME does not say so by itself, and the config has no mapping_confidence. Under 5b that means confidence should be 0.7 or lower unless the register's label is cited. (suggested: Add a mapping_confidence for the legal_name mapping. Cite the register's own wording (for example, the licensee column definition) to support the 5b mapping, or lower the confidence to 0.7 or below.)
  - [advisory] `entity.status<-CRED_LIC_STATUS`: The map_values table covers only APPR and SUSP. The profile shows only APPR, so other licence status codes, such as cancelled or expired, are unmapped and will be handled silently. (suggested: Confirm the full set of CRED_LIC_STATUS values in the profile and map each one, or leave unseen values unmapped with an explicit note.)
  - [advisory] `record_id`: record_id uses CRED_LIC_NUM but the config does not say it was checked for uniqueness (check_unique) or what happens if it is not unique. (suggested: Record a check_unique result for CRED_LIC_NUM, or use hash_row if uniqueness cannot be confirmed.)
  - [advisory] `config (source reliability and confidence)`: The config has no mapping_confidence per field and no source_reliability with its basis, although rules 14 and 16 require them. (suggested: Add mapping_confidence for each field and a source_reliability value per claim kind, with source_reliability_basis explaining the judgement.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-CRED_LIC_NAME`: `FIRST MORTGAGE MANAGED INVESTMENTS LIMITED` → `FIRST MORTGAGE MANAGED INVESTMENTS LIMITED`; `AIA AUSTRALIA LIMITED` → `AIA AUSTRALIA LIMITED`; `PERPETUAL TRUSTEE COMPANY LIMITED` → `PERPETUAL TRUSTEE COMPANY LIMITED`
- `entity.entity_type<-CRED_LIC_NAME`: `FIRST MORTGAGE MANAGED INVESTMENTS LIMITED` → `company`; `AIA AUSTRALIA LIMITED` → `company`; `PERPETUAL TRUSTEE COMPANY LIMITED` → `company`
- `entity.abn<-CRED_LIC_ABN_ACN`: `39089507899` → `39089507899`; `79004837861` → `79004837861`; `42000001007` → `42000001007`
- `address.locality<-CRED_LIC_LOCALITY`: `BURLEIGH HEADS` → `BURLEIGH HEADS`; `MELBOURNE` → `MELBOURNE`; `SYDNEY` → `SYDNEY`
- `address.state<-CRED_LIC_STATE`: `QLD` → `QLD`; `VIC` → `VIC`; `NSW` → `NSW`
- `address.postcode<-CRED_LIC_PCODE`: `4220` → `4220`; `3004` → `3004`; `2000` → `2000`
- `entity.trading_name<-CRED_LIC_BN`: `AIA AUSTRALIA` → `AIA AUSTRALIA`; `PERPETUAL FUNDS MANAGEMENT` → `PERPETUAL FUNDS MANAGEMENT`; `BFG FINANCIAL SERVICES` → `BFG FINANCIAL SERVICES`
- `entity.acn<-CRED_LIC_ABN_ACN`: `107895652` → `107895652`; `108548750` → `108548750`; `123131957` → `123131957`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
