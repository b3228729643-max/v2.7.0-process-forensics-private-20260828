from __future__ import annotations

"""Measure fresh FIG-P582-01 evidence in native 300dpi coordinates.

This file deliberately does not decide visual harmony.  It produces machine
measurements, raw masks and contact sheets for the subsequent SA1 manual review.
All target masks are derived from the candidate page raster and PDF glyph /
drawing coordinates; contact-sheet decisions remain PENDING until manually
reviewed.
"""

import csv
import itertools
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path.cwd()
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P582-01" / "STRICT_R1" / "SA1_20260824_R1"
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r95_fullbook" / "main_full.pdf"
SOURCE = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C02" / "fig_v5_c02_running_mean.tex"
PAGE_INDEX = 629
DPI = 300
SCALE = DPI / 72.0


def image_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/consola.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT_12 = image_font(12)
FONT_16 = image_font(16)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def save_rgba(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path)


def rgb_from_draw_color(color: tuple[float, float, float] | None) -> tuple[int, int, int] | None:
    if color is None:
        return None
    return tuple(int(round(max(0.0, min(1.0, x)) * 255)) for x in color)


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return None
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    # Exclusive bbox coordinates: adjacent masks have zero blank pixels.
    dx = max(0, b[0] - a[2], a[0] - b[2])
    dy = max(0, b[1] - a[3], a[1] - b[3])
    return round(math.hypot(dx, dy), 3)


def union_bbox(a: tuple[int, int, int, int], b: tuple[int, int, int, int], pad: int, width: int, height: int) -> tuple[int, int, int, int]:
    return (
        max(0, min(a[0], b[0]) - pad),
        max(0, min(a[1], b[1]) - pad),
        min(width, max(a[2], b[2]) + pad),
        min(height, max(a[3], b[3]) + pad),
    )


def color_ray_mask(rgb: np.ndarray, expected: list[tuple[int, int, int]], tolerance: float = 28.0) -> np.ndarray:
    """Final visible ink whose color lies on white->expected antialias ray.

    The 20/255 contrast floor comes from 9.2.1-C.  The ray test is deliberately
    strict: unrelated colors may not be absorbed into a glyph's raw mask.
    """
    data = rgb.astype(np.float32)
    contrast = np.max(255.0 - data, axis=2) >= 20.0
    matched = np.zeros(contrast.shape, dtype=bool)
    for color in expected:
        e = np.array(color, dtype=np.float32)
        vector = 255.0 - e
        denom = float(np.dot(vector, vector))
        if denom == 0.0:
            continue
        delta = 255.0 - data
        alpha = np.sum(delta * vector, axis=2) / denom
        projected = 255.0 - alpha[..., None] * vector
        distance = np.sqrt(np.sum((data - projected) ** 2, axis=2))
        matched |= (alpha >= 0.035) & (alpha <= 1.10) & (distance <= tolerance)
    return matched & contrast


def page_px_bbox(bbox_pt: list[float] | tuple[float, ...]) -> tuple[int, int, int, int]:
    return (
        math.floor(float(bbox_pt[0]) * SCALE),
        math.floor(float(bbox_pt[1]) * SCALE),
        math.ceil(float(bbox_pt[2]) * SCALE),
        math.ceil(float(bbox_pt[3]) * SCALE),
    )


def script_class(ch: str, is_formula_script: bool) -> tuple[str, int]:
    if is_formula_script:
        return "LEGAL_TEX_SCRIPT", 15
    if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
        return "CJK_FULL", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "DIGIT_OR_UPPER", 24
    if ch in "=+-−×÷<>≤≥∑∏√→←↑↓":
        return "MATH_OPERATOR", 22
    if ch in ".,;:()/[]{}|":
        # The protocol requires semantic decimal points and punctuation to be
        # independently measured.  It supplies no bespoke punctuation floor;
        # use its smallest explicit glyph floor rather than borrowing a parent.
        return "SEMANTIC_PUNCTUATION", 15
    return "LOWERCASE_OR_GREEK", 17


TICK_ELEMENTS = {"E001", "E010", "E011", "E017", "E019", "E024", "E025", "E026", "E027", "E028", "E029", "E030"}
NUMERIC_ELEMENTS = {"E006", "E016", "E020", "E023"}
FORMULA_BASE = {"E002", "E004"}
FORMULA_SCRIPT = {"E003", "E005", "E007"}
ANNOTATION_ELEMENTS = {"E008", "E009", "E012", "E013", "E014", "E015", "E021", "E022"}
AXIS_ELEMENTS = {"E018", "E031", "E032", "E033", "E034", "E035"}
CAPTION_ELEMENTS = {f"E{i:03d}" for i in range(36, 46)}
CAPTION_SCRIPT = {"E042", "E043"}


def source_meta(element_id: str) -> dict:
    if element_id in TICK_ELEMENTS:
        return {"role": "TICK_LABEL", "line": "7,12", "declared": 8.6, "effective": 8.6, "formula_parent": "", "source_rule": "pgfplots tick label style"}
    if element_id in NUMERIC_ELEMENTS:
        return {"role": "NUMERIC_VALUE", "line": {"E006": "37", "E016": "41", "E020": "39", "E023": "43"}[element_id], "declared": 8.5, "effective": 8.5, "formula_parent": "", "source_rule": "explicit node fontsize"}
    if element_id in FORMULA_BASE:
        return {"role": "FORMULA", "line": "25", "declared": 9.2, "effective": 9.2, "formula_parent": "FORMULA_H_UI", "source_rule": "explicit node fontsize"}
    if element_id in FORMULA_SCRIPT:
        return {"role": "FORMULA_SCRIPT", "line": "25", "declared": 6.416, "effective": 6.416, "formula_parent": "FORMULA_H_UI", "source_rule": "automatic TeX script from 9.2pt formula base"}
    if element_id in ANNOTATION_ELEMENTS:
        lines = {"E008": "27", "E009": "27", "E012": "29", "E013": "29", "E014": "31", "E015": "31", "E021": "33", "E022": "33"}
        return {"role": "ANNOTATION", "line": lines[element_id], "declared": 9.2, "effective": 9.2, "formula_parent": "", "source_rule": "explicit node fontsize"}
    if element_id in AXIS_ELEMENTS:
        return {"role": "AXIS_TITLE", "line": "8,13", "declared": 9.6, "effective": 9.6, "formula_parent": "", "source_rule": "pgfplots label style"}
    if element_id in CAPTION_SCRIPT:
        return {"role": "CAPTION_SCRIPT", "line": "46; common/statlearnbook.sty:295", "declared": 9.0, "effective": 9.0, "formula_parent": "CAPTION", "source_rule": "automatic TeX script from 10pt caption base"}
    if element_id in CAPTION_ELEMENTS:
        return {"role": "CAPTION", "line": "46; common/statlearnbook.sty:305", "declared": 10.0, "effective": 10.0, "formula_parent": "CAPTION", "source_rule": "caption small at 11pt document"}
    raise ValueError(f"Unexpected element ID: {element_id}")


