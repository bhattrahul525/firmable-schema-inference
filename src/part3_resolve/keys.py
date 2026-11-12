"""Canonical entity keys for links, and the guard that stops a name-only link borrowing a wrong ABN.

A link's canonical_entity_key is `abn:<11 digits>` when an ABN is involved. That is safe for identifier links
(T1/T2), where both records carry the ABN and the names agree. It is NOT safe for a name-only link (T3) whose ABN
comes from just ONE record: if that record's ABN is a source error, the link inherits it.

Found by the Part 3 hand check: ACT lists "STRYKER AUSTRALIA PTY LTD" with J.J. Richards & Sons' ABN
(40000805425; Stryker's is 48002873850). The loose Stryker link (ACT record + a QLD Health record with no ABN)
was keyed abn:40000805425, the same key as the genuine J.J. Richards links.

Rule (matcher m1.2): a T3 link keyed by an ABN is re-keyed by NAME + STATE when none of its names agree with any
name carried by the identifier links (T1/T2) under that same key. It is a pure function of the stored evidence,
so `rescore` can apply it to old links without reading any source.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict

from src.part3_resolve.features import containment, name_core

NAME_OK = 0.5  # same threshold the scorer uses to say "these names agree"


def name_key(core: str, state: str | None) -> str:
    return "name:" + hashlib.sha1(f"{core}|{state or ''}".encode()).hexdigest()[:12]


def _cores(link: dict) -> set[str]:
    e = link["evidence"]
    return {c for c in (name_core(e.get("name_a")), name_core(e.get("name_b"))) if c}


def rekey_conflicting_name_links(links: list[dict]) -> list[dict]:
    """Mutates `canonical_entity_key` on offending T3 links and returns a list of what changed:
    [{link_id, from, to, why}]. Identifier links (T1/T2) are never touched."""
    by_key: dict[str, list[dict]] = defaultdict(list)
    for l in links:
        by_key[l["canonical_entity_key"]].append(l)
    changes = []
    for key, group in by_key.items():
        if not key.startswith("abn:"):
            continue
        anchors = {c for l in group if not l["tier"].startswith("T3") for c in _cores(l)}
        if not anchors:
            continue  # nothing to compare against: we cannot tell the ABN is wrong
        for l in group:
            if not l["tier"].startswith("T3"):
                continue
            if any(containment(c, a) >= NAME_OK for c in _cores(l) for a in anchors):
                continue  # agrees with at least one anchor name: the ABN key is consistent
            e = l["evidence"]
            core = name_core(e.get("name_a")) or name_core(e.get("name_b"))
            new = name_key(core, e.get("state_a") or e.get("state_b"))
            changes.append({"link_id": l.get("link_id"), "from": key, "to": new,
                            "names": [e.get("name_a"), e.get("name_b")],
                            "why": "name-only link disagrees with every identifier link under this ABN key"})
            l["canonical_entity_key"] = new
            l["key_note"] = f"re-keyed from {key}: its names disagree with the identifier links under that ABN"
    return changes
