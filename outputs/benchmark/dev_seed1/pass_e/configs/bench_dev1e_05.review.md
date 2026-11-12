# Review packet (round-2 agent): validated_config

**Dataset:** Register Of Disciplinary Actions — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `export.csv` (sha256 `45f1d68c461b…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.0089, 43.29s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1e_05/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `A.C.N` | `entity.acn` | clean_whitespace → acn | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Licensee Name is the licensee's name on the register; treated as the registered/licensee name per rule 5
2. `entity.acn` ← `A.C.N`: A.C.N column, 9-digit ACNs with spaces, checksum validated; N/A values skipped

## Left unmapped (not guessed)

- `Licence Number`: licence identifier of the state regulator, not an ABN/ACN/NZBN
- `Occupation`: trade licence category, not an ANZSIC industry classification
- `Occupation Class`: licence class, not an industry code
- `Licence Conditions/Endorsement`: licence conditions, not mapped to ontology
- `Action Type`: regulatory action type; not mapped to entity status because the suspension applies to the licence, not necessarily the company
- `Action Date`: date of regulatory action; does not state when the name or ACN became true, so not used as valid_from
- `Action End Date`: date regulatory action ends; not used as valid_to for name/ACN claims
- `Circumstances/Reasons`: free-text reasons for action
- `Action under review by the ACAT`: regulatory review detail
- `Period licensee can apply to ACAT for review expired`: regulatory review detail
- `Applicant has applied to ACAT for review and the review is incomplete`: regulatory review detail
- `Partnership details (Partnerships only)`: partnership flag, not mapped
- `Compliance with Rectification Order`: regulatory compliance detail
- `Related licensees`: related licensee detail, not mapped
- `Licence Expiry Date`: licence expiry, not the entity's registration date
- `Date stop work notice lifted`: regulatory detail
- `Reason stop work notice lifted`: regulatory detail

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 393, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The name and ACN mappings are sound and follow the rules, but the envelope's valid_from and valid_to are applied to the name and ACN claims using regulatory action dates, which the source does not support as the dates those claims became true. That is blocking. The rest are advisory points about the Action Type status question, the Occupation exclusions, and the inconsistent handling of Action Date between the unmapped list and the envelope.
  - [blocking] `observation.valid_from`: The envelope sets valid_from from Action Date and valid_to from Action End Date on every observation, including entity.legal_name and entity.acn. A regulatory action date says when a suspension, condition or disqualification started or ended. It does not say when the registered name or ACN became true, so these dates are attached to claims the source does not date that way. The unmapped entries also say Action Date and Action End Date are 'used as valid_from/valid_to', but no transform or config key for valid_from or valid_to appears in the fields list. (suggested: Do not apply the action dates as valid_from/valid_to on the name and ACN observations. Either drop them, or model the action as its own observation with its own validity, and record the date format (dd/mm/yyyy) in an explicit parse_date transform with a try_transform check.)
  - [advisory] `Action Type`: Action Type values such as 'Suspension' and 'Automatic Suspension' are listed as unmapped on the grounds that they are not entity status. The ontology has a 'suspended' status, and these values may describe the entity's status more directly than the reason given. Disqualification and Condition are not statuses, so the exclusion is reasonable for those. (suggested: Consider whether a licence action of type suspension should be mapped to entity.status via map_values, with only the suspension values, and keep Condition and Disqualification unmapped. Record the caveat that the suspension applies to the licence, not necessarily to the company.)
  - [advisory] `Occupation / Occupation Class`: Occupation and Occupation Class are left unmapped with the reason that they are not ANZSIC codes. Rule 9 allows the source's own code or description to be mapped to industry_code as it is, and these values (e.g. Electrician, Builder, Plumber) are descriptive trade categories. The exclusion is defensible, but the reason given does not show that these are not the source's own industry description. (suggested: Either keep them unmapped with a clearer reason (trade licence category, not an industry classification), or map Occupation to entity.industry_code at a lower mapping_confidence after checking its values against the rule.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `Worldwide Solutions Pty Ltd` → `Worldwide Solutions Pty Ltd`; `BGIS PTY LTD` → `BGIS PTY LTD`; `LIPACON PTY LTD` → `LIPACON PTY LTD`
- `entity.acn<-A.C.N`: `646158581` → `646158581`; `064 638 197` → `064638197`; `626 540 065` → `626540065`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