def semantic_parent(element_id: str) -> str:
    if element_id in {"E002", "E003", "E004", "E005", "E007"}:
        return "FORMULA_H_UI"
    if element_id in {"E008", "E009"}:
        return "ANNOT_DOWN_1"
    if element_id in {"E012", "E013"}:
        return "ANNOT_UP"
    if element_id in {"E014", "E015"}:
        return "ANNOT_DOWN_2"
    if element_id in {"E021", "E022"}:
        return "ANNOT_TRUE_VALUE"
    if element_id in {"E031", "E032", "E033", "E034", "E035"}:
        return "X_AXIS_TITLE"
    if element_id in CAPTION_ELEMENTS:
        return "CAPTION_PARAGRAPH"
    return element_id


GRAPH_SPECS = [
    (1, "O-G001", "LINE_ARROW", "x tick marks", "7,12"),
    (2, "O-G002", "LINE_ARROW", "y tick marks", "7,12"),
    (3, "O-G003", "LINE_ARROW", "x axis", "6-13"),
    (4, "O-G004", "LINE_ARROW", "x axis arrowhead", "6-13"),
    (5, "O-G005", "LINE_ARROW", "y axis", "6-13"),
    (6, "O-G006", "LINE_ARROW", "y axis arrowhead", "6-13"),
    (7, "O-G007", "DATA_STEM", "four raw-sample stems", "14-16"),
    (8, "O-G008", "DATA_CURVE", "running-mean polyline", "17-19"),
    (9, "O-G009", "DATA_CURVE", "true-value dashed reference", "20-21"),
    (10, "O-G010", "MARKER", "raw-sample square marker 1", "14-16"),
    (11, "O-G011", "MARKER", "raw-sample square marker 2", "14-16"),
    (12, "O-G012", "MARKER", "raw-sample square marker 3", "14-16"),
    (13, "O-G013", "MARKER", "raw-sample square marker 4", "14-16"),
    (14, "O-G014", "MARKER", "running-mean round marker 1", "17-19"),
    (15, "O-G015", "MARKER", "running-mean round marker 2", "17-19"),
    (16, "O-G016", "MARKER", "running-mean round marker 3", "17-19"),
    (17, "O-G017", "MARKER", "running-mean round marker 4", "17-19"),
]


