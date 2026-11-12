"""Step 3b: evidence states (C), protected top rows and raw_top (B), skip_rows_after_header (A), the header-like
warning and the packet's raw rows (E), valid_from / valid_to statistics and visibility (D), rule wording (F) and the
reasoning summary in the trace (G). Nothing here needs an API key or the network."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.part2_agent import agent_hooks
from src.part2_agent.agent_table import PROTECTED_ROWS, Table, build_table, get_table
from src.engine.readers import ReaderError, row_fingerprint
from tests.agent_env import Env, FakeCritic, good_config, make_abn, write_big_csv

FIX = Path(__file__).parent / "fixtures"


def fake_table(rows: list[dict], held_idx: set[int] | None = None, tmp: Path | None = None) -> Table:
    """A Table over in-memory rows: fingerprints from the cell values, held-out rows by index."""
    held_idx = held_idx or set()
    cache = [(row_fingerprint(list(r.values()) + [i]) , r) for i, r in enumerate(rows)]   # i: identical rows stay distinct
    held_fp = frozenset(fp for i, (fp, _) in enumerate(cache) if i in held_idx)
    path = (tmp or Path(".")) / "fake_table.csv"
    path.write_text("x\n")   # training_stats caches by the file's stat
    headers = list(rows[0]) if rows else []
    return Table(path=path, reader={"format": "csv"}, headers=headers, n_rows=len(rows),
                 visible_n=len(rows) - len(held_idx), held_fp=held_fp,
                 held_rows=[r for i, r in enumerate(rows) if i in held_idx], cache=cache)


class TestEvidenceStates(unittest.TestCase):
    """Item C: held_out / training / unverified, computed by code, never by a statement from the model."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        agent_hooks._TRAINING_STATS.clear()

    def cfg(self, *fields):
        return {"reader": {"format": "csv"}, "record_id": {"hash_row": True},
                "observed_at": {"from_metadata": "resource_last_modified"},
                "fields": [dict(f) for f in fields], "unmapped": [], "needs_transform": [],
                "source_reliability": {"identity": 0.9}, "meaning_check_responses": []}

    @staticmethod
    def report(stats: dict) -> dict:
        return {"structural_errors": [], "field_failures": [], "unaccounted_columns": [], "duplicate_ids": None,
                "warnings": [], "infos": [], "stats": stats, "n_rows": 0, "hard_failure_count": 0, "id_failure": False}

    def test_five_or_more_judged_held_out_values_mean_held_out_and_no_training_scan(self):
        rows = [{"A": f"Name {i} Pty Ltd"} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10)), tmp=self.tmp)
        cfg = self.cfg({"source": "A", "canonical": "entity.legal_name", "transforms": [{"name": "clean_whitespace", "arg": ""}]})
        stats = {"entity.legal_name<-A": {"rows": 10, "blank": 0, "ok": 10, "reject": 0, "parse_rate": 1.0}}
        with mock.patch.object(agent_hooks, "training_stats", side_effect=AssertionError("must not scan training rows")) :
            states, failures = agent_hooks.evidence_states(cfg, t, self.report(stats))
        self.assertEqual(states["entity.legal_name<-A"], {"evidence": "held_out"})
        self.assertEqual(failures, [])

    def test_a_sparse_column_judged_on_training_rows_gets_training_evidence_with_whole_file_counts_and_examples(self):
        rows = [{"A": make_abn(i) if i < 8 else ""} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)   # every populated row is a training row
        cfg = self.cfg({"source": "A", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}]})
        stats = {"entity.abn<-A": {"rows": 10, "blank": 10, "ok": 0, "reject": 0, "parse_rate": None}}
        states, failures = agent_hooks.evidence_states(cfg, t, self.report(stats))
        s = states["entity.abn<-A"]
        self.assertEqual(s["evidence"], "training")
        self.assertEqual(s["whole_file"], {"populated": 8, "judged": 8, "ok": 8, "rejected": 0})
        self.assertEqual(s["parse_rate"], 1.0)
        self.assertEqual(len(s["examples"]), 3)      # up to EXAMPLES_PER_FIELD raw-to-value pairs
        self.assertEqual(failures, [])

    def test_training_evidence_below_the_floor_is_a_hard_failure(self):
        rows = [{"A": "not-a-date" if i < 9 else ("01/03/2021" if i == 9 else "")} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)
        cfg = self.cfg({"source": "A", "canonical": "entity.date_registered",
                        "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]})
        stats = {"entity.date_registered<-A": {"rows": 10, "blank": 10, "ok": 0, "reject": 0, "parse_rate": None}}
        states, failures = agent_hooks.evidence_states(cfg, t, self.report(stats))
        self.assertEqual(states["entity.date_registered<-A"]["evidence"], "training")
        self.assertEqual(len(failures), 1)
        self.assertIn("below", failures[0]["reason"])
        self.assertEqual(failures[0]["key"], "entity.date_registered<-A")

    def test_fewer_than_five_judged_values_in_the_whole_file_is_unverified(self):
        rows = [{"A": make_abn(i) if i < 2 else ""} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)
        cfg = self.cfg({"source": "A", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}]})
        stats = {"entity.abn<-A": {"rows": 10, "blank": 10, "ok": 0, "reject": 0, "parse_rate": None}}
        states, failures = agent_hooks.evidence_states(cfg, t, self.report(stats))
        self.assertEqual(states["entity.abn<-A"]["evidence"], "unverified")
        self.assertEqual(failures, [])   # two valid values: not a zero-parse failure

    def test_unverified_with_values_that_never_parse_is_a_hard_failure(self):
        rows = [{"A": "junk" if i < 3 else ""} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)
        cfg = self.cfg({"source": "A", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}]})
        stats = {"entity.abn<-A": {"rows": 10, "blank": 10, "ok": 0, "reject": 0, "parse_rate": None}}
        states, failures = agent_hooks.evidence_states(cfg, t, self.report(stats))
        self.assertEqual(states["entity.abn<-A"]["evidence"], "unverified")
        self.assertEqual(len(failures), 1)
        self.assertIn("never produced a valid value anywhere in the file", failures[0]["reason"])

    def test_boundary_the_fifth_judged_value_moves_unverified_to_training(self):
        for populated, expected in ((4, "unverified"), (5, "training")):
            agent_hooks._TRAINING_STATS.clear()
            rows = [{"A": make_abn(i) if i < populated else ""} for i in range(20)]
            t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)
            cfg = self.cfg({"source": "A", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}]})
            stats = {"entity.abn<-A": {"rows": 10, "blank": 10, "ok": 0, "reject": 0, "parse_rate": None}}
            states, _ = agent_hooks.evidence_states(cfg, t, self.report(stats))
            self.assertEqual(states["entity.abn<-A"]["evidence"], expected, populated)

    def test_held_out_and_training_values_are_combined_when_held_out_alone_is_too_thin(self):
        rows = [{"A": make_abn(i) if i in (0, 1, 10, 11, 12) else ""} for i in range(20)]
        t = fake_table(rows, held_idx=set(range(10, 20)), tmp=self.tmp)   # 3 populated held-out, 2 training
        cfg = self.cfg({"source": "A", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}]})
        stats = {"entity.abn<-A": {"rows": 10, "blank": 7, "ok": 3, "reject": 0, "parse_rate": 1.0}}
        states, _ = agent_hooks.evidence_states(cfg, t, self.report(stats))
        s = states["entity.abn<-A"]
        self.assertEqual(s["evidence"], "training")           # 3 held + 2 training = 5 judged
        self.assertEqual(s["whole_file"]["judged"], 5)


