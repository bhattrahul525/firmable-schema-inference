"""Phase A (unattended session): the finish-rule fixes. finish validates by itself; a narrowing config needs no new critique;
the last critique says no calls remain; every refusal names the next call; critique severity; a forced end keeps advisory
fields; a forced end with no mapped field is `incomplete`. No API key, no network."""

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

import yaml

from src.part2_agent import agent_hooks
from src.part2_agent.agent_hooks import issue_id
from src.part2_agent.guard import FinishGate, narrowing_changes
from src.part2_agent.tools import ToolResult
from tests.agent_env import FakeCritic, good_config
from tests.agent_fakes import text_turn, tool_turn
from tests.test_agent_loop import Base
from tests.test_agent_wiring import Wiring, front, t, READ


def cfg(*names):
    """A small real-shaped config with one field per name."""
    return {"reader": {"format": "csv"}, "record_id": {"hash_row": True}, "observed_at": {"from_metadata": "downloaded_at"},
            "source_reliability": {"identity": 0.5}, "unmapped": [],
            "fields": [{"source": n, "canonical": f"entity.{n}", "transforms": [{"name": "clean_whitespace", "arg": ""}],
                        "group": "main", "mapping_confidence": 0.9, "reason": "r"} for n in names]}


OK = lambda c: {"hard_failures": 0, "failing_fields": []}
FAIL = lambda c: {"hard_failures": 1, "failing_fields": ["entity.b<-b"]}


def critiqued(gate, config, issues=()):
    gate.note("critique", {"config": config}, ToolResult(status={"issues": list(issues)}))


def issue(config_field, severity="advisory", n="1"):
    return {"id": f"i{n}", "field": config_field, "problem": f"p{n}", "severity": severity}


class TestFinishValidatesItself(unittest.TestCase):
    def test_no_validate_call_is_needed_and_a_failing_validate_refuses(self):
        g, c = FinishGate(), cfg("a", "b")
        critiqued(g, c)                                    # critique ran; validate was never called as a tool
        self.assertTrue(g.check({"outcome": "validated_config", "config": c}, OK).ok)
        d = g.check({"outcome": "validated_config", "config": c}, FAIL)
        self.assertFalse(d.ok)
        self.assertIn("validate fails", d.reason)
        self.assertIn("Call `validate`", d.reason)
        self.assertIn("removed from `fields` and listed in `unmapped`", d.reason)

    def test_validate_that_cannot_run_is_a_refusal_with_a_next_call(self):
        g, c = FinishGate(), cfg("a")
        critiqued(g, c)
        d = g.check({"outcome": "validated_config", "config": c}, mock.Mock(side_effect=RuntimeError("x")))
        self.assertFalse(d.ok)
        self.assertIn("Call `read_table`", d.reason)

    def test_validate_not_having_run_is_never_the_reason(self):
        g, c = FinishGate(), cfg("a")
        d = g.check({"outcome": "validated_config", "config": c}, OK, critiques_left=2)
        self.assertNotIn("validate has not run", d.reason)
        self.assertIn("`critique`", d.reason)


