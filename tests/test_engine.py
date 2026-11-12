"""Engine tests on tiny synthetic data. The configs below are TEST FIXTURES, not source
configs (real configs in configs/ are written only by the agent)."""

import unittest

from src.engine.config import normalise_transforms, structural_errors, load_ontology
from src.engine.extract import run_rows, select_rows
from src.engine.transforms import Reject, Skip, abn, acn, entity_type_from_suffix, parse_date, postcode, state_code

META = {"licence": "CC-BY", "licence_flag": False, "resource_last_modified": "2026-01-01T00:00:00"}


def field(source, canonical, transforms, group="main", conf=0.9):
    return {"source": source, "canonical": canonical, "transforms": normalise_transforms(transforms),
            "group": group, "mapping_confidence": conf}


def cfg(fields, **kw):
    base = {"source_id": "t", "config_version": 1, "reader": {"format": "csv"},
            "record_id": {"from": ["id"]}, "observed_at": {"from_metadata": "resource_last_modified"},
            "fields": fields,
            "source_reliability": {"identity": 0.9, "address": 0.8, "classification": 0.7, "contact": 0.6}}
    base.update(kw)
    return base


class TestTransforms(unittest.TestCase):
    def test_abn_checksum_and_length(self):
        self.assertEqual(abn("51 824 753 556"), "51824753556")
        with self.assertRaises(Reject):
            abn("51824753557")          # right length, wrong checksum
        with self.assertRaises(Skip):
            abn("000000019")            # an ACN-length value is not an ABN
        self.assertIsNone(abn(""))

    def test_acn(self):
        self.assertEqual(acn("000 000 019"), "000000019")
        with self.assertRaises(Reject):
            acn("000000018")

    def test_dates_states_postcodes(self):
        self.assertEqual(parse_date("04/10/2010", ["%d/%m/%Y"]), "2010-10-04")
        with self.assertRaises(Reject):
            parse_date("31/02/2010", ["%d/%m/%Y"])
        self.assertEqual(state_code("Victoria"), "VIC")
        with self.assertRaises(Reject):
            state_code("Narnia")
        self.assertEqual(postcode(800.0), "0800")

    def test_entity_type_never_guesses_beyond_company(self):
        self.assertEqual(entity_type_from_suffix("Acme Pty Ltd"), "company")
        self.assertEqual(entity_type_from_suffix("Limited Tender Services"), "unknown")
        self.assertEqual(entity_type_from_suffix("Smith Family Trust"), "unknown")


