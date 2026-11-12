"""The round-2 agent's tools (ARCHITECTURE.md section b), as one `AgentKit` per run.

Rules every tool here follows (the status contract in tools.py):
  * `ToolResult.text` is OUR words: counts, closed vocabulary, instructions. Never a column name, cell value, file name,
    sheet name or reader error detail. All of that goes in `payload`, which the harness caps and wraps in <data>.
  * A tool puts a machine-readable fact in `status` only where the guard reads one (validate, critique, fetch).
  * A failure is an error result with a plain reason, never an exception the model can see a stack trace of.
  * Long loops call ctx.check_deadline(), the cooperative half of the per-tool timeout.

Which rows each tool may touch (agent_table.py explains the split):
  training rows  read_table (first rows), sample, search, profile, check_unique, try_transform
  held-out rows  validate, critique and the harness's own finalise hooks ONLY

`AgentKit.tools` is the registry handed to the loop and `AgentKit.hooks` the finalise hooks; both share one state
(questions asked, critiques made) so the packet can report them.
"""

from __future__ import annotations

import codecs
import csv
import hashlib
import io
import random
import re
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from src.common.ckan import PORTAL_DATASET_PAGE
from src.common.ids import digits_only
from src.engine.config import _check_transforms, load_ontology, normalise_transforms
from src.engine.extract import FieldStats, _is_blank, _ontology_ok, _value_of, apply_transforms
from src.engine.readers import (ALL_FORMATS, ARCHIVES, MAX_DECOMPRESSED_BYTES, ReaderError, _open_binary, workbook_sheets,
                                zip_members)
from src.engine.transforms import _COMPANY_END, CATALOGUE, clean_whitespace
from src.part1_triage.pull import slim
from src.part1_triage.run import licence_of
from src.part2_agent import agent_hooks as hooks_mod
from src.part2_agent.agent_table import (RAW_DIR, NoTable, build_table, get_table, input_info, input_path, remember_table,
                                         save_input)
from src.part2_agent.guard import FetchRefused
from src.part2_agent.loop import FinaliseHooks
from src.part2_agent.profile import _DATE_LIKE, trim_row
from src.part2_agent.tools import ToolContext, ToolResult, ToolSpec, registry

MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024     # the fetch cap, enforced while streaming
PROGRESS_EVERY_BYTES = 10 * 1024 * 1024
SNIFF_BYTES = 64 * 1024
DISTINCT_CAP = 200_000
TRY_ROWS = 1000
MAX_PATTERN_CHARS = 200
MEMBER_LIST_CAP = 50


def fail(text: str, detail=None, **status) -> ToolResult:
    return ToolResult(text=text, payload=detail, is_error=True, status=status)


def _int_arg(args: dict, key: str, default: int, lo: int, hi: int) -> int:
    v = args.get(key, default)
    return max(lo, min(hi, v))


# ---- file kind and encoding ----------------------------------------------------------------------------------------

_EXT_KIND = {".csv": "text", ".tsv": "text", ".txt": "text", ".json": "text", ".ndjson": "text", ".jsonl": "text",
             ".xlsx": "xlsx", ".xlsm": "xlsx", ".xls": "ole2", ".zip": "zip", ".gz": "gzip", ".pdf": "pdf"}


def detect_kind(head: bytes, names: list[str] | None = None) -> str:
    """Closed vocabulary: empty, zip, xlsx, ole2 (an old .xls), gzip, pdf, xml, html, text, binary."""
    if not head:
        return "empty"
    if head[:2] == b"PK":
        if names is not None and "[Content_Types].xml" in names and any(n.startswith("xl/") for n in names):
            return "xlsx"
        return "zip"
    if head[:8] == bytes.fromhex("D0CF11E0A1B11AE1"):
        return "ole2"
    if head[:2] == b"\x1f\x8b":
        return "gzip"
    if head[:4] == b"%PDF":
        return "pdf"
    probe = head[:512].lstrip().lower()
    if probe.startswith(b"<?xml"):
        return "xml"
    if probe.startswith(b"<!doctype html") or probe.startswith(b"<html"):
        return "html"
    if b"\x00" in head[:4096] and not head.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE)):
        return "binary"
    return "text"


