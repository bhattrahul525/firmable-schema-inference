import json

import pytest

from src.part3_resolve import rescore
from src.part3_resolve.graph import edge_id, nominee_edges
from src.part3_resolve.labels import pair_id

A = {"source_id": "s1", "source_record_id": "r1"}
B = {"source_id": "s2", "source_record_id": "r2"}
PID = pair_id(A, B)


def change(frm, to):
    return {"a": A, "b": B, "from": ["m1", 0.9, frm], "to": ["m2", 0.5, to]}


def test_edge_id_ignores_version_and_endpoint_order():
    assert edge_id("same_as", "s1|a", "s2|b") == edge_id("same_as", "s2|b", "s1|a")
    assert edge_id("nominee_of", "p", "c") != edge_id("nominee_of", "c", "p")  # directed
    assert edge_id("same_as", "x", "y") != edge_id("nominee_of", "x", "y")


def test_pair_id_is_order_free():
    assert pair_id(A, B) == pair_id(B, A)


def test_gate_blocks_y_demotion_and_n_promotion():
    _, blocking, _ = rescore.gate([change("accepted", "loose")], {PID: "Y"}, {})
    assert [b["problem"] for b in blocking] == ["Y_demoted"]
    _, blocking, _ = rescore.gate([change("loose", "accepted")], {PID: "N"}, {})
    assert [b["problem"] for b in blocking] == ["N_promoted"]


def test_gate_allows_the_good_directions_and_unlabelled_pairs():
    assert rescore.gate([change("loose", "accepted")], {PID: "Y"}, {})[1] == []
    assert rescore.gate([change("accepted", "refused")], {}, {})[1] == []


def test_allow_list_reports_instead_of_blocking():
    _, blocking, accepted = rescore.gate([change("accepted", "refused")], {PID: "Y"}, {PID: {"reason": "rename"}})
    assert blocking == [] and accepted[0]["reason"] == "rename"


def test_old_links_without_m2_features_are_not_rescoreable(tmp_path, monkeypatch):
    link = {"source_a_record": A, "source_b_record": B, "link_confidence": 0.98, "tier": "T1_abn_equal", "band": "accepted",
            "matcher_version": "m1.2", "evidence": {"abn_equal": True, "name_a": "x", "name_b": "y"}, "canonical_entity_key": "abn:1"}
    (tmp_path / "links.jsonl").write_text(json.dumps(link) + "\n")
    (tmp_path / "unlinked_queue.jsonl").write_text("")
    monkeypatch.setattr(rescore, "OUT", tmp_path)
    monkeypatch.setattr("sys.argv", ["rescore", "--to", "m2.0"])
    rescore.main()
    assert json.loads((tmp_path / "rescore_to_m2.0.json").read_text())["not_rescoreable"] == 1


def m(name, abn, person, src="qbcc"):
    return {"source_id": src, "entity_ref": name, "source_record_id": name, "legal_name": name, "core": name.lower(),
            "abn": abn, "person_like": person}


def test_nominee_of_person_under_company_abn():
    edges = nominee_edges([m("Jane Smith", "1", True), m("Smith Builders", "1", False), m("Bob Jones", "2", True)])
    assert [(p["legal_name"], c["legal_name"]) for p, c, _ in edges] == [("Jane Smith", "Smith Builders")]
