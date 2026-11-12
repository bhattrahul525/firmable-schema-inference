# Architecture (round 2)

Status: DRAFT (not approved)
Version: 2.0
Last updated: 2026-11-12

Round 1's design (fixed 8-step agent, whitelisted engine, ABN/name matcher) stays described in WRITEUP.md and
DECISIONS.md. This document is the round-2 design that answers the CTO's feedback: a tool-using agent that can
ingest a random dataset live, and richer entity resolution. Numbers marked (measured) come from read-only checks on
the Part 1 outputs.

## a. Ground rules

1. The harness decides safety; the model decides the investigation. Validation, critique, budgets, output caps and
   the human gate are enforced in code.
2. All dataset content is untrusted. Cell values, headers, sheet names, file names and CKAN text enter prompts only
   as JSON inside a `<data>` block; the system prompt says nothing inside it is an instruction.
3. Observations stay claims. A looked-up ABN is never written onto a record as if the source stated it; it arrives
   through a link to a register record that carries it.
4. Three confidences, never blended. Relationship edges carry their own `relation_confidence`.
5. Abstaining is a correct result: "no business entities" and "could not read" are valid outcomes.
6. Round-1 raw files are pinned by SHA-256 and not re-downloaded (QBCC is a live register; labels must carry over).
7. Package names do not change. New modules sit beside existing ones; README commands and tests keep working.

## b. Agent

**Loop.** System prompt, then the model picks one tool, the harness runs it, a capped result returns, repeat until a
terminal outcome. Every call is appended to `logs/agent_runs/<source>/trace.jsonl`; a re-run replays the trace.
The round-1 pipeline stays available as `--mode pipeline` (fallback).

| Tool | Does | Cap |
|---|---|---|
| `fetch` | The reference the human gave (URL, CKAN id, local path, CKAN datastore dump). Streams; progress lines go in the trace | 200 MB enforced while streaming (1,956 of 2,440 pool datasets publish no size) |
| `list_members` / `list_sheets` | Archive members; workbook sheets with dimensions | 50 entries; 1 GB decompressed |
| `sniff` | Magic bytes, encoding, delimiter guess, raw head | 12 lines x 300 chars |
| `read_table` | Runs a parametric reader; returns headers, row count, first rows, or the error | 20 rows x 40 cols x 100 chars |
| `profile` | Per-column fill, distinct count, shapes | 60 columns; distinct counts above 200k marked `capped` |
| `check_unique` | Exact uniqueness of named columns (streamed) | one answer |
| `sample` / `search` | Rows by strategy or regex, from the non-held-out partition only | 30 / 10 rows |
| `try_transform` | Real engine on the 300 held-out rows: parse rate and rejects | 5 examples |
| `define_transform` | Level-G generated transform (section c) | 40 lines of code |
| `validate` | Structural, held-out and meaning checks | 6,000 chars |
| `critique` | Separate model call, fresh context: raw rows beside their observations | 10 examples |
| `ask_human` | Question goes into the packet and the run pauses | 1 per run |
| `finish` | Declares an outcome | see below |

**Enforced by the harness**
- The model can fetch only the reference the human supplied; a URL found inside a cell is never fetched.
- The held-out split is made when a table is first read; the model never sees held-out rows while proposing.
- `finish` is refused unless both `validate` AND `critique` ran on the exact config being finished (matched by hash).
- Every critique issue must be fixed or answered; an issue that is neither gets its field abstained by code.
  At most 2 critique rounds.
- `no_business_entities` requires `read_table` and `profile` to have run. `could_not_read` requires two reader
  attempts or a fetch failure.
- Code computes `field_confidence` (lower of model confidence and parse rate; level G capped at 0.8),
  `derivation_level`, and abstention.

**Chosen by the model:** tool order, reader options, what to inspect, which transforms to use, when to abstain,
when to ask.

**Terminal outcomes:** `validated_config`, `partial_config` (abstentions listed with reasons),
`no_business_entities` (evidence cited), `could_not_read` (reason).

**Budget.** 40 tool calls, $1.00, and 4 minutes of wall-clock excluding download (the trace shows download
progress). At 80% of any limit the harness tells the model to wrap up. At 100%, or when `finish` is refused twice
in a row, the harness finalises itself: validate, abstain on failing fields, one critique, write the packet,
outcome `partial_config`. No budget burn.

## c. Transforms and readers

**Three levels, logged per field as `transform_level`.**

