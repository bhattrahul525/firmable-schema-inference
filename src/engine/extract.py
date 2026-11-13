"""The generic extractor: (config, raw file) -> canonical observations.

There is no source-specific code here. Everything a source needs is in its config. The same
`run_rows` function is used by the agent's validation step (on held-out rows, with a draft
config) and by production extraction (on the sampled file, with an approved config), so what
the agent tested is exactly what ships.

Multi-entity rows: if a field uses `split`, its items line up by position with the other split
fields in the same `group` (supplier 1's name with supplier 1's ABN). Scalar fields apply to
every entity in the group. The exception is entity.trading_name: its items are several names
of ONE entity, one observation each (as the ontology requires).

CLI:  python -m src.engine.extract <source_id> [--limit 1000]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.engine.config import (CLAIM_KIND, config_path, derivation_level, extractor_version,
                               load_approved_config, load_ontology, sha256_of)
from src.engine.readers import read_rows
from src.engine.transforms import CATALOGUE, Reject, Skip, clean_whitespace, run_regex

RAW_DIR = Path("data/raw/sources")
OUT_DIR = Path("outputs/observations")
REJECT_DIR = Path("outputs/rejects")
MAX_REJECT_EXAMPLES = 5


def apply_transforms(raw, transforms: list[dict]):
    """Run a value through a transform chain. Returns (values, events) where events is a list of
    ('ok'|'skip'|'reject', reason, raw_item). A `split` turns one value into several, each then
    handled on its own."""
    items = [raw]
    events = []
    for t in transforms:
        fn = CATALOGUE[t["name"]][0]
        nxt = []
        for it in items:
            try:
                out = fn(it, t["arg"])
            except Skip as e:
                events.append(("skip", str(e), it))
                continue
            except Reject as e:
                events.append(("reject", str(e), it))
                continue
            if out is None:
                continue
            nxt.extend(out) if isinstance(out, list) else nxt.append(out)
        items = nxt
    return items, events


def make_record_id(cfg: dict, row: dict) -> str:
    """Source key if the config names one (joined with '|'); otherwise, or if the key is blank on
    this row, 'h:' + first 16 hex of SHA-1 over the whitespace-normalised row. The hash is
    deterministic, so re-running gives the same ids, but two identical rows share one id."""
    cols = (cfg["record_id"].get("from") or [])
    if cols:
        parts = [clean_whitespace(row.get(c)) for c in cols]
        if all(parts):
            return "|".join(parts)
    norm = {k: clean_whitespace(v) for k, v in sorted(row.items(), key=lambda kv: str(kv[0]))}
    return "h:" + hashlib.sha1(json.dumps(norm, sort_keys=True, default=str).encode()).hexdigest()[:16]


def when_met(when, row) -> bool:
    """A field's `when` (step 4a): does this row hold? No `when` -> True. Judged on the condition column alone, whitespace-cleaned;
    `equals` ignores case; `matches` is re.search under the regex timer. A blank cell, a timeout or a bad pattern -> not met."""
    if not when:
        return True
    cell = clean_whitespace(row.get(when["column"]))
    if not cell:
        return False
    if "equals" in when:
        return cell.lower() in {(clean_whitespace(x) or "").lower() for x in when["equals"]}
    try:
        return bool(run_regex(when["matches"], lambda rx: rx.search(cell)))
    except Reject:
        return False


def _value_of(spec_source, row):
    if isinstance(spec_source, list):
        return [row.get(c) for c in spec_source]
    return row.get(spec_source)


def _is_blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, list) and not any(
        x not in (None, "") for x in v))


def _ontology_ok(canonical: str, value, ontology: dict) -> str | None:
    """Final guard on the ontology's own rules. Returns a reason if the value is not allowed."""
    spec = ontology[canonical]
    if spec.get("type") == "enum" and value not in spec["values"]:
        return f"not_in_enum:{value}"
    if spec.get("pattern") and not re.fullmatch(spec["pattern"], str(value)):
        return "pattern_mismatch"
    return None


class FieldStats:
    def __init__(self):
        self.rows = self.blank = self.ok = self.skip = self.reject = 0
        self.skip_reasons: Counter = Counter()
        self.reject_reasons: Counter = Counter()
        self.reject_examples: list[dict] = []

    def as_dict(self) -> dict:
        judged = self.ok + self.reject  # skips are "rule not applicable", not failures
        return {
            "rows": self.rows, "blank": self.blank, "ok": self.ok, "skip": self.skip,
            "reject": self.reject,
            "parse_rate": round(self.ok / judged, 4) if judged else None,
            "skip_reasons": dict(self.skip_reasons), "reject_reasons": dict(self.reject_reasons),
            "reject_examples": self.reject_examples,
        }


