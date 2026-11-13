# Review packet (round-2 agent): validated_config

**Dataset:** Notifiable Invoices Register — ACT Government Open Data  
**Licence:** Other  ⚠️ **LICENCE FLAGGED: check terms before use**  
**File:** `query.json` (sha256 `5f1ef1fd815f…`)

## How this ended

- Outcome **validated_config**.
- 9 model turns, 9 tool calls, $0.0066, 35.01s (download and human waits excluded). Trace: `logs/agent_runs/act_notifiable_invoices/trace.jsonl`.
- Evidence the agent gave at finish (its words): Resource 1 (query.json, JSON array of 127,437 records, 300 held out). :id unique across 127,137 training rows. supplier_abn passes abn checksum on 99.9% of sampled rows; supplier_name parses 100%. Validate: 0 hard failures, 0 meaning warnings. Critique: 0 blocking, 2 advisory.

## Reader and record settings

- reader: `{"format": "json", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- `record_id`: from `:id` — 0 duplicate / blank keys of 127437 rows (whole file)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. `{":id": "row-ym6w~bnk9-yypb", ":version": "rv-maa4-2xjk.h4pk", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MARSH PTY LTD", "supplier_abn": "`
2. `{":id": "row-428w-rrmt~ebuw", ":version": "rv-na9i-ji33~ven6", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MARSH PTY LTD", "supplier_abn": "`
3. `{":id": "row-q8fq_ac3e~ggvw", ":version": "rv-e6eb~m2h4_byyg", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "LEGATO TECHNOLOGIES CONSULTING PT`
4. `{":id": "row-5fmq_akrz-tj7a", ":version": "rv-rj5k.a8yd.uxn3", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "BELLCHAMBERS BARRETT PTY LTD", "s`
5. `{":id": "row-usse-esmk.dw4x", ":version": "rv-4eck_zy24~3g7n", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MARSH PTY LTD", "supplier_abn": "`
6. `{":id": "row-tvn2_xqvv-vwhg", ":version": "rv-5qap-4mc9.ammh", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MINTER ELLISON LAWYERS", "supplie`
7. `{":id": "row-e6fi_jt5j.en3a", ":version": "rv-gijk~fj5b.c8q6", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "ABA CONSTRUCTION MANAGERS AUSTRAL`
8. `{":id": "row-y3mx_rdty~ri45", ":version": "rv-q9vc_uau8~texc", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "AUSTRALIAN ELECTORAL COMMISSION",`
9. `{":id": "row-8sa3-6xs9~7svm", ":version": "rv-vyzt-93z4_cuzv", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "F1 SOLUTIONS PTY LIMITED", "suppl`
10. `{":id": "row-f95h~azsp.hf2z", ":version": "rv-5is7_kfta~gezj", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MARSH PTY LTD - CANBERRA", "suppl`
11. `{":id": "row-ksbe.qz5c-g57x", ":version": "rv-43rk_7ct3~y987", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "ABBOTT AUSTRALASIA PTY LTD", "sup`
12. `{":id": "row-m2r4-rce8-w3pp", ":version": "rv-rq85_upfa-7erg", ":created_at": "2026-04-24T03:25:02.713Z", ":updated_at": "2026-04-24T03:25:02.713Z", "supplier_name": "MARSH PTY LTD", "supplier_abn": "`

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `supplier_name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 2 | `supplier_abn` | `entity.abn` | abn | W | held_out | 0.95 | 100.0% | **0.95** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `supplier_name`: Supplier name on a payment record; the supplier is the entity, and the column is the supplier's name as stated in the source.
2. `entity.abn` ← `supplier_abn`: Supplier ABN column, checksum-validated.

## Left unmapped (not guessed)

- `reporting_entity`: government buyer (ACT agency reporting the payment), not the supplier
- `publish_description`: description of the goods/services purchased, not an industry code
- `date_invoice_received`: date of a transaction the row records; not when the supplier's identity became true
- `payment_date`: date of a payment event
- `payment_amount`: transaction amount; no canonical field
- `contract_number`: contract reference of the transaction, not an entity identifier
- `:version`: source record revision metadata
- `:created_at`: source system timestamp, not the claim date
- `:updated_at`: source system timestamp, not the claim date

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `observed_at`: Critique advisory c-5c1dd88a: observed_at uses dataset-level resource_last_modified, not a per-row statement date; kept as the best available metadata date and flagged.

## Checks

- Duplicate record ids in held-out rows: {'rows': 127437, 'key': [':id'], 'duplicate_rows': 0, 'blank_key_rows': 0}
- Critique: The mapping is largely sound: supplier_name is the supplier (the entity) and maps to legal_name as the supplier's stated name, and supplier_abn maps to abn with checksum validation. The reporting agency, descriptions, dates and amounts are correctly left unmapped. No value appears in the wrong field in the examples, so I found no blocking issues. The remaining points are advisory: the observed_at provenance and the unverified record_id uniqueness.
  - [advisory] `observed_at`: observed_at comes from resource_last_modified, which is a dataset-level timestamp. The rows carry :created_at and :updated_at, which the config treats as system timestamps, so the claim date is not stated per row. The envelope's 2026-09-30 is therefore a metadata date, not a date the payment record states. (suggested: Keep from_metadata if the dataset-level date is the best available statement date, and note in the source documentation that observed_at is the publication/modification date rather than a claim date.)
  - [advisory] `record_id`: The config takes record_id from :id but does not show a check_unique result. The sample :id values look unique, but the config does not confirm it. (suggested: Record the check_unique result for :id, or use hash_row=true if uniqueness fails.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-supplier_name`: `SCYNE ADVISORY` → `SCYNE ADVISORY`; `AITCH ADVISORY PTY LTD` → `AITCH ADVISORY PTY LTD`; `ACTEWAGL RETAIL` → `ACTEWAGL RETAIL`
- `entity.abn<-supplier_abn`: `20 607 773 295` → `20607773295`; `38 659 121 258` → `38659121258`; `44 600 665 183` → `44600665183`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
