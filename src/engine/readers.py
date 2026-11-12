"""Read a raw file into rows using the `reader:` section of a config (ARCHITECTURE.md section c).

The readers are hand-written and tested. The agent only chooses OPTIONS; it never writes reader code.

  format            csv | tsv | xlsx | xls | json          (FORMATS, the round-1 four, is what the round-1 pipeline offers)
  encoding          csv/tsv/json text encoding (default utf-8-sig)
  delimiter, quote  csv/tsv (one character each)
  skip_rows         rows dropped before the header
  header_rows       0 (no header: col_1, col_2 ...), 1 (default) or n (n rows merged into one name; the upper rows are
                    filled rightwards over blanks, because merged header cells come out blank after the first column)
  skip_rows_after_header  raw rows dropped AFTER the header rows and before the data (label or note rows under the real
                    header). A count like skip_rows (blank lines count). Needs header_rows >= 1 (with 0 use skip_rows);
                    refused for json. Default 0, so every config without it reads exactly as before
  skip_footer_rows  last n NON-BLANK rows dropped
  drop_empty_columns  drop columns with a blank header that are also empty in the first 1,000 data rows
  sheet             xlsx / xls sheet name (default: the first)
  records_path      json: dotted path to the list of records ("features" for GeoJSON)
  flatten_depth     json: levels of nested objects turned into "outer.inner" columns (default 1)
  ndjson            json: one record per line
  archive, member   archive: "zip" or "gz"; for zip, `member` names the file inside. Dispatches to the format above.
  header_row        ROUND-1 option, still accepted: 1-based row number of the header (= skip_rows header_row-1, header_rows 1)

Streaming. Rows are produced one at a time by `iter_table`, so a delimited file, an xlsx sheet or an NDJSON file of any
size is read in constant memory. Two formats cannot be streamed and are loaded whole: a plain JSON array and an .xls
workbook. Archive members are NEVER extracted to disk: they are read through a stream that counts decompressed bytes and
stops at MAX_DECOMPRESSED_BYTES (1 GB), whatever the archive header claims (a zip bomb lies in its header).

Each row comes with a fingerprint (a hash of its raw cells, trailing blanks ignored, independent of header options). The
agent's held-out split is made of fingerprints, so it survives a re-read with different options.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import zipfile
from collections import deque
from contextlib import ExitStack, contextmanager
from itertools import chain, islice
from pathlib import Path
from typing import Callable, Iterator

FORMATS = ("csv", "tsv", "xlsx", "json")                  # round 1: what the pipeline's inspect step may choose
ALL_FORMATS = ("csv", "tsv", "xlsx", "xls", "json")       # round 2: what the readers can do
ARCHIVES = ("zip", "gz")
STREAM_ABOVE_BYTES = 50 * 1024 * 1024        # files over this are streamed on every call instead of cached in memory
MAX_DECOMPRESSED_BYTES = 1 << 30             # 1 GB, per archive member
MAX_WORKBOOK_BYTES = 200 * 1024 * 1024       # a workbook inside an archive (or any .xls) is loaded whole: smaller cap
HEADER_PEEK_ROWS = 1000
JSON_HEADER_ROWS = 500
CHECK_EVERY_ROWS = 2000                      # how often a row loop calls the cooperative deadline check


class ReaderError(ValueError):
    """A reader could not read the file. str(e) is a plain reason; it MAY contain dataset content (a sheet or member
    name), so the tools put it in a <data> payload, never in trusted text."""


# ---- small helpers (round 1, unchanged) ---------------------------------------------------------------------------

def _name_headers(cells: list) -> list[str]:
    """Strip header cells; blank -> '_blank_<position>'; duplicates get a numeric suffix."""
    names, seen = [], {}
    for i, c in enumerate(cells):
        n = " ".join(str(c).replace("﻿", "").split()) if c not in (None, "") else f"_blank_{i}"
        n = n or f"_blank_{i}"
        if n in seen:
            seen[n] += 1
            n = f"{n}__{seen[n]}"
        else:
            seen[n] = 1
        names.append(n)
    return names


def _flatten(d: dict, prefix: str = "", depth: int = 1) -> dict:
    """`depth` levels of nested objects become 'outer.inner'. Deeper structures, and lists, are kept as they are."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and depth > 0:
            out.update(_flatten(v, key + ".", depth - 1))
        else:
            out[key] = v
    return out


