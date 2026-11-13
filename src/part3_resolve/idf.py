"""Token rarity (IDF) for names, and a rarity-weighted name overlap.

Why: "Acme Australia" vs "Zenith Australia" share a word, but "australia" is in thousands of names and says almost
nothing; "acme" says a lot. Corpus (step 7 decision 1=B):
  (a) the six approved sources: each source's DISTINCT normalised names (ACT repeats a supplier on 127k invoices);
  (b) the FULL Business Names register (Registered rows), counted once and cached in data/cache/ (git-ignored).
Token weight = ln((N + 1) / (df + 1)), df = number of names containing the token, N = number of names. A token never
seen gets the largest weight. Tokens come from `name_core`, so Pty / Ltd / Limited are already gone.

overlap(a, b) = weighted Jaccard: sum of weights of shared tokens / sum of weights of all tokens in either name, in [0, 1].
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

from src.common.names import name_core
from src.engine.config import config_path, load_config_file
from src.engine.readers import iter_table
from src.part3_resolve.features import load_mentions
from src.part3_resolve.run import SOURCES

REGISTER = Path("data/raw/reference/business_names_202611.zip")
REGISTER_ID = "asic_business_names"
CACHE = Path("data/cache/bn_token_counts.json")  # git-ignored (.gitignore: data/cache/)
KEEP_WHERE = ("BN_STATUS", "Registered")  # same rule as the row filter: current names only


def tokens(name: str | None) -> set[str]:
    return set(name_core(name).split())


class Idf:
    def __init__(self, df: Counter, n: int):
        self.df, self.n = df, n

    def idf(self, token: str) -> float:
        return math.log((self.n + 1) / (self.df.get(token, 0) + 1))

    def overlap(self, a: str | None, b: str | None) -> float:
        ta, tb = tokens(a), tokens(b)
        union = sum(self.idf(t) for t in ta | tb)
        return sum(self.idf(t) for t in ta & tb) / union if union else 0.0


def mention_counts() -> tuple[Counter, int]:
    """Document frequency over distinct normalised names per source."""
    names = set()
    for m in load_mentions(SOURCES):
        for c in [m["core"], *m["trading_cores"]]:
            if c:
                names.add((m["source_id"], c))
    df = Counter(t for _, c in names for t in set(c.split()))
    return df, len(names)


def register_counts(raw: Path = REGISTER, cache: Path = CACHE) -> tuple[Counter, int]:
    """Token counts over the full register: one streamed pass, then cached (re-built if the file changes)."""
    stamp = {"file": raw.name, "size": raw.stat().st_size}
    if cache.exists():
        c = json.loads(cache.read_text())
        if c["stamp"] == stamp:
            return Counter(c["df"]), c["n"]
    cfg = load_config_file(config_path(REGISTER_ID))
    name_col = next(f["source"] for f in cfg["fields"] if f["canonical"] == "entity.trading_name")
    df, n = Counter(), 0
    with iter_table(cfg["reader"], raw) as (_, rows):
        for _, row in rows:
            if (row.get(KEEP_WHERE[0]) or "").strip() != KEEP_WHERE[1]:
                continue
            toks = tokens(row.get(name_col))
            if toks:
                n += 1
                df.update(toks)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"stamp": stamp, "n": n, "df": df}))
    return df, n


def load_idf() -> Idf:
    mdf, mn = mention_counts()
    rdf, rn = register_counts()
    return Idf(mdf + rdf, mn + rn)
