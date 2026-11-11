# Decisions

Notable design decisions and why. Feeds WRITEUP.md.

## Setup

- **LLM provider: Claude API (official `anthropic` SDK).** Dev on `claude-haiku-5-5`, final runs on
  `claude-sonnet-5-5`. All provider code lives in `src/llm.py`; nothing else imports `anthropic`,
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
- **Run-to-run variation:** two ASIC runs differed (first run dropped licence dates as unmapped; second mapped them to valid_from/valid_to). Both defensible; shows why the human gate exists. Model was Haiku (dev); final runs on Sonnet.
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
- **Hand check (50, labelled by Rahul, seed 20261112):** accepted 23 Y / 0 N / 7 U of 30 (unsure excluded: 100%, 95% CI 86-100%; unsure counted wrong: 76.7%); loose 20 Y / 0 N / 0 U of 20 (100%, CI 84-100%). All 7 U are ABN-equal links whose names differ (e.g. Cantel vs Steris, Hartwigs vs Hartwigs Trucks). Caveats: narrow sample; the matcher already required names to agree so the check is partly circular, an upper bound.
- **Known weakness:** name containment >= 0.5 passes on a shared generic word ("Australia"), e.g. Cantel (Australia) vs Steris Australia. A rarity-weighted name score (down-weight "australia", "group", "services") is the first fix.
- **Not done:** refused pairs were not hand-checked (we do not know how many true links the names-conflict rule discarded); no cross-state same-name test; Tier 2 (ACN-in-ABN) produced zero links in this data.
