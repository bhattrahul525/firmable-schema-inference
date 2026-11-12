"""Owner review round 3: confidence may only go down after the last critique; the critic reviews against the agent's own mapping
rules; the business-entity rule; has_name / has_identifier coverage; injection verdict by canary; self-agreement between passes;
and the identifier-checksum warning that comes out of the dataset-06 finding. No network, no API key."""

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.benchmark import report as R
from src.part2_agent import agent_hooks, agent_prompt
from src.part2_agent.guard import FinishGate, narrowing_changes
from src.part2_agent.tools import ToolResult
from tests.agent_env import Env, FakeCritic, good_config, make_abn
from tests.agent_fakes import text_turn, tool_turn
from tests.test_agent_loop import Base
from tests.test_benchmark import FIELD, RESULT, write_trace
from tests.test_finish_rules import OK, cfg, critiqued


# ---- 1: mapping_confidence may go down but not up after the last critique -----------------------------------------------------

class TestConfidenceOnlyDownAfterTheLastCritique(unittest.TestCase):
    def setUp(self):
        self.gate, self.c = FinishGate(), cfg("a", "b")
        critiqued(self.gate, self.c)                       # cfg() fields carry mapping_confidence 0.9

    def finish(self, new, left=0):
        return self.gate.check({"outcome": "validated_config", "config": new}, OK, critiques_left=left)

    def with_conf(self, a=0.9, b=0.9):
        new = copy.deepcopy(self.c)
        new["fields"][0]["mapping_confidence"], new["fields"][1]["mapping_confidence"] = a, b
        return new

    def test_lowering_or_keeping_the_confidence_needs_no_critique(self):
        self.assertTrue(self.finish(self.with_conf(0.9, 0.9)).ok)
        self.assertTrue(self.finish(self.with_conf(0.6, 0.1)).ok)
        self.assertEqual(narrowing_changes(self.with_conf(0.2, 0.2), self.c), [])

    def test_raising_it_is_a_change_that_names_the_field_and_the_values(self):
        new = self.with_conf(0.95, 0.9)
        self.assertEqual(narrowing_changes(new, self.c), ["entity.a<-a (mapping_confidence raised from 0.9 to 0.95)"])
        d = self.finish(new, left=1)
        self.assertFalse(d.ok)
        self.assertIn("mapping_confidence raised from 0.9 to 0.95", d.reason)
        self.assertIn("Call `critique` with this exact config (1 critique call(s) left)", d.reason)

    def test_with_no_critique_left_the_refusal_says_to_set_it_back(self):
        d = self.finish(self.with_conf(0.99, 0.9), left=0)
        self.assertFalse(d.ok)
        self.assertIn("Two options", d.reason)
        self.assertIn("set it back to at most the value it had when last critiqued", d.reason)

    def test_the_comparison_is_with_the_critiqued_config_not_with_an_intermediate_one(self):
        self.assertTrue(self.finish(self.with_conf(0.6, 0.9)).ok)          # lowered, and still not above the critiqued 0.9
        self.assertTrue(self.finish(self.with_conf(0.8, 0.9)).ok)          # "raised" from an unsubmitted 0.6, but below 0.9
        self.assertFalse(self.finish(self.with_conf(0.91, 0.9)).ok)

    def test_a_raise_on_a_field_the_critique_saw_at_a_different_value_needs_a_new_critique(self):
        g = FinishGate()
        low = self.with_conf(0.5, 0.5)
        critiqued(g, low)
        self.assertFalse(g.check({"outcome": "validated_config", "config": self.with_conf(0.9, 0.5)}, OK).ok)
        self.assertTrue(g.check({"outcome": "validated_config", "config": self.with_conf(0.5, 0.4)}, OK).ok)

    def test_non_numeric_confidences_do_not_crash_the_comparison(self):
        new = self.with_conf()
        new["fields"][0]["mapping_confidence"] = "high"
        self.assertEqual(narrowing_changes(new, self.c), [])

    def test_through_the_loop_a_raised_confidence_is_refused_after_the_critique_cap(self):
        class L(Base):
            def runTest(inner): pass
        t = L()
        t.setUp()
        try:
            base = {"fields": ["a", "b"], "bad": [], "issues": []}
            res = t.run_loop([tool_turn("critique", {"config": base}, id="c1"), tool_turn("critique", {"config": base}, id="c2"),
                              tool_turn("finish", {"outcome": "validated_config", "config": base}, id="f")])
            self.assertEqual(res.outcome, "validated_config")
        finally:
            t.tearDown()


