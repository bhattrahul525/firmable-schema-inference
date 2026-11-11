"""Part 4: one company profile per linked entity, merged from every source record that describes it.

  python -m src.part4_profiles.build

A profile is NOT a reconciled fact table row; it is a transparent merge. For every field it shows the
winning value, WHY it won, who else said something different, and which source record each value came
from. Where nothing separates two values, we do not pick: both go under `unresolved`.

Confidence stays in separate numbers per field (never blended into one score):
  field_confidence   did we map/parse this value correctly      (from the Part 2 config + validation)
  source_reliability how far we trust this publisher for this kind of claim (Part 2, model judgement)
  agreement          how many of the sources that stated the field agree on it
  link_confidence    only on the links that attached a record to the entity (member_records / attached_by)

Winner rule for a scalar field, applied to groups of values that agree after normalisation
(so 'Pty Ltd' vs 'P/L' and capitals are agreement, not conflict). Each SOURCE counts once, however many rows
it repeats the value on:
  1. more distinct sources agree  ->  wins
  2. higher source_reliability (difference >= 0.05)  ->  wins
  3. otherwise UNRESOLVED: both values are shown, none is chosen.
There is deliberately NO "most recent wins" step: our observed_at is a file's last-modified date, not the date the
claim was made (a live register updated in 2026 can hold names from years ago), so recency would be a confident-looking
guess. It is still shown in provenance.
Claims with field_confidence < 0.6 are used only if nothing better exists.
The address (full, locality, state, postcode) is resolved as ONE unit from ONE record, so a profile never
mixes a street from one source with a postcode from another.
"""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.part3_resolve.features import name_core

BUILDER_VERSION = "p1.0"
OBS_DIR = Path("outputs/observations")
LINKS = Path("outputs/part3/links.jsonl")
HANDCHECK = Path("handcheck/part3_link_check.csv")
OUT = Path("outputs/profiles")
SEED = 20261112
N_PROFILES = 50
LOW_TRUST = 0.6          # claims below this field_confidence lose to any claim at or above it
RELIABILITY_GAP = 0.05   # smaller differences in source_reliability are treated as equal
IDENTITY_FIELDS = {"entity.legal_name", "entity.abn", "entity.acn"}
SCALAR_FIELDS = ["entity.legal_name", "entity.abn", "entity.acn", "entity.entity_type", "entity.status",
                 "entity.website", "entity.industry_code", "entity.date_registered"]
ADDRESS_FIELDS = ["address.full", "address.locality", "address.state", "address.postcode", "address.country"]


# ---- normalisation: what counts as "the same value" ---------------------------------------------------

def norm_value(field: str, v) -> str:
    s = str(v).strip()
    if field in ("entity.abn", "entity.acn", "address.postcode"):
        return re.sub(r"\D", "", s)
    if field == "entity.legal_name":
        return name_core(re.sub(r"\bp/l\b", "pty ltd", s, flags=re.I))  # 'P/L' is 'Pty Ltd'
    return re.sub(r"[^a-z0-9]", "", s.lower())


def usable_address_value(field: str, v) -> bool:
    """Drops values that cannot be an address part (QLD Health has 15 addresses that are just '0')."""
    s = str(v).strip()
    if field == "address.full":
        return bool(re.search(r"[A-Za-z]", s)) and len(s) >= 5
    if field == "address.postcode":
        return bool(re.fullmatch(r"\d{4}", s))
    return bool(s)


# ---- decision rule ------------------------------------------------------------------------------------

def rank_groups(groups: list[dict]) -> tuple[list[dict], str | None, str]:
    """groups: [{norm, sources:set, reliability, latest}]. Returns (ordered groups, winner decided_by or None
    if unresolved, explanation). One group -> trivially resolved."""
    ordered = sorted(groups, key=lambda g: (-len(g["sources"]), -round(g["reliability"] / RELIABILITY_GAP), g["norm"]))
    if len(ordered) == 1:
        g = ordered[0]
        return ordered, ("all_sources_agree" if len(g["sources"]) > 1 else "single_source"), "only one distinct value"
    a, b = ordered[0], ordered[1]
    if len(a["sources"]) != len(b["sources"]):
        return ordered, "more_sources_agree", f"{len(a['sources'])} sources vs {len(b['sources'])}"
    if abs(a["reliability"] - b["reliability"]) >= RELIABILITY_GAP:
        return ordered, "higher_source_reliability", f"{a['reliability']} vs {b['reliability']}"
    return ordered, None, "same number of sources and source reliability within 0.05: nothing separates the values"


