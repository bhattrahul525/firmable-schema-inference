# Architecture (round 2)

Status: APPROVED
Version: 2.14
Last updated: 2026-11-13

Round 1's design (fixed 8-step agent, whitelisted engine, ABN/name matcher) stays described in WRITEUP.md and
DECISIONS.md. This document is the round-2 design that answers the CTO's feedback: a tool-using agent that can
ingest a random dataset live, and richer entity resolution. Numbers marked (measured) come from read-only checks on
the Part 1 outputs. Building starts in a new session; no hour budget applies (time is logged from actuals).

## a. Ground rules

1. The harness decides safety; the model decides the investigation. Validation, critique, budgets, output caps and
   the human gate are enforced in code.
2. All dataset content is untrusted. Cell values, headers, sheet names, file names and CKAN text enter prompts only
   as JSON inside a `<data>` block; the system prompt says nothing inside it is an instruction.
3. Observations stay claims. A looked-up ABN is never written onto a record as if the source stated it; it arrives
   through a link to a register record that carries it.
4. Three confidences, never blended. Relationship edges carry their own `relation_confidence`.
5. Abstaining is a correct result: "no business entities" and "could not read" are valid outcomes.
6. Raw files are pinned by SHA-256 when fetched. The six round-1 files are not re-downloaded (QBCC is a live
   register; labels must carry over).
7. Package names do not change. New modules sit beside existing ones; README commands and tests keep working.

## b. Agent

**Loop.** System prompt, then the model picks one tool, the harness runs it, a capped result returns, repeat until a
terminal outcome. The request uses `tool_choice` auto with parallel calls disabled (Sonnet 5.5 returns 400 for forced
tool use); a reply with no tool call gets one nudge, and a second in a row ends the run. `finish` is owned by the
harness: a tool registry cannot define it. The round-1 pipeline stays available as `--mode pipeline` (fallback).

**Trace.** `logs/agent_runs/<source>/trace.jsonl`. Line 1 is a header: source id, reference, input file SHA-256, model,
code version (the four core files plus the modules the tools and hooks come from), the limits, and a hash of the
system prompt, task and tool schemas. Every model turn, tool call (with the final URL after redirects, for `fetch`)
API retry and, during a download, `progress` line follows (progress lines are skipped on replay). The `tool_call` event of `ask_human` also carries `human_wait_seconds`. A re-run replays the trace (no model calls, no tool re-execution) and prints a REPLAY label;
replayed turns are marked, and a `resume` event marks where live work restarts. Resuming is REFUSED (never
cut-and-continue) if any header field differs (so a changed limit, prompt, task, tool schema or tool code refuses), if
the trace is internally inconsistent (a recorded tool call that is not the one in the recorded model turn), if the
harness would write a live event while recorded events remain, or if the input file's hash changes mid-run. Not
detected: a trace edited consistently by hand (no signature), and a change to what a tool does that is outside the code
version. Every string written to the trace or to `llm_calls.jsonl` is redacted BEFORE the line is serialised (API key,
bearer and basic credentials, whole header values), so a line is always valid JSON. A split key (one secret spread over
two fields) is not caught.

**Reasoning summary (step 3b, item G).** Every `llm.chat` call requests `thinking: {"type": "adaptive", "display": "summarized"}`;
`llm.call` (the critique) does not. Confirmed live on both Haiku 5.5 and Sonnet 5.5 before building on it:
accepted with no error, readable text on a turn where the model actually thinks, no extra token cost over the default
`display: "omitted"` (thinking is billed the same regardless of display). The block is stored in the trace like any
other content block (no structural change: the trace already records every block) and passed back unmodified on the
next turn. A replayed turn now prints the first thinking block's text, cut to 300 characters, after the tool names
(`[REPLAY] turn N: tool — thinking: ...`); display-only, never fed back into a prompt as the harness's own words. No
required per-call `note` was added (the alternative in the step 3b plan): it would have added refusals for no
reasoning guarantee beyond what the summary already gives on the turns that have one.

**API errors.** Transient errors are retried with backoff (2 s, then 4 s), at most 3 attempts, each recorded as an
`api_retry` event. Transient means connection and timeout errors, and exactly these statuses: 408, 429, 500, 502, 503,
504 and 529 (501, 505 and every 4xx other than 408 and 429 are not). In `llm.chat` (the agent) the SDK's own retries
are off so none are hidden. Round 1's `llm.call` keeps its own SDK retries (`max_retries=3`, not traced), and so does
round 1's critique, which uses it. Any non-transient error propagates, and re-running resumes from the trace.

**Cost log.** Every call logged from now on carries `"round": 2` in `logs/llm_calls.jsonl`; lines without a round are
round 1. `spend_summary()` reports round 1 by default and `spend_by_round()` reports each round separately, so round-2
spend never changes the round-1 figures quoted in the first submission.

