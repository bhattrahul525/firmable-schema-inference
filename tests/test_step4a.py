"""Step 4a: regex safety (R1, R2), regex_replace (R3), template (R4), constant (R5), the `when` condition (R6), the gate and the
transform level (R7). Two tests per rule. Nothing here needs an API key or the network."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from src.engine import transforms
from src.engine.config import load_ontology, structural_errors
from src.engine.extract import apply_transforms, run_rows
from src.part2_agent import agent_hooks
from src.part2_agent.guard import narrowing_changes
from tests.agent_env import Env, good_config

ONT = load_ontology()
META = {"downloaded_at": "2026-01-01", "resource_last_modified": "2026-01-01", "licence": "cc-by"}
EVIL = "a" * 40 + "b"   # (a+)+$ takes exponential time on it


def field(source, canonical, transforms, **extra):
    return {"source": source, "canonical": canonical, "transforms": transforms, "group": "main",
            "mapping_confidence": 0.9, "reason": "t", **extra}


def cfg_of(*fields):
    return {"source_id": "t", "config_version": "1", "reader": {"format": "csv"}, "record_id": {"hash_row": True},
            "observed_at": {"from_metadata": "downloaded_at"}, "fields": list(fields),
            "source_reliability": {"identity": 0.9, "address": 0.8, "classification": 0.5, "contact": 0.5}}


def errors(*fields, headers=("A", "B", "C", "Kind")):
    return structural_errors(cfg_of(*fields), ONT, list(headers), META)


def t(name, arg=None):
    return {"name": name, "arg": arg}


class TestR1PatternCheck(unittest.TestCase):
    def test_bad_or_overlong_pattern_is_a_sentence_in_each_of_the_three_places_not_an_exception(self):
        for pat in ("(unclosed", "x" * 201):
            es = errors(field("A", "entity.legal_name", [t("regex_extract", pat)]),
                        field("B", "entity.legal_name", [t("regex_replace", {"pattern": pat, "repl": ""})]),
                        field("C", "entity.legal_name", [t("clean_whitespace")], when={"column": "Kind", "matches": pat}))
            for where in ("fields[0]", "fields[1]", "fields[2]"):
                self.assertTrue(any(e.startswith(where) for e in es), (pat[:10], where, es))

    def test_a_pattern_that_fails_to_compile_at_run_time_is_a_bad_pattern_reject(self):
        _, events = apply_transforms("abc", [t("regex_extract", "(unclosed")])
        self.assertEqual(events, [("reject", "bad_pattern", "abc")])


@unittest.skipUnless(hasattr(__import__("signal"), "setitimer"), "no SIGALRM timer on this platform")
class TestR2Timer(unittest.TestCase):
    def setUp(self):
        transforms._TIMEOUTS.clear()
        for name, val in (("REGEX_SECONDS", 0.1), ("REGEX_MAX_TIMEOUTS", 2)):
            p = mock.patch.object(transforms, name, val)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(transforms._TIMEOUTS.clear)

    def test_a_slow_pattern_times_out_and_the_next_value_is_still_processed(self):
        vals, events = apply_transforms(EVIL, [t("regex_extract", r"(a+)+$")])
        self.assertEqual((vals, events[0][:2]), ([], ("reject", "regex_timeout")))
        vals, _ = apply_transforms("aaa", [t("regex_extract", r"(a+)+$")])
        self.assertEqual(vals, ["aaa"])

    def test_a_pattern_is_switched_off_after_the_limit(self):
        for _ in range(2):
            apply_transforms(EVIL, [t("regex_extract", r"(a+)+$")])
        _, events = apply_transforms("aaa", [t("regex_extract", r"(a+)+$")])
        self.assertEqual(events[0][:2], ("reject", "regex_switched_off"))


class TestR3RegexReplace(unittest.TestCase):
    def test_replaces_all_matches_leaves_no_match_alone_and_an_empty_result_is_absent(self):
        arg = {"pattern": r"\s*\([^)]*\)", "repl": ""}
        self.assertEqual(apply_transforms("ACME PTY LTD (ACME PLUMBING)", [t("regex_replace", arg)])[0], ["ACME PTY LTD"])
        self.assertEqual(apply_transforms("A (x) B (y)", [t("regex_replace", arg)])[0], ["A B"])
        self.assertEqual(apply_transforms("PLAIN", [t("regex_replace", arg)])[0], ["PLAIN"])
        self.assertEqual(apply_transforms("(only)", [t("regex_replace", arg)])[0], [])

    def test_repl_with_a_letter_or_a_bad_group_reference_is_refused(self):
        for repl in ("Pty Ltd", "2", "\\1"):   # a word, a digit, a reference to a group the pattern lacks
            self.assertTrue(errors(field("A", "entity.legal_name", [t("regex_replace", {"pattern": "x", "repl": repl})])), repl)
        self.assertFalse(errors(field("A", "entity.legal_name", [t("regex_replace", {"pattern": r"(\d+)-(\d+)", "repl": r"\1/\2"})])))


class TestR4Template(unittest.TestCase):
    def test_positions_filled_all_blank_absent_some_blank_rejected(self):
        tpl = [t("template", "{1}, {2} {3}")]
        self.assertEqual(apply_transforms(["1 High St", "Fitzroy", "3065"], tpl)[0], ["1 High St, Fitzroy 3065"])
        self.assertEqual(apply_transforms([None, " ", ""], tpl), ([], []))
        _, events = apply_transforms(["1 High St", "", "3065"], tpl)
        self.assertEqual(events[0][:2], ("reject", "template_missing_part"))

    def test_not_first_index_out_of_range_or_a_word_in_the_literal_are_structural_errors(self):
        bad = ([t("clean_whitespace"), t("template", "{1}, {2}")], [t("template", "{1}, {3}")], [t("template", "{1} Pty {2}")],
               [t("template", "{0}, {1}")], [t("template", ", ")])
        for ts in bad:
            self.assertTrue(errors(field(["A", "B"], "address.full", ts)), ts)
        self.assertFalse(errors(field(["A", "B"], "address.full", [t("template", "{1}, {2}")])))


class TestR5Constant(unittest.TestCase):
    def test_refused_on_the_wrong_field_inside_a_chain_and_with_a_state_outside_the_enum(self):
        for f in (field("A", "entity.legal_name", [t("constant", "VIC")]),
                  field("A", "address.state", [t("clean_whitespace"), t("constant", "VIC")]),
                  field("A", "address.state", [t("constant", "Victoria")]),
                  field(["A", "B"], "address.state", [t("constant", "VIC")])):
            self.assertTrue(errors(f), f)
        self.assertFalse(errors(field("A", "address.state", [t("constant", "VIC")])))

    def test_emitted_only_where_the_anchor_is_filled_and_tagged_l3(self):
        cfg = cfg_of(field("A", "address.state", [t("constant", "VIC")]))
        obs, rejects, _ = run_rows(cfg, [{"A": "Fitzroy"}, {"A": ""}], META, cfg_hash="x")
        states = [o for o in obs if o["field"] == "address.state"]
        self.assertEqual([(o["value"], o["derivation_level"]) for o in states], [("VIC", "L3")])
        self.assertEqual(rejects, [])


class TestR6When(unittest.TestCase):
    ROWS = [{"Id": "51824753556", "Kind": "abn"}, {"Id": "004085616", "Kind": "ACN"}, {"Id": "51824753556", "Kind": ""}]

    def run_abn(self, when):
        cfg = cfg_of(field("Id", "entity.abn", [t("abn")], when=when))
        obs, rejects, stats = run_rows(cfg, self.ROWS, META, cfg_hash="x")
        return [o for o in obs if o["field"] == "entity.abn"], rejects, stats["entity.abn<-Id"]

    def test_not_met_means_no_observation_a_when_not_met_skip_and_no_reject_and_equals_ignores_case(self):
        obs, rejects, st = self.run_abn({"column": "Kind", "equals": ["ABN"]})
        self.assertEqual(len(obs), 1)                         # row 1 ("abn" matches "ABN"); rows 2 and 3 do not hold
        self.assertEqual((st["skip_reasons"], st["reject"], rejects), ({"when_not_met": 2}, 0, []))

    def test_unknown_column_or_both_keys_are_structural_errors_and_the_condition_column_is_accounted_for(self):
        for when in ({"column": "Nope", "equals": ["x"]}, {"column": "Kind", "equals": ["x"], "matches": "x"}, {"column": "Kind"}):
            self.assertTrue(errors(field("A", "entity.abn", [t("abn")], when=when)), when)
        cfg = cfg_of(field("A", "entity.abn", [t("abn")], when={"column": "Kind", "equals": ["ABN"]}))
        cfg.update(unmapped=[], needs_transform=[], record_id={"from": ["B"]})
        from src.part2_agent.validate import _referenced_columns
        self.assertIn("Kind", _referenced_columns(cfg))


class TestR7GateAndLevel(Env):
    def test_changing_a_when_is_not_a_narrowing(self):
        old = cfg_of(field("A", "entity.abn", [t("abn")], when={"column": "Kind", "equals": ["ABN"]}))
        for when in ({"column": "Kind", "equals": ["ABN", "ACN"]}, None):
            new = cfg_of(field("A", "entity.abn", [t("abn")], **({"when": when} if when else {})))
            self.assertTrue(narrowing_changes(new, old), when)
        self.assertEqual(narrowing_changes(old, old), [])

    def test_level_p_for_the_new_transforms_w_for_clean_whitespace_and_a_constant_is_asserted_and_capped(self):
        src = Path(self._tmp.name) / "s.csv"
        src.write_text("Licence No,Business Name,Suburb\n" + "".join(f"L{i:05d},Company {i} Pty Ltd,Fitzroy\n" for i in range(1, 301)))
        self.start(src)
        self.call("read_table", {"format": "csv"})
        cfg = good_config()
        cfg["fields"] = [cfg["fields"][0],
                         field("Suburb", "address.state", [t("constant", "VIC")], reason="the dataset title says Victoria"),
                         field("Business Name", "entity.trading_name", [t("regex_replace", {"pattern": r"\d+", "repl": ""})])]
        cfg["unmapped"] = []
        out, _ = agent_hooks.finalise_config(cfg, self.sid, self.work, None, "v", [], [])
        name, const, repl = out["fields"]
        self.assertEqual((name["transform_level"], const["transform_level"], repl["transform_level"]), ("W", "P", "P"))
        self.assertEqual(const["evidence"], "asserted")
        self.assertLessEqual(const["field_confidence"], agent_hooks.ASSERTED_CAP)


if __name__ == "__main__":
    unittest.main()
