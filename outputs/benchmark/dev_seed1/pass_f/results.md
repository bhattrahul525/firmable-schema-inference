| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1f_01 | datagovau:asic-smsf | csv | validated_config | 11 | 0.010328 | 54.99 | entity.abn<-SMSF_PERSON_ABN |  |  |
| bench_dev1f_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 11 | 0.007537 | 41.63 | entity.trading_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1f_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 9 | 0.005454 | 30.01 | entity.abn<-ABN; entity.trading_name<-SchoolName |  |  |
| bench_dev1f_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 10 | 0.011241 | 55.61 | entity.legal_name<-Supplier name; address.full<-Supplier address; enti |  |  |
| bench_dev1f_05 | datagovau:avib-prrz | csv | validated_config | 11 | 0.008661 | 47.33 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N; entity.entity_typ |  |  |
| bench_dev1f_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 18 | 0.028426 | 226.62 | entity.abn<-lord_party_id_type+lord_party_id; entity.trading_name<-par |  |  |
| bench_dev1f_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 7 | 0.002543 | 11.3 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1f_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.001749 | 6.16 |  |  |  |
| bench_dev1f_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 9 | 0.005435 | 23.86 | entity.trading_name<-School Name |  |  |
| bench_dev1f_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.002778 | 9.38 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1f_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 5 | 0.002144 | 7.69 |  |  |  |
