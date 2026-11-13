# Step 4a plan: regex_replace, template, constant, and conditional mapping

Plan only; nothing is built. Source of truth: ARCHITECTURE.md v2.12 (b, c, i). Section 9 items are the owner's call, not the builder's.

## 0. Scope, and how a transform works today
- ARCHITECTURE i.4 lists the three transforms under step 4 (with the sandbox); i.4a is the condition only. This plan
  builds all four as 4a. Step 4 keeps level G (sandbox, `define_transform`, `custom.py`, `promote`).
- Defined: `f(value, arg)` in `engine/transforms.py`, registered in `CATALOGUE`; returns a value, `None` (blank), or raises
  `Skip` / `Reject`. Validated: `config._check_transforms`, shape by `agent_hooks.shape_errors`. Applied: `apply_transforms`,
  from three row loops (`extract.run_rows`, `agent_hooks.training_stats`, `AgentKit.t_try_transform`). Exposed: both prompts
  print `CATALOGUE` (`agent_prompt.py:12`; `llm_steps.py:24`, enum `:60`); the critic sees `transforms`; the gate compares `guard.field_def`.
- Found while reading (fixed by R1): `regex_extract` never checks its pattern. One that does not compile raises
  `re.error` out of `apply_transforms`: an error result in a tool, a crash in the finish hook and in extract.

## 1. Config syntax (one example each)
| What | Example | Behaviour |
|---|---|---|
| `regex_replace` | `{"name": "regex_replace", "arg": {"pattern": "\\s*\\([^)]*\\)\\s*$", "repl": ""}}`: `ACME PTY LTD (ACME PLUMBING)` becomes `ACME PTY LTD` | Every match replaced; no match leaves the value unchanged; an empty result is absent |
| `template` | `{"source": ["Street", "Suburb", "Postcode"], "transforms": [{"name": "template", "arg": "{1}, {2} {3}"}]}` | `{n}` is the n-th column of `source` (1-based). Must be the FIRST transform (in `join_nonempty`'s place); one column with `{1}` is allowed. Filled by one `re.sub` over `\{(\d+)\}`, never `str.format` |
| `constant` | `{"source": "Suburb", "canonical": "address.state", "transforms": [{"name": "constant", "arg": "VIC"}], "reason": "..."}` | `source` is an ANCHOR column: emitted only on rows where the anchor cell is not blank |
| `when` (on a field) | `{"source": "Identifier", "canonical": "entity.abn", "transforms": [{"name": "abn"}], "when": {"column": "Id Type", "equals": ["ABN"]}}` or `"when": {"column": "Identifier", "matches": "^\\d{11}$"}` | Section 5 |

- Literal text in a `template` or a `repl` may hold no letter or digit: separators and group references (`\1`) only.
  So neither can write a word the source does not hold; `constant` is the only way to state such a value (DECISION 5).
- `transform_level` (in `finalise_config`): P when the chain uses any of section c's six (`regex_extract`, `regex_replace`,
  `template`, `map_values`, `split`, `constant`) or the field has a `when`; otherwise W. Section c both says "W = the
  existing 12" and lists three of those twelve under P; this follows the P list. Labels only.
- `derivation_level`: `regex_replace` and `template` join `L1_TRANSFORMS`; a chain with `constant` is L3. Round-1 pipeline
  (`llm_steps.py`): prompt and schema enum keep the original 12 names (a fixed list), so the fallback behaves as before.

## 2. regex safety (`regex_extract`, `regex_replace`, `when.matches`: one helper in `transforms.py`)
- Config time (`_check_transforms`): the pattern must be a string, at most 200 characters (`MAX_PATTERN_CHARS` moves from
  `agent_tools.py` to the engine; the `search` tool imports it) and must compile; `repl` is checked by one substitution
  on an empty string. A failure is a structural-error sentence: validate reports it, finish refuses. Never an exception.
- Run time: each match or substitution runs under a 1-second timer (`REGEX_SECONDS`; SIGALRM, POSIX main thread, the
  mechanism `guard.tool_deadline` uses and section b measured on `(a+)+$`). The helper restores the outer tool timer's
  remaining time from `setitimer`'s return value. A timeout is `Reject("regex_timeout")`; the row loop continues.
