"""Step 4 (code only): test a draft config on rows the model never saw.

It runs the real engine (src/engine/extract.run_rows) on the held-out rows and produces a report:

  HARD FAILURES  the config must be fixed (or the field abstained):
     - structural errors (invented field, bad transform, missing column)
     - a field whose values mostly fail to parse (parse rate < 90%) or never produce a value
     - columns the config neither uses nor lists as unmapped
     - record ids that are not unique
  MEANING WARNINGS  rules that are true of real data in any source (legal name should look more
     like a company than the trading name; postcode should fit the state; ...). The model must
     change the mapping or say why it is keeping it. A warning is not proof of a mistake.
  INFO  numbers shown to the human (e.g. how often ACN equals the last 9 digits of the ABN).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date

from src.engine.config import load_ontology, structural_errors
from src.engine.extract import make_record_id, run_rows
from src.engine.transforms import _COMPANY_END

PARSE_FLOOR = 0.90        # fields below this parse rate are hard failures
MIN_JUDGED = 5            # ... but only judged once we have at least this many values
DUP_ID_LIMIT = 0.01       # more than 1% duplicate record ids is a failure
WARN_MIN_N = 10           # meaning checks need enough data to mean anything

# First digit(s) of a postcode -> plausible state (coarse; PO boxes and border towns exist).
POSTCODE_STATES = {"0": {"NT", "ACT"}, "1": {"NSW"}, "2": {"NSW", "ACT"}, "3": {"VIC"}, "4": {"QLD"},
                   "5": {"SA"}, "6": {"WA"}, "7": {"TAS"}, "8": {"VIC", "NT"}, "9": {"QLD"}}


def _referenced_columns(cfg: dict) -> set[str]:
    cols: set[str] = set(cfg["record_id"].get("from") or [])
    for f in cfg["fields"]:
        cols |= set(f["source"] if isinstance(f["source"], list) else [f["source"]])
        if isinstance(f.get("when"), dict):
            cols.add(f["when"].get("column"))
    for k in ("observed_at", "valid_from", "valid_to"):
        s = cfg.get(k)
        if s and s.get("source"):
            cols |= set(s["source"] if isinstance(s["source"], list) else [s["source"]])
    cols |= {u["source"] for u in cfg.get("unmapped", [])}
    cols |= {u["source"] for u in cfg.get("needs_transform", [])}
    return cols


def _entities(obs: list[dict]) -> dict[str, dict[str, list]]:
    ents: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for o in obs:
        ents[o["entity_ref"]][o["field"]].append(o["value"])
    return ents


def meaning_checks(cfg: dict, obs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (warnings, infos). Each has an id (so the model can answer by id) and text."""
    warnings, infos = [], []
    ents = _entities(obs)
    vals = lambda field: [v for e in ents.values() for v in e.get(field, [])]

    legal, trading = vals("entity.legal_name"), vals("entity.trading_name")
    rate = lambda xs: sum(1 for x in xs if _COMPANY_END.search(x)) / len(xs) if xs else 0
    if len(legal) >= WARN_MIN_N and len(trading) >= WARN_MIN_N and rate(trading) > rate(legal) + 0.2:
        warnings.append({"id": "name_swap", "text": (
            f"Company suffixes (Pty Ltd, Limited...) appear in {rate(trading):.0%} of values mapped to trading_name "
            f"but only {rate(legal):.0%} of values mapped to legal_name. legal_name and trading_name may be swapped.")})

    if len(legal) >= WARN_MIN_N:
        no_letters = sum(1 for x in legal if not re.search(r"[A-Za-z]", x)) / len(legal)
        if no_letters > 0.05:
            warnings.append({"id": "legal_name_no_letters", "text": (
                f"{no_letters:.0%} of legal_name values contain no letters (ids or numbers?). Wrong column?")})
        multi = sum(1 for x in legal if ";" in x) / len(legal)
        if multi > 0.05:
            warnings.append({"id": "legal_name_multiple", "text": (
                f"{multi:.0%} of legal_name values contain ';': a cell may hold several entities. Consider `split`.")})

    pairs = [(e["address.state"][0], e["address.postcode"][0]) for e in ents.values()
             if e.get("address.state") and e.get("address.postcode")]
    if len(pairs) >= WARN_MIN_N:
        agree = sum(1 for st, pc in pairs if st in POSTCODE_STATES.get(pc[0], set())) / len(pairs)
        if agree < 0.90:
            warnings.append({"id": "postcode_state", "text": (
                f"Only {agree:.0%} of address.state / address.postcode pairs are consistent "
                "(e.g. a 3xxx postcode should be VIC). The two fields may be mapped from the wrong columns.")})

    today = date.today().isoformat()
    future = [v for f in ("entity.date_registered",) for v in vals(f) if v > today]
    future += [o["valid_from"] for o in obs if o.get("valid_from") and o["valid_from"] > today]
    if future:
        warnings.append({"id": "future_dates", "text": (
            f"{len(future)} date_registered/valid_from values are in the future (e.g. {future[0]}). "
            "Wrong column, wrong date format (day/month swapped?) or not a registration date.")})

    both = [(e["entity.abn"][0], e["entity.acn"][0]) for e in ents.values() if e.get("entity.abn") and e.get("entity.acn")]
    if both:
        same = sum(1 for a, c in both if a[-9:] == c) / len(both)
        infos.append({"id": "abn_acn_overlap", "text": (
            f"Where one entity has both an ABN and an ACN ({len(both)} cases), the ACN equals the last 9 digits of "
            f"the ABN in {same:.0%}. Reported as evidence only; not assumed anywhere.")})
    return warnings, infos


