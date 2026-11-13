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
import signal
import threading
import time
from collections import Counter
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


# --- regex safety (ARCHITECTURE.md section c). One helper for regex_extract, regex_replace and `when.matches`. ---
MAX_PATTERN_CHARS = 200     # config time: a longer pattern is refused
REGEX_SECONDS = 1.0         # run time: one match or substitution may take this long (SIGALRM: Unix, main thread only)
REGEX_MAX_TIMEOUTS = 20     # after this many timeouts one pattern is switched off for the rest of the process
_TIMEOUTS: Counter = Counter()


class _RegexTimeout(Exception):
    pass


def pattern_error(pattern) -> str | None:
    """Why `pattern` cannot be used, or None. A sentence, so it can go back to the model. Never raises."""
    if not isinstance(pattern, str) or not pattern:
        return "the pattern must be a non-empty string"
    if len(pattern) > MAX_PATTERN_CHARS:
        return f"the pattern is longer than {MAX_PATTERN_CHARS} characters"
    try:
        re.compile(pattern)
    except re.error as e:
        return f"the pattern does not compile ({e})"
    return None


def run_regex(pattern, fn):
    """fn(compiled_pattern) under a REGEX_SECONDS timer. Raises Reject (never re.error): bad_pattern, regex_timeout,
    regex_switched_off. The timer nests inside guard.tool_deadline's: the outer remaining time is read first and put back
    afterwards, and if the outer timer would fire sooner, no inner timer is set (the tool deadline wins).
    shortcut: no timer on Windows or off the main thread (only the length and compile checks apply); upgrade = run regex in a subprocess."""
    if _TIMEOUTS[pattern] >= REGEX_MAX_TIMEOUTS:
        raise Reject("regex_switched_off")
    try:
        rx = re.compile(pattern)
    except (re.error, TypeError):
        raise Reject("bad_pattern")
    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        return _guarded(rx, fn)
    outer_left, _ = signal.getitimer(signal.ITIMER_REAL)
    if outer_left and outer_left <= REGEX_SECONDS:
        return _guarded(rx, fn)

    def on_alarm(signum, frame):
        raise _RegexTimeout()
    old = signal.signal(signal.SIGALRM, on_alarm)
    t0 = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, REGEX_SECONDS)
    try:
        return _guarded(rx, fn)
    except _RegexTimeout:
        _TIMEOUTS[pattern] += 1
        raise Reject("regex_timeout")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
        if outer_left:
            signal.setitimer(signal.ITIMER_REAL, max(outer_left - (time.monotonic() - t0), 0.001))


def _guarded(rx, fn):
    try:
        return fn(rx)
    except re.error:   # e.g. a bad group reference in `repl`
        raise Reject("bad_pattern")


def regex_extract(v, pattern):
    """First capture group of `pattern`; no match -> Skip."""
    s = clean_whitespace(v)
    if not s:
        return None
    m = run_regex(pattern, lambda rx: rx.search(s))
    if not m:
        raise Skip("regex_no_match")
    return m.group(1) if m.groups() else m.group(0)


_GROUP_REF = re.compile(r"\\(?:g<[^>]*>|\d{1,2})")


def _words_in(text: str) -> bool:
    """True if `text` holds a letter or digit (any script). Template / repl literals may not."""
    return bool(re.search(r"[^\W_]", text))


def regex_replace_error(arg) -> str | None:
    """Config-time check of regex_replace's argument {"pattern", "repl"}. One sentence or None."""
    if not isinstance(arg, dict) or set(arg) != {"pattern", "repl"} or not isinstance(arg["repl"], str):
        return "regex_replace needs an argument {\"pattern\": ..., \"repl\": ...}"
    bad = pattern_error(arg["pattern"])
    if bad:
        return f"regex_replace: {bad}"
    if _words_in(_GROUP_REF.sub("", arg["repl"])):
        return "regex_replace: `repl` may hold only separators and group references (\\1), no letters or digits"
    try:
        re.sub(arg["pattern"], arg["repl"], "")   # parses `repl` (a bad group reference raises even with no match)
    except re.error as e:
        return f"regex_replace: `repl` is not valid ({e})"
    return None


def regex_replace(v, arg):
    """Replace every match of arg['pattern'] by arg['repl']. No match leaves the value; an empty result is absent."""
    s = clean_whitespace(v)
    if not s:
        return None
    return clean_whitespace(run_regex(arg["pattern"], lambda rx: rx.sub(arg["repl"], s)))


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


_PLACEHOLDER = re.compile(r"\{(\d+)\}")


def template_error(arg, n_cols: int) -> str | None:
    """Config-time check of template's argument, a string like "{1}, {2} {3}" (1-based positions in `source`)."""
    if not isinstance(arg, str):
        return "template needs a string argument such as \"{1}, {2}\""
    nums = [int(n) for n in _PLACEHOLDER.findall(arg)]
    if not nums:
        return "template needs at least one placeholder such as {1}"
    if min(nums) < 1 or max(nums) > n_cols:
        return f"template placeholders must be between {{1}} and {{{n_cols}}} (the number of source columns)"
    if _words_in(_PLACEHOLDER.sub("", arg)):
        return "template: the text between placeholders may hold only separators, no letters or digits"
    return None


def template(values, arg):
    """Fill {n} in `arg` with the n-th source column. All blank -> absent; some blank -> Reject (a half-built value is
    worse than none). Plain re.sub, never str.format (a config must not reach into Python objects)."""
    parts = [clean_whitespace(x) for x in (values if isinstance(values, list) else [values])]
    if not any(parts):
        return None
    used = {int(n) for n in _PLACEHOLDER.findall(arg)}
    if any(n > len(parts) or not parts[n - 1] for n in used):
        raise Reject("template_missing_part")
    return clean_whitespace(_PLACEHOLDER.sub(lambda m: parts[int(m.group(1)) - 1], arg))


def constant(v, arg):
    """A fixed value (the engine only calls this where the anchor column is not blank). Not read from the source:
    config marks it L3 and caps its confidence."""
    return str(arg)


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
    "regex_replace": (regex_replace, "Replace every match of a regex. Argument: {\"pattern\": ..., \"repl\": ...}. `repl` may hold only separators and group references (\\1), never words. No match leaves the value unchanged; an empty result is absent.", "JSON object {pattern, repl}"),
    "template": (template, "ONLY as the first transform: build one value from the `source` columns (a list, or one column). Argument: text with {1}, {2}... for the source columns in order, e.g. \"{1}, {2} {3}\". Text between placeholders: separators only. All parts blank -> absent; some blank -> rejected.", "text with {n} placeholders"),
    "constant": (constant, "ONLY for address.state / address.country, as the sole transform, with `source` = one anchor column: emits the fixed argument on rows where the anchor is not blank. Marked as not read from the source (level L3, confidence capped, evidence `asserted`). Argument: the value, e.g. \"VIC\".", "the fixed value"),
}

# Added in step 4a. The round-1 pipeline (llm_steps.py) keeps its fixed list of the original 12 names.
STEP4A_TRANSFORMS = {"regex_replace", "template", "constant"}