def run_rows(cfg: dict, rows: list[dict], metadata: dict, *, ingested_at: str | None = None,
             cfg_hash: str = "draft") -> tuple[list[dict], list[dict], dict]:
    """Core loop. Returns (observations, rejects, field_stats)."""
    ontology = load_ontology()
    ingested_at = ingested_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    version = extractor_version(cfg, cfg_hash)
    licence, licence_flag = metadata.get("licence") or "unknown", bool(metadata.get("licence_flag", True))
    reliability = cfg["source_reliability"]

    observations: list[dict] = []
    rejects: list[dict] = []
    stats: dict[str, FieldStats] = {}

    def key_of(f):
        return f"{f['canonical']}<-{f['source'] if isinstance(f['source'], str) else '+'.join(f['source'])}"

    for f in cfg["fields"]:
        stats[key_of(f)] = FieldStats()
    # ENVELOPE settings with their own per-row column (not from_metadata) get a FieldStats entry too (step 3b, item D):
    # a parse failure on observed_at / valid_from / valid_to is otherwise invisible to validate and the packet. Their
    # keys ("observed_at", "valid_from", "valid_to") never collide with a field key, which always contains "<-".
    envelope_keys = [k for k in ("observed_at", "valid_from", "valid_to")
                     if isinstance(cfg.get(k), dict) and cfg[k].get("source")]
    for k in envelope_keys:
        stats[k] = FieldStats()

    for row in rows:
        rid = make_record_id(cfg, row)

        def per_record(key):
            """observed_at / valid_from / valid_to: a metadata value or a per-row column. Tracked in `stats[key]` and
            `rejects` exactly like a mapped field, when the setting has its own column (from_metadata has no parsing
            to track)."""
            spec = cfg.get(key)
            if not spec:
                return None, None
            if spec.get("from_metadata"):
                return metadata[spec["from_metadata"]], None
            st = stats[key]
            st.rows += 1
            raw = _value_of(spec["source"], row)
            if _is_blank(raw):
                st.blank += 1
                return None, None
            vals, ev = apply_transforms(raw, spec.get("transforms") or [])
            had_reject = False
            for kind, reason, item in ev:
                if kind == "skip":
                    st.skip += 1
                    st.skip_reasons[reason] += 1
                else:
                    had_reject = True
                    st.reject += 1
                    st.reject_reasons[reason] += 1
                    ex = {"raw": str(item)[:80], "reason": reason, "source_record_id": rid}
                    if len(st.reject_examples) < MAX_REJECT_EXAMPLES:
                        st.reject_examples.append(ex)
                    rejects.append({"source_record_id": rid, "field": key, "source_field": spec["source"],
                                    "raw_value": str(item)[:200], "reason": reason})
            if vals:
                st.ok += 1
                return vals[0], None
            # skip-only outcome: nothing was appended to rejects above, so the caller must still treat
            # this like blank and record observed_at_blank (step 3b item D regression)
            return None, (ev[-1][1] if had_reject else None)

        observed_at, err = per_record("observed_at")
        if observed_at is None:
            if err is None:   # a transform failure was already recorded inside per_record; blank needs its own reason
                rejects.append({"source_record_id": rid, "field": "observed_at", "reason": "observed_at_blank"})
            continue  # a claim with no time is not an observation
        valid_from, _ = per_record("valid_from")
        valid_to, _ = per_record("valid_to")

        # field values per group: list of (field, [values], raw)
        groups: dict[str, list] = {}
        for f in cfg["fields"]:
            st = stats[key_of(f)]
            st.rows += 1
            raw = _value_of(f["source"], row)
            if _is_blank(raw):
                st.blank += 1
                continue
            if not when_met(f.get("when"), row):   # not an error and not in the parse rate: the rule does not apply to this row
                st.skip += 1
                st.skip_reasons["when_not_met"] += 1
                continue
            values, events = apply_transforms(raw, f["transforms"])
            for kind, reason, item in events:
                if kind == "skip":
                    st.skip += 1
                    st.skip_reasons[reason] += 1
                else:
                    st.reject += 1
                    st.reject_reasons[reason] += 1
                    ex = {"raw": str(item)[:80], "reason": reason, "source_record_id": rid}
                    if len(st.reject_examples) < MAX_REJECT_EXAMPLES:
                        st.reject_examples.append(ex)
                    rejects.append({"source_record_id": rid, "field": f["canonical"],
                                    "source_field": f["source"], "raw_value": str(item)[:200], "reason": reason})
            # ontology guard on each value
            good = []
            for v in values:
                why = _ontology_ok(f["canonical"], v, ontology)
                if why:
                    st.reject += 1
                    st.reject_reasons[why] += 1
                    if len(st.reject_examples) < MAX_REJECT_EXAMPLES:
                        st.reject_examples.append({"raw": str(v)[:80], "reason": why, "source_record_id": rid})
                    rejects.append({"source_record_id": rid, "field": f["canonical"],
                                    "source_field": f["source"], "raw_value": str(v)[:200], "reason": why})
                else:
                    good.append(v)
            if good:
                st.ok += len(good)
                groups.setdefault(f.get("group", "main"), []).append((f, good, raw))

        for gname, items in groups.items():
            aligned = [(f, v, r) for f, v, r in items
                       if any(t["name"] == "split" for t in f["transforms"]) and f["canonical"] != "entity.trading_name"]
            aligned_ids = {id(f) for f, _, _ in aligned}
            n = max([len(v) for _, v, _ in aligned], default=1)
            for i in range(n):
                ref = f"{rid}#{gname}:{i}"
                emitted_fields = set()
                for f, vals, raw in items:
                    if id(f) in aligned_ids:
                        if len(vals) == n:
                            chosen = [vals[i]]
                        elif len(vals) == 1:
                            chosen = vals  # one value for several entities: applies to all
                        else:
                            if i == 0:
                                stats[key_of(f)].ok -= len(vals)  # these were counted ok above
                                stats[key_of(f)].reject += 1
                                stats[key_of(f)].reject_reasons[f"misaligned_split({len(vals)}_vs_{n})"] += 1
                            continue
                    elif f["canonical"] == "entity.trading_name":
                        chosen = vals if i == 0 else []  # all trading names belong to the first entity
                    else:
                        chosen = vals
                    for v in chosen:
                        emitted_fields.add(f["canonical"])
                        observations.append({
                            "source_id": cfg["source_id"], "source_record_id": rid, "entity_ref": ref,
                            "field": f["canonical"], "value": v,
                            "raw_value": raw if isinstance(raw, (str, int, float)) else str(raw),
                            "source_field": f["source"],
                            "observed_at": observed_at, "ingested_at": ingested_at,
                            "valid_from": valid_from, "valid_to": valid_to,
                            "licence": licence, "licence_flag": licence_flag,
                            "extractor_version": version,
                            "source_reliability": reliability[CLAIM_KIND[f["canonical"]]],
                            "field_confidence": f.get("field_confidence", f["mapping_confidence"]),
                            "derivation_level": derivation_level(f["transforms"]),
                        })
                if emitted_fields and "entity.entity_type" not in emitted_fields:
                    # Ontology: entity_type defaults to unknown. We state that explicitly (L1 default)
                    # rather than leave consumers to guess what absence means.
                    observations.append({
                        "source_id": cfg["source_id"], "source_record_id": rid, "entity_ref": ref,
                        "field": "entity.entity_type", "value": "unknown", "raw_value": None,
                        "source_field": None, "observed_at": observed_at, "ingested_at": ingested_at,
                        "valid_from": valid_from, "valid_to": valid_to, "licence": licence,
                        "licence_flag": licence_flag, "extractor_version": version,
                        "source_reliability": reliability["identity"], "field_confidence": 1.0,
                        "derivation_level": "L1", "is_default": True,
                    })
    return observations, rejects, {k: s.as_dict() for k, s in stats.items()}


