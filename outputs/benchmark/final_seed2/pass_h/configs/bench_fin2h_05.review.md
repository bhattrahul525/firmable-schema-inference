# Review packet (round-2 agent): validated_config

**Dataset:** Consultancies, contractors and Contracts over 10K  - OIC — Office of the Information Commissioner  
**Licence:** Creative Commons Attribution-NoDerivatives 4.0  
**File:** `202627_oic_contract-disclosure-report-1.xlsx` (sha256 `74156a48b119…`)

## How this ended

- Outcome **validated_config**.
- 10 model turns, 10 tool calls, $0.0072, 34.61s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_05/trace.jsonl`.
- Evidence the agent gave at finish (its words): Resource 4 (2026/27 workbook) read from sheet 'upload template': 4 data rows, 23 columns; Contract reference number unique; Supplier ABN passes abn checksum on all 4 rows; Award contract date parses as ISO dates.

## Reader and record settings

- reader: `{"format": "xlsx", "sheet": "upload template", "header_rows": 1, "encoding": "utf-8-sig", "skip_rows": 0}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `Contract reference number` — 0 duplicate / blank keys of 4 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 5 raw rows of the file (numbered as skip_rows counts them; never held out):

1. Contract reference number | Agency name | Agency address | Contract category group | Parent contract/Head agremeent/Common-us | Contract description/name | Award contract date | Contract value | Supplier ABN | Supplier name | Supplier address | Variation to contract (Yes/No) | Specific confidentiality provision used | Procurement method | Reason for use of limited tendering
2. CTR26-01 | Office of the Information Commissioner | Level, 7, 53 Albert Street, Brisbane, Ql | Goods and Services | GGS0060 | Contractor  | 2026-07-15 00:00:00 | 248105 | 18 079 521 618 | Robert Walters Pty LTD | Level 23, 376-390 Collins Street VIC 300 | No | No | ∅ | ∅
3. CTR26-02 | Office of the Information Commissioner | Level, 7, 53 Albert Street, Brisbane, Ql | Goods and Services | GGS0060 | Contractor | 2026-08-17 00:00:00 | 73651 | 15 162 677 830 | Kingston Human Capital Pty Ltd | Level 17 307 Queen Street, Brisbane QLD  | No | No | ∅ | ∅
4. OIC-26CRM/1 | Office of the Information Commissioner | Level, 7, 53 Albert Street, Brisbane, Ql | Information and Communication Technology | ICTSS1303B | CRM Support Arrangement | 2026-09-03 00:00:00 | 148500 | 11 162 612 553 | Brooke Institute Pty Ltd | Level 1, 187 Wakefield Street, Adelaide  | No | No | ∅ | ∅
5. CTR26-03 | Office of the Information Commissioner | Level, 7, 53 Albert Street, Brisbane, Ql | Goods and Services | GGS0060 | Contractor  | 2026-10-08 00:00:00 | 170000 | 18 079 521 618 | Robert Walters Pty LTD | Level 23, 376-390 Collins Street VIC 300 | No | No | ∅ | ∅

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Supplier name` | `entity.legal_name` | clean_whitespace | W | unverified | 0.85 | n/a | **0.50** |
| 2 | `Supplier ABN` | `entity.abn` | clean_whitespace → abn | W | unverified | 0.95 | n/a | **0.50** |
| 3 | `Supplier address` | `address.full` | clean_whitespace | W | unverified | 0.85 | n/a | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: Column is the contract supplier's name; in a contract disclosure the supplier is the registered counterparty.
2. `entity.abn` ← `Supplier ABN`: Supplier ABN with spaces, checksum-validated.
3. `address.full` ← `Supplier address`: Supplier's postal/business address.

## Fields without enough held-out evidence

No held-out test was possible: the file has too few rows, so every field is judged on rows the agent saw (evidence `training`) or on nothing (`unverified`).
- `entity.legal_name<-Supplier name`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `Robert Walters Pty LTD` → `Robert Walters Pty LTD`; `Kingston Human Capital Pty Ltd` → `Kingston Human Capital Pty Ltd`; `Brooke Institute Pty Ltd` → `Brooke Institute Pty Ltd`
- `entity.abn<-Supplier ABN`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `18 079 521 618` → `18079521618`; `15 162 677 830` → `15162677830`; `11 162 612 553` → `11162612553`
- `address.full<-Supplier address`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `Level 23, 376-390 Collins Street VIC 3000` → `Level 23, 376-390 Collins Street VIC 3000`; `Level 17 307 Queen Street, Brisbane QLD 4002` → `Level 17 307 Queen Street, Brisbane QLD 4002`; `Level 1, 187 Wakefield Street, Adelaide SA 5000` → `Level 1, 187 Wakefield Street, Adelaide SA 5000`

## Left unmapped (not guessed)

- `Agency name`: government buyer, not the supplier (rule 4)
- `Agency address`: government buyer address, not the supplier
- `Contract category group`: procurement category, not an industry code
- `Parent contract/Head agremeent/Common-use supply arrangement number`: procurement arrangement reference
- `Contract description/name`: contract description; no entity field
- `Award contract date`: date of the contract award event, not when the supplier's registration became true (rule 10)
- `Contract value`: transaction value; no ontology field
- `Variation to contract (Yes/No)`: contract attribute; no ontology field
- `Specific confidentiality provision used`: contract attribute; no ontology field
- `Procurement method`: contract attribute
- `Reason for use of limited tendering`: contract attribute
- `Form of contract`: contract attribute
- `Number of offers sought`: contract attribute
- `Evaluation criteria and weightings`: contract attribute
- `Deliverables`: contract attribute
- `Contract milestones`: contract attribute
- `Contract performance management`: contract attribute
- `Additional details`: contract attribute
- `Consultancy (Yes/No)`: contract attribute; no ontology field

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 4, 'key': ['Contract reference number'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The core mappings hold up: 'Supplier name' to legal_name, 'Supplier ABN' to abn, and 'Supplier address' to address.full. Both sample ABNs pass the checksum. The government buyer columns and the award date are correctly left unmapped under rules 4 and 10. The main concern is that the chosen record_id is not shown to be unique, since a contract reference repeats across rows. No blocking meaning errors are visible in the examples.
  - [advisory] `record_id`: The record_id is built from 'Contract reference number', but the sample shows the same reference (CTR26-01) on three identical raw rows. Rule 15 requires a column that uniquely identifies each row (check_unique), and this one does not hold on these examples, so the source_record_id would collide. (suggested: Run check_unique on 'Contract reference number' across the full file. If duplicates exist, use a composite key (for example reference number plus supplier ABN) or hash_row=true, and document the choice.)
  - [advisory] `observation`: The config does not state a licence, source_reliability, or source_reliability_basis. The envelope requires licence, and the sample rows carry no dataset licence information. (suggested: Take the licence from the dataset metadata (CKAN). If none is clear, record 'unknown' and flag it. Add a source_reliability judgement for entity claims with a short basis.)

## Examples (raw → value, held-out rows)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
