# Step 8 hand check: results

Rows labelled: 18 of 18. Blank or invalid labels: 0.
Precision = Y / (Y + N); U is excluded from precision but shown. 95% Wilson interval. Not tuned on: no rule or threshold changes from these results.

## Per stratum

| stratum | rows | Y | N | U | precision | 95% CI |
|---|---|---|---|---|---|---|
| no_abn | 4 | 2 | 2 | 0 | 0.5 | (0.15, 0.85) |
| register_bridged_accepted | 4 | 4 | 0 | 0 | 1.0 | (0.51, 1) |
| register_bridged_loose | 6 | 2 | 3 | 1 | 0.4 | (0.118, 0.769) |
| sole_trader | 2 | 2 | 0 | 0 | 1.0 | (0.342, 1) |
| t1r | 2 | 2 | 0 | 0 | 1.0 | (0.342, 1) |

## Per tier

| tier | rows | Y | N | U | precision | 95% CI |
|---|---|---|---|---|---|---|
| T1_abn_equal | 1 | 1 | 0 | 0 | 1.0 | (0.207, 1) |
| T1_register_abn | 5 | 5 | 0 | 0 | 1.0 | (0.566, 1) |
| T1r_abn_equal_bn_name | 2 | 2 | 0 | 0 | 1.0 | (0.342, 1) |
| T3_register_name | 10 | 4 | 5 | 1 | 0.444 | (0.189, 0.733) |

## Per band

| band | rows | Y | N | U | precision | 95% CI |
|---|---|---|---|---|---|---|
| accepted | 8 | 8 | 0 | 0 | 1.0 | (0.676, 1) |
| loose | 10 | 4 | 5 | 1 | 0.444 | (0.189, 0.733) |

## Caveats

- Labels are non-independent: ABN Lookup shows ASIC business names and the registers are matcher features.
- Samples are small (n per stratum); intervals are wide.
- Some labels were model-assisted (notes marked); the rest are the owner's.
