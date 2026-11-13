# Round-2 write-up: tool-using agent and richer entity resolution

Every number names the file it came from. "Not measured" means no file holds it. The round-1 write-up is `WRITEUP.md`
(left as submitted). The design is `ARCHITECTURE.md` v2.15; reasons for choices are in `DECISIONS.md`.

## 1. What changed and why
The CTO feedback asked for an agent that uses tools and can ingest a random dataset live, plus richer entity
resolution (ARCHITECTURE.md section j). Round 1 was a fixed 8-step pipeline with a whitelisted engine and an
ABN/name matcher.

## 2. Design
- **Agent loop** (ARCHITECTURE.md section b). The model picks one tool per turn: `fetch`, `list_members`, `list_sheets`,
  `sniff`, `read_table`, `profile`, `check_unique`, `sample`, `search`, `try_transform`, `validate`, `critique`,
  `ask_human`, `finish`. The harness runs the tool and caps the result. Budget: 40 turns, $1.00, 4 minutes of agent time.
- **The harness decides safety; the model decides the investigation.** Enforced in code: a held-out split stored as row
  fingerprints (only `validate` and `critique` see held-out rows); `finish` runs validate itself and needs a critique;
  blocking critique issues refuse a finish twice, then the outcome is `needs_review`; a human approves by config SHA-256.
- **Evidence states per field** (`held_out`, `training`, `unverified`, `asserted`) are set by code and cap
  `field_confidence` at 0.8 / 0.5 / 0.5 (section b). The model cannot raise them.
- **Untrusted data.** Cell values, headers and CKAN text reach the model only inside a `<data>` block. `fetch` takes no
  URL from the model, checks every redirect hop, and caps downloads at 200 MB.
- **Trace and replay.** Every turn and tool call is written to `logs/agent_runs/<source>/trace.jsonl`; a re-run replays it,
  and resume is refused if the header (limits, prompt hash, code version) differs. Secrets are redacted before writing.
- **Transforms.** Three levels (section c): W (12 whitelisted), P (`regex_extract`, `regex_replace`, `template`,
  `map_values`, `split`, `constant`, and a per-field `when`), G (generated Python). W and P are built; G is not.
- **Matcher m2.0** (DECISIONS.md, steps 7b2-7e2): equal-ABN/ACN tiers need rarity-weighted name agreement (0.6, hand-set,
  not tuned on labels); a name that hits more than one registered holder is refused; generic names are refused by an
  IDF threshold (14.02, set before labels were viewed). Accept 0.80, loose 0.60. Graph edges: `same_as`, `nominee_of`.
- **Three confidences stay separate:** `source_reliability`, `field_confidence`, `link_confidence`.

## 3. Results
**Step 5: six sources re-onboarded by the agent (claude-haiku-5-5), then approved.** From `reviews/step5_summary.md` and
`configs/*.approval.json`: all six ended `validated_config`, each cost $0.0066 to $0.0186 on the pinned run (step total $0.096, including discarded first-pass runs) and took 40 to 83 s.
Approvals (`configs/<source>.approval.json`, reviewer rahul, 2026-11-13): fields reviewed and fields marked wrong:
act_notifiable_invoices 2 / 0, asic_credit_licensee 7 / 0, qbcc_licensed_contractors 7 / 0,
qld_health_contracts_2023_24 3 / 0, vic_liquor_licences 6 / 0, wa_tenders_awards_2023_24 2 / 0. Critic flags still open in
the packets at the time of the step 5 runs: blocking issues on asic, qld_health and wa (later re-runs for those three
left 0 blocking open at finish, `reviews/step5_summary.md`).

**Step 6: Business Names register onboarded by the agent** (`reviews/step6_summary.md`): `validated_config`, $0.0092, 10 turns,
200.3 s including a 72 MB download. Row filter over 3,312,255 rows kept 3,867 in 16.9 s (`docs/runbook.md`).

**Matcher output** (`outputs/part3/summary.json`, m2.0): 562 accepted and 464 loose links; tiers T1_register_abn 511,
T1_abn_equal 49, T1r 2 (accepted), T3_register_name 463, T4_name_postcode 1 (loose); 9 cross-source entities.
Graph check: 0 components with more than one ABN (`outputs/part3/graph_checks.json`).
**Profiles** (`outputs/profiles/graph_profiles_summary.json`): 778 profiles: cross_source accepted 9, cross_source loose 3,
single_source_register_confirmed accepted 348, loose 418. One person-only component skipped.

**Step 8 hand check, verbatim from `reviews/step8_results.md`** (18 of 18 rows labelled; precision = Y / (Y + N), U excluded; 95% Wilson interval):

| band | rows | Y | N | U | precision | 95% CI |
|---|---|---|---|---|---|---|
| accepted | 8 | 8 | 0 | 0 | 1.0 | (0.676, 1) |
| loose | 10 | 4 | 5 | 1 | 0.444 | (0.189, 0.733) |

Caveats (verbatim): "Labels are non-independent: ABN Lookup shows ASIC business names and the registers are matcher
features." "Samples are small (n per stratum); intervals are wide." "Some labels were model-assisted (notes marked); the rest
are the owner's." By tier: T3_register_name 10 rows, 4 Y, 5 N, 1 U (0.444); T1_register_abn 5/5; T1r 2/2; T1_abn_equal 1/1.

**Round-1 hand check kept as history** (`handcheck/part3_link_result.json`): 30 of 30 accepted correct. That was matcher m1.x.

