#!/usr/bin/env python3
"""Scan only the locked candidate for independent matched CJK-colon glyphs."""
import csv
from pathlib import Path
import fitz

OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
TARGET_FONT = "NotoSerifSC-ExtraLight"
TARGET_SIZE = 9.564140
TARGET_COLOR = (31, 35, 40)

def rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)

rows = []
doc = fitz.open(PDF)
for page_no, page in enumerate(doc, start=1):
    if page_no == 801:
        continue
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span["chars"]:
                    if char["c"] != "：":
                        continue
                    row = {
                        "PHYSICAL_PAGE": page_no,
                        "FONT": span.get("font", ""),
                        "PDF_SIZE": f"{float(span.get('size', 0)):.6f}",
                        "COLOR_RGB": "/".join(map(str, rgb(span.get("color", 0)))),
                        "BBOX_PT": ",".join(f"{x:.6f}" for x in char["bbox"]),
                    }
                    row["FONT_MATCH"] = row["FONT"] == TARGET_FONT
                    row["SIZE_MATCH_025PT"] = abs(float(span.get("size", 0)) - TARGET_SIZE) <= 0.25
                    row["COLOR_MATCH"] = rgb(span.get("color", 0)) == TARGET_COLOR
                    row["ELIGIBLE"] = row["FONT_MATCH"] and row["SIZE_MATCH_025PT"] and row["COLOR_MATCH"]
                    rows.append(row)
with (OUT / "punctuation_candidate_scan.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["PHYSICAL_PAGE", "FONT", "PDF_SIZE", "COLOR_RGB", "BBOX_PT", "FONT_MATCH", "SIZE_MATCH_025PT", "COLOR_MATCH", "ELIGIBLE"])
    w.writeheader(); w.writerows(rows)
print(f"total={len(rows)} eligible={sum(bool(r['ELIGIBLE']) for r in rows)}")
for r in rows:
    if r["ELIGIBLE"]:
        print(r)