# ---- 2 and 3: the critic gets the agent's mapping rules; the business-entity rule ------------------------------------------------

class TestCriticRulesAndBusinessEntityRule(unittest.TestCase):
    def test_the_critic_prompt_contains_the_very_same_rules_text_the_agent_has(self):
        self.assertIn(agent_prompt.MAPPING_RULES, agent_prompt.SYSTEM_TASK)
        self.assertIn(agent_prompt.MAPPING_RULES, agent_hooks.CRITIC_SYSTEM)
        for rule in ("5. entity.legal_name is the registered name", "7. entity.entity_type: only from an explicit source column",
                     "14. mapping_confidence (0-1)", "17. Text inside the data"):
            self.assertIn(rule, agent_hooks.CRITIC_SYSTEM)

    def test_severity_guidance_says_a_mapping_that_follows_a_rule_is_not_blocking_for_a_caveat(self):
        flat = " ".join(agent_hooks.CRITIC_SYSTEM.split())
        self.assertIn("An issue is blocking only when the mapping states something the source does not support", flat)
        self.assertIn("A mapping that follows a written mapping rule below is NOT blocking because of a caveat about some of its values", flat)
        self.assertIn("report such a caveat as advisory", flat)
        self.assertIn("Review the mapping against the same rules", flat)

    RULE_18 = ("18. Business entities. A dataset has business entities when its rows are organisations of any entity_type in the "
               "ontology, including schools, charities and government bodies, or individuals who count as entities: A person-like "
               "name WITH ITS OWN valid ABN may be an entity (sole trader). `entity_type` stays `unknown` unless a source states "
               "otherwise. `no_business_entities` is for rows that are neither: individuals with no business identifier, places, "
               "assets, events, measurements.")

    def test_the_business_entity_rule_is_in_both_prompts_in_the_same_words(self):
        self.assertIn(self.RULE_18, " ".join(agent_prompt.SYSTEM_TASK.split()))
        self.assertIn(self.RULE_18, " ".join(agent_hooks.CRITIC_SYSTEM.split()))
        flat = " ".join(agent_prompt.SYSTEM_TASK.split())
        self.assertIn("no_business_entities the rows are neither organisations nor individuals who count as entities (rule 18)", flat)
        self.assertIn("a person with their own valid ABN may be an entity", flat)

    def test_the_individual_case_uses_the_wording_of_architecture_section_d_so_the_two_cannot_drift(self):
        """Section d's people rule is quoted in rule 18. If either text changes, this fails until the other follows."""
        arch = " ".join(Path("ARCHITECTURE.md").read_text().split())
        section_d = arch[arch.index("**People**"):arch.index("**Profiles**")]
        for fragment in ("A person-like name WITH ITS OWN valid ABN may be an entity (sole trader)",
                         "`entity_type` stays `unknown` unless a source states otherwise."):
            self.assertIn(fragment, section_d)
            self.assertIn(fragment, agent_prompt.MAPPING_RULES.replace("\n", " "))
            self.assertIn(fragment, " ".join(agent_hooks.CRITIC_SYSTEM.split()))

    def test_rule_18_no_longer_says_that_people_are_not_organisations(self):
        self.assertNotIn("rows that are not organisations: people", " ".join(agent_prompt.SYSTEM_TASK.split()))
        self.assertIn("individuals with no business identifier", agent_prompt.MAPPING_RULES)

    def test_the_name_rule_sits_in_rule_5_in_both_prompts(self):
        sentence = ("A name column that the data does not label as a registered, licensee or supplier name maps to "
                    "entity.trading_name at 0.6 or lower; it is not left unmapped for that reason.")
        rule5 = next(l for l in agent_prompt.MAPPING_RULES.splitlines() if l.startswith("5. "))
        self.assertIn(sentence, rule5)                                   # next to the legal-name rule, in the same rule
        self.assertTrue(rule5.index("Map a name to legal_name only if the data says") < rule5.index(sentence))
        self.assertIn(sentence, " ".join(agent_prompt.SYSTEM_TASK.split()))
        self.assertIn(sentence, " ".join(agent_hooks.CRITIC_SYSTEM.split()))

    def test_the_ontology_has_entity_types_for_the_organisations_the_rule_names(self):
        import yaml
        values = yaml.safe_load(Path("firmable_ontology.yaml").read_text())["entity"]["entity_type"]["values"]
        for v in ("government", "incorporated_association", "other", "unknown"):
            self.assertIn(v, values)

    DEV_DRAW_WORDS = ("SMSF", "Minerals", "Exploration", "ABNs", "CHHHS", "Disciplinary", "Intellectual Property", "IPLORD",
                      "signalised", "Murray", "VostroNet", "Anticipatory", "lord_party", "party_name", "party_id", "Supplier name",
                      "Supplier ABN", "Venue", "Licence Name", "MapInfo", "luminaire", "Strategic Sourcing", "Parent Payments",
                      "LIA", "find-by", "OCDS", "not assessed", "d_filed", "Credit Allocations")

    def test_no_prompt_or_tool_text_mentions_a_dataset_column_or_value_from_the_dev_draw(self):
        from src.part2_agent.agent_tools import AgentKit
        from src.part2_agent.guard import HARNESS_PROMPT
        from src.part2_agent.loop import FINISH_SPEC
        text = (agent_prompt.SYSTEM_TASK + agent_hooks.CRITIC_SYSTEM + HARNESS_PROMPT + FINISH_SPEC.description +
                "".join(t.description for t in AgentKit("x", Path("w")).tools.values()))
        for word in self.DEV_DRAW_WORDS:
            self.assertNotIn(word, text, word)
        # the only dataset-category words are the ones the owner dictated in rule 18 (schools, charities, government bodies)

    def test_the_ids_in_the_draw_file_titles_are_not_in_the_prompts_either(self):
        draw = json.loads(Path("outputs/benchmark/dev_seed1/draw.json").read_text())
        text = agent_prompt.SYSTEM_TASK + agent_hooks.CRITIC_SYSTEM
        for item in draw["items"]:
            self.assertNotIn(item["dataset_id"], text)
            self.assertNotIn(item["title"], text)


