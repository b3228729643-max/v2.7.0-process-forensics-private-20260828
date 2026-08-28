from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_acceptance_function.tex")
PAGE_INDEX = 654
PAGE_NUMBER = PAGE_INDEX + 1
SCALE_300 = 300.0 / 72.0
FIGURE_CLIP_PT = (60.0, 504.0, 524.0, 689.0)
STANDALONE_CLIP_PT = (109.0, 504.0, 475.0, 657.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_float(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(v) * 255)) for v in value)


def pt_rect_to_px(rect) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * SCALE_300)),
        int(math.floor(y0 * SCALE_300)),
        int(math.ceil(x1 * SCALE_300)),
        int(math.ceil(y1 * SCALE_300)),
    )


def clamp_rect(rect, width: int, height: int, pad: int = 0):
    x0, y0, x1, y1 = rect
    return (
        max(0, x0 - pad),
        max(0, y0 - pad),
        min(width, x1 + pad),
        min(height, y1 + pad),
    )


def estimate_background(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return np.array([255.0, 255.0, 255.0])
    if min(arr.shape[:2]) < 3:
        vals = arr.reshape(-1, 3)
    else:
        vals = np.concatenate(
            [arr[0], arr[-1], arr[1:-1, 0], arr[1:-1, -1]], axis=0
        )
    quant = (vals // 4) * 4
    key = Counter(map(tuple, quant.tolist())).most_common(1)[0][0]
    near = vals[np.all(np.abs(quant.astype(int) - np.array(key)) <= 3, axis=1)]
    return np.median(near if len(near) else vals, axis=0)


def color_mask(
    full_arr: np.ndarray,
    rect_px,
    target_rgb,
    *,
    pad: int = 1,
    min_contrast: float = 20.0,
    perpendicular_tolerance: float = 24.0,
):
    height, width = full_arr.shape[:2]
    rect = clamp_rect(rect_px, width, height, pad=pad)
    x0, y0, x1, y1 = rect
    arr = full_arr[y0:y1, x0:x1].astype(np.float64)
    bg = estimate_background(arr)
    target = np.array(target_rgb, dtype=np.float64)
    vector = bg - target
    denom = float(np.dot(vector, vector))
    if denom < 1.0:
        return rect, np.zeros(arr.shape[:2], dtype=bool), bg
    delta = bg - arr
    projection = np.einsum("...i,i->...", delta, vector) / denom
    reconstruction = bg - projection[..., None] * vector
    perpendicular = np.linalg.norm(arr - reconstruction, axis=2)
    contrast = np.linalg.norm(delta, axis=2)
    mask = (
        (projection >= 0.055)
        & (projection <= 1.45)
        & (perpendicular <= perpendicular_tolerance)
        & (contrast >= min_contrast)
    )
    return rect, mask, bg


def cubic_points(p0, p1, p2, p3, steps=32):
    points = []
    for t in np.linspace(0.0, 1.0, steps):
        u = 1.0 - t
        x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
        points.append((x, y))
    return points


def geometry_corridor(drawing, rect_px, *, fill_geometry: bool = False):
    """Rasterize a narrow vector-coordinate corridor; it is only a selector.

    The returned mask is intersected with the actual official-PDF RGB pixels, so
    measurements remain on native rendered pixels rather than this rasterization.
    """
    x0, y0, x1, y1 = rect_px
    corridor = Image.new("L", (x1 - x0, y1 - y0), 0)
    draw = ImageDraw.Draw(corridor)
    width = max(3, int(math.ceil(float(drawing.get("width") or 0.8) * SCALE_300)) + 4)

    def xy(point):
        return (point.x * SCALE_300 - x0, point.y * SCALE_300 - y0)

    subpaths = []
    current = []
    for item in drawing["items"]:
        if item[0] == "l":
            a, b = item[1], item[2]
            if not current:
                current.append(xy(a))
            elif current[-1] != xy(a):
                subpaths.append(current)
                current = [xy(a)]
            current.append(xy(b))
        elif item[0] == "c":
            p0, p1, p2, p3 = item[1], item[2], item[3], item[4]
            pts = [xy(fitz.Point(x, y)) for x, y in cubic_points(p0, p1, p2, p3)]
            if not current:
                current.extend(pts)
            else:
                current.extend(pts[1:])
        elif item[0] == "re":
            r = item[1]
            pts = [xy(fitz.Point(r.x0, r.y0)), xy(fitz.Point(r.x1, r.y0)), xy(fitz.Point(r.x1, r.y1)), xy(fitz.Point(r.x0, r.y1))]
            subpaths.append(pts + [pts[0]])
    if current:
        subpaths.append(current)
    for points in subpaths:
        if len(points) < 2:
            continue
        if fill_geometry:
            draw.polygon(points, fill=255)
        else:
            draw.line(points, fill=255, width=width, joint="curve")
    return np.asarray(corridor) > 0


def ink_bbox(mask: np.ndarray, rect_px):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    x0, y0, _, _ = rect_px
    return (
        int(x0 + xs.min()),
        int(y0 + ys.min()),
        int(x0 + xs.max() + 1),
        int(y0 + ys.max() + 1),
    )


def save_mask(mask: np.ndarray, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def safe_font(size=18):
    for candidate in [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


FONT = safe_font(18)
FONT_SMALL = safe_font(14)


def label_image(draw: ImageDraw.ImageDraw, xy, text, fill=(0, 0, 0), font=FONT):
    draw.text(xy, text, fill=fill, font=font)


def make_object_evidence(
    full_image: Image.Image,
    rect_px,
    mask: np.ndarray,
    object_id: str,
    label: str,
    output: Path,
):
    x0, y0, x1, y1 = rect_px
    context = clamp_rect((x0, y0, x1, y1), full_image.width, full_image.height, pad=10)
    cx0, cy0, cx1, cy1 = context
    original = full_image.crop(context)
    local_mask = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
    ox0, oy0 = x0 - cx0, y0 - cy0
    local_mask[oy0 : oy0 + mask.shape[0], ox0 : ox0 + mask.shape[1]] = mask
    overlay = np.asarray(original).copy()
    overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
    overlay_im = Image.fromarray(overlay)
    mask_im = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    nearest = overlay_im.resize((overlay_im.width * 8, overlay_im.height * 8), Image.Resampling.NEAREST)

    canvas = Image.new("RGB", (1740, 500), "white")
    d = ImageDraw.Draw(canvas)
    label_image(d, (15, 7), f"{object_id} | {label}")
    panels = [
        ("ORIGINAL native 1x", original, 15, 45, 300, 400),
        ("TARGET OVERLAY native 1x", overlay_im, 335, 45, 300, 400),
        ("MASK ONLY native 1x", mask_im, 655, 45, 300, 400),
        ("TARGET OVERLAY 8x nearest", nearest, 975, 45, 745, 400),
    ]
    for title, image, px, py, pw, ph in panels:
        label_image(d, (px, py), title, font=FONT_SMALL)
        box = (px, py + 25, px + pw, py + 25 + ph)
        d.rectangle(box, outline="black", width=1)
        if title.endswith("8x nearest"):
            show = image.crop((0, 0, min(image.width, pw - 4), min(image.height, ph - 4)))
        else:
            show = image
        dx = px + 2 + max(0, (pw - 4 - show.width) // 2)
        dy = py + 27 + max(0, (ph - 4 - show.height) // 2)
        canvas.paste(show, (dx, dy))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def make_contact_sheets(evidence_files: list[Path], target_dir: Path, prefix: str):
    target_dir.mkdir(parents=True, exist_ok=True)
    sheets = []
    for sheet_no, start in enumerate(range(0, len(evidence_files), 10), 1):
        batch = evidence_files[start : start + 10]
        sheet = Image.new("RGB", (3480, 2500), (232, 232, 232))
        for idx, file in enumerate(batch):
            im = Image.open(file).convert("RGB")
            x = (idx % 2) * 1740
            y = (idx // 2) * 500
            sheet.paste(im, (x, y))
        out = target_dir / f"{prefix}_{sheet_no:02d}.png"
        sheet.save(out)
        sheets.append(out)
    return sheets


def make_pair_contact_sheets(evidence_files: list[Path], target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for sheet_no, start in enumerate(range(0, len(evidence_files), 4), 1):
        batch = evidence_files[start : start + 4]
        sheet = Image.new("RGB", (3400, 1860), (232, 232, 232))
        for idx, file in enumerate(batch):
            im = Image.open(file).convert("RGB")
            x = (idx % 2) * 1700
            y = (idx // 2) * 930
            sheet.paste(im, (x, y))
        out = target_dir / f"critical_pair_contact_sheet_{sheet_no:02d}.png"
        sheet.save(out)
        outputs.append(out)
    return outputs


def classify_char(ch: str) -> str:
    cp = ord(ch)
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
        return "CJK_FULL_HEIGHT"
    if ch in ".,;:，、：；…":
        return "LOW_PROFILE_PUNCTUATION"
    if ch in "<>=≤≥+-−/":
        return "MATH_OPERATOR"
    if ch.isdigit() or (ch.isascii() and ch.isupper()):
        return "LATIN_UPPER_OR_DIGIT"
    if ch in "()[]{}":
        return "DELIMITER"
    return "MATH_OR_LOWERCASE"


def char_group(index: int):
    if 1 <= index <= 9:
        return "PLOT_TICKS", "TICK_LABEL", "source:16", "plot"
    if 10 <= index <= 18:
        return "ANNOTATION_R_LT_1", "ANNOTATION", "source:23", "plot"
    if 19 <= index <= 26:
        return "ANNOTATION_R_GE_1", "ANNOTATION", "source:24", "plot"
    if 27 <= index <= 28:
        return "ANNOTATION_KINK", "ANNOTATION", "source:25", "plot"
    if index == 29:
        return "AXIS_TITLE_X", "AXIS_TITLE", "source:14", "plot"
    if 30 <= index <= 35:
        return "AXIS_TITLE_Y", "AXIS_TITLE", "source:15", "plot"
    if 36 <= index <= 57:
        return "FORMULA_RATIO_GENERAL", "FORMULA", "source:29", "formula_card"
    if 58 <= index <= 72:
        return "FORMULA_RATIO_INDEPENDENT", "FORMULA", "source:30", "formula_card"
    return "CAPTION_FIG32_6", "CAPTION", "source:32", "caption"


def render_and_inventory():
    document = fitz.open(PDF)
    page = document[PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(dpi=300, colorspace=fitz.csRGB, alpha=False)
    full300 = Image.frombytes("RGB", (pix300.width, pix300.height), pix300.samples)
    full300.save(ROOT / "full_page_300dpi.png", dpi=(300, 300))
    pix200 = page.get_pixmap(dpi=200, colorspace=fitz.csRGB, alpha=False)
    full200 = Image.frombytes("RGB", (pix200.width, pix200.height), pix200.samples)
    full200.save(ROOT / "full_page_200dpi.png", dpi=(200, 200))
    figure_px = pt_rect_to_px(FIGURE_CLIP_PT)
    standalone_px = pt_rect_to_px(STANDALONE_CLIP_PT)
    figure = full300.crop(figure_px)
    standalone = full300.crop(standalone_px)
    figure.save(ROOT / "figure_crop_300dpi.png", dpi=(300, 300))
    standalone.save(ROOT / "standalone_300dpi.png", dpi=(300, 300))
    figure.convert("L").save(ROOT / "grayscale_300dpi.png", dpi=(300, 300))
    standalone.convert("L").save(ROOT / "standalone_grayscale_300dpi.png", dpi=(300, 300))
    full_arr = np.asarray(full300)

    raw = page.get_text(
        "rawdict",
        flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE,
    )
    chars = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    bbox = ch["bbox"]
                    if bbox[1] >= 505 and bbox[3] <= 689 and ch["c"].strip():
                        chars.append((ch, span, line))

    objects = []
    object_masks = {}
    glyph_evidence = []
    glyph_rows = []
    for idx, (ch, span, line) in enumerate(chars, 1):
        object_id = f"GLYPH-{idx:03d}"
        safe = object_id.replace("-", "_")
        bbox_pt = tuple(float(v) for v in ch["bbox"])
        bbox_px = pt_rect_to_px(bbox_pt)
        target = rgb_from_int(int(span["color"]))
        # The PDF character bbox is the ownership boundary. Do not pad glyph
        # masks, because padding would copy adjacent same-colour antialias ink.
        rect_px, mask, bg = color_mask(full_arr, bbox_px, target, pad=0)
        ibox = ink_bbox(mask, rect_px)
        mask_path = ROOT / "glyph_masks" / f"{safe}.png"
        save_mask(mask, mask_path)
        evidence_path = ROOT / "glyph_evidence" / f"{safe}.png"
        make_object_evidence(full300, rect_px, mask, object_id, ch["c"], evidence_path)
        glyph_evidence.append(evidence_path)
        parent, role, source_line, panel = char_group(idx)
        h_ink = 0 if ibox is None else ibox[3] - ibox[1]
        w_ink = 0 if ibox is None else ibox[2] - ibox[0]
        row = {
            "object_id": object_id,
            "safe_filename": safe,
            "object_type": "GLYPH",
            "char": ch["c"],
            "codepoint": f"U+{ord(ch['c']):04X}",
            "semantic_parent": parent,
            "panel_id": panel,
            "role": role,
            "script_class": classify_char(ch["c"]),
            "source_line": source_line,
            "pdf_bbox_pt": [round(v, 4) for v in bbox_pt],
            "mask_rect_px": list(rect_px),
            "ink_bbox_px": list(ibox) if ibox else None,
            "span_size_pt": round(float(span["size"]), 4),
            "font": span["font"],
            "target_rgb": list(target),
            "estimated_background_rgb": [round(float(v), 2) for v in bg],
            "mask_pixel_count": int(mask.sum()),
            "h_ink_px": int(h_ink),
            "w_ink_px": int(w_ink),
            "mask_empty": bool(not mask.any()),
            "mask_path": mask_path.relative_to(ROOT).as_posix(),
            "evidence_path": evidence_path.relative_to(ROOT).as_posix(),
            "pair_scope": "foreground",
        }
        objects.append(row)
        glyph_rows.append(row)
        object_masks[object_id] = (rect_px, mask)

    # PDF character boxes can overlap fractionally at kerning boundaries. Assign
    # every native foreground pixel to exactly one glyph (nearest bbox centre),
    # preventing duplicated ownership without deleting any visible ink.
    claims = {}
    for row in glyph_rows:
        rect_px, mask = object_masks[row["object_id"]]
        ys, xs = np.nonzero(mask)
        for yy, xx in zip(ys.tolist(), xs.tolist()):
            claims.setdefault((rect_px[0] + xx, rect_px[1] + yy), []).append(row["object_id"])
    centers = {
        row["object_id"]: (
            (row["mask_rect_px"][0] + row["mask_rect_px"][2]) / 2.0,
            (row["mask_rect_px"][1] + row["mask_rect_px"][3]) / 2.0,
        )
        for row in glyph_rows
    }
    for (gx, gy), owners in claims.items():
        if len(owners) <= 1:
            continue
        winner = min(owners, key=lambda oid: (centers[oid][0] - gx) ** 2 + (centers[oid][1] - gy) ** 2)
        for oid in owners:
            if oid == winner:
                continue
            rect_px, mask = object_masks[oid]
            mask[gy - rect_px[1], gx - rect_px[0]] = False
    for row in glyph_rows:
        rect_px, mask = object_masks[row["object_id"]]
        ibox = ink_bbox(mask, rect_px)
        row["ink_bbox_px"] = list(ibox) if ibox else None
        row["mask_pixel_count"] = int(mask.sum())
        row["h_ink_px"] = 0 if ibox is None else ibox[3] - ibox[1]
        row["w_ink_px"] = 0 if ibox is None else ibox[2] - ibox[0]
        row["mask_empty"] = bool(not mask.any())
        save_mask(mask, ROOT / row["mask_path"])
        make_object_evidence(
            full300,
            rect_px,
            mask,
            row["object_id"],
            row["char"],
            ROOT / row["evidence_path"],
        )

    drawing_map = [
        ("GRAPHIC-001", 25, "AXIS_TICKS_X", "TICK_MARK", (128, 128, 128), "source:16", "foreground", False),
        ("GRAPHIC-002", 26, "AXIS_TICKS_Y", "TICK_MARK", (128, 128, 128), "source:16", "foreground", False),
        ("GRAPHIC-003", 27, "AXIS_X_SHAFT", "LINE_ARROW", (31, 38, 40), "source:7", "foreground", False),
        ("GRAPHIC-004", 28, "AXIS_X_ARROWHEAD", "ARROWHEAD", (31, 38, 40), "source:7", "foreground", True),
        ("GRAPHIC-005", 29, "AXIS_Y_SHAFT", "LINE_ARROW", (31, 38, 40), "source:7", "foreground", False),
        ("GRAPHIC-006", 30, "AXIS_Y_ARROWHEAD", "ARROWHEAD", (31, 38, 40), "source:7", "foreground", True),
        ("GRAPHIC-007", 38, "PLOT_AREA_FILL", "BACKGROUND_FILL", (239, 243, 246), "source:18", "excluded_background_fill", True),
        ("GRAPHIC-008", 39, "ACCEPTANCE_RISING_CURVE", "DATA_CURVE", (31, 78, 121), "source:19", "foreground", False),
        ("GRAPHIC-009", 40, "ACCEPTANCE_PLATEAU_CURVE", "DATA_CURVE", (31, 78, 121), "source:20", "foreground", False),
        ("GRAPHIC-010", 41, "THRESHOLD_DASHED_GUIDE", "LINE_ARROW", (107, 114, 128), "source:21", "foreground", False),
        ("GRAPHIC-011", 45, "BREAKPOINT_MARKER", "MARKER", (183, 121, 31), "source:22", "foreground", True),
        ("GRAPHIC-012", 49, "FORMULA_CARD_BORDER", "NODE_BORDER", (184, 192, 200), "source:27", "foreground", False),
        ("GRAPHIC-013", 49, "FORMULA_CARD_FILL", "BACKGROUND_FILL", (255, 255, 255), "source:27", "excluded_background_fill", True),
        ("GRAPHIC-014", 52, "GENERAL_RATIO_FRACTION_RULE", "MATH_RULE", (31, 38, 40), "source:29", "foreground", False),
        ("GRAPHIC-015", 54, "INDEPENDENT_RATIO_FRACTION_RULE", "MATH_RULE", (31, 38, 40), "source:30", "foreground", False),
    ]
    drawings = {int(d["seqno"]): d for d in page.get_drawings(extended=True)}
    graphic_evidence = []
    graphic_rows = []
    for object_id, seqno, name, role, target, source_line, scope, fill_geometry in drawing_map:
        drawing = drawings[seqno]
        rect_pt = tuple(float(v) for v in drawing["rect"])
        rect_px0 = pt_rect_to_px(rect_pt)
        if scope == "excluded_background_fill":
            rect_px = clamp_rect(rect_px0, full300.width, full300.height, pad=1)
            mask = np.zeros((rect_px[3] - rect_px[1], rect_px[2] - rect_px[0]), dtype=bool)
            bg = np.array(target, dtype=float)
        else:
            rect_px, mask, bg = color_mask(
                full_arr,
                rect_px0,
                target,
                pad=2,
                min_contrast=12.0,
                perpendicular_tolerance=32.0,
            )
            corridor = geometry_corridor(drawing, rect_px, fill_geometry=fill_geometry)
            mask &= corridor
        ibox = ink_bbox(mask, rect_px)
        safe = object_id.replace("-", "_")
        mask_path = ROOT / "graphic_masks" / f"{safe}.png"
        save_mask(mask, mask_path)
        evidence_path = ROOT / "graphic_evidence" / f"{safe}.png"
        make_object_evidence(full300, rect_px, mask, object_id, name, evidence_path)
        graphic_evidence.append(evidence_path)
        parent = "formula_card" if object_id in {"GRAPHIC-012", "GRAPHIC-013", "GRAPHIC-014", "GRAPHIC-015"} else "plot"
        row = {
            "object_id": object_id,
            "safe_filename": safe,
            "object_type": "GRAPHIC",
            "name": name,
            "semantic_parent": parent,
            "panel_id": parent,
            "role": role,
            "script_class": "N/A",
            "source_line": source_line,
            "pdf_bbox_pt": [round(v, 4) for v in rect_pt],
            "mask_rect_px": list(rect_px),
            "ink_bbox_px": list(ibox) if ibox else None,
            "drawing_seqno": seqno,
            "drawing_type": drawing["type"],
            "drawing_color_rgb": list(rgb_from_float(drawing.get("color"))) if drawing.get("color") is not None else None,
            "drawing_fill_rgb": list(rgb_from_float(drawing.get("fill"))) if drawing.get("fill") is not None else None,
            "drawing_width_pt": drawing.get("width"),
            "target_rgb": list(target),
            "estimated_background_rgb": [round(float(v), 2) for v in bg],
            "mask_pixel_count": int(mask.sum()),
            "mask_empty": bool(not mask.any()),
            "mask_path": mask_path.relative_to(ROOT).as_posix(),
            "evidence_path": evidence_path.relative_to(ROOT).as_posix(),
            "pair_scope": scope,
            "explicit_exclusion_reason": (
                "visible non-semantic background fill; mapped but excluded from foreground collision masks"
                if scope != "foreground"
                else ""
            ),
        }
        objects.append(row)
        graphic_rows.append(row)
        object_masks[object_id] = (rect_px, mask)

    make_contact_sheets(glyph_evidence, ROOT / "glyph_contact_sheets", "glyph_contact_sheet")
    make_contact_sheets(graphic_evidence, ROOT / "graphic_contact_sheets", "graphic_contact_sheet")

    with (ROOT / "machine_object_inventory.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(objects, fh, ensure_ascii=False, indent=2)
    inventory_fields = [
        "object_id", "safe_filename", "object_type", "char", "codepoint", "name",
        "semantic_parent", "panel_id", "role", "script_class", "source_line",
        "pdf_bbox_pt", "mask_rect_px", "ink_bbox_px", "span_size_pt", "font",
        "target_rgb", "estimated_background_rgb", "mask_pixel_count", "h_ink_px",
        "w_ink_px", "mask_empty", "mask_path", "evidence_path", "pair_scope",
        "explicit_exclusion_reason", "drawing_seqno", "drawing_type", "drawing_width_pt",
    ]
    with (ROOT / "machine_object_inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=inventory_fields, extrasaction="ignore")
        writer.writeheader()
        for row in objects:
            cooked = dict(row)
            for key in ["pdf_bbox_pt", "mask_rect_px", "ink_bbox_px", "target_rgb", "estimated_background_rgb"]:
                cooked[key] = json.dumps(cooked.get(key), ensure_ascii=False)
            writer.writerow(cooked)

    # Whole-figure object overlay. It is an annotation-only reviewer navigation aid.
    overlay = full300.crop(figure_px).copy()
    draw = ImageDraw.Draw(overlay)
    fx0, fy0, _, _ = figure_px
    for row in objects:
        bbox = row.get("ink_bbox_px") or row["mask_rect_px"]
        x0, y0, x1, y1 = bbox
        color = (220, 30, 30) if row["object_type"] == "GLYPH" else (20, 90, 220)
        draw.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=color, width=1)
        if row["object_type"] == "GRAPHIC":
            label_image(draw, (x0 - fx0, y0 - fy0), row["object_id"], fill=color, font=FONT_SMALL)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    pair_rows, critical = build_pairs(objects, object_masks, full300)
    with (ROOT / "machine_all_pairs.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(pair_rows[0].keys()))
        writer.writeheader()
        writer.writerows(pair_rows)
    with (ROOT / "machine_all_pairs.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(pair_rows, fh, ensure_ascii=False, indent=2)
    make_pair_contact_sheets(
        [ROOT / row["evidence_path"] for row in critical],
        ROOT / "critical_pair_contact_sheets",
    )

    peer_rows = []
    grouped = {}
    for row in glyph_rows:
        grouped.setdefault((row["semantic_parent"], row["role"], row["script_class"]), []).append(row)
    for group_idx, (key, members) in enumerate(sorted(grouped.items()), 1):
        hs = [m["h_ink_px"] for m in members if m["h_ink_px"] > 0]
        median = float(np.median(hs)) if hs else 0.0
        peer_rows.append({
            "group_id": f"PEER-{group_idx:03d}",
            "semantic_parent": key[0],
            "role": key[1],
            "script_class": key[2],
            "member_ids": "|".join(m["object_id"] for m in members),
            "member_count": len(members),
            "h_ink_median_px": median,
            "h_ink_min_px": min(hs) if hs else 0,
            "h_ink_max_px": max(hs) if hs else 0,
            "max_min_ratio": (max(hs) / min(hs)) if hs and min(hs) > 0 else "N/A",
            "machine_note": "measurement only; R168 peer/proportion differences are advisory unless obviously severe",
        })
    with (ROOT / "machine_peer_role_inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(peer_rows[0].keys()))
        writer.writeheader()
        writer.writerows(peer_rows)

    source_text = SOURCE.read_text(encoding="utf-8")
    source_rows = [
        {"source_lines": "3", "role": "figure default", "declared_pt": "9.2", "graphics_scale": "1", "effective_pt": "9.2", "machine_fact": "fontsize declaration"},
        {"source_lines": "5", "role": "tick labels", "declared_pt": "8.5", "graphics_scale": "1", "effective_pt": "8.5", "machine_fact": "fontsize declaration"},
        {"source_lines": "6", "role": "axis labels", "declared_pt": "9.2", "graphics_scale": "1", "effective_pt": "9.2", "machine_fact": "fontsize declaration"},
        {"source_lines": "10", "role": "TikZ nodes", "declared_pt": "9.2", "graphics_scale": "1", "effective_pt": "9.2", "machine_fact": "fontsize declaration"},
        {"source_lines": "27-30", "role": "formula card", "declared_pt": "9.2", "graphics_scale": "1", "effective_pt": "9.2", "machine_fact": "fontsize declaration"},
        {"source_lines": "all", "role": "graphics transforms", "declared_pt": "N/A", "graphics_scale": "1", "effective_pt": "N/A", "machine_fact": "no resizebox/scalebox/transform shape found"},
    ]
    if any(token in source_text for token in ["\\resizebox", "\\scalebox", "transform shape"]):
        source_rows[-1]["machine_fact"] = "transform token found; inspect source"
    with (ROOT / "machine_source_font_inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(source_rows[0].keys()))
        writer.writeheader()
        writer.writerows(source_rows)

    identity = {
        "handoff_id": "C-FIG-P603-01-R104-SA3-FRESH-ISOLATED-V1",
        "uid": "FIG-P603-01",
        "role": "SA3",
        "pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "page_count": document.page_count,
        "physical_page_1_based": PAGE_NUMBER,
        "page_index_0_based": PAGE_INDEX,
        "printed_page_number": 642,
        "figure_number": "32.6",
        "page_size_pt": [page_rect.width, page_rect.height],
        "page_size_name": "A4",
        "full_page_300dpi_native_px": [pix300.width, pix300.height],
        "full_page_200dpi_native_px": [pix200.width, pix200.height],
        "figure_clip_pt": list(FIGURE_CLIP_PT),
        "figure_crop_300dpi_global_integer_px": list(figure_px),
        "figure_crop_300dpi_native_px": list(figure.size),
        "standalone_clip_pt": list(STANDALONE_CLIP_PT),
        "standalone_300dpi_global_integer_px": list(standalone_px),
        "standalone_300dpi_native_px": list(standalone.size),
        "source": str(SOURCE),
        "tex_execution": "DISABLED",
        "source_writer": "NONE",
        "object_count": len(objects),
        "glyph_count": len(glyph_rows),
        "graphic_object_count": len(graphic_rows),
        "unordered_pair_expected": len(objects) * (len(objects) - 1) // 2,
        "unordered_pair_actual": len(pair_rows),
        "machine_manual_required_pair_count": len(critical),
        "note": "identity and measurements only; no manual PASS/FAIL or decision generated by script",
    }
    with (ROOT / "IDENTITY.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(identity, fh, ensure_ascii=False, indent=2)

    machine_summary = {
        "identity": identity,
        "glyph_empty_mask_count": sum(r["mask_empty"] for r in glyph_rows),
        "graphic_empty_foreground_mask_count": sum(r["mask_empty"] and r["pair_scope"] == "foreground" for r in graphic_rows),
        "pair_count": len(pair_rows),
        "critical_pair_count": len(critical),
        "critical_pair_ids": [r["pair_id"] for r in critical],
        "pair_overlap_nonzero_count": sum(int(r["overlap_px"] or 0) > 0 for r in pair_rows),
        "machine_warning": "all status/decision/reviewer fields are intentionally absent",
    }
    with (ROOT / "machine_summary.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(machine_summary, fh, ensure_ascii=False, indent=2)


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def pair_clearance(mask_a_info, mask_b_info):
    (ar, am), (br, bm) = mask_a_info, mask_b_info
    if not am.any() or not bm.any():
        return 0, None
    x0 = min(ar[0], br[0]) - 1
    y0 = min(ar[1], br[1]) - 1
    x1 = max(ar[2], br[2]) + 1
    y1 = max(ar[3], br[3]) + 1
    aa = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bb = np.zeros_like(aa)
    aa[ar[1] - y0 : ar[3] - y0, ar[0] - x0 : ar[2] - x0] = am
    bb[br[1] - y0 : br[3] - y0, br[0] - x0 : br[2] - x0] = bm
    overlap = int(np.count_nonzero(aa & bb))
    if overlap:
        return overlap, 0.0
    distance = distance_transform_edt(~aa)
    center_distance = float(distance[bb].min())
    return 0, max(0.0, center_distance - 1.0)


def required_clearance(a, b):
    if a["pair_scope"] != "foreground" or b["pair_scope"] != "foreground":
        return 0, "BACKGROUND_EXCLUSION"
    if a["object_type"] == "GLYPH" and b["object_type"] == "GLYPH":
        if a["semantic_parent"] == b["semantic_parent"]:
            return 0, "SAME_SEMANTIC_PARENT_INTERNAL_LAYOUT"
        return 4, "TEXT_TEXT"
    if a["object_type"] == "GRAPHIC" and b["object_type"] == "GRAPHIC":
        return 0, "GRAPHIC_GRAPHIC_GEOMETRY"
    glyph = a if a["object_type"] == "GLYPH" else b
    graphic = b if a["object_type"] == "GLYPH" else a
    if graphic["role"] == "NODE_BORDER":
        return 5, "TEXT_NODE_BORDER"
    if graphic["role"] in {"LINE_ARROW", "ARROWHEAD", "MARKER", "DATA_CURVE", "TICK_MARK", "MATH_RULE"}:
        if graphic["role"] == "MATH_RULE" and glyph["semantic_parent"] in {"FORMULA_RATIO_GENERAL", "FORMULA_RATIO_INDEPENDENT"}:
            return 0, "SAME_FORMULA_DESIGN_RULE"
        return 3, "TEXT_GRAPHIC"
    return 3, "TEXT_GRAPHIC_OTHER"


def make_pair_evidence(full_image, a, b, mask_a_info, mask_b_info, output):
    ar, am = mask_a_info
    br, bm = mask_b_info
    x0 = max(0, min(ar[0], br[0]) - 12)
    y0 = max(0, min(ar[1], br[1]) - 12)
    x1 = min(full_image.width, max(ar[2], br[2]) + 12)
    y1 = min(full_image.height, max(ar[3], br[3]) + 12)
    original = np.asarray(full_image.crop((x0, y0, x1, y1))).copy()
    aa = np.zeros(original.shape[:2], dtype=bool)
    bb = np.zeros_like(aa)
    aa[ar[1] - y0 : ar[3] - y0, ar[0] - x0 : ar[2] - x0] = am
    bb[br[1] - y0 : br[3] - y0, br[0] - x0 : br[2] - x0] = bm
    overlay = original.copy()
    overlay[aa] = [255, 0, 0]
    overlay[bb] = [0, 80, 255]
    overlay[aa & bb] = [255, 0, 255]
    masks = np.full_like(original, 255)
    masks[aa] = [255, 0, 0]
    masks[bb] = [0, 80, 255]
    masks[aa & bb] = [255, 0, 255]
    overlap = np.where(aa & bb, 0, 255).astype(np.uint8)
    overlap_rgb = np.repeat(overlap[..., None], 3, axis=2)
    panels = [Image.fromarray(original), Image.fromarray(overlay), Image.fromarray(masks), Image.fromarray(overlap_rgb)]
    titles = ["ORIGINAL native 1x", "A red / B blue native 1x", "MASK A/B native 1x", "INTERSECTION native 1x"]
    canvas = Image.new("RGB", (1700, 930), "white")
    d = ImageDraw.Draw(canvas)
    label_image(d, (15, 8), f"{a['object_id']} vs {b['object_id']}")
    for i, (title, panel) in enumerate(zip(titles, panels)):
        px = 15 + i * 420
        label_image(d, (px, 40), title, font=FONT_SMALL)
        d.rectangle((px, 65, px + 400, 465), outline="black")
        canvas.paste(panel.crop((0, 0, min(panel.width, 396), min(panel.height, 396))), (px + 2, 67))
    nearest = Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST)
    label_image(d, (15, 490), "OVERLAY 8x nearest (cropped only for display; counts remain native 1x)", font=FONT_SMALL)
    d.rectangle((15, 515, 1685, 915), outline="black")
    canvas.paste(nearest.crop((0, 0, min(nearest.width, 1666), min(nearest.height, 396))), (17, 517))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def build_pairs(objects, object_masks, full_image):
    rows = []
    critical = []
    pair_dir = ROOT / "critical_pair_evidence"
    pair_dir.mkdir(parents=True, exist_ok=True)
    for idx, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        pair_id = f"PAIR-{idx:05d}"
        a_bbox = a.get("ink_bbox_px") or a["mask_rect_px"]
        b_bbox = b.get("ink_bbox_px") or b["mask_rect_px"]
        lower = bbox_gap(a_bbox, b_bbox)
        required, relation = required_clearance(a, b)
        exact = lower <= 40 and a["pair_scope"] == "foreground" and b["pair_scope"] == "foreground"
        if exact:
            overlap, clearance = pair_clearance(object_masks[a["object_id"]], object_masks[b["object_id"]])
        else:
            overlap, clearance = 0, None
        same_parent = a["semantic_parent"] == b["semantic_parent"]
        if a["pair_scope"] != "foreground" or b["pair_scope"] != "foreground":
            machine_scope = "EXCLUDED_BACKGROUND_FILL"
        elif relation in {"SAME_SEMANTIC_PARENT_INTERNAL_LAYOUT", "SAME_FORMULA_DESIGN_RULE", "GRAPHIC_GRAPHIC_GEOMETRY"}:
            machine_scope = "MAPPED_DESIGN_RELATION"
        elif lower > 40:
            machine_scope = "EXCLUDED_BY_BBOX_CLEARANCE_LOWER_BOUND_GT_40PX"
        else:
            machine_scope = "INTERACTION_CANDIDATE_MEASURED"
        manual_required = (
            machine_scope == "INTERACTION_CANDIDATE_MEASURED"
            and (overlap > 0 or (clearance is not None and clearance <= 30.0))
        ) or (
            relation == "GRAPHIC_GRAPHIC_GEOMETRY" and overlap > 0
        )
        evidence = ""
        if manual_required:
            evidence_path = pair_dir / f"{pair_id}.png"
            make_pair_evidence(full_image, a, b, object_masks[a["object_id"]], object_masks[b["object_id"]], evidence_path)
            evidence = evidence_path.relative_to(ROOT).as_posix()
        row = {
            "pair_id": pair_id,
            "object_a": a["object_id"],
            "object_b": b["object_id"],
            "type_a": a["object_type"],
            "type_b": b["object_type"],
            "role_a": a["role"],
            "role_b": b["role"],
            "parent_a": a["semantic_parent"],
            "parent_b": b["semantic_parent"],
            "same_semantic_parent": same_parent,
            "relation_class": relation,
            "required_clearance_px": required,
            "bbox_gap_lower_bound_px": round(lower, 4),
            "exact_mask_measurement_performed": exact,
            "overlap_px": overlap,
            "min_raw_foreground_clearance_px": "" if clearance is None else round(clearance, 4),
            "machine_scope": machine_scope,
            "manual_review_required": manual_required,
            "evidence_path": evidence,
            "machine_note": "measurement/scope only; no human decision",
        }
        rows.append(row)
        if manual_required:
            critical.append(row)
    return rows, critical


if __name__ == "__main__":
    render_and_inventory()
    print(json.dumps({"root": str(ROOT), "status": "MACHINE_BUILD_COMPLETE"}, ensure_ascii=True))
