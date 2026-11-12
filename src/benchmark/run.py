"""Run a benchmark draw: one agent run per item, then collect and report (ARCHITECTURE.md section e).

  python -m src.benchmark.run --draw outputs/benchmark/dev_seed1/draw.json --pass a --baseline 0.0 --session-limit 3.0

One SUBPROCESS per run (`python -m src.part2_agent.onboard --mode agent ...`): the per-tool SIGALRM timeout, the cost counter and a
crash stay isolated, and a few runs can go at once. The results are read from the traces afterwards, never from console output.
Before each launch the session's live spend (the round-2 total in logs/llm_calls.jsonl minus --baseline) is checked; no run starts
at or past --session-limit (it is recorded as `skipped: spend limit`). Each run has its own dollar limit (--per-run-dollars) and a
wall-clock kill (--timeout); a kill is recorded as `unfinished`.

Benchmark configs and packets go to outputs/benchmark/<draw>/pass_<x>/configs/, never to configs/. No approval file is ever made.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src import llm
from src.benchmark import injection, report

DEFAULT_MODEL = "claude-haiku-5-5"
DEV_MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5")    # the dev draw may run on either; the final draw is a separate decision


def session_spend(baseline: float, log_path: Path | None = None) -> float:
    path = log_path or llm.LOG_PATH
    total = llm.spend_summary(path, 2)["total"]["cost_usd"]
    return total - baseline


def source_id_for(draw_name: str, pass_label: str, index: int) -> str:
    return f"bench_{draw_name}{pass_label}_{index:02d}"


def command(reference: str, source_id: str, *, model: str, per_run_dollars: float, config_dir: Path) -> list[str]:
    return [sys.executable, "-m", "src.part2_agent.onboard", "--mode", "agent", reference, "--source-id", source_id,
            "--max-dollars", str(per_run_dollars), "--model", model, "--config-dir", str(config_dir)]


def subprocess_runner(cmd: list[str], timeout: float, log_path: Path) -> str:
    """Run one command, stdout and stderr to a log file. Returns "ok", "exit N" or "killed"."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as f:
        try:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "killed"
    return "ok" if r.returncode == 0 else f"exit {r.returncode}"


def run_items(jobs: list[dict], *, out_dir: Path, model: str, per_run_dollars: float, baseline: float, session_limit: float,
              parallel: int = 3, timeout: float = 900, runner=subprocess_runner, spend=session_spend) -> dict[str, str]:
    """jobs: [{"source_id", "reference"}]. Returns {source_id: status}. Spend is checked under a lock before every launch."""
    status: dict[str, str] = {}
    lock = threading.Lock()

    def one(job: dict) -> None:
        sid = job["source_id"]
        with lock:     # checked before every launch; runs already started may finish, so overshoot <= parallel x per-run limit
            if spend(baseline) >= session_limit:
                status[sid] = "skipped: spend limit"
                return
        cmd = command(job["reference"], sid, model=model, per_run_dollars=per_run_dollars, config_dir=out_dir / "configs")
        status[sid] = runner(cmd, timeout, out_dir / "logs" / f"{sid}.txt")

    with ThreadPoolExecutor(parallel) as ex:
        list(ex.map(one, jobs))
    return status


def load_causes(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def collect(draw: dict, pass_label: str, out_dir: Path, status: dict[str, str], *, draw_name: str = "dev1",
            runs_dir: Path = report.RUNS_DIR, raw_dir: Path = report.RAW_DIR) -> list[dict]:
    causes = load_causes(out_dir.parent / f"causes_{pass_label}.json")
    rows, review = [], []
    for i, item in enumerate(draw["items"], 1):
        sid = source_id_for(draw_name, pass_label, i)
        s = report.summarise(sid, runs_dir=runs_dir, raw_dir=raw_dir)
        if status.get(sid, "").startswith("skipped"):
            s["outcome"] = "skipped (spend limit)"
        rows.append(report.row_for(s, item, causes.get(sid)))
        review += report.review_rows(sid, s, item, runs_dir=runs_dir)
    report.write_review(review, Path("handcheck") / f"benchmark_review_{draw_name}{pass_label}.csv")
    return rows


def run_injection(draw: dict, pass_label: str, out_dir: Path, *, model: str, per_run_dollars: float, baseline: float,
                  session_limit: float, timeout: float = 900, runner=subprocess_runner, spend=session_spend,
                  runs_dir: Path = report.RUNS_DIR, raw_dir: Path = report.RAW_DIR) -> dict:
    inj = draw["injection"]
    ids = {"clean": f"bench_inj{pass_label}_clean", "injected": f"bench_inj{pass_label}_injected"}
    jobs = [{"source_id": ids["clean"], "reference": inj["clean"]}, {"source_id": ids["injected"], "reference": inj["injected"]}]
    run_items(jobs, out_dir=out_dir, model=model, per_run_dollars=per_run_dollars, baseline=baseline, session_limit=session_limit,
              parallel=2, timeout=timeout, runner=runner, spend=spend)
    summ = {k: report.summarise(v, runs_dir=runs_dir, raw_dir=raw_dir) for k, v in ids.items()}
    v = injection.verdict(summ["clean"], summ["injected"])     # canary checks decide; the comparison is information only
    v["run_ids"] = ids
    v["cost_usd"] = round(sum(s.get("cost_usd") or 0 for s in summ.values()), 6)
    (out_dir / "injection.json").write_text(json.dumps(v, indent=1, default=str))
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description="Run a benchmark draw (dev draw: seed 1, Haiku or Sonnet).")
    ap.add_argument("--draw", required=True)
    ap.add_argument("--pass", dest="pass_label", required=True, help="a, b ... (suffix of the source ids and the output folder)")
    ap.add_argument("--baseline", type=float, required=True, help="round-2 spend at the start of the session")
    ap.add_argument("--session-limit", type=float, default=3.0)
    ap.add_argument("--per-run-dollars", type=float, default=0.5)
    ap.add_argument("--model", default=DEFAULT_MODEL, help="claude-haiku-5-5 (default) or claude-sonnet-5-5")
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=900)
    a = ap.parse_args()
    if a.model not in DEV_MODELS:
        raise SystemExit(f"the dev draw runs on Haiku or Sonnet only ({DEV_MODELS})")
    draw_path = Path(a.draw)
    draw = json.loads(draw_path.read_text())
    if draw["seed"] != 1:
        raise SystemExit("only the dev draw (seed 1) may be run here")
    out_dir = draw_path.parent / f"pass_{a.pass_label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [{"source_id": source_id_for("dev1", a.pass_label, i), "reference": it["reference"]} for i, it in enumerate(draw["items"], 1)]
    kw = dict(out_dir=out_dir, model=a.model, per_run_dollars=a.per_run_dollars, baseline=a.baseline, session_limit=a.session_limit,
              timeout=a.timeout)
    status = run_items(jobs, parallel=a.parallel, **kw)
    inj = run_injection(draw, a.pass_label, **kw)
    rows = collect(draw, a.pass_label, out_dir, status)
    report.write_tables(rows, out_dir)
    (out_dir / "run_status.json").write_text(json.dumps(status, indent=1))
    print(json.dumps({"run_status": status, "injection": inj["verdict"], "session_spend": round(session_spend(a.baseline), 4)}, indent=1))


if __name__ == "__main__":
    main()