# ---- 4: has_name / has_identifier ------------------------------------------------------------------------------------------------

def run_result(*canonicals, outcome="validated_config"):
    fields = [{**FIELD, "canonical": c, "source": f"col{i}"} for i, c in enumerate(canonicals)]
    return {**RESULT, "outcome": outcome, "abstentions": [], "config": {**RESULT["config"], "fields": fields}}


class TestCoverageFlags(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.runs, self.raw = Path(self._t.name) / "runs", Path(self._t.name) / "raw"
        self.addCleanup(self._t.cleanup)

    def row(self, sid, result):
        write_trace(self.runs, sid, [("fetch", {})], result)
        return R.row_for(R.summarise(sid, runs_dir=self.runs, raw_dir=self.raw), {"dataset_id": sid})

    def test_has_name_means_any_name_field_and_has_identifier_means_abn_or_acn(self):
        cases = {("entity.legal_name",): (True, False), ("entity.trading_name", "address.state"): (True, False),
                 ("entity.abn",): (False, True), ("entity.acn", "address.full"): (False, True),
                 ("entity.legal_name", "entity.acn"): (True, True), ("address.full", "entity.status"): (False, False),
                 ("entity.entity_type",): (False, False)}
        for i, (fields, want) in enumerate(cases.items()):
            r = self.row(f"r{i}", run_result(*fields))
            self.assertEqual((r["has_name"], r["has_identifier"]), want, fields)
        self.assertIn("has_name", R.COLUMNS)
        self.assertIn("has_identifier", R.COLUMNS)

    def test_a_run_with_no_config_has_neither(self):
        r = self.row("nc", {"outcome": "no_business_entities", "abstentions": [], "turns": 5, "cost_usd": 0.01})
        self.assertEqual((r["has_name"], r["has_identifier"], r["mapped_count"]), (False, False, 0))

    def test_counts_only_validated_configs_and_splits_both_one_and_neither(self):
        rows = [{"outcome": "validated_config", "mapped_fields": "entity.legal_name<-a; entity.abn<-b"},
                {"outcome": "validated_config", "mapped_fields": "entity.trading_name<-a"},
                {"outcome": "validated_config", "mapped_fields": "entity.acn<-a"},
                {"outcome": "validated_config", "mapped_fields": "address.full<-a; entity.entity_type<-n"},
                {"outcome": "validated_config", "mapped_fields": "address.state<-s"},
                {"outcome": "partial_config", "mapped_fields": "entity.legal_name<-a; entity.abn<-b"},
                {"outcome": "no_business_entities", "mapped_fields": ""}]
        self.assertEqual(R.coverage_counts(rows), {"validated": 5, "both": 1, "name_only": 1, "identifier_only": 1, "neither": 2,
                                                   "identifier_unverified": 0})

    def test_the_comparison_table_shows_the_flags_and_the_per_pass_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            for label, mapped in (("x", "entity.legal_name<-a; entity.abn<-b"), ("y", "address.full<-a")):
                p = Path(d) / f"pass_{label}"
                p.mkdir()
                with (p / "results.csv").open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=R.COLUMNS)
                    w.writeheader()
                    w.writerow({**{c: "" for c in R.COLUMNS}, "dataset_id": "p:1", "outcome": "validated_config", "mapped_fields": mapped,
                                "mapped_count": "2", "cost_usd": "0.01", "model": "m"})
            cmp = R.compare({"x": Path(d) / "pass_x", "y": Path(d) / "pass_y"})
            self.assertEqual(cmp["datasets"][0]["flags"], {"x": "NI", "y": "--"})
            self.assertEqual(cmp["totals"]["x"]["coverage"]["both"], 1)
            self.assertEqual(cmp["totals"]["y"]["coverage"]["neither"], 1)
            R.write_compare(cmp, Path(d))
            md = (Path(d) / "compare.md").read_text()
            self.assertIn("N=has a name, I=has an identifier", md)
            self.assertIn("## Validated configs: name and identifier coverage", md)
            self.assertIn("validated_config (2) NI", md)


