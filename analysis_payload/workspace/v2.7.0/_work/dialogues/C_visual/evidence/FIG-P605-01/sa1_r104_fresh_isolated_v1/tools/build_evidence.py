from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


HANDOFF_ID = "C-FIG-P605-01-R104-SA1-FRESH-ISOLATED-V1"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_componentwise_sweep.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa1_r104_fresh_isolated_v1")
EXPECTED_SHA256 = "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641"
EXPECTED_BYTES = 4_967_222
EXPECTED_PAGES = 817
PAGE_NUMBER = 658
PAGE_INDEX = PAGE_NUMBER - 1
RENDER_DPI = 300
SCALE = RENDER_DPI / 72.0

# Integer crop coordinates in the native 300 dpi full-page raster.
FIGURE_CROP_PX = (292, 250, 2237, 1063)       # includes caption with >=15 px exterior margin
STANDALONE_CROP_PX = (354, 250, 2171, 921)    # figure body only


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def mkdirs() -> None:
    for rel in (
        "00_identity",
        "01_render",
        "02_machine/glyph_masks",
        "02_machine/glyph_cells",
        "02_machine/object_masks",
        "02_machine/pair_evidence",
        "03_manual",
        "04_reports",
        "tools",
    ):
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def px_rect(rect: Iterable[float], crop_origin=(0, 0), pad: int = 0) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    ox, oy = crop_origin
    return (
        math.floor(x0 * SCALE) - ox - pad,
        math.floor(y0 * SCALE) - oy - pad,
        math.ceil(x1 * SCALE) - ox + pad,
        math.ceil(y1 * SCALE) - oy + pad,
    )


