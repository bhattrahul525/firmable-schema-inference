"""Matcher scoring and re-scoring, on hand-made feature dicts."""

import unittest

from src.part3_resolve.features import pair_features, name_core, person_like
from src.part3_resolve.score import SCORERS, band


def mention(name, abn=None, acn=None, postcode=None, state=None, etype="unknown", trading=()):
    core = name_core(name)
    return {"legal_name": name, "core": core, "abn": abn, "acn": acn, "postcode": postcode, "state": state,
            "entity_type": etype, "trading_names": list(trading), "trading_cores": [name_core(t) for t in trading],
            "person_like": person_like(name, etype)}


class TestMatcher(unittest.TestCase):
    def f(self, a, b, how="abn"):
        return pair_features(a, b, how)

    def test_equal_abn_and_agreeing_names_is_accepted(self):
        f = self.f(mention("Westlab Pty Ltd", abn="71606662113"), mention("WESTLAB PTY LTD", abn="71606662113"))
        conf, tier, why = SCORERS["m1.0"](f)
        self.assertEqual((band(conf), tier, why), ("accepted", "T1_abn_equal", None))

    def test_equal_abn_but_person_vs_company_is_refused(self):
        # QBCC lists individuals under their company's ABN: ABN alone must not link them
        f = self.f(mention("Gary Andrew Scott", abn="11"), mention("TRANE THERMO KING PTY LTD", abn="11"))
        conf, _, why = SCORERS["m1.0"](f)
        self.assertEqual((band(conf), why), ("refused", "identifier_match_but_names_conflict"))

    def test_name_only_never_links_two_different_abns(self):
        f = self.f(mention("Stryker Australia Pty Ltd", abn="1"), mention("STRYKER AUSTRALIA PTY LTD", abn="2"), "name")
        self.assertEqual(SCORERS["m1.0"](f)[2], "name_match_but_different_abns")

    def test_person_names_are_not_linked_on_name_alone(self):
        f = self.f(mention("Michael William Argus", postcode="4000"), mention("MICHAEL WILLIAM ARGUS", postcode="4000"), "name")
        self.assertEqual(SCORERS["m1.0"](f)[2], "person_name_not_linked_by_name")

    def test_name_only_tiers(self):
        co = lambda **k: mention("Acme Constructions Pty Ltd", etype="company", **k)
        self.assertEqual(SCORERS["m1.0"](self.f(co(postcode="4000"), co(postcode="4000"), "name"))[:2], (0.85, "T3_name_postcode"))
        self.assertEqual(band(SCORERS["m1.0"](self.f(co(), co(), "name"))[0]), "loose")        # both companies, no address
        self.assertEqual(SCORERS["m1.0"](self.f(co(postcode="4000"), co(postcode="3000"), "name"))[2],
                         "name_match_but_locations_differ")

    def test_rescore_demotes_names_that_share_only_generic_words(self):
        f = self.f(mention("CANTEL (AUSTRALIA) PTY LTD", abn="1"), mention("STERIS AUSTRALIA PTY LTD", abn="1"))
        self.assertEqual(band(SCORERS["m1.0"](f)[0]), "accepted")   # old matcher: passes (shares 'australia')
        conf, _, why = SCORERS["m1.1"](f)                           # new matcher, same stored features
        self.assertEqual((band(conf), why), ("refused", "identifier_match_but_only_generic_words_shared"))

    def test_rescore_leaves_genuine_matches_alone(self):
        f = self.f(mention("Hartwigs", abn="1"), mention("HARTWIGS TRUCKS PTY LTD", abn="1"))
        self.assertEqual(SCORERS["m1.0"](f), SCORERS["m1.1"](f))


if __name__ == "__main__":
    unittest.main()
