"""The round-2 agent loop (ARCHITECTURE.md section b).

    system prompt -> model picks ONE tool -> harness runs it -> capped result back -> repeat until a terminal outcome

The model decides what to investigate. The harness (guard.py) decides everything about safety: budgets, the finish
gate, the fetch rule, output caps. This file wires them together and keeps the trace.

Trace, replay, resume. Every model turn and tool call is appended to logs/agent_runs/<source_id>/trace.jsonl, whose
first line is a HEADER: the reference, the input file's SHA-256 (when known), the model and the code version. Running
the same source again REPLAYS the trace: recorded model turns and tool results are fed back through the same code path
without calling the model or re-running tools, so a run that died resumes where it stopped and a finished run returns
its recorded result. Resuming is REFUSED (TraceMismatch) if the header does not match this run, or if the model or the
tools ever produce something different from the trace. We never "cut the tail and carry on live": a trace is evidence of
one specific run. Everything replayed is announced with a REPLAY label and marked by a `resume` event in the trace.

Transient API errors (rate limit, overloaded, timeout, connection) are retried with backoff, at most 3 attempts, each
attempt recorded as an `api_retry` event. Any other error propagates, and re-running resumes from the trace.

`chat`, `clock`, `sleep` and `say` are injectable so every rule is tested with a fake model, a fake clock and no API key.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src import llm
from src.part2_agent.guard import (ALL_OUTCOMES, CONFIG_OUTCOMES, HARNESS_PROMPT, INCOMPLETE, OUTCOMES, Budget,
                                   FetchGuard, FinishGate, Limits, render_result, validate_args)
from src.part2_agent.tools import ToolContext, ToolResult, ToolSpec

RUNS_DIR = Path("logs/agent_runs")
FINISH_REFUSALS_ALLOWED = 2   # a second consecutive refusal ends the run (partial config, or incomplete)
TEXT_ONLY_ALLOWED = 2         # two replies without a tool call in a row end the run the same way
RETRY_ATTEMPTS = 3            # transient API errors: at most 3 attempts in all
RETRY_BACKOFF_SECONDS = 2.0   # waits 2 s, then 4 s
_SKIP_ON_REPLAY = ("resume", "api_retry")   # bookkeeping events: replay steps over them


def _code_version() -> str:
    """Hash of the agent's own source files. Part of the trace header, so a trace is never resumed by different code."""
    root = Path(__file__).resolve().parent
    files = [Path(llm.__file__), root / "loop.py", root / "guard.py", root / "tools.py"]
    return hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()[:12]


CODE_VERSION = _code_version()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class TraceMismatch(ValueError):
    """The trace on disk does not belong to this run. We refuse rather than guess."""


FINISH_SPEC = ToolSpec(
    name="finish",
    description=("Declare the outcome and end the run. Outcomes: validated_config, partial_config, no_business_entities, "
                 "could_not_read. For a config outcome pass the exact `config` you validated and critiqued, and in "
                 "`answers` answer every critique issue still open on it."),
    input_schema={
        "type": "object", "additionalProperties": False, "required": ["outcome"],
        "properties": {
            "outcome": {"type": "string", "enum": list(OUTCOMES)},
            "config": {"type": "object"},
            "answers": {"type": "array"},        # [{issue_id, action: "answered", note}]
            "abstentions": {"type": "array"},    # [{field, reason}]
            "evidence": {"type": "string"},      # no_business_entities: what the data shows
            "reason": {"type": "string"},        # could_not_read: why
        }},
    run=lambda args, ctx: ToolResult(),          # never executed: the loop handles finish through the gate
)


@dataclass
class RunResult:
    outcome: str                       # one of ALL_OUTCOMES (the fifth, "incomplete", is harness-only)
    config: dict | None = None
    abstentions: list[dict] = field(default_factory=list)
    evidence: str = ""
    reason: str = ""
    forced_by: str | None = None       # set when the HARNESS ended the run (budget, repeated refusals, ...)
    turns: int = 0                     # model turns used: this is what the 40-call budget counts
    tool_calls: int = 0                # tool calls actually executed
    cost_usd: float = 0.0
    elapsed_seconds: float = 0.0
    packet_path: str | None = None
    replayed: bool = False             # True when the whole result came from a finished trace
    replayed_turns: int = 0            # model turns that were replayed from the trace, not live