def prov(c: dict) -> dict:
    return {k: c[k] for k in ("source_id", "source_record_id", "entity_ref", "source_field", "observed_at",
                              "extractor_version", "derivation_level", "raw_value", "attached_by")}


def make_groups(field: str, claims: list[dict]) -> list[dict]:
    by: dict[str, list[dict]] = defaultdict(list)
    for c in claims:
        by[norm_value(field, c["value"])].append(c)
    out = []
    for n, cs in by.items():
        rep = sorted(cs, key=lambda c: (-c["source_reliability"], -c["field_confidence"], c["source_id"], str(c["value"])))[0]
        out.append({"norm": n, "claims": cs, "rep": rep, "sources": {c["source_id"] for c in cs},
                    "reliability": max(c["source_reliability"] for c in cs),
                    "latest": max(c["observed_at"] for c in cs)})
    return out


def resolve_scalar(field: str, claims: list[dict]) -> tuple[dict | None, dict | None]:
    """Returns (resolved field dict, None) or (None, unresolved dict)."""
    strong = [c for c in claims if c["field_confidence"] >= LOW_TRUST]
    use = strong or claims
    groups = rank_groups(make_groups(field, use))
    ordered, decided, why = groups
    all_groups = make_groups(field, claims)
    stating = len({c["source_id"] for c in claims})
    if decided is None:
        return None, {"field": field, "why_unresolved": why, "candidates": [
            {"value": g["rep"]["value"], "variants": sorted({str(c["value"]) for c in g["claims"]} - {str(g['rep']['value'])}),
             "sources": sorted(g["sources"]), "source_reliability": g["reliability"],
             "provenance": [prov(c) for c in g["claims"]]} for g in ordered[:3]]}
    win = ordered[0]
    rep = win["rep"]
    res = {
        "value": rep["value"],
        "variants": sorted({str(c["value"]) for c in win["claims"]} - {str(rep["value"])}),
        "confidence": {"field_confidence": rep["field_confidence"], "source_reliability": rep["source_reliability"],
                       "agreement": {"sources_agreeing": len(win["sources"]), "sources_stating": stating}},
        "decided_by": decided, "decided_detail": why,
        "provenance": [prov(c) for c in win["claims"]],
    }
    losers = [g for g in all_groups if g["norm"] != win["norm"]]
    if losers:
        res["conflict"] = {"losing_values": [
            {"value": g["rep"]["value"], "sources": sorted(g["sources"]), "source_reliability": g["reliability"],
             "field_confidence": g["rep"]["field_confidence"],
             "why_lost": ("low_trust_claim_ignored" if g["rep"]["field_confidence"] < LOW_TRUST and strong else decided),
             "provenance": [prov(c) for c in g["claims"]]} for g in losers]}
    return res, None