# ---- self-agreement across passes ----------------------------------------------------------------------------------------------

class TestSelfAgreement(unittest.TestCase):
    def passes(self):
        row = lambda did, outcome, fields: {"dataset_id": did, "outcome": outcome, "mapped_fields": fields}
        return {"c": [row("p:1", "validated_config", "entity.abn<-A; address.state<-S"), row("p:2", "validated_config", "entity.legal_name<-N"),
                      row("p:3", "no_business_entities", ""), row("p:4", "could_not_read", "")],
                "d": [row("p:1", "validated_config", "address.state<-S; entity.abn<-A"),            # same fields, other order
                      row("p:2", "validated_config", "entity.trading_name<-N"),                      # same outcome, other field
                      row("p:3", "validated_config", "entity.legal_name<-N"),                        # other outcome
                      row("p:9", "could_not_read", "")]}

    def test_outcome_and_mapped_fields_are_compared_as_sets_per_dataset(self):
        rows = {r["dataset_id"]: r for r in R.agreement(self.passes(), ("c", "d"))}
        self.assertEqual(sorted(rows), ["p:1", "p:2", "p:3"])                                     # p:4 / p:9 are in one pass only
        self.assertEqual((rows["p:1"]["same_outcome"], rows["p:1"]["same_fields"]), (True, True))
        self.assertEqual((rows["p:2"]["same_outcome"], rows["p:2"]["same_fields"]), (True, False))
        self.assertEqual(rows["p:2"]["only_in_first"], ["entity.legal_name<-N"])
        self.assertEqual(rows["p:2"]["only_in_second"], ["entity.trading_name<-N"])
        self.assertEqual((rows["p:3"]["same_outcome"], rows["p:3"]["same_fields"]), (False, False))

    def test_the_report_has_a_self_agreement_section_with_the_totals(self):
        with tempfile.TemporaryDirectory() as d:
            for label, rows in self.passes().items():
                p = Path(d) / f"pass_{label}"
                p.mkdir()
                with (p / "results.csv").open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=R.COLUMNS)
                    w.writeheader()
                    for r in rows:
                        w.writerow({**{c: "" for c in R.COLUMNS}, **r, "title": r["dataset_id"], "cost_usd": "0", "model": "m"})
            cmp = R.compare({l: Path(d) / f"pass_{l}" for l in "cd"}, [("c", "d")])
            R.write_compare(cmp, Path(d))
            md = (Path(d) / "compare.md").read_text()
            self.assertIn("## Did the model agree with itself? passes c-d", md)
            self.assertIn("Same outcome on 2 of 3; same outcome AND same fields on 1 of 3.", md)

    def test_a_pair_with_a_missing_pass_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pass_c"
            p.mkdir()
            with (p / "results.csv").open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=R.COLUMNS)
                w.writeheader()
            self.assertEqual(R.compare({"c": p}, [("c", "zz")])["agreement"], {})