**Step 9: final benchmark, seed 2, one run per model** (`reviews/step9_results.md`; automatic outcomes only):

| | Haiku | Sonnet |
|---|---|---|
| validated_config / partial / could_not_read / no_business_entities (of 15) | 7 / 0 / 2 / 6 | 6 / 1 / 2 / 6 |
| W / P / G field levels | 13 / 9 / 0 | 17 / 4 / 0 |
| cost, 15 runs | $0.0918 | $1.1403 |
| agent wall-clock, mean per run | 28.6 s | 19.4 s |
| injection case | PASS | PASS |

Same outcome on 14 of 15 datasets. The two `could_not_read` cases are a host network error and an HTML-only dataset, the
same for both models. Same outcome with different mapping on the QLD supplier directory (Haiku `legal_name`, Sonnet `abn`);
one of them is probably wrong (`reviews/step9_results.md`), and the human columns (`handcheck/benchmark_review_fin2{h,s}.csv`) are not filled.
Dev draw (seed 1) validated 7 of 11 in the last Haiku pass (`outputs/benchmark/dev_seed1/compare.md`, via ARCHITECTURE.md section e).
Demo model: Haiku (`reviews/step9_results.md`).

## 4. Cost
- Summed from `logs/llm_calls.jsonl` by its `round` field: round 1 $0.166 (60 calls), round 2 $5.558 (1,769 calls). Total about
  $5.72, under the $10 target. This is my sum of the log as it stands, not an invoice.
- Benchmark share: $1.42 (`reviews/step9_results.md`). Per run: Haiku $0.0061, Sonnet $0.076 (same file). Per record: $0 (extraction uses no model).
- One-time inference per source versus per record: onboarding costs cents once; extraction, matching and profiles run with no model.

## 5. Designed, not built
- **Sandbox for generated code (step 4b, level G):** AST allowlist, restricted builtins, `python -I -S` subprocess with
  rlimits, approval hash over generated code (ARCHITECTURE.md section c). No `sandbox.py` exists; the benchmark shows G = 0.
- **Companies register** (ACN, type, status, former names), **T1r** as designed (register name history confirming both
  names) and **T3c** (second independent hit): cut at step 6. T3c is disabled; T1r as built confirms one side only (DECISIONS.md, 7b2).
- **`renamed_to` and `trustee_for` edges:** not built. Round 1 found 13 ATF patterns as an unmerged relationship;
  m2.0 `summary.json` still reports `atf_relationships` 22, but no typed edge exists in the graph.
- **ABR lookup** (stretch): not built.
- **Code cap on name confidence by header word:** a cap on `legal_name` (0.7) and `trading_name` (0.6) unless the header
  carries a matching word. Prompt wording only today (ARCHITECTURE.md section b, rule 5).
- **Consequence recorded in DECISIONS.md (7b2):** a rename with no Business Names history is refused. Check 8, Cantel
  to Steris, a true link, is refused by m2.0. It is a recall loss and reported through `handcheck/accepted_conflicts.csv`.

## 6. Limitations
- **Loose T3 precision is weak:** 4 Y / 5 N / 1 U, precision 0.444, CI 0.189 to 0.733 (`reviews/step8_results.md`). 463 of 464
  loose links are T3. The loose band is not safe to treat as correct, and 418 single-source profiles are in the loose band.
- **Few labels:** m2.0 precision rests on 18 new labels. Only 2 of the 50 round-1 labels carried over
  (figure from the step 10 brief; my own count of the round-1 pair ids present in `outputs/part3/links.jsonl` found 1 of 50,
  so check this before quoting either). Accepted-band precision is 8 of 8 on a small sample; it is not a measure of the 562 accepted links.
- **Sampled extraction:** extraction is capped at 1,000 rows per source by default (`outputs/part3/summary.json` mentions: 1,000 for five sources,
  191 for QLD Health). Profiles and links describe the sample, not the files.
- **Labels are not independent** (ABN Lookup shows ASIC business names; registers are matcher features) and some were model-assisted.
- **No human check of the final benchmark yet.** Haiku's lower W count (13 against 17) and higher P count (9 against 4) may mean weaker evidence.
- **n = 15, one run each.** Self-agreement between runs of one model was imperfect on the dev draw (Haiku 10 of 11 on outcome, 6 of 11 on outcome and fields, d to e; ARCHITECTURE.md section e).
- **Source reliability numbers are model judgements** (round 1, `README`/`WRITEUP.md`).
- **Open critic risk:** the critic can share the agent's blind spots (ARCHITECTURE.md section k, item 2).
- **Reproducibility:** QBCC is a live register; a fresh download differs from the committed one (round 1, `DECISIONS.md`).

## 7. Change: re-running an improved matcher
Each link stores `matcher_version`, thresholds, raw evidence features and `previous` (`outputs/part3/links.jsonl`). `rescore`
is a pure function over stored evidence and refuses to write if a human Y would be demoted or an N promoted. Demonstrated
in round 1: m1.1 touched one labelled link, a Y, and was rejected (`DECISIONS.md`). Consequence of the same design: the 420
round-1 (m1.2) links cannot be rescored to m2.0 because they lack the features it needs (DECISIONS.md, step 7c).

## 8. Next
Run the human review of the final benchmark. Label 15 rows per stratum, loose T3 first, and promote or drop it. Build
the Companies register and name history. Build the sandbox only if the benchmark shows G is needed.
