Passes a, b: Haiku, OLD outcome definition. c (Haiku), s (Sonnet): new outcome definition. d (Haiku), t (Sonnet): + critic rules, severity guidance, confidence-only-down, identifier warning. e (Haiku): d + rule 18 amended to section d (individuals with their own valid ABN may be entities), name rule in rule 5, placeholder-header warning. N = has a name, I = has an identifier.

## Outcome per dataset across passes: outcome (mapped fields) N=has a name, I=has an identifier

| dataset | fmt | a | b | c | d | e | s | t |
|---|---|---|---|---|---|---|---|---|
| datagovau:asic-smsf | csv | validated_config (7) NI | validated_config (7) NI | validated_config (7) NI | no_business_entities (0) -- | validated_config (7) NI | validated_config (7) NI | validated_config (7) NI |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | xlsx | partial_config (2) NI | partial_config (2) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI |
| vic:victorian-government-schools-abns | xlsx | partial_config (1) N- | validated_config (1) -I | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI |
| qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config (3) -I | partial_config (2) -I | validated_config (2) -I | validated_config (3) NI | validated_config (3) NI | validated_config (3) NI | validated_config (3) NI |
| datagovau:avib-prrz | csv | validated_config (3) NI | validated_config (2) NI | validated_config (2) NI | validated_config (3) NI | validated_config (2) NI | validated_config (2) NI | validated_config (2) NI |
| datagovau:intellectual-property-longitudinal-research-data-2 | csv | partial_config (4) -I | partial_config (4) -I | validated_config (4) -I | validated_config (4) -I | validated_config (4) -I | validated_config (5) NI | validated_config (4) N- |
| sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- |
| vic:contract-expenditure-under-strategic-sourcing-management | xlsx | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- |
| vic:victorian-state-schools-voluntary-parent-payments | xls | partial_config (0) -- | validated_config (1) N- | no_business_entities (0) -- | validated_config (1) N- | validated_config (1) N- | validated_config (1) N- | validated_config (1) N- |
| sa:river-murray-protection-area | json | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- | no_business_entities (0) -- |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | zip | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- | could_not_read (0) -- |

## Validated configs: name and identifier coverage

| pass | validated | name + identifier | name only | identifier only | neither |
|---|---|---|---|---|---|
| a | 3 | 2 | 0 | 1 | 0 |
| b | 4 | 2 | 1 | 1 | 0 |
| c | 6 | 4 | 0 | 2 | 0 |
| d | 6 | 4 | 1 | 1 | 0 |
| e | 7 | 5 | 1 | 1 | 0 |
| s | 7 | 6 | 1 | 0 | 0 |
| t | 7 | 5 | 2 | 0 | 0 |

## Did the model agree with itself? passes c-d (outcome, then mapped fields)

| dataset | outcome | same outcome | same fields | differences |
|---|---|---|---|---|
| datagovau:asic-smsf | validated_config / no_business_entities | NO | NO | only in first: address.locality<-SMSF_LOCALITY, address.postcode<-SMSF_POST_CODE, address.state<-SMSF_STATE, entity.abn<-SMSF_PERSON_ABN, entity.date_registered<-SMSF_REG_DT, entity.legal_name<-SMSF_N |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | validated_config / validated_config | yes | yes |  |
| vic:victorian-government-schools-abns | validated_config / validated_config | yes | yes |  |
| qld:chhhs-contracts-disclosure-register-2020-21 | validated_config / validated_config | yes | NO | only in first: address.full<-Supplier address Parties/address not assessed, entity.abn<-Supplier ABN Parties/identifier/uri not assessed; only in second: address.full<-Supplier address, entity.abn<-Su |
| datagovau:avib-prrz | validated_config / validated_config | yes | NO | ; only in second: entity.entity_type<-Licensee Name |
| datagovau:intellectual-property-longitudinal-research-data-2 | validated_config / validated_config | yes | yes |  |
| sa:south-australian-signalised-intersections-and-crossings | no_business_entities / no_business_entities | yes | yes |  |
| vic:contract-expenditure-under-strategic-sourcing-management | could_not_read / could_not_read | yes | yes |  |
| vic:victorian-state-schools-voluntary-parent-payments | no_business_entities / validated_config | NO | NO | ; only in second: entity.legal_name<-School Name |
| sa:river-murray-protection-area | no_business_entities / no_business_entities | yes | yes |  |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | could_not_read / could_not_read | yes | yes |  |

Same outcome on 9 of 11; same outcome AND same fields on 7 of 11.

## Did the model agree with itself? passes d-e (outcome, then mapped fields)

| dataset | outcome | same outcome | same fields | differences |
|---|---|---|---|---|
| datagovau:asic-smsf | no_business_entities / validated_config | NO | NO | ; only in second: address.locality<-SMSF_LOCALITY, address.postcode<-SMSF_POST_CODE, address.state<-SMSF_STATE, entity.abn<-SMSF_PERSON_ABN, entity.date_registered<-SMSF_REG_DT, entity.legal_name<-SMS |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | validated_config / validated_config | yes | NO | only in first: entity.legal_name<-Name; only in second: entity.trading_name<-Name |
| vic:victorian-government-schools-abns | validated_config / validated_config | yes | yes |  |
| qld:chhhs-contracts-disclosure-register-2020-21 | validated_config / validated_config | yes | NO | only in first: address.full<-Supplier address, entity.abn<-Supplier ABN, entity.legal_name<-Supplier name; only in second: address.full<-Supplier address Parties/address not assessed, entity.abn<-Supp |
| datagovau:avib-prrz | validated_config / validated_config | yes | NO | only in first: entity.entity_type<-Licensee Name |
| datagovau:intellectual-property-longitudinal-research-data-2 | validated_config / validated_config | yes | yes |  |
| sa:south-australian-signalised-intersections-and-crossings | no_business_entities / no_business_entities | yes | yes |  |
| vic:contract-expenditure-under-strategic-sourcing-management | could_not_read / could_not_read | yes | yes |  |
| vic:victorian-state-schools-voluntary-parent-payments | validated_config / validated_config | yes | NO | only in first: entity.legal_name<-School Name; only in second: entity.trading_name<-School Name |
| sa:river-murray-protection-area | no_business_entities / no_business_entities | yes | yes |  |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | could_not_read / could_not_read | yes | yes |  |

