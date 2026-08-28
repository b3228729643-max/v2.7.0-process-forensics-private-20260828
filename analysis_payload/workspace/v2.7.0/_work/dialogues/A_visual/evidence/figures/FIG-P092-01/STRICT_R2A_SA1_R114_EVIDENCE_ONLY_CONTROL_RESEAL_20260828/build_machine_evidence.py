from __future__ import annotations

import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r114_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第01册_数学基础与统计学习基本理论\V1-C06\fig_v1_c06_binary_entropy.tex"
)
PAGE = ROOT / "P092_page096_native300dpi.png"
DENOMINATOR = ROOT / "object_denominator_frozen.csv"
SCALE = 300.0 / 72.0
CROP_BOX = (450, 650, 2040, 1525)
CRITICAL_BOX = (700, 700, 1960, 1240)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


with DENOMINATOR.open(newline="", encoding="utf-8-sig") as stream:
    objects = list(csv.DictReader(stream))
if len(objects) != 21:
    raise RuntimeError(f"frozen denominator must contain 21 objects, got {len(objects)}")

pair_path = ROOT / "unordered_pairs_frozen.csv"
with pair_path.open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.writer(stream)
    writer.writerow(["pair_id", "object_a", "object_b"])
    for index, (a, b) in enumerate(combinations(objects, 2), start=1):
        writer.writerow([f"P{index:03d}", a["object_id"], b["object_id"]])
if sum(1 for _ in pair_path.open(encoding="utf-8-sig")) - 1 != 210:
    raise RuntimeError("unordered-pair freeze is incomplete")

page = Image.open(PAGE).convert("RGB")
if page.size != (2481, 3508):
    raise RuntimeError(f"unexpected native 300 dpi page size: {page.size}")

crop = page.crop(CROP_BOX)
crop.save(ROOT / "P092_figure_crop_native300dpi.png")
crop.convert("L").save(ROOT / "P092_figure_grayscale_native300dpi.png")

overlay = crop.copy()
draw = ImageDraw.Draw(overlay)
try:
    font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()

machine_rows = []
for obj in objects:
    x0 = round(float(obj["pdf_x0_pt"]) * SCALE) - CROP_BOX[0]
    y0 = round(float(obj["pdf_y0_pt"]) * SCALE) - CROP_BOX[1]
    x1 = round(float(obj["pdf_x1_pt"]) * SCALE) - CROP_BOX[0]
    y1 = round(float(obj["pdf_y1_pt"]) * SCALE) - CROP_BOX[1]
    color = (220, 20, 60) if obj["class"] == "TEXT" else (0, 150, 70)
    draw.rectangle((x0, y0, x1, y1), outline=color, width=3)
    label_y = max(0, y0 - 20)
    draw.rectangle((x0, label_y, x0 + 48, label_y + 20), fill=(255, 255, 255))
    draw.text((x0 + 2, label_y), obj["object_id"], fill=color, font=font)
    machine_rows.append(
        {
            "object_id": obj["object_id"],
            "crop_x0_px": x0,
            "crop_y0_px": y0,
            "crop_x1_px": x1,
            "crop_y1_px": y1,
            "bbox_width_px": x1 - x0 + 1,
            "bbox_height_px": y1 - y0 + 1,
        }
    )
overlay.save(ROOT / "P092_object_overlay_native300dpi.png")

with (ROOT / "machine_object_geometry.csv").open(
    "w", newline="", encoding="utf-8-sig"
) as stream:
    writer = csv.DictWriter(stream, fieldnames=list(machine_rows[0]))
    writer.writeheader()
    writer.writerows(machine_rows)

critical = page.crop(CRITICAL_BOX)
critical.save(ROOT / "P092_critical_native1x.png")
critical.resize(
    (critical.width * 8, critical.height * 8), resample=Image.Resampling.NEAREST
).save(ROOT / "P092_critical_nearest8x.png")

provenance = {
    "handoff_id": "A-R114-P092-SA1-FRESH-ISOLATED-20260828",
    "canonical_instance": "/root/p092_r114_fresh_sa1",
    "uid": "FIG-P092-01",
    "pdf_physical_page": 96,
    "pdf_sha256": sha256(PDF),
    "source_sha256": sha256(SOURCE),
    "native_page_png_size_px": list(page.size),
    "native_render_dpi": 300,
    "figure_crop_box_on_native_page_px": list(CROP_BOX),
    "critical_roi_box_on_native_page_px": list(CRITICAL_BOX),
    "denominator_file": DENOMINATOR.name,
    "pair_file": pair_path.name,
    "denominator_count": len(objects),
    "unordered_pair_count": 210,
    "manual_review_fields_generated_by_script": False,
}
(ROOT / "machine_provenance.json").write_text(
    json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print(json.dumps(provenance, ensure_ascii=False))
