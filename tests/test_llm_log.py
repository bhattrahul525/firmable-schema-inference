"""Round tagging in logs/llm_calls.jsonl: round-2 calls must never change round-1 cost figures."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from src import llm


def line(round_no=None, cost=0.01, source="s", step="x"):
    e = {"step": step, "source_id": source, "cost_usd": cost, "input_tokens": 100, "output_tokens": 10, "seconds": 1.0}
    if round_no is not None:
        e["round"] = round_no
    return json.dumps(e)


class TestRoundTagging(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "calls.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_new_log_line_is_tagged_round_2(self):
        with mock.patch.object(llm, "LOG_PATH", self.path):
            llm._log({"step": "a", "source_id": "s", "cost_usd": 0.01})
            llm._log({"step": "b", "source_id": "s", "cost_usd": 0.01, "round": 1})   # an explicit tag is respected
        rows = [json.loads(l) for l in self.path.read_text().splitlines()]
        self.assertEqual([r["round"] for r in rows], [2, 1])

    def test_chat_logs_its_turns_as_round_2(self):
        usage = SimpleNamespace(input_tokens=10, output_tokens=2, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        block = SimpleNamespace(model_dump=lambda **kw: {"type": "text", "text": "hi"})
        resp = SimpleNamespace(content=[block], stop_reason="end_turn", usage=usage, _request_id="r")
        client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: resp))
        with mock.patch.object(llm, "_get_client", return_value=client), mock.patch.object(llm, "LOG_PATH", self.path):
            llm.chat([{"role": "user", "content": "x"}], step="agent.turn", model="claude-haiku-5-5")
        self.assertEqual(json.loads(self.path.read_text())["round"], 2)

    def test_untagged_lines_are_round_1_and_rounds_are_reported_separately(self):
        self.path.write_text("\n".join([line(None, 0.10), line(None, 0.05), line(2, 0.30), line(2, 0.20), line(1, 0.01)]) + "\n")
        r1 = llm.spend_summary(self.path)                      # the default is round 1
        self.assertEqual((r1["total"]["calls"], round(r1["total"]["cost_usd"], 4)), (3, 0.16))
        r2 = llm.spend_summary(self.path, round_no=2)
        self.assertEqual((r2["total"]["calls"], round(r2["total"]["cost_usd"], 4)), (2, 0.50))
        every = llm.spend_summary(self.path, round_no=None)
        self.assertEqual((every["total"]["calls"], round(every["total"]["cost_usd"], 4)), (5, 0.66))
        by = llm.spend_by_round(self.path)
        self.assertEqual(sorted(by), [1, 2])
        self.assertEqual(round(by[1]["total"]["cost_usd"], 4), 0.16)

    def test_round_2_calls_never_change_the_round_1_figures(self):
        self.path.write_text("\n".join([line(None, 0.10), line(None, 0.05)]) + "\n")
        before = llm.spend_summary(self.path)["total"]
        with mock.patch.object(llm, "LOG_PATH", self.path):
            for _ in range(20):
                llm._log({"step": "agent.turn", "source_id": "new", "cost_usd": 0.50, "input_tokens": 999, "output_tokens": 99})
        after = llm.spend_summary(self.path)["total"]
        self.assertEqual(before, after)                        # round 1 did not move
        self.assertEqual(llm.spend_summary(self.path, round_no=2)["total"]["calls"], 20)

    def test_missing_log_is_an_empty_summary(self):
        self.assertEqual(llm.spend_summary(self.path)["total"]["calls"], 0)
        self.assertEqual(llm.spend_by_round(self.path), {})


if __name__ == "__main__":
    unittest.main()
