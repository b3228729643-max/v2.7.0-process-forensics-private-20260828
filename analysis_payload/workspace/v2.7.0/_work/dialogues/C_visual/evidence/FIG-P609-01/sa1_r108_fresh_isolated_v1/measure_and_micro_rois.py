from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa1_r108_fresh_isolated_v1")
VIEWS = ROOT / "views"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
FULL = VIEWS / "r108_p661_full_300dpi.png"
PAGE_INDEX = 660
FIG_RECT = fitz.Rect(60, 525, 530, 730)


def px_box(rect: fitz.Rect, sx: float, sy: float) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * sx),
        math.floor(rect.y0 * sy),
        math.ceil(rect.x1 * sx),
        math.ceil(rect.y1 * sy),
    )


def semantic_class(text: str, size: float) -> tuple[str, int | None]:
    stripped = text.strip()
    if not stripped:
        return "WHITESPACE_AUX", None
    if size < 8.0:
        return "MATH_SCRIPT", 15
    if re.fullmatch(r"[\W_]+", stripped, flags=re.UNICODE):
        return "PUNCTUATION_AUX", None
    if any("\u4e00" <= char <= "\u9fff" for char in stripped):
        return "CJK_FULL_HEIGHT", 30
    if re.fullmatch(r"[0-9.]+", stripped):
        return "LATIN_DIGIT", 24
    if any(char.isupper() for char in stripped if char.isascii()):
        return "LATIN_UPPER", 24
    if any(char.islower() for char in stripped if char.isascii()) or any(
        "\u0370" <= char <= "\u03ff" for char in stripped
    ):
        return "LATIN_GREEK_LOWER", 17
    return "MATH_BASE", 22


def ink_extent(image: Image.Image, box: tuple[int, int, int, int], vertical: bool) -> tuple[int, int, int]:
    gray = image.crop(box).convert("L")
    values = sorted(gray.getdata())
    if not values:
        return 0, 255, 0
    bg = values[min(len(values) - 1, int(len(values) * 0.90))]
    points: list[tuple[int, int]] = []
    for y in range(gray.height):
        for x in range(gray.width):
            if abs(gray.getpixel((x, y)) - bg) >= 20:
                points.append((x, y))
    if not points:
        return 0, bg, 0
    coords = [p[0] if vertical else p[1] for p in points]
    extent = max(coords) - min(coords) + 1
    return extent, bg, len(points)


def main() -> None:
    image = Image.open(FULL).convert("RGB")
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = image.width / page.rect.width
    sy = image.height / page.rect.height

    rows: list[dict] = []
    index = 0
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            direction = line.get("dir", (1.0, 0.0))
            vertical = abs(direction[1]) > abs(direction[0])
            for span in line.get("spans", []):
                rect = fitz.Rect(span["bbox"])
                if not rect.intersects(FIG_RECT):
                    continue
                index += 1
                box = px_box(rect, sx, sy)
                extent, bg, foreground_count = ink_extent(image, box, vertical)
                classification, threshold = semantic_class(span["text"], float(span["size"]))
                rows.append(
                    {
                        "measurement_id": f"M{index:03d}",
                        "text": span["text"],
                        "font": span["font"],
                        "pdf_size_pt": f"{span['size']:.3f}",
                        "orientation": "vertical" if vertical else "horizontal",
                        "script_class_machine": classification,
                        "threshold_px_protocol": "" if threshold is None else threshold,
                        "h_ink_px_machine": extent,
                        "background_luma_machine": bg,
                        "foreground_pixel_count_machine": foreground_count,
                        "bbox_x0_px": box[0],
                        "bbox_y0_px": box[1],
                        "bbox_x1_px": box[2],
                        "bbox_y1_px": box[3],
                    }
                )
    fields = list(rows[0].keys())
    with (ROOT / "machine_pixel_span_measurements.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    measured = [r for r in rows if r["threshold_px_protocol"] != ""]
    by_class: dict[str, dict] = {}
    for row in measured:
        cls = row["script_class_machine"]
        value = int(row["h_ink_px_machine"])
        item = by_class.setdefault(cls, {"count": 0, "min_h_ink_px_machine": value, "examples_at_min": []})
        item["count"] += 1
        if value < item["min_h_ink_px_machine"]:
            item["min_h_ink_px_machine"] = value
            item["examples_at_min"] = [row["measurement_id"] + ":" + row["text"]]
        elif value == item["min_h_ink_px_machine"]:
            item["examples_at_min"].append(row["measurement_id"] + ":" + row["text"])
    (ROOT / "machine_pixel_summary.json").write_text(
        json.dumps({"measured_span_count": len(measured), "by_class": by_class}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    micro_rects = {
        "micro_cutoff_text_line": fitz.Rect(232, 558, 258, 586),
        "micro_tau_limits": fitz.Rect(366, 570, 386, 605),
        "micro_tau_rhs_script": fitz.Rect(411, 580, 432, 600),
        "micro_neff_scripts": fitz.Rect(316, 603, 410, 628),
        "micro_box_bottom_clearance": fitz.Rect(310, 657, 505, 681),
        "micro_caption_top_clearance": fitz.Rect(70, 690, 225, 725),
    }
    for name, rect in micro_rects.items():
        native = image.crop(px_box(rect, sx, sy))
        native.save(VIEWS / f"{name}_native1x.png")
        native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
            VIEWS / f"{name}_nearest8x.png"
        )


if __name__ == "__main__":
    main()
