"""Part 3 precision check: a human labels 50 proposed links.

  python -m src.part3_resolve.handcheck make    -> handcheck/part3_link_check.csv   (fill in 'label')
  python -m src.part3_resolve.handcheck score   -> handcheck/part3_link_result.json

Sampling: the 266+ accepted links are mostly repeats of ~40 businesses (a supplier appears on many invoice
rows), so we sample DISTINCT UNITS = (canonical entity key or name pair, source pair), one link per unit,
chosen at random with a fixed seed. Two strata are sampled so the looser threshold is measured too:
accepted (>= 0.80) and loose (0.60-0.80). Precision is reported PER STRATUM, never blended.

LABELLING RULE (read before starting; one pass, about 20 seconds per row):
  Y = both records describe the same real-world organisation (same legal entity).
  N = different organisations. Includes: a person vs a company; two different companies; a company vs
      its trust, parent or subsidiary (related is NOT the same).
  U = you cannot tell from what is shown. Do not research for more than a minute; mark U.
  Judge by NAME and ADDRESS. The ABN shown is what the matcher used, so equal ABNs are the claim being
  tested, not proof. Same business under a different trading name counts as Y only if the names are
  plausibly the same business.
"""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

from src.part3_resolve.features import load_mentions
from src.part3_resolve.run import SOURCES

LINKS = Path("outputs/part3/links.jsonl")
SHEET = Path("handcheck/part3_link_check.csv")
RESULT = Path("handcheck/part3_link_result.json")
SEED = 20261112
TOTAL_N = 50
ACCEPTED_N = 30  # the rest (20) come from the loose band; if a stratum is smaller, take all of it

COLUMNS = ["check_id", "band", "tier", "link_confidence", "canonical_entity_key", "matched_on",
           "a_source", "a_record_id", "a_legal_name", "a_trading_names", "a_abn", "a_acn", "a_address",
           "b_source", "b_record_id", "b_legal_name", "b_trading_names", "b_abn", "b_acn", "b_address",
           "label", "note"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a proportion. With n this small the interval is wide, and we show it."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, centre - half), 3), round(min(1, centre + half), 3))


def units(links: list[dict]) -> dict[str, list[dict]]:
    """One representative link per (entity-or-name, source pair); chosen deterministically."""
    best: dict[tuple, dict] = {}
    for l in sorted(links, key=lambda l: l["link_id"]):
        e = l["evidence"]
        ident = l["canonical_entity_key"] if l["canonical_entity_key"].startswith("abn:") else \
            (e["name_a"] or "").lower()
        key = (l["band"], ident, l["source_a_record"]["source_id"], l["source_b_record"]["source_id"])
        best.setdefault(key, l)
    out: dict[str, list[dict]] = {"accepted": [], "loose": []}
    for (b, *_), l in best.items():
        out[b].append(l)
    return out


def addr(m: dict) -> str:
    return " ".join(x for x in (m["locality"], m["state"], m["postcode"]) if x) or "(no address)"


def make() -> None:
    links = [json.loads(line) for line in LINKS.open()]
    frame = units(links)
    rng = random.Random(SEED)
    n_acc = min(ACCEPTED_N, len(frame["accepted"]))
    n_loose = min(TOTAL_N - n_acc, len(frame["loose"]))
    n_acc = min(TOTAL_N - n_loose, len(frame["accepted"]))  # if loose is small, take more accepted
    sample = rng.sample(frame["accepted"], n_acc) + rng.sample(frame["loose"], n_loose)
    rng.shuffle(sample)  # mixed order so the labeller is not primed by band
    mentions = {m["mention_id"]: m for m in load_mentions(SOURCES)}
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with SHEET.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for i, l in enumerate(sample, 1):
            a = mentions[f"{l['source_a_record']['source_id']}|{l['source_a_record']['entity_ref']}"]
            b = mentions[f"{l['source_b_record']['source_id']}|{l['source_b_record']['entity_ref']}"]
            w.writerow({
                "check_id": i, "band": l["band"], "tier": l["tier"], "link_confidence": l["link_confidence"],
                "canonical_entity_key": l["canonical_entity_key"], "matched_on": l["evidence"]["how"],
                **{f"{p}_{k}": v for p, m in (("a", a), ("b", b)) for k, v in {
                    "source": m["source_id"], "record_id": m["source_record_id"], "legal_name": m["legal_name"] or "",
                    "trading_names": " | ".join(m["trading_names"]), "abn": m["abn"] or "", "acn": m["acn"] or "",
                    "address": addr(m)}.items()},
                "label": "", "note": ""})
    print(f"wrote {SHEET}: {len(sample)} links ({n_acc} accepted, {n_loose} loose) from frames "
          f"accepted={len(frame['accepted'])} loose={len(frame['loose'])} distinct units (seed {SEED}).")


def score() -> None:
    rows = list(csv.DictReader(SHEET.open(encoding="utf-8-sig")))
    bad = [r["check_id"] for r in rows if r["label"].strip().upper()[:1] not in ("Y", "N", "U")]
    if bad:
        sys.exit(f"unlabelled or invalid rows: {bad}. Use Y, N or U.")
    frame = units([json.loads(line) for line in LINKS.open()])
    res: dict = {"seed": SEED, "labelling_rule": __doc__.split("LABELLING RULE")[1].strip(), "strata": {}}
    for band in ("accepted", "loose"):
        sub = [r for r in rows if r["band"] == band]
        lab = [r["label"].strip().upper()[:1] for r in sub]
        y, n, u = lab.count("Y"), lab.count("N"), lab.count("U")
        res["strata"][band] = {
            "threshold": "link_confidence >= 0.80" if band == "accepted" else "0.60 <= link_confidence < 0.80",
            "sampled": len(sub), "frame_distinct_units": len(frame[band]), "yes": y, "no": n, "unsure": u,
            "precision_excl_unsure": round(y / (y + n), 3) if y + n else None,
            "precision_95ci_excl_unsure": wilson(y, y + n),
            "precision_unsure_counted_wrong": round(y / len(sub), 3) if sub else None,
            "wrong_links": [{"check_id": r["check_id"], "a": r["a_legal_name"], "b": r["b_legal_name"], "tier": r["tier"],
                             "note": r["note"]} for r, x in zip(sub, lab) if x == "N"]}
    a, l = res["strata"]["accepted"], res["strata"]["loose"]
    if a["precision_excl_unsure"] is not None and l["precision_excl_unsure"] is not None:
        wa, wl = a["frame_distinct_units"], l["frame_distinct_units"]
        res["at_loose_threshold_0.60_weighted_by_unit_counts"] = round(
            (a["precision_excl_unsure"] * wa + l["precision_excl_unsure"] * wl) / (wa + wl), 3)
    RESULT.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "labelling_rule"}, indent=2))


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1] if len(sys.argv) > 1 else "make"]()
