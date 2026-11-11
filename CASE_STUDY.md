# Case Study: Schema Inference and Agentic Ingestion Systems

**Technical Assignment: Schema Inference and Entity Identification at Scale (Firmable)**

> Source: the Firmable Notion page "Case study - Schema Inference and agentic ingestion systems".
> The brief below is reproduced in full. The canonical ontology ([firmable_ontology.yaml](firmable_ontology.yaml)) is summarised and reproduced near the end, followed by a quick-reference checklist.

---

## At a glance

| Item | Value |
| --- | --- |
| Time box | **6 hours total** (not per day) |
| Return window | Within **7 days** of receiving it (ask if you need more time) |
| API budget | Designed to cost **under USD $10**. Report your actual spend (keep receipts) |
| AI tools | Expected. You must be able to explain every line |
| Local models | Acceptable, judged on the same terms |
| Core requirement | **Part 2 must be agentic**: a multi-step agent that infers schema and writes mapping configs at runtime for a source it has never seen |
| Submission | Git repo or zip with `README.md`, code, `WRITEUP.md`, and all outputs |

---

## Before you start

**Time box: 6 hours.** Not 6 hours per day; 6 hours total. We would rather see a well-reasoned partial solution than a complete one that took a weekend. If you run out of time, stop, and tell us in the write-up what you would have done next. How you spend a fixed budget is part of what we are assessing.

**Window:** please return it within 7 days of receiving this. Tell us if that does not work and we will move the date.

**AI tools are expected, not tolerated.** Use Claude, GPT, Cursor, whatever you normally use. This task is about building a system that uses models to do work at scale; pretending you would build it by hand would tell us nothing. We do ask that you can explain every line you submit.

**The system itself has to be agentic.** This is the part candidates most often get wrong, so we are being explicit. Using Cursor to help you write a parser is not what we are asking for. We are asking you to build a multi-step agent that does the schema inference and mapping work itself, at runtime, on a source it has not seen before. The test is simple: if we handed your submission a seventh dataset tomorrow, could it produce a mapping config without you writing anything? If the answer is no, you have built the wrong thing, however good the code is. This applies to Part 2. Part 1 can be as deterministic as you like.

**Cost:** the task is designed to cost under USD $10 in API spend. Keep your receipts; we ask you to report actual spend. If you would rather not use paid APIs, a local model is completely acceptable and we will judge the result on the same terms.

---

## Context

Firmable maintains a resolved graph of Australian and New Zealand businesses, roughly 15 million companies today. The problem we are solving is that adding a new public data source currently costs an engineer several weeks: someone reads the schema, writes a connector, writes a transformer, and writes the logic that links each record to the right company.

There are thousands of useful public sources: company registers, building approvals, trade licences, workplace safety notices, court lists, procurement contracts. At an engineer-month per source, the ten-thousandth source is never worth loading. We think that maths changed. We want to find out whether adding a source can become **a review rather than a build**: a model infers the schema, proposes the mapping, and a human approves it.

This assignment is a small, real version of that problem.

Two things we care about more than most teams:

1. **A wrong link is worse than no link.** One bad merge quietly corrupts every answer built on top of it. We would always rather return nothing.
2. **Config beats code.** A solution that works for six sources because you wrote six parsers has not solved anything. A solution that works for six sources because you wrote one engine and six config files might.
3. **The configs have to be written by the agent, not by you.** One engine plus six hand-authored configs is the same problem as six parsers, moved sideways. The agent inspects the source, proposes the mapping, checks its own work, and emits the config. Your job is the system that does that, and the review step a human uses to accept or reject what it produces.

---

## The task

### Part 1: Discovery and triage

`data.gov.au` exposes a CKAN Action API at `https://data.gov.au/data/api/3/action/` over a catalogue of 100,000+ datasets. No API key required. Useful actions: `package_search`, `package_show`, `resource_search`. State portals (`data.nsw.gov.au`, `data.qld.gov.au`, `data.vic.gov.au`, `data.sa.gov.au`) run the same API if you want more breadth.

**Deliverable:** from a pool of at least 200 catalogue records you retrieved programmatically, produce a **ranked shortlist of 50 datasets that plausibly contain identifiable Australian business entities.**

Rules:

- The shortlist must be produced by code, not by you reading titles. Hand-picking 50 datasets is a different and much easier task.
- Agentic triage is a bonus here, not a requirement. Cheap deterministic filtering ahead of any model call is a perfectly good answer at this stage, and if that is what you do, tell us why. The agentic requirement applies to Part 2.
- For each of the 50, output: dataset ID, title, publishing organisation, resource format(s), your confidence that it contains business entities, and a one-line reason.
- Tell us your false positive rate. Hand-check a random sample of 20 of your 50 and report how many actually contain business entities. We are more interested in this number being honest than in it being high.

Output as CSV or JSONL.

### Part 2: Schema inference and canonical mapping

Choose **6 datasets** from your shortlist that you can actually download, and that are as different from each other as you can manage: different publishers, different formats, different shapes. At least one should not be a clean CSV.

Map each one to the canonical ontology in the attached `firmable_ontology.yaml`.

**Deliverable:** for each source, a **mapping config**, a machine-readable file that describes how to get from that source's raw records to canonical observations. Plus **one generic extractor** that reads a config and produces output. Six configs and one engine; not six scripts.

**The configs must be generated by a multi-step agent.** A single prompt that swallows a sample and returns a mapping is not enough, and it will not hold up on the messier sources. We expect to see a pipeline with distinct steps, something along the lines of: inspect the resource and work out what it actually is, sample it, propose a mapping against the ontology, validate that proposal by running it over records it has not seen, and revise where it fails. How you decompose it is your call. What we want to see is state carried between steps, a model correcting its own output rather than being corrected by you, and a clear point at which a human is asked to approve.

Tell us the step count, the token cost and the wall-clock time for onboarding one source, and where a run can fail without losing the whole job.

Each mapping should record, per field: the source field it came from, the canonical field it maps to, any transformation applied, and your confidence in the mapping. Fields you could not map confidently should be left unmapped and listed, not guessed at.

Run the extractor over a sample of each source (1,000 records is plenty) and output canonical observations.

### Part 3: Entity identification

Across the six sources you just processed, find businesses that appear in more than one of them.

The ontology file covers what an entity looks like. It deliberately says nothing about how entities relate to each other, or how you represent the fact that two records are the same business. That part is yours to design. Whether you model it as a cluster, a canonical key, a pairwise link table, a graph, or something else, we want to see the model you chose and the reasoning. Sources will also hint at relationships between different businesses, parent and subsidiary being the obvious one. Do something sensible with that or explain why you left it alone.

**Deliverable:**

- A set of proposed links: `{source_a_record, source_b_record, canonical_entity_key, confidence, evidence}`.
- An **unlinked queue**: records you believed contained a business but deliberately refused to link, and why. This is not a list of failures. We want to see where you drew the line.
- **Measured precision.** Hand-check 50 of your proposed links and report how many are correct. Tell us the threshold you used and what precision you got at that threshold. If you also want to report what happens at a looser threshold, we would find that interesting.

You do not need prior entity resolution experience to do this well. We are looking at how you reason about it, not whether you already know the standard techniques.

### Part 4: Company profile

Take 50 of the entities you linked and produce a **company profile** for each: one record per business, merging what all six sources say about it.

**Deliverable:**

- One profile per entity, with a confidence on **each field**, not a single score for the whole profile. A profile can be highly confident about a name and barely confident about an address, and that has to be visible.
- Provenance per field: which source record the value came from.
- Where sources disagree, show your working. Which value won, why, and what the losing values were. Silently picking one is the failure mode we are looking for.
- Fields you could not fill should be absent, not blank and not guessed.
- A short note on what happens when a source is wrong. If we deleted one of your six sources, how many profiles change and how badly?

Format is up to you. One JSON object per entity is fine.

### Part 5: Write-up

**Two pages maximum.** Bullets are fine. Cover:

1. **Cost.** What did it actually cost, in dollars and tokens, to onboard one source? Break out the one-time inference cost from the per-record cost. If your answer is "I don't know", say so; if it is a guess, label it as one.
2. **Agent design.** How did you decompose the work into steps, and why that way? Where does the agent check itself, what happens when a step fails, and what does a human actually see when they are asked to approve? Tell us which step is the weakest and how you know.
3. **The hard one.** At least one of your six sources will have resisted. Which, why, and what would you do about it, noting that "write custom code for this one" is sometimes the correct answer, and we want to know how you decide when.
4. **Scale.** What breaks between 6 sources and 500? Be specific about which component fails first.
5. **Change.** Six months from now you improve the matching model. There are millions of existing links made by the old one. What do you do, and what do you need to have recorded in advance to be able to do it? *This is the question we are most interested in.*
6. **Next.** With three weeks instead of six hours, what would you build first?

