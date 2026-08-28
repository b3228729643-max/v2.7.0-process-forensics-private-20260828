from __future__ import annotations

import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual"
    r"\evidence\figures\FIG-P077-01\STRICT_R1_SA2_R168_READONLY_R114_20260827"
)
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0"
    r"\src\build\strict_current_r114_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src"
    r"\绘图源码\第01册_数学基础与统计学习基本理论\V1-C05"
    r"\fig_v1_c05_gaussian.tex"
)
PAGE_NUMBER = 79
EXPECTED = {
    PDF: (4_967_122, "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"),
    SOURCE: (2_603, "ED96F120CFF0815122B2914D7D94D12884FAC3DB328D30E883F93457C68484E4"),
}

# The semantic denominator was transcribed after opening the native 300 dpi page.
# This dictionary contains geometry and taxonomy only.  It intentionally has no
# reviewer, boolean, decision, verdict, or note fields.
OBJECTS = [
    ("O01", "x tick label -4", "TEXT", "TICK", (144.10, 566.63, 156.48, 575.89), "26"),
    ("O02", "x tick label 0", "TEXT", "TICK", (303.20, 566.62, 308.57, 575.89), "26"),
    ("O03", "x tick label 4", "TEXT", "TICK", (458.87, 566.63, 464.09, 575.89), "26"),
    ("O04", "y tick label 0", "TEXT", "TICK", (119.51, 540.31, 124.88, 549.57), "26"),
    ("O05", "y tick label 0.2", "TEXT", "TICK", (111.94, 487.42, 124.88, 496.69), "26"),
    ("O06", "y tick label 0.4", "TEXT", "TICK", (111.57, 434.52, 124.88, 443.79), "26"),
    ("O07", "x axis label x", "FORMULA", "AXIS_LABEL", (303.05, 578.45, 308.62, 588.41), "23"),
    ("O08", "y axis label density", "TEXT", "AXIS_LABEL", (95.64, 486.10, 105.60, 506.02), "23"),
    ("O09", "N(0,1) direct label and peak", "FORMULA", "DIRECT_LABEL", (343.04, 450.16, 434.12, 463.47), "44-45"),
    ("O10", "N(0,2^2) direct label and peak", "FORMULA", "DIRECT_LABEL", (385.82, 495.12, 493.45, 508.43), "46-47"),
    ("O11", "area equals one annotation", "FORMULA", "ANNOTATION", (264.78, 552.33, 346.99, 563.10), "51-53"),
    ("O12", "caption label Figure 5.1", "TEXT", "CAPTION_LABEL", (141.30, 596.54, 166.22, 607.00), "56"),
    ("O13", "caption conclusion", "TEXT", "CAPTION", (176.18, 596.54, 442.63, 606.83), "56"),
    ("O14", "axis frame and tick marks", "LINE_ARROW", "AXIS_FRAME", (128.71, 430.60, 480.94, 563.65), "21-27"),
    ("O15", "solid narrow Gaussian curve", "DATA_CURVE", "CURVE", (130.84, 438.81, 480.93, 544.33), "37-38"),
    ("O16", "dashed wide Gaussian curve", "DATA_CURVE", "CURVE", (130.84, 491.57, 480.93, 540.14), "39-41"),
    ("O17", "narrow Gaussian pale fill", "DATA_FILL", "FILL", (130.84, 438.81, 480.94, 544.33), "33-36"),
    ("O18", "wide Gaussian pale fill", "DATA_FILL", "FILL", (130.84, 491.57, 480.94, 544.33), "29-32"),
    ("O19", "vertical x equals zero guide", "LINE_ARROW", "REFERENCE_LINE", (305.88, 437.21, 305.90, 544.33), "42-43"),
    ("O20", "area brace", "LINE_ARROW", "BRACE", (169.74, 549.08, 442.04, 552.08), "48-50"),
]

TEXT_SCRIPT = {
    "O01": "LATIN_DIGIT",
    "O02": "LATIN_DIGIT",
    "O03": "LATIN_DIGIT",
    "O04": "LATIN_DIGIT",
    "O05": "LATIN_DIGIT",
    "O06": "LATIN_DIGIT",
    "O07": "MATH_LOWERCASE",
    "O08": "CJK_VERTICAL",
    "O09": "MIXED_MATH_CJK",
    "O10": "MIXED_MATH_CJK",
    "O11": "MIXED_CJK_MATH",
    "O12": "MIXED_CJK_DIGIT",
    "O13": "CJK",
}

