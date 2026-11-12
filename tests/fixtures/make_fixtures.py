"""Regenerates the small committed fixtures in this folder. Tests never run this: they read the committed files.
Needs openpyxl (a project dependency) and xlwt (only for the old .xls; `pip install xlwt`).

    python tests/fixtures/make_fixtures.py
"""
import datetime
import gzip
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).parent

# multi-row header: 2 title rows, a two-row header (merged group cell over two columns), a footer
(HERE / "multirow_header.csv").write_text(
    "Licence register extract,,,\n"
    ",,,\n"
    "Licensee,,Licence,\n"
    "Name,ABN,Number,Class\n"
    "Acme Constructions Pty Ltd,51 824 753 556,L001,A\n"
    "Harbour Plumbing Pty Ltd,33 051 775 556,L002,B\n"
    "Smith Family Trust,,L003,A\n"
    "Delta Electrical Pty Ltd,53 004 085 616,L004,C\n"
    "Total,4,,\n"
    "Source: example register,,,\n")

import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Summary"
ws.append(["Licences by class"])
ws.append(["A", 2])
ws.append(["B", 1])
ws2 = wb.create_sheet("Licences")
ws2.append(["Licence No", "Business", "ABN", "Issued", "Postcode"])
for i, (n, a) in enumerate([("Acme Constructions Pty Ltd", "51824753556"), ("Harbour Plumbing Pty Ltd", "33051775556"),
                            ("Delta Electrical Pty Ltd", "53004085616"), ("Smith Family Trust", None),
                            ("Quay Cafe", None)], 1):
    ws2.append([f"L{i:03d}", n, a, datetime.datetime(2021, 3, i), 2000 + i])
wb.save(HERE / "two_sheets.xlsx")

import xlwt
book = xlwt.Workbook()
sh = book.add_sheet("Old")
for c, h in enumerate(["Licence No", "Business", "Issued", "Postcode"]):
    sh.write(0, c, h)
datestyle = xlwt.easyxf(num_format_str="DD/MM/YYYY")
for r, (n, d) in enumerate([("Acme Constructions Pty Ltd", datetime.date(2019, 5, 17)), ("Harbour Plumbing Pty Ltd", datetime.date(2020, 1, 2)),
                            ("Delta Electrical Pty Ltd", datetime.date(2022, 12, 31))], 1):
    sh.write(r, 0, f"L{r:03d}")
    sh.write(r, 1, n)
    sh.write(r, 2, d, datestyle)
    sh.write(r, 3, 3000 + r)
book.save(str(HERE / "old.xls"))

(HERE / "nested.json").write_text(json.dumps({
    "meta": {"generated": "2026-01-01", "count": 3},
    "data": {"items": [
        {"id": 1, "name": "Acme Constructions Pty Ltd", "address": {"state": "NSW", "postcode": "2000", "geo": {"lat": -33.8}}, "tags": ["a", "b"]},
        {"id": 2, "name": "Harbour Plumbing Pty Ltd", "address": {"state": "VIC", "postcode": "3000", "geo": {"lat": -37.8}}, "tags": []},
        {"id": 3, "name": "Quay Cafe", "address": {"state": "QLD"}}]}}, indent=1))

(HERE / "lines.ndjson").write_text("".join(json.dumps(r) + "\n" for r in [
    {"id": i, "name": n, "state": s} for i, (n, s) in enumerate(
        [("Acme Constructions Pty Ltd", "NSW"), ("Harbour Plumbing Pty Ltd", "VIC"), ("Delta Electrical Pty Ltd", "SA"),
         ("Quay Cafe", "QLD"), ("Smith Family Trust", "WA")], 1)]))

(HERE / "places.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
    {"type": "Feature", "properties": {"NAME": "Acme Constructions Pty Ltd", "STATE": "NSW"}, "geometry": {"type": "Point", "coordinates": [151.2, -33.8]}},
    {"type": "Feature", "properties": {"NAME": "Harbour Plumbing Pty Ltd", "STATE": "VIC"}, "geometry": {"type": "Point", "coordinates": [144.9, -37.8]}}]}))

with zipfile.ZipFile(HERE / "two_members.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("a.csv", "Name,ABN\nAcme Constructions Pty Ltd,51 824 753 556\nHarbour Plumbing Pty Ltd,33 051 775 556\n")
    z.writestr("b.csv", "Licence,Class\nL001,A\nL002,B\n")

# a CSV that is named .xlsx
(HERE / "wrong_ext.xlsx").write_text("Name,ABN\nAcme Constructions Pty Ltd,51 824 753 556\nHarbour Plumbing Pty Ltd,33 051 775 556\n")
(HERE / "empty.csv").write_bytes(b"")
(HERE / "latin1.csv").write_bytes("Name,Town\nCafé Müller Pty Ltd,Zürich\nZoë Plumbing Pty Ltd,Montréal\n".encode("latin-1"))

# zip bombs: 5 MB of zeros compress to a few KB. Tests lower the 1 GB cap so these trip it.
zeros = b"0" * (5 * 1024 * 1024)
with zipfile.ZipFile(HERE / "bomb.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("big.csv", b"a,b\n" + zeros)
(HERE / "bomb.csv.gz").write_bytes(gzip.compress(b"a,b\n" + zeros))
