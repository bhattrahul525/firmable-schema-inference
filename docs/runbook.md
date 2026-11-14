# Runbook

## Business Names row filter (step 6)
`python -m src.engine.row_filter asic_business_names` (file path and keep_where BN_STATUS=Registered come from configs/reference_sources.yaml; `--raw` and `--keep-where` override)

Full 247 MB register (zip read, streamed, no LLM): **16.9 s** (an earlier identical run: 18.9 s), on the dev laptop,
2026-11-13. Rows kept / total: **3,867 / 3,312,255** (Registered rows whose ABN or name key is in the six sources'
mentions). Trimmed file 0.98 MB in `data/reference/`, attribution beside it.

## Demo command sequence (new source, end to end)
```bash
python -m src.part2_agent.onboard <file, URL or portal:dataset> --source-id <id> --max-dollars 0.5
python -m src.part2_agent.approve <id>
python -m src.engine.extract <id>                      # resolve only reads approved AND extracted sources
python -m src.engine.row_filter asic_business_names --out data/reference/demo_trimmed.csv   # needs the full register zip
export BN_TRIMMED=data/reference/demo_trimmed.csv      # resolve, graph, profiles read this instead of the tracked file
python -m src.part3_resolve.run                        # prints "sources (N): ..." first: check your id is listed
python -m src.part3_resolve.graph
python -m src.part4_profiles.profiles
python -m src.part4_profiles.show <id>
```
Timings: TBD (to be measured). Resolve, graph and profiles read every approved, extracted source (six base sources plus
others; `src/part3_resolve/sources.py`); reference registers are excluded. Without extra sources the six-source results are
unchanged. Skip `--out` and `BN_TRIMMED` to overwrite the tracked trimmed file (the default). Re-running resolve with a new
source also shifts the name-rarity counts, so existing links can move; commit the outputs only if you mean to.

## Full register needed by resolve
`resolve` (IDF) stops with an error unless `data/raw/reference/business_names_202611.zip` exists. Download it from https://data.gov.au/data/dataset/asic-business-names (CC BY 3.0 AU). Pipeline order: onboard, approve, extract, `python -m src.part3_resolve.run`, `python -m src.part3_resolve.graph`, `python -m src.part4_profiles.profiles`, `show`. These last four take no flags; `--help` runs them.

## Token-count cache for IDF (step 7a)
`python -c "from src.part3_resolve.idf import load_idf; load_idf()"` (first call streams the full 247 MB register;
later calls read the cache). One-time build: **15.5 s** (2,978,106 Registered names with a token), cache
`data/cache/bn_token_counts.json` **8.2 MB**, git-ignored; cached load 0.3 s. Rebuilt automatically if the register
file's name or size changes.
