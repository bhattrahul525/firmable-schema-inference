"""The table the agent is working on, and the held-out split (ARCHITECTURE.md sections b and c).

What lives where. Everything the tools and the finalise hooks need to know about the run's input is kept in the run's work
folder (logs/agent_runs/<source_id>/), not only in memory, so a resumed run (the trace is replayed, tools are not re-run)
finds the same state:

  input.json        the downloaded file: path, sha256, resource index, the metadata.json path     (written by `fetch`)
  table_state.json  the reader options of the latest successful `read_table`
  split.json        the held-out fingerprints (the split)

THE HELD-OUT SPLIT. It is made when a table is first read: a seeded reservoir sample of up to HELD_OUT_MAX rows (half the
rows if there are fewer than twice that). Rows are remembered by FINGERPRINT (a hash of their raw cells, see readers.py), not
by position, so a later read with different header options still excludes them. Training rows are every other row.

PROTECTED TOP. The first PROTECTED_ROWS (12) raw rows of the file are NEVER held out (their fingerprints come from a
layout-free read, so the protection holds whatever skip_rows / header_rows say, and a data row identical to a protected row
is protected with it). The split used to be made before the layout was known, so a title or the real header row could land
in the held-out set and be hidden from the agent for the whole run; `sniff` also shows the first 12 raw lines, so holding
any of them out tested the mapping on rows the agent had already seen. Protecting the top removes both. A file where fewer
than MIN_ELIGIBLE_FOR_SPLIT (10) rows remain eligible gets NO held-out set: fields are then judged on training evidence
(agent_hooks evidence states) and the packet says no held-out test was possible.

  * `read_table` (first rows), `sample`, `search`, `profile`, `check_unique`, `try_transform`: training rows only.
  * `validate`, `critique` and the harness's own finalise hooks: held-out rows.

Known weakness, stated: if the very first read parsed the file wrongly (e.g. the wrong delimiter), the fingerprints do not
match the later, correct parse. We then re-make the split (`resplit`) and say so; rows shown to the model under the wrong
parse could by chance be in the new held-out set.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

from src.engine.readers import STREAM_ABOVE_BYTES, iter_table, raw_head_fingerprints

RAW_DIR = Path("data/raw/sources")
HELD_OUT_MAX = 300
PROTECTED_ROWS = 12          # the first raw rows of the file, never held out (the layout must never be hidden)
MIN_ELIGIBLE_FOR_SPLIT = 10  # fewer eligible rows than this -> no held-out set (fields judged on training evidence)
RESPLIT_BELOW = 0.5      # fewer than this share of the old held-out rows found under a new parse -> make a new split
MAX_HELD_ROWS = 1000     # rows kept in memory for the held-out set (duplicates of one fingerprint included)
_TABLES: dict = {}       # process cache, so tools and finalise hooks share one build


class NoTable(Exception):
    """A tool needs a table but nothing has been fetched or read yet. str(e) is a sentence written by our code."""


@dataclass
class Table:
    path: Path
    reader: dict
    headers: list[str]
    n_rows: int
    visible_n: int
    held_fp: frozenset
    held_rows: list[dict]
    resplit: bool = False
    cache: list | None = None      # [(fingerprint, row)] when the file is small enough to keep in memory

    def rows(self, check: Callable | None = None) -> Iterator[tuple[bytes, dict]]:
        if self.cache is not None:
            yield from self.cache
            return
        with iter_table(self.reader, self.path, check) as (_, rows):
            yield from rows

    def training(self, check: Callable | None = None) -> Iterator[dict]:
        """Training rows only: every row whose fingerprint is not held out."""
        for fp, row in self.rows(check):
            if fp not in self.held_fp:
                yield row


# ---- files in the work folder --------------------------------------------------------------------------------------

def _read_json(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def input_info(work_dir: Path) -> dict | None:
    return _read_json(work_dir / "input.json")


def save_input(work_dir: Path, info: dict) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "input.json").write_text(json.dumps(info, indent=1))


def input_path(work_dir: Path) -> Path:
    info = input_info(work_dir)
    if not info or not Path(info["path"]).exists():
        raise NoTable("no input file yet: call `fetch` first (no arguments lists the resources; `resource_index` downloads one)")
    return Path(info["path"])


def load_metadata(source_id: str) -> dict:
    p = RAW_DIR / source_id / "metadata.json"
    if not p.exists():
        raise NoTable("no metadata for this run yet: call `fetch` first")
    return json.loads(p.read_text())


# ---- building the table --------------------------------------------------------------------------------------------

def build_table(source_id: str, work_dir: Path, path: Path, reader: dict, check: Callable | None = None) -> Table:
    """One pass to count rows and pick the split, a second (or the cache) to find the held-out rows. Raises ReaderError."""
    split_path = work_dir / "split.json"
    prior_raw = _read_json(split_path)
    prior = frozenset(bytes.fromhex(x) for x in prior_raw["fps"]) if prior_raw else None

    protected = raw_head_fingerprints(reader, path, PROTECTED_ROWS)   # layout-free: the same rows whatever the options say
    cacheable = not reader.get("archive") and path.stat().st_size <= STREAM_ABOVE_BYTES
    cache: list | None = [] if cacheable else None
    rng = random.Random(source_id)
    reservoir: list[bytes] = []
    n = found = eligible = 0
    with iter_table(reader, path, check) as (headers, rows):
        for fp, row in rows:
            if cache is not None:
                cache.append((fp, row))
            if prior is not None and fp in prior:
                found += 1
            n += 1
            if fp in protected:     # the first PROTECTED_ROWS raw rows (and any row identical to one) are never held out
                continue
            if eligible < HELD_OUT_MAX:
                reservoir.append(fp)
            else:
                j = rng.randint(0, eligible)
                if j < HELD_OUT_MAX:
                    reservoir[j] = fp
            eligible += 1

    resplit = False
    if prior and found >= RESPLIT_BELOW * len(prior):
        held = prior
    else:
        resplit = prior is not None
        k = 0 if eligible < MIN_ELIGIBLE_FOR_SPLIT else min(HELD_OUT_MAX, n // 2, len(reservoir))
        held = frozenset(random.Random(source_id + ":pick").sample(reservoir, k)) if k else frozenset()
        work_dir.mkdir(parents=True, exist_ok=True)
        split_path.write_text(json.dumps({"fps": sorted(x.hex() for x in held), "protected": PROTECTED_ROWS,
                                          "no_held_out": not held}))

    table = Table(path=path, reader=reader, headers=headers, n_rows=n, visible_n=n, held_fp=held, held_rows=[],
                  resplit=resplit, cache=cache)
    held_count, held_rows = 0, []
    for fp, row in table.rows(check):
        if fp in held:
            held_count += 1
            if len(held_rows) < MAX_HELD_ROWS:
                held_rows.append(row)
    table.visible_n, table.held_rows = n - held_count, held_rows
    return table


def remember_table(source_id: str, work_dir: Path, table: Table) -> None:
    """Make `table` the current one: process cache plus table_state.json (so a resumed run can rebuild it)."""
    info = input_info(work_dir) or {}
    _TABLES[(source_id, str(work_dir.resolve()), info.get("sha256"))] = table
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "table_state.json").write_text(json.dumps({"reader": table.reader}))


def get_table(source_id: str, work_dir: Path, check: Callable | None = None) -> Table:
    """The current table: from the process cache, else rebuilt from the work folder (resume after a replay)."""
    info = input_info(work_dir)
    state = _read_json(work_dir / "table_state.json")
    if not info or not state:
        raise NoTable("no table has been read yet: call `read_table` with reader options first")
    key = (source_id, str(work_dir.resolve()), info.get("sha256"))
    cached = _TABLES.get(key)
    if cached is not None and cached.reader == state["reader"]:
        return cached
    table = build_table(source_id, work_dir, input_path(work_dir), state["reader"], check)
    _TABLES[key] = table
    return table


def collect_held(table: Table, reader: dict, check: Callable | None = None) -> tuple[list[str], list[dict]]:
    """Headers and held-out rows as `reader` (a config's reader) parses them. Same fingerprints, so the same rows."""
    if reader == table.reader:
        return table.headers, table.held_rows
    held = []
    with iter_table(reader, table.path, check) as (headers, rows):
        for fp, row in rows:
            if fp in table.held_fp and len(held) < MAX_HELD_ROWS:
                held.append(row)
    return headers, held