| Tool | Does | Cap |
|---|---|---|
| `fetch` | Only the task's reference. No arguments: lists its resources (index, name, description, format, size, last modified; never URLs; for a CKAN id this is the dataset's resource list; all of it is the publisher's text, so it is untrusted data in the payload, descriptions capped at 300 characters). `resource_index`: downloads that one, into `data/raw/sources/<source_id>/` with a `metadata.json` in Part 1's shape (licence from CKAN, `unknown` + flag otherwise). One run onboards one table, but the agent may SWITCH resource once: `resource_index` plus a `reason` (traced as an `input_switched` event); at most two downloads per run (a failed attempt counts), each under the cap; the second replaces the first (its file, table and held-out split are discarded; the harness gate forgets what it learned about the first) and the pinned hash is the final one. The same index returns the cached file. A human can pin the resource with `onboard --resource-index N`: only that resource is listed or fetchable and there is no switch (the trace header records the pin). The model never supplies a URL or path. Fetch safety: CKAN targets and every redirect hop (followed by the harness, max 5, each re-checked) must be http or https and must not resolve to a loopback, private or link-local address; a local path is allowed only as the human-supplied reference; the final URL is traced. Streams; a progress line every 10 MB goes in the trace. A network or download failure, or exceeding the cap, returns `status.download_failed`; a refused index, URL or redirect hop does not | 200 MB enforced while streaming, and up front if the server declares a size (1,956 of 2,440 pool datasets publish no size) |
| `list_members` / `list_sheets` | Archive members; workbook sheets with dimensions. `list_members` returns `archive_has_no_tabular_member` only when code can show it: at most 20 members, none with a tabular extension, none whose first bytes look like delimited text, JSON, a workbook or an archive | 50 entries; 1 GB decompressed per member, counted while decompressing (a zip header can lie; a gz has no size at all) |
| `sniff` | Magic bytes, encoding, delimiter guess, raw head. Also classifies the FILE (not one archive member) with a fixed reason code in `status` when it is not tabular or unsupported: `empty_file`, `pdf_document`, `html_page`, `xml_unsupported`, `binary_unknown` | 12 lines x 300 chars |
| `read_table` | Runs a parametric reader; returns headers, row count, the first TRAINING rows, the applied layout in code's own words, and `raw_top` (the first 12 raw rows, numbered as `skip_rows` counts them, never held out, shown on success and on a failed read), or the error. Later tools use the reader of the latest successful call | 20 rows x 40 cols x 100 chars |
| `profile` | Per-column fill, distinct count, shapes, over training rows | 60 columns; distinct counts above 200k marked `capped` |
| `check_unique` | Uniqueness of named columns over training rows (streamed; 128-bit key digests, so a collision is not a practical concern) | one answer |
| `sample` / `search` | Rows by strategy (head, spread, random, by_column) or regex, from the training partition only | 30 / 10 rows |
| `try_transform` | Real engine on up to 1,000 TRAINING rows (spread): parse rate and rejects. Levels W and P (step 4a; optional `when`); level G is step 4 | 5 examples |
| `define_transform` | Level-G generated transform (section c) | 40 lines of code |
| `validate` | Structural, held-out and meaning checks on the held-out rows through the config's own reader, plus two checks over the WHOLE file (unaccounted columns, `record_id` uniqueness), an EVIDENCE state per mapped field and envelope setting (`held_out` / `training` / `unverified`; step 3b item C — see below), and meaning warnings when an ABN / ACN field fails its checksum on more than 2% of judged values (a column mixing real identifiers with look-alikes of the same length), when a MAPPED column has a generated placeholder header (`_blank_N`, `Unnamed`: the header rows may be misread; the text names `skip_rows`, `header_rows` and `skip_rows_after_header`), and when `header_rows` is 0 and the first data row looks like a misread header (`header_like_first_row`: distinct all-text cells, most columns below them numeric or date-like) | 6,000 chars; at most 6 calls per run; example values on the first call only, counts after |
| `critique` | Separate model call, fresh context: raw rows beside their observations, reviewed against the SAME mapping rules text the agent has (`agent_prompt.MAPPING_RULES`). The config summary it sees includes `valid_from` / `valid_to` / `needs_transform` (step 3b item D2); for a field with no populated example among the sampled rows, up to 2 populated TRAINING rows are added, marked as such | 10 examples |
| `ask_human` | Question goes into the packet. On a terminal the run waits for the answer (the wait is excluded from the time budget and traced as `human_wait_seconds`); without a human the model is told so. The answer is data in a `<data>` block, never approval: only `approve` approves | 1 per run |
| `finish` | Declares an outcome | see below |

**Enforced by the harness**
- `fetch` accepts no argument except `resource_index`; a URL or path found inside a cell is never fetched.
- The held-out split is made when a table is first read (a seeded reservoir of up to 300 rows, or half the rows if fewer than 600) and is stored as row FINGERPRINTS (a hash of the raw cells), so a later read with other options still excludes them. `read_table` (first rows), `sample`, `search`, `profile`, `check_unique` and `try_transform` see training rows only; only `validate`, `critique` and the harness's own hooks read held-out rows. If the first read was a wrong parse and fewer than half the fingerprints match a later parse, the split is re-made and the tool says so. Identical rows share a fingerprint, so copies of a held-out row are all held out. `validate` shows example values on its first call only (later calls: counts, with raw values scrubbed from reject reasons), which limits what repeated calls can reveal (counts still carry some information; the cap bounds it).
- **Protected top rows (step 3b, item B).** The first 12 raw rows of the file (`PROTECTED_ROWS`, a layout-free read so it holds whatever `skip_rows` / `header_rows` end up being) are NEVER candidates for the held-out set; a data row identical to one of them is protected too. This closes two leaks found in the dev draw: a title or the real header row could land in the held-out set and be hidden from the agent for the whole run, and `sniff` already showed the first 12 raw lines regardless of the split, so a row shown there could later be tested as "unseen". `read_table` always returns these 12 rows as `raw_top`, numbered as `skip_rows` counts them, on success and on a failed read; no prompt hint and no finish gate enforce this (a hint already existed and Sonnet never followed it). A file with fewer than 10 rows eligible after the top is protected gets NO held-out split at all (`held_fp` empty); its fields are judged on training evidence instead (item C) and the packet says so.
- Every tool has a per-call time limit (`ToolSpec.timeout_seconds`, default 60 s; sniff and list tools 20-30 s, `critique` 150 s). `fetch` (a download) and `ask_human` (a human) have none. On POSIX in the main thread a SIGALRM timer interrupts the tool, including a runaway regex (measured: `(a+)+$` was stopped at the limit); everywhere the row loops also check a cooperative deadline. A timeout is an error result. On Windows only the cooperative check exists, so a catastrophic regex is not interrupted there. A regex in a config (`regex_extract`, `regex_replace`, `when.matches`) also runs under its own 1 s per-value timer, nested inside the tool timer (same Unix-only limit), see section c.
- `finish` runs `validate` ITSELF (code) on the submitted config, so "validate has not run" is never a refusal reason; it
  refuses only if validation fails. It also needs a `critique`, with one exception, the NARROWING rule: a config that only
  removes fields, abstains fields or moves columns to `unmapped` compared with a critiqued config needs no new critique (it
  cannot add an error). Adding a field, changing a field's source, canonical field, transforms or group, changing the reader,
  `record_id` or `observed_at`, or adding / altering `valid_from` / `valid_to` needs a critique on that config; dropping
  `valid_from` / `valid_to` is a narrowing. Reason text and `source_reliability` (never shown to the critic) may change freely,
  and a field's `mapping_confidence` may go DOWN but not UP after the last critique. With no critique calls left, the refusal states the two options: revert that change,
  or abstain the field. Issues from every critique the finished config narrows accumulate; an issue about a field that is no
  longer in the config drops. The gate is "ran, and each issue fixed or answered", not "critic satisfied". Every refusal names
  the exact next call. Malformed `answers` or `abstentions` are refused with a sentence (and the shape), never an exception.
- A config outcome must map at least one field: `finish` refuses a config with none (or a code abstention that would remove every
  field), naming the next call. The `critique` result says how many critique calls remain; after the last it says the agent can
  only remove or abstain fields or answer the remaining issues (text written by code).
