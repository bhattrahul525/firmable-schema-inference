# CLAUDE.md — Firmable take-home: Schema Inference & Agentic Ingestion

## Who / what
- I'm Rahul, applying for **Senior Applied AI Engineer (part-time)** at Firmable (Melbourne).
- This repo is my submission for their technical assignment. The full brief is in `CASE_STUDY.md`
  and the target schema is `firmable_ontology.yaml` — **read both before doing anything**.
- After submission there is a follow-up call where I must **explain every line and every design
  choice**. So: prefer simple, legible code over clever code, and explain your reasoning as you go.

## Model rule
- Planning and costly decisions are made on Fable 5.2. Building is done on Sonnet 5.5. Reviews are done on Opus 5.5 in a fresh session.
- If you are building and reach a decision that changes the design, a gate, an outcome definition or ARCHITECTURE.md, stop. Say "This needs a planning decision" and describe the options. Do not decide it yourself.
- Small implementation choices (names, file layout, test structure) are yours to make. Log them in your report.

## Hard constraints (from the brief)
- **Time box: 6 hours total** of my working time, spread over two sessions. Optimise for a
  well-reasoned partial solution, not completeness. Keep a running time log in `TIMELOG.md`.
- **API spend target < USD $10.** Every LLM call must go through one wrapper that logs
  model, input/output tokens, cost and wall-clock time to `logs/llm_calls.jsonl`.
- **Part 2 must be agentic at runtime.** The test: given a 7th unseen dataset, the system
  produces a mapping config with no human writing code or config.
  - NEVER hand-write or hand-edit a mapping config. If a config is wrong, fix the agent
    (prompts, validation, revision loop), then regenerate.
  - NEVER write per-source parsers. One generic extractor engine + N agent-generated configs.
  - A single prompt that returns a mapping is not enough — needs distinct steps, state carried
    between steps, self-validation on unseen records, self-revision, and a human approval gate.
- Part 1 may be deterministic (cheap filtering before any model call is fine — explain why).
- It must run from a clean checkout in < 10 minutes via `README.md`. If something is broken,
  say so in the README.

## What they value (design must reflect these)
1. **A wrong link is worse than no link.** Abstain when unsure; unlinked queue with reasons.
2. **Config beats code.**
3. **Honest measurement.** Report real false-positive rate (Part 1, hand-check 20), real link
   precision (Part 3, hand-check 50) at a stated threshold. Never round in our favour. No
   "100% coverage" claims.
4. Respect dataset **licence** terms (from CKAN metadata).

Things that lose marks: hand-written configs; single-prompt inference with no validation/revision;
per-source parsers; one blended confidence score; links without a precision number;
100% coverage claims; ignoring licences.

## Ontology rules (firmable_ontology.yaml is a contract — use exact field names)
- Emit **observations** (a claim by a source at a time), not reconciled facts. Do not merge at
  ingest; reconciliation only happens in Part 4 profiles.
- **Three separate confidences, never blended:**
  - `source_reliability` — per source/publisher, per kind of claim.
  - `field_confidence` — per mapped field: did we map/parse it correctly.
  - `link_confidence` — only on entity links (Part 3).
- **ABN (11 digits) and ACN (9 digits) have checksums — validate them**, don't length-check.
  ACN is often but not always the last 9 digits of the ABN — don't assume.
- `entity_type` defaults to `unknown`. Only set it from explicit source values or unambiguous
  markers (e.g. "Pty Ltd" → company, record as derivation L1).
- `trading_name`: one observation per name.
- `industry_code`: keep the raw source value as well.
- Every record carries the envelope: `source_id`, `source_record_id` (if no key in source,
  build a deterministic one, e.g. hash of normalised row, and document it), `observed_at`,
  `ingested_at` (different things — keep both), `valid_from`/`valid_to`, `licence`
  (`unknown` + flag if missing), `extractor_version` (config version + engine version).
- Tag values with `derivation_level` L0–L4 (L0 stated, L1 deterministic parse/checksum,
  L2 statistical, L3 model-inferred).
- Unmappable fields: leave unmapped and **list them** in the config — never guess.

## Deliverables (see CASE_STUDY.md for exact details)
- Part 1: ranked shortlist of 50 (from ≥200 records pulled via CKAN API) as CSV/JSONL with
  dataset_id, title, organisation, formats, confidence, one-line reason + FP rate from 20 checks.
- Part 2: 6 diverse downloadable sources (different publishers/formats/shapes, ≥1 not clean CSV)
  → 6 agent-generated mapping configs + 1 generic extractor + canonical observations
  (~1,000 records per source). Per field: source field, canonical field, transform, confidence.
  Report step count, token cost, wall-clock per source onboarding, and where a run can fail
  without losing the whole job (checkpoint state per step so runs can resume).
