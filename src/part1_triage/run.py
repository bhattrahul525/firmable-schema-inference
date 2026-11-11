"""Part 1 end-to-end: score pool -> de-duplicate -> probe top N -> rank -> shortlist of 50.

Deterministic, no LLM calls. Same inputs (cached catalogue + probe cache) give the
same shortlist.

Run:  python -m src.part1_triage.pull      (once; builds outputs/part1_pool.jsonl)
      python -m src.part1_triage.run

Outputs:
  outputs/part1_pool_scored.jsonl  every pooled dataset with its scores (so cuts are visible)
  outputs/part1_shortlist.csv      top 50, the deliverable
  outputs/part1_shortlist.jsonl    same, plus probe details and sample rows
"""

from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.common.ckan import PORTAL_DATASET_PAGE
from src.part1_triage.probe import probe_dataset
from src.part1_triage.score import score_metadata

POOL_PATH = Path("outputs/part1_pool.jsonl")
SCORED_PATH = Path("outputs/part1_pool_scored.jsonl")
SHORTLIST_CSV = Path("outputs/part1_shortlist.csv")
SHORTLIST_JSONL = Path("outputs/part1_shortlist.jsonl")

PROBE_TOP_N = 120  # content-probe this many after metadata ranking
SHORTLIST_N = 50
W_META, W_PROBE = 0.35, 0.65  # probe weighted higher: it is evidence from the rows themselves
UNPROBED_CAP = 0.5  # a dataset we could not look inside can never outrank one we verified

# Prefer the original state-portal record over data.gov.au's harvested copy.
PORTAL_PREFERENCE = {"nsw": 0, "vic": 0, "qld": 0, "sa": 0, "datagovau": 1}
OPEN_LICENCE_HINT = re.compile(r"cc|creative commons|open|ogl|odc|public domain", re.I)


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def dedupe(pool: list[dict]) -> tuple[list[dict], int]:
    """data.gov.au harvests the state portals, so many datasets appear twice. Two records
    are the same dataset if they share a normalised title AND either the same publishing
    organisation or at least one resource URL. Same title from different councils is kept."""
    pool = sorted(pool, key=lambda r: (PORTAL_PREFERENCE[r["portal"]], r["dataset_id"]))
    seen: set[tuple[str, str]] = set()
    kept, dropped = [], 0
    for r in pool:
        title = _norm_title(r["title"])
        keys = {(title, "org:" + _norm_title(r["organisation"]))}
        keys |= {(title, "url:" + res["url"]) for res in r["resources"] if res["url"]}
        if keys & seen:
            dropped += 1
            continue
        seen |= keys
        kept.append(r)
    return kept, dropped


def licence_of(rec: dict) -> tuple[str, bool]:
    """(licence string, flagged). Missing / 'notspecified' -> 'unknown' and flagged."""
    lic = rec["license_title"] or rec["license_id"]
    if not lic or rec["license_id"] in ("notspecified", "other-closed", ""):
        return ("unknown" if not lic or rec["license_id"] == "notspecified" else lic), True
    return lic, not OPEN_LICENCE_HINT.search(lic)


def reason_of(rec: dict) -> str:
    """One line built only from signals that actually fired."""
    parts = []
    if rec.get("probe_status") == "ok":
        if rec["abn_rate"] > 0:
            parts.append(f"{rec['abn_rate']:.0%} valid ABNs in '{rec['abn_column']}'")
        if rec["suffix_rate"] > 0:
            parts.append(f"company suffix in {rec['suffix_rate']:.0%} of '{rec['suffix_column']}'")
        if rec["header_hits"]:
            parts.append("business columns: " + ", ".join(rec["header_hits"][:3]))
        if not parts:
            parts.append(f"probed {rec['rows_read']} rows: no ABNs, company names or business columns")
    else:
        parts.append(f"content not probed ({rec.get('probe_error', 'below probe cut')})")
    pos = [s.split(" (")[0] for s in rec["meta_signals"] if "(+" in s]
    neg = [s.split(" (")[0] for s in rec["meta_signals"] if "(-" in s]
    if pos:
        parts.append("metadata: " + ", ".join(pos[:3]))
    if neg:
        parts.append("against: " + ", ".join(neg[:2]))
    return "; ".join(parts)


def main() -> None:
    pool = [json.loads(line) for line in POOL_PATH.open()]
    for r in pool:
        r.update(score_metadata(r))
    pool, dropped = dedupe(pool)
    pool.sort(key=lambda r: (-r["meta_raw"], r["dataset_id"]))
    print(f"pool {len(pool) + dropped} -> {len(pool)} after removing {dropped} harvested duplicates")

    to_probe = pool[:PROBE_TOP_N]
    print(f"probing top {len(to_probe)} by metadata score ...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        for rec, result in zip(to_probe, ex.map(probe_dataset, to_probe)):
            rec.update(result)

    for r in pool:
        if r.get("probe_status") == "ok":
            r["confidence"] = round(W_META * r["meta_score"] + W_PROBE * r["probe_score"], 3)
        else:
            r["confidence"] = round(UNPROBED_CAP * r["meta_score"], 3)
        r["licence"], r["licence_flag"] = licence_of(r)
        r["reason"] = reason_of(r)
        r["dataset_page"] = PORTAL_DATASET_PAGE[r["portal"]].format(name=r["name"])
        r["download_url"] = r.get("probe_url") or next(
            (res["url"] for res in r["resources"] if res["url"]), "")

    pool.sort(key=lambda r: (-r["confidence"], -r["meta_raw"], r["dataset_id"]))
    for i, r in enumerate(pool, 1):
        r["rank"] = i

    with SCORED_PATH.open("w") as f:
        for r in pool:
            f.write(json.dumps({k: v for k, v in r.items() if k not in ("notes", "sample_rows")}) + "\n")

    shortlist = pool[:SHORTLIST_N]
    cols = ["rank", "dataset_id", "title", "organisation", "formats", "confidence", "reason",
            "licence", "licence_flag", "dataset_page", "download_url"]
    with SHORTLIST_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in shortlist:
            w.writerow({c: ("|".join(r[c]) if isinstance(r[c], list) else r[c]) for c in cols})
    with SHORTLIST_JSONL.open("w") as f:
        for r in shortlist:
            f.write(json.dumps({k: v for k, v in r.items() if k != "notes"}) + "\n")

    statuses: dict[str, int] = {}
    for r in to_probe:
        statuses[r.get("probe_status", "?")] = statuses.get(r.get("probe_status", "?"), 0) + 1
    print(f"probe results: {statuses}")
    print(f"shortlist: {SHORTLIST_CSV} ({len(shortlist)} rows)\n")
    for r in shortlist:
        print(f"{r['rank']:>3} {r['confidence']:.2f} {r['portal']:9s} {r['title'][:55]:55s} | {r['reason'][:90]}")


if __name__ == "__main__":
    main()