- Each critique issue carries a SEVERITY from the critic: `blocking` (the mapping states something the source does not
  support) or `advisory` (everything else; the critic is told to choose advisory when unsure, and that a mapping which follows a written mapping rule is not blocking because of a caveat about some values). At a forced end only fields
  with a blocking issue are abstained; fields that pass validate with only advisory issues stay and the issues go in the
  packet. An issue with no severity counts as blocking. The same rule holds at an ordinary `finish`: every BLOCKING issue must
  be fixed or answered in `answers`, or the finish is REFUSED with the issue text (2 such refusals per run; they do not count toward
  "refused twice in a row"). The next finish is then accepted with outcome `needs_review` and the field abstained by code;
  `approve` refuses a `needs_review` config unless `--allow-needs-review` is passed (the outcome is stored in
  `validation_summary.outcome`). Unanswered ADVISORY issues
  leave the field in place and are listed in the packet and in the finish event's `open_advisory`. After code abstains fields the
  harness re-validates (code) but does not re-critique: removing fields cannot add an error.
- **Outcomes are defined by who ended the run.** `validated_config` = the agent's own `finish` was accepted by the gate with no blocking issue open (fields
  left out are in `unmapped` or `abstentions`). `needs_review` = the gate accepted a finish only after refusing it twice for open blocking issues (the fields are abstained). `partial_config`
  = the HARNESS ended the run (turns, dollars, time, repeated refusals) and at least one field passed validate. `incomplete` =
  the harness ended it and no field did, or no config existed. The model can declare only `validated_config`,
  `no_business_entities` and `could_not_read`. How much a config covers is a separate measure (benchmark columns
  `mapped_count`, `abstained_count`, `unresolved_blocking`: blocking issues the run ended without fixing or answering), so a thin
  `validated_config` is visible. Business-entity rule 18 (both prompts, built on section d's people rule so they cannot
  drift; a test compares the wording): `no_business_entities` is for rows that are neither organisations (any ontology
  entity_type, schools, charities and government bodies included) nor individuals who count as entities (section d: a person-like
  name WITH ITS OWN valid ABN may be an entity, `entity_type` stays `unknown` unless a source states otherwise); a name column the
  data does not label registered, licensee or supplier maps to `entity.trading_name` at 0.6 or lower, never left unmapped for that.
  Not settled by this: whether the agent chose well what to drop (that needs the human review).
- **Register exception (step 3b, item F; both prompts, rule 5).** A name maps to `legal_name` when the data labels the column
  as registered/legal/licensee/supplier, OR (5b) the dataset is a register kept by a regulator or licensing body and the row's
  subject is the person or organisation the register lists as HOLDING a licence, registration, accreditation or approval (the
  holder, not a premises, venue or product the licence covers); without a label, `mapping_confidence` is 0.7 or lower under 5b.
  Rule 4 points individuals at 5b instead of restating it. Prompt wording only: NO code cap enforces the 0.7/0.6 numbers and no
  header-word-list check exists yet. DEFERRED, not built: a code cap on `legal_name` (0.7) / `trading_name` (0.6) unless the
  source header carries a matching word from two short fixed lists, applied where `field_confidence` is computed.
- Harness constants, not tool settings: `critique` at most 2 per run, `ask_human` at most 1, `validate` at most 6 (a tool
  spec may only tighten them). The harness's own critique inside a forced end is not one of the model's rounds.
- Whole-file checks (one streamed pass per config, cached): a column may be ignored only if it is empty in the whole file (a column empty in the held-out rows but filled elsewhere must be mapped or listed in `unmapped`); a `record_id` made of columns FAILS validation on any repeated key, or on more than 1% blank keys; `hash_row` fails only if more than 1% of rows are exact repeats of another row. This is code: it holds whatever the model did or did not check. A failing id is a hard failure but not a field, so abstaining cannot fix it (a run that cannot fix it ends `incomplete`).
- A finish refused only because `answers` or `abstentions` was malformed is a FORMAT refusal: the first 3 per run do not count toward "refused twice in a row"; from the 4th they do. The `finish` description shows the shape of both lists (generic ids and words).
- "Finish refused twice in a row" means two consecutive refused `finish` calls, including a refusal because
  re-validation after abstention still failed; any other tool call resets the count.
- `no_business_entities` requires `read_table` and `profile` to have run. `could_not_read` requires evidence CODE has: two FAILED
  `read_table` calls, a failed download (`status.download_failed`), or a `sniff` / `list_members` result carrying one of the fixed
  reason codes (the model's own statement is never enough; a later successful read does not cancel the evidence; switching
  resource clears it). Successful reads and refused indexes do not count as failed reads.
- Tools receive a deep copy of their arguments (the model's original is what the gate hashes, the trace records and
  replay compares), and hooks receive copies of the config. A tool that raises, returns something that is not a
  well-formed result, or reports a non-finite or negative cost is turned into an error result, never a crash; exception
  text reaches the model only inside `<data>`. A model-calling tool's cost is taken from the call log, not from what
  the tool reports. A tool's reported download time is capped at the time the harness measured for the call.
- Code computes `field_confidence` (lower of model confidence, parse rate and an EVIDENCE cap; level G capped at 0.8),
  `derivation_level`, and abstention.
- **Evidence states (step 3b, item C).** Each mapped field, and each per-row `observed_at` / `valid_from` / `valid_to`,
  gets one of three states, set by code, never by the model's own statement (the same principle as `could_not_read`):
  `held_out` (5 or more judged values on held-out rows: no cap beyond the usual parse-rate floor); `training` (fewer
  on held-out, but 5 or more over held-out plus training rows combined: same 90% floor on the combined rate, hard
  failure below it, `field_confidence` capped at 0.8); `unverified` (fewer than 5 judged values anywhere in the file:
  capped at 0.5, already below Part 4's 0.6 low-trust line, hard failure only if no value ever parses). A fourth state, `asserted` (step 4a), is set for a `constant` field: its value is
  stated by the config, so its 100% parse rate is not evidence; capped at 0.5. Training
  evidence is scanned only for fields the held-out rows cannot judge alone, through the same `apply_transforms` +
  ontology-guard path the engine uses. The config, the packet ("Fields without enough held-out evidence", with
  whole-file counts and training examples), the review sheet and the benchmark (`fields_training_evidence`,
  `fields_unverified`, `identifier_evidence`) all carry the state. An unverified field may stay in a
  `validated_config`. DEFERRED to step 7 (not built): an ABN whose evidence is `unverified` may not support a Part-3
  link above the loose tier.
- **Raw rows and the layout sentence in the packet (step 3b, item E).** The review packet's new "Reader and record
  settings" section (see D1 below) shows the reader options, the applied layout in words written by code (which raw
  row gave the names, which were dropped, where data starts), and the first 12 raw rows of the file (reusing
  `raw_top`/`raw_head`: never held out, so always safe to print). Column labels written by the model were considered
  and rejected: untrusted label text would be promoted into config metadata with no code check that it is right, and
  items A and B already remove the two causes seen in the dev draw (a merged or off-by-one layout, a hidden header).
