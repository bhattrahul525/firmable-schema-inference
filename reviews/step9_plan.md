# Step 9 plan: final benchmark (seed 2), run once

## Draw and models
Seed 2, `draw.py --final`, written once and never adjusted: 8 shortlist (ranks 7-50, rank 38 excluded) +
7 pool (one per format class csv/xlsx/xls/json/zip, one from the no-tabular group, and a SECOND csv: a different
dataset in a different publisher-and-title family from the first csv) + 1 injection case = 16 datasets.
Haiku and Sonnet each run the same draw once, at the same recorded commit.

## Frozen conditions
Tree must be clean and the commit hash recorded with the results. The owner commits after the final-review fixes; the chain resumes at stage 3. No code, prompt or config edits between
the draw and the end of both runs. A harness crash (infrastructure, not an outcome) may be re-run once and
is documented. Outcomes are never re-run.

## Cost
Haiku about $0.15; Sonnet about $1.5 (dev: $0.86 for 11 datasets, plus injection). Per-run limit $0.50 (same as the dev passes; the
system prompt tells the model "$1.00" whatever the cap is), session limit $3. Round-2 spend so far about $4.2 of the $10 target.

## Measures
Automatic, from traces: outcome counts, could_not_read by reason, has_name / has_identifier coverage, cost,
tool calls, wall-clock, W/P/G counts, Haiku-vs-Sonnet agreement, injection verdict (canary checks).
Human, later: validated with 0 wrong fields on review, key field missed, non-business correctly declared
(spot check). The run only produces the review sheets. Published with the dev rate beside it.
Not a pass/fail gate: results are reported as they come.

## Demo model rule (written before the run)
Haiku is the demo default, unless Sonnet validates at least 2 more datasets than Haiku, or Haiku fails the
injection case and Sonnet passes it. Decide from the final numbers, not from impressions.