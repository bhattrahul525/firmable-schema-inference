"""Download the 6 chosen sources and record exactly what was fetched.

For each source in sources.yaml we save the file plus a metadata.json with:
  * licence (from CKAN; 'unknown' + flagged if missing or unclear)
  * the dataset's and the file's last-modified dates (Part 2 uses these for observed_at)
  * the URL, resource id, size and SHA-256 of the bytes we got
So any observation can be traced back to an exact file, and a changed upstream file is
detectable (different hash) rather than silent.

Run: python -m src.part1_triage.download
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

from src.common.ckan import PORTAL_DATASET_PAGE, http_session
from src.part1_triage.run import licence_of

SOURCES_FILE = Path("sources.yaml")
POOL_PATH = Path("outputs/part1_pool.jsonl")
RAW_DIR = Path("data/raw/sources")
MANIFEST = Path("outputs/part1_sources_manifest.json")


def pick(rec: dict, rule: dict) -> dict:
    matches = [
        r for r in rec["resources"]
        if (not rule.get("format") or rule["format"].upper() in r["format"])
        and (not rule.get("name_contains") or rule["name_contains"].lower() in r["name"].lower())
    ]
    if len(matches) != 1:
        names = [f"{r['format']}: {r['name']}" for r in rec["resources"]]
        raise ValueError(f"{rec['dataset_id']}: rule {rule} matched {len(matches)} resources; have {names}")
    return matches[0]


def filename_for(res: dict) -> str:
    """File name from the URL path (query string dropped); 'data.<format>' if it has no extension."""
    name = Path(urlparse(res["url"]).path).name
    if not Path(name).suffix:
        name = "data." + res["format"].lower().lstrip(".")
    return name


def download(source: dict, pool: dict[str, dict], res: dict | None = None) -> dict:
    """`res` lets a caller choose the resource itself (used for unseen datasets); otherwise the
    rule in sources.yaml must match exactly one resource."""
    rec = pool[source["dataset_id"]]
    res = res or pick(rec, source["resource"])
    out_dir = RAW_DIR / source["source_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename_for(res)

    sha, size = hashlib.sha256(), 0
    with http_session().get(res["url"], stream=True, timeout=(15, 300)) as resp:
        resp.raise_for_status()
        with path.open("wb") as f:
            for chunk in resp.iter_content(256 * 1024):
                f.write(chunk)
                sha.update(chunk)
                size += len(chunk)

    licence, flagged = licence_of(rec)
    meta = {
        "source_id": source["source_id"],
        "dataset_id": rec["dataset_id"],
        "portal": rec["portal"],
        "title": rec["title"],
        "organisation": rec["organisation"],
        "dataset_page": PORTAL_DATASET_PAGE[rec["portal"]].format(name=rec["name"]),
        "licence": licence,
        "licence_flag": flagged,
        "ckan_license_id": rec["license_id"],
        "dataset_modified": rec["metadata_modified"],
        "resource_id": res["id"],
        "resource_name": res["name"],
        "resource_format": res["format"],
        "resource_last_modified": res["last_modified"],
        "url": res["url"],
        "file": path.name,
        "bytes": size,
        "sha256": sha.hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    pool = {r["dataset_id"]: r for r in map(json.loads, POOL_PATH.open())}
    sources = yaml.safe_load(SOURCES_FILE.read_text())["sources"]
    manifest = []
    for s in sources:
        try:
            m = download(s, pool)
            manifest.append(m)
            flag = "  LICENCE FLAGGED" if m["licence_flag"] else ""
            print(f"ok   {s['source_id']:30s} {m['bytes'] / 1e6:7.1f} MB  {m['file']:45s} {m['licence']}{flag}")
        except Exception as e:  # one failed source must not stop the others
            print(f"FAIL {s['source_id']:30s} {type(e).__name__}: {e}")
    # data/raw is gitignored, so keep a committed record of exactly what was fetched
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"manifest -> {MANIFEST}")


if __name__ == "__main__":
    main()
