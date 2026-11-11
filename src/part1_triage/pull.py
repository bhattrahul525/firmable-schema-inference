"""Step 1 of triage: build the candidate pool from the CKAN catalogues.

We run a fixed list of search queries against each portal and de-duplicate.
Most queries lean towards business-heavy data (registers, licences, contracts)
because that is where the positives are. A few neutral queries ("*:*" etc.) are
included on purpose so the pool also contains plenty of non-business datasets,
otherwise the scorer would never be tested on negatives.

Output: outputs/part1_pool.jsonl  (one slimmed CKAN package per line)
Run:    python -m src.part1_triage.pull
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common.ckan import PORTALS, CkanClient

QUERIES = [
    # identifiers: the strongest hint a dataset names businesses
    "ABN", "ACN",
    # registers and licences: lists of who is allowed to do something
    "licence", "licensee", "register", "permit", "operator", "accredited",
    # money flowing to organisations
    "contracts", "tenders", "procurement", "supplier", "grants",
    # generic business words
    "business", "company",
    # neutral queries, mostly negatives, so the scorer sees non-business data too
    "*:*", "environment", "transport",
]
ROWS_PER_QUERY = 50
POOL_PATH = Path("outputs/part1_pool.jsonl")
NOTES_MAX_CHARS = 3000  # some descriptions embed images (800 KB); keep enough text to score


def slim(pkg: dict, portal: str) -> dict:
    """Keep only the fields triage needs. Full packages stay in the CKAN cache."""
    org = pkg.get("organization") or {}
    return {
        "dataset_id": f"{portal}:{pkg['name']}",  # unique across portals
        "portal": portal,
        "name": pkg["name"],
        "ckan_id": pkg.get("id"),
        "title": (pkg.get("title") or "").strip(),
        "organisation": org.get("title") or org.get("name") or "",
        "notes": (pkg.get("notes") or "")[:NOTES_MAX_CHARS],
        "tags": [t.get("name", "") for t in pkg.get("tags") or []],
        "license_id": pkg.get("license_id") or "",
        "license_title": pkg.get("license_title") or "",
        "metadata_modified": pkg.get("metadata_modified"),
        "resources": [
            {
                "id": r.get("id"),
                "name": (r.get("name") or "")[:200],
                "format": (r.get("format") or "").strip().upper(),
                "url": r.get("url") or "",
                "datastore_active": bool(r.get("datastore_active")),
                "size": r.get("size"),
                "last_modified": r.get("last_modified") or r.get("metadata_modified"),
            }
            for r in pkg.get("resources") or []
        ],
    }


def build_pool() -> tuple[list[dict], list[dict]]:
    pool: dict[str, dict] = {}
    errors: list[dict] = []
    for portal in PORTALS:
        client = CkanClient(portal)
        for q in QUERIES:
            try:
                result = client.package_search(q=q, rows=ROWS_PER_QUERY)
            except Exception as e:  # one dead portal/query must not kill the pull
                errors.append({"portal": portal, "query": q, "error": f"{type(e).__name__}: {e}"})
                continue
            for pkg in result.get("results", []):
                rec = slim(pkg, portal)
                if rec["dataset_id"] in pool:
                    pool[rec["dataset_id"]]["matched_queries"].append(q)
                else:
                    rec["matched_queries"] = [q]
                    pool[rec["dataset_id"]] = rec
            print(f"  {portal:10s} {q!r:14s} total={result.get('count', 0):>6}  pool={len(pool)}")
    return list(pool.values()), errors


def main() -> None:
    pool, errors = build_pool()
    POOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with POOL_PATH.open("w") as f:
        for rec in pool:
            f.write(json.dumps(rec) + "\n")
    by_portal: dict[str, int] = {}
    for r in pool:
        by_portal[r["portal"]] = by_portal.get(r["portal"], 0) + 1
    print(f"\npool: {len(pool)} unique datasets -> {POOL_PATH}  by portal: {by_portal}")
    for e in errors:
        print("  ERROR", e)


if __name__ == "__main__":
    main()
