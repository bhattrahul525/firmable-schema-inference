import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.engine import config as engine_config
from src.part3_resolve import features
from src.part3_resolve.sources import BASE, active_sources


def approval(d: Path, sid: str, status: str) -> None:
    (d / f"{sid}.approval.json").write_text(json.dumps({"status": status}))


class TestActiveSources(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg, self.obs = Path(self.tmp.name, "configs"), Path(self.tmp.name, "obs")
        self.cfg.mkdir(), self.obs.mkdir()
        self.ref = {"asic_business_names"}

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, **kw):
        return active_sources(self.cfg, self.obs, self.ref, **kw)

    def test_no_extra_source_gives_exactly_the_base_list(self):
        for sid in BASE:
            approval(self.cfg, sid, "approved")
        approval(self.cfg, "other", "pending_review")
        self.assertEqual(self.call(), BASE)

    def test_one_approved_extracted_extra_is_appended_after_base(self):
        approval(self.cfg, "zeta", "approved"), approval(self.cfg, "alpha", "approved")
        for sid in ("zeta", "alpha"):
            (self.obs / f"{sid}.jsonl").write_text("")
        self.assertEqual(self.call(), BASE + ["alpha", "zeta"])

    def test_unapproved_reference_and_unextracted_sources_are_left_out(self):
        approval(self.cfg, "rej", "rejected"), approval(self.cfg, "asic_business_names", "approved")
        approval(self.cfg, "noobs", "approved")
        for sid in ("rej", "asic_business_names"):
            (self.obs / f"{sid}.jsonl").write_text("")
        skipped = []
        self.assertEqual(self.call(skipped=skipped), BASE)
        self.assertEqual(skipped, ["noobs"])


class TestExtraSourceMentionsLoad(unittest.TestCase):
    def test_agent_style_source_without_abn_loads_as_a_mention(self):
        with tempfile.TemporaryDirectory() as d:
            obs = Path(d)
            rows = [{"source_id": "newsrc", "source_record_id": "h1", "entity_ref": "h1", "field": "entity.legal_name",
                     "value": "Acme Widgets Pty Ltd"},
                    {"source_id": "newsrc", "source_record_id": "h1", "entity_ref": "h1", "field": "address.postcode", "value": "3000"}]
            (obs / "newsrc.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            with mock.patch.object(features, "OBS_DIR", obs), mock.patch.object(features, "abn_unverified", return_value=False), \
                    mock.patch.object(features, "reference_sources", return_value={}):
                m = features.load_mentions(["newsrc"])
        self.assertEqual(len(m), 1)
        self.assertEqual((m[0]["abn"], m[0]["postcode"], m[0]["mention_id"]), (None, "3000", "newsrc|h1"))
        self.assertTrue(m[0]["core"])