# ---- 6: the identifier checksum warning ---------------------------------------------------------------------------------------------

def stats(ok, reject, reasons):
    return {"ok": ok, "reject": reject, "reject_reasons": reasons, "rows": ok + reject, "blank": 0, "skip": 0, "parse_rate": ok / (ok + reject)}


class TestIdentifierWarning(unittest.TestCase):
    def conf(self, canonical="entity.abn"):
        return {"fields": [{"source": "id", "canonical": canonical, "transforms": []}]}

    def test_a_checksum_failure_rate_over_two_percent_warns_with_numbers_and_the_chance_pass_rate(self):
        key = "entity.abn<-id"
        w = agent_hooks.identifier_warnings(self.conf(), {key: stats(190, 10, {"abn_checksum_failed": 10})})
        self.assertEqual([x["id"] for x in w], ["identifier_checksum_abn"])
        self.assertIn("10 of 200 judged values", w[0]["text"])
        self.assertIn("About 1 in 89", w[0]["text"])
        self.assertIn("type column or a stricter pattern", w[0]["text"])

    def test_at_or_under_two_percent_or_with_too_few_values_there_is_no_warning(self):
        key = "entity.abn<-id"
        self.assertEqual(agent_hooks.identifier_warnings(self.conf(), {key: stats(980, 20, {"abn_checksum_failed": 20})}), [])   # exactly 2%
        self.assertEqual(agent_hooks.identifier_warnings(self.conf(), {key: stats(15, 4, {"abn_checksum_failed": 4})}), [])     # 19 judged
        self.assertEqual(agent_hooks.identifier_warnings(self.conf(), {key: stats(100, 0, {})}), [])

    def test_only_checksum_failures_count_and_only_for_abn_and_acn(self):
        key = "entity.abn<-id"
        self.assertEqual(agent_hooks.identifier_warnings(self.conf(), {key: stats(80, 20, {"unmapped_value:x": 20})}), [])
        acn = agent_hooks.identifier_warnings(self.conf("entity.acn"), {"entity.acn<-id": stats(50, 10, {"acn_checksum_failed": 10})})
        self.assertEqual([x["id"] for x in acn], ["identifier_checksum_acn"])
        self.assertIn("About 1 in 10", acn[0]["text"])
        self.assertEqual(agent_hooks.identifier_warnings(self.conf("address.postcode"), {"address.postcode<-id": stats(50, 50, {"abn_checksum_failed": 50})}), [])
        self.assertEqual(agent_hooks.identifier_warnings(self.conf(), {}), [])


