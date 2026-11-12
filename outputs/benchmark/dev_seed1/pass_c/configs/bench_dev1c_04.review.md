# Review packet (round-2 agent): validated_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **validated_config**.
- 12 model turns, 12 tool calls, $0.0154, 69.85s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1c_04/trace.jsonl`.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier address Parties/address not assessed` | `address.full` | clean_whitespace | W | 0.80 | 100.0% | **0.80** |
| 2 | `Supplier ABN Parties/identifier/uri not assessed` | `entity.abn` | abn | W | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `address.full` ← `Supplier address Parties/address not assessed`: Supplier address as free text.
2. `entity.abn` ← `Supplier ABN Parties/identifier/uri not assessed`: Column is labelled Supplier ABN; checksum-validated by the abn transform. Populated sparsely.

## Left unmapped (not guessed)

- `Supplier name Parties additionalidentifiers/id not assessed`: Supplier name in a contract disclosure is not stated to be the registered name; withheld from legal_name pending a registry join (critique blocking issue).
- `Description OCDS name KDS`: Blank column in data rows
- `Agency (Dept or Stat Body) OCDS name`: government buyer, not the supplier entity
- `Agency address OCDS name`: government buyer address
- `Contract description/name Contracts/Title Contract Name`: contract title, no ontology field
- `Award contract date Contracts/dateSigned Contract Awarded Date`: contract award date, not the entity registration date
- `Contract value Contracts/value/amount Executed Contract Value`: no ontology field for contract value
- `Variation to contract (Yes/No) Not listed Not listed`: no ontology field
- `Specific confidentiality provision used Not listed`: no ontology field
- `Procurement method Tender procurementMethod Contract Type`: no ontology field
- `Form of contract Tender procurementMethod`: no ontology field
- `Number of offers sought Tender procurementMethod`: no ontology field
- `Evaluation criteria and weightings Tender procurementMethod`: no ontology field
- `Deliverables Tender procurementMethod`: no ontology field
- `Contract milestones Tender procurementMethod`: no ontology field
- `Contract performance management Tender procurementMethod`: no ontology field
- `Contract reference number Contracts/AwardID Tender Number`: contract identifier, not an entity identifier; partly blank
- `Contract category group Contracts/items/classification/description Category Group`: procurement category, no ontology field
- `Parent contract number/SOA Contracts Contracts`: no ontology field
- `Commence date Contracts/period/Start Date Planned Commencement Date`: mostly blank contract period, not entity validity
- `Finish date Contracts/period/endDate Planned Finish Date`: contract planned finish period, mostly blank; not entity validity

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 49, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping has one blocking problem: the supplier name is mapped to entity.legal_name although the source does not say it is the registered name, and the examples look like trading names. Several advisory items remain: a valid ABN in the data is unmapped and its column is wrongly described as empty, a finish date is wrongly described as empty, addresses could be parsed further, entity_type defaults need marking, and the envelope and source_record_id need checking against the required fields.
  - [blocking] `entity.legal_name<-Supplier name Parties additionalidentifiers/id not assessed`: The ontology defines legal_name as the name as registered, not the trading name. The config's own reason admits the register does not say this column is the registered name. Examples such as '1300 Smiles', 'Stryker' and 'Baxter Healthcare' read like trading names, and the mapping still asserts a registered-name meaning the source does not state. (suggested: Do not map this column to entity.legal_name. Map it to a supplier-name or trading_name observation with a caveat, or leave legal_name unmapped until a registered-name source (ABN Lookup or ASIC) is joined.)
  - [advisory] `entity.abn`: The config lists 'Supplier ABN' as an entirely empty column that is unmapped. Row 3 (Rauland Australia) has 'Supplier ABN' = '63 056 360 653'. That value passes the ABN checksum (weighted sum 445, divisible by 89), so the column is not empty and holds a usable identifier that is being discarded. (suggested: Map 'Supplier ABN Parties/identifier/uri not assessed' to entity.abn, strip spaces, validate the checksum, record derivation_level L1, and correct the 'entirely empty' note.)
  - [advisory] `unmapped: Finish date Contracts/period/endDate Planned Finish Date`: The reason says this column is entirely empty, but row 3 has '1/02/2026'. The documentation does not match the data and may hide values that matter. (suggested: Correct the reason to say the column is mostly blank, or remove it from the unmapped list with a note that it is contract-period data, not entity validity.)
  - [advisory] `address.full<-Supplier address Parties/address not assessed`: The raw address contains parseable parts such as state and postcode ('West End 4101', 'Atherton', 'NSW'), but the mapping stores the whole string in address.full only. The ontology's state, postcode and locality fields stay empty, and the address is not parsed further. (suggested: Keep address.full as the raw text and add parsed observations for address.state, address.postcode and address.locality where present, at derivation_level L1 with field_confidence reflecting parse quality.)
  - [advisory] `entity.entity_type`: Each record emits entity.entity_type = 'unknown' with source null. That is the ontology default, but it is shown as an observation without a derivation level or confidence values, so it reads like a claim rather than a default. (suggested: Either omit default-unknown entity_type observations or mark them explicitly as defaults with derivation_level and field_confidence, so they are not confused with source claims.)
  - [advisory] `observation envelope (source_id, source_record_id, ingested_at, licence, extractor_version)`: The example envelopes show only observed_at, valid_from and valid_to. The ontology marks source_id, source_record_id, ingested_at, licence and extractor_version as required on every record, and none appear in the examples. This may be display truncation, but it is unverified. (suggested: Confirm the emitted records carry all required envelope fields. Set licence from CKAN metadata, or 'unknown' with a flag. Use the 'Contract reference number' column as source_record_id in preference to a row hash, since it is traceable to the exact record.)
  - [advisory] `observation.source_record_id (record_id hash_row)`: source_record_id is a hash of the row, which the ontology requires to be traceable to the exact raw record. The source has a stable key ('Contract reference number', for example CHHHS89289-3), which is more traceable than a row hash, and the config does not document how the hash is built. (suggested: Use the contract reference number (plus row position if needed) as source_record_id, or document the deterministic hash construction and keep the raw row offset alongside it.)