class TestNarrowingRule(unittest.TestCase):
    def setUp(self):
        self.gate, self.c = FinishGate(), cfg("a", "b", "c")
        critiqued(self.gate, self.c)

    def finish(self, new, left=0, **kw):
        return self.gate.check({"outcome": "validated_config", "config": new, **kw}, OK, critiques_left=left)

    def test_removing_a_field_needs_no_new_critique(self):
        self.assertTrue(self.finish(cfg("a", "b")).ok)

    def test_moving_a_column_to_unmapped_needs_no_new_critique(self):
        new = cfg("a", "b")
        new["unmapped"] = [{"source": "c", "reason": "abstained"}]
        new["needs_transform"] = [{"source": "z", "why": "w"}]
        self.assertTrue(self.finish(new).ok)

    def test_changing_confidence_or_reason_is_not_a_mapping_change(self):
        new = cfg("a", "b", "c")
        new["fields"][0]["mapping_confidence"], new["fields"][0]["reason"] = 0.2, "reworded"
        self.assertTrue(self.finish(new).ok)

    def test_adding_a_field_needs_a_critique_and_names_it(self):
        d = self.finish(cfg("a", "b", "c", "d"), left=1)
        self.assertFalse(d.ok)
        self.assertIn("entity.d<-d", d.reason)
        self.assertIn("Call `critique` with this exact config (1 critique call(s) left)", d.reason)

    def test_altering_a_transform_or_a_source_needs_a_critique(self):
        new = cfg("a", "b", "c")
        new["fields"][1]["transforms"] = [{"name": "upper", "arg": ""}]
        self.assertFalse(self.finish(new, left=1).ok)
        new = cfg("a", "b", "c")
        new["fields"][2]["source"] = "other"
        self.assertFalse(self.finish(new, left=1).ok)
        new = cfg("a", "b", "c")
        new["fields"][2]["canonical"] = "entity.something_else"                  # same column, different meaning
        d = self.finish(new, left=1)
        self.assertFalse(d.ok)
        self.assertIn("entity.something_else", d.reason)

    def test_changing_reader_record_id_or_observed_at_needs_a_critique(self):
        for key, value in (("reader", {"format": "tsv"}), ("record_id", {"from": ["a"]}),
                           ("observed_at", {"from_metadata": "dataset_modified"})):
            new = cfg("a", "b")
            new[key] = value
            d = self.finish(new, left=1)
            self.assertFalse(d.ok, key)
            self.assertIn(key, d.reason)

    def test_with_no_critique_calls_left_the_refusal_states_the_two_options(self):
        d = self.finish(cfg("a", "b", "c", "d"), left=0)
        self.assertFalse(d.ok)
        self.assertIn("no critique calls remain", d.reason)
        self.assertIn("(1) revert that change", d.reason)
        self.assertIn("(2) abstain it", d.reason)
        self.assertIn("remove them from `fields`", d.reason)

    def test_source_reliability_is_a_judgement_the_critic_never_sees_so_it_may_change(self):
        new = cfg("a", "b", "c")
        new["source_reliability"] = {"identity": 0.9, "address": 0.1}
        self.assertTrue(self.finish(new).ok)

    def test_dropping_valid_from_or_valid_to_is_a_narrowing_but_adding_or_altering_one_is_not(self):
        g, c = FinishGate(), cfg("a", "b")
        c["valid_from"] = {"source": "Start", "transforms": [{"name": "parse_date", "arg": "%d/%m/%Y"}]}
        c["valid_to"] = {"source": "End", "transforms": []}
        critiqued(g, c)
        dropped = copy.deepcopy(c)
        del dropped["valid_from"]
        dropped["valid_to"] = None
        self.assertEqual(narrowing_changes(dropped, c), [])
        self.assertTrue(g.check({"outcome": "validated_config", "config": dropped}, OK).ok)
        altered = copy.deepcopy(c)
        altered["valid_from"]["source"] = "Other"
        self.assertEqual(narrowing_changes(altered, c), ["valid_from"])
        added = cfg("a", "b")
        added["valid_from"] = {"source": "Start", "transforms": []}
        self.assertEqual(narrowing_changes(added, cfg("a", "b")), ["valid_from"])

    def test_a_refused_key_change_says_how_to_undo_it_not_to_remove_it_from_fields(self):
        g, c = FinishGate(), cfg("a", "b")
        c["valid_from"] = {"source": "Start", "transforms": []}
        critiqued(g, c)
        new = copy.deepcopy(c)
        new["valid_from"] = {"source": "Other", "transforms": []}
        new["fields"].append(cfg("z")["fields"][0])
        d = g.check({"outcome": "validated_config", "config": new}, OK, critiques_left=0)
        self.assertIn("valid_from", d.reason)
        self.assertIn("put the value back exactly as it was when last critiqued", d.reason)
        self.assertIn("delete the key", d.reason)
        self.assertIn("remove them from `fields` and list them in `unmapped`", d.reason)

    def test_transform_spelling_does_not_count_as_a_change(self):
        new = cfg("a", "b", "c")
        new["fields"][0]["transforms"] = ["clean_whitespace"]                     # a bare name instead of {name, arg}
        self.assertEqual(narrowing_changes(new, self.c), [])

    def test_issues_about_a_removed_field_no_longer_apply_but_others_do(self):
        g, c = FinishGate(), cfg("a", "b")
        critiqued(g, c, [issue("entity.a<-a", "blocking", "1"), issue("entity.b<-b", "blocking", "2"),
                         issue("observation envelope", "blocking", "3")])
        d = g.check({"outcome": "validated_config", "config": cfg("b")}, OK)
        self.assertTrue(d.ok)
        self.assertEqual(d.outcome, "partial_config")
        self.assertEqual([a["field"] for a in d.abstentions], ["entity.b<-b", "observation envelope"])   # a's issue is gone
        ans = [{"issue_id": "i2", "action": "answered", "note": "n"}, {"issue_id": "i3", "action": "answered", "note": "n"}]
        d = g.check({"outcome": "validated_config", "config": cfg("b"), "answers": ans}, OK)
        self.assertEqual((d.ok, d.outcome, d.abstentions), (True, "validated_config", []))

    def test_unanswered_advisory_issues_keep_the_field_and_are_reported_open(self):
        g, c = FinishGate(), cfg("a", "b")
        critiqued(g, c, [issue("entity.a<-a", "advisory", "1"), issue("entity.b<-b", "blocking", "2"), issue("envelope", "advisory", "3")])
        d = g.check({"outcome": "validated_config", "config": c}, OK)
        self.assertEqual((d.outcome, [a["field"] for a in d.abstentions]), ("partial_config", ["entity.b<-b"]))   # only blocking abstains
        self.assertEqual([i["id"] for i in d.open_advisory], ["i1", "i3"])
        d = g.check({"outcome": "validated_config", "config": c, "answers": [{"issue_id": "i2", "action": "answered", "note": "n"}]}, OK)
        self.assertEqual((d.ok, d.outcome, d.abstentions), (True, "validated_config", []))     # the advisory ones may stay open
        self.assertEqual(len(d.open_advisory), 2)

    def test_an_issue_without_a_severity_is_blocking_at_finish_too(self):
        g, c = FinishGate(), cfg("a")
        critiqued(g, c, [{"id": "x", "field": "entity.a<-a", "problem": "p"}])
        d = g.check({"outcome": "validated_config", "config": c}, OK)
        self.assertEqual([a["field"] for a in d.abstentions], ["entity.a<-a"])

    def test_issues_of_every_critique_a_config_narrows_accumulate(self):
        g = FinishGate()
        c1, c2 = cfg("a", "b", "c"), cfg("a", "b")
        critiqued(g, c1, [issue("entity.a<-a", "blocking", "1")])
        critiqued(g, c2, [issue("entity.b<-b", "blocking", "2")])
        d = g.check({"outcome": "validated_config", "config": cfg("a", "b")}, OK)
        self.assertEqual({a["field"] for a in d.abstentions}, {"entity.a<-a", "entity.b<-b"})


