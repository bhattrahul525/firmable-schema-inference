# Review packet (round-2 agent): validated_config

**Dataset:** QBCC Licensed Contractors Register — Queensland Building and Construction Commission  
**Licence:** Creative Commons Attribution 4.0  
**File:** `active_licensees.csv` (sha256 `7c649ed59714…`)

## How this ended

- Outcome **validated_config**.
- 13 model turns, 13 tool calls, $0.0126, 64.11s (download and human waits excluded). Trace: `logs/agent_runs/qbcc_licensed_contractors/trace.jsonl`.

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
| 1 | `Licensee Name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 2 | `ABN` | `entity.abn` | abn | W | held_out | 0.95 | 100.0% | **0.95** |
| 3 | `ACN` | `entity.acn` | acn | W | held_out | 0.95 | 98.4% | **0.95** |
| 4 | `Licensee Business Address` | `address.full` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 5 | `Licensee Business Address` | `address.state` | regex_extract((?i)\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\s+\d{4}\b) → state_code | P | held_out | 0.85 | 100.0% | **0.85** |
| 6 | `Licence Type DESC` | `entity.entity_type` | map_values({'Company': 'company', 'Individual': 'unknown'}) | P | held_out | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee Name`: Register kept by licensing body; Licensee Name is the holder of the QBCC licence (rule 5b).
2. `entity.abn` ← `ABN`: ABN column, 11 digits, checksum validated.
3. `entity.acn` ← `ACN`: ACN column, 9 digits, checksum validated.
4. `address.full` ← `Licensee Business Address`: Business address of the licensee.
5. `address.state` ← `Licensee Business Address`: State abbreviation preceding the postcode in the address text, case-insensitive.
6. `entity.entity_type` ← `Licence Type DESC`: Explicit licence type column: Company vs Individual. Individual is deliberately mapped to unknown because the ontology has no individual value and sole_trader must not be inferred from a person-like name.

## Left unmapped (not guessed)

- `id`: used as record_id (check_unique: 206,405 distinct, no blanks)
- `Licence Number`: QBCC licence number, not an entity identifier
- `Licence Type CODE`: code duplicate of Licence Type DESC
- `Financial Category DESC`: licensing financial category, not an ontology field
- `Financial Category CODE`: licensing financial category code
- `Licence Grade`: licence grade/class, no ontology field
- `Licence Class Type`: licence scope of work (trade class), a licence scope rather than an ANZSIC industry code; not mapped to industry_code

## Needs a transform the engine does not have

- none

## Checks

- ℹ️ Where one entity has both an ABN and an ACN (58 cases), the ACN equals the last 9 digits of the ABN in 95%. Reported as evidence only; not assumed anywhere.
- Duplicate record ids in held-out rows: {'rows': 206705, 'key': ['id'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound. Licensee Name is correctly mapped to legal_name under rule 5b, because the QBCC register lists the licensee as the holder, and the ABN and ACN columns match their checksummed transforms. Licence Type 'Individual' maps to unknown and 'Company' to company, which fits the explicit source column. The only issues are advisory: the case-sensitive state regex misses lowercase 'Qld', and the record_id uniqueness is unverified.
  - [advisory] `address.state<-Licensee Business Address`: The regex_extract is case-sensitive and only matches uppercase state codes. Row 81888 has 'Qld 4700', so no address.state observation is produced for it even though the state is stated in the source. (suggested: Make the pattern case-insensitive (e.g. a (?i) flag or equivalent) so lowercase or mixed-case state abbreviations are captured, then keep state_code to normalise them.)
  - [advisory] `record_id`: record_id is taken from the 'id' column, but the mapping does not state a uniqueness check. The config gives no evidence that 'id' is unique across rows. (suggested: Confirm 'id' is unique with check_unique, or fall back to a hash_row or composite key if it is not.)
- Critique: The mapping is largely sound. Every column is accounted for, ABN and ACN are checksum-validated in separate columns, the state regex and state_code handle the mixed-case address text correctly (e.g. 'Qld 4700'), and the legal_name mapping is supported by the licensing-register rule. I found no blocking meaning errors in the examples; the remaining points are advisory about entity_type granularity, a possibly richer industry description, and missing confidence/basis notes.
  - [advisory] `entity.entity_type<-Licence Type DESC`: Mapping Individual to unknown is a defensible conservative choice, but it discards a meaningful source value. The source states the holder is an individual, which is not the same as the entity type being unknown. (suggested: Keep the mapping if the team prefers conservatism, but document in the config reason that Individual is deliberately mapped to unknown, since the ontology has no individual value and sole_trader must not be inferred from a person-like name.)
  - [advisory] `industry_code`: Licence Class Type (e.g. 'Builder - Medium Rise', 'Carpentry', 'Painting and Decorating') describes the licensed scope of work and could arguably populate industry_code as the source's own description. It is currently unmapped with the reason 'no ontology field', which is slightly inaccurate because industry_code exists in the ontology. (suggested: Consider mapping Licence Class Type to entity.industry_code as the raw description (rule 9), with a note that it is a licence scope rather than an ANZSIC classification, or keep it unmapped and correct the reason to state that it is a licence scope, not an industry code.)
  - [advisory] `entity.legal_name<-Licensee Name`: The register is a licensing body's list of licence holders, so Licensee Name is the holder under rule 5b. The config does not record a mapping_confidence or a note that this relies on 5b, so the label basis is not visible to reviewers. (suggested: Record mapping_confidence at or below 0.7 with a reason that cites rule 5b and the holder-of-licence label, or add an explicit statement in the reason that the register lists Licensee Name as the holder.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Licensee Name`: `PAC BUILDING GROUP PTY LTD` → `PAC BUILDING GROUP PTY LTD`; `SOBERON INVESTMENTS PTY LTD` → `SOBERON INVESTMENTS PTY LTD`; `DOUGLAS JOHN GUNN` → `DOUGLAS JOHN GUNN`
- `entity.abn<-ABN`: `57 616 508 037` → `57616508037`; `73 060 714 874` → `73060714874`; `45 103 001 074` → `45103001074`
- `entity.acn<-ACN`: `616 508 037` → `616508037`; `060 714 874` → `060714874`; `656 007 564` → `656007564`
- `address.full<-Licensee Business Address`: `70 Plucks Rd Arana Hills QLD 4054` → `70 Plucks Rd Arana Hills QLD 4054`; `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035` → `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035`; `Shop 1  38 Neumann Rd Capalaba QLD 4157` → `Shop 1 38 Neumann Rd Capalaba QLD 4157`
- `address.state<-Licensee Business Address`: `70 Plucks Rd Arana Hills QLD 4054` → `QLD`; `133 GALAXY ST BRIDGEMAN DOWNS QLD 4035` → `QLD`; `Shop 1  38 Neumann Rd Capalaba QLD 4157` → `QLD`
- `entity.entity_type<-Licence Type DESC`: `Company` → `company`; `Individual` → `unknown`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
