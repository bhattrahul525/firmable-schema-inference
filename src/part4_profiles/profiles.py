"""Profiles built from the m2.0 graph (outputs/part3/graph_*.jsonl). Round-1 `build.py` is left as it was.

  python -m src.part4_profiles.profiles        # writes outputs/profiles/graph_profiles.jsonl + graph_profiles_summary.json
  python -m src.part4_profiles.show <source_id>

A profile = a connected component of `same_as` edges of ANY band (so one loose link makes the whole profile loose;
trust = the weakest band inside it). Two types, always labelled:
  cross_source                       mentions from 2+ onboarded sources
  single_source_register_confirmed   mentions from ONE source + a Business Names record (the register record
                                     enriches fields but is never a second source; the link band is shown)
A component of person nodes only (no ABN) gets no profile. A component whose members carry more than one ABN gets no
profile either and is counted in the summary (conservative; see DECISIONS.md, 7d).

Field choice (the only rule): every distinct value is shown with its provenance; each value scores
field_confidence x source_reliability (the claim kind's reliability the observation carries); the highest score is marked
`chosen`. If the top two scores are equal, NOTHING is marked (`decided: tie_none_chosen`). Address is one unit per record,
never mixed across records. No recency step (observed_at is a file date, not a claim date). Confidences are never blended.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from src.engine.config import config_path, load_config_file
from src.part3_resolve.registers import REGISTER_ID, bn_record_id, load_business_names
from src.part4_profiles.build import ADDRESS_FIELDS, SCALAR_FIELDS, load_observations, norm_value, usable_address_value

PART3 = Path("outputs/part3")
OUT = Path("outputs/profiles")
VERSION = "p2.0"
RANK = {"accepted": 2, "loose": 1}


def score(c: dict) -> float:
    return round(c["field_confidence"] * c["source_reliability"], 4)


def prov(c: dict) -> dict:
    return {k: c.get(k) for k in ("source_id", "source_record_id", "observed_at", "field_confidence", "source_reliability",
                                  "derivation_level", "raw_value")}


def choose(groups: list[dict]) -> tuple[list[dict], str]:
    """groups: [{value, score, claims}] -> (groups sorted best first with `chosen` set, decided)."""
    groups = sorted(groups, key=lambda g: (-g["score"], str(g["value"])))
    for g in groups:
        g["chosen"] = False
    if len(groups) > 1 and groups[0]["score"] == groups[1]["score"]:
        return groups, "tie_none_chosen"
    groups[0]["chosen"] = True
    return groups, "single_value" if len(groups) == 1 else "highest_confidence_x_reliability"


def resolve(field: str, claims: list[dict]) -> dict:
    by = defaultdict(list)
    for c in claims:
        by[norm_value(field, c["value"])].append(c)
    groups = []
    for cs in by.values():
        best = max(cs, key=lambda c: (score(c), str(c["value"])))
        groups.append({"value": best["value"], "score": score(best), "sources": sorted({c["source_id"] for c in cs}),
                       "claims": [prov(c) for c in cs]})
    values, decided = choose(groups)
    return {"decided": decided, "values": values}


def resolve_address(per_record: dict[str, list[dict]]) -> dict | None:
    units = {}
    for mid, claims in per_record.items():
        parts = {c["field"]: c for c in claims if c["field"] in ADDRESS_FIELDS and usable_address_value(c["field"], c["value"])}
        if parts:
            key = tuple(sorted((f, norm_value(f, c["value"])) for f, c in parts.items()))
            u = units.setdefault(key, {"value": {f: c["value"] for f, c in parts.items()}, "score": 0, "sources": set(), "claims": []})
            u["score"] = max(u["score"], max(score(c) for c in parts.values()))
            u["sources"] |= {c["source_id"] for c in parts.values()}
            u["claims"] += [prov(c) for c in parts.values()]
    if not units:
        return None
    for u in units.values():
        u["sources"] = sorted(u["sources"])
    values, decided = choose(list(units.values()))
    return {"decided": decided, "values": values}


def register_claims(bn_rows: dict[str, dict], cfg: dict) -> dict[str, list[dict]]:
    """Business Names records as claims (trading_name, ABN), with the config's confidences."""
    by_canon = {f["canonical"]: f for f in cfg["fields"]}
    out = {}
    for rid, r in bn_rows.items():
        claims = []
        for canon, col in (("entity.trading_name", "BN_NAME"), ("entity.abn", "abn")):
            f = by_canon[canon]
            if r.get(col):
                claims.append({"field": canon, "value": r[col], "raw_value": r[col], "source_id": REGISTER_ID,
                               "source_record_id": rid, "observed_at": cfg.get("snapshot", "snapshot 202611"),
                               "field_confidence": f["field_confidence"], "source_reliability": cfg["source_reliability"]["identity"],
                               "derivation_level": "L0"})
        out[rid] = claims
    return out