- After 20 timeouts of one pattern in a process it is switched off: later values are rejected at once. Worst case about
  20 s per pattern, inside the 60 s tool limit; the parse rate then falls under the 90% floor, a hard failure.
- A pattern that fails to compile at run time (check bypassed) is `Reject("bad_pattern")`, not a crash. Not covered:
  Windows and non-main threads have no timer (the gap section b already states); only the length and compile checks apply.

## 3. template: missing or blank parts
- Every referenced column blank: absent for that row (existing `_is_blank` on a list source). Some blank, some filled:
  DECISION 2 (recommended: reject `template_missing_part`). Output is whitespace-cleaned.
- `{0}`, an index above the number of `source` columns, no placeholder, a letter or digit in the literal, or not first: structural error.

## 4. constant
- Only for `address.state` and `address.country` (section c), only as the field's sole transform, only with one anchor
  column, never in `observed_at` / `valid_from` / `valid_to`. The argument must be in the ontology's state enum, or two
  capital letters for country. Anything else is a structural error.
- Marked as not from the source, all by code: `derivation_level` L3 on every observation; `transform_level` P; a new
  evidence value `asserted` (a constant "parses" 100% by construction, so its parse rate is not used as evidence);
  `field_confidence` capped (DECISION 3). The packet's evidence column shows `asserted`. New rule 19 (agent and critic): only
  when the dataset's own metadata or title states the jurisdiction for every row; basis in `reason`. Not enforced by code: that the anchor is an address column.

## 5. Conditional mapping
- Syntax: optional `when` on a field (not on envelope settings): `{"column": <a column of the file>}` plus exactly one
  of `"equals": [strings]` or `"matches": <pattern>`. The column may be the field's own source (mapping by pattern).
  Both sides are whitespace-cleaned; `equals` ignores case (as `map_values`); `matches` is `re.search` under section 2.
  A blank condition cell means not met.
- Order: none (DECISION 4). Each field is judged alone, so the order of `fields` cannot change the result. One field per (source,
  canonical, group) stays the rule, so several accepted values go in one `equals` list. Two fields whose conditions both hold both emit.
- No condition met: the field emits nothing for that row, counted as a skip with reason `when_not_met`: not a reject,
  not in the parse rate, no reject-file line. The count shows in `skip_reasons` (validate, try_transform, packet). A
  condition never met anywhere, on a column that has values, is already a hard failure ("never produced a valid value").
- Code: one helper `when_met(field, row)` in `extract.py`, called after the blank check in the three row loops;
  `validate._referenced_columns` counts `when.column` as accounted for; `when` joins `guard.field_def`, so adding,
  changing or removing one needs a critique on that config.

## 6. Prompt, tool schema, finish rules (smallest edits)
- `CATALOGUE` gains three entries; the agent prompt prints them with no other change. CONFIG example: one `"when"` line.
- `MAPPING_RULES` (shared with the critic): rule 6 gains "if another column says which rows hold an ABN or ACN, add `when` so only
  those rows are mapped"; rule 1 gains "`regex_replace` and `template` remove or rearrange text, they never add words"; new rule 19.
- `try_transform`: one optional `when` property; the result text names the level; the "Level W only for now" refusal
  text goes. `identifier_warnings` text names `when` as the fix. Critic config summary and packet `_t` show `when`.
- `shape_errors`: `when` must be an object with a string `column`. `validate` / `critique` / `finish` schemas do not change.
  Finish rules: only the `field_def` change, no new refusal kind. The trace header hash changes, so old traces refuse to resume (by design).

## 7. Held-out split and evidence states
- The split does not change: the new transforms run only through `apply_transforms`, so `try_transform` sees training rows
  and only `validate` / `critique` see held-out rows. `regex_replace`, `template`: no extra cap; the ordinary states apply.
- A field with `when`: judged values are the rows where the condition holds; fewer than 5 on held-out rows falls to `training` (0.8) or
  `unverified` (0.5) by the existing rule. `_evidence_specs` and the `training_stats` cache key must carry `when`, or the scan judges excluded rows.
