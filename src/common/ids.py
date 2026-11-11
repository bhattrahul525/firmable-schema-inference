"""Australian business identifiers: normalise and validate ABN / ACN by checksum.

The ontology says to validate these by checksum, not by length. Length-only checks
let through any 11-digit number (phone numbers, invoice numbers, row IDs), which
would poison entity matching later.

ABN algorithm (Australian Business Register):
  1. Subtract 1 from the first digit.
  2. Multiply each of the 11 digits by its weight: 10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19.
  3. Valid if the sum is divisible by 89.

ACN algorithm (ASIC):
  1. Multiply the first 8 digits by weights 8, 7, 6, 5, 4, 3, 2, 1 and sum.
  2. check = (10 - sum % 10) % 10
  3. Valid if check equals the 9th digit.
"""

from __future__ import annotations

import re

ABN_WEIGHTS = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
ACN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 1)

# Digits with optional spaces, as ABNs are usually written "51 824 753 556".
# Lookarounds stop us matching a slice of a longer number.
_ABN_IN_TEXT = re.compile(r"(?<!\d)(\d{2}\s?\d{3}\s?\d{3}\s?\d{3})(?!\d)")
_ACN_IN_TEXT = re.compile(r"(?<!\d)(\d{3}\s?\d{3}\s?\d{3})(?!\d)")


def digits_only(value: object) -> str:
    """Strip everything except digits. Handles ints, floats read from Excel
    (e.g. 51824753556.0) and strings with spaces or dashes."""
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value or not value.is_integer():  # NaN or fractional
            return ""
        value = int(value)
    return re.sub(r"\D", "", str(value))


def normalise_abn(value: object) -> str | None:
    """Return the 11-digit ABN if `value` is a checksum-valid ABN, else None."""
    d = digits_only(value)
    return d if is_valid_abn(d) else None


def normalise_acn(value: object) -> str | None:
    """Return the 9-digit ACN if `value` is a checksum-valid ACN, else None.

    Spreadsheets often drop leading zeros (000 000 019 -> 19), so we left-pad
    up to 9 digits before checking. Padding is safe because the checksum still
    has to pass."""
    d = digits_only(value)
    if 0 < len(d) < 9:
        d = d.zfill(9)
    return d if is_valid_acn(d) else None


def is_valid_abn(abn: str) -> bool:
    if len(abn) != 11 or not abn.isdigit():
        return False
    digits = [int(c) for c in abn]
    digits[0] -= 1
    return sum(d * w for d, w in zip(digits, ABN_WEIGHTS)) % 89 == 0


def is_valid_acn(acn: str) -> bool:
    if len(acn) != 9 or not acn.isdigit():
        return False
    digits = [int(c) for c in acn]
    total = sum(d * w for d, w in zip(digits[:8], ACN_WEIGHTS))
    return (10 - total % 10) % 10 == digits[8]


def find_abns(text: str) -> list[str]:
    """All checksum-valid ABNs appearing in free text, in order, de-duplicated."""
    found: list[str] = []
    for m in _ABN_IN_TEXT.finditer(text or ""):
        abn = normalise_abn(m.group(1))
        if abn and abn not in found:
            found.append(abn)
    return found


def find_acns(text: str) -> list[str]:
    """All checksum-valid ACNs appearing in free text. Note: about 1 in 10 random
    9-digit numbers passes the ACN checksum, so this is weak evidence on its own;
    callers should require context (a column called ACN, or 'ACN' nearby)."""
    found: list[str] = []
    for m in _ACN_IN_TEXT.finditer(text or ""):
        acn = normalise_acn(m.group(1))
        if acn and acn not in found:
            found.append(acn)
    return found