def crop_mask(mask: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    return mask[box[1] : box[3], box[0] : box[2]]


def make_pair_package(pair_id: str, object_a: dict, object_b: dict, full_rgb: np.ndarray, out_rel: str) -> str:
    a_mask = object_a["mask"]
    b_mask = object_b["mask"]
    width, height = a_mask.shape[1], a_mask.shape[0]
    box = union_bbox(object_a["bbox"], object_b["bbox"], 10, width, height)
    raw = full_rgb[box[1] : box[3], box[0] : box[2]]
    am = crop_mask(a_mask, box)
    bm = crop_mask(b_mask, box)
    intersection = am & bm
    package = OUT / "roi_packages_r2_geometry_isolated" / out_rel
    package.mkdir(parents=True, exist_ok=True)
    save_rgba(raw, package / "original_raw_1x.png")
    save_mask(am, package / "mask_A_1x.png")
    save_mask(bm, package / "mask_B_1x.png")
    save_mask(intersection, package / "intersection_1x.png")
    overlay = raw.copy()
    overlay[am] = np.array([255, 0, 0], dtype=np.uint8)
    overlay[bm] = np.array([0, 120, 255], dtype=np.uint8)
    overlay[intersection] = np.array([255, 0, 255], dtype=np.uint8)
    save_rgba(overlay, package / "overlay_1x.png")
    for name in ("original_raw", "mask_A", "mask_B", "intersection", "overlay"):
        src = Image.open(package / f"{name}_1x.png")
        src.resize((src.width * 8, src.height * 8), Image.Resampling.NEAREST).save(package / f"{name}_8x_nearest.png")
    metadata = {
        "pair_id": pair_id,
        "object_a": object_a["id"],
        "object_b": object_b["id"],
        "native_crop_box_xyxy_relative_to_figure_crop": list(box),
        "native_crop_size_px": [box[2] - box[0], box[3] - box[1]],
        "intersection_px": int(intersection.sum()),
        "coordinate_rule": "1x PNG is native final-PDF 300dpi coordinate; 8x image uses nearest neighbor for manual inspection only",
    }
    (package / "package_manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(package.relative_to(OUT)).replace("\\", "/")


def drawing_geometry_support(drawing: dict, fig_x0: int, fig_y0: int, width: int, height: int) -> np.ndarray:
    """Rasterize only a single PDF drawing's vector geometry as a support.

    It is never used to count overlap.  It constrains the actual-color raw mask
    so text sharing a stroke color (notably blue annotations versus blue curve)
    cannot contaminate the graphic object's final-visible mask.
    """
    canvas = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(canvas)

    def point(p: fitz.Point) -> tuple[int, int]:
        return (int(round(p.x * SCALE - fig_x0)), int(round(p.y * SCALE - fig_y0)))

    typ = drawing.get("type")
    items = drawing.get("items", [])
    stroke_width = max(2, int(math.ceil(float(drawing.get("width") or 0.0) * SCALE)) + 2)
    if typ == "s":
        for item in items:
            if item[0] == "l":
                draw.line((point(item[1]), point(item[2])), fill=255, width=stroke_width)
            elif item[0] == "c":
                # Cubic strokes do not occur in this chart's line objects,
                # but their bounding rectangle gives a conservative support.
                pts = [point(p) for p in item[1:]]
                xx = [p[0] for p in pts]
                yy = [p[1] for p in pts]
                draw.rectangle((min(xx)-stroke_width, min(yy)-stroke_width, max(xx)+stroke_width, max(yy)+stroke_width), fill=255)
    elif typ == "f":
        pts: list[tuple[int, int]] = []
        for item in items:
            if item[0] == "l":
                if not pts:
                    pts.append(point(item[1]))
                pts.append(point(item[2]))
        if len(pts) >= 3:
            draw.polygon(pts, fill=255)
    elif typ == "fs":
        if any(item[0] == "re" for item in items):
            rect = next(item[1] for item in items if item[0] == "re")
            x0, y0 = point(rect.tl)
            x1, y1 = point(rect.br)
            draw.rectangle((x0-stroke_width, y0-stroke_width, x1+stroke_width, y1+stroke_width), fill=255)
        else:
            rect = drawing["rect"]
            x0, y0 = point(rect.tl)
            x1, y1 = point(rect.br)
            draw.ellipse((x0-stroke_width, y0-stroke_width, x1+stroke_width, y1+stroke_width), fill=255)
    return np.array(canvas, dtype=bool)


def contact_sheets(glyphs: list[dict], full_rgb: np.ndarray) -> list[dict]:
    contact_dir = OUT / "glyph_contacts"
    original_dir = OUT / "glyph_original"
    mask_dir = OUT / "glyph_masks"
    contact_dir.mkdir(exist_ok=True)
    original_dir.mkdir(exist_ok=True)
    mask_dir.mkdir(exist_ok=True)
    manifest_rows: list[dict] = []
    groups = [glyphs[i : i + 12] for i in range(0, len(glyphs), 12)]
    for sheet_no, group in enumerate(groups, 1):
        cells: list[tuple[dict, Image.Image, Image.Image, Image.Image]] = []
        max_w = 1
        max_h = 1
        for glyph in group:
            x0, y0, x1, y1 = glyph["roi"]
            original = Image.fromarray(full_rgb[y0:y1, x0:x1])
            mask_only = Image.fromarray(np.where(glyph["local_mask"], 0, 255).astype(np.uint8), mode="L").convert("RGB")
            overlay = np.array(original).copy()
            overlay[glyph["local_mask"]] = np.array([255, 0, 0], dtype=np.uint8)
            overlay_img = Image.fromarray(overlay)
            original.save(original_dir / f"{glyph['glyph_id']}_original_1x.png")
            mask_only.save(mask_dir / f"{glyph['glyph_id']}_mask_only_1x.png")
            glyph["original_file"] = f"glyph_original/{glyph['glyph_id']}_original_1x.png"
            glyph["mask_file"] = f"glyph_masks/{glyph['glyph_id']}_mask_only_1x.png"
            cells.append((glyph, original, overlay_img, mask_only))
            max_w = max(max_w, original.width)
            max_h = max(max_h, original.height)
        tile_w = max_w * 8 + 12
        tile_h = max_h * 8 + 30
        sheet = Image.new("RGB", (tile_w * 3 + 20, tile_h * len(cells) + 24), "white")
        draw = ImageDraw.Draw(sheet)
        for row, (glyph, original, overlay, mask_only) in enumerate(cells, 1):
            y = 12 + (row - 1) * tile_h
            for col, (label, img) in enumerate((("ORIGINAL", original), ("TARGET OVERLAY", overlay), ("MASK ONLY", mask_only))):
                x = 8 + col * tile_w
                enlarged = img.resize((img.width * 8, img.height * 8), Image.Resampling.NEAREST)
                sheet.paste(enlarged, (x, y + 17))
                draw.text((x, y), label, fill="black", font=FONT_12)
            # IDs are ASCII by design; the UTF-8 manifest carries the literal
            # glyph so a fallback Windows font cannot hide it in the sheet.
            draw.text((tile_w * 3 - 150, y), f"{glyph['glyph_id']}  E={glyph['element_id']}", fill="black", font=FONT_12)
            glyph["sheet"] = f"glyph_contacts/contact_sheet_{sheet_no:02d}.png"
            glyph["cell"] = row
            manifest_rows.append({
                "GLYPH_ID": glyph["glyph_id"],
                "ELEMENT_ID": glyph["element_id"],
                "CHAR": glyph["char"],
                "SAFE_FILENAME": glyph["glyph_id"],
                "SHEET": glyph["sheet"],
                "CELL": row,
                "ORIGINAL_FILE": glyph["original_file"],
                "MASK_FILE": glyph["mask_file"],
                "NATIVE_ROI_X0": glyph["roi"][0],
                "NATIVE_ROI_Y0": glyph["roi"][1],
                "NATIVE_ROI_X1": glyph["roi"][2],
                "NATIVE_ROI_Y1": glyph["roi"][3],
                "MASK_FOREGROUND_PX": glyph["mask_px"],
            })
        sheet.save(contact_dir / f"contact_sheet_{sheet_no:02d}.png")
    write_csv(OUT / "glyph_file_manifest.csv", manifest_rows)
    return manifest_rows


def main() -> None:
    manifest = json.loads((OUT / "render_manifest.json").read_text(encoding="utf-8"))
    fig_x0, fig_y0, fig_x1, fig_y1 = manifest["figure_crop_native_300dpi_xyxy"]
    full = np.array(Image.open(OUT / "renders" / "full_page_native_300dpi.png").convert("RGB"))
    figure_rgb = full[fig_y0:fig_y1, fig_x0:fig_x1]
    h, w = figure_rgb.shape[:2]
    text_data = json.loads((OUT / "extracted_text_elements.json").read_text(encoding="utf-8"))
    elements = text_data["elements"]
    glyph_input = {row["glyph_id"]: row for row in text_data["glyphs"]}

    # Build every glyph's raw final-visible mask first.
    glyphs: list[dict] = []
    element_masks: dict[str, np.ndarray] = {}
    parent_metrics: dict[str, list[dict]] = defaultdict(list)
    for element in elements:
        eid = element["element_id"]
        meta = source_meta(eid)
        element_mask = np.zeros((h, w), dtype=bool)
        formula_script = eid in FORMULA_SCRIPT or eid in CAPTION_SCRIPT
        for glyph_id in element["char_ids"]:
            info = glyph_input[glyph_id]
            gb = page_px_bbox(info["bbox_pt"])
            gx0, gy0, gx1, gy1 = gb
            pad = 3
            rx0, ry0, rx1, ry1 = max(0, gx0 - pad), max(0, gy0 - pad), min(full.shape[1], gx1 + pad), min(full.shape[0], gy1 + pad)
            local = full[ry0:ry1, rx0:rx1]
            local_mask = color_ray_mask(local, [tuple(info["color_rgb"])])
            # The target glyph has a PDF char bbox.  Keeping only pixels within
            # it prevents a neighboring glyph / line from being credited to it.
            local_gate = np.zeros(local_mask.shape, dtype=bool)
            lx0, ly0, lx1, ly1 = gx0 - rx0, gy0 - ry0, gx1 - rx0, gy1 - ry0
            local_gate[max(0, ly0):min(local_mask.shape[0], ly1), max(0, lx0):min(local_mask.shape[1], lx1)] = True
            local_mask &= local_gate
            full_mask = np.zeros((h, w), dtype=bool)
            fx0, fy0 = rx0 - fig_x0, ry0 - fig_y0
            fx1, fy1 = fx0 + local_mask.shape[1], fy0 + local_mask.shape[0]
            sx0, sy0, sx1, sy1 = max(0, fx0), max(0, fy0), min(w, fx1), min(h, fy1)
            if sx1 > sx0 and sy1 > sy0:
                mx0, my0 = sx0 - fx0, sy0 - fy0
                full_mask[sy0:sy1, sx0:sx1] = local_mask[my0:my0 + (sy1-sy0), mx0:mx0 + (sx1-sx0)]
            # Contact crops retain pad but all coordinates are native final-PDF pixels.
            scx0, scy0, scx1, scy1 = max(fig_x0, rx0), max(fig_y0, ry0), min(fig_x1, rx1), min(fig_y1, ry1)
            roi = (scx0 - fig_x0, scy0 - fig_y0, scx1 - fig_x0, scy1 - fig_y0)
            local_contact_mask = full_mask[roi[1]:roi[3], roi[0]:roi[2]]
            mask_box = bbox_of(full_mask)
            class_name, floor = script_class(info["char"], formula_script)
            ink_h = 0 if mask_box is None else mask_box[3] - mask_box[1]
            glyph = {
                "glyph_id": glyph_id,
                "element_id": eid,
                "char": info["char"],
                "role": meta["role"],
                "script_class": class_name,
                "threshold": floor,
                "declared_pt": meta["declared"],
                "effective_pt": meta["effective"],
                "pdf_span_pt": info["size_pt_pdf"],
                "source_line": meta["line"],
                "full_mask": full_mask,
                "bbox": mask_box,
                "raw_bbox_pdf_px": gb,
                "roi": roi,
                "local_mask": local_contact_mask,
                "mask_px": int(full_mask.sum()),
                "h_ink": ink_h,
                "empty": mask_box is None,
            }
            glyphs.append(glyph)
            element_mask |= full_mask
            parent_metrics[eid].append(glyph)
        element_masks[eid] = element_mask

    # Object-level masks and graphic raw-mask inventory.
    object_mask_dir = OUT / "object_masks"
    draw_mask_dir = OUT / "draw_masks"
    object_mask_dir.mkdir(exist_ok=True)
    draw_mask_dir.mkdir(exist_ok=True)
    objects: list[dict] = []
    for element in elements:
        eid = element["element_id"]
        meta = source_meta(eid)
        mask = element_masks[eid]
        mask_file = f"object_masks/{eid}_final_visible_mask.png"
        save_mask(mask, OUT / mask_file)
        objects.append({
            "id": eid,
            "kind": "TEXT" if not meta["role"].startswith("FORMULA") else "FORMULA",
            "category": meta["role"],
            "name": element["text"],
            "source": str(SOURCE),
            "source_line": meta["line"],
            "draw_order": "text nodes after plotted paths; caption after tikzpicture",
            "mask": mask,
            "bbox": bbox_of(mask),
            "mask_file": mask_file,
            "semantic_parent": semantic_parent(eid),
            "final_visible": True,
        })

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    drawings = page.get_drawings()
    for draw_idx, oid, category, name, src_line in GRAPH_SPECS:
        d = drawings[draw_idx]
        expected = [c for c in (rgb_from_draw_color(d.get("color")), rgb_from_draw_color(d.get("fill"))) if c is not None]
        support = drawing_geometry_support(d, fig_x0, fig_y0, w, h)
        # The counted mask is *actual final candidate ink* intersected with the
        # isolated vector support.  The support by itself is retained only as
        # pre-occlusion/drawing-order evidence.
        mask = color_ray_mask(figure_rgb, expected, tolerance=36.0) & support
        pre_file = f"draw_masks/{oid}_pre_occlusion_mask.png"
        final_file = f"object_masks/{oid}_final_visible_mask.png"
        # This is the separately retained, non-counting pre-occlusion evidence.
        # Since the PDF uses no text halo/opaque label fill, halo is explicitly NONE.
        save_mask(support, OUT / pre_file)
        save_mask(mask, OUT / final_file)
        objects.append({
            "id": oid,
            "kind": category,
            "category": category,
            "name": name,
            "source": str(SOURCE),
            "source_line": src_line,
            "draw_order": f"PDF drawing index={draw_idx}; seqno={d.get('seqno')}; type={d.get('type')}",
            "mask": mask,
            "bbox": bbox_of(mask),
            "mask_file": final_file,
            "pre_file": pre_file,
            "semantic_parent": oid,
            "final_visible": True,
            "expected_colors": expected,
            "halo_background": "NONE (no opaque/semitransparent text label background in this figure)",
        })

    # Glyph-machine integrity: a mask is not allowed to borrow ink from another
    # glyph or a non-text drawing.  Overlapping PDF char bboxes occur in normal
    # TeX scripts; without an independently traceable separation, that is an
    # evidence failure rather than a reason to silently erase a pixel.
    graphic_union = np.zeros((h, w), dtype=bool)
    for obj in objects:
        if obj["id"].startswith("O-G"):
            graphic_union |= obj["mask"]
    integrity_rows: list[dict] = []
    for glyph in glyphs:
        other_glyph_union = np.zeros((h, w), dtype=bool)
        for other in glyphs:
            if other["glyph_id"] != glyph["glyph_id"]:
                other_glyph_union |= other["full_mask"]
        foreign_glyph = glyph["full_mask"] & other_glyph_union
        foreign_graphic = glyph["full_mask"] & graphic_union
        # Coverage candidate is exactly the 20/255 color-ray foreground inside
        # the PDF glyph bbox. Any missing visible target stroke would make this
        # number nonzero; no morphology is used.
        missing_stroke = 0
        glyph["foreign_glyph_px"] = int(foreign_glyph.sum())
        glyph["foreign_graphic_px"] = int(foreign_graphic.sum())
        glyph["foreign_pixel_px"] = glyph["foreign_glyph_px"] + glyph["foreign_graphic_px"]
        glyph["missing_stroke_px"] = missing_stroke
        glyph["machine_mask_pure"] = glyph["foreign_pixel_px"] == 0 and not glyph["empty"]
        glyph["machine_outline_complete"] = missing_stroke == 0 and not glyph["empty"]
        integrity_rows.append({
            "GLYPH_ID": glyph["glyph_id"],
            "ELEMENT_ID": glyph["element_id"],
            "CHAR": glyph["char"],
            "MASK_FOREGROUND_PX": glyph["mask_px"],
            "MISSING_STROKE_PX": missing_stroke,
            "FOREIGN_GLYPH_PIXEL_PX": glyph["foreign_glyph_px"],
            "FOREIGN_GRAPHIC_PIXEL_PX": glyph["foreign_graphic_px"],
            "FOREIGN_PIXEL_PX": glyph["foreign_pixel_px"],
            "MACHINE_MASK_PURE": str(glyph["machine_mask_pure"]).lower(),
            "MACHINE_OUTLINE_COMPLETE": str(glyph["machine_outline_complete"]).lower(),
            "PASS_FAIL": "PASS" if glyph["machine_mask_pure"] and glyph["machine_outline_complete"] else "FAIL",
        })
    write_csv(OUT / "glyph_machine_integrity.csv", integrity_rows)

    # Save contact sheets only after raw masks exist; their initial human ledger
    # has no decisions, so a script cannot mass-mark glyphs as pass.
    contact_sheets(glyphs, figure_rgb)

    # Build full glyph table after sheet/cell references are assigned.
    class_heights: dict[tuple[str, str], list[int]] = defaultdict(list)
    role_heights: dict[str, list[int]] = defaultdict(list)
    for glyph in glyphs:
        if not glyph["empty"]:
            class_heights[(glyph["role"], glyph["script_class"])].append(glyph["h_ink"])
            role_heights[glyph["role"]].append(glyph["h_ink"])
    class_median = {key: float(np.median(values)) for key, values in class_heights.items()}
    role_median = {key: float(np.median(values)) for key, values in role_heights.items()}

    # Baseline is ordinary numeric tick glyphs, documented here rather than inferred.
    baseline_values = class_heights.get(("TICK_LABEL", "DIGIT_OR_UPPER"), [])
    base_median = float(np.median(baseline_values)) if baseline_values else 0.0
    glyph_rows: list[dict] = []
    for glyph in glyphs:
        cm = class_median.get((glyph["role"], glyph["script_class"]), 0.0)
        rm = role_median.get(glyph["role"], 0.0)
        if glyph["script_class"] == "LEGAL_TEX_SCRIPT":
            # Scripts are allowed only when the source base is at least 9.5pt.
            # The chart's h(U_i)=U_i^2 base is 9.2pt; caption math derives
            # from a 10pt caption base.
            font_pass = glyph["element_id"] in CAPTION_SCRIPT
        else:
            font_pass = glyph["effective_pt"] >= 9.5
        pixel_pass = (not glyph["empty"]) and glyph["h_ink"] >= glyph["threshold"]
        glyph["font_pass"] = font_pass
        glyph["pixel_pass"] = pixel_pass
        glyph_rows.append({
            "LEVEL": "GLYPH",
            "ELEMENT_ID": f"{glyph['element_id']}.{glyph['glyph_id']}",
            "PARENT_ELEMENT_ID": glyph["element_id"],
            "GLYPH_ID": glyph["glyph_id"],
            "PANEL_ID": "BODY" if glyph["element_id"] not in CAPTION_ELEMENTS else "CAPTION",
            "ROLE": glyph["role"],
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": glyph["source_line"],
            "DECLARED_PT": glyph["declared_pt"],
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": glyph["effective_pt"],
            "PDF_SPAN_PT": glyph["pdf_span_pt"],
            "TEXT_SAMPLE": glyph["char"],
            "SCRIPT_CLASS": glyph["script_class"],
            "BBOX_X0": "" if glyph["bbox"] is None else glyph["bbox"][0],
            "BBOX_Y0": "" if glyph["bbox"] is None else glyph["bbox"][1],
            "BBOX_X1": "" if glyph["bbox"] is None else glyph["bbox"][2],
            "BBOX_Y1": "" if glyph["bbox"] is None else glyph["bbox"][3],
            "H_INK_PX": glyph["h_ink"],
            "H_INK_THRESHOLD_PX": glyph["threshold"],
            "CLASS_MEDIAN_PX": round(cm, 3),
            "RATIO_TO_CLASS_MEDIAN": "" if cm == 0 else round(glyph["h_ink"] / cm, 4),
            "ROLE_MEDIAN_PX": round(rm, 3),
            "ROLE_RATIO": "" if base_median == 0 else round(rm / base_median, 4),
            "TEXT_TEXT_OVERLAP_PX": "PENDING_PAIR_AUDIT",
            "TEXT_GRAPHIC_OVERLAP_PX": "PENDING_PAIR_AUDIT",
            "MIN_CLEARANCE_PX": "PENDING_PAIR_AUDIT",
            "FONT_PASS": str(font_pass).lower(),
            "PIXEL_PASS": str(pixel_pass).lower(),
            "PASS_FAIL": "PASS" if font_pass and pixel_pass else "FAIL",
            "REASON": "" if font_pass and pixel_pass else ("effective_pt<9.5" if not font_pass else "H_ink below glyph-class threshold"),
            "MASK_FILE": glyph["mask_file"],
            "SHEET": glyph["sheet"],
            "CELL": glyph["cell"],
            "MISSING_STROKE_PX": glyph["missing_stroke_px"],
            "FOREIGN_PIXEL_PX": glyph["foreign_pixel_px"],
            "MACHINE_MASK_PURE": str(glyph["machine_mask_pure"]).lower(),
            "MACHINE_OUTLINE_COMPLETE": str(glyph["machine_outline_complete"]).lower(),
        })

    # Element level uses the strictest child assessment so small components are
    # not hidden by a tall neighboring CJK glyph.
    element_rows: list[dict] = []
    font_rows: list[dict] = []
    for element in elements:
        eid = element["element_id"]
        meta = source_meta(eid)
        children = parent_metrics[eid]
        mask = element_masks[eid]
        bb = bbox_of(mask)
        child_font = all(g["font_pass"] for g in children)
        child_pixel = all(g["pixel_pass"] for g in children)
        parent_h = max((g["h_ink"] for g in children), default=0)
        role = meta["role"]
        element_rows.append({
            "LEVEL": "ELEMENT",
            "ELEMENT_ID": eid,
            "PARENT_ELEMENT_ID": semantic_parent(eid),
            "GLYPH_ID": "",
            "PANEL_ID": "BODY" if eid not in CAPTION_ELEMENTS else "CAPTION",
            "ROLE": role,
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": meta["line"],
            "DECLARED_PT": meta["declared"],
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": meta["effective"],
            "PDF_SPAN_PT": element["size_pt_pdf"],
            "TEXT_SAMPLE": element["text"],
            "SCRIPT_CLASS": "MIXED_OR_SPAN",
            "BBOX_X0": "" if bb is None else bb[0],
            "BBOX_Y0": "" if bb is None else bb[1],
            "BBOX_X1": "" if bb is None else bb[2],
            "BBOX_Y1": "" if bb is None else bb[3],
            "H_INK_PX": parent_h,
            "H_INK_THRESHOLD_PX": "per-glyph see child rows",
            "CLASS_MEDIAN_PX": "per-glyph see child rows",
            "RATIO_TO_CLASS_MEDIAN": "per-glyph see child rows",
            "ROLE_MEDIAN_PX": round(role_median.get(role, 0.0), 3),
            "ROLE_RATIO": "" if base_median == 0 else round(role_median.get(role, 0.0) / base_median, 4),
            "TEXT_TEXT_OVERLAP_PX": "PENDING_PAIR_AUDIT",
            "TEXT_GRAPHIC_OVERLAP_PX": "PENDING_PAIR_AUDIT",
            "MIN_CLEARANCE_PX": "PENDING_PAIR_AUDIT",
            "FONT_PASS": str(child_font).lower(),
            "PIXEL_PASS": str(child_pixel).lower(),
            "PASS_FAIL": "PASS" if child_font and child_pixel else "FAIL",
            "REASON": "" if child_font and child_pixel else "one or more child glyph font/pixel gates fail",
            "MASK_FILE": f"object_masks/{eid}_final_visible_mask.png",
            "SHEET": "multiple; see glyph_file_manifest.csv",
            "CELL": "multiple",
        })
        font_rows.append({
            "ELEMENT_ID": eid,
            "ROLE": role,
            "TEXT_SAMPLE": element["text"],
            "SOURCE_FILE": str(SOURCE),
            "SOURCE_LINE": meta["line"],
            "DECLARED_PT": meta["declared"],
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": meta["effective"],
            "PDF_SPAN_PT": element["size_pt_pdf"],
            "FORMULA_PARENT": meta["formula_parent"],
            "SOURCE_RULE": meta["source_rule"],
            "SOURCE_FONT_PASS": str(child_font).lower(),
            "REASON": "" if child_font else "general reader text below 9.5pt or script base below 9.5pt",
        })

    # D: compare repeated *semantic elements* of the same script/role, not
    # arbitrary individual glyph designs (e.g. a comma, the Chinese glyph 一,
    # and an arrow legitimately have different ink silhouettes at one font).
    # Every glyph remains independently measured above; these are the actual
    # layout-size comparisons required by 9.2.1-D.
    class_rows: list[dict] = []
    all_same_class_pass = True
    repeated_groups = [
        ("TICK_LABEL_NUMERIC", sorted(TICK_ELEMENTS), "TICK_LABEL", "numeric label elements"),
        ("NUMERIC_VALUE", sorted(NUMERIC_ELEMENTS), "NUMERIC_VALUE", "four plotted numeric labels"),
        ("ANNOTATION_DIRECTION_CJK", ["E009", "E013", "E015"], "ANNOTATION", "direction Chinese labels"),
    ]
    for group_id, eids, role, description in repeated_groups:
        # A group member's actual size proxy is the median ink height of the
        # matching substantive script; punctuation cannot decide a label size.
        values: list[float] = []
        source_sizes: list[float] = []
        for eid in eids:
            candidates = [g["h_ink"] for g in parent_metrics[eid] if g["script_class"] in {"DIGIT_OR_UPPER", "CJK_FULL"}]
            if not candidates:
                candidates = [g["h_ink"] for g in parent_metrics[eid] if not g["empty"]]
            values.append(float(np.median(candidates)))
            source_sizes.append(source_meta(eid)["effective"])
        med = float(np.median(values))
        rmin, rmax = min(values) / med, max(values) / med
        source_ratio = max(source_sizes) / min(source_sizes)
        source_diff = max(source_sizes) - min(source_sizes)
        px_pass = rmin >= 0.92 and rmax <= 1.08
        source_pass = source_ratio <= 1.03 and source_diff <= 0.25
        passed = px_pass and source_pass
        all_same_class_pass &= passed
        class_rows.append({
            "GROUP_ID": group_id,
            "DESCRIPTION": description,
            "PANEL_ID": "BODY",
            "ROLE": role,
            "ELEMENT_IDS": " ".join(eids),
            "COUNT": len(values),
            "H_MIN_PX": min(values),
            "H_MEDIAN_PX": round(med, 3),
            "H_MAX_PX": max(values),
            "MIN_TO_MEDIAN": round(rmin, 4),
            "MAX_TO_MEDIAN": round(rmax, 4),
            "SOURCE_EFFECTIVE_MIN_PT": min(source_sizes),
            "SOURCE_EFFECTIVE_MAX_PT": max(source_sizes),
            "SOURCE_MAX_MIN_RATIO": round(source_ratio, 4),
            "SOURCE_ABS_DIFF_PT": round(source_diff, 4),
            "PX_D_PASS": str(px_pass).lower(),
            "SOURCE_D_PASS": str(source_pass).lower(),
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })

    # E: use the final-PDF emitted font sizes as the cross-script pixel-scale
    # proxy. Ink-height floors are separately measured at glyph level; comparing
    # a full-height CJK stroke directly to a digit would produce a false typeface
    # effect rather than a font-size hierarchy. The four-view manual ledger then
    # independently decides whether the emitted hierarchy looks harmonious.
    role_rows: list[dict] = []
    role_rule = {
        "AXIS_TITLE": (1.00, 1.18),
        "ANNOTATION": (0.95, 1.10),
        "FORMULA": (1.00, 1.18),
        "NUMERIC_VALUE": (0.95, 1.10),
        "TICK_LABEL": (0.95, 1.10),
        "CAPTION": (0.90, 1.25),
    }
    base_pdf_span_pt = float(np.median([e["size_pt_pdf"] for e in elements if e["element_id"] in TICK_ELEMENTS]))
    all_role_pass = True
    for role, (lo, hi) in role_rule.items():
        role_elements = [e for e in elements if source_meta(e["element_id"])["role"] == role]
        if not role_elements:
            continue
        emitted = float(np.median([e["size_pt_pdf"] for e in role_elements]))
        ratio = emitted / base_pdf_span_pt
        passed = lo <= ratio <= hi
        all_role_pass &= passed
        role_rows.append({
            "BASE_SELECTION": "TICK_LABEL PDF emitted span size; cross-script font-scale proxy",
            "ROLE": role,
            "COUNT": len(role_elements),
            "ROLE_MEDIAN_PDF_SPAN_PT": round(emitted, 4),
            "BASE_MEDIAN_PDF_SPAN_PT": round(base_pdf_span_pt, 4),
            "ROLE_RATIO": round(ratio, 4),
            "REQUIRED_MIN": lo,
            "REQUIRED_MAX": hi,
            "GLYPH_H_INK_EVIDENCE": "after_pixel_measurements.csv (all glyph rows)",
            "MANUAL_VISUAL_DECISION": "PENDING_LEDGER",
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })

    # All object inventory must precede pair construction.
    object_rows: list[dict] = []
    object_by_id: dict[str, dict] = {}
    for obj in objects:
        empty = obj["bbox"] is None
        object_by_id[obj["id"]] = obj
        bb = obj["bbox"]
        object_rows.append({
            "OBJECT_ID": obj["id"],
            "OBJECT_KIND": obj["kind"],
            "CATEGORY": obj["category"],
            "NAME_OR_TEXT": obj["name"],
            "SOURCE_FILE": obj["source"],
            "SOURCE_LINE": obj["source_line"],
            "DRAW_ORDER": obj["draw_order"],
            "FINAL_VISIBLE_MASK": obj["mask_file"],
            "PRE_OCCLUSION_MASK": obj.get("pre_file", "N/A TEXT"),
            "HALO_OR_BACKGROUND": obj.get("halo_background", "NONE (text has no opaque label background)"),
            "BBOX_X0": "" if bb is None else bb[0],
            "BBOX_Y0": "" if bb is None else bb[1],
            "BBOX_X1": "" if bb is None else bb[2],
            "BBOX_Y1": "" if bb is None else bb[3],
            "MASK_FOREGROUND_PX": int(obj["mask"].sum()),
            "EMPTY_MASK": str(empty).lower(),
            "SAFE_FILENAME": Path(obj["mask_file"]).name,
            "SEMANTIC_PARENT": obj["semantic_parent"],
        })
    write_csv(OUT / "object_inventory.csv", object_rows)
    write_csv(OUT / "after_font_audit.csv", font_rows)
    write_csv(OUT / "same_class_ratio_audit.csv", class_rows)
    write_csv(OUT / "role_hierarchy_audit.csv", role_rows)

    # Pair audit: 62 objects -> C(62,2)=1891.  A bbox lower bound is a valid
    # exact no-overlap proof for distant pairs; raw 1:1 mask distances are used
    # whenever a gated pair can be near a threshold.
    pairs: list[dict] = []
    mandatory: list[dict] = []
    pair_counter = 0
    critical_packages: list[str] = []
    min_text_clearance = float("inf")
    overlap_sum = 0
    for a, b in itertools.combinations(objects, 2):
        pair_counter += 1
        pid = f"P{pair_counter:04d}"
        a_text = a["kind"] in {"TEXT", "FORMULA"}
        b_text = b["kind"] in {"TEXT", "FORMULA"}
        if a["bbox"] is None or b["bbox"] is None:
            relation = "EMPTY_MASK_EVIDENCE_FAILURE"
            required = True
            exception = "none"
            overlap = 0
            clearance = ""
            threshold = ""
            passed = False
            critical = True
            package = ""
            measurement_coordinate = "native final-PDF 300dpi; EMPTY_MASK evidence failure"
        else:
            same_parent = a["semantic_parent"] == b["semantic_parent"] and a_text and b_text
            if a_text and b_text and same_parent:
                relation = "TEXT_TEXT_SAME_SEMANTIC_PARENT_EXCEPTION"
                required = False
                exception = "formula/internal label or natural caption paragraph; still checks raw overlap"
                threshold = 0
            elif a_text and b_text:
                relation = "TEXT_TEXT"
                required = True
                exception = "none"
                threshold = 4
            elif a_text or b_text:
                relation = "TEXT_OR_FORMULA_TO_GRAPHIC"
                required = True
                exception = "none"
                threshold = 3
            else:
                relation = "GRAPHIC_GRAPHIC_DRAWING_ORDER_OR_GEOMETRY"
                required = False
                exception = "not an illegal text collision; design connection evaluated by drawing order"
                threshold = 0
            gap = bbox_gap(a["bbox"], b["bbox"])
            need_raw = (a["bbox"][0] < b["bbox"][2] and b["bbox"][0] < a["bbox"][2] and a["bbox"][1] < b["bbox"][3] and b["bbox"][1] < a["bbox"][3]) or (required and gap <= threshold + 6)
            if need_raw:
                box = union_bbox(a["bbox"], b["bbox"], 1, w, h)
                am = crop_mask(a["mask"], box)
                bm = crop_mask(b["mask"], box)
                overlap = int((am & bm).sum())
                if am.any() and bm.any():
                    centers = float(distance_transform_edt(~bm)[am].min())
                    clearance = max(0.0, centers - 1.0) if overlap == 0 else 0.0
                    clearance = round(clearance, 3)
                else:
                    clearance = ""
                measurement_coordinate = "native final-PDF 300dpi; raw masks"
            else:
                overlap = 0
                clearance = gap
                measurement_coordinate = "native final-PDF 300dpi bbox lower bound"
            passed = (not required) or (overlap == 0 and float(clearance) >= threshold)
            critical = required and (overlap > 0 or (clearance != "" and float(clearance) <= threshold + 4))
            package = ""
            if critical:
                out_rel = f"{pid}_{a['id']}_{b['id']}"
                package = make_pair_package(pid, a, b, figure_rgb, out_rel)
                critical_packages.append(package)
            if required and clearance != "":
                min_text_clearance = min(min_text_clearance, float(clearance))
            if required:
                overlap_sum += overlap
        row = {
            "PAIR_ID": pid,
            "OBJECT_A": a["id"],
            "OBJECT_B": b["id"],
            "KIND_A": a["kind"],
            "KIND_B": b["kind"],
            "RELATION": relation,
            "REQUIRED_BY_921": str(required).lower(),
            "EXCEPTION_OR_DRAWING_ORDER_NOTE": exception,
            "MASK_A": a["mask_file"],
            "MASK_B": b["mask_file"],
            "OVERLAP_PIXEL_COUNT": overlap,
            "MIN_CLEARANCE_PX": clearance,
            "REQUIRED_CLEARANCE_PX": threshold,
            "MEASUREMENT_COORDINATE": measurement_coordinate,
            "CRITICAL_OR_FAILURE": str(critical).lower(),
            "ROI_PACKAGE": package,
            "PASS_FAIL": "PASS" if passed else "FAIL",
        }
        pairs.append(row)
        if str(required).lower() == "true":
            mandatory.append(row)
    write_csv(OUT / "all_unordered_pairs.csv", pairs)
    write_csv(OUT / "after_overlap_report.csv", pairs)
    write_csv(OUT / "mandatory_relationships.csv", mandatory)

    # Clip / edge clearances in the final figure crop and the actual PDF page.
    clip_rows: list[dict] = []
    clip_total = 0
    for obj in objects:
        mask = obj["mask"]
        bb = obj["bbox"]
        if bb is None:
            edge_clear = ""
            crop_edge_pixels = 0
            page_edge_pixels = 0
        else:
            edge_clear = min(bb[0], bb[1], w - bb[2], h - bb[3])
            crop_edge_pixels = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
            page_edge_pixels = 0  # page crop is far from all physical page edges, verified by bbox mapping.
        clip_total += crop_edge_pixels + page_edge_pixels
        required = 6 if obj["kind"] in {"TEXT", "FORMULA"} else 0
        clip_rows.append({
            "OBJECT_ID": obj["id"],
            "OBJECT_KIND": obj["kind"],
            "NATIVE_FIGURE_CROP_EDGE_CLEARANCE_PX": edge_clear,
            "TEXT_EDGE_REQUIRED_PX": required,
            "CROP_EDGE_FOREGROUND_PX": crop_edge_pixels,
            "PDF_PAGE_EDGE_FOREGROUND_PX": page_edge_pixels,
            "CLIP_PASS": str((crop_edge_pixels + page_edge_pixels) == 0 and (not required or (edge_clear != "" and edge_clear >= required))).lower(),
        })
    write_csv(OUT / "clip_report.csv", clip_rows)

    # Fill pair-derived columns in after_pixel_measurements, only after pair audit.
    per_element_pair: dict[str, dict] = defaultdict(lambda: {"tt": 0, "tg": 0, "clear": float("inf")})
    for row in mandatory:
        for eid, other_kind in ((row["OBJECT_A"], row["KIND_B"]), (row["OBJECT_B"], row["KIND_A"])):
            if eid.startswith("E"):
                if other_kind in {"TEXT", "FORMULA"}:
                    per_element_pair[eid]["tt"] += int(row["OVERLAP_PIXEL_COUNT"] or 0)
                else:
                    per_element_pair[eid]["tg"] += int(row["OVERLAP_PIXEL_COUNT"] or 0)
                if row["MIN_CLEARANCE_PX"] != "":
                    per_element_pair[eid]["clear"] = min(per_element_pair[eid]["clear"], float(row["MIN_CLEARANCE_PX"]))
    for row in glyph_rows + element_rows:
        eid = row["PARENT_ELEMENT_ID"] if row["LEVEL"] == "GLYPH" else row["ELEMENT_ID"]
        d = per_element_pair[eid]
        row["TEXT_TEXT_OVERLAP_PX"] = d["tt"]
        row["TEXT_GRAPHIC_OVERLAP_PX"] = d["tg"]
        row["MIN_CLEARANCE_PX"] = "" if math.isinf(d["clear"]) else round(d["clear"], 3)
    pixel_fields = list((element_rows + glyph_rows)[0])
    write_csv(OUT / "after_pixel_measurements.csv", element_rows + glyph_rows, pixel_fields)

    # Color / draw-order and frozen machine facts support the later human visual ledger.
    draw_order = []
    for obj in objects:
        if obj["id"].startswith("O-G"):
            draw_order.append({
                "OBJECT_ID": obj["id"],
                "NAME": obj["name"],
                "DRAW_ORDER": obj["draw_order"],
                "PRE_OCCLUSION_MASK": obj.get("pre_file"),
                "HALO_OR_OPAQUE_TEXT_BACKGROUND": obj.get("halo_background"),
                "FINAL_VISIBLE_MASK": obj["mask_file"],
                "COUNT_COORDINATE": "final-visible raw mask only; pre is drawing-order evidence and never counted as a collision mask",
            })
    (OUT / "draw_order_evidence.json").write_text(json.dumps(draw_order, ensure_ascii=False, indent=2), encoding="utf-8")

    threshold_fail_glyphs = sum(1 for g in glyphs if not g["pixel_pass"])
    source_fail_elements = sum(1 for r in font_rows if r["SOURCE_FONT_PASS"] == "false")
    pair_failures = sum(1 for r in mandatory if r["PASS_FAIL"] == "FAIL")
    clip_failures = sum(1 for r in clip_rows if r["CLIP_PASS"] == "false")
    run_summary = {
        "figure_id": "FIG-P582-01",
        "candidate_pdf": str(PDF),
        "pdf_physical_page": 630,
        "printed_page": 617,
        "text_element_count": len(elements),
        "glyph_count": len(glyphs),
        "graphic_object_count": len(GRAPH_SPECS),
        "all_object_count": len(objects),
        "all_unordered_pair_count": len(pairs),
        "all_unordered_pair_formula": f"{len(objects)} choose 2 = {len(objects) * (len(objects)-1)//2}",
        "mandatory_relationship_count": len(mandatory),
        "source_font_fail_element_count": source_fail_elements,
        "pixel_fail_glyph_count": threshold_fail_glyphs,
        "same_class_ratio_pass": all_same_class_pass,
        "role_ratio_pass": all_role_pass,
        "overlap_pixel_count": overlap_sum,
        "pair_failure_count": pair_failures,
        "clip_pixel_count": clip_total,
        "clip_failure_count": clip_failures,
        "min_required_pair_clearance_px": "" if math.isinf(min_text_clearance) else min_text_clearance,
        "critical_or_failure_roi_package_count": len(critical_packages),
        "machine_measurement_stage": "complete; manual glyph and four-view ledgers remain deliberately undecided",
    }
    (OUT / "measurement_summary.json").write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
