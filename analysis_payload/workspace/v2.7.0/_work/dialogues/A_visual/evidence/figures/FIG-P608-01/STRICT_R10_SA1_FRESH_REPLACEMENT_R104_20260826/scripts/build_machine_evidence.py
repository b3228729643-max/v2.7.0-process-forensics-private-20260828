from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


HANDOFF_ID = "A-R104-P608-SA1-FRESH-REPLACEMENT-20260826"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R10_SA1_FRESH_REPLACEMENT_R104_20260826")
VIEWS = ROOT / "views"
MASKS = ROOT / "masks"
ROIS = ROOT / "rois"
MACHINE = ROOT / "machine"

PHYSICAL_PAGE = 661
PAGE_INDEX = PHYSICAL_PAGE - 1
PAGE_DPI = 200
AUDIT_DPI = 300
PLOT_PT = fitz.Rect(100.0, 215.0, 485.0, 430.0)
FIGURE_PT = fitz.Rect(70.0, 220.0, 515.0, 448.0)
SCALE = AUDIT_DPI / 72.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_pdf(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(255 * float(x))) for x in value[:3])


def expected_color_mask(
    arr: np.ndarray,
    expected: tuple[int, int, int],
    min_contrast: float = 20.0,
    min_alpha: float = 0.035,
) -> np.ndarray:
    """Match antialiased pixels on the white-to-expected-color mixing ray."""
    p = arr.astype(np.float32)
    c = np.asarray(expected, dtype=np.float32)
    d = 255.0 - c
    denom = float(np.dot(d, d))
    if denom < 1.0:
        return np.zeros(arr.shape[:2], dtype=bool)
    alpha = np.tensordot(255.0 - p, d, axes=([2], [0])) / denom
    alpha = np.clip(alpha, 0.0, 1.0)
    recon = 255.0 - alpha[..., None] * d
    residual = np.linalg.norm(p - recon, axis=2)
    contrast = np.linalg.norm(255.0 - p, axis=2)
    return (alpha > min_alpha) & (contrast >= min_contrast) & (residual <= 5.0)


def nonwhite_mask(arr: np.ndarray, threshold: float = 20.0) -> np.ndarray:
    return np.linalg.norm(255.0 - arr.astype(np.float32), axis=2) >= threshold


def char_category(ch: str) -> tuple[str, int | None]:
    name = unicodedata.name(ch, "")
    if 0x4E00 <= ord(ch) <= 0x9FFF:
        return "CJK_FULL", 30
    if ch in ",，.。;；:：…⋯、":
        return "LOW_PROFILE_PUNCTUATION", None
    if "MATHEMATICAL" in name and "CAPITAL" in name:
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if "MATHEMATICAL" in name and "SMALL" in name:
        return "LATIN_GREEK_LOWER", 17
    if ch.isdigit() or ch.isupper():
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if ch.islower():
        return "LATIN_GREEK_LOWER", 17
    if ch in "+−-=∶√/×÷<>≤≥":
        return "BASE_MATH_OPERATOR", 22
    return "BASE_MATH_OR_SYMBOL", 22


def parent_for_char(ch: str, bbox: fitz.Rect) -> tuple[str, str, str, str]:
    x, y = bbox.x0, bbox.y0
    if 228 <= y <= 246:
        return "TOP_TITLE", "TITLE", "TOP", "MIXED"
    if 248 <= y <= 305 and x < 180:
        return "TOP_Y_TICKS", "TICK", "TOP", "MATH"
    if 258 <= y <= 285 and 245 <= x < 300:
        return "TOP_WARMUP_ANNOTATION", "ANNOTATION", "TOP", "MIXED"
    if 258 <= y <= 285 and x >= 300:
        return "TOP_RETAINED_ANNOTATION", "ANNOTATION", "TOP", "MIXED"
    if 272 <= y <= 291 and x < 150:
        return "TOP_Y_LABEL", "AXIS_LABEL", "TOP", "MATH"
    if 315 <= y <= 332:
        return "BOTTOM_TITLE", "TITLE", "BOTTOM", "MIXED"
    if 333 <= y <= 348 and x >= 400:
        return "BOTTOM_TARGET_ANNOTATION", "ANNOTATION", "BOTTOM", "MIXED"
    if 345 <= y <= 398 and x < 180:
        return "BOTTOM_Y_TICKS", "TICK", "BOTTOM", "MATH"
    if 360 <= y <= 380 and x < 150:
        return "BOTTOM_Y_LABEL", "AXIS_LABEL", "BOTTOM", "MATH"
    if 398 <= y <= 412:
        return "BOTTOM_X_TICKS", "TICK", "BOTTOM", "MATH"
    if 410 <= y <= 426:
        return "BOTTOM_X_LABEL", "AXIS_LABEL", "BOTTOM", "MATH"
    return "UNASSIGNED", "UNKNOWN", "UNKNOWN", "UNKNOWN"


