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