- **`valid_from` / `valid_to` visibility and strictness (step 3b, item D).** A per-row `observed_at` / `valid_from` /
  `valid_to` (one with its own `source`, not `from_metadata`) now gets the same `FieldStats` tracking as a mapped
  field in `run_rows`: rows, blank, ok, reject, reject reasons and reject records (previously a failed `valid_from` /
  `valid_to` parse was silently dropped, the stamped value staying `None`; the value stamped on an observation is
  unchanged by this, only its visibility is). The 90% floor and the evidence states (item C) apply to them too. The
  packet's "Reader and record settings" table and the review sheet show `record_id`, `observed_at`, `valid_from`,
  `valid_to` with source, transforms, parse rate, evidence and examples (the round-1 packet showed this; the round-2
  packet had dropped it). `valid_from` / `valid_to` are abstained by code DELETING the config key (there is nothing
  to move to `unmapped`); `observed_at` is never abstained this way, since every record needs one, so a failing
  `observed_at` stays a hard failure that must be fixed. Rule text (both prompts, `agent_prompt.MAPPING_RULES` rule
  10): `valid_from` / `valid_to` may be mapped only from a column that says when the entity's OWN registration,
  licence, accreditation or status started or ended; a date of an event or transaction the row records (a contract,
  an order, an invoice, a payment, an application) is not when a name, identifier or address became true and is left
  unmapped. This reverses the round-1 practice in one approved config (a contract's commencement/expiry dates stamped
  on supplier-identity claims); it takes effect only when the six sources are RE-ONBOARDED in step 5 — no round-1
  config, output or reject file was touched to make this change, and a read-only measurement on the two round-1
  sources that set these fields (`asic_credit_licensee`, `wa_tenders_awards_2023_24`) found the stats-and-rejects
  tracking itself adds zero new reject entries on their existing data (both already parse cleanly).

**Chosen by the model:** tool order, reader options, what to inspect, which transforms to use, when to abstain,
when to ask.

**Terminal outcomes:** `validated_config` (the agent's own finish was accepted), `partial_config` (harness-ended with at
least one field passing validate), `no_business_entities` (evidence cited), `could_not_read` (verified evidence, with the reason),
and `incomplete`, which only the harness can declare, with the reason: the run ended (budget exhausted, repeated refusals,
replies without a tool call, model refusal) before any config was proposed, OR a config was proposed but still fails
validation after the harness abstained its failing fields, OR a forced end left no mapped field.

**Budget.** 40 model turns (every model reply counts, text-only ones and the max_tokens retry included, and the retry
is itself checked against the budget, so there is no turn 41; a turn makes at most one tool call; a `finish` on the last
budgeted turn still goes through the gate), $1.00, and 4 minutes of wall-clock excluding download (the trace shows download progress).
At 80% of any limit the harness tells the model to wrap up, inside the next tool result (a text block after tool
results can produce an empty reply). At 100%, or when `finish` is refused twice in a row, the harness finalises
itself: validate, abstain on failing fields, one critique (only BLOCKING issues abstain a field), write the packet, outcome
`partial_config` (or `incomplete` if no config was ever proposed or no mapped field is left). No budget burn. The packet hook
never creates an `approval.json` (it only resets an existing one); only `approve` creates one.

## c. Transforms and readers

**Three levels, logged per field as `transform_level`.**