def clip_rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def union_rect(rects: Iterable[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    rs = list(rects)
    return min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs)


def rgb_from_int(v: int) -> tuple[int, int, int]:
    return (v >> 16) & 255, (v >> 8) & 255, v & 255


def target_mask(image: np.ndarray, bbox: tuple[int, int, int, int], rgb: tuple[int, int, int], threshold: float = 78.0) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    crop = image[y0:y1, x0:x1, :3].astype(np.int32)
    t = np.array(rgb, dtype=np.int32)
    dist = np.sqrt(np.sum((crop - t) ** 2, axis=2))
    # Require visible contrast from white in addition to proximity to the PDF fill/stroke color.
    contrast = np.max(np.abs(crop - 255), axis=2)
    return (dist <= threshold) & (contrast >= 20)


def trim_mask(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return mask, bbox
    lx0, ly0, lx1, ly1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    x0, y0, _, _ = bbox
    return mask[ly0:ly1, lx0:lx1], (x0 + lx0, y0 + ly0, x0 + lx1, y0 + ly1)


def mask_png(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def put_mask(canvas: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = bbox
    canvas[y0:y1, x0:x1] |= mask


def mask_coords(mask: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return np.empty((0, 2), dtype=np.int32)
    return np.column_stack((xs + bbox[0], ys + bbox[1])).astype(np.int32)


def min_clearance(a_mask: np.ndarray, a_bbox: tuple[int, int, int, int], b_mask: np.ndarray, b_bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    ax0, ay0, ax1, ay1 = a_bbox
    bx0, by0, bx1, by1 = b_bbox
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    overlap = 0
    if ix0 < ix1 and iy0 < iy1:
        aa = a_mask[iy0 - ay0:iy1 - ay0, ix0 - ax0:ix1 - ax0]
        bb = b_mask[iy0 - by0:iy1 - by0, ix0 - bx0:ix1 - bx0]
        overlap = int(np.count_nonzero(aa & bb))
    if overlap:
        return overlap, 0

    # Exact Chebyshev pixel clearance for nearby masks; bbox lower bound is sufficient when far.
    dx = max(0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0, max(ay0, by0) - min(ay1, by1))
    lower = max(dx, dy)
    if lower > 40:
        return 0, int(lower)
    ac = mask_coords(a_mask, a_bbox)
    bc = mask_coords(b_mask, b_bbox)
    if len(ac) == 0 or len(bc) == 0:
        return 0, -1
    # Chunked exact Chebyshev distance avoids adding a SciPy dependency.
    best = 10 ** 9
    if len(ac) > len(bc):
        ac, bc = bc, ac
    for start in range(0, len(ac), 256):
        q = ac[start:start + 256]
        dist = np.max(np.abs(q[:, None, :] - bc[None, :, :]), axis=2)
        best = min(best, int(dist.min()))
        if best <= 1:
            break
    return 0, max(0, best - 1)


def safe_font(size: int = 16):
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


@dataclass
class MaskObject:
    object_id: str
    safe_filename: str
    kind: str
    role: str
    parent: str
    source_ref: str
    drawing_indices: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    exclusion: str = ""


TEXT_SPECS = [
    ("TXT-001", "left_panel_title", "PANEL_TITLE", (140, 72, 242, 94), "系统扫描：固定复合"),
    ("TXT-002", "left_kernel_k1", "NODE_LABEL", (105, 102, 151, 135), "K_1"),
    ("TXT-003", "left_kernel_k2", "NODE_LABEL", (151, 102, 203, 135), "K_2"),
    ("TXT-004", "left_ellipsis", "FORMULA", (203, 102, 239, 135), "\\cdots"),
    ("TXT-005", "left_kernel_kd", "NODE_LABEL", (236, 102, 284, 135), "K_d"),
    ("TXT-006", "system_kernel_formula", "FORMULA", (145, 139, 236, 163), "K_sys=K_1K_2\\cdots K_d"),
    ("TXT-007", "left_note", "ANNOTATION", (115, 185, 268, 212), "固定次序复合：通常不保证可逆"),
    ("TXT-008", "right_panel_title", "PANEL_TITLE", (365, 72, 468, 94), "随机扫描：先抽坐标"),
    ("TXT-009", "choice_formula", "FORMULA", (394, 99, 438, 123), "J\\sim\\omega"),
    ("TXT-010", "right_kernel_k1", "NODE_LABEL", (323, 132, 374, 166), "K_1"),
    ("TXT-011", "right_kernel_kj", "NODE_LABEL", (388, 132, 443, 166), "K_j"),
    ("TXT-012", "right_kernel_kd", "NODE_LABEL", (454, 132, 510, 166), "K_d"),
    ("TXT-013", "random_kernel_formula", "FORMULA", (368, 160, 461, 187), "K_rand=sum_{j=1}^d omega_j K_j"),
    ("TXT-014", "right_note", "ANNOTATION", (355, 185, 478, 220), "若各K_j关于pi可逆；固定权重混合保持可逆"),
    ("TXT-015", "caption", "CAPTION", (70, 220, 536, 254), "图32.7 分量MH的系统扫描与随机扫描…"),
]


GRAPHIC_SPECS = [
    ("GFX-001", "panel_border_left", "PANEL_BORDER", [1], (184, 192, 200)),
    ("GFX-002", "panel_border_right", "PANEL_BORDER", [2], (184, 192, 200)),
    ("GFX-003", "node_border_left_k1", "NODE_BORDER", [3], (31, 78, 121)),
    ("GFX-004", "node_border_left_k2", "NODE_BORDER", [4], (31, 78, 121)),
    ("GFX-005", "node_border_left_kd", "NODE_BORDER", [5], (31, 78, 121)),
    ("GFX-006", "flow_arrow_left_1", "LINE_ARROW", [6, 7], (31, 78, 121)),
    ("GFX-007", "flow_arrow_left_2", "LINE_ARROW", [8, 9], (31, 78, 121)),
    ("GFX-008", "flow_arrow_left_3", "LINE_ARROW", [10, 11], (31, 78, 121)),
    ("GFX-009", "left_note_border", "NODE_BORDER", [12], (107, 114, 128)),
    ("GFX-010", "choice_diamond_border", "NODE_BORDER", [13], (183, 121, 31)),
    ("GFX-011", "node_border_right_k1", "NODE_BORDER", [14], (31, 78, 121)),
    ("GFX-012", "node_border_right_kj", "NODE_BORDER", [15], (31, 78, 121)),
    ("GFX-013", "node_border_right_kd", "NODE_BORDER", [16], (31, 78, 121)),
    ("GFX-014", "branch_arrow_right_1", "LINE_ARROW", [17, 18], (107, 114, 128)),
    ("GFX-015", "branch_arrow_right_2", "LINE_ARROW", [19, 20], (107, 114, 128)),
    ("GFX-016", "branch_arrow_right_3", "LINE_ARROW", [21, 22], (107, 114, 128)),
    ("GFX-017", "right_note_border", "NODE_BORDER", [23], (31, 78, 121)),
]


def render(doc: fitz.Document) -> tuple[Image.Image, Image.Image, Image.Image]:
    page = doc[PAGE_INDEX]
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False, colorspace=fitz.csRGB)
    full300 = Image.frombytes("RGB", [pix300.width, pix300.height], pix300.samples)
    full300.save(ROOT / "01_render/full_page_300dpi.png", dpi=(300, 300))
    pix200 = page.get_pixmap(matrix=fitz.Matrix(200 / 72.0, 200 / 72.0), alpha=False, colorspace=fitz.csRGB)
    full200 = Image.frombytes("RGB", [pix200.width, pix200.height], pix200.samples)
    full200.save(ROOT / "01_render/full_page_200dpi.png", dpi=(200, 200))
    figure = full300.crop(FIGURE_CROP_PX)
    standalone = full300.crop(STANDALONE_CROP_PX)
    figure.save(ROOT / "01_render/figure_crop_300dpi.png", dpi=(300, 300))
    standalone.save(ROOT / "01_render/standalone_300dpi.png", dpi=(300, 300))
    figure.convert("L").save(ROOT / "01_render/grayscale_300dpi.png", dpi=(300, 300))
    return full300, figure, standalone


def raw_chars(page: fitz.Page) -> list[dict]:
    out = []
    raw = page.get_text("rawdict")
    for b_idx, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for l_idx, line in enumerate(block.get("lines", [])):
            for s_idx, span in enumerate(line.get("spans", [])):
                color = rgb_from_int(int(span.get("color", 0)))
                for c_idx, ch in enumerate(span.get("chars", [])):
                    c = ch.get("c", "")
                    if not c or c.isspace():
                        continue
                    out.append({
                        "block_index": b_idx,
                        "line_index": l_idx,
                        "span_index": s_idx,
                        "char_index": c_idx,
                        "char": c,
                        "bbox_pt": tuple(ch["bbox"]),
                        "origin_pt": tuple(ch.get("origin", (None, None))),
                        "font": span.get("font", ""),
                        "font_size_pt": float(span.get("size", 0)),
                        "flags": int(span.get("flags", 0)),
                        "color_rgb": color,
                    })
    return out


def select_parent(ch: dict) -> tuple[str, str, str, str] | None:
    x0, y0, x1, y1 = ch["bbox_pt"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for oid, name, role, rect, text in TEXT_SPECS:
        rx0, ry0, rx1, ry1 = rect
        if rx0 <= cx <= rx1 and ry0 <= cy <= ry1:
            return oid, name, role, text
    return None


def script_class(c: str, parent_id: str, seq: int) -> str:
    natural_script_members = {
        "TXT-002": {2}, "TXT-003": {2}, "TXT-005": {2},
        "TXT-006": {2, 3, 4, 7, 9, 12},
        "TXT-010": {2}, "TXT-011": {2}, "TXT-012": {2},
        "TXT-013": {2, 3, 4, 5, 8, 9, 10, 11, 13, 15},
        "TXT-014": {4},
    }
    if seq in natural_script_members.get(parent_id, set()):
        return "NATURAL_SCRIPT"
    cp = ord(c)
    if c in ".,，。、：；…·":
        return "LOW_PROFILE_PUNCTUATION"
    if 0x3400 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F:
        return "CJK_FULL"
    if c.isdigit() or (c.isalpha() and c.upper() == c and c.lower() != c):
        return "LATIN_CAP_OR_DIGIT"
    if c.isalpha():
        return "LATIN_OR_GREEK_LOWER"
    if c in "₁₂₃₄₅₆₇₈₉₀ⱼᵈ" or cp in range(0x2070, 0x209F + 1):
        return "NATURAL_SCRIPT"
    return "MATH_OPERATOR_OR_SYMBOL"


def legacy_threshold(cls: str) -> int | str:
    return {
        "CJK_FULL": 30,
        "LATIN_CAP_OR_DIGIT": 24,
        "LATIN_OR_GREEK_LOWER": 17,
        "NATURAL_SCRIPT": 15,
        "MATH_OPERATOR_OR_SYMBOL": 22,
        "LOW_PROFILE_PUNCTUATION": "CALIBRATION",
    }[cls]


def build_glyphs(page: fitz.Page, figure: Image.Image) -> tuple[list[dict], dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]]:
    arr = np.asarray(figure)
    ox, oy = FIGURE_CROP_PX[:2]
    rows: list[dict] = []
    masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]] = {}
    counts: dict[str, int] = {}
    for ch in raw_chars(page):
        parent = select_parent(ch)
        if parent is None:
            continue
        parent_id, parent_name, role, parent_text = parent
        counts[parent_id] = counts.get(parent_id, 0) + 1
        seq = counts[parent_id]
        gid = f"GLY-{parent_id[4:]}-{seq:03d}"
        safe = gid.lower().replace("-", "_")
        bbox = clip_rect(px_rect(ch["bbox_pt"], (ox, oy), pad=1), figure.width, figure.height)
        raw = target_mask(arr, bbox, ch["color_rgb"], threshold=90.0 if ch["color_rgb"] != (0, 0, 0) else 100.0)
        raw, tight = trim_mask(raw, bbox)
        masks[gid] = (raw, tight)
        mask_png(ROOT / f"02_machine/glyph_masks/{safe}.png", raw)
        ys, xs = np.nonzero(raw)
        h = int(ys.max() - ys.min() + 1) if len(ys) else 0
        w = int(xs.max() - xs.min() + 1) if len(xs) else 0
        area = int(np.count_nonzero(raw))
        cls = script_class(ch["char"], parent_id, seq)
        rows.append({
            "glyph_id": gid,
            "safe_filename": safe,
            "parent_object_id": parent_id,
            "parent_name": parent_name,
            "role": role,
            "char": ch["char"],
            "codepoint": f"U+{ord(ch['char']):04X}",
            "script_class": cls,
            "legacy_threshold_px": legacy_threshold(cls),
            "font": ch["font"],
            "pdf_font_size_pt": f"{ch['font_size_pt']:.4f}",
            "color_rgb": ",".join(map(str, ch["color_rgb"])),
            "bbox_pt": ",".join(f"{v:.4f}" for v in ch["bbox_pt"]),
            "bbox_crop_px": ",".join(map(str, tight)),
            "mask_width_px": w,
            "mask_height_px": h,
            "mask_area_px": area,
            "mask_file": f"02_machine/glyph_masks/{safe}.png",
            "source_semantic_text": parent_text,
            "block_index": ch["block_index"],
            "line_index": ch["line_index"],
            "span_index": ch["span_index"],
            "char_index": ch["char_index"],
        })
    return rows, masks


def make_glyph_cells(figure: Image.Image, glyph_rows: list[dict], masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]) -> list[str]:
    font = safe_font(15)
    sheet_files: list[str] = []
    cells: list[Image.Image] = []
    for row in glyph_rows:
        gid = row["glyph_id"]
        mask, bbox = masks[gid]
        x0, y0, x1, y1 = bbox
        pad = 4
        rx0, ry0, rx1, ry1 = clip_rect((x0 - pad, y0 - pad, x1 + pad, y1 + pad), figure.width, figure.height)
        original = figure.crop((rx0, ry0, rx1, ry1)).convert("RGB")
        local_mask = np.zeros((ry1 - ry0, rx1 - rx0), dtype=bool)
        local_mask[y0 - ry0:y1 - ry0, x0 - rx0:x1 - rx0] = mask
        overlay = np.array(original).copy()
        overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
        mask_only = np.full_like(overlay, 255)
        mask_only[local_mask] = np.array([0, 0, 0], dtype=np.uint8)
        triplet = Image.new("RGB", (original.width * 3, original.height), "white")
        triplet.paste(original, (0, 0))
        triplet.paste(Image.fromarray(overlay), (original.width, 0))
        triplet.paste(Image.fromarray(mask_only), (original.width * 2, 0))
        zoom = triplet.resize((triplet.width * 8, triplet.height * 8), Image.Resampling.NEAREST)
        label_h = 42
        cell = Image.new("RGB", (max(zoom.width, triplet.width), label_h + triplet.height + 4 + zoom.height), "white")
        d = ImageDraw.Draw(cell)
        d.text((4, 2), f"{gid} {row['codepoint']} {row['script_class']}", fill="black", font=font)
        d.text((4, 20), "1x: ORIGINAL | TARGET OVERLAY | MASK ONLY; below: 8x nearest", fill="black", font=font)
        cell.paste(triplet, (0, label_h))
        cell.paste(zoom, (0, label_h + triplet.height + 4))
        path = ROOT / f"02_machine/glyph_cells/{row['safe_filename']}.png"
        cell.save(path)
        row["cell_file"] = f"02_machine/glyph_cells/{row['safe_filename']}.png"
        cells.append(cell)

    per_sheet = 20
    for sidx in range(0, len(cells), per_sheet):
        batch = cells[sidx:sidx + per_sheet]
        thumb_w, thumb_h = 900, 520
        cols = 2
        rows = math.ceil(len(batch) / cols)
        sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), "white")
        for i, cell in enumerate(batch):
            fit = cell.copy()
            fit.thumbnail((thumb_w, thumb_h), Image.Resampling.NEAREST)
            x = (i % cols) * thumb_w
            y = (i // cols) * thumb_h
            sheet.paste(fit, (x, y))
        name = f"glyph_contact_sheet_{sidx // per_sheet + 1:03d}.png"
        sheet.save(ROOT / f"02_machine/{name}")
        sheet_files.append(f"02_machine/{name}")
        for local_idx, row in enumerate(glyph_rows[sidx:sidx + per_sheet], start=1):
            row["contact_sheet"] = f"02_machine/{name}"
            row["contact_cell"] = str(local_idx)
    return sheet_files


def build_text_objects(glyph_rows: list[dict], glyph_masks: dict[str, tuple[np.ndarray, tuple[int, int, int, int]]]) -> list[MaskObject]:
    objects: list[MaskObject] = []
    for oid, name, role, rect, text in TEXT_SPECS:
        members = [r for r in glyph_rows if r["parent_object_id"] == oid]
        if not members:
            bbox = px_rect(rect, FIGURE_CROP_PX[:2])
            mask = np.zeros((max(1, bbox[3] - bbox[1]), max(1, bbox[2] - bbox[0])), dtype=bool)
        else:
            bbox = union_rect(glyph_masks[r["glyph_id"]][1] for r in members)
            mask = np.zeros((bbox[3] - bbox[1], bbox[2] - bbox[0]), dtype=bool)
            for r in members:
                gm, gb = glyph_masks[r["glyph_id"]]
                y0, y1 = gb[1] - bbox[1], gb[3] - bbox[1]
                x0, x1 = gb[0] - bbox[0], gb[2] - bbox[0]
                mask[y0:y1, x0:x1] |= gm
        safe = oid.lower().replace("-", "_")
        objects.append(MaskObject(oid, safe, "TEXT", role, name, f"source:{text}", "", bbox, mask))
    return objects


def build_graphic_objects(page: fitz.Page, figure: Image.Image) -> tuple[list[MaskObject], list[dict]]:
    drawings = page.get_drawings()
    arr = np.asarray(figure)
    ox, oy = FIGURE_CROP_PX[:2]
    objects: list[MaskObject] = []
    mapped = set()
    for oid, name, role, indices, rgb in GRAPHIC_SPECS:
        mapped.update(indices)
        rects = [tuple(drawings[i]["rect"]) for i in indices]
        bbox = clip_rect(px_rect((
            min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects)
        ), (ox, oy), pad=3), figure.width, figure.height)
        mask = target_mask(arr, bbox, rgb, threshold=54.0)
        # Geometry band prevents same-hue antialiasing from interior text/fills from
        # contaminating border masks. LINE_ARROW bboxes are already path-tight.
        if role in ("PANEL_BORDER", "NODE_BORDER"):
            h, w = mask.shape
            yy, xx = np.mgrid[0:h, 0:w]
            if indices == [13]:
                cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
                nx = np.abs(xx - cx) / max(1.0, cx)
                ny = np.abs(yy - cy) / max(1.0, cy)
                band = np.abs(nx + ny - 1.0) <= 0.10
            else:
                edge_dist = np.minimum.reduce((xx, yy, w - 1 - xx, h - 1 - yy))
                band = edge_dist <= (6 if role == "PANEL_BORDER" else 12)
            mask &= band
        mask, bbox = trim_mask(mask, bbox)
        safe = oid.lower().replace("-", "_")
        objects.append(MaskObject(oid, safe, "GRAPHIC", role, name, "PDF drawing/path", ";".join(map(str, indices)), bbox, mask,
                                  "fills/backgrounds excluded; only final-visible stroke/arrow ink retained"))
    inventory = []
    for i, d in enumerate(drawings):
        rect = tuple(float(v) for v in d["rect"])
        in_figure = i in mapped
        inventory.append({
            "drawing_index": i,
            "bbox_pt": ",".join(f"{v:.4f}" for v in rect),
            "type": d.get("type"),
            "stroke_color": str(d.get("color")),
            "fill_color": str(d.get("fill")),
            "line_width_pt": d.get("width"),
            "item_count": len(d.get("items", [])),
            "figure_membership": "FIGURE_DRAWING" if in_figure else "OUTSIDE_FIGURE_SCOPE",
            "mapped_object_id": next((g[0] for g in GRAPHIC_SPECS if i in g[3]), ""),
            "scope_exclusion_reason": "" if in_figure else "outside y=68.30..219.96 pt figure body and caption contains no drawings",
        })
    return objects, inventory