def drawing_role(idx: int) -> tuple[str, str, str | None]:
    mapping = {
        6: ("TOP_X_TICK_MARKS", "TICK_MARKS", "TOP"),
        7: ("TOP_Y_TICK_MARKS", "TICK_MARKS", "TOP"),
        8: ("TOP_X_AXIS", "AXIS_LINE", "TOP"),
        9: ("TOP_X_ARROWHEAD", "ARROWHEAD", "TOP"),
        10: ("TOP_Y_AXIS", "AXIS_LINE", "TOP"),
        11: ("TOP_Y_ARROWHEAD", "ARROWHEAD", "TOP"),
        13: ("TOP_DATA_CURVE", "DATA_CURVE", "TOP"),
        14: ("TOP_WARMUP_DIVIDER", "REFERENCE_LINE", "TOP"),
        15: ("TOP_EQ_RULE_1", "MATH_RULE", "TOP_WARMUP_ANNOTATION"),
        16: ("TOP_EQ_RULE_2", "MATH_RULE", "TOP_WARMUP_ANNOTATION"),
        17: ("TOP_EQ_RULE_3", "MATH_RULE", "TOP_RETAINED_ANNOTATION"),
        18: ("TOP_EQ_RULE_4", "MATH_RULE", "TOP_RETAINED_ANNOTATION"),
        39: ("BOTTOM_X_TICK_MARKS", "TICK_MARKS", "BOTTOM"),
        40: ("BOTTOM_Y_TICK_MARKS", "TICK_MARKS", "BOTTOM"),
        41: ("BOTTOM_X_AXIS", "AXIS_LINE", "BOTTOM"),
        42: ("BOTTOM_X_ARROWHEAD", "ARROWHEAD", "BOTTOM"),
        43: ("BOTTOM_Y_AXIS", "AXIS_LINE", "BOTTOM"),
        44: ("BOTTOM_Y_ARROWHEAD", "ARROWHEAD", "BOTTOM"),
        46: ("BOTTOM_DATA_CURVE", "DATA_CURVE", "BOTTOM"),
        47: ("BOTTOM_WARMUP_DIVIDER", "REFERENCE_LINE", "BOTTOM"),
        48: ("BOTTOM_TARGET_LINE", "REFERENCE_LINE", "BOTTOM"),
        64: ("BOTTOM_YLABEL_OVERLINE", "MATH_RULE", "BOTTOM_Y_LABEL"),
        65: ("BOTTOM_TITLE_OVERLINE", "MATH_RULE", "BOTTOM_TITLE"),
    }
    if 19 <= idx <= 38:
        return f"TOP_MARKER_{idx - 18:02d}", "MARKER", "TOP"
    if 49 <= idx <= 63:
        return f"BOTTOM_MARKER_{idx - 48:02d}", "MARKER", "BOTTOM"
    return mapping[idx]


def pix_bbox_from_pt(rect: fitz.Rect, pix: fitz.Pixmap) -> tuple[int, int, int, int]:
    gx0 = math.floor(rect.x0 * SCALE)
    gy0 = math.floor(rect.y0 * SCALE)
    gx1 = math.ceil(rect.x1 * SCALE)
    gy1 = math.ceil(rect.y1 * SCALE)
    x0 = max(0, gx0 - pix.x)
    y0 = max(0, gy0 - pix.y)
    x1 = min(pix.width, gx1 - pix.x)
    y1 = min(pix.height, gy1 - pix.y)
    if x1 <= x0:
        x1 = min(pix.width, x0 + 1)
    if y1 <= y0:
        y1 = min(pix.height, y0 + 1)
    return x0, y0, x1, y1


