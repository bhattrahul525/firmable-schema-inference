"""Step 2 (code only): profile every column and split the rows three ways.

  sample A  (30 rows)  -> shown to proposal 1
  sample B  (30 rows)  -> shown to proposal 2 (different rows, so the two proposals are independent)
  held out (<=300)     -> never shown to the model while proposing; used to test the mapping

The shuffle is seeded by source_id, so the split is the same every run.
"""

from __future__ import annotations

import random
import re
from collections import Counter

from src.engine.transforms import _COMPANY_END, clean_whitespace
from src.common.ids import digits_only

SAMPLE_N = 30
HELD_OUT_MAX = 300
CELL_MAX = 100

_DATE_LIKE = re.compile(r"^\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}([ T].*)?$")


def trim_row(row: dict) -> dict:
    """Compact view of a row for prompts: only non-blank cells, long values cut."""
    out = {}
    for k, v in row.items():
        s = clean_whitespace(v)
        if s:
            out[k] = s if len(s) <= CELL_MAX else s[:CELL_MAX] + "…"
    return out


def split_rows(source_id: str, n_rows: int) -> dict:
    """Indices (into the loaded rows) for sample A, sample B and held-out."""
    idx = list(range(n_rows))
    random.Random(source_id).shuffle(idx)
    held = min(HELD_OUT_MAX, n_rows // 2)
    each = min(SAMPLE_N, max(1, (n_rows - held) // 2))
    return {"A": idx[:each], "B": idx[each:2 * each], "held_out": idx[2 * each:2 * each + held]}


def profile_columns(headers: list[str], rows: list[dict]) -> list[dict]:
    """Per column: fill rate, distinct values, most common values, and 'shape' rates that help
    the model recognise identifiers and dates without reading every row."""
    n = len(rows)
    out = []
    for h in headers:
        vals = [clean_whitespace(r.get(h)) for r in rows]
        present = [v for v in vals if v]
        c = Counter(present)
        digits = [digits_only(v) for v in present]
        p = {
            "column": h,
            "fill_rate": round(len(present) / n, 3) if n else 0,
            "distinct": len(c),
            "top_values": [[v[:50], k] for v, k in c.most_common(5)],
            "avg_length": round(sum(len(v) for v in present) / len(present), 1) if present else 0,
        }
        if present:
            share = lambda pred: round(sum(1 for x in present if pred(x)) / len(present), 3)
            p["shape"] = {k: v for k, v in {
                "pct_11_digits": round(sum(1 for d in digits if len(d) == 11) / len(present), 3),
                "pct_9_digits": round(sum(1 for d in digits if len(d) == 9) / len(present), 3),
                "pct_date_like": share(lambda x: bool(_DATE_LIKE.match(x))),
                "pct_company_suffix": share(lambda x: bool(_COMPANY_END.search(x))),
                "pct_contains_semicolon": share(lambda x: ";" in x),
            }.items() if v > 0}
        out.append(p)
    return out