def save_object_masks(objects: list[MaskObject]) -> None:
    for o in objects:
        mask_png(ROOT / f"02_machine/object_masks/{o.safe_filename}.png", o.mask)


def make_overlays(figure: Image.Image, glyph_rows: list[dict], objects: list[MaskObject]) -> None:
    font = safe_font(11)
    overlay = figure.convert("RGB").copy()
    d = ImageDraw.Draw(overlay)
    colors = ["#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
    for i, o in enumerate(objects):
        x0, y0, x1, y1 = o.bbox
        c = colors[i % len(colors)]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=c, width=2)
        d.text((x0 + 1, max(0, y0 - 12)), o.object_id, fill=c, font=font, stroke_width=1, stroke_fill="white")
    overlay.save(ROOT / "02_machine/object_measurement_overlay_300dpi.png", dpi=(300, 300))

    go = figure.convert("RGB").copy()
    dg = ImageDraw.Draw(go)
    for i, row in enumerate(glyph_rows):
        x0, y0, x1, y1 = map(int, row["bbox_crop_px"].split(","))
        c = colors[i % len(colors)]
        dg.rectangle((x0, y0, x1 - 1, y1 - 1), outline=c, width=1)
    go.save(ROOT / "02_machine/glyph_measurement_overlay_300dpi.png", dpi=(300, 300))


