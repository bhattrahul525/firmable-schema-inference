# Step 6 plan: ASIC Business Names register only (reduced scope)

## What and why
ASIC Business Names register: 72 MB zip / 247 MB CSV, business name -> holder ABN, CC BY 3.0 AU.
Used as matcher evidence (step 7): bridges a no-ABN trading name to a registered holder ABN.
Reduction: the Companies register (401 MB, ACN/type/status/former names) is cut (cut order item 4).

## Path
1. Download the Business Names zip to data/raw/reference/ (git-ignored). Save licence + attribution text.
2. Onboard by the agent like any source (Haiku, pinned resource). Output: config + review packet; one human approval.
3. Generic engine row filter: keep only register rows whose ABN or normalised name key appears in the
   mentions of the six approved sources. Pure code, no LLM.
4. Commit the trimmed result with attribution; full file stays on disk only.
5. Measure the row-filter time on the full file; record in the runbook (ARCHITECTURE line 388).

## Rules enforced by code
- Only status Registered rows are kept/used (current names only).
- A name that matches more than one holder is refused, never loose.
- Name key uses the same normalisation as the matcher (rarity-weighted tokens, step 7).

## Cost and size
Agent onboarding on a 247 MB CSV: about $0.02-0.05 on Haiku (one or two runs). Row filter: no LLM cost;
time unknown until measured. Trimmed output expected small; measure and record.

## Designed-not-built (record in ARCHITECTURE + DECISIONS)
- Companies register and its features (ACN/type/status/registration date/former names).
- T1r register-history leg; T3c as defined (licensee -> Companies leg).
- Offline fallback is now Business Names only; output must say Companies and ABR features are absent.

## Build order
1 download + licence file -> 2 agent onboarding + approval -> 3 row filter -> 4 trimmed output + attribution
-> 5 timing -> 6 doc updates (v2.15, DECISIONS, runbook).
Tests (max 2 per enforced rule): row filter keeps ABN match and name-key match; Registered-only.

## DECISION NEEDED
1. Filter keys: A) ABN only; B) ABN + name key. Recommend B (no-ABN trading names need the name key).
2. T3c without Companies: A) redefine as two Business Names hits; B) disable T3c, record designed-not-built,
   keep T3 (single hit, 0.65 loose), no-ABN links hand-judged. Recommend B (A's hits are not independent).
3. Onboarding path: A) agent, with pre-extracted CSV fallback if the zip read fails; B) custom loader.
   Recommend A (it is the demo story; dev source 11, a zip, was could_not_read, so keep the fallback).
4. Trimmed result: A) commit with attribution; B) regenerate only at resolve time. Recommend A.