class TestEvidenceCaps(unittest.TestCase):
    """Item C: field_confidence is the lowest of the model's confidence, the measured rate and the evidence cap."""

    def run_finalise(self, report, conf=0.95):
        cfg = good_config()
        cfg["fields"] = [cfg["fields"][1]]           # entity.abn<-ABN only
        cfg["fields"][0]["mapping_confidence"] = conf
        cfg["unmapped"] += [{"source": c, "reason": "test"} for c in ("Business Name", "State", "Registered")]
        with mock.patch.object(agent_hooks, "validate_config", return_value=report):
            out, _ = agent_hooks.finalise_config(cfg, "s", Path("w"), None, "v", [], [])
        return out["fields"][0]

    def report(self, state, parse_rate=None, held_rate=None, whole=None):
        return {"stats": {"entity.abn<-ABN": {"parse_rate": held_rate, "rows": 10, "ok": 0, "reject": 0}},
                "held_rows": 10, "observations": 0, "warnings": [],
                "evidence": {"entity.abn<-ABN": {"evidence": state, "parse_rate": parse_rate,
                                                 "whole_file": whole or {"populated": 6, "judged": 6, "ok": 6, "rejected": 0}}}}

    def test_training_evidence_caps_field_confidence_at_0_8(self):
        f = self.run_finalise(self.report("training", parse_rate=1.0))
        self.assertEqual(f["field_confidence"], agent_hooks.TRAINING_CAP)
        self.assertEqual(f["evidence"], "training")
        self.assertEqual(f["validation"]["whole_file"]["judged"], 6)

    def test_training_evidence_uses_the_combined_rate_when_it_is_lower_than_the_cap(self):
        f = self.run_finalise(self.report("training", parse_rate=0.75))
        self.assertEqual(f["field_confidence"], 0.75)

    def test_unverified_caps_at_0_5(self):
        f = self.run_finalise(self.report("unverified", whole={"populated": 1, "judged": 1, "ok": 1, "rejected": 0}))
        self.assertEqual(f["field_confidence"], agent_hooks.UNVERIFIED_CAP)
        self.assertEqual(f["evidence"], "unverified")

    def test_held_out_evidence_keeps_the_old_rule(self):
        rep = self.report("held_out")
        rep["stats"]["entity.abn<-ABN"] = {"parse_rate": 0.93, "rows": 100, "ok": 93, "reject": 7}
        f = self.run_finalise(rep)
        self.assertEqual(f["field_confidence"], 0.93)
        self.assertEqual(f["evidence"], "held_out")


