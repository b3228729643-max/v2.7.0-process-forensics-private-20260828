from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build"
    r"\strict_current_r105_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码"
    r"\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex"
)
PAGE_NUMBER = 661
EXPECTED_PDF_BYTES = 4_967_209
EXPECTED_PDF_SHA256 = "F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1"
DPI = 300
SCALE = DPI / 72.0

# All coordinates below are integer coordinates on the unresized 2481x3508
# Poppler raster of physical page 661.  The figure crop includes the published
# caption; the standalone crop contains the full graphic and generous white
# safety margins but excludes the caption.
FIGURE_CROP_PX = (292, 917, 2146, 1867)
STANDALONE_CROP_PX = (479, 917, 1959, 1784)
STANDALONE_PT = fitz.Rect(*(v / SCALE for v in STANDALONE_CROP_PX))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rect_tuple(rect: fitz.Rect, digits: int = 3) -> list[float]:
    return [round(rect.x0, digits), round(rect.y0, digits), round(rect.x1, digits), round(rect.y1, digits)]


def pt_to_full_px(rect: fitz.Rect) -> tuple[int, int, int, int]:
    return (
        math.floor(rect.x0 * SCALE),
        math.floor(rect.y0 * SCALE),
        math.ceil(rect.x1 * SCALE),
        math.ceil(rect.y1 * SCALE),
    )


def full_to_standalone(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    sx0, sy0, _, _ = STANDALONE_CROP_PX
    return x0 - sx0, y0 - sy0, x1 - sx0, y1 - sy0


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def color_to_rgb(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(c) * 255)) for c in value)


def target_mask_from_patch(patch: np.ndarray, target: tuple[int, int, int]) -> np.ndarray:
    """Raw visible pixels at >=20/255 contrast, constrained to target color ray.

    All audited glyphs in this figure sit on white page background.  Requiring
    the observed RGB to remain near the alpha-compositing line from white to the
    PDF foreground color excludes blue curves, gold rules, and grey hatching.
    """
    arr = patch.astype(np.float32)
    bg = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    fg = np.array(target, dtype=np.float32)
    direction = fg - bg
    norm2 = float(np.dot(direction, direction))
    if norm2 == 0:
        return np.zeros(arr.shape[:2], dtype=bool)
    delta = arr - bg
    alpha = np.einsum("...c,c->...", delta, direction) / norm2
    recon = bg + alpha[..., None] * direction
    perp = np.linalg.norm(arr - recon, axis=2)
    contrast = np.max(np.abs(arr - bg), axis=2)
    return (alpha > 0.0) & (alpha <= 1.15) & (contrast >= 20.0) & (perp <= 18.0)


def ink_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def char_class(ch: str, span_size: float, parent: str) -> tuple[str, int]:
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if span_size < 8.5 and parent in {"YLABEL_UPPER", "TITLE_UPPER", "YLABEL_LOWER", "TITLE_LOWER"}:
        return "NATURAL_MATH_SCRIPT", 15
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK", 30
    if ch in "+−=<>≤≥≈∑√×÷":
        return "BASE_MATH_OPERATOR", 22
    if ch in ",.，。:：;；…":
        return "LOW_PROFILE_PUNCTUATION", 0
    if ch.isdigit() or ch.isupper():
        return "LATIN_UPPER_OR_DIGIT", 24
    if ch.islower() or "GREEK" in unicodedata.name(ch, "") or 0x1D400 <= cp <= 0x1D7FF:
        return "LATIN_GREEK_LOWER_OR_MATH_LETTER", 17
    if cat.startswith("P"):
        return "PUNCTUATION", 0
    return "OTHER_VISIBLE", 17


def parent_for_char(cx: float, cy: float) -> str:
    if cy < 247:
        return "TITLE_UPPER"
    if cx < 155 and 265 <= cy < 300:
        return "YLABEL_UPPER"
    if 245 <= cx < 305 and 250 <= cy < 288:
        return "ANNO_WARMUP"
    if 305 <= cx < 405 and 250 <= cy < 286:
        return "ANNO_RETAINED"
    if cx < 180 and 245 <= cy < 310:
        return "YTICKS_UPPER"
    if 305 <= cy < 334:
        return "TITLE_LOWER"
    if cx < 155 and 345 <= cy < 385:
        return "YLABEL_LOWER"
    if cx < 180 and 340 <= cy < 398:
        return "YTICKS_LOWER"
    if 398 <= cy < 413:
        return "XTICKS_LOWER"
    if cy >= 411:
        return "XLABEL_LOWER"
    if 400 <= cx and 328 <= cy < 352:
        return "ANNO_TARGET"
    return "UNMAPPED_TEXT_PARENT"


