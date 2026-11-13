"""Lookups into the (trimmed) Business Names register: ABN -> rows, normalised name -> holder.

Only Registered rows are used (current names). A register record is evidence, never a mention (R1).
Holder uniqueness (R4): distinct holders = distinct ABNs, and each blank-ABN row counts as its own holder.
A name with more than one holder is REFUSED, never resolved loosely.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from src.common.ids import normalise_abn
from src.common.names import name_core

TRIMMED = Path("data/reference/asic_business_names_trimmed.csv")


class BusinessNames:
    def __init__(self, rows):
        self.by_abn: dict[str, list[dict]] = defaultdict(list)
        self.by_name: dict[str, list[dict]] = defaultdict(list)
        for i, r in enumerate(rows):
            if (r.get("BN_STATUS") or "").strip() != "Registered":
                continue
            abn = normalise_abn(r.get("BN_ABN"))
            r = {**r, "abn": abn, "holder": abn or f"blank-row-{i}"}
            if abn:
                self.by_abn[abn].append(r)
            if (key := name_core(r.get("BN_NAME"))):
                self.by_name[key].append(r)

    def names_of_abn(self, abn: str | None) -> list[str]:
        return [r["BN_NAME"] for r in self.by_abn.get(abn or "", [])]

    def holder_of_name(self, name: str | None) -> tuple[str, list[dict]]:
        """('none' | 'ok' | 'refused', rows). 'ok' means exactly one holder (which may have no ABN)."""
        rows = self.by_name.get(name_core(name), [])
        holders = {r["holder"] for r in rows}
        return ("none" if not rows else "ok" if len(holders) == 1 else "refused"), rows


def load_business_names(path: Path = TRIMMED) -> BusinessNames:
    with path.open(newline="", encoding="utf-8") as f:
        return BusinessNames(csv.DictReader(f))
