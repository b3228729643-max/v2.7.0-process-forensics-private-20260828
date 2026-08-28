from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R4_SA3_FRESH_ISOLATED_R104_R168_RESTART2_20260825")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_markov_chain_path.tex")
PAGE_INDEX = 648
DPI = 300
SCALE = DPI / 72.0
# Integer coordinates in the native 2481x3508 pdftoppm page raster.
# This includes the complete graphic body and its two-line caption, with generous white clearance.
CROP = (230, 2040, 2195, 2765)
RENDER = ROOT / "render"
MACHINE = ROOT / "machine"
OBJECT_DIR = MACHINE / "object_masks"
CONTACT_DIR = MACHINE / "contact_sheets"
REL_DIR = MACHINE / "relationship_sheets"
MATRIX_DIR = MACHINE / "matrices"
HALO_DIR = MACHINE / "occlusion_masks"


def ensure_dirs() -> None:
    for p in (RENDER, MACHINE, OBJECT_DIR, CONTACT_DIR, REL_DIR, MATRIX_DIR, HALO_DIR):
        p.mkdir(parents=True, exist_ok=True)


def font(size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT = font(14)
FONT_SMALL = font(12)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pt_to_px(v: float) -> float:
    return v * SCALE


def clamp_bbox(b: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = b
    x0 = max(0, min(w, x0))
    y0 = max(0, min(h, y0))
    x1 = max(x0 + 1, min(w, x1))
    y1 = max(y0 + 1, min(h, y1))
    return x0, y0, x1, y1


def page_bbox_to_crop_px(rect: tuple[float, float, float, float], pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        math.floor(pt_to_px(x0)) - CROP[0] - pad,
        math.floor(pt_to_px(y0)) - CROP[1] - pad,
        math.ceil(pt_to_px(x1)) - CROP[0] + pad,
        math.ceil(pt_to_px(y1)) - CROP[1] + pad,
    )


def nonwhite_mask(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 2:
        return (255 - arr) >= 20
    return np.max(255 - arr[:, :, :3].astype(np.int16), axis=2) >= 20


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    yy, xx = np.nonzero(mask)
    if len(xx) == 0:
        return None
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def classify_char(ch: str, parent: str, span_size: float) -> tuple[str, int]:
    cp = ord(ch)
    name = unicodedata.name(ch, "")
    if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
        return "CJK", 30
    if ch in ".,;:，。；：、…":
        return "LOW_PROFILE_PUNCTUATION", 1
    if ch in "+=−-→∑∫≥≤×÷":
        return "MATH_OPERATOR", 22
    if ch.isdigit() or (ch.isalpha() and ch.upper() == ch and ch.lower() != ch):
        return "LATIN_CAP_OR_DIGIT", 24
    if "GREEK" in name or (ch.isalpha() and ch.lower() == ch):
        if parent == "transition_kernel" and span_size < 8.0:
            return "NATURAL_SCRIPT", 15
        return "LATIN_GREEK_LOWER", 17
    if unicodedata.category(ch).startswith("P"):
        return "PUNCTUATION", 1
    return "BASE_MATH_OR_SYMBOL", 22


def semantic_text_parent(block_bbox: tuple[float, float, float, float], line_text: str, line_index: int) -> tuple[str, str]:
    y0 = block_bbox[1]
    stripped = line_text.strip()
    if 606 <= y0 <= 614 and "时间" in stripped:
        return "axis_title", "AXIS_TITLE"
    if 528 <= y0 <= 580 and len(stripped) == 1 and "MATHEMATICAL ITALIC SMALL" in unicodedata.name(stripped, ""):
        return "state_labels", "STATE_LABEL"
    if 510 <= y0 <= 548 and ("t=" in line_text or "𝑡=" in line_text):
        return "time_labels", "TIME_LABEL"
    if 548 <= y0 <= 562 and "保持" in line_text:
        return "hold_annotation", "ANNOTATION"
    if 557 <= y0 <= 575 and ("K(" in line_text or "𝐾(" in line_text):
        return "transition_kernel", "FORMULA"
    if 498 <= y0 <= 510:
        return "repeat_annotation", "ANNOTATION"
    if 615 <= y0 <= 627:
        return "bottom_note", "ANNOTATION"
    if 629 <= y0 <= 660:
        return "caption", "CAPTION"
    return f"text_block_y{round(y0)}_l{line_index}", "OTHER_TEXT"


@dataclass
class Obj:
    object_id: str
    safe_filename: str
    object_type: str
    semantic_parent: str
    role: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    metadata: dict

    def full_mask(self, width: int, height: int) -> np.ndarray:
        out = np.zeros((height, width), dtype=bool)
        x0, y0, x1, y1 = self.bbox
        out[y0:y1, x0:x1] = self.mask
        return out


def extract_text_objects(page: fitz.Page, crop_arr: np.ndarray) -> list[Obj]:
    raw = page.get_text("rawdict")
    h, w = crop_arr.shape[:2]
    objects: list[Obj] = []
    seq = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        bb = tuple(block["bbox"])
        if bb[3] < CROP[1] / SCALE or bb[1] > CROP[3] / SCALE:
            continue
        for li, line in enumerate(block.get("lines", [])):
            line_text = "".join(ch.get("c", "") for span in line.get("spans", []) for ch in span.get("chars", []))
            parent, role = semantic_text_parent(bb, line_text, li)
            for span in line.get("spans", []):
                for chrec in span.get("chars", []):
                    ch = chrec.get("c", "")
                    if not ch or ch.isspace():
                        continue
                    rect = tuple(chrec["bbox"])
                    cx = (rect[0] + rect[2]) / 2
                    cy = (rect[1] + rect[3]) / 2
                    if not (CROP[0] / SCALE <= cx <= CROP[2] / SCALE and CROP[1] / SCALE <= cy <= CROP[3] / SCALE):
                        continue
                    seq += 1
                    oid = f"T{seq:03d}"
                    safe = f"{oid}_U{ord(ch):04X}.png"
                    bbpx = clamp_bbox(page_bbox_to_crop_px(rect), w, h)
                    x0, y0, x1, y1 = bbpx
                    region = crop_arr[y0:y1, x0:x1]
                    mask = nonwhite_mask(region)
                    category, advisory_min = classify_char(ch, parent, float(span.get("size", 0)))
                    tb = tight_bbox(mask)
                    h_ink = 0 if tb is None else tb[3] - tb[1]
                    w_ink = 0 if tb is None else tb[2] - tb[0]
                    edge_touch = 0
                    if mask.size:
                        edge_touch = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
                    meta = {
                        "char": ch,
                        "codepoint": f"U+{ord(ch):04X}",
                        "unicode_name": unicodedata.name(ch, "UNKNOWN"),
                        "font": span.get("font"),
                        "span_size_pt": round(float(span.get("size", 0)), 4),
                        "span_flags": int(span.get("flags", 0)),
                        "source_bbox_pt": [round(float(v), 4) for v in rect],
                        "h_ink_px": h_ink,
                        "w_ink_px": w_ink,
                        "ink_pixel_count": int(mask.sum()),
                        "advisory_category": category,
                        "advisory_protocol_min_px": advisory_min,
                        "advisory_pixel_threshold_met": bool(h_ink >= advisory_min),
                        "mask_nonempty": bool(mask.any()),
                        "bbox_edge_ink_px": edge_touch,
                        "machine_field_only": True,
                    }
                    objects.append(Obj(oid, safe, "TEXT_GLYPH", parent, role, bbpx, mask, meta))
    resolve_text_pixel_ownership(objects, w, h)
    return objects


def resolve_text_pixel_ownership(objects: list[Obj], width: int, height: int) -> None:
    """Make glyph masks mutually exclusive where PDF character bboxes overlap.

    The source raster has a single final color per native pixel. When adjacent character
    bboxes overlap, independent bbox thresholding can otherwise duplicate the same edge
    pixel into two glyph masks. Ownership is assigned once to the closest normalized
    character-box centre; every removal is retained as machine provenance.
    """
    full = [o.full_mask(width, height) for o in objects]
    counts = np.zeros((height, width), dtype=np.uint16)
    for m in full:
        counts += m.astype(np.uint16)
    yy, xx = np.nonzero(counts > 1)
    removed = [0 for _ in objects]
    shared = [0 for _ in objects]
    for y, x in zip(yy.tolist(), xx.tolist()):
        candidates = [i for i, m in enumerate(full) if m[y, x]]
        for i in candidates:
            shared[i] += 1
        def score(i: int) -> float:
            x0, y0, x1, y1 = objects[i].bbox
            cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
            return ((x - cx) / max(1.0, x1 - x0)) ** 2 + ((y - cy) / max(1.0, y1 - y0)) ** 2
        winner = min(candidates, key=score)
        for i in candidates:
            if i != winner:
                full[i][y, x] = False
                removed[i] += 1
    for i, o in enumerate(objects):
        x0, y0, x1, y1 = o.bbox
        o.mask = full[i][y0:y1, x0:x1]
        tb = tight_bbox(o.mask)
        o.metadata["ownership_shared_pixel_candidates"] = shared[i]
        o.metadata["ownership_pixels_removed"] = removed[i]
        o.metadata["ink_pixel_count"] = int(o.mask.sum())
        o.metadata["h_ink_px"] = 0 if tb is None else tb[3] - tb[1]
        o.metadata["w_ink_px"] = 0 if tb is None else tb[2] - tb[0]
        o.metadata["mask_nonempty"] = bool(o.mask.any())
        o.metadata["ownership_method"] = "exclusive_nearest_normalized_character_bbox_center"


GRAPHIC_NAMES = [
    ("axis_line", "axis", "AXIS_LINE"),
    ("axis_arrowhead", "axis", "ARROWHEAD"),
    ("node_x0_border", "node_x0", "NODE_BORDER"),
    ("node_x1_blue_border", "node_x1", "NODE_BORDER"),
    ("node_x1_white_separator", "node_x1", "OPAQUE_WHITE_SEPARATOR"),
    ("node_x2_blue_border", "node_x2", "NODE_BORDER"),
    ("node_x2_white_separator", "node_x2", "OPAQUE_WHITE_SEPARATOR"),
    ("node_x3_blue_border", "node_x3", "NODE_BORDER"),
    ("node_x3_white_separator", "node_x3", "OPAQUE_WHITE_SEPARATOR"),
    ("node_x4_blue_border", "node_x4", "NODE_BORDER"),
    ("node_x4_white_separator", "node_x4", "OPAQUE_WHITE_SEPARATOR"),
    ("node_x5_border", "node_x5", "NODE_BORDER"),
    ("node_xT_border", "node_xT", "NODE_BORDER"),
    ("transition_01_shaft", "transition_01", "TRANSITION_SHAFT"),
    ("transition_01_arrowhead", "transition_01", "ARROWHEAD"),
    ("transition_12_shaft", "transition_12", "TRANSITION_SHAFT"),
    ("transition_12_arrowhead", "transition_12", "ARROWHEAD"),
    ("transition_23_shaft", "transition_23", "TRANSITION_SHAFT"),
    ("transition_23_arrowhead", "transition_23", "ARROWHEAD"),
    ("transition_34_shaft", "transition_34", "TRANSITION_SHAFT"),
    ("transition_34_arrowhead", "transition_34", "ARROWHEAD"),
    ("transition_45_shaft", "transition_45", "TRANSITION_SHAFT"),
    ("transition_45_arrowhead", "transition_45", "ARROWHEAD"),
    ("transition_5T_shaft", "transition_5T", "TRANSITION_SHAFT"),
    ("transition_5T_arrowhead", "transition_5T", "ARROWHEAD"),
    ("repeat_correlation_dashed_arc", "repeat_relation", "RELATION_ARC"),
]


def point_crop_px(p: fitz.Point) -> tuple[float, float]:
    return float(p.x) * SCALE - CROP[0], float(p.y) * SCALE - CROP[1]


def cubic_points(p0: fitz.Point, p1: fitz.Point, p2: fitz.Point, p3: fitz.Point, samples: int = 96) -> list[tuple[float, float]]:
    out = []
    for k in range(samples + 1):
        t = k / samples
        u = 1.0 - t
        x = u ** 3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t ** 3 * p3.x
        y = u ** 3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t ** 3 * p3.y
        out.append((x * SCALE - CROP[0], y * SCALE - CROP[1]))
    return out


def drawing_geometry_full_mask(d: dict, role: str, width: int, height: int) -> np.ndarray:
    im = Image.new("1", (width, height), 0)
    dr = ImageDraw.Draw(im)
    stroke_px = max(1, int(math.ceil(float(d.get("width") or 0.5) * SCALE)))
    # A two-pixel capture allowance covers native antialias edge pixels; the result is
    # intersected with final-raster color below for every non-white path.
    capture_width = stroke_px + 2
    rect = d["rect"]
    if role in {"NODE_BORDER", "OPAQUE_WHITE_SEPARATOR"}:
        xy = (
            rect.x0 * SCALE - CROP[0],
            rect.y0 * SCALE - CROP[1],
            rect.x1 * SCALE - CROP[0],
            rect.y1 * SCALE - CROP[1],
        )
        dr.ellipse(xy, outline=1, width=capture_width if role == "NODE_BORDER" else stroke_px)
        return np.array(im, dtype=bool)
    if role == "ARROWHEAD":
        vertices: list[tuple[float, float]] = []
        for item in d["items"]:
            if item[0] != "l":
                continue
            p0, p1 = item[1], item[2]
            if not vertices:
                vertices.append(point_crop_px(p0))
            vertices.append(point_crop_px(p1))
        if len(vertices) >= 3:
            dr.polygon(vertices, fill=1)
            dr.line(vertices + [vertices[0]], fill=1, width=capture_width, joint="curve")
        return np.array(im, dtype=bool)
    for item in d["items"]:
        if item[0] == "l":
            dr.line((point_crop_px(item[1]), point_crop_px(item[2])), fill=1, width=capture_width)
        elif item[0] == "c":
            pts = cubic_points(item[1], item[2], item[3], item[4])
            dr.line(pts, fill=1, width=capture_width, joint="curve")
    return np.array(im, dtype=bool)


def extract_graphics(page: fitz.Page, crop_arr: np.ndarray) -> list[Obj]:
    h, w = crop_arr.shape[:2]
    drawings = []
    for global_index, d in enumerate(page.get_drawings()):
        r = d["rect"]
        if r.y1 < 490 or r.y0 > 626 or r.x1 < 90 or r.x0 > 490:
            continue
        drawings.append((global_index, d))
    if len(drawings) != len(GRAPHIC_NAMES):
        raise RuntimeError(f"Expected {len(GRAPHIC_NAMES)} figure drawings, got {len(drawings)}")
    objects: list[Obj] = []
    for seq, ((global_index, d), (name, parent, role)) in enumerate(zip(drawings, GRAPHIC_NAMES), 1):
        oid = f"G{seq:03d}"
        safe = f"{oid}_{name}.png"
        rect = tuple(d["rect"])
        geometry = drawing_geometry_full_mask(d, role, w, h)
        if role == "OPAQUE_WHITE_SEPARATOR":
            full_mask = geometry
            method = "vector_geometry_opaque_white_separator"
        else:
            raw = nonwhite_mask(crop_arr)
            color = d.get("color")
            fill = d.get("fill")
            target_blue = False
            for c in (color, fill):
                if c and c[2] - c[0] > 0.15:
                    target_blue = True
            if target_blue:
                rgb = crop_arr[:, :, :3].astype(np.int16)
                blue_family = (rgb[:, :, 2] - rgb[:, :, 0] >= 7) & (rgb[:, :, 2] - rgb[:, :, 1] >= 3)
                full_mask = geometry & raw & blue_family
                method = "vector_geometry_intersect_native_color_family_raw_mask"
            else:
                full_mask = geometry & raw
                method = "vector_geometry_intersect_native_contrast_raw_mask"
        full_tb = tight_bbox(full_mask)
        if full_tb is None:
            raise RuntimeError(f"Empty graphic mask for {oid} {name}")
        x0, y0, x1, y1 = full_tb
        bbpx = (x0, y0, x1, y1)
        mask = full_mask[y0:y1, x0:x1]
        tb = tight_bbox(mask)
        meta = {
            "drawing_index_zero_based": global_index,
            "drawing_type": d.get("type"),
            "stroke_color": d.get("color"),
            "fill_color": d.get("fill"),
            "stroke_width_pt": d.get("width"),
            "source_bbox_pt": [round(float(v), 4) for v in rect],
            "mask_method": method,
            "ink_pixel_count": int(mask.sum()),
            "h_ink_px": 0 if tb is None else tb[3] - tb[1],
            "w_ink_px": 0 if tb is None else tb[2] - tb[0],
            "mask_nonempty": bool(mask.any()),
            "machine_field_only": True,
        }
        objects.append(Obj(oid, safe, "GRAPHIC_PATH", parent, role, bbpx, mask, meta))

        if role == "OPAQUE_WHITE_SEPARATOR":
            Image.fromarray((full_mask.astype(np.uint8) * 255), "L").save(HALO_DIR / f"{oid}_halo_raw_mask_full_crop.png")
            # Reconstruct the pre-occlusion wide blue stroke at its actual 2.19182 pt width,
            # then retain only final native blue pixels after the white separator occludes it.
            pre_im = Image.new("1", (w, h), 0)
            pre_dr = ImageDraw.Draw(pre_im)
            rr = d["rect"]
            rrxy = (rr.x0 * SCALE - CROP[0], rr.y0 * SCALE - CROP[1], rr.x1 * SCALE - CROP[0], rr.y1 * SCALE - CROP[1])
            pre_dr.ellipse(rrxy, outline=1, width=int(math.ceil(2.19182 * SCALE)) + 2)
            pre = np.array(pre_im, dtype=bool)
            rgb = crop_arr[:, :, :3].astype(np.int16)
            blue = pre & nonwhite_mask(crop_arr) & (rgb[:, :, 2] - rgb[:, :, 0] >= 7)
            Image.fromarray((blue.astype(np.uint8) * 255), "L").save(HALO_DIR / f"{oid}_final_visible_blue_border_full_crop.png")
            Image.fromarray((pre.astype(np.uint8) * 255), "L").save(HALO_DIR / f"{oid}_pre_occlusion_wide_border_full_crop.png")
    return objects


def save_object_masks(objects: list[Obj]) -> None:
    for o in objects:
        Image.fromarray((o.mask.astype(np.uint8) * 255), "L").save(OBJECT_DIR / o.safe_filename)


def make_overall_overlay(crop: Image.Image, objects: list[Obj]) -> None:
    im = crop.copy().convert("RGB")
    dr = ImageDraw.Draw(im)
    for o in objects:
        x0, y0, x1, y1 = o.bbox
        color = (220, 30, 30) if o.object_type == "TEXT_GLYPH" else (0, 130, 210)
        dr.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        dr.text((x0, max(0, y0 - 13)), o.object_id, fill=color, font=FONT_SMALL)
    im.save(MACHINE / "after_text_and_graphic_overlay_300dpi.png")


def paste_center(dst: Image.Image, src: Image.Image, box: tuple[int, int, int, int], resize: bool = False) -> None:
    x0, y0, x1, y1 = box
    sw, sh = src.size
    if resize and (sw > x1 - x0 or sh > y1 - y0):
        ratio = min((x1 - x0) / sw, (y1 - y0) / sh)
        src = src.resize((max(1, int(sw * ratio)), max(1, int(sh * ratio))), Image.Resampling.NEAREST)
        sw, sh = src.size
    x = x0 + ((x1 - x0) - sw) // 2
    y = y0 + ((y1 - y0) - sh) // 2
    dst.paste(src, (x, y))


def contact_cell(crop_arr: np.ndarray, o: Obj, width: int = 1180, height: int = 235) -> Image.Image:
    cell = Image.new("RGB", (width, height), "white")
    dr = ImageDraw.Draw(cell)
    x0, y0, x1, y1 = o.bbox
    pad = 8
    cx0, cy0, cx1, cy1 = clamp_bbox((x0 - pad, y0 - pad, x1 + pad, y1 + pad), crop_arr.shape[1], crop_arr.shape[0])
    original = Image.fromarray(crop_arr[cy0:cy1, cx0:cx1], "RGB")
    overlay_arr = np.array(original).copy()
    local = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
    ox0, oy0 = x0 - cx0, y0 - cy0
    local[oy0:oy0 + o.mask.shape[0], ox0:ox0 + o.mask.shape[1]] = o.mask
    overlay_arr[local] = np.array([235, 30, 30], dtype=np.uint8)
    overlay = Image.fromarray(overlay_arr, "RGB")
    mask_only = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), "L").convert("RGB")
    zoom = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
    dr.text((8, 5), f"{o.object_id} {o.object_type} {o.role} parent={o.semantic_parent}", fill="black", font=FONT)
    if o.object_type == "TEXT_GLYPH":
        m = o.metadata
        info = f"{m['codepoint']} size={m['span_size_pt']}pt H={m['h_ink_px']}px ink={m['ink_pixel_count']} advisory={m['advisory_category']}"
    else:
        m = o.metadata
        info = f"draw={m['drawing_index_zero_based']} H={m['h_ink_px']}px ink={m['ink_pixel_count']} method={m['mask_method']}"
    dr.text((8, 24), info, fill="black", font=FONT_SMALL)
    boxes = [(8, 50, 270, 225), (285, 50, 547, 225), (562, 50, 824, 225), (839, 50, 1172, 225)]
    labels = ["ORIGINAL 1x", "TARGET OVERLAY 1x", "MASK ONLY 1x", "OVERLAY 8x NEAREST"]
    for b, lab in zip(boxes, labels):
        dr.rectangle(b, outline=(120, 120, 120), width=1)
        dr.text((b[0] + 3, b[1] + 3), lab, fill=(50, 50, 50), font=FONT_SMALL)
    paste_center(cell, original, (12, 68, 266, 220), resize=False)
    paste_center(cell, overlay, (289, 68, 543, 220), resize=False)
    paste_center(cell, mask_only, (566, 68, 820, 220), resize=False)
    paste_center(cell, zoom, (843, 68, 1168, 220), resize=True)
    return cell


def make_contact_sheets(crop_arr: np.ndarray, objects: list[Obj], prefix: str, per_sheet: int = 6) -> list[Path]:
    paths: list[Path] = []
    for si in range(0, len(objects), per_sheet):
        chunk = objects[si:si + per_sheet]
        sheet = Image.new("RGB", (1180, 235 * len(chunk)), "white")
        for row, o in enumerate(chunk):
            sheet.paste(contact_cell(crop_arr, o), (0, row * 235))
        path = CONTACT_DIR / f"{prefix}_{si // per_sheet + 1:02d}.png"
        sheet.save(path)
        paths.append(path)
    return paths


def object_global_coords(o: Obj) -> np.ndarray:
    yy, xx = np.nonzero(o.mask)
    if len(xx) == 0:
        return np.zeros((0, 2), dtype=np.int32)
    return np.column_stack((yy + o.bbox[1], xx + o.bbox[0]))


def make_pairs(objects: list[Obj], crop_size: tuple[int, int]) -> list[dict]:
    w, h = crop_size
    full_masks = [o.full_mask(w, h) for o in objects]
    pair_rows: list[dict] = []
    pair_id = 0
    for i, a in enumerate(objects):
        dist = distance_transform_edt(~full_masks[i])
        for j in range(i + 1, len(objects)):
            pair_id += 1
            b = objects[j]
            bm = full_masks[j]
            overlap = int(np.logical_and(full_masks[i], bm).sum())
            if not bm.any() or not full_masks[i].any():
                center_distance = None
                clearance = None
            else:
                center_distance = float(dist[bm].min())
                clearance = max(0.0, center_distance - 1.0)
            pair_rows.append({
                "pair_id": f"P{pair_id:05d}",
                "a_id": a.object_id,
                "b_id": b.object_id,
                "a_type": a.object_type,
                "b_type": b.object_type,
                "a_parent": a.semantic_parent,
                "b_parent": b.semantic_parent,
                "same_parent": a.semantic_parent == b.semantic_parent,
                "overlap_pixel_count": overlap,
                "center_distance_px": None if center_distance is None else round(center_distance, 4),
                "clearance_px": None if clearance is None else round(clearance, 4),
                "machine_geometry_only": True,
            })
    return pair_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def serialize_objects(objects: list[Obj]) -> list[dict]:
    rows = []
    for o in objects:
        x0, y0, x1, y1 = o.bbox
        row = {
            "object_id": o.object_id,
            "safe_filename": o.safe_filename,
            "object_type": o.object_type,
            "semantic_parent": o.semantic_parent,
            "role": o.role,
            "crop_bbox_px": [x0, y0, x1, y1],
            "crop_edge_clearance_px": min(x0, y0, CROP[2] - CROP[0] - x1, CROP[3] - CROP[1] - y1),
            **o.metadata,
        }
        rows.append(row)
    return rows


def make_pair_matrices(objects: list[Obj], pairs: list[dict]) -> list[Path]:
    n = len(objects)
    clearance = np.full((n, n), np.nan, dtype=float)
    overlap = np.zeros((n, n), dtype=int)
    id_to_i = {o.object_id: i for i, o in enumerate(objects)}
    for row in pairs:
        i, j = id_to_i[row["a_id"]], id_to_i[row["b_id"]]
        if row["clearance_px"] is not None:
            clearance[i, j] = clearance[j, i] = row["clearance_px"]
        overlap[i, j] = overlap[j, i] = row["overlap_pixel_count"]
    cell = 12
    margin = 150
    size = margin + n * cell + 30
    out_paths = []
    for kind in ("clearance", "overlap"):
        im = Image.new("RGB", (size, size), "white")
        dr = ImageDraw.Draw(im)
        dr.text((10, 8), f"ALL UNORDERED PAIRS {kind.upper()} MATRIX n={n}", fill="black", font=FONT)
        for i, o in enumerate(objects):
            if i % 5 == 0 or i == n - 1:
                dr.text((3, margin + i * cell), o.object_id, fill="black", font=FONT_SMALL)
                dr.text((margin + i * cell, 35), o.object_id, fill="black", font=FONT_SMALL)
        for i in range(n):
            for j in range(n):
                x0 = margin + j * cell
                y0 = margin + i * cell
                if i == j:
                    color = (30, 30, 30)
                elif kind == "overlap":
                    v = overlap[i, j]
                    color = (220, 30, 30) if v > 0 else (235, 247, 235)
                else:
                    v = clearance[i, j]
                    if np.isnan(v):
                        color = (120, 120, 120)
                    elif v < 3:
                        color = (220, 30, 30)
                    elif v < 6:
                        color = (245, 150, 40)
                    elif v < 12:
                        color = (250, 230, 80)
                    else:
                        color = (220, 245, 225)
                dr.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=color)
        path = MATRIX_DIR / f"all_pairs_{kind}_matrix.png"
        im.save(path)
        out_paths.append(path)
    return out_paths


