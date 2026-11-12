# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 13 model turns, 13 tool calls, $0.0160, 77.08s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1a_04/trace.jsonl`.
- Evidence the agent gave at finish (its words): validate (call 3): 0 hard failures, record_id hash_row unique, all parse rates 1.0 on held-out rows. Header rows merged (skip_rows 2, header_rows 3) to remove the OCDS/KDS label rows.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier name Parties additionalidentifiers/id not assessed` | `entity.entity_type` | entity_type_from_suffix | W | 0.60 | 100.0% | **0.60** |
| 2 | `Supplier ABN Parties/identifier/uri not assessed` | `entity.abn` | abn | W | 0.90 | 100.0% | **0.90** |
| 3 | `Supplier address Parties/address not assessed` | `address.full` | clean_whitespace | W | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.entity_type` ← `Supplier name Parties additionalidentifiers/id not assessed`: No explicit entity type column; suffix rule on supplier name.
2. `entity.abn` ← `Supplier ABN Parties/identifier/uri not assessed`: Supplier ABN column; checksum validated. Very sparsely filled.
3. `address.full` ← `Supplier address Parties/address not assessed`: Supplier address as given.

## Left unmapped (not guessed)

- `Supplier name Parties additionalidentifiers/id not assessed`: Supplier name is not stated as the registered name (procurement disclosure; examples are trading-style names); not mapped to legal_name pending ABN/register match. Used only for entity_type suffix rule.
- `Description OCDS name KDS`: Blank in data rows; label text only
- `Agency (Dept or Stat Body) OCDS name`: government buyer, not the supplier
- `Agency address OCDS name`: government buyer address, not the supplier
- `Contract description/name Contracts/Title Contract Name`: contract description; no ontology field
- `Award contract date Contracts/dateSigned Contract Awarded Date`: contract award date; no ontology field; not date_registered
- `Contract value Contracts/value/amount Executed Contract Value`: contract value; no ontology field
- `Variation to contract (Yes/No) Not listed Not listed`: contract attribute
- `Specific confidentiality provision used Not listed`: contract attribute
- `Procurement method Tender procurementMethod Contract Type`: contract attribute
- `Form of contract Tender procurementMethod`: contract attribute
- `Number of offers sought Tender procurementMethod`: contract attribute
- `Evaluation criteria and weightings Tender procurementMethod`: contract attribute
- `Deliverables Tender procurementMethod`: contract attribute
- `Contract milestones Tender procurementMethod`: contract attribute
- `Contract performance management Tender procurementMethod`: contract attribute
- `Contract reference number Contracts/AwardID Tender Number`: contract identifier, not entity; not unique
- `Contract category group Contracts/items/classification/description Category Group`: contract attribute, not ANZSIC
- `Parent contract number/SOA Contracts Contracts`: contract attribute
- `Commence date Contracts/period/Start Date Planned Commencement Date`: contract period; not licence validity
- `Finish date Contracts/period/endDate Planned Finish Date`: contract period

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 49, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The main blocking problem is that a column-label row is treated as a supplier record, and its 'not assessed' placeholder is emitted as a legal name and address. Other points are advisory: legal_name is taken from a procurement label that does not establish registration, the ABN is configured but never observed, state is not parsed, and the envelope examples omit required fields.
  - [blocking] `entity.legal_name<-Supplier name`: The first example row is a column-label row, not a supplier record. Its Supplier name is the placeholder 'not assessed', and the mapping still emits it as entity.legal_name. The value is a placeholder, not a company name the source states. (suggested: Detect and drop label/placeholder rows before mapping (e.g. Supplier name equal to 'not assessed' or a header-style row). Emit no legal_name observation for them.)
  - [blocking] `address.full<-Supplier address`: The same label row emits address.full = 'not assessed'. This is a placeholder meaning 'not assessed', not a supplier address. (suggested: Treat 'not assessed' and similar sentinel strings as missing values and emit no address observation.)
  - [advisory] `entity.entity_type<-Supplier name`: The label row also yields entity_type 'unknown' from a placeholder name. This is harmless only because the default is unknown, but it is still an observation produced from no real claim. (suggested: Suppress the entity_type observation whenever the supplier name is a placeholder, so no observation is produced from a non-claim.)
  - [advisory] `entity.legal_name<-Supplier name`: The ontology defines legal_name as 'as registered, not the trading name'. The source column is a procurement 'Supplier name' with no registration basis. Names such as 'Blue Care', 'QRMC', 'Benstar', '1300 Smiles' and 'Bidfood Cairns' may be trading names, so the claim that they are registered legal names is not supported by the source. (suggested: Record the value under a source-labelled name or lower the confidence/caveat it, and note that it is the name as typed in the procurement disclosure, not the registered legal name, until matched to a register.)
  - [advisory] `entity.abn<-Supplier ABN`: The ABN mapping is configured, but no abn observation appears in any example, including rows where the column is blank or 'not assessed'. The config says the field is very sparse, so the absence is expected, but it is not shown as an explicit missing-value outcome. (suggested: Confirm that blank and 'not assessed' ABNs produce no observation and are logged as missing, and that checksum failures are logged separately.)
  - [advisory] `address.state`: Supplier addresses such as '105 Denham Street, Townsville QLD' and 'Brisbane City QLD' contain a state, and '347 Spence Street, Bungalow' contains none. The mapping only fills address.full, so the state and postcode that the source does state are not parsed out. (suggested: Add a parse of the state abbreviation into address.state (L1, with field_confidence reflecting parse certainty) and leave it null when absent.)
  - [advisory] `observation.licence`: The example envelopes show observed_at, valid_from and valid_to, but no source_id, source_record_id, ingested_at, licence or extractor_version, which are all required by the ontology. (suggested: Show the complete envelope in the examples. Licence should be read from the CKAN metadata or recorded as 'unknown' and flagged.)