class TestEveryRefusalNamesTheNextCall(unittest.TestCase):
    def test_each_refusal_reason_contains_a_call_instruction(self):
        g, c = FinishGate(), cfg("a", "b")
        cases = [
            ({"outcome": "nonsense"}, OK, 2),
            ({"outcome": "validated_config", "config": c, "answers": "x"}, OK, 2),
            ({"outcome": "validated_config", "config": c, "abstentions": [1]}, OK, 2),
            ({"outcome": "no_business_entities", "evidence": "e"}, OK, 2),
            ({"outcome": "could_not_read", "reason": "r"}, OK, 2),
            ({"outcome": "validated_config"}, OK, 2),
            ({"outcome": "validated_config", "config": c}, FAIL, 2),
            ({"outcome": "validated_config", "config": c}, OK, 2),
            ({"outcome": "validated_config", "config": c}, OK, 0),
        ]
        for args, vfn, left in cases:
            d = g.check(args, vfn, critiques_left=left)
            if d.ok:
                continue
            self.assertRegex(d.reason, r"[Cc]all `?\w+`?|call finish again|Call finish again|no config can be finished", args)
        g.ok_tools.update({"read_table", "profile"})
        d = g.check({"outcome": "no_business_entities"}, OK)
        self.assertIn("Call finish again with `evidence`", d.reason)
        critiqued(g, c)
        d = g.check({"outcome": "partial_config", "config": c}, OK)
        self.assertIn("Call finish again with `abstentions`", d.reason)
        g.failed_reads = 1
        self.assertIn("Call `read_table` again", g.check({"outcome": "could_not_read", "reason": "r"}, OK).reason)

    def test_the_malformed_lists_refusal_shows_the_shape(self):
        d = FinishGate().check({"outcome": "validated_config", "config": cfg("a"), "answers": "x"}, OK)
        self.assertIn('"issue_id": "c-1a2b3c4d"', d.reason)
        self.assertTrue(d.format)