def guess_encoding(head: bytes) -> str:
    for bom, name in ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF32_LE, "utf-32"), (codecs.BOM_UTF32_BE, "utf-32"),
                      (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16")):
        if head.startswith(bom):
            return name
    try:
        codecs.getincrementaldecoder("utf-8")().decode(head, final=False)   # a cut-off last character is not an error
        return "utf-8"
    except UnicodeDecodeError:
        return "cp1252"   # a superset of latin-1 for printable text; the model can still try latin-1


def guess_delimiter(text: str) -> str | None:
    lines = [l for l in text.splitlines()[:30] if l.strip()]
    if len(lines) < 2:
        return None
    try:
        d = csv.Sniffer().sniff("\n".join(lines), delimiters=",;\t|").delimiter
        if all(l.count(d) > 0 for l in lines[:10]):
            return d
    except csv.Error:
        pass
    best = None
    for d in ",;\t|":
        counts = {l.count(d) for l in lines[:10]}
        if len(counts) == 1 and counts != {0}:
            best = d if best is None or lines[0].count(d) > lines[0].count(best) else best
    return best


def _archive_kind(path: Path, kind: str) -> str | None:
    return {"zip": "zip", "gzip": "gz"}.get(kind)


def _head_of(path: Path, member: str | None, archive: str | None) -> tuple[bytes, list[str] | None]:
    """First SNIFF_BYTES of the file, or of an archive member. Also the zip's member names (to tell xlsx from a zip)."""
    names = None
    with path.open("rb") as f:
        magic = f.read(4)
    if magic[:2] == b"PK":
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
        except zipfile.BadZipFile:
            names = None
    if archive:
        with _open_binary({"archive": archive, "member": member}, path) as s:
            return s.read(SNIFF_BYTES), None
    with path.open("rb") as f:
        return f.read(SNIFF_BYTES), names


# ---- streaming profile ---------------------------------------------------------------------------------------------

class _Col:
    __slots__ = ("present", "counter", "capped", "length", "d11", "d9", "date", "suffix", "semi")

    def __init__(self):
        self.present = self.length = self.d11 = self.d9 = self.date = self.suffix = self.semi = 0
        self.counter: Counter = Counter()
        self.capped = False

    def add(self, v: str) -> None:
        self.present += 1
        self.length += len(v)
        if v in self.counter or len(self.counter) < DISTINCT_CAP:
            self.counter[v] += 1
        else:
            self.capped = True
        d = len(digits_only(v))
        self.d11 += d == 11
        self.d9 += d == 9
        self.date += bool(_DATE_LIKE.match(v))
        self.suffix += bool(_COMPANY_END.search(v))
        self.semi += ";" in v

    def summary(self, name: str, n: int) -> dict:
        out = {"column": name, "fill_rate": round(self.present / n, 3) if n else 0, "distinct": len(self.counter)}
        if self.capped:
            out["capped"] = True
        out["top_values"] = [[v[:50], k] for v, k in self.counter.most_common(5)]
        out["avg_length"] = round(self.length / self.present, 1) if self.present else 0
        if self.present:
            shape = {"pct_11_digits": self.d11, "pct_9_digits": self.d9, "pct_date_like": self.date,
                     "pct_company_suffix": self.suffix, "pct_contains_semicolon": self.semi}
            out["shape"] = {k: round(v / self.present, 3) for k, v in shape.items() if v}
        return out


# ---- the kit -------------------------------------------------------------------------------------------------------

class AgentKit:
    """Tools and finalise hooks for ONE run. `ask` (question -> answer or None) is what ask_human uses when the loop gave the
    context none (tests inject one; a terminal gets a prompt)."""

    def __init__(self, source_id: str, work_dir: Path, *, model: str | None = None, code_version: str = "",
                 allow_overwrite: bool = False):
        self.sid, self.wd, self.model, self.code_version = source_id, Path(work_dir), model, code_version
        self.allow_overwrite = allow_overwrite
        self.questions: list[dict] = []
        self.critiques: list[dict] = []
        cfg_schema = {"type": "object", "additionalProperties": False, "required": ["config"],
                      "properties": {"config": {"type": "object"}}}
        reader_props = {
            "format": {"type": "string", "enum": list(ALL_FORMATS)},
            "encoding": {"type": "string"}, "delimiter": {"type": "string"}, "quote": {"type": "string"},
            "skip_rows": {"type": "integer"}, "header_rows": {"type": "integer"}, "skip_footer_rows": {"type": "integer"},
            "drop_empty_columns": {"type": "boolean"}, "sheet": {"type": "string"}, "records_path": {"type": "string"},
            "flatten_depth": {"type": "integer"}, "ndjson": {"type": "boolean"},
            "archive": {"type": "string", "enum": list(ARCHIVES)}, "member": {"type": "string"}}
        self.tools = registry(
            ToolSpec("fetch", "Download the dataset's input file. With NO arguments it lists the resources of the task's "
                              "reference (index, name, format, size). With `resource_index` it downloads that one (at most "
                              "200 MB). One run onboards one table, so only one resource can be downloaded. You never "
                              "supply a URL or path.",
                     {"type": "object", "additionalProperties": False, "properties": {"resource_index": {"type": "integer"}}},
                     self.t_fetch, max_rows=60, timeout_seconds=None),
            ToolSpec("list_members", "List the members of the downloaded zip or gz archive (names and sizes, at most 50). "
                                     "Members are read in place, never extracted; decompressed reads are capped at 1 GB.",
                     {"type": "object", "additionalProperties": False, "properties": {}}, self.t_list_members,
                     max_rows=MEMBER_LIST_CAP, timeout_seconds=20),
            ToolSpec("list_sheets", "List the sheets of a workbook (xlsx or xls) with their dimensions. For a workbook inside "
                                    "an archive pass `member`.",
                     {"type": "object", "additionalProperties": False, "properties": {"member": {"type": "string"}}},
                     self.t_list_sheets, max_rows=50, timeout_seconds=30),
            ToolSpec("sniff", "Look at the raw start of the file (or of an archive `member`): what kind of file it really is "
                              "(by its magic bytes, not its extension), its text encoding, a delimiter guess and the first "
                              "12 raw lines. Use it before read_table.",
                     {"type": "object", "additionalProperties": False, "properties": {"member": {"type": "string"}}},
                     self.t_sniff, max_rows=12, max_cell_chars=300, timeout_seconds=20),
            ToolSpec("read_table", "Read the file with the reader options you choose and return the column names, the row "
                                   "count and the first rows. `format` is required. header_rows: 0 (no header), 1, or n rows "
                                   "merged into one name; skip_rows drops rows above the header; for a zip give archive "
                                   "'zip' and `member`; for NDJSON set ndjson true; for GeoJSON records_path 'features'. A "
                                   "random sample of rows is held out for validation and never shown to you. Later tools "
                                   "use the reader of your latest successful read_table.",
                     {"type": "object", "additionalProperties": False, "required": ["format"], "properties": reader_props},
                     self.t_read_table, max_rows=20, max_cols=40, max_cell_chars=100, timeout_seconds=60),
            ToolSpec("profile", "Per-column profile of the training rows: fill rate, distinct count, most common values, "
                                "average length and shape rates (11-digit, 9-digit, date-like, company suffix, ';'). At most "
                                "60 columns per call; pass `columns` to choose which.",
                     {"type": "object", "additionalProperties": False, "properties": {"columns": {"type": "array"}}},
                     self.t_profile, max_rows=60, max_cols=12, max_cell_chars=100, timeout_seconds=60),
            ToolSpec("check_unique", "Exactly how unique one column, or a combination of columns, is across the training rows "
                                     "(for choosing record_id).",
                     {"type": "object", "additionalProperties": False, "required": ["columns"],
                      "properties": {"columns": {"type": "array"}}},
                     self.t_check_unique, max_rows=3, timeout_seconds=60),
            ToolSpec("sample", "Rows from the training set (never the held-out rows). strategy: head, spread (evenly spaced), "
                               "random, or by_column (one row for each of the most common values of `column`). n is at most "
                               "30. Only non-blank cells are shown.",
                     {"type": "object", "additionalProperties": False, "required": ["strategy"],
                      "properties": {"strategy": {"type": "string", "enum": ["head", "spread", "random", "by_column"]},
                                     "n": {"type": "integer"}, "column": {"type": "string"}, "columns": {"type": "array"}}},
                     self.t_sample, max_rows=30, max_cols=40, timeout_seconds=30),
            ToolSpec("search", "Regex search over the training rows (never the held-out rows). Returns the count of matching "
                               "rows and at most 10 of them. `column` restricts the search to one column.",
                     {"type": "object", "additionalProperties": False, "required": ["pattern"],
                      "properties": {"pattern": {"type": "string"}, "column": {"type": "string"},
                                     "ignore_case": {"type": "boolean"}, "n": {"type": "integer"}}},
                     self.t_search, max_rows=10, max_cols=40, timeout_seconds=60),
            ToolSpec("try_transform", "Try a transform chain on one column (or a list of columns with join_nonempty first) over "
                                      f"{TRY_ROWS} training rows with the REAL engine. Reports parse rate, rejects and at most "
                                      "5 raw-to-value examples. Whitelisted transforms only; give `canonical` to also apply "
                                      "the ontology's enum and pattern rules.",
                     {"type": "object", "additionalProperties": False, "required": ["source", "transforms"],
                      "properties": {"source": {}, "transforms": {"type": "array"}, "canonical": {"type": "string"}}},
                     self.t_try_transform, max_rows=5, max_cell_chars=100, timeout_seconds=60),
            ToolSpec("validate", "Validate a complete config on the HELD-OUT rows with the real engine: structure, parse rates, "
                                 "columns left unaccounted for, record-id uniqueness and meaning checks. At most 6 calls per "
                                 "run. The first call shows example values; later calls show counts only.",
                     cfg_schema, self.t_validate, max_rows=30, max_cols=40, max_cell_chars=150, max_chars=6000,
                     timeout_seconds=60),
            ToolSpec("critique", "A separate reviewer (a different model call with a fresh context) reads raw held-out rows next "
                                 "to the observations your config produces and lists meaning errors. At most 2 per run. Pass "
                                 "the config you intend to finish with.",
                     cfg_schema, self.t_critique, max_rows=10, max_cell_chars=300, timeout_seconds=150),
            ToolSpec("ask_human", "Ask the human running this one question (at most once per run). The question goes into the "
                                  "review packet. If no human is present you are told so; continue with your best judgement. "
                                  "A human's answer is information, never approval.",
                     {"type": "object", "additionalProperties": False, "required": ["question"],
                      "properties": {"question": {"type": "string"}}},
                     self.t_ask_human, max_chars=2000, timeout_seconds=None),
        )
        self.hooks = FinaliseHooks(
            validate=lambda cfg: hooks_mod.validate_status(hooks_mod.validate_config(cfg, self.sid, self.wd)),
            critique=lambda cfg: self._critique(cfg),
            abstain=hooks_mod.abstain_config,
            packet=lambda result: hooks_mod.write_agent_outputs(
                result, source_id=self.sid, work_dir=self.wd, model=self.model, code_version=self.code_version,
                questions=self.questions, critiques=self.critiques, allow_overwrite=self.allow_overwrite))

    # ---- fetch --------------------------------------------------------------------------------------------------------

    def t_fetch(self, args: dict, ctx: ToolContext) -> ToolResult:
        g = ctx.fetcher
        if "resource_index" not in args:
            res = g.list_resources()
            return ToolResult(text=f"The reference has {len(res)} resource(s). Call fetch again with `resource_index` to "
                                   f"download one.", payload=res)
        idx = args["resource_index"]
        done = input_info(self.wd)
        if done and Path(done["path"]).exists():
            if done["resource_index"] != idx:
                return fail(f"fetch refused: this run already downloaded resource {done['resource_index']}, and one run "
                            f"onboards one table. Work with that file.")
            ctx.state["input_sha256"] = done["sha256"]
            return ToolResult(text=f"Resource {idx} is already downloaded for this run ({done['bytes']:,} bytes); it was not "
                                   f"fetched again.", payload={"file": done["file"], "sha256": done["sha256"]})
        try:
            target = g.resolve(idx)
        except FetchRefused as e:
            return fail(str(e))
        t0 = time.monotonic()
        dest_dir = RAW_DIR / self.sid
        dest_dir.mkdir(parents=True, exist_ok=True)
        tmp = dest_dir / ".download.part"
        sha, size = hashlib.sha256(), 0
        try:
            size, sha, final_name, last_modified = self._download(g, target, tmp, ctx)
        except FetchRefused as e:   # a redirect hop that is not allowed: a refusal, not a download failure
            tmp.unlink(missing_ok=True)
            return fail(str(e))
        except _TooBig as e:
            tmp.unlink(missing_ok=True)
            return ToolResult(text=f"download failed: the file is larger than the {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB cap "
                                   f"({e.detail}). Nothing was kept.", is_error=True, status={"download_failed": True},
                              download_seconds=time.monotonic() - t0)
        except (requests.RequestException, OSError) as e:
            tmp.unlink(missing_ok=True)
            return ToolResult(text="download failed: a network or file error stopped it (detail below).", payload=str(e)[:300],
                              is_error=True, status={"download_failed": True}, download_seconds=time.monotonic() - t0)
        path = dest_dir / final_name
        tmp.replace(path)
        meta = self._metadata(g, idx, target, path, size, sha.hexdigest(), last_modified)
        (dest_dir / "metadata.json").write_text(_json(meta))
        save_input(self.wd, {"resource_index": idx, "path": str(path), "file": path.name, "bytes": size,
                             "sha256": sha.hexdigest()})
        ctx.state["input_sha256"] = sha.hexdigest()
        flag = " The licence is unknown or unclear (flagged)." if meta["licence_flag"] else ""
        return ToolResult(text=f"Downloaded resource {idx}: {size:,} bytes, sha256 {sha.hexdigest()[:12]}.{flag} Next: sniff.",
                          payload={"file": path.name}, download_seconds=time.monotonic() - t0)

    def _download(self, g, target: str, tmp: Path, ctx: ToolContext):
        sha, size, next_log = hashlib.sha256(), 0, PROGRESS_EVERY_BYTES
        last_modified = None
        if g.kind == "path":   # the human-supplied local file: copied, same cap
            src = Path(target).expanduser()
            if not src.is_file():
                raise OSError("the local reference is not a readable file")
            if src.stat().st_size > MAX_DOWNLOAD_BYTES:
                raise _TooBig(f"{src.stat().st_size:,} bytes")
            last_modified = datetime.fromtimestamp(src.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")

            def local_chunks():
                with src.open("rb") as fh:
                    while True:
                        block = fh.read(256 * 1024)
                        if not block:
                            return
                        yield block
            chunks, closer, name = local_chunks(), None, src.name
        else:
            resp = g.open_url(target)
            declared = resp.headers.get("Content-Length")
            if declared and str(declared).isdigit() and int(declared) > MAX_DOWNLOAD_BYTES:
                resp.close()
                raise _TooBig(f"the server declares {int(declared):,} bytes")
            last_modified = resp.headers.get("Last-Modified")
            chunks, closer = resp.iter_content(256 * 1024), resp
            name = Path(urlparse(g.final_url or target).path).name
        try:
            with tmp.open("wb") as f:
                for chunk in chunks:
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise _TooBig(f"more than {MAX_DOWNLOAD_BYTES:,} bytes arrived")
                    f.write(chunk)
                    sha.update(chunk)
                    if size >= next_log:
                        ctx.log(f"downloaded {size / (1024 * 1024):.0f} MB")
                        next_log += PROGRESS_EVERY_BYTES
        finally:
            if closer is not None:
                closer.close()
        ctx.log(f"download complete: {size:,} bytes")
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)[-80:] or "data"
        return size, sha, name, last_modified

    def _metadata(self, g, idx: int, target: str, path: Path, size: int, sha: str, last_modified) -> dict:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        res = g.resource_meta(idx)
        fmt = (res.get("format") or path.suffix.lstrip(".")).upper()
        base = {"source_id": self.sid, "url": target, "file": path.name, "bytes": size, "sha256": sha, "downloaded_at": now,
                "resource_format": fmt, "resource_name": str(res.get("name") or path.name)}
        if g.kind == "ckan" and g.package:
            portal = g._ckan[0]
            rec = slim(g.package, portal)
            licence, flagged = licence_of(rec)
            return {**base, "dataset_id": rec["dataset_id"], "portal": portal, "title": rec["title"],
                    "organisation": rec["organisation"],
                    "dataset_page": PORTAL_DATASET_PAGE[portal].format(name=rec["name"]),
                    "licence": licence, "licence_flag": flagged, "ckan_license_id": rec["license_id"],
                    "dataset_modified": rec["metadata_modified"] or now, "resource_id": res.get("id") or "",
                    "resource_last_modified": res.get("last_modified") or res.get("metadata_modified") or now}
        return {**base, "dataset_id": f"file:{path.name}", "portal": "local" if g.kind == "path" else "url",
                "title": path.stem, "organisation": "unknown (not from a catalogue)", "dataset_page": "",
                "licence": "unknown", "licence_flag": True, "ckan_license_id": "", "dataset_modified": last_modified or now,
                "resource_id": "", "resource_last_modified": last_modified or now}

    # ---- looking at the file -------------------------------------------------------------------------------------------

    def _input(self) -> Path:
        return input_path(self.wd)

    def t_list_members(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            path = self._input()
            head, names = _head_of(path, None, None)
            kind = detect_kind(head, names)
            if kind == "gzip":
                return ToolResult(text="A gzip file holds one member; its size is not recorded in the header. Reads of it are "
                                       "capped at 1 GB decompressed. Use archive 'gz' in read_table.",
                                  payload=[{"name": path.stem, "size": None}])
            if kind != "zip":
                return fail(f"this file is not a zip or gz archive (it looks like: {kind})")
            infos = zip_members(path)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the archive could not be read (detail below)",
                        None if isinstance(e, NoTable) else str(e))
        total = sum(i.file_size for i in infos)
        rows = [{"name": i.filename, "size": i.file_size, "compressed": i.compress_size} for i in infos[:MEMBER_LIST_CAP]]
        warn = (f" WARNING: the members declare {total:,} decompressed bytes, over the {MAX_DECOMPRESSED_BYTES:,} cap; a read "
                f"of an over-cap member is refused.") if total > MAX_DECOMPRESSED_BYTES else ""
        return ToolResult(text=f"The zip has {len(infos)} member(s), {total:,} bytes decompressed in all (as declared)."
                               f"{' Showing the first 50.' if len(infos) > MEMBER_LIST_CAP else ''}{warn}", payload=rows)

    def t_list_sheets(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            path = self._input()
            member = args.get("member")
            head, names = _head_of(path, None, None)
            kind = detect_kind(head, names)
            archive = None
            if member is not None:
                archive = {"zip": "zip", "gzip": "gz"}.get(kind)
                if archive is None:
                    return fail("`member` only applies to a zip or gz archive")
                head, _ = _head_of(path, member, archive)
                kind = detect_kind(head, ["[Content_Types].xml", "xl/"] if head[:2] == b"PK" else None)
            fmt = {"xlsx": "xlsx", "ole2": "xls"}.get(kind)
            if fmt is None:
                return fail(f"this is not a workbook (it looks like: {kind})")
            sheets = workbook_sheets({"format": fmt, "archive": archive, "member": member}, path)
        except NoTable as e:
            return fail(str(e))
        except ReaderError as e:
            return fail("the workbook could not be read (detail below)", str(e))
        return ToolResult(text=f"The workbook ({fmt}) has {len(sheets)} sheet(s).", payload=sheets)

    def t_sniff(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            path = self._input()
            member = args.get("member")
            head, names = _head_of(path, None, None)
            kind = detect_kind(head, names)
            if member is not None:
                archive = {"zip": "zip", "gzip": "gz"}.get(kind)
                if archive is None:
                    return fail("`member` only applies to a zip or gz archive")
                head, _ = _head_of(path, member, archive)
                kind = detect_kind(head, None)
        except NoTable as e:
            return fail(str(e))
        except ReaderError as e:
            return fail("that member could not be read (detail below)", str(e))
        ext_kind = _EXT_KIND.get(path.suffix.lower())
        note = ""
        if member is None and ext_kind and ext_kind != kind and not (ext_kind == "text" and kind in ("xml", "html")):
            note = f" The file extension suggests {ext_kind}, but the content looks like {kind}: trust the content."
        if kind == "empty":
            return ToolResult(text="The file is empty (0 bytes).", payload={"kind": "empty"})
        payload: dict = {"kind": kind}
        text = f"Content looks like: {kind}.{note}"
        if kind in ("text", "xml", "html"):
            enc = guess_encoding(head)
            decoded = head.decode(enc if enc != "utf-8" else "utf-8", errors="replace")
            lines = decoded.splitlines()[:12]
            payload.update(encoding=enc, delimiter=guess_delimiter(decoded), head=[l[:300] for l in lines])
            first = decoded.lstrip()[:1]
            payload["json_like"] = first in "{["
            payload["ndjson_like"] = bool(len(lines) >= 2 and all(l.strip().startswith("{") and l.strip().endswith("}") for l in lines[:3]))
            text += f" Encoding guess {enc}. Details and the first lines are below."
        elif kind in ("zip", "gzip"):
            text += " It is an archive: use list_members, then read_table with archive and member."
        elif kind in ("xlsx", "ole2"):
            text += " It is a workbook: use list_sheets, then read_table."
        return ToolResult(text=text, payload=payload)

    # ---- read_table and the tools that use it ---------------------------------------------------------------------------

    def t_read_table(self, args: dict, ctx: ToolContext) -> ToolResult:
        reader = {k: v for k, v in args.items() if v is not None and v != ""}
        try:
            path = self._input()
            table = build_table(self.sid, self.wd, path, reader, ctx.check_deadline)
        except NoTable as e:
            return fail(str(e))
        except ReaderError as e:
            return fail("read_table failed: the reader could not read the file with these options (reason below).", str(e))
        if table.n_rows == 0:
            return fail("read_table failed: these options produced no data rows. Check skip_rows, header_rows and the format.")
        remember_table(self.sid, self.wd, table)
        first = []
        for row in table.training(ctx.check_deadline):
            first.append(row)
            if len(first) >= 20:
                break
        blank = sum(1 for h in table.headers if h.startswith("_blank_"))
        text = (f"Read {table.n_rows:,} data rows and {len(table.headers)} columns"
                f"{f' ({blank} with a blank header)' if blank else ''}. {len(table.held_fp)} rows are held out for validation and "
                f"never shown to you; {table.visible_n:,} training rows remain. The column names and the first training rows "
                f"are below.")
        if table.resplit:
            text += " NOTE: the held-out split was re-made because the first parse of the file did not match this one."
        if len(table.headers) > 40:
            text += f" Only the first 40 columns are shown; use `profile` with `columns` for the rest."
        return ToolResult(text=text, payload={"columns": {str(i): h for i, h in enumerate(table.headers)}, "first_rows": first},
                          status={"rows": table.n_rows, "columns": len(table.headers)})

    def _table(self, ctx: ToolContext):
        return get_table(self.sid, self.wd, ctx.check_deadline)

    def t_profile(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            table = self._table(ctx)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the table could not be re-read (detail below)", None if isinstance(e, NoTable) else str(e))
        names = args.get("columns") or table.headers[:60]
        bad = [c for c in names if c not in table.headers]
        if bad or not all(isinstance(c, str) for c in names):
            return fail("profile: some requested columns do not exist (the file's columns are in `valid_columns`).",
                        {"unknown": [str(b) for b in bad][:20], "valid_columns": table.headers[:60]})
        names = names[:60]
        accs = {c: _Col() for c in names}
        n = 0
        for row in table.training(ctx.check_deadline):
            n += 1
            if n % 2000 == 0:
                ctx.check_deadline()
            for c, acc in accs.items():
                v = clean_whitespace(row.get(c))
                if v:
                    acc.add(v)
        rows = [acc.summary(c, n) for c, acc in accs.items()]
        capped = [r["column"] for r in rows if r.get("capped")]
        return ToolResult(text=f"Profile of {len(rows)} column(s) over {n:,} training rows (the {len(table.held_fp)} held-out rows "
                               f"are excluded)." + (f" {len(capped)} column(s) have more than {DISTINCT_CAP:,} distinct values; "
                                                    f"their distinct count is marked capped." if capped else ""), payload=rows)

    def t_check_unique(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            table = self._table(ctx)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the table could not be re-read (detail below)", None if isinstance(e, NoTable) else str(e))
        cols = args["columns"]
        if not cols or not all(isinstance(c, str) and c in table.headers for c in cols):
            return fail("check_unique: every name in `columns` must be a column of the file (see read_table).",
                        {"valid_columns": table.headers[:60]})
        seen: set = set()
        total = blank = dup = 0
        examples = []
        for row in table.training(ctx.check_deadline):
            total += 1
            parts = [clean_whitespace(row.get(c)) for c in cols]
            if not all(parts):
                blank += 1
                continue
            key = "\x1f".join(parts)
            d = hashlib.blake2b(key.encode(), digest_size=16).digest()   # 128-bit: a collision is not a practical concern
            if d in seen:
                dup += 1
                if len(examples) < 3:
                    examples.append({"duplicate_key": key[:100]})
            else:
                seen.add(d)
        unique = dup == 0 and blank == 0
        return ToolResult(text=f"Over {total:,} training rows: {len(seen):,} distinct keys, {dup:,} repeated, {blank:,} rows with a "
                               f"blank in the key. {'The key is unique and always filled.' if unique else 'The key is NOT unique and complete.'}",
                          payload=examples, status={"unique": unique})

    def t_sample(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            table = self._table(ctx)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the table could not be re-read (detail below)", None if isinstance(e, NoTable) else str(e))
        n = _int_arg(args, "n", 10, 1, 30)
        strategy = args["strategy"]
        keep = args.get("columns")
        if keep is not None and not all(c in table.headers for c in keep if isinstance(c, str)):
            return fail("sample: `columns` names a column that does not exist.", {"valid_columns": table.headers[:60]})
        total = table.visible_n
        rows: list[dict] = []
        if strategy == "by_column":
            col = args.get("column")
            if col not in table.headers:
                return fail("sample by_column needs `column`, one of the file's columns.", {"valid_columns": table.headers[:60]})
            counts: Counter = Counter()
            first: dict = {}
            for row in table.training(ctx.check_deadline):
                v = clean_whitespace(row.get(col))
                if v:
                    counts[v] += 1
                    if v not in first and len(first) < 20000:
                        first[v] = row
            rows = [first[v] for v, _ in counts.most_common() if v in first][:n]
        elif strategy == "head":
            for row in table.training(ctx.check_deadline):
                rows.append(row)
                if len(rows) >= n:
                    break
        else:
            if strategy == "spread":
                want = {i * total // n for i in range(min(n, total))}
            else:   # random: seeded by the source and the call number, so a replay picks the same rows
                call = ctx.uses["sample"] if ctx.uses is not None else 0
                want = set(random.Random(f"{self.sid}:{call}").sample(range(total), min(n, total)))
            for i, row in enumerate(table.training(ctx.check_deadline)):
                if i in want:
                    rows.append(row)
        shown = [{k: v for k, v in trim_row(r).items() if keep is None or k in keep} for r in rows]
        return ToolResult(text=f"{len(shown)} training row(s) ({strategy}) of {total:,}; only non-blank cells are shown.", payload=shown)

    def t_search(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            table = self._table(ctx)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the table could not be re-read (detail below)", None if isinstance(e, NoTable) else str(e))
        pattern = args["pattern"]
        if len(pattern) > MAX_PATTERN_CHARS:
            return fail(f"search: the pattern is longer than {MAX_PATTERN_CHARS} characters.")
        try:
            rx = re.compile(pattern, re.I if args.get("ignore_case") else 0)
        except re.error as e:
            return fail("search: the pattern is not a valid regex (detail below).", str(e)[:200])
        col = args.get("column")
        if col is not None and col not in table.headers:
            return fail("search: `column` is not a column of the file.", {"valid_columns": table.headers[:60]})
        n = _int_arg(args, "n", 10, 1, 10)
        count, hits = 0, []
        for i, row in enumerate(table.training(ctx.check_deadline)):
            cells = [row.get(col)] if col else list(row.values())
            if any(v is not None and rx.search(str(v)) for v in cells):
                count += 1
                if len(hits) < n:
                    hits.append(trim_row(row))
        return ToolResult(text=f"{count:,} training row(s) match; showing {len(hits)}.", payload=hits, status={"matches": count})

    def t_try_transform(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            table = self._table(ctx)
        except (NoTable, ReaderError) as e:
            return fail(str(e) if isinstance(e, NoTable) else "the table could not be re-read (detail below)", None if isinstance(e, NoTable) else str(e))
        source, raw_ts = args["source"], args["transforms"]
        cols = source if isinstance(source, list) else [source]
        if not cols or not all(isinstance(c, str) and c in table.headers for c in cols):
            return fail("try_transform: `source` must be a column of the file, or a list of columns.",
                        {"valid_columns": table.headers[:60]})
        if not all(isinstance(t, str) or (isinstance(t, dict) and isinstance(t.get("name"), str)) for t in raw_ts):
            return fail("try_transform: each transform must be {\"name\": ..., \"arg\": ...}.")
        ts = normalise_transforms(raw_ts)
        errs: list[str] = []
        _check_transforms(ts, "try_transform", errs, is_list_source=isinstance(source, list))
        canonical = args.get("canonical")
        ontology = load_ontology()
        if canonical is not None and canonical not in ontology:
            errs.append(f"`canonical` {canonical!r} is not in the ontology")
        if errs:
            return fail("try_transform refused: " + "; ".join(errs) + ". Level W (whitelisted) transforms only for now.")
        step = max(1, table.visible_n // TRY_ROWS)
        stats, examples, rejected = FieldStats(), [], []
        rows_n = 0
        for i, row in enumerate(table.training(ctx.check_deadline)):
            if i % step or rows_n >= TRY_ROWS:
                continue
            rows_n += 1
            stats.rows += 1
            raw = _value_of(source, row)
            if _is_blank(raw):
                stats.blank += 1
                continue
            values, events = apply_transforms(raw, ts)
            for kind, reason, item in events:
                if kind == "skip":
                    stats.skip += 1
                    stats.skip_reasons[reason] += 1
                else:
                    stats.reject += 1
                    stats.reject_reasons[reason] += 1
                    if len(rejected) < 5:
                        rejected.append({"raw": str(item)[:80], "reason": reason})
            for v in values:
                why = _ontology_ok(canonical, v, ontology) if canonical else None
                if why:
                    stats.reject += 1
                    stats.reject_reasons[why] += 1
                    if len(rejected) < 5:
                        rejected.append({"raw": str(v)[:80], "reason": why})
                else:
                    stats.ok += 1
                    if len(examples) < 5:
                        examples.append({"raw": str(raw)[:80], "value": str(v)[:80]})
        d = stats.as_dict()
        rate = "n/a (nothing was judged)" if d["parse_rate"] is None else f"{d['parse_rate']:.1%}"
        return ToolResult(
            text=f"Tried level-W transforms on {rows_n} training rows: parse rate {rate} (ok {d['ok']}, rejected {d['reject']}, "
                 f"not applicable {d['skip']}, blank {d['blank']}). Examples and rejects are below.",
            payload={"examples": examples, "rejects": rejected, "reject_reasons": d["reject_reasons"],
                     "skip_reasons": d["skip_reasons"]},
            status={"parse_rate": d["parse_rate"], "ok": d["ok"], "reject": d["reject"]})

    # ---- validate, critique, ask_human -------------------------------------------------------------------------------------

    def t_validate(self, args: dict, ctx: ToolContext) -> ToolResult:
        call_no = (ctx.uses["validate"] if ctx.uses is not None else 0) + 1
        first = call_no == 1
        try:
            report = hooks_mod.validate_config(args["config"], self.sid, self.wd, ctx.check_deadline)
        except NoTable as e:
            return fail(str(e))
        status = hooks_mod.validate_status(report)
        unanswered = hooks_mod.unanswered(report, args["config"]) if report["stats"] else []

        def scrub(reasons: dict) -> dict:   # a reject reason can carry a raw value ("unmapped_value:FOO"): counts only after call 1
            if first:
                return reasons
            out: Counter = Counter()
            for r, c in reasons.items():
                out[str(r).split(":")[0]] += c
            return dict(out)

        def warning_text(t: str) -> str:
            return t if first else re.sub(r"\s*\(e\.g\.[^)]*\)", "", t)

        payload = {
            "structural_errors": report["structural_errors"],
            "failing_fields": [{"field": f["key"], "reason": f["reason"], "reject_reasons": scrub(f["reject_reasons"]),
                                "skip_reasons": f["skip_reasons"], **({"examples": f["examples"]} if first else {})}
                               for f in report["field_failures"]],
            "unaccounted_columns": report["unaccounted_columns"],
            "record_id": ({"FAILED": "the record id is not unique enough over the WHOLE file: choose a column or columns that "
                                     "are unique and filled (check_unique), or hash_row", **report["duplicate_ids"]}
                          if report.get("id_failure") else report["duplicate_ids"]),
            "meaning_warnings": [{"id": w["id"], "text": warning_text(w["text"])} for w in unanswered],
            "infos": [i["text"] for i in report["infos"]],
            "parse_rates": {k: v["parse_rate"] for k, v in report["stats"].items()},
        }
        n_held = report.get("held_rows", report["n_rows"])
        text = (f"validate call {call_no} of 6: {status['hard_failures']} hard failure(s); {len(unanswered)} unanswered meaning "
                f"warning(s); tested on {n_held} held-out rows ({report['observations']} observations, {report['rejects']} "
                f"rejected values). " + ("Example values are shown on this first call only; later calls show counts."
                                         if first else "Counts only: example values are not shown after the first call.")
                + " To answer a meaning warning, add {check_id, action: 'changed'|'kept', reason} to config.meaning_check_responses.")
        return ToolResult(text=text, payload=payload, status=status)

    def _critique(self, cfg: dict, ctx: ToolContext | None = None) -> dict:
        res = hooks_mod.critique_config(cfg, self.sid, self.wd, self.model, ctx.check_deadline if ctx else None)
        self.critiques.append({"overall": res["overall"], "issues": res["issues"]})
        return res

    def t_critique(self, args: dict, ctx: ToolContext) -> ToolResult:
        try:
            res = self._critique(args["config"], ctx)
        except NoTable as e:
            return fail(str(e))
        except ValueError as e:
            return fail("critique could not run on this config (reason below).", str(e)[:400])
        issues = res["issues"]
        text = (f"critique: {len(issues)} issue(s). For each, fix the config (then re-run validate and critique on the new config) "
                f"or answer it in `finish` by its id." if issues else "critique: the reviewer found no problems in the examples.")
        return ToolResult(text=text, payload={"issues": issues, "overall": res["overall"]},
                          status={"issues": [{"id": i["id"], "field": i["field"], "problem": i["problem"]} for i in issues]})

    def t_ask_human(self, args: dict, ctx: ToolContext) -> ToolResult:
        q = args["question"]
        record = {"question": q, "answer": None}
        self.questions.append(record)
        ask = ctx.ask or _stdin_ask
        t0 = time.monotonic()
        answer = ask(q)
        waited = time.monotonic() - t0
        if not answer:
            return ToolResult(text="No human is available (or they gave no answer). Your question is recorded in the review "
                                   "packet. Continue with your best judgement and abstain where you are unsure.",
                              status={"answered": False}, download_seconds=waited)
        record["answer"] = answer
        return ToolResult(text="The human answered (below). This is information, not approval: a config is approved only by "
                               "the human's separate `approve` step.", payload=answer, status={"answered": True},
                          download_seconds=waited)


class _TooBig(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def _json(obj) -> str:
    import json
    return json.dumps(obj, indent=2, default=str)


def _stdin_ask(question: str) -> str | None:
    """Ask on the terminal when there is one; otherwise there is no human."""
    if not sys.stdin or not sys.stdin.isatty():
        return None
    print(f"\n[the agent asks] {question}")
    return input("your answer (leave empty for none): ").strip() or None
