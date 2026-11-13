"""The seeded benchmark draw (ARCHITECTURE.md section e). Pure and deterministic: no network, no model, no peeking at content.

  python -m src.benchmark.draw --seed 1 --out outputs/benchmark/dev_seed1/draw.json

Frame: the 2,440-dataset pool (outputs/part1_pool_scored.jsonl) minus the six round-1 sources, minus `find_by_lia_band`
(used to develop the finish rules), minus every dataset in the same FAMILY as one of those (a family is publisher + title with
digits, years and months removed: monthly or yearly siblings of one release). Siblings are listed in the draw file (flagged) and
excluded. One dataset per family: the lowest rank in the shortlist stratum, the lowest dataset_id in the pool stratum.

Dev draw (seed 1): 6 from shortlist ranks 7-50, 5 from the non-shortlist pool, one per format class (csv, xlsx, xls, json,
zip-only: five classes, five slots), plus the injection slot (a fixture pair, see injection.py). The draw file is written once,
before any run; writing it again with different content is refused, so a draw cannot be adjusted after the fact.

The FINAL draw (seed 2) is not made in the dev phase: `--seed 2` is refused unless `--final` is passed. Its shape is
8 shortlist + 7 pool (5 format classes, one no-tabular, one second csv).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

import yaml

POOL = Path("outputs/part1_pool_scored.jsonl")
SHORTLIST = Path("outputs/part1_shortlist.csv")
SOURCES = Path("sources.yaml")
EXTRA_EXCLUDED = ["nsw:find-by-lia-band"]          # used to develop the finish rules (unattended session, phase A)
FORMAT_CLASSES = ("csv", "xlsx", "xls", "json", "zip")
CSV_FORMATS, XLSX_FORMATS, XLS_FORMATS = {"CSV", "TSV"}, {"XLSX"}, {"XLS"}
JSON_FORMATS, ZIP_FORMATS, XML_FORMATS = {"JSON", "GEOJSON", "NDJSON"}, {"ZIP", "GZ"}, {"XML"}
# Counts quoted in ARCHITECTURE.md section e, compared with what this code measures (a difference is reported, not hidden).
ARCH_COUNTS = {"core(csv|xlsx|json)": 1140, "xls": 52, "zip": 87, "xml": 37, "no-tabular": 856, "no-resources": 268}
_MONTHS = ("january february march april may june july august september october november december "
           "jan feb mar apr jun jul aug sep sept oct nov dec").split()
_NOISE = re.compile(r"\b(" + "|".join(_MONTHS) + r"|fy|q[1-4]|version|v)\b|\d+|[^a-z ]+")


def family_key(rec: dict) -> str:
    """Publisher + title with digits, years, months, quarters and punctuation removed, lower-cased, spaces collapsed."""
    title = _NOISE.sub(" ", str(rec.get("title", "")).lower())
    return f"{str(rec.get('organisation', '')).strip().lower()}|{' '.join(title.split())}"


def format_class(rec: dict) -> str:
    fmts = {str(r.get("format", "")).strip().lstrip(".").upper() for r in rec.get("resources") or []}
    if not rec.get("resources"):
        return "no-resources"
    if fmts & CSV_FORMATS:
        return "csv"
    if fmts & XLSX_FORMATS:
        return "xlsx"
    if fmts & JSON_FORMATS:
        return "json"
    if fmts & XLS_FORMATS:
        return "xls"
    if fmts & ZIP_FORMATS:
        return "zip"
    if fmts & XML_FORMATS:
        return "xml"
    return "no-tabular"


def load_pool(path: Path = POOL) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def load_shortlist(path: Path = SHORTLIST) -> dict[str, int]:
    with path.open() as f:
        return {r["dataset_id"]: int(r["rank"]) for r in csv.DictReader(f)}


def excluded_ids(sources: Path = SOURCES) -> list[str]:
    cfg = yaml.safe_load(sources.read_text())
    return [s["dataset_id"] for s in cfg["sources"]] + EXTRA_EXCLUDED


def class_counts(pool: list[dict]) -> dict[str, int]:
    c = Counter(format_class(r) for r in pool)
    return {"csv": c["csv"], "xlsx": c["xlsx"], "json": c["json"], "xls": c["xls"], "zip": c["zip"], "xml": c["xml"],
            "no-tabular": c["no-tabular"], "no-resources": c["no-resources"]}


def build_frame(pool: list[dict], excluded: list[str]) -> tuple[list[dict], dict]:
    """(eligible datasets, report). Excluded = the listed datasets plus their family siblings (flagged in the report)."""
    by_id = {r["dataset_id"]: r for r in pool}
    families = {family_key(by_id[i]) for i in excluded if i in by_id}
    siblings, eligible = [], []
    for r in pool:
        if r["dataset_id"] in excluded:
            continue
        if family_key(r) in families:
            siblings.append(r["dataset_id"])
        else:
            eligible.append(r)
    return eligible, {"excluded": [i for i in excluded if i in by_id], "excluded_missing_from_pool": [i for i in excluded if i not in by_id],
                      "siblings_flagged_and_excluded": sorted(siblings)}


def _item(rec: dict, slot: str, stratum: str, rank: int | None) -> dict:
    return {"slot": slot, "stratum": stratum, "rank": rank, "dataset_id": rec["dataset_id"], "reference": rec["dataset_id"],
            "title": rec.get("title"), "organisation": rec.get("organisation"), "formats": sorted(
                {str(r.get("format", "")).strip().upper() for r in rec.get("resources") or []}),
            "format_class": format_class(rec), "family": family_key(rec)}


def make_draw(seed: int, pool: list[dict], shortlist: dict[str, int], excluded: list[str], *, n_shortlist: int = 6, final: bool = False) -> dict:
    eligible, frame_report = build_frame(pool, excluded)
    rng = random.Random(seed)
    used_families: set[str] = set()

    # shortlist stratum: ranks 7-50, one per family (the lowest rank), then n at random
    cand = sorted((r for r in eligible if 7 <= shortlist.get(r["dataset_id"], 0) <= 50), key=lambda r: shortlist[r["dataset_id"]])
    reps: dict[str, dict] = {}
    for r in cand:
        reps.setdefault(family_key(r), r)
    pick = rng.sample(sorted(reps.values(), key=lambda r: shortlist[r["dataset_id"]]), n_shortlist)
    items = [_item(r, "shortlist", "ranks 7-50", shortlist[r["dataset_id"]]) for r in sorted(pick, key=lambda r: shortlist[r["dataset_id"]])]
    used_families |= {family_key(r) for r in pick}

    # pool stratum: non-shortlist datasets, one family representative per format class, one drawn per class
    # final shape (seed 2, --final): 8 shortlist + 7 pool = the 5 classes, one no-tabular, and a SECOND csv
    # (a different dataset in a different family from the first csv). Appended after the dev slots, so dev is unchanged.
    slots = [(c, f"format: {c}") for c in FORMAT_CLASSES]
    if final:
        slots += [("no-tabular", "format: no-tabular"), ("csv", "format: csv (second)")]
    for cls, stratum in slots:
        pool_cand = {}
        for r in sorted((r for r in eligible if r["dataset_id"] not in shortlist and format_class(r) == cls), key=lambda r: r["dataset_id"]):
            fam = family_key(r)
            if fam not in used_families:
                pool_cand.setdefault(fam, r)
        chosen = rng.choice(sorted(pool_cand.values(), key=lambda r: r["dataset_id"]))
        used_families.add(family_key(chosen))
        items.append(_item(chosen, "pool", stratum, None))

    counts = class_counts(pool)
    core = counts["csv"] + counts["xlsx"] + counts["json"]
    measured = {"core(csv|xlsx|json)": core, "xls": counts["xls"], "zip": counts["zip"], "xml": counts["xml"],
                "no-tabular": counts["no-tabular"], "no-resources": counts["no-resources"]}
    return {"seed": seed, "frame": {**frame_report, "pool_size": len(pool), "eligible": len(eligible), "class_counts_pool": counts,
                                    "class_counts_measured_vs_architecture": {k: {"measured": measured[k], "architecture": ARCH_COUNTS[k]}
                                                                              for k in ARCH_COUNTS}},
            "items": items, "injection": {"slot": "injection", "clean": "tests/fixtures/injection/clean.csv",
                                          "injected": "tests/fixtures/injection/injected.csv"}}


def write_draw_once(draw: dict, path: Path) -> None:
    """Write the draw file; refuse to replace it with different content."""
    text = json.dumps(draw, indent=1, sort_keys=True)
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashlib.sha256(text.encode()).hexdigest():
            raise FileExistsError(f"{path} already exists with different content: a draw is made once and never adjusted")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser(description="Make the seeded benchmark draw (dev draw = seed 1).")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--final", action="store_true", help="required for the final draw (seed 2): refused otherwise")
    a = ap.parse_args()
    if a.seed == 2 and not a.final:
        raise SystemExit("seed 2 is the FINAL draw: it is not made in the dev phase (pass --final only for the real final run)")
    draw = make_draw(a.seed, load_pool(), load_shortlist(), excluded_ids(), **({"n_shortlist": 8, "final": True} if a.final else {}))
    write_draw_once(draw, Path(a.out))
    for it in draw["items"]:
        print(f"{it['slot']:9s} {it['stratum']:14s} rank={it['rank']} {it['dataset_id']}  [{it['format_class']}]  {it['title']}")


if __name__ == "__main__":
    main()