def row_fingerprint(cells) -> bytes:
    """Hash of a row's raw cells with trailing blanks removed. Same row, same fingerprint, whatever header options."""
    cells = list(cells)
    while cells and cells[-1] in (None, ""):
        cells.pop()
    return hashlib.blake2b(repr(cells).encode("utf-8", "replace"), digest_size=12).digest()


# ---- streams: archives and the decompression cap ------------------------------------------------------------------

class _CappedRaw(io.RawIOBase):
    """Counts bytes as they are DECOMPRESSED and fails when the total passes the cap. Counting is the only thing that can
    be trusted: a zip header can claim any size."""

    def __init__(self, inner, limit: int):
        self._inner, self._limit, self._n = inner, limit, 0

    def readable(self) -> bool:
        return True

    def readinto(self, b) -> int:
        data = self._inner.read(len(b))
        self._n += len(data)
        if self._n > self._limit:
            raise ReaderError(f"decompressed data passed the {self._limit:,} byte cap: refusing to read this archive "
                              f"member (possible zip bomb)")
        b[:len(data)] = data
        return len(data)


def _archive_error(e: Exception) -> ReaderError:
    return ReaderError(f"archive could not be read: {type(e).__name__}")


def zip_members(path: Path) -> list[zipfile.ZipInfo]:
    try:
        with zipfile.ZipFile(path) as zf:
            return [i for i in zf.infolist() if not i.is_dir()]
    except zipfile.BadZipFile as e:
        raise _archive_error(e)


@contextmanager
def _open_binary(reader: dict, path: Path):
    """A binary stream of the file, or of the archive member the reader names (never extracted to disk)."""
    archive = reader.get("archive")
    if not archive:
        with path.open("rb") as f:
            yield f
        return
    if archive not in ARCHIVES:
        raise ReaderError(f"archive must be one of {ARCHIVES}")
    limit = MAX_DECOMPRESSED_BYTES
    try:
        if archive == "gz":
            with gzip.open(path, "rb") as raw:
                yield io.BufferedReader(_CappedRaw(raw, limit))
            return
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            names = [i.filename for i in infos]
            member = reader.get("member")
            if member is None:
                if len(names) != 1:
                    raise ReaderError(f"zip has {len(names)} members; set `member` to one of {names[:50]}")
                member = names[0]
            if member not in names:
                raise ReaderError(f"member {member!r} is not in the archive; members: {names[:50]}")
            info = zf.getinfo(member)
            if info.file_size > limit:
                raise ReaderError(f"member declares {info.file_size:,} decompressed bytes, over the {limit:,} cap")
            with zf.open(info) as raw:
                yield io.BufferedReader(_CappedRaw(raw, limit))
    except zipfile.BadZipFile as e:
        raise _archive_error(e)
    except (gzip.BadGzipFile, EOFError, RuntimeError) as e:   # RuntimeError: encrypted zip member
        raise _archive_error(e)


def _text_stream(reader: dict, stream) -> io.TextIOWrapper:
    enc = reader.get("encoding") or "utf-8-sig"
    try:
        # newline=None: universal newlines, exactly what Path.read_text did in round 1
        return io.TextIOWrapper(stream, encoding=enc, errors="replace")
    except LookupError:
        raise ReaderError(f"unknown encoding {enc!r}")


# ---- matrix readers: raw cell lists --------------------------------------------------------------------------------

