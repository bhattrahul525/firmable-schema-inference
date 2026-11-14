# Runbook

## Business Names row filter (step 6)
`python -m src.engine.row_filter asic_business_names` (file path and keep_where BN_STATUS=Registered come from configs/reference_sources.yaml; `--raw` and `--keep-where` override)

Full 247 MB register (zip read, streamed, no LLM): **16.9 s** (an earlier identical run: 18.9 s), on the dev laptop,
2026-11-13. Rows kept / total: **3,867 / 3,312,255** (Registered rows whose ABN or name key is in the six sources'
mentions). Trimmed file 0.98 MB in `data/reference/`, attribution beside it.

## Full register needed by resolve
`resolve` (IDF) stops with an error unless `data/raw/reference/business_names_202611.zip` exists. Download it from https://data.gov.au/data/dataset/asic-business-names (CC BY 3.0 AU). Pipeline order: onboard, approve, extract, `python -m src.part3_resolve.run`, `python -m src.part3_resolve.graph`, `python -m src.part4_profiles.profiles`, `show`. These last four take no flags; `--help` runs them.

## Token-count cache for IDF (step 7a)
`python -c "from src.part3_resolve.idf import load_idf; load_idf()"` (first call streams the full 247 MB register;
later calls read the cache). One-time build: **15.5 s** (2,978,106 Registered names with a token), cache
`data/cache/bn_token_counts.json` **8.2 MB**, git-ignored; cached load 0.3 s. Rebuilt automatically if the register
file's name or size changes.