@dataclass
class FinaliseHooks:
    """What the harness needs from the rest of the system to end a run by itself. Build step 2 supplies real ones.
      validate(config) -> {"hard_failures": int, "failing_fields": [...]}
      critique(config) -> {"issues": [{"id", "field", "problem"}], "cost_usd": float (optional)}
      abstain(config, fields) -> a config with those fields moved to 'unmapped' (code, never the model)
      packet(result) -> path of the written review packet, or None"""
    validate: Callable[[dict], dict]
    critique: Callable[[dict], dict]
    abstain: Callable[[dict, list], dict]
    packet: Callable[[RunResult], str | None]


class Trace:
    """Append-only JSONL trace plus replay cursor. Every line is passed through llm.redact: the API key and request
    headers can never reach this file, whatever a tool result or the model happens to contain."""

    def __init__(self, path: Path):
        self.path = path
        self.events: list[dict] = []
        if path.exists():
            self.events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.cursor = 0   # next event to replay

    def completed(self) -> dict | None:
        return next((e for e in self.events if e["type"] == "run_end"), None)

    def _skip_bookkeeping(self) -> None:
        while self.cursor < len(self.events) and self.events[self.cursor]["type"] in _SKIP_ON_REPLAY:
            self.cursor += 1

    def replaying(self) -> bool:
        self._skip_bookkeeping()
        return self.cursor < len(self.events)

    def peek(self, kind: str) -> dict | None:
        if self.replaying() and self.events[self.cursor]["type"] == kind:
            return self.events[self.cursor]
        return None

    def next_type(self) -> str | None:
        return self.events[self.cursor]["type"] if self.replaying() else None

    def consume(self) -> dict:
        ev = self.events[self.cursor]
        self.cursor += 1
        return ev

    def append(self, kind: str, **data) -> None:
        ev = {"seq": len(self.events), "ts": datetime.now(timezone.utc).isoformat(), "type": kind, **data}
        self.events.append(ev)
        self.cursor = len(self.events)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(llm.redact(json.dumps(ev, default=str)) + "\n")


