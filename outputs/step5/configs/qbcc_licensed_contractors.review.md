# Review packet (round-2 agent): validated_config

**Dataset:** QBCC Licensed Contractors Register — Queensland Building and Construction Commission  
**Licence:** Creative Commons Attribution 4.0  
**File:** `active_licensees.csv` (sha256 `7c649ed59714…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0085, 47.31s (download and human waits excluded). Trace: `logs/agent_runs/qbcc_licensed_contractors/trace.jsonl`.
- Evidence the agent gave at finish (its words): Validate call 1: 0 hard failures, 0 unaccounted columns, record_id unique over 206,705 rows; parse rates ABN 1.0, ACN 0.98, legal_name 1.0. Critique: 3 advisory issues, 0 blocking.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: from `id` — 0 duplicate / blank keys of 206705 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. id | Licence Number | Licensee Name | ACN | ABN | Licensee Business Address | Licence Type DESC | Licence Type CODE | Financial Category DESC | Financial Category CODE | Licence Grade | Licence Class Type
2. 1 | 1213176 | PHILLIP ANTHONY MELVILLE | ∅ | ∅ | 26 Pollock Ave Kariong NSW 2250 | Individual | I | No Financials Required | N/A | Fire Occupational | Fire Protection - Electrical Stream Occu
3. 2 | 22382 | Christopher Grant LAZZARO | ∅ | 39 720 443 835 | 4/5-7 Prosper Cres Burleigh Heads QLD 42 | Individual | I | Self Certification - Builder/Trade | SC2 | Builder Licence | Builder - Low Rise
4. 3 | 22382 | Christopher Grant LAZZARO | ∅ | 39 720 443 835 | 4/5-7 Prosper Cres Burleigh Heads QLD 42 | Individual | I | Self Certification - Builder/Trade | SC2 | Trade Contractor Licence | Termite Management - Chemical
5. 4 | 22382 | Christopher Grant LAZZARO | ∅ | 39 720 443 835 | 4/5-7 Prosper Cres Burleigh Heads QLD 42 | Individual | I | Self Certification - Builder/Trade | SC2 | Nominee Supervisor | Termite Management - Physical
6. 5 | 22382 | Christopher Grant LAZZARO | ∅ | 39 720 443 835 | 4/5-7 Prosper Cres Burleigh Heads QLD 42 | Individual | I | Self Certification - Builder/Trade | SC2 | Builder Licence | Builder - Open
7. 6 | 22382 | Christopher Grant LAZZARO | ∅ | 39 720 443 835 | 4/5-7 Prosper Cres Burleigh Heads QLD 42 | Individual | I | Self Certification - Builder/Trade | SC2 | Builder Licence | Completed Residential Building Inspectio
8. 7 | 739833 | MATTHEW BATSON COLLINS | ∅ | ∅ | 112 Palmerin St Warwick QLD 4370 | Individual | I | No Financials Required | N/A | Nominee Supervisor | Carpentry
9. 8 | 739833 | MATTHEW BATSON COLLINS | ∅ | ∅ | 112 Palmerin St Warwick QLD 4370 | Individual | I | No Financials Required | N/A | Nominee Supervisor | Joinery
10. 9 | 739833 | MATTHEW BATSON COLLINS | ∅ | ∅ | 112 Palmerin St Warwick QLD 4370 | Individual | I | No Financials Required | N/A | Nominee Supervisor | Builder - Low Rise
11. 10 | 15207115 | Timothy Byron O'Dell | ∅ | ∅ | 438 Palmwoods Montville RD Palmwoods QLD | Individual | I | Self Certification - Builder/Trade | SC2 | Trade Contractor Licence | Carpentry
12. 11 | 15209262 | Callum James Lee | ∅ | 15 848 926 225 | 28 Murphy Street Tolga QLD 4882 | Individual | I | Self Certification - Builder/Trade | SC2 | Builder Licence | Builder - Low Rise

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |
| 2 | `ACN` | `entity.acn` | acn | W | held_out | 0.90 | 98.4% | **0.90** |
| 3 | `ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |
| 4 | `Licence Type DESC` | `entity.entity_type` | map_values({'Company': 'company', 'Individual': 'unknown'}) | P | held_out | 0.80 | 100.0% | **0.80** |
| 5 | `Licensee Business Address` | `address.full` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `Licensee Business Address` | `address.state` | regex_extract(\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\s+\d{4}\s*$) → state_code | P | held_out | 0.85 | 100.0% | **0.85** |
| 7 | `Licensee Business Address` | `address.postcode` | regex_extract((\d{4})\s*$) → postcode | P | held_out | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Regulator register; the row's subject is the licence holder (Licensee Name).
2. `entity.acn` ← `ACN`: ACN column, checksum validated.
3. `entity.abn` ← `ABN`: ABN column, checksum validated.
4. `entity.entity_type` ← `Licence Type DESC`: Explicit licence-holder type column: Company vs Individual.
5. `address.full` ← `Licensee Business Address`: Business address of licensee.
6. `address.state` ← `Licensee Business Address`: State abbreviation before the postcode at the end of the address.
7. `address.postcode` ← `Licensee Business Address`: Four-digit postcode at the end of the address.

## Left unmapped (not guessed)

- `Licence Number`: Licence number, not an entity identifier.
- `Licence Type CODE`: Code duplicate of Licence Type DESC.
- `Financial Category DESC`: Licence financial category, not an entity field in ontology.
- `Financial Category CODE`: Code for financial category.
- `Licence Grade`: Licence grade, no ontology field.
- `Licence Class Type`: Licence class of work; not an ANZSIC industry code, so not mapped.

## Needs a transform the engine does not have

- none

## Checks

- ℹ️ Where one entity has both an ABN and an ACN (58 cases), the ACN equals the last 9 digits of the ABN in 95%. Reported as evidence only; not assumed anywhere.
- Duplicate record ids in held-out rows: {'rows': 206705, 'key': ['id'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. Licensee Name is a licence-holder label on a regulator register, so mapping it to legal_name is supported. The Licence Type DESC to entity_type map is explicit and Individual to unknown is conservative. ABN and ACN are checksum-validated and the ABN column holds only 11-digit values. No blocking meaning errors appear in the examples. The remaining issues are a case-sensitivity gap in the state extraction, a possibly over-strict exclusion of the licence class description, and a missing uniqueness check on id.
  - [advisory] `address.state<-Licensee Business Address`: The state regex is case-sensitive and only matches uppercase abbreviations, so for row 81888 ('18 Penlington Street Allenstown Qld 4700') no address.state observation is produced even though the source states Queensland. The postcode still maps, so the gap is incompleteness, not a wrong value. (suggested: Make the regex case-insensitive (e.g. prefix with (?i)) and keep state_code to normalise to uppercase, then re-check row 81888.)
  - [advisory] `industry_code`: Licence Class Type holds work-class descriptions such as 'Painting and Decorating', 'Carpentry' and 'Builder - Medium Rise'. It is unmapped on the grounds that it is not ANZSIC, but rule 9 says to map the source's own code or description as it is, without translating it to ANZSIC. The ontology's industry_code note says to record the raw source value too. The exclusion may be too strict. (suggested: Consider mapping Licence Class Type to entity.industry_code as the raw description, with a caveat that it is a licence class and not an ANZSIC code; otherwise keep it unmapped with the reason stated more precisely.)
  - [advisory] `record_id`: The config uses the id column for record_id but does not state that it was checked for uniqueness. The rule requires check_unique or hash_row. (suggested: Confirm id is unique across the file (check_unique) before relying on it as source_record_id.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `PAC BUILDING GROUP PTY LTD` → `PAC BUILDING GROUP PTY LTD`; `SOBERON INVESTMENTS PTY LTD` → `SOBERON INVESTMENTS PTY LTD`; `DOUGLAS JOHN GUNN` → `DOUGLAS JOHN GUNN`
- `entity.acn<-ACN`: `616 508 037` → `616508037`; `060 714 874` → `060714874`; `656 007 564` → `656007564`
- `entity.abn<-ABN`: `57 616 508 037` → `57616508037`; `73 060 714 874` → `73060714874`; `45 103 001 074` → `45103001074`
- `entity.entity_type<-Licence Type DESC`: `Company` → `company`; `Individual` → `unknown`
- `address.full<-Licensee Business Address`: `70 Plucks Rd Arana Hills QLD 4054` → `70 Plucks Rd Arana Hills QLD 4054`; `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035` → `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035`; `Shop 1  38 Neumann Rd Capalaba QLD 4157` → `Shop 1 38 Neumann Rd Capalaba QLD 4157`
- `address.state<-Licensee Business Address`: `70 Plucks Rd Arana Hills QLD 4054` → `QLD`; `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035` → `QLD`; `Shop 1  38 Neumann Rd Capalaba QLD 4157` → `QLD`
- `address.postcode<-Licensee Business Address`: `70 Plucks Rd Arana Hills QLD 4054` → `4054`; `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035` → `4035`; `Shop 1  38 Neumann Rd Capalaba QLD 4157` → `4157`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
