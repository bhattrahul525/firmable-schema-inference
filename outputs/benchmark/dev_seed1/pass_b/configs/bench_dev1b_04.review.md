# Review packet (round-2 agent): partial_config

**Dataset:** CHHHS Contracts Disclosure 2020-21 — Queensland Health  
**Licence:** Creative Commons Attribution 4.0  
**File:** `chhhs_contract-disclosure-report.csv` (sha256 `baad51dea1d8…`)

## How this ended

- Outcome **partial_config**.
- 15 model turns, 15 tool calls, $0.0153, 73.25s (download and human waits excluded). Trace: `logs/agent_runs/bench_dev1b_04/trace.jsonl`.
- Reason: The register holds supplier ABNs (mostly blank) and supplier addresses for 51 contract rows. Supplier name is withheld from legal_name because the source does not state it is the registered name. Two label rows (KDS, OCDS name) are excluded from the address mapping by regex.

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|
| 1 | `Supplier ABN` | `entity.abn` | clean_whitespace → abn | W | 0.95 | n/a | **0.50** |
| 2 | `Supplier address` | `address.full` | clean_whitespace → regex_extract(^(?!Parties|not assessed)(.+)$) | W | 0.80 | 100.0% | **0.80** |

The model's reasons per field (its words, not verified):

1. `entity.abn` ← `Supplier ABN`: Explicitly labelled Supplier ABN; checksum validated; mostly blank in this register
2. `address.full` ← `Supplier address`: Supplier's address as free text; schema label rows excluded

## Left unmapped (not guessed)

- `Supplier name`: Contract counterparty name; the disclosure does not state it is the registered name, so not mapped to legal_name (blocking critique c-4afe96c4)
- `Description`: Row-type label only
- `Agency (Dept or Stat Body)`: government buyer
- `Agency address`: government buyer address
- `Contract description/name`: contract title, no canonical field
- `Award contract date`: contract award date, not entity registration date
- `Contract value`: contract value; no canonical field
- `Variation to contract (Yes/No)`: contract attribute
- `Specific confidentiality provision used`: contract attribute
- `Procurement method`: contract attribute
- `Form of contract`: contract attribute
- `Number of offers sought`: contract attribute
- `Evaluation criteria and weightings`: contract attribute
- `Deliverables`: contract attribute
- `Contract milestones`: contract attribute
- `Contract performance management`: contract attribute
- `Contract reference number`: contract identifier, not reliably filled
- `Contract category group`: contract classification
- `Parent contract number/SOA`: contract attribute
- `Commence date`: planned contract dates
- `Finish date`: planned contract dates

## Needs a transform the engine does not have

- `Contract value`: currency string needs a money-parse transform; no canonical field exists anyway

## Abstentions (fields removed, with reasons)

- `entity.legal_name<-Supplier name`: Supplier name is a counterparty name in a procurement disclosure, not stated as registered name; critique flagged it as blocking. Left out rather than guessed. Could be mapped to trading_name in a later run with a new critique.

## Checks

