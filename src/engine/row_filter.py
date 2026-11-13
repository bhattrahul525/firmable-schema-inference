"""Generic row filter for big reference registers (no LLM, no source-specific code).

Streams the register one row at a time (iter_table, so the 247 MB file is never in memory) and keeps a row when
  1. the keep_where condition holds (an explicit {column, equals}; e.g. BN_STATUS == Registered), AND
  2. its ABN is the ABN of a mention in the six approved sources, OR its name key matches a mention name key.
The ABN and name columns come from the register's agent-generated config (fields mapped to entity.abn and
entity.trading_name / entity.legal_name). The name key is the matcher's own `name_core`, so filter and matcher agree.

keep_where and the file path come from configs/reference_sources.yaml (hand-written; agent configs are never edited);
--keep-where COLUMN=VALUE overrides.

CLI:  python -m src.engine.row_filter <ref_source_id> [--raw <file>] [--keep-where BN_STATUS=Registered]
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from src.common.ids import normalise_abn
from src.engine.config import config_path, load_config_file
from src.engine.readers import iter_table
from src.common.names import name_core
from src.part3_resolve.features import load_mentions, reference_sources
from src.part3_resolve.run import SOURCES

OUT_DIR = Path("data/reference")
ATTRIBUTION_SRC = Path("docs/asic_business_names_licence.md")
MAX_OUT_MB = 20


def mention_keys(mentions: list[dict]) -> tuple[set[str], set[str]]:
    """(ABNs, name keys) of everything the six sources mention."""
    abns = {m["abn"] for m in mentions if m["abn"]}
    names = {m["core"] for m in mentions if m["core"]} | {c for m in mentions for c in m["trading_cores"]}
    return abns, names


def filter_rows(rows, keep_where: dict, abn_col: str, name_col: str, abns: set, names: set):
    """Yields (row, matched_by) for rows that pass keep_where and hit an ABN or a name key."""
    col, want = keep_where["column"], keep_where["equals"]
    for row in rows:
        if (row.get(col) or "").strip() != want:
            continue
        by_abn = normalise_abn(row.get(abn_col)) in abns  # None (blank / bad checksum) is never in abns
        by_name = name_core(row.get(name_col)) in names
        if by_abn or by_name:
            yield row, "abn+name" if by_abn and by_name else "abn" if by_abn else "name"


def run(ref_id: str, raw: Path, keep_where: dict | None) -> dict:
    cfg = load_config_file(config_path(ref_id))
    keep_where = keep_where or reference_sources()[ref_id]["keep_where"]  # CLI flag overrides
    by_canon = {f["canonical"]: f["source"] for f in cfg["fields"]}
    abn_col, name_col = by_canon["entity.abn"], by_canon["entity.trading_name"]
    abns, names = mention_keys(load_mentions(SOURCES))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{ref_id}_trimmed.csv"
    total = kept = 0
    t0 = time.time()
    with iter_table(cfg["reader"], raw) as (headers, rows), out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[*headers, "matched_by"])
        w.writeheader()

        def counting():  # total = every row read, including those keep_where drops
            nonlocal total
            for _, r in rows:
                total += 1
                yield r

        for row, how in filter_rows(counting(), keep_where, abn_col, name_col, abns, names):
            w.writerow({**row, "matched_by": how})
            kept += 1
    seconds = round(time.time() - t0, 1)
    (OUT_DIR / "ATTRIBUTION.md").write_text(ATTRIBUTION_SRC.read_text())
    size_mb = out.stat().st_size / 1e6
    return {"kept": kept, "total": total, "seconds": seconds, "size_mb": round(size_mb, 2),
            "over_limit": size_mb > MAX_OUT_MB}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ref_id")
    ap.add_argument("--raw", help="default: path in configs/reference_sources.yaml")
    ap.add_argument("--keep-where", help="COLUMN=VALUE")
    a = ap.parse_args()
    kw = None
    if a.keep_where:
        c, _, v = a.keep_where.partition("=")
        kw = {"column": c, "equals": v}
    print(run(a.ref_id, Path(a.raw or reference_sources()[a.ref_id]["path"]), kw))


if __name__ == "__main__":
    main()
