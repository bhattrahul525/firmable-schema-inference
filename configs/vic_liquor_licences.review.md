# Review packet: vic_liquor_licences (config v2)

**Dataset:** Victorian liquor licences by location — Liquor Control Victoria  
**Page:** https://discover.data.vic.gov.au/dataset/victorian-liquor-licences-by-location  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `Current_Victorian_Licences_By_Location_30_September_2026.xlsx` (sha256 `382364f5ccca…`)  
**What the agent says it is:** Current Victorian liquor licences by location, published by Liquor Control Victoria as a snapshot register of licensed premises with licensee, trading name, address and location.  
**One row is:** one current liquor licence held by a licensee for a premises

## How this was produced

- Model `claude-haiku-5-5`; 5 LLM calls; 62,571 input + 13,948 output tokens; cost $0.0116 (computed from list prices); LLM time 59.3s.
- Revision rounds: 1. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'xlsx', 'encoding': 'utf-8-sig', 'sheet': 'Current_Victorian_Licences_By_L', 'header_row': 5}`. Record id: `{'from': ['Licence Number']}` — Licence Number is distinct across all 23169 rows (distinct equals row count) and identifies one current licence per row.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.9, 'address': 0.85, 'classification': 0.7, 'contact': 0.5}` — Liquor Control Victoria is the statutory licensing regulator, so its register is highly reliable for licensee identity and premises address at the snapshot date. Classification is lower because licence category describes the licence, not the entity's industry. No contact fields are present, so contact is 0.5 (cannot tell).

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee` | `entity.legal_name` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `THE WAREHOUSE GEELONG PTY LTD` → `THE WAREHOUSE GEELONG PTY LTD`<br>`MORDI-DELI PTY LTD` → `MORDI-DELI PTY LTD`<br>`WALKER FOODS PTY LTD` → `WALKER FOODS PTY LTD` |
| 2 | `Trading As` | `entity.trading_name` | clean_whitespace | 0.90 | 100.0% (ok 296, rejected 0) | **0.90** | agreed | `THE WAREHOUSE GEELONG` → `THE WAREHOUSE GEELONG`<br>`MORDI-DELI` → `MORDI-DELI`<br>`GUZMAN Y GOMEZ SOUTH YARRA` → `GUZMAN Y GOMEZ SOUTH YARRA` |
| 3 | `Licensee` | `entity.entity_type` | entity_type_from_suffix | 0.80 | 100.0% (ok 300, rejected 0) | **0.80** | agreed | `THE WAREHOUSE GEELONG PTY LTD` → `company`<br>`MORDI-DELI PTY LTD` → `company`<br>`WALKER FOODS PTY LTD` → `company` |
| 4 | `Suburb` | `address.locality` | clean_whitespace | 0.95 | 100.0% (ok 288, rejected 0) | **0.95** | agreed | `GEELONG` → `GEELONG`<br>`MORDIALLOC` → `MORDIALLOC`<br>`SOUTH YARRA` → `SOUTH YARRA` |
| 5 | `Postcode` | `address.postcode` | postcode | 0.90 | 98.3% (ok 283, rejected 5) | **0.90** | agreed | `3220` → `3220`<br>`3195` → `3195`<br>`3141` → `3141` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee`: Licensee is the named holder of the liquor licence, which is the registered licensee name. Individuals appear as licensees (for example EDWARDS NADIA) and are mapped as legal_name without inferring entity type.
2. `entity.trading_name` ← `Trading As`: Trading As is the name the premises trades under, as distinct from the licensee's registered name. Single value per row, no splitting observed.
3. `entity.entity_type` ← `Licensee`: The source has no explicit entity-type column, so the suffix rule is applied to the Licensee name. Names ending Pty Ltd, Pty Limited or Limited become company; others (persons, incorporated associations, clubs) become unknown. Lower confidence because some Limited names may not be companies.
4. `address.locality` ← `Suburb`: Suburb is the premises locality, matching the column name and sample values such as MELBOURNE and RICHMOND.
5. `address.postcode` ← `Postcode`: Postcode is the premises postcode. About 266 rows carry the value 0, which is not a valid 4-digit postcode; the postcode transform should reject it rather than emit it.

## Left unmapped (not guessed)

