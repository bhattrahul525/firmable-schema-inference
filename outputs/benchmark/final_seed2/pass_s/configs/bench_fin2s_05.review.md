# Review packet (round-2 agent): validated_config

**Dataset:** Consultancies, contractors and Contracts over 10K  - OIC — Office of the Information Commissioner  
**Licence:** Creative Commons Attribution-NoDerivatives 4.0  
**File:** `202627_oic_contract-disclosure-report-1.xlsx` (sha256 `74156a48b119…`)

## How this ended

- Outcome **validated_config**.
- 6 model turns, 6 tool calls, $0.0826, 22.25s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_05/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "xlsx", "header_rows": 1}`
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
| 2 | `Supplier ABN` | `entity.abn` | abn | W | unverified | 0.90 | n/a | **0.50** |
| 3 | `Supplier address` | `address.full` | clean_whitespace | W | unverified | 0.80 | n/a | **0.50** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name`: supplier name
2. `entity.abn` ← `Supplier ABN`: supplier ABN
3. `address.full` ← `Supplier address`: supplier address

## Fields without enough held-out evidence

No held-out test was possible: the file has too few rows, so every field is judged on rows the agent saw (evidence `training`) or on nothing (`unverified`).
- `entity.legal_name<-Supplier name`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `Robert Walters Pty LTD` → `Robert Walters Pty LTD`; `Kingston Human Capital Pty Ltd` → `Kingston Human Capital Pty Ltd`; `Brooke Institute Pty Ltd` → `Brooke Institute Pty Ltd`
- `entity.abn<-Supplier ABN`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `18 079 521 618` → `18079521618`; `15 162 677 830` → `15162677830`; `11 162 612 553` → `11162612553`
- `address.full<-Supplier address`: evidence **unverified** (capped at 0.5); whole file: 4 populated, 4 judged, 4 ok, 0 rejected. Training examples: `Level 23, 376-390 Collins Street VIC 3000` → `Level 23, 376-390 Collins Street VIC 3000`; `Level 17 307 Queen Street, Brisbane QLD 4002` → `Level 17 307 Queen Street, Brisbane QLD 4002`; `Level 1, 187 Wakefield Street, Adelaide SA 5000` → `Level 1, 187 Wakefield Street, Adelaide SA 5000`

## Left unmapped (not guessed)

- `Agency name`: government buyer
- `Agency address`: government buyer
- `Contract category group`: contract detail
- `Parent contract/Head agremeent/Common-use supply arrangement number`: contract detail
- `Contract description/name`: contract detail
- `Award contract date`: transaction date
- `Contract value`: contract detail
- `Variation to contract (Yes/No)`: contract detail
- `Specific confidentiality provision used`: contract detail
- `Procurement method`: contract detail
- `Reason for use of limited tendering`: contract detail
- `Form of contract`: contract detail
- `Number of offers sought`: contract detail
- `Evaluation criteria and weightings`: contract detail
- `Deliverables`: contract detail
- `Contract milestones`: contract detail
- `Contract performance management`: contract detail
- `Additional details`: contract detail
- `Consultancy (Yes/No)`: contract detail

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 4, 'key': ['Contract reference number'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping follows the rules. Supplier name, ABN and address are mapped as the entity, and the government buyer columns are unmapped with the reason 'government buyer'. The award date is correctly left out of valid_from, since it records a transaction event. entity_type is left as unknown, and the abn transform produced valid 11-digit values. Every column is either mapped or listed in unmapped. I found nothing I can point to as a meaning error in the examples.

## Examples (raw → value, held-out rows)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