Also tell us how you modelled entity relationships in Part 3 and why, in a few lines. We left that open on purpose and the choice tells us more than the implementation does.

---

## What to submit

A git repository (or a zip) containing:

- `README.md`: how to run it, from a clean checkout, in under 10 minutes
- Your code
- `WRITEUP.md`: Part 5
- Outputs: the shortlist, the six mapping configs, the canonical observations, the proposed links, the unlinked queue, the 50 company profiles
- Anything you used to hand-check precision

It must run. If something is broken, say so in the README rather than leaving us to find it.

---

## How we will assess it

Roughly in this order:

| Criterion | What they're looking at |
| --- | --- |
| **Is it agentic?** | Part 2 built as a multi-step system that maps a source it has not seen, or a person doing the mapping with AI help |
| **Does it generalise?** | One engine and six configs, or six scripts wearing a trench coat |
| **Mapping quality** | Correct, and honest about what it could not map |
| **Resolution judgment** | Sensible confidence, real abstention, measured precision |
| **Profile assembly** | Field-level confidence, visible conflict handling, provenance kept |
| **Measurement** | You know your own numbers and did not round them in your favour |
| **Engineering** | It runs, it is legible, it is reproducible |
| **Judgment** | The write-up |

**Things that will count against a submission:**

- Mapping configs you wrote by hand
- A single prompt doing the whole inference with no validation or revision step
- Per-source hand-tuned parsers
- A single blended confidence score covering several different kinds of uncertainty
- Links reported without a precision number
- 100% coverage claims
- Ignoring the licence terms attached to a dataset

We are not scoring English. Write however you write.

---

## Questions

Ask them. Sending this task and then penalising you for clarifying it would be a strange thing for us to do. If something is ambiguous, either ask or make a decision and note it in the README; both are fine.

---

## Canonical ontology (`firmable_ontology.yaml`, v0.1)

This is a deliberately small slice of Firmable's real ontology. **Treat it as a contract: mapping configs must target these field names exactly.**

### Two core ideas

1. **An observation is a claim, not a fact.** It is something a source stated at a point in time. Five sources saying five different things about one company produce five observations, not one curated value. **Do not reconcile at ingest**; reconciliation happens later (Part 4).
2. **Confidence is not one number.** "This record says ABC Pty Ltd", "this record is entity 874219" and "ABC is probably expanding" are different claims with different failure modes. Keep them apart.

### `entity` fields

| Field | Type | Constraint / values | Notes |
| --- | --- | --- | --- |
| `legal_name` | string | | As registered. Not the trading name. |
| `trading_name` | string | | May be multiple. **Emit one observation each.** |
| `abn` | string | `^\d{11}$` | Australian Business Number. Has a checksum: **validate it, do not just length-check.** |
| `acn` | string | `^\d{9}$` | Australian Company Number. Also checksummed. The last 9 digits of an ABN are often the ACN, **but not always.** |
| `nzbn` | string | `^\d{13}$` | New Zealand Business Number, if you hit an NZ source. |
| `entity_type` | enum | `company`, `sole_trader`, `partnership`, `trust`, `incorporated_association`, `government`, `other`, `unknown` | **Default to `unknown`. Guessing here causes downstream harm.** |
| `status` | enum | `active`, `deregistered`, `in_liquidation`, `suspended`, `unknown` | |
| `website` | string | | |
| `industry_code` | string | | ANZSIC where available. **Record the raw source value too.** |
| `date_registered` | date | | |

### `address` fields

| Field | Type | Constraint / values | Notes |
| --- | --- | --- | --- |
| `full` | string | | |
| `locality` | string | | |
| `state` | enum | `NSW`, `VIC`, `QLD`, `WA`, `SA`, `TAS`, `ACT`, `NT`, `NZ`, `OTHER` | |
| `postcode` | string | | |
| `country` | string | default `AU` | |

### `observation` envelope (every emitted record carries it; no exceptions)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `source_id` | string | ✅ | Stable identifier for the dataset the claim came from. |
| `source_record_id` | string | ✅ | Must trace back to the exact raw record. If the source has no key, **construct a deterministic one and document how.** |
| `observed_at` | datetime | ✅ | When the source stated it. |
| `ingested_at` | datetime | ✅ | When you read it. Different from `observed_at`; both matter. |
| `valid_from` | date | | When the claim became true in the world, if the source says. |
| `valid_to` | date | | Null means still current as far as this source knows. |
| `licence` | string | ✅ | From dataset metadata (CKAN exposes it). No clear licence is a finding, not a blocker: **record `unknown` and flag it.** |
| `extractor_version` | string | ✅ | Which version of the mapping config and engine produced this. "You will be glad of it later." (This ties directly to Write-up Q5, re-matching after a model change.) |