class AgentRun:
    def __init__(self, *, source_id: str, reference: str, task: str, tools: dict[str, ToolSpec], hooks: FinaliseHooks,
                 system: str = "", chat: Callable = llm.chat, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, say: Callable[[str], None] = print,
                 limits: Limits = Limits(), trace_root: Path = RUNS_DIR, model: str | None = None,
                 max_tokens: int = 4096, input_path: Path | None = None, fetcher: FetchGuard | None = None,
                 code_version: str = CODE_VERSION):
        if "finish" in tools:
            raise ValueError("`finish` is owned by the harness; do not register a tool with that name")
        self.source_id, self.reference, self.task, self.hooks = source_id, reference, task, hooks
        self.tools = {**tools, "finish": FINISH_SPEC}
        self.system = HARNESS_PROMPT + ("\n" + system if system else "")
        self.chat, self.model, self.max_tokens, self.sleep, self.say = chat, model, max_tokens, sleep, say
        self.input_path, self.code_version = input_path, code_version
        self.budget = Budget(limits, clock)
        self.gate = FinishGate()
        self.fetch_guard = fetcher or FetchGuard(reference)
        self.trace = Trace(trace_root / source_id / "trace.jsonl")
        self.ctx = ToolContext(source_id=source_id, reference=reference, work_dir=trace_root / source_id,
                               fetcher=self.fetch_guard)
        self.uses: Counter = Counter()
        self.executed = 0
        self.refused_finishes = 0
        self.text_only = 0
        self.replayed_events = 0
        self.replayed_turns = 0
        self._resume_marked = False
        self.pinned_input: str | None = None
        self.messages: list[dict] = [{"role": "user", "content": task}]
        self.tool_schemas = [t.api_schema() for t in self.tools.values()]
        self.clock = clock

    # ---- public ----------------------------------------------------------------------------------------------------

    def run(self) -> RunResult:
        self._open_trace()
        done = self.trace.completed()
        if done:   # a finished trace: return its result, no model, no tools
            self.say("=== REPLAY: this run already finished; returning the recorded result "
                     "(no model calls, no tools executed) ===")
            turns = sum(1 for e in self.trace.events if e["type"] == "model_turn")
            return RunResult(**{**done["result"], "replayed": True, "replayed_turns": turns})
        if self.trace.replaying():
            n = sum(1 for e in self.trace.events if e["type"] in ("model_turn", "tool_call"))
            self.say(f"=== REPLAY: resuming from {self.trace.path} ({n} recorded model turns and tool calls; "
                     f"they are NOT live) ===")

        while True:
            why = self.budget.exhausted()
            if why:
                return self._force(f"budget exhausted: {why}")
            turn = self._model_turn(self.max_tokens)
            if turn.stop_reason == "max_tokens":   # may hold a cut-off tool call: retry once with more room
                turn = self._model_turn(self.max_tokens * 2)
                if turn.stop_reason == "max_tokens":
                    return self._force("model output hit max_tokens twice")
            if turn.stop_reason in ("refusal", "model_context_window_exceeded"):
                return self._force(f"model stopped with {turn.stop_reason}")
            blocks = llm.request_blocks(turn.content) or [{"type": "text", "text": "(no output)"}]
            self.messages.append({"role": "assistant", "content": blocks})
            why = self.budget.exhausted()
            if why:   # this turn used the last of the budget: do not run its tool
                return self._force(f"budget exhausted: {why}")

            tool_uses = turn.tool_uses
            if not tool_uses:
                self.text_only += 1
                if self.text_only >= TEXT_ONLY_ALLOWED:
                    return self._force("model replied without a tool call twice in a row")
                self.messages.append({"role": "user", "content": "Call a tool now. To end the run, call `finish`."})
                continue
            self.text_only = 0

            results, final = [], None
            for i, tu in enumerate(tool_uses):
                if i == 0:
                    content, is_error, final = self._handle(tu)
                else:   # one call per turn; every tool_use id must still be answered
                    content, is_error = "only one tool call per turn: this call was ignored; call it again next turn", True
                block = {"type": "tool_result", "tool_use_id": tu["id"], "content": content}
                if is_error:
                    block["is_error"] = True
                results.append(block)
            if final is not None:
                return final
            notice = self._notice()
            if notice:   # inside the last tool_result: text AFTER tool results can produce an empty reply
                results[-1]["content"] += "\n" + notice
            self.messages.append({"role": "user", "content": results})

    # ---- trace header and replay bookkeeping -------------------------------------------------------------------------

    def _header(self) -> dict:
        return {"source_id": self.source_id, "reference": self.reference, "model": self.model or llm.DEFAULT_MODEL,
                "code_version": self.code_version,
                "input_sha256": file_sha256(self.input_path) if self.input_path and self.input_path.exists() else None}

    def _open_trace(self) -> None:
        mine = self._header()
        if not self.trace.events:
            self.trace.append("trace_header", **mine, limits=asdict(self.budget.limits))
            return
        first = self.trace.events[0]
        if first["type"] != "trace_header":
            raise TraceMismatch(f"{self.trace.path} has no header line; refusing to resume it. Delete it to start over.")
        diffs = [f"{k}: trace has {first.get(k)!r}, this run has {mine[k]!r}" for k in mine if first.get(k) != mine[k]]
        if diffs:
            raise TraceMismatch("refusing to resume: the trace was made by a different run (" + "; ".join(diffs) +
                                f"). Delete {self.trace.path} to start a new run.")
        self.trace.cursor = 1

    def _live(self, kind: str, **data) -> None:
        """Append a live event. The first live event after replaying marks the join with a `resume` event."""
        if self.replayed_events and not self._resume_marked:
            self._resume_marked = True
            self.trace.append("resume", replayed_events=self.replayed_events, replayed_turns=self.replayed_turns)
            self.say("=== REPLAY ended: continuing live ===")
        self.trace.append(kind, **data)

    def _mismatch(self, expected: str) -> TraceMismatch:
        return TraceMismatch(f"the trace and this run disagree at event {self.trace.cursor}: the run needs {expected} "
                             f"but the trace has {self.trace.next_type()!r} (or different content). Refusing to "
                             f"continue; delete {self.trace.path} to start over.")

    # ---- one model turn (replayed or live) ----------------------------------------------------------------------------

    def _model_turn(self, max_tokens: int) -> llm.LLMTurn:
        if self.trace.replaying():
            ev = self.trace.peek("model_turn")
            if not ev:
                raise self._mismatch("a model turn")
            self.trace.consume()
            self.replayed_events += 1
            self.replayed_turns += 1
            turn = llm.LLMTurn(**{k: ev[k] for k in llm.LLMTurn.__dataclass_fields__})
            self.budget.replayed_seconds += turn.seconds
            names = [b["name"] for b in turn.tool_uses] or ["(text only)"]
            self.say(f"[REPLAY] turn {self.replayed_turns}: {', '.join(names)}")
        else:
            turn = self._chat_with_retries(max_tokens)
            self._live("model_turn", **asdict(turn))
        self.budget.calls += 1          # EVERY model turn counts against the budget, text-only ones included
        self.budget.dollars += turn.cost_usd
        return turn

    def _chat_with_retries(self, max_tokens: int) -> llm.LLMTurn:
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                return self.chat(list(self.messages), step="agent.turn", source_id=self.source_id, system=self.system,
                                 tools=self.tool_schemas, model=self.model, max_tokens=max_tokens)
            except Exception as e:
                if not llm.is_transient(e):
                    raise
                will_retry = attempt < RETRY_ATTEMPTS
                wait = RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1) if will_retry else 0.0
                self._live("api_retry", attempt=attempt, error_type=type(e).__name__, error=str(e)[:300],
                           will_retry=will_retry, wait_seconds=wait)
                if not will_retry:
                    raise
                self.sleep(wait)
        raise AssertionError("unreachable")

    # ---- one tool call ----------------------------------------------------------------------------------------------

    def _handle(self, tu: dict) -> tuple[str, bool, RunResult | None]:
        """Returns (text for the model, is_error, final RunResult if the run ends here)."""
        name, args = tu["name"], tu["input"]
        if self.trace.replaying():
            ev = self.trace.peek("tool_call")
            if not ev or ev["name"] != name or ev["args"] != args:
                raise self._mismatch(f"the tool call {name}({json.dumps(args)[:80]})")
            self.trace.consume()
            self.replayed_events += 1
            result = ToolResult(status=ev["status"], is_error=ev["is_error"], cost_usd=ev["cost_usd"],
                                download_seconds=ev["download_seconds"])
            rendered, seconds, refused = ev["rendered"], ev["seconds"], ev["refused"]
            self.budget.replayed_seconds += seconds
            pinned = self.trace.peek("input_pinned")
            if pinned:
                self.trace.consume()
                self.pinned_input = self.ctx.state["input_sha256"] = pinned["sha256"]
        else:
            t0 = self.clock()
            result, rendered, refused = self._execute(name, args)
            seconds = self.clock() - t0 - result.download_seconds
            self._live("tool_call", tool_use_id=tu["id"], name=name, args=args, is_error=result.is_error,
                       status=result.status, rendered=rendered, cost_usd=result.cost_usd,
                       download_seconds=result.download_seconds, seconds=seconds, refused=refused)
            self._pin_input()

        self.executed += 1
        self.budget.dollars += result.cost_usd
        self.budget.download_seconds += result.download_seconds
        if refused is None:
            self.uses[name] += 1
            if name != "finish":
                self.gate.note(name, args, result)
        if name == "finish":
            return self._after_finish(args, result, rendered)
        self.refused_finishes = 0   # "in a row": any other tool call resets the count
        return rendered, result.is_error, None

    def _pin_input(self) -> None:
        """Once a tool has put the input file's SHA-256 in ctx.state, pin it in the trace. If a later tool reports a
        DIFFERENT hash the input changed under us (e.g. a live register re-downloaded): refuse to go on."""
        sha = self.ctx.state.get("input_sha256")
        if not sha or sha == self.pinned_input:
            return
        if self.pinned_input:
            raise TraceMismatch(f"the input file changed during the run (pinned {self.pinned_input[:12]}, now {sha[:12]})")
        self.pinned_input = sha
        self._live("input_pinned", sha256=sha)

    def _execute(self, name: str, args: dict) -> tuple[ToolResult, str, str | None]:
        """Run the pre-checks, then the tool. Returns (result, text for the model, refusal reason or None)."""
        spec = self.tools.get(name)
        if spec is None:
            return self._refuse(f"unknown tool {name!r}; available: {sorted(self.tools)}")
        if name == "fetch":   # checked first: the model never supplies a URL, whatever the tool's own schema says
            bad = self.fetch_guard.check_args(args)
            if bad:
                return self._refuse(bad)
        bad = validate_args(spec.input_schema, args)
        if bad:
            return self._refuse(f"bad arguments for {name}: {bad}")
        if spec.max_uses is not None and self.uses[name] >= spec.max_uses:
            return self._refuse(f"{name} may be used at most {spec.max_uses} times per run and that limit is reached")
        if name in ("validate", "critique") and not isinstance(args.get("config"), dict):
            return self._refuse(f"{name} needs a `config` object")
        if name == "finish":
            decision = self.gate.check(args)
            if not decision.ok:
                return self._refuse(decision.reason)
            return ToolResult(status={"accepted": True, "outcome": decision.outcome,
                                      "abstentions": decision.abstentions}), "accepted", None
        try:
            result = spec.run(args, self.ctx)
        except Exception as e:   # a tool crash is an error result, never a crashed run; no stack trace to the model
            result = ToolResult(text=f"{type(e).__name__}: {str(e)[:300]}", is_error=True)
        return result, render_result(spec, result), None

    @staticmethod
    def _refuse(reason: str) -> tuple[ToolResult, str, str]:
        return ToolResult(text=reason, is_error=True), reason, reason

    def _notice(self) -> str | None:
        """The one-time 80% wrap-up text. It is a trace event of its own so a replay reproduces it exactly: while
        replaying we only ever use what was recorded; live, we ask the budget and record the answer."""
        if self.trace.replaying():
            ev = self.trace.peek("notice")
            if not ev:
                return None
            self.trace.consume()
            self.budget._wrap_issued = True
            return ev["text"]
        text = self.budget.wrap_up_notice()
        if text:
            self._live("notice", text=text)
        return text

    # ---- finish and forced finish ------------------------------------------------------------------------------------

    def _after_finish(self, args: dict, result: ToolResult, rendered: str) -> tuple[str, bool, RunResult | None]:
        if result.is_error:
            self.refused_finishes += 1
            if self.refused_finishes >= FINISH_REFUSALS_ALLOWED:
                return rendered, True, self._force(f"finish refused {FINISH_REFUSALS_ALLOWED} times in a row")
            return rendered, True, None
        decision = result.status
        config, outcome = args.get("config"), decision["outcome"]
        abstentions = list(args.get("abstentions") or []) + list(decision["abstentions"])
        if outcome in CONFIG_OUTCOMES and decision["abstentions"]:
            # Unanswered critique issues: code removes those fields and RE-VALIDATES (code, no model). It does not
            # re-critique: removing fields cannot add an error, only take one away.
            config = self.hooks.abstain(config, [a["field"] for a in decision["abstentions"]])
            status = self.hooks.validate(config)
            if status.get("hard_failures", 1) != 0:
                self.refused_finishes += 1
                return "finish refused: removing unanswered fields left validation failing; fix and re-run both.", True, None
        final = RunResult(outcome=outcome, config=config, abstentions=abstentions,
                          evidence=str(args.get("evidence", "")), reason=str(args.get("reason", "")))
        return "accepted", False, self._end(final)

    def _force(self, why: str) -> RunResult:
        """The harness ends the run: validate, abstain on failing fields, one critique, write the packet; outcome
        partial_config. If no config was ever proposed there is nothing to make partial: the outcome is `incomplete`
        with the reason. (could_not_read stays reserved for reader or fetch failures.)"""
        config, abstentions = self.gate.last_config, []
        if config is None:
            return self._end(RunResult(outcome=INCOMPLETE, reason=f"{why}; no config had been proposed", forced_by=why))
        for _ in range(2):
            status = self.hooks.validate(config)
            fields = status.get("failing_fields", [])
            if status.get("hard_failures", 0) == 0 or not fields:
                break
            abstentions += [{"field": f, "reason": "failed validation when the harness ended the run"} for f in fields]
            config = self.hooks.abstain(config, fields)
        crit = self.hooks.critique(config)
        self.budget.dollars += crit.get("cost_usd", 0.0)
        fields = [i["field"] for i in crit.get("issues", [])]
        if fields:   # nobody is left to answer the critic: its fields are abstained
            abstentions += [{"field": i["field"], "reason": f"critique issue unanswered: {i.get('problem', '')}"}
                            for i in crit["issues"]]
            config = self.hooks.abstain(config, fields)
        if self.hooks.validate(config).get("hard_failures", 0) != 0:
            return self._end(RunResult(outcome=INCOMPLETE, forced_by=why,
                                       reason=f"{why}; the config still failed validation after abstaining"))
        return self._end(RunResult(outcome="partial_config", config=config, abstentions=abstentions, forced_by=why))

    def _end(self, result: RunResult) -> RunResult:
        assert result.outcome in ALL_OUTCOMES
        result.turns = self.budget.calls
        result.tool_calls = self.executed
        result.cost_usd = round(self.budget.dollars, 6)
        result.elapsed_seconds = round(self.budget.elapsed(), 2)
        result.replayed_turns = self.replayed_turns
        result.packet_path = self.hooks.packet(result)
        if result.forced_by:
            self._live("forced_end", reason=result.forced_by)
        self._live("run_end", result=asdict(result))
        return result


def run_agent(**kwargs) -> RunResult:
    """See AgentRun for the arguments."""
    return AgentRun(**kwargs).run()
