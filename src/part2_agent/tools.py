"""Tool mechanics for the round-2 agent (ARCHITECTURE.md section b).

This file defines WHAT a tool is, not the tools themselves (those arrive in build step 2). The harness
(guard.py, loop.py) only ever sees tools through these two small types.

Status contract between a tool and the harness. A tool puts machine-readable facts in `ToolResult.status`; the guard
reads ONLY these keys, never the model's own words:
  validate  -> {"hard_failures": int, "failing_fields": [str]}
  critique  -> {"issues": [{"id": str, "field": str, "problem": str}]}
  fetch     -> {"download_failed": True} when a DOWNLOAD or NETWORK failure happened (a refused index or URL is not one)
  anything else -> free-form
The harness checks the shape of every result: a ToolResult with finite, non-negative `cost_usd` and `download_seconds`,
a dict `status`, and for validate / critique the keys above. Anything else becomes an error result, never a crash.
A tool receives a COPY of its arguments, so editing them in place cannot change what the gate hashes or the trace records.
`ToolResult.text` is written by our code (trusted). `ToolResult.payload` is dataset content (untrusted): it is capped
and wrapped in a <data> block before the model sees it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


class ToolTimeout(BaseException):
    """A tool ran past its time limit. A BaseException on purpose (like KeyboardInterrupt): a broad `except Exception`
    inside a tool or a library must not be able to swallow it. The loop catches it and returns an error result."""


@dataclass
class ToolContext:
    """What a tool may use. `reference` is the ONE thing the human asked us to ingest (url, CKAN id or path)."""
    source_id: str
    reference: str
    work_dir: Path
    state: dict = field(default_factory=dict)  # tool-to-tool memory (e.g. the held-out row partition, step 2)
    fetcher: Any = None   # the harness's FetchGuard: the fetch tool lists and resolves resources through it, and sets
                          # state["input_sha256"] once the input file is on disk (the loop pins it in the trace)
    log: Callable[[str], None] = lambda message: None   # a progress line for the trace (the loop sets it)
    ask: Callable[[str], "str | None"] | None = None     # ask_human: question -> the human's answer, or None
    uses: Any = None      # Counter of the tools used so far in this run (replayed calls included); set by the loop
    deadline: float | None = None   # time.monotonic() limit of the running tool call; set by the loop

    def check_deadline(self) -> None:
        """Cooperative half of the per-tool timeout (the other half is a signal on POSIX): long row loops call this."""
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise ToolTimeout("tool deadline passed")


@dataclass
class ToolResult:
    text: str = ""                    # trusted explanation written by our code
    payload: Any = None               # untrusted dataset content: list of rows, dict, string...
    status: dict = field(default_factory=dict)  # machine-readable facts for the guard (see module docstring)
    is_error: bool = False
    cost_usd: float = 0.0             # a tool that calls a model (critique) reports its cost so the budget counts it
    download_seconds: float = 0.0     # excluded from the wall-clock budget (downloads; ask_human reuses it for the human's
                                      # wait and the trace labels that one human_wait_seconds)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    run: Callable[[dict, ToolContext], ToolResult]
    # output caps, applied by the HARNESS to the payload (a tool cannot opt out)
    max_rows: int | None = None
    max_cols: int | None = None
    max_cell_chars: int = 100
    max_chars: int = 6000             # hard ceiling on everything the model sees from one call
    max_uses: int | None = None       # e.g. critique 2, ask_human 1 (section b)
    timeout_seconds: float | None = 60.0   # per call; None only for a download (fetch) or a human wait (ask_human)

    def api_schema(self) -> dict:
        """The tool definition sent to the API. Same for the whole run (changing tools breaks the prompt cache)."""
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


def registry(*specs: ToolSpec) -> dict[str, ToolSpec]:
    names = [s.name for s in specs]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate tool names: {names}")
    return {s.name: s for s in specs}