### `confidence`: three separate scores, never blended

| Score | Range | Meaning | Where it applies |
| --- | --- | --- | --- |
| `source_reliability` | 0–1 | How much we trust this publisher on this kind of claim | Per source / claim type |
| `field_confidence` | 0–1 | How sure we are that we mapped and parsed this field correctly | Per mapped field / observation |
| `link_confidence` | 0–1 | How sure we are that this record refers to that entity | **Only on links** |

### `derivation_level` (optional; use it if it helps)

| Level | Meaning |
| --- | --- |
| L0 | A source stated it directly. |
| L1 | Computed deterministically from L0 (parsing, normalising, checksums). |
| L2 | Derived statistically. |
| L3 | A model inferred it. |
| L4 | Inference on top of inference. Capped in production. |

### Full file (verbatim)

```yaml
# Firmable canonical ontology — assignment subset v0.1
#
# This is a deliberately small slice of the real ontology, enough to do the task.
# Treat it as a contract: your mapping configs target these field names exactly.
#
# Two ideas matter here.
#
# 1. An OBSERVATION is a claim a source made at a point in time. It is not a fact.
#    Five sources saying five different things about one company produce five
#    observations, not one curated value. We reconcile later; you do not reconcile
#    at ingest.
#
# 2. Confidence is not one number. "This record says ABC Pty Ltd", "this record is
#    entity 874219" and "ABC is probably expanding" are different claims with
#    different failure modes. Keep them apart.

version: 0.1

entity:
  legal_name:
    type: string
    notes: As registered. Not the trading name.
  trading_name:
    type: string
    notes: May be multiple. Emit one observation each.
  abn:
    type: string
    pattern: '^\d{11}$'
    notes: Australian Business Number. Has a checksum — validate it, do not just length-check.
  acn:
    type: string
    pattern: '^\d{9}$'
    notes: Australian Company Number. Also checksummed. The last 9 digits of an ABN are often the ACN, but not always.
  nzbn:
    type: string
    pattern: '^\d{13}$'
    notes: New Zealand Business Number, if you happen to hit an NZ source.
  entity_type:
    type: enum
    values: [company, sole_trader, partnership, trust, incorporated_association, government, other, unknown]
    notes: Default to unknown. Guessing here causes downstream harm.
  status:
    type: enum
    values: [active, deregistered, in_liquidation, suspended, unknown]
  website:
    type: string
  industry_code:
    type: string
    notes: ANZSIC where available. Record the raw source value too.
  date_registered:
    type: date

address:
  full:
    type: string
  locality:
    type: string
  state:
    type: enum
    values: [NSW, VIC, QLD, WA, SA, TAS, ACT, NT, NZ, OTHER]
  postcode:
    type: string
  country:
    type: string
    default: AU

# Every emitted record carries this envelope. No exceptions.
observation:
  source_id:
    type: string
    required: true
    notes: Stable identifier for the dataset the claim came from.
  source_record_id:
    type: string
    required: true
    notes: Must be traceable back to the exact raw record. If the source has no key, construct a deterministic one and document how.
  observed_at:
    type: datetime
    required: true
    notes: When the source stated it.
  ingested_at:
    type: datetime
    required: true
    notes: When you read it. These are different and both matter.
  valid_from:
    type: date
    notes: When the claim became true in the world, if the source says.
  valid_to:
    type: date
    notes: Null means still current as far as this source knows.
  licence:
    type: string
    required: true
    notes: >
      From the dataset metadata. CKAN exposes it. If a source has no clear licence,
      that is a finding, not a blocker — record 'unknown' and flag it.
  extractor_version:
    type: string
    required: true
    notes: >
      Which version of your mapping config and engine produced this. You will be
      glad of it later.

# Keep these separate. Do not blend them into one score.
confidence:
  source_reliability:
    type: float
    range: [0, 1]
    notes: How much do we trust this publisher on this kind of claim.
  field_confidence:
    type: float
    range: [0, 1]
    notes: How sure are we that we mapped and parsed this field correctly.
  link_confidence:
    type: float
    range: [0, 1]
    notes: How sure are we that this record refers to that entity. Only on links.

# Optional: use it if it helps you, ignore it if not.
derivation_level:
  L0: A source stated it directly.
  L1: We computed it deterministically from L0 (parsing, normalising, checksums).
  L2: We derived it statistically.
  L3: A model inferred it.
  L4: Inference on top of inference. We cap this in production.
```

