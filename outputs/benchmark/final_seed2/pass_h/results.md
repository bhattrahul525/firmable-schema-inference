| source_id | dataset_id | format_class | outcome | turns | cost_usd | agent_seconds | mapped_fields | refusals | cause |
|---|---|---|---|---|---|---|---|---|---|
| bench_fin2h_01 | datagovau:asic-smsf | csv | validated_config | 9 | 0.009844 | 44.58 | entity.abn<-SMSF_PERSON_ABN; entity.legal_name<-SMSF_NAME; entity.stat |  |  |
| bench_fin2h_02 | sa:sacommunitydirectory | csv | validated_config | 12 | 0.013364 | 60.3 | entity.trading_name<-Org_name; entity.abn<-Organisati_ABN; entity.webs |  |  |
| bench_fin2h_03 | qld:queensland-government-arrangements-directory-supplier-procurement- | csv | validated_config | 12 | 0.010456 | 57.04 | entity.legal_name<-Suppliers | finish: finish refused: validated_config needs at least one mapped fie |  |
| bench_fin2h_04 | qld:dcdss-contract-disclosure-1-july-2020-31-december-2020 | csv | could_not_read | 4 | 0.001813 | 5.08 |  |  |  |
| bench_fin2h_05 | qld:consultancies-and-contractors-office-of-the-information-commission | csv | validated_config | 10 | 0.007202 | 34.61 | entity.legal_name<-Supplier name; entity.abn<-Supplier ABN; address.fu |  |  |
| bench_fin2h_06 | datagovau:asic-banned-disqualified-org | csv | validated_config | 11 | 0.00855 | 41.31 | entity.legal_name<-BD_ORG_NAME; entity.acn<-BD_ORG_ACN |  |  |
| bench_fin2h_07 | qld:temporary-emissions-licences-tel | xlsx | validated_config | 15 | 0.013505 | 71.94 | entity.legal_name<-TEL Holder(s) | finish: finish refused: validated_config needs at least one mapped fie |  |
| bench_fin2h_08 | sa:ict-contract-usage-guidelines | csv | validated_config | 9 | 0.008323 | 46.86 | entity.trading_name<-Contract |  |  |
| bench_fin2h_09 | sa:2020-21-number-of-food-businesses-in-sa-per-risk-classification | csv | no_business_entities | 7 | 0.002711 | 9.99 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_fin2h_10 | sa:annual-report-cbs | xlsx | no_business_entities | 7 | 0.00296 | 10.7 |  | finish: finish refused: no_business_entities needs a successful read_t |  |
| bench_fin2h_11 | vic:taxi-industry-statistics | xls | no_business_entities | 7 | 0.002778 | 9.82 |  |  |  |
| bench_fin2h_12 | sa:corrosion-environment-areas | json | no_business_entities | 6 | 0.002647 | 9.74 |  |  |  |
| bench_fin2h_13 | nsw:water-modelling-modelled-data-annual-permitted-take-apt-murrumbidg | zip | no_business_entities | 6 | 0.002655 | 9.85 |  |  |  |
| bench_fin2h_14 | datagovau:data-collected-on-voyages-of-australian-antarctic-program-ve | no-tabular | could_not_read | 4 | 0.002062 | 8.71 |  |  |  |
| bench_fin2h_15 | vic:summary-residential-community-emissions | csv | no_business_entities | 6 | 0.002942 | 9.09 |  |  |  |