def build_profile(members: list[dict], edges: list[dict], obs_by_m: dict, reg_claims: dict) -> dict | None:
    mentions = [n for n in members if n["type"] != "register"]
    regs = [n for n in members if n["type"] == "register"]
    sources = sorted({n["source_id"] for n in mentions})
    if all(n["type"] == "person" for n in mentions):
        return None  # people with no ABN are edge endpoints only
    ptype = "cross_source" if len(sources) >= 2 else "single_source_register_confirmed" if regs else None
    if ptype is None:
        return None
    claims: dict[str, list[dict]] = defaultdict(list)
    per_record = {}
    for n in mentions:
        per_record[n["node_id"]] = obs_by_m.get(n["node_id"], [])
        for o in per_record[n["node_id"]]:
            claims[o["field"]].append(o)
    for r in regs:
        for c in reg_claims.get(r["source_record_id"], []):
            claims[c["field"]].append(c)
    fields = {f: resolve(f, claims[f]) for f in SCALAR_FIELDS if claims.get(f)}
    address = resolve_address(per_record)
    trading = [{"value": g["value"], "sources": g["sources"], "claims": g["claims"]}
               for g in resolve("entity.trading_name", claims["entity.trading_name"])["values"]] if claims.get("entity.trading_name") else []
    trust = min((e["band"] for e in edges), key=RANK.get)
    return {
        "profile_id": "profile:" + hashlib.sha1("|".join(sorted(n["node_id"] for n in members)).encode()).hexdigest()[:12],
        "type": ptype, "trust": trust, "sources": sources, "register_records": [r["source_record_id"] for r in regs],
        "register_counts_as_source": False,
        "links": [{"edge_id": e["edge_id"], "tier": e["tier"], "band": e["band"], "link_confidence": e["link_confidence"],
                   "human_label": e["human_label"], "matcher_version": e["matcher_version"]} for e in edges],
        "members": [{"source_id": n["source_id"], "source_record_id": n["source_record_id"], "node_id": n["node_id"],
                     "type": n["type"]} for n in mentions],
        "fields": fields, "address": address, "trading_names": trading,
        "built_with": {"builder_version": VERSION, "matcher_versions": sorted({e["matcher_version"] for e in edges})},
    }


def main() -> None:
    nodes = {n["node_id"]: n for n in map(json.loads, (PART3 / "graph_nodes.jsonl").open())}
    edges = [e for e in map(json.loads, (PART3 / "graph_edges.jsonl").open()) if e["type"] == "same_as"]
    obs_by_m = load_observations()
    bn = load_business_names()
    bn_rows = {bn_record_id(r): r for rows in bn.by_name.values() for r in rows}
    reg_claims = register_claims(bn_rows, load_config_file(config_path(REGISTER_ID)))

    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        parent[find(e["from"])] = find(e["to"])
    comps, comp_edges = defaultdict(list), defaultdict(list)
    for x in list(parent):
        comps[find(x)].append(nodes[x])
    for e in edges:
        comp_edges[find(e["from"])].append(e)

    profiles, skipped = [], Counter()
    for root, members in comps.items():
        if len({n["abn"] for n in members if n.get("abn")}) > 1:
            skipped["more_than_one_abn"] += 1
            continue
        p = build_profile(members, comp_edges[root], obs_by_m, reg_claims)
        if p:
            profiles.append(p)
        else:
            skipped["person_only_or_no_type"] += 1
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "graph_profiles.jsonl").open("w") as f:
        for p in sorted(profiles, key=lambda p: p["profile_id"]):
            f.write(json.dumps(p, default=str) + "\n")
    summary = {"builder_version": VERSION, "profiles": len(profiles),
               "by_type_and_trust": {f"{t}|{r}": c for (t, r), c in sorted(Counter((p["type"], p["trust"]) for p in profiles).items())},
               "components_skipped": dict(skipped),
               "fields_with_tie_none_chosen": sum(1 for p in profiles for f in p["fields"].values() if f["decided"] == "tie_none_chosen")}
    (OUT / "graph_profiles_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
