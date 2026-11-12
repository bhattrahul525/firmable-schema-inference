"""Test doubles for the agent loop: a scripted fake model, a fake clock and three stub tools.
Nothing here ships as production code and nothing needs an API key."""

from __future__ import annotations

from src import llm
from src.part2_agent.loop import FinaliseHooks, RunResult
from src.part2_agent.tools import ToolResult, ToolSpec, registry


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def tool_turn(name: str, args: dict, *, id: str = "toolu_1", cost: float = 0.01, seconds: float = 0.0,
              stop: str = "tool_use", extra_blocks: list | None = None) -> llm.LLMTurn:
    blocks = list(extra_blocks or []) + [{"type": "tool_use", "id": id, "name": name, "input": args}]
    return llm.LLMTurn(content=blocks, stop_reason=stop, model="fake", input_tokens=10, output_tokens=5,
                       cache_read_tokens=0, cache_write_tokens=0, cost_usd=cost, seconds=seconds)


def text_turn(text: str = "I will think about it.", *, cost: float = 0.01, stop: str = "end_turn") -> llm.LLMTurn:
    return llm.LLMTurn(content=[{"type": "text", "text": text}], stop_reason=stop, model="fake", input_tokens=10,
                       output_tokens=5, cache_read_tokens=0, cache_write_tokens=0, cost_usd=cost, seconds=0.0)


class _ApiError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class ScriptedChat:
    """Stands in for llm.chat. Plays scripted turns in order; an item may also be a function (messages) -> turn.
    Records every call (with a copy of the messages and the max_tokens asked for). A CRASH item raises."""
    CRASH = object()
    TRANSIENT = object()      # raises an overloaded-style error (status 529): the loop should retry
    BAD_REQUEST = object()    # raises a status-400 error: the loop must NOT retry

    def __init__(self, script, clock: FakeClock | None = None):
        self.script, self.clock, self.calls = list(script), clock, []

    def __call__(self, messages, **kw):
        self.calls.append({"messages": messages, **kw})
        if not self.script:
            raise AssertionError("the loop asked the model for more turns than the test scripted")
        item = self.script.pop(0)
        if item is self.CRASH:
            raise RuntimeError("simulated network failure")
        if item is self.TRANSIENT:
            raise _ApiError("overloaded", 529)
        if item is self.BAD_REQUEST:
            raise _ApiError("bad request", 400)
        turn = item(messages) if callable(item) else item
        if self.clock:
            self.clock.advance(turn.seconds)
        return turn


class Counter:
    """Counts how often each stub tool really executed (replay must not execute them) and holds the knobs tests turn
    to make the stub fetch slow, failing, or report a different input file."""

    def __init__(self):
        self.runs: dict[str, int] = {}
        self.fetch_slow = 0.0       # seconds of "download" the stub fetch reports (and advances the fake clock by)
        self.fetch_fail = False
        self.sha = "sha-A"          # input file hash the stub fetch reports

    def hit(self, name: str) -> None:
        self.runs[name] = self.runs.get(name, 0) + 1


def make_tools(counter: Counter, clock: FakeClock | None = None) -> dict[str, ToolSpec]:
    """Stub tools. A 'config' in these tests is {"fields": [...], "bad": [fields failing validation],
    "issues": [{"id", "field", "problem"}]}."""
    cfg = {"type": "object", "properties": {"config": {"type": "object"}}, "required": ["config"]}

    def fetch(args, ctx):
        counter.hit("fetch")
        if clock:
            clock.advance(counter.fetch_slow)
        if "resource_index" in args:
            ctx.state["input_sha256"] = counter.sha
        return ToolResult(text="fetched", payload=ctx.fetcher.list_resources() if "resource_index" not in args else None,
                          download_seconds=counter.fetch_slow, is_error=counter.fetch_fail)

    def read_table(args, ctx):
        counter.hit("read_table")
        rows = [{f"col{c}": f"value-{r}-{c}-" + "x" * 300 for c in range(60)} for r in range(50)]
        return ToolResult(text="read ok", payload=rows if not args.get("fail") else None, is_error=bool(args.get("fail")))

    def profile(args, ctx):
        counter.hit("profile")
        return ToolResult(text="profile ok", payload=args.get("payload", {"columns": 3}))

    def validate(args, ctx):
        counter.hit("validate")
        c = args["config"]
        bad = [f for f in c.get("bad", []) if f in c.get("fields", [])]
        return ToolResult(text="validated", status={"hard_failures": len(bad), "failing_fields": bad})

    def critique(args, ctx):
        counter.hit("critique")
        c = args["config"]
        issues = [i for i in c.get("issues", []) if i["field"] in c.get("fields", [])]
        return ToolResult(text="critiqued", status={"issues": issues}, cost_usd=0.02)

    def boom(args, ctx):
        counter.hit("boom")
        raise ValueError("secret internal detail " * 40)

    return registry(
        ToolSpec("fetch", "fetch", {"type": "object", "properties": {"resource_index": {"type": "integer"}}}, fetch),
        ToolSpec("read_table", "read", {"type": "object", "properties": {"fail": {"type": "boolean"}}}, read_table,
                 max_rows=20, max_cols=40, max_cell_chars=100, max_chars=6000),
        ToolSpec("profile", "profile", {"type": "object", "properties": {"payload": {}}}, profile),
        ToolSpec("validate", "validate", cfg, validate, max_chars=6000),
        ToolSpec("critique", "critique", cfg, critique, max_uses=2),
        ToolSpec("boom", "crashes", {"type": "object", "properties": {}}, boom),
    )


def abstain(config: dict, fields: list) -> dict:
    return {**config, "fields": [f for f in config["fields"] if f not in fields]}


class FakeHooks(FinaliseHooks):
    def __init__(self):
        self.packets: list[RunResult] = []
        super().__init__(
            validate=lambda c: {"hard_failures": len([f for f in c.get("bad", []) if f in c["fields"]]),
                                "failing_fields": [f for f in c.get("bad", []) if f in c["fields"]]},
            critique=lambda c: {"issues": [i for i in c.get("issues", []) if i["field"] in c["fields"]], "cost_usd": 0.02},
            abstain=abstain,
            packet=self._packet)

    def _packet(self, result: RunResult) -> str:
        self.packets.append(result)
        return "packet.md"
