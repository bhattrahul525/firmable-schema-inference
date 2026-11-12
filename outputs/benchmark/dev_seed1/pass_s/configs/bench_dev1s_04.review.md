# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 11 model turns, 11 tool calls, $0.1848, 56.27s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1s_04/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier name Parties additionalidentifiers/id` | `entity.legal_name` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |
| 2 | `Supplier ABN Parties/identifier/uri` | `entity.abn` | clean_whitespace → regex_extract(^(\d{2}) ?(\d{3}) ?(\d{3}) ?(\d{3})$) → abn | W | 0.50 | n/a | **0.50** |
| 3 | `Supplier address Parties/address` | `address.full` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Supplier name Parties additionalidentifiers/id`: supplier name
2. `entity.abn` ← `Supplier ABN Parties/identifier/uri`: supplier ABN
3. `address.full` ← `Supplier address Parties/address`: supplier address

## Left unmapped (not guessed)

- `Description OCDS name`: blank
- `Agency (Dept or Stat Body)`: government buyer
- `Agency address`: government buyer
- `Contract description/name Contracts/Title`: not entity field
- `Award contract date Contracts/dateSigned`: contract date
- `Contract value Contracts/value/amount`: not entity field
- `Variation to contract (Yes/No) Not listed`: contract attr
- `Specific confidentiality provision used`: contract attr
- `Procurement method Tender procurementMethod`: contract attr
- `Form of contract`: contract attr
- `Number of offers sought`: contract attr
- `Evaluation criteria and weightings`: contract attr
- `Deliverables`: contract attr
- `Contract milestones`: contract attr
- `Contract performance management`: contract attr
- `Contract reference number Contracts/AwardID`: not unique, contract id
- `Contract category group Contracts/items/classification/description`: contract attr
- `Parent contract number/SOA Contracts`: contract attr

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 50, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is broadly sound: it keeps the government agency out of the entity fields and defaults entity_type to unknown. However, the OCDS description row is emitted as data, which puts field-path labels into legal_name and address.full, and one row puts a company name into the address field. Fix those before use.
  - [blocking] `entity.legal_name<-Supplier name`: In the first example row, the 'Supplier name' cell holds the OCDS field-path label 'Parties additionalidentifiers/id', not a supplier name. The mapping emits it as legal_name. This is a schema-description row, not a data row, and the skip_rows setting did not remove it. (suggested: Increase skip_rows or add a filter to drop the OCDS mapping row so its header-like text is never emitted as a legal_name.)
  - [blocking] `address.full<-Supplier address`: The first example emits 'Parties/address' as an address, which is an OCDS field path, not an address. In the MIMS row, the 'Supplier address' column holds 'MIMS Australia', which is a company name, not an address. The mapping emits it as address.full, so a value is placed in a field it does not mean, and the supplier name is missing. (suggested: Drop the OCDS description row. Add validation so address.full is only emitted when the value looks like an address (street, locality, state or postcode). Route name-like values to a review queue or treat them as a possible legal_name candidate.)
  - [advisory] `entity.abn<-Supplier ABN`: No example row carries a Supplier ABN value, so the ABN mapping is untested. The only value seen is the OCDS label 'Parties/identifier/uri', which the regex rightly rejects. (suggested: Verify the ABN mapping on real rows with an ABN present before relying on it.)
  - [advisory] `envelope.valid_from`: Only the Blue Care row has valid_from (2020-08-08), taken from 'Commence date'. This column is not listed in the config, so the source of valid_from is undocumented. 'Commence date' is a contract start date, not the date the entity's claim became true. The config's 'unmapped' list also omits 'Commence date' and 'Finish date'. (suggested: Document the valid_from source in the config, or drop it. List Commence date and Finish date in 'unmapped' as contract attributes.)
  - [advisory] `observed_at`: observed_at is the resource last-modified time (2021-08-02). One row has an award date of 13/08/2021, which is after that timestamp, so the claimed observation time is inconsistent with the data. (suggested: Check the metadata timestamp, or flag rows whose dates postdate observed_at.)
- Critique: Agency columns are correctly left unmapped as the government buyer. The placeholder 'not assessed' values in the first row were emitted as a legal_name and an address, and these are blocking. The remaining issues are advisory: entity names of uncertain legal status, partial addresses, no supplier ABNs, and an undocumented valid_from.
  - [blocking] `entity.legal_name<-Supplier name Parties additionalidentifiers/id`: The first example row is a template or placeholder row (the other columns hold header text such as 'Contract Name' and 'Executed Contract Value'). Its supplier name 'not assessed' was emitted as a legal_name observation, but it is not a name. (suggested: Add a null-token filter that drops 'not assessed', 'N/A' and similar placeholders for this field. Skip rows whose other columns repeat header text.)
  - [blocking] `address.full<-Supplier address Parties/address`: The value 'not assessed' was emitted as a supplier address. The source states no address, so this puts a non-address value in the field. (suggested: Treat 'not assessed' and 'N/A' as null for this field and emit no observation.)
  - [advisory] `entity.legal_name<-Supplier name Parties additionalidentifiers/id`: Several supplier names look like trading or short names rather than registered legal names, for example 'Stryker', 'Blue Care', 'Bunzl Outsourcing' and 'Corrs Chambers Westgarth'. The source does not say they are legal names. (suggested: Lower field_confidence for names without a suffix such as Pty Ltd. Resolve them against the ABR later.)
  - [advisory] `entity.abn<-Supplier ABN Parties/identifier/uri`: The ABN mapping produced no observations in any example. The column is either absent or holds 'not assessed', so the mapping gives no supplier identifier. This limits entity resolution to name matching. (suggested: Confirm whether the ABN column is populated in other rows. If it is not, flag the lack of identifiers.)
  - [advisory] `address.full<-Supplier address Parties/address`: Some addresses are only a locality or city, for example 'Brisbane' and 'Perth, WA'. They are stored as full addresses, and state and locality are not parsed out. (suggested: Parse locality, state and postcode where present. Lower field_confidence for partial addresses.)
  - [advisory] `envelope.valid_from`: valid_from is filled from the contract commence date in some rows and left null in others. The commence date is not in the config's mapped or unmapped lists, so the source of valid_from is undocumented. A contract start date also does not show when the supplier's name or address became true. (suggested: Document where valid_from comes from, or leave it null. A contract start date is not an entity-level validity date.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Supplier name Parties additionalidentifiers/id`: `not assessed` → `not assessed`; `Bunzl Outsourcing ` → `Bunzl Outsourcing`; `MaxStocks Frozen Foods Pty Ltd` → `MaxStocks Frozen Foods Pty Ltd`
- `address.full<-Supplier address Parties/address`: `not assessed` → `not assessed`; `42-44 Ponzo Street, Woree` → `42-44 Ponzo Street, Woree`; `347 Spence Street, Bungalow` → `347 Spence Street, Bungalow`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