class TestFinishThroughTheLoop(Base):
    """The loop passes the number of critique calls left and runs the hooks' validate for finish."""

    def three_field(self, bad=()):
        return {"fields": ["a", "b", "c"], "bad": list(bad), "issues": []}

    def test_a_narrowed_config_finishes_after_the_critique_cap(self):
        full = self.three_field()
        narrow = {**full, "fields": ["a", "b"]}
        res = self.run_loop([tool_turn("critique", {"config": full}, id="c1"), tool_turn("critique", {"config": full}, id="c2"),
                             tool_turn("finish", {"outcome": "validated_config", "config": narrow}, id="f")])
        self.assertEqual(res.outcome, "validated_config", res.reason)
        self.assertEqual(self.counter.runs.get("validate", 0), 0)                # no validate TOOL call anywhere

    def test_a_changed_config_after_the_cap_is_refused_with_the_two_options(self):
        full = self.three_field()
        grown = {**full, "fields": ["a", "b", "c", "d"]}
        res = self.run_loop([tool_turn("critique", {"config": full}, id="c1"), tool_turn("critique", {"config": full}, id="c2"),
                             tool_turn("finish", {"outcome": "validated_config", "config": grown}, id="f1"),
                             tool_turn("finish", {"outcome": "validated_config", "config": full}, id="f2")])
        refusal = self.tool_results(3)[0]["content"]
        self.assertIn("Two options", refusal)
        self.assertIn("[d]", refusal)
        self.assertEqual(res.outcome, "validated_config")                         # option 1: revert; finishes

    def test_the_same_change_with_a_critique_call_left_names_the_critique_call(self):
        full = self.three_field()
        grown = {**full, "fields": ["a", "b", "c", "d"]}
        self.run_loop([tool_turn("critique", {"config": full}, id="c1"),
                       tool_turn("finish", {"outcome": "validated_config", "config": grown}, id="f1"), text_turn(), text_turn()])
        self.assertIn("Call `critique` with this exact config (1 critique call(s) left)", self.tool_results(2)[0]["content"])


class TestForcedEnd(Base):
    def forced(self, config):
        return self.run_loop([tool_turn("validate", {"config": config}, id="v"), tool_turn("critique", {"config": config}, id="c"),
                              text_turn(), text_turn()])

    def test_only_blocking_fields_are_abstained_and_advisory_fields_stay(self):
        c = {"fields": ["a", "b"], "bad": [], "issues": [issue("a", "advisory", "1"), issue("b", "blocking", "2")]}
        res = self.forced(c)
        self.assertEqual(res.outcome, "partial_config")
        self.assertEqual(res.config["fields"], ["a"])
        self.assertEqual([x["field"] for x in res.abstentions], ["b"])
        self.assertIn("blocking critique issue", res.abstentions[0]["reason"])

    def test_with_only_advisory_issues_both_fields_stay(self):
        c = {"fields": ["a", "b"], "bad": [], "issues": [issue("a", "advisory", "1"), issue("b", "advisory", "2")]}
        res = self.forced(c)
        self.assertEqual(res.outcome, "partial_config")
        self.assertEqual(res.config["fields"], ["a", "b"])
        self.assertEqual(res.abstentions, [])

    def test_an_issue_without_a_severity_counts_as_blocking(self):
        c = {"fields": ["a", "b"], "bad": [], "issues": [{"id": "x", "field": "a", "problem": "p"}]}
        self.assertEqual(self.forced(c).config["fields"], ["b"])

    def test_a_forced_end_with_no_mapped_field_is_incomplete(self):
        c = {"fields": ["a", "b"], "bad": [], "issues": [issue("a", "blocking", "1"), issue("b", "blocking", "2")]}
        res = self.forced(c)
        self.assertEqual(res.outcome, "incomplete")
        self.assertIn("no mapped field is left", res.reason)
        self.assertIsNone(res.config)

    def test_every_field_failing_validation_at_a_forced_end_is_incomplete_without_a_critique_call(self):
        c = {"fields": ["a"], "bad": ["a"], "issues": []}
        orig = self.hooks.critique
        self.hooks.critique = mock.Mock(side_effect=orig)
        res = self.run_loop([tool_turn("validate", {"config": c}, id="v"), text_turn(), text_turn()])
        self.assertEqual(res.outcome, "incomplete")
        self.assertIn("every field failed validation", res.reason)
        self.hooks.critique.assert_not_called()                                      # nothing left to critique: no model call


