"""Part 3 precision check: a human labels 50 proposed links.

  python -m src.part3_resolve.handcheck make    -> handcheck/part3_link_check.csv   (fill in 'label')
  python -m src.part3_resolve.handcheck score   -> handcheck/part3_link_result.json
  python -m src.part3_resolve.handcheck step8   -> handcheck/step8_sheet.csv (blind) + step8_key.csv

Sampling: the 266+ accepted links are mostly repeats of ~40 businesses (a supplier appears on many invoice
rows), so we sample DISTINCT UNITS = (canonical entity key or name pair, source pair), one link per unit,
chosen at random with a fixed seed. Two strata are sampled so the looser threshold is measured too:
accepted (>= 0.80) and loose (0.60-0.80). Precision is reported PER STRATUM, never blended.

LABELLING RULE (read before starting; one pass, about 20 seconds per row):
  Y = both records describe the same real-world organisation (same legal entity).
  N = different organisations. Includes: a person vs a company; two different companies; a company vs
      its trust, parent or subsidiary (related is NOT the same).
  U = you cannot tell from what is shown. Do not research for more than a minute; mark U.
  Judge by NAME and ADDRESS. The ABN shown is what the matcher used, so equal ABNs are the claim being
  tested, not proof. Same business under a different trading name counts as Y only if the names are
  plausibly the same business.
"""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

from src.part3_resolve.features import load_mentions, name_core
from src.part3_resolve.run import SOURCES

LINKS = Path("outputs/part3/links.jsonl")
SHEET = Path("handcheck/part3_link_check.csv")
RESULT = Path("handcheck/part3_link_result.json")
SEED = 20261112
TOTAL_N = 50
ACCEPTED_N = 30  # the rest (20) come from the loose band; if a stratum is smaller, take all of it