- `Street Address`: Street line only (for example 5 LITTLE RYRIE ST), with no suburb, postcode or state in the same cell. The ontology has no street-level address field. Mapping it to address.full would state a complete address the source does not give, and joining it with Suburb and Postcode still omits state, so it is not emitted as address.full. Suburb and Postcode are mapped separately to address.locality and address.postcode.
- `Licence Category`: Licence class (for example Restaurant and cafe Licence, General Licence). No canonical licence or classification field exists in this ontology slice.
- `Trading Hours`: Trading hours class. No canonical field for this in the ontology.
- `Patron Capacity (if applicable)`: Patron capacity of the premises. No canonical field exists for capacity.
- `Council`: Local government area name. No canonical address field for council or LGA.
- `Region`: Liquor Control Victoria regional grouping (for example Metro South). This is an administrative region, not an address.state value, so it is not mapped to state.
- `Metro/Regional`: Metro or regional classification. No canonical field exists.
- `Latitude`: Geographic coordinate. No canonical geo field exists in this ontology slice.
- `Longitude`: Geographic coordinate. No canonical geo field exists in this ontology slice.
- `Postal Address`: Postal or mailing address, often a PO Box or the regulator's own office, and not the premises. The ontology has no postal address field, and mapping it to address.full would misrepresent the premises location.
- `Postal Suburb`: Postal suburb, paired with Postal Address. No canonical postal field exists.
- `Postal Postcode`: Postal postcode, paired with Postal Address. No canonical postal field exists.
- `_blank_7`: Completely empty column (fill rate 0). Ignored.
- `_blank_8`: Completely empty column (fill rate 0). Ignored.
- `_blank_13`: Completely empty column (fill rate 0). Ignored.
- `_blank_14`: Completely empty column (fill rate 0). Ignored.

## Needs a transform the engine does not have

- `—`: none

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 0, only-2 0; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

The entity mappings look right in the examples: legal_name and trading_name are not swapped, individuals and clubs are handled consistently, and the entity_type suffix rule matches the examples. The main meaning error is that the street-only Street Address is emitted as address.full.
- `address.full`: Street Address holds only the street line (e.g. "5 LITTLE RYRIE ST", "4A EDINBURGH ST"). Suburb and postcode are separate, and no state column exists. The engine emits it as address.full, so the observation claims a complete address the source does not state. The config's own reason calls it a 'partial full address', which confirms the mismatch. (suggested: Do not map Street Address to address.full as it stands. Either map it to a street-level field if one is added to the ontology, or combine it with Suburb and Postcode using join_nonempty(', ') as a first transform on a source list. Only then emit address.full, and lower mapping_confidence to reflect the partial-address meaning.)

## What changed during revision

**critique**
- Removed the address.full field mapped from Street Address. — The reviewer found that Street Address holds only the street line, so emitting it as address.full would claim a complete address. The source has no state column, so joining Suburb and Postcode would still not give a full address. Under the never-guess rule the field is removed rather than approximated.
- Listed Street Address under unmapped with the reason that the ontology has no street-level field. — Account for every column: a column that cannot be mapped correctly goes to unmapped with a reason.
- Kept Suburb and Postcode mapped to address.locality and address.postcode. — These columns match their canonical meanings and are not affected by the warning. They still carry the premises locality and postcode.

## Three sample rows, raw

- `{'Licence Number': '36155675', 'Licensee': 'THE WAREHOUSE GEELONG PTY LTD', 'Trading As': 'THE WAREHOUSE GEELONG', 'Licence Category': 'Limited Licence', 'Trading Hours': 'Limited Licence', 'Street Address': '5 LITTLE RYRIE ST', 'Suburb': 'GEELONG', 'Postcode': '3220', 'Council': 'GREATER GEELONG CITY COUNCIL', 'Region': 'Barwon South-West', 'Metro/Regional': 'Regional', 'Latitude': '-38.22323293', 'Longitude': '145.17033890', 'Postal Address': '5 LITTLE RYRIE STREET', 'Postal Suburb': 'GEELONG', 'Postal Postcode': '3220'}`
- `{'Licence Number': '32384947', 'Licensee': 'MORDI-DELI PTY LTD', 'Trading As': 'MORDI-DELI', 'Licence Category': 'Restaurant and cafe Licence', 'Trading Hours': 'Trading to 1am', 'Patron Capacity (if applicable)': '26', 'Street Address': 'SHOP 3, 570 MAIN ST', 'Suburb': 'MORDIALLOC', 'Postcode': '3195', 'Council': 'KINGSTON CITY COUNCIL', 'Region': 'Metro South', 'Metro/Regional': 'Metro', 'Latitude': '-38.00688161', 'Longitude': '145.08588524', 'Postal Address': '6/1 BOUVERIE STREET', 'Postal Suburb': 'CARLTON', 'Postal Postcode': '3053'}`
- `{'Licence Number': '32331130', 'Licensee': 'WALKER FOODS PTY LTD', 'Trading As': 'GUZMAN Y GOMEZ SOUTH YARRA', 'Licence Category': 'Restaurant and cafe Licence', 'Trading Hours': 'Trading to 1am', 'Patron Capacity (if applicable)': '124', 'Street Address': 'TENANCY 5, 6 & 7 190 -206 TOORAK ROAD', 'Suburb': 'SOUTH YARRA', 'Postcode': '3141', 'Council': 'STONNINGTON CITY COUNCIL', 'Region': 'Metro South', 'Metro/Regional': 'Metro', 'Latitude': '-37.83940704', 'Longitude': '144.99357495', 'Postal Address': '120 ROSLYN STREET', 'Postal Suburb': 'BRIGHTON', 'Postal Postcode': '3186'}`

---
To review: `python -m src.part2_agent.approve vic_liquor_licences`
