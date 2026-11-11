"""Run with: python -m unittest discover tests"""

import unittest

from src.common.ids import (
    find_abns,
    is_valid_abn,
    is_valid_acn,
    normalise_abn,
    normalise_acn,
)


class TestABN(unittest.TestCase):
    def test_known_valid(self):
        # 51 824 753 556 is the ABR's published example ABN.
        for abn in ["51824753556", "33051775556", "49004028077"]:
            self.assertTrue(is_valid_abn(abn), abn)

    def test_invalid(self):
        for abn in ["51824753557", "12345678901", "5182475355", "abcdefghijk", ""]:
            self.assertFalse(is_valid_abn(abn), abn)

    def test_normalise_formats(self):
        self.assertEqual(normalise_abn("51 824 753 556"), "51824753556")
        self.assertEqual(normalise_abn("51-824-753-556"), "51824753556")
        self.assertEqual(normalise_abn(51824753556), "51824753556")
        self.assertEqual(normalise_abn(51824753556.0), "51824753556")  # Excel float
        self.assertIsNone(normalise_abn("0412 345 678"))  # phone number
        self.assertIsNone(normalise_abn(None))
        self.assertIsNone(normalise_abn(float("nan")))

    def test_find_in_text(self):
        text = "Supplier ABN 51 824 753 556; ph 0298765432; invoice 12345678901"
        self.assertEqual(find_abns(text), ["51824753556"])


class TestACN(unittest.TestCase):
    def test_known_valid(self):
        # Examples from ASIC's published ACN check-digit list.
        for acn in ["000000019", "000250000", "005499981", "010749961", "004085616"]:
            self.assertTrue(is_valid_acn(acn), acn)

    def test_invalid(self):
        for acn in ["000000018", "12345678", "1234567890", ""]:
            self.assertFalse(is_valid_acn(acn), acn)

    def test_leading_zeros_restored(self):
        self.assertEqual(normalise_acn(19), "000000019")
        self.assertEqual(normalise_acn("004 085 616"), "004085616")


if __name__ == "__main__":
    unittest.main()