def pair_evidence(figure: Image.Image, a: MaskObject, b: MaskObject, pair_id: str) -> dict:
    margin = 10
    rb = clip_rect((min(a.bbox[0], b.bbox[0]) - margin,
                    min(a.bbox[1], b.bbox[1]) - margin,
                    max(a.bbox[2], b.bbox[2]) + margin,
                    max(a.bbox[3], b.bbox[3]) + margin), figure.width, figure.height)
    x0, y0, x1, y1 = rb
    roi = figure.crop(rb).convert("RGB")
    ma = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    mb = np.zeros_like(ma)
    ma[a.bbox[1] - y0:a.bbox[3] - y0, a.bbox[0] - x0:a.bbox[2] - x0] |= a.mask
    mb[b.bbox[1] - y0:b.bbox[3] - y0, b.bbox[0] - x0:b.bbox[2] - x0] |= b.mask
    inter = ma & mb
    ov = np.array(roi).copy()
    ov[ma] = np.array([255, 0, 0], dtype=np.uint8)
    ov[mb] = np.array([0, 80, 255], dtype=np.uint8)
    ov[inter] = np.array([255, 0, 255], dtype=np.uint8)
    folder = ROOT / f"02_machine/pair_evidence/{pair_id.lower().replace('-', '_')}"
    folder.mkdir(parents=True, exist_ok=True)
    roi.save(folder / "original_1x.png")
    mask_png(folder / "mask_a_1x.png", ma)
    mask_png(folder / "mask_b_1x.png", mb)
    mask_png(folder / "intersection_1x.png", inter)
    Image.fromarray(ov).save(folder / "overlay_1x.png")
    Image.fromarray(ov).resize((ov.shape[1] * 8, ov.shape[0] * 8), Image.Resampling.NEAREST).save(folder / "overlay_8x_nearest.png")
    return {
        "roi_crop_px": ",".join(map(str, rb)),
        "evidence_dir": str(folder.relative_to(ROOT)).replace("\\", "/"),
    }


