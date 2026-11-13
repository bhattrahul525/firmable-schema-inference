"""Step 5: approve.py works on an agent-produced config (no round-1 `proposal_agreement`; valid_from may come from metadata)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.engine import config as engine_config
from src.part2_agent import approve


def agent_cfg():
    f = {"source": "Name", "canonical": "entity.legal_name", "transforms": [{"name": "clean_whitespace", "arg": None}],
         "field_confidence": 0.9, "evidence": "held_out", "mapping_confidence": 0.9, "transform_level": "W"}
    return {"source_id": "s", "config_version": 1, "fields": [f], "unmapped": [], "record_id": {"hash_row": True},
            "observed_at": {"from_metadata": "downloaded_at"}, "valid_from": {"from_metadata": "downloaded_at"}}


class TestApproveAgentConfig(unittest.TestCase):
    def run_approve(self, answers):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(engine_config, "CONFIG_DIR", Path(d)):
            engine_config.write_config(agent_cfg(), engine_config.config_path("s"))
            with mock.patch("sys.argv", ["approve", "s"]), mock.patch("builtins.input", side_effect=answers):
                approve.main()
            return json.loads(engine_config.approval_path("s").read_text()), engine_config.sha256_of(engine_config.config_path("s"))

    def test_nothing_wrong_approves_and_locks_the_config_hash(self):
        approval, sha = self.run_approve([""])
        self.assertEqual((approval["status"], approval["config_sha256"]), ("approved", sha))

    def test_a_wrong_field_rejects_and_stores_no_hash(self):
        approval, _ = self.run_approve(["1", "wrong column", ""])
        self.assertEqual((approval["status"], approval["config_sha256"]), ("rejected", None))
