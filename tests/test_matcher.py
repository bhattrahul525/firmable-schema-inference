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


class TestCanonicalKeyGuard(unittest.TestCase):
    """Found by the Part 3 hand check (check 15): ACT lists Stryker with J.J. Richards' ABN."""

    def link(self, tier, band, a, b, key, abn_equal, state_b=None):
        return {"link_id": f"{a}-{b}-{tier}", "tier": tier, "band": band, "canonical_entity_key": key,
                "evidence": {"name_a": a, "name_b": b, "abn_equal": abn_equal, "state_a": None, "state_b": state_b}}

    def test_name_only_link_does_not_borrow_a_conflicting_abn(self):
        from src.part3_resolve.keys import rekey_conflicting_name_links
        jjr = self.link("T1_abn_equal", "accepted", "J.J. RICHARDS & SONS PTY LTD", "J.J. Richards & Sons Pty Ltd", "abn:40000805425", True)
        stryker = self.link("T3_name_company", "loose", "STRYKER AUSTRALIA PTY LTD", "STRYKER AUSTRALIA PTY LTD",
                            "abn:40000805425", False, state_b="NSW")   # A carries J.J. Richards' ABN by mistake
        changes = rekey_conflicting_name_links([jjr, stryker])
        self.assertEqual(len(changes), 1)
        self.assertTrue(stryker["canonical_entity_key"].startswith("name:"))
        self.assertEqual(jjr["canonical_entity_key"], "abn:40000805425")   # identifier links are never re-keyed

    def test_name_only_link_that_agrees_keeps_its_abn_key(self):
        from src.part3_resolve.keys import rekey_conflicting_name_links
        t1 = self.link("T1_abn_equal", "accepted", "STRYKER AUSTRALIA PTY LTD", "Stryker Aust P/L", "abn:48002873850", True)
        t3 = self.link("T3_name_company", "loose", "STRYKER AUSTRALIA PTY LTD", "STRYKER AUSTRALIA PTY LTD", "abn:48002873850", False)
        self.assertEqual(rekey_conflicting_name_links([t1, t3]), [])
        self.assertEqual(t3["canonical_entity_key"], "abn:48002873850")

    def test_without_an_identifier_anchor_nothing_is_re_keyed(self):
        from src.part3_resolve.keys import rekey_conflicting_name_links
        t3 = self.link("T3_name_company", "loose", "Alpha Pty Ltd", "ALPHA PTY LTD", "abn:1", False)
        self.assertEqual(rekey_conflicting_name_links([t3]), [])  # we cannot tell the ABN is wrong

    def test_m1_2_scores_like_m1_0_but_m1_1_regresses_a_true_rename(self):
        f = pair_features(mention("CANTEL (AUSTRALIA) PTY LTD", abn="1"), mention("STERIS AUSTRALIA PTY LTD", abn="1"), "abn")
        self.assertEqual(SCORERS["m1.2"](f), SCORERS["m1.0"](f))          # accepted: a registered rename, a TRUE link
        self.assertEqual(band(SCORERS["m1.1"](f)[0]), "refused")          # the regression the labelled set caught
