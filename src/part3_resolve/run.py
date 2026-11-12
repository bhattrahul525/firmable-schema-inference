"""Part 3: find businesses that appear in more than one source, propose links, refuse the rest.

  python -m src.part3_resolve.run

Identity model (see DECISIONS.md): a LINK TABLE of pairwise, evidence-carrying links between
source records, plus a CANONICAL ENTITY KEY per cluster of linked records (the ABN when verified,
otherwise a hash of the normalised name + state). Links are the primary data; clusters and keys are
derived from accepted links, so a wrong link can be removed and the clusters recomputed.

Steps: mentions -> block (cheap candidate pairs) -> features -> score -> bands -> cluster -> write.
Everything is deterministic and free: no model calls.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from src.part3_resolve.features import load_mentions, pair_features
from src.part3_resolve.keys import rekey_conflicting_name_links
from src.part3_resolve.score import ACCEPT, KEY_RULE_VERSIONS, LOOSE, MATCHER_VERSION, SCORERS, band

SOURCES = ["asic_credit_licensee", "qbcc_licensed_contractors", "qld_health_contracts_2023_24",
           "wa_tenders_awards_2023_24", "vic_liquor_licences", "act_notifiable_invoices"]
OUT = Path("outputs/part3")
MAX_BLOCK = 300  # a name shared by more mentions than this is too generic to trust


def block_pairs(mentions: list[dict]) -> tuple[dict, list[dict]]:
    """Cheap candidate generation. Returns ({(id_a,id_b): [how,...]}, queue entries for skipped blocks)."""
    by_id = {m["mention_id"]: m for m in mentions}
    cand: dict[tuple, list] = defaultdict(list)
    skipped: list[dict] = []

    def add_group(ids: list[str], how: str, label: str) -> None:
        if len(ids) > MAX_BLOCK:
            skipped.append({"kind": "block", "reason": "block_too_large", "detail": f"{how}: {label} ({len(ids)} records)"})
            return
        for x, y in combinations(ids, 2):
            if by_id[x]["source_id"] != by_id[y]["source_id"]:  # we link ACROSS sources
                cand[tuple(sorted((x, y)))].append(how)

    groups: dict[tuple, list[str]] = defaultdict(list)
    abn_suffix: dict[str, list[str]] = defaultdict(list)
    for m in mentions:
        i = m["mention_id"]
        if m["abn"]:
            groups[("abn", m["abn"])].append(i)
            abn_suffix[m["abn"][-9:]].append(i)
        if m["acn"]:
            groups[("acn", m["acn"])].append(i)
        if m["core"]:
            groups[("name", m["core"])].append(i)
            if m["postcode"]:
                groups[("fuzzy", m["postcode"], m["core"].split()[0])].append(i)
    for key, ids in groups.items():
        if key[0] == "fuzzy":  # only pairs that are similar but not identical (exact ones come from 'name')
            ids = [i for i in ids]
        add_group(ids, key[0], str(key[1:]))
    for m in mentions:  # ACN of one record equals the tail of another record's ABN
        if m["acn"]:
            for j in abn_suffix.get(m["acn"], []):
                if by_id[j]["source_id"] != m["source_id"]:
                    cand[tuple(sorted((m["mention_id"], j)))].append("acn_in_abn")
    return cand, skipped


class DSU:
    def __init__(self):
        self.p: dict[str, str] = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def cluster_key(members: list[dict]) -> str:
    abns = {m["abn"] for m in members if m["abn"]}
    if len(abns) == 1:
        return f"abn:{next(iter(abns))}"
    if len(abns) > 1:
        return "conflict:" + "+".join(sorted(abns))  # should never be linked; kept visible if it happens
    first = sorted(members, key=lambda m: m["mention_id"])[0]
    return "name:" + hashlib.sha1(f"{first['core']}|{first['state'] or ''}".encode()).hexdigest()[:12]


def rec(m: dict) -> dict:
    return {"source_id": m["source_id"], "source_record_id": m["source_record_id"], "entity_ref": m["entity_ref"]}


def main() -> None:
    mentions = load_mentions(SOURCES)
    by_id = {m["mention_id"]: m for m in mentions}
    cand, queue = block_pairs(mentions)
    scorer = SCORERS[MATCHER_VERSION]

    links, pair_queue = [], []
    for (x, y), hows in sorted(cand.items()):
        a, b = by_id[x], by_id[y]
        f = pair_features(a, b, "+".join(sorted(set(hows))))
        if "fuzzy" in hows and not (f["name_exact"] or f["abn_equal"] or f["acn_equal"] or f["acn_is_abn_suffix"]) \
                and not (f["name_containment"] >= 0.6 and f["postcode_equal"]):
            continue  # fuzzy block members that are not actually similar are just noise
        conf, tier, why = scorer(f)
        item = {"source_a_record": rec(a), "source_b_record": rec(b), "link_confidence": conf, "tier": tier,
                "evidence": f, "matcher_version": MATCHER_VERSION,
                "thresholds": {"accept": ACCEPT, "loose": LOOSE}}
        if band(conf) == "refused":
            pair_queue.append({"kind": "pair", "reason": why, **item})
        else:
            item["band"] = band(conf)
            links.append(item)

    # Clusters come ONLY from accepted links. We do not merge records just because they share an ABN
    # inside one source: QBCC lists individuals under their company's ABN, so ABN alone would pull
    # a person into the company's cluster. (Found by reading the refused pairs.)
    dsu = DSU()
    for m in mentions:
        dsu.find(m["mention_id"])
    members_of = lambda root: [by_id[i] for i in by_id if dsu.find(i) == root]
    for l in sorted((l for l in links if l["band"] == "accepted"), key=lambda l: -l["link_confidence"]):
        ia = f"{l['source_a_record']['source_id']}|{l['source_a_record']['entity_ref']}"
        ib = f"{l['source_b_record']['source_id']}|{l['source_b_record']['entity_ref']}"
        ra, rb = dsu.find(ia), dsu.find(ib)
        if ra == rb:
            continue
        abns = {m["abn"] for m in by_id.values() if m["abn"] and dsu.find(m["mention_id"]) in (ra, rb)}
        if len(abns) > 1:  # joining would put two different ABNs in one entity: never
            l["band"] = "refused_cluster_conflict"
            continue
        dsu.union(ia, ib)
    clusters: dict[str, list[dict]] = defaultdict(list)
    for m in mentions:
        clusters[dsu.find(m["mention_id"])].append(m)
    keys = {root: cluster_key(ms) for root, ms in clusters.items()}

    for l in links:
        ia = f"{l['source_a_record']['source_id']}|{l['source_a_record']['entity_ref']}"
        ib = f"{l['source_b_record']['source_id']}|{l['source_b_record']['entity_ref']}"
        ra, rb = dsu.find(ia), dsu.find(ib)
        l["canonical_entity_key"] = keys[ra] if ra == rb else cluster_key(clusters[ra] + clusters[rb])
        raw = f"{ia}|{ib}|{MATCHER_VERSION}"
        l["link_id"] = hashlib.sha1(raw.encode()).hexdigest()[:12]
    links = [l for l in links if l["band"] in ("accepted", "loose")]
    key_changes = rekey_conflicting_name_links(links) if MATCHER_VERSION in KEY_RULE_VERSIONS else []

    # records we believed were businesses but cannot link at all (no name and no identifier)
    for m in mentions:
        if not m["legal_name"] and not m["abn"] and not m["acn"]:
            queue.append({"kind": "record", "reason": "no_name_or_identifier", "source_a_record": rec(m),
                          "detail": f"{m['source_id']}: record has only address/type fields"})
    queue += pair_queue

    entities = []
    for root, ms in clusters.items():
        if len({m["source_id"] for m in ms}) > 1:
            entities.append({"canonical_entity_key": keys[root], "sources": sorted({m["source_id"] for m in ms}),
                             "n_records": len(ms), "names": sorted({m["legal_name"] for m in ms if m["legal_name"]})[:6],
                             "records": [rec(m) for m in ms][:50]})
    relationships = [{"relation": "acts_as_trustee_for", "from": rec(m), "from_name": m["legal_name"],
                      "to_name": m["atf_trust"], "note": "relationship only; not merged with the trust"}
                     for m in mentions if m["atf_trust"]]

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("links", links), ("unlinked_queue", queue), ("entities", entities), ("relationships", relationships)):
        with (OUT / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    linked_ids = {f"{l[s]['source_id']}|{l[s]['entity_ref']}" for l in links if l["band"] == "accepted" for s in ("source_a_record", "source_b_record")}
    summary = {
        "matcher_version": MATCHER_VERSION, "thresholds": {"accept": ACCEPT, "loose": LOOSE},
        "mentions_by_source": dict(Counter(m["source_id"] for m in mentions)),
        "links_by_band": dict(Counter(l["band"] for l in links)),
        "links_by_tier_and_band": {f"{t}|{b}": c for (t, b), c in sorted(Counter((l["tier"], l["band"]) for l in links).items())},
        "cross_source_entities": len(entities),
        "queue_by_reason": dict(Counter(q["reason"] for q in queue)),
        "mentions_with_abn_in_no_accepted_link": sum(1 for m in mentions if m["abn"] and m["mention_id"] not in linked_ids),
        "atf_relationships": len(relationships),
        "canonical_keys_rekeyed": len(key_changes),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