class TestSparseColumnThroughTheTools(Env):
    """Item C end to end: a column with two values in the whole file ends `unverified` whatever the split chose."""

    def setUp(self):
        super().setUp()
        src = Path(self._tmp.name) / "sparse.csv"
        lines = ["Licence No,Business Name,Sparse ABN"]
        for i in range(1, 801):
            abn = make_abn(i) if i in (3, 4) else ""
            lines.append(f"L{i:05d},Company {i} Pty Ltd,{abn}")
        src.write_text("\n".join(lines) + "\n")
        self.start(src)
        self.call("read_table", {"format": "csv"})
        self.cfg = good_config()
        self.cfg["fields"] = [self.cfg["fields"][0],
                              {"source": "Sparse ABN", "canonical": "entity.abn", "transforms": [{"name": "abn", "arg": ""}],
                               "group": "main", "mapping_confidence": 0.9, "reason": "sparse"}]
        self.cfg["unmapped"] = []

    def test_validate_passes_and_the_evidence_is_unverified_not_a_silent_pass(self):
        res, _ = self.call("validate", {"config": self.cfg})
        self.assertEqual(res.status["hard_failures"], 0, res.payload)
        report = agent_hooks.validate_config(self.cfg, self.sid, self.work)
        key = "entity.abn<-Sparse ABN"
        self.assertEqual(report["evidence"][key]["evidence"], "unverified")
        self.assertLessEqual(report["evidence"][key]["whole_file"]["judged"], 2)

    def test_finalise_caps_the_sparse_field_and_the_packet_lists_it(self):
        cfg, report = agent_hooks.finalise_config(self.cfg, self.sid, self.work, None, "v", [], [])
        sparse = next(f for f in cfg["fields"] if f["canonical"] == "entity.abn")
        self.assertEqual(sparse["evidence"], "unverified")
        self.assertLessEqual(sparse["field_confidence"], agent_hooks.UNVERIFIED_CAP)
        name = next(f for f in cfg["fields"] if f["canonical"] == "entity.legal_name")
        self.assertEqual(name["evidence"], "held_out")
        result = mock.Mock(outcome="validated_config", forced_by=None, turns=1, tool_calls=1, cost_usd=0.0,
                           elapsed_seconds=1, evidence="", reason="", abstentions=[], config=cfg)
        md = agent_hooks._packet_markdown(result, cfg, report, None, [], [], "trace")
        self.assertIn("## Fields without enough held-out evidence", md)
        self.assertIn("**unverified**", md)
        self.assertIn("Evidence", md.splitlines()[next(i for i, l in enumerate(md.splitlines()) if l.startswith("| # |"))])

    def test_the_critic_is_shown_populated_training_rows_for_the_sparse_column(self):
        fake = FakeCritic([])
        with mock.patch("src.part2_agent.agent_hooks.llm.call", fake):
            self.call("critique", {"config": self.cfg})
        prompt = fake.prompts[0][0]
        self.assertIn('"note": "training row', prompt)   # a marked extra example inside the <data> block, not just prompt text