def _csv_matrix(reader: dict, stack: ExitStack, path: Path) -> Iterator[list]:
    stream = stack.enter_context(_open_binary(reader, path))
    delim = reader.get("delimiter") or ("\t" if reader["format"] == "tsv" else ",")
    quote = reader.get("quote") or '"'
    if len(delim) != 1 or len(quote) != 1:
        raise ReaderError("delimiter and quote must each be a single character")
    text = _text_stream(reader, stream)
    csv.field_size_limit(10_000_000)
    try:
        yield from csv.reader(text, delimiter=delim, quotechar=quote)
    except csv.Error as e:
        raise ReaderError(f"csv could not be parsed: {e}")
    except (zipfile.BadZipFile, gzip.BadGzipFile, EOFError) as e:
        raise _archive_error(e)
    finally:
        try:
            text.detach()
        except ValueError:
            pass


def _workbook_source(reader: dict, stack: ExitStack, path: Path):
    """A path for a plain workbook; for one inside an archive, the decompressed bytes (capped, loaded whole)."""
    if not reader.get("archive"):
        return path
    stream = stack.enter_context(_open_binary(reader, path))
    data = stream.read(MAX_WORKBOOK_BYTES + 1)
    if len(data) > MAX_WORKBOOK_BYTES:
        raise ReaderError(f"a workbook inside an archive is loaded whole and may not exceed {MAX_WORKBOOK_BYTES:,} bytes")
    return io.BytesIO(data)


def _xlsx_matrix(reader: dict, stack: ExitStack, path: Path) -> Iterator[list]:
    import openpyxl
    source = _workbook_source(reader, stack, path)
    try:
        wb = openpyxl.load_workbook(source, read_only=True, data_only=True)
    except (zipfile.BadZipFile, KeyError, OSError, ValueError) as e:
        raise ReaderError(f"not a readable xlsx workbook: {type(e).__name__}")
    except Exception as e:   # openpyxl raises its own InvalidFileException
        raise ReaderError(f"not a readable xlsx workbook: {type(e).__name__}")
    try:
        names = wb.sheetnames
        if not names:
            raise ReaderError("the workbook has no sheets")
        sheet = reader.get("sheet") or names[0]
        if sheet not in names:
            raise ReaderError(f"sheet {sheet!r} not found; sheets: {names}")
        for r in wb[sheet].iter_rows(values_only=True):
            yield list(r)
    finally:
        wb.close()


def _xls_cells(book, ws, i: int) -> list:
    import xlrd
    out = []
    for c in ws.row(i):
        t = c.ctype
        if t in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK, xlrd.XL_CELL_ERROR):
            out.append(None)
        elif t == xlrd.XL_CELL_DATE:
            try:
                out.append(xlrd.xldate.xldate_as_datetime(c.value, book.datemode))   # a real datetime, like openpyxl
            except Exception:
                out.append(c.value)
        elif t == xlrd.XL_CELL_BOOLEAN:
            out.append(bool(c.value))
        else:
            out.append(c.value)
    return out


def _open_xls(reader: dict, stack: ExitStack, path: Path):
    import xlrd
    source = _workbook_source(reader, stack, path)
    try:
        if isinstance(source, Path):
            if source.stat().st_size > MAX_WORKBOOK_BYTES:
                raise ReaderError(f"an .xls workbook is loaded whole and may not exceed {MAX_WORKBOOK_BYTES:,} bytes")
            book = xlrd.open_workbook(filename=str(source))
        else:
            book = xlrd.open_workbook(file_contents=source.getvalue())
    except ReaderError:
        raise
    except Exception as e:
        raise ReaderError(f"not a readable xls workbook: {type(e).__name__}")
    stack.callback(book.release_resources)
    return book


def _xls_matrix(reader: dict, stack: ExitStack, path: Path) -> Iterator[list]:
    book = _open_xls(reader, stack, path)
    names = book.sheet_names()
    if not names:
        raise ReaderError("the workbook has no sheets")
    sheet = reader.get("sheet") or names[0]
    if sheet not in names:
        raise ReaderError(f"sheet {sheet!r} not found; sheets: {names}")
    ws = book.sheet_by_name(sheet)
    for i in range(ws.nrows):
        yield _xls_cells(book, ws, i)