class TestScriptedReproductionOfTheRerun(Wiring):
    """The tool sequence of the live re-run: validate x2, critique, validate, critique, validate, a third critique (refused,
    cap 2), then finish. Before the fix it ended `partial_config` with no fields. Now both fields are kept."""

    def issues(self, *pairs):
        return [{"field": f, "severity": s, "problem": f"problem about {f}", "suggested_fix": "x"} for f, s in pairs]

    def run_it(self, finish_answers):
        base = good_config()
        base["fields"] = base["fields"][:3]                       # name, abn, state ...
        base["unmapped"] = base["unmapped"] + [{"source": "Registered", "reason": "not needed here"}]
        first = copy.deepcopy(base)                               # critique 1 flags the name mapping
        second = copy.deepcopy(base)                              # the agent re-maps (an ALTERED mapping): needs critique 2
        second["fields"][0] = {**second["fields"][0], "canonical": "entity.trading_name", "reason": "venue names"}
        third = copy.deepcopy(second)                             # then drops the abn field to unmapped (narrowing only)
        third["fields"] = [third["fields"][0], third["fields"][2]]
        third["unmapped"] = third["unmapped"] + [{"source": "ABN", "reason": "abstained"}]
        critic = FakeCritic([])
        seq = iter([self.issues(("entity.legal_name", "blocking")),
                    self.issues(("entity.trading_name", "advisory"), ("address.state", "advisory"))])
        def call(prompt, **kw):
            critic.issues = next(seq)
            return FakeCritic.__call__(critic, prompt, **kw)
        script = front() + [t("validate", {"config": first}), t("critique", {"config": first}),
                            t("validate", {"config": second}), t("critique", {"config": second}),
                            t("validate", {"config": third}), t("critique", {"config": third}),
                            t("finish", {"outcome": "validated_config", "config": third, "answers": finish_answers})]
        with mock.patch("src.part2_agent.agent_hooks.llm.call", call):
            return self.agent(script).run(), third

    def test_both_fields_are_kept_and_the_run_finishes(self):
        ids = [issue_id("entity.trading_name<-Business Name", "problem about entity.trading_name"),
               issue_id("address.state<-State", "problem about address.state")]
        res, third = self.run_it([{"issue_id": i, "action": "answered", "note": "intended"} for i in ids])
        names = [c["name"] + (" (refused)" if c.get("refused") else "") for c in self.calls()]
        self.assertEqual(names.count("critique"), 2)
        self.assertIn("critique (refused)", names)                                 # the third critique hit the cap
        refused = next(c for c in self.calls() if c.get("refused") and c["name"] == "critique")
        self.assertIn("at most 2", refused["refused"])
        self.assertEqual(res.outcome, "validated_config", res.reason)
        self.assertEqual(sorted(f["canonical"] for f in res.config["fields"]), ["address.state", "entity.trading_name"])

    def test_the_second_critique_tells_the_agent_no_calls_remain(self):
        self.run_it([])
        crit = [c for c in self.calls() if c["name"] == "critique" and not c.get("refused")]
        self.assertIn("1 critique call(s) remain", crit[0]["rendered"])
        self.assertIn("a blocking issue must be fixed or answered; an advisory one may be left", crit[0]["rendered"])
        self.assertIn("NO critique calls remain", crit[1]["rendered"])
        self.assertIn("only remove or abstain fields", crit[1]["rendered"])
        self.assertIn("answer the remaining blocking issues in `finish`", crit[1]["rendered"])

    def test_unanswered_advisory_issues_keep_both_fields_at_an_ordinary_finish(self):
        res, _ = self.run_it([])                                                    # the agent answers nothing
        self.assertEqual(res.outcome, "validated_config", res.reason)
        self.assertEqual(res.abstentions, [])
        self.assertEqual(len(res.config["fields"]), 2)
        fin = next(c for c in self.calls() if c["name"] == "finish")
        self.assertEqual(len(fin["status"]["open_advisory"]), 2)                     # recorded in the trace, shown in the packet

    def test_severity_reaches_the_gate_status_and_the_packet(self):
        res, _ = self.run_it([])
        packet = Path(res.packet_path).read_text()
        self.assertIn("[advisory]", packet)

    def test_the_packet_hook_never_creates_an_approval_file(self):
        self.run_it([])
        self.assertFalse(list(Path("configs").glob("*.approval.json")))


