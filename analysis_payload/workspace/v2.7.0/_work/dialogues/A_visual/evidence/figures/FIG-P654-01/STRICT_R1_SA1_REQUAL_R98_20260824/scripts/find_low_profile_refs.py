from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R1_SA1_REQUAL_R98_20260824\inventory\low_profile_reference_candidates.csv")
TARGET_PHYSICAL_PAGE = 702

TARGETS = {
    ",": {
        "codepoint": "U+002C",
        "font": "STIXTwoMath-Regular",
        "trace_size_bp": 11.75592,
        "color": (31, 35, 40),
    },
    "、": {
        "codepoint": "U+3001",
        "font": "NotoSerifSC-ExtraLight",
        "trace_size_bp": 9.56414,
        "color": (31, 35, 40),
    },
}


def rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


rows: list[dict[str, object]] = []
doc = fitz.open(PDF)
for page_index, page in enumerate(doc):
    physical = page_index + 1
    if physical == TARGET_PHYSICAL_PAGE:
        continue
    raw = page.get_text("rawdict")
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line.get("spans", [])):
                text = "".join(ch.get("c", "") for ch in span.get("chars", []))
                for char_index, ch in enumerate(span.get("chars", [])):
                    value = ch.get("c", "")
                    if value not in TARGETS:
                        continue
                    target = TARGETS[value]
                    same_font = span.get("font") == target["font"]
                    same_size = abs(float(span.get("size", 0)) - float(target["trace_size_bp"])) <= 0.0001
                    same_color = rgb(int(span.get("color", 0))) == target["color"]
                    if not (same_font and same_size and same_color):
                        continue
                    rows.append({
                        "candidate_id": f"R{len(rows)+1:05d}",
                        "char": value,
                        "codepoint": target["codepoint"],
                        "physical_page": physical,
                        "printed_label": page.get_label(),
                        "block_index": block_index,
                        "line_index": line_index,
                        "span_index": span_index,
                        "char_index": char_index,
                        "font": span.get("font"),
                        "trace_size_bp": f"{float(span.get('size', 0)):.8f}",
                        "color_rgb": json.dumps(rgb(int(span.get("color", 0)))),
                        "char_bbox_pt": json.dumps(ch.get("bbox")),
                        "span_bbox_pt": json.dumps(span.get("bbox")),
                        "span_text": text,
                        "line_dir": json.dumps(line.get("dir")),
                    })

fields = [
    "candidate_id", "char", "codepoint", "physical_page", "printed_label",
    "block_index", "line_index", "span_index", "char_index", "font",
    "trace_size_bp", "color_rgb", "char_bbox_pt", "span_bbox_pt", "span_text", "line_dir",
]
with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(json.dumps({
    "candidate_count": len(rows),
    "comma": sum(row["char"] == "," for row in rows),
    "ideographic_comma": sum(row["char"] == "、" for row in rows),
    "target_page_excluded": TARGET_PHYSICAL_PAGE,
}, ensure_ascii=False))
