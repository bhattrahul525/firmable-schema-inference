from collections import Counter

from src.part3_resolve.graph import abn_offenders
from src.part3_resolve.idf import Idf
from src.part3_resolve.registers import BusinessNames, register_links
from src.part3_resolve.score import score_m2_0

IDF = Idf(Counter({"custom": 2, "finance": 40, "group": 60}), 1000)
BN = BusinessNames([{"BN_NAME": "Custom Finance Group", "BN_ABN": "", "BN_STATUS": "Registered", "BN_STATE_NUM": "1", "BN_STATE_OF_REG": "VIC"}])


def mention(mid, abn):
    return {"mention_id": mid, "legal_name": "Custom Finance Group", "trading_names": [], "abn": abn, "person_like": False,
            "abn_unverified": False, "state": None}


def tier_reasons(mentions, monkeypatch):
    monkeypatch.setattr("src.part3_resolve.idf.GENERIC_MIN_WEIGHT", 1)  # toy corpus
    return [score_m2_0(c["evidence"])[2] for c in register_links(mentions, BN, IDF)]


def test_blank_abn_register_record_cannot_bridge_different_abns(monkeypatch):
    assert tier_reasons([mention("a", "51824753556"), mention("b", "83072293880")], monkeypatch) == ["register_bridge_different_abns"] * 2
    assert tier_reasons([mention("a", "51824753556"), mention("b", None)], monkeypatch) == [None, None]  # absent ABN does not differ
    assert tier_reasons([mention("a", "51824753556"), mention("b", "51824753556")], monkeypatch) == [None, None]


def test_abn_check_reports_loose_edge_offenders():
    nodes = {"a": {"name": "A", "abn": "1"}, "b": {"name": "B", "abn": "2"}, "r": {"name": "R", "abn": None}}
    edges = [{"type": "same_as", "from": "a", "to": "r", "band": "loose"}, {"type": "same_as", "from": "b", "to": "r", "band": "loose"}]
    (o,) = abn_offenders(edges, nodes)
    assert o["abns"] == ["1", "2"]