class TestNoConfigWithoutFields(Base):
    """Dev-draw finding (a harness defect): a config outcome that maps no field is not a config."""

    def test_the_gate_refuses_a_config_with_no_mapped_field_and_names_the_next_call(self):
        for c in (cfg(), {"reader": {}, "unmapped": []}, {"fields": "x"}):
            d = FinishGate().check({"outcome": "partial_config", "config": c, "abstentions": [{"field": "a", "reason": "r"}]}, OK, 2)
            self.assertFalse(d.ok)
            self.assertIn("maps none", d.reason)
            self.assertIn("outcome no_business_entities", d.reason)
            self.assertIn("call `validate` with a config that maps at least one field", d.reason)

    def test_no_business_entities_is_still_available_with_no_fields(self):
        g = FinishGate()
        g.ok_tools.update({"read_table", "profile"})
        self.assertTrue(g.check({"outcome": "no_business_entities", "evidence": "e"}, OK).ok)

    def test_a_finish_whose_unanswered_blocking_issues_would_remove_every_field_is_refused_not_accepted(self):
        c = {"fields": ["a", "b"], "bad": [], "issues": [issue("a", "blocking", "1"), issue("b", "blocking", "2")]}
        res = self.run_loop([tool_turn("validate", {"config": c}, id="v"), tool_turn("critique", {"config": c}, id="k"),
                             tool_turn("finish", {"outcome": "validated_config", "config": c}, id="f1"),
                             tool_turn("finish", {"outcome": "validated_config", "config": c, "answers": [
                                 {"issue_id": "1", "action": "answered", "note": "n"}, {"issue_id": "i1", "action": "answered", "note": "n"},
                                 {"issue_id": "i2", "action": "answered", "note": "n"}]}, id="f2")])
        refusal = self.tool_results(3)[0]["content"]
        self.assertIn("would leave no mapped field", refusal)
        self.assertIn("Call finish again with `answers`", refusal)
        self.assertEqual(res.outcome, "validated_config")                           # once answered, the fields stay

    def test_a_forced_end_still_uses_incomplete_for_no_fields(self):
        c = {"fields": ["a"], "bad": [], "issues": [issue("a", "blocking", "1")]}
        res = self.run_loop([tool_turn("validate", {"config": c}, id="v"), tool_turn("critique", {"config": c}, id="k"),
                             text_turn(), text_turn()])
        self.assertEqual(res.outcome, "incomplete")


class TestOutcomeDefinitions(unittest.TestCase):
    """Generic wording only: nothing here may name a dataset, a column or a value."""

    def test_prompt_and_finish_description_say_a_fix_is_not_an_abstention(self):
        from src.part2_agent.agent_prompt import SYSTEM_TASK
        from src.part2_agent.loop import FINISH_SPEC
        flat = " ".join(SYSTEM_TASK.split())
        self.assertIn("is a FIX, not an abstention", flat)
        self.assertIn("Columns left in `unmapped` with reasons are normal", flat)
        self.assertIn("because you could not get it right", flat)
        self.assertIn("do not make a config partial", flat)
        self.assertIn("dropping or re-mapping a field the critique showed was wrong is a fix", FINISH_SPEC.description)
        self.assertIn("Use validated_config when the config is complete for what the source supports", FINISH_SPEC.description)

    def test_the_task_prompt_and_tool_text_mention_no_dataset(self):
        from src.part2_agent import agent_prompt
        from src.part2_agent.loop import FINISH_SPEC
        from src.part2_agent.agent_tools import AgentKit
        text = agent_prompt.SYSTEM_TASK + FINISH_SPEC.description + "".join(t.description for t in AgentKit("x", Path("w")).tools.values())
        for word in ("LIA", "Licence Name", "Venue", "liquor", "nsw:", "find-by", "Trading Status", "Start Date"):
            self.assertNotIn(word, text, word)


class TestCritiqueSeverityPlumbing(unittest.TestCase):
    def test_the_schema_requires_a_severity_and_the_prompt_defines_both(self):
        item = agent_hooks.AGENT_CRITIQUE_SCHEMA["properties"]["issues"]["items"]
        self.assertIn("severity", item["required"])
        self.assertEqual(item["properties"]["severity"]["enum"], ["blocking", "advisory"])
        self.assertIn("BLOCKING: the mapping states something the source does not support", agent_hooks.CRITIC_SYSTEM)
        self.assertIn("ADVISORY:", agent_hooks.CRITIC_SYSTEM)
        self.assertIn("When unsure, choose advisory", agent_hooks.CRITIC_SYSTEM)


if __name__ == "__main__":
    unittest.main()
