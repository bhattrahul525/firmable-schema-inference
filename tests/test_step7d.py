from src.part4_profiles.profiles import build_profile, choose


def node(sid, rid, typ="mention", abn="51824753556"):
    return {"node_id": f"{sid}|{rid}", "type": typ, "source_id": sid, "source_record_id": rid, "abn": abn, "name": rid}


def edge(a, b, band="accepted"):
    return {"edge_id": a + b, "tier": "T1", "band": band, "link_confidence": 0.98, "human_label": None, "matcher_version": "m2.0"}


def obs(n, value, fc=0.9, rel=0.8):
    return {"field": "entity.legal_name", "value": value, "raw_value": value, "source_id": n["source_id"],
            "source_record_id": n["source_record_id"], "observed_at": "2026-01-01", "field_confidence": fc,
            "source_reliability": rel, "derivation_level": "L0"}


A, B, R = node("s1", "a"), node("s2", "b"), node("asic_business_names", "bn:NSW:1", "register")


def build(members, edges, claims=None):
    return build_profile(members, edges, {n["node_id"]: [obs(n, "ACME")] for n in members} if claims is None else claims, {})


def test_type_labelling():
    assert build([A, B], [edge("a", "b")])["type"] == "cross_source"
    assert build([A, R], [edge("a", "r")])["type"] == "single_source_register_confirmed"


def test_register_never_counts_as_a_second_source():
    p = build([A, R], [edge("a", "r")])
    assert p["sources"] == ["s1"] and p["register_counts_as_source"] is False
    assert build([R, node("asic_business_names", "bn:NSW:2", "register")], [edge("r", "r2")]) is None  # no mention at all


def test_person_only_component_gets_no_profile_but_sole_trader_does():
    assert build([node("s1", "p", "person", None), node("s2", "q", "person", None)], [edge("p", "q")]) is None
    assert build([node("s1", "p", "mention"), node("s2", "q", "mention")], [edge("p", "q")]) is not None  # own ABN


def test_one_loose_link_makes_the_profile_loose():
    C = node("s3", "c")
    assert build([A, B, C], [edge("a", "b"), edge("b", "c", "loose")])["trust"] == "loose"
    assert build([A, B, C], [edge("a", "b"), edge("b", "c")])["trust"] == "accepted"


def test_field_choice_highest_score_or_tie_marks_none():
    groups = [{"value": "X", "score": 0.72}, {"value": "Y", "score": 0.5}]
    g, decided = choose(groups)
    assert [x["chosen"] for x in g] == [True, False] and decided == "highest_confidence_x_reliability"
    g, decided = choose([{"value": "X", "score": 0.6}, {"value": "Y", "score": 0.6}])
    assert not any(x["chosen"] for x in g) and decided == "tie_none_chosen"
