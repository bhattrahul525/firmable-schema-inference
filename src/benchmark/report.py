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
           "mapped_fields", "abstained_fields", "unmapped_columns", "critique_blocking", "critique_advisory", "open_advisory",
           "refusals", "licence", "licence_flag", "model", "tool_sequence", "cause", "fix", *HUMAN_COLUMNS]


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
