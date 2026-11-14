"""Which sources resolve, graph, profiles and the register row filter read.

BASE is the six round-1 sources (kept for tests, docs and the hand-check labels). `active_sources()` adds every other
source whose configs/<id>.approval.json says approved AND whose observations were extracted, so a newly onboarded
dataset reaches the matcher. With no such source it returns BASE exactly, so the six-source results stay reproducible.
Reference registers (configs/reference_sources.yaml) are never mentions.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = ["asic_credit_licensee", "qbcc_licensed_contractors", "qld_health_contracts_2023_24",
        "wa_tenders_awards_2023_24", "vic_liquor_licences", "act_notifiable_invoices"]


def active_sources(config_dir: Path | None = None, obs_dir: Path | None = None, reference: set | None = None,
                   skipped: list | None = None) -> list[str]:
    from src.engine.config import CONFIG_DIR
    from src.part3_resolve.features import OBS_DIR, reference_sources
    config_dir, obs_dir = Path(config_dir or CONFIG_DIR), Path(obs_dir or OBS_DIR)
    reference = set(reference_sources()) if reference is None else reference
    extra = []
    for ap in sorted(config_dir.glob("*.approval.json")):
        sid = ap.name[: -len(".approval.json")]
        if sid in BASE or sid in reference:
            continue
        try:
            approved = json.loads(ap.read_text()).get("status") == "approved"
        except ValueError:
            approved = False
        if not approved:
            continue
        if (obs_dir / f"{sid}.jsonl").exists():
            extra.append(sid)
        elif skipped is not None:
            skipped.append(sid)   # approved but not extracted yet: run `python -m src.engine.extract <id>`
    return BASE + sorted(extra)


def announce_sources() -> list[str]:
    """active_sources(), printed, so a stale approved config can never change results silently."""
    skipped: list[str] = []
    srcs = active_sources(skipped=skipped)
    print(f"sources ({len(srcs)}): {', '.join(srcs)}" + (f"  [{len(srcs) - len(BASE)} beyond the six]" if len(srcs) > len(BASE) else ""))
    if skipped:
        print(f"approved but NOT extracted yet (left out): {', '.join(skipped)}")
    return srcs
