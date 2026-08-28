from __future__ import annotations

import csv
import itertools
import json
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P609-01\sa3_r109_fresh_isolated_replacement_v2")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_autocorrelation_ess.tex")
PDFTOTEXT = Path(r"D:\texlive\2026\bin\windows\pdftotext.exe")
PAGE_NUMBER = 661
PAGE_INDEX = PAGE_NUMBER - 1
DPI = 300
SCALE = DPI / 72.0

FULL_RGB = ROOT / "full_page_p661_300dpi.png"
FULL_GRAY = ROOT / "full_page_p661_grayscale_300dpi.png"

# Coordinates are in PDF points and deliberately include the whole figure and its caption.
FIGURE_BODY_PDF = (55.0, 525.0, 535.0, 702.5)
FIGURE_CAPTION_PDF = (55.0, 525.0, 535.0, 726.5)
LEFT_PANEL_PDF = (55.0, 525.0, 307.0, 704.0)
RIGHT_PANEL_PDF = (305.0, 525.0, 514.0, 684.0)
CAPTION_PDF = (55.0, 701.5, 535.0, 727.0)
FIGURE_TEXT_REGION_PDF = (55.0, 525.0, 535.0, 726.5)


def px_box(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(v * SCALE) for v in box)  # type: ignore[return-value]


def save_crop(source: Image.Image, box_pdf: tuple[float, float, float, float], name: str) -> Image.Image:
    crop = source.crop(px_box(box_pdf))
    crop.save(ROOT / name)
    return crop


rgb = Image.open(FULL_RGB).convert("RGB")
gray = Image.open(FULL_GRAY).convert("L")

body = save_crop(rgb, FIGURE_BODY_PDF, "figure_body_crop_300dpi.png")
body_gray = save_crop(gray, FIGURE_BODY_PDF, "figure_body_crop_grayscale_300dpi.png")
figcap = save_crop(rgb, FIGURE_CAPTION_PDF, "figure_caption_crop_300dpi.png")
figcap_gray = save_crop(gray, FIGURE_CAPTION_PDF, "figure_caption_crop_grayscale_300dpi.png")

roi_specs = {
    "left_panel": LEFT_PANEL_PDF,
    "right_panel": RIGHT_PANEL_PDF,
    "caption": CAPTION_PDF,
}
for stem, box in roi_specs.items():
    roi = save_crop(rgb, box, f"roi_{stem}_native300.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
        ROOT / f"roi_{stem}_nearest8x.png"
    )

# Extract Unicode word geometry directly from the official PDF without an intermediate file.
proc = subprocess.run(
    [
        str(PDFTOTEXT),
        "-f",
        str(PAGE_NUMBER),
        "-l",
        str(PAGE_NUMBER),
        "-bbox-layout",
        "-enc",
        "UTF-8",
        str(PDF),
        "-",
    ],
    check=True,
    capture_output=True,
)
xml_text = proc.stdout.decode("utf-8", errors="strict")
xml_root = ET.fromstring(xml_text)

ns = {"x": "http://www.w3.org/1999/xhtml"}


def fattr(node: ET.Element, key: str) -> float:
    return float(node.attrib[key])


