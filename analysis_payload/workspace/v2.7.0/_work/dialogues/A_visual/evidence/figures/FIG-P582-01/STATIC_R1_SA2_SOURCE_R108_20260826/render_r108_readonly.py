from __future__ import annotations

import json
from pathlib import Path

import fitz
from PIL import Image

PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STATIC_R1_SA2_SOURCE_R108_20260826")
PAGE_INDEX = 631


def render(page: fitz.Page, clip: fitz.Rect, dpi: int, name: str) -> Path:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), clip=clip, alpha=False)
    output = ROOT / name
    pix.save(output)
    return output


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rect = page.rect

full = render(page, page_rect, 200, "full_page_200dpi.png")
figure_clip = fitz.Rect(150, 320, 450, 515)
standalone_clip = fitz.Rect(150, 320, 450, 483)
figure = render(page, figure_clip, 300, "figure_crop_300dpi.png")
standalone = render(page, standalone_clip, 300, "standalone_300dpi.png")

with Image.open(figure) as image:
    image.convert("L").save(ROOT / "figure_grayscale_300dpi.png")

roi_specs = {
    "first_value_arrow": fitz.Rect(225, 328, 276, 360),
    "third_value_arrow": fitz.Rect(358, 356, 416, 387),
    "all_values_arrows": fitz.Rect(220, 326, 437, 419),
}
roi_records = []
for stem, clip in roi_specs.items():
    native = render(page, clip, 300, f"{stem}_native1x.png")
    with Image.open(native) as image:
        enlarged = image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)
        enlarged.save(ROOT / f"{stem}_8x_nearest.png")
        roi_records.append(
            {
                "name": stem,
                "clip_points": [clip.x0, clip.y0, clip.x1, clip.y1],
                "native_pixels": [image.width, image.height],
            }
        )

targets = {".640", ".325", ".380", "↓", "↑", "下降", "上升", "再下降"}
spans = []
for block in page.get_text("dict")["blocks"]:
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span["text"].strip()
            if text in targets:
                spans.append(
                    {
                        "text": text,
                        "bbox_points": span["bbox"],
                        "size_pt": span["size"],
                        "font": span["font"],
                    }
                )

result = {
    "pdf": str(PDF),
    "page_index_zero_based": PAGE_INDEX,
    "physical_page": PAGE_INDEX + 1,
    "page_points": [page_rect.width, page_rect.height],
    "figure_clip_points": list(figure_clip),
    "standalone_clip_points": list(standalone_clip),
    "renders": {
        "full_page_200dpi": full.name,
        "figure_crop_300dpi": figure.name,
        "standalone_300dpi": standalone.name,
        "figure_grayscale_300dpi": "figure_grayscale_300dpi.png",
    },
    "roi_records": roi_records,
    "target_spans": spans,
}
(ROOT / "r108_native_locator.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"physical_page": PAGE_INDEX + 1, "target_spans": len(spans), "roi_count": len(roi_records)}))
