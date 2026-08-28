from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")
REGISTRY = ROOT / "visible_object_registry.csv"
NATIVE = ROOT / "figure_crop_native_300dpi.png"
CROP_X0_PT = 115.0
CROP_Y0_PT = 145.0
PX_PER_PT = 300.0 / 72.0


def pt_to_px(x: float, y: float) -> tuple[int, int]:
    return (
        round((x - CROP_X0_PT) * PX_PER_PT),
        round((y - CROP_Y0_PT) * PX_PER_PT),
    )


def pad_degenerate(x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int, int]:
    if x0 == x1:
        x0 -= 2
        x1 += 2
    if y0 == y1:
        y0 -= 2
        y1 += 2
    return x0, y0, x1, y1


def make_roi(image: Image.Image, name: str, rect_pt: tuple[float, float, float, float]) -> None:
    left, top = pt_to_px(rect_pt[0], rect_pt[1])
    right, bottom = pt_to_px(rect_pt[2], rect_pt[3])
    roi = image.crop((left, top, right, bottom))
    roi.save(ROOT / f"critical_{name}_native1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / f"critical_{name}_nearest8x.png"
    )


def main() -> None:
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as stream:
        objects = list(csv.DictReader(stream))
    object_ids = [row["OBJECT_ID"] for row in objects]
    if len(objects) != 21 or len(set(object_ids)) != 21:
        raise RuntimeError("visible object registry is not the frozen 21-object denominator")

    with (ROOT / "machine_unordered_pair_universe.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["PAIR_ID", "OBJECT_A_ID", "OBJECT_B_ID"])
        for index, (a_id, b_id) in enumerate(combinations(object_ids, 2), start=1):
            writer.writerow([f"P{index:03d}", a_id, b_id])

    image = Image.open(NATIVE).convert("RGB")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for row in objects:
        x0, y0 = pt_to_px(float(row["BBOX_X0_PT"]), float(row["BBOX_Y0_PT"]))
        x1, y1 = pt_to_px(float(row["BBOX_X1_PT"]), float(row["BBOX_Y1_PT"]))
        x0, y0, x1, y1 = pad_degenerate(x0, y0, x1, y1)
        color = (220, 35, 35) if row["OBJECT_CLASS"] == "TEXT" else (0, 150, 210)
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        label = row["OBJECT_ID"]
        label_box = draw.textbbox((x0, y0), label, font=font, stroke_width=0)
        width = label_box[2] - label_box[0] + 4
        height = label_box[3] - label_box[1] + 4
        label_y = max(0, y0 - height)
        draw.rectangle((x0, label_y, x0 + width, label_y + height), fill=(255, 250, 160))
        draw.text((x0 + 2, label_y + 1), label, fill=(0, 0, 0), font=font)
    overlay.save(ROOT / "text_and_graphics_measurement_overlay_300dpi.png")

    make_roi(image, "peak_label_marker_guides", (265.0, 168.0, 375.0, 201.0))
    make_roi(image, "left_endpoint_label_curve", (165.0, 264.0, 220.0, 300.0))
    make_roi(image, "right_endpoint_label_curve", (418.0, 264.0, 474.0, 300.0))

    pair_count = len(objects) * (len(objects) - 1) // 2
    if pair_count != 210:
        raise RuntimeError(f"unexpected pair count: {pair_count}")
    print(f"objects={len(objects)} pairs={pair_count} overlay={overlay.size}")


if __name__ == "__main__":
    main()