- Critique: The entity_type suffix rule and the default of unknown are applied correctly, and the buyer fields are correctly excluded. The main meaning error is that supplier names, which the config itself says are not registered names, are emitted as legal_name. Address and envelope points are advisory.
  - [blocking] `entity.legal_name<-Supplier name Parties additionalidentifiers/id not assessed`: The ontology defines legal_name as the registered name, not the trading name. The config's own reason says the supplier name is 'not stated as registered name', yet it is mapped to legal_name. The examples show trading-style names such as 'Bidfood Cairns', 'Blue Care', '1300 Smiles' and 'Benstar' being emitted as legal names, which the source does not support. (suggested: Do not emit legal_name from this column. Emit the supplier name as a low-confidence observation under a non-legal field, or hold it until an ABN/ACN lookup confirms the registered name.)
  - [advisory] `address.full<-Supplier address Parties/address not assessed`: Several values are not full addresses. 'Brisbane' (Blue Care) and 'Unit 21, 170-182 Mayers Street' (Activtec, no suburb or state) are mapped as address.full. Others, such as '5 Commercial Place, Cairns QLD', contain a state and locality that are not parsed into address.state, address.locality or address.postcode. (suggested: Keep address.full as the raw string, parse locality and state where present, and lower field_confidence or note incompleteness for partial addresses such as 'Brisbane'.)
  - [advisory] `observation envelope`: The shown envelopes contain only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are absent from the examples, although the ontology says every emitted record carries them. (suggested: Confirm the full envelope is emitted, including licence from the CKAN metadata (or 'unknown' with a flag) and a deterministic source_record_id from the hashed row.)
  - [advisory] `observed_at`: observed_at is taken from resource_last_modified, but the ontology says observed_at is 'when the source stated it'. The Activtec row has a contract award date of 1/09/2021, which is after the observed_at of 2021-08-02, so the timestamp may not reflect when the claim was made. (suggested: Document that observed_at is a proxy from dataset metadata, and consider keeping the contract award date as a separate provenance note rather than relying on it for observed_at.)

## Examples (raw → value, held-out rows)

- `entity.entity_type<-Supplier name Parties additionalidentifiers/id not assessed`: `Bidfood Cairns ` → `unknown`; `MaxStocks Frozen Foods Pty Ltd` → `company`; `Maxwells H20 Services Pty Ltd ` → `company`
- `address.full<-Supplier address Parties/address not assessed`: `38 Redden Street, Cairns` → `38 Redden Street, Cairns`; `347 Spence Street, Bungalow` → `347 Spence Street, Bungalow`; `5 Commercial Place, Cairns QLD ` → `5 Commercial Place, Cairns QLD`
- `entity.abn<-Supplier ABN Parties/identifier/uri not assessed`: `63 056 360 653` → `63056360653`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
