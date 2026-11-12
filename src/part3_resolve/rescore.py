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
import csv
import json
from collections import Counter
from pathlib import Path

from src.part3_resolve.score import ACCEPT, LOOSE, SCORERS, band

OUT = Path("outputs/part3")
HANDCHECK = Path("handcheck/part3_link_check.csv")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, choices=sorted(SCORERS))
    new_v = ap.parse_args().to
    scorer = SCORERS[new_v]

    links = [json.loads(l) for l in (OUT / "links.jsonl").open()]
    refused = [json.loads(l) for l in (OUT / "unlinked_queue.jsonl").open()]
    refused = [q for q in refused if q.get("kind") == "pair"]  # refused pairs also carry their features

    moves: Counter = Counter()
    rescored, changed = [], []
    for l in links + refused:
        old_conf, old_v = l["link_confidence"], l["matcher_version"]
        old_band = band(old_conf)
        conf, tier, why = scorer(l["evidence"])
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

    # what would this change have done to the 50 links a human labelled?
    labels = {((r["a_source"], r["a_record_id"]), (r["b_source"], r["b_record_id"])): r["label"].strip().upper()[:1]
              for r in csv.DictReader(HANDCHECK.open(encoding="utf-8-sig"))}
    effect: Counter = Counter()
    for c in changed:
        key = ((c["a"]["source_id"], c["a"]["source_record_id"]), (c["b"]["source_id"], c["b"]["source_record_id"]))
        if key in labels:
            effect[f"{c['from'][2]}->{c['to'][2]} hand label {labels[key]}"] += 1
    with (OUT / f"links_rescored_{new_v}.jsonl").open("w") as f:
        for r in rescored:
            f.write(json.dumps(r) + "\n")
    report = {"from_versions": sorted({l["matcher_version"] for l in links}), "to_version": new_v,
              "thresholds": {"accept": ACCEPT, "loose": LOOSE}, "links_considered": len(links) + len(refused),
              "band_moves": dict(moves), "links_changed": len(changed),
              "effect_on_hand_labelled_links": dict(effect), "changed_links": changed[:40]}
    (OUT / f"rescore_to_{new_v}.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "changed_links"}, indent=2))
    for c in changed[:8]:
        print(f"  {c['names'][0]!r} == {c['names'][1]!r}: {c['from'][1:]} -> {c['to'][1:]} ({c['why']})")


if __name__ == "__main__":
    main()
