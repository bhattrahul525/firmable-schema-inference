| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1b_01 | datagovau:asic-smsf | csv | validated_config | 10 | 0.009961 | 50.67 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.stat |  |  |
| bench_dev1b_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | partial_config | 10 | 0.007308 | 40.69 | entity.legal_name<-Name; entity.abn<-ABN | finish: finish refused: this config adds or changes [reader] since the | design: one table per run |
| bench_dev1b_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 9 | 0.004958 | 28.91 | entity.abn<-ABN |  |  |
| bench_dev1b_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | partial_config | 15 | 0.015338 | 73.25 | entity.abn<-Supplier ABN; address.full<-Supplier address |  | model_judgement (run-to-run variance: validated in pass A) |
| bench_dev1b_05 | datagovau:avib-prrz | csv | validated_config | 12 | 0.009347 | 49.34 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1b_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | partial_config | 15 | 0.016394 | 166.97 | entity.abn<-lord_party_id; address.state<-state_code; address.postcode |  | model_judgement (same as pass A) |
| bench_dev1b_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 7 | 0.002129 | 9.51 |  |  | non_business (plausibly correct) |
| bench_dev1b_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.001472 | 3.73 |  |  | download: the publisher URL returns 404 |
| bench_dev1b_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 15 | 0.010813 | 56.51 | entity.trading_name<-School Name | finish: finish refused: partial_config needs at least one mapped field |  |
| bench_dev1b_10 | sa:river-murray-protection-area | json | no_business_entities | 6 | 0.002056 | 7.01 |  |  | non_business (plausibly correct) |
| bench_dev1b_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 14 | 0.004792 | 29.58 |  | finish: finish refused: could_not_read needs two reader attempts that  | reader_gap: MapInfo TAB geodata zip (not tabular) |
