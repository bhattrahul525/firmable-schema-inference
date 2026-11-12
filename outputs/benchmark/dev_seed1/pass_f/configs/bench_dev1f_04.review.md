# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0112, 55.61s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1f_04/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 2, "header_rows": 1, "skip_rows_after_header": 2}`
- layout: column names from raw row 3; raw rows 4-5 dropped; data starts at raw row 6.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. CONTRACT DISCLOSURE FIELDS | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
2. Financial Year 2020/21 | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ | ∅
3. Description | Agency (Dept or Stat Body) | Agency address | Contract description/name | Award contract date | Contract value | Supplier name | Supplier address | Variation to contract (Yes/No) | Specific confidentiality provision used | Procurement method | Form of contract | Number of offers sought | Evaluation criteria and weightings | Deliverables
4. OCDS name | ∅ | ∅ | Contracts/Title | Contracts/dateSigned | Contracts/value/amount | Parties additionalidentifiers/id | Parties/address | Not listed | ∅ | Tender procurementMethod | ∅ | ∅ | ∅ | ∅
5. KDS | ∅ | ∅ | Contract Name | Contract Awarded Date | Executed Contract Value | not assessed | not assessed | Not listed | ∅ | Contract Type | ∅ | ∅ | ∅ | ∅
6. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Provision of Kitchen Consumables  | 31/07/2020 | $175,000.00 | Bunzl Outsourcing  | 42-44 Ponzo Street, Woree | Yes | No | Confined  | Variation  | N/A | N/A | Yes
7. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Provision of Groceries, Beverages, Froze | 31/07/2020 | $1,980,000.00 | Bidfood Cairns  | 38 Redden Street, Cairns | Yes | No | Confined  | Variation  | N/A | N/A | Yes
8. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Provision of Frozen Foods | 31/07/2020 | $1,160,000.00 | MaxStocks Frozen Foods Pty Ltd | 347 Spence Street, Bungalow | Yes | No | Confined  | Variation  | N/A | N/A | Yes
9. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Order Form - Cleaning Services - SCU  | 1/06/2020 | $24,440.00 | Taylor Made Enterprises Pty Ltd  | 121 Enmore Street, Manoora QLD  | No | No | Open  | Order Form  | N/A | N/A | Yes
10. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Comprehensive Maintenance of Automatic D | 1/07/2020 | $25,648.00 | Kone Elevators Pty Ltd  | 40 Campbell Street, Bowen Hills QLD  | No | No  | Open  | Extension  | N/A | N/A | Yes
11. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Water Treatment of Cooling Towers and Bo | 1/07/2020 | $10,668.00 | Maxwells H20 Services Pty Ltd  | 5 Commercial Place, Cairns QLD  | Yes | No | Confined  | Variation to extend  | N/A | N/A | Yes 
12. ∅ | CHHHS | 165 The Esplanade, Cairns, QLD | Order Form - Design Placemat - CHHHS Inf | 26/06/2020 | $12,500.00 | Deloitte Financial Advisory Services  | Level 23, Riverside Centre 123 Eagle Str | No | No | Open  | Order Form  | N/A | N/A | Yes 

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 2 | `Supplier address` | `address.full` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 3 | `Supplier ABN` | `entity.abn` | abn | W | unverified | 0.90 | 100.0% | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column labelled Supplier name; the row's subject is the supplier party.
2. `address.full` ← `Supplier address`: Supplier address column for the supplier party.
3. `entity.abn` ← `Supplier ABN`: Column labelled Supplier ABN for the supplier party; checksum validated.

## Fields without enough held-out evidence

- `entity.abn<-Supplier ABN`: evidence **unverified** (capped at 0.5); whole file: 1 populated, 1 judged, 1 ok, 0 rejected. Training examples: none

## Left unmapped (not guessed)