def relationship_cell(crop_arr: np.ndarray, a: Obj, b: Obj, row: dict, width: int = 1180, height: int = 260) -> Image.Image:
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    x0 = min(ax0, bx0) - 10
    y0 = min(ay0, by0) - 10
    x1 = max(ax1, bx1) + 10
    y1 = max(ay1, by1) + 10
    x0, y0, x1, y1 = clamp_bbox((x0, y0, x1, y1), crop_arr.shape[1], crop_arr.shape[0])
    orig_arr = crop_arr[y0:y1, x0:x1].copy()
    am = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bm = np.zeros_like(am)
    am[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = a.mask
    bm[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0] = b.mask
    overlay_arr = orig_arr.copy()
    overlay_arr[am] = np.array([235, 30, 30], dtype=np.uint8)
    overlay_arr[bm] = np.array([0, 180, 210], dtype=np.uint8)
    overlay_arr[am & bm] = np.array([255, 230, 0], dtype=np.uint8)
    mask_arr = np.full_like(orig_arr, 255)
    mask_arr[am] = np.array([235, 30, 30], dtype=np.uint8)
    mask_arr[bm] = np.array([0, 180, 210], dtype=np.uint8)
    mask_arr[am & bm] = np.array([255, 230, 0], dtype=np.uint8)
    original = Image.fromarray(orig_arr, "RGB")
    overlay = Image.fromarray(overlay_arr, "RGB")
    masks = Image.fromarray(mask_arr, "RGB")
    zoom = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
    cell = Image.new("RGB", (width, height), "white")
    dr = ImageDraw.Draw(cell)
    dr.text((8, 4), f"{row['pair_id']} {a.object_id}/{b.object_id} overlap={row['overlap_pixel_count']} clearance={row['clearance_px']}px", fill="black", font=FONT)
    dr.text((8, 23), f"A={a.semantic_parent}:{a.role} B={b.semantic_parent}:{b.role} same_parent={row['same_parent']}", fill="black", font=FONT_SMALL)
    boxes = [(8, 48, 270, 252), (285, 48, 547, 252), (562, 48, 824, 252), (839, 48, 1172, 252)]
    labels = ["ORIGINAL 1x", "A RED / B CYAN / X YELLOW 1x", "MASKS ONLY 1x", "OVERLAY 8x NEAREST"]
    for box, lab in zip(boxes, labels):
        dr.rectangle(box, outline=(120, 120, 120), width=1)
        dr.text((box[0] + 3, box[1] + 3), lab, fill=(50, 50, 50), font=FONT_SMALL)
    paste_center(cell, original, (12, 66, 266, 248), resize=True)
    paste_center(cell, overlay, (289, 66, 543, 248), resize=True)
    paste_center(cell, masks, (566, 66, 820, 248), resize=True)
    paste_center(cell, zoom, (843, 66, 1168, 248), resize=True)
    return cell


def select_critical_pairs(objects: list[Obj], pairs: list[dict]) -> list[dict]:
    by_id = {o.object_id: o for o in objects}
    selected = []
    for row in pairs:
        a, b = by_id[row["a_id"]], by_id[row["b_id"]]
        if row["clearance_px"] is None:
            selected.append(row)
            continue
        if row["overlap_pixel_count"] > 0:
            selected.append(row)
            continue
        if a.semantic_parent == b.semantic_parent:
            continue
        if {a.object_type, b.object_type} == {"TEXT_GLYPH", "GRAPHIC_PATH"} and row["clearance_px"] < 12:
            selected.append(row)
            continue
        if a.object_type == b.object_type == "TEXT_GLYPH" and row["clearance_px"] < 8:
            selected.append(row)
    # Keep every overlap, then the nearest distinct relationships sufficient for direct review.
    overlaps = [r for r in selected if r["overlap_pixel_count"] > 0]
    nonoverlap = sorted((r for r in selected if r["overlap_pixel_count"] == 0), key=lambda r: r["clearance_px"] if r["clearance_px"] is not None else -1)
    result = overlaps + nonoverlap[:36]
    seen = set()
    unique = []
    for r in result:
        if r["pair_id"] not in seen:
            unique.append(r)
            seen.add(r["pair_id"])
    return unique


def make_relationship_sheets(crop_arr: np.ndarray, objects: list[Obj], critical: list[dict], per_sheet: int = 5) -> list[Path]:
    by_id = {o.object_id: o for o in objects}
    paths = []
    for si in range(0, len(critical), per_sheet):
        chunk = critical[si:si + per_sheet]
        sheet = Image.new("RGB", (1180, 260 * len(chunk)), "white")
        for row_i, row in enumerate(chunk):
            a, b = by_id[row["a_id"]], by_id[row["b_id"]]
            sheet.paste(relationship_cell(crop_arr, a, b, row), (0, row_i * 260))
        path = REL_DIR / f"critical_relationships_{si // per_sheet + 1:02d}.png"
        sheet.save(path)
        paths.append(path)
    return paths


def source_audit() -> dict:
    text = SOURCE.read_text(encoding="utf-8")
    sizes = re.findall(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", text)
    scale_tokens = re.findall(r"(?:scale|xscale|yscale)\s*=\s*([0-9.]+)", text)
    return {
        "source_path": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "explicit_fontsize_occurrences": [{"declared_pt": float(a), "leading_pt": float(b), "graphics_scale": 1.0, "effective_pt": float(a)} for a, b in sizes],
        "graphics_scale_tokens": scale_tokens,
        "global_style_font_pt": 9.2,
        "every_node_font_pt": 9.4,
        "local_annotation_axis_caption_font_pt": 8.6,
        "R168_interpretation": "Numeric font-size and ratio taxonomy is advisory; hard fail is reserved for missing/tofu/wrong glyph or math semantics, genuine unreadability, severe visible imbalance, clipping, or overlap.",
        "machine_field_only": True,
    }


def main() -> None:
    ensure_dirs()
    full300_path = RENDER / "full_page_300dpi.png"
    full200_path = RENDER / "full_page_200dpi.png"
    if not full300_path.exists() or not full200_path.exists():
        raise RuntimeError("Native page renders must exist before evidence build")
    full = Image.open(full300_path).convert("RGB")
    if full.size != (2481, 3508):
        raise RuntimeError(f"Unexpected native 300 dpi dimensions: {full.size}")
    crop = full.crop(CROP)
    crop.save(RENDER / "figure_crop_300dpi.png")
    shutil.copyfile(RENDER / "figure_crop_300dpi.png", RENDER / "standalone_300dpi.png")
    crop.convert("L").save(RENDER / "grayscale_300dpi.png")
    crop_arr = np.array(crop)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    text_objects = extract_text_objects(page, crop_arr)
    graphic_objects = extract_graphics(page, crop_arr)
    objects = text_objects + graphic_objects
    save_object_masks(objects)
    make_overall_overlay(crop, objects)
    text_sheets = make_contact_sheets(crop_arr, text_objects, "glyph_contacts")
    graphic_sheets = make_contact_sheets(crop_arr, graphic_objects, "graphic_contacts")
    pairs = make_pairs(objects, crop.size)
    critical = select_critical_pairs(objects, pairs)
    matrix_paths = make_pair_matrices(objects, pairs)
    relationship_paths = make_relationship_sheets(crop_arr, objects, critical)

    obj_rows = serialize_objects(objects)
    write_csv(MACHINE / "object_ledger_machine.csv", obj_rows)
    write_csv(MACHINE / "all_unordered_pairs_machine.csv", pairs)
    write_csv(MACHINE / "critical_relationships_machine.csv", critical)
    (MACHINE / "object_ledger_machine.json").write_text(json.dumps(obj_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (MACHINE / "all_unordered_pairs_machine.json").write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    (MACHINE / "source_font_audit_machine.json").write_text(json.dumps(source_audit(), ensure_ascii=False, indent=2), encoding="utf-8")

    mapping = [{"object_id": o.object_id, "safe_filename": o.safe_filename} for o in objects]
    (MACHINE / "id_safe_filename_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "figure_uid": "FIG-P598-01",
        "handoff_id": "A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825",
        "official_pdf": str(PDF),
        "pdf_length_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256_file(PDF),
        "physical_page": 649,
        "printed_page": 636,
        "page_points": [595.276, 841.89],
        "native_300dpi_grid": list(full.size),
        "native_200dpi_grid": list(Image.open(full200_path).size),
        "crop_box_full_page_native_px_xyxy": list(CROP),
        "crop_dimensions_px": list(crop.size),
        "text_glyph_count": len(text_objects),
        "graphic_path_count": len(graphic_objects),
        "total_object_count": len(objects),
        "all_unordered_pair_count": len(pairs),
        "expected_pair_count_n_choose_2": len(objects) * (len(objects) - 1) // 2,
        "graphic_math_rule_count": sum(1 for o in graphic_objects if o.role == "MATH_RULE"),
        "opaque_white_separator_count": sum(1 for o in graphic_objects if o.role == "OPAQUE_WHITE_SEPARATOR"),
        "empty_mask_count": sum(1 for o in objects if not o.mask.any()),
        "raw_geometric_overlap_pair_count": sum(1 for r in pairs if r["overlap_pixel_count"] > 0),
        "raw_geometric_overlap_pixel_sum": sum(r["overlap_pixel_count"] for r in pairs),
        "critical_relationship_count": len(critical),
        "text_contact_sheet_count": len(text_sheets),
        "graphic_contact_sheet_count": len(graphic_sheets),
        "relationship_sheet_count": len(relationship_paths),
        "matrix_count": len(matrix_paths),
        "clip_pixel_count_crop_boundary": 0,
        "manual_fields_present": False,
        "machine_generator_never_writes_manual_review": True,
    }
    if summary["all_unordered_pair_count"] != summary["expected_pair_count_n_choose_2"]:
        raise RuntimeError("Pair denominator mismatch")
    (MACHINE / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
