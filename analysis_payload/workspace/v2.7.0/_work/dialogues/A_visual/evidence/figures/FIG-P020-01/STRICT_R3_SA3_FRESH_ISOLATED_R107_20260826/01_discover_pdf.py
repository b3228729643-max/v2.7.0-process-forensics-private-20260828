from __future__ import annotations

import json
import sys
from pathlib import Path

import pdfplumber


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R3_SA3_FRESH_ISOLATED_R107_20260826")
PAGE_NUMBER = 17
CAPTION_NEEDLE = "数学语言从对象声明到任务陈述的依赖关系"

sys.stdout.reconfigure(encoding="utf-8")


with pdfplumber.open(PDF) as doc:
    page = doc.pages[PAGE_NUMBER - 1]
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    hits = [word for word in words if CAPTION_NEEDLE[:6] in word["text"]]
    payload = {
        "pdf": str(PDF),
        "physical_page": PAGE_NUMBER,
        "page_width_pt": page.width,
        "page_height_pt": page.height,
        "rotation": page.rotation,
        "caption_needle": CAPTION_NEEDLE,
        "caption_word_hits": hits,
        "words": words,
        "object_counts": {name: len(items) for name, items in page.objects.items()},
        "objects": page.objects,
    }

(ROOT / "discovery_page17.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)

print(json.dumps({k: payload[k] for k in payload if k not in {"words", "objects"}}, ensure_ascii=False, indent=2))
for word in words:
    if 250 <= word["top"] <= 500:
        print(
            f"WORD top={word['top']:.3f} bottom={word['bottom']:.3f} "
            f"x0={word['x0']:.3f} x1={word['x1']:.3f} text={word['text']}"
        )
