# Step 3b plan: layout, held-out split, sparse evidence, valid_from, placeholders, name rules, trace

Status: PLAN ONLY. Nothing here is built. No code, prompt, config or other file was changed to write it.
Written 2026-11-13 against ARCHITECTURE.md v2.11 (414 lines) and 464 passing tests.

Every proposed prompt or rule wording below is generic. Dataset, column and value names appear only under "Evidence".

## Evidence used (all measured read-only)

| # | Fact | Where it comes from |
|---|---|---|
| E1 | One dev-draw file has a title on raw row 1, a second title on row 2, the real header on row 3, two label rows on rows 4 and 5, and 49 data rows from row 6. | `data/raw/sources/bench_dev1t_04/` |
| E2 | The reader has three layout numbers only: `skip_rows`, `header_rows`, `skip_footer_rows`. After `skip_rows` it takes `header_rows` consecutive rows as names and everything after is data. | `_layout`, `_table_from_matrix` in `src/engine/readers.py` |
| E3 | In that run the three `read_table` calls gave: names from the title row plus 22 placeholders; then `col_N` with the label rows as data (`skip_rows=3` skipped the real header, an off-by-one); then `col_N` from row 6. The agent finished with `col_N` names. | `logs/agent_runs/bench_dev1t_04/trace.jsonl` |
| E4 | On the first read, raw rows 2 and 3 (second title, real header) were data rows and both were in the held-out set, so the agent was never shown the column names. The file has 53 such rows; half of a small file is held out. | `split.json` of that run, fingerprints recomputed |
| E5 | Over the 42 dev-draw runs (passes c, d, e, s, t) that read a non-JSON table: in 26 runs at least one of the first 10 raw rows was held out (76 rows in all); in 11 runs one of raw rows 1 to 3 was. | recomputed per run from `split.json` |
| E6 | `sniff` shows the first 12 raw lines of a text file whatever the split says. In 10 of the 17 runs that called `sniff`, some of the first 10 raw rows were later held out: rows the agent had seen were then used as "unseen" test rows. | same computation, tool sequences |
| E7 | The prompt already suggests `fetch -> sniff -> ...` and the fetch result ends "Next: sniff". Haiku called `sniff` before its first `read_table` in 18 of 29 runs. Sonnet did in 0 of 18. | tool sequences, passes c, d, e, s, t |
| E8 | The identifier field of the E1 run has one value in 49 rows; all 24 held-out rows are blank for it. Validate reported parse rate `null`, zero failures. Code capped `field_confidence` at 0.5 but nothing says "unverified"; the benchmark shows `has_identifier = True`. | run_end config of `bench_dev1t_04` |
| E9 | `valid_from` and `valid_to` were set from two date columns in that run. The critic's config summary has `reader`, `record_id`, `observed_at`, `fields`, `unmapped` and nothing else, so the critic reported one of those columns as "not accounted for". One of the seven values in that column is a stray punctuation mark; the engine drops a failed `valid_from` silently (`valid_from, _ = per_record("valid_from")`). | `critique_config`, `run_rows`, trace |
| E10 | The round-2 packet has no table of reader options, `observed_at`, `valid_from` or `valid_to`. The round-1 packet printed all of them. | packet of `bench_dev1t_04`; `src/part2_agent/packet.py` |
| E11 | Two of the six approved round-1 configs set `valid_from` / `valid_to`: one from a licence start and end date, one from a contract commencement and final expiry date. | `configs/asic_credit_licensee.yaml`, `configs/wa_tenders_awards_2023_24.yaml` |
| E12 | Nothing in Part 3 or Part 4 reads `valid_from` or `valid_to`. | grep over `src/part3_resolve`, `src/part4_profiles` |
| E13 | Part 4 treats a claim with `field_confidence` below 0.6 as low trust: it is used only if no claim at or above 0.6 exists. | `LOW_TRUST = 0.6` in `src/part4_profiles/build.py` |
| E14 | In pass e a file of individuals on a regulator's register (16% of rows carry an ABN) mapped its unlabelled name column to `legal_name` at 0.7, citing rule 4. The critic rated it advisory and suggested `trading_name` at 0.6 or lower under rule 5. No code limits `mapping_confidence` by how a column is labelled. | `logs/agent_runs/bench_dev1e_01/trace.jsonl` |
| E15 | The trace does record every content block. In 463 model turns: Haiku has a thinking block in 151 of 305 turns, Sonnet in 29 of 158; every one has empty text and a signature. Text blocks: 9 (Haiku), 20 (Sonnet). `llm.chat` sends effort `low` and no `thinking` parameter. | traces of passes c, d, e, s, t; `src/llm.py` |
| E16 | Per the API reference bundled with the claude-api skill (cached 2026-11-03): on both models thinking is adaptive and on by default; `display` defaults to `"omitted"` (empty text); `display: "summarized"` returns a readable summary; display changes visibility only, thinking is billed the same; thinking blocks must be passed back unchanged; a between-tool progress display (`"updates"`) is a beta listed for Sonnet 5.5, not for Haiku 5.5. | skill text; to be confirmed by one live call before building on it |
| E17 | Trace files today: median 23 KB (Sonnet pass t) to 41 KB (Haiku pass e), largest 123 KB. | file sizes |

