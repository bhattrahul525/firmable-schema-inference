"""Turn observations into one 'mention' per entity per source record, and compute the features
the matcher scores. No decisions are made here; this file only describes records and pairs.

A mention = what ONE source record says about ONE entity (the observations sharing an entity_ref).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.common.names import ATF, SUFFIX_TOKENS, name_core  # noqa: F401  (re-exported; moved in step 7a)

OBS_DIR = Path("outputs/observations")

# A name with none of these, made of 2-4 plain words, looks like a person ("Michael William Argus").
BUSINESS_WORDS = {
    "pty", "ltd", "limited", "inc", "incorporated", "club", "hotel", "group", "holdings", "services", "trust",
    "association", "partners", "partnership", "enterprises", "company", "co", "cooperative", "corporation",
    "council", "school", "college", "finance", "capital", "solutions", "industries", "consulting", "pharmacy",
    "construction", "constructions", "plumbing", "electrical", "building", "builders", "homes", "australia",
    "australian", "queensland", "foundation", "society", "centre", "center", "hospital", "health", "bank",
    "insurance", "legal", "accounting", "property", "properties", "developments", "engineering", "technologies",
    "systems", "management", "mortgage", "loans", "lending", "advisers", "advisory", "financial", "agency",
}


def atf_trust(name: str | None) -> str | None:
    """'X Pty Ltd ATF The X Family Trust' -> 'The X Family Trust' (a relationship, not a merge)."""
    parts = ATF.split(name or "", maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else None


def person_like(name: str, entity_type: str) -> bool:
    """True if the name looks like an individual. Deliberately crude and conservative: when it says
    'person' we refuse to link on the name alone."""
    if entity_type == "company":
        return False
    toks = re.sub(r"[^a-z ]", " ", name.lower()).split()
    if not 2 <= len(toks) <= 4 or any(t in BUSINESS_WORDS for t in toks):
        return False
    return all(len(t) > 1 for t in toks)


def containment(a: str, b: str) -> float:
    """Share of the shorter name's words found in the other. 'metcash' vs 'metcash food division' = 1.0."""
    ta, tb = set(a.split()), set(b.split())
    return len(ta & tb) / min(len(ta), len(tb)) if ta and tb else 0.0


def load_mentions(sources: list[str]) -> list[dict]:
    mentions: dict[str, dict] = {}
    for sid in sources:
        for line in (OBS_DIR / f"{sid}.jsonl").open():
            o = json.loads(line)
            mid = f"{sid}|{o['entity_ref']}"
            m = mentions.setdefault(mid, {
                "mention_id": mid, "source_id": sid, "source_record_id": o["source_record_id"],
                "entity_ref": o["entity_ref"], "legal_name": None, "trading_names": [], "abn": None,
                "acn": None, "state": None, "postcode": None, "locality": None, "entity_type": "unknown"})
            f, v = o["field"], o["value"]
            if f == "entity.legal_name":
                m["legal_name"] = v
            elif f == "entity.trading_name":
                m["trading_names"].append(v)
            elif f in ("entity.abn", "entity.acn", "entity.entity_type"):
                m[f.split(".")[1]] = v
            elif f in ("address.state", "address.postcode", "address.locality"):
                m[f.split(".")[1]] = v
    out = list(mentions.values())
    for m in out:
        m["core"] = name_core(m["legal_name"])
        m["trading_cores"] = [c for c in (name_core(t) for t in m["trading_names"]) if c]
        m["person_like"] = bool(m["legal_name"]) and person_like(m["legal_name"], m["entity_type"])
        m["atf_trust"] = atf_trust(m["legal_name"])
    return out


def pair_features(a: dict, b: dict, how: str) -> dict:
    """Everything a scorer may use about a candidate pair. Stored on the link so it can be
    re-scored later without re-reading the sources."""
    shared_trading = bool(set(a["trading_cores"]) & set(b["trading_cores"])) or \
        bool({a["core"]} & set(b["trading_cores"])) or bool({b["core"]} & set(a["trading_cores"]))
    return {
        "how": how,  # which blocking rule proposed the pair
        "abn_equal": bool(a["abn"] and a["abn"] == b["abn"]),
        "abn_differ": bool(a["abn"] and b["abn"] and a["abn"] != b["abn"]),
        "acn_equal": bool(a["acn"] and a["acn"] == b["acn"]),
        "acn_is_abn_suffix": bool((a["acn"] and b["abn"] and b["abn"][-9:] == a["acn"]) or
                                  (b["acn"] and a["abn"] and a["abn"][-9:] == b["acn"])),
        "name_a": a["legal_name"], "name_b": b["legal_name"],
        "name_exact": bool(a["core"]) and a["core"] == b["core"],
        "name_containment": round(containment(a["core"], b["core"]), 3),
        "shared_trading_name": shared_trading,
        "name_len": min(len(a["core"]), len(b["core"])),
        "name_tokens": min(len(a["core"].split()), len(b["core"].split())),
        # a person-like name on ONE side is not enough: its counterpart may carry "Pty Ltd" (a business)
        "person_like": a["person_like"] and b["person_like"],
        "both_company": a["entity_type"] == "company" and b["entity_type"] == "company",
        "postcode_a": a["postcode"], "postcode_b": b["postcode"],
        "postcode_equal": bool(a["postcode"] and a["postcode"] == b["postcode"]),
        "postcode_differ": bool(a["postcode"] and b["postcode"] and a["postcode"] != b["postcode"]),
        "state_a": a["state"], "state_b": b["state"],
        "state_equal": bool(a["state"] and a["state"] == b["state"]),
        "state_differ": bool(a["state"] and b["state"] and a["state"] != b["state"]),
    }
