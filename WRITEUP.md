# Write-up (Part 5)

Numbers are measured unless marked *guess*. Cost is computed from list prices in `src/llm.py` (`logs/llm_calls.jsonl`), not reconciled with an invoice.

## 1. Cost
- **Whole project: $0.17** (60 LLM calls, 459k input + 220k output tokens), including development, four regenerated configs and the seventh-source test. Parts 1, 3 and 4 use no model.
- **Onboarding one source** (Haiku 5.5, final run): 4-7 calls, **$0.009-0.032** (median $0.014), 47-130k input + 9-43k output tokens, 1-3 minutes of model time, 7-13 checkpointed steps, plus about 5 minutes of human review. WA Tenders cost most ($0.032).
- **One-time vs per-record:** inference is paid once per source. Extraction is deterministic code: **$0 per record**, under 2 seconds for 5,000 rows.
- *Guess:* Sonnet 5.5 would cost about 20x more for the same tokens (price ratio), roughly $0.2-0.6 per source. Not run; all six configs were made with Haiku.

## 2. Agent design
**Steps:** inspect (model proposes reader settings, code proves them by loading the file) → profile and split rows into sample A, sample B and 300 held-out (code) → propose twice from different rows (model) → compare → validate on held-out rows with the real engine (code) → revise, max 2 rounds (model) → critique raw rows beside their output (model) → abstain, confidence, packet (code) → human gate. The model does only what code cannot: read an unfamiliar file and judge meaning.

**Self-checks:** parse rate ≥90% per field, unique record ids, every column used or listed as unmapped with a reason, meaning checks (legal vs trading name, postcode vs state, future dates). A field still failing after revision is **removed by code** (QBCC `entity_type` failed at 21%). `field_confidence` = the lower of the model's confidence and the measured parse rate, never an average.
**Failure handling:** each step checkpoints to `logs/agent_runs/<source>/`; re-running resumes at the first missing step, so an API error costs one step.
**What the human sees:** a packet per source: each field with three raw → output examples, model confidence, measured parse rate, unmapped columns with reasons, warnings with the agent's answers, and what each revision changed. One question: which numbers are wrong. Approval stores the config's SHA-256; the engine refuses an edited config.

**Weakest step: meaning checks.** Code only checks form. WA's names parsed 100% and passed validation while swapping legal and trading name for about 12% of bracketed names (409 of 3,260 in the full file); only the human caught it. 41 field verdicts across review rounds, 2 wrong, both WA names (small n; judged from the packet). Two runs of the same source also differed (ASIC dates, VIC `address.full`). Running it also exposed a bug in my harness: a profile capped at 20,000 rows made the agent think real keys were non-unique (fixed; three configs regenerated).

**Seventh source:** `onboard nsw:find-by-lia-band` (seed-drawn, licence unknown) produced a config with no human input: 6 calls, $0.019, ~2 minutes. Left pending review.

## 3. The hard one: WA Tenders
Supplier names are "Trading (Legal)" in some rows and "Legal (Trading)" in others; 44% have no brackets. The first mapping swapped names; a reviewer rejected it with evidence; the revision then dropped both name fields rather than guess. WA now contributes only address and type, so **all 5,817 records are unlinkable** (in the unlinked queue). *When custom code is right:* add a whitelisted transform (not a parser) when the rule is source-independent and likely to recur (a suffix-aware bracket split would recover ~80% of bracketed names); write per-source code only for an unreadable format or a one-off source of high value. I did neither: name-only links are where wrong links come from.

## 4. Scale: 6 → 500 sources
**Human review breaks first:** 500 × ~5 minutes is ~40 hours and the gate has no triage. **Matching is second:** the link table and name blocks grow with every source, ABN reuse (QBCC lists individuals under their company's ABN) and generic names breed wrong links, and my tier scores are uncalibrated. **Third, the transform whitelist:** 3 of 6 approved configs report a gap, so expect ~80 at 500. Fix: risk-rank packets (low parse rate, disputed fields, new transforms first) and sample clean ones.

## 5. Change: improving the matcher in six months
**Recorded in advance, per link:** `matcher_version`, the raw `evidence` features (names, ABN/ACN equality, containment, postcode, state), thresholds, a stable `link_id`, and both source record ids; refused pairs are stored with features too. Per observation: `extractor_version` = config version + config hash + engine version. Links are never overwritten.
**What we do:** `rescore` is a pure function over stored rows: no source files, no extractor, no model. It writes a new file where each link keeps `previous` = {version, confidence, band}. *Demonstrated:* matcher m1.1 (names sharing only generic words like "Australia" no longer agree) re-scored all 420 links and refused pairs in under a second: 2 accepted links demoted (Cantel/Steris, Tyco/Wormald), 418 unchanged. Of the 50 hand-labelled links it touched one (labelled *unsure*) and none labelled *yes*, so the change is measured against labels.
**At millions:** re-score only the partitions a change can affect, promote newly acceptable refused pairs, gate every release on a frozen labelled set, rebuild profiles from links. **Cannot be redone:** a rule needing a field we did not store, so evidence must carry every candidate attribute, and human-confirmed links must be flagged so a re-score never overrides a person.

## 6. Next: three weeks
1. **A larger stratified labelled set, including refused pairs** (I did not check them, so I do not know how many true links the names-conflict rule discards). Thresholds, scale and rescore all depend on it.
2. Claim-level dates (recency is unused today: our dates are file snapshots).
3. Risk-ranked packets; Sonnet-vs-Haiku comparison on the same six sources.
4. The engine gaps the agent reported (bracket split, constant value, licence-scoped observations).

## Relationship model (Part 3)
A **link table plus a canonical entity key**. Pairwise links with evidence are the primary data; clusters and keys (`abn:<11 digits>`, else a hash of name and state) derive from accepted links only, so a wrong link can be deleted and clusters recomputed. An equal ABN is not enough: names must also agree (23 pairs refused, including people carrying a company's ABN), and names alone never link people. **Parent/subsidiary:** no source states ownership, so none is inferred and similar names are not grouped; the one relationship recorded is "acting as trustee for" (13 found), as an edge, never a merge.

## Measurements and limits
- Part 1 false positive rate **26.3%** (5 no of 19 judged, 1 unsure; 30% if unsure counts as wrong), n=20.
- Part 3 precision at the 0.80 threshold, n=30: **100% excluding unsure (95% interval 86-100%), 76.7% counting unsure as wrong**; looser band 20/20 (interval 84-100%). All 7 unsure are ABN-equal links with differing names. 42 of the 50 checks are ACT vs QLD Health and the matcher already required names to agree, so these are upper bounds.
- Part 4: 50 profiles (40 accepted, 10 looser); 9 names unresolved by design. Deleting ACT or QLD Health ends cross-source support for 44-47 profiles; no deletion silently rewrites a name.
- Reproducibility: the QBCC register is live; a fresh download had 47 more rows and gave 268 accepted links / 41 entities (not 266 / 40). The committed outputs are the reference; `download` warns on upstream changes.
- Licences: five datasets are Creative Commons; ACT's is "Other", flagged on every observation. Source reliability scores are model judgements.