def validate(cfg: dict, headers: list[str], held_rows: list[dict], metadata: dict, empty_columns: set[str]) -> dict:
    ontology = load_ontology()
    structural = structural_errors(cfg, ontology, headers, metadata)
    report = {"structural_errors": structural, "field_failures": [], "unaccounted_columns": [],
              "duplicate_ids": None, "warnings": [], "infos": [], "stats": {}, "n_rows": len(held_rows)}
    if structural:  # cannot run the engine on a broken config
        report["hard_failure_count"] = len(structural)
        return report

    obs, rejects, stats = run_rows(cfg, held_rows, metadata)
    report["stats"] = stats

    for f in cfg["fields"]:
        key = f"{f['canonical']}<-{f['source'] if isinstance(f['source'], str) else '+'.join(f['source'])}"
        s = stats[key]
        judged, nonblank = s["ok"] + s["reject"], s["rows"] - s["blank"]
        why = None
        if judged >= MIN_JUDGED and s["parse_rate"] < PARSE_FLOOR:
            why = f"parse rate {s['parse_rate']:.0%} is below {PARSE_FLOOR:.0%}"
        elif nonblank >= MIN_JUDGED and s["ok"] == 0:
            why = "never produced a valid value although the source column is filled"
        if why:
            report["field_failures"].append({
                "key": key, "reason": why, "reject_reasons": s["reject_reasons"],
                "skip_reasons": s["skip_reasons"], "examples": s["reject_examples"]})

    unaccounted = sorted(set(headers) - _referenced_columns(cfg) - empty_columns)
    report["unaccounted_columns"] = unaccounted

    # duplicates among *rows* (not observations): count rows by id directly
    row_ids = Counter(make_record_id(cfg, r) for r in held_rows)
    dups = sum(c - 1 for c in row_ids.values() if c > 1)
    report["duplicate_ids"] = {"duplicate_rows": dups, "of": len(held_rows)}
    id_fail = len(held_rows) and dups / len(held_rows) > DUP_ID_LIMIT

    report["warnings"], report["infos"] = meaning_checks(cfg, obs)
    report["hard_failure_count"] = len(report["field_failures"]) + len(unaccounted) + (1 if id_fail else 0)
    report["id_failure"] = bool(id_fail)
    report["observations"] = len(obs)
    report["rejects"] = len(rejects)
    return report


def unanswered_warnings(report: dict, cfg: dict) -> list[dict]:
    answered = {r["check_id"] for r in cfg.get("meaning_check_responses", [])}
    return [w for w in report["warnings"] if w["id"] not in answered]


def needs_revision(report: dict, cfg: dict) -> bool:
    return report["hard_failure_count"] > 0 or bool(unanswered_warnings(report, cfg))


def report_as_text(report: dict, cfg: dict) -> str:
    """The failure report, written for the model."""
    lines = []
    if report["structural_errors"]:
        lines.append("STRUCTURAL ERRORS (config unusable until fixed):")
        lines += [f"- {e}" for e in report["structural_errors"]]
        return "\n".join(lines)
    lines.append(f"Tested on {report['n_rows']} held-out rows: {report['observations']} observations, {report['rejects']} rejected values.")
    if report["field_failures"]:
        lines.append("\nHARD FAILURES (fix these or move the column to `unmapped`):")
        for f in report["field_failures"]:
            lines.append(f"- {f['key']}: {f['reason']}. reject reasons={f['reject_reasons']} skips={f['skip_reasons']} examples={f['examples']}")
    if report["unaccounted_columns"]:
        lines.append(f"\nCOLUMNS NOT ACCOUNTED FOR (map them, or list in `unmapped` with a reason): {report['unaccounted_columns']}")
    if report["id_failure"]:
        lines.append(f"\nRECORD ID NOT UNIQUE: {report['duplicate_ids']}. Choose a better key or use hash_row.")
    todo = unanswered_warnings(report, cfg)
    if todo:
        lines.append("\nMEANING WARNINGS (answer each by id in `warning_responses`: change the mapping, or keep it and say why):")
        lines += [f"- [{w['id']}] {w['text']}" for w in todo]
    return "\n".join(lines)
