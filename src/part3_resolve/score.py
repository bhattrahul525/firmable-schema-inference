"""Scoring: pair features -> (link_confidence, tier, reason).

Versioned on purpose. Every link stores MATCHER_VERSION and the raw features, so when a better
matcher exists we can re-score old links from the stored features (see rescore.py) instead of
re-running everything. A new scoring function is a new entry in SCORERS; old versions stay.

link_confidence is a hand-set score per evidence tier. It is NOT calibrated. Calibration comes
from the hand check: we report measured precision per tier, never the score as a probability.
"""

from __future__ import annotations

from src.part3_resolve.features import name_core

MATCHER_VERSION = "m2.0"
ACCEPT = 0.80  # main threshold: links at or above are proposed
LOOSE = 0.60   # looser threshold: [0.60, 0.80) is reported separately; below is the unlinked queue

NAME_OK = 0.5  # name containment needed to believe an identifier match is the same business (m1.x)
# m2.0: two names "agree" when their rarity-weighted overlap (idf.py) is at least this. Hand-set, recorded in
# DECISIONS.md, never tuned against hand-check labels.
NAME_AGREE_MIN = 0.6
UNVERIFIED_CAP = 0.79  # a link resting on an ABN whose field evidence is `unverified` cannot be accepted


def score_m1_0(f: dict) -> tuple[float, str, str | None]:
    """Returns (confidence, tier, queue_reason). queue_reason is set when we refuse (conf < LOOSE)."""
    names_agree = f["name_containment"] >= NAME_OK or f["shared_trading_name"]

    # Tier 1: an identifier that is checksum-valid and equal. Strongest evidence we have, but an
    # ID match with names that disagree is suspicious (ID reuse, data entry error): refuse and say why.
    if f["abn_equal"] or f["acn_equal"]:
        tier = "T1_abn_equal" if f["abn_equal"] else "T1_acn_equal"
        if names_agree:
            return (0.98 if f["abn_equal"] else 0.96), tier, None
        return 0.40, tier, "identifier_match_but_names_conflict"

    # Tier 2: ACN equals the last 9 digits of the other record's ABN. 'Often but not always' the
    # same entity, so we also require the names to agree.
    if f["acn_is_abn_suffix"]:
        if names_agree:
            return 0.88, "T2_acn_in_abn", None
        return 0.40, "T2_acn_in_abn", "acn_suffix_match_but_names_conflict"

    # Tier 3: name evidence only. Never for people, never when the two sides carry different ABNs.
    if f["abn_differ"]:
        return 0.0, "T3_name", "name_match_but_different_abns"
    if f["name_exact"]:
        if f["person_like"]:
            return 0.0, "T3_name", "person_name_not_linked_by_name"
        if f["name_tokens"] < 2 and f["name_len"] < 8:
            return 0.0, "T3_name", "name_too_generic"
        if f["postcode_equal"]:
            return 0.85, "T3_name_postcode", None
        if f["postcode_differ"] or f["state_differ"]:
            return 0.30, "T3_name", "name_match_but_locations_differ"
        if f["state_equal"]:
            return 0.70, "T3_name_state", None
        if f["both_company"]:  # identical full company name incl. Pty Ltd on both sides, no address to check
            return 0.65, "T3_name_company", None
        return 0.55, "T3_name", "name_match_without_location_evidence"
    # near-miss names in the same postcode block: never linked, but worth a human look
    return 0.50, "T3_fuzzy", "similar_name_not_exact"


# Words that say where or what kind of company it is, not WHICH company. Two names that share only these
# ("Cantel (Australia)" / "Steris Australia") should not count as agreeing.
GENERIC_WORDS = {"australia", "australian", "australasia", "group", "services", "holdings", "international",
                 "pacific", "global", "solutions", "company", "queensland", "nsw", "victoria", "and", "of"}


def score_m1_1(f: dict) -> tuple[float, str, str | None]:
    """m1.0 plus one rule, computed ONLY from the features stored on each link (so it can be applied to old
    links without re-reading any source): an identifier match whose names share nothing but generic words
    is refused instead of accepted."""
    conf, tier, why = score_m1_0(f)
    if tier.startswith(("T1", "T2")) and conf >= ACCEPT and not f["shared_trading_name"]:
        shared = set(name_core(f["name_a"]).split()) & set(name_core(f["name_b"]).split())
        if not shared - GENERIC_WORDS:
            return 0.40, tier, "identifier_match_but_only_generic_words_shared"
    return conf, tier, why


