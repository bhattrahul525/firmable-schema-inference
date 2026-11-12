"""Tests for the parametric readers (src/engine/readers.py) on small committed fixtures (tests/fixtures/). No network, no key."""

import datetime
import io
import unittest
from pathlib import Path
from unittest import mock

from src.engine import readers
from src.engine.readers import ReaderError, iter_table, read_rows, row_fingerprint

FIX = Path(__file__).parent / "fixtures"


def rows_of(reader, name):
    return read_rows(reader, FIX / name)


class TestDelimited(unittest.TestCase):
    def test_multi_row_header_merged_with_skip_and_footer(self):
        headers, rows = rows_of({"format": "csv", "skip_rows": 2, "header_rows": 2, "skip_footer_rows": 2}, "multirow_header.csv")
        # "Licensee" sits over two columns: the merged cell is blank after the first, so the upper row is filled rightwards
        self.assertEqual(headers, ["Licensee Name", "Licensee ABN", "Licence Number", "Licence Class"])
        self.assertEqual(len(rows), 4)                                         # "Total" and "Source" footer rows dropped
        self.assertEqual(rows[0]["Licensee Name"], "Acme Constructions Pty Ltd")
        self.assertEqual(rows[3]["Licence Class"], "C")

    def test_without_the_footer_option_the_footer_is_data(self):
        _, rows = rows_of({"format": "csv", "skip_rows": 2, "header_rows": 2}, "multirow_header.csv")
        self.assertEqual(len(rows), 6)

    def test_no_header_gets_generated_names(self):
        headers, rows = rows_of({"format": "csv", "header_rows": 0}, "latin1.csv")
        self.assertEqual(headers, ["col_1", "col_2"])
        self.assertEqual(len(rows), 3)                                          # the header line is data now

    def test_round_one_header_row_option_still_works(self):
        a = rows_of({"format": "csv", "header_row": 4}, "multirow_header.csv")
        b = rows_of({"format": "csv", "skip_rows": 3, "header_rows": 1}, "multirow_header.csv")
        self.assertEqual(a, b)
        self.assertEqual(a[0], ["Name", "ABN", "Number", "Class"])

    def test_skip_rows_beyond_the_file_is_a_reader_error(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv", "skip_rows": 99}, "multirow_header.csv")

    def test_latin1_file_needs_the_right_encoding(self):
        _, good = rows_of({"format": "csv", "encoding": "latin-1"}, "latin1.csv")
        self.assertEqual(good[0]["Name"], "Café Müller Pty Ltd")
        _, bad = rows_of({"format": "csv"}, "latin1.csv")                      # default utf-8: undecodable bytes become U+FFFD
        self.assertIn("�", bad[0]["Name"])

    def test_unknown_encoding_and_bad_delimiter_are_reader_errors(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv", "encoding": "no-such-codec"}, "latin1.csv")
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv", "delimiter": ";;"}, "latin1.csv")

    def test_empty_file_is_a_reader_error_not_a_crash(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv"}, "empty.csv")

    def test_file_with_a_wrong_extension_reads_by_content(self):
        _, rows = rows_of({"format": "csv"}, "wrong_ext.xlsx")                   # a CSV named .xlsx
        self.assertEqual(len(rows), 2)
        with self.assertRaises(ReaderError):                                    # read as the xlsx its name claims: a clean error
            rows_of({"format": "xlsx"}, "wrong_ext.xlsx")

    def test_drop_empty_columns_drops_blank_header_columns_that_are_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.csv"
            p.write_text("Name,,ABN,\nAcme,,1,\nBeta,,2,x\n")        # column 2 is blank and empty; column 4 is blank but filled
            keep = read_rows({"format": "csv"}, p)[0]
            drop = read_rows({"format": "csv", "drop_empty_columns": True}, p)[0]
        self.assertEqual(keep, ["Name", "_blank_1", "ABN", "_blank_3"])
        self.assertEqual(drop, ["Name", "ABN", "_blank_3"])              # a blank-header column WITH data is never dropped


class TestWorkbooks(unittest.TestCase):
    def test_xlsx_sheets_and_dimensions(self):
        sheets = readers.workbook_sheets({"format": "xlsx"}, FIX / "two_sheets.xlsx")
        self.assertEqual([s["name"] for s in sheets], ["Summary", "Licences"])
        self.assertEqual(sheets[1]["rows"], 6)
        self.assertEqual(sheets[1]["cols"], 5)

    def test_xlsx_default_is_first_sheet_and_named_sheet_works(self):
        h, rows = rows_of({"format": "xlsx"}, "two_sheets.xlsx")
        self.assertEqual(h, ["Licences by class", "_blank_1"])
        h, rows = rows_of({"format": "xlsx", "sheet": "Licences"}, "two_sheets.xlsx")
        self.assertEqual(h, ["Licence No", "Business", "ABN", "Issued", "Postcode"])
        self.assertEqual(len(rows), 5)
        self.assertIsInstance(rows[0]["Issued"], datetime.datetime)

    def test_missing_sheet_error_lists_the_sheets(self):
        with self.assertRaises(ReaderError) as cm:
            rows_of({"format": "xlsx", "sheet": "Nope"}, "two_sheets.xlsx")
        self.assertIn("Licences", str(cm.exception))

    def test_old_xls_reads_and_converts_dates(self):
        sheets = readers.workbook_sheets({"format": "xls"}, FIX / "old.xls")
        self.assertEqual(sheets[0]["name"], "Old")
        h, rows = rows_of({"format": "xls"}, "old.xls")
        self.assertEqual(h, ["Licence No", "Business", "Issued", "Postcode"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["Issued"], datetime.datetime(2019, 5, 17))     # a real datetime, like openpyxl gives
        self.assertEqual(rows[0]["Postcode"], 3001.0)                            # xls numbers are floats; the transforms cope

    def test_xls_that_is_not_xls_is_a_reader_error(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "xls"}, "latin1.csv")


class TestJson(unittest.TestCase):
    def test_nested_records_path_and_flatten_depth(self):
        h, rows = rows_of({"format": "json", "records_path": "data.items"}, "nested.json")
        self.assertIn("address.state", h)
        self.assertIn("address.geo", h)                                          # depth 1: the deeper object is kept whole
        self.assertEqual(rows[0]["address.geo"], {"lat": -33.8})
        h2, rows2 = rows_of({"format": "json", "records_path": "data.items", "flatten_depth": 2}, "nested.json")
        self.assertIn("address.geo.lat", h2)
        h0, _ = rows_of({"format": "json", "records_path": "data.items", "flatten_depth": 0}, "nested.json")
        self.assertIn("address", h0)

    def test_bad_records_path_error_lists_keys(self):
        with self.assertRaises(ReaderError) as cm:
            rows_of({"format": "json", "records_path": "data.nope"}, "nested.json")
        self.assertIn("items", str(cm.exception))
        with self.assertRaises(ReaderError) as cm:
            rows_of({"format": "json"}, "nested.json")                           # top level is an object, not a list
        self.assertIn("records_path", str(cm.exception))

    def test_ndjson(self):
        h, rows = rows_of({"format": "json", "ndjson": True}, "lines.ndjson")
        self.assertEqual(h, ["id", "name", "state"])
        self.assertEqual(len(rows), 5)
        with self.assertRaises(ReaderError):
            rows_of({"format": "json"}, "lines.ndjson")                          # NDJSON read as one JSON document

    def test_geojson_features(self):
        h, rows = rows_of({"format": "json", "records_path": "features"}, "places.geojson")
        self.assertIn("properties.NAME", h)
        self.assertEqual(rows[1]["properties.STATE"], "VIC")


class TestArchives(unittest.TestCase):
    def test_zip_with_two_members_needs_a_member(self):
        with self.assertRaises(ReaderError) as cm:
            rows_of({"format": "csv", "archive": "zip"}, "two_members.zip")
        self.assertIn("a.csv", str(cm.exception))
        h, rows = rows_of({"format": "csv", "archive": "zip", "member": "b.csv"}, "two_members.zip")
        self.assertEqual(h, ["Licence", "Class"])
        self.assertEqual(len(rows), 2)
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv", "archive": "zip", "member": "../etc/passwd"}, "two_members.zip")

    def test_not_a_zip_is_a_clean_error(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "csv", "archive": "zip"}, "latin1.csv")

    def test_the_decompression_cap_is_one_gigabyte(self):
        self.assertEqual(readers.MAX_DECOMPRESSED_BYTES, 1 << 30)

    def test_zip_bomb_is_refused_by_its_declared_size(self):
        with mock.patch.object(readers, "MAX_DECOMPRESSED_BYTES", 1024 * 1024):
            with self.assertRaises(ReaderError) as cm:
                rows_of({"format": "csv", "archive": "zip", "member": "big.csv"}, "bomb.zip")
        self.assertIn("declares", str(cm.exception))                              # stopped by the header, before any decompression

    def test_zip_bomb_whose_header_lies_is_stopped_by_counting(self):
        """The header may claim any size: the stream counts the bytes it really decompresses."""
        raw = io.BytesIO(b"x" * 5000)
        capped = io.BufferedReader(readers._CappedRaw(raw, 1000))
        with self.assertRaises(ReaderError):
            capped.read()

    def test_gz_bomb_has_no_declared_size_so_only_counting_can_stop_it(self):
        with mock.patch.object(readers, "MAX_DECOMPRESSED_BYTES", 1024 * 1024):
            with self.assertRaises(ReaderError) as cm:
                rows_of({"format": "csv", "archive": "gz"}, "bomb.csv.gz")
        self.assertIn("cap", str(cm.exception))

    def test_a_workbook_inside_an_archive_is_loaded_whole_and_has_its_own_cap(self):
        import tempfile, zipfile
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "wb.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.write(FIX / "two_sheets.xlsx", "book.xlsx")
            h, rows = read_rows({"format": "xlsx", "archive": "zip", "member": "book.xlsx", "sheet": "Licences"}, z)
            self.assertEqual(len(rows), 5)
            with mock.patch.object(readers, "MAX_WORKBOOK_BYTES", 1000):
                with self.assertRaises(ReaderError) as cm:
                    read_rows({"format": "xlsx", "archive": "zip", "member": "book.xlsx"}, z)
            self.assertIn("loaded whole", str(cm.exception))

    def test_a_normal_member_still_reads_under_the_cap(self):
        with mock.patch.object(readers, "MAX_DECOMPRESSED_BYTES", 1024 * 1024):
            _, rows = rows_of({"format": "csv", "archive": "zip", "member": "a.csv"}, "two_members.zip")
        self.assertEqual(len(rows), 2)


class TestStreamingAndFingerprints(unittest.TestCase):
    def test_rows_are_produced_lazily(self):
        with iter_table({"format": "csv"}, FIX / "latin1.csv") as (_, rows):
            first = next(rows)
            self.assertEqual(len(first), 2)                                      # (fingerprint, row), one at a time
            self.assertTrue(hasattr(rows, "__next__"))

    def test_fingerprint_ignores_header_options_and_trailing_blanks(self):
        a = {fp for fp, _ in self._fps({"format": "csv", "skip_rows": 2, "header_rows": 2})}
        b = {fp for fp, _ in self._fps({"format": "csv", "skip_rows": 3, "header_rows": 1})}
        self.assertEqual(a & b, b & a)
        self.assertTrue(len(a & b) >= 4)
        self.assertEqual(row_fingerprint(["x", "y", None, ""]), row_fingerprint(["x", "y"]))
        self.assertNotEqual(row_fingerprint(["x", "y"]), row_fingerprint(["x", "z"]))

    def _fps(self, reader):
        with iter_table(reader, FIX / "multirow_header.csv") as (_, rows):
            return list(rows)

    def test_the_cooperative_check_is_called_while_reading(self):
        calls = []
        with mock.patch.object(readers, "CHECK_EVERY_ROWS", 1):
            with iter_table({"format": "json", "ndjson": True}, FIX / "lines.ndjson", check=lambda: calls.append(1)) as (_, rows):
                list(rows)
        self.assertGreaterEqual(len(calls), 5)

    def test_unsupported_format_is_a_reader_error(self):
        with self.assertRaises(ReaderError):
            rows_of({"format": "parquet"}, "latin1.csv")


if __name__ == "__main__":
    unittest.main()
