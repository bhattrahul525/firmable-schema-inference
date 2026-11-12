| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1e_01 | datagovau:asic-smsf | csv | validated_config | 11 | 0.010514 | 47.28 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.stat |  |  |
| bench_dev1e_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 10 | 0.005462 | 26.21 | entity.abn<-ABN; entity.trading_name<-Name |  |  |
| bench_dev1e_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 13 | 0.008818 | 43.04 | entity.abn<-ABN; entity.trading_name<-SchoolName |  |  |
| bench_dev1e_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 10 | 0.009951 | 45.3 | entity.legal_name<-Supplier name Parties additionalidentifiers/id not  | finish: finish refused: `critique` has not run. Call `critique` with t |  |
| bench_dev1e_05 | datagovau:avib-prrz | csv | validated_config | 11 | 0.008939 | 43.29 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1e_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 15 | 0.016048 | 182.7 | entity.abn<-lord_party_id; address.state<-state_code; address.postcode |  |  |
| bench_dev1e_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 8 | 0.002459 | 10.15 |  |  |  |
| bench_dev1e_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.00169 | 4.75 |  |  |  |
| bench_dev1e_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 10 | 0.005354 | 22.91 | entity.trading_name<-School Name |  |  |
| bench_dev1e_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.0024 | 7.91 |  |  |  |
| bench_dev1e_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 5 | 0.002153 | 8.82 |  |  |  |
