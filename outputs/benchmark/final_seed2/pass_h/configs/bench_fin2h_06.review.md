# Review packet (round-2 agent): validated_config

**Dataset:** ASIC - Banned and Disqualified Organisations Dataset — Australian Securities and Investments Commission (ASIC)  
**Licence:** Creative Commons Attribution 3.0 Australia  
**File:** `bd_org_202611.csv` (sha256 `67fc279cf567…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0086, 41.31s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_06/trace.jsonl`.
- Evidence the agent gave at finish (its words): Downloaded CSV/TSV resource (15 rows, 8 columns). BD_ORG_ACN checksum parse 100%; BD_ORG_NAME is the banned company name; dates in dd/mm/yyyy. Licence not present in the file; not set (advisory).

## Reader and record settings

- reader: `{"format": "tsv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `BD_ORG_ACN, BD_ORG_START_DT` — 0 duplicate / blank keys of 15 rows (whole file)
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
| 1 | `BD_ORG_NAME` | `entity.legal_name` | clean_whitespace | W | training | 0.70 | n/a | **0.70** |
| 2 | `BD_ORG_ACN` | `entity.acn` | acn | W | training | 0.95 | n/a | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `BD_ORG_NAME`: Register of banned organisations kept by ASIC; the row subject is the organisation holding the banning (rule 5b). No explicit registered-name label, so confidence capped at 0.7.
2. `entity.acn` ← `BD_ORG_ACN`: Column named ACN, 9-digit, checksum validated.

## Fields without enough held-out evidence

No held-out test was possible: the file has too few rows, so every field is judged on rows the agent saw (evidence `training`) or on nothing (`unverified`).
- `entity.legal_name<-BD_ORG_NAME`: evidence **training** (capped at 0.8); whole file: 15 populated, 15 judged, 15 ok, 0 rejected. Training examples: `AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD` → `AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD`; `BLACKBURNE & DIXON PTY LTD` → `BLACKBURNE & DIXON PTY LTD`; `BRANNELLY FINANCIAL PTY LTD` → `BRANNELLY FINANCIAL PTY LTD`
- `entity.acn<-BD_ORG_ACN`: evidence **training** (capped at 0.8); whole file: 15 populated, 15 judged, 15 ok, 0 rejected. Training examples: `081402379` → `081402379`; `008876033` → `008876033`; `011021640` → `011021640`

## Left unmapped (not guessed)

- `REGISTER_NAME`: constant register title
- `BD_ORG_TYPE`: ban category (e.g. credit banning), not an entity type or status enum value
- `BD_ORG_URL`: link to ASIC help or banning order document
- `BD_ORG_COMMENT`: free-text comment, mostly 'No comment made'
- `BD_ORG_START_DT`: start date of a banning order (an event), not when the entity's name or ACN became true; no status enum value for banned
- `BD_ORG_END_DT`: end date of a banning period (an event); not applied to identity fields; contains 'Permanent banning' text

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 15, 'key': ['BD_ORG_ACN', 'BD_ORG_START_DT'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The ACN and name mappings look right on the sample rows, and the ACN checksum transform is appropriate. The main problem is that the banning start and end dates are used as the valid_from and valid_to of the entity's name and ACN observations, which the source does not support. The name mapping also needs a lower confidence under rule 5b.
  - [blocking] `valid_from`: valid_from is sourced from BD_ORG_START_DT, which records the start date of a banning order, an event against the organisation. The envelope applies it to the entity.legal_name and entity.acn observations, so the output claims the registered name and ACN became true on the ban date. Rule 10 says an event date the row records is not when a name or identifier became true, and the register does not state when the organisation's registration started. (suggested: Remove valid_from and valid_to from the envelope for the name and ACN observations. If the ban itself is to be recorded, map it to a status-type field with its own basis, not to the envelope dates of the identity fields.)
  - [blocking] `valid_to`: valid_to is sourced from BD_ORG_END_DT, the end of a banning period. It is applied to the identity observations (legal_name, acn) and states that the organisation's registration or name ended on that date. The source does not say this. (suggested: Do not apply valid_to to name or ACN observations. Drop it, or confine it to a status-level claim whose meaning is the banning period.)
  - [advisory] `entity.legal_name<-BD_ORG_NAME`: The rule 5b basis is stated in the reason, but the config has no label in the source saying BD_ORG_NAME is the registered name. The register does list the organisation as holding the banning, so the mapping is supportable, but the confidence should be 0.7 or lower without a label. (suggested: Set mapping_confidence to 0.7 or lower for entity.legal_name, citing the 5b basis.)
  - [advisory] `entity.legal_name<-BD_ORG_NAME`: Some values carry a former name inside the value, e.g. 'KNIGHTSBRIDGE FINANCE PTY LTD (Formerly CLIFTON PARTNERS FINANCE PTY LTD)'. The whole string goes into legal_name, so the former name is presented as part of the registered name. (suggested: Leave as is under rule 1 (no added or removed text), but record this as a caveat. A later regex_replace could split the former name out, but only if the rule permits removing text from the value.)
  - [advisory] `observation.licence`: The config has no licence entry. The envelope requires a licence value from dataset metadata, and none is given for this register. (suggested: Take the licence from the CKAN metadata for this resource, or record 'unknown' and flag it.)

## Examples (raw → value, held-out rows)

---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
