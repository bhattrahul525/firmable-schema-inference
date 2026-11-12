| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_dev1a_01 | datagovau:asic-smsf | csv | validated_config | 9 | 0.009245 | 48.36 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.stat |  |  |
| bench_dev1a_02 | datagovau:junior-minerals-exploration-incentive-credit-allocations | xlsx | partial_config | 10 | 0.00588 | 31.83 | entity.legal_name<-Name; entity.abn<-ABN |  | design: one table per run |
| bench_dev1a_03 | vic:victorian-government-schools-abns | xlsx | partial_config | 11 | 0.008447 | 52.36 | entity.trading_name<-SchoolName |  | model_judgement |
| bench_dev1a_04 | qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config | 13 | 0.015964 | 77.08 | entity.entity_type<-Supplier name Parties additionalidentifiers/id not |  |  |
| bench_dev1a_05 | datagovau:avib-prrz | csv | validated_config | 14 | 0.010487 | 47.82 | entity.legal_name<-Licensee Name; entity.acn<-A.C.N; entity.entity_typ |  |  |
| bench_dev1a_06 | datagovau:intellectual-property-longitudinal-research-data-2020 | csv | partial_config | 15 | 0.016803 | 180.42 | entity.abn<-lord_party_id; address.state<-state_code; address.postcode |  | model_judgement (+ download cap on the first resource tried) |
| bench_dev1a_07 | sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities | 8 | 0.002459 | 11.03 |  | finish: finish refused: no_business_entities needs a successful read_t | non_business (plausibly correct); resource choice |
| bench_dev1a_08 | vic:contract-expenditure-under-strategic-sourcing-management-2010-11-i | xlsx | could_not_read | 4 | 0.001471 | 5.44 |  |  | download: the publisher URL returns 404 |
| bench_dev1a_09 | vic:victorian-state-schools-voluntary-parent-payments | xls | partial_config | 10 | 0.005704 | 32.16 |  |  | harness_defect: a partial_config with ZERO mapped fields was accepted |
| bench_dev1a_10 | sa:river-murray-protection-area | json | no_business_entities | 7 | 0.002292 | 9.68 |  | finish: finish refused: no_business_entities needs a successful read_t | non_business (plausibly correct) |
| bench_dev1a_11 | datagovau:vostronet-australia-pty-ltd-anticipatory-notice-augustine-he | zip | could_not_read | 15 | 0.005055 | 26.29 |  | finish: finish refused: could_not_read needs two reader attempts that  | reader_gap: a zip of a MapInfo TAB geodataset (not tabular) |