- `constant`: `asserted`, set in `finalise_config` before the parse-rate branches. Level G's 0.8 cap is untouched.

## 8. Build order and tests (new `tests/test_step4a.py`; run it and touched files only, full suite once at the end)
1. `transforms.py`: regex helper (cache, timer, switch-off), `regex_extract` moved onto it, three functions, `CATALOGUE`.
2. `config.py`: argument checks, `when` check, `derivation_level` L3, `L1_TRANSFORMS`, list source accepts `template`.
3. `extract.py`: `when_met` in `run_rows`; `validate._referenced_columns`.
4. Agent: `shape_errors`, `_evidence_specs` / `training_stats`, `finalise_config` (level, `asserted`, cap), critic summary,
   packet, `guard.field_def`, `try_transform`, `identifier_warnings` text, `llm_steps.py` fixed list.
5. `agent_prompt.py` rules and example; update `tests/test_agent_tools.py:506` (asserts the level-W wording).
6. ARCHITECTURE.md v2.13 (b: `try_transform` row, evidence states; c: P row, literal rule, timer; i: rows 4, 4a; change log), DECISIONS.md.
7. One live Haiku run on the dev-draw mixed-identifier dataset (seed 1 only, about $0.01): does it use `when`?

| Rule the code enforces | Test 1 | Test 2 |
|---|---|---|
| R1 pattern check | bad or over-long pattern in each of the three places: structural-error sentence, no exception | `apply_transforms` with a bad pattern: a `bad_pattern` reject event |
| R2 timer | `(a+)+$` on a long value: `regex_timeout`, next value still processed (skipped on Windows) | pattern switched off after the limit (limit and seconds patched small) |
| R3 `regex_replace` | all matches replaced; no match unchanged; empty result absent | `repl` with a letter refused |
| R4 `template` | positions filled; all blank absent; partly blank per DECISION 2 | not first, index out of range, letter in literal: structural errors |
| R5 `constant` | refused on `entity.legal_name`, inside a chain, with a state not in the enum | emitted only where the anchor is filled, L3; finalised `asserted`, at or under the cap |
| R6 `when` | not met: no observation, skip `when_not_met`, zero rejects; `equals` ignores case | unknown column or both keys: structural error; `when.column` not reported unaccounted |
| R7 gate and level | changing a `when` is not a narrowing | level P for the new transforms, W for a `clean_whitespace`-only chain |

## 9. DECISIONS (final, 2026-11-13: 1=A, 2=A, 3=B, 4=A, 5=A; the regex timer is Unix-only)
Was "DECISION NEEDED"; the owner chose the options above. Text below kept for the record.
1. **regex safety.** (A) the 1-second per-value timer of section 2, plus length limit and compile check. (B) no timer; a
   static safe subset (refuse a quantified group that contains a quantifier or `|`). Recommend A: it stops any pattern
   on the demo machine with a mechanism already measured; B guesses which patterns are slow. A leaves Windows open.
2. **template with some parts blank.** (A) reject `template_missing_part`: counts against the 90% floor, so a template over optional
   columns fails validate and the agent moves to `join_nonempty`. (B) skip: not counted, so one that drops 70% of rows still validates. Recommend A.
3. **constant cap.** (A) 0.6 as section c says; Part 4's low-trust line is `< 0.6`, so the constant counts as a normal
   claim. (B) 0.5: under the line, so a model-asserted state loses to any stated value. Recommend B (edits section c).
4. **Condition shape.** (A) a `when` on each field, no order. (B) one field with an ordered `cases` list, first match wins.
   Recommend A: keys, stats, abstention and critique issues stay per field; B needs a new key scheme and an order rule.
5. **Literal text in `template` / `repl`.** (A) separators only. (B) free text (e.g. append "Pty Ltd"). Recommend A: B
   lets the agent write values no source stated, with no cap and no L3 tag.

Left out on purpose: negation and and/or in `when`; `when` on envelope settings; named placeholders in `template`; level G.
