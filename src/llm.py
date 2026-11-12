"""The single entry point for every LLM call in this project.

Rules:
  * Nothing else in the codebase imports `anthropic`. Swapping provider = edit this file.
  * Every call (success or failure) appends one line to logs/llm_calls.jsonl with model,
    tokens, computed cost, wall-clock time and the caller's `step` / `source_id` tags.
    Per-source onboarding cost and step count in the write-up come from this log.

Cost here is *computed* from the price table below, not read from an invoice. The
write-up should report it as such and cross-check against the Anthropic console.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

LOG_PATH = Path("logs/llm_calls.jsonl")
# Every call logged from now on is tagged with the round it belongs to. Lines without a "round" are round 1 (the
# first submission), so round-2 work can never change round-1 cost figures.
CURRENT_ROUND = 2
DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")

# USD per 1M tokens: (input, output, cache_read). Anthropic first-party prices as of
# 2026-11-03. Cache writes are billed at 1.25x input. Haiku 5.5 prices apply to prompts
# up to 100K tokens; we keep prompts well under that.
PRICES: dict[str, tuple[float, float, float]] = {
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-opus-5-5": (4.00, 20.00, 0.20),
}
CACHE_WRITE_MULTIPLIER = 1.25

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # Reads ANTHROPIC_API_KEY from the environment (.env loaded above).
        _client = anthropic.Anthropic(max_retries=3, timeout=120.0)
    return _client


@dataclass
class LLMResult:
    data: dict | None  # parsed JSON when a schema was given
    text: str  # raw text of the answer
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    seconds: float
    stop_reason: str | None


def compute_cost(model: str, usage) -> float:
    if model not in PRICES:
        raise ValueError(f"no price for {model!r}; add it to PRICES in src/llm.py")
    p_in, p_out, p_cache_read = PRICES[model]
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (
        usage.input_tokens * p_in
        + cache_write * p_in * CACHE_WRITE_MULTIPLIER
        + cache_read * p_cache_read
        + usage.output_tokens * p_out
    ) / 1_000_000


_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}"),                                   # Anthropic key shape
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=\-]{8,}", re.I),          # bearer / basic credentials anywhere
    # header-ish `name: value` / `name=value`. The WHOLE value goes, including an auth scheme word ("Bearer x", "Basic x").
    re.compile(r"""((?:x-api-key|authorization|api[_-]?key)(?:\\?["'])?\s*[:=]\s*(?:\\?["'])?)(?:(?:Bearer|Basic)\s+)?([^\s"',}\\]+)""",
               re.I),   # the (?:\\?["']) parts also match a quote that is escaped inside JSON text
]


def redact(text: str) -> str:
    """Remove anything that looks like our API key or a request header value from ONE string."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if len(key) >= 8:
        text = text.replace(key, "[REDACTED]")
    text = _SECRET_PATTERNS[0].sub("[REDACTED]", text)
    text = _SECRET_PATTERNS[1].sub("[REDACTED]", text)
    return _SECRET_PATTERNS[2].sub(lambda m: m.group(1) + "[REDACTED]", text)


def _redact_values(obj):
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, list):
        return [_redact_values(x) for x in obj]
    if isinstance(obj, dict):
        return {redact(str(k)): _redact_values(v) for k, v in obj.items()}
    return obj


def dumps_redacted(obj) -> str:
    """JSON for ONE log or trace line with every string value (and key) redacted BEFORE serialising. Redacting the
    serialised text is unsafe: a pattern can swallow the backslash that escapes a quote (`api_key=abc\\"`) and leave
    an unescaped quote, breaking the JSONL line. Here the redactor only ever sees plain strings, so the JSON it
    produces is always valid. Objects json cannot encode are turned into strings first (default=str), then redacted."""
    return json.dumps(_redact_values(json.loads(json.dumps(obj, default=str))))


# Cost the call log has recorded in THIS process. The agent loop reads it before and after a tool runs, so what a
# model-calling tool cost comes from the log (which our code wrote) and not from what the tool says about itself.
_logged_cost_total = 0.0


def logged_cost_total() -> float:
    return _logged_cost_total


TRANSIENT_STATUS = (408, 429, 500, 502, 503, 504, 529)


def is_transient(exc: BaseException) -> bool:
    """True for errors worth retrying: connection errors and timeouts, and exactly these HTTP statuses: 408 request
    timeout, 429 rate limit, 500, 502, 503, 504 server errors, 529 overloaded. Every other status (400, 401, 403, 404,
    413, 422, 501, ...) is NOT transient."""
    if isinstance(exc, anthropic.APIConnectionError):   # includes APITimeoutError
        return True
    return getattr(exc, "status_code", None) in TRANSIENT_STATUS