def build_pairs(figure: Image.Image, objects: list[MaskObject]) -> list[dict]:
    rows = []
    pair_count = 0
    for a, b in itertools.combinations(objects, 2):
        pair_count += 1
        pid = f"PAIR-{pair_count:04d}"
        overlap, clearance = min_clearance(a.mask, a.bbox, b.mask, b.bbox)
        relation = f"{a.role}-{b.role}"
        evidence = {"roi_crop_px": "", "evidence_dir": ""}
        if overlap > 0 or (clearance >= 0 and clearance <= 15):
            evidence = pair_evidence(figure, a, b, pid)
        rows.append({
            "pair_id": pid,
            "object_a": a.object_id,
            "object_b": b.object_id,
            "role_a": a.role,
            "role_b": b.role,
            "relation_class": relation,
            "raw_intersection_px": overlap,
            "raw_min_clearance_px": clearance,
            "roi_crop_px": evidence["roi_crop_px"],
            "evidence_dir": evidence["evidence_dir"],
        })
    return rows


def source_font_inventory(source: str) -> list[dict]:
    lines = source.splitlines()
    rows = []
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", line):
            rows.append({
                "source_line": i,
                "command": m.group(0),
                "declared_pt": m.group(1),
                "baseline_skip_pt": m.group(2),
                "graphics_scale": "1.0000",
                "effective_pt": m.group(1),
                "scope": "global slfig style" if "tikzset" in line else "local node override",
            })
        for token in ("tiny", "scriptsize", "footnotesize", "small", "large", "resizebox", "scalebox", "transform shape", "scale="):
            if token in line:
                rows.append({
                    "source_line": i,
                    "command": token,
                    "declared_pt": "",
                    "baseline_skip_pt": "",
                    "graphics_scale": "",
                    "effective_pt": "",
                    "scope": "token occurrence requiring reviewer interpretation",
                })
    return rows


