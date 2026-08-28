from __future__ import annotations

import fitz

PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf"
PAGE_INDEX = 681

doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
raw = page.get_text("rawdict")
for block_no, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for line_no, line in enumerate(block["lines"]):
        text = "".join(ch["c"] for span in line["spans"] for ch in span["chars"])
        if text.strip():
            print(
                f"block={block_no:02d} line={line_no:02d} "
                f"bbox={tuple(round(v, 2) for v in line['bbox'])} text={text}"
            )
