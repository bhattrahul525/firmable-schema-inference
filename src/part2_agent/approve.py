"""Step 8: the human approval gate.

  python -m src.part2_agent.approve <source_id>

Shows the mapped fields and asks ONE question: which are wrong? (numbers, or blank if none).
  * none wrong  -> approved. We store the SHA-256 of the config file; the engine will only run a
                   config whose hash matches (see src/engine/config.load_approved_config).
  * some wrong  -> rejected, with your comment per field. Run onboard again: the agent revises using
                   your comments, re-validates, and writes a new packet.
Every review round is kept in configs/<source>.approval.json, so the share of fields wrong at
first review (a measured accuracy of the agent) can be reported later.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from src.engine.config import approval_path, config_path, load_config_file, sha256_of
from src.part2_agent.packet import _src, _t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_id")
    ap.add_argument("--reviewer", default="rahul")
    a = ap.parse_args()
    sid = a.source_id
    cp = config_path(sid)
    if not cp.exists():
        raise SystemExit(f"no config for {sid}; run onboard first")
    cfg = load_config_file(cp)
    apath = approval_path(sid)
    approval = json.loads(apath.read_text()) if apath.exists() else {"rounds": []}

    print(f"\n{sid}  (config v{cfg['config_version']}). Full detail: configs/{sid}.review.md\n")
    for i, f in enumerate(cfg["fields"], 1):
        print(f"{i:>2}. {_src(f)[:34]:34s} → {f['canonical']:22s} [{_t(f)[:40]}]  field_conf {f['field_confidence']:.2f}  ({f['proposal_agreement']})")
    print(f"\n    record id : {cfg['record_id']}\n    observed_at: {cfg['observed_at']}")
    for k in ("valid_from", "valid_to"):
        if cfg.get(k):
            print(f"    {k:10s}: {cfg[k]['source']} [{', '.join(t['name'] for t in cfg[k]['transforms'])}]")
    print("\nUnmapped:", "; ".join(f"{u['source']}" for u in cfg["unmapped"]) or "none")
    raw = input("\nWhich numbers are WRONG? (e.g. 3,5 — or press Enter if all are right): ").strip()
    wrong_idx = sorted({int(x) for x in raw.replace(" ", "").split(",") if x}) if raw else []
    if any(i < 1 or i > len(cfg["fields"]) for i in wrong_idx):
        raise SystemExit("number out of range")

    wrong = []
    for i in wrong_idx:
        f = cfg["fields"][i - 1]
        c = input(f"  What is wrong with #{i} ({_src(f)} → {f['canonical']})? ").strip()
        wrong.append({"index": i, "field": f"{f['canonical']} <- {_src(f)}", "comment": c})
    general = input("Any general comment (Enter to skip): ").strip() if wrong else ""

    sha = sha256_of(cp)
    approval["rounds"].append({
        "round": len(approval["rounds"]) + 1, "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewer": a.reviewer, "config_version": cfg["config_version"], "config_sha256": sha,
        "n_fields": len(cfg["fields"]), "wrong": wrong, "general_comment": general,
    })
    if wrong:
        approval.update(status="rejected", config_sha256=None, feedback_pending={"wrong": wrong, "general": general})
        print(f"\nRejected {len(wrong)} field(s). Now run: python -m src.part2_agent.onboard {sid}")
    else:
        approval.update(status="approved", config_sha256=sha)
        approval.pop("feedback_pending", None)
        print(f"\nApproved. Locked to sha256 {sha[:12]}…  Extract with: python -m src.engine.extract {sid}")
    apath.write_text(json.dumps(approval, indent=2))


if __name__ == "__main__":
    main()