class TestProtectedTopRows(Env):
    """Item B: the first PROTECTED_ROWS raw rows are never held out, through read_table and sniff."""

    def setUp(self):
        super().setUp()
        self.src = Path(self._tmp.name) / "big.csv"
        write_big_csv(self.src)
        self.start(self.src)

    def _raw_top_fingerprints(self) -> set:
        from src.engine.readers import raw_head_fingerprints
        return raw_head_fingerprints({"format": "csv"}, self.src, PROTECTED_ROWS)

    def test_none_of_the_first_protected_rows_is_ever_held_out(self):
        self.call("read_table", {"format": "csv"})
        table = get_table(self.sid, self.work)
        self.assertFalse(table.held_fp & self._raw_top_fingerprints())

    def test_sniffs_twelve_lines_are_all_training_rows(self):
        res, _ = self.call("sniff", {})
        built = build_table(self.sid, self.work, self.src, {"format": "csv"})
        self.assertFalse(built.held_fp & self._raw_top_fingerprints())
        self.assertEqual(PROTECTED_ROWS, 12)
        self.assertEqual(len(res.payload["head"]), 12)

    def test_protection_survives_a_re_read_with_other_options(self):
        self.call("read_table", {"format": "csv"})
        self.call("read_table", {"format": "csv", "encoding": "utf-8", "drop_empty_columns": True})
        table = get_table(self.sid, self.work)
        self.assertFalse(table.held_fp & self._raw_top_fingerprints())

    def test_protection_survives_a_resplit(self):
        self.call("read_table", {"format": "csv", "delimiter": ";"})   # wrong parse -> forces a resplit on the next call
        res, _ = self.call("read_table", {"format": "csv"})
        self.assertIn("re-made", res.text)
        table = get_table(self.sid, self.work)
        self.assertFalse(table.held_fp & self._raw_top_fingerprints())

    def test_read_table_returns_raw_top_numbered_and_never_held_out(self):
        res, _ = self.call("read_table", {"format": "csv"})
        raw_top = res.payload["raw_top"]
        self.assertEqual(len(raw_top), PROTECTED_ROWS)
        self.assertEqual(raw_top[0]["row"], 1)
        self.assertEqual(raw_top[11]["row"], 12)
        self.assertEqual(raw_top[0]["cells"][0], "Licence No")   # the header row, shown even though training hides nothing here

    def test_raw_top_is_present_on_a_failed_read_too(self):
        res, _ = self.call("read_table", {"format": "csv", "skip_rows": 9000})
        self.assertTrue(res.is_error)
        self.assertIn("raw_top", res.payload)
        self.assertIsNotNone(res.payload["raw_top"])

    def test_a_file_too_small_for_a_held_out_split_gets_none_and_says_so(self):
        small = Path(self._tmp.name) / "small.csv"
        small.write_text("A,B\n" + "\n".join(f"v{i},w{i}" for i in range(5)) + "\n")
        self.start(small, sid="small")
        res, _ = self.call("read_table", {"format": "csv"})
        self.assertFalse(res.is_error, res.text)
        table = get_table(self.sid, self.work)
        self.assertEqual(table.held_fp, frozenset())
        self.assertIn("too small for a held-out set", res.text)

    def test_json_protects_the_first_records_too(self):
        import json as _json
        p = Path(self._tmp.name) / "recs.json"
        _json.dump([{"a": i} for i in range(40)], p.open("w"))
        from src.engine.readers import raw_head_fingerprints
        protected = raw_head_fingerprints({"format": "json"}, p, PROTECTED_ROWS)
        self.start(p, sid="j")
        self.call("read_table", {"format": "json"})
        table = get_table(self.sid, self.work)
        self.assertFalse(table.held_fp & protected)


