| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_fin2s_01 | datagovau:asic-smsf | csv | validated_config | 8 | 0.130863 | 38.87 | entity.legal_name<-SMSF_NAME; entity.abn<-SMSF_PERSON_ABN; entity.stat |  |  |
| bench_fin2s_02 | sa:sacommunitydirectory | csv | partial_config | 8 | 0.167645 | 46.56 | entity.legal_name<-Org_name; entity.abn<-Organisati_ABN; entity.websit | finish: finish refused: validate fails on this config (hard failures:  |  |
| bench_fin2s_03 | qld:queensland-government-arrangements-directory-supplier-procurement- | csv | validated_config | 8 | 0.149416 | 45.39 | entity.abn<-Suppliers | finish: finish refused: validated_config needs at least one mapped fie |  |
| bench_fin2s_04 | qld:dcdss-contract-disclosure-1-july-2020-31-december-2020 | csv | could_not_read | 4 | 0.031242 | 4.67 |  |  |  |
| bench_fin2s_05 | qld:consultancies-and-contractors-office-of-the-information-commission | csv | validated_config | 6 | 0.082591 | 22.25 | entity.legal_name<-Supplier name; entity.abn<-Supplier ABN; address.fu |  |  |
| bench_fin2s_06 | datagovau:asic-banned-disqualified-org | csv | validated_config | 7 | 0.091353 | 21.62 | entity.acn<-BD_ORG_ACN; entity.legal_name<-BD_ORG_NAME |  |  |
| bench_fin2s_07 | qld:temporary-emissions-licences-tel | xlsx | validated_config | 8 | 0.085698 | 24.59 | entity.legal_name<-TEL Holder(s) |  |  |
| bench_fin2s_08 | sa:ict-contract-usage-guidelines | csv | validated_config | 8 | 0.108785 | 35.34 | entity.trading_name<-Contract | finish: finish refused: validated_config needs at least one mapped fie |  |
| bench_fin2s_09 | sa:2020-21-number-of-food-businesses-in-sa-per-risk-classification | csv | no_business_entities | 5 | 0.037884 | 5.99 |  |  |  |
| bench_fin2s_10 | sa:annual-report-cbs | xlsx | no_business_entities | 5 | 0.039274 | 5.99 |  |  |  |
| bench_fin2s_11 | vic:taxi-industry-statistics | xls | no_business_entities | 6 | 0.046826 | 8.58 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_fin2s_12 | sa:corrosion-environment-areas | json | no_business_entities | 7 | 0.048261 | 11.83 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_fin2s_13 | nsw:water-modelling-modelled-data-annual-permitted-take-apt-murrumbidg | zip | no_business_entities | 6 | 0.044151 | 7.77 |  |  |  |
| bench_fin2s_14 | datagovau:data-collected-on-voyages-of-australian-antarctic-program-ve | no-tabular | could_not_read | 4 | 0.034309 | 4.76 |  |  |  |
| bench_fin2s_15 | vic:summary-residential-community-emissions | csv | no_business_entities | 5 | 0.041958 | 6.87 |  |  |  |
