"""Turn the traces of benchmark runs into a results table (ARCHITECTURE.md section e, "Per run").

Everything comes from files the run itself wrote (the trace, metadata.json, the config in the run_end event), never from console
output. A run with no trace is `no_trace`; a trace with no run_end is `unfinished` (killed or crashed).

Columns left blank on purpose are for the human: outcome_correct, key_field_missed, reviewer_notes. `cause` and `fix` are filled
by whoever reads the failing traces (causes.json), not guessed by code.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

RUNS_DIR = Path("logs/agent_runs")
RAW_DIR = Path("data/raw/sources")
HUMAN_COLUMNS = ("outcome_correct", "key_field_missed", "reviewer_notes")
COLUMNS = ["source_id", "slot", "stratum", "dataset_id", "title", "format_class", "outcome", "forced_by", "turns", "tool_calls",
           "cost_usd", "agent_seconds", "download_seconds", "download_bytes", "file_format", "reader", "levels_W_P_G",
           "mapped_count", "mapped_fields", "abstained_count", "abstained_fields", "unresolved_blocking", "unmapped_columns",
           "critique_blocking", "critique_advisory", "open_advisory", "resource_switches", "refusals", "licence", "licence_flag", "model", "tool_sequence", "cause", "fix", *HUMAN_COLUMNS]


def read_events(source_id: str, runs_dir: Path = RUNS_DIR) -> list[dict] | None:
    p = runs_dir / source_id / "trace.jsonl"
    if not p.exists():
        return None
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def summarise(source_id: str, *, runs_dir: Path = RUNS_DIR, raw_dir: Path = RAW_DIR) -> dict:
    ev = read_events(source_id, runs_dir)
    if ev is None:
        return {"source_id": source_id, "outcome": "no_trace"}
    header = ev[0] if ev and ev[0]["type"] == "trace_header" else {}
    calls = [e for e in ev if e["type"] == "tool_call"]
    end = next((e for e in ev if e["type"] == "run_end"), None)
    result = end["result"] if end else {}
    cfg = result.get("config") or {}
    meta_path = raw_dir / source_id / "metadata.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    fields = cfg.get("fields") or []
    levels = Counter(f.get("transform_level", "W") for f in fields)
    crit = [c for c in calls if c["name"] == "critique" and not c.get("refused") and not c["is_error"]]
    last_issues = crit[-1]["status"].get("issues", []) if crit else []
    fin = next((c for c in calls if c["name"] == "finish" and not c["is_error"]), None)
    refusals = [{"tool": c["name"], "text": (c.get("refused") or c["rendered"])[:160]}
                for c in calls if c.get("refused") or (c["name"] == "finish" and c["is_error"])]
    seq = [c["name"] + (" (refused)" if c.get("refused") else " (error)" if c["is_error"] else "") for c in calls]
    return {
        "source_id": source_id, "outcome": result.get("outcome", "unfinished"), "forced_by": result.get("forced_by"),
        "reason": result.get("reason"), "evidence": result.get("evidence"),
        "turns": result.get("turns", sum(1 for e in ev if e["type"] == "model_turn")), "tool_calls": len(calls),
        "cost_usd": result.get("cost_usd", round(sum(e.get("cost_usd", 0) for e in ev if e["type"] in ("model_turn", "tool_call")), 6)),
        "agent_seconds": result.get("elapsed_seconds"),
        "download_seconds": round(sum(c.get("download_seconds", 0) for c in calls if c["name"] == "fetch"), 2),
        "download_bytes": meta.get("bytes"), "file_format": meta.get("resource_format"), "reader": cfg.get("reader"),
        "levels_W_P_G": f"{levels.get('W', 0)}/{levels.get('P', 0)}/{levels.get('G', 0)}",
        "mapped_fields": [{"canonical": f["canonical"], "source": f["source"], "level": f.get("transform_level", "W"),
                           "field_confidence": f.get("field_confidence")} for f in fields],
        "abstained_fields": [a.get("field") for a in result.get("abstentions") or []],
        "unmapped_columns": len(cfg.get("unmapped") or []),
        # coverage, separate from the outcome (who ended the run): a thin validated config shows up here
        "mapped_count": len(fields), "abstained_count": len(result.get("abstentions") or []),
        "unresolved_blocking": sum(1 for a in result.get("abstentions") or []
                                   if str(a.get("reason", "")).startswith("blocking critique issue unanswered")),
        "resource_switches": sum(1 for e in ev if e["type"] == "input_switched"),
        "critique_blocking": sum(1 for i in last_issues if i.get("severity", "blocking") == "blocking"),
        "critique_advisory": sum(1 for i in last_issues if i.get("severity") == "advisory"),
        "open_advisory": len(fin["status"].get("open_advisory", [])) if fin else 0,
        "refusals": refusals, "licence": meta.get("licence"), "licence_flag": meta.get("licence_flag"),
        "model": header.get("model"), "tool_sequence": seq,
        "download_failed": any(c["name"] == "fetch" and c["status"].get("download_failed") for c in calls),
        "tool_args": [c["args"] for c in calls], "config": cfg, "packet_path": result.get("packet_path"),
    }


def row_for(summary: dict, item: dict | None = None, cause: dict | None = None) -> dict:
    item = item or {}
    cause = cause or {}
    flat = {**summary}
    flat["mapped_fields"] = "; ".join(f"{m['canonical']}<-{m['source'] if isinstance(m['source'], str) else '+'.join(m['source'])}"
                                      for m in summary.get("mapped_fields", []))
    flat["abstained_fields"] = "; ".join(map(str, summary.get("abstained_fields", [])))
    flat["refusals"] = " | ".join(f"{r['tool']}: {r['text'][:90]}" for r in summary.get("refusals", []))
    flat["tool_sequence"] = " > ".join(summary.get("tool_sequence", []))
    flat["reader"] = json.dumps(summary.get("reader")) if summary.get("reader") else ""
    for k in ("slot", "stratum", "dataset_id", "title", "format_class"):
        flat[k] = item.get(k, "")
    flat["cause"], flat["fix"] = cause.get("cause", ""), cause.get("fix", "")
    flat["mapped_count"] = summary.get("mapped_count", "")
    for k in HUMAN_COLUMNS:
        flat[k] = ""
    return {k: flat.get(k, "") for k in COLUMNS}


def write_tables(rows: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "results.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    (out_dir / "results.jsonl").write_text("\n".join(json.dumps(r, default=str) for r in rows) + "\n")
    show = ["source_id", "dataset_id", "format_class", "outcome", "turns", "cost_usd", "agent_seconds", "mapped_fields", "refusals", "cause"]
    md = ["| " + " | ".join(show) + " |", "|" + "---|" * len(show)]
    for r in rows:
        md.append("| " + " | ".join(str(r.get(k, "")).replace("|", "/")[:70] for k in show) + " |")
    (out_dir / "results.md").write_text("\n".join(md) + "\n")


def review_rows(source_id: str, summary: dict, item: dict | None, *, runs_dir: Path = RUNS_DIR) -> list[dict]:
    """One row per mapped field with three raw-to-value examples from the HELD-OUT rows: the human sheet. Best effort: if the
    table cannot be rebuilt the examples are blank and the row is still written."""
    cfg = summary.get("config") or {}
    out, examples = [], {}
    try:
        from src.engine.extract import run_rows
        from src.part2_agent.agent_table import get_table, load_metadata
        table = get_table(source_id, runs_dir / source_id)
        obs, _, _ = run_rows(cfg, table.held_rows[:300], load_metadata(source_id))
        for o in obs:
            if o["source_field"] is None:
                continue
            src = o["source_field"] if isinstance(o["source_field"], str) else "+".join(o["source_field"])
            ex = examples.setdefault(f"{o['field']}<-{src}", [])
            pair = f"{str(o['raw_value'])[:50]} -> {str(o['value'])[:60]}"
            if len(ex) < 3 and pair not in ex:
                ex.append(pair)
    except Exception:
        pass
    for f in cfg.get("fields") or []:
        src = f["source"] if isinstance(f["source"], str) else "+".join(f["source"])
        ex = examples.get(f"{f['canonical']}<-{src}", [])
        out.append({"source_id": source_id, "dataset_id": (item or {}).get("dataset_id", ""), "field": f["canonical"], "source_column": src,
                    "level": f.get("transform_level", "W"), "field_confidence": f.get("field_confidence"),
                    "example_1": ex[0] if len(ex) > 0 else "", "example_2": ex[1] if len(ex) > 1 else "",
                    "example_3": ex[2] if len(ex) > 2 else "", "wrong": ""})
    return out


def write_review(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["source_id", "dataset_id", "field", "source_column", "level", "field_confidence", "example_1", "example_2", "example_3", "wrong"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


# ---- comparison across passes ---------------------------------------------------------------------------------------

def _read_pass(path: Path) -> list[dict]:
    with (path / "results.csv").open() as f:
        return list(csv.DictReader(f))


def compare(pass_dirs: dict[str, Path]) -> dict:
    """Side by side: each dataset's outcome in every pass, plus per pass and per model totals (runs, outcomes, cost, time).
    Rows are matched by dataset_id; a pass that lacks a dataset shows `-`."""
    passes = {label: _read_pass(d) for label, d in pass_dirs.items()}
    order, titles = [], {}
    for rows in passes.values():
        for r in rows:
            if r["dataset_id"] not in titles:
                order.append(r["dataset_id"])
                titles[r["dataset_id"]] = (r["title"], r["format_class"])
    datasets = []
    for did in order:
        outcomes, mapped = {}, {}
        for label, rows in passes.items():
            hit = next((r for r in rows if r["dataset_id"] == did), None)
            outcomes[label] = hit["outcome"] if hit else "-"
            mapped[label] = (hit.get("mapped_count") or "n/a") if hit else "-"
        datasets.append({"dataset_id": did, "title": titles[did][0], "format_class": titles[did][1], "outcomes": outcomes, "mapped": mapped})
    totals = {}
    for label, rows in passes.items():
        costs = [float(r["cost_usd"] or 0) for r in rows]
        secs = [float(r["agent_seconds"] or 0) for r in rows if r["agent_seconds"] not in ("", None)]
        turns = [int(float(r["turns"])) for r in rows if r["turns"] not in ("", None)]
        totals[label] = {"model": next((r["model"] for r in rows if r["model"]), ""), "runs": len(rows),
                         "outcomes": dict(Counter(r["outcome"] for r in rows)), "cost_usd": round(sum(costs), 4),
                         "mean_cost_usd": round(sum(costs) / len(costs), 4) if costs else 0,
                         "mean_agent_seconds": round(sum(secs) / len(secs), 1) if secs else 0,
                         "mean_turns": round(sum(turns) / len(turns), 1) if turns else 0}
    by_model: dict[str, dict] = {}
    for label, t in totals.items():
        m = by_model.setdefault(t["model"] or "?", {"passes": [], "runs": 0, "cost_usd": 0.0, "seconds": 0.0, "turns": 0})
        rows = passes[label]
        m["passes"].append(label)
        m["runs"] += t["runs"]
        m["cost_usd"] = round(m["cost_usd"] + t["cost_usd"], 4)
        m["seconds"] += sum(float(r["agent_seconds"] or 0) for r in rows if r["agent_seconds"] not in ("", None))
        m["turns"] += sum(int(float(r["turns"])) for r in rows if r["turns"] not in ("", None))
    for m in by_model.values():
        m["mean_cost_usd"] = round(m["cost_usd"] / m["runs"], 4) if m["runs"] else 0
        m["mean_agent_seconds"] = round(m["seconds"] / m["runs"], 1) if m["runs"] else 0
        m["mean_turns"] = round(m["turns"] / m["runs"], 1) if m["runs"] else 0
        del m["seconds"], m["turns"]
    return {"datasets": datasets, "totals": totals, "by_model": by_model, "passes": list(pass_dirs)}


def write_compare(cmp: dict, out_dir: Path, notes: str = "") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    labels = cmp["passes"]
    md = [notes, "", "## Outcome per dataset (and mapped-field count) across passes", "",
          "| dataset | fmt | " + " | ".join(labels) + " |", "|---|---|" + "---|" * len(labels)]
    for d in cmp["datasets"]:
        md.append(f"| {d['dataset_id'][:60]} | {d['format_class']} | " + " | ".join(
            f"{d['outcomes'][l]} ({d['mapped'][l]})" for l in labels) + " |")
    md += ["", "## Per pass", "", "| pass | model | runs | outcomes | cost | mean cost | mean agent s | mean turns |", "|---|---|---|---|---|---|---|---|"]
    for l, t in cmp["totals"].items():
        md.append(f"| {l} | {t['model']} | {t['runs']} | {t['outcomes']} | ${t['cost_usd']} | ${t['mean_cost_usd']} | {t['mean_agent_seconds']} | {t['mean_turns']} |")
    md += ["", "## Per model", "", "| model | passes | runs | cost | mean cost per run | mean agent s | mean turns |", "|---|---|---|---|---|---|---|"]
    for name, m in cmp["by_model"].items():
        md.append(f"| {name} | {','.join(m['passes'])} | {m['runs']} | ${m['cost_usd']} | ${m['mean_cost_usd']} | {m['mean_agent_seconds']} | {m['mean_turns']} |")
    (out_dir / "compare.md").write_text("\n".join(md) + "\n")
    with (out_dir / "compare.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dataset_id", "title", "format_class", *[f"outcome_{l}" for l in labels], *[f"mapped_{l}" for l in labels]])
        for d in cmp["datasets"]:
            w.writerow([d["dataset_id"], d["title"], d["format_class"], *[d["outcomes"][l] for l in labels], *[d["mapped"][l] for l in labels]])
    (out_dir / "compare.json").write_text(json.dumps(cmp, indent=1))


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Compare benchmark passes side by side.")
    ap.add_argument("--dir", required=True, help="e.g. outputs/benchmark/dev_seed1")
    ap.add_argument("--passes", nargs="+", required=True, help="pass labels, e.g. a b c s")
    ap.add_argument("--notes", default="")
    a = ap.parse_args()
    base = Path(a.dir)
    cmp = compare({l: base / f"pass_{l}" for l in a.passes})
    write_compare(cmp, base, a.notes)
    print((base / "compare.md").read_text())


if __name__ == "__main__":
    main()
