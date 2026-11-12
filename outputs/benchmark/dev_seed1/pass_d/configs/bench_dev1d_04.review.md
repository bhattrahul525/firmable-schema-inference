# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0085, 40.22s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1d_04/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded CSV (51 data rows after header; rows 1-2 are OCDS/KDS annotation rows that will produce non-business records; the 'Contracts/dateSigned' and 'Contract Awarded Date' rejects in date tests came from them). Supplier ABN is ~8% filled. Validation on held-out rows: 0 hard failures, parse rate 1.0 for mapped fields.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier name` | `entity.legal_name` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `Supplier ABN` | `entity.abn` | clean_whitespace → abn | W | 0.90 | 100.0% | **0.90** |
| 3 | `Supplier address` | `address.full` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column is the contracted supplier name, the entity each row is about. Treated as the supplier name claim, moderate confidence that it is the registered name.
2. `entity.abn` ← `Supplier ABN`: Supplier ABN column, checksum-validated. Mostly blank in this file.
3. `address.full` ← `Supplier address`: Supplier's address, kept as full text including any embedded state or postcode.

## Left unmapped (not guessed)

- `Description`: Empty in data rows; holds annotation text in the first two rows
- `Agency (Dept or Stat Body)`: government buyer, not the supplier
- `Agency address`: government buyer address
- `Contract description/name`: contract title, not an entity name
- `Award contract date`: contract award date; not a registration or licence start
- `Contract value`: contract value, no ontology field
- `Variation to contract (Yes/No)`: no ontology field
- `Specific confidentiality provision used`: no ontology field
- `Procurement method`: no ontology field
- `Form of contract`: no ontology field
- `Number of offers sought`: no ontology field
- `Evaluation criteria and weightings`: no ontology field
- `Deliverables`: no ontology field
- `Contract milestones`: no ontology field
- `Contract performance management`: no ontology field
- `Contract reference number`: contract reference, no ontology field
- `Contract category group`: no ontology field
- `Parent contract number/SOA`: no ontology field
- `Commence date`: contract start, not a licence/status validity period
- `Finish date`: contract end, not a licence/status validity period

## Needs a transform the engine does not have

- `Contract value`: currency strings with $ and thousands separators; no numeric transform, and no ontology field anyway

## Checks

- Duplicate record ids in held-out rows: {'rows': 51, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: No blocking meaning errors. The supplier name, supplier ABN and supplier address are mapped to the supplier entity, which is correct. The ABN checksum for 63 056 360 653 validates. The government buyer, the contract dates and the other contract fields are correctly left unmapped, and contract dates are not treated as licence validity. The remaining points are advisory: the observed_at timestamp conflicts with a later award date in the data, state and postcode could be parsed from the address, and a unique contract reference could serve as record_id.
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, which is 2021-08-02, but the last example row has an Award contract date of 13/08/2021, after that timestamp. A claim cannot have been stated before the award it describes, so the metadata timestamp may not reflect when these rows were stated. (suggested: Verify the dataset's resource_last_modified value for this resource, and consider whether a per-row statement date exists or whether the observation time needs a caveat.)
  - [advisory] `address.state`: The supplier address column often contains the state (for example 'Manoora QLD', 'Brisbane City QLD', 'Cairns'), but no address.state or address.postcode mapping is configured. The postcode is also embedded in some values (for example '249 Boundary Street, West End 4101'). (suggested: Consider parsing state and postcode from the supplier address with a transform if one exists. Otherwise, record in the config that these are left inside address.full.)
  - [advisory] `record_id`: record_id uses hash_row, but the 'Contract reference number' column appears unique per row in the sample and could identify each row directly. Hashing the whole row also means any re-export that changes a field such as the contract value would produce a new record id. (suggested: Check whether 'Contract reference number' is unique across the file using check_unique. If it is, use it as the record_id column and keep hash_row only as a fallback.)
  - [advisory] `entity.legal_name<-Supplier name`: Some supplier names look like short or trading-style names (for example 'QRMC', 'Benstar', 'Deloitte'). The column is the contracted supplier name, which rule 5 accepts as the supplier name. However, the reason text says the data does not state it is the registered name, which is an inconsistency with that rule. (suggested: Keep the mapping to legal_name, since the column is the supplier name. Revise the reason to say it is the contracted supplier name, and treat legal_name as a claim with moderate mapping confidence.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name`: `Taylor Made Enterprises Pty Ltd ` → `Taylor Made Enterprises Pty Ltd`; `Maxwells H20 Services Pty Ltd ` → `Maxwells H20 Services Pty Ltd`; `Rauland Australia ` → `Rauland Australia`
- `address.full<-Supplier address`: `121 Enmore Street, Manoora QLD ` → `121 Enmore Street, Manoora QLD`; `5 Commercial Place, Cairns QLD ` → `5 Commercial Place, Cairns QLD`; `249 Boundary Street, West End 4101` → `249 Boundary Street, West End 4101`
- `entity.abn<-Supplier ABN`: `63 056 360 653` → `63056360653`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
