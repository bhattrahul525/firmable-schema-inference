| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1s_01 | datagovau:asic-smsf | csv | validated_config | 8 | 0.127094 | 38.68 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.date |  |  |
| bench_dev1s_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 7 | 0.06407 | 17.46 | entity.legal_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1s_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 7 | 0.063123 | 21.93 | entity.legal_name<-SchoolName; entity.abn<-ABN |  |  |
| bench_dev1s_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 11 | 0.184845 | 56.27 | entity.legal_name<-Supplier name Parties additionalidentifiers/id; ent |  |  |
| bench_dev1s_05 | datagovau:avib-prrz | csv | validated_config | 8 | 0.100588 | 30.97 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1s_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 16 | 0.330576 | 196.94 | entity.abn<-lord_party_id; entity.legal_name<-party_name; address.stat | execute: unknown tool 'execute'; available: ['ask_human', 'check_uniqu |  |
| bench_dev1s_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 6 | 0.033657 | 7.17 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1s_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 3 | 0.025629 | 4.0 |  |  |  |
| bench_dev1s_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | validated_config | 8 | 0.068596 | 18.53 | entity.legal_name<-School Name |  |  |
| bench_dev1s_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.040153 | 9.25 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1s_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 4 | 0.028679 | 4.76 |  |  |  |
