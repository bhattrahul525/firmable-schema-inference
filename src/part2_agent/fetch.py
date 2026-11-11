"""Fetch a dataset we have never seen, so the agent can onboard it: from CKAN, or a local file.

  python -m src.part2_agent.onboard nsw:find-by-lia-band        (CKAN: <portal>:<dataset name>)
  python -m src.part2_agent.onboard --file path/to/data.csv      (local file; licence recorded as unknown)

Both write data/raw/sources/<source_id>/metadata.json in the same shape Part 1's download step
uses, so everything downstream (agent, engine, licence flag) is identical. No human chooses
columns, formats or a mapping; the only inputs are WHICH dataset and (optionally) which resource.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.common.ckan import CkanClient
from src.engine.readers import FORMATS
from src.part1_triage.download import RAW_DIR, download
from src.part1_triage.pull import slim

PREFERENCE = ["CSV", "TSV", "XLSX", "JSON"]  # tabular formats the engine can read, best first


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def fetch_ckan(ref: str, resource_contains: str | None = None) -> str:
    portal, name = ref.split(":", 1)
    rec = slim(CkanClient(portal).package_show(name), portal)
    options = [r for r in rec["resources"] if r["url"] and any(f == r["format"].lstrip(".") for f in PREFERENCE)
               and (not resource_contains or resource_contains.lower() in r["name"].lower())]
    if not options:
        have = [f"{r['format']}: {r['name']}" for r in rec["resources"]]
        raise SystemExit(f"{ref}: no resource the engine can read ({PREFERENCE}). Resources: {have}")
    # best format first; within a format the most recently modified
    options.sort(key=lambda r: (PREFERENCE.index(r["format"].lstrip(".")), -(datetime.fromisoformat(
        (r["last_modified"] or "1970-01-01").replace("Z", "")).timestamp())))
    source_id = slug(name)
    meta = download({"source_id": source_id, "dataset_id": rec["dataset_id"], "resource": {}},
                    {rec["dataset_id"]: rec}, res=options[0])
    print(f"fetched {ref} -> {source_id}: {options[0]['format']} '{options[0]['name']}', licence: {meta['licence']}"
          + ("  (FLAGGED)" if meta["licence_flag"] else ""))
    return source_id


def fetch_file(path: str, licence: str = "unknown") -> str:
    src = Path(path)
    fmt = src.suffix.lstrip(".").upper()
    if fmt.lower() not in FORMATS:
        raise SystemExit(f"unsupported file type {src.suffix!r}; the engine reads {FORMATS}")
    source_id = slug(src.stem)
    out = RAW_DIR / source_id
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, out / src.name)
    mtime = datetime.fromtimestamp(src.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    meta = {
        "source_id": source_id, "dataset_id": f"file:{src.name}", "portal": "local", "title": src.stem,
        "organisation": "unknown (local file)", "dataset_page": "", "licence": licence,
        "licence_flag": licence == "unknown", "ckan_license_id": "", "dataset_modified": mtime,
        "resource_id": "", "resource_name": src.name, "resource_format": fmt, "resource_last_modified": mtime,
        "url": str(src), "file": src.name, "bytes": src.stat().st_size,
        "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"copied {src} -> {source_id}; licence recorded as {licence!r}" + (" (FLAGGED: unknown)" if licence == "unknown" else ""))
    return source_id