def workbook_sheets(reader: dict, path: Path) -> list[dict]:
    """[{name, rows, cols, state}] for an xlsx or xls workbook (the reader dict may name an archive member)."""
    fmt = reader.get("format")
    with ExitStack() as stack:
        if fmt == "xls":
            book = _open_xls(reader, stack, path)
            out = []
            for i, name in enumerate(book.sheet_names()):
                ws = book.sheet_by_index(i)
                out.append({"name": name, "rows": ws.nrows, "cols": ws.ncols, "state": "visible" if ws.visibility == 0 else "hidden"})
            return out
        import openpyxl
        source = _workbook_source(reader, stack, path)
        try:
            wb = openpyxl.load_workbook(source, read_only=True, data_only=True)
        except Exception as e:
            raise ReaderError(f"not a readable xlsx workbook: {type(e).__name__}")
        try:
            return [{"name": ws.title, "rows": ws.max_row, "cols": ws.max_column, "state": ws.sheet_state}
                    for ws in (wb[n] for n in wb.sheetnames)]
        finally:
            wb.close()


# ---- header handling -----------------------------------------------------------------------------------------------

def _layout(reader: dict) -> tuple[int, int, int, int]:
    """(skip_rows, header_rows, skip_footer_rows, skip_rows_after_header), with the round-1 `header_row` accepted."""
    def num(key, default):
        v = reader.get(key, default)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ReaderError(f"{key} must be a non-negative integer")
        return v
    drop = num("skip_rows_after_header", 0)
    if "header_row" in reader and "skip_rows" not in reader and "header_rows" not in reader:
        hr = reader["header_row"]
        if isinstance(hr, bool) or not isinstance(hr, int) or hr < 1:
            raise ReaderError("header_row must be an integer of at least 1")
        return hr - 1, 1, num("skip_footer_rows", 0), drop
    nh = num("header_rows", 1)
    if drop and nh == 0:
        raise ReaderError("skip_rows_after_header needs header_rows of at least 1; with header_rows 0 use skip_rows")
    return num("skip_rows", 0), nh, num("skip_footer_rows", 0), drop


def _merge_headers(rows: list[list]) -> list:
    """n header rows -> one name per column. Upper rows are filled rightwards over blanks (merged cells)."""
    width = max(len(r) for r in rows)
    filled = []
    for k, r in enumerate(rows):
        r = list(r) + [None] * (width - len(r))
        if k < len(rows) - 1:
            last = None
            for i, c in enumerate(r):
                if c in (None, ""):
                    r[i] = last
                else:
                    last = c
        filled.append(r)
    merged = []
    for i in range(width):
        parts = [" ".join(str(r[i]).split()) for r in filled if r[i] not in (None, "")]
        merged.append(" ".join(parts) if parts else None)
    return merged