class TestHeaderLikeFirstRowWarning(unittest.TestCase):
    """Item E: a generic, code-computed warning that header_rows: 0 may have missed a real header."""

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        self.path = self.tmp / "f.csv"

    def cfg(self, header_rows=0):
        return {"reader": {"format": "csv", "header_rows": header_rows}, "record_id": {"hash_row": True},
                "observed_at": {"from_metadata": "resource_last_modified"}, "fields": [], "unmapped": [],
                "needs_transform": [], "source_reliability": {"identity": 0.9}}

    def write(self, header: list[str], n: int = 30):
        lines = [",".join(header)]
        for i in range(n):
            lines.append(f"Name {i} Pty Ltd,{100000000 + i},01/0{(i % 9) + 1}/2021")
        self.path.write_text("\n".join(lines) + "\n")

    def table(self):
        return fake_table_from_file(self.path)

    def test_fires_when_a_real_header_was_read_as_data(self):
        self.write(["Name", "ABN", "Registered"])
        t = self.table()
        out = agent_hooks.header_like_first_row_warning(self.cfg(0), t)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["id"], "header_like_first_row")

    def test_does_not_fire_with_header_rows_one(self):
        self.write(["Name", "ABN", "Registered"])
        t = self.table()
        self.assertEqual(agent_hooks.header_like_first_row_warning(self.cfg(1), t), [])

    def test_does_not_fire_on_an_all_text_table_with_no_header_like_row(self):
        lines = ["Alpha Pty Ltd,Beta Pty Ltd,Gamma Pty Ltd"] + [f"Row {i} Pty Ltd,Row {i} Pty Ltd,Row {i} Pty Ltd" for i in range(30)]
        self.path.write_text("\n".join(lines) + "\n")
        t = self.table()
        self.assertEqual(agent_hooks.header_like_first_row_warning(self.cfg(0), t), [])

    def test_does_not_fire_when_the_first_row_itself_looks_like_a_number_or_date(self):
        lines = ["100000000,33051775556,01/03/2021"] + [f"Name {i} Pty Ltd,{100000000 + i},01/0{(i % 9) + 1}/2021" for i in range(30)]
        self.path.write_text("\n".join(lines) + "\n")
        t = self.table()
        self.assertEqual(agent_hooks.header_like_first_row_warning(self.cfg(0), t), [])

    def test_answerable_like_any_meaning_warning(self):
        self.write(["Name", "ABN", "Registered"])
        cfg = self.cfg(0)
        cfg["meaning_check_responses"] = [{"check_id": "header_like_first_row", "action": "kept", "reason": "no header really"}]
        report = {"warnings": agent_hooks.header_like_first_row_warning(cfg, self.table()), "stats": {"x": {}}}
        self.assertEqual(agent_hooks.unanswered(report, cfg), [])


def fake_table_from_file(path: Path) -> Table:
    from src.engine.readers import iter_table
    with iter_table({"format": "csv", "header_rows": 0}, path) as (headers, rows):
        rows = list(rows)
    cache = [(fp, r) for fp, r in rows]
    return Table(path=path, reader={"format": "csv", "header_rows": 0}, headers=headers, n_rows=len(cache),
                visible_n=len(cache), held_fp=frozenset(), held_rows=[], cache=cache)


