# Runbook

## Business Names row filter (step 6)
`python -m src.engine.row_filter asic_business_names --raw data/raw/reference/business_names_202611.zip --keep-where BN_STATUS=Registered`

Full 247 MB register (zip read, streamed, no LLM): **16.9 s** (an earlier identical run: 18.9 s), on the dev laptop,
2026-11-13. Rows kept / total: **3,867 / 3,312,255** (Registered rows whose ABN or name key is in the six sources'
mentions). Trimmed file 0.98 MB in `data/reference/`, attribution beside it.