def _table_from_matrix(reader: dict, matrix: Iterator[list], check: Callable | None):
    skip, nh, footer, drop = _layout(reader)
    it = iter(matrix)
    seen_rows = 0
    for _ in range(skip):
        if next(it, None) is None:
            raise ReaderError(f"skip_rows {skip} is outside the file")
        seen_rows += 1
    if nh == 0:
        first = next(it, None)
        if first is None:
            raise ReaderError("the file has no data rows")
        headers = [f"col_{i + 1}" for i in range(len(first))]
        it = chain([first], it)
    else:
        head = []
        for _ in range(nh):
            r = next(it, None)
            if r is None:
                raise ReaderError(f"header_rows {nh} (after skip_rows {skip}) is outside the file")
            head.append(r)
        headers = _name_headers(head[0] if nh == 1 else _merge_headers(head))
        for _ in range(drop):   # label or note rows directly under the header: raw rows, blank lines count
            if next(it, None) is None:
                raise ReaderError(f"skip_rows_after_header {drop} (after the header rows) is outside the file")
    keep = list(range(len(headers)))
    peek: list = []
    if reader.get("drop_empty_columns"):
        peek = list(islice(it, HEADER_PEEK_ROWS))
        blank = [i for i, h in enumerate(headers) if h.startswith("_blank_")
                 and not any(i < len(r) and r[i] not in (None, "") for r in peek)]
        keep = [i for i in range(len(headers)) if i not in set(blank)]
        it = chain(peek, it)
    names = [headers[i] for i in keep]
    full_width = len(headers)

    def rows():
        buf: deque = deque()
        for n, r in enumerate(it):
            if check and n % CHECK_EVERY_ROWS == 0:
                check()
            r = list(r)
            if not any(c not in (None, "") for c in r):
                continue   # fully blank line
            fp = row_fingerprint(r)
            r = r + [None] * (full_width - len(r))
            item = (fp, {headers[i]: r[i] for i in keep})
            if footer:
                buf.append(item)
                if len(buf) > footer:
                    yield buf.popleft()
            else:
                yield item
    return names, rows()


# ---- json ----------------------------------------------------------------------------------------------------------

def _json_records(reader: dict, stack: ExitStack, path: Path) -> Iterator[dict]:
    stream = stack.enter_context(_open_binary(reader, path))
    text = _text_stream(reader, stream)
    try:
        if reader.get("ndjson"):
            for n, line in enumerate(text, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    raise ReaderError(f"line {n} is not valid JSON (ndjson expects one JSON object per line)")
                if not isinstance(rec, dict):
                    raise ReaderError(f"line {n} is not a JSON object")
                yield rec
            return
        try:
            data = json.load(text)
        except json.JSONDecodeError as e:
            raise ReaderError(f"not valid JSON: {e.msg} at line {e.lineno}")
        except RecursionError:
            raise ReaderError("JSON is nested too deeply")
        for key in [k for k in (reader.get("records_path") or "").split(".") if k]:
            if not isinstance(data, dict) or key not in data:
                keys = list(data)[:30] if isinstance(data, dict) else f"(a {type(data).__name__}, not an object)"
                raise ReaderError(f"records_path key {key!r} not found; keys here: {keys}")
            data = data[key]
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data[:50]):
            hint = ""
            if isinstance(data, dict):
                hint = f" Keys that hold lists: {[k for k, v in data.items() if isinstance(v, list)][:20]}"
            raise ReaderError("json records_path must point at a list of objects." + hint)
        yield from data
    finally:
        try:
            text.detach()
        except ValueError:
            pass


def _json_table(reader: dict, stack: ExitStack, path: Path, check: Callable | None):
    if reader.get("skip_rows_after_header"):
        raise ReaderError("skip_rows_after_header applies to the table formats (csv, tsv, xlsx, xls), not json")
    depth = reader.get("flatten_depth", 1)
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        raise ReaderError("flatten_depth must be a non-negative integer")
    records = _json_records(reader, stack, path)
    head = list(islice(records, JSON_HEADER_ROWS))
    if not head:
        raise ReaderError("the file has no records")
    headers = list(dict.fromkeys(k for r in head for k in _flatten(r, depth=depth)))

    def rows():
        for n, rec in enumerate(chain(head, records)):
            if check and n % CHECK_EVERY_ROWS == 0:
                check()
            fp = hashlib.blake2b(json.dumps(rec, sort_keys=True, default=str).encode(), digest_size=12).digest()
            yield fp, _flatten(rec, depth=depth)
    return headers, rows()


# ---- public API ----------------------------------------------------------------------------------------------------