| Level | What | Notes |
|---|---|---|
| W | The existing 12 whitelisted transforms | |
| P | Parametric primitives: `regex_extract`, `regex_replace`, `template`, `map_values`, `split`, `constant` | `constant` tagged L3, capped at 0.6, allowed only for `address.state` and `address.country` |
| G | Generated Python | Accepted only after `try_transform` shows W and P stay below 90% parse rate |

Preference order is W, then P, then G. The packet shows the level per field; the benchmark reports how often G was
needed. Recurring G transforms are listed by a `promote` report for the human to move into the whitelist.

**Readers** are hand-written and tested; the agent only sets options.

| Reader | Options |
|---|---|
| delimited | encoding, delimiter, quote, `skip_rows`, `header_rows` (0, 1 or n merged), `skip_footer_rows` |
| xlsx | sheet, `skip_rows`, `header_rows`, drop empty columns |
| json | `records_path`, flatten depth, NDJSON (GeoJSON via `features`) |
| archive | zip or gz member, dispatched to the readers above |

Files over 50 MB are streamed. Not in the core: PDF, HTML, parquet, XLS, XML, reshape (XLS is a recommended
stretch: 52 pool datasets are reachable only through XLS, measured). One run onboards one table; cross-table
joins are out of scope.

**Sandbox for level G: defence in depth, not a security boundary.**
- *Static check.* One function `transform(value)`. Allowlist of AST node types and of every name and attribute
  name. Forbidden: `import`, `while`, `lambda`, `*` and `**`, any attribute starting with `_`, `.format`,
  `format_map`, and anything not listed.
- *Runtime namespace.* Builtins replaced by a short allowlist (`str int float len min max sorted any all enumerate
  zip range isinstance`). `re` and date parsing are facade objects exposing only allowed functions, so no path from
  a module's public attributes to `sys` exists. Regex patterns over 200 characters are rejected.
- *Process.* `python -I -S` subprocess, empty environment, temp cwd, JSON on stdin/stdout. Limits come from a
  start-up probe that tests which rlimits actually stop a violator on this host: Linux uses memory, CPU and wall
  timeout; macOS uses CPU and wall timeout (the memory limit is unreliable); Windows has no `resource` module, so
  wall timeout only. The probe result is printed in the packet.
- *File and network blocking rests on the AST allowlist and the facade alone.* The subprocess runs as the same
  user on the same filesystem. Container or WASM isolation is the production answer.
- *Extraction.* Values are batched per field. A batch that times out is bisected; offending values become rejects.
- *Tests.* Unbounded loop; catastrophic regex `(a+)+$` on long input; `import`; dunder access; `.format`; module
  traversal; memory bomb; oversize output; an injection string in a cell passes through as plain data; the
  capability probe.
- *Approval.* Code, tests and sha256 live in the config under `custom_transforms`, covered by the approval hash
  and shown at the gate. The engine runs generated code only from an approved config, in the same sandbox.

## d. Entity resolution

**Evidence sources, in build order**
1. **Recovered names.** Re-onboard the six sources with levels P and G (WA bracket names, QLD comma lists).
2. **Rarity-weighted names.** Token IDF over all mentions and register names; "Australia" and "Group" count for
   almost nothing.
3. **ASIC registers, onboarded by the agent like any source** (both CC BY 3.0 AU, measured). Companies: 79 MB zip /
   401 MB CSV, carries ACN, ABN, type, status, registration date and former-name rows. Business Names: 72 MB zip,
   business name to holder ABN. A generic engine row filter keeps only rows whose ABN, ACN or name key appears in
   our mentions; the trimmed result is committed with attribution.
4. **ABR lookup (stretch, not on the critical path).** Only for ABNs in candidate links and profiles, git-ignored
   cache, terms saved to `docs/abr_terms.txt`; the method name is read from the live WSDL, not from memory.

**Offline fallback = the two ASIC registers.** They lack non-company entity types, ABN status and location. With
no internet the matcher runs with ABR features marked absent and the output says so.

**Matcher m2.0** (hand-set tiers; accept 0.80, loose 0.60). Scores are calibrated by the hand check, not fitted.

| Tier | Evidence | Confidence |
|---|---|---|
| T1 | Equal ABN or ACN, names agree by rarity-weighted overlap | 0.98 |
| T1r | Equal identifier, names differ, a register or ABR name history confirms both names | 0.95 |
| T2 | ACN inside ABN, names agree | 0.88 |
| T3c | No-ABN record bridges to exactly one registered holder AND a second independent hit agrees (licensee to Companies, trading name to Business Names, same ABN) | 0.88 |
| T3 | Single uncorroborated register hit | 0.75 (loose) |
| T4 | Exact name plus postcode / plus state / both companies with no location | 0.85 / 0.70 / 0.65 |

