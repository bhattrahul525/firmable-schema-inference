"""The relationship graph, built from the m2.0 link table (the model chosen in the write-up: nodes + typed edges).

Nodes  mention (one source record's claim about one entity) | register (a Business Names record) | person (a
       person-like mention) | entity (DERIVED: a connected component of accepted same_as edges; recomputed on every
       build, never stored as truth, so a better matcher just yields different components).
Edges  same_as   from the link table (accepted and loose bands; only accepted ones form entities)
       nominee_of  a person-like name listed under the ABN of a company-like name (the QBCC pattern); loose, 0.70, a
                   hand-set relationship score (not calibrated, not an identity claim)
NOT built: renamed_to, trustee_for (the ATF handling in run.py stays as it is).

edge_id = sha1(type + endpoints) and does NOT include the matcher version, so the same pair keeps one id across
matcher versions; `previous` then records the earlier version's tier/band/confidence (read from the graph file being
replaced). human_label comes from the hand-check CSVs where one exists.

  python -m src.part3_resolve.graph
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from src.part3_resolve.features import load_mentions
from src.part3_resolve.labels import load_labels, pair_id
from src.part3_resolve.run import SOURCES

OUT = Path("outputs/part3")
OBS = Path("outputs/observations")
NOMINEE_CONF = 0.70
NOMINEE_THRESHOLDS = {"accept": 0.80, "loose": 0.60}


def edge_id(etype: str, a: str, b: str) -> str:
    ends = [a, b] if etype == "nominee_of" else sorted([a, b])  # nominee_of is directed (person -> company)
    return hashlib.sha1(f"{etype}|{ends[0]}|{ends[1]}".encode()).hexdigest()[:12]


def node_id(rec: dict) -> str:
    return f"{rec['source_id']}|{rec.get('entity_ref') or rec['source_record_id']}"


def observed_dates() -> dict[tuple, dict]:
    out = {}
    for sid in SOURCES:
        for line in (OBS / f"{sid}.jsonl").open():
            o = json.loads(line)
            out.setdefault((sid, o["source_record_id"]), {"observed_at": o["observed_at"], "ingested_at": o["ingested_at"]})
    return out


def sources_of(link_or_rec: list[dict], dates: dict, snapshot: str | None) -> list[dict]:
    res = []
    for r in link_or_rec:
        d = dates.get((r["source_id"], r["source_record_id"]))
        res.append({"source_id": r["source_id"], "source_record_id": r["source_record_id"],
                    **(d or {"snapshot": snapshot})})
    return res


def nominee_edges(mentions: list[dict]) -> list[dict]:
    by_abn = defaultdict(list)
    for m in mentions:
        if m["abn"]:
            by_abn[m["abn"]].append(m)
    out = []
    for abn, group in by_abn.items():
        companies = {}
        for m in group:  # one company-like mention per distinct normalised name
            if m["core"] and not m["person_like"]:
                companies.setdefault(m["core"], m)
        for p in (m for m in group if m["person_like"]):
            for c in companies.values():
                out.append((p, c, abn))
    return out


def abn_offenders(edges: list[dict], nodes: dict) -> list[dict]:
    """Components of same_as edges of ANY band that hold more than one ABN."""
    allp: dict[str, str] = {}

    def afind(x):
        allp.setdefault(x, x)
        while allp[x] != x:
            allp[x] = allp[allp[x]]
            x = allp[x]
        return x

    for e in edges:
        if e["type"] == "same_as":
            allp[afind(e["from"])] = afind(e["to"])
    groups = defaultdict(list)
    for x in list(allp):
        groups[afind(x)].append(x)
    return [{"members": [(nodes[m]["name"], nodes[m]["abn"]) for m in ms],
             "abns": sorted({nodes[m]["abn"] for m in ms if nodes[m].get("abn")})}
            for ms in groups.values() if len({nodes[m]["abn"] for m in ms if nodes[m].get("abn")}) > 1]


def main() -> None:
    mentions = load_mentions(SOURCES)
    links = [json.loads(l) for l in (OUT / "links.jsonl").open()]
    labels = load_labels()
    dates = observed_dates()
    snapshot = yaml.safe_load(Path("configs/reference_sources.yaml").read_text())["sources"][0]["path"].split("_")[-1][:6]
    old = {}
    if (OUT / "graph_edges.jsonl").exists():
        old = {e["edge_id"]: e for e in map(json.loads, (OUT / "graph_edges.jsonl").open())}

    nodes: dict[str, dict] = {}
    for m in mentions:
        nid = f"{m['source_id']}|{m['entity_ref']}"
        nodes[nid] = {"node_id": nid, "type": "person" if m["person_like"] and not m["abn"] else "mention",  # nominee persons are retyped below
                      "name": m["legal_name"], "abn": m["abn"], "source_id": m["source_id"], "source_record_id": m["source_record_id"]}
    edges = []

    def add(etype, ra, rb, tier, band, conf, evidence, matcher_version, thresholds, note=None):
        na, nb = node_id(ra), node_id(rb)
        eid = edge_id(etype, na, nb)
        prev = old.get(eid)
        previous = None
        if prev:
            previous = prev["previous"] if prev["matcher_version"] == matcher_version else \
                {k: prev[k] for k in ("matcher_version", "tier", "band", "link_confidence")}
        edges.append({"edge_id": eid, "type": etype, "from": na, "to": nb, "tier": tier, "band": band,
                      "link_confidence": conf, "evidence": evidence, "sources": sources_of([ra, rb], dates, snapshot),
                      "matcher_version": matcher_version, "thresholds": thresholds, "previous": previous,
                      "human_label": labels.get(pair_id(ra, rb)), **({"note": note} if note else {})})

    for l in links:
        ra, rb = l["source_a_record"], l["source_b_record"]
        if rb["entity_ref"] is None:  # register record
            nodes.setdefault(node_id(rb), {"node_id": node_id(rb), "type": "register", "name": l["evidence"]["name_b"],
                                           "abn": l["evidence"]["register_holder_abn"], "source_id": rb["source_id"],
                                           "source_record_id": rb["source_record_id"]})
        add("same_as", ra, rb, l["tier"], l["band"], l["link_confidence"], l["evidence"], l["matcher_version"],
            l["thresholds"], l.get("note"))
    for p, c, abn in nominee_edges(mentions):
        rec = lambda m: {"source_id": m["source_id"], "source_record_id": m["source_record_id"], "entity_ref": m["entity_ref"]}
        nodes[f"{p['source_id']}|{p['entity_ref']}"]["type"] = "person"
        add("nominee_of", rec(p), rec(c), "N1_person_under_company_abn", "loose", NOMINEE_CONF,
            {"abn": abn, "person_name": p["legal_name"], "company_name": c["legal_name"],
             "same_source": p["source_id"] == c["source_id"]}, "m2.0", NOMINEE_THRESHOLDS)

    # entities: connected components of ACCEPTED same_as edges
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        if e["type"] == "same_as" and e["band"] == "accepted":
            parent[find(e["from"])] = find(e["to"])
    comps = defaultdict(list)
    for x in list(parent):
        comps[find(x)].append(x)
    for members in comps.values():
        if len(members) > 1:
            members = sorted(members)
            abns = sorted({nodes[m]["abn"] for m in members if nodes[m]["abn"]})
            eid = "entity:" + hashlib.sha1("|".join(members).encode()).hexdigest()[:12]
            nodes[eid] = {"node_id": eid, "type": "entity", "members": members, "abns": abns}

    offenders = abn_offenders(edges, nodes)  # ABN check over ALL same_as edges (accepted and loose); reports, never a silent zero
    (OUT / "graph_checks.json").write_text(json.dumps({"components_with_more_than_one_abn_all_same_as_edges": offenders}, indent=2))

    with (OUT / "graph_nodes.jsonl").open("w") as f:
        for n in nodes.values():
            f.write(json.dumps(n) + "\n")
    with (OUT / "graph_edges.jsonl").open("w") as f:
        for e in edges:
            f.write(json.dumps(e) + "\n")
    print(json.dumps({"nodes": dict(Counter(n["type"] for n in nodes.values())),
                      "edges": dict(Counter(e["type"] for e in edges)),
                      "edges_by_band": {f"{t}|{b}": c for (t, b), c in Counter((e["type"], e["band"]) for e in edges).items()},
                      "components_with_more_than_one_abn_all_edges": len(offenders),
                      "entities_with_more_than_one_abn": sum(1 for n in nodes.values() if n["type"] == "entity" and len(n["abns"]) > 1),
                      "labelled_edges": sum(1 for e in edges if e["human_label"])}, indent=2, default=str))


if __name__ == "__main__":
    main()
