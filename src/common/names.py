"""Shared name normalisation: the one place a name becomes a comparison key (filter, matcher and IDF all use it)."""

from __future__ import annotations

import re

# Words that carry no identity ("Acme Pty Ltd" and "ACME PTY. LIMITED" are the same name).
SUFFIX_TOKENS = {"pty", "ltd", "limited", "proprietary", "inc", "incorporated", "the"}
ATF = re.compile(r"\s+(?:ATF|A\.T\.F\.?|as trustee for)\s+", re.I)


def name_core(name: str | None) -> str:
    """Normalised comparison form: lower-case, '&'->'and', punctuation and literal quote characters gone, suffix words dropped,
    and anything after 'ATF' (acting as trustee for ...) cut off, because that names the trust,
    not the company."""
    if not name:
        return ""
    name = ATF.split(name)[0]
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower().replace("&", " and "))
    return " ".join(t for t in s.split() if t not in SUFFIX_TOKENS)