COLUMNS = ["check_id", "band", "tier", "link_confidence", "canonical_entity_key", "matched_on",
           "a_source", "a_record_id", "a_legal_name", "a_trading_names", "a_abn", "a_acn", "a_address",
           "b_source", "b_record_id", "b_legal_name", "b_trading_names", "b_abn", "b_acn", "b_address",
           "label", "note"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a proportion. With n this small the interval is wide, and we show it."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, centre - half), 3), round(min(1, centre + half), 3))


def units(links: list[dict]) -> dict[str, list[dict]]:
    """One representative link per (entity-or-name, source pair); chosen deterministically."""
    best: dict[tuple, dict] = {}
    for l in sorted(links, key=lambda l: l["link_id"]):
        e = l["evidence"]
        ident = l["canonical_entity_key"] if l["canonical_entity_key"].startswith("abn:") else \
            (e["name_a"] or "").lower()
        key = (l["band"], ident, l["source_a_record"]["source_id"], l["source_b_record"]["source_id"])
        best.setdefault(key, l)
    out: dict[str, list[dict]] = {"accepted": [], "loose": []}
    for (b, *_), l in best.items():
        out[b].append(l)
    return out


def addr(m: dict) -> str:
    return " ".join(x for x in (m["locality"], m["state"], m["postcode"]) if x) or "(no address)"


def make() -> None:
    links = [json.loads(line) for line in LINKS.open()]
    frame = units(links)
    rng = random.Random(SEED)
    n_acc = min(ACCEPTED_N, len(frame["accepted"]))
    n_loose = min(TOTAL_N - n_acc, len(frame["loose"]))
    n_acc = min(TOTAL_N - n_loose, len(frame["accepted"]))  # if loose is small, take more accepted
    sample = rng.sample(frame["accepted"], n_acc) + rng.sample(frame["loose"], n_loose)
    rng.shuffle(sample)  # mixed order so the labeller is not primed by band
    mentions = {m["mention_id"]: m for m in load_mentions(SOURCES)}
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with SHEET.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for i, l in enumerate(sample, 1):
            a = mentions[f"{l['source_a_record']['source_id']}|{l['source_a_record']['entity_ref']}"]
            b = mentions[f"{l['source_b_record']['source_id']}|{l['source_b_record']['entity_ref']}"]
            w.writerow({
                "check_id": i, "band": l["band"], "tier": l["tier"], "link_confidence": l["link_confidence"],
                "canonical_entity_key": l["canonical_entity_key"], "matched_on": l["evidence"]["how"],
                **{f"{p}_{k}": v for p, m in (("a", a), ("b", b)) for k, v in {
                    "source": m["source_id"], "record_id": m["source_record_id"], "legal_name": m["legal_name"] or "",
                    "trading_names": " | ".join(m["trading_names"]), "abn": m["abn"] or "", "acn": m["acn"] or "",
                    "address": addr(m)}.items()},
                "label": "", "note": ""})
    print(f"wrote {SHEET}: {len(sample)} links ({n_acc} accepted, {n_loose} loose) from frames "
          f"accepted={len(frame['accepted'])} loose={len(frame['loose'])} distinct units (seed {SEED}).")


def distinct_businesses(rows: list[dict]) -> dict:
    """How many different real-world businesses the checked rows cover (several rows can be the same business,
    e.g. the same supplier on two source pairs). Rows are joined when they share an ABN (accepted rows only: a
    loose link's ABN may come from one record and be wrong) or share a normalised name. Reported so the sample
    size is not overstated."""
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for r in rows:
        nodes = [f"name:{name_core(r['a_legal_name'])}", f"name:{name_core(r['b_legal_name'])}"]
        if r["band"] == "accepted" and r["a_abn"] and r["a_abn"] == r["b_abn"]:
            nodes.append(f"abn:{r['a_abn']}")
        for n in nodes[1:]:
            parent[find(n)] = find(nodes[0])
    comp = {band: len({find(f"name:{name_core(r['a_legal_name'])}") for r in rows if r["band"] == band})
            for band in ("accepted", "loose")}
    return {"all_rows": len({find(f"name:{name_core(r['a_legal_name'])}") for r in rows}), "accepted_rows": comp["accepted"],
            "loose_rows": comp["loose"]}


def score() -> None:
    rows = list(csv.DictReader(SHEET.open(encoding="utf-8-sig")))
    bad = [r["check_id"] for r in rows if r["label"].strip().upper()[:1] not in ("Y", "N", "U")]
    if bad:
        sys.exit(f"unlabelled or invalid rows: {bad}. Use Y, N or U.")
    frame = units([json.loads(line) for line in LINKS.open()])
    res: dict = {"seed": SEED, "labelling_rule": __doc__.split("LABELLING RULE")[1].strip(), "strata": {}}
    for band in ("accepted", "loose"):
        sub = [r for r in rows if r["band"] == band]
        lab = [r["label"].strip().upper()[:1] for r in sub]
        y, n, u = lab.count("Y"), lab.count("N"), lab.count("U")
        res["strata"][band] = {
            "threshold": "link_confidence >= 0.80" if band == "accepted" else "0.60 <= link_confidence < 0.80",
            "sampled": len(sub), "frame_distinct_units": len(frame[band]), "yes": y, "no": n, "unsure": u,
            "precision_excl_unsure": round(y / (y + n), 3) if y + n else None,
            "precision_95ci_excl_unsure": wilson(y, y + n),
            "precision_unsure_counted_wrong": round(y / len(sub), 3) if sub else None,
            "wrong_links": [{"check_id": r["check_id"], "a": r["a_legal_name"], "b": r["b_legal_name"], "tier": r["tier"],
                             "note": r["note"]} for r, x in zip(sub, lab) if x == "N"]}
    res["distinct_businesses_checked"] = distinct_businesses(rows)
    res["rows_checked"] = len(rows)
    a, l = res["strata"]["accepted"], res["strata"]["loose"]
    if a["precision_excl_unsure"] is not None and l["precision_excl_unsure"] is not None:
        wa, wl = a["frame_distinct_units"], l["frame_distinct_units"]
        res["at_loose_threshold_0.60_weighted_by_unit_counts"] = round(
            (a["precision_excl_unsure"] * wa + l["precision_excl_unsure"] * wl) / (wa + wl), 3)
        res["at_loose_threshold_0.60_weighted_unsure_counted_wrong"] = round(
            (a["precision_unsure_counted_wrong"] * wa + l["precision_unsure_counted_wrong"] * wl) / (wa + wl), 3)
    RESULT.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "labelling_rule"}, indent=2))


# ---- step 8: blind sheet over the m2.0 graph ------------------------------------------------------------------
STEP8_SEED = 7  # NOT seed 2 (the final benchmark draw)
STEP8_SHEET = Path("handcheck/step8_sheet.csv")
STEP8_KEY = Path("handcheck/step8_key.csv")
STEP8_COLUMNS = ["check_id"] + [c for c in COLUMNS if c.startswith(("a_", "b_"))] + ["label", "notes"]  # no tier / band / confidence / key / matched_on
STEP8_ASK = {"register_bridged_loose": 6, "register_bridged_accepted": 4, "no_abn": 4, "t1r": 99, "sole_trader": 2}


