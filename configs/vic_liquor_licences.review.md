# Review packet: vic_liquor_licences (config v2)

**Dataset:** Victorian liquor licences by location — Liquor Control Victoria  
**Page:** https://discover.data.vic.gov.au/dataset/victorian-liquor-licences-by-location  
**Licence:** Creative Commons Attribution 4.0 International  
**File:** `Current_Victorian_Licences_By_Location_30_September_2026.xlsx` (sha256 `382364f5ccca…`)  
**What the agent says it is:** Register of current Victorian liquor licences by location, published by Liquor Control Victoria as an XLSX snapshot.  
**One row is:** one current liquor licence held by a licensee at a premises address

## How this was produced

- Model `claude-haiku-5-5`; 5 LLM calls; 62,160 input + 17,099 output tokens; cost $0.0125 (computed from list prices); LLM time 78.5s.
- Revision rounds: 1. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'xlsx', 'encoding': 'utf-8-sig', 'sheet': 'Current_Victorian_Licences_By_L', 'header_row': 5}`. Record id: `{'hash_row': True}` — Licence Number has 20000 distinct values across 23169 rows, so it is not a unique row key. Each row is hashed instead.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.9, 'address': 0.8, 'classification': 0.8, 'contact': 0.5}` — Liquor Control Victoria is the statutory regulator that issues and records these licences, so identity (licensee and trading name) is high. Premises addresses are reliable at the time of the snapshot but can go stale, so address is a little lower. The classification score is a publisher-level judgement only: licence category is not mapped in this ontology slice, so it is not used by any field. No contact fields are mapped, so contact is a neutral 0.5.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licensee` | `entity.legal_name` | clean_whitespace | 0.90 | 100.0% (ok 300, rejected 0) | **0.90** | agreed | `THE WAREHOUSE GEELONG PTY LTD` → `THE WAREHOUSE GEELONG PTY LTD`<br>`MORDI-DELI PTY LTD` → `MORDI-DELI PTY LTD`<br>`WALKER FOODS PTY LTD` → `WALKER FOODS PTY LTD` |
| 2 | `Licensee` | `entity.entity_type` | entity_type_from_suffix | 0.60 | 100.0% (ok 300, rejected 0) | **0.60** | agreed | `THE WAREHOUSE GEELONG PTY LTD` → `company`<br>`MORDI-DELI PTY LTD` → `company`<br>`WALKER FOODS PTY LTD` → `company` |
| 3 | `Trading As` | `entity.trading_name` | clean_whitespace | 0.90 | 100.0% (ok 296, rejected 0) | **0.90** | agreed | `THE WAREHOUSE GEELONG` → `THE WAREHOUSE GEELONG`<br>`MORDI-DELI` → `MORDI-DELI`<br>`GUZMAN Y GOMEZ SOUTH YARRA` → `GUZMAN Y GOMEZ SOUTH YARRA` |
| 4 | `Street Address + Suburb` | `address.full` | join_nonempty(, ) | 0.80 | 100.0% (ok 288, rejected 0) | **0.70** | resolved_by_revision | `['5 LITTLE RYRIE ST', 'GEELONG']` → `5 LITTLE RYRIE ST, GEELONG`<br>`['SHOP 3, 570 MAIN ST', 'MORDIALLOC']` → `SHOP 3, 570 MAIN ST, MORDIALLOC`<br>`['TENANCY 5, 6 & 7 190 -206 TOORAK ROAD', 'SOUTH Y` → `TENANCY 5, 6 & 7 190 -206 TOORAK ROAD, SOUTH YARRA` |
| 5 | `Suburb` | `address.locality` | upper | 0.90 | 100.0% (ok 288, rejected 0) | **0.90** | agreed | `GEELONG` → `GEELONG`<br>`MORDIALLOC` → `MORDIALLOC`<br>`SOUTH YARRA` → `SOUTH YARRA` |
| 6 | `Postcode` | `address.postcode` | postcode | 0.90 | 98.3% (ok 283, rejected 5) | **0.90** | agreed | `3220` → `3220`<br>`3195` → `3195`<br>`3141` → `3141` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Licensee`: The Licensee column is the licence holder's name, which is the registered licensee and therefore legal_name. Individual licensees (e.g. 'EDWARDS NADIA') are mapped as legal_name without inferring entity type. Names truncated in the source (e.g. 'PTY LIMIT') are passed through as received.
2. `entity.entity_type` ← `Licensee`: No explicit entity-type column exists (Licence Category and Trading Hours are licence classes, not entity types), so the rule is derived from the Licensee suffix. Pty Ltd/Limited gives company, otherwise unknown. Individuals, associations and truncated suffixes will be unknown.
3. `entity.trading_name` ← `Trading As`: 'Trading As' is the name the business trades under, which is the trading name. It is a single name per row with no splitting needed. Blank values (0.8% of rows) are absent.
4. `address.full` ← `Street Address + Suburb`: Joining Street Address with Suburb is kept because address.full should be a complete premises line, and Street Address alone lacks the suburb. The Street Address-only alternative is rejected for that reason. State is not included because no state column exists in the source.
5. `address.locality` ← `Suburb`: Suburb is the premises locality. Values are upper-cased, though some sample rows are in mixed case.
6. `address.postcode` ← `Postcode`: Premises postcode. The postcode transform restores dropped leading zeros. The value '0' (229 rows in the full dataset) is not a postcode and will be rejected by the transform. It is not guessed or nulled.

## Left unmapped (not guessed)

- `Licence Number`: No ontology field for a licence number. Retained in the raw record for traceability. Not unique, so not used as record_id.
- `Licence Category`: No ontology field for licence class. Would need a classification field that does not exist in this ontology slice.
- `Trading Hours`: No ontology field for trading hours or conditions.
- `Patron Capacity (if applicable)`: No ontology field for patron capacity.
- `Postal Address`: Correspondence address of the licensee, not the premises. The ontology has no postal address field, and mapping it to address.full would conflate two different addresses.
- `Postal Suburb`: Correspondence address component, not premises. No ontology field.
- `Postal Postcode`: Correspondence address component, not premises. No ontology field.
- `Council`: Local government area. No ontology field.
- `Region`: Liquor regulatory region. No ontology field.
- `Metro/Regional`: Metro/regional flag. No ontology field.
- `Latitude`: Geocoordinate. No ontology field in this slice.
- `Longitude`: Geocoordinate. No ontology field in this slice.
- `_blank_7`: Completely empty column (fill rate 0).
- `_blank_8`: Completely empty column (fill rate 0).
- `_blank_13`: Completely empty column (fill rate 0).
- `_blank_14`: Completely empty column (fill rate 0).

## Needs a transform the engine does not have

- `address.state`: Every row is a Victorian premises, so address.state should be VIC, but no constant-value transform exists. The state is left unmapped until one is available.

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 1, only-2 1; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

The mapping looks right on every example row. Licensee maps to legal_name and Trading As to trading_name, and the entity_type results (company for Pty Ltd, unknown for Inc. and clubs) match the suffix rule. Street Address plus Suburb joins to address.full, Suburb to locality, and Postcode to postcode. Postal address columns, licence class and hours are correctly left unmapped, and the postcode '0' rejection is consistent with the transform. No meaning errors are visible in the examples.

## What changed during revision

**r1**
- address.full reason rewritten to state why the Street Address-only proposal was rejected. The join with Suburb is kept. — The two held-out proposals disagreed. Street Address alone is a street line, not a full address, so proposal 2 would mislabel it. Proposal 1 matches the ontology meaning of address.full, so the config is unchanged in substance.
- source_reliability_basis reworded so the classification score is not described as backed by a mapped field. — Licence Category is unmapped in this slice, so no classification claim is emitted from this source. The numeric scores are unchanged.

## Three sample rows, raw

- `{'Licence Number': '36155675', 'Licensee': 'THE WAREHOUSE GEELONG PTY LTD', 'Trading As': 'THE WAREHOUSE GEELONG', 'Licence Category': 'Limited Licence', 'Trading Hours': 'Limited Licence', 'Street Address': '5 LITTLE RYRIE ST', 'Suburb': 'GEELONG', 'Postcode': '3220', 'Council': 'GREATER GEELONG CITY COUNCIL', 'Region': 'Barwon South-West', 'Metro/Regional': 'Regional', 'Latitude': '-38.22323293', 'Longitude': '145.17033890', 'Postal Address': '5 LITTLE RYRIE STREET', 'Postal Suburb': 'GEELONG', 'Postal Postcode': '3220'}`
- `{'Licence Number': '32384947', 'Licensee': 'MORDI-DELI PTY LTD', 'Trading As': 'MORDI-DELI', 'Licence Category': 'Restaurant and cafe Licence', 'Trading Hours': 'Trading to 1am', 'Patron Capacity (if applicable)': '26', 'Street Address': 'SHOP 3, 570 MAIN ST', 'Suburb': 'MORDIALLOC', 'Postcode': '3195', 'Council': 'KINGSTON CITY COUNCIL', 'Region': 'Metro South', 'Metro/Regional': 'Metro', 'Latitude': '-38.00688161', 'Longitude': '145.08588524', 'Postal Address': '6/1 BOUVERIE STREET', 'Postal Suburb': 'CARLTON', 'Postal Postcode': '3053'}`
- `{'Licence Number': '32331130', 'Licensee': 'WALKER FOODS PTY LTD', 'Trading As': 'GUZMAN Y GOMEZ SOUTH YARRA', 'Licence Category': 'Restaurant and cafe Licence', 'Trading Hours': 'Trading to 1am', 'Patron Capacity (if applicable)': '124', 'Street Address': 'TENANCY 5, 6 & 7 190 -206 TOORAK ROAD', 'Suburb': 'SOUTH YARRA', 'Postcode': '3141', 'Council': 'STONNINGTON CITY COUNCIL', 'Region': 'Metro South', 'Metro/Regional': 'Metro', 'Latitude': '-37.83940704', 'Longitude': '144.99357495', 'Postal Address': '120 ROSLYN STREET', 'Postal Suburb': 'BRIGHTON', 'Postal Postcode': '3186'}`

---
To review: `python -m src.part2_agent.approve vic_liquor_licences`