## A. Reader layout: "names from row N, then drop the next M rows"

**Problem.** E1, E2, E3. Today the file can be read three ways, none right: correct names with two junk data rows; three header rows merged into one long composite name per column; or generated `col_N` names.

**Options**
1. `skip_rows_after_header: M` (a count, default 0). Order becomes: skip `skip_rows` rows, take `header_rows` rows as names, drop the next M rows, then data, then `skip_footer_rows`.
2. `data_start_row: R` (an absolute, 1-based raw row). Rows between the header block and row R are dropped.
3. No new reader option: keep `header_rows=n` merging, or let the agent write column labels (item E).

**Against the leaning (one new option, existing ones unchanged).**
- A new option is a third way to spell the same file. Pass a merged the three header rows; pass t used `col_N`. The self-agreement measure compares `canonical<-source` strings, so two acceptable layouts already count as disagreement, and a third adds another.
- The run's actual error was an off-by-one on a count the reader already had (E3), made by an agent that never saw the rows it was counting (E4). A new option does not fix that. Without item B this option would not have been used correctly.
- Option 3 costs nothing in the reader and the merged names are not wrong data, only ugly.

**Recommendation: option 1, built after item B.** Names taken from the file are the only names code can vouch for; composite or generated names make the packet harder to review and defeat item F's label check.

Why the count and not the absolute row:
- Every existing layout option is a count. A count has one invalid combination; an absolute row has a family of them (R at or before the header, or redundant with `skip_rows` when there is no header).
- The off-by-one risk is handled by output, not by the option's form: `read_table` (item B) shows numbered raw rows, and its result states in words written by code which row gave the names, which rows were dropped and where data starts.

**Meaning, exactly**
- Applies to the delimited, xlsx and xls readers, including archive members. Refused for json.
- Counts raw rows the same way `skip_rows` does (blank lines count). `skip_footer_rows` keeps its own rule.
- Refused with `header_rows=0` ("use skip_rows"), so there stays one way to say it.
- Accepted with the round-1 `header_row` option. Default 0, so the seven round-1 files read identically (parity test unchanged).
- Dropped rows are not data rows: not counted, not fingerprinted, never candidates for the held-out set. If an earlier, wrong parse put their fingerprints in the split, they now match nothing; with item B that can only happen below the protected rows, and the existing "fewer than half found, re-split" rule still covers the gross case.
- The pipeline's `FORMATS` enum is not touched: it lists formats, not options, and the pipeline's inspect step does not offer the option.
- The `read_table` tool schema gains one property, so the schema hash in the trace header changes and existing traces cannot be resumed. All of them are finished.

