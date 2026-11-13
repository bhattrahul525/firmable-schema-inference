from collections import Counter

import src.part3_resolve.features as F
from src.part3_resolve.idf import Idf
from src.part3_resolve.registers import BusinessNames

ABN1, ABN2 = "51824753556", "83072293880"  # checksum-valid


def row(name, abn="", status="Registered"):
    return {"BN_NAME": name, "BN_ABN": abn, "BN_STATUS": status}


def test_lookup_excludes_non_registered():
    bn = BusinessNames([row("Old Cafe", ABN1, "Cancelled"), row("New Cafe", ABN1)])
    assert bn.holder_of_name("Old Cafe")[0] == "none" and bn.names_of_abn(ABN1) == ["New Cafe"]


def test_two_holders_refused_same_holder_ok():
    two = BusinessNames([row("Acme Trading", ABN1), row("ACME TRADING", ABN2)])
    one = BusinessNames([row("Acme Trading", ABN1), row("Acme Trading", ABN1)])
    assert two.holder_of_name("acme trading")[0] == "refused" and one.holder_of_name("acme trading")[0] == "ok"


def test_blank_abn_rows_are_separate_holders():
    assert BusinessNames([row("Acme Trading"), row("Acme Trading")]).holder_of_name("Acme Trading")[0] == "refused"


def test_load_mentions_skips_reference(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "OBS_DIR", tmp_path)
    monkeypatch.setattr(F, "reference_sources", lambda: {"reg": {}})
    monkeypatch.setattr(F, "abn_unverified", lambda sid: False)
    (tmp_path / "src1.jsonl").write_text('{"entity_ref":"a","source_record_id":"1","field":"entity.legal_name","value":"X Pty Ltd"}\n')
    assert [m["source_id"] for m in F.load_mentions(["src1", "reg"])] == ["src1"]  # reg has no file: it is never opened


def test_state_postcode_derivation():
    d = F.derive_state_postcode
    assert d("26 Pollock Ave Kariong NSW 2250") == ("NSW", "2250")
    assert d("9 Mumford Place, Balcatta, 6024") == (None, "6024")  # no state invented from a postcode
    assert d("Shop 1234") == (None, None)


def test_generic_rule(monkeypatch):
    monkeypatch.setattr("src.part3_resolve.idf.GENERIC_MIN_WEIGHT", 8)  # the real 14.02 fits the real corpus, not this toy one
    idf = Idf(Counter({"australia": 300, "group": 200}), 1000)
    assert idf.is_generic("Australia Group Pty Ltd") and not idf.is_generic("Zenith Plumbing")
