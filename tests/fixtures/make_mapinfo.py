"""Regenerates mapinfo.zip: a zip of a MapInfo TAB geodataset (a text header plus binary sidecars), the shape of file that is not
tabular. Fixed timestamps, so regenerating gives identical bytes.   python tests/fixtures/make_mapinfo.py"""
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
TAB = (b'!table\n!version 300\n!charset WindowsLatin1\n\nDefinition Table\n  Type NATIVE Charset "WindowsLatin1"\n  Fields 3\n'
       b'    Name Char (254) ;\n    Area Char (254) ;\n    Contract Char (254) ;\n')
DAT = bytes([0x03, 0x00, 0x00, 0x00, 0x1A, 0x80, 0x01, 0xFF]) + bytes(range(8, 200))
ID = bytes(range(0, 64)) * 2
MAP = bytes([0xC4, 0x00, 0x01, 0x02, 0x00, 0x00, 0xFE]) + bytes(range(0, 255)) * 2
with zipfile.ZipFile(HERE / "mapinfo.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in (("sites.tab", TAB), ("sites.dat", DAT), ("sites.id", ID), ("sites.map", MAP)):
        z.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data)