**Cost of being wrong.** The name is sticky: reader options live in approved configs. A wrong count drops a data row silently or keeps a label row as data, and a label row becomes junk observations. The echo line, the numbered raw rows and item E's warning are the guards.

**Tests.** A synthetic fixture (header on row 3, two label rows): names, row count, first data row; default 0 parity on existing fixtures; negative, boolean and beyond-end values; refused with `header_rows=0` and with json; xlsx, xls and zip member; with a footer; with the round-1 `header_row`; fingerprints of data rows equal with and without the option; the engine extracts with a config that uses it; validate uses the config's own reader. Mutation targets: off-by-one in the drop, option ignored, applied before the header.

**ARCHITECTURE.md.** Section c reader table (three rows), `read_table` row in section b, change log.

## B. The held-out split must never hide the layout

**Problem.** E4, E5, E6, E7. The split is made on the first read, before the layout is known, so rows that are really titles or headers can be held out and hidden. Separately, `sniff` already shows rows that are later treated as unseen.

**Options**
1. Never hold out the first K raw rows of the file.
2. Make the split only after the agent confirms the layout.
3. Make the split at the first `validate` call.
Plus two possible gates: require a raw-lines view before `read_table` may set `header_rows`; refuse `finish` if no tool call ever returned the first raw lines.

**Leakage each option creates**
- Option 1: none. It removes the existing leak in E6 if K is at least the 12 lines `sniff` shows. Its cost is that the held-out set is no longer a uniform sample: it never contains the top K rows.
- Option 2: everything shown before confirmation must be remembered and kept out of the held-out candidates, or it leaks. It also needs a confirmation step from an agent that skips suggested steps (E7); if it never confirms, this becomes option 3.
- Option 3: rows shown earlier can be excluded, but aggregates cannot. Profile top values, search counts and transform parse rates would be computed over rows that later become the test set. A value map built from the profile would then cover every held-out value, so validate could no longer catch an unseen value, which is one of the main things it catches. This weakens the test most.

**Against the leaning (protect the first K lines, plus a one-line prompt hint).**
- The hint already exists twice and Sonnet followed it in 0 of 18 runs (E7). A third sentence is unlikely to change that, and a rule that works on one model only is not a harness rule.
- K is arbitrary. A file with a longer preamble than K can still have its header held out.
- Protection alone only helps if the agent happens to look. It should not depend on that.

**Recommendation: option 1 with K = 12, and `read_table` itself returns the raw top of the file. No prompt hint is relied on, and no gate.**
- `read_table` always returns `raw_top`: the first 12 raw rows, numbered as `skip_rows` counts them, before any option is applied, on a successful and on a failed read. Because those rows are never held out, showing them leaks nothing.
- This makes the second gate unnecessary (every run that reads a table has seen the top) and replaces the first gate, which would force an order of calls and cannot work for workbooks, where `sniff` shows nothing.
- `raw_top` is dataset content: payload only, with its own budget (cells cut at 30 characters, 25 columns) inside the existing 6,000-character cap.
- Implementation stays out of the reader: the table builder fingerprints the first 12 raw rows with a no-layout read and excludes those fingerprints from the reservoir. A data row identical to a protected row is protected too.
- JSON: the first 12 records.
- Residual limit, stated: a header below row 12 can still be hidden by a first wrong parse. Not solved here.

