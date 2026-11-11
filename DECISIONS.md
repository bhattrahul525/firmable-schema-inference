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
