"""Human labels and the accepted-conflicts allow-list, keyed by pair_id (record level, order-free).

pair_id = the two "source_id#source_record_id" endpoints, sorted, joined by " <-> ".
Final label of a labelled pair = `my_label` in handcheck/part3_verify.csv (the re-check on ABN Lookup) where it exists,
else `label` in handcheck/part3_link_check.csv. Labels are read, never written.
"""

from __future__ import annotations

import csv
from pathlib import Path

CHECK = Path("handcheck/part3_link_check.csv")
VERIFY = Path("handcheck/part3_verify.csv")
ACCEPTED = Path("handcheck/accepted_conflicts.csv")  # hand-written: pair_id, reason, date


def pair_id(a: dict, b: dict) -> str:
    return " <-> ".join(sorted(f"{r['source_id']}#{r['source_record_id']}" for r in (a, b)))


def _rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig"))) if path.exists() else []


def load_labels() -> dict[str, str]:
    final = {r["check_id"]: r["my_label"].strip().upper()[:1] for r in _rows(VERIFY) if r.get("my_label", "").strip()}
    out = {}
    for r in _rows(CHECK):
        lab = final.get(r["check_id"]) or r["label"].strip().upper()[:1]
        if lab in ("Y", "N", "U"):
            out[pair_id({"source_id": r["a_source"], "source_record_id": r["a_record_id"]},
                        {"source_id": r["b_source"], "source_record_id": r["b_record_id"]})] = lab
    return out


def load_allowlist() -> dict[str, dict]:
    return {r["pair_id"]: r for r in _rows(ACCEPTED)}