**Consequence for small files (ties to item C).** With 12 rows protected, a file with fewer than about 22 data rows has too few rows left for a useful held-out set. Rule: when fewer than 10 rows remain eligible, no held-out set is made, the fields are judged on rows the agent saw (item C's `training` evidence), and the packet says "no held-out test was possible". Today such a file gets half its rows held out, including possibly its header (E4). So item C must be built before item B.

**Cost of being wrong.** K too small leaves deep headers hidden; K too large removes the held-out test from more small files. A held-out set that excludes the top rows is slightly optimistic for files whose first rows are unusual. Changing K later changes every split, so earlier traces would not reproduce.

**Tests.** For csv, xlsx, xls, json and a zip member: none of the first 12 raw rows is ever held out, including after a re-read with other options and after a re-split. The 12 lines `sniff` shows are all training rows. `raw_top` is present on success and on a failed read, in payload not text, and its numbering matches `skip_rows` on a fixture with a blank line. Small-file rule at the boundary. Mutation targets: protection removed, K changed, `raw_top` filtered or renumbered, protection lost on re-split.

**ARCHITECTURE.md.** Held-out bullet and `read_table` row in section b; change log.

## C. Sparse columns: a field whose held-out rows are all empty

**Problem.** E8. A mapping with no evidence at all passes as validated.

**Options**
1. Judge the field on the populated training rows of the whole file when the held-out rows give fewer than 5 judged values.
2. Cap its `field_confidence` and mark it unverified.
3. Refuse `finish` unless the agent states the evidence.

**Recommendation: options 1 and 2 together, as one three-state `evidence` value per mapped field, set by code. Not option 3.**
Option 3 asks for a statement, and the project has already decided that the model's own statement is not evidence (the `could_not_read` rule).

| `evidence` | When | Rule | Cap on `field_confidence` |
|---|---|---|---|
| `held_out` | 5 or more judged values on held-out rows | 90% floor, as today | none |
| `training` | fewer than 5 on held-out, 5 or more over all training rows | same 90% floor, hard failure below it | 0.8 |
| `unverified` | fewer than 5 judged values in the whole file | hard failure only if no value parses at all | 0.5 (the existing cap) |

- Why 0.8: it is the cap already chosen for generated transforms, "tested, but not on unseen rows", and it stays above Part 4's 0.6 line so the claim competes normally.
- Why 0.5: it is below that line, so Part 4 uses an unverified claim only if nothing better exists (E13). That is the downstream meaning of "unverified", and it needs no new mechanism at ingest.
- Training evidence is weaker than held-out evidence for anything fitted to seen values, such as a value map. For a sparse column it is all the evidence the file has.

**What "unverified" does downstream**
- Config: each field carries `evidence` and whole-file counts (populated, judged, ok, rejected).
- Packet: an evidence column, and a separate list of unverified fields with their populated-row count and up to three raw-to-value examples from training rows.
- Review sheet: an evidence column; examples come from training rows when held-out has none, and are labelled so.
- Critic: for a field with no populated held-out example, the examples include up to two populated training rows, so the critic is not judging blind (E8: "no example row contains" the column).
- Benchmark: `fields_training_evidence`, `fields_unverified`, and coverage counts that separate "identifier verified" from "identifier unverified".
- Ingest: no change to the observation schema. The capped `field_confidence` carries it.
- Finish: not refused. An unverified field may stay in a `validated_config`; the coverage columns show it.

**Not decided here.** Part 3 links on ABN equality and does not read `field_confidence`, so an ABN from an unverified field can still support a link (the checksum and name agreement still apply). Whether it should is the owner's call.

**Cost of being wrong.** Caps too generous let an untested mapping compete as normal in profiles. Too strict and a real sparse identifier is lost. The threshold of 5 is inherited, not measured.

**Tests.** A sparse fixture with values only in training rows; each state and its boundary; the floor on training evidence; both caps; the zero-parse failure; packet list, sheet labels, benchmark columns; a forced end abstains a field that fails on training evidence; a file too small for a held-out set. Mutation targets: state boundaries, caps, floor skipped for training evidence.

**ARCHITECTURE.md.** `validate` row, the "Code computes field_confidence" bullet, section e per-run list, change log.

## D. valid_from and valid_to

**Problem.** E9, E10, E11, E12. They are set by the agent and stamped on every observation of the row, yet no person, no critic and no check looks at them.

**D1. Packet and review sheet: show them.** A "record-level settings" table in the packet: reader options with the layout stated in words, `record_id` with its whole-file uniqueness numbers, `observed_at`, `valid_from`, `valid_to`, each with source column, transforms, populated rows, parse rate, evidence state and three examples. One sheet row each for `valid_from`, `valid_to` and a per-row `observed_at`. No real alternative; this restores what the round-1 packet showed.

**D2. Critic: show them.** Add `valid_from`, `valid_to` and `needs_transform` to the critic's config summary. This removes the false "column not accounted for" issue (E9) and lets the critic judge the meaning.

**D3. Parse failures. Options**
1. Count them in validate only, by re-applying the transforms in the agent's code.
2. The engine's `run_rows` returns statistics and reject records for the three envelope settings.
3. Leave them silent.

Recommendation: option 2. The engine docstring's promise is that what the agent tested is what ships; a second implementation in validate breaks it. Same 90% floor and the same evidence states as item C. A failing `valid_from` or `valid_to` is abstained by code by deleting the key, which the gate already treats as a narrowing.
Cost: the reject files of round-1 sources can change on re-extract, for the two configs in E11. Measure the difference on the six in a scratch copy before accepting.

**D4. Which columns may feed them. Options**
1. Strict: only a column that says when the entity's own registration, licence, accreditation or status started or ended.
2. Round-1 practice: any start or end date of whatever the row describes, a contract included (E11).
3. Scoped: `valid_from` / `valid_to` apply only to named canonical fields, and the engine stamps per field.

Reasoning. The ontology says `valid_from` is "when the claim became true in the world, if the source says" and that a null `valid_to` means "still current". A contract's commencement is not when a supplier's name became true, and a contract's end date stamped as `valid_to` says the supplier's name, address and identifier stopped being true when the contract ended. That is a wrong claim. It is latent today because nothing reads these fields (E12), not because it is right.
The same objection applies in a weaker form to a licence register: the row-level stamp is right for the licence or status claim and wrong for the name. Only option 3 fixes that properly.

Recommendation: option 1 now; option 3 recorded as a companion to step 4a (both are "apply this only to part of the row"). Proposed generic wording to replace the sentence in rule 10, in the shared rules text so the critic has it too:

> valid_from / valid_to: only from a column that says when the entity's own registration, licence, accreditation or status started or ended. A date of an event or transaction the row records (a contract, an order, an invoice, a payment, an application) is not when a name, identifier or address became true: leave it unmapped.

This reverses one round-1 approval (the contract-dates config in E11) when the six are re-onboarded at step 5, so it is the owner's decision.

**Cost of being wrong.** Strict loses the contract period, for which the ontology has no field anyway. Round-1 practice writes false validity windows onto identity claims. Scoped is the right model and the most engine work.

**Tests.** Packet table and sheet rows; critic summary keys; engine statistics and reject records for all three settings; floor and abstention by key deletion; evidence states; the six-source reject diff as a recorded measurement; rule text present in both prompts. Mutation targets: failures not counted, key not deleted, summary keys dropped.

**ARCHITECTURE.md.** `validate` and `critique` rows, the packet description, section i (option 3 next to 4a), change log.

## E. Placeholder headers: `col_N` cannot be told from a misread header

**Problem.** E3. `header_rows=0` is a legitimate setting and also what a confused agent falls back to. The existing placeholder warning covers `_blank_N` and `Unnamed`, not `col_N`.

**Options**
1. The config carries column labels the agent writes, and the packet shows them.
2. Warn when `header_rows` is 0 and the first raw rows look like a header.
3. Require a stated reason for `header_rows=0`.
4. The packet shows the raw top of the file beside the reader options.

**Against the leaning (column labels in the config).**
- Once A and B exist, a file that has a header row can be read with its real names. `col_N` is then left for files with no header at all, where each field's `reason` already says what the column is.
- A label is model-written text that the engine never reads: two names for one column, and no code check can tell whether the label is right.
- In the run that prompted this, the label text would have been copied from label rows in the data: untrusted content promoted into config metadata and shown to the reviewer as if it were a name.
- The root causes were the reader (A) and the hidden header (B), not a missing label.

**Recommendation: options 4 and 2. Not 1, not 3.**
- Option 4 is evidence made by code: the reviewer sees rows 1 to 12 and the layout the agent chose, and can judge `header_rows=0` directly. It reuses item B's `raw_top`.
- Option 2 as a meaning warning, generic and computed by code: with `header_rows=0`, if the first row read as data is all text, its cells are distinct, and at least half of the columns hold numbers or dates in the rows below it, warn that the row looks like a header and name the three layout options. An all-text table can trigger it falsely; the warning is answerable like any other.
- Option 3 is a statement, not evidence.

If labels are still wanted, the smallest safe form is an optional `label` on a field: display only, never read by the engine, covered by the approval hash, shown in the packet as "the agent's label, not from the file".

**Cost of being wrong.** Without labels, a reviewer of a headerless file reads `col_7` plus a reason and examples: slower. With labels, a reviewer may trust a name the file never contained.

**Tests.** The warning fires on a fixture whose header was read as data and not on a headerless numeric table or an all-text table without a header-like first row; it is answerable; the packet shows the raw rows and the layout sentence. Mutation targets: each of the three conditions.

**ARCHITECTURE.md.** `validate` row, packet description, change log.

## F. Rule 4 versus rule 5: individuals listed on a register

**Problem.** E14. Rule 4 says individuals listed as licensees are mapped as `legal_name`. Rule 5 says a name the data does not label as registered, licensee or supplier name maps to `trading_name` at 0.6 or lower. A register of approved persons with a plainly named column falls under both, and nothing limits the confidence of a `legal_name` chosen under rule 4.

**Options**
1. Rule 5 always wins: unlabelled names are trading names, persons included.
2. A stated exception with a definition: a register kept by a regulator or licensing body makes its registrants' names registered names.
3. A person rule: an individual's own name is a legal name wherever the row is about that individual.

**Recommendation: option 2, with a cap enforced by code.**
- Option 1 calls registrants' registered names trading names, and section d bridges the two differently (licensee to the companies register, trading name to the business-names register), so it sends them down the wrong path.
- Option 3 has no test a critic can apply.
- Option 2's test can be checked from the dataset's description and rows: does the register list this row's subject as the holder?

Proposed generic wording for rule 5 (shared rules text, so agent and critic get the same words):

> entity.legal_name is the registered name; entity.trading_name is a name traded under. Use legal_name when (a) the data labels the column as a registered, legal, licensee or supplier name, or (b) the dataset is a register kept by a regulator or licensing body and each row is the person or organisation that the register lists as HOLDING a licence, registration, accreditation or approval (the holder, not a premises, venue or product the licence covers). Under (b) without such a label, mapping_confidence is 0.7 or lower. Any other name column maps to entity.trading_name at 0.6 or lower; it is not left unmapped for that reason.

And the last sentence of rule 4 becomes: "Individuals listed as registrants are mapped the same way (rule 5b); never infer sole_trader from a person-like name."

Critic guidance, one sentence: a `legal_name` with neither a label nor the register basis is blocking; one with the register basis is not blocking because the column is plainly named.

**Should code cap the confidence? Options**
1. No: prompt and critic only.
2. The agent declares a basis for each name field and code caps by the declared basis.
3. Code checks the source column's header against two short fixed word lists and caps when no word is present.

Recommendation: option 3. It needs no statement from the model, it can only lower a number, and it never changes a value or a field. `legal_name` is capped at 0.7 unless the header carries a registered-name word; `trading_name` at 0.6 unless it carries a trading-name word. A placeholder or generated header is always capped. The cap is applied where `field_confidence` is computed (lowest of model confidence, parse rate, evidence cap, label cap), so it does not touch the "confidence only down after the last critique" rule. The packet says which cap applied.

**The individual-register case under this.** The name maps to `legal_name` (5b), capped at 0.7 because the header is unlabelled, which is what the agent chose (E14). Rows without an ABN still emit name observations: observations are claims and ingest does not reconcile. Section d then decides: a person without their own ABN is an edge endpoint only, never a profile. Dropping such rows at ingest would need a conditional mapping (step 4a).

**Cost of being wrong.**
- 5b too generous: names of premises or venues on a licensing list become legal names. The holder-not-premises clause and the 0.7 cap are the guards; the first live dataset of this project is exactly that risk.
- The word lists are a heuristic. A terse header on a true company register gets 0.7 instead of 0.95. That is still above Part 4's 0.6 line, but Part 4 breaks ties on `field_confidence`, so winners can change when the six are re-onboarded. Measure then.
- 0.6 is exactly Part 4's low-trust line (E13): a trading name at 0.6 competes normally, one at 0.59 does not.

**Tests.** Rule text in both prompts, word for word; the existing no-dataset-words test extended to the new text; cap function on labelled, unlabelled, placeholder and list-source headers; `field_confidence` is the lowest of the four; the packet names the cap. Mutation targets: each cap value, each word list, the placeholder case.

**ARCHITECTURE.md.** The rules summary bullet and the "Code computes field_confidence" bullet in section b, change log.

## G. Trace: the agent's reasoning is not recorded

**Problem, restated from the evidence.** The trace is not dropping anything (E15). The model does reason, in a third to a half of Haiku turns and under a fifth of Sonnet turns, and that reasoning is billed; the request simply never asks for its text (E16). In the other turns there is no reasoning block at all.

**Options**
1. Ask for the summary: `thinking: {"type": "adaptive", "display": "summarized"}` in `llm.chat`, the one place provider code lives.
2. A harness-owned `note` on every tool call: a required short string, "why this call", added to every tool schema by the loop, removed before validation and execution, stored in the trace event.
3. The between-tool progress display (beta).

**Recommendation: options 1 and 2. Not 3.**
- Option 1 records the model's actual reasoning at no extra token cost, but only in the turns that have any (E15), so it cannot give the demo a line per step.
- Option 2 gives one line for every call, live and in the replay. It is what the model says about its choice, not its reasoning, and the plan should not present it as more.
- Option 3 is listed for one of the two models only and needs a beta header (E16).

**Cost and size**
- Option 1: no added thinking tokens per E16. Trace growth is unknown until measured; the full block must be stored because a resumed run sends it back.
- Option 2: roughly 20 to 40 output tokens per turn, about $0.0002 per Haiku run and $0.004 per Sonnet run, and under 2 KB per trace against 23 to 41 KB today (E17).

**How it appears**
- Live and replay print one line per turn: turn number, tool, the note.
- A flag on `onboard` prints the reasoning summary under the turn, cut at 300 characters.
- Notes and summaries can quote dataset content. They go to the terminal and the trace only; the harness never places them in a prompt as its own text.

**Risks to settle during the build**
- One live call per model first (about $0.01) to confirm the pinned SDK accepts `display` and to measure summary length.
- A resumed run rebuilds history from the trace, which is written after redaction. A thinking block altered by redaction would no longer be the block the API issued. The 180 signed blocks in today's traces already carry this exposure. Test that a thinking block survives the trace byte for byte, and exempt the `signature` value from redaction (it is opaque API output, not a secret this project holds).
- A required `note` that a model omits costs a refused call. Count those refusals in the benchmark; if more than 2% of calls are refused for it, make the note optional.

**Cost of being wrong.** Long summaries bloat traces (bounded by the 4,096-token turn limit). A required note adds refusals. If `display` is rejected by a model, every call fails, which is why the live call comes first.

**Tests.** The loop adds `note` to every schema, refuses a call without it with a sentence naming the fix, stores it in the event, and never passes it to a tool or to the finish gate's hash; replay prints it; `llm.chat` sends the display setting (fake client); a thinking block round-trips through the trace unchanged; redaction leaves a signature alone. Mutation targets: note not removed before execution, not stored, signature redacted.

**ARCHITECTURE.md.** Trace and Loop paragraphs in section b, change log.

## H. Order

| # | Item | Why here | One Sonnet pass? |
|---|---|---|---|
| 0 | Move per-module detail out of ARCHITECTURE.md into docstrings (tool table detail, reader options, benchmark harness) | The document is 414 lines against a guideline of about 400, and every item below adds to it | Yes |
| 1 | G: reasoning summary and `note` | Every later live check becomes explainable | Yes, after the two live calls |
| 2 | C: evidence states | B needs it for small files | Yes, but review it closely: it changes what `field_confidence` means |
| 3 | B: protected rows and `raw_top` | A is useless without it | Yes, with the mutation list |
| 4 | A: `skip_rows_after_header` | Small once B exists | Yes |
| 5 | E: raw rows in the packet, header-like warning | Reuses B and A | Yes |
| 6 | D1, D2, D3: packet, critic, parse failures | Reuses C's states | D1 and D2 yes. D3 touches the engine and round-1 outputs: its own pass, with the six-source diff |
| 7 | F: wording and label cap; D4 wording | Prompt changes last, after the owner's decisions | Yes |

After the build: one Haiku dev pass (about $0.09) and, if wanted, one Sonnet pass (about $1.00), compared with passes e and t. Seed 2 stays untouched. The dev draw has now been run seven times and fixes have been made against it each time; its results are a regression check, not a measurement.

**Must wait for step 4a** (conditional or scoped mapping): `valid_from` / `valid_to` applied only to named fields (D4 option 3); mapping a row only when it carries an identifier (F); the mixed identifier column already recorded there.

**Not in 3b:** `approve.py` still reads a round-1-only field and fails on agent configs (step 5). The packet changes in C and D should keep its field numbering in mind.

## What you must decide

1. **D4.** Strict rule for `valid_from` / `valid_to` (recommended), which reverses the contract-dates choice in one approved round-1 config at step 5, or keep round-1 practice.
2. **F.** The register exception and its wording; the caps 0.7 and 0.6; the two header word lists; and whether 0.6 sitting exactly on Part 4's low-trust line is what you want.
3. **C.** The caps 0.8 (training evidence) and 0.5 (unverified); whether an unverified field may stay in a `validated_config` (recommended yes); and whether an ABN from an unverified field may support a link.
4. **E.** Column labels in the config, against the recommendation, or not.
5. **B.** K = 12, and that a file with fewer than about 22 rows gets no held-out test.
6. **G.** A required `note` on every call, and whether reasoning summaries are shown in the live demo.
7. **D3.** That reject files of round-1 sources may change on re-extract.
8. **After the build.** Whether to spend a Haiku pass, and a Sonnet pass, on the dev draw again.

## What I decided for you

- The reader option is `skip_rows_after_header`: a count of raw rows, refused with `header_rows=0` and for json, default 0. `FORMATS` is not touched.
- The raw top of the file is returned by `read_table` itself. No prompt hint is relied on, `sniff` is unchanged, and there is no new finish gate and no forced call order.
- Splitting at the first validate, or after a layout confirmation, is rejected: both leak or weaken the test.
- "Refuse finish unless the agent states the evidence" is rejected: a statement is not evidence.
- The beta progress display is rejected: one model only.
- Evidence states and all caps are applied where `field_confidence` is computed, so the gate's confidence rule is untouched.
- C is built before B, B before A, prompt wording last.
- No proposed rule or prompt text in this plan names a dataset, a column or a value.