def drawing_class(index: int) -> tuple[str, str]:
    fixed = {
        6: ("TICKS", "XTICKS_UPPER"),
        7: ("TICKS", "YTICKS_UPPER"),
        8: ("AXIS_LINE", "AXIS_UPPER_X"),
        9: ("ARROWHEAD", "AXIS_UPPER_X"),
        10: ("AXIS_LINE", "AXIS_UPPER_Y"),
        11: ("ARROWHEAD", "AXIS_UPPER_Y"),
        13: ("DATA_CURVE", "SERIES_UPPER"),
        14: ("REFERENCE_LINE", "DIVIDER_UPPER"),
        15: ("MATH_RULE", "ANNO_WARMUP_EQ"),
        16: ("MATH_RULE", "ANNO_WARMUP_EQ"),
        17: ("MATH_RULE", "ANNO_RETAINED_EQ"),
        18: ("MATH_RULE", "ANNO_RETAINED_EQ"),
        39: ("TICKS", "XTICKS_LOWER"),
        40: ("TICKS", "YTICKS_LOWER"),
        41: ("AXIS_LINE", "AXIS_LOWER_X"),
        42: ("ARROWHEAD", "AXIS_LOWER_X"),
        43: ("AXIS_LINE", "AXIS_LOWER_Y"),
        44: ("ARROWHEAD", "AXIS_LOWER_Y"),
        46: ("DATA_CURVE", "SERIES_LOWER"),
        47: ("REFERENCE_LINE", "DIVIDER_LOWER"),
        48: ("REFERENCE_LINE", "TARGET_LINE"),
        64: ("MATH_RULE", "YLABEL_LOWER_OVERLINE"),
        65: ("MATH_RULE", "TITLE_LOWER_OVERLINE"),
    }
    if 19 <= index <= 38:
        return "MARKER", f"MARKER_UPPER_{index - 18:02d}"
    if 49 <= index <= 63:
        return "MARKER", f"MARKER_LOWER_{index - 48:02d}"
    return fixed.get(index, ("UNCLASSIFIED_DRAWING", f"DRAWING_{index:03d}"))


