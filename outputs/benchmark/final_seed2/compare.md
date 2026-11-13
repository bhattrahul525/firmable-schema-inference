

## Outcome per dataset across passes: outcome (mapped fields) N=has a name, I=has an identifier

| dataset | fmt | h | s |
|---|---|---|---|
| datagovau:asic-smsf | csv | validated_config (7) NI | validated_config (7) NI |
| sa:sacommunitydirectory | csv | validated_config (7) NI | partial_config (6) NI |
| qld:queensland-government-arrangements-directory-supplier-pr | csv | validated_config (1) N- | validated_config (1) -I |
| qld:dcdss-contract-disclosure-1-july-2020-31-december-2020 | csv | could_not_read (0) -- | could_not_read (0) -- |
| qld:consultancies-and-contractors-office-of-the-information- | csv | validated_config (3) NI | validated_config (3) NI |
| datagovau:asic-banned-disqualified-org | csv | validated_config (2) NI | validated_config (2) NI |
| qld:temporary-emissions-licences-tel | xlsx | validated_config (1) N- | validated_config (1) N- |
| sa:ict-contract-usage-guidelines | csv | validated_config (1) N- | validated_config (1) N- |
| sa:2020-21-number-of-food-businesses-in-sa-per-risk-classifi | csv | no_business_entities (0) -- | no_business_entities (0) -- |
| sa:annual-report-cbs | xlsx | no_business_entities (0) -- | no_business_entities (0) -- |
| vic:taxi-industry-statistics | xls | no_business_entities (0) -- | no_business_entities (0) -- |
| sa:corrosion-environment-areas | json | no_business_entities (0) -- | no_business_entities (0) -- |
| nsw:water-modelling-modelled-data-annual-permitted-take-apt- | zip | no_business_entities (0) -- | no_business_entities (0) -- |
| datagovau:data-collected-on-voyages-of-australian-antarctic- | no-tabular | could_not_read (0) -- | could_not_read (0) -- |
| vic:summary-residential-community-emissions | csv | no_business_entities (0) -- | no_business_entities (0) -- |

## Validated configs: name and identifier coverage

| pass | validated | name + identifier | name only | identifier only | neither | identifier unverified |
|---|---|---|---|---|---|---|
| h | 7 | 4 | 3 | 0 | 0 | 1 |
| s | 6 | 3 | 2 | 1 | 0 | 1 |

## Per pass

| pass | model | runs | outcomes | cost | mean cost | mean agent s | mean turns |
|---|---|---|---|---|---|---|---|
| h | claude-haiku-5-5 | 15 | {'validated_config': 7, 'could_not_read': 2, 'no_business_entities': 6} | $0.0918 | $0.0061 | 28.6 | 8.3 |
| s | claude-sonnet-5-5 | 15 | {'validated_config': 6, 'partial_config': 1, 'could_not_read': 2, 'no_business_entities': 6} | $1.1403 | $0.076 | 19.4 | 6.3 |

## Per model

| model | passes | runs | cost | mean cost per run | mean agent s | mean turns |
|---|---|---|---|---|---|---|
| claude-haiku-5-5 | h | 15 | $0.0918 | $0.0061 | 28.6 | 8.3 |
| claude-sonnet-5-5 | s | 15 | $1.1403 | $0.076 | 19.4 | 6.3 |
