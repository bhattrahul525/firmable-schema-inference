| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1t_01 | datagovau:asic-smsf | csv | validated_config | 8 | 0.12788 | 36.85 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.date |  |  |
| bench_dev1t_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 8 | 0.063262 | 20.06 | entity.legal_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1t_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 7 | 0.069612 | 17.34 | entity.legal_name<-SchoolName; entity.abn<-ABN |  |  |
| bench_dev1t_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 8 | 0.114835 | 31.67 | entity.legal_name<-col_7; address.full<-col_8; entity.abn<-col_22 |  |  |
| bench_dev1t_05 | datagovau:avib-prrz | csv | validated_config | 7 | 0.096794 | 30.29 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1t_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 9 | 0.18096 | 109.51 | entity.legal_name<-party_name; address.state<-state_code; address.post |  |  |
| bench_dev1t_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 5 | 0.030975 | 6.0 |  |  |  |
| bench_dev1t_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 3 | 0.02594 | 4.08 |  |  |  |
| bench_dev1t_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 7 | 0.064132 | 18.5 | entity.legal_name<-_blank_1 |  |  |
| bench_dev1t_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.041659 | 9.01 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1t_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 4 | 0.028964 | 4.1 |  |  |  |
