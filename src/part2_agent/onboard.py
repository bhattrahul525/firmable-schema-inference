"""The Part 2 agent: onboard one source into a mapping config, end to end.

  python -m src.part2_agent.onboard <source_id>

Steps (each checkpointed in logs/agent_runs/<source_id>/, so a re-run resumes):
  1 inspect   LLM+code  what is this file, how to read it; proved by actually loading it
  2 profile   code      column stats; rows split into sample A, sample B, held-out
  3 propose   LLM x2    two independent proposals (A rows, B rows); code compares them
  4 validate  code      run the real engine on held-out rows: format + meaning checks
  5 revise    LLM       fix what validation found (max MAX_REVISIONS rounds), then back to 4
  6 critique  LLM       reads raw rows next to their observations; one more revise if it finds problems
  7 finalise  code      abstain on anything still failing; field_confidence; write config + review packet
  8 gate      human    `python -m src.part2_agent.approve <source_id>`; rejection comments come back
                        here on the next run of this command (a human-feedback revise round)

This is the round-1 PIPELINE (`--mode pipeline`, now an explicit option). The default `--mode agent` runs the round-2
tool-using agent (onboard_agent below; design in ARCHITECTURE.md). The pipeline code is unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src import llm
from src.engine.config import (approval_path, config_path, load_ontology, structural_errors, write_config)
from src.engine.extract import RAW_DIR, run_rows
from src.engine.readers import read_raw_lines, read_rows, sheet_names
from src.part2_agent import llm_steps as steps
from src.part2_agent.packet import write_packet
from src.part2_agent.profile import profile_columns, split_rows, trim_row
from src.part2_agent.state import Run
from src.part2_agent.validate import needs_revision, report_as_text, validate

MAX_REVISIONS = 2        # validation-driven revise rounds
INSPECT_ATTEMPTS = 3
CRITIQUE_ROWS = 10
DISPUTED_CAP = 0.7       # a field the two proposals disagreed on never exceeds this confidence
UNVERIFIED_CAP = 0.5     # a field with no judged values in held-out rows never exceeds this
AGENT_VERSION = "0.1.0"


# ---- step 1 ------------------------------------------------------------------------------------

def check_reader(reader: dict, path: Path) -> tuple[list[str], list[dict]]:
    """Try the reader settings on the real file; raise ValueError with a plain reason if implausible."""
    headers, rows = read_rows(reader, path)
    named = [h for h in headers if not h.startswith("_blank_")]
    if len(headers) < 2 or not rows:
        raise ValueError(f"read {len(headers)} columns and {len(rows)} rows; that is not a table")
    if len(named) < 0.5 * len(headers):
        raise ValueError(f"over half the column names are blank: {headers[:10]}. Wrong header_row?")
    numeric_like = sum(1 for h in named if h.replace(".", "").replace("-", "").isdigit())
    if numeric_like > 0.3 * len(named):
        raise ValueError(f"column names look like data values: {headers[:10]}. Wrong header_row?")
    return headers, rows


def do_inspect(source_id: str, metadata: dict, raw_path: Path) -> dict:
    fmt = metadata["resource_format"].lower()
    preview_fmt = fmt if fmt in ("csv", "tsv", "xlsx", "json") else "csv"
    preview = read_raw_lines(raw_path, preview_fmt, n=12)
    sheets = sheet_names(raw_path) if preview_fmt == "xlsx" else None
    error = None
    for attempt in range(1, INSPECT_ATTEMPTS + 1):
        result = steps.inspect_step(source_id, metadata, preview, sheets, previous_error=error)
        if not result["contains_business_entities"]:
            return {**result, "attempts": attempt, "reader_check": "skipped: no business entities"}
        try:
            headers, rows = check_reader(steps.reader_from_inspect(result), raw_path)
            return {**result, "attempts": attempt, "reader_check": f"ok: {len(headers)} columns, {len(rows)} rows"}
        except Exception as e:  # any reader failure goes back to the model as feedback
            error = f"{type(e).__name__}: {e}"
            print(f"  inspect attempt {attempt} failed: {error}")
    raise RuntimeError(f"{source_id}: could not find working reader settings after {INSPECT_ATTEMPTS} attempts ({error})")


# ---- helpers for steps 3-7 ---------------------------------------------------------------------

def pair_set(proposal: dict) -> dict[tuple, dict]:
    return {(tuple(f["source"]), f["canonical"]): f for f in proposal["fields"]}


def compare(pa: dict, pb: dict) -> dict:
    a, b = pair_set(pa), pair_set(pb)
    fmt = lambda f: {"source": f["source"], "canonical": f["canonical"],
                     "transforms": [t["name"] + (f"({t['arg']})" if t["arg"] else "") for t in f["transforms"]]}
    return {"agreed": sorted(f"{k[0]} -> {k[1]}" for k in a.keys() & b.keys()),
            "only_A": [fmt(a[k]) for k in a.keys() - b.keys()],
            "only_B": [fmt(b[k]) for k in b.keys() - a.keys()]}


def disputes_text(cmp: dict) -> str:
    if not cmp["only_A"] and not cmp["only_B"]:
        return ""
    lines = ["TWO INDEPENDENT PROPOSALS (made from different sample rows) DISAGREED. Decide each one on the evidence:"]
    lines += [f"- only proposal 1 mapped: {d}" for d in cmp["only_A"]]
    lines += [f"- only proposal 2 mapped: {d}" for d in cmp["only_B"]]
    return "\n".join(lines)


def key_of(f: dict) -> tuple:
    return (tuple(f["source"]) if isinstance(f["source"], list) else (f["source"],), f["canonical"])


def mark_agreement(cfg: dict, previous: dict[tuple, str], cmp: dict, first: bool) -> None:
    """Each field is 'agreed' (both proposals had it), 'resolved_by_revision' (they disagreed and a
    revision decided), or 'new_in_revision'."""
    disputed = {(tuple(d["source"]), d["canonical"]) for d in cmp["only_A"] + cmp["only_B"]}
    for f in cfg["fields"]:
        k = key_of(f)
        if first:
            f["proposal_agreement"] = "disputed" if k in disputed else "agreed"
        elif previous.get(k) in ("disputed", "resolved_by_revision") or k in disputed:
            f["proposal_agreement"] = "resolved_by_revision"
        else:
            f["proposal_agreement"] = previous.get(k, "new_in_revision")


def abstain(cfg: dict, report: dict, why_prefix: str) -> list[str]:
    """Anything still failing is removed from `fields` and listed under `unmapped` with the reason.
    Better a missing field than a wrong one."""
    removed = []
    failing = {f["key"]: f for f in report["field_failures"]}
    keep = []
    for f in cfg["fields"]:
        k = f"{f['canonical']}<-{f['source'] if isinstance(f['source'], str) else '+'.join(f['source'])}"
        if k in failing:
            cfg["unmapped"].append({"source": f["source"] if isinstance(f["source"], str) else "+".join(f["source"]),
                                    "reason": f"abstained ({f['canonical']}): {why_prefix}: {failing[k]['reason']}"})
            removed.append(k)
        else:
            keep.append(f)
    cfg["fields"] = keep
    for col in report["unaccounted_columns"]:
        cfg["unmapped"].append({"source": col, "reason": f"abstained: agent did not account for this column ({why_prefix})"})
        removed.append(f"column:{col}")
    return removed


def finalise_confidence(cfg: dict, report: dict) -> None:
    """field_confidence = the LOWER of (model's confidence the column means this field) and
    (measured parse rate on held-out rows). Disputed fields and unverifiable fields are capped.
    Never an average: a field is only as trustworthy as its weakest evidence."""
    for f in cfg["fields"]:
        k = f"{f['canonical']}<-{f['source'] if isinstance(f['source'], str) else '+'.join(f['source'])}"
        s = report["stats"].get(k, {})
        rate = s.get("parse_rate")
        conf = f["mapping_confidence"]
        conf = min(conf, rate) if rate is not None else min(conf, UNVERIFIED_CAP)
        if f.get("proposal_agreement") == "resolved_by_revision":
            conf = min(conf, DISPUTED_CAP)
        f["field_confidence"] = round(conf, 3)
        f["validation"] = {"held_out_rows": s.get("rows"), "blank": s.get("blank"), "ok": s.get("ok"),
                           "skipped_not_applicable": s.get("skip"), "rejected": s.get("reject"), "parse_rate": rate}


# ---- the run -----------------------------------------------------------------------------------

def onboard(source_id: str, *, quiet: bool = False) -> dict:
    t_start = time.monotonic()
    run = Run(source_id)
    src_dir = RAW_DIR / source_id
    metadata = json.loads((src_dir / "metadata.json").read_text())
    raw_path = src_dir / metadata["file"]
    ontology = load_ontology()
    print(f"onboarding {source_id} with model {llm.DEFAULT_MODEL}")

    # 1 inspect
    inspect = run.step("01_inspect", lambda: do_inspect(source_id, metadata, raw_path))
    if not inspect["contains_business_entities"]:
        print(f"  agent finds no business entities in this dataset ({inspect['what_it_is']}). Stopping; no config written.")
        return {"status": "no_business_entities", "inspect": inspect}
    reader = steps.reader_from_inspect(inspect)
    headers, rows = read_rows(reader, raw_path)

    # 2 profile + split
    def do_profile():
        # Profile ALL rows: a capped profile reported "20000 distinct of 206548 rows", which the agent
        # read as "not unique" and so wrongly gave up on real source keys (found on QBCC/ACT/VIC).
        cols = profile_columns(headers, rows)
        return {"n_rows": len(rows), "columns": cols, "split": split_rows(source_id, len(rows)),
                "empty_columns": [c["column"] for c in cols if c["fill_rate"] == 0]}
    prof = run.step("02_profile", do_profile)
    held = [rows[i] for i in prof["split"]["held_out"]]
    empty = set(prof["empty_columns"])
    sample = lambda label: [trim_row(rows[i]) for i in prof["split"][label]]

    # 3 propose twice, compare
    pa = run.step("03a_propose_A", lambda: steps.propose_step(source_id, "A", metadata, inspect, prof["columns"], sample("A"), len(rows)))
    pb = run.step("03b_propose_B", lambda: steps.propose_step(source_id, "B", metadata, inspect, prof["columns"], sample("B"), len(rows)))
    cmp = run.step("03c_compare", lambda: compare(pa, pb))

    version = 1
    cfg = steps.to_config(pa, inspect, source_id, version)
    cfg["meaning_check_responses"] = []
    cfg["revision_history"] = []
    agreement: dict[tuple, str] = {}
    mark_agreement(cfg, agreement, cmp, first=True)
    agreement = {key_of(f): f["proposal_agreement"] for f in cfg["fields"]}

    def revise(label: str, feedback: str) -> dict:
        nonlocal cfg, version, agreement
        ans = run.step(f"05_revise_{label}", lambda: steps.revise_step(source_id, label, cfg, feedback, prof["columns"], metadata))
        version += 1
        new = steps.to_config(ans, inspect, source_id, version)
        new["meaning_check_responses"] = cfg["meaning_check_responses"] + ans["warning_responses"]
        new["revision_history"] = cfg["revision_history"] + [{"round": label, "changes": ans["changes"]}]
        mark_agreement(new, agreement, cmp, first=False)
        agreement = {key_of(f): f["proposal_agreement"] for f in new["fields"]}
        cfg = new
        return ans

    def do_validate(name: str) -> dict:
        return run.step(name, lambda: validate(cfg, headers, held, metadata, empty))

    # 4-5 validate / revise loop
    disputes = disputes_text(cmp)
    for r in range(MAX_REVISIONS + 1):
        report = do_validate(f"04_validate_r{r}")
        pending_disputes = disputes if r == 0 else ""
        print(f"  validate r{r}: hard failures={report['hard_failure_count']}, warnings={len(report['warnings'])}")
        if not (needs_revision(report, cfg) or pending_disputes) or r == MAX_REVISIONS:
            break
        revise(f"r{r + 1}", "\n\n".join(x for x in (pending_disputes, report_as_text(report, cfg)) if x))

    # human feedback from a previous rejection, if any
    ap = approval_path(source_id)
    approval = json.loads(ap.read_text()) if ap.exists() else {"rounds": []}
    feedback = approval.get("feedback_pending")
    if feedback:
        lines = ["A HUMAN REVIEWER MARKED THESE MAPPINGS WRONG (their comments are authoritative):"]
        lines += [f"- {w['field']}: {w['comment'] or '(no comment)'}" for w in feedback["wrong"]]
        if feedback.get("general"):
            lines.append(f"General comment: {feedback['general']}")
        revise(f"human_{len(approval['rounds'])}", "\n".join(lines))
        report = do_validate(f"04_validate_human_{len(approval['rounds'])}")

    # 6 critique: meaning errors that code cannot see
    if not report["structural_errors"]:
        step_rows = [held[i * len(held) // CRITIQUE_ROWS] for i in range(min(CRITIQUE_ROWS, len(held)))]

        def do_critique():
            examples = []
            for row in step_rows:
                obs, _, _ = run_rows(cfg, [row], metadata)
                examples.append({"raw": trim_row(row),
                                 "observations": [{"field": o["field"], "value": o["value"]} for o in obs],
                                 # envelope values the critic must be able to see, or it reports them missing
                                 "envelope": {"observed_at": obs[0]["observed_at"] if obs else None,
                                              "valid_from": obs[0]["valid_from"] if obs else None,
                                              "valid_to": obs[0]["valid_to"] if obs else None}})
            return {"examples": examples, **steps.critique_step(source_id, cfg, examples)}
        critique = run.step("06_critique", do_critique)
        if critique["issues"] and not feedback:
            txt = "A REVIEWER READING RAW ROWS NEXT TO THEIR OUTPUT FOUND THESE MEANING PROBLEMS:\n" + "\n".join(
                f"- {i['field']}: {i['problem']} (suggested: {i['suggested_fix']})" for i in critique["issues"])
            revise("critique", txt)
            report = do_validate("04_validate_post_critique")
    else:
        critique = {"issues": [], "overall": "skipped: config structurally invalid"}

    # 7 finalise
    if report["structural_errors"]:
        raise RuntimeError(f"{source_id}: config still structurally invalid after revisions: {report['structural_errors']}")
    removed = []
    if report["hard_failure_count"]:
        removed = abstain(cfg, report, f"still failing after {len(cfg['revision_history'])} revision(s)")
        print(f"  abstained on: {removed}")
        report = run.step(f"04_validate_final_v{version}", lambda: validate(cfg, headers, held, metadata, empty))
    finalise_confidence(cfg, report)
    cfg["validation_summary"] = {
        "held_out_rows": report["n_rows"], "observations_in_held_out": report["observations"],
        "abstained": removed, "warnings": report["warnings"], "infos": report["infos"],
        "critique_issues": critique["issues"], "proposal_disagreements": {"only_A": cmp["only_A"], "only_B": cmp["only_B"]},
    }
    cfg["generated_by"] = {"agent_version": AGENT_VERSION, "model": llm.DEFAULT_MODEL,
                           "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    errs = structural_errors(cfg, ontology, headers, metadata)
    assert not errs, errs

    write_config(cfg, config_path(source_id))
    # a changed config is never approved: reset the lock but keep the review history
    approval["status"] = "pending_review"
    approval["config_sha256"] = None
    approval.pop("feedback_pending", None)
    ap.write_text(json.dumps(approval, indent=2))

    summary = run_summary(source_id, run.state["started_at"])
    summary["wall_clock_this_invocation_s"] = round(time.monotonic() - t_start, 1)
    summary["step_timings_s"] = run.state["timings"]
    run.save("run_summary", summary)
    write_packet(cfg, metadata, report, held, summary, critique)
    print(f"  config -> {config_path(source_id)} (v{version}); packet -> configs/{source_id}.review.md")
    print(f"  LLM calls={summary['llm_calls']} cost=${summary['cost_usd']:.4f} tokens={summary['input_tokens']}+{summary['output_tokens']}")
    return {"status": "pending_review", "summary": summary}


def run_summary(source_id: str, started_at: str) -> dict:
    """Cost and time for this onboarding, summed from the LLM log (calls tagged with this source
    since the run started)."""
    calls, cost, tin, tout, secs = 0, 0.0, 0, 0, 0.0
    by_step: dict[str, float] = {}
    if llm.LOG_PATH.exists():
        for line in llm.LOG_PATH.read_text().splitlines():
            e = json.loads(line)
            if e.get("source_id") == source_id and e["ts"] >= started_at and e.get("ok"):
                calls += 1
                cost += e["cost_usd"]
                tin += e["input_tokens"] + e.get("cache_read_tokens", 0) + e.get("cache_write_tokens", 0)
                tout += e["output_tokens"]
                secs += e["seconds"]
                by_step[e["step"]] = round(by_step.get(e["step"], 0) + e["cost_usd"], 6)
    return {"source_id": source_id, "model": llm.DEFAULT_MODEL, "llm_calls": calls, "cost_usd": round(cost, 6),
            "input_tokens": tin, "output_tokens": tout, "llm_seconds": round(secs, 1), "cost_by_step": by_step}


def trace_summary(trace_path: Path) -> list[str]:
    """The tool sequence of a run, one entry per executed tool call (refused calls are marked)."""
    if not trace_path.exists():
        return []
    out = []
    for line in trace_path.read_text().splitlines():
        ev = json.loads(line)
        if ev["type"] == "tool_call":
            out.append(ev["name"] + (" (refused)" if ev.get("refused") else " (error)" if ev.get("is_error") else ""))
    return out


def default_source_id(reference: str) -> str:
    from src.part2_agent.fetch import slug
    if re.fullmatch(r"[a-z]+:[A-Za-z0-9_\-]+", reference):
        return slug(reference.split(":", 1)[1])
    leaf = re.split(r"[/\\]", reference.split("?")[0].rstrip("/\\"))[-1]
    return slug(Path(leaf).stem or leaf) or "source"


def onboard_agent(reference: str, *, source_id: str | None = None, model: str | None = None, limits=None,
                  overwrite: bool = False, say=print, config_dir: str | None = None,
                  resource_index: int | None = None) -> dict:
    """ARCHITECTURE.md round 2: the tool-using agent. Returns {"result": RunResult, "tools": [...]}."""
    from src.engine import extract as _extract, readers as _readers, config as _config, transforms as _transforms
    from src.part2_agent import agent_hooks, agent_prompt, agent_table, agent_tools, guard, loop, tools as _tools
    sid = source_id or default_source_id(reference)
    ap = (Path(config_dir) / f"{sid}.approval.json") if config_dir else _config.approval_path(sid)
    if ap.exists() and json.loads(ap.read_text()).get("status") == "approved" and not overwrite:
        sys.exit(f"{sid} already has an APPROVED config. Pick another --source-id, or pass --overwrite to replace it "
                 f"(its approval is reset).")
    files = [m.__file__ for m in (agent_hooks, agent_prompt, agent_table, agent_tools, _extract, _readers, _config, _transforms)]
    version = loop.code_version(files)
    work_dir = loop.RUNS_DIR / sid
    kit = agent_tools.AgentKit(sid, work_dir, model=model, code_version=version, allow_overwrite=overwrite,
                              config_dir=Path(config_dir) if config_dir else None)
    run = loop.AgentRun(source_id=sid, reference=reference, task=agent_prompt.make_task(reference, sid, resource_index),
                        tools=kit.tools, hooks=kit.hooks, system=agent_prompt.SYSTEM_TASK, model=model,
                        limits=limits or guard.Limits(), code_version=version, say=say,
                        fetcher=guard.FetchGuard(reference, pinned_index=resource_index))
    say(f"onboarding {sid} (round-2 agent, model {model or llm.DEFAULT_MODEL})")
    t0 = time.monotonic()
    result = run.run()
    seq = trace_summary(work_dir / "trace.jsonl")
    say(f"outcome: {result.outcome}" + (f" (ended by the harness: {result.forced_by})" if result.forced_by else ""))
    say(f"turns={result.turns} tool_calls={result.tool_calls} cost=${result.cost_usd:.4f} "
        f"agent_seconds={result.elapsed_seconds} wall_clock_seconds={time.monotonic() - t0:.1f}")
    say("tool sequence: " + " -> ".join(seq))
    if result.packet_path:
        say(f"packet: {result.packet_path}")
    return {"result": result, "tools": seq}


def main() -> None:
    ap = argparse.ArgumentParser(description="Onboard one source with the Part 2 agent.")
    ap.add_argument("source", nargs="?", help="pipeline: a downloaded source_id or <portal>:<ckan dataset>; agent: a "
                    "<portal>:<ckan dataset>, an http(s) URL or a file path")
    ap.add_argument("--mode", choices=("pipeline", "agent"), default="agent",
                    help="agent = the round-2 tool-using agent (default); pipeline = the round-1 fixed pipeline")
    ap.add_argument("--file", help="onboard a local file instead (pipeline: csv/tsv/xlsx/json copied in; agent: any path)")
    ap.add_argument("--licence", default="unknown", help="pipeline: licence of a local file (default: unknown, flagged)")
    ap.add_argument("--resource-contains", help="pipeline, CKAN: only consider resources whose name contains this")
    ap.add_argument("--source-id", help="agent: name for the source (default: from the dataset name or file name)")
    ap.add_argument("--model", help="agent: model id (default: the setting in src/llm.py)")
    ap.add_argument("--max-dollars", type=float, help="agent: dollar budget for the run (default 1.00)")
    ap.add_argument("--max-turns", type=int, help="agent: model-turn budget (default 40)")
    ap.add_argument("--overwrite", action="store_true", help="agent: replace an approved config of the same source id")
    ap.add_argument("--resource-index", type=int, help="agent: pin the resource (its index in the dataset's resource list); "
                    "the agent can then fetch only that one")
    ap.add_argument("--config-dir", help="agent: write the config and review packet here instead of configs/ (benchmark runs)")
    a = ap.parse_args()
    if a.mode == "agent":
        from src.part2_agent.guard import Limits
        ref = a.file or a.source
        if not ref:
            sys.exit("agent mode needs a reference: <portal>:<dataset>, a URL, or a file path")
        kw = {k: v for k, v in (("max_dollars", a.max_dollars), ("max_calls", a.max_turns)) if v is not None}
        onboard_agent(ref, source_id=a.source_id, model=a.model, limits=Limits(**kw), overwrite=a.overwrite,
                      config_dir=a.config_dir, resource_index=a.resource_index)
        return
    if a.file:
        from src.part2_agent.fetch import fetch_file
        source_id = fetch_file(a.file, a.licence)
    elif a.source and ":" in a.source:
        from src.part2_agent.fetch import fetch_ckan
        source_id = fetch_ckan(a.source, a.resource_contains)
    elif a.source:
        source_id = a.source
    else:
        sys.exit("give a source_id, a <portal>:<dataset> reference, or --file")
    if not (RAW_DIR / source_id / "metadata.json").exists():
        sys.exit(f"no downloaded source {source_id!r}. Run: python -m src.part1_triage.download")
    onboard(source_id)


if __name__ == "__main__":
    main()
