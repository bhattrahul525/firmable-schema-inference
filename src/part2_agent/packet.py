"""Step 7: the review packet a human reads before approving (configs/<source>.review.md).

Everything in it is computed from the run, not written by the model, except the model's own
reasons, which are labelled as such.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.engine.extract import run_rows
from src.part2_agent.profile import trim_row


def _t(f: dict) -> str:
    parts = [t["name"] + (f"({t['arg']})" if t["arg"] not in (None, "") else "") for t in f["transforms"]]
    return " → ".join(parts) or "none"


def _src(f: dict) -> str:
    return f["source"] if isinstance(f["source"], str) else " + ".join(f["source"])


def field_examples(cfg: dict, held: list[dict], metadata: dict, per_field: int = 3) -> dict[str, list]:
    obs, _, _ = run_rows(cfg, held[:300], metadata)
    out: dict[str, list] = defaultdict(list)
    for o in obs:
        if o["source_field"] is None:
            continue
        src = o["source_field"] if isinstance(o["source_field"], str) else " + ".join(o["source_field"])
        k = f"{o['field']}<-{src}"
        if len(out[k]) < per_field and (str(o["raw_value"])[:50], o["value"]) not in [(a, b) for a, b in out[k]]:
            out[k].append((str(o["raw_value"])[:50], o["value"]))
    return out


def write_packet(cfg: dict, metadata: dict, report: dict, held: list[dict], summary: dict, critique: dict) -> Path:
    sid = cfg["source_id"]
    ex = field_examples(cfg, held, metadata)
    L = []
    L.append(f"# Review packet: {sid} (config v{cfg['config_version']})\n")
    L.append(f"**Dataset:** {metadata['title']} — {metadata['organisation']}  \n**Page:** {metadata['dataset_page']}  ")
    flag = "  ⚠️ **LICENCE FLAGGED: check terms before use**" if metadata["licence_flag"] else ""
    L.append(f"**Licence:** {metadata['licence']}{flag}  \n**File:** `{metadata['file']}` (sha256 `{metadata['sha256'][:12]}…`)  ")
    L.append(f"**What the agent says it is:** {cfg['what_it_is']}  \n**One row is:** {cfg['one_row_is']}\n")
    L.append("## How this was produced\n")
    L.append(f"- Model `{summary['model']}`; {summary['llm_calls']} LLM calls; {summary['input_tokens']:,} input + {summary['output_tokens']:,} output tokens; "
             f"cost ${summary['cost_usd']:.4f} (computed from list prices); LLM time {summary['llm_seconds']}s.")
    L.append(f"- Revision rounds: {len(cfg['revision_history'])}. Tested on {report['n_rows']} held-out rows the model never saw.")
    L.append(f"- Reader: `{cfg['reader']}`. Record id: `{cfg['record_id']}` — {cfg.get('record_id_reason', '')}")
    L.append(f"- observed_at: `{cfg['observed_at']}`. valid_from: `{cfg.get('valid_from')}`. valid_to: `{cfg.get('valid_to')}`.")
    L.append(f"- source_reliability (the model's judgement, not measured): `{cfg['source_reliability']}` — {cfg.get('source_reliability_basis', '')}\n")

    L.append("## Mapped fields: mark any that are WRONG when you run `approve`\n")
    L.append("| # | Source column | → Canonical field | Transforms | Mapping conf. (model) | Parse rate (measured) | **Field conf.** | Proposals | Examples (raw → value) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, f in enumerate(cfg["fields"], 1):
        v = f["validation"]
        rate = "n/a" if v["parse_rate"] is None else f"{v['parse_rate']:.1%}"
        key = f"{f['canonical']}<-{_src(f)}"
        examples = "<br>".join(f"`{a}` → `{b}`" for a, b in ex.get(key, [])) or "—"
        L.append(f"| {i} | `{_src(f)}` | `{f['canonical']}` | {_t(f)} | {f['mapping_confidence']:.2f} | {rate} (ok {v['ok']}, rejected {v['rejected']}) "
                 f"| **{f['field_confidence']:.2f}** | {f['proposal_agreement']} | {examples} |")
    L.append("")
    L.append("Model's reasons per field (its words, not verified):\n")
    for i, f in enumerate(cfg["fields"], 1):
        L.append(f"{i}. `{f['canonical']}` ← `{_src(f)}`: {f.get('reason', '')}")
    L.append("")

    L.append("## Left unmapped (not guessed)\n")
    for u in cfg["unmapped"] or [{"source": "—", "reason": "none"}]:
        L.append(f"- `{u['source']}`: {u['reason']}")
    L.append("\n## Needs a transform the engine does not have\n")
    for u in cfg["needs_transform"] or [{"source": "—", "why": "none"}]:
        L.append(f"- `{u['source']}`: {u['why']}")

    L.append("\n## Checks\n")
    resp = {r["check_id"]: r for r in cfg.get("meaning_check_responses", [])}
    if report["warnings"]:
        for w in report["warnings"]:
            r = resp.get(w["id"])
            L.append(f"- ⚠️ **{w['id']}**: {w['text']}  \n  Agent's answer: " + (f"*{r['action']}*: {r['reason']}" if r else "**not answered**"))
    else:
        L.append("- No meaning warnings on held-out rows.")
    for i in report["infos"]:
        L.append(f"- ℹ️ {i['text']}")
    L.append(f"- Duplicate record ids in held-out rows: {report['duplicate_ids']}")
    L.append(f"- Proposal disagreements (two independent proposals): only-1 {len(cfg['validation_summary']['proposal_disagreements']['only_A'])}, "
             f"only-2 {len(cfg['validation_summary']['proposal_disagreements']['only_B'])}; those fields are capped at 0.70.")
    L.append(f"- Fields the agent abstained on after failing validation: {cfg['validation_summary']['abstained'] or 'none'}")
    L.append("\n## Critique step (reads raw rows next to output)\n")
    L.append(f"{critique['overall']}")
    for i in critique["issues"]:
        L.append(f"- `{i['field']}`: {i['problem']} (suggested: {i['suggested_fix']})")

    L.append("\n## What changed during revision\n")
    if not cfg["revision_history"]:
        L.append("- No revisions were needed.")
    for h in cfg["revision_history"]:
        L.append(f"**{h['round']}**")
        L += [f"- {c['what']} — {c['why']}" for c in h["changes"]]

    L.append("\n## Three sample rows, raw\n")
    for row in held[:3]:
        L.append(f"- `{trim_row(row)}`")
    L.append(f"\n---\nTo review: `python -m src.part2_agent.approve {sid}`\n")
    path = Path("configs") / f"{sid}.review.md"
    path.write_text("\n".join(L))
    return path