Refused: identifier match with unconfirmed name conflict, ambiguous register name, generic name, different ABNs,
person-like on both sides. Address evidence is postcode + state only (no address parser).

**Graph**

| | |
|---|---|
| Nodes | mention, register record, entity (derived), person, trust |
| Edges | `same_as` (the link table), `renamed_to` (register or ABR name history), `trustee_for` (ATF patterns), `nominee_of` (person listed under a company's ABN, the QBCC pattern) |
| Each edge stores | stable `edge_id` (endpoints + type, not the version), tier, band, `relation_confidence` / `link_confidence`, raw evidence features, evidence sources with dates, `matcher_version`, thresholds, `previous`, `human_label` |

**Rescore** stays a pure function over stored evidence (no sources, no extractor, no model). New: it refuses to
write if a human-labelled Y would be demoted or a human-labelled N promoted.

**People stay out of profiles.** A person-like mention under a company's ABN becomes a `nominee_of` endpoint.
Components made only of person-like mentions get no profile. Profiles are built from `same_as` components with
mentions from two or more of the six sources; register and ABR records enrich but do not count toward that.
(Known cost: sole traders who hold an ABN are excluded; stated in the write-up.)

**Hand check.** Round-1 labels carry over wherever both records are unchanged (same source, row hash, name and
identifier); expected 45 to 50 of 50 survive. They become the frozen regression set and the ABN-equal stratum.
New labelling samples only new strata (register-bridged, no-ABN, ABR-assisted if built): 15 rows each, so 30 to
45 rows, about 45 to 70 minutes. Round-2 precision is labelled non-independent (the registers are matcher
features, and ABN Lookup shows ASIC business names); no-ABN links are judged by hand.

## e. Benchmark

**Frame.** The 2,440-dataset pool minus the six (measured). Reachable through the readers above: 1,140. Zip only:
87. XLS only: 52. XML only: 37. No tabular file (PDF, shapefile, web services): 856. No resources: 268.

**Draws** (at most one dataset per publisher-and-title family; siblings of the six flagged):

| Draw | Seed | Shortlist ranks 7-50 | Pool, stratified by format | Injection case |
|---|---|---|---|---|
| dev (fix against it) | 1 | 6 | 5 | 1 |
| final (run once, unchanged) | 2 | 8 (rank 38 excluded) | 7 (one from the no-tabular group) | 1 |

The final draw runs once per model (Haiku and Sonnet) at a recorded commit.

**Per run:** outcome, tool calls, cost, wall-clock, download seconds and bytes, reader, W/P/G counts, fields
mapped and abstained, open critique issues, sandbox capabilities, model.

**Verification.** One sheet, `handcheck/benchmark_review.csv`: for each business-bearing dataset one row per mapped
field (three raw to value examples, level, "wrong?"), plus "outcome correct?" and "key field missed?". About 5
minutes per dataset, 30 to 40 minutes in total. Non-business verdicts are spot-checked.

**Published (final draw only, dev rate beside it):** validated; validated with 0 wrong fields on review; key field
missed; non-business correctly declared; could not read by reason; injection pass or fail.

## f. Demo runbook

`onboard <ref>` (live trace) -> packet -> `approve` -> `extract` -> `resolve` (full re-run, seconds) -> one profile
with provenance. A second rehearsal uses a deliberately wrong dataset (weather data) to show "no business entities".

| Case | Works | Degrades |
|---|---|---|
| My machine, internet | Everything | Nothing |
| My machine, no internet | Extract, resolve, rescore, profiles, trace replay | No LLM, so no onboarding of a new dataset (phone hotspot is the backup) |
| Their machine, internet | Onboarding with their key and model access | Registers need a ~150 MB download; without it the new dataset links by identifier and name only; sandbox weaker on macOS/Windows |
| Their machine, no internet | Tests and committed outputs | A walkthrough only |

## g. File layout

**Changed:** `src/llm.py` (tool-use call, history caching); `src/part2_agent/` (`onboard.py`, `fetch.py`,
`packet.py`, `approve.py` numbers every setting and shows generated code); `src/engine/` (`readers.py`,
`transforms.py`, `config.py`, `extract.py`: row hash, row filter, streaming); `src/part3_resolve/` (`features.py`,
`score.py`, `run.py`, `rescore.py`, `handcheck.py`); `src/part4_profiles/build.py`; `requirements.txt`.

**New:** `src/part2_agent/` (`loop.py`, `tools.py`, `guard.py`); `src/engine/` (`sandbox.py`, `custom.py`);
`src/common/names.py`; `src/part3_resolve/` (`idf.py`, `registers.py`, `graph.py`, `abr.py`); `src/benchmark/`;
`demo/RUNBOOK.md`; `docs/abr_terms.txt`; new tests.

## h. Build order (12-hour limit, including your review time)

| # | Step | Hours |
|---|---|---|
| 1 | Loop, tool-use wrapper, guards, outcomes, trace | 1.25 |
| 2 | Tools and parametric readers | 1.5 |
| 3 | Benchmark harness, injection case, dev draw and fixes | 1.5 |
| 4 | Primitives, sandbox, custom execution, tests | 1.25 |
| 5 | Re-onboard the six, your 6 approvals, extract | 0.75 |
| 6 | Registers (streaming, row filter, 2 approvals), bridging | 1.25 |
| 7 | IDF, m2.0, graph, rescore gate, profiles | 1.5 |
| 8 | Round-2 hand check | 1.0 |
| 9 | Final draw on both models, your review sheet | 1.0 |
| 10 | Write-up, README, runbook, rehearsal | 1.0 |
| | **Total** | **12.0** |

No slack. Stretch outside the 12 hours: ABR lookup (0.75), XLS reader (0.25), XML and reshape (0.5).

**Cut order if over:** (1) stretch items; (2) hand check down to 10 rows per stratum; (3) `renamed_to` edges;
(4) Business Names register only. Never cut: enforced validate and critique, the sandbox tests, the unchanged
final draw, the hand-judged no-ABN stratum, the human gate.

## i. CTO feedback to design

| Feedback | Answered by |
|---|---|
| Agents with tools, not rigid; ingest a random dataset live | Tool loop (b); three transform levels and generated code (c); parametric readers; four clean outcomes; the benchmark's published final-draw rate (e); the runbook (f) |
| More creative entity resolution, connect more data points | Recovered WA and QLD names; register bridging with two-register corroboration; name history; rarity-weighted names; typed graph edges; richer profiles (d) |

## j. Open questions and risks

1. No internet means no agent: the largest demo risk. Recommend a hotspot and asking Chath; no local-model path planned.
2. Critique gate is "ran, and each issue fixed or answered", not "critic satisfied": the critic raised a false
   alarm in round 1 and shares the agent's blind spots.
3. "0 wrong fields" rewards under-mapping, hence the "key field missed" measure.
4. Sandbox on Windows has no CPU limit, only the wall timeout.
5. Full independence is unachievable: ABN Lookup shows ASIC business names. We report matcher evidence versus
   labeller evidence.
6. Carried labels are not a random sample of the new matcher's links: regression gate and unchanged stratum only.
7. The people rule excludes sole traders with an ABN, which the ontology allows.
8. Register bridging could add thousands of name-based links from VIC and WA; uncorroborated hits stay loose.
9. XLS reader recommended (52 datasets); the owner decides.
10. `nzbn` cut: an NZ dataset can still map a 13-digit NZBN at level P without a check digit.
11. Cost estimate $8 to $10 for round 2, so project spend will likely pass $10; we report the real number.
12. Sonnet may miss the 4-minute target; the benchmark will show it.
13. If the final draw crashes, publish as-is and report fixes separately.
14. 12 hours is tight; the time limit N is not yet confirmed by the owner.

## k. Change from the round-2 plan before this version

Critique harness-enforced before `finish`; two benchmark rates plus a review sheet; sandbox rlimit probe, attribute
allowlist, facade and `.format` ban; registers built before ABR, agent-onboarded, labelled non-independent; label
carry-over by row hash with an estimate of new rows; cut address parser, postcode table, `--incremental`,
`co_located`, parquet, `nzbn`, `second_opinion`, calibrated-score fit; kept package names; download excluded from
the 4-minute budget; four demo cases; new `check_unique`, held-out partition rule, fetch restriction, two-register
corroboration tier, stable edge ids, rescore gate.

## Change log

| Date | Version | What changed | Why |
|---|---|---|---|
| 2026-11-12 | 2.0 | Initial round-2 design: tool-using agent, three transform levels with sandboxed generated code, ASIC-register bridging, typed graph, generality benchmark, demo runbook | CTO feedback on the first submission: more agentic and generic ingestion, live demo on a random dataset, more creative entity resolution |
