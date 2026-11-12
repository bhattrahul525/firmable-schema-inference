| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1d_01 | datagovau:asic-smsf | csv | no_business_entities | 9 | 0.004434 | 13.98 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1d_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 9 | 0.005005 | 23.4 | entity.legal_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1d_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 11 | 0.007972 | 49.04 | entity.trading_name<-SchoolName; entity.abn<-ABN |  |  |
| bench_dev1d_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 9 | 0.008514 | 40.22 | entity.legal_name<-Supplier name; entity.abn<-Supplier ABN; address.fu |  |  |
| bench_dev1d_05 | datagovau:avib-prrz | csv | validated_config | 13 | 0.009923 | 47.05 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N; entity.entity_typ |  |  |
| bench_dev1d_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 15 | 0.017547 | 162.4 | entity.abn<-lord_party_id; address.state<-state_code; address.postcode |  |  |
| bench_dev1d_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 7 | 0.002309 | 8.82 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1d_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.001662 | 6.9 |  |  |  |
| bench_dev1d_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 12 | 0.006958 | 34.95 | entity.legal_name<-School Name | finish: finish refused: validated_config needs at least one mapped fie |  |
| bench_dev1d_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.002454 | 9.68 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1d_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 7 | 0.002715 | 10.77 |  |  |  |
