# Review packet (round-2 agent): validated_config

**Dataset:** ASIC - Banned and Disqualified Organisations Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `bd_org_202611.csv` (sha256 `67fc279cf567…`)

## How this ended

- Outcome **validated_config**.
- 7 model turns, 7 tool calls, $0.0914, 21.62s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_06/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "tsv", "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `BD_ORG_ACN` — 0 duplicate / blank keys of 15 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. REGISTER_NAME | BD_ORG_ACN | BD_ORG_NAME | BD_ORG_TYPE | BD_ORG_URL | BD_ORG_START_DT | BD_ORG_END_DT | BD_ORG_COMMENT
2. Banned and Disqualified Organisations | 081402379 | AUSTRALIAN BUSINESS INSURANCE ADVISERS ( | Australian Financial Services banning | Not available | 07/11/2006 | 07/11/2008 | No comment made
3. Banned and Disqualified Organisations | 008876033 | BLACKBURNE & DIXON PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 10/04/2001 | ∅ | No comment made
4. Banned and Disqualified Organisations | 011021640 | BRANNELLY FINANCIAL PTY LTD | Australian Financial Services banning | Not available | 09/02/2009 | 08/02/2015 | No comment made
5. Banned and Disqualified Organisations | 052177009 | CHARTER FINANCE AND INSURANCE PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 31/07/2003 | ∅ | No comment made
6. Banned and Disqualified Organisations | 090251086 | CLAIREMAY PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 05/12/2004 | ∅ | No comment made
7. Banned and Disqualified Organisations | 118554046 | FIRST HOME SHOP PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 04/06/2009 | ∅ | No comment made
8. Banned and Disqualified Organisations | 008853914 | GAMEL WARD PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 24/07/2002 | ∅ | No comment made
9. Banned and Disqualified Organisations | 008669645 | GERALDTON FINANCE COMPANY PTY LIMITED | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 04/03/2002 | ∅ | No comment made
10. Banned and Disqualified Organisations | 009380205 | GLOBAL FINANCE GROUP PTY LTD | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 06/06/1999 | ∅ | No comment made
11. Banned and Disqualified Organisations | 008716872 | KNIGHTSBRIDGE FINANCE PTY LTD (Formerly  | Credit banning by a State or Territory | http://asic.gov.au/online-services/searc | 21/11/2001 | ∅ | No comment made
12. Banned and Disqualified Organisations | 095393007 | M.A.I PACIFIC PTY LTD | Credit Banning | http://download.asic.gov.au/media/132217 | 03/12/2013 | Permanent banning | No comment made

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `BD_ORG_ACN` | `entity.acn` | acn | W | training | 0.95 | n/a | **0.80** |
| 2 | `BD_ORG_NAME` | `entity.legal_name` | clean_whitespace | W | training | 0.70 | n/a | **0.70** |

The model's reasons per field (its words, not verified):

1. `entity.acn` ← `BD_ORG_ACN`: ACN column
2. `entity.legal_name` ← `BD_ORG_NAME`: organisation named on ASIC register with ACN

## Fields without enough held-out evidence

No held-out test was possible: the file has too few rows, so every field is judged on rows the agent saw (evidence `training`) or on nothing (`unverified`).
- `entity.acn<-BD_ORG_ACN`: evidence **training** (capped at 0.8); whole file: 15 populated, 15 judged, 15 ok, 0 rejected. Training examples: `081402379` → `081402379`; `008876033` → `008876033`; `011021640` → `011021640`
- `entity.legal_name<-BD_ORG_NAME`: evidence **training** (capped at 0.8); whole file: 15 populated, 15 judged, 15 ok, 0 rejected. Training examples: `AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD` → `AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD`; `BLACKBURNE & DIXON PTY LTD` → `BLACKBURNE & DIXON PTY LTD`; `BRANNELLY FINANCIAL PTY LTD` → `BRANNELLY FINANCIAL PTY LTD`

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant register title
- `BD_ORG_TYPE`: type of ban, not entity type
- `BD_ORG_URL`: link to register, not website of entity
- `BD_ORG_START_DT`: ban start date, not registration
- `BD_ORG_END_DT`: ban end date
- `BD_ORG_COMMENT`: free comment

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 15, 'key': ['BD_ORG_ACN'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is sound. ACN and legal_name are correctly mapped from an ASIC regulator register. The ban type, URL and comment columns are rightly left unmapped, and entity_type is left unknown. Only advisory notes remain: the ban dates could populate valid_from/valid_to, and some names embed 'Formerly' text.
  - [advisory] `valid_from`: BD_ORG_START_DT states when the ban began, which is when the entity's own status on the register started. Rule 10 permits valid_from from a column saying when a status started. The mapping leaves it null, so useful temporal information is lost. (suggested: Optionally map valid_from from BD_ORG_START_DT with parse_date format %d/%m/%Y, and valid_to from BD_ORG_END_DT. Handle non-date values like 'Permanent banning' and blanks, for example by leaving valid_to null.)
  - [advisory] `entity.legal_name<-BD_ORG_NAME`: Some names embed a former name, e.g. 'KNIGHTSBRIDGE FINANCE PTY LTD (Formerly CLIFTON PARTNERS FINANCE PTY LTD)'. The legal_name claim therefore contains extra text beyond the registered name. This follows the register-holder rule, but the value is not a clean legal name. (suggested: Keep the mapping, but note the caveat. Optionally use regex_replace to strip the '(Formerly ...)' text, or leave it as a raw claim. Consider mapping_confidence of about 0.8.)

## Examples (raw → value, held-out rows)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