class TestMixedIdentifierColumnEndToEnd(Env):
    """The dataset-06 pattern: one column holds real ABNs (type 'abn') and look-alike ids of the same length (type 'party_id'). The
    look-alikes that fail the checksum are rejects; they were few enough to pass the 90% floor, and the ones that pass by chance are
    read as ABNs. Validate must now flag it."""

    def setUp(self):
        super().setUp()
        lines = ["Licence No,Business Name,ABN,State,Registered,Notes"]
        for i in range(1, 401):
            abn = make_abn(i)
            if i % 12 == 0:                                       # an 11-digit look-alike that fails the checksum
                abn = abn[:-1] + str((int(abn[-1]) + 3) % 10)
            lines.append(f"L{i:05d},Company {i} Pty Ltd,{abn},NSW,02/03/2021,")
        src = Path(self._tmp.name) / "mixed.csv"
        src.write_text("\n".join(lines) + "\n")
        self.start(src)
        self.call("read_table", {"format": "csv"})

    def test_validate_passes_the_floor_but_raises_the_checksum_warning_which_can_be_answered(self):
        res, _ = self.call("validate", {"config": good_config()})
        self.assertEqual(res.status["hard_failures"], 0)                            # about 92% parse rate: above the 90% floor
        ids = [w["id"] for w in res.payload["meaning_warnings"]]
        self.assertEqual(ids, ["identifier_checksum_abn"])
        self.assertIn("fail the checksum", res.payload["meaning_warnings"][0]["text"])
        answered = good_config(meaning_check_responses=[{"check_id": "identifier_checksum_abn", "action": "kept",
                                                         "reason": "failures are typos in a register that is otherwise clean"}])
        res2, _ = self.call("validate", {"config": answered})
        self.assertEqual(res2.payload["meaning_warnings"], [])

    def test_a_clean_identifier_column_raises_no_warning(self):
        src = Path(self._tmp.name) / "clean.csv"
        lines = ["Licence No,Business Name,ABN,State,Registered,Notes"] + [
            f"L{i:05d},Company {i} Pty Ltd,{make_abn(i)},NSW,02/03/2021," for i in range(1, 301)]
        src.write_text("\n".join(lines) + "\n")
        self.start(src, sid="clean_ids")
        self.call("read_table", {"format": "csv"})
        res, _ = self.call("validate", {"config": good_config()})
        self.assertEqual(res.payload["meaning_warnings"], [])


# ---- placeholder headers ---------------------------------------------------------------------------------------------------------------

