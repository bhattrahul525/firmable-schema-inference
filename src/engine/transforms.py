"""The whitelist of transforms a mapping config may use.

The agent can only pick from this list; it cannot write code. That is what keeps
"config beats code": a new source never needs a new parser, and if a source needs
something not on this list, the agent must say so (`needs_transform`) instead of faking it.

Each transform takes one value and returns one of:
  * a value            -> carried to the next transform
  * None               -> "nothing here" (blank cell); the field is simply absent
  * raises Skip(why)   -> "this rule does not apply to this value" (e.g. `abn` given a 9-digit
                          ACN). Not an error; counted separately.
  * raises Reject(why) -> the value is present but wrong (bad checksum, unparseable date).
                          Not emitted; written to the rejects file; counts against parse rate.

A transform may return a list (only `split`); the engine then handles each item.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from src.common.ids import digits_only, is_valid_abn, is_valid_acn


class Skip(Exception):
    """Rule not applicable to this value."""


class Reject(Exception):
    """Value present but invalid."""


def _text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)  # Excel gives 3953.0 for a postcode
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def clean_whitespace(v, _arg=None):
    """Trim, turn non-breaking spaces into spaces, collapse runs. Blank -> None."""
    s = re.sub(r"\s+", " ", _text(v).replace("\xa0", " ")).strip()
    return s or None


def upper(v, _arg=None):
    s = clean_whitespace(v)
    return s.upper() if s else None


def abn(v, _arg=None):
    """11-digit ABN, validated by checksum. Any other length is not an ABN (Skip)."""
    d = digits_only(v)
    if not d:
        if clean_whitespace(v):
            raise Skip("not_digits")
        return None
    if len(d) != 11:
        raise Skip(f"not_11_digits({len(d)})")
    if not is_valid_abn(d):
        raise Reject("abn_checksum_failed")
    return d


def acn(v, _arg=None):
    """9-digit ACN, validated by checksum. Exactly 9 digits (we do not zero-pad)."""
    d = digits_only(v)
    if not d:
        if clean_whitespace(v):
            raise Skip("not_digits")
        return None
    if len(d) != 9:
        raise Skip(f"not_9_digits({len(d)})")
    if not is_valid_acn(d):
        raise Reject("acn_checksum_failed")
    return d


def split(v, sep):
    """Split one cell into several values (e.g. 'A Pty Ltd; B Pty Ltd'). Returns a list."""
    s = clean_whitespace(v)
    if not s:
        return None
    parts = [clean_whitespace(p) for p in s.split(str(sep))]
    return [p for p in parts if p]


def regex_extract(v, pattern):
    """First capture group of `pattern`; no match -> Skip."""
    s = clean_whitespace(v)
    if not s:
        return None
    m = re.search(pattern, s)
    if not m:
        raise Skip("regex_no_match")
    return m.group(1) if m.groups() else m.group(0)


def parse_date(v, formats):
    """To ISO date (YYYY-MM-DD). `formats` is a strptime format or list of them.
    Real date/datetime cells (from xlsx) pass straight through."""
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = clean_whitespace(v)
    if not s:
        return None
    for fmt in ([formats] if isinstance(formats, str) else list(formats)):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    raise Reject("date_unparseable")


def map_values(v, table):
    """Map raw values to canonical ones, case-insensitively. A value not in the table is a
    Reject (so the validator shows the agent exactly which raw values it forgot)."""
    s = clean_whitespace(v)
    if not s:
        return None
    lookup = {str(k).strip().lower(): val for k, val in table.items()}
    if s.lower() not in lookup:
        raise Reject(f"unmapped_value:{s[:40]}")
    return lookup[s.lower()]


_COMPANY_END = re.compile(
    r"\b(pty\.?\s*ltd|pty\.?\s*limited|proprietary\s+limited|limited|ltd)\.?\)?\s*$", re.I)


def entity_type_from_suffix(v, _arg=None):
    """'company' if the name ends in Pty Ltd / Limited / Ltd, else 'unknown'.
    Derivation level L1 (deterministic rule on the name). Never guesses any other type:
    'Smith Family Trust' stays 'unknown'."""
    s = clean_whitespace(v)
    if not s:
        return None
    return "company" if _COMPANY_END.search(s) else "unknown"


_STATES = {
    "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT", "NZ",
}
_STATE_NAMES = {
    "NEW SOUTH WALES": "NSW", "VICTORIA": "VIC", "QUEENSLAND": "QLD",
    "WESTERN AUSTRALIA": "WA", "SOUTH AUSTRALIA": "SA", "TASMANIA": "TAS",
    "AUSTRALIAN CAPITAL TERRITORY": "ACT", "NORTHERN TERRITORY": "NT",
    "NEW ZEALAND": "NZ",
}


def state_code(v, _arg=None):
    """To the ontology's state enum. Codes pass through; full names are converted.
    Anything else is a Reject (we do not map it to OTHER silently)."""
    s = clean_whitespace(v)
    if not s:
        return None
    u = s.upper().replace(".", "")
    if u in _STATES:
        return u
    if u in _STATE_NAMES:
        return _STATE_NAMES[u]
    raise Reject(f"unknown_state:{s[:20]}")


def postcode(v, _arg=None):
    """4-digit Australian postcode. A 3-digit value gets its leading zero back (NT/ACT
    postcodes like 0800 lose it in Excel)."""
    d = digits_only(v)
    if not d:
        if clean_whitespace(v):
            raise Reject("postcode_not_digits")
        return None
    if len(d) == 3:
        d = "0" + d
    if len(d) != 4:
        raise Reject(f"postcode_length({len(d)})")
    return d


def join_nonempty(values, sep):
    """For multi-column fields: join the non-blank values with `sep`. Input is a list."""
    parts = [clean_whitespace(x) for x in values]
    parts = [p for p in parts if p]
    return str(sep).join(parts) if parts else None


# name -> (function, description shown to the agent, argument description or None)
CATALOGUE: dict[str, tuple] = {
    "clean_whitespace": (clean_whitespace, "Trim, fix non-breaking spaces, collapse runs of spaces. Blank -> absent.", None),
    "upper": (upper, "Clean whitespace and upper-case.", None),
    "abn": (abn, "Validate an 11-digit ABN by checksum. Other lengths are skipped (not an ABN); an 11-digit value with a bad checksum is rejected.", None),
    "acn": (acn, "Validate a 9-digit ACN by checksum. Other lengths are skipped; a 9-digit value with a bad checksum is rejected.", None),
    "split": (split, "Split one cell into several values. Argument: the separator, e.g. ';'. Returns a list; every later transform applies to each item.", "separator string"),
    "regex_extract": (regex_extract, "Take the first capture group of a regex. Argument: the pattern. No match -> skipped.", "regex pattern"),
    "parse_date": (parse_date, "Parse to ISO date. Argument: a strptime format string or a JSON list of formats, e.g. [\"%d/%m/%Y\"]. Real date cells pass through.", "strptime format or list of formats"),
    "map_values": (map_values, "Map raw values to canonical values. Argument: a JSON object {\"raw\": \"canonical\"}. Raw values not in the table are rejected.", "JSON object of raw -> canonical"),
    "entity_type_from_suffix": (entity_type_from_suffix, "Apply to a NAME column when mapping entity.entity_type: 'company' if the name ends in Pty Ltd / Limited / Ltd, else 'unknown'. Use only when the source has no explicit entity-type column.", None),
    "state_code": (state_code, "To the ontology state enum (NSW, VIC, ...). Full state names are converted.", None),
    "postcode": (postcode, "4-digit Australian postcode (restores a dropped leading zero).", None),
    "join_nonempty": (join_nonempty, "ONLY as the first transform when `source` is a list of columns: join the non-blank values. Argument: separator, e.g. ', '.", "separator string"),
}
