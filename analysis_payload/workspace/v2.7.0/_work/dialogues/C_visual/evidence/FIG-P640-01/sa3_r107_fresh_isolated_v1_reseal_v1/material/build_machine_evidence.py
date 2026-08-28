from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree


PDF_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa3_r107_fresh_isolated_v1")
PAGE_INDEX = 689
PHYSICAL_PAGE = 690
PRINTED_PAGE = 677
FIGURE_NO = "33.7"
UID = "FIG-P640-01"
EXPECTED_PDF_SIZE = 4_967_249
EXPECTED_PDF_SHA256 = "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3"
S300 = 300.0 / 72.0
S200 = 200.0 / 72.0

# These rectangles were located independently from current page-690 vector/text coordinates.
RECT_STANDALONE_PT = fitz.Rect(86.0, 62.0, 516.0, 260.0)
RECT_FIGURE_WITH_CAPTION_PT = fitz.Rect(84.0, 60.0, 522.0, 294.0)
RECT_PANEL_A_PT = fitz.Rect(88.0, 63.0, 348.0, 259.0)
RECT_PANEL_B_PT = fitz.Rect(363.0, 63.0, 516.0, 219.0)
RECT_PAGE_INTEGRATION_PT = fitz.Rect(70.0, 51.0, 535.0, 368.0)


def ensure_dirs() -> dict[str, Path]:
    dirs = {
        "renders": ROOT / "renders",
        "machine": ROOT / "machine",
        "glyph_native": ROOT / "glyphs" / "native",
        "glyph_8x": ROOT / "glyphs" / "eightx",
        "glyph_masks": ROOT / "glyphs" / "raw_masks",
        "contact": ROOT / "glyphs" / "contact_sheets",
        "object_masks": ROOT / "objects" / "raw_masks",
        "critical": ROOT / "critical_relations",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGB" if pix.n == 3 else "RGBA"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def rect_to_px(rect: fitz.Rect, scale: float, page_size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * scale)))
    y0 = max(0, int(math.floor(rect.y0 * scale)))
    x1 = min(page_size[0], int(math.ceil(rect.x1 * scale)))
    y1 = min(page_size[1], int(math.ceil(rect.y1 * scale)))
    return x0, y0, x1, y1


def rgb_from_int(color: int) -> tuple[int, int, int]:
    return fitz.sRGB_to_rgb(int(color))


def rgb_from_pdf_color(color) -> tuple[int, int, int] | None:
    if color is None:
        return None
    if len(color) == 1:
        v = int(round(255 * float(color[0])))
        return v, v, v
    if len(color) == 3:
        return tuple(int(round(255 * float(c))) for c in color)
    return None


def color_line_mask(region_rgb: np.ndarray, target_rgb: tuple[int, int, int], min_contrast: int = 20) -> np.ndarray:
    # Accept antialiased pixels lying on the white-to-target color segment.
    arr = region_rgb.astype(np.float32)
    target = np.array(target_rgb, dtype=np.float32)
    d = 255.0 - target
    denom = float(np.dot(d, d))
    delta = 255.0 - arr
    if denom < 1.0:
        return np.zeros(arr.shape[:2], dtype=bool)
    alpha = np.tensordot(delta, d, axes=([2], [0])) / denom
    recon = 255.0 - alpha[..., None] * d[None, None, :]
    residual = np.max(np.abs(recon - arr), axis=2)
    contrast = np.max(delta, axis=2)
    return (alpha > 0.0) & (alpha <= 1.12) & (contrast >= min_contrast) & (residual <= 10.0)


def pt_xy(p) -> tuple[int, int]:
    return int(round(float(p.x) * S300)), int(round(float(p.y) * S300))


def cubic_points(p0, p1, p2, p3, steps: int = 36) -> np.ndarray:
    t = np.linspace(0.0, 1.0, steps + 1)[:, None]
    a = np.array(pt_xy(p0), dtype=np.float64)
    b = np.array(pt_xy(p1), dtype=np.float64)
    c = np.array(pt_xy(p2), dtype=np.float64)
    d = np.array(pt_xy(p3), dtype=np.float64)
    pts = (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
    return np.rint(pts).astype(np.int32)


def vector_geometry_mask(drawing: dict, page_size: tuple[int, int]) -> np.ndarray:
    """Raster corridor from PDF vectors, intersected later with official pixels."""
    mask = np.zeros((page_size[1], page_size[0]), dtype=np.uint8)
    width_pt = float(drawing.get("width") or 0.8)
    thickness = max(2, int(math.ceil(width_pt * S300)) + 2)
    fill = drawing.get("type") in {"f", "fs"}
    for item in drawing.get("items", []):
        op = item[0]
        if op == "l":
            cv2.line(mask, pt_xy(item[1]), pt_xy(item[2]), 255, thickness=thickness, lineType=cv2.LINE_8)
        elif op == "c":
            pts = cubic_points(item[1], item[2], item[3], item[4])
            cv2.polylines(mask, [pts], False, 255, thickness=thickness, lineType=cv2.LINE_8)
        elif op == "re":
            r = item[1]
            pts = np.array([pt_xy(r.tl), pt_xy(r.tr), pt_xy(r.br), pt_xy(r.bl)], dtype=np.int32)
            if fill:
                cv2.fillPoly(mask, [pts], 255, lineType=cv2.LINE_8)
            else:
                cv2.polylines(mask, [pts], True, 255, thickness=thickness, lineType=cv2.LINE_8)
        elif op == "qu":
            q = item[1]
            pts = np.array([pt_xy(q.ul), pt_xy(q.ur), pt_xy(q.lr), pt_xy(q.ll)], dtype=np.int32)
            if fill:
                cv2.fillPoly(mask, [pts], 255, lineType=cv2.LINE_8)
            else:
                cv2.polylines(mask, [pts], True, 255, thickness=thickness, lineType=cv2.LINE_8)
    return mask.astype(bool)


def class_for_char(ch: str, span_size: float, parent_max_size: float) -> tuple[str, int]:
    if span_size < 0.82 * parent_max_size:
        return "NATURAL_SCRIPT", 15
    code = ord(ch)
    if (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or unicodedata.east_asian_width(ch) in {"W", "F"}
    ):
        return "CJK_FULL", 30
    if ch.isdigit() or ("A" <= ch <= "Z"):
        return "LATIN_UPPER_OR_DIGIT", 24
    if ("a" <= ch <= "z") or (0x0370 <= code <= 0x03FF and ch.islower()):
        return "LATIN_GREEK_LOWER", 17
    if ch in {".", ",", "，", "。", "：", ":", ";", "；"}:
        return "LOW_PROFILE_PUNCTUATION", 0
    return "BASE_MATH_OR_SYMBOL", 22


def role_parent_for_bbox(rect: fitz.Rect) -> tuple[str, str, str]:
    cx = (rect.x0 + rect.x1) / 2
    cy = (rect.y0 + rect.y1) / 2
    if cx < 360:
        panel = "A"
        if cy < 90:
            return "TXT-A-TITLE", panel, "PANEL_TITLE"
        if cy > 240:
            if cx < 215:
                return "TXT-A-LEGEND-095", panel, "LEGEND"
            if cx < 280:
                return "TXT-A-LEGEND-070", panel, "LEGEND"
            return "TXT-A-LEGEND-020", panel, "LEGEND"
        if cy > 222:
            return "TXT-A-XLABEL", panel, "AXIS_TITLE"
        if cx < 116:
            return "TXT-A-YLABEL", panel, "AXIS_TITLE"
        if cx < 138:
            return "TXT-A-YTICKS", panel, "TICK_LABEL"
        if cy > 204:
            return "TXT-A-XTICKS", panel, "TICK_LABEL"
        return "TXT-A-OTHER", panel, "ANNOTATION"
    panel = "B"
    if cy < 105:
        return "TXT-B-TITLE", panel, "PANEL_TITLE_FORMULA"
    if cx > 445 and 108 <= cy <= 140:
        return "TXT-B-LIMIT-ANNOTATION", panel, "ANNOTATION_FORMULA"
    if cx > 445 and 160 <= cy <= 181:
        return "TXT-B-POINT-ANNOTATION", panel, "ANNOTATION_FORMULA"
    if cx < 390 and 120 <= cy <= 170:
        return "TXT-B-YLABEL", panel, "AXIS_TITLE_FORMULA"
    if cx < 406 and 100 <= cy <= 190:
        return "TXT-B-YTICKS", panel, "TICK_LABEL"
    if cy > 199:
        return "TXT-B-XLABEL", panel, "AXIS_TITLE_FORMULA"
    if cy > 185:
        return "TXT-B-XTICKS", panel, "TICK_LABEL"
    return "TXT-B-OTHER", panel, "ANNOTATION"


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def make_triptych(original: Image.Image, local_mask: np.ndarray, label: str, scale8: bool) -> Image.Image:
    rgb = np.asarray(original.convert("RGB")).copy()
    overlay = rgb.copy()
    overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_rgb = np.full_like(rgb, 255)
    mask_rgb[local_mask] = 0
    imgs = [Image.fromarray(rgb), Image.fromarray(overlay), Image.fromarray(mask_rgb)]
    if scale8:
        imgs = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in imgs]
    w = sum(i.width for i in imgs) + 20
    h = max(i.height for i in imgs) + 34
    out = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(out)
    dr.text((4, 2), label, fill="black")
    x = 0
    for name, im in zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), imgs):
        out.paste(im, (x, 28))
        dr.text((x + 3, 14), name, fill="black")
        x += im.width + 10
    return out


