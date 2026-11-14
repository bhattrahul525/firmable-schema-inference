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

    def test_a_needs_review_config_is_refused_unless_the_override_flag_is_passed(self):
        cfg = agent_cfg()
        cfg["validation_summary"] = {"outcome": "needs_review"}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(engine_config, "CONFIG_DIR", Path(d)):
            engine_config.write_config(cfg, engine_config.config_path("s"))
            with mock.patch("sys.argv", ["approve", "s"]), self.assertRaises(SystemExit) as e:
                approve.main()
            self.assertIn("--allow-needs-review", str(e.exception))
            self.assertFalse(engine_config.approval_path("s").exists())
            with mock.patch("sys.argv", ["approve", "s", "--allow-needs-review"]), mock.patch("builtins.input", side_effect=[""]):
                approve.main()
            self.assertEqual(json.loads(engine_config.approval_path("s").read_text())["status"], "approved")

    def test_a_wrong_field_rejects_and_stores_no_hash(self):
        approval, _ = self.run_approve(["1", "wrong column", ""])
        self.assertEqual((approval["status"], approval["config_sha256"]), ("rejected", None))


class TestRejectionReachesNextRun(unittest.TestCase):
    def test_feedback_is_written_and_read_into_the_agent_task(self):
        from src.part2_agent import agent_prompt
        with tempfile.TemporaryDirectory() as d, mock.patch.object(engine_config, "CONFIG_DIR", Path(d)):
            engine_config.write_config(agent_cfg(), engine_config.config_path("s"))
            with mock.patch("sys.argv", ["approve", "s"]), mock.patch("builtins.input", side_effect=["1", "wrong column", "too vague"]):
                approve.main()
            fb = json.loads(engine_config.approval_path("s").read_text())["feedback_pending"]
        task = agent_prompt.make_task("f.csv", "s", None, fb)
        self.assertIn("wrong column", task)
        self.assertIn("too vague", task)
        self.assertNotIn("REVIEWER", agent_prompt.make_task("f.csv", "s"))

    def test_hint_uses_the_original_reference_and_trace_is_archived(self):
        from src.part2_agent import loop, onboard
        with tempfile.TemporaryDirectory() as d, mock.patch.object(loop, "RUNS_DIR", Path(d)):
            (Path(d) / "s").mkdir()
            (Path(d) / "s" / "trace.jsonl").write_text(json.dumps({"type": "trace_header", "reference": "/tmp/my data.csv"}) + "\n")
            self.assertEqual(approve.rerun_command("s"), "python -m src.part2_agent.onboard '/tmp/my data.csv' --source-id s")
            moved = onboard.archive_trace(Path(d) / "s", 1)
            self.assertEqual(moved.name, "trace.round1.jsonl")
            self.assertFalse((Path(d) / "s" / "trace.jsonl").exists())
            self.assertIsNone(onboard.archive_trace(Path(d) / "s", 1))


class TestMissingRegister(unittest.TestCase):
    def test_clear_error_names_the_file(self):
        from src.part3_resolve import idf
        with self.assertRaises(SystemExit) as e:
            idf.register_counts(raw=Path("nowhere/business_names_202611.zip"))
        self.assertIn("business_names_202611.zip", str(e.exception))
        self.assertIn("data.gov.au", str(e.exception))
