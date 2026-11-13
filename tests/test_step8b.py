from src.part3_resolve import handcheck


def test_join_and_precision(tmp_path, monkeypatch):
    sheet, key = tmp_path / "sheet.csv", tmp_path / "key.csv"
    sheet.write_text("check_id,label,notes\n1,Y,\n2,n,\n3,U,\n4,,\n5,maybe,\n")
    key.write_text("".join(["check_id,pair_id,stratum,tier,band,link_confidence\n"] +
                           [f"{i},p{i},s,t,loose,0.65\n" for i in range(1, 6)]))
    monkeypatch.setattr(handcheck, "STEP8_SHEET", sheet)
    monkeypatch.setattr(handcheck, "STEP8_KEY", key)
    rows, bad = handcheck.step8_join()
    assert bad == ["4", "5"] and [r["label"] for r in rows] == ["Y", "N", "U"]
    (t,) = handcheck.step8_table(rows, "stratum")
    assert (t["Y"], t["N"], t["U"], t["precision"]) == (1, 1, 1, 0.5)  # U excluded from precision
