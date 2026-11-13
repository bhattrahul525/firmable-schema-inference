# Decisions

Notable design decisions and why. Feeds WRITEUP.md.

## Setup

- **LLM provider: Claude API (official `anthropic` SDK).** Planned: dev on `claude-haiku-5-5`, final runs on
  `claude-sonnet-5-5`. **What actually happened: every config, the seventh-source test and all other model calls used
  `claude-haiku-5-5`; Sonnet was never run.** The model is one setting in `src/llm.py` (`LLM_MODEL`). All provider code lives in `src/llm.py`; nothing else imports `anthropic`,
  so swapping providers means one new class, not touching the agent.
- **One LLM wrapper, one log.** Every call appends to `logs/llm_calls.jsonl` with a `step` and
  `source_id` tag, so per-source cost, step count and wall-clock time come straight from the log
  rather than being estimated. Cost is computed from a price table in code (prices as of
  2026-11-03) and labelled as computed, not billed.
- **CKAN responses are cached on disk** (`data/raw/catalogue/cache/`), keyed by portal + action +
  params. Reruns are free and reproducible; the cache is gitignored but rebuilt automatically.
- **Portal endpoints differ.** data.gov.au, NSW, SA use `/data/api/3/action/`; QLD uses
  `https://www.data.qld.gov.au/api/3/action/`; VIC uses `https://discover.data.vic.gov.au/api/3/action/`.
- **ABN/ACN are validated by checksum** (`src/common/ids.py`), never by length alone. The ABN's last
  9 digits are not assumed to be the ACN.

## Part 1

- **Fully deterministic triage, no LLM calls** (decided 2026-11-11). Metadata score over the whole
  pool, then a content probe (headers, ABN checksum hits, company suffixes) on the top candidates.
  Reasons: free, reproducible, every score is traceable to a signal, and the content probe looks
  at actual rows, which is stronger evidence than a model reading titles.
- **Pool:** 18 queries × 5 portals × 50 rows → 2,895 records, 2,440 after de-duplication. data.gov.au
  harvests the state portals, so the same dataset appears twice; duplicates = same normalised
  title AND (same organisation OR a shared resource URL). The state-portal original is kept.
  Neutral queries (`*:*`, environment, transport) are in the pool on purpose so the scorer is
  tested on negatives.
- **Two-stage scoring.** Metadata score (named keyword signals, ±, plus a format bonus/penalty)
  over all 2,440; content probe on the top 120 only (reads ~200 real rows: share of
  checksum-valid ABNs, share of names ending in a company suffix, business-like headers).
  Final confidence = 0.35 × metadata + 0.65 × probe; unprobed datasets capped at 0.5 so an
  unverified dataset never outranks a verified one. This is a triage score only, not one of
  the ontology's three confidences.
- **Noise floors found by probing:** an ABN column needs ≥ 20% checksum-valid values (random
  11-digit numbers pass ~1.1% of the time); a company suffix must *end* the value
  ("Limited tender" is not a company). `ids.digits_only` now rejects values with letters or
  decimal points: a longitude (144.95000009) was passing the ABN checksum.
