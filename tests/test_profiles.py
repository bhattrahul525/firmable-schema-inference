"""The Part 4 decision rules, on tiny synthetic claims."""

import unittest

from src.part4_profiles.build import resolve_address, resolve_scalar


def claim(field, value, source, rel=0.6, fc=0.9, ref="1#main:0"):
    return {"field": field, "value": value, "source_id": source, "source_record_id": ref.split("#")[0], "entity_ref": ref,
            "source_field": "x", "observed_at": "2026-01-01T00:00:00", "extractor_version": "v", "derivation_level": "L0",
            "raw_value": value, "attached_by": None, "source_reliability": rel, "field_confidence": fc}


class TestScalar(unittest.TestCase):
    def test_spelling_variants_are_agreement_not_conflict(self):
        res, un = resolve_scalar("entity.legal_name", [claim("entity.legal_name", "ACME PTY LTD", "a"),
                                                       claim("entity.legal_name", "Acme P/L", "b")])
        self.assertIsNone(un)
        self.assertNotIn("conflict", res)
        self.assertEqual(res["confidence"]["agreement"], {"sources_agreeing": 2, "sources_stating": 2})
        self.assertEqual(res["decided_by"], "all_sources_agree")

    def test_nothing_separates_two_values_so_no_winner(self):
        res, un = resolve_scalar("entity.legal_name", [claim("entity.legal_name", "Tyco Australia Pty Ltd", "a"),
                                                       claim("entity.legal_name", "Wormald Australia Pty Ltd", "b")])
        self.assertIsNone(res)
        self.assertEqual(len(un["candidates"]), 2)

    def test_more_sources_agreeing_wins_and_loser_is_shown(self):
        cs = [claim("entity.abn", "11", "a"), claim("entity.abn", "11", "b"), claim("entity.abn", "22", "c", rel=0.9)]
        res, _ = resolve_scalar("entity.abn", cs)
        self.assertEqual(res["value"], "11")
        self.assertEqual(res["decided_by"], "more_sources_agree")
        self.assertEqual(res["conflict"]["losing_values"][0]["value"], "22")

    def test_higher_reliability_wins_a_one_vs_one(self):
        res, _ = resolve_scalar("entity.legal_name", [claim("entity.legal_name", "Alpha Pty Ltd", "a", rel=0.9),
                                                      claim("entity.legal_name", "Beta Pty Ltd", "b", rel=0.6)])
        self.assertEqual((res["value"], res["decided_by"]), ("Alpha Pty Ltd", "higher_source_reliability"))

    def test_repeated_rows_from_one_source_count_once(self):
        cs = [claim("entity.abn", "11", "a", ref=f"{i}#main:0") for i in range(5)] + [claim("entity.abn", "22", "b"), claim("entity.abn", "22", "c")]
        res, _ = resolve_scalar("entity.abn", cs)
        self.assertEqual(res["value"], "22")  # 2 sources beat 1 source that repeats itself 5 times

    def test_low_trust_claim_loses_to_a_trusted_one(self):
        res, _ = resolve_scalar("entity.abn", [claim("entity.abn", "11", "a", fc=0.3), claim("entity.abn", "22", "b", fc=0.9)])
        self.assertEqual(res["value"], "22")
        self.assertEqual(res["conflict"]["losing_values"][0]["why_lost"], "low_trust_claim_ignored")


class TestAddress(unittest.TestCase):
    def test_junk_address_is_discarded_and_address_comes_from_one_record(self):
        cs = [claim("address.full", "0", "qld", ref="1#main:0"), claim("address.postcode", "4000", "qld", ref="1#main:0"),
              claim("address.full", "1 Main St, Brisbane QLD 4000", "asic", rel=0.9, ref="2#main:0"),
              claim("address.postcode", "4000", "asic", rel=0.9, ref="2#main:0")]
        fields, un = resolve_address(cs)
        self.assertIsNone(un)
        self.assertEqual(fields["address.full"]["value"], "1 Main St, Brisbane QLD 4000")
        self.assertEqual({p["source_id"] for f in fields.values() for p in f["provenance"]}, {"asic"})

    def test_two_different_equal_addresses_are_unresolved(self):
        cs = [claim("address.full", "1 A St, Clayton VIC 3168", "vic", ref="1#main:0"),
              claim("address.full", "9 B St, Geelong VIC 3220", "vic", ref="2#main:0")]
        fields, un = resolve_address(cs)
        self.assertEqual(fields, {})
        self.assertEqual(len(un["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
