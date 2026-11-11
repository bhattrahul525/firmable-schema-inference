"""Run state: every agent step saves its output to logs/agent_runs/<source_id>/<step>.json.

If a run dies (API error, laptop closed), re-running the same command skips every step that
already has a checkpoint and carries on from the first one that does not. So a failure costs
one step, not the whole onboarding. To redo a step on purpose, delete its file.

state.json keeps the run's start time and per-step wall-clock seconds for the write-up.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

RUNS_DIR = Path("logs/agent_runs")


class Run:
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.dir = RUNS_DIR / source_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            "source_id": source_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "timings": {},
            "step_log": [],
        }
        self._save_state()

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def path(self, name: str) -> Path:
        return self.dir / f"{name}.json"

    def has(self, name: str) -> bool:
        return self.path(name).exists()

    def load(self, name: str):
        return json.loads(self.path(name).read_text())

    def save(self, name: str, data) -> None:
        self.path(name).write_text(json.dumps(data, indent=2, default=str))

    def step(self, name: str, fn):
        """Run fn() and checkpoint its (JSON-serialisable) result, unless already done."""
        if self.has(name):
            print(f"  [resume] {name}: using checkpoint")
            return self.load(name)
        t0 = time.monotonic()
        result = fn()
        secs = round(time.monotonic() - t0, 2)
        self.save(name, result)
        self.state["timings"][name] = secs
        self.state["step_log"].append(name)
        self._save_state()
        print(f"  [done]   {name} ({secs}s)")
        return result