def resolve_address(claims: list[dict]) -> tuple[dict, dict | None]:
    """One address, from one record. Returns ({field: resolved}, unresolved or None)."""
    recs: dict[tuple, dict] = defaultdict(dict)
    for c in claims:
        if usable_address_value(c["field"], c["value"]):
            recs[(c["source_id"], c["entity_ref"])][c["field"]] = c
    cands = []
    for key, parts in recs.items():
        sig = norm_value("address.full", parts["address.full"]["value"]) if "address.full" in parts else \
            "|".join(norm_value(f, parts[f]["value"]) if f in parts else "" for f in ("address.state", "address.postcode", "address.locality"))
        cands.append({"sig": sig, "parts": parts, "source": key[0],
                      "reliability": min(p["source_reliability"] for p in parts.values()),
                      "fc": min(p["field_confidence"] for p in parts.values()),
                      "latest": max(p["observed_at"] for p in parts.values())})
    if not cands:
        return {}, None
    strong = [c for c in cands if c["fc"] >= LOW_TRUST] or cands
    by: dict[str, list[dict]] = defaultdict(list)
    for c in strong:
        by[c["sig"]].append(c)
    groups = [{"norm": s, "cands": cs, "sources": {c["source"] for c in cs},
               "reliability": max(c["reliability"] for c in cs), "latest": max(c["latest"] for c in cs),
               "rep": sorted(cs, key=lambda c: (-c["reliability"], -c["fc"], c["source"]))[0]} for s, cs in by.items()]
    ordered, decided, why = rank_groups(groups)
    if decided is None:
        return {}, {"field": "address", "why_unresolved": why, "candidates": [
            {"fields": {f: p["value"] for f, p in g["rep"]["parts"].items()}, "sources": sorted(g["sources"]),
             "source_reliability": g["reliability"],
             "provenance": {f: prov(p) for f, p in g["rep"]["parts"].items()}} for g in ordered[:3]]}
    win = ordered[0]["rep"]
    stating = len({c["source"] for c in cands})
    fields = {}
    for f, p in win["parts"].items():
        entry = {"value": p["value"],
                 "confidence": {"field_confidence": p["field_confidence"], "source_reliability": p["source_reliability"],
                                "agreement": {"sources_agreeing": len(ordered[0]["sources"]), "sources_stating": stating}},
                 "decided_by": decided, "decided_detail": why, "provenance": [prov(p)]}
        other = [(c["source"], c["parts"][f]) for c in cands if c["sig"] != ordered[0]["norm"] and f in c["parts"]
                 and norm_value(f, c["parts"][f]["value"]) != norm_value(f, p["value"])]
        if other:
            entry["conflict"] = {"losing_values": [
                {"value": q["value"], "sources": [s], "source_reliability": q["source_reliability"],
                 "field_confidence": q["field_confidence"], "why_lost": decided, "provenance": [prov(q)]} for s, q in other]}
        fields[f] = entry
    return fields, None


# ---- assembling profiles -----------------------------------------------------------------------------

def load_observations() -> dict[str, list[dict]]:
    by_m: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(OBS_DIR.glob("*.jsonl")):
        for line in f.open():
            o = json.loads(line)
            if o["field"] == "entity.entity_type" and o["value"] == "unknown":
                continue  # 'unknown' is the absence of a claim, not a claim
            by_m[f"{o['source_id']}|{o['entity_ref']}"].append(o)
    return by_m


def mid(r: dict) -> str:
    return f"{r['source_id']}|{r['entity_ref']}"


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


def define_entities(links: list[dict]) -> tuple[list[dict], dict]:
    """Entity groups from Part 3 links. Accepted links define the main entities. Loose links define extra,
    lower-trust entities only for groups that touch no accepted entity and point to at most one canonical key
    (a loose group whose links disagree about the entity is ambiguous: skipped and counted)."""
    acc, loose = DSU(), DSU()
    for l in links:
        (acc if l["band"] == "accepted" else loose).union(mid(l["source_a_record"]), mid(l["source_b_record"]))
    groups: dict[tuple, dict] = {}
    for l in links:
        d, tag = (acc, "accepted") if l["band"] == "accepted" else (loose, "loose_only")
        root = d.find(mid(l["source_a_record"]))
        g = groups.setdefault((tag, root), {"trust": tag, "members": set(), "links": [], "keys": set()})
        g["members"] |= {mid(l["source_a_record"]), mid(l["source_b_record"])}
        g["links"].append(l)
        g["keys"].add(l["canonical_entity_key"])
    accepted_members = set().union(*[g["members"] for (t, _), g in groups.items() if t == "accepted"])
    stats = {"loose_groups": 0, "loose_skipped_touch_accepted": 0, "loose_skipped_ambiguous": 0}
    entities = []
    for (tag, _), g in sorted(groups.items(), key=lambda kv: sorted(kv[1]["keys"])):
        if tag == "loose_only":
            stats["loose_groups"] += 1
            if g["members"] & accepted_members:
                stats["loose_skipped_touch_accepted"] += 1
                continue
            if len(g["keys"]) > 1:
                stats["loose_skipped_ambiguous"] += 1
                continue
        g["key"] = sorted(g["keys"])[0]
        entities.append(g)
    return entities, stats


