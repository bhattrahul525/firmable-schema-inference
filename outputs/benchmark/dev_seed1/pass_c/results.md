| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1c_01 | datagovau:asic-smsf | csv | validated_config | 11 | 0.010056 | 49.16 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.stat |  |  |
| bench_dev1c_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | validated_config | 9 | 0.005582 | 27.45 | entity.legal_name<-Name; entity.abn<-ABN |  |  |
| bench_dev1c_03 | vic:victorian-government-schools-abns | xlsx | validated_config | 10 | 0.007366 | 40.12 | entity.trading_name<-SchoolName; entity.abn<-ABN |  |  |
| bench_dev1c_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 12 | 0.015386 | 69.85 | address.full<-Supplier address Parties/address not assessed; entity.ab |  |  |
| bench_dev1c_05 | datagovau:avib-prrz | csv | validated_config | 11 | 0.008401 | 41.27 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N |  |  |
| bench_dev1c_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | validated_config | 13 | 0.016735 | 147.04 | entity.abn<-lord_party_id; address.state<-state_code; address.postcode |  |  |
| bench_dev1c_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 8 | 0.002485 | 10.84 |  |  |  |
| bench_dev1c_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.00156 | 4.76 |  |  |  |
| bench_dev1c_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | no_business_entities | 6 | 0.00248 | 9.29 |  |  |  |
| bench_dev1c_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.00259 | 9.62 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_dev1c_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 7 | 0.00252 | 10.47 |  |  |  |
