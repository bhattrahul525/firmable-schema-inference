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
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

LOG_PATH = Path("logs/llm_calls.jsonl")
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


def _log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


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
    """One model call.

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


def spend_summary(path: Path = LOG_PATH) -> dict:
    """Totals from the log, overall and per step / per source. Used by the write-up."""
    totals = {"calls": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}
    by_step: dict[str, float] = {}
    by_source: dict[str, float] = {}
    if not path.exists():
        return {"total": totals, "by_step": by_step, "by_source": by_source}
    for line in path.read_text().splitlines():
        e = json.loads(line)
        totals["calls"] += 1
        totals["seconds"] += e.get("seconds", 0)
        c = e.get("cost_usd", 0.0)
        totals["cost_usd"] += c
        totals["input_tokens"] += e.get("input_tokens", 0)
        totals["output_tokens"] += e.get("output_tokens", 0)
        by_step[e["step"]] = by_step.get(e["step"], 0.0) + c
        src = e.get("source_id") or "-"
        by_source[src] = by_source.get(src, 0.0) + c
    return {"total": totals, "by_step": by_step, "by_source": by_source}


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
    print(spend_summary()["total"])