@contextmanager
def iter_table(reader: dict, path: Path, check: Callable | None = None):
    """`with iter_table(reader, path) as (headers, rows):` rows yields (fingerprint, {header: value}) one at a time.
    `check` is called every CHECK_EVERY_ROWS rows (the harness passes its cooperative deadline here)."""
    fmt = reader.get("format")
    if fmt not in ALL_FORMATS:
        raise ReaderError(f"unsupported format {fmt!r}; supported: {ALL_FORMATS}")
    with ExitStack() as stack:
        if fmt == "json":
            headers, rows = _json_table(reader, stack, path, check)
        else:
            matrix = {"csv": _csv_matrix, "tsv": _csv_matrix, "xlsx": _xlsx_matrix, "xls": _xls_matrix}[fmt](reader, stack, path)
            headers, rows = _table_from_matrix(reader, matrix, check)
        yield headers, rows


def read_rows(reader: dict, path: Path) -> tuple[list[str], list[dict]]:
    """Round-1 API: everything in memory as (headers, [row dicts])."""
    with iter_table(reader, path) as (headers, rows):
        return headers, [r for _, r in rows]


def raw_head(reader: dict, path: Path, n: int = 12) -> list[list]:
    """The first n RAW rows of the file with NO layout applied (skip_rows, header_rows, skip_rows_after_header and
    skip_footer_rows are ignored; format, encoding, delimiter, quote, sheet, archive/member and the json options are
    honoured). Matrix formats return cell lists, blank rows included, numbered as `skip_rows` counts them; json returns
    the first n raw records. The agent's held-out split protects exactly these rows (agent_table.py), so showing them
    never reveals a held-out row."""
    fmt = reader.get("format")
    if fmt not in ALL_FORMATS:
        raise ReaderError(f"unsupported format {fmt!r}; supported: {ALL_FORMATS}")
    keep = ("format", "encoding", "delimiter", "quote", "sheet", "archive", "member", "records_path", "flatten_depth", "ndjson")
    base = {k: reader[k] for k in keep if k in reader}
    with ExitStack() as stack:
        if fmt == "json":
            return [[r] for r in islice(_json_records(base, stack, path), n)]
        matrix = {"csv": _csv_matrix, "tsv": _csv_matrix, "xlsx": _xlsx_matrix, "xls": _xls_matrix}[fmt](base, stack, path)
        return [list(r) for r in islice(matrix, n)]


def raw_head_fingerprints(reader: dict, path: Path, n: int = 12) -> frozenset:
    """Fingerprints of the first n raw rows (blank rows have none). For json, the record fingerprint _json_table uses."""
    if reader.get("format") == "json":
        fps = []
        for (rec,) in raw_head(reader, path, n):
            fps.append(hashlib.blake2b(json.dumps(rec, sort_keys=True, default=str).encode(), digest_size=12).digest())
        return frozenset(fps)
    return frozenset(row_fingerprint(r) for r in raw_head(reader, path, n)
                     if any(c not in (None, "") for c in r))


def read_raw_lines(path: Path, fmt: str, n: int = 12, encoding: str = "utf-8-sig") -> list[list]:
    """First n raw lines/rows with no interpretation, so the agent can see what the file is.
    Used by the round-1 inspect step before any reader settings are known."""
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


def layout_description(reader: dict) -> str:
    """The applied layout in words written by CODE (not the model): which raw row gave the column names, which raw
    rows were dropped, and where data starts. Used by read_table's result and the review packet, so the human and the
    agent see the same sentence next to the numbered raw rows (item A/E, step 3b)."""
    if reader.get("format") == "json":
        return ""
    try:
        skip, nh, _footer, drop = _layout(reader)
    except ReaderError:
        return ""
    if nh == 0:
        return f"no header row (generated column names); data starts at raw row {skip + 1}."
    dropped = f" raw rows {skip + nh + 1}-{skip + nh + drop} dropped;" if drop else ""
    names = f"raw row {skip + 1}" if nh == 1 else f"raw rows {skip + 1}-{skip + nh} (merged)"
    return f"column names from {names};{dropped} data starts at raw row {skip + nh + drop + 1}."


def sheet_names(path: Path) -> list[str]:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    return wb.sheetnames