---

## Quick-reference checklist

### Part 1: Discovery and triage
- [ ] Programmatically retrieve **≥200** catalogue records (data.gov.au CKAN, optionally state portals)
- [ ] Produce a code-generated, ranked shortlist of **50** datasets (CSV or JSONL)
- [ ] Per row: dataset ID, title, publishing org, resource format(s), confidence, one-line reason
- [ ] Hand-check a random **20 of 50** and report the false positive rate honestly
- [ ] If triage is deterministic (no model), explain why

### Part 2: Schema inference and mapping (must be agentic)
- [ ] Choose **6** downloadable, diverse datasets (different publishers, formats, shapes; **at least one not a clean CSV**)
- [ ] Multi-step agent: inspect → sample → propose mapping → validate on unseen records → self-revise → **human approval gate**
- [ ] State carried between steps; the model corrects its own output
- [ ] **6 agent-generated mapping configs** plus **1 generic extractor**
- [ ] Per field in each config: source field, canonical field, transformation, confidence
- [ ] Unmapped fields listed explicitly, not guessed
- [ ] Configs target the ontology field names **exactly**
- [ ] Every observation carries the full envelope: `source_id`, `source_record_id`, `observed_at`, `ingested_at`, `licence`, `extractor_version` (plus `valid_from`/`valid_to` where known)
- [ ] Deterministic `source_record_id` for keyless sources, with the construction documented
- [ ] ABN and ACN validated by **checksum**, not just length; ACN ≠ ABN[-9:] assumed only when verified
- [ ] `entity_type` defaults to `unknown` (no guessing); `industry_code` keeps the raw source value
- [ ] One observation per `trading_name`
- [ ] No reconciliation at ingest: conflicting claims stay as separate observations
- [ ] Missing licence recorded as `unknown` and flagged
- [ ] Keep `source_reliability`, `field_confidence` and `link_confidence` separate (optionally tag `derivation_level` L0–L4)
- [ ] Run the extractor on about **1,000 records per source** and output canonical observations
- [ ] Report step count, token cost, and wall-clock time per source onboarding
- [ ] Explain where a run can fail without losing the whole job (resumability)
- [ ] Respect dataset licence terms

### Part 3: Entity identification
- [ ] Design and justify an entity-identity model (cluster / canonical key / link table / graph / other)
- [ ] Handle or explicitly defer inter-business relationships (e.g. parent/subsidiary)
- [ ] Proposed links: `{source_a_record, source_b_record, canonical_entity_key, confidence, evidence}`
- [ ] Unlinked queue with reasons (deliberate abstentions)
- [ ] Hand-check **50 links**; report the threshold and precision (optionally also a looser threshold)

### Part 4: Company profiles
- [ ] **50** merged profiles, one per entity
- [ ] Per-field confidence (not a single profile score)
- [ ] Per-field provenance (source record)
- [ ] Conflicts shown: winning value, why it won, losing values
- [ ] Unfillable fields absent (not blank, not guessed)
- [ ] Source-deletion impact note: how many profiles change, and how badly

### Part 5: `WRITEUP.md` (2 pages max)
- [ ] Cost: dollars and tokens per source; one-time inference vs per-record cost (label guesses)
- [ ] Agent design: steps, self-checks, failure handling, what the human reviewer sees, the weakest step and how you know
- [ ] The hard source: why it resisted, and when custom code is the right call
- [ ] Scale: what breaks first going from 6 to 500 sources
- [ ] Change: re-matching millions of old links after a model upgrade, and what must be recorded in advance (**most important**)
- [ ] Next: what you'd build first with 3 weeks
- [ ] A few lines on how entity relationships were modelled in Part 3, and why

### Submission
- [ ] `README.md`: runs from a clean checkout in under 10 minutes; note anything broken and any assumptions made
- [ ] Code
- [ ] `WRITEUP.md`
- [ ] Outputs: shortlist, 6 configs, canonical observations, links, unlinked queue, 50 profiles
- [ ] Precision hand-check materials
- [ ] Actual API spend reported

### Guiding principles
- **A wrong link is worse than no link.** Prefer abstaining.
- **Config beats code.** One engine, many configs.
- **The agent writes the configs**, not you. The human reviews and approves.
- Be honest with your numbers: no 100% coverage claims, no flattering rounding.
