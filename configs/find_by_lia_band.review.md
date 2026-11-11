# Review packet: find_by_lia_band (config v3)

**Dataset:** Find by LIA Band — Department of Customer Service  
**Page:** https://data.nsw.gov.au/data/dataset/find-by-lia-band  
**Licence:** unknown  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `find-my-lia-band-1-dec-2020.csv` (sha256 `f1b572c81483…`)  
**What the agent says it is:** NSW Liquor and Gaming Authority (Find by LIA Band) snapshot register of licensed clubs and hotels with gaming machine entitlements as at 1 Dec 2020.  
**One row is:** one licensed venue (club or hotel) holding a liquor/gaming licence, with its trading status, location and gaming machine entitlement figures.

## How this was produced

- Model `claude-haiku-5-5`; 6 LLM calls; 73,058 input + 24,209 output tokens; cost $0.0188 (computed from list prices); LLM time 107.2s.
- Revision rounds: 2. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'csv', 'encoding': 'utf-8', 'delimiter': ',', 'header_row': 1}`. Record id: `{'hash_row': True}` — Licence No is not unique (3305 distinct values across 3306 rows; LIQC324007158 appears twice), so no column set is a verified row key. Hash the row instead.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.8, 'address': 0.8, 'classification': 0.7, 'contact': 0.5}` — NSW Liquor and Gaming Authority (Department of Customer Service) is a statutory regulator publishing a licence register. That supports high trust on identity and address. Classification is somewhat lower because the gaming figures are a point-in-time snapshot. The dataset licence is 'unknown' and flagged, which is a finding and lowers confidence in downstream reuse. The register has no contact fields, so contact is 0.5 by default.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `Licence Name` | `entity.trading_name` | clean_whitespace | 0.60 | 100.0% (ok 300, rejected 0) | **0.60** | resolved_by_revision | `Royal Oak Hotel` → `Royal Oak Hotel`<br>`Wingham District Memorial Services Club Ltd` → `Wingham District Memorial Services Club Ltd`<br>`Ellalong Hotel` → `Ellalong Hotel` |
| 2 | `Venue Address` | `address.full` | clean_whitespace | 0.85 | 100.0% (ok 300, rejected 0) | **0.85** | agreed | `College St & Curtis Rd BALMAIN` → `College St & Curtis Rd BALMAIN`<br>`28-38 Bent St WINGHAM` → `28-38 Bent St WINGHAM`<br>`80 Helena St ELLALONG` → `80 Helena St ELLALONG` |
| 3 | `Venue Address` | `address.locality` | clean_whitespace → regex_extract(([A-Z][A-Z ]+)$) | 0.75 | 100.0% (ok 299, rejected 0) | **0.70** | resolved_by_revision | `College St & Curtis Rd BALMAIN` → `BALMAIN`<br>`28-38 Bent St WINGHAM` → `WINGHAM`<br>`80 Helena St ELLALONG` → `ELLALONG` |

