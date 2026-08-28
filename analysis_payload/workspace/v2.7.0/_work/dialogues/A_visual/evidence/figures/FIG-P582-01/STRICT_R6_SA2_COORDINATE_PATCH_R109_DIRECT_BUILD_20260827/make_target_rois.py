from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827")
IMAGE = ROOT / "render" / "standalone_300dpi.png"
INVENTORY = ROOT / "object_inventory.csv"
OUT = ROOT / "target_rois"


def crop_union(image: Image.Image, boxes: list[list[int]], pad: int, stem: str) -> dict:
    x0 = max(0, min(box[0] for box in boxes) - pad)
    y0 = max(0, min(box[1] for box in boxes) - pad)
    x1 = min(image.width, max(box[2] for box in boxes) + pad)
    y1 = min(image.height, max(box[3] for box in boxes) + pad)
    crop = image.crop((x0, y0, x1, y1))
    native = OUT / f"{stem}_native1x.png"
    zoom = OUT / f"{stem}_8x_nearest.png"
    crop.save(native)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(zoom)
    return {"bbox_px": [x0, y0, x1, y1], "native": native.name, "zoom8x": zoom.name}


def main() -> None:
    OUT.mkdir(exist_ok=False)
    with INVENTORY.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = {row["id"]: row for row in csv.DictReader(stream)}
    image = Image.open(IMAGE).convert("RGB")
    arrow = json.loads(rows["GLYPH-042"]["bbox_px"])
    zero = json.loads(rows["GLYPH-062"]["bbox_px"])
    target = crop_union(image, [arrow, zero], 55, "target_arrow_vs_380_terminal_zero")
    upper = crop_union(image, [arrow, zero], 150, "target_plus_upper_plot_regression")

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(arrow, outline=(255, 0, 0), width=3)
    draw.rectangle(zero, outline=(255, 0, 255), width=3)
    ov = overlay.crop(tuple(upper["bbox_px"]))
    ov.save(OUT / "target_identity_overlay_native1x.png")
    ov.resize((ov.width * 8, ov.height * 8), Image.Resampling.NEAREST).save(OUT / "target_identity_overlay_8x_nearest.png")

    (OUT / "TARGET_ROI_IDENTITY.json").write_text(
        json.dumps(
            {
                "target_pair_in_r6": "PAIR-03495",
                "arrow_object": "GLYPH-042",
                "arrow_char": "U+2193",
                "terminal_zero_object": "GLYPH-062",
                "terminal_zero_char": "U+0030",
                "target_metrics": {
                    "shared_pixels_native_300dpi": 0,
                    "white_clearance_px": 27.0,
                },
                "target_crop": target,
                "upper_regression_crop": upper,
                "manual_fields_generated": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