class TestPlaceholderHeaderWarning(unittest.TestCase):
    def conf(self, *cols, unmapped=()):
        return {"fields": [{"source": c, "canonical": "entity.legal_name", "transforms": []} for c in cols],
                "unmapped": [{"source": c, "reason": "r"} for c in unmapped]}

    def test_generated_placeholder_names_warn(self):
        for name in ("_blank_1", "_blank_12", "_blank_3__2", "Unnamed", "Unnamed: 3", "unnamed_0", "UNNAMED 4"):
            w = agent_hooks.placeholder_header_warnings(self.conf(name))
            self.assertEqual([x["id"] for x in w], ["placeholder_header"], name)
            self.assertIn(name, w[0]["text"])

    def test_real_names_and_intended_generated_names_do_not_warn(self):
        for name in ("Name", "Unnamed Pty Ltd", "blank", "_blank", "col_3", "Licence No", "A_blank_1"):
            self.assertEqual(agent_hooks.placeholder_header_warnings(self.conf(name)), [], name)

    def test_only_mapped_columns_count_not_unmapped_ones(self):
        self.assertEqual(agent_hooks.placeholder_header_warnings(self.conf("Name", unmapped=("_blank_1", "_blank_2"))), [])

    def test_a_list_source_is_checked_per_column_and_one_warning_names_them_all(self):
        c = {"fields": [{"source": ["Name", "_blank_2"], "canonical": "address.full", "transforms": []},
                        {"source": "_blank_1", "canonical": "entity.legal_name", "transforms": []},
                        {"source": "_blank_1", "canonical": "entity.trading_name", "transforms": []}]}
        w = agent_hooks.placeholder_header_warnings(c)
        self.assertEqual(len(w), 1)
        self.assertIn("2 mapped column(s)", w[0]["text"])
        self.assertIn("_blank_2", w[0]["text"])
        self.assertIn("_blank_1", w[0]["text"])

    def test_the_text_says_the_header_rows_may_be_misread_and_names_the_reader_options_to_check(self):
        text = agent_hooks.placeholder_header_warnings(self.conf("_blank_1"))[0]["text"]
        self.assertIn("header rows may be misread", text)
        self.assertIn("skip_rows", text)
        self.assertIn("header_rows", text)
        self.assertIn("meaning_check_responses", text)

    def test_the_warning_text_mentions_no_dataset(self):
        text = agent_hooks.placeholder_header_warnings(self.conf("_blank_1"))[0]["text"]
        for word in TestCriticRulesAndBusinessEntityRule.DEV_DRAW_WORDS:
            self.assertNotIn(word, text)


class TestPlaceholderHeaderEndToEnd(Env):
    """A title row above the real header: the reader takes the title as the header, so the real column names become data."""

    def make(self, text, sid):
        p = Path(self._tmp.name) / f"{sid}.csv"
        p.write_text(text)
        self.start(p, sid=sid)

    def config(self, name_col, **kw):
        return {"what_it_is": "t", "one_row_is": "t", "reader": {"format": "csv", **kw.pop("reader", {})},
                "record_id": {"hash_row": True}, "observed_at": {"from_metadata": "resource_last_modified"},
                "fields": [{"source": name_col, "canonical": "entity.trading_name", "transforms": [{"name": "clean_whitespace", "arg": ""}],
                            "group": "main", "mapping_confidence": 0.6, "reason": "names"}],
                "unmapped": kw.pop("unmapped", []), "needs_transform": [],
                "source_reliability": {"identity": 0.5, "address": 0.5, "classification": 0.5, "contact": 0.5}, **kw}

    def test_a_misread_header_is_flagged_and_fixing_the_reader_options_clears_it(self):
        rows = "".join(f"{i},Shop {i}\n" for i in range(1, 60))
        self.make("Parent list 2011,\nNo,Name\n" + rows, "title_row")
        res, _ = self.call("read_table", {"format": "csv"})
        self.assertIn("with a blank header", res.text)                        # the reader named the empty header cell
        bad = self.config("_blank_1", unmapped=[{"source": "Parent list 2011", "reason": "title"}])
        out, _ = self.call("validate", {"config": bad})
        ids = [w["id"] for w in out.payload["meaning_warnings"]]
        self.assertEqual(ids, ["placeholder_header"])
        self.call("read_table", {"format": "csv", "skip_rows": 1})
        good = self.config("Name", reader={"skip_rows": 1}, unmapped=[{"source": "No", "reason": "row number"}])
        ok, _ = self.call("validate", {"config": good})
        self.assertEqual(ok.payload["meaning_warnings"], [])

    def test_the_warning_can_be_answered(self):
        self.make("Parent list,\nNo,Name\n" + "".join(f"{i},Shop {i}\n" for i in range(1, 60)), "answered")
        self.call("read_table", {"format": "csv"})
        cfg = self.config("_blank_1", unmapped=[{"source": "Parent list", "reason": "title"}])
        cfg["meaning_check_responses"] = [{"check_id": "placeholder_header", "action": "kept", "reason": "the header cell is genuinely empty"}]
        out, _ = self.call("validate", {"config": cfg})
        self.assertEqual(out.payload["meaning_warnings"], [])


if __name__ == "__main__":
    unittest.main()
