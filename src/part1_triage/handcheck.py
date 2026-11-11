"""Part 1 false-positive check: a human labels a random 20 of the 50.

  python -m src.part1_triage.handcheck make    -> handcheck/part1_fp_check.csv  (fill in by hand)
  python -m src.part1_triage.handcheck score   -> handcheck/part1_fp_result.json

The sample is random with a fixed seed, so it is reproducible and not cherry-picked.

Labelling rule (applied by the human, written down so it is applied consistently):
  Y = rows name specific Australian businesses / non-government organisations
      (company, sole trader, partnership, trust, incorporated association), one per row
      or as a named party on each row, for a meaningful share of rows.
  N = no such entities: aggregates, individuals only, government bodies only,
      or the data does not actually contain the names.
  U = cannot tell (e.g. the file is unreachable). Reported separately, never counted as Y.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

SHORTLIST = Path("outputs/part1_shortlist.jsonl")
SHEET = Path("handcheck/part1_fp_check.csv")
RESULT = Path("handcheck/part1_fp_result.json")
SEED = 20261111
SAMPLE_N = 20

# The rule the human reviewer actually applied (settled during the check, 2026-11-11).
LABEL_RULE = (
    "Rule A: Y only if the MAIN entity on most rows is a non-government business. "
    "Registers of individuals (advisers, auditors, credit reps) are N even when a company "
    "appears as a secondary party. Government bodies are N. In contract/invoice data the "
    "supplier is the entity (the government buyer is ignored). Licensed clubs counted Y; "
    "a foundation-run childcare register counted N (reviewer judged foundations not businesses)."
)

COLUMNS = ["check_id", "rank", "dataset_id", "title", "organisation", "confidence", "reason",
           "dataset_page", "download_url", "sample_headers", "sample_row_1", "sample_row_2",
           "sample_row_3", "contains_business", "note"]


def _row_text(row: dict) -> str:
    return " | ".join(f"{k}={v}" for k, v in row.items() if v)[:400]


def make() -> None:
    shortlist = [json.loads(line) for line in SHORTLIST.open()]
    sample = random.Random(SEED).sample(shortlist, SAMPLE_N)
    sample.sort(key=lambda r: r["rank"])
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with SHEET.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for i, r in enumerate(sample, 1):
            rows = r.get("sample_rows") or []
            w.writerow({
                "check_id": i, "rank": r["rank"], "dataset_id": r["dataset_id"], "title": r["title"],
                "organisation": r["organisation"], "confidence": r["confidence"], "reason": r["reason"],
                "dataset_page": r["dataset_page"], "download_url": r["download_url"],
                "sample_headers": " | ".join(r.get("sample_headers") or []),
                **{f"sample_row_{j + 1}": _row_text(rows[j]) if j < len(rows) else "" for j in range(3)},
                "contains_business": "", "note": "",
            })
    print(f"wrote {SHEET}: {SAMPLE_N} of {len(shortlist)} (seed {SEED}). Fill 'contains_business' with Y/N/U.")


def score() -> None:
    rows = list(csv.DictReader(SHEET.open(encoding="utf-8-sig")))  # Excel adds a BOM
    labels = [r["contains_business"].strip().upper()[:1] for r in rows]
    missing = [r["check_id"] for r, lab in zip(rows, labels) if lab not in ("Y", "N", "U")]
    if missing:
        sys.exit(f"unlabelled or invalid rows: {missing}. Use Y, N or U.")
    y, n, u = labels.count("Y"), labels.count("N"), labels.count("U")
    result = {
        "labelling_rule": LABEL_RULE,
        "sample_size": len(rows), "seed": SEED, "yes": y, "no": n, "unsure": u,
        "false_positive_rate_excl_unsure": round(n / (y + n), 3) if y + n else None,
        "false_positive_rate_unsure_counted_as_fp": round((n + u) / len(rows), 3),
        "false_positives": [{"rank": r["rank"], "title": r["title"], "note": r["note"]}
                            for r, lab in zip(rows, labels) if lab == "N"],
        "unsure_items": [{"rank": r["rank"], "title": r["title"], "note": r["note"]}
                   for r, lab in zip(rows, labels) if lab == "U"],
    }
    RESULT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1] if len(sys.argv) > 1 else "make"]()