- Critique: The mapping has one blocking meaning error: supplier names from a contract disclosure are mapped to legal_name, which the ontology reserves for registered names, and several examples look like trading names. The ABN mapping checks out on the one example that has it. The remaining points are advisory: an unsourced entity_type default, unparsed address components, and provenance caveats on the ABN column.
  - [blocking] `entity.legal_name<-Supplier name Parties additionalidentifiers/id not assessed`: The ontology defines legal_name as the name as registered, not the trading name. The config justifies mapping this contract-disclosure supplier name to legal_name by saying the ontology accepts 'supplier name' as legal_name, but the ontology says no such thing. The examples show names that are plausibly trading names rather than registered names, such as '1300 Smiles', 'A1 Cleaners', 'Bunzl Outsourcing', 'Stryker' and 'Baxter Healthcare'. The source does not state that these are registered legal names. (suggested: Stop emitting entity.legal_name from this column. Either emit it as a trading_name observation (one per record, with the source column cited), or hold it until an ABN or registry lookup confirms the registered name. Remove the reason text that claims the ontology accepts supplier name as legal_name.)
  - [advisory] `entity.entity_type`: Every example emits entity_type 'unknown' with from: null. No source column supports it. The default is correct under the ontology, but the observation carries no source trace. (suggested: Either omit the observation when no source supports it, or document it explicitly as a default rather than a source-derived claim, with derivation level and provenance recorded.)
  - [advisory] `address.full<-Supplier address Parties/address not assessed`: Addresses are passed through as free text. Some contain a state or postcode that could be parsed, for example '249 Boundary Street, West End 4101' and '43 Robert Street Atherton', and some lack a state, for example 'Level 23, Riverside Centre 123 Eagle Street Brisbane'. The address.state and address.postcode fields are never populated. (suggested: Add a deterministic parse step that extracts postcode (4-digit) and state where present, recording these as L1 derived values with field_confidence reflecting the parse. Leave them null where absent.)
  - [advisory] `entity.abn<-Supplier ABN Parties/identifier/uri not assessed`: The ABN column is populated in only one example. The checksum for 63 056 360 653 validates, so that example is fine. The header label 'identifier/uri not assessed' suggests the column's provenance has not been checked, and the config does not record that caveat. (suggested: Keep the abn transform, which already validates the checksum. Record the 'not assessed' provenance caveat in the config notes, and lower field_confidence or note the source limitation for the ABN observation.)

## Examples (raw → value, held-out rows)

- `address.full<-Supplier address Parties/address not assessed`: `42-44 Ponzo Street, Woree` → `42-44 Ponzo Street, Woree`; `38 Redden Street, Cairns` → `38 Redden Street, Cairns`; `347 Spence Street, Bungalow` → `347 Spence Street, Bungalow`
- `entity.abn<-Supplier ABN Parties/identifier/uri not assessed`: `63 056 360 653` → `63056360653`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
