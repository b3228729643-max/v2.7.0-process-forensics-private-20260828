#!/usr/bin/env python3
"""Candidate-only exact-match scan for every low-profile target glyph."""
import csv
from pathlib import Path
import fitz

OUT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
LOW = set(",.;:，。；：、…")

def rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)

targets = []
with (OUT / "after_pixel_measurements.csv").open(encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION":
            targets.append(r)
rows = []
doc = fitz.open(PDF)
for physical, page in enumerate(doc, start=1):
    if physical == 801:
        continue
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                size = float(span.get("size", 0))
                color = "/".join(map(str, rgb(span.get("color", 0))))
                for char in span["chars"]:
                    c = char["c"]
                    if c not in LOW:
                        continue
                    for target in targets:
                        eligible = (c == target["CHAR"] and font == target["PDF_FONT"] and abs(size - float(target["PDF_FONT_SIZE"])) <= 0.25 and color == target["PDF_COLOR_RGB"])
                        if eligible:
                            rows.append({
                                "TARGET_GLYPH_ID": target["GLYPH_ID"], "TARGET_CHAR": target["CHAR"],
                                "PHYSICAL_PAGE": physical, "FONT": font, "PDF_SIZE": f"{size:.6f}", "COLOR_RGB": color,
                                "BBOX_PT": ",".join(f"{x:.6f}" for x in char["bbox"]), "ELIGIBLE": True,
                            })
with (OUT / "low_profile_candidate_scan.csv").open("w", encoding="utf-8", newline="") as f:
    columns = ["TARGET_GLYPH_ID", "TARGET_CHAR", "PHYSICAL_PAGE", "FONT", "PDF_SIZE", "COLOR_RGB", "BBOX_PT", "ELIGIBLE"]
    w = csv.DictWriter(f, fieldnames=columns); w.writeheader(); w.writerows(rows)
print(f"targets={len(targets)} exact_candidates={len(rows)}")
for target in targets:
    count = sum(r["TARGET_GLYPH_ID"] == target["GLYPH_ID"] for r in rows)
    print(target["GLYPH_ID"], repr(target["CHAR"]), count)