| Level | What | Notes |
|---|---|---|
| W | The existing 12 whitelisted transforms | |
| P | Parametric primitives: `regex_extract`, `regex_replace`, `template`, `map_values`, `split`, `constant`; also any field with a `when` (step 4a) | `constant` tagged L3, evidence `asserted`, capped at 0.5 (under Part 4's 0.6 line), allowed only for `address.state` and `address.country`, as the field's only transform, with one anchor column |
| G | Generated Python | Accepted only after `try_transform` shows W and P stay below 90% parse rate |

Step 4a rules (code, `src/engine/transforms.py`, `config.py`, `extract.py`): text in a `template` or `repl` may hold separators and
group references only, never a letter or digit, so neither can write a word the source does not hold; a `template` with some parts
blank is rejected (`template_missing_part`), all blank is absent. Regex safety: pattern a string of at most 200 characters that
compiles (config time, a structural error); at run time one 1 s timer per value (SIGALRM, Unix main thread only, nested inside
the tool timer, which wins if it would fire first), a timeout is `Reject("regex_timeout")`, a pattern is switched off after 20
timeouts, an uncompilable pattern is `Reject("bad_pattern")`, never a crash. `when` on a field: `{"column", "equals": [..]}` or
`{"column", "matches": regex}`, judged per row alone (no order); not met = skip `when_not_met`, not a reject, not in the parse
rate; it is part of the field's definition for the critique gate.

Preference order is W, then P, then G. The packet shows the level per field; the benchmark reports how often G was
needed. Recurring G transforms are listed by a `promote` report for the human to move into the whitelist.

**Readers** are hand-written and tested; the agent only sets options.

| Reader | Options |
|---|---|
| delimited | encoding, delimiter, quote, `skip_rows`, `header_rows` (0, 1 or n merged; upper rows filled rightwards over merged cells), `skip_rows_after_header` (step 3b item A: raw rows dropped AFTER the header and before the data — label or note rows under a real header; a count like `skip_rows`; needs `header_rows` >= 1; default 0, so every existing config reads identically), `skip_footer_rows` (last n non-blank rows), `drop_empty_columns` (blank-header columns that are empty in the first 1,000 rows) |
| xlsx | sheet, `skip_rows`, `header_rows`, `skip_rows_after_header`, `skip_footer_rows`, `drop_empty_columns` |
| xls | same options as xlsx (legacy format; adds the `xlrd` dependency) |
| json | `records_path`, `flatten_depth` (default 1), `ndjson` (GeoJSON via `records_path: features`) |
| archive | `archive: zip\|gz`, `member`; read as a stream, never extracted; dispatched to the readers above |

`skip_rows_after_header` is refused for json (there is no header row to drop rows after) and with `header_rows: 0`
(there is no header at all; use `skip_rows`).

**Step 2 requirements carried from the step 1 review (built in step 2):** a per-call timeout for every tool except a
download and a human wait (section b); the `fetch` tool enforces the 200 MB cap while streaming and reports
`download_failed` and the final URL; tool results follow the status contract in `tools.py` (dataset content only in
`payload`, never in `text`). The round-1 option `header_row` is still accepted; the six round-1 sources and the seventh read
identically through the new reader (checked row for row against the committed round-1 reader).

Files over 50 MB are streamed (delimited, xlsx and NDJSON, constant memory; smaller files are cached in memory after the
first read). A plain JSON array and an .xls workbook cannot be streamed and are loaded whole; a workbook inside an archive
and any .xls are capped at 200 MB. Decompressed bytes of a zip or gz member are capped at 1 GB while counting. Not in the core: PDF, HTML, parquet, XML, reshape. One run onboards one table; cross-
table joins are out of scope.

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
   401 MB CSV, carries ACN, ABN, type, status, registration date and former-name rows. Business Names: 72 MB zip /
   247 MB CSV, business name to holder ABN. A generic engine row filter keeps only rows whose ABN, ACN or name key
   appears in our mentions. For the six, the trimmed result is committed with attribution. For a NEW source,
   `resolve` re-runs the row filter over the full registers on disk (`data/raw/reference/`); the time on the 401 MB
   file is measured at build step 6 and recorded in the runbook (not yet known).
4. **ABR lookup (stretch, not on the critical path).** Only for ABNs in candidate links and profiles, git-ignored
   cache, terms saved to `docs/abr_terms.txt`; the method name is read from the live WSDL, not from memory.

**Register bridging uses registered, current names only** (Companies: current-name rows; Business Names: status
Registered). A name matching more than one holder is **refused**, not loose.

**Offline fallback = the two ASIC registers.** They lack non-company entity types, ABN status and location. With
no internet the matcher runs with ABR features marked absent and the output says so.

**Matcher m2.0** (hand-set tiers; accept 0.80, loose 0.60). Scores are calibrated by the hand check, not fitted.
**Promotion rule:** T3c and "T4 exact name plus postcode" START in the loose band (capped below 0.80). A tier moves
to accepted only after its hand-check stratum is clean (at least 15 rows labelled, 0 wrong, at most 1 unsure); the
matcher version is bumped and the promotion plus its evidence is recorded in DECISIONS.md.

| Tier | Evidence | Confidence |
|---|---|---|
| T1 | Equal ABN or ACN, names agree by rarity-weighted overlap | 0.98 |
| T1r | Equal identifier, names differ, a register or ABR name history confirms both names | 0.95 |
| T2 | ACN inside ABN, names agree | 0.88 |
| T3c | No-ABN record bridges to exactly one registered current holder AND a second independent hit agrees (licensee to Companies, trading name to Business Names, same ABN) | 0.70, loose until promoted (0.88 after) |
| T3 | Single uncorroborated register hit on a unique registered current name | 0.65 (loose) |
| T4 | Exact name plus postcode / plus state / both companies with no location | 0.70 loose until promoted (0.85 after) / 0.70 / 0.65 |

Refused: identifier match with unconfirmed name conflict, a name matching more than one registered holder, generic
name, different ABNs, person-like on both sides without an equal ABN. Address evidence is postcode + state only.

**Graph**

| | |
|---|---|
| Nodes | mention, register record, entity (derived), person, trust |
| Edges | `same_as` (the link table), `renamed_to` (register or ABR name history), `trustee_for` (ATF patterns), `nominee_of` (person listed under a company's ABN, the QBCC pattern) |
| Each edge stores | stable `edge_id` (endpoints + type, not the version), tier, band, `relation_confidence` / `link_confidence`, raw evidence features, evidence sources with dates, `matcher_version`, thresholds, `previous`, `human_label` |

**Rescore** stays a pure function over stored evidence (no sources, no extractor, no model). New: it refuses to
write if a human-labelled Y would be demoted or a human-labelled N promoted.

**People**
- A person-like name WITH ITS OWN valid ABN may be an entity (sole trader), linked only on equal ABN with agreeing
  names. `entity_type` stays `unknown` unless a source states otherwise.
- A person with no ABN, or listed under a company's ABN (the ABN belongs to a company-like name or a registered
  company), is an edge endpoint only (`nominee_of`, `trustee_for`) and never a profile.

**Profiles** count ANY onboarded source, not only the six. Two types, always labelled:
- `cross_source`: mentions from two or more onboarded sources linked by `same_as`.
- `single_source_register_confirmed`: one source plus a register record joined by a `same_as` link; the link's band
  (`accepted` or `loose`) is shown on the profile. Register and ABR records enrich fields but never count as a second
  source. Components made only of people with no ABN get no profile.
So a new dataset that contains a registered company always ends with a profile, at the trust level its link earned.

**Hand check.** Round-1 labels carry over wherever both records are unchanged (same source, row hash, name and
identifier); expected 45 to 50 of 50 survive. They become the frozen regression set and the ABN-equal stratum.
New labelling samples only new strata: register-bridged, no-ABN, sole-trader (person with own ABN), and ABR-assisted
if built; 15 rows each, so 45 to 60 rows, about 70 to 90 minutes. Round-2 precision is labelled non-independent
(the registers are matcher features, and ABN Lookup shows ASIC business names); no-ABN links are judged by hand.

## e. Benchmark

**Frame.** The 2,440-dataset pool minus the six (measured). Reachable through the core readers: 1,140 plus 52
XLS-only = 1,192. Zip only: 87 (reachable if the members are readable). XML only: 37 (out of core). No tabular file
(PDF, shapefile, web services): 856. No resources: 268.

**Draws** (at most one dataset per publisher-and-title family; siblings of the six flagged):

| Draw | Seed | Shortlist ranks 7-50 | Pool, stratified by format | Injection case |
|---|---|---|---|---|
| dev (fix against it) | 1 | 6 | 5 | 1 |
| final (run once, unchanged) | 2 | 8 (rank 38 excluded) | 7 (one from the no-tabular group) | 1 |

The final draw runs once per model (Haiku and Sonnet) at a recorded commit.

**Harness (step 3).** `src/benchmark/`: `draw.py` (seeded, written once and never adjusted; the six, `find_by_lia_band` and their
siblings are excluded; seed 2 refused unless `--final`), `run.py` (a subprocess per run; per-run dollar limit, session spend limit
checked before each launch, wall-clock kill; Haiku or Sonnet), `report.py` (read from the trace, never the console; blank human
columns; review sheets; `compare` with coverage and self-agreement) and `injection.py` (verdict by canary checks alone; the
comparison with the clean copy is information). Output goes to `outputs/benchmark/`. Frame counts match this section except
no-tabular 875 (here 856) and no-resources 249 (268).

**Per run:** outcome, `has_name` (a name field mapped), `has_identifier` (ABN or ACN mapped), tool calls, cost, wall-clock, download seconds and bytes, reader, W/P/G counts, fields
mapped and abstained, open critique issues, sandbox capabilities (empty until step 4), model.

**Verification.** One sheet, `handcheck/benchmark_review.csv`: for each business-bearing dataset one row per mapped
field (three raw to value examples, level, "wrong?"), plus "outcome correct?" and "key field missed?". About 5
minutes per dataset. Non-business verdicts are spot-checked.

**Published (final draw only, dev rate beside it):** validated; validated with 0 wrong fields on review; key field
missed; non-business correctly declared; could not read by reason; injection pass or fail.

**Known results (not tuned for).** `address.locality` is never mapped on find-by-lia-band (round 1 derived it with `regex_extract`).
**Dev draw, seed 1, seven passes** (`outputs/benchmark/dev_seed1/compare.md`): a, b Haiku, old outcome definition; c Haiku, s Sonnet,
new definition; d Haiku, t Sonnet, after the round-3 changes; e Haiku, after rule 18 was aligned with section d and the name rule
and placeholder-header warning were added. Validated / no business entities / could not read (partial 0 from c on): a 3/2/2 (+4
partial), b 4/2/2 (+3), c 6/3/2, d 6/3/2, e 7/2/2, s 7/2/2, t 7/2/2. Validated configs with name and identifier / name only /
identifier only / neither: c 4/0/2/0, d 4/1/1/0, e 5/1/1/0, s 6/1/0/0, t 5/2/0/0. Self-agreement (outcome; outcome and fields):
Haiku c-d 9 and 7 of 11, d-e 10 and 6, Sonnet s-t 11 and 8. The individual-ABN file (individual auditors, 16% with an ABN) was
`no_business_entities` in d (rule 18 as first written) and validated in c, e, s and t. Cost per run: Haiku $0.006 to $0.008,
Sonnet $0.077 to $0.097. The injection pair passes in every pass since the verdict became canary-only. Human sheets:
`handcheck/benchmark_review_dev1{d,e,t}.csv`.

## f. Demo runbook

| Case | Works | Degrades |
|---|---|---|
| My machine, internet | Everything | Nothing |
| My machine, no internet | Extract, resolve, rescore, profiles, trace replay | No LLM, so no onboarding of a new dataset (phone hotspot is the backup) |
| Their machine, internet | Onboarding with their key and model access | Register-confirmed profiles need the registers on disk (151 MB of zips, plus the filter pass); without them the new dataset links by identifier and name only; sandbox weaker on macOS/Windows |
| Their machine, no internet | Tests and committed outputs | A walkthrough only |

The register row-filter time on the 401 MB file is recorded here once measured (build step 6).

## g. Demo path

Dataset A contains registered companies; dataset B contains no businesses. Times marked "target" are goals, not
measurements; "to measure" is filled in during the build.

| Step | Command | Time | What the audience sees |
|---|---|---|---|
| 1 Onboard | `python -m src.part2_agent.onboard --mode agent <url or file>` (`--mode pipeline`, the round-1 pipeline, is still the default until build step 10) | target 4 min excl. download | Live trace: fetch progress, `sniff`, `read_table` headers, `profile` shapes, `try_transform` parse rates, `validate` pass, `critique` issues answered, outcome `validated_config`. For B the trace ends at `no_business_entities` with the cited evidence, and the demo stops there |
| 2 Review | open `configs/<source>.review.md` | 1-2 min (human) | Fields with raw to value examples, transform level W/P/G, generated code if any, unmapped columns with reasons |
| 3 Approve | `python -m src.part2_agent.approve <source_id>` | 1 min | One question: which numbers are wrong; approval stores the hash (covers any generated code) |
| 4 Extract | `python -m src.engine.extract <source_id>` | target under 10 s | Rows, observations, rejects with reasons |
| 5 Resolve | `python -m src.part3_resolve.run` | to measure (registers filter on 401 MB file + seconds) | Links by tier and band, refused pairs with reasons, edges by type |
| 6 Profile | `python -m src.part4_profiles.show <source_id>` | target under 2 s | A profile for the new dataset: fields with provenance and confidence, the register record that confirmed it, the profile type and link band. For A it always shows at least one profile |

## h. File layout

**Changed:** `src/llm.py` (tool-use call, history caching); `src/part2_agent/` (`onboard.py`, `fetch.py`,
`packet.py`, `approve.py` numbers every setting and shows generated code); `src/engine/` (`readers.py` incl. xls,
`transforms.py`, `config.py`, `extract.py`: row hash, row filter, streaming); `src/part3_resolve/` (`features.py`,
`score.py`, `run.py`, `rescore.py`, `handcheck.py`); `src/part4_profiles/build.py`; `requirements.txt` (`xlrd`).

**New:** `src/part2_agent/` (`loop.py`, `tools.py`, `guard.py`, `agent_tools.py`, `agent_table.py`, `agent_hooks.py`, `agent_prompt.py`); `src/engine/` (`sandbox.py`, `custom.py`);
`src/common/names.py`; `src/part3_resolve/` (`idf.py`, `registers.py`, `graph.py`, `abr.py`);
`src/part4_profiles/show.py`; `src/benchmark/`; `demo/RUNBOOK.md`; `docs/abr_terms.txt`; new tests.

## i. Build order (no hour budget; time is logged from actuals)

1. Loop, tool-use wrapper, guards, outcomes, trace.
2. Tools and parametric readers (incl. xls).
3. Benchmark harness, injection case, dev draw and fixes.
4. Primitives, sandbox, custom execution, tests.
   4a. BUILT (v2.13; scope: the three transforms `regex_replace`, `template`, `constant` and the condition are all 4a; step 4 keeps level G): a CONDITIONAL mapping, "apply this mapping only where another column equals a value" (and its
   `try_transform` / `validate` support). The dev draw found a mixed identifier column: real ABNs for the rows a second column
   labels as ABN, look-alike internal ids of the same length for the rest. Without a condition the look-alikes that fail the
   checksum are rejects and about 1 in 89 of them passes by chance as a false ABN (about 0.05% of that file's ABN observations);
   the identifier-checksum warning (round 3) now names `when` as the fix.
5. Re-onboard the six, your approvals, extract. The step 3b `valid_from` / `valid_to` strict rule (section b) changes
   what two round-1 configs produce (a contract-dates config loses that mapping); the reject-file difference it makes
   is measured here, not before.
6. Registers (streaming, row filter, two approvals), bridging; time the 401 MB filter pass.
7. IDF, m2.0, graph, rescore gate, profiles (both types). DEFERRED from step 3b: an ABN whose evidence is
   `unverified` (section b) may not support a link above the loose tier; a code cap on `legal_name` / `trading_name`
   confidence by header word (section b, rule 5's register exception) is prompt-only until this step.
8. Round-2 hand check (new strata); tier promotions recorded in DECISIONS.md.
9. Final draw on both models; your review sheet.
10. Write-up, README, runbook, rehearsal.

Stretch: ABR lookup.

**Cut order when time is called:** (1) stretch items; (2) hand check down to 10 rows per stratum; (3) `renamed_to`
edges; (4) Business Names register only. Never cut: enforced validate and critique, the sandbox tests, the
unchanged final draw, the hand-judged no-ABN stratum, the human gate.

## j. CTO feedback to design

| Feedback | Answered by |
|---|---|
| Agents with tools, not rigid; ingest a random dataset live | Tool loop (b); three transform levels and generated code (c); parametric readers incl. xls; four clean outcomes; the benchmark's published final-draw rate (e); the demo path (g) |
| More creative entity resolution, connect more data points | Recovered WA and QLD names; register bridging with unique registered-current-name rule; name history; rarity-weighted names; typed graph edges; sole-trader and nominee handling; register-confirmed profiles for any new source (d) |

## k. Open questions and risks

1. No internet means no agent: the largest demo risk. Recommend a hotspot and asking Chath; no local-model path.
2. The critique gate can pass a wrong mapping (the critic shares the agent's blind spots); the benchmark's human
   review measures this.
3. "0 wrong fields" rewards under-mapping, hence "key field missed".
4. Sandbox on Windows has no CPU limit, only the wall timeout.
5. Full independence is unachievable: ABN Lookup shows ASIC business names. We report matcher evidence versus
   labeller evidence.
6. Carried labels are not a random sample of the new matcher's links: regression gate and unchanged stratum only.
7. Register-confirmed single-source profiles rest on one register match, not a second source; the profile type and
   link band are always shown. Loose-band profiles are lower trust by design.
8. The register filter over 401 MB per new source has unknown time; if it is slow, the demo needs a pre-built
   index (not in this design, would be a change).
9. Promotion of T3c and T4 depends on a clean 15-row stratum; if it is not clean they stay loose and name-only
   bridging contributes no accepted links.
10. Sole traders are linked only on an equal ABN; people with no ABN never become profiles, which loses some real
    businesses.
11. Cost estimate $8 to $10 for round 2; project spend will likely pass $10; we report the real number.
12. Sonnet may miss the 4-minute target; the benchmark will show it.
13. If the final draw crashes, publish as-is and report fixes separately.

## Change log

| Date | Version | What changed | Why |
|---|---|---|---|
| 2026-11-12 | 2.0 | Initial round-2 design: tool-using agent, three transform levels with sandboxed generated code, ASIC-register bridging, typed graph, generality benchmark, demo runbook | CTO feedback on the first submission: more agentic and generic ingestion, live demo on a random dataset, more creative entity resolution |
| 2026-11-12 | 2.0 | Approved with seven edits: profiles count any source and add a single-source register-confirmed type; T3c and T4-postcode start loose with a hand-check promotion rule; people rule (own ABN may be an entity, no ABN or under a company's ABN is an edge endpoint only); xls reader added to core; critique gate and "key field missed" kept; register bridging uses unique registered current names (ambiguous refused); 12-hour limit and hour estimates removed; Demo path section added | Owner review before building |
| 2026-11-12 | 2.1 | Build step 1 (agent loop, tool-use wrapper, guards, trace) and owner review: `tool_choice` auto with parallel calls off, plus a one-nudge rule for replies with no tool call; "finish refused twice in a row" defined as consecutive refusals; fifth, harness-only outcome `incomplete`; re-validate without re-critique after harness abstention; `finish` owned by the harness; `fetch` takes only `resource_index` (CKAN: resource list, pick by index; no model-supplied URLs; redirects followed); every model turn counts against the 40-call budget; trace header with input SHA-256, model and code version, resume refused on mismatch, REPLAY labels; transient API errors retried (max 3, traced); secrets redacted from trace and logs | Forced tool use is rejected by Sonnet 5.5; the owner required a refusal-on-mismatch trace, a single fetch rule, visible retries and no secret leakage; the live smoke test confirmed the request shapes |
| 2026-11-12 | 2.2 | Cost log: every call logged from now on is tagged `"round": 2`; untagged lines are round 1; the spend summary reports the rounds separately (round 1 by default); the 12 smoke-test lines were retagged round 2 | Round-2 model calls must not change the round-1 cost figures in the README and WRITEUP |
| 2026-11-12 | 2.3 | Independent review of step 1 applied. `incomplete` also covers a config that still fails after abstention; critique (2) and ask_human (1) limits are harness constants; trace header carries the limits and a hash of the system prompt, task and tool schemas, code version includes tool and hook modules, and resume is refused on any header difference or if a live event would be written while recorded events remain (the "replayed event no longer matches" wording is replaced by what the code actually checks, with its limits stated); fetch safety rule (http/https only, no loopback/private/link-local on CKAN targets and every redirect hop, final URL traced, local path only as the human-supplied reference); exact retried status codes, and round-1 `llm.call` keeps its own SDK retries; `could_not_read` counts failed reads and download failures only; tool isolation (copies, malformed results, costs from the call log, download time capped); per-tool timeout and fetch size cap recorded as step 2 requirements | Review findings: wrong results that blocked the demo (crash on malformed `answers`, redaction corrupting trace lines, tools editing their config in place) and rules the documents claimed but the code did not enforce |
| 2026-11-12 | 2.4 | Build step 2 (tools, readers, hooks, `onboard --mode`) and owner changes: `try_transform` runs on TRAINING rows only (was the held-out rows); only `validate` and `critique` read held-out rows; `validate` capped at 6 calls per run and shows examples on its first call only; held-out split stored as row fingerprints (survives re-reads, re-made if the first parse was wrong); 1 GB decompression cap counted while streaming for zip and gz; every redirect hop re-checked (test added); per-tool timeout (SIGALRM on POSIX plus a cooperative deadline; `fetch` and `ask_human` exempt); `ask_human` wait labelled `human_wait_seconds` in the trace, and its answer is data, never approval; one resource per run; `fetch` writes `metadata.json`; `progress` trace events; `--mode` default stays `pipeline`; level P stays in step 4 | Owner approval of the step 2 plan with changes; reader and tool limits needed concrete values |
| 2026-11-12 | 2.5 | Step 2 review fixes: `validate` checks unaccounted columns and `record_id` uniqueness over the WHOLE file (was the 300 held-out rows), so a repeated key is a validate failure whatever the model checked; malformed `answers` / `abstentions` are format refusals, counted separately (3 per run) from the "refused twice" rule, and the `finish` description shows the list shapes; known benchmark results recorded (missed `address.locality`, run-to-run variance, forced end abstaining every field) | Review of step 2: the live run's `Licence No` has a duplicate the held-out-only check could not see; a column empty in the held-out rows could hide an unmapped column; a formatting slip cost a finish refusal |
| 2026-11-12 | 2.6 | Finish-rule fixes (unattended session, phase A): `finish` validates by itself; the narrowing rule (removing, abstaining or unmapping fields needs no new critique); the last critique says no calls remain; every finish refusal names the next call; critique issues carry a severity (blocking / advisory) and a forced end abstains only blocking fields; a forced end with no mapped field is `incomplete`; the packet hook never creates `approval.json` | Live re-run of find-by-lia-band: the agent used both critiques, then was refused for a finish it could not fix and the harness abstained both fields on advisory issues |
| 2026-11-12 | 2.7 | Finish-rule fixes after three live rounds on find-by-lia-band: removing `valid_from` / `valid_to` is a narrowing and `source_reliability` is not a mapping (the refusal text now says how to undo a key change, not to remove it from `fields`); unanswered ADVISORY issues no longer abstain a field at an ordinary finish (only blocking ones do), matching the forced end; generic outcome wording in the prompt and the `finish` description | Round 0: 1 of 3 runs validated (a narrowing-rule defect and an ambiguous partial/validated definition). Retry 1: 0 of 3 (agents answered no advisory issues and lost fields). Retry 2: 2 of 3 validated with both target fields mapped, no refusals |
| 2026-11-12 | 2.8 | Build step 3 (benchmark harness, injection case, dev draw, two passes) and one harness fix: a config outcome must map at least one field (finish refuses a config with none, and a code abstention that would remove every field); known results recorded | Dev-draw pass A: a `partial_config` with no mapped field was accepted |
| 2026-11-12 | 2.9 | Review decisions: outcomes are defined by who ended the run (`validated_config` = the agent's own finish accepted; `partial_config` = harness-ended with a passing field; the model cannot declare `partial_config`), coverage columns added (`mapped_count`, `abstained_count`, `unresolved_blocking`, `resource_switches`); `could_not_read` needs evidence code has (two failed reads, a failed download, or a fixed reason code from `sniff` / `list_members`); the resource listing shows description and last-modified (untrusted data), one switch of resource per run (reason traced, at most two downloads, final hash pinned), `onboard --resource-index` pins a resource; the dev draw may run on Haiku or Sonnet; `compare` across passes | Owner review of the dev draw: partial vs validated was ambiguous, a run made two reads fail on purpose, a run picked the wrong resource |
| 2026-11-12 | 2.10 | Round-3 review changes: after the last critique `mapping_confidence` may go down but not up (a raise needs a critique); the critic reviews against the same mapping rules text as the agent (`MAPPING_RULES`) and is told a mapping that follows a written rule is not blocking for a caveat; business-entity rule 18 (organisations of any entity_type, including schools, charities and government bodies; `no_business_entities` is for people, places, assets, events, measurements); benchmark `has_name` / `has_identifier`, coverage counts and self-agreement; injection verdict by canary checks only (comparison is information); validate warns when an ABN / ACN field fails its checksum on more than 2% of judged values | Review of dev draw c and s: a name column kept as legal_name, a mixed-identifier column read as ABN, two clean runs of one file differing |
| 2026-11-12 | 2.11 | Rule 18 amended to section d (a person-like name WITH ITS OWN valid ABN may be an entity; `no_business_entities` is for rows that are neither organisations nor such individuals), wording shared with this document and guarded by a test; name rule next to rule 5 (an unlabelled name column maps to `trading_name` at 0.6 or lower, never left unmapped for that); validate warns on a mapped placeholder header (`_blank_N`, `Unnamed`); step 4a open item recorded (conditional mapping for a mixed identifier column) | Dev draw d: the first wording of rule 18 sent a file of individual sole traders to `no_business_entities` |
| 2026-11-13 | 2.12 | Step 3b (reviews/step3b_plan.md) built: (C) three evidence states per mapped field / envelope setting (`held_out`/`training`/`unverified`), capped at 0.8/0.5, computed by code, not a model statement; (B) the first 12 raw rows of a file are never held out, `read_table` returns them as `raw_top`, a too-small file gets no held-out split; (A) `skip_rows_after_header` reader option; (E) the packet shows the raw top rows and the layout in code's words, plus a `header_like_first_row` warning; no model-written column labels; (D) `valid_from`/`valid_to` get the same stats/reject tracking as a field, shown in the packet and the critic's config summary, abstained by deleting the key, and mapped only from the entity's own registration/licence/status date (reverses one round-1 config's practice, effective only on re-onboarding at step 5); (F) a register exception added to rule 5 (prompt wording only; a code cap on the confidence and header word lists are deferred); (G) `llm.chat` requests `display: "summarized"` thinking (confirmed live on both models, no extra token cost), shown in the replay line. DEFERRED, not built: the F code cap, an ABN-evidence rule for Part-3 linking (item C) | Planning session (reviews/step3b_plan.md) found: a run's held-out split hid the real header from the agent; a sparse ABN column passed validation with no evidence; `valid_from`/`valid_to` were invisible to the critic and the packet; an individual-register name rule conflicted with rule 5; the trace's thinking text was empty because display was never requested |
| 2026-11-13 | 2.13 | Step 4a (reviews/step4a_plan.md) built: `regex_replace`, `template`, `constant` and the per-field `when` condition; regex safety (200 chars, compile check, 1 s per-value timer, switch-off after 20, `bad_pattern` instead of a crash); literal text in `template` / `repl` is separators only; template with a blank part is rejected; `constant` capped at 0.5 (was 0.6) with evidence `asserted`; `try_transform` takes `when`; rule 19; scope: all four items are 4a (section i), step 4 keeps level G | Owner decisions 1-5 on the 4a plan |
| 2026-11-13 | 2.14 | Blocking-issue finish gate: a finish with an open BLOCKING critique issue is refused with the issue text (2 per run, not counted toward "refused twice in a row"); the next is accepted as outcome `needs_review` (fields abstained by code, `validation_summary.outcome` stored); `approve` refuses `needs_review` unless `--allow-needs-review` | Step 5 re-runs ended `validated_config` with blocking issues still in the config |
