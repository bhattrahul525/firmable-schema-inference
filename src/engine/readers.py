"""Read a raw file into (headers, rows) using the `reader:` section of a config.

Supported: csv, tsv, xlsx, json. Everything is loaded into memory (the biggest source here is
55 MB of JSON, which is fine). Each row is a dict {header: value}. Blank header cells get a
placeholder name so the agent can see the column exists and decide what to do with it.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

FORMATS = ("csv", "tsv", "xlsx", "json")


def _name_headers(cells: list) -> list[str]:
    """Strip header cells; blank -> '_blank_<position>'; duplicates get a numeric suffix."""
    names, seen = [], {}
    for i, c in enumerate(cells):
        n = " ".join(str(c).replace("\ufeff", "").split()) if c not in (None, "") else f"_blank_{i}"
        n = n or f"_blank_{i}"
        if n in seen:
            seen[n] += 1
            n = f"{n}__{seen[n]}"
        else:
            seen[n] = 1
        names.append(n)
    return names


def _flatten(d: dict, prefix: str = "") -> dict:
    """One level of nesting becomes 'outer.inner'. Deeper structures are kept as-is."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and not prefix:
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def read_raw_lines(path: Path, fmt: str, n: int = 12, encoding: str = "utf-8-sig") -> list[list]:
    """First n raw lines/rows with no interpretation, so the agent can see what the file is.
    Used by the inspect step before any reader settings are known."""
    if fmt == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        rows = []
        for r in ws.iter_rows(max_row=n, values_only=True):
            rows.append([c for c in r])
        return rows
    if fmt == "json":
        return [[path.open(encoding=encoding).read(3000)]]
    with path.open(encoding=encoding, errors="replace") as f:
        return [[line.rstrip("\r\n")[:400]] for _, line in zip(range(n), f)]


def sheet_names(path: Path) -> list[str]:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    return wb.sheetnames


def read_rows(reader: dict, path: Path) -> tuple[list[str], list[dict]]:
    fmt = reader["format"]
    if fmt not in FORMATS:
        raise ValueError(f"unsupported format {fmt!r}; supported: {FORMATS}")
    enc = reader.get("encoding") or "utf-8-sig"

    if fmt in ("csv", "tsv"):
        delim = reader.get("delimiter") or ("\t" if fmt == "tsv" else ",")
        text = path.read_text(encoding=enc, errors="replace")
        all_rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        return _rows_from_matrix(all_rows, reader.get("header_row", 1))

    if fmt == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet = reader.get("sheet") or wb.sheetnames[0]
        if sheet not in wb.sheetnames:
            raise ValueError(f"sheet {sheet!r} not found; have {wb.sheetnames}")
        matrix = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
        return _rows_from_matrix(matrix, reader.get("header_row", 1))

    # json: a list of objects, optionally under a dotted path
    data = json.loads(path.read_text(encoding=enc))
    for key in [k for k in (reader.get("records_path") or "").split(".") if k]:
        data = data[key]
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data[:50]):
        raise ValueError("json records_path must point at a list of objects")
    rows = [_flatten(x) for x in data]
    headers = list(dict.fromkeys(k for r in rows[:500] for k in r))
    return headers, rows


def _rows_from_matrix(matrix: list[list], header_row: int) -> tuple[list[str], list[dict]]:
    if not 1 <= header_row <= len(matrix):
        raise ValueError(f"header_row {header_row} outside file (has {len(matrix)} rows)")
    headers = _name_headers(matrix[header_row - 1])
    rows = []
    for r in matrix[header_row:]:
        if not any(c not in (None, "") for c in r):
            continue  # fully blank line
        r = list(r) + [None] * (len(headers) - len(r))
        rows.append(dict(zip(headers, r)))
    return headers, rows
