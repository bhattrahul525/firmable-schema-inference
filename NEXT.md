# What I'd do next (running list, feeds WRITEUP.md §6)

- **Part 1 triage:** score the *primary* name column, not the best column; add a person-name
  detector ("SURNAME, First" share) and a government-name penalty (School, Council, Department,
  Health Service). These would have caught 4 of the 5 measured false positives.
- **Part 1 triage:** detect multi-row headers properly; content-hash de-duplication so two
  views of the same data (NSW liquor premises vs "Find by LIA Band") collapse.
- **Part 1 triage:** probe ZIP/XML (ABN Bulk Extract is the best source in the catalogue and we
  cannot look inside it).