- Part 3: proposed links `{source_a_record, source_b_record, canonical_entity_key, confidence,
  evidence}`, unlinked queue with reasons, measured precision on 50 hand-checked links at a
  stated threshold (optionally a looser threshold too). Explain the relationship model chosen
  (clusters / canonical key / link table / graph) and parent–subsidiary handling.
- Part 4: 50 company profiles — per-field confidence, per-field provenance, conflicts shown
  (winner, why, losing values), unfillable fields absent. Note on impact of deleting one source.
- Part 5: `WRITEUP.md`, max 2 pages: cost (one-time inference vs per-record), agent design &
  weakest step, the hard source, scale (6 → 500 sources, what breaks first), **change (re-running
  an improved matcher over millions of old links — what must be recorded in advance; they care
  about this most)**, next 3 weeks, relationship model rationale.
- Submit: README.md, code, WRITEUP.md, all outputs, hand-check materials.

## Environment
- data.gov.au CKAN API: `https://data.gov.au/data/api/3/action/` (`package_search`,
  `package_show`, `resource_search`). No key. State portals (NSW/QLD/VIC/SA) use the same API.
- Python 3.10+. LLM provider: **Claude API via the official `anthropic` Python SDK.**
  Dev iterations on `claude-haiku-5-5` ($0.10/$0.50 per MTok). Plan was Sonnet for final runs
  (`claude-sonnet-5-5`, $2/$10 per MTok); all six configs and the seventh-source test shipped with
  claude-haiku-5-5 (see DECISIONS.md). The model is a setting in `src/llm.py`, never hard-coded in agent code; all
  provider-specific code stays inside `src/llm.py`. API key via `.env` (never commit it).
- Part 1 is fully deterministic (metadata score + content probe), with no LLM calls. Decided 2026-11-11.
- The user runs `git init` and handles all git operations themselves.
- Keep dependencies minimal and pinned in `requirements.txt`.

## Suggested layout (adjust if there's a good reason)
```
CASE_STUDY.md  firmable_ontology.yaml  README.md  WRITEUP.md  TIMELOG.md  DECISIONS.md
src/
  llm.py            # single LLM wrapper with cost/token/time logging
  part1_triage/     # CKAN pull + deterministic scoring (+ optional LLM for borderline)
  part2_agent/      # multi-step agent: inspect → sample → propose → validate → revise → approve
  engine/           # generic config-driven extractor
  part3_resolve/    # blocking, matching, links, unlinked queue
  part4_profiles/
  common/           # ABN/ACN checksum, normalisers, envelope builder
configs/            # agent-generated mapping configs ONLY (never hand-edited)
data/raw/           # downloaded sources (gitignored if large)
outputs/            # shortlist, observations, links, unlinked queue, profiles
handcheck/          # sheets used for FP rate and precision checks
logs/               # llm_calls.jsonl, agent run state/checkpoints
```

## Time plan
- **Session 1 (3h):** 0:00–0:30 setup + logger · 0:30–1:15 Part 1 + pick & download 6 sources ·
  1:15–3:00 Part 2 agent + generic extractor working end-to-end on 2 sources (incl. the non-CSV).
- **Session 2 (3h):** 0:00–0:45 agent on remaining 4 sources + extract 1,000 records each ·
  0:45–1:45 Part 3 + hand-check 50 · 1:45–2:15 Part 4 · 2:15–3:00 WRITEUP + README.
- If Part 2 overruns, **cut Part 4 scope first** (fewer profiles, stated honestly). Never cut the
  precision checks or the write-up.
- One creative extension only: link records store model/threshold version + raw evidence/features
  so links can be re-scored later (supports write-up Q5).

## How to work with me
- Before writing code for a part, give a short plan (≤10 bullets) and wait for my OK.
- After finishing a part, summarise: what was built, key design choices and why, known weaknesses.
  Append notable decisions to `DECISIONS.md` and "what I'd do next" ideas to a running list —
  these feed WRITEUP.md.
- Remind me to update `TIMELOG.md` at the end of each block.
- Don't silently expand scope. If something will blow the time box, say so and propose a cut.

## Architecture (round 2)
- ARCHITECTURE.md is the single source of truth for the design. Read it at the start
  of every session before planning or writing code. Do not re-derive the design from
  the conversation.
- Do not build anything while its Status line says DRAFT.
- If a change to the design is agreed, or the code has to deviate from the document
  (a tool added or removed, a new edge type, a changed budget, a cut, a new reader,
  a sandbox rule), update ARCHITECTURE.md in the SAME commit as the code: edit the
  affected section, bump the version (2.1, 2.2, ...), update "Last updated", and add
  a Change log row saying what changed and why.
- Never change the design silently. If you think the architecture is wrong, say so and
  propose the edit; wait for my OK before changing the document or the code.
- Before every commit, check that the code and ARCHITECTURE.md agree. If they do not,
  fix the document or tell me.
- Keep ARCHITECTURE.md under about 400 lines. Details that belong to one module go in
  that module's docstring, with a pointer from the document.
