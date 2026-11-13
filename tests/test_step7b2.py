from collections import Counter

from src.part3_resolve.idf import Idf
from src.part3_resolve.registers import BusinessNames, bn_record_id, register_links
from src.part3_resolve.score import band, score_m2_0

BASE = dict(abn_equal=False, abn_differ=False, acn_equal=False, acn_is_abn_suffix=False, name_overlap=0.0,
            name_exact=False, shared_trading_name=False, generic_name=False, person_like=False, both_company=False,
            postcode_equal=False, postcode_differ=False, state_equal=False, state_differ=False,
            bn_confirms_a=False, bn_confirms_b=False, abn_unverified=False)


def s(**kw):
    return score_m2_0({**BASE, **kw})


def test_identifier_tiers():
    assert s(abn_equal=True, name_overlap=0.9)[:2] == (0.98, "T1_abn_equal")
    assert s(acn_is_abn_suffix=True, name_overlap=0.9)[:2] == (0.88, "T2_acn_in_abn")
    assert s(abn_equal=True, name_overlap=0.1)[2] == "identifier_match_but_names_conflict"


def test_t1r_needs_a_register_name():
    assert s(abn_equal=True, name_overlap=0.1, bn_confirms_a=True)[:2] == (0.95, "T1r_abn_equal_bn_name")


def test_name_tiers_are_loose_and_capped_below_accept():
    for kw, tier in ((dict(postcode_equal=True), "T4_name_postcode"), (dict(state_equal=True), "T4_name_state"),
                     (dict(both_company=True), "T4_name_company")):
        conf, t, _ = s(name_exact=True, **kw)
        assert t == tier and band(conf) == "loose" and conf < 0.80


def test_refusals():
    assert s(name_exact=True, generic_name=True)[2] == "generic_name"
    assert s(name_exact=True, person_like=True, postcode_equal=True)[2] == "person_name_not_linked_by_name"
    assert s(name_exact=True, abn_differ=True, postcode_equal=True)[2] == "name_match_but_different_abns"


def test_unverified_abn_caps_at_079():
    conf, _, why = s(abn_equal=True, name_overlap=0.9, abn_unverified=True)
    assert conf == 0.79 and band(conf) == "loose" and why == "abn_evidence_unverified_cap"


def mention(name, abn=None):
    return {"mention_id": "m", "legal_name": name, "trading_names": [], "abn": abn, "person_like": False,
            "abn_unverified": False, "state": None}


def reg(name, abn, num, state="NSW"):
    return {"BN_NAME": name, "BN_ABN": abn, "BN_STATUS": "Registered", "BN_STATE_NUM": num, "BN_STATE_OF_REG": state}


ABN1, ABN2 = "51824753556", "83072293880"
IDF = Idf(Counter({"acme": 2, "plumbing": 40}), 1000)


def test_register_abn_link_is_t1_and_name_bridge_is_t3(monkeypatch):
    monkeypatch.setattr("src.part3_resolve.idf.GENERIC_MIN_WEIGHT", 5)  # toy corpus
    bn = BusinessNames([reg("Acme Plumbing", ABN1, "BN1")])
    (c,) = register_links([mention("ACME PLUMBING PTY LTD", ABN1)], bn, IDF)
    assert score_m2_0(c["evidence"])[:2] == (0.98, "T1_register_abn")
    (c,) = register_links([mention("ACME PLUMBING PTY LTD")], bn, IDF)
    assert score_m2_0(c["evidence"])[:2] == (0.65, "T3_register_name")


def test_register_name_with_two_holders_is_refused_and_ids_are_stable():
    bn = BusinessNames([reg("Acme Plumbing", ABN1, "BN1"), reg("Acme Plumbing", ABN2, "BN2", "VIC")])
    (c,) = register_links([mention("Acme Plumbing")], bn, IDF)
    assert score_m2_0(c["evidence"])[2] == "name_matches_more_than_one_holder"
    assert bn_record_id(reg("x", ABN1, "BN2", "VIC")) == "bn:VIC:BN2"