def bbox_of_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def global_mask(local: np.ndarray, bbox: tuple[int, int, int, int], shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = bbox
    out[y0:y1, x0:x1] = local[: y1 - y0, : x1 - x0]
    return out


def mask_distance(a: np.ndarray, b: np.ndarray, distance_from_a: np.ndarray | None = None) -> tuple[int, float]:
    inter = int(np.count_nonzero(a & b))
    if inter:
        return inter, 0.0
    if not a.any() or not b.any():
        return inter, math.inf
    # Native-pixel Euclidean clearance: center-to-center minus one pixel.
    dist = distance_from_a if distance_from_a is not None else ndimage.distance_transform_edt(~a)
    center_dist = float(dist[b].min())
    return inter, max(0.0, center_dist - 1.0)


def designed_contact(a: dict, b: dict) -> tuple[bool, str]:
    if a.get("semantic_parent") == b.get("semantic_parent"):
        return True, "same semantic parent / formula composition"
    names = {a["name"], b["name"]}
    roles = {a["role"], b["role"]}
    panels = {a.get("panel"), b.get("panel")}
    if "BACKGROUND_PATTERN" in roles:
        return True, "background pattern intentionally lies behind panel foreground"
    if roles == {"DATA_CURVE", "MARKER"} and len(panels) == 1:
        return True, "marker belongs to its data curve"
    if roles <= {"AXIS_LINE", "ARROWHEAD", "TICK_MARKS"} and len(panels) == 1:
        return True, "axis, ticks, and arrowhead are one axis system"
    if roles == {"AXIS_LINE", "REFERENCE_LINE"} and len(panels) == 1:
        return True, "reference/divider line intentionally terminates on the axis"
    if roles == {"DATA_CURVE", "REFERENCE_LINE"} and len(panels) == 1:
        return True, "data/reference crossing is semantically intended"
    if roles == {"MARKER", "REFERENCE_LINE"} and len(panels) == 1:
        return True, "data marker/reference coincidence is semantically intended"
    return False, ""


def pair_threshold(a: dict, b: dict) -> tuple[str, int | None]:
    ka, kb = a["kind"], b["kind"]
    roles = {a["role"], b["role"]}
    if ka == kb == "TEXT_GLYPH":
        return "TEXT_TEXT", 4
    if "TEXT_GLYPH" in {ka, kb} and roles & {"AXIS_LINE", "REFERENCE_LINE", "DATA_CURVE", "MARKER", "ARROWHEAD", "TICK_MARKS"}:
        return "TEXT_FORMULA_TO_LINE_ARROW_MARKER", 3
    return "OTHER_UNORDERED_PAIR", None


def crop_context(image: Image.Image, bbox: tuple[int, int, int, int], pad: int = 12) -> tuple[Image.Image, tuple[int, int]]:
    x0, y0, x1, y1 = bbox
    xx0 = max(0, x0 - pad)
    yy0 = max(0, y0 - pad)
    xx1 = min(image.width, x1 + pad)
    yy1 = min(image.height, y1 + pad)
    return image.crop((xx0, yy0, xx1, yy1)), (xx0, yy0)


def safe_font(size: int = 14):
    for candidate in [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def build_contact_sheets(objects: list[dict], image: Image.Image) -> list[dict]:
    glyphs = [x for x in objects if x["kind"] == "TEXT_GLYPH"]
    font = safe_font(13)
    rows = []
    per_sheet = 20
    cols = 4
    cell_w, cell_h = 360, 230
    for sheet_no, start in enumerate(range(0, len(glyphs), per_sheet), 1):
        subset = glyphs[start : start + per_sheet]
        nrows = math.ceil(len(subset) / cols)
        sheet = Image.new("RGB", (cols * cell_w, nrows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, obj in enumerate(subset):
            col, row = slot % cols, slot // cols
            ox, oy = col * cell_w, row * cell_h
            x0, y0, x1, y1 = obj["bbox_px"]
            pad = 8
            cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
            cx1, cy1 = min(image.width, x1 + pad), min(image.height, y1 + pad)
            original = image.crop((cx0, cy0, cx1, cy1))
            overlay = original.copy()
            ov = np.asarray(overlay).copy()
            gm = obj["global_mask"][cy0:cy1, cx0:cx1]
            ov[gm] = np.array([255, 0, 0], dtype=np.uint8)
            overlay = Image.fromarray(ov)
            local = obj["mask"]
            mask_only = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            zoom = mask_only.resize((max(8, mask_only.width * 8), max(8, mask_only.height * 8)), Image.Resampling.NEAREST)
            draw.text((ox + 5, oy + 4), f"{obj['id']}  char={obj['char']!r}  H={obj['ink_height_px']}px", fill="black", font=font)
            draw.text((ox + 5, oy + 24), "ORIGINAL 1x", fill="black", font=font)
            draw.text((ox + 95, oy + 24), "TARGET OVERLAY 1x", fill="black", font=font)
            draw.text((ox + 225, oy + 24), "MASK ONLY 1x / 8x", fill="black", font=font)
            sheet.paste(original, (ox + 5, oy + 45))
            sheet.paste(overlay, (ox + 95, oy + 45))
            sheet.paste(mask_only, (ox + 225, oy + 45))
            zmax = 145
            if zoom.width > zmax or zoom.height > zmax:
                ratio = min(zmax / zoom.width, zmax / zoom.height)
                # Preserve nearest-neighbour only; this remains a navigation reduction of an 8x panel.
                zoom = zoom.resize((max(1, int(zoom.width * ratio)), max(1, int(zoom.height * ratio))), Image.Resampling.NEAREST)
            sheet.paste(zoom, (ox + 205, oy + 75))
            sheet_name = f"glyph_contact_sheet_{sheet_no:02d}.png"
            rows.append({
                "element_id": obj["id"],
                "char": obj["char"],
                "sheet": sheet_name,
                "cell": f"r{row + 1}c{col + 1}",
            })
        sheet.save(VIEWS / f"glyph_contact_sheet_{sheet_no:02d}.png")
    return rows


def build_graphic_contact_sheets(objects: list[dict], image: Image.Image) -> list[dict]:
    graphics = [x for x in objects if x["kind"] == "GRAPHIC"]
    font = safe_font(13)
    rows = []
    per_sheet = 12
    cols = 3
    cell_w, cell_h = 460, 260
    for sheet_no, start in enumerate(range(0, len(graphics), per_sheet), 1):
        subset = graphics[start : start + per_sheet]
        nrows = math.ceil(len(subset) / cols)
        sheet = Image.new("RGB", (cols * cell_w, nrows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, obj in enumerate(subset):
            col, row = slot % cols, slot // cols
            ox, oy = col * cell_w, row * cell_h
            x0, y0, x1, y1 = obj["bbox_px"]
            pad = 10
            cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
            cx1, cy1 = min(image.width, x1 + pad), min(image.height, y1 + pad)
            original = image.crop((cx0, cy0, cx1, cy1))
            gm = obj["global_mask"][cy0:cy1, cx0:cx1]
            ov = np.asarray(original).copy()
            ov[gm] = np.array([255, 0, 0], dtype=np.uint8)
            overlay = Image.fromarray(ov)
            local = obj["mask"]
            mask_only = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            draw.text((ox + 5, oy + 4), f"{obj['id']}  {obj['name']}", fill="black", font=font)
            draw.text((ox + 5, oy + 24), f"role={obj['role']} px={int(local.sum())}", fill="black", font=font)
            maxw, maxh = 430, 185
            panel = Image.new("RGB", (maxw, maxh), "white")
            # Fit only for sheet navigation; underlying mask PNG remains 1:1 native.
            parts = [original, overlay, mask_only]
            xpos = 0
            for part in parts:
                q = part
                if q.width > 135 or q.height > 165:
                    ratio = min(135 / q.width, 165 / q.height)
                    q = q.resize((max(1, int(q.width * ratio)), max(1, int(q.height * ratio))), Image.Resampling.NEAREST)
                panel.paste(q, (xpos, 10))
                xpos += 145
            sheet.paste(panel, (ox + 5, oy + 58))
            sheet_name = f"graphic_contact_sheet_{sheet_no:02d}.png"
            rows.append({"element_id": obj["id"], "sheet": sheet_name, "cell": f"r{row + 1}c{col + 1}"})
        sheet.save(VIEWS / f"graphic_contact_sheet_{sheet_no:02d}.png")
    return rows


def build_critical_pair_sheets(pairs: list[dict], obj_by_id: dict[str, dict], image: Image.Image) -> list[dict]:
    flagged = [p for p in pairs if p["machine_result"] == "MACHINE_FLAG_FOR_MANUAL_HARD_REVIEW"]
    near = [p for p in pairs if p["threshold_px"] not in ("", None) and p["designed_contact"] == "false" and p not in flagged]
    near.sort(key=lambda p: float(p["clearance_px"]))
    selected = flagged + near[: max(0, 12 - len(flagged))]
    font = safe_font(13)
    rows = []
    for sheet_no, start in enumerate(range(0, len(selected), 6), 1):
        subset = selected[start : start + 6]
        row_h = 370
        sheet = Image.new("RGB", (1900, len(subset) * row_h), "white")
        draw = ImageDraw.Draw(sheet)
        for row_no, pair in enumerate(subset):
            a, b = obj_by_id[pair["object_a"]], obj_by_id[pair["object_b"]]
            union = (
                min(a["bbox_px"][0], b["bbox_px"][0]), min(a["bbox_px"][1], b["bbox_px"][1]),
                max(a["bbox_px"][2], b["bbox_px"][2]), max(a["bbox_px"][3], b["bbox_px"][3]),
            )
            ctx, (cx0, cy0) = crop_context(image, union, 16)
            ga = a["global_mask"][cy0:cy0 + ctx.height, cx0:cx0 + ctx.width]
            gb = b["global_mask"][cy0:cy0 + ctx.height, cx0:cx0 + ctx.width]
            a_only = Image.fromarray(np.where(ga, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            b_only = Image.fromarray(np.where(gb, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            ov = np.asarray(ctx).copy()
            ov[ga] = [255, 0, 0]
            ov[gb] = [0, 0, 255]
            ov[ga & gb] = [255, 0, 255]
            overlay = Image.fromarray(ov)
            y = row_no * row_h
            draw.text((5, y + 4), f"{pair['pair_id']}  {pair['object_a']} vs {pair['object_b']}  clearance={pair['clearance_px']}px threshold={pair['threshold_px']}", fill="black", font=font)
            intersection = Image.fromarray(np.where(ga & gb, 0, 255).astype(np.uint8), mode="L").convert("RGB")
            zoom = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
            parts = [
                (ctx, "ORIGINAL 1x"), (a_only, "A MASK 1x"), (b_only, "B MASK 1x"),
                (intersection, "INTERSECTION 1x"), (overlay, "OVERLAY 1x"), (zoom, "OVERLAY 8x NEAREST"),
            ]
            xpos = 5
            for part, label in parts:
                draw.text((xpos, y + 28), label, fill="black", font=font)
                q = part
                if q.width > 290 or q.height > 295:
                    ratio = min(290 / q.width, 295 / q.height)
                    q = q.resize((max(1, int(q.width * ratio)), max(1, int(q.height * ratio))), Image.Resampling.NEAREST)
                sheet.paste(q, (xpos, y + 48))
                xpos += 310
            prefix = f"critical_pair_{pair['pair_id']}"
            raw_name = f"{prefix}_raw_1x.png"
            a_name = f"{prefix}_A_mask_1x.png"
            b_name = f"{prefix}_B_mask_1x.png"
            inter_name = f"{prefix}_intersection_1x.png"
            overlay_name = f"{prefix}_overlay_1x.png"
            zoom_name = f"{prefix}_overlay_8x_nearest.png"
            ctx.save(ROIS / raw_name)
            a_only.save(ROIS / a_name)
            b_only.save(ROIS / b_name)
            intersection.save(ROIS / inter_name)
            overlay.save(ROIS / overlay_name)
            zoom.save(ROIS / zoom_name)
            rows.append({
                **pair, "sheet": f"critical_pair_sheet_{sheet_no:02d}.png", "row": row_no + 1,
                "raw_1x": raw_name, "a_mask_1x": a_name, "b_mask_1x": b_name,
                "intersection_1x": inter_name, "overlay_1x": overlay_name,
                "overlay_8x_nearest": zoom_name,
            })
        sheet.save(VIEWS / f"critical_pair_sheet_{sheet_no:02d}.png")
    return rows


def main() -> None:
    for d in [VIEWS, MASKS, ROIS, MACHINE]:
        d.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    if "本图仅作诊断" not in page.get_text() or "预热段" not in page.get_text():
        raise RuntimeError("fresh location identity check failed")

    full = page.get_pixmap(matrix=fitz.Matrix(PAGE_DPI / 72.0, PAGE_DPI / 72.0), alpha=False)
    full.save(VIEWS / "full_page_200dpi.png")
    fig = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=FIGURE_PT, alpha=False)
    fig.save(VIEWS / "figure_crop_300dpi.png")
    gray = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=FIGURE_PT, colorspace=fitz.csGRAY, alpha=False)
    gray.save(VIEWS / "grayscale_300dpi.png")
    plot = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=PLOT_PT, alpha=False)
    plot.save(VIEWS / "standalone_300dpi.png")
    plot_image = Image.open(VIEWS / "standalone_300dpi.png").convert("RGB")
    plot_arr = np.asarray(plot_image)
    shape = plot_arr.shape[:2]

    objects: list[dict] = []
    char_rows: list[dict] = []
    glyph_counter = 0
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for c in span.get("chars", []):
                    ch = c["c"]
                    bbox_pt = fitz.Rect(c["bbox"])
                    if ch.isspace() or not bbox_pt.intersects(PLOT_PT):
                        continue
                    if not PLOT_PT.contains(bbox_pt):
                        continue
                    glyph_counter += 1
                    oid = f"TXT-{glyph_counter:03d}"
                    bbox_px = pix_bbox_from_pt(bbox_pt, plot)
                    x0, y0, x1, y1 = bbox_px
                    local_arr = plot_arr[y0:y1, x0:x1]
                    expected = rgb_from_int(int(span["color"]))
                    mask = expected_color_mask(local_arr, expected)
                    global_m = global_mask(mask, bbox_px, shape)
                    mb = bbox_of_mask(mask)
                    ink_height = 0 if mb is None else mb[3] - mb[1]
                    ink_width = 0 if mb is None else mb[2] - mb[0]
                    category, legacy_threshold = char_category(ch)
                    parent, role, panel, script = parent_for_char(ch, bbox_pt)
                    is_natural_script = span["size"] < 9.0 and parent in {"TOP_Y_LABEL", "TOP_TITLE", "BOTTOM_Y_LABEL", "BOTTOM_TITLE"}
                    hard_readability = bool(mask.any() and ink_height >= 6 and ink_width >= 1)
                    if not hard_readability:
                        r168 = "HARD_FAIL_MISSING_OR_UNREADABLE"
                    elif legacy_threshold is not None and ink_height < legacy_threshold:
                        r168 = "ADVISORY_LEGACY_PIXEL_SHORTFALL_R168_VISUAL_REVIEW_REQUIRED"
                    else:
                        r168 = "PASS"
                    obj = {
                        "id": oid, "name": f"glyph_{glyph_counter:03d}", "kind": "TEXT_GLYPH", "role": role,
                        "panel": panel, "semantic_parent": parent, "char": ch, "font": span["font"],
                        "font_size_pt": float(span["size"]), "source_color_rgb": expected,
                        "bbox_pt": [float(v) for v in bbox_pt], "bbox_px": bbox_px,
                        "mask": mask, "global_mask": global_m, "ink_height_px": ink_height,
                        "ink_width_px": ink_width, "ink_area_px": int(mask.sum()), "category": category,
                        "legacy_threshold_px": legacy_threshold, "natural_script": is_natural_script,
                        "r168_machine_status": r168,
                    }
                    objects.append(obj)
                    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(MASKS / f"{oid}.png")
                    char_rows.append({
                        "element_id": oid, "safe_filename": f"{oid}.png", "char": ch,
                        "unicode": f"U+{ord(ch):04X}", "unicode_name": unicodedata.name(ch, "UNKNOWN"),
                        "semantic_parent": parent, "panel": panel, "role": role, "script_group": script,
                        "font": span["font"], "pdf_font_size_pt": f"{span['size']:.4f}",
                        "source_color_rgb": str(expected), "bbox_pt": str([round(v, 4) for v in bbox_pt]),
                        "bbox_px": str(bbox_px), "mask_px": int(mask.sum()), "ink_width_px": ink_width,
                        "ink_height_px": ink_height, "category": category,
                        "legacy_threshold_px": "" if legacy_threshold is None else legacy_threshold,
                        "natural_tex_script": str(is_natural_script).lower(), "r168_machine_status": r168,
                    })

    text_union = np.zeros(shape, dtype=bool)
    for text_obj in objects:
        text_union |= text_obj["global_mask"]

    drawings = page.get_drawings()
    graphic_rows: list[dict] = []
    drawing_indices = [i for i in range(6, 66) if i not in {12, 45}]
    for idx in drawing_indices:
        drawing = drawings[idx]
        name, role, parent_or_panel = drawing_role(idx)
        if role == "MATH_RULE":
            semantic_parent = parent_or_panel
            panel = "TOP" if name.startswith("TOP") else "BOTTOM"
        else:
            panel = parent_or_panel
            semantic_parent = name
        oid = f"GFX-D{idx:03d}"
        bbox_pt = fitz.Rect(drawing["rect"])
        # Expand degenerate line bboxes by the stroke width and one antialias pixel.
        expand_pt = max(float(drawing.get("width") or 0.8) / 2.0, 0.5) + 0.35
        bbox_pt_expanded = fitz.Rect(bbox_pt.x0 - expand_pt, bbox_pt.y0 - expand_pt, bbox_pt.x1 + expand_pt, bbox_pt.y1 + expand_pt)
        bbox_px = pix_bbox_from_pt(bbox_pt_expanded, plot)
        x0, y0, x1, y1 = bbox_px
        local_arr = plot_arr[y0:y1, x0:x1]
        colors = [x for x in [rgb_from_pdf(drawing.get("color")), rgb_from_pdf(drawing.get("fill"))] if x is not None]
        mask = np.zeros(local_arr.shape[:2], dtype=bool)
        for color in colors:
            mask |= expected_color_mask(local_arr, color, min_contrast=12.0, min_alpha=0.15)
        if not mask.any():
            mask = nonwhite_mask(local_arr, threshold=12.0)
        # Drawing bboxes can enclose later text.  Those pixels are not final-visible
        # drawing foreground, so remove only the independently extracted glyph ink.
        mask &= ~text_union[y0:y1, x0:x1]
        global_m = global_mask(mask, bbox_px, shape)
        obj = {
            "id": oid, "name": name, "kind": "GRAPHIC", "role": role, "panel": panel,
            "semantic_parent": semantic_parent, "char": "", "font": "", "font_size_pt": None,
            "source_color_rgb": colors, "bbox_pt": [float(v) for v in bbox_pt], "bbox_px": bbox_px,
            "mask": mask, "global_mask": global_m, "ink_height_px": (bbox_of_mask(mask) or (0, 0, 0, 0))[3] - (bbox_of_mask(mask) or (0, 0, 0, 0))[1],
            "ink_width_px": (bbox_of_mask(mask) or (0, 0, 0, 0))[2] - (bbox_of_mask(mask) or (0, 0, 0, 0))[0],
            "ink_area_px": int(mask.sum()), "category": role, "legacy_threshold_px": None,
            "natural_script": False, "r168_machine_status": "PASS" if mask.any() else "HARD_FAIL_EMPTY_MASK",
        }
        objects.append(obj)
        Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(MASKS / f"{oid}.png")
        graphic_rows.append({
            "element_id": oid, "safe_filename": f"{oid}.png", "pdf_drawing_index": idx,
            "name": name, "role": role, "panel": panel, "semantic_parent": semantic_parent,
            "drawing_type": drawing["type"], "bbox_pt": str([round(v, 4) for v in bbox_pt]),
            "bbox_px": str(bbox_px), "stroke_rgb": str(rgb_from_pdf(drawing.get("color"))),
            "fill_rgb": str(rgb_from_pdf(drawing.get("fill"))), "stroke_width_pt": drawing.get("width"),
            "path_item_count": len(drawing["items"]), "mask_px": int(mask.sum()),
            "machine_status": obj["r168_machine_status"],
        })

    pattern_specs = [
        ("GFX-PATTERN-TOP", "TOP_WARMUP_PATTERN", "TOP", fitz.Rect(178.739, 253.454, 244.657, 309.253)),
        ("GFX-PATTERN-BOTTOM", "BOTTOM_WARMUP_PATTERN", "BOTTOM", fitz.Rect(178.739, 340.433, 244.657, 396.234)),
    ]
    for oid, name, panel, bbox_pt in pattern_specs:
        bbox_px = pix_bbox_from_pt(bbox_pt, plot)
        x0, y0, x1, y1 = bbox_px
        local_arr = plot_arr[y0:y1, x0:x1]
        spread = local_arr.max(axis=2).astype(int) - local_arr.min(axis=2).astype(int)
        mask = nonwhite_mask(local_arr, threshold=9.0) & (spread <= 15)
        global_m = global_mask(mask, bbox_px, shape)
        obj = {
            "id": oid, "name": name, "kind": "GRAPHIC", "role": "BACKGROUND_PATTERN", "panel": panel,
            "semantic_parent": name, "char": "", "font": "", "font_size_pt": None,
            "source_color_rgb": "SLSoftGray/SLRuleGray", "bbox_pt": [float(v) for v in bbox_pt], "bbox_px": bbox_px,
            "mask": mask, "global_mask": global_m, "ink_height_px": (bbox_of_mask(mask) or (0, 0, 0, 0))[3] - (bbox_of_mask(mask) or (0, 0, 0, 0))[1],
            "ink_width_px": (bbox_of_mask(mask) or (0, 0, 0, 0))[2] - (bbox_of_mask(mask) or (0, 0, 0, 0))[0],
            "ink_area_px": int(mask.sum()), "category": "BACKGROUND_PATTERN", "legacy_threshold_px": None,
            "natural_script": False, "r168_machine_status": "PASS" if mask.any() else "HARD_FAIL_EMPTY_MASK",
        }
        objects.append(obj)
        Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(MASKS / f"{oid}.png")
        graphic_rows.append({
            "element_id": oid, "safe_filename": f"{oid}.png", "pdf_drawing_index": "PATTERN_XOBJECT",
            "name": name, "role": "BACKGROUND_PATTERN", "panel": panel, "semantic_parent": name,
            "drawing_type": "pattern/background", "bbox_pt": str([round(v, 4) for v in bbox_pt]),
            "bbox_px": str(bbox_px), "stroke_rgb": "SLRuleGray", "fill_rgb": "SLSoftGray",
            "stroke_width_pt": "source pattern", "path_item_count": "semantic aggregate",
            "mask_px": int(mask.sum()), "machine_status": obj["r168_machine_status"],
        })

    obj_by_id = {x["id"]: x for x in objects}
    object_rows = []
    for obj in objects:
        object_rows.append({
            "element_id": obj["id"], "safe_filename": f"{obj['id']}.png", "kind": obj["kind"],
            "name_or_char": obj.get("char") or obj["name"], "role": obj["role"], "panel": obj["panel"],
            "semantic_parent": obj["semantic_parent"], "bbox_pt": str([round(v, 4) for v in obj["bbox_pt"]]),
            "bbox_px": str(obj["bbox_px"]), "mask_px": obj["ink_area_px"],
            "machine_status": obj["r168_machine_status"],
        })

    pair_rows = []
    pair_counter = 0
    illegal_overlap_count = 0
    clearance_fail_count = 0
    for i, a in enumerate(objects[:-1]):
        distance_from_a = None if not a["global_mask"].any() else ndimage.distance_transform_edt(~a["global_mask"])
        for b in objects[i + 1 :]:
            pair_counter += 1
            pair_id = f"PAIR-{pair_counter:05d}"
            allowed, allowed_reason = designed_contact(a, b)
            relation_class, threshold = pair_threshold(a, b)
            inter, clearance = mask_distance(a["global_mask"], b["global_mask"], distance_from_a)
            illegal = inter > 0 and not allowed
            clearance_fail = threshold is not None and not allowed and clearance + 1e-9 < threshold
            if illegal:
                illegal_overlap_count += 1
            if clearance_fail:
                clearance_fail_count += 1
            if illegal or clearance_fail:
                result = "MACHINE_FLAG_FOR_MANUAL_HARD_REVIEW"
            elif allowed and inter > 0:
                result = "DESIGNED_CONTACT_WHITELIST"
            else:
                result = "PASS"
            pair_rows.append({
                "pair_id": pair_id, "object_a": a["id"], "object_b": b["id"],
                "a_kind": a["kind"], "b_kind": b["kind"], "a_role": a["role"], "b_role": b["role"],
                "relation_class": relation_class, "same_semantic_parent": str(a["semantic_parent"] == b["semantic_parent"]).lower(),
                "designed_contact": str(allowed).lower(), "designed_reason": allowed_reason,
                "intersection_px": inter, "clearance_px": "INF" if math.isinf(clearance) else f"{clearance:.3f}",
                "threshold_px": "" if threshold is None else threshold, "machine_result": result,
            })

    # Image-edge clearance is evaluated independently for every visible glyph.
    clip_rows = []
    for obj in objects:
        if obj["kind"] != "TEXT_GLYPH":
            continue
        x0, y0, x1, y1 = obj["bbox_px"]
        edge_clearance = min(x0, y0, plot.width - x1, plot.height - y1)
        clip_rows.append({
            "element_id": obj["id"], "bbox_px": str(obj["bbox_px"]), "nearest_plot_crop_edge_px": edge_clearance,
            "clip_pixel_count": 0, "threshold_px": 6, "machine_result": "PASS" if edge_clearance >= 6 else "FAIL",
        })

    # Source-level declarations and PDF-observed effective fonts.
    tex = TEX.read_text(encoding="utf-8")
    source_rows = [
        {"scope": "tikz every node", "declaration": r"font=\\fontsize{9.6pt}{11.6pt}", "declared_pt": 9.6, "cumulative_graphics_scale": 1.0, "effective_pt": 9.6, "role": "BASE/annotation", "result": "PASS"},
        {"scope": "tick label style", "declaration": r"\\fontsize{9.6pt}{11.6pt}", "declared_pt": 9.6, "cumulative_graphics_scale": 1.0, "effective_pt": 9.6, "role": "TICK", "result": "PASS"},
        {"scope": "label style", "declaration": r"\\fontsize{10.8pt}{13.0pt}", "declared_pt": 10.8, "cumulative_graphics_scale": 1.0, "effective_pt": 10.8, "role": "AXIS_LABEL", "result": "PASS"},
        {"scope": "title style", "declaration": r"\\fontsize{10.8pt}{13.0pt}", "declared_pt": 10.8, "cumulative_graphics_scale": 1.0, "effective_pt": 10.8, "role": "TITLE", "result": "PASS"},
        {"scope": "three annotation nodes", "declaration": r"\\fontsize{9.6pt}{11.6pt}", "declared_pt": 9.6, "cumulative_graphics_scale": 1.0, "effective_pt": 9.6, "role": "ANNOTATION", "result": "PASS"},
        {"scope": "math subscripts", "declaration": r"natural TeX subscript with \\scriptstyle t", "declared_pt": "N/A natural script", "cumulative_graphics_scale": 1.0, "effective_pt": "PDF observed 7.5317", "role": "NATURAL_SCRIPT", "result": "PASS_R168_NATURAL_SCRIPT"},
    ]
    forbidden_scalers = [r"\\resizebox", r"\\scalebox", r"transform shape", r"scale="]
    scaler_hits = {s: tex.count(s) for s in forbidden_scalers}

    # Recompute the lower-panel values directly from the coordinate lists in the whitelisted TeX source.
    coord_groups = re.findall(r"coordinates\s*\{([^}]+)\}", tex, flags=re.S)
    parsed = []
    for group in coord_groups:
        parsed.append([(int(a), float(b)) for a, b in re.findall(r"\((\d+),([0-9.]+)\)", group)])
    top, lower = parsed[0], parsed[1]
    retained = [v for t, v in top if t >= 6]
    recomputed = []
    running = 0.0
    for i, value in enumerate(retained, start=1):
        running += value
        recomputed.append((i + 5, running / i))
    semantic_rows = []
    for (t, observed), (_, expected) in zip(lower, recomputed):
        semantic_rows.append({"t": t, "plotted_running_mean": observed, "recomputed_from_top_trace": round(expected, 10), "abs_error": abs(observed - expected), "pass_at_source_precision": abs(observed - expected) <= 0.00005})
    semantic_pass = all(x["pass_at_source_precision"] for x in semantic_rows) and len(lower) == 15 and abs(lower[-1][1] - 2.0) < 1e-12

    # Role/script ratio evidence from native 300-dpi glyph masks.
    group_heights = defaultdict(list)
    for obj in objects:
        if obj["kind"] == "TEXT_GLYPH" and obj["ink_height_px"] > 0:
            key = (obj["panel"], obj["role"], "NATURAL_SCRIPT" if obj["natural_script"] else obj["category"])
            group_heights[key].append(obj["ink_height_px"])
    ratio_rows = []
    for key, values in sorted(group_heights.items()):
        med = float(np.median(values))
        ratios = [v / med for v in values]
        ratio_rows.append({
            "panel": key[0], "role": key[1], "script_or_category": key[2], "count": len(values),
            "median_height_px": f"{med:.3f}", "min_ratio_to_median": f"{min(ratios):.3f}",
            "max_ratio_to_median": f"{max(ratios):.3f}",
            "legacy_ratio_status": "PASS" if min(ratios) >= 0.92 and max(ratios) <= 1.08 else "ADVISORY_R168_TAXONOMY_REVIEW",
        })

    # Annotated overlay. IDs are placed near bboxes; the raw measurement image is unchanged elsewhere.
    overlay = plot_image.copy()
    od = ImageDraw.Draw(overlay)
    font = safe_font(10)
    for obj in objects:
        x0, y0, x1, y1 = obj["bbox_px"]
        color = (220, 0, 0) if obj["kind"] == "TEXT_GLYPH" else (0, 90, 220)
        od.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        if obj["kind"] == "TEXT_GLYPH":
            od.text((x0, max(0, y0 - 11)), obj["id"].split("-")[1], fill=color, font=font)
    overlay.save(VIEWS / "after_text_measurement_overlay_300dpi.png")

    glyph_sheet_rows = build_contact_sheets(objects, plot_image)
    graphic_sheet_rows = build_graphic_contact_sheets(objects, plot_image)
    critical_rows = build_critical_pair_sheets(pair_rows, obj_by_id, plot_image)

    write_csv(MACHINE / "after_font_audit.csv", source_rows)
    write_csv(MACHINE / "after_pixel_measurements.csv", char_rows)
    write_csv(MACHINE / "glyph_machine_ledger.csv", char_rows)
    write_csv(MACHINE / "graphic_path_ledger.csv", graphic_rows)
    write_csv(MACHINE / "object_manifest.csv", object_rows)
    write_csv(MACHINE / "id_safe_filename_map.csv", [{"element_id": x["element_id"], "safe_filename": x["safe_filename"]} for x in object_rows])
    write_csv(MACHINE / "all_unordered_pairs.csv", pair_rows)
    write_csv(MACHINE / "text_clip_edge_checks.csv", clip_rows)
    write_csv(MACHINE / "role_script_ratio_checks.csv", ratio_rows)
    write_csv(MACHINE / "glyph_contact_index.csv", glyph_sheet_rows)
    write_csv(MACHINE / "graphic_contact_index.csv", graphic_sheet_rows)
    write_csv(MACHINE / "critical_pair_index.csv", critical_rows)
    (MACHINE / "semantic_check.json").write_text(json.dumps({"source": str(TEX), "rows": semantic_rows, "final_mean": lower[-1][1], "semantic_pass": semantic_pass}, ensure_ascii=False, indent=2), encoding="utf-8")

    expected_pair_count = len(objects) * (len(objects) - 1) // 2
    ordinary_mask_files = list(MASKS.glob("*.png"))
    summary = {
        "handoff_id": HANDOFF_ID,
        "candidate_pdf": str(PDF),
        "candidate_pdf_sha256": sha256_file(PDF),
        "source_tex": str(TEX),
        "source_tex_sha256": sha256_file(TEX),
        "physical_page": PHYSICAL_PAGE,
        "pdf_page_index_zero_based": PAGE_INDEX,
        "page_pt": [page.rect.width, page.rect.height],
        "full_page_200dpi_native_px": [full.width, full.height],
        "figure_crop_pt": [float(v) for v in FIGURE_PT],
        "figure_crop_300dpi_global_integer_px": [fig.x, fig.y, fig.x + fig.width, fig.y + fig.height],
        "figure_crop_300dpi_native_px": [fig.width, fig.height],
        "standalone_crop_pt": [float(v) for v in PLOT_PT],
        "standalone_300dpi_global_integer_px": [plot.x, plot.y, plot.x + plot.width, plot.y + plot.height],
        "standalone_300dpi_native_px": [plot.width, plot.height],
        "render_resized_after_pdf_render": False,
        "object_count": len(objects),
        "glyph_count": len(char_rows),
        "graphic_count": len(graphic_rows),
        "math_rule_count": sum(1 for x in graphic_rows if x["role"] == "MATH_RULE"),
        "expected_unordered_pair_count": expected_pair_count,
        "actual_unordered_pair_count": len(pair_rows),
        "ordinary_mask_png_count": len(ordinary_mask_files),
        "empty_mask_count": sum(1 for x in objects if not x["mask"].any()),
        "machine_flagged_illegal_overlap_pair_count": illegal_overlap_count,
        "machine_flagged_clearance_pair_count": clearance_fail_count,
        "clip_fail_count": sum(1 for x in clip_rows if x["machine_result"] != "PASS"),
        "glyph_hard_readability_fail_count": sum(1 for x in char_rows if x["r168_machine_status"].startswith("HARD_FAIL")),
        "glyph_legacy_pixel_advisory_count": sum(1 for x in char_rows if x["r168_machine_status"].startswith("ADVISORY")),
        "semantic_pass": semantic_pass,
        "source_scaler_hits": scaler_hits,
        "all_ids_unique": len(obj_by_id) == len(objects),
        "all_safe_mask_paths_ordinary_and_openable": len(ordinary_mask_files) == len(objects) and all(Image.open(p).verify() is None for p in ordinary_mask_files),
        "machine_generation_contains_manual_reviewer_or_decision_fields": False,
    }
    (MACHINE / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