def reconstruct_drawing_mask(page_rect: fitz.Rect, drawing: dict, clip: fitz.Rect) -> np.ndarray:
    """Rasterize one get_drawings() path independently at native 300 dpi.

    This mask is used for proximity candidate generation.  Final critical
    relationship evidence also includes the unmodified Poppler original ROI.
    """
    doc = fitz.open()
    p = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for item in drawing.get("items", []):
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise ValueError(f"Unsupported drawing operation {op!r}")
    line_caps = drawing.get("lineCap") or (0, 0, 0)
    line_cap = max(line_caps) if isinstance(line_caps, (tuple, list)) else int(line_caps)
    dashes = drawing.get("dashes") or None
    shape.finish(
        color=drawing.get("color"),
        fill=drawing.get("fill"),
        dashes=dashes,
        even_odd=bool(drawing.get("even_odd", False)),
        closePath=bool(drawing.get("closePath", False)),
        lineJoin=float(drawing.get("lineJoin", 0.0) or 0.0),
        lineCap=line_cap,
        width=float(drawing.get("width", 1.0) or 0.0),
        stroke_opacity=float(drawing.get("stroke_opacity", 1.0) or 1.0),
        fill_opacity=float(drawing.get("fill_opacity", 1.0) or 1.0),
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    alpha = arr[:, :, 3] if pix.n == 4 else np.max(255 - arr[:, :, :3], axis=2)
    doc.close()
    return alpha >= 20


def global_mask_from_tight(
    shape: tuple[int, int], box: tuple[int, int, int, int], tight: np.ndarray
) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = box
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(shape[1], x1), min(shape[0], y1)
    if cx1 > cx0 and cy1 > cy0:
        out[cy0:cy1, cx0:cx1] = tight[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0]
    return out


def mask_distance(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, float | None]:
    intersection = int(np.count_nonzero(mask_a & mask_b))
    if intersection:
        return intersection, 0.0
    if not mask_a.any() or not mask_b.any():
        return 0, None
    dist = distance_transform_edt(~mask_a)
    center_distance = float(dist[mask_b].min())
    return 0, max(0.0, center_distance - 1.0)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def safe_char(ch: str) -> str:
    return f"U{ord(ch):04X}"


def make_contact_sheets(
    image: Image.Image, glyph_rows: list[dict], masks: dict[str, np.ndarray]
) -> list[dict]:
    out_dir = ROOT / "glyph_contacts"
    out_dir.mkdir(exist_ok=True)
    font = ImageFont.load_default()
    per_sheet = 6
    cell_w, cell_h = 1580, 600
    mapping = []
    for sheet_no, start in enumerate(range(0, len(glyph_rows), per_sheet), 1):
        subset = glyph_rows[start : start + per_sheet]
        sheet = Image.new("RGB", (cell_w, cell_h * len(subset)), "white")
        draw = ImageDraw.Draw(sheet)
        for row_no, row in enumerate(subset, 1):
            obj_id = row["object_id"]
            x0, y0, x1, y1 = (int(row[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
            pad = 4
            bx0, by0 = max(0, x0 - pad), max(0, y0 - pad)
            bx1, by1 = min(image.width, x1 + pad), min(image.height, y1 + pad)
            original = image.crop((bx0, by0, bx1, by1)).convert("RGB")
            local_global = masks[obj_id][by0:by1, bx0:bx1]
            overlay = np.asarray(original).copy()
            overlay[local_global] = np.array([255, 0, 0], dtype=np.uint8)
            overlay_img = Image.fromarray(overlay)
            mask_img = Image.fromarray(np.where(local_global, 0, 255).astype(np.uint8), "L").convert("RGB")
            scale8 = lambda im: im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST)
            views = [scale8(original), scale8(overlay_img), scale8(mask_img)]
            native_views = [original, overlay_img, mask_img]
            x_columns = [160, 630, 1100]
            y_base = (row_no - 1) * cell_h
            for x, native, view8 in zip(x_columns, native_views, views):
                sheet.paste(native, (x, y_base + 32))
                sheet.paste(view8, (x, y_base + 112))
            label = (
                f"{obj_id} {safe_char(row['char'])} {row['parent_id']} "
                f"H={row['h_ink_px']} A={row['ink_area_px']}"
            )
            draw.text((6, y_base + 6), label, fill="black", font=font)
            draw.text((160, y_base + 6), "ORIGINAL 1x + complete 8x nearest", fill="black", font=font)
            draw.text((630, y_base + 6), "TARGET OVERLAY 1x + complete 8x nearest", fill="black", font=font)
            draw.text((1100, y_base + 6), "MASK ONLY 1x + complete 8x nearest", fill="black", font=font)
            mapping.append(
                {
                    "object_id": obj_id,
                    "sheet": f"contact_sheet_{sheet_no:02d}.png",
                    "cell": row_no,
                }
            )
        sheet.save(out_dir / f"contact_sheet_{sheet_no:02d}.png")
    return mapping


def make_overlay(image: Image.Image, glyph_rows: list[dict], drawing_rows: list[dict]) -> None:
    overlay = image.copy().convert("RGB")
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    for row in glyph_rows:
        box = tuple(int(row[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
        draw.rectangle(box, outline=(220, 0, 0), width=1)
        draw.text((box[0], max(0, box[1] - 9)), row["object_id"], fill=(180, 0, 0), font=font)
    for row in drawing_rows:
        if row["object_type"] != "MATH_RULE":
            continue
        box = tuple(int(row[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
        draw.rectangle(box, outline=(128, 0, 180), width=2)
        draw.text((box[0], max(0, box[1] - 9)), row["object_id"], fill=(128, 0, 180), font=font)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def make_math_rule_sheet(
    image: Image.Image, drawing_rows: list[dict], masks: dict[str, np.ndarray]
) -> list[dict]:
    rules = [r for r in drawing_rows if r["object_type"] == "MATH_RULE"]
    font = ImageFont.load_default()
    sheet = Image.new("RGB", (1300, 260 * len(rules)), "white")
    draw = ImageDraw.Draw(sheet)
    mapping = []
    for cell, row in enumerate(rules, 1):
        x0, y0, x1, y1 = (int(row[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
        pad = 5
        bx0, by0 = max(0, x0 - pad), max(0, y0 - pad)
        bx1, by1 = min(image.width, x1 + pad), min(image.height, y1 + pad)
        original = image.crop((bx0, by0, bx1, by1)).convert("RGB")
        local = masks[row["object_id"]][by0:by1, bx0:bx1]
        overlay = np.asarray(original).copy()
        overlay[local] = np.array([255, 0, 0], dtype=np.uint8)
        mask_img = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), "L").convert("RGB")
        views = [
            original.resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST),
            Image.fromarray(overlay).resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST),
            mask_img.resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST),
        ]
        native_views = [original, Image.fromarray(overlay), mask_img]
        y_base = (cell - 1) * 260
        for x, native, view8 in zip([210, 570, 930], native_views, views):
            sheet.paste(native, (x, y_base + 30))
            sheet.paste(view8, (x, y_base + 72))
        draw.text((8, y_base + 8), f"{row['object_id']} {row['parent_id']}", fill="black", font=font)
        draw.text((210, y_base + 8), "ORIGINAL 1x + 8x", fill="black", font=font)
        draw.text((570, y_base + 8), "TARGET OVERLAY 1x + 8x", fill="black", font=font)
        draw.text((930, y_base + 8), "MASK ONLY 1x + 8x", fill="black", font=font)
        mapping.append({"object_id": row["object_id"], "sheet": "math_rule_contact_sheet.png", "cell": cell})
    sheet.save(ROOT / "math_rule_contact_sheet.png")
    return mapping


def make_counterevidence(full: Image.Image) -> list[dict]:
    # ROI boxes are physical-page native 300 dpi coordinates and deliberately
    # include the nearest plausible interacting objects.
    specs = [
        ("C01_WARMUP_DIVIDER_EQ", (1010, 1038, 1280, 1205)),
        ("C02_RETAINED_EQ_SERIES", (1265, 1038, 1690, 1260)),
        ("C03_LOWER_TITLE_OVERLINE_PANEL_GAP", (1050, 1275, 1605, 1425)),
        ("C04_TARGET_LABEL_TARGET_LINE", (1645, 1360, 1905, 1575)),
        ("C05_LOWER_YLABEL_OVERLINE_AXIS", (500, 1440, 790, 1635)),
        ("C06_XTICKS_XLABEL_AXIS", (1180, 1600, 1500, 1780)),
    ]
    one_x = Image.new("RGB", (max(b[2] - b[0] for _, b in specs), sum(b[3] - b[1] + 28 for _, b in specs)), "white")
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(one_x)
    y = 0
    rows = []
    roi_dir = ROOT / "critical_rois"
    roi_dir.mkdir(exist_ok=True)
    for roi_id, box in specs:
        roi = full.crop(box).convert("RGB")
        roi.save(roi_dir / f"{roi_id}__native1x.png")
        roi8 = roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST)
        roi8.save(roi_dir / f"{roi_id}__8x_nearest.png")
        draw.text((4, y + 4), roi_id, fill="black", font=font)
        one_x.paste(roi, (0, y + 24))
        y += roi.height + 28
        rows.append(
            {
                "roi_id": roi_id,
                "page_box_px": list(box),
                "native1x": f"critical_rois/{roi_id}__native1x.png",
                "nearest8x": f"critical_rois/{roi_id}__8x_nearest.png",
            }
        )
    one_x = one_x.crop((0, 0, one_x.width, y))
    one_x.save(ROOT / "counterevidence_native1x_sheet.png")
    # Keep exact nearest-neighbour pixels in the 8x sheet; it is intentionally large.
    one_x.resize((one_x.width * 8, one_x.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "counterevidence_8x_nearest_sheet.png"
    )
    write_json(ROOT / "critical_roi_manifest.json", rows)
    return rows


def source_semantic_check(source_text: str) -> dict:
    blocks = re.findall(r"\\addplot\[[^\]]+\]\s+coordinates\s*\{([^}]*)\}", source_text, re.S)
    if len(blocks) != 2:
        raise RuntimeError(f"Expected 2 addplot coordinate blocks, got {len(blocks)}")

    def parse(block: str) -> list[tuple[int, float]]:
        return [(int(t), float(v)) for t, v in re.findall(r"\((\d+),([0-9.]+)\)", block)]

    trace = parse(blocks[0])
    running = parse(blocks[1])
    retained = [value for t, value in trace if t >= 6]
    recomputed = []
    total = 0.0
    for i, value in enumerate(retained, 1):
        total += value
        recomputed.append((i + 5, total / i))
    comparisons = []
    for (t, rendered), (_, expected) in zip(running, recomputed):
        comparisons.append(
            {
                "t": t,
                "source_running_mean": rendered,
                "recomputed_running_mean": round(expected, 8),
                "absolute_difference": round(abs(rendered - expected), 8),
            }
        )
    return {
        "trace_point_count": len(trace),
        "retained_point_count": len(retained),
        "running_mean_point_count": len(running),
        "retained_t_range": [6, 20],
        "final_recomputed_mean": round(recomputed[-1][1], 8),
        "max_rounded_difference": max(r["absolute_difference"] for r in comparisons),
        "coordinate_comparisons": comparisons,
        "source_semantic_strings_present": {
            "upper_title_X_t": "title={轨迹 $X_t$}" in source_text,
            "warmup_t_1_to_5": "{预热段\\\\$t\\slfigTraceTallEq 1,\\ldots,5$}" in source_text,
            "retained_t_6_to_20": "{保留样本 $t\\slfigTraceTallEq 6,\\ldots,20$}" in source_text,
            "lower_ylabel_Xbar_6_t": "ylabel={$\\overline X_{6:\\slfigTraceScriptT}$}" in source_text,
            "lower_title_Xbar_6_t": "title={保留样本运行均值 $\\overline X_{6:t}$}" in source_text,
            "target_value_2": "{目标值 $2$}" in source_text,
            "caption_diagnostic_not_proof": "本图仅作诊断，不构成收敛证明" in source_text,
        },
    }


def main() -> None:
    pdf_hash = sha256(PDF)
    if PDF.stat().st_size != EXPECTED_PDF_BYTES:
        raise RuntimeError("Official PDF byte size mismatch")
    if pdf_hash != EXPECTED_PDF_SHA256:
        raise RuntimeError("Official PDF SHA256 mismatch")

    full_path = ROOT / "full_page_300dpi.png"
    gray_path = ROOT / "full_page_gray_300dpi.png"
    full = Image.open(full_path).convert("RGB")
    gray = Image.open(gray_path).convert("L")
    if full.size != (2481, 3508) or gray.size != (2481, 3508):
        raise RuntimeError(f"Unexpected native page raster dimensions: {full.size}, {gray.size}")
    full.crop(FIGURE_CROP_PX).save(ROOT / "figure_crop_300dpi.png")
    full.crop(STANDALONE_CROP_PX).save(ROOT / "standalone_300dpi.png")
    gray.crop(FIGURE_CROP_PX).save(ROOT / "grayscale_300dpi.png")
    standalone = full.crop(STANDALONE_CROP_PX).convert("RGB")
    standalone_arr = np.asarray(standalone)
    mask_shape = (standalone.height, standalone.width)

    doc = fitz.open(PDF)
    if len(doc) != 817:
        raise RuntimeError(f"Official PDF page count mismatch: {len(doc)}")
    page = doc[PAGE_NUMBER - 1]
    raw = page.get_text("rawdict")
    drawings = page.get_drawings()

    glyph_rows: list[dict] = []
    object_rows: list[dict] = []
    masks: dict[str, np.ndarray] = {}
    glyph_dir = ROOT / "glyph_masks"
    glyph_dir.mkdir(exist_ok=True)
    glyph_index = 0
    unmapped = 0
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_color = rgb_from_int(int(span.get("color", 0)))
                for char in span.get("chars", []):
                    ch = char.get("c", "")
                    if not ch or ch.isspace():
                        continue
                    rect = fitz.Rect(char["bbox"])
                    center = ((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)
                    if not STANDALONE_PT.contains(fitz.Point(*center)):
                        continue
                    parent = parent_for_char(*center)
                    if parent == "UNMAPPED_TEXT_PARENT":
                        unmapped += 1
                    glyph_index += 1
                    obj_id = f"G{glyph_index:04d}"
                    full_box = pt_to_full_px(rect)
                    local_box = full_to_standalone(full_box)
                    x0, y0, x1, y1 = local_box
                    cx0, cy0 = max(0, x0), max(0, y0)
                    cx1, cy1 = min(standalone.width, x1), min(standalone.height, y1)
                    patch = standalone_arr[cy0:cy1, cx0:cx1]
                    tight = target_mask_from_patch(patch, span_color)
                    # Adjacent PDF character bboxes often share one raster
                    # column after floor/ceil conversion.  Assign each pixel by
                    # its physical center to exactly one half-open PDF bbox so
                    # the CHAR-to-mask mapping remains one-to-one.
                    page_x_centers_pt = (
                        np.arange(cx0, cx1, dtype=np.float64) + STANDALONE_CROP_PX[0] + 0.5
                    ) / SCALE
                    page_y_centers_pt = (
                        np.arange(cy0, cy1, dtype=np.float64) + STANDALONE_CROP_PX[1] + 0.5
                    ) / SCALE
                    ownership = (
                        (page_x_centers_pt[None, :] >= rect.x0)
                        & (page_x_centers_pt[None, :] < rect.x1)
                        & (page_y_centers_pt[:, None] >= rect.y0)
                        & (page_y_centers_pt[:, None] < rect.y1)
                    )
                    tight &= ownership
                    global_mask = np.zeros(mask_shape, dtype=bool)
                    global_mask[cy0:cy1, cx0:cx1] = tight
                    masks[obj_id] = global_mask
                    ib = ink_bbox(tight)
                    if ib is None:
                        h_ink = 0
                        w_ink = 0
                        area = 0
                    else:
                        w_ink = ib[2] - ib[0]
                        h_ink = ib[3] - ib[1]
                        area = int(np.count_nonzero(tight))
                    cls, threshold = char_class(ch, float(span["size"]), parent)
                    safe_name = f"{obj_id}__{safe_char(ch)}.png"
                    Image.fromarray(np.where(tight, 0, 255).astype(np.uint8), "L").save(glyph_dir / safe_name)
                    row = {
                        "object_id": obj_id,
                        "safe_filename": f"glyph_masks/{safe_name}",
                        "char": ch,
                        "codepoint": f"U+{ord(ch):04X}",
                        "unicode_name": unicodedata.name(ch, "UNKNOWN"),
                        "parent_id": parent,
                        "font": span.get("font", ""),
                        "declared_pdf_pt": round(float(span["size"]), 3),
                        "char_class": cls,
                        "r168_reference_threshold_px": threshold,
                        "bbox_x0_pt": round(rect.x0, 3),
                        "bbox_y0_pt": round(rect.y0, 3),
                        "bbox_x1_pt": round(rect.x1, 3),
                        "bbox_y1_pt": round(rect.y1, 3),
                        "bbox_x0_px": x0,
                        "bbox_y0_px": y0,
                        "bbox_x1_px": x1,
                        "bbox_y1_px": y1,
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "ink_area_px": area,
                        "foreign_color_candidate_px": int(np.count_nonzero((np.max(np.abs(patch.astype(int) - 255), axis=2) >= 20) & ~tight)),
                    }
                    glyph_rows.append(row)
                    object_rows.append(
                        {
                            "object_id": obj_id,
                            "object_type": "TEXT_GLYPH",
                            "parent_id": parent,
                            "source_index": glyph_index,
                            "bbox_x0_px": x0,
                            "bbox_y0_px": y0,
                            "bbox_x1_px": x1,
                            "bbox_y1_px": y1,
                            "mask_pixel_count": area,
                            "safe_filename": f"glyph_masks/{safe_name}",
                        }
                    )

    drawing_rows: list[dict] = []
    drawing_dir = ROOT / "drawing_masks"
    drawing_dir.mkdir(exist_ok=True)
    for index, drawing in enumerate(drawings):
        rect = fitz.Rect(drawing["rect"])
        width = float(drawing.get("width", 0.0) or 0.0)
        expanded = fitz.Rect(
            rect.x0 - max(0.5, width), rect.y0 - max(0.5, width),
            rect.x1 + max(0.5, width), rect.y1 + max(0.5, width),
        )
        if not expanded.intersects(STANDALONE_PT):
            continue
        obj_type, parent = drawing_class(index)
        if obj_type == "UNCLASSIFIED_DRAWING":
            raise RuntimeError(f"Unclassified in-scope drawing {index}: {rect}")
        obj_id = f"D{index:04d}"
        mask = reconstruct_drawing_mask(page.rect, drawing, STANDALONE_PT)
        if mask.shape != mask_shape:
            raise RuntimeError(f"Drawing mask shape mismatch for {obj_id}: {mask.shape} != {mask_shape}")
        masks[obj_id] = mask
        ib = ink_bbox(mask)
        if ib is None:
            # A visible in-scope path with an empty independent mask is never
            # silently discarded.  Preserve it for the machine integrity gate.
            local_box = full_to_standalone(pt_to_full_px(rect))
        else:
            local_box = ib
        safe_name = f"{obj_id}__{obj_type}.png"
        Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(drawing_dir / safe_name)
        endpoints = []
        for item in drawing.get("items", []):
            if item[0] == "l":
                endpoints.append([round(item[1].x, 3), round(item[1].y, 3)])
                endpoints.append([round(item[2].x, 3), round(item[2].y, 3)])
            elif item[0] == "c":
                endpoints.append([round(item[1].x, 3), round(item[1].y, 3)])
                endpoints.append([round(item[4].x, 3), round(item[4].y, 3)])
            elif item[0] == "re":
                r = item[1]
                endpoints.extend([[round(r.x0, 3), round(r.y0, 3)], [round(r.x1, 3), round(r.y1, 3)]])
        row = {
            "object_id": obj_id,
            "object_type": obj_type,
            "parent_id": parent,
            "source_index": index,
            "sequence_number": drawing.get("seqno"),
            "pdf_rect_pt": json.dumps(rect_tuple(rect), ensure_ascii=False),
            "bbox_x0_px": int(local_box[0]),
            "bbox_y0_px": int(local_box[1]),
            "bbox_x1_px": int(local_box[2]),
            "bbox_y1_px": int(local_box[3]),
            "mask_pixel_count": int(np.count_nonzero(mask)),
            "stroke_rgb": json.dumps(color_to_rgb(drawing.get("color"))),
            "fill_rgb": json.dumps(color_to_rgb(drawing.get("fill"))),
            "width_pt": drawing.get("width"),
            "dash_pattern": str(drawing.get("dashes") or ""),
            "endpoints_pt": json.dumps(endpoints),
            "safe_filename": f"drawing_masks/{safe_name}",
        }
        drawing_rows.append(row)
        object_rows.append(row.copy())

    # PyMuPDF does not expose the tiling-pattern hatch as page drawing paths.
    # Add one semantic foreground object per visible hatch region, using pixels
    # directly from the official Poppler raster.  These two objects close the
    # PDF foreground denominator without inventing per-stroke path identities.
    hatch_specs = [
        ("H0001", "HATCH_UPPER", (189.176, 253.454, 251.798, 309.253)),
        ("H0002", "HATCH_LOWER", (189.176, 340.433, 251.798, 396.234)),
    ]
    for obj_id, parent, pt_box in hatch_specs:
        rect = fitz.Rect(*pt_box)
        local_box = full_to_standalone(pt_to_full_px(rect))
        x0, y0, x1, y1 = local_box
        patch = standalone_arr[y0:y1, x0:x1]
        # Hatching/pattern foreground is blue-grey; keep pixels that are visibly
        # non-white but exclude gold dividers and dark blue curve/markers.
        r, g, b = patch[:, :, 0], patch[:, :, 1], patch[:, :, 2]
        local = (np.max(np.abs(patch.astype(int) - 255), axis=2) >= 20) & (b >= r) & (g >= r) & (r >= 150)
        mask = global_mask_from_tight(mask_shape, local_box, local)
        masks[obj_id] = mask
        safe_name = f"{obj_id}__HATCH_PATTERN.png"
        Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(drawing_dir / safe_name)
        row = {
            "object_id": obj_id,
            "object_type": "HATCH_PATTERN",
            "parent_id": parent,
            "source_index": "SOURCE_PATTERN_GROUP",
            "sequence_number": "NOT_EXPOSED_BY_GET_DRAWINGS",
            "pdf_rect_pt": json.dumps(list(pt_box)),
            "bbox_x0_px": x0,
            "bbox_y0_px": y0,
            "bbox_x1_px": x1,
            "bbox_y1_px": y1,
            "mask_pixel_count": int(np.count_nonzero(mask)),
            "stroke_rgb": json.dumps([184, 192, 200]),
            "fill_rgb": "null",
            "width_pt": "PATTERN",
            "dash_pattern": "TILING_PATTERN",
            "endpoints_pt": "[]",
            "safe_filename": f"drawing_masks/{safe_name}",
        }
        drawing_rows.append(row)
        object_rows.append(row.copy())

    if unmapped:
        raise RuntimeError(f"Unmapped text-parent assignments: {unmapped}")

    pair_rows = []
    critical_rows = []
    for pair_index, (a, b) in enumerate(itertools.combinations(object_rows, 2), 1):
        a_id, b_id = a["object_id"], b["object_id"]
        a_box = tuple(int(a[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
        b_box = tuple(int(b[k]) for k in ("bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px"))
        bgap = bbox_gap(a_box, b_box)
        same_parent = a["parent_id"] == b["parent_id"]
        pair_class = f"{a['object_type']}--{b['object_type']}"
        intersection = ""
        raw_clearance = ""
        metric_kind = "BBOX_LOWER_BOUND"
        if bgap <= 48.0:
            inter, clearance = mask_distance(masks[a_id], masks[b_id])
            intersection = inter
            raw_clearance = "" if clearance is None else round(clearance, 3)
            metric_kind = "SEPARATED_RAW_MASKS"
        row = {
            "pair_id": f"P{pair_index:06d}",
            "object_a": a_id,
            "object_b": b_id,
            "type_a": a["object_type"],
            "type_b": b["object_type"],
            "parent_a": a["parent_id"],
            "parent_b": b["parent_id"],
            "same_semantic_parent_int": int(same_parent),
            "pair_class": pair_class,
            "bbox_gap_px": round(bgap, 3),
            "raw_intersection_px": intersection,
            "raw_clearance_px": raw_clearance,
            "metric_kind": metric_kind,
        }
        pair_rows.append(row)
        if bgap <= 16.0 or (intersection not in ("", 0)):
            critical_rows.append(row.copy())

    contact_map = make_contact_sheets(standalone, glyph_rows, masks)
    rule_map = make_math_rule_sheet(standalone, drawing_rows, masks)
    make_overlay(standalone, glyph_rows, drawing_rows)
    critical_rois = make_counterevidence(full)

    glyph_fields = [
        "object_id", "safe_filename", "char", "codepoint", "unicode_name", "parent_id", "font",
        "declared_pdf_pt", "char_class", "r168_reference_threshold_px", "bbox_x0_pt", "bbox_y0_pt",
        "bbox_x1_pt", "bbox_y1_pt", "bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px",
        "h_ink_px", "w_ink_px", "ink_area_px", "foreign_color_candidate_px",
    ]
    object_fields = [
        "object_id", "object_type", "parent_id", "source_index", "sequence_number", "pdf_rect_pt",
        "bbox_x0_px", "bbox_y0_px", "bbox_x1_px", "bbox_y1_px", "mask_pixel_count", "stroke_rgb",
        "fill_rgb", "width_pt", "dash_pattern", "endpoints_pt", "safe_filename",
    ]
    drawing_fields = object_fields
    pair_fields = [
        "pair_id", "object_a", "object_b", "type_a", "type_b", "parent_a", "parent_b",
        "same_semantic_parent_int", "pair_class", "bbox_gap_px", "raw_intersection_px",
        "raw_clearance_px", "metric_kind",
    ]
    write_csv(ROOT / "after_pixel_measurements.csv", glyph_fields, glyph_rows)
    write_csv(ROOT / "object_manifest.csv", object_fields, object_rows)
    write_csv(ROOT / "drawing_path_ledger.csv", drawing_fields, drawing_rows)
    write_csv(ROOT / "all_unordered_pairs.csv", pair_fields, pair_rows)
    write_csv(ROOT / "critical_pair_candidates.csv", pair_fields, critical_rows)
    write_csv(ROOT / "glyph_contact_map.csv", ["object_id", "sheet", "cell"], contact_map)
    write_csv(ROOT / "math_rule_contact_map.csv", ["object_id", "sheet", "cell"], rule_map)

    source_text = SOURCE.read_text(encoding="utf-8")
    semantic = source_semantic_check(source_text)
    write_json(ROOT / "semantic_recomputation.json", semantic)

    object_counts = Counter(r["object_type"] for r in object_rows)
    parent_counts = Counter(r["parent_id"] for r in object_rows)
    drawing_index_set = sorted(
        int(r["source_index"]) for r in drawing_rows if isinstance(r["source_index"], int)
    )
    inventory = {
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": pdf_hash,
        "official_pdf_pages": len(doc),
        "physical_page": PAGE_NUMBER,
        "page_box_pt": rect_tuple(page.rect),
        "native_200dpi_grid_px": [1654, 2339],
        "native_300dpi_grid_px": list(full.size),
        "figure_crop_page_px": list(FIGURE_CROP_PX),
        "figure_crop_native_dimensions_px": list(full.crop(FIGURE_CROP_PX).size),
        "standalone_crop_page_px": list(STANDALONE_CROP_PX),
        "standalone_native_dimensions_px": list(standalone.size),
        "grayscale_crop_page_px": list(FIGURE_CROP_PX),
        "grayscale_native_dimensions_px": list(gray.crop(FIGURE_CROP_PX).size),
        "text_glyph_count": len(glyph_rows),
        "drawing_path_count": len(drawing_rows),
        "math_rule_count": sum(r["object_type"] == "MATH_RULE" for r in drawing_rows),
        "hatch_pattern_group_count": 2,
        "total_object_denominator": len(object_rows),
        "unordered_pair_denominator": len(pair_rows),
        "expected_unordered_pair_denominator": len(object_rows) * (len(object_rows) - 1) // 2,
        "critical_pair_candidate_count": len(critical_rows),
        "object_counts": dict(sorted(object_counts.items())),
        "parent_counts": dict(sorted(parent_counts.items())),
        "in_scope_pdf_drawing_indices": drawing_index_set,
        "in_scope_pdf_drawing_index_count": len(drawing_index_set),
        "page_get_drawings_total": len(drawings),
        "contact_sheet_count": len({r["sheet"] for r in contact_map}),
        "glyph_contact_row_count": len(contact_map),
        "math_rule_contact_row_count": len(rule_map),
        "critical_roi_count": len(critical_rois),
        "empty_glyph_mask_count": sum(r["ink_area_px"] == 0 for r in glyph_rows),
        "empty_drawing_mask_count": sum(r["mask_pixel_count"] == 0 for r in drawing_rows),
        "source_file": str(SOURCE),
        "source_file_sha256": sha256(SOURCE),
    }
    write_json(ROOT / "candidate_inventory.json", inventory)
    doc.close()


if __name__ == "__main__":
    main()