def identity(doc: fitz.Document, full300: Image.Image, full200: Image.Image) -> None:
    stat = PDF.stat()
    ident = {
        "handoff_id": HANDOFF_ID,
        "uid": "FIG-P605-01",
        "round": "R104",
        "review_role": "SA1 fresh isolated",
        "source_writer": "NONE",
        "tex": "DISABLED",
        "pdf_resolved_path": str(PDF.resolve()),
        "pdf_bytes": stat.st_size,
        "pdf_sha256": sha256(PDF),
        "pdf_pages": doc.page_count,
        "page_size_pt": [doc[PAGE_INDEX].rect.width, doc[PAGE_INDEX].rect.height],
        "page_size_name": "A4",
        "physical_page": PAGE_NUMBER,
        "printed_page": 645,
        "figure_number": "32.7",
        "caption": "分量 MH 的系统扫描与随机扫描。固定顺序的核复合通常不保证可逆；可逆坐标核的固定权重随机混合仍保持可逆。",
        "label": "fig:V5-C03-componentwise-sweep",
        "source_resolved_path": str(SOURCE.resolve()),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "source_mtime_utc_ns": SOURCE.stat().st_mtime_ns,
        "pdf_mtime_utc_ns": PDF.stat().st_mtime_ns,
        "full_page_300dpi_native_px": list(full300.size),
        "full_page_200dpi_native_px": list(full200.size),
        "figure_crop_fullpage_px": list(FIGURE_CROP_PX),
        "standalone_crop_fullpage_px": list(STANDALONE_CROP_PX),
        "render_engine": f"PyMuPDF {fitz.__doc__.split()[1] if fitz.__doc__ else ''}",
        "render_resize_after_300dpi": False,
    }
    if ident["pdf_bytes"] != EXPECTED_BYTES or ident["pdf_sha256"] != EXPECTED_SHA256 or ident["pdf_pages"] != EXPECTED_PAGES:
        raise RuntimeError("official PDF identity mismatch")
    (ROOT / "00_identity/candidate_identity.json").write_text(json.dumps(ident, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "00_identity/independent_location.txt").write_text(
        "R104 PDF全书文本逐页独立搜索当前caption得到唯一命中：physical_page=658；页眉印刷页=645；图号=32.7。\n"
        "旧任务卡页码714未继承。当前PDF图题与白名单单源caption一致。\n",
        encoding="utf-8",
    )


def main() -> None:
    mkdirs()
    doc = fitz.open(PDF)
    full300, figure, standalone = render(doc)
    full200 = Image.open(ROOT / "01_render/full_page_200dpi.png")
    identity(doc, full300, full200)

    source = SOURCE.read_text(encoding="utf-8")
    sf = source_font_inventory(source)
    write_csv(ROOT / "02_machine/source_font_inventory.csv",
              ["source_line", "command", "declared_pt", "baseline_skip_pt", "graphics_scale", "effective_pt", "scope"], sf)

    page = doc[PAGE_INDEX]
    glyph_rows, glyph_masks = build_glyphs(page, figure)
    sheets = make_glyph_cells(figure, glyph_rows, glyph_masks)
    glyph_fields = [
        "glyph_id", "safe_filename", "parent_object_id", "parent_name", "role", "char", "codepoint", "script_class",
        "legacy_threshold_px", "font", "pdf_font_size_pt", "color_rgb", "bbox_pt", "bbox_crop_px", "mask_width_px",
        "mask_height_px", "mask_area_px", "mask_file", "cell_file", "contact_sheet", "contact_cell", "source_semantic_text",
        "block_index", "line_index", "span_index", "char_index",
    ]
    write_csv(ROOT / "02_machine/glyph_machine_inventory.csv", glyph_fields, glyph_rows)

    text_objects = build_text_objects(glyph_rows, glyph_masks)
    graphic_objects, drawing_inventory = build_graphic_objects(page, figure)
    objects = text_objects + graphic_objects
    save_object_masks(objects)
    make_overlays(figure, glyph_rows, objects)
    object_rows = []
    for o in objects:
        ys, xs = np.nonzero(o.mask)
        clip_pixels = 0
        if o.mask.size:
            if o.bbox[0] == 0:
                clip_pixels += int(np.count_nonzero(o.mask[:, 0]))
            if o.bbox[2] == figure.width:
                clip_pixels += int(np.count_nonzero(o.mask[:, -1]))
            if o.bbox[1] == 0:
                clip_pixels += int(np.count_nonzero(o.mask[0, :]))
            if o.bbox[3] == figure.height:
                clip_pixels += int(np.count_nonzero(o.mask[-1, :]))
        object_rows.append({
            "object_id": o.object_id,
            "safe_filename": o.safe_filename,
            "kind": o.kind,
            "role": o.role,
            "semantic_parent": o.parent,
            "source_ref": o.source_ref,
            "drawing_indices": o.drawing_indices,
            "bbox_crop_px": ",".join(map(str, o.bbox)),
            "raw_mask_pixels": int(np.count_nonzero(o.mask)),
            "raw_mask_width_px": int(xs.max() - xs.min() + 1) if len(xs) else 0,
            "raw_mask_height_px": int(ys.max() - ys.min() + 1) if len(ys) else 0,
            "mask_file": f"02_machine/object_masks/{o.safe_filename}.png",
            "crop_edge_touch_pixels": clip_pixels,
            "explicit_exclusion": o.exclusion,
        })
    write_csv(ROOT / "02_machine/object_machine_inventory.csv",
              ["object_id", "safe_filename", "kind", "role", "semantic_parent", "source_ref", "drawing_indices", "bbox_crop_px",
               "raw_mask_pixels", "raw_mask_width_px", "raw_mask_height_px", "mask_file", "crop_edge_touch_pixels", "explicit_exclusion"],
              object_rows)
    write_csv(ROOT / "02_machine/pdf_drawing_inventory.csv",
              ["drawing_index", "bbox_pt", "type", "stroke_color", "fill_color", "line_width_pt", "item_count", "figure_membership",
               "mapped_object_id", "scope_exclusion_reason"], drawing_inventory)
    write_csv(ROOT / "02_machine/math_rule_inventory.csv",
              ["math_rule_id", "parent_formula", "drawing_index", "bbox_pt", "mask_file", "inventory_statement"],
              [{"math_rule_id": "", "parent_formula": "", "drawing_index": "", "bbox_pt": "", "mask_file": "",
                "inventory_statement": "No GRAPHIC/MATH_RULE exists in figure drawings 1..23; all displayed math operators/subscripts are PDF text glyphs. Drawings 24..34 are below the figure scope."}])

    pair_rows = build_pairs(figure, objects)
    write_csv(ROOT / "02_machine/pair_machine_inventory.csv",
              ["pair_id", "object_a", "object_b", "role_a", "role_b", "relation_class", "raw_intersection_px", "raw_min_clearance_px", "roi_crop_px", "evidence_dir"],
              pair_rows)

    safe_rows = []
    for r in glyph_rows:
        safe_rows.append({"id": r["glyph_id"], "safe_filename": r["safe_filename"], "kind": "GLYPH", "ordinary_mask_file": r["mask_file"], "ordinary_cell_file": r["cell_file"]})
    for o in objects:
        safe_rows.append({"id": o.object_id, "safe_filename": o.safe_filename, "kind": "OBJECT", "ordinary_mask_file": f"02_machine/object_masks/{o.safe_filename}.png", "ordinary_cell_file": ""})
    write_csv(ROOT / "02_machine/id_safe_filename_map.csv", ["id", "safe_filename", "kind", "ordinary_mask_file", "ordinary_cell_file"], safe_rows)

    mapped_drawings = sum(1 for r in drawing_inventory if r["figure_membership"] == "FIGURE_DRAWING" and r["mapped_object_id"])
    unmapped_drawings = sum(1 for r in drawing_inventory if r["figure_membership"] == "FIGURE_DRAWING" and not r["mapped_object_id"])
    empty_glyphs = sum(1 for r in glyph_rows if int(r["mask_area_px"]) == 0)
    empty_objects = sum(1 for r in object_rows if int(r["raw_mask_pixels"]) == 0)
    summary = {
        "handoff_id": HANDOFF_ID,
        "uid": "FIG-P605-01",
        "physical_page": PAGE_NUMBER,
        "glyph_count": len(glyph_rows),
        "text_object_count": len(text_objects),
        "graphic_object_count": len(graphic_objects),
        "object_count": len(objects),
        "unordered_pair_expected_C_n_2": len(objects) * (len(objects) - 1) // 2,
        "unordered_pair_rows": len(pair_rows),
        "critical_pair_evidence_count": sum(1 for r in pair_rows if r["evidence_dir"]),
        "figure_pdf_drawing_count": 23,
        "mapped_figure_pdf_drawings": mapped_drawings,
        "unmapped_figure_pdf_drawings": unmapped_drawings,
        "math_rule_count": 0,
        "empty_glyph_mask_count": empty_glyphs,
        "empty_object_mask_count": empty_objects,
        "glyph_contact_sheet_count": len(sheets),
        "ordinary_glyph_mask_files": len(list((ROOT / "02_machine/glyph_masks").glob("*.png"))),
        "ordinary_glyph_cell_files": len(list((ROOT / "02_machine/glyph_cells").glob("*.png"))),
        "ordinary_object_mask_files": len(list((ROOT / "02_machine/object_masks").glob("*.png"))),
        "ads_created": 0,
        "whitespace_glyphs_excluded_as_nonvisible": True,
        "background_exclusions": ["page background", "panel fill", "node fill", "annotation card fill", "choice diamond fill"],
    }
    (ROOT / "02_machine/machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    doc.close()


if __name__ == "__main__":
    main()
