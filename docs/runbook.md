# Runbook

## Business Names row filter (step 6)
`python -m src.engine.row_filter asic_business_names --raw data/raw/reference/business_names_202611.zip --keep-where BN_STATUS=Registered`

Full 247 MB register (zip read, streamed, no LLM): **16.9 s** (an earlier identical run: 18.9 s), on the dev laptop,
2026-11-13. Rows kept / total: **3,867 / 3,312,255** (Registered rows whose ABN or name key is in the six sources'
mentions). Trimmed file 0.98 MB in `data/reference/`, attribution beside it.

## Token-count cache for IDF (step 7a)
`python -c "from src.part3_resolve.idf import load_idf; load_idf()"` (first call streams the full 247 MB register;
later calls read the cache). One-time build: **15.5 s** (2,978,106 Registered names with a token), cache
`data/cache/bn_token_counts.json` **8.2 MB**, git-ignored; cached load 0.3 s. Rebuilt automatically if the register
file's name or size changes.