- Duplicate record ids in held-out rows: {'rows': 51, 'key': 'hash_row', 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is close, but the first example row is a schema row that the reader passes through as data, and it produces two blocking observations with nonsense values. Once that row is filtered out, the remaining legal_name and address mappings are mostly sound, with caveats about contract names versus registered names. The ABN mapping has never been exercised on real data, and the envelope is incomplete in the examples.
  - [blocking] `entity.legal_name<-Supplier name`: The first example row is a schema or metadata row (Description 'OCDS name', with column values such as 'Parties additionalidentifiers/id' and 'Parties/identifier/uri') that survived the reader. The engine turned its 'Supplier name' value into an entity.legal_name observation, so the output asserts that a company is legally named 'Parties additionalidentifiers/id'. The source does not support that. (suggested: Drop this row before mapping. Raise skip_rows or add a rule that discards rows whose Description is a schema label, and emit no entity observations from it.)
  - [blocking] `address.full<-Supplier address`: The same schema row yields an address.full observation with the value 'Parties/address'. That is a field path, not an address. (suggested: Filter out the schema row as above so that no address observation is produced from it.)
  - [advisory] `entity.legal_name<-Supplier name`: The source column is a contracting party name ('Supplier name'), and the mapping labels it legal_name 'as registered' on the basis of rule 4. Names such as 'Deloitte', 'Ozcare', 'Compumedics' and 'Baxter Healthcare' may be trading names, and nothing in the source says they are registered names. (suggested: Keep the observation but record the source as a contract counterparty name, or emit it as trading_name with lower field_confidence unless it is matched to a registry record that confirms the registered name.)
  - [advisory] `entity.abn<-Supplier ABN`: No real data row carries a Supplier ABN value; the only appearance is in the schema row, and drop_empty_columns may remove the column entirely. The ABN mapping therefore produces nothing and is untested against real values. (suggested: Confirm the column exists and is populated in the actual data. If it is always empty, document that the field is unavailable for this source rather than leaving an unexercised mapping in place.)
  - [advisory] `entity.entity_type`: Every record emits an entity_type observation of 'unknown' with a null source column. This is a default, not a claim from the source, and it adds an observation to every row. (suggested: Do not emit default values as observations. Set entity_type only when a source states it.)
  - [advisory] `address.full<-Supplier address`: Some supplier addresses contain a state (for example 'Old Toongabbie, NSW', 'Abbotsford VIC', 'Perth WA') but the mapping stores only the raw string and does not parse state or postcode. The agency address state QLD must not be used for the supplier. (suggested: Parse state into address.state, using an L1 derivation, and keep the raw string in address.full. Leave state empty when the address does not state one.)
  - [advisory] `observation`: The example envelopes show only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are absent from the output shown, and licence is not stated for this dataset. (suggested: Show or emit the full required envelope on every observation. Record licence as 'unknown' and flag it if the CKAN metadata does not state one.)
- Critique: The config handles the schema label rows and placeholder rows, but the main meaning error is that supplier names are mapped to entity.legal_name when the disclosure does not state registered names. The default 'unknown' entity_type observations and the envelope and regex issues are advisory.
  - [blocking] `entity.legal_name<-Supplier name`: The source column is the supplier name as written in a procurement disclosure. Several examples are brand or trading-style names, not registered legal names (for example 'Deloitte', 'Ozcare', 'Compumedics', 'Ernst and Young', 'Baxter Healthcare'). Mapping them to entity.legal_name states a registered name the source does not support. (suggested: Map Supplier name to entity.trading_name (or an observation of the name as stated in the disclosure) rather than legal_name. Only populate legal_name from a source that states the registered name, such as an ABN or ACN register lookup.)
  - [advisory] `entity.entity_type`: Every emitted record includes an entity.entity_type observation with value 'unknown' and from: null. No source column produces it. It is a default written as if it were a source claim. (suggested: Do not emit default values as observations. Omit entity_type when no source states it, or record it explicitly as a defaulted value with a derivation note.)
  - [advisory] `observation envelope`: The shown envelopes contain only observed_at, valid_from and valid_to. The required fields source_id, source_record_id, ingested_at, licence and extractor_version are not visible in the examples, and the config does not show where licence or source_id come from. (suggested: Confirm that every emitted observation carries all required envelope fields, including licence (or 'unknown' with a flag) and extractor_version, and show them in the examples.)
  - [advisory] `entity.legal_name<-Supplier name regex`: The regex excludes any supplier name beginning with 'Parties' or 'not assessed'. This is a prefix match, so a real supplier whose name begins with 'Parties' would be dropped, and the match is case-sensitive, so 'Not assessed' would pass through. (suggested: Match the exact placeholder and label rows (for example anchored full-line matches) and make the placeholder check case-insensitive, rather than excluding by name prefix.)

## Examples (raw → value, held-out rows)

- `address.full<-Supplier address`: `38 Redden Street, Cairns` → `38 Redden Street, Cairns`; `347 Spence Street, Bungalow` → `347 Spence Street, Bungalow`; `Level 23, Riverside Centre 123 Eagle Street Brisba` → `Level 23, Riverside Centre 123 Eagle Street Brisbane`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