def _log(entry: dict) -> None:
    global _logged_cost_total
    entry.setdefault("round", CURRENT_ROUND)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(dumps_redacted(entry) + "\n")
    cost = entry.get("cost_usd")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost == cost and cost > 0:
        _logged_cost_total += cost


def call(
    prompt: str,
    *,
    step: str,
    source_id: str | None = None,
    system: str | None = None,
    schema: dict | None = None,
    model: str | None = None,
    effort: str = "low",
    max_tokens: int = 16000,
) -> LLMResult:
    """One model call. (Round 1's single-shot call. It keeps the SDK's own max_retries=3 from _get_client(); only chat()
    below turns SDK retries off so the agent loop can trace each one.)

    step:      which pipeline step is calling (e.g. "part2.propose_mapping"); used for
               per-step cost/latency breakdowns.
    source_id: which dataset the call is about, so cost per source can be summed.
    schema:    JSON schema; when given, the API guarantees a JSON answer matching it
               (structured outputs) and `.data` holds the parsed object.
    effort:    thinking depth. "low" is enough for most mapping steps; raise it per
               step only where a measured quality gain justifies the extra tokens.
    """
    model = model or DEFAULT_MODEL
    output_config: dict = {"effort": effort}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "output_config": output_config,
    }
    if system:
        # The system prompt is the stable part (ontology + instructions), so cache it.
        kwargs["system"] = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "source_id": source_id,
        "model": model,
        "effort": effort,
    }
    t0 = time.monotonic()
    try:
        resp = _get_client().messages.create(**kwargs)
    except anthropic.APIError as e:
        entry.update(ok=False, seconds=round(time.monotonic() - t0, 2), error=f"{type(e).__name__}: {e}")
        _log(entry)
        raise
    seconds = time.monotonic() - t0

    text = "".join(b.text for b in resp.content if b.type == "text")
    cost = compute_cost(model, resp.usage)
    entry.update(
        ok=resp.stop_reason not in ("refusal", "max_tokens"),
        seconds=round(seconds, 2),
        stop_reason=resp.stop_reason,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        cache_read_tokens=getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
        cost_usd=round(cost, 6),
        request_id=resp._request_id,
    )
    _log(entry)

    if resp.stop_reason == "refusal":
        raise RuntimeError(f"model refused ({step}): {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(f"hit max_tokens={max_tokens} ({step}); raise it or shrink the prompt")

    data = json.loads(text) if schema is not None else None
    return LLMResult(
        data=data,
        text=text,
        model=model,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        cost_usd=cost,
        seconds=seconds,
        stop_reason=resp.stop_reason,
    )


@dataclass
class LLMTurn:
    """One assistant turn of a tool-using conversation (round 2, ARCHITECTURE.md section b)."""
    content: list[dict]  # the assistant's blocks as plain dicts, exactly as returned (JSON-safe)
    stop_reason: str | None
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    seconds: float

    @property
    def tool_uses(self) -> list[dict]:
        return [b for b in self.content if b.get("type") == "tool_use"]


def request_blocks(content: list[dict]) -> list[dict]:
    """Assistant blocks -> blocks we send back in the next request.

    Thinking / redacted_thinking blocks must be passed back COMPLETE and UNMODIFIED (the docs say a modified thinking
    block returns 400), so they are copied as they came. Text and tool_use blocks are reduced to the documented
    request fields, dropping response-only extras."""
    out = []
    for b in content:
        if b["type"] == "text":
            out.append({"type": "text", "text": b["text"]})
        elif b["type"] == "tool_use":
            out.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
        else:
            out.append(b)
    return out


def chat(
    messages: list[dict],
    *,
    step: str,
    source_id: str | None = None,
    system: str | None = None,
    tools: list[dict] | None = None,
    model: str | None = None,
    effort: str = "low",
    max_tokens: int = 4096,
) -> LLMTurn:
    """One turn of a conversation with tools. The agent loop calls this; nothing else touches the API.

    Differences from call():
      * tools are passed with tool_choice {"type": "auto", "disable_parallel_tool_use": True}. Forced tool use
        ("any" / "tool") returns 400 on Sonnet 5.5, so the model may answer in text; the loop handles that.
      * history caching uses the top-level `cache_control` (automatic breakpoint on the last block). Tools and system
        stay identical for a whole run, because changing tools invalidates the entire cache.
      * a refusal or max_tokens stop is RETURNED (stop_reason), not raised: the loop decides what to do.
      * thinking is requested with `display: "summarized"` (step 3b, item G): on both Haiku 5.5 and Sonnet 5.5 this
        was confirmed live to be accepted (no 400) and, on turns where the model actually thinks, to return readable
        text at no extra token cost over the default `display: "omitted"` (thinking is billed the same either way).
        The block is passed back unmodified on the next turn, like any other (request_blocks).
    Every turn is logged to logs/llm_calls.jsonl like any other call, with the number of tool calls it made."""
    model = model or DEFAULT_MODEL
    kwargs: dict = {
        "model": model, "max_tokens": max_tokens, "messages": messages,
        "output_config": {"effort": effort}, "cache_control": {"type": "ephemeral"},
        "thinking": {"type": "adaptive", "display": "summarized"},
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}

    entry = {"ts": datetime.now(timezone.utc).isoformat(), "step": step, "source_id": source_id, "model": model,
             "effort": effort}
    t0 = time.monotonic()
    client = _get_client()
    if hasattr(client, "with_options"):
        client = client.with_options(max_retries=0)   # retries are the AGENT LOOP's job, so each one is traced
    try:
        resp = client.messages.create(**kwargs)
    except anthropic.APIError as e:
        entry.update(ok=False, seconds=round(time.monotonic() - t0, 2), error=f"{type(e).__name__}: {e}")
        _log(entry)
        raise
    seconds = time.monotonic() - t0

    content = [b.model_dump(mode="json", exclude_none=True) for b in resp.content]
    cost = compute_cost(model, resp.usage)
    cache_read = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
    entry.update(
        ok=resp.stop_reason not in ("refusal", "max_tokens"), seconds=round(seconds, 2), stop_reason=resp.stop_reason,
        input_tokens=resp.usage.input_tokens, output_tokens=resp.usage.output_tokens,
        cache_read_tokens=cache_read, cache_write_tokens=cache_write, cost_usd=round(cost, 6),
        tool_calls=sum(1 for b in content if b["type"] == "tool_use"), request_id=resp._request_id,
    )
    _log(entry)
    return LLMTurn(content=content, stop_reason=resp.stop_reason, model=model, input_tokens=resp.usage.input_tokens,
                   output_tokens=resp.usage.output_tokens, cache_read_tokens=cache_read, cache_write_tokens=cache_write,
                   cost_usd=cost, seconds=seconds)


def spend_summary(path: Path = LOG_PATH, round_no: int | None = 1) -> dict:
    """Totals from the log, overall and per step / per source, for ONE round. The default is round 1, so the figures
    quoted in the first submission (README, WRITEUP) never move when round-2 calls are logged. Lines without a "round"
    field are round 1. Pass round_no=None for every round combined; spend_by_round() gives them side by side."""
    totals = {"calls": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}
    by_step: dict[str, float] = {}
    by_source: dict[str, float] = {}
    if not path.exists():
        return {"round": round_no, "total": totals, "by_step": by_step, "by_source": by_source}
    for line in path.read_text().splitlines():
        e = json.loads(line)
        if round_no is not None and e.get("round", 1) != round_no:
            continue
        totals["calls"] += 1
        totals["seconds"] += e.get("seconds", 0)
        c = e.get("cost_usd", 0.0)
        totals["cost_usd"] += c
        totals["input_tokens"] += e.get("input_tokens", 0)
        totals["output_tokens"] += e.get("output_tokens", 0)
        by_step[e["step"]] = by_step.get(e["step"], 0.0) + c
        src = e.get("source_id") or "-"
        by_source[src] = by_source.get(src, 0.0) + c
    return {"round": round_no, "total": totals, "by_step": by_step, "by_source": by_source}


def spend_by_round(path: Path = LOG_PATH) -> dict[int, dict]:
    """{round: spend_summary} for every round present in the log, reported separately, never blended."""
    if not path.exists():
        return {}
    rounds = sorted({json.loads(line).get("round", 1) for line in path.read_text().splitlines()})
    return {r: spend_summary(path, r) for r in rounds}


if __name__ == "__main__":
    # Smoke test: python -m src.llm  (costs a fraction of a cent on Haiku)
    r = call(
        "Return the ABN in this text: 'Acme Pty Ltd, ABN 51 824 753 556'.",
        step="smoke_test",
        schema={
            "type": "object",
            "properties": {"abn": {"type": "string"}},
            "required": ["abn"],
            "additionalProperties": False,
        },
    )
    print(r.data, f"${r.cost_usd:.6f}", f"{r.seconds:.1f}s")
    for rnd, summary in spend_by_round().items():
        print(f"round {rnd}:", summary["total"])
