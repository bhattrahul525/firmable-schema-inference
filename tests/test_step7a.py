from collections import Counter

from src.part3_resolve.idf import Idf

# 1000 names: "australia" in 300 of them, "group" in 200, "zenith"/"acme" in 2 each
IDF = Idf(Counter({"australia": 300, "group": 200, "zenith": 2, "acme": 2, "plumbing": 40, "services": 150}), 1000)


def test_common_tokens_weigh_far_less_than_rare():
    assert IDF.idf("acme") > 3 * IDF.idf("australia")
    assert IDF.idf("acme") > 2 * IDF.idf("group")


def test_overlap_high_for_variants_low_for_generic_only():
    assert IDF.overlap("Acme Plumbing Pty Ltd", '"ACME PLUMBING"') == 1.0
    assert IDF.overlap("Acme Australia", "Zenith Australia") < 0.25
    assert IDF.overlap("Acme Plumbing Services", "Acme Plumbing") > 0.7