class TestEngine(unittest.TestCase):
    def test_envelope_and_default_entity_type(self):
        c = cfg([field("name", "entity.legal_name", ["clean_whitespace"]), field("abn", "entity.abn", ["abn"])])
        obs, rej, stats = run_rows(c, [{"id": "1", "name": " Acme\xa0Pty Ltd ", "abn": "51824753556"}], META)
        by = {o["field"]: o for o in obs}
        self.assertEqual(by["entity.legal_name"]["value"], "Acme Pty Ltd")
        self.assertEqual(by["entity.abn"]["derivation_level"], "L1")
        self.assertEqual(by["entity.entity_type"]["value"], "unknown")  # default, flagged
        self.assertTrue(by["entity.entity_type"]["is_default"])
        for key in ("source_id", "source_record_id", "observed_at", "ingested_at", "licence", "extractor_version"):
            self.assertTrue(by["entity.legal_name"][key])
        self.assertEqual(rej, [])

    def test_bad_abn_is_rejected_not_emitted(self):
        c = cfg([field("name", "entity.legal_name", []), field("abn", "entity.abn", ["abn"])])
        obs, rej, stats = run_rows(c, [{"id": "1", "name": "X", "abn": "51824753557"}], META)
        self.assertNotIn("entity.abn", {o["field"] for o in obs})
        self.assertEqual(rej[0]["reason"], "abn_checksum_failed")
        self.assertEqual(stats["entity.abn<-abn"]["parse_rate"], 0.0)


    def test_skip_only_observed_at_still_records_a_blank_reject(self):
        """Step 3b review fix: a transform that only emits `skip` events (no reject) must not silently drop the row."""
        c = cfg([field("name", "entity.legal_name", [])],
                observed_at={"source": "d", "transforms": [{"name": "regex_extract", "arg": r"(\d{4}-\d{2}-\d{2})"}]})
        obs, rej, _ = run_rows(c, [{"id": "1", "name": "X", "d": "not a date"}], META)
        self.assertEqual(obs, [])
        self.assertEqual(rej, [{"source_record_id": "1", "field": "observed_at", "reason": "observed_at_blank"}])

    def test_mixed_abn_acn_column_routes_by_length(self):
        c = cfg([field("x", "entity.abn", ["abn"]), field("x", "entity.acn", ["acn"])])
        obs, rej, stats = run_rows(c, [{"id": "1", "x": "51824753556"}, {"id": "2", "x": "000000019"}], META)
        got = {(o["source_record_id"], o["field"]) for o in obs}
        self.assertIn(("1", "entity.abn"), got)
        self.assertIn(("2", "entity.acn"), got)
        self.assertEqual(rej, [])  # skips are not failures
        self.assertEqual(stats["entity.abn<-x"]["parse_rate"], 1.0)

    def test_split_aligns_entities_and_trading_names_stay_on_one(self):
        c = cfg([field("names", "entity.legal_name", [{"name": "split", "arg": ";"}]),
                 field("abns", "entity.abn", [{"name": "split", "arg": ";"}, "abn"]),
                 field("tn", "entity.trading_name", [{"name": "split", "arg": "|"}])])
        row = {"id": "7", "names": "A Pty Ltd; B Pty Ltd", "abns": "51824753556; 33051775556", "tn": "Alpha|Beta"}
        obs, rej, _ = run_rows(c, [row], META)
        refs = {o["entity_ref"] for o in obs}
        self.assertEqual(refs, {"7#main:0", "7#main:1"})
        e1 = {o["field"]: o["value"] for o in obs if o["entity_ref"] == "7#main:1" and o["field"] != "entity.trading_name"}
        self.assertEqual(e1["entity.legal_name"], "B Pty Ltd")
        self.assertEqual(e1["entity.abn"], "33051775556")
        tn = [o for o in obs if o["field"] == "entity.trading_name"]
        self.assertEqual(sorted(o["value"] for o in tn), ["Alpha", "Beta"])  # one observation each
        self.assertEqual({o["entity_ref"] for o in tn}, {"7#main:0"})

    def test_hash_id_is_deterministic(self):
        c = cfg([field("name", "entity.legal_name", [])], record_id={"hash_row": True})
        a, _, _ = run_rows(c, [{"name": "X"}], META)
        b, _, _ = run_rows(c, [{"name": "X"}], META)
        self.assertEqual(a[0]["source_record_id"], b[0]["source_record_id"])
        self.assertTrue(a[0]["source_record_id"].startswith("h:"))

    def test_enum_guard(self):
        c = cfg([field("s", "entity.status", [{"name": "map_values", "arg": '{"APPR": "active", "X": "bogus"}'}])])
        obs, rej, _ = run_rows(c, [{"id": "1", "s": "APPR"}, {"id": "2", "s": "X"}, {"id": "3", "s": "??"}], META)
        self.assertEqual([o["value"] for o in obs if o["field"] == "entity.status"], ["active"])
        self.assertEqual(len(rej), 2)

    def test_select_rows_is_even_and_deterministic(self):
        rows = [{"i": i} for i in range(10_000)]
        s = select_rows(rows, 1000)
        self.assertEqual(len(s), 1000)
        self.assertEqual(s[0]["i"], 0)
        self.assertEqual(s[-1]["i"], 9990)


class TestStructuralValidation(unittest.TestCase):
    def test_catches_invented_field_transform_and_column(self):
        c = cfg([field("nope", "entity.favourite_colour", ["wizardry"])])
        errs = structural_errors(c, load_ontology(), ["name"], META)
        text = " ".join(errs)
        self.assertIn("not in the ontology", text)
        self.assertIn("whitelist", text)
        self.assertIn("does not exist", text)


if __name__ == "__main__":
    unittest.main()


class TestApprovalLock(unittest.TestCase):
    def test_lock_refuses_unapproved_and_edited_configs(self):
        import json, tempfile
        from pathlib import Path
        from unittest import mock
        from src.engine import config as C
        with tempfile.TemporaryDirectory() as d, mock.patch.object(C, "CONFIG_DIR", Path(d)):
            sid = "demo"
            fixture = cfg([field("name", "entity.legal_name", [])], source_id=sid)
            C.write_config(fixture, C.config_path(sid))
            with self.assertRaises(PermissionError):           # no approval file at all
                C.load_approved_config(sid)
            C.approval_path(sid).write_text(json.dumps({"status": "approved", "config_sha256": C.sha256_of(C.config_path(sid))}))
            self.assertEqual(C.load_approved_config(sid)["source_id"], sid)   # approved and untouched
            C.config_path(sid).write_text(C.config_path(sid).read_text() + "\n# hand edit\n")
            with self.assertRaises(PermissionError):           # edited after approval
                C.load_approved_config(sid)


class TestReaders(unittest.TestCase):
    def test_bom_is_stripped_from_first_header(self):
        from src.engine.readers import _name_headers
        self.assertEqual(_name_headers(["﻿REGISTER", None, "A", "A"]), ["REGISTER", "_blank_1", "A", "A__2"])
