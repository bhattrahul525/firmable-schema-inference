from src.engine.row_filter import filter_rows

KW = {"column": "BN_STATUS", "equals": "Registered"}
ABN = "51824753556"  # checksum-valid
ROWS = [
    {"BN_STATUS": "Registered", "BN_ABN": ABN, "BN_NAME": "Zzz"},               # ABN match
    {"BN_STATUS": "Registered", "BN_ABN": "", "BN_NAME": "ACME Trading Pty Ltd"},  # name-key match
    {"BN_STATUS": "Registered", "BN_ABN": "51824753557", "BN_NAME": "Other"},      # bad checksum, no name hit
    {"BN_STATUS": "Cancelled", "BN_ABN": ABN, "BN_NAME": "ACME Trading"},        # would match but not Registered
]


def run():
    return [(r["BN_NAME"], how) for r, how in filter_rows(ROWS, KW, "BN_ABN", "BN_NAME", {ABN}, {"acme trading"})]


def test_abn_and_name_key_kept_nonmatch_dropped():
    assert run() == [("Zzz", "abn"), ("ACME Trading Pty Ltd", "name")]


def test_keep_where_drops_non_registered():
    assert "Cancelled" not in [r["BN_STATUS"] for r, _ in filter_rows(ROWS, KW, "BN_ABN", "BN_NAME", {ABN}, {"acme trading"})]