class TestPacketShowsRawRows(Env):
    """Item E: the packet shows the reader options, the layout sentence and the raw rows beside the reader options."""

    def setUp(self):
        super().setUp()
        self.src = Path(self._tmp.name) / "data.csv"
        self.src.write_text("Title line\n\nName,ABN\nAcme Pty Ltd,51824753556\nBeta Pty Ltd,33051775556\n")
        self.start(self.src)

    def test_packet_lists_the_raw_rows_and_the_layout(self):
        cfg = good_config(reader={"format": "csv", "skip_rows": 2, "header_rows": 1})
        cfg["fields"] = [cfg["fields"][0]]
        cfg["fields"][0]["source"] = "Name"
        cfg["unmapped"] = [{"source": "ABN", "reason": "test"}]
        md = agent_hooks._reader_settings_section(cfg, self.sid, self.work)
        text = "\n".join(md)
        self.assertIn("Reader and record settings", text)
        self.assertIn("Title line", text)
        self.assertIn("layout:", text)
        self.assertIn("column names from raw row 3", text)


class TestEnvelopeStats(unittest.TestCase):
    """Item D3: observed_at / valid_from / valid_to get the same stats and reject tracking as a mapped field."""

    def cfg(self, **over):
        c = {"source_id": "s", "config_version": 1, "reader": {"format": "csv"},
            "record_id": {"from": ["Number"]}, "observed_at": {"from_metadata": "resource_last_modified"},
            "fields": [{"source": "Name", "canonical": "entity.legal_name",
                       "transforms": [{"name": "clean_whitespace", "arg": ""}], "group": "main", "mapping_confidence": 0.9}],
            "unmapped": [], "needs_transform": [], "source_reliability": {"identity": 0.9}}
        c.update(over)
        return c

    def test_a_per_row_valid_from_gets_a_stats_entry_and_its_rejects_are_recorded(self):
        from src.engine.extract import run_rows
        cfg = self.cfg(valid_from={"source": "Start", "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]})
        rows = [{"Name": "A Pty Ltd", "Number": "1", "Start": "01/03/2021"},
               {"Name": "B Pty Ltd", "Number": "2", "Start": "not-a-date"},
               {"Name": "C Pty Ltd", "Number": "3", "Start": ""}]
        obs, rej, stats = run_rows(cfg, rows, {"resource_last_modified": "2024-01-01", "licence": "x", "licence_flag": False})
        self.assertIn("valid_from", stats)
        self.assertEqual(stats["valid_from"]["rows"], 3)
        self.assertEqual(stats["valid_from"]["ok"], 1)
        self.assertEqual(stats["valid_from"]["reject"], 1)
        self.assertEqual(stats["valid_from"]["blank"], 1)
        env_rejects = [r for r in rej if r["field"] == "valid_from"]
        self.assertEqual(len(env_rejects), 1)
        self.assertEqual(env_rejects[0]["raw_value"], "not-a-date")
        # the row with the reject still produces observations, with valid_from None (unchanged stamping behaviour)
        row2_obs = [o for o in obs if o["source_record_id"] == "2"]
        self.assertTrue(row2_obs)
        self.assertIsNone(row2_obs[0]["valid_from"])

    def test_from_metadata_settings_get_no_stats_entry(self):
        from src.engine.extract import run_rows
        cfg = self.cfg()
        obs, rej, stats = run_rows(cfg, [{"Name": "A Pty Ltd", "Number": "1"}],
                                   {"resource_last_modified": "2024-01-01", "licence": "x", "licence_flag": False})
        self.assertNotIn("observed_at", stats)

    def test_a_blank_observed_at_is_rejected_exactly_once_not_twice(self):
        from src.engine.extract import run_rows
        cfg = self.cfg(observed_at={"source": "When", "transforms": []})
        rows = [{"Name": "A Pty Ltd", "Number": "1", "When": ""}]
        obs, rej, stats = run_rows(cfg, rows, {"licence": "x", "licence_flag": False})
        self.assertEqual(len([r for r in rej if r["source_record_id"] == "1"]), 1)
        self.assertEqual(rej[0]["reason"], "observed_at_blank")


class TestAbstainDeletesValidFromValidTo(unittest.TestCase):
    """Item D3: valid_from / valid_to are abstained by deleting the config key, not by moving a column to unmapped."""

    def cfg(self):
        return {"fields": [], "unmapped": [],
               "valid_from": {"source": "Start", "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]},
               "valid_to": {"source": "End", "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]}}

    def test_abstaining_valid_from_deletes_the_key(self):
        out = agent_hooks.abstain_config(self.cfg(), ["valid_from"])
        self.assertNotIn("valid_from", out)
        self.assertIn("valid_to", out)
        self.assertEqual(out["unmapped"], [])   # nothing was added to unmapped for it

    def test_abstaining_both(self):
        out = agent_hooks.abstain_config(self.cfg(), ["valid_from", "valid_to"])
        self.assertNotIn("valid_from", out)
        self.assertNotIn("valid_to", out)

    def test_observed_at_is_never_deleted_this_way(self):
        cfg = self.cfg()
        cfg["observed_at"] = {"source": "When", "transforms": []}
        out = agent_hooks.abstain_config(cfg, ["observed_at"])
        self.assertIn("observed_at", out)   # not one of the two keys this path handles


class TestPacketRecordLevelSettings(Env):
    """Item D1: the packet shows record_id, observed_at, valid_from, valid_to with evidence and examples."""

    def setUp(self):
        super().setUp()
        src = Path(self._tmp.name) / "dates.csv"
        lines = ["Licence No,Business Name,Start,ABN"]
        for i in range(1, 60):
            lines.append(f"L{i:04d},Company {i} Pty Ltd,01/0{(i % 9) + 1}/2021,{make_abn(i)}")
        src.write_text("\n".join(lines) + "\n")
        self.start(src)
        self.call("read_table", {"format": "csv"})
        self.cfg = good_config()
        self.cfg["fields"] = [self.cfg["fields"][0]]
        self.cfg["fields"][0]["source"] = "Business Name"
        self.cfg["record_id"] = {"from": ["Licence No"]}
        self.cfg["valid_from"] = {"source": "Start", "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]}
        self.cfg["unmapped"] = [{"source": "Start", "reason": "x"}, {"source": "ABN", "reason": "x"}]
        self.cfg["unmapped"] = [{"source": "ABN", "reason": "x"}]

    def test_the_critic_summary_carries_valid_from_and_needs_transform(self):
        fake = FakeCritic([])
        with mock.patch("src.part2_agent.agent_hooks.llm.call", fake):
            self.call("critique", {"config": self.cfg})
        prompt = fake.prompts[0][0]
        self.assertIn('"valid_from"', prompt)
        self.assertIn('"needs_transform"', prompt)

    def test_the_packet_shows_the_record_level_settings_table(self):
        cfg, report = agent_hooks.finalise_config(self.cfg, self.sid, self.work, None, "v", [], [])
        result = mock.Mock(outcome="validated_config", forced_by=None, turns=1, tool_calls=1, cost_usd=0.0,
                           elapsed_seconds=1, evidence="", reason="", abstentions=[], config=cfg)
        md = agent_hooks._packet_markdown(result, cfg, report, None, [], [], "trace", self.sid, self.work)
        self.assertIn("Reader and record settings", md)
        self.assertIn("`record_id`: from `Licence No`", md)
        self.assertIn("`valid_from`: from `Start`", md)


class TestRuleWordingFandD4(unittest.TestCase):
    """Item F (register exception in rule 5, rule 4 cross-reference) and D4 (strict valid_from/valid_to in rule 10),
    in both the agent prompt and the critic prompt, the same words."""

    def setUp(self):
        from src.part2_agent import agent_prompt
        self.agent_prompt = agent_prompt

    def flat(self, text: str) -> str:
        return " ".join(text.split())

    def test_rule_5_states_the_register_exception_with_the_holder_not_premises_clause(self):
        rule5 = next(l for l in self.agent_prompt.MAPPING_RULES.splitlines() if l.startswith("5. "))
        for fragment in ("register kept by a regulator or licensing body", "HOLDING a licence, registration, "
                        "accreditation or approval", "not a premises, venue or product", "mapping_confidence is 0.7 "
                        "or lower under 5b"):
            self.assertIn(fragment, rule5)
        # the pre-existing sentence (step 3) is kept verbatim, still after the legal_name sentence
        kept = ("A name column that the data does not label as a registered, licensee or supplier name maps to "
               "entity.trading_name at 0.6 or lower; it is not left unmapped for that reason.")
        self.assertIn(kept, rule5)
        self.assertTrue(rule5.index("Map a name to legal_name only if the data says") < rule5.index(kept))

    def test_rule_4_points_at_rule_5b_and_still_warns_against_inferring_sole_trader(self):
        rule4 = next(l for l in self.agent_prompt.MAPPING_RULES.splitlines() if l.startswith("4. "))
        self.assertIn("rule 5b", rule4)
        self.assertIn("never infer sole_trader from a person-like name", rule4)

    def test_rule_10_states_the_strict_valid_from_valid_to_rule(self):
        sentence = ("valid_from/valid_to: only from a column that says when the entity's own registration, licence, "
                   "accreditation or status started or ended. A date of an event or transaction the row records (a "
                   "contract, an order, an invoice, a payment, an application) is not when a name, identifier or "
                   "address became true: leave it unmapped.")
        rule10 = next(l for l in self.agent_prompt.MAPPING_RULES.splitlines() if l.startswith("10. "))
        self.assertIn(sentence, rule10)

    def test_both_rules_reach_the_critic_through_the_shared_rules_text(self):
        from src.part2_agent import agent_hooks
        for fragment in ("register kept by a regulator or licensing body",
                        "A date of an event or transaction the row records"):
            self.assertIn(fragment, self.flat(agent_hooks.CRITIC_SYSTEM))
            self.assertIn(fragment, self.flat(self.agent_prompt.SYSTEM_TASK))

    def test_no_rule_text_mentions_a_dataset_column_or_value(self):
        """Mirrors the existing no-dataset-words test (test_critic_and_coverage.py): the new wording stays generic."""
        from tests.test_critic_and_coverage import TestCriticRulesAndBusinessEntityRule
        for word in TestCriticRulesAndBusinessEntityRule.DEV_DRAW_WORDS:
            self.assertNotIn(word, self.agent_prompt.MAPPING_RULES, word)


class TestReasoningSummary(unittest.TestCase):
    """Item G: llm.chat requests a reasoning summary, and the replay line shows it (code-enforced rules only)."""

    def test_chat_requests_a_summarized_adaptive_thinking_block(self):
        from unittest import mock as _mock
        from src import llm
        captured = {}

        class FakeResp:
            content, stop_reason, usage, _request_id = [], "end_turn", _mock.Mock(input_tokens=1, output_tokens=1,
                                                                                   cache_read_input_tokens=0,
                                                                                   cache_creation_input_tokens=0), "r"

        def fake_create(**kwargs):
            captured.update(kwargs)
            return FakeResp()
        fake_client = _mock.Mock()
        fake_client.with_options.return_value = fake_client
        fake_client.messages.create = fake_create
        with _mock.patch.object(llm, "_get_client", return_value=fake_client):
            llm.chat([{"role": "user", "content": "hi"}], step="t", model="claude-haiku-5-5")
        self.assertEqual(captured.get("thinking"), {"type": "adaptive", "display": "summarized"})

    def test_thinking_summary_extracts_the_text_and_cuts_it(self):
        from src.part2_agent.loop import thinking_summary
        self.assertIsNone(thinking_summary([{"type": "text", "text": "hi"}]))
        self.assertEqual(thinking_summary([{"type": "thinking", "thinking": "because X"}]), "because X")
        long = "x" * 500
        self.assertTrue(thinking_summary([{"type": "thinking", "thinking": long}], cut=10).endswith("…"))

    def test_a_thinking_block_round_trips_the_trace_unchanged_including_the_signature(self):
        from src import llm
        block = [{"type": "thinking", "thinking": "reasoning text", "signature": "abcDEF123=="}]
        back = json.loads(llm.dumps_redacted(block))
        self.assertEqual(back, block)


if __name__ == "__main__":
    unittest.main()