- `Description`: empty column
- `Agency (Dept or Stat Body)`: government buyer, not the supplier entity
- `Agency address`: address of the government buyer
- `Contract description/name`: contract title, not an entity attribute
- `Award contract date`: date of the contract event, not when the entity's identity became true
- `Contract value`: contract financial value, not mapped to ontology
- `Variation to contract (Yes/No)`: contract attribute
- `Specific confidentiality provision used`: contract attribute
- `Procurement method`: contract attribute
- `Form of contract`: contract attribute
- `Number of offers sought`: contract attribute
- `Evaluation criteria and weightings`: contract attribute
- `Deliverables`: contract attribute
- `Contract milestones`: contract attribute
- `Contract performance management`: contract attribute
- `Contract reference number`: contract identifier, not entity identifier
- `Contract category group`: procurement category, not ANZSIC industry code
- `Parent contract number/SOA`: contract identifier
- `Commence date`: contract event date, sparse
- `Finish date`: contract end date for the disclosed contract, an event date not the entity's own status end

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 49, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The core mapping is sound: Supplier name goes to entity.legal_name, which the data labels as the supplier name, and Supplier address goes to address.full for the supplier party. The buyer columns are correctly excluded, entity_type is correctly left unknown, and the contract columns are correctly unmapped. I found no blocking errors. The main gaps are that Supplier ABN is wrongly excluded with a reason the held-out rows contradict, Finish date's unmapped reason is inaccurate, and supplier address components could be parsed further.
  - [advisory] `entity.abn<-Supplier ABN`: Supplier ABN is listed as unmapped on the grounds that it is empty in training rows. The held-out row for Rauland Australia carries a populated value ('63 056 360 653'), so the stated reason does not hold and the column is not being used. Rule 6 requires an identifier column like this to go through the abn transform. (suggested: Map Supplier ABN to entity.abn with the abn checksum transform (separate spaces before validation), and state the reason accurately if any rows remain blank.)
  - [advisory] `Finish date`: Finish date is marked as an empty column, but the held-out row for Rauland Australia has a value ('1/02/2026'). The reason is inaccurate. Leaving it unmapped is still defensible, because it is a contract end date and not the entity's registration or status end date. (suggested: Correct the unmapped reason to say it is a contract event date, not the entity's own status end, and keep it unmapped.)
  - [advisory] `address.full<-Supplier address`: The supplier address contains a state and postcode in several rows (e.g. '249 Boundary Street, West End 4101', '21 Enmore Street Manoora QLD', '38 Redden Street, Cairns'), but only the full string is mapped. Components the source states could be parsed further. (suggested: Consider parsing address.state and address.postcode from the supplier address where the source states them explicitly, keeping address.full as the raw string. Leave them unmapped where the text does not state them.)
- Critique: The mapping is largely sound. The supplier name, supplier address and supplier ABN are mapped to the supplier party, and the government buyer (Agency) and contract attributes are correctly left unmapped. The ABN in the example checks out (63 056 360 653 passes the checksum). I found no blocking meaning errors. The remaining points are advisory: parsing the supplier address into locality, state and postcode, the registered-versus-supplier-name nuance, and the reader skip-row settings.
  - [advisory] `address.full<-Supplier address`: The supplier address is mapped only as a whole string with whitespace cleaning. Several rows contain a state and postcode (e.g. '249 Boundary Street, West End 4101', '3 Acacia Place, Notting Hill, Victoria'), which could be parsed into address.locality, address.state and address.postcode. The state is also written inconsistently ('Victoria' versus 'QLD' and 'NSW'), and the enum requires codes such as VIC. (suggested: Keep address.full, and consider adding parsed locality, state (normalised to the enum codes) and postcode sourced from the same column, or record that parsing was not attempted.)
  - [advisory] `entity.legal_name<-Supplier name`: The column is labelled 'Supplier name', which meets the legal_name rule. The names shown, such as 'Stryker', 'Bidfood Cairns' and 'Deloitte Touche Tohmatsu', look like trading or brand names rather than registered names. Nothing in the source confirms registration, so the claim is only as strong as the supplier label. (suggested: Keep the mapping, since the label supports it, but consider a lower mapping_confidence or a source_reliability note stating that the name is the supplier name as given in the contract, not a checked registered name.)
  - [advisory] `reader`: The config skips 2 rows before the header and 2 rows after it. This is unusual for a contract export and could drop or misalign data if the layout differs from what was sampled. It is not a meaning error on the rows shown. (suggested: Confirm the skip counts against the raw file layout and document why they are needed.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name`: `Rauland Australia ` → `Rauland Australia`; `Ozcare ` → `Ozcare`; `Olympus Pty Ltd ` → `Olympus Pty Ltd`
- `address.full<-Supplier address`: `249 Boundary Street, West End 4101` → `249 Boundary Street, West End 4101`; `66 River Terrace Kanagroo Point ` → `66 River Terrace Kanagroo Point`; `3 Acacia Place, Notting Hill, Victoria ` → `3 Acacia Place, Notting Hill, Victoria`
- `entity.abn<-Supplier ABN`: `63 056 360 653` → `63056360653`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
