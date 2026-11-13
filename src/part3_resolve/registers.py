"""Lookups into the (trimmed) Business Names register: ABN -> rows, normalised name -> holder.

Only Registered rows are used (current names). A register record is evidence, never a mention (R1).
Holder uniqueness (R4): distinct holders = distinct ABNs, and each blank-ABN row counts as its own holder.
A name with more than one holder is REFUSED, never resolved loosely.
"""

from __future__ import annotations

import csv
import hashlib
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


REGISTER_ID = "asic_business_names"


def bn_record_id(r: dict) -> str:
    """Stable id of a register record: BN_STATE_NUM + state of registration (the register's own key). A row with no
    number gets a hash of its name, ABN and registration date instead."""
    if (r.get("BN_STATE_NUM") or "").strip():
        return f"bn:{r['BN_STATE_OF_REG'].strip()}:{r['BN_STATE_NUM'].strip()}"
    return "bn-hash:" + hashlib.sha1(f"{r['BN_NAME']}|{r.get('BN_ABN')}|{r.get('BN_REG_DT')}".encode()).hexdigest()[:12]


def register_links(mentions: list[dict], bn: BusinessNames, idf) -> list[dict]:
    """Candidate mention-register pairs (R2), with the features the m2.0 scorer needs. Two routes:
    (1) mention ABN == a register ABN and a name of that ABN agrees with the mention's name -> T1;
    (2) a mention name key hits the register by name -> holder count decides (more than one holder = refused)."""
    from src.part3_resolve.score import NAME_AGREE_MIN  # local import: score imports features, features not us

    out, seen = [], set()
    for m in mentions:
        names = [n for n in [m["legal_name"], *m["trading_names"]] if n]
        if not names:
            continue

        def make(row, how, name, holders):
            return {"mention": m, "bn_row": row, "evidence": {
                "kind": "register", "how": how, "name_a": name, "name_b": row["BN_NAME"],
                "name_overlap": round(idf.overlap(name, row["BN_NAME"]), 3),
                "name_exact": name_core(name) == name_core(row["BN_NAME"]),
                "abn_equal": bool(m["abn"] and m["abn"] == row["abn"]),
                "abn_differ": bool(m["abn"] and row["abn"] and m["abn"] != row["abn"]),
                "holders": holders, "person_like": m["person_like"], "generic_name": idf.is_generic(name),
                "abn_unverified": m["abn_unverified"], "abn_a": m["abn"], "state_a": m["state"], "state_b": row.get("BN_STATE_OF_REG"),
                "register_holder_abn": row["abn"]}}

        if m["abn"] and bn.by_abn.get(m["abn"]):  # route 1: best-agreeing register name under the same ABN
            best = max(((idf.overlap(n, r["BN_NAME"]), n, r) for n in names for r in bn.by_abn[m["abn"]]),
                       key=lambda t: t[0])
            if best[0] >= NAME_AGREE_MIN or name_core(best[1]) == name_core(best[2]["BN_NAME"]):
                out.append(make(best[2], "register_abn", best[1], 1))
                seen.add((m["mention_id"], bn_record_id(best[2])))
                continue
        for n in names:  # route 2: name bridge
            status, rows = bn.holder_of_name(n)
            if status == "none":
                continue
            row = sorted(rows, key=bn_record_id)[0]
            if (m["mention_id"], bn_record_id(row)) in seen:
                continue
            seen.add((m["mention_id"], bn_record_id(row)))
            out.append(make(row, "register_name", n, len({r["holder"] for r in rows})))
            break  # one register candidate per mention
    # A register record with NO ABN may bridge mentions only if their valid ABNs do not differ. Stored on each link as a
    # feature (not a cross-link lookup at scoring time), so the scorer stays a pure function and rescore can apply it.
    by_record = defaultdict(list)
    for c in out:
        if not c["evidence"]["register_holder_abn"]:
            by_record[bn_record_id(c["bn_row"])].append(c)
    for group in by_record.values():
        if len({c["evidence"]["abn_a"] for c in group if c["evidence"]["abn_a"]}) > 1:
            for c in group:
                c["evidence"]["bridge_abn_conflict"] = True
    return out