def intersects(box: tuple[float, float, float, float], region: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = box
    rx0, ry0, rx1, ry1 = region
    return x1 > rx0 and x0 < rx1 and y1 > ry0 and y0 < ry1


def classify_script(text: str) -> tuple[str, int | None]:
    token = text.strip()
    if token in {"…", "...", "⋯", "·", "̂", "ˆ", ",", "，", ";", "；", ":", "："}:
        return "punctuation_advisory", None
    if token and all(unicodedata.category(ch).startswith(("S", "P", "M")) for ch in token):
        return "low_profile_operator_or_accent_advisory", None
    has_cjk = bool(re.search(r"[\u3400-\u9fff]", text))
    if has_cjk:
        return "cjk_or_mixed", 30
    if re.fullmatch(r"[0-9.]+", text):
        return "latin_digit", 24
    letters = [ch for ch in text if ch.isalpha()]
    if letters and any(ch.isupper() for ch in letters):
        return "latin_upper_or_mixed", 24
    if letters:
        return "latin_or_greek_lower", 17
    return "math_symbol", 22


def role_for(text: str, box: tuple[float, float, float, float]) -> tuple[str, float, int]:
    x0, y0, x1, y1 = box
    if y0 >= 700.0:
        return "caption", 10.90909, 40
    if y0 < 551.0 and x0 < 310.0:
        return "panel_title", 10.4, 17
    if y0 < 572.0 and x0 >= 300.0:
        return "panel_title", 10.4, 32
    if 684.0 <= y0 < 704.5 and x0 < 300.0:
        return "axis_label", 9.8, 18
    if 100.0 < x0 < 132.0 and 560.0 <= y0 < 680.0 and re.fullmatch(r"[0-9.]+", text.strip()):
        return "tick_label", 9.6, 19
    if x0 < 132.0 and 560.0 <= y0 < 695.0:
        return "axis_label", 9.8, 18
    if 560.0 <= y0 < 704.5 and x0 < 310.0:
        if re.fullmatch(r"[0-9.]+", text.strip()):
            return "tick_label", 9.6, 19
        if "截断" in text or "K" in text:
            return "annotation", 9.6, 25
        if text.strip() in {"…", "...", "⋯"}:
            return "continuation_mark", 9.6, 27
        return "plot_text", 9.6, 13
    if 575.0 <= y0 < 630.5 and x0 >= 300.0:
        return "formula", 9.6, 33
    if y0 >= 630.0 and x0 >= 300.0:
        return "explanatory_text", 9.6, 35
    return "figure_text", 9.6, 13


image_gray = np.array(gray)
words: list[dict[str, object]] = []
lines: list[dict[str, object]] = []
line_counter = 0
word_counter = 0
for line in xml_root.findall(".//x:line", ns):
    line_box = (fattr(line, "xMin"), fattr(line, "yMin"), fattr(line, "xMax"), fattr(line, "yMax"))
    if not intersects(line_box, FIGURE_TEXT_REGION_PDF):
        continue
    line_counter += 1
    line_words = line.findall("x:word", ns)
    text = " ".join((w.text or "") for w in line_words).strip()
    lines.append(
        {
            "line_id": f"L{line_counter:03d}",
            "text": text,
            "bbox_x0_pt": round(line_box[0], 3),
            "bbox_y0_pt": round(line_box[1], 3),
            "bbox_x1_pt": round(line_box[2], 3),
            "bbox_y1_pt": round(line_box[3], 3),
        }
    )
    for word in line_words:
        word_counter += 1
        text = (word.text or "").strip()
        box = (fattr(word, "xMin"), fattr(word, "yMin"), fattr(word, "xMax"), fattr(word, "yMax"))
        x0, y0, x1, y1 = px_box(box)
        x0 = max(0, min(image_gray.shape[1] - 1, x0))
        x1 = max(x0 + 1, min(image_gray.shape[1], x1))
        y0 = max(0, min(image_gray.shape[0] - 1, y0))
        y1 = max(y0 + 1, min(image_gray.shape[0], y1))
        patch = image_gray[y0:y1, x0:x1]
        bg = float(np.percentile(patch, 92))
        ink = np.abs(patch.astype(np.float32) - bg) >= 20.0
        rows = np.where(np.any(ink, axis=1))[0]
        h_ink = int(rows[-1] - rows[0] + 1) if rows.size else 0
        script_class, hard_threshold = classify_script(text)
        role, declared_pt, source_line = role_for(text, box)
        derived_script_ids = {"T007", "T017", "T020", "T031", "T034", "T044", "T046", "T049", "T053", "T054", "T056"}
        current_id = f"T{word_counter:03d}"
        if current_id in derived_script_ids:
            script_class, hard_threshold = "derived_math_script", 15
        hard_pass = "ADVISORY" if hard_threshold is None else str(h_ink >= hard_threshold).lower()
        words.append(
            {
                "element_id": current_id,
                "panel_id": "CAPTION" if role == "caption" else ("LEFT" if box[0] < 305 else "RIGHT"),
                "role": role,
                "source_file": SOURCE.name,
                "source_line": source_line,
                "declared_pt": declared_pt,
                "graphics_scale": 1.0,
                "effective_pt": declared_pt,
                "text_sample": text,
                "script_class": script_class,
                "bbox_x0_pt": round(box[0], 3),
                "bbox_y0_pt": round(box[1], 3),
                "bbox_x1_pt": round(box[2], 3),
                "bbox_y1_pt": round(box[3], 3),
                "bbox_x0_px": x0,
                "bbox_y0_px": y0,
                "bbox_x1_px": x1,
                "bbox_y1_px": y1,
                "h_ink_px": h_ink,
                "hard_threshold_px": "" if hard_threshold is None else hard_threshold,
                "machine_threshold_result": hard_pass,
                "local_background_gray": round(bg, 2),
            }
        )

with (ROOT / "pdf_text_lines.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
    writer.writeheader()
    writer.writerows(lines)

with (ROOT / "text_word_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(words[0].keys()))
    writer.writeheader()
    writer.writerows(words)

# Overlay every extracted word box with its unique machine ID.
overlay = rgb.copy()
draw = ImageDraw.Draw(overlay)
try:
    font = ImageFont.truetype("arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()
for row in words:
    box = (
        int(row["bbox_x0_px"]),
        int(row["bbox_y0_px"]),
        int(row["bbox_x1_px"]),
        int(row["bbox_y1_px"]),
    )
    draw.rectangle(box, outline=(220, 0, 0), width=2)
    draw.text((box[0], max(0, box[1] - 14)), str(row["element_id"]), fill=(220, 0, 0), font=font)
overlay.crop(px_box(FIGURE_CAPTION_PDF)).save(ROOT / "text_measurement_overlay_300dpi.png")

# Build a conservative native-raster foreground mask and an outline overlay.
figcap_gray_arr = np.array(figcap_gray)
background = cv2.GaussianBlur(figcap_gray_arr, (0, 0), sigmaX=8.0)
contrast = cv2.absdiff(figcap_gray_arr, background)
mask = np.where(contrast >= 20, 255, 0).astype(np.uint8)
Image.fromarray(mask).save(ROOT / "figure_foreground_mask_300dpi.png")
contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
outline_arr = np.array(figcap).copy()
cv2.drawContours(outline_arr, contours, -1, (220, 0, 0), 1)
Image.fromarray(outline_arr).save(ROOT / "figure_outline_overlay_300dpi.png")

# A semantic denominator at the granularity used for pairwise overlap review.
# Formula constituents and contiguous title/caption phrases are one semantic object;
# every independent tick label remains its own reader-visible object.
objects: list[dict[str, object]] = []
word_lookup = {str(row["element_id"]): row for row in words}

semantic_text_specs = [
    ("S001", ["T001", "T002", "T003"], "LEFT", "panel_title", "1. 经验 ACF：预设窗口", 10.4, "17"),
    ("S002", ["T004", "T005", "T006", "T007", "T008"], "LEFT", "axis_label", "经验 ACF rhohat_k", 9.8, "18"),
    ("S003", ["T009"], "LEFT", "tick_label", "y tick 1", 9.6, "19"),
    ("S004", ["T018"], "LEFT", "tick_label", "y tick 0.75", 9.6, "19"),
    ("S005", ["T029"], "LEFT", "tick_label", "y tick 0.5", 9.6, "19"),
    ("S006", ["T035"], "LEFT", "tick_label", "y tick 0.25", 9.6, "19"),
    ("S007", ["T036"], "LEFT", "tick_label", "y tick 0", 9.6, "19"),
    ("S008", ["T038"], "LEFT", "tick_label", "x tick 0", 9.6, "19"),
    ("S009", ["T039"], "LEFT", "tick_label", "x tick 1", 9.6, "19"),
    ("S010", ["T040"], "LEFT", "tick_label", "x tick 2", 9.6, "19"),
    ("S011", ["T041"], "LEFT", "tick_label", "x tick 3", 9.6, "19"),
    ("S012", ["T042"], "LEFT", "tick_label", "x tick 4", 9.6, "19"),
    ("S013", ["T043"], "LEFT", "tick_label", "x tick 5", 9.6, "19"),
    ("S014", ["T071"], "LEFT", "tick_label", "x tick 6", 9.6, "19"),
    ("S015", ["T072", "T073"], "LEFT", "axis_label", "滞后 k", 9.8, "18"),
    ("S016", ["T013", "T014", "T015", "T016"], "LEFT", "annotation", "截断 K=6", 9.6, "25-26"),
    ("S017", ["T037"], "LEFT", "continuation_mark", "ellipsis after the preset window", 9.6, "27-28"),
    ("S018", ["T010", "T011", "T012"], "RIGHT", "panel_title", "2. 有限样本加权 ESS", 10.4, "32"),
    ("S019", ["T017", "T019", "T020", "T021", "T022", "T023", "T024", "T025", "T026", "T027", "T028", "T034", "T049", "T050", "T051", "T052", "T053", "T054"], "RIGHT", "formula", "tauhat_K,n weighted-window formula", 9.6, "33"),
    ("S020", ["T030", "T031", "T032", "T033", "T044", "T045", "T046", "T047", "T048"], "RIGHT", "formula", "Nhat_eff = n/tauhat_K,n", 9.6, "34"),
    ("S021", ["T055", "T056", "T057", "T058"], "RIGHT", "formula", "tauhat_K,n > 0", 9.6, "34"),
    ("S022", ["T059", "T060", "T061", "T062", "T063", "T064", "T065", "T066", "T067", "T068"], "RIGHT", "explanatory_text", "preset K=6<n; include only 1<=k<=K", 9.6, "35"),
    ("S023", ["T069"], "RIGHT", "explanatory_text", "later lags not shown or included", 9.6, "36"),
    ("S024", ["T070"], "RIGHT", "explanatory_text", "finite-trajectory diagnostic, not convergence proof", 9.6, "37"),
    ("S025", ["T074", "T075"], "CAPTION", "caption_label", "图 32.9", 10.90909, "40-41"),
    ("S026", ["T076"], "CAPTION", "caption_text", "fixed-window positive autocorrelation increases variance weight and reduces ESS", 10.90909, "40-41"),
]

source_audit: list[dict[str, object]] = []
for oid, members, panel, role, desc, declared_pt, source_lines in semantic_text_specs:
    member_rows = [word_lookup[mid] for mid in members]
    box = (
        min(float(row["bbox_x0_pt"]) for row in member_rows),
        min(float(row["bbox_y0_pt"]) for row in member_rows),
        max(float(row["bbox_x1_pt"]) for row in member_rows),
        max(float(row["bbox_y1_pt"]) for row in member_rows),
    )
    objects.append(
        {
            "object_id": oid,
            "object_class": "TEXT_OR_FORMULA",
            "panel_id": panel,
            "role": role,
            "description": desc,
            "bbox_x0_pt": round(box[0], 3),
            "bbox_y0_pt": round(box[1], 3),
            "bbox_x1_pt": round(box[2], 3),
            "bbox_y1_pt": round(box[3], 3),
            "source_line": source_lines,
        }
    )
    source_audit.append(
        {
            "element_id": oid,
            "panel_id": panel,
            "role": role,
            "description": desc,
            "source_lines": source_lines,
            "declared_pt": declared_pt,
            "graphics_scale": 1.0,
            "effective_pt": declared_pt,
            "source_font_metadata": "explicit fontsize; caption compiled normalsize",
        }
    )

with (ROOT / "source_font_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(source_audit[0].keys()))
    writer.writeheader()
    writer.writerows(source_audit)

graphic_objects = [
    ("G001", "PANEL_BACKGROUND", "LEFT", "light-blue ACF window fill", (140.0, 558.0, 266.0, 679.0), 21),
    ("G002", "AXIS_AND_TICKS", "LEFT", "left and bottom axes with tick marks", (126.0, 558.0, 304.0, 682.0), 19),
    ("G003", "DATA_CURVE", "LEFT", "seven ACF stems and circular markers for k=0..6", (132.0, 563.0, 259.0, 679.0), 22),
    ("G004", "WINDOW_BOUNDARY", "LEFT", "dashed K=6.5 boundary", (267.0, 557.0, 269.0, 680.0), 24),
    ("G005", "PANEL_BORDER", "RIGHT", "rounded ESS explanation box", (308.0, 542.0, 509.0, 682.0), 30),
    ("G006", "LINE_ARROW", "BETWEEN", "left-to-right connector arrow", (296.0, 613.0, 307.0, 617.0), 38),
]
for oid, cls, panel, desc, box, source_line in graphic_objects:
    objects.append(
        {
            "object_id": oid,
            "object_class": cls,
            "panel_id": panel,
            "role": cls.lower(),
            "description": desc,
            "bbox_x0_pt": box[0],
            "bbox_y0_pt": box[1],
            "bbox_x1_pt": box[2],
            "bbox_y1_pt": box[3],
            "source_line": source_line,
        }
    )

with (ROOT / "visible_object_denominator.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(objects[0].keys()))
    writer.writeheader()
    writer.writerows(objects)

semantic_overlay = rgb.copy()
semantic_draw = ImageDraw.Draw(semantic_overlay)
for row in objects:
    box = px_box(
        (
            float(row["bbox_x0_pt"]),
            float(row["bbox_y0_pt"]),
            float(row["bbox_x1_pt"]),
            float(row["bbox_y1_pt"]),
        )
    )
    color = (220, 0, 0) if row["object_class"] == "TEXT_OR_FORMULA" else (0, 80, 220)
    semantic_draw.rectangle(box, outline=color, width=2)
    semantic_draw.text((box[0], max(0, box[1] - 14)), str(row["object_id"]), fill=color, font=font)
semantic_overlay.crop(px_box(FIGURE_CAPTION_PDF)).save(ROOT / "semantic_object_overlay_300dpi.png")

# Conservative native-raster clearance estimates. These are machine measurements,
# not semantic judgments: the reviewer must decide whether the nearest external ink
# belongs to a prohibited pair, an intentional chart contact, or an advisory halo.
crop_x0, crop_y0, _, _ = px_box(FIGURE_CAPTION_PDF)
foreground_bool = mask > 0
clearance_rows: list[dict[str, object]] = []
for row in objects:
    if row["object_class"] != "TEXT_OR_FORMULA":
        continue
    ax0, ay0, ax1, ay1 = px_box(
        (
            float(row["bbox_x0_pt"]),
            float(row["bbox_y0_pt"]),
            float(row["bbox_x1_pt"]),
            float(row["bbox_y1_pt"]),
        )
    )
    x0 = max(0, ax0 - crop_x0)
    y0 = max(0, ay0 - crop_y0)
    x1 = min(foreground_bool.shape[1], ax1 - crop_x0)
    y1 = min(foreground_bool.shape[0], ay1 - crop_y0)
    object_pixels = foreground_bool[y0:y1, x0:x1]
    external = foreground_bool.copy()
    pad = 6
    external[max(0, y0 - pad):min(external.shape[0], y1 + pad), max(0, x0 - pad):min(external.shape[1], x1 + pad)] = False
    distance = cv2.distanceTransform((~external).astype(np.uint8), cv2.DIST_L2, 5)
    estimate = float(np.min(distance[y0:y1, x0:x1][object_pixels])) if np.any(object_pixels) else float("nan")
    clearance_rows.append(
        {
            "element_id": row["object_id"],
            "panel_id": row["panel_id"],
            "role": row["role"],
            "estimated_min_external_ink_clearance_px": round(estimate, 3),
            "exclusion_pad_px": pad,
            "machine_note": "native-300dpi foreground estimate; manual semantic classification required",
        }
    )

with (ROOT / "machine_clearance_estimates.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(clearance_rows[0].keys()))
    writer.writeheader()
    writer.writerows(clearance_rows)

pairs: list[dict[str, object]] = []
for idx, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
    ax0, ay0, ax1, ay1 = (float(a[k]) for k in ("bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt"))
    bx0, by0, bx1, by1 = (float(b[k]) for k in ("bbox_x0_pt", "bbox_y0_pt", "bbox_x1_pt", "bbox_y1_pt"))
    gap_x = max(bx0 - ax1, ax0 - bx1, 0.0)
    gap_y = max(by0 - ay1, ay0 - by1, 0.0)
    bbox_intersection = max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))
    pairs.append(
        {
            "pair_id": f"P{idx:05d}",
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "class_a": a["object_class"],
            "class_b": b["object_class"],
            "bbox_intersection_pt2": round(bbox_intersection, 4),
            "bbox_gap_x_pt": round(gap_x, 4),
            "bbox_gap_y_pt": round(gap_y, 4),
        }
    )

with (ROOT / "unordered_pairs.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(pairs[0].keys()))
    writer.writeheader()
    writer.writerows(pairs)

metadata = {
    "candidate": "official_R109",
    "physical_page": PAGE_NUMBER,
    "printed_page": 648,
    "render_dpi": DPI,
    "render_scale_px_per_pdf_pt": SCALE,
    "full_page_pixels": [rgb.width, rgb.height],
    "figure_body_pdf_bbox": FIGURE_BODY_PDF,
    "figure_caption_pdf_bbox": FIGURE_CAPTION_PDF,
    "word_fragment_count": len(words),
    "semantic_text_element_count": len(semantic_text_specs),
    "semantic_graphic_object_count": len(graphic_objects),
    "visible_object_denominator": len(objects),
    "unordered_pair_count": len(pairs),
    "pair_count_formula": f"{len(objects)}*({len(objects)}-1)/2",
    "foreground_mask_threshold": "abs(native_gray - gaussian_local_background_sigma8) >= 20/255",
    "outline_method": "OpenCV RETR_LIST contours over the native 300 dpi foreground mask",
    "taxonomy_note": "R168 micro pixel/outline/taxonomy/peer/font metadata is advisory; hard decisions use true glyph integrity, readability, clipping, illegal overlap, geometry, and semantics.",
    "manual_fields_present": False,
}
(ROOT / "machine_geometry_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps(metadata, ensure_ascii=False))