- **Hand check (20 random of 50, seed 20261111, labelled by Rahul):** 14 Y, 5 N, 1 U →
  **false-positive rate 26.3%** (5/19, unsure excluded); **30%** if the unsure one counts as a
  false positive. Rule applied: the *main* entity on most rows must be a non-government business.
  - 4 of 5 false positives share one cause: the rows carry business signals (ABNs, a company
    column) but the row is about a **person** (credit reps, financial advisers, SMSF auditors)
    or a **government body** (government schools). The probe scores the *best* column, so a
    secondary company column lifts a register of people.
  - The 5th (#20, childcare providers) is a boundary call: the reviewer counted foundations as
    not businesses, while licensed clubs were counted as businesses. If non-profits are counted
    as businesses, the rate is 21.1% (4/19). Both numbers are reported; the 26.3% stands.
  - The false positives are not at the bottom of the list (ranks 5, 11, 12, 18, 44), so the
    confidence is not well calibrated at the top: ABN presence alone is over-weighted.
- **Known probe weaknesses seen during the check:** multi-row headers (NSW liquor XLSX) produced
  header lines as "sample rows"; sample rows were cut at 30 columns, hiding supplier columns;
  two views of the same NSW liquor data (#7, #17) survived de-duplication because titles differ.
- **The 6 Part 2 sources (approved by Rahul):** ASIC Credit Licensee (Cth, TSV, register),
  QBCC Licensed Contractors (QLD, CSV, register), QLD Health Contract Disclosure (QLD, CSV,
  transactions, multi-supplier cells), Tenders WA Contract Awards 2023-24 (WA, CSV,
  "Trading (Legal)" names, no ABN), Victorian Liquor Licences by Location (VIC, XLSX, monthly
  snapshots), ACT Notifiable Invoices (ACT, JSON API, licence "Other" → recorded unknown + flagged).
  Chosen for 6 publishers / 5 jurisdictions / 4 formats / 2 shapes, and a measured mix of entity
  types inside sources (companies, people, trusts, partnerships, incorporated associations,
  government as supplier). Left out: multi-million-row ASIC Company / Business Names and the ABN
  Bulk Extract (random 1,000 rows would barely overlap; ZIP/XML) and all hand-check false positives.
- **Extraction volume:** small sources are extracted in full, large ones sampled evenly across the
  file (not the first N rows), to give Part 3 a fair chance of overlap without hand-picking records.
  Extraction is deterministic, so extra records cost $0; only inference is per-source.

## Part 2 (build block 1): engine + agent on ASIC and VIC (2026-11-12)

- **Architecture:** one generic engine (`src/engine/`, 12 whitelisted transforms, no source names) + an 8-step agent (`src/part2_agent/`): inspect, profile/split, propose x2, compare, validate (held-out, real engine), revise (max 2), critique, finalise, human gate. Each step checkpoints to `logs/agent_runs/<source>/`; re-running resumes.
- **Two independent proposals** (sample A vs sample B). Disagreements go to the revise step; fields they disputed are capped at field_confidence 0.70.
- **field_confidence = min(model's mapping confidence, measured parse rate)**, never an average. Fields with no judged held-out values are capped at 0.5. source_reliability is the model's judgement per claim kind (labelled as such, not measured).
- **derivation_level is computed from the transforms** (L0 cosmetic only; L1 parse/checksum/map), never claimed by the agent. Mapping the column itself was model-inferred; that is recorded in the config, not in the value's level.
- **Meaning checks in code** (legal vs trading name suffix rates, postcode/state agreement, future dates, split-needed, ABN/ACN overlap reported as evidence only). A warning must be answered (changed / kept + reason), not silently ignored.
- **Abstain, don't guess:** a field still failing validation after the revision budget is moved to `unmapped` by code. The agent also surfaced a real engine gap: VIC `address.state` needs a constant-value transform (`needs_transform`); we left it unmapped rather than infer VIC from the publisher.
- **Approval lock:** `configs/<source>.approval.json` stores the SHA-256 of the approved config; the engine refuses an unapproved or edited config (tested). Rejection comments feed a human-feedback revise round on the next `onboard` run.
- **Bugs found by running it:** BOM stuck to first header (fixed in reader, config regenerated, not hand-edited); critique step could not see envelope dates and falsely reported `valid_from` missing (fixed: critic now sees observed_at/valid_from/valid_to).
- **Run-to-run variation:** two ASIC runs differed (first run dropped licence dates as unmapped; second mapped them to valid_from/valid_to). Both defensible; shows why the human gate exists. Model was Haiku 5.5 throughout (no Sonnet run).
- **First-review result:** 14 of 14 fields marked right on first review (ASIC 8, VIC 6). Caveat: n is small and the reviewer judged from packet examples, so this is weak evidence of accuracy, not a benchmark.
- **Extraction:** 1,000 rows per source, evenly spaced. 11 VIC postcodes rejected (value '0'), 0 ASIC rejects.
- **Open decision:** sampling 1,000 of 4,313 (ASIC) and 23,169 (VIC) will thin cross-source overlap for Part 3. Extraction costs $0, so consider larger limits for small sources (brief allows ~1,000).

## Part 2 (build block 2): remaining four sources, extraction (2026-11-12)

- **Profile bug found and fixed:** the profile step only looked at 20,000 rows but compared distinct counts to the full row count ("20000 distinct of 206548"), so the agent wrongly treated real keys as non-unique and hashed rows (QBCC, ACT, VIC). Fixed to profile all rows; those three were regenerated by the agent (not edited) and re-approved. Record ids are now the sources' own keys (Licence Number / id / :id).
- **WA Tenders is the hard source.** Supplier names are "Trading (Legal)" in some rows and "Legal (Trading)" in others (409 of 3,260 bracketed names have the company suffix before the brackets; 44% have no brackets). First proposal split on brackets and swapped legal/trading for ~12% of bracketed names. Human rejected both name fields with that evidence; the agent's revision then dropped both name fields rather than guess. Result: WA has address, postcode, entity_type only; no name or ABN, so it cannot be linked and goes to the Part 3 unlinked queue. Chose NOT to add an engine transform (about +15 min; name-only links are the riskiest). A suffix-aware transform is a next-3-weeks item.
- **Known weakness:** WA contract Commencement/Final-expiry dates are mapped as valid_from/valid_to on address and type claims, which is questionable (contract term is not when an address became true). The approval table did not number these settings so they could not be marked wrong. Fix next: number every setting at the gate.
- **QBCC:** the agent mapped Licence Type DESC to entity_type, it failed validation (21% parse rate) and the abstain rule dropped it. Licence class held back as industry_code (needs a class-to-ANZSIC lookup the engine lacks).
- **Run-to-run variation:** VIC regenerated without address.full (Street Address left unmapped) where the earlier run joined street and suburb. Agent output is not deterministic; the approval hash makes each approved version exact.
- **Human review results:** first-review verdicts: 3 fields rejected out of the 6 sources' fields at first look (WA name fields x2 plus none elsewhere); all others right. See configs/*.approval.json for the exact rounds.
- **Extraction volumes (option A):** small sources in full (ASIC 4,313; QLD Health 210; WA 5,817), large ones 5,000 evenly spaced rows (VIC of 23,169; QBCC of 206,548; ACT of 127,437). Extraction costs $0.

## Part 2: seventh-source test (2026-11-12)

- **Command:** `python -m src.part2_agent.onboard <portal>:<dataset-name>` (or `--file path`) fetches an unseen dataset with its CKAN licence/dates, then runs the same agent. No column, format or mapping is chosen by a human.
- **Pick was not cherry-picked:** random.Random(7) over shortlist entries that were tabular and outside dataset families we had already covered (contracts/tenders/liquor/ASIC/QBCC). First draw (before excluding families) hit another QLD contract-disclosure report, too similar to QLD Health, so the rule was tightened and the same seed re-drawn. Picked `nsw:find-by-lia-band` (shortlist rank 38; licence unknown, flagged).
- **Result:** config v3 in 6 LLM calls, $0.019, about 2 minutes. It is a NSW register of licensed clubs/hotels (gaming machines). Agent mapped Licence Name as trading_name only (not legal_name: the data does not say it is the registered name), address.full and a suburb extraction; abstained on status, start date and all gaming columns, with reasons; critique step removed an unsupported entity.status and valid_from itself.
- **Honest limits:** under-fills legal_name (club names like "... Club Ltd" are probably legal names but the source does not say so); no ABN in this dataset, so it could not be linked by ID. The config is left pending review, not approved and not extracted: it demonstrates onboarding, it is not one of the six.

## Part 3: entity identification (2026-11-12)

- **Relationship model: link table + canonical entity key.** Pairwise, evidence-carrying links between source records are the primary data; clusters and keys are derived from accepted links only. Chosen because a wrong link can be removed and clusters recomputed, and every link can be re-scored later. Key = `abn:<11 digits>` when the cluster has one verified ABN, else `name:<hash of normalised name + state>`; a cluster with two different ABNs is never formed.
- **Tiers (matcher m1.0, deterministic, no LLM):** T1 equal checksum-valid ABN/ACN with agreeing names (0.98/0.96); T2 ACN equals last 9 of the other record's ABN with agreeing names (0.88); T3 exact normalised name: +postcode 0.85, +state 0.70, both companies with identical full name and no location 0.65, else refused. Scores are hand-set, NOT calibrated; calibration comes from the hand check, per tier.
- **Names must agree even when the ABN is equal** (containment >= 0.5 or a shared trading name). Reason, found by reading the refused pairs: QBCC lists individuals under their company's ABN (2,344 of 57,415 ABNs carry more than one licensee name), and ACT/QLD data has ABN/name disagreements (e.g. CBA vs Vantive). 23 pairs were refused on this rule.
- **No clustering by shared ABN inside a source** (it pulled persons into company clusters). Clusters form only from accepted cross-source links.
- **Person-like names are never linked on name alone,** but only when BOTH sides look like persons (first version used "either", which wrongly refused `WAVELENGTH INTERNATIONAL` vs `... Pty Limited`).
- **Parent/subsidiary:** no source states ownership, so none is inferred. The only relationship recorded is `acts_as_trustee_for` from "X Pty Ltd ATF The X Trust" patterns (13 found), kept as an edge, never merged. Similar names (Pty Ltd siblings) are not grouped.
- **Unlinked queue (5,850 items):** 5,817 WA records (no name, no identifier), 23 identifier-match-but-names-conflict, 7 name match without location evidence, 2 name match with different ABNs, 3 similar-but-not-exact names (e.g. Bacchus Marsh Finance vs Bowling Club, correctly refused).
- **Result:** 266 accepted links (all T1) over 40 cross-source entities; 119 loose links (T3 company-name). VIC overlaps another source on a single name; WA is unlinkable. Overlap is thin and concentrated in ACT x QLD Health (42 of the 50 checked links).
- **Hand check (50 links, seed 20261112), FINAL labels (see "Hand-check verification" below):** accepted 30 Y / 0 N / 0 U of 30 (100%, 95% CI 89-100%); loose 19 Y / 0 N / 1 U of 20 (100% excluding unsure, CI 83-100%; 95% counting unsure as wrong). 43 distinct businesses. (The first, AI-drafted labels were 23 Y / 7 U in the accepted band; they were superseded.) Caveats: narrow sample; the matcher already required names to agree, so the check is partly circular, an upper bound.
- **Weakness (revised after verification):** name containment >= 0.5 can pass on a shared generic word, e.g. Cantel (Australia) vs Steris Australia. That pair turned out to be a TRUE link (a registered rename), so the rule that "fixes" it (m1.1) was wrong; see below.
- **Not done:** refused pairs were not hand-checked (we do not know how many true links the names-conflict rule discarded); no cross-state same-name test; Tier 2 (ACN-in-ABN) produced zero links in this data.

## Part 4: company profiles (2026-11-12)

- **50 profiles:** 40 accepted-link entities (all there are) + 10 loose-only entities drawn with seed 20261112 from 16 available (10 more loose groups touch an accepted entity and were skipped; 0 were ambiguous). Each profile carries `trust: accepted | loose_only`; loose ones are lower-trust. One loose link (Stryker "Aust P/L") name-matches records carrying two different ABNs: no single pairwise hand check could show that. Profiles are built from accepted clusters, so the two Stryker ABNs stay two entities.
- **A profile is a transparent merge, not a reconciled row.** Per field: value, `variants` (spelling), `confidence` as separate numbers (field_confidence, source_reliability, agreement = sources agreeing out of sources stating), `decided_by`, per-record `provenance` (source, record id, extractor_version, observed_at, source field, raw value, and the link that attached the record with its link_confidence), and a `conflict` block listing every losing value with its reason. link_confidence appears only on links / attachment, never on a field.
- **Winner rule:** (1) more distinct SOURCES agree (a source repeating itself on 5 rows counts once); (2) higher source_reliability if the gap >= 0.05; (3) otherwise UNRESOLVED: both candidates are shown and no value is chosen. Claims with field_confidence < 0.6 are used only if nothing better exists. Spelling variants ("Pty Ltd" vs "P/L", capitals) are agreement, not conflict.
- **Removed "most recent wins".** First version used it (snapshot dates > 365 days apart) and it decided 9 of 13 name conflicts, e.g. ACT's "CANTEL (AUSTRALIA)" beating QLD Health's "STERIS AUSTRALIA" (a pair ABN Lookup later showed to be a registered rename: STERIS is the CURRENT name, so a recency rule would have picked the older name). Our observed_at is a file's last-modified date, not when the claim was made, so recency was a confident-looking guess. Equal evidence is now unresolved. Found by reading a real conflict, not by theory.
- **Address is resolved as one unit from one record** so a profile never mixes a street from one source with a postcode from another. Junk values are dropped (15 QLD Health addresses are just "0"). An entity with two different VIC premises (Metcash) has an unresolved address with both shown.
- **Unfillable fields are absent.** No source gave status, website, industry_code or date_registered, so none appear. Filled: legal_name 41 (9 more unresolved), abn 50, entity_type 45 (company only; "unknown" is not a claim), address.full 31, state 35, postcode 25, locality 5, acn 2; trading names on 3 profiles (one observation per name, no winner).
- **Conflicts:** 4 profiles with a resolved conflict (all legal_name); 10 profiles with something unresolved (9 legal_name, 1 address). Automated checks (no blank value, provenance on every value, every conflict lists losers and reasons) pass for all 50.
- **Source-deletion test (code, rebuilds all 50 with each source removed).** Two separate questions: corroboration (does the profile stop having 2+ sources) and content (does a value change or vanish). Results of 50: delete ACT: corroboration lost 47, identity (name/ABN) changed or lost 11, other field 3, unchanged 30. Delete QLD Health: corroboration lost 44, identity 2, other field (mostly address) 31, unchanged 15. Delete ASIC: 5 profiles lose address and corroboration, 1 identity change. Delete QBCC: 2 profiles lose ACN and address. Delete VIC: 1 profile (resolution only). WA appears in no profile (no names). Reading: the profile set is fragile to ACT and QLD Health because nearly every entity is an ACT x QLD Health pair; no single source deletion silently rewrites a name, since conflicts surface as `unresolved`, but ABN is lost in 9 profiles without ACT (QLD Health often lacks an ABN).
- **Known weaknesses:** thin profiles (name, ABN, type, address); "company" is the only entity_type we ever assert; source_reliability numbers are model judgements (ACT and QLD Health both 0.6), so they rarely separate values; 9 of 50 headline names are unresolved by design.

## Part 3 re-scoring and deliverables (2026-11-12)

- **Matcher m1.1** adds one rule computed only from stored link features: an identifier match whose names share only generic words (Australia, Group, Services, ...) is refused. `python -m src.part3_resolve.rescore --to m1.1` re-scored 420 stored links and refused pairs without reading any source: 2 accepted links demoted (Cantel/Steris, Tyco/Wormald), 418 unchanged; of the 50 hand-labelled links ONE was affected, and with the verified labels it is a YES (check 8, Cantel -> Steris). **m1.1 was therefore a regression and is rejected** (kept in the registry for lineage). Old links are not overwritten; the new file carries `previous` = {matcher_version, link_confidence, band}.
- **Superseded:** `links.jsonl` and profiles were regenerated with matcher m1.2 (below).
- **Write-up and README:** WRITEUP.md is about 1,200 words including markdown (aimed at two pages; render it to check the page count); all numbers come from logs/llm_calls.jsonl, configs/*.approval.json and handcheck/*.json. The README has a no-API-key path (download, extract, link, profile) that I ran piece by piece; I did not run it as one command sequence on a fresh clone.

## Clean-clone test (2026-11-12)

- Ran the README steps in a fresh clone: install + 37 tests + download + extract x6 + Part 3 + rescore + Part 4 took **24 seconds** (no API key).
- **Found:** QBCC is a live register: 206,595 rows vs 206,548 at onboarding, so the re-run gave 268 accepted links / 41 entities (committed: 266 / 40); 47 of the 50 hand-checked links still appear. Before the fix, `download` silently rewrote the recorded SHA-256, so `extract`'s changed-file refusal could not trigger on the clean path (the README wrongly said it would).
- **Fix:** `download` now compares with the committed manifest, prints a WARNING for any changed file and leaves the manifest unchanged unless `--refresh-manifest`. README and WRITEUP state the caveat; the committed outputs are the reference. Not done: pinning raw files (141 MB) in the repo.

## Hand-check verification and matcher m1.2 (2026-11-12)

- **Provenance of the labels.** The first Part 3 labels were drafted with an AI assistant: Rahul's chat reply named the exceptions (`U: 8, 18, 19, 24, 35, 49, 50`, all others Y) after the assistant had pointed out ten rows with differing names, and the assistant wrote them into the sheet. Rahul then re-checked ALL 50 rows on ABN Lookup (abr.business.gov.au) and wrote a note per row in `handcheck/part3_verify.csv`; those `my_label` values are the final labels (49 Y, 1 U). Changes vs the draft: 7 former U rows (8, 18, 19, 24, 35, 49, 50) became Y; check 23 (Culpan Medical) went Y -> U.
- **Final precision** (`handcheck/part3_link_result.json`): accepted (>= 0.80) 30/30 Y, 95% CI 89-100%; loose (0.60-0.80) 19 Y / 1 U of 20, 100% excluding unsure (CI 83-100%), 95% counting unsure as wrong; weighted over both bands 100% (98% counting unsure as wrong). The 50 rows are **43 distinct businesses** (repeats: 9/48, 20/45, 22/44, 28/37, 4/38, 14/40, 7/15); the intervals treat rows as independent, so they are slightly optimistic.
- **Findings from the verification.** (1) Cantel -> Steris, Everlight Limited -> Pty Ltd and Hologic (Australia & New Zealand) are true same-entity pairs whose names differ by rename, company-type change or shortening. The matcher accepted all three, but Cantel/Steris only because both names contain "Australia": a rename sharing no word would be refused (the 23 refused identifier-match pairs were never checked and may hold true links). ABN name history is the evidence to add next. (2) Check 15: the Stryker pair is the same business, but the ACT record carries J.J. Richards & Sons' ABN 40000805425 (Stryker's is 48002873850): a source error. (3) Check 23 stays unsure: ABN Lookup shows NSW 2000 throughout, record B says VIC 3189 and has no ABN. (4) Every name-only link checked (record B without an ABN) was correct or unsure, but with no address on either side a same-named different company cannot be ruled out from the data.
- **m1.1 rejected, m1.2 shipped.** Re-scoring with the verified labels shows m1.1 touches one labelled link and it is a yes: the labelled set caught a regression in the "improved" matcher. **m1.2 scores exactly like m1.0** and changes only canonical keys (next bullet). Registry: m1.0, m1.1 (rejected), m1.2 (current).
- **Key defect and fix.** Exactly one canonical_entity_key was shared by links whose names disagree: `abn:40000805425` held J.J. Richards' identifier links AND the loose Stryker link (it borrowed the ACT record's wrong ABN). m1.2 re-keys a name-only (T3) link by name + state when none of its names agree with the identifier links under the same ABN key (`src/part3_resolve/keys.py`; pure function of stored evidence, so `rescore` applies it too; unit tests cover the Stryker case). Result of re-running Part 3, rescore and Part 4: 1 link re-keyed (Stryker, to a name key); accepted/loose link counts (266/119), entities (40), queue (5,852) and all 50 profile keys unchanged; no profile contains a Stryker record with J.J. Richards' ABN, before or after. `link_id` hashes the matcher version, so a full re-run issues new ids; `rescore` keeps the old id.
- **QLD Health finding.** 24 of 433 legal_name observations (from 7 source records) are comma-joined multi-supplier cells left unsplit (the config's needs_transform says a split on ',' is unsafe because addresses contain commas) yet carry field_confidence 0.9; they should have been lowered or abstained. A 25th comma value is a person name ("WILKINSON, KANE EDWARD"), not a supplier list.

## Step 4a: regex_replace, template, constant, conditional mapping (2026-11-13)
Owner decisions (final), from reviews/step4a_plan.md section 9:
1. **Regex safety = A.** A 1-second per-value timer plus a 200-character limit and a compile check. The timer uses SIGALRM, so it is **Unix-only** and main-thread-only (Windows and worker threads get only the length and compile checks). It nests inside the tool timer: verified before building that the outer remaining time is restored and that the outer timer wins when it would fire first.
2. **Template with a blank part = reject** (`template_missing_part`); it counts against the 90% floor.
3. **Constant confidence cap = B**, a constant 0.5 (under Part 4's 0.6 low-trust line); section c's 0.6 was edited.
4. **`when` per field = A**, `when_not_met` is a skip, no ordering between fields.
5. **Literal text in `template` / `repl` = A**, separators and group references only.
Build notes: the uncompilable-pattern crash in `regex_extract` is fixed in the shared helper (`run_regex`). `repl` is checked by one substitution on an empty string (verified: a bad group reference raises even with no match). Small choices: `P_TRANSFORMS` lives in `engine/config.py`; round-1 `llm_steps.py` keeps the original 12 names through `ROUND1_CATALOGUE`; `_evidence_specs` tuples carry `when` as a fifth element.

## Step 6B: Business Names row filter (2026-11-13)
Owner decisions (final), from reviews/step6_plan.md: 1=B filter keys are ABN + name key; 2=B T3c disabled (a second Business Names hit is not independent), T3 kept, no-ABN links hand-judged; 3=A agent onboarding; 4=A trimmed result committed with attribution. Companies register, T1r and T3c are designed, not built; offline fallback is Business Names only and outputs must say Companies and ABR features are absent.
- `keep_where` (column, equals) is an explicit row-filter condition; `BN_STATUS == Registered` is applied there and is NOT mapped to entity.status. The approved-style config has no `keep_where` key (configs are agent-written, never hand-edited), so it is passed as `--keep-where`; the filter also reads a `keep_where:` from the config if an agent ever writes one.
- Name key = the matcher's `name_core` (legal and trading names of every mention), no state: the register's state is where the name is registered, not the holder's address. Result: 3,867 of 3,312,255 rows kept in ~17 s (`docs/runbook.md`).

## Step 7b1: reference sources, Business Names lookups, generic-name threshold (2026-11-13)
- `configs/reference_sources.yaml` (hand-written, R1) lists reference registers; `load_mentions` skips them; the row filter reads path and `keep_where` from it (CLI flags override). Supersedes the "pass --keep-where" note in step 6B.
- Holder uniqueness (R4): holders = distinct valid ABNs, each blank-ABN row its own holder; a name with more than one holder is refused. Over the 5,224 distinct mention names (legal + trading, normalised): 961 hit exactly one holder, **14 refused** (more than one holder).
- State / postcode derived from `address.full` (L1, only where the source gave none; a state is never inferred from a postcode): 86 mentions gain a state, 1,056 a postcode (mostly the WA tender addresses, which end in a bare postcode). This changes matcher inputs (postcode/state evidence) only when Part 3 is re-run in 7b2.
- **GENERIC_MIN_WEIGHT = 14.02**, set before any labels were viewed. Summed IDF weight of the normalised name (suffix words dropped) over the 5,224 distinct mention names: min 5.56, p5 14.02, p10 14.66, median 23.23. So about 5% of mention names count as generic. The weights depend on the IDF corpus, so the threshold is a version-stamped constant: rebuild the cache and the weights move.