FIGURE_CROP = (360, 1760, 2110, 2565)
ROIS = {
    "critical_roi_narrow_label": (1400, 1840, 1835, 1985),
    "critical_roi_wide_label": (1575, 2025, 2075, 2175),
    "critical_roi_area_annotation": (1050, 2260, 1495, 2380),
    "critical_roi_y_ticks": (430, 1770, 555, 2325),
    "critical_roi_x_ticks_caption": (565, 2320, 1900, 2555),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def px_box(pt_box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pt_box
    return (round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy))


def ink_metrics(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int]:
    gray = image.convert("L").crop(box)
    mask = gray.point(lambda value: 255 if value <= 235 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return 0, 0
    histogram = mask.histogram()
    foreground_pixels = histogram[255]
    return bbox[3] - bbox[1], foreground_pixels


def main() -> None:
    ROOT.mkdir(parents=False, exist_ok=True)
    identities = []
    for path, (expected_size, expected_hash) in EXPECTED.items():
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if (actual_size, actual_hash) != (expected_size, expected_hash):
            raise RuntimeError(f"identity mismatch: {path}")
        identities.append(
            {
                "path": str(path),
                "size_bytes": actual_size,
                "sha256": actual_hash,
                "expected_size_bytes": expected_size,
                "expected_sha256": expected_hash,
                "identity_match": True,
            }
        )
    (ROOT / "machine_input_identity.json").write_text(
        json.dumps(identities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    reader = PdfReader(PDF)
    needle = "方差增大使高斯密度变宽"
    hits = [index + 1 for index, page in enumerate(reader.pages) if needle in (page.extract_text() or "")]
    if hits != [PAGE_NUMBER]:
        raise RuntimeError(f"caption location mismatch: {hits}")
    (ROOT / "machine_caption_location.json").write_text(
        json.dumps(
            {
                "needle": needle,
                "page_hits_1_based": hits,
                "located_pdf_physical_page": PAGE_NUMBER,
                "pdf_page_count": len(reader.pages),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    full = Image.open(ROOT / "full_page_native_300dpi.png").convert("RGB")
    sx = full.width / 595.276
    sy = full.height / 841.890
    figure = full.crop(FIGURE_CROP)
    figure.save(ROOT / "figure_crop_native_300dpi.png")
    figure.convert("L").save(ROOT / "figure_crop_grayscale_300dpi.png")

    object_rows = []
    text_rows = []
    for object_id, name, object_class, role, pt, source_line in OBJECTS:
        pixels = px_box(pt, sx, sy)
        object_rows.append(
            {
                "object_id": object_id,
                "name": name,
                "object_class": object_class,
                "role": role,
                "panel_id": "PANEL-A",
                "pdf_x0_pt": pt[0],
                "pdf_top_pt": pt[1],
                "pdf_x1_pt": pt[2],
                "pdf_bottom_pt": pt[3],
                "pixel_x0": pixels[0],
                "pixel_y0": pixels[1],
                "pixel_x1": pixels[2],
                "pixel_y1": pixels[3],
                "source_line": source_line,
            }
        )
        if object_id in TEXT_SCRIPT:
            height, count = ink_metrics(full, pixels)
            text_rows.append(
                {
                    "element_id": object_id,
                    "role": role,
                    "script_class": TEXT_SCRIPT[object_id],
                    "bbox_x0": pixels[0],
                    "bbox_y0": pixels[1],
                    "bbox_x1": pixels[2],
                    "bbox_y1": pixels[3],
                    "bbox_height_px": pixels[3] - pixels[1],
                    "threshold_20_255_h_ink_px": height,
                    "threshold_20_255_foreground_pixel_count": count,
                    "threshold_gray_max": 235,
                }
            )

    with (ROOT / "machine_visible_object_geometry.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(object_rows[0]))
        writer.writeheader()
        writer.writerows(object_rows)
    with (ROOT / "machine_text_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(text_rows[0]))
        writer.writeheader()
        writer.writerows(text_rows)

    pair_rows = []
    for index, (left, right) in enumerate(combinations(object_rows, 2), start=1):
        pair_rows.append(
            {
                "pair_id": f"P{index:03d}",
                "object_a": left["object_id"],
                "object_b": right["object_id"],
                "class_a": left["object_class"],
                "class_b": right["object_class"],
            }
        )
    if len(pair_rows) != 190:
        raise RuntimeError(f"pair denominator is {len(pair_rows)}, expected 190")
    with (ROOT / "machine_unordered_pair_denominator.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    overlay = full.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    palette = {
        "TEXT": "#d62728",
        "FORMULA": "#ff7f0e",
        "LINE_ARROW": "#9467bd",
        "DATA_CURVE": "#1f77b4",
        "DATA_FILL": "#2ca02c",
    }
    for row in object_rows:
        box = (row["pixel_x0"], row["pixel_y0"], row["pixel_x1"], row["pixel_y1"])
        color = palette[row["object_class"]]
        draw.rectangle(box, outline=color, width=3)
        label_y = max(0, box[1] - 13)
        draw.rectangle((box[0], label_y, box[0] + 28, label_y + 12), fill="white")
        draw.text((box[0] + 1, label_y), row["object_id"], fill=color, font=font)
    overlay.crop(FIGURE_CROP).save(ROOT / "object_id_overlay_300dpi.png")

    for name, box in ROIS.items():
        roi = full.crop(box)
        roi.save(ROOT / f"{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{name}_nearest8x.png"
        )

    (ROOT / "machine_render_geometry.json").write_text(
        json.dumps(
            {
                "pdf_page_1_based": PAGE_NUMBER,
                "render_dpi": 300,
                "full_page_pixel_size": [full.width, full.height],
                "scale_x_px_per_pt": sx,
                "scale_y_px_per_pt": sy,
                "figure_crop_pixel_box": FIGURE_CROP,
                "critical_roi_pixel_boxes": ROIS,
                "visible_object_count": len(object_rows),
                "unordered_pair_count": len(pair_rows),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