def hand_labels() -> dict[tuple, str]:
    if not HANDCHECK.exists():
        return {}
    out = {}
    for r in csv.DictReader(HANDCHECK.open(encoding="utf-8-sig")):
        out[((r["a_source"], r["a_record_id"]), (r["b_source"], r["b_record_id"]))] = r["label"].strip().upper()[:1]
    return out


def build_profile(ent: dict, obs_by_m: dict, labels: dict, drop_source: str | None = None) -> dict:
    """With drop_source set, rebuilds the profile as if that source did not exist (deletion test). What remains
    may be a single-source profile: the records are still there, but nothing corroborates them any more."""
    members = sorted(m for m in ent["members"] if m.split("|")[0] != drop_source)
    attach: dict[str, dict] = {}
    for l in ent["links"]:
        for rec in (l["source_a_record"], l["source_b_record"]):
            if rec["source_id"] == drop_source:
                continue
            best = attach.get(mid(rec))
            if best is None or l["link_confidence"] > best["link_confidence"]:
                attach[mid(rec)] = {"link_id": l["link_id"], "link_confidence": l["link_confidence"], "tier": l["tier"], "band": l["band"]}
    claims: dict[str, list[dict]] = defaultdict(list)
    for m in members:
        for o in obs_by_m[m]:
            claims[o["field"]].append({**o, "attached_by": attach.get(m)})
    fields, unresolved = {}, {}
    for f in SCALAR_FIELDS:
        if f in claims:
            res, un = resolve_scalar(f, claims[f])
            if res:
                fields[f] = res
            else:
                unresolved[f] = un
    addr_claims = [c for f in ADDRESS_FIELDS for c in claims.get(f, [])]
    addr_fields, addr_un = resolve_address(addr_claims)
    fields.update(addr_fields)
    if addr_un:
        unresolved["address"] = addr_un
    trading = []
    for g in make_groups("entity.trading_name", claims.get("entity.trading_name", [])):
        trading.append({"value": g["rep"]["value"], "variants": sorted({str(c["value"]) for c in g["claims"]} - {str(g["rep"]["value"])}),
                        "sources": sorted(g["sources"]), "provenance": [prov(c) for c in g["claims"]]})
    keyset = {(m.split("|")[0], obs_by_m[m][0]["source_record_id"]) for m in members}
    checked = Counter(lab for (a, b), lab in labels.items() if a in keyset and b in keyset)
    prof = {
        "canonical_entity_key": ent["key"], "trust": ent["trust"],
        "sources": sorted({m.split("|")[0] for m in members}),
        "member_records": [{"source_id": m.split("|")[0], "source_record_id": obs_by_m[m][0]["source_record_id"],
                            "entity_ref": obs_by_m[m][0]["entity_ref"], "attached_by": attach.get(m)} for m in members],
        "fields": dict(sorted(fields.items())),
    }
    if trading:
        prof["trading_names"] = trading
    if unresolved:
        prof["unresolved"] = unresolved
    if checked:
        prof["hand_checked_links"] = dict(checked)
    prof["built_with"] = {"builder_version": BUILDER_VERSION, "matcher_versions": sorted({l["matcher_version"] for l in ent["links"]})}
    return prof


# ---- deletion test -----------------------------------------------------------------------------------

def compare(base: dict, new: dict) -> dict:
    """How one profile changes when a source is deleted. Two separate questions:
       corroboration_lost: did it stop being supported by 2+ sources?   (trust impact)
       content: did any value change or disappear?                      (data impact)"""
    changed = [f for f, v in base["fields"].items() if f in new["fields"] and norm_value(f, v["value"]) != norm_value(f, new["fields"][f]["value"])]
    lost = [f for f in base["fields"] if f not in new["fields"]]
    gained = [f for f in new["fields"] if f not in base["fields"]]
    if set(changed + lost) & IDENTITY_FIELDS:
        content = "identity_changed_or_lost"      # name / ABN / ACN: the worst case
    elif changed or lost:
        content = "other_field_changed_or_lost"   # e.g. address, entity type
    elif gained or set(base.get("unresolved", {})) != set(new.get("unresolved", {})):
        content = "conflict_resolution_changed"   # nothing lost; an unresolved item became resolved or vice versa
    else:
        content = "unchanged"
    return {"corroboration_lost": len(new["sources"]) < 2 <= len(base["sources"]), "content": content,
            "changed": changed, "lost": lost}


