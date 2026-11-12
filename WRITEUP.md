# Write-up (Part 5)

Numbers are measured unless marked *guess*; headline results are in the README. Cost is computed from list prices, not reconciled with an invoice.

## 1. Cost
- **Whole project: $0.17** (60 calls, 459k input + 220k output tokens), including development and regenerated configs. Parts 1, 3, 4 use no model.
- **Onboarding one source** (Haiku 5.5): 4-7 calls, **$0.009-0.032** (median $0.014), 57-130k input + 12-43k output tokens, 1-3 minutes of model time, ~5 minutes of human review. **Per record: $0** (deterministic extraction, under 2 seconds for 5,000 rows).
- *Guess:* Sonnet 5.5 would cost ~20x more for the same tokens, roughly $0.2-0.6 per source. Not run: **all six configs and the seventh-source test used Haiku 5.5**.

## 2. Agent design
**Steps:** inspect (code proves the model's reader settings by loading the file) → profile and split rows (code) → propose twice from different rows (model) → validate on 300 held-out rows with the real engine (code) → revise, max 2 rounds (model) → critique raw rows beside output (model) → abstain, confidence, packet (code) → human gate.
**Self-checks:** parse rate ≥90%, unique ids, every column used or listed unmapped, meaning checks; a still-failing field is **removed by code**. `field_confidence` = the lower of model confidence and measured parse rate. Each step checkpoints to `logs/agent_runs/<source>/`, so a failure costs one step.
**Human sees:** one packet per source (fields with raw → output examples, confidences, unmapped columns with reasons, warnings, revision changes) and one question: which numbers are wrong. Approval stores the config's SHA-256; the engine refuses an edited config.
**Weakest step: meaning checks.** Code checks form only: WA's names parsed 100% while swapping legal and trading name for ~12% of bracketed names (409 of 3,260); only the human caught it. Reviewers judged 41 fields, 2 wrong (both WA). Runs of one source also differ. **Seventh source:** `onboard nsw:find-by-lia-band` produced a config unaided (6 calls, $0.019, ~2 min), left unapproved.

## 3. The hard one: WA Tenders
Names are "Trading (Legal)" in some rows, "Legal (Trading)" in others; 44% have no brackets. A reviewer rejected the first mapping and the revision dropped both name fields rather than guess, so all 5,817 records are unlinkable. *Custom code vs config:* add a whitelisted transform when the rule is source-independent and recurs (a suffix-aware bracket split would recover ~80%); write per-source code only for an unreadable format or a one-off high-value source.

## 4. Scale: 6 → 500 sources
**Human review breaks first** (500 × ~5 min ≈ 40 hours, no triage); **matching second** (ABN reuse, generic names, uncalibrated scores); then the transform whitelist (3 of 6 configs report a gap).

## 5. Change: improving the matcher in six months
**Recorded in advance, per link:** `matcher_version`, the raw `evidence` features (names, ABN/ACN equality, containment, postcode, state), thresholds, a `link_id` (kept by `rescore`) and both source record ids; refused pairs are stored too. Per observation: `extractor_version` = config version + hash + engine version. Links are never overwritten.
**What we do:** `rescore` is a pure function over stored rows: no sources, no extractor, no model; each new link keeps `previous` = {version, confidence, band}. *Demonstrated, and it caught a regression:* matcher m1.1 (names sharing only generic words like "Australia" no longer agree) re-scored all 420 links in under a second and demoted 2 accepted links (Cantel/Steris, Tyco/Wormald). Of the 50 labelled links it touched exactly one, a **true** link: ABN Lookup confirms Cantel (Australia) was renamed Steris Australia on the same ABN (label yes). The labelled set caught this regression, so m1.1 was **rejected** before it was ever used for the production links. m1.2 (current) scores like m1.0 and fixes another defect found by the same check: a name-only link had borrowed a wrong ABN as its canonical key (one link re-keyed, no profile changed).
**At millions:** re-score only partitions a change can affect, promote newly acceptable refused pairs, gate every release on a frozen labelled set, rebuild profiles from links. **Cannot be redone:** a rule needing a field we did not store, so evidence must carry every candidate attribute, and human-confirmed links must be flagged so a re-score never overrides a person.

## 6. Next: three weeks
(1) A larger labelled set **including refused pairs** (unchecked, so I do not know how many true links the names-agree rule discards). (2) **ABN name history** as link evidence. (3) Risk-ranked review packets, a Sonnet-vs-Haiku comparison, the engine gaps the agent reported.

## Relationship model (Part 3)
A **link table plus a canonical entity key**. Pairwise links with evidence are the primary data; clusters and keys (`abn:<11 digits>`, else a hash of name and state) derive from accepted links only, so a wrong link can be deleted and clusters recomputed. An equal ABN is not enough: names must also agree (23 pairs refused, including people carrying a company's ABN), and names alone never link people. **Parent/subsidiary:** no source states ownership, so none is inferred and similar names are not grouped; the one relationship recorded is "acting as trustee for" (13 found), as an edge, never a merge.

## Measurements and limits
Headline numbers (false positive rate, precision, counts): see README headline numbers.
- **Disclosure:** labels were drafted with an AI assistant, then each of the 50 rows was checked by me on ABN Lookup (abr.business.gov.au); notes are in `handcheck/part3_verify.csv`. Precision at 0.80 counting unsure as wrong moved from 76.7% (AI-drafted labels) to 100% because the 7 rows then marked unsure were ABN-equal pairs with differing names that the ABN Lookup history confirmed as the same entity; the matcher did not change. The 50 rows cover 43 distinct businesses, and 42 of the 50 rows are ACT vs QLD Health; the matcher already required names to agree, so precision is an upper bound.
- Three same-entity pairs differ in name by rename or company-type change (Cantel → Steris, Everlight Limited → Pty Ltd, Hologic (Australia & New Zealand)). The matcher **accepted** all three, but partly by luck: Cantel/Steris passed only because both names contain "Australia"; a rename sharing no word would be refused. ABN name history is the evidence to add next.
- Check 15: the Stryker pair is the same business, but the ACT record carries J.J. Richards' ABN (40000805425; Stryker's is 48002873850), a source error, so that loose link had a wrong `canonical_entity_key`. Fixed in m1.2; no accepted entity or profile is affected.
- Check 23 (Culpan Medical) stays unsure: ABN Lookup shows NSW 2000 throughout; record B says VIC 3189 and has no ABN.
- Name-only links checked (record B without an ABN) were correct or unsure, but with no address on either side a same-named different company cannot be ruled out by the data.
- QLD Health: 24 of 433 `legal_name` observations (7 source records) are comma-joined multi-supplier cells left unsplit (`needs_transform`: addresses also contain commas) at `field_confidence` 0.9; they should have been lowered or abstained.
- QBCC is a live register: a fresh download gave 268 accepted links / 41 entities (not 266 / 40); committed outputs are the reference. ACT's licence is "Other", flagged on every observation. Source reliability scores are model judgements.