def score_m1_2(f: dict) -> tuple[float, str, str | None]:
    """m1.2 scores exactly like m1.0. It is NOT built on m1.1: the hand check showed m1.1's generic-words rule
    demoted a TRUE link (Cantel (Australia) -> Steris Australia, a registered rename on the same ABN), so that rule
    is rejected, not shipped. What m1.2 changes is the canonical key of name-only links (see keys.py)."""
    return score_m1_0(f)


def score_m2_0(f: dict) -> tuple[float, str, str | None]:
    """m2.0: rarity-weighted names, T1/T1r/T2 identifier tiers, T3 register name bridge, T4 exact-name tiers.
    Pure function of the stored features. T3c (a second independent register hit) is NOT built.
    `why` is the queue reason when refused, or a note when a non-refused link was capped."""
    conf, tier, why = _tiers_m2_0(f)
    if f.get("abn_unverified") and conf >= ACCEPT:
        return UNVERIFIED_CAP, tier, "abn_evidence_unverified_cap"
    return conf, tier, why


def _tiers_m2_0(f: dict) -> tuple[float, str, str | None]:
    agree = f["name_overlap"] >= NAME_AGREE_MIN or f.get("shared_trading_name", False) or f.get("name_exact", False)
    if f.get("kind") == "register":  # mention vs Business Names record (R2)
        if f["abn_differ"]:
            return 0.0, "T3_register_name", "name_match_but_different_abns"
        if f["abn_equal"]:  # only generated when the names agree
            return 0.98, "T1_register_abn", None
        if f["holders"] > 1:
            return 0.0, "T3_register_name", "name_matches_more_than_one_holder"
        if f["person_like"]:
            return 0.0, "T3_register_name", "person_name_not_linked_by_name"
        if f["generic_name"]:
            return 0.0, "T3_register_name", "generic_name"
        return 0.65, "T3_register_name", None  # one registered holder, name only: loose, never promoted

    if f["abn_equal"] or f["acn_equal"]:
        tier = "T1_abn_equal" if f["abn_equal"] else "T1_acn_equal"
        if agree:
            return 0.98, tier, None
        # R3: the register confirms ONE side's name only (a Business Names name under this ABN); weaker than the design
        if f["abn_equal"] and (f["bn_confirms_a"] or f["bn_confirms_b"]):
            return 0.95, "T1r_abn_equal_bn_name", None
        return 0.40, tier, "identifier_match_but_names_conflict"
    if f["acn_is_abn_suffix"]:
        if agree:
            return 0.88, "T2_acn_in_abn", None
        return 0.40, "T2_acn_in_abn", "acn_suffix_match_but_names_conflict"
    if f["abn_differ"]:
        return 0.0, "T4_name", "name_match_but_different_abns"
    if f["name_exact"]:
        if f["person_like"]:
            return 0.0, "T4_name", "person_name_not_linked_by_name"
        if f["generic_name"]:
            return 0.0, "T4_name", "generic_name"
        if f["postcode_differ"] or f["state_differ"]:
            return 0.30, "T4_name", "name_match_but_locations_differ"
        if f["postcode_equal"]:
            return 0.70, "T4_name_postcode", None  # loose; NOT promoted this round
        if f["state_equal"]:
            return 0.70, "T4_name_state", None
        if f["both_company"]:
            return 0.65, "T4_name_company", None
        return 0.55, "T4_name", "name_match_without_location_evidence"
    return 0.50, "T4_fuzzy", "similar_name_not_exact"


SCORERS = {"m1.0": score_m1_0, "m1.1": score_m1_1, "m1.2": score_m1_2, "m2.0": score_m2_0}
# versions whose canonical-key rule (keys.rekey_conflicting_name_links) applies
KEY_RULE_VERSIONS = {"m1.2", "m2.0"}


def band(conf: float) -> str:
    return "accepted" if conf >= ACCEPT else "loose" if conf >= LOOSE else "refused"
