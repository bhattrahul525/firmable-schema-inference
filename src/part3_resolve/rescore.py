"""Re-score existing links with a newer matcher, WITHOUT re-reading any source.

  python -m src.part3_resolve.rescore --to m1.1

This is the answer to "six months from now you improve the matching model; there are millions of old links".
It works only because every link already stores what the matcher saw (the raw `evidence` features, the
`matcher_version`, the thresholds). Re-scoring is then a pure function over stored rows: no source files, no
extractor, no model calls. It writes a NEW file (the old links are never overwritten) in which each link keeps
`previous` = {matcher_version, link_confidence, band}, so the history of every decision survives.

It also reports what the change would have done to the links a human already labelled, so the improvement is
measured, not assumed.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from src.part3_resolve.labels import load_allowlist, load_labels, pair_id
from src.part3_resolve.keys import rekey_conflicting_name_links
from src.part3_resolve.score import ACCEPT, KEY_RULE_VERSIONS, LOOSE, SCORERS, band

OUT = Path("outputs/part3")


def gate(changed: list[dict], labels: dict, allowed: dict) -> tuple[Counter, list, list]:
    """THE GATE. A rescore may not demote a pair a human labelled Y or promote one labelled N, unless the pair is in
    handcheck/accepted_conflicts.csv (hand-written; reported, not blocking). Returns (effect, blocking, accepted).
    Pure function; labels are never edited."""
    rank = {"refused": 0, "loose": 1, "accepted": 2}
    effect: Counter = Counter()
    blocking, accepted_conflicts = [], []
    for c in changed:
        pid = pair_id(c["a"], c["b"])
        if pid not in labels:
            continue
        effect[f"{c['from'][2]}->{c['to'][2]} hand label {labels[pid]}"] += 1
        delta = rank[c["to"][2]] - rank[c["from"][2]]
        kind = "Y_demoted" if labels[pid] == "Y" and delta < 0 else "N_promoted" if labels[pid] == "N" and delta > 0 else None
        if kind:
            (accepted_conflicts if pid in allowed else blocking).append(
                {"pair_id": pid, "problem": kind, "from": c["from"], "to": c["to"],
                 **({"reason": allowed[pid]["reason"]} if pid in allowed else {})})
    return effect, blocking, accepted_conflicts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, choices=sorted(SCORERS))
    new_v = ap.parse_args().to
    scorer = SCORERS[new_v]

    links = [json.loads(l) for l in (OUT / "links.jsonl").open()]
    refused = [json.loads(l) for l in (OUT / "unlinked_queue.jsonl").open()]
    refused = [q for q in refused if q.get("kind") == "pair"]  # refused pairs also carry their features

    moves: Counter = Counter()
    rescored, changed, not_rescoreable = [], [], 0
    for l in links + refused:
        old_conf, old_v = l["link_confidence"], l["matcher_version"]
        old_band = band(old_conf)
        try:
            conf, tier, why = scorer(l["evidence"])
        except KeyError:  # an old link that lacks the features this matcher needs: report it, do not guess
            not_rescoreable += 1
            continue
        new_band = band(conf)
        moves[f"{old_band} -> {new_band}"] += 1
        row = {**l, "link_confidence": conf, "tier": tier, "matcher_version": new_v,
               "previous": {"matcher_version": old_v, "link_confidence": old_conf, "band": old_band}}
        if new_band == "refused":
            row["refusal_reason"] = why
        else:
            row["band"] = new_band
        if old_band != new_band:
            changed.append({"link_id": l.get("link_id"), "a": l["source_a_record"], "b": l["source_b_record"],
                            "names": [l["evidence"]["name_a"], l["evidence"]["name_b"]],
                            "from": [old_v, old_conf, old_band], "to": [new_v, conf, new_band], "why": why})
        if new_band != "refused":
            rescored.append(row)

    # canonical-key rule (m1.2+): also a pure function of the stored evidence
    key_changes = rekey_conflicting_name_links(rescored) if new_v in KEY_RULE_VERSIONS else []

    effect, blocking, accepted_conflicts = gate(changed, load_labels(), load_allowlist())
    report = {"from_versions": sorted({l["matcher_version"] for l in links}), "to_version": new_v,
              "thresholds": {"accept": ACCEPT, "loose": LOOSE}, "links_considered": len(links) + len(refused),
              "band_moves": dict(moves), "links_changed": len(changed), "not_rescoreable": not_rescoreable,
              "gate_blocking": blocking, "gate_accepted_conflicts": accepted_conflicts, "written": not blocking,
              "effect_on_hand_labelled_links": dict(effect),
              "labelled_yes_links_demoted_or_refused": sum(v for k, v in effect.items() if k.endswith("hand label Y") and k.split("->")[1].startswith("refused")),
              "canonical_keys_rekeyed": key_changes, "changed_links": changed[:40]}
    (OUT / f"rescore_to_{new_v}.json").write_text(json.dumps(report, indent=2))
    if blocking:
        raise SystemExit(f"REFUSED to write rescored links: {len(blocking)} human label(s) contradicted: {blocking}")
    with (OUT / f"links_rescored_{new_v}.jsonl").open("w") as f:
        for r in rescored:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("changed_links", "canonical_keys_rekeyed")}, indent=2))
    print("canonical keys re-keyed:", [(k["names"][0], k["from"], "->", k["to"]) for k in key_changes])
    for c in changed[:8]:
        print(f"  {c['names'][0]!r} == {c['names'][1]!r}: {c['from'][1:]} -> {c['to'][1:]} ({c['why']})")


if __name__ == "__main__":
    main()