def deletion_test(entities, obs_by_m, labels, base_profiles, sources) -> dict:
    out = {}
    for s in sources:
        res = [compare(base, build_profile(ent, obs_by_m, labels, drop_source=s)) for ent, base in zip(entities, base_profiles)]
        containing = [r for r, p in zip(res, base_profiles) if s in p["sources"]]
        out[s] = {
            "profiles_containing_source": len(containing),
            "corroboration_lost": sum(r["corroboration_lost"] for r in res),
            "content": dict(Counter(r["content"] for r in res)),
            "fields_lost": dict(Counter(f for r in res for f in r["lost"])),
            "fields_changed": dict(Counter(f for r in res for f in r["changed"])),
        }
    return out


# ---- checks, main ------------------------------------------------------------------------------------

def check_profiles(profiles: list[dict]) -> list[str]:
    problems = []
    for p in profiles:
        k = p["canonical_entity_key"]
        for f, v in p["fields"].items():
            if v["value"] in (None, "", "0") or not v["provenance"]:
                problems.append(f"{k} {f}: blank value or no provenance")
            if not {"field_confidence", "source_reliability", "agreement"} <= set(v["confidence"]):
                problems.append(f"{k} {f}: confidence block incomplete")
            if "conflict" in v and not all(x.get("why_lost") and x.get("provenance") for x in v["conflict"]["losing_values"]):
                problems.append(f"{k} {f}: conflict without reason or provenance")
        for f, u in p.get("unresolved", {}).items():
            if len(u["candidates"]) < 2:
                problems.append(f"{k} {f}: unresolved with fewer than two candidates")
    return problems


def main() -> None:
    links = [json.loads(line) for line in LINKS.open()]
    entities, stats = define_entities(links)
    accepted = [e for e in entities if e["trust"] == "accepted"]
    loose = [e for e in entities if e["trust"] == "loose_only"]
    pick_loose = random.Random(SEED).sample(loose, min(N_PROFILES - len(accepted), len(loose))) if len(accepted) < N_PROFILES else []
    chosen = sorted(accepted + pick_loose, key=lambda e: (e["trust"], e["key"]))[:N_PROFILES]
    obs_by_m, labels = load_observations(), hand_labels()
    profiles = [build_profile(e, obs_by_m, labels) for e in chosen]
    problems = check_profiles(profiles)
    assert not problems, problems

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "profiles.jsonl").open("w") as f:
        for p in profiles:
            f.write(json.dumps(p, default=str) + "\n")
    sources = sorted({s for p in profiles for s in p["sources"]})
    summary = {
        "builder_version": BUILDER_VERSION, "profiles": len(profiles),
        "by_trust": dict(Counter(p["trust"] for p in profiles)),
        "entity_frame": {"accepted": len(accepted), "loose_only_available": len(loose), "loose_only_used": len(pick_loose), **stats},
        "fields_filled": dict(Counter(f for p in profiles for f in p["fields"])),
        "profiles_with_trading_names": sum(1 for p in profiles if p.get("trading_names")),
        "profiles_with_conflicts": sum(1 for p in profiles if any("conflict" in v for v in p["fields"].values())),
        "conflicts_by_field": dict(Counter(f for p in profiles for f, v in p["fields"].items() if "conflict" in v)),
        "profiles_with_unresolved": sum(1 for p in profiles if p.get("unresolved")),
        "unresolved_by_field": dict(Counter(f for p in profiles for f in p.get("unresolved", {}))),
        "decided_by": dict(Counter(v["decided_by"] for p in profiles for v in p["fields"].values())),
        "deletion_test": deletion_test(chosen, obs_by_m, labels, profiles, sources),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