def mask_points(mask: np.ndarray, x0: int, y0: int) -> set[tuple[int, int]]:
    ys, xs = np.nonzero(mask)
    return set(zip((xs + x0).tolist(), (ys + y0).tolist()))


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def exact_mask_distance(a_pts: set[tuple[int, int]], b_pts: set[tuple[int, int]], a_bbox, b_bbox) -> float:
    if a_pts & b_pts:
        return 0.0
    x0 = min(a_bbox[0], b_bbox[0]) - 2
    y0 = min(a_bbox[1], b_bbox[1]) - 2
    x1 = max(a_bbox[2], b_bbox[2]) + 2
    y1 = max(a_bbox[3], b_bbox[3]) + 2
    if (x1 - x0) * (y1 - y0) > 8_000_000:
        return bbox_distance(a_bbox, b_bbox)
    aa = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    bb = np.zeros_like(aa)
    for x, y in a_pts:
        aa[y - y0, x - x0] = True
    for x, y in b_pts:
        bb[y - y0, x - x0] = True
    dt = distance_transform_edt(~aa)
    vals = dt[bb]
    return float(vals.min()) if vals.size else float("inf")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    dirs = ensure_dirs()
    pdf_size = PDF_PATH.stat().st_size
    pdf_sha = sha256_file(PDF_PATH)
    doc = fitz.open(PDF_PATH)
    if pdf_size != EXPECTED_PDF_SIZE or pdf_sha != EXPECTED_PDF_SHA256 or doc.page_count != 817:
        raise RuntimeError("official PDF identity mismatch")
    page = doc[PAGE_INDEX]
    page_w, page_h = page.rect.width, page.rect.height

    # Native PDF renders; all 300 dpi derivatives are integer crops with no resize.
    pix300 = page.get_pixmap(matrix=fitz.Matrix(S300, S300), alpha=False, colorspace=fitz.csRGB)
    full300 = pix_to_pil(pix300).convert("RGB")
    full300.save(dirs["renders"] / "full_page_300dpi_native.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(S200, S200), alpha=False, colorspace=fitz.csRGB)
    full200 = pix_to_pil(pix200).convert("RGB")
    full200.save(dirs["renders"] / "full_page_200dpi.png")
    full200.save(ROOT / "full_page_200dpi.png")

    render_specs = {
        "figure_crop_300dpi.png": RECT_FIGURE_WITH_CAPTION_PT,
        "standalone_300dpi.png": RECT_STANDALONE_PT,
        "panel_a_300dpi.png": RECT_PANEL_A_PT,
        "panel_b_300dpi.png": RECT_PANEL_B_PT,
    }
    crop_records = []
    for name, rect in render_specs.items():
        pxrect = rect_to_px(rect, S300, full300.size)
        im = full300.crop(pxrect)
        im.save(dirs["renders"] / name)
        if name in {"figure_crop_300dpi.png", "standalone_300dpi.png"}:
            im.save(ROOT / name)
        crop_records.append({"view": name, "dpi": 300, "pt_rect": list(rect), "px_rect_full_page": pxrect, "native_dimensions": im.size, "resized": False})
    fig = Image.open(dirs["renders"] / "figure_crop_300dpi.png").convert("RGB")
    ImageOps.grayscale(fig).save(dirs["renders"] / "grayscale_300dpi.png")
    ImageOps.grayscale(fig).save(ROOT / "grayscale_300dpi.png")
    crop_records.append({"view": "grayscale_300dpi.png", "dpi": 300, "pt_rect": list(RECT_FIGURE_WITH_CAPTION_PT), "px_rect_full_page": rect_to_px(RECT_FIGURE_WITH_CAPTION_PT, S300, full300.size), "native_dimensions": fig.size, "resized": False, "conversion": "RGB_to_L_only"})
    integ_rect200 = rect_to_px(RECT_PAGE_INTEGRATION_PT, S200, full200.size)
    integ = full200.crop(integ_rect200)
    integ.save(dirs["renders"] / "page_integration_200dpi.png")
    crop_records.append({"view": "page_integration_200dpi.png", "dpi": 200, "pt_rect": list(RECT_PAGE_INTEGRATION_PT), "px_rect_full_page": integ_rect200, "native_dimensions": integ.size, "resized": False})

    raw = page.get_text("rawdict")
    raw_chars = []
    line_no = 0
    for block_no, block in enumerate(raw.get("blocks", [])):
        for line in block.get("lines", []):
            line_no += 1
            line_chars = [c for s in line.get("spans", []) for c in s.get("chars", []) if c.get("c") and not c.get("c").isspace()]
            if not line_chars:
                continue
            line_max = max(float(s.get("size", 0.0)) for s in line.get("spans", []))
            for span_no, span in enumerate(line.get("spans", [])):
                expected_rgb = rgb_from_int(span.get("color", 0))
                for char_no, ch in enumerate(span.get("chars", [])):
                    text = ch.get("c", "")
                    if not text or text.isspace():
                        continue
                    bbox = fitz.Rect(ch["bbox"])
                    if not RECT_STANDALONE_PT.intersects(bbox):
                        continue
                    parent, panel, role = role_parent_for_bbox(bbox)
                    raw_chars.append({
                        "text": text,
                        "bbox_pt": bbox,
                        "origin_pt": ch.get("origin"),
                        "font": span.get("font", ""),
                        "span_size_pt": float(span.get("size", 0.0)),
                        "span_flags": int(span.get("flags", 0)),
                        "bidi": int(span.get("bidi", 0)),
                        "color_int": int(span.get("color", 0)),
                        "expected_rgb": expected_rgb,
                        "line_dir": line.get("dir", (1.0, 0.0)),
                        "line_max_size_pt": line_max,
                        "block_no": block_no,
                        "line_no": line_no,
                        "span_no": span_no,
                        "char_no": char_no,
                        "parent": parent,
                        "panel": panel,
                        "role": role,
                    })

    page_arr = np.asarray(full300)
    # Partition tightly kerned / rotated raw character bboxes along each PDF text
    # line direction. This prevents the bbox of one glyph from claiming antialias
    # pixels belonging to its neighbour; the partition itself makes no judgment.
    line_members: dict[int, list[int]] = defaultdict(list)
    for raw_idx, item in enumerate(raw_chars):
        line_members[item["line_no"]].append(raw_idx)
    projection_bounds: dict[int, tuple[float, float, float, float]] = {}
    raw_bbox_px = [rect_to_px(item["bbox_pt"], S300, full300.size) for item in raw_chars]
    for members in line_members.values():
        dx, dy = raw_chars[members[0]]["line_dir"]
        ordered = sorted(
            members,
            key=lambda j: dx * ((raw_chars[j]["bbox_pt"].x0 + raw_chars[j]["bbox_pt"].x1) * 0.5 * S300)
            + dy * ((raw_chars[j]["bbox_pt"].y0 + raw_chars[j]["bbox_pt"].y1) * 0.5 * S300),
        )
        centers = [
            dx * ((raw_chars[j]["bbox_pt"].x0 + raw_chars[j]["bbox_pt"].x1) * 0.5 * S300)
            + dy * ((raw_chars[j]["bbox_pt"].y0 + raw_chars[j]["bbox_pt"].y1) * 0.5 * S300)
            for j in ordered
        ]
        for k, j in enumerate(ordered):
            lo = -float("inf") if k == 0 else (centers[k - 1] + centers[k]) * 0.5
            hi = float("inf") if k == len(ordered) - 1 else (centers[k] + centers[k + 1]) * 0.5
            projection_bounds[j] = (lo, hi, float(dx), float(dy))

    glyph_rows = []
    glyph_masks_global: dict[str, tuple[np.ndarray, tuple[int, int, int, int], set[tuple[int, int]]]] = {}
    parent_glyphs: dict[str, list[str]] = defaultdict(list)
    contact_entries = []
    for raw_idx, item in enumerate(raw_chars):
        idx = raw_idx + 1
        gid = f"GLYPH-{idx:04d}"
        bbox_px = rect_to_px(item["bbox_pt"], S300, full300.size)
        x0, y0, x1, y1 = bbox_px
        region = page_arr[y0:y1, x0:x1, :]
        mask = color_line_mask(region, item["expected_rgb"], min_contrast=20)
        lo, hi, dx, dy = projection_bounds[raw_idx]
        yy, xx = np.indices(mask.shape)
        global_x = xx + x0
        global_y = yy + y0
        proj = dx * global_x + dy * global_y
        mask &= (proj >= lo) & (proj < hi)
        # Use pixel-centre membership in the exact PDF char bbox so floor-rounded
        # crop pixels do not import a neighbour's antialias fringe.
        bx = item["bbox_pt"]
        corners = [
            (bx.x0 * S300, bx.y0 * S300), (bx.x1 * S300, bx.y0 * S300),
            (bx.x1 * S300, bx.y1 * S300), (bx.x0 * S300, bx.y1 * S300),
        ]
        char_proj = [dx * px + dy * py for px, py in corners]
        proj_center = dx * (global_x + 0.5) + dy * (global_y + 0.5)
        mask &= (proj_center >= min(char_proj)) & (proj_center < max(char_proj))
        # Same-parent text can have overlapping vector bboxes across adjacent raw
        # lines (notably the two-line fraction below the panel title). Assign those
        # ambiguous same-colour pixels to the nearest glyph center in 2-D.
        own_cx, own_cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        own_d2 = (global_x - own_cx) ** 2 + (global_y - own_cy) ** 2
        for other_idx, other in enumerate(raw_chars):
            if other_idx == raw_idx or other["parent"] != item["parent"] or other["expected_rgb"] != item["expected_rgb"]:
                continue
            ox0, oy0, ox1, oy1 = raw_bbox_px[other_idx]
            if ox1 <= x0 or ox0 >= x1 or oy1 <= y0 or oy0 >= y1:
                continue
            ocx, ocy = (ox0 + ox1) * 0.5, (oy0 + oy1) * 0.5
            other_d2 = (global_x - ocx) ** 2 + (global_y - ocy) ** 2
            inside_other = (global_x >= ox0) & (global_x < ox1) & (global_y >= oy0) & (global_y < oy1)
            mask &= ~(inside_other & (other_d2 < own_d2))
        tbb = tight_bbox(mask)
        h_ink = 0 if tbb is None else tbb[3] - tbb[1]
        w_ink = 0 if tbb is None else tbb[2] - tbb[0]
        ink_px = int(mask.sum())
        script_class, nominal_threshold = class_for_char(item["text"], item["span_size_pt"], item["line_max_size_pt"])
        mask_path = dirs["glyph_masks"] / f"{gid}.png"
        save_mask(mask, mask_path)
        pad = 5
        cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
        cx1, cy1 = min(full300.width, x1 + pad), min(full300.height, y1 + pad)
        context = full300.crop((cx0, cy0, cx1, cy1)).convert("RGB")
        context_mask = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
        context_mask[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0] = mask
        label = f"{gid}  U+{ord(item['text']):04X}  {item['text']}  parent={item['parent']}  bbox={bbox_px}  H={h_ink}px"
        trip1 = make_triptych(context, context_mask, label, scale8=False)
        trip8 = make_triptych(context, context_mask, label, scale8=True)
        native_path = dirs["glyph_native"] / f"{gid}_triptych_native1x.png"
        eight_path = dirs["glyph_8x"] / f"{gid}_triptych_8x_nearest.png"
        trip1.save(native_path)
        trip8.save(eight_path)
        parent_glyphs[item["parent"]].append(gid)
        pts = mask_points(mask, x0, y0)
        glyph_masks_global[gid] = (mask, bbox_px, pts)
        glyph_rows.append({
            "glyph_id": gid,
            "char": item["text"],
            "codepoint": f"U+{ord(item['text']):04X}",
            "unicode_name": unicodedata.name(item["text"], "UNNAMED"),
            "parent_object_id": item["parent"],
            "panel_id": item["panel"],
            "role": item["role"],
            "font": item["font"],
            "pdf_span_size_pt": f"{item['span_size_pt']:.4f}",
            "line_max_size_pt": f"{item['line_max_size_pt']:.4f}",
            "script_class": script_class,
            "protocol_nominal_threshold_px": nominal_threshold,
            "bbox_pt": ";".join(f"{v:.4f}" for v in item["bbox_pt"]),
            "bbox_px_fullpage": ";".join(str(v) for v in bbox_px),
            "h_ink_px": h_ink,
            "w_ink_px": w_ink,
            "ink_pixel_count": ink_px,
            "mask_empty": str(ink_px == 0).lower(),
            "expected_rgb": ";".join(str(v) for v in item["expected_rgb"]),
            "source_pdf": str(PDF_PATH),
            "physical_page": PHYSICAL_PAGE,
            "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
            "native1x_triptych_path": str(native_path.relative_to(ROOT)).replace("\\", "/"),
            "eightx_triptych_path": str(eight_path.relative_to(ROOT)).replace("\\", "/"),
            "machine_only_no_manual_decision": "true",
            "neighbor_partition": "pdf_line_direction_voronoi",
        })
        contact_entries.append((gid, trip8.copy()))

    # Compact contact sheets: every cell is the exact 8x-nearest triptych already saved above.
    per_sheet = 5
    contact_index_rows = []
    for sheet_idx in range(0, len(contact_entries), per_sheet):
        entries = contact_entries[sheet_idx:sheet_idx + per_sheet]
        widths = [im.width for _, im in entries]
        heights = [im.height for _, im in entries]
        sheet = Image.new("RGB", (max(widths), sum(heights) + 10 * (len(entries) - 1)), "white")
        y = 0
        sheet_name = f"glyph_contact_sheet_{sheet_idx // per_sheet + 1:03d}_8x_nearest.png"
        for cell_no, (gid, im) in enumerate(entries, start=1):
            sheet.paste(im, (0, y))
            contact_index_rows.append({"glyph_id": gid, "sheet": sheet_name, "cell": cell_no})
            y += im.height + 10
        sheet.save(dirs["contact"] / sheet_name)

    glyph_fields = list(glyph_rows[0].keys())
    write_csv(dirs["machine"] / "machine_glyph_inventory.csv", glyph_rows, glyph_fields)
    write_csv(ROOT / "after_pixel_measurements.csv", glyph_rows, glyph_fields)
    write_csv(dirs["machine"] / "machine_glyph_contact_index.csv", contact_index_rows, ["glyph_id", "sheet", "cell"])

    # Every visible drawing record in the standalone figure is assigned exactly once.
    drawings = page.get_drawings(extended=True)
    # Use inclusive coordinate overlap instead of Rect.intersects: stroked rules may
    # have zero-height / zero-width vector bboxes while remaining visibly rendered.
    selected_drawing_indices = [
        i for i, d in enumerate(drawings)
        if d["rect"].x1 >= RECT_STANDALONE_PT.x0
        and d["rect"].x0 <= RECT_STANDALONE_PT.x1
        and d["rect"].y1 >= RECT_STANDALONE_PT.y0
        and d["rect"].y0 <= RECT_STANDALONE_PT.y1
        and d["rect"].y0 >= 62
        and d["rect"].y1 <= 260
    ]
    group_defs = {
        "GFX-A-AXES-TICKS": [1, 2, 3],
        "GFX-A-CURVE-RHO095": [4],
        "GFX-A-CURVE-RHO070": [5],
        "GFX-A-CURVE-RHO020": [6],
        "GFX-A-LEGEND-SWATCH-095": [7],
        "GFX-A-LEGEND-SWATCH-070": [8],
        "GFX-A-LEGEND-SWATCH-020": [9],
        "GFX-B-AXES-TICKS": [10, 11, 12, 13, 14, 15],
        "GFX-B-CURVE-ESS": [16],
        "BG-B-POINT-ANNOTATION": [17],
        "BG-B-LIMIT-ANNOTATION": [18],
        "GFX-B-ENDPOINT-MARKER": [19],
        "GFX-B-TITLE-FRACTION-RULE": [20],
    }
    assigned = sorted(i for members in group_defs.values() for i in members)
    if selected_drawing_indices != assigned:
        raise RuntimeError(f"drawing denominator mismatch: selected={selected_drawing_indices} assigned={assigned}")

    drawing_rows = []
    drawing_to_group = {i: g for g, members in group_defs.items() for i in members}
    for i in selected_drawing_indices:
        d = drawings[i]
        r = d["rect"]
        drawing_rows.append({
            "pdf_drawing_index": i,
            "semantic_object_id": drawing_to_group[i],
            "draw_type": d.get("type"),
            "rect_pt": ";".join(f"{v:.4f}" for v in r),
            "stroke_rgb": "" if d.get("color") is None else ";".join(str(v) for v in rgb_from_pdf_color(d.get("color"))),
            "fill_rgb": "" if d.get("fill") is None else ";".join(str(v) for v in rgb_from_pdf_color(d.get("fill"))),
            "width_pt": "" if d.get("width") is None else f"{float(d.get('width')):.5f}",
            "item_count": len(d.get("items", [])),
            "is_math_rule": str(i == 20).lower(),
            "is_opaque_background": str(i in {17, 18}).lower(),
            "machine_only_no_manual_decision": "true",
        })
    write_csv(dirs["machine"] / "machine_pdf_drawing_inventory.csv", drawing_rows, list(drawing_rows[0].keys()))

    # Build semantic text masks by unioning glyph raw masks.
    semantic_objects = []
    object_masks: dict[str, dict] = {}
    for parent in sorted(parent_glyphs):
        gids = parent_glyphs[parent]
        pts = set()
        for gid in gids:
            pts.update(glyph_masks_global[gid][2])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        bbox = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        x0, y0, x1, y1 = bbox
        local = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        for x, y in pts:
            local[y - y0, x - x0] = True
        path = dirs["object_masks"] / f"{parent}.png"
        save_mask(local, path)
        panel = parent.split("-")[1]
        role = next(row["role"] for row in glyph_rows if row["parent_object_id"] == parent)
        object_masks[parent] = {"points": pts, "bbox": bbox, "foreground": True, "kind": "TEXT", "panel": panel, "role": role, "mask_path": path}
        semantic_objects.append({
            "object_id": parent, "kind": "TEXT", "panel_id": panel, "role": role,
            "member_ids": ";".join(gids), "member_count": len(gids),
            "bbox_px_fullpage": ";".join(str(v) for v in bbox), "raw_mask_pixel_count": len(pts),
            "foreground": "true", "mask_type": "final_visible_raw_20_of_255",
            "mask_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "machine_only_no_manual_decision": "true",
        })

    # Subtract all text pixels when color-segmenting drawings to avoid glyph contamination.
    all_text_pts = set().union(*(d["points"] for d in object_masks.values()))
    for group_id, members in group_defs.items():
        group_pts: set[tuple[int, int]] = set()
        is_bg = all(i in {17, 18} for i in members)
        for i in members:
            d = drawings[i]
            if i in {17, 18}:
                # PDF opaque fill coverage, retained separately from foreground semantics.
                rect_px = rect_to_px(d["rect"], S300, full300.size)
                x0, y0, x1, y1 = rect_px
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        group_pts.add((x, y))
                continue
            target = rgb_from_pdf_color(d.get("color") if d.get("color") is not None else d.get("fill"))
            if target is None:
                continue
            geometry = vector_geometry_mask(d, full300.size)
            ys, xs = np.nonzero(geometry)
            gx0, gy0, gx1, gy1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
            color_mask = color_line_mask(page_arr[gy0:gy1, gx0:gx1, :], target, min_contrast=20)
            m = color_mask & geometry[gy0:gy1, gx0:gx1]
            pts = mask_points(m, gx0, gy0)
            pts.difference_update(all_text_pts)
            group_pts.update(pts)
        if not group_pts:
            raise RuntimeError(f"empty drawing group mask: {group_id}")
        xs = [p[0] for p in group_pts]
        ys = [p[1] for p in group_pts]
        bbox = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        x0, y0, x1, y1 = bbox
        local = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        for x, y in group_pts:
            local[y - y0, x - x0] = True
        path = dirs["object_masks"] / f"{group_id}.png"
        save_mask(local, path)
        panel = "A" if "-A-" in group_id else "B"
        is_math_rule = group_id == "GFX-B-TITLE-FRACTION-RULE"
        role = "OPAQUE_BACKGROUND" if is_bg else ("MATH_RULE" if is_math_rule else "DRAWING")
        kind = "BACKGROUND" if is_bg else ("GRAPHIC_MATH_RULE" if is_math_rule else "GRAPHIC")
        object_masks[group_id] = {"points": group_pts, "bbox": bbox, "foreground": not is_bg, "kind": kind, "panel": panel, "role": role, "mask_path": path}
        semantic_objects.append({
            "object_id": group_id, "kind": kind, "panel_id": panel, "role": role,
            "member_ids": ";".join(f"PDF-DRAW-{i}" for i in members), "member_count": len(members),
            "bbox_px_fullpage": ";".join(str(v) for v in bbox), "raw_mask_pixel_count": len(group_pts),
            "foreground": str(not is_bg).lower(), "mask_type": "opaque_coverage" if is_bg else "final_visible_raw_20_of_255",
            "mask_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "machine_only_no_manual_decision": "true",
        })

    semantic_objects.sort(key=lambda r: r["object_id"])
    write_csv(dirs["machine"] / "machine_semantic_object_inventory.csv", semantic_objects, list(semantic_objects[0].keys()))

    # Machine-only measurement overlay.  It records every glyph bbox/ID and every
    # semantic object bbox/ID/role on the native 300 dpi raster; it carries no
    # reviewer decision.  Glyph labels are intentionally compact and remain
    # readable under ordinary zoom because the saved image is not downsampled.
    overlay = full300.copy()
    odraw = ImageDraw.Draw(overlay)
    glyph_font = ImageFont.load_default(size=8)
    object_font = ImageFont.load_default(size=11)
    for row in glyph_rows:
        x0, y0, x1, y1 = (int(v) for v in row["bbox_px_fullpage"].split(";"))
        odraw.rectangle((x0, y0, x1, y1), outline=(0, 110, 255), width=1)
        odraw.text((x0, max(0, y0 - 9)), row["glyph_id"].replace("GLYPH-", "G"), fill=(0, 70, 190), font=glyph_font)
    object_colors = {
        "TEXT": (210, 0, 180),
        "GRAPHIC": (220, 40, 20),
        "GRAPHIC_MATH_RULE": (130, 0, 220),
        "BACKGROUND": (0, 145, 65),
    }
    for row in semantic_objects:
        x0, y0, x1, y1 = (int(v) for v in row["bbox_px_fullpage"].split(";"))
        color = object_colors[row["kind"]]
        odraw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        odraw.text((x0, max(0, y0 - 13)), f'{row["object_id"]} [{row["role"]}]', fill=color, font=object_font)
    overlay_rect = rect_to_px(RECT_STANDALONE_PT, S300, full300.size)
    measurement_overlay = overlay.crop(overlay_rect)
    measurement_overlay.save(dirs["renders"] / "text_measurement_overlay_300dpi.png")
    measurement_overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Complete unordered pair denominator. No human decision columns are created.
    object_ids = sorted(object_masks)
    pair_rows = []
    critical_rows = []
    design_parent_pairs = {
        frozenset(("TXT-A-LEGEND-095", "GFX-A-LEGEND-SWATCH-095")),
        frozenset(("TXT-A-LEGEND-070", "GFX-A-LEGEND-SWATCH-070")),
        frozenset(("TXT-A-LEGEND-020", "GFX-A-LEGEND-SWATCH-020")),
        frozenset(("TXT-B-POINT-ANNOTATION", "BG-B-POINT-ANNOTATION")),
        frozenset(("TXT-B-LIMIT-ANNOTATION", "BG-B-LIMIT-ANNOTATION")),
        frozenset(("TXT-B-TITLE", "GFX-B-TITLE-FRACTION-RULE")),
        frozenset(("GFX-B-ENDPOINT-MARKER", "BG-B-POINT-ANNOTATION")),
    }
    pair_no = 0
    for ia, aid in enumerate(object_ids):
        a = object_masks[aid]
        for bid in object_ids[ia + 1:]:
            pair_no += 1
            b = object_masks[bid]
            pair_id = f"PAIR-{pair_no:04d}"
            overlap = len(a["points"] & b["points"])
            bdist = bbox_distance(a["bbox"], b["bbox"])
            exact = ""
            method = "bbox_lower_bound"
            if bdist <= 24 or overlap > 0:
                exact = exact_mask_distance(a["points"], b["points"], a["bbox"], b["bbox"])
                method = "exact_native_pixel_edt"
            policy_hint = "DESIGN_COMPOSITION_CANDIDATE" if frozenset((aid, bid)) in design_parent_pairs else "INDEPENDENT_OBJECT_PAIR"
            row = {
                "pair_id": pair_id,
                "object_a": aid,
                "object_b": bid,
                "kind_a": a["kind"],
                "kind_b": b["kind"],
                "panel_a": a["panel"],
                "panel_b": b["panel"],
                "role_a": a["role"],
                "role_b": b["role"],
                "bbox_clearance_px": f"{bdist:.3f}",
                "raw_mask_overlap_px": overlap,
                "min_raw_mask_distance_px": "" if exact == "" else f"{exact:.3f}",
                "distance_method": method,
                "machine_policy_hint_not_decision": policy_hint,
                "machine_only_no_manual_decision": "true",
            }
            pair_rows.append(row)
            mandatory = (a["kind"] == "TEXT" or b["kind"] == "TEXT") and (
                a["kind"] != "BACKGROUND" and b["kind"] != "BACKGROUND"
            )
            if overlap > 0 or bdist <= 20 or mandatory and bdist <= 36 or frozenset((aid, bid)) in design_parent_pairs:
                critical_rows.append({**row, "critical_reason_machine": "raw_overlap" if overlap > 0 else ("design_composition" if frozenset((aid, bid)) in design_parent_pairs else "proximity_or_mandatory_class")})

    expected_pairs = len(object_ids) * (len(object_ids) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise RuntimeError("pair denominator mismatch")
    write_csv(dirs["machine"] / "machine_all_unordered_pairs.csv", pair_rows, list(pair_rows[0].keys()))
    write_csv(dirs["machine"] / "machine_critical_relation_candidates.csv", critical_rows, list(critical_rows[0].keys()))

    # Critical relation native 1x and 8x four-panel evidence (original, A, B, intersection).
    critical_index = []
    for row in critical_rows:
        aid, bid = row["object_a"], row["object_b"]
        a, b = object_masks[aid], object_masks[bid]
        common = a["points"] & b["points"]
        if common:
            p = sorted(common)[len(common) // 2]
            pa = pb = p
        else:
            aa = np.array(sorted(a["points"]), dtype=np.float64)
            bb = np.array(sorted(b["points"]), dtype=np.float64)
            if len(aa) <= len(bb):
                dist, idx = cKDTree(bb).query(aa, k=1)
                j = int(np.argmin(dist)); pa = tuple(aa[j].astype(int)); pb = tuple(bb[int(idx[j])].astype(int))
            else:
                dist, idx = cKDTree(aa).query(bb, k=1)
                j = int(np.argmin(dist)); pb = tuple(bb[j].astype(int)); pa = tuple(aa[int(idx[j])].astype(int))
        pad = 36
        x0 = max(0, min(pa[0], pb[0]) - pad)
        y0 = max(0, min(pa[1], pb[1]) - pad)
        x1 = min(full300.width, max(pa[0], pb[0]) + pad + 1)
        y1 = min(full300.height, max(pa[1], pb[1]) + pad + 1)
        orig = np.asarray(full300.crop((x0, y0, x1, y1)).convert("RGB")).copy()
        ma = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        mb = np.zeros_like(ma)
        for x, y in a["points"]:
            if x0 <= x < x1 and y0 <= y < y1:
                ma[y - y0, x - x0] = True
        for x, y in b["points"]:
            if x0 <= x < x1 and y0 <= y < y1:
                mb[y - y0, x - x0] = True
        va = orig.copy(); va[ma] = [255, 0, 0]
        vb = orig.copy(); vb[mb] = [0, 80, 255]
        inter = np.full_like(orig, 255); inter[ma] = [255, 0, 0]; inter[mb] = [0, 80, 255]; inter[ma & mb] = [255, 0, 255]
        panels = [Image.fromarray(orig), Image.fromarray(va), Image.fromarray(vb), Image.fromarray(inter)]
        labels = ["ORIGINAL", "A RED", "B BLUE", "INTERSECTION MAGENTA"]
        native = Image.new("RGB", (sum(im.width for im in panels) + 30, max(im.height for im in panels) + 32), "white")
        dr = ImageDraw.Draw(native)
        x = 0
        for lab, im in zip(labels, panels):
            native.paste(im, (x, 28)); dr.text((x + 2, 10), lab, fill="black"); x += im.width + 10
        base = dirs["critical"] / row["pair_id"]
        native_path = base.with_name(base.name + "_native1x.png")
        eight_path = base.with_name(base.name + "_8x_nearest.png")
        native.save(native_path)
        native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(eight_path)
        critical_index.append({
            "pair_id": row["pair_id"], "roi_px_fullpage": f"{x0};{y0};{x1};{y1}",
            "nearest_pixel_a_fullpage": f"{pa[0]};{pa[1]}",
            "nearest_pixel_b_fullpage": f"{pb[0]};{pb[1]}",
            "native1x_path": str(native_path.relative_to(ROOT)).replace("\\", "/"),
            "eightx_path": str(eight_path.relative_to(ROOT)).replace("\\", "/"),
        })
    write_csv(dirs["machine"] / "machine_critical_evidence_index.csv", critical_index, ["pair_id", "roi_px_fullpage", "nearest_pixel_a_fullpage", "nearest_pixel_b_fullpage", "native1x_path", "eightx_path"])

    # Pixel and role summaries remain machine observations only.
    role_groups = defaultdict(list)
    for row in glyph_rows:
        if row["script_class"] != "LOW_PROFILE_PUNCTUATION":
            role_groups[(row["panel_id"], row["role"], row["script_class"])].append(int(row["h_ink_px"]))
    role_rows = []
    for (panel, role, cls), vals in sorted(role_groups.items()):
        med = float(np.median(vals))
        role_rows.append({
            "panel_id": panel, "role": role, "script_class": cls, "glyph_count": len(vals),
            "min_h_ink_px": min(vals), "median_h_ink_px": f"{med:.3f}", "max_h_ink_px": max(vals),
            "max_over_min": f"{max(vals) / min(vals):.4f}" if min(vals) else "INF",
            "machine_only_no_manual_decision": "true",
        })
    write_csv(dirs["machine"] / "machine_role_pixel_stats.csv", role_rows, list(role_rows[0].keys()))

    caption_text = " ".join(
        span.get("text", "")
        for b in page.get_text("dict").get("blocks", [])
        for line in b.get("lines", [])
        for span in line.get("spans", [])
        if 260 <= span.get("bbox", (0, 0, 0, 0))[1] < 294
    )
    identity = {
        "uid": UID,
        "figure_no": FIGURE_NO,
        "official_pdf": str(PDF_PATH),
        "pdf_size_bytes": pdf_size,
        "pdf_sha256": pdf_sha,
        "pdf_pages": doc.page_count,
        "physical_page": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "page_size_pt": [page_w, page_h],
        "page_300dpi_native_dimensions": full300.size,
        "page_200dpi_native_dimensions": full200.size,
        "caption_extracted_current_page": caption_text,
        "current_source": str(SOURCE_PATH),
        "crop_records": crop_records,
    }
    (dirs["machine"] / "machine_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

    glyph_ids_for_overlap = sorted(glyph_masks_global)
    glyph_pair_overlap_pairs = []
    for ia, ga in enumerate(glyph_ids_for_overlap):
        for gb in glyph_ids_for_overlap[ia + 1:]:
            ov = len(glyph_masks_global[ga][2] & glyph_masks_global[gb][2])
            if ov:
                glyph_pair_overlap_pairs.append((ga, gb, ov))
    write_csv(
        dirs["machine"] / "machine_glyph_cross_mask_overlaps.csv",
        [{"glyph_a": a, "glyph_b": b, "overlap_px": v, "machine_only_no_manual_decision": "true"} for a, b, v in glyph_pair_overlap_pairs],
        ["glyph_a", "glyph_b", "overlap_px", "machine_only_no_manual_decision"],
    )

    summary = {
        "uid": UID,
        "glyph_count": len(glyph_rows),
        "glyph_unique_id_count": len({r["glyph_id"] for r in glyph_rows}),
        "glyph_empty_mask_count": sum(r["mask_empty"] == "true" for r in glyph_rows),
        "glyph_cross_mask_overlap_pair_count": len(glyph_pair_overlap_pairs),
        "glyph_cross_mask_overlap_pixel_sum": sum(v for _, _, v in glyph_pair_overlap_pairs),
        "text_semantic_object_count": sum(o["kind"] == "TEXT" for o in semantic_objects),
        "pdf_visible_drawing_record_count": len(drawing_rows),
        "pdf_drawing_record_unique_count": len({r["pdf_drawing_index"] for r in drawing_rows}),
        "semantic_drawing_object_count": sum(o["kind"] != "TEXT" for o in semantic_objects),
        "math_rule_object_count": sum(o["kind"] == "GRAPHIC_MATH_RULE" for o in semantic_objects),
        "opaque_background_object_count": sum(o["kind"] == "BACKGROUND" for o in semantic_objects),
        "semantic_leaf_object_denominator_n": len(object_ids),
        "unordered_pair_expected_c_n_2": expected_pairs,
        "unordered_pair_emitted_count": len(pair_rows),
        "critical_relation_candidate_count": len(critical_rows),
        "critical_relation_evidence_count": len(critical_index),
        "pair_raw_overlap_candidate_count": sum(int(r["raw_mask_overlap_px"]) > 0 for r in pair_rows),
        "pair_raw_overlap_candidate_pixels_sum_noncanonical": sum(int(r["raw_mask_overlap_px"]) for r in pair_rows),
        "contact_sheet_count": math.ceil(len(glyph_rows) / per_sheet),
        "render_count": len(crop_records) + 3,
        "manual_decisions_present": False,
        "sealed": False,
    }
    (dirs["machine"] / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
    print("machine evidence generated; no manual decisions written")
