"""Step 2 of triage: score each dataset's *metadata* for business-entity signals.

Cheap and runs over the whole pool. It only decides which datasets are worth
the more expensive content probe (probe.py); the final confidence leans mostly
on the probe because metadata can be misleading (a dataset *about* business
licensing policy may contain no businesses at all).

The score is a plain weighted keyword count, so every point is traceable to a
named signal. That is what the one-line reason in the shortlist is built from.
"""

from __future__ import annotations

import re

# (label, regex, weight). Matched against title + description + tags + resource
# names, lower-cased. Each signal counts once per dataset, however often it occurs.
POSITIVE = [
    ("mentions ABN", r"\babns?\b|australian business number", 4),
    ("mentions ACN", r"\bacns?\b|australian company number", 3),
    ("business/trading name", r"business names?|trading names?|company names?|entity names?", 3),
    ("licensee/licence holder", r"licensees?|licen[cs]e holders?|permit holders?", 3),
    ("supplier/contractor", r"\bsuppliers?\b|\bcontractors?\b|\bvendors?\b", 3),
    ("contract/tender", r"\bcontracts? (awarded|disclos|notice|register)|\btenders?\b|procurement", 2),
    ("register/list of", r"\bregister\b|\blist of\b|\bdirectory\b", 2),
    ("licence/permit", r"\blicen[cs]es?\b|\bpermits?\b|\bapprovals?\b|\baccredit", 1),
    ("grant recipients", r"grant recipients?|recipients? of|funding recipients?|grantees?", 2),
    ("company suffix in text", r"\bpty\.? ?ltd\b|\blimited\b|\bincorporated\b", 2),
    ("businesses/companies", r"\bbusinesses\b|\bcompanies\b|\bemployers?\b|\boperators?\b|\borgani[sz]ations\b", 1),
]
NEGATIVE = [
    ("statistical/aggregate", r"statistic|aggregat|\bcensus\b|\bindicators?\b|time series|summary", -3),
    ("spatial/imagery", r"boundar|\bspatial\b|imagery|elevation|lidar|\bdem\b|aerial|\bgeolog", -3),
    ("environmental measurement", r"weather|rainfall|water quality|air quality|monitoring site|species|vegetation", -3),
    ("budget/financial report", r"\bbudget\b|annual report|financial statements", -2),
]

TABULAR = {"CSV", "XLSX", "XLS", "JSON", "TSV", "TXT"}
NON_TABULAR_ONLY = {"PDF", "WMS", "WFS", "SHP", "KML", "KMZ", "HTML", "WEBSITE LINK", "API", "ZIP", "GEOJSON", "ESRI REST", "DOCX"}

# metadata raw score at which we call it "1.0". Chosen so a dataset with an ABN
# mention + a register/supplier signal + a tabular file lands near the top.
META_SCALE = 12.0


def _text(rec: dict) -> str:
    parts = [rec["title"], rec["notes"], " ".join(rec["tags"])]
    parts += [r["name"] for r in rec["resources"]]
    return " ".join(parts).lower()


def score_metadata(rec: dict) -> dict:
    text = _text(rec)
    raw = 0.0
    signals: list[str] = []
    for label, pattern, weight in POSITIVE + NEGATIVE:
        if re.search(pattern, text):
            raw += weight
            signals.append(f"{label} ({weight:+d})")

    formats = {r["format"] for r in rec["resources"] if r["format"]}
    if formats & TABULAR:
        raw += 2
        signals.append("tabular file (+2)")
    elif not rec["resources"]:
        raw -= 4
        signals.append("no resources (-4)")
    elif formats and formats <= NON_TABULAR_ONLY:
        raw -= 3
        signals.append("no tabular file (-3)")

    meta = max(0.0, min(1.0, raw / META_SCALE))
    return {"meta_raw": raw, "meta_score": round(meta, 3), "meta_signals": signals, "formats": sorted(formats)}
