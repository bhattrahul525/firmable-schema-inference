# Review packet: act_notifiable_invoices (config v2)

**Dataset:** Notifiable Invoices Register — ACT Government Open Data  
**Page:** https://data.gov.au/data/dataset/kzmf-7uhp  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `query.json` (sha256 `5f1ef1fd815f…`)  
**What the agent says it is:** ACT Government Notifiable Invoices Register: a JSON export of invoices/payments made by ACT government agencies to suppliers above the notification threshold.  
**One row is:** one notified invoice payment from an ACT government reporting entity to a supplier

## How this was produced

- Model `claude-haiku-5-5`; 5 LLM calls; 57,297 input + 11,796 output tokens; cost $0.0093 (computed from list prices); LLM time 55.4s.
- Revision rounds: 1. Tested on 300 held-out rows the model never saw.
- Reader: `{'format': 'json', 'encoding': 'utf-8'}`. Record id: `{'from': [':id']}` — Column :id has 127437 distinct values across 127437 rows, so it uniquely identifies each row.
- observed_at: `{'from_metadata': 'resource_last_modified'}`. valid_from: `None`. valid_to: `None`.
- source_reliability (the model's judgement, not measured): `{'identity': 0.6, 'address': 0.5, 'classification': 0.4, 'contact': 0.5}` — Statutory ACT government disclosure of payments above the notification threshold. Supplier names and ABNs come from government accounts-payable records, not a verified register, so identity is moderate. There is no address or contact data. Classification is weak because publish_description describes spend, not the supplier's industry. Licence is listed as Other and flagged, so it is not a clear open licence.

## Mapped fields: mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |
|---|---|---|---|---|---|---|---|---|
| 1 | `supplier_name` | `entity.legal_name` | clean_whitespace | 0.85 | 100.0% (ok 300, rejected 0) | **0.85** | agreed | `SYDNEY NIGHT PATROL AND INQUIRY CO. PTY LTD` → `SYDNEY NIGHT PATROL AND INQUIRY CO. PTY LTD`<br>`CAP SUPPORT PTY LTD` → `CAP SUPPORT PTY LTD`<br>`COMENSURA PTY LIMITED` → `COMENSURA PTY LIMITED` |
| 2 | `supplier_abn` | `entity.abn` | abn | 0.85 | 100.0% (ok 298, rejected 0) | **0.85** | agreed | `11 000 013 098` → `11000013098`<br>`63 668 733 220` → `63668733220`<br>`30 120 725 902` → `30120725902` |
| 3 | `supplier_name` | `entity.entity_type` | entity_type_from_suffix | 0.60 | 100.0% (ok 300, rejected 0) | **0.60** | agreed | `SYDNEY NIGHT PATROL AND INQUIRY CO. PTY LTD` → `company`<br>`CAP SUPPORT PTY LTD` → `company`<br>`COMENSURA PTY LIMITED` → `company` |

Model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `supplier_name`: Supplier name on a government payment register. The data says it is the supplier name, which we treat as the registered name. Not verified against a company register, so confidence is below 0.9.
2. `entity.abn` ← `supplier_abn`: Column is named supplier_abn and about 99.6 percent of values are 11-digit numbers. Values are space-grouped (e.g. 83 121 852 088); spaced values were observed to produce valid entity.abn observations in tested rows (e.g. 11 000 013 098 gives 11000013098). Non-ABN values such as International are skipped by the abn transform and remain unmapped. Checksum validation is applied.
3. `entity.entity_type` ← `supplier_name`: The source has no explicit entity-type column, so the suffix rule on the supplier name is used. Names without a company suffix, such as trusts and bodies, resolve to unknown.

## Left unmapped (not guessed)

- `reporting_entity`: Government buyer (ACT agency or directorate reporting the payment), not the supplier. Not mapped per rule 4.
- `publish_description`: Describes the purchase or expense category, not the supplier's industry. No canonical field matches. Not translated to ANZSIC.
- `date_invoice_received`: Invoice receipt date is a transaction date, not a registration or licence validity date. No canonical field matches. Sparsely filled at about 85 percent.
- `payment_date`: Payment transaction date. No canonical field matches, and it does not state when a supplier's status or licence started or ended.
- `payment_amount`: Transaction amount. No canonical amount field exists in this ontology subset.
- `contract_number`: Contract reference for the payment. No canonical field matches. Mostly blank, with N/A values.
- `:version`: System or export revision identifier. Not a claim about the entity.
- `:created_at`: System export timestamp. Not the statement date of the claim, which is covered by observed_at from resource_last_modified.
- `:updated_at`: System export timestamp. Not the statement date of the claim, which is covered by observed_at from resource_last_modified.

## Needs a transform the engine does not have

- `—`: none

## Checks

- No meaning warnings on held-out rows.
- Duplicate record ids in held-out rows: {'duplicate_rows': 0, 'of': 300}
- Proposal disagreements (two independent proposals): only-1 0, only-2 0; those fields are capped at 0.70.
- Fields the agent abstained on after failing validation: none

## Critique step (reads raw rows next to output)

No meaning errors in the examples: legal_name comes from supplier_name, abn from supplier_abn, entity_type is 'company' only for Pty Ltd/Ltd names and 'unknown' for individuals and other names, and the reporting_entity buyer is correctly left unmapped. The only real problem is the stale needs_transform entry about ABN spacing, which the examples contradict.
- `needs_transform`: The needs_transform entry says the abn transform may reject space-grouped ABNs and a whitespace-stripping transform may be needed. The examples show space-grouped values such as '11 000 013 098' and '83 072 293 880' producing valid entity.abn observations ('11000013098', '83072293880'), so the risk appears to be resolved. The entry is stale and contradicts the working output. (suggested: Confirm the abn transform strips internal spaces on a larger sample, then remove the needs_transform entry or change it to a note that spaced values are handled. Keep the non-AU 'International' values unmapped as the config already states.)

## What changed during revision

**critique**
- Removed the needs_transform entry for supplier_abn and rewrote the supplier_abn field reason to state that space-grouped ABNs are handled by the abn transform. — Reviewer raw rows show space-grouped values such as 11 000 013 098 and 83 072 293 880 producing valid entity.abn observations (11000013098, 83072293880), so the spacing risk recorded in the earlier config is not present. The entry was stale and contradicted the working output. Non-AU International values remain unmapped as before.

## Three sample rows, raw

- `{':id': 'row-2i8t-f32t_62sc', ':version': 'rv-kzjh-s9p2_vmp7', ':created_at': '2026-04-24T03:25:02.713Z', ':updated_at': '2026-04-24T03:25:02.713Z', 'supplier_name': 'SYDNEY NIGHT PATROL AND INQUIRY CO. PTY LTD', 'supplier_abn': '11 000 013 098', 'reporting_entity': 'CMTEDD-ED', 'publish_description': 'SECURITY COSTS FOR FRANCE V LEBANON RUGBY LEAGUE WORLD CUP MATCH AT GIO STADIUM', 'date_invoice_received': '2017-11-08T00:00:00.000', 'payment_date': '2017-11-16T00:00:00.000', 'payment_amount': '49655.36'}`
- `{':id': 'row-id7q-dg48~6jfk', ':version': 'rv-gtw2~gn3z.u52y', ':created_at': '2026-04-24T03:25:02.713Z', ':updated_at': '2026-04-24T03:25:02.713Z', 'supplier_name': 'CAP SUPPORT PTY LTD', 'supplier_abn': '63 668 733 220', 'reporting_entity': 'CSD', 'publish_description': 'YOUNG PEOPLE WITH HIGH AND COMPLEX NEEDS', 'date_invoice_received': '2025-05-29T00:00:00.000', 'payment_date': '2025-06-06T00:00:00.000', 'payment_amount': '87757.03'}`
- `{':id': 'row-etfq_vikq-7qsw', ':version': 'rv-jq5h_irvz_k45d', ':created_at': '2026-04-24T03:25:02.713Z', ':updated_at': '2026-04-24T03:25:02.713Z', 'supplier_name': 'COMENSURA PTY LIMITED', 'supplier_abn': '30 120 725 902', 'reporting_entity': 'ETD', 'publish_description': 'SUPPLY OF CONTRACTOR CENTRAL WORKERS FOR ALL INVOICES APPROVED IN W/E 11/09/2024', 'date_invoice_received': '2024-09-13T00:00:00.000', 'payment_date': '2024-09-24T00:00:00.000', 'payment_amount': '28300.07'}`

---
To review: `python -m src.part2_agent.approve act_notifiable_invoices`
