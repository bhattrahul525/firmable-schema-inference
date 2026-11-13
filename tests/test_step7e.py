from src.part3_resolve import handcheck


def run(tmp_path, tag):
    handcheck.STEP8_SHEET = tmp_path / f"sheet_{tag}.csv"
    handcheck.STEP8_KEY = tmp_path / f"key_{tag}.csv"
    handcheck.make_step8()
    return handcheck.STEP8_SHEET.read_text(encoding="utf-8-sig"), handcheck.STEP8_KEY.read_text(encoding="utf-8-sig")


def test_blind_sheet_has_no_tier_band_or_confidence(tmp_path, monkeypatch):
    monkeypatch.setattr(handcheck, "STEP8_SHEET", handcheck.STEP8_SHEET)
    monkeypatch.setattr(handcheck, "STEP8_KEY", handcheck.STEP8_KEY)
    sheet, key = run(tmp_path, "a")
    header = sheet.splitlines()[0].lower()
    assert not any(w in header for w in ("tier", "band", "confidence", "stratum", "matched_on", "canonical"))
    assert "label" in header and "tier" in key.splitlines()[0]  # they live in the key file only


def test_sampling_is_reproducible_with_the_same_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(handcheck, "STEP8_SHEET", handcheck.STEP8_SHEET)
    monkeypatch.setattr(handcheck, "STEP8_KEY", handcheck.STEP8_KEY)
    assert run(tmp_path, "x") == run(tmp_path, "y")
