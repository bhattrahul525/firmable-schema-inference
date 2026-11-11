# What I'd do next (running list, feeds WRITEUP.md §6)

- **Part 1 triage:** score the *primary* name column, not the best column; add a person-name
  detector ("SURNAME, First" share) and a government-name penalty (School, Council, Department,
  Health Service). These would have caught 4 of the 5 measured false positives.
- **Part 1 triage:** detect multi-row headers properly; content-hash de-duplication so two
  views of the same data (NSW liquor premises vs "Find by LIA Band") collapse.
- **Part 1 triage:** probe ZIP/XML (ABN Bulk Extract is the best source in the catalogue and we
  cannot look inside it).

## Part 2 ideas (for write-up "next 3 weeks")
- Constant-value / jurisdiction transform (VIC `address.state`); the agent already reports it as `needs_transform`.
- Licence-scoped observations (status, start/end) instead of dropping or attaching them to entity claims.
- Reuse approved configs as few-shot examples for new sources (needs ~20+ approved configs first).
- Cheap model first, escalate to a stronger one only when validation fails.
- Re-run both proposals at higher effort for fields the human marks wrong; measure agent accuracy across more reviews.

## Part 3 ideas
- Rarity-weighted name similarity (IDF over tokens) so "Australia"/"Group" do not carry a match.
- Hand-check a sample of the REFUSED pairs to measure what the names-conflict rule throws away.
- LLM adjudicator for the borderline band only (ABN equal, names differ) with the evidence packet; measure vs hand labels.
- Re-score demo: `rescore` from stored features when the matcher changes (m1.1 variant), to show the "change" answer in practice.
- QBCC person-under-company-ABN pattern: model as a `nominee_of` relationship instead of a conflict.