Model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Licence Name`: Name on the liquor/gaming licence for the venue (e.g. 'Royal Hotel'). The column is not labelled or described as the registered or licensee legal name, so under the rules it stays trading_name. Some values carry company suffixes (25%), but that does not make the column a registered name, so entity.legal_name and entity_type are not derived from it.
2. `address.full` ← `Venue Address`: Street address plus locality in capitals (e.g. '482 Kent St SYDNEY'). Column name and samples agree on venue location. No postcode or state is embedded in the value.
3. `address.locality` ← `Venue Address`: The locality is the trailing all-capitals suburb in every sample (e.g. 'SYDNEY', 'BOWRAL', 'COFFS HARBOUR'). Street names are mixed case, so the leftmost anchored match picks the suburb. Values with no trailing capitals are skipped, not guessed. Confidence is below 0.9 because the pattern is verified on samples only, not on all 3306 rows.

## Left unmapped (not guessed)

- `Data as of`: Constant snapshot date '01-Dec-20' for the whole register. It describes the snapshot, not an entity claim. observed_at is taken from resource_last_modified instead.
- `Licence No`: Liquor licence number (LIQH/LIQC prefix). No ontology field exists for it, and it is not an ABN or ACN. It is not unique, so it is not used as the record key.
- `Trading Status`: Venue operating state ('Trading' / 'Temporarily ceased trading'), not an entity status. Mapping 'Trading' to active would state an entity-level claim the register does not make. Mapping it to unknown carries no information. No entity.status mapping is emitted.
- `Start Date`: The metadata does not say what this date describes, so it cannot be confirmed as the licence start for the name and address claims (rule 10). It is not used for valid_from. The heavy recurrence of 1947 and 1955 suggests placeholder values, not real start dates.
- `Latitude`: Coordinate. The ontology has no geo field, so it is not mapped.
- `Longitude`: Coordinate. The ontology has no geo field, so it is not mapped.
- `Type`: Venue kind (hotel or club). It is not an entity.entity_type value and not an ANZSIC code, and no explicit entity-type column exists, so it is not mapped.
- `Filter Category`: Venue size and gaming category (e.g. 'Hotel - large'). No ontology field exists for it.
- `SA2 Name`: ABS Statistical Area 2 name for gaming-machine banding. It is not a postal locality, so it is not mapped to address.locality.
- `SA2 Band`: Gaming-machine band tier. No ontology field exists for it.
- `Subject to Cap`: Gaming-machine cap flag. No ontology field exists for it.
- `LGA`: Local government area. The ontology has no LGA field, and address.locality would be wrong.
- `Region`: Metropolitan or Country classification. No ontology field exists for it.
- `GME`: Gaming machine entitlement figure. No ontology field exists for it.
- `PMP`: Gaming machine entitlement figure (poker machine permits). No ontology field exists for it.
- `Auth Total`: Authorised gaming machine total. No ontology field exists for it.
- `Unfulfilled Quota`: Gaming machine quota figure. No ontology field exists for it.
- `GMT`: Gaming machine total figure. No ontology field exists for it.
- `EGMs`: Electronic gaming machine count. No ontology field exists for it.

## Needs a transform the engine does not have

- `—`: none

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 1, only-2 2; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

The core mappings are mostly sound: Licence Name is correctly kept as trading_name, the address and locality extraction matches the examples, and the unmapped columns are reasonable. The main meaning problems are the inconsistent status treatment of trading versus ceased trading, and the unexplained application of Start Date as valid_from to every observation.
- `entity.status`: The status mapping is inconsistent. 'Temporarily ceased trading' is treated as a venue operating state, not an entity status, so it becomes unknown. But 'Trading' is mapped to active, which makes the same kind of venue operating state into an entity-level active claim. Examples 1-10 all emit entity.status 'active' from a venue operating state, which overstates what the register says about the entity. (suggested: Apply the same reasoning to both values. Either map 'Trading' to unknown with a reason stating it is a venue operating state, or keep 'active' with a reason explaining why this register's 'Trading' is a licence/entity-level claim. Lower mapping_confidence for entity.status accordingly.)
- `valid_from`: valid_from is taken from 'Start Date' and then applied to every observation, including entity.trading_name and address.full. Rule 10 allows valid_from only when the source states when the described licence or status started. The config gives no reason establishing that Start Date is the licence start, so it is unverified for the name and address claims. (suggested: Document in the config what 'Start Date' describes (for example, the liquor licence start date) and confirm that it applies to the name and address claims. If it is not confirmed, leave valid_from unmapped.)

## What changed during revision

**r1**
- Kept entity.trading_name for Licence Name and rejected proposal 2's entity.legal_name mapping. — The data does not say Licence Name is the registered, licensee or supplier name. Rule 5 requires that statement before a name can be legal_name. Proposal 2 offered no evidence beyond the 25% company-suffix share, which does not establish registration.
- Added address.locality from Venue Address using clean_whitespace then regex_extract of the trailing all-caps suburb, with mapping_confidence 0.75. address.full is kept. — Proposal 2 showed that the suburb is consistently the trailing all-caps segment in the samples. Extracting it is a deterministic L1 parse, not a guess. Rows with no trailing capitals are skipped. Confidence is below 0.9 because the pattern is checked on samples only.
- Changed the Trading Status map so 'Temporarily ceased trading' maps to unknown instead of suspended. Trading maps to active, and mapping_confidence is 0.75. — A venue temporarily ceasing trading is not a regulatory suspension of the entity. The 0 rejected values result shows only that the raw strings matched the table. It does not show the mapping is semantically right, so the earlier suspended interpretation is not supported.
- Left record_id, observed_at, valid_from, source_reliability and the unmapped list unchanged. — The proposals did not contest these, and the test results do not give a reason to change them. Start Date is kept for valid_from. The unmapped list covers every remaining column.
**critique**
- Removed the entity.status field (map_values on Trading Status) and listed Trading Status under unmapped. — Both raw values describe venue operating state, not entity status. Mapping 'Trading' to active made an entity-level claim the register does not support, and mapping to unknown adds nothing. Removing the field is more conservative than either option the reviewer offered.
- Cleared the valid_from mapping (Start Date parse_date) and listed Start Date under unmapped. — The metadata does not state what Start Date describes, so rule 10 is not satisfied for applying it to the name and address claims. The recurring 1947/1955 values also look like placeholders.
- No changes to record_id, observed_at, valid_to, the trading_name mapping, the address.full mapping, the address.locality mapping, or source_reliability. — The reviewer raised no issue with these, and the current reasoning holds.

## Three sample rows, raw

- `{'Data as of': '01-Dec-20', 'Licence Name': 'Royal Oak Hotel', 'Licence No': 'LIQH400105363', 'Start Date': '30/05/1960', 'Trading Status': 'Trading', 'Latitude': '-33.8557040000', 'Longitude': '151.1810240000', 'Type': 'hotel', 'Filter Category': 'Hotel - small', 'Venue Address': 'College St & Curtis Rd BALMAIN', 'SA2 Name': 'Double Bay - Bellevue Hill', 'SA2 Band': '1', 'Subject to Cap': 'No', 'LGA': 'Inner West Council', 'Region': 'Metropolitan', 'GME': '9', 'PMP': '0', 'Auth Total': '9', 'Unfulfilled Quota': '0', 'GMT': '9', 'EGMs': '3'}`
- `{'Data as of': '01-Dec-20', 'Licence Name': 'Wingham District Memorial Services Club Ltd', 'Licence No': 'LIQC300239241', 'Start Date': '21/03/1949', 'Trading Status': 'Trading', 'Latitude': '-31.8698810000', 'Longitude': '152.3736260000', 'Type': 'club', 'Filter Category': 'Club - medium', 'Venue Address': '28-38 Bent St WINGHAM', 'SA2 Name': 'Wingham', 'SA2 Band': '3', 'Subject to Cap': 'Yes', 'LGA': 'Mid-Coast Council', 'Region': 'Country', 'GME': '62', 'PMP': '0', 'Auth Total': '62', 'Unfulfilled Quota': '0', 'GMT': '62', 'EGMs': '62'}`
- `{'Data as of': '01-Dec-20', 'Licence Name': 'Ellalong Hotel', 'Licence No': 'LIQH400115164', 'Start Date': '7/01/1940', 'Trading Status': 'Trading', 'Latitude': '-32.9139970000', 'Longitude': '151.3067270000', 'Type': 'hotel', 'Filter Category': 'Hotel - non gaming', 'Venue Address': '80 Helena St ELLALONG', 'SA2 Name': 'Lavington', 'SA2 Band': '1', 'Subject to Cap': 'No', 'LGA': 'Cessnock City Council', 'Region': 'Country', 'GME': '0', 'PMP': '0', 'Auth Total': '0', 'Unfulfilled Quota': '0', 'GMT': '0', 'EGMs': '0'}`

---
To review: `python -m src.part2_agent.approve find_by_lia_band`
