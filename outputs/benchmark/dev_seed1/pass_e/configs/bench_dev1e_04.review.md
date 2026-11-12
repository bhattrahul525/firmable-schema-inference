# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0100, 45.3s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_04/trace.jsonl`.
- Evidence the agent gave at finish (its words): Read with skip_rows 2 and header_rows 3 (three header lines merged; 49 data rows). Award dates parse 100% with %d/%m/%Y. Critique raised only advisory issues, addressed in the reasons.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier name Parties additionalidentifiers/id not assessed` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `Supplier address Parties/address not assessed` | `address.full` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 3 | `Supplier ABN Parties/identifier/uri not assessed` | `entity.abn` | clean_whitespace → abn | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name Parties additionalidentifiers/id not assessed`: Column is labelled Supplier name; the data identifies the supplier as the contracting party, so it is the supplier's name.
2. `address.full` ← `Supplier address Parties/address not assessed`: Supplier address column, full free-text address of the supplier. Many addresses are partial (no state or postcode), so they are kept as free text only.
3. `entity.abn` ← `Supplier ABN Parties/identifier/uri not assessed`: Supplier ABN column; checksum-validated. Populated for only some suppliers (sparse overall).

## Left unmapped (not guessed)

- `Description OCDS name KDS`: Empty column in the data rows (only used as a header annotation).
- `Agency (Dept or Stat Body) OCDS name`: Government buyer (CHHHS), not the supplier entity.
- `Agency address OCDS name`: Address of the government buyer, not the supplier.
- `Contract description/name Contracts/Title Contract Name`: Contract title; no ontology field for contract descriptions.
- `Award contract date Contracts/dateSigned Contract Awarded Date`: Contract award date; not an entity registration date and not a licence validity start, so not mapped to date_registered or valid_from.
- `Contract value Contracts/value/amount Executed Contract Value`: Contract value; no ontology field.
- `Variation to contract (Yes/No) Not listed Not listed`: Contract attribute; no ontology field.
- `Specific confidentiality provision used Not listed`: Contract attribute; no ontology field.
- `Procurement method Tender procurementMethod Contract Type`: Procurement attribute; no ontology field.
- `Form of contract Tender procurementMethod`: Procurement attribute; no ontology field.
- `Number of offers sought Tender procurementMethod`: Procurement attribute; no ontology field.
- `Evaluation criteria and weightings Tender procurementMethod`: Procurement attribute; no ontology field.
- `Deliverables Tender procurementMethod`: Procurement attribute; no ontology field.
- `Contract milestones Tender procurementMethod`: Procurement attribute; no ontology field.
- `Contract performance management Tender procurementMethod`: Procurement attribute; no ontology field.
- `Contract reference number Contracts/AwardID Tender Number`: Contract reference; only 76% filled, so record_id uses hash_row instead.
- `Contract category group Contracts/items/classification/description Category Group`: Procurement category; not an ANZSIC industry code of the entity, so not mapped to industry_code.
- `Parent contract number/SOA Contracts Contracts`: Parent contract reference; no ontology field.
- `Commence date Contracts/period/Start Date Planned Commencement Date`: Planned contract commencement, not a licence validity start; left unmapped.
- `Finish date Contracts/period/endDate Planned Finish Date`: Empty column.

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 49, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: I found no blocking meaning errors. Supplier name maps to legal_name under the supplier-name rule, the government buyer and agency address are correctly left unmapped, the sample ABN passes its checksum, and contract dates are correctly kept out of date_registered and valid_from. The remaining points are advisory: an inaccurate reason text for the ABN, incomplete address parsing, and envelope fields that are not shown.
  - [advisory] `entity.abn<-Supplier ABN Parties/identifier/uri not assessed`: The config reason says the Supplier ABN column is empty in the sample rows, but the Rauland Australia row carries 63 056 360 653. That ABN passes the checksum, so the mapping itself is sound; only the stated rationale is inaccurate. (suggested: Correct the reason text to note that the column is populated for some suppliers (e.g. Rauland Australia) and sparse overall.)
  - [advisory] `address.full<-Supplier address Parties/address not assessed`: Several supplier addresses are partial or lack a state or postcode (e.g. '3 Acacia Place, Notting Hill, Victoria', '3 Bloomfield Close, Forest Gardens', 'Suite 5.03 Building C, Foundation Park 7-11 Talavera Rd'). Mapping the raw text to address.full is correct, but address.state and address.postcode are left unpopulated even where the text states them. (suggested: Keep address.full as mapped. Consider a later parsing step for state and postcode, recorded as derived, and note that many addresses are incomplete.)
  - [advisory] `observation.licence`: The config does not show how the required licence envelope field is set, nor source_reliability, extractor_version or source_record_id. The envelope is therefore not evidenced in this mapping. (suggested: Confirm the licence is taken from the CKAN metadata (or recorded as 'unknown' and flagged), and that the envelope fields are populated by the engine.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name Parties additionalidentifiers/id not assessed`: `Kone Elevators Pty Ltd ` → `Kone Elevators Pty Ltd`; `Maxwells H20 Services Pty Ltd ` → `Maxwells H20 Services Pty Ltd`; `Rauland Australia ` → `Rauland Australia`
- `address.full<-Supplier address Parties/address not assessed`: `40 Campbell Street, Bowen Hills QLD ` → `40 Campbell Street, Bowen Hills QLD`; `5 Commercial Place, Cairns QLD ` → `5 Commercial Place, Cairns QLD`; `249 Boundary Street, West End 4101` → `249 Boundary Street, West End 4101`
- `entity.abn<-Supplier ABN Parties/identifier/uri not assessed`: `63 056 360 653` → `63056360653`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