def select_rows(rows: list[dict], limit: int) -> list[dict]:
    """All rows if few; otherwise evenly spaced (every n-th), so the sample spans the whole file
    and is the same every run."""
    if len(rows) <= limit:
        return rows
    return [rows[i * len(rows) // limit] for i in range(limit)]


def extract(source_id: str, limit: int = 1000) -> dict:
    """Production run for one source: approved config only; verifies the raw file is the one
    that was onboarded; writes observations, rejects and a summary."""
    cfg = load_approved_config(source_id)
    cfg_hash = sha256_of(config_path(source_id))
    src_dir = RAW_DIR / source_id
    metadata = json.loads((src_dir / "metadata.json").read_text())
    raw_path = src_dir / metadata["file"]
    if sha256_of(raw_path) != metadata["sha256"]:
        raise RuntimeError(f"{raw_path} does not match the SHA-256 recorded at download; refusing to extract")

    headers, rows = read_rows(cfg["reader"], raw_path)
    chosen = select_rows(rows, limit)
    obs, rej, stats = run_rows(cfg, chosen, metadata, cfg_hash=cfg_hash)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REJECT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / f"{source_id}.jsonl").open("w") as f:
        for o in obs:
            f.write(json.dumps(o, default=str) + "\n")
    with (REJECT_DIR / f"{source_id}.jsonl").open("w") as f:
        for r in rej:
            f.write(json.dumps(r, default=str) + "\n")
    ids = Counter(o["source_record_id"] for o in obs if o["field"] != "entity.entity_type" or not o.get("is_default"))
    summary = {
        "source_id": source_id, "extractor_version": obs[0]["extractor_version"] if obs else None,
        "rows_in_file": len(rows), "rows_extracted": len(chosen),
        "sampling": "all rows" if len(rows) <= limit else f"every {len(rows) / limit:.1f}th row",
        "observations": len(obs), "rejects": len(rej),
        "licence": metadata["licence"], "licence_flag": metadata["licence_flag"],
        "distinct_source_record_ids": len(ids), "field_stats": stats,
    }
    (OUT_DIR / f"{source_id}.summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_id")
    ap.add_argument("--limit", type=int, default=1000)
    a = ap.parse_args()
    s = extract(a.source_id, a.limit)
    print(f"{s['source_id']}: {s['rows_extracted']}/{s['rows_in_file']} rows ({s['sampling']}) "
          f"-> {s['observations']} observations, {s['rejects']} rejects")


if __name__ == "__main__":
    main()
