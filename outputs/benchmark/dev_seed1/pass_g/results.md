| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1g_01 | datagovau:asic-smsf | csv | validated_config | 8 | 0.126906 | 33.69 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.date |  |  |
| bench_dev1g_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 8 | 0.074705 | 18.1 | entity.legal_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1g_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 7 | 0.06509 | 19.33 | entity.legal_name<-SchoolName; entity.abn<-ABN |  |  |
| bench_dev1g_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 8 | 0.106671 | 29.41 | entity.legal_name<-Supplier name; entity.abn<-Supplier ABN; address.fu |  |  |
| bench_dev1g_05 | datagovau:avib-prrz | csv | validated_config | 7 | 0.093417 | 24.57 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1g_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 10 | 0.17847 | 204.19 | entity.legal_name<-party_name; address.state<-state_code; address.post |  |  |
| bench_dev1g_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 5 | 0.033471 | 7.35 |  |  |  |
| bench_dev1g_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 3 | 0.02709 | 3.28 |  |  |  |
| bench_dev1g_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 8 | 0.073343 | 17.94 | entity.legal_name<-School Name |  |  |
| bench_dev1g_10 | sa:river-murray-protection-area | json | no_business_entities | 8 | 0.048436 | 9.9 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1g_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 4 | 0.030013 | 5.66 |  |  |  |