def step8_strata(edges: list[dict], nodes: dict, sole_trader_ids: set[str]) -> dict[str, list[dict]]:
    """Candidate same_as edges per stratum. Sampling order (in make_step8) is: loose bridge, accepted register, T1r,
    sole trader, then no-ABN, and an edge is used once (a later stratum skips edges an earlier one took)."""
    same = sorted((e for e in edges if e["type"] == "same_as"), key=lambda e: e["edge_id"])
    no_abn = lambda e: not nodes[e["from"]].get("abn") or (nodes[e["to"]]["type"] != "register" and not nodes[e["to"]].get("abn"))
    return {
        "register_bridged_loose": [e for e in same if e["tier"] == "T3_register_name"],
        "register_bridged_accepted": [e for e in same if e["tier"] == "T1_register_abn"],
        "t1r": [e for e in same if e["tier"].startswith("T1r")],
        "sole_trader": [e for e in same if e["from"] in sole_trader_ids or e["to"] in sole_trader_ids],
        "no_abn": [e for e in same if no_abn(e) and not e["evidence"].get("abn_equal")],
    }


def make_step8() -> None:
    from src.part3_resolve.labels import pair_id
    from src.part3_resolve.registers import bn_record_id, load_business_names

    edges = [json.loads(l) for l in Path("outputs/part3/graph_edges.jsonl").open()]
    nodes = {n["node_id"]: n for n in map(json.loads, Path("outputs/part3/graph_nodes.jsonl").open())}
    mentions = {m["mention_id"]: m for m in load_mentions(SOURCES)}
    bn = load_business_names()
    bn_rows = {bn_record_id(r): r for rows in bn.by_name.values() for r in rows}
    sole = {nid for nid, m in mentions.items() if m["person_like"] and m["abn"]}
    strata = step8_strata(edges, nodes, sole)
    rng = random.Random(STEP8_SEED)
    chosen, used, counts = [], set(), {}
    for name in ("register_bridged_loose", "register_bridged_accepted", "t1r", "sole_trader", "no_abn"):
        pool = [e for e in strata[name] if e["edge_id"] not in used]
        take = pool if len(pool) <= STEP8_ASK[name] else rng.sample(pool, STEP8_ASK[name])
        counts[name] = (len(take), STEP8_ASK[name] if name != "t1r" else len(pool), len(pool))
        used |= {e["edge_id"] for e in take}
        chosen += [(name, e) for e in take]
    rng.shuffle(chosen)  # mixed order so the labeller is not primed by stratum

    def side(node_id: str) -> dict:
        n = nodes[node_id]
        if n["type"] == "register":
            r = bn_rows[n["source_record_id"]]
            return {"source": n["source_id"], "record_id": n["source_record_id"], "legal_name": r["BN_NAME"], "trading_names": "",
                    "abn": r["abn"] or "", "acn": "", "address": f"(register: registered in {r['BN_STATE_OF_REG'] or 'unknown state'})"}
        m = mentions[node_id]
        return {"source": m["source_id"], "record_id": m["source_record_id"], "legal_name": m["legal_name"] or "",
                "trading_names": " | ".join(m["trading_names"]), "abn": m["abn"] or "", "acn": m["acn"] or "", "address": addr(m)}

    STEP8_SHEET.parent.mkdir(parents=True, exist_ok=True)
    with STEP8_SHEET.open("w", newline="", encoding="utf-8-sig") as fs, STEP8_KEY.open("w", newline="", encoding="utf-8-sig") as fk:
        ws = csv.DictWriter(fs, fieldnames=STEP8_COLUMNS)
        wk = csv.DictWriter(fk, fieldnames=["check_id", "pair_id", "stratum", "tier", "band", "link_confidence"])
        ws.writeheader()
        wk.writeheader()
        for i, (name, e) in enumerate(chosen, 1):
            a, b = side(e["from"]), side(e["to"])
            ws.writerow({"check_id": i, **{f"{p}_{k}": v for p, d in (("a", a), ("b", b)) for k, v in d.items()}, "label": "", "notes": ""})
            ra, rb = ({"source_id": d["source"], "source_record_id": d["record_id"]} for d in (a, b))
            wk.writerow({"check_id": i, "pair_id": pair_id(ra, rb), "stratum": name, "tier": e["tier"], "band": e["band"],
                         "link_confidence": e["link_confidence"]})
    print(f"wrote {STEP8_SHEET} and {STEP8_KEY}: {len(chosen)} rows; per stratum (taken, asked, available):", counts)


if __name__ == "__main__":
    {"make": make, "score": score, "step8": make_step8}[sys.argv[1] if len(sys.argv) > 1 else "make"]()
