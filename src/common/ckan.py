"""Minimal CKAN Action API client with an on-disk response cache.

Why a cache: Part 1 makes a few hundred catalogue calls. Caching makes reruns free,
makes results reproducible (same input -> same shortlist), and keeps the
"clean checkout runs in < 10 minutes" promise. Delete data/raw/catalogue/cache/ to
force a fresh pull.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Each portal's Action API base. These differ, checked by hand on 2026-11-11.
PORTALS: dict[str, str] = {
    "datagovau": "https://data.gov.au/data/api/3/action/",
    "nsw": "https://data.nsw.gov.au/data/api/3/action/",
    "sa": "https://data.sa.gov.au/data/api/3/action/",
    "qld": "https://www.data.qld.gov.au/api/3/action/",
    "vic": "https://discover.data.vic.gov.au/api/3/action/",
}

CACHE_DIR = Path("data/raw/catalogue/cache")
USER_AGENT = "schema-inference-case-study/0.1 (research; python-requests)"


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,  # 1s, 2s, 4s
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = USER_AGENT
    return s


class CkanClient:
    def __init__(self, portal: str, cache_dir: Path = CACHE_DIR, polite_delay: float = 0.2):
        if portal not in PORTALS:
            raise ValueError(f"unknown portal {portal!r}; known: {sorted(PORTALS)}")
        self.portal = portal
        self.base_url = PORTALS[portal]
        self.cache_dir = cache_dir / portal
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.polite_delay = polite_delay  # seconds between uncached calls
        self.session = _session()

    def _cache_path(self, action: str, params: dict) -> Path:
        key = json.dumps({"action": action, "params": params}, sort_keys=True)
        return self.cache_dir / f"{action}-{hashlib.sha1(key.encode()).hexdigest()[:16]}.json"

    def call(self, action: str, timeout: float = 30.0, **params) -> dict:
        """Call a CKAN action and return its `result`. Raises on API-level failure."""
        path = self._cache_path(action, params)
        if path.exists():
            return json.loads(path.read_text())["result"]

        resp = self.session.get(self.base_url + action, params=params, timeout=timeout)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            raise RuntimeError(f"{self.portal} {action} failed: {body.get('error')}")
        path.write_text(json.dumps(body))
        time.sleep(self.polite_delay)
        return body["result"]

    def package_search(self, q: str = "*:*", rows: int = 100, start: int = 0, **extra) -> dict:
        return self.call("package_search", q=q, rows=rows, start=start, **extra)

    def package_show(self, id: str) -> dict:
        return self.call("package_show", id=id)

    def datastore_search(self, resource_id: str, limit: int = 20) -> dict:
        return self.call("datastore_search", resource_id=resource_id, limit=limit)
