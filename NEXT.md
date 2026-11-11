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
