Passes a and b ran under the OLD outcome definition (partial_config could be declared by the agent; a = before the zero-field fix, b = after). Passes c (Haiku) and s (Sonnet) ran under the NEW definition (validated_config = the agent's own finish was accepted; partial_config = harness-ended with a passing field), with the could_not_read evidence rule and resource switching. Counts in brackets are mapped fields. a, b, c: claude-haiku-5-5; s: claude-sonnet-5-5.

## Outcome per dataset (and mapped-field count) across passes

| dataset | fmt | a | b | c | s |
|---|---|---|---|---|---|
| datagovau:asic-smsf | csv | validated_config (7) | validated_config (7) | validated_config (7) | validated_config (7) |
| datagovau:junior-minerals-exploration-incentive-credit-alloc | xlsx | partial_config (2) | partial_config (2) | validated_config (2) | validated_config (2) |
| vic:victorian-government-schools-abns | xlsx | partial_config (1) | validated_config (1) | validated_config (2) | validated_config (2) |
| qld:chhhs-contracts-disclosure-register-2020-21 | csv | validated_config (3) | partial_config (2) | validated_config (2) | validated_config (3) |
| datagovau:avib-prrz | csv | validated_config (3) | validated_config (2) | validated_config (2) | validated_config (2) |
| datagovau:intellectual-property-longitudinal-research-data-2 | csv | partial_config (4) | partial_config (4) | validated_config (4) | validated_config (5) |
| sa:south-australian-signalised-intersections-and-crossings | csv | no_business_entities (0) | no_business_entities (0) | no_business_entities (0) | no_business_entities (0) |
| vic:contract-expenditure-under-strategic-sourcing-management | xlsx | could_not_read (0) | could_not_read (0) | could_not_read (0) | could_not_read (0) |
| vic:victorian-state-schools-voluntary-parent-payments | xls | partial_config (0) | validated_config (1) | no_business_entities (0) | validated_config (1) |
| sa:river-murray-protection-area | json | no_business_entities (0) | no_business_entities (0) | no_business_entities (0) | no_business_entities (0) |
| datagovau:vostronet-australia-pty-ltd-anticipatory-notice-au | zip | could_not_read (0) | could_not_read (0) | could_not_read (0) | could_not_read (0) |

## Per pass

| pass | model | runs | outcomes | cost | mean cost | mean agent s | mean turns |
|---|---|---|---|---|---|---|---|
| a | claude-haiku-5-5 | 11 | {'validated_config': 3, 'partial_config': 4, 'no_business_entities': 2, 'could_not_read': 2} | $0.0838 | $0.0076 | 47.5 | 10.5 |
| b | claude-haiku-5-5 | 11 | {'validated_config': 4, 'partial_config': 3, 'no_business_entities': 2, 'could_not_read': 2} | $0.0846 | $0.0077 | 46.9 | 10.6 |
| c | claude-haiku-5-5 | 11 | {'validated_config': 6, 'no_business_entities': 3, 'could_not_read': 2} | $0.0752 | $0.0068 | 38.2 | 8.9 |
| s | claude-sonnet-5-5 | 11 | {'validated_config': 7, 'no_business_entities': 2, 'could_not_read': 2} | $1.067 | $0.097 | 36.9 | 7.7 |

## Per model

| model | passes | runs | cost | mean cost per run | mean agent s | mean turns |
|---|---|---|---|---|---|---|
| claude-haiku-5-5 | a,b,c | 33 | $0.2436 | $0.0074 | 44.2 | 10.0 |
| claude-sonnet-5-5 | s | 11 | $1.067 | $0.097 | 36.9 | 7.7 |