Same outcome on 10 of 11; same outcome AND same fields on 6 of 11.

## Did the model agree with itself? passes c-e (outcome, then mapped fields)

| dataset | outcome | same outcome | same fields | differences |
|---|---|---|---|---|
| datagovau:asic-smsf | validated_config / validated_config | yes | yes |  |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | validated_config / validated_config | yes | NO | only in first: entity.legal_name<-Name; only in second: entity.trading_name<-Name |
| vic:victorian-government-schools-abns | validated_config / validated_config | yes | yes |  |
| qld:chhhs-contracts-disclosure-register-2020-21 | validated_config / validated_config | yes | NO | ; only in second: entity.legal_name<-Supplier name Parties additionalidentifiers/id not assessed |
| datagovau:avib-prrz | validated_config / validated_config | yes | yes |  |
| datagovau:intellectual-property-longitudinal-research-data-2 | validated_config / validated_config | yes | yes |  |
| sa:south-australian-signalised-intersections-and-crossings | no_business_entities / no_business_entities | yes | yes |  |
| vic:contract-expenditure-under-strategic-sourcing-management | could_not_read / could_not_read | yes | yes |  |
| vic:victorian-state-schools-voluntary-parent-payments | no_business_entities / validated_config | NO | NO | ; only in second: entity.trading_name<-School Name |
| sa:river-murray-protection-area | no_business_entities / no_business_entities | yes | yes |  |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | could_not_read / could_not_read | yes | yes |  |

Same outcome on 10 of 11; same outcome AND same fields on 8 of 11.

## Did the model agree with itself? passes s-t (outcome, then mapped fields)

| dataset | outcome | same outcome | same fields | differences |
|---|---|---|---|---|
| datagovau:asic-smsf | validated_config / validated_config | yes | yes |  |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | validated_config / validated_config | yes | yes |  |
| vic:victorian-government-schools-abns | validated_config / validated_config | yes | yes |  |
| qld:chhhs-contracts-disclosure-register-2020-21 | validated_config / validated_config | yes | NO | only in first: address.full<-Supplier address Parties/address, entity.abn<-Supplier ABN Parties/identifier/uri, entity.legal_name<-Supplier name Parties additionalidentifiers/id; only in second: addre |
| datagovau:avib-prrz | validated_config / validated_config | yes | yes |  |
| datagovau:intellectual-property-longitudinal-research-data-2 | validated_config / validated_config | yes | NO | only in first: entity.abn<-lord_party_id |
| sa:south-australian-signalised-intersections-and-crossings | no_business_entities / no_business_entities | yes | yes |  |
| vic:contract-expenditure-under-strategic-sourcing-management | could_not_read / could_not_read | yes | yes |  |
| vic:victorian-state-schools-voluntary-parent-payments | validated_config / validated_config | yes | NO | only in first: entity.legal_name<-School Name; only in second: entity.legal_name<-_blank_1 |
| sa:river-murray-protection-area | no_business_entities / no_business_entities | yes | yes |  |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | could_not_read / could_not_read | yes | yes |  |

Same outcome on 11 of 11; same outcome AND same fields on 8 of 11.

## Per pass

| pass | model | runs | outcomes | cost | mean cost | mean agent s | mean turns |
|---|---|---|---|---|---|---|---|
| a | claude-haiku-5-5 | 11 | {'validated_config': 3, 'partial_config': 4, 'no_business_entities': 2, 'could_not_read': 2} | $0.0838 | $0.0076 | 47.5 | 10.5 |
| b | claude-haiku-5-5 | 11 | {'validated_config': 4, 'partial_config': 3, 'no_business_entities': 2, 'could_not_read': 2} | $0.0846 | $0.0077 | 46.9 | 10.6 |
| c | claude-haiku-5-5 | 11 | {'validated_config': 6, 'no_business_entities': 3, 'could_not_read': 2} | $0.0752 | $0.0068 | 38.2 | 8.9 |
| d | claude-haiku-5-5 | 11 | {'no_business_entities': 3, 'validated_config': 6, 'could_not_read': 2} | $0.0695 | $0.0063 | 37.0 | 9.4 |
| e | claude-haiku-5-5 | 11 | {'validated_config': 7, 'no_business_entities': 2, 'could_not_read': 2} | $0.0738 | $0.0067 | 40.2 | 9.5 |
| s | claude-sonnet-5-5 | 11 | {'validated_config': 7, 'no_business_entities': 2, 'could_not_read': 2} | $1.067 | $0.097 | 36.9 | 7.7 |
| t | claude-sonnet-5-5 | 11 | {'validated_config': 7, 'no_business_entities': 2, 'could_not_read': 2} | $0.845 | $0.0768 | 26.1 | 6.6 |

## Per model

| model | passes | runs | cost | mean cost per run | mean agent s | mean turns |
|---|---|---|---|---|---|---|
| claude-haiku-5-5 | a,b,c,d,e | 55 | $0.3869 | $0.007 | 42.0 | 9.8 |
| claude-sonnet-5-5 | s,t | 22 | $1.912 | $0.0869 | 31.5 | 7.2 |
