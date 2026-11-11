"""Step 3 of triage: look inside the data, not just the metadata.

For one tabular resource per dataset we read ~200 rows and measure three things:
  * abn_rate     - best column's share of values that are checksum-valid ABNs
  * suffix_rate  - best column's share of values with a company suffix (Pty Ltd, Limited, Inc...)
  * header_hits  - column names that look like business fields (abn, licensee, supplier...)

These are facts about the rows, which is much stronger evidence than a title.
Reading is capped (first 1 MB of a CSV, XLSX up to 25 MB) so one huge file
cannot stall the run. Results are cached on disk so reruns are free.

Limits (stated, not hidden): ZIP, XML, PDF, legacy XLS and APIs are not probed;
those datasets fall back to their metadata score, capped (see run.py).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path

from src.common.ckan import CkanClient, http_session
from src.common.ids import normalise_abn

PROBE_CACHE = Path("data/raw/catalogue/probe_cache")
SAMPLE_ROWS = 200
CSV_MAX_BYTES = 1_000_000
FILE_MAX_BYTES = 25_000_000  # XLSX/JSON must be read whole

BUSINESS_HEADER = re.compile(
    r"\babn\b|\bacn\b|business|company|trading|licensee|licen[cs]e holder|supplier|vendor|"
    r"contractor|entity|organi[sz]ation|employer|operator|recipient|applicant|legal.?name|proprietor|firm",
    re.I,
)
# A suffix must END the value ("Acme Limited"), so "Limited tender" does not count.
# "Pty Ltd" and "trustee for" are distinctive enough to count anywhere.
COMPANY_SUFFIX = re.compile(
    r"\b(pty\.?\s*ltd|pty\.?\s*limited|limited|ltd|inc|incorporated|corporation|co-?operative)\.?\)?\s*$"
    r"|\bpty\.?\s*(ltd|limited)\b|\btrustee for\b",
    re.I,
)
ABN_NOISE_FLOOR = 0.2  # random 11-digit numbers pass the checksum ~1.1% of the time

# preference order when a dataset has several tabular resources
_KINDS = ["CSV", "TSV", "XLSX", "JSON"]


def _kind(res: dict) -> str | None:
    fmt, url = res["format"], res["url"].lower().split("?")[0]
    for k in _KINDS:
        if k in fmt or url.endswith("." + k.lower()):
            return k
    return None


def pick_resource(rec: dict) -> tuple[dict, str] | None:
    """Datastore-backed resources first (structured, fast), then by format preference."""
    candidates = [(r, _kind(r)) for r in rec["resources"]]
    candidates = [(r, k) for r, k in candidates if k]
    if not candidates:
        return None
    candidates.sort(key=lambda rk: (not rk[0]["datastore_active"], _KINDS.index(rk[1])))
    return candidates[0]


# ---------- readers: each returns (headers, rows as list[dict]) ----------

def _find_header(rows: list[list]) -> int:
    """Index of the header row: the first row (of the first 20) that is at least half
    as wide as the widest row. Skips title lines that some publishers put above the header."""
    widths = [sum(1 for c in r if str(c or "").strip()) for r in rows[:20]]
    if not widths:
        return 0
    target = max(widths) / 2
    return next(i for i, w in enumerate(widths) if w >= target and w >= 2) if max(widths) >= 2 else 0


def _to_dicts(rows: list[list]) -> tuple[list[str], list[dict]]:
    h = _find_header(rows)
    headers = [str(c or "").strip() or f"col_{i}" for i, c in enumerate(rows[h])] if rows else []
    out = []
    for r in rows[h + 1 : h + 1 + SAMPLE_ROWS]:
        if any(str(c or "").strip() for c in r):
            out.append({headers[i]: ("" if c is None else str(c)) for i, c in enumerate(r[: len(headers)])})
    return headers, out


def read_csv_bytes(data: bytes, truncated: bool) -> tuple[list[str], list[dict]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    if truncated:  # drop the partial last line
        text = text[: text.rfind("\n")]
    try:
        dialect = csv.Sniffer().sniff(text[:5000], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))[: SAMPLE_ROWS + 25]
    return _to_dicts(rows)


def read_xlsx_bytes(data: bytes) -> tuple[list[str], list[dict]]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    for ws in wb.worksheets:  # first sheet that has a real table
        rows = [list(r) for _, r in zip(range(SAMPLE_ROWS + 25), ws.iter_rows(values_only=True))]
        headers, out = _to_dicts(rows)
        if out:
            return headers, out
    return [], []


def _first_list_of_dicts(obj, depth: int = 0):
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj
    if isinstance(obj, dict) and depth < 3:
        for v in obj.values():
            found = _first_list_of_dicts(v, depth + 1)
            if found:
                return found
    return None


def read_json_bytes(data: bytes) -> tuple[list[str], list[dict]]:
    records = _first_list_of_dicts(json.loads(data)) or []
    rows = [{k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in r.items()}
            for r in records[:SAMPLE_ROWS]]
    headers = list(rows[0].keys()) if rows else []
    return headers, rows


def fetch_sample(portal: str, res: dict, kind: str) -> tuple[list[str], list[dict], str]:
    """Returns (headers, rows, method). Raises on failure."""
    if res["datastore_active"]:
        try:
            result = CkanClient(portal).datastore_search(res["id"], limit=SAMPLE_ROWS)
            rows = [{k: ("" if v is None else str(v)) for k, v in r.items() if k != "_id"}
                    for r in result.get("records", [])]
            headers = [f["id"] for f in result.get("fields", []) if f["id"] != "_id"]
            if rows:
                return headers, rows, "datastore_search"
        except Exception:
            pass  # fall through to downloading the file

    limit = CSV_MAX_BYTES if kind in ("CSV", "TSV") else FILE_MAX_BYTES
    with http_session(retries=1).get(res["url"], stream=True, timeout=(10, 30)) as resp:
        resp.raise_for_status()
        size = int(resp.headers.get("Content-Length") or 0)
        if kind not in ("CSV", "TSV") and size > FILE_MAX_BYTES:
            raise ValueError(f"{kind} too large to probe ({size / 1e6:.0f} MB)")
        buf = bytearray()
        for chunk in resp.iter_content(64 * 1024):
            buf.extend(chunk)
            if len(buf) >= limit:
                break
    truncated = len(buf) >= limit
    if kind != "CSV" and kind != "TSV" and truncated:
        raise ValueError(f"{kind} exceeded {limit / 1e6:.0f} MB")
    data = bytes(buf)
    if data[:2] == b"PK" and kind != "XLSX":  # a zip/xlsx served under another label
        return (*read_xlsx_bytes(data), "download:xlsx-sniffed")
    if data.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
        raise ValueError("URL returned an HTML page, not data")
    if kind in ("CSV", "TSV"):
        return (*read_csv_bytes(data, truncated), "download:csv")
    if kind == "XLSX":
        return (*read_xlsx_bytes(data), "download:xlsx")
    return (*read_json_bytes(data), "download:json")


# ---------- measurements ----------

def measure(headers: list[str], rows: list[dict]) -> dict:
    header_hits = [h for h in headers if BUSINESS_HEADER.search(h)]
    best_abn = (0.0, None)
    best_suffix = (0.0, None)
    for h in headers:
        values = [r.get(h, "").strip() for r in rows]
        values = [v for v in values if v]
        if len(values) < 5:
            continue
        abn_rate = sum(1 for v in values if normalise_abn(v)) / len(values)
        if abn_rate > best_abn[0]:
            best_abn = (abn_rate, h)
        suffix_rate = sum(1 for v in values if COMPANY_SUFFIX.search(v)) / len(values)
        if suffix_rate > best_suffix[0]:
            best_suffix = (suffix_rate, h)
    if best_abn[0] < ABN_NOISE_FLOOR:  # a few stray checksum passes are noise, not an ABN column
        best_abn = (0.0, None)

    probe = (
        0.45 * min(1.0, best_abn[0] / 0.5)  # half the rows carrying a valid ABN = full marks
        + 0.35 * min(1.0, best_suffix[0] / 0.3)  # 30% company-suffixed names = full marks
        + 0.20 * min(1.0, len(header_hits) / 2)
    )
    return {
        "abn_rate": round(best_abn[0], 3), "abn_column": best_abn[1],
        "suffix_rate": round(best_suffix[0], 3), "suffix_column": best_suffix[1],
        "header_hits": header_hits,
        "probe_score": round(probe, 3),
    }


def probe_dataset(rec: dict) -> dict:
    picked = pick_resource(rec)
    if not picked:
        return {"probe_status": "skipped", "probe_error": "no CSV/XLSX/JSON resource"}
    res, kind = picked
    key = hashlib.sha1(f"{res['id']}|{res['url']}".encode()).hexdigest()[:16]
    cache = PROBE_CACHE / f"{key}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    out = {"probe_resource_id": res["id"], "probe_url": res["url"], "probe_kind": kind}
    try:
        headers, rows, method = fetch_sample(rec["portal"], res, kind)
        if not rows:
            raise ValueError("no rows found")
        out.update(probe_status="ok", probe_method=method, rows_read=len(rows), **measure(headers, rows))
        out["sample_headers"] = headers[:30]
        out["sample_rows"] = [{k: v[:80] for k, v in list(r.items())[:30]} for r in rows[:3]]
    except Exception as e:
        out.update(probe_status="failed", probe_error=f"{type(e).__name__}: {str(e)[:200]}")
    PROBE_CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out
