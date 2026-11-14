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
Timings (MacBook, Haiku 5.5 agent, 121-row Australian modern slavery sample, 2026-11-15): onboard 31-45 s ($0.007); re-onboard after a rejection 31 s ($0.007); extract 0.08 s; register row filter 17 s (streams the full register zip once); resolve 0.8 s; graph 0.3 s; profiles 0.2 s; show 0.03 s. Machine time for the whole path is about one minute; the approval step is human time. Resolve, graph and profiles read every approved, extracted source (six base sources plus
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

## Demo notes
1. Onboard a new file: `python -m src.part2_agent.onboard <file> --source-id <id> --max-dollars 0.5`.
2. Approve: `python -m src.part2_agent.approve <id>`. Mark ONE field wrong with a comment to show the reviewer loop, then run
   the command approve prints (it re-onboards with the comment and archives the old trace as `trace.round<N>.jsonl`), then approve again.
3. Then extract, filter (`--out`, `BN_TRIMMED`), resolve, graph, profiles, show, as in the sequence above.
4. A good example entity in the 121-row sample: MENZIES INTERNATIONAL (AUST.) PTY. LTD. (exact ABN link, 0.98, to act_notifiable_invoices).

## Known limits
Only some entities in a new source get a register-confirmed profile: the trimmed register is the Business Names register only (the Companies register was cut). In the 121-row sample, 3 profiles resulted.

## Cleanup after a rehearsal
```bash
rm -rf configs/<id>.* outputs/observations/<id>.* outputs/rejects/<id>.jsonl logs/agent_runs/<id>
rm data/reference/demo_trimmed.csv data/reference/ATTRIBUTION.md   # the --out file and its attribution file (only if --out wrote them elsewhere than the tracked ones; check the path first)
unset BN_TRIMMED
git restore .   # last, so it also brings back the tracked ATTRIBUTION.md if it was removed above
python -m src.part3_resolve.run && python -m src.part3_resolve.graph && python -m src.part4_profiles.profiles   # six-source baseline
```
Note: `ATTRIBUTION.md` is written next to the `--out` file. If `--out` is in `data/reference/`, that is the tracked attribution file; the final `git restore .` brings it back.
