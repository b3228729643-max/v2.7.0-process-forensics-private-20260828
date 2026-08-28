from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


HANDOFF_ID = "C-FIG-P637-01-R103-SA1-FRESH-ISOLATED-V1"
UID = "FIG-P637-01"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_gibbs_axis_path.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa1_r103_fresh_isolated_v1")
SCALE300 = 300.0 / 72.0
SCALE200 = 200.0 / 72.0

DIRS = {
    "render": ROOT / "render",
    "mask_glyph": ROOT / "masks" / "glyph",
    "mask_object": ROOT / "masks" / "object",
    "contact_glyph": ROOT / "contact_sheets" / "glyph",
    "contact_graphic": ROOT / "contact_sheets" / "graphic",
    "roi": ROOT / "pair_rois",
    "machine": ROOT / "machine",
}


def mkdirs() -> None:
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def rect_union(rects: list[fitz.Rect]) -> fitz.Rect:
    # PyMuPDF union operators ignore zero-height/zero-width line rects.  Use
    # explicit extrema so axis shafts and other hairlines remain in bounds.
    return fitz.Rect(
        min(r.x0 for r in rects), min(r.y0 for r in rects),
        max(r.x1 for r in rects), max(r.y1 for r in rects),
    )


def pix_rect(r: fitz.Rect, scale: float, bounds: tuple[int, int]) -> tuple[int, int, int, int]:
    w, h = bounds
    return (
        max(0, int(math.floor(r.x0 * scale))),
        max(0, int(math.floor(r.y0 * scale))),
        min(w, int(math.ceil(r.x1 * scale))),
        min(h, int(math.ceil(r.y1 * scale))),
    )


def int_to_rgb(c: int) -> tuple[int, int, int]:
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


def safe_char(c: str) -> str:
    return f"U{ord(c):04X}"


def classify_char(c: str, font: str, parent: str) -> str:
    cp = ord(c)
    if c in "，。、；：？！,.;:…":
        return "LOW_PROFILE_PUNCTUATION"
    if c in "+−-=<>∣∏":
        return "MATH_OPERATOR"
    if "Math" in font and c.isdigit() and parent in {"TXT_AXIS_X1", "TXT_AXIS_X2", "TXT_UPDATE_X1", "TXT_UPDATE_X2"}:
        return "NATURAL_SUBSCRIPT"
    if c.isdigit():
        return "LATIN_UPPER_OR_DIGIT"
    if (0x4E00 <= cp <= 0x9FFF) or (0x3000 <= cp <= 0x303F):
        return "CJK_FULL_HEIGHT"
    if c.isalpha() and c.islower():
        return "LATIN_GREEK_LOWER"
    if c.isalpha() and c.isupper():
        return "LATIN_UPPER_OR_DIGIT"
    if "Math" in font:
        return "BASE_MATH"
    return "OTHER_VISIBLE"


def threshold_for_class(cls: str) -> int | None:
    return {
        "CJK_FULL_HEIGHT": 30,
        "LATIN_UPPER_OR_DIGIT": 24,
        "LATIN_GREEK_LOWER": 17,
        "BASE_MATH": 22,
        "MATH_OPERATOR": 22,
        "NATURAL_SUBSCRIPT": 15,
    }.get(cls)


def group_for_char(block: int, line: int, x0: float, c: str) -> tuple[str, str, int]:
    if block == 1:
        return "TXT_AXIS_X1", "AXIS_TITLE", 18
    if block == 2:
        return "TXT_AXIS_X2", "AXIS_TITLE", 19
    if block == 3 and line == 0:
        return "TXT_UPDATE_X1", "ANNOTATION", 33
    if block == 3 and line == 1:
        return "TXT_UPDATE_X2", "ANNOTATION", 34
    if block == 4:
        return "TXT_STEP_0", "NUMERIC_LABEL", 41
    if block == 5:
        return "TXT_STEP_1", "NUMERIC_LABEL", 41
    if block == 6:
        return "TXT_STEP_2", "NUMERIC_LABEL", 41
    if block == 7:
        return "TXT_STEP_3", "NUMERIC_LABEL", 41
    if block == 8 and c == "4":
        return "TXT_STEP_4", "NUMERIC_LABEL", 41
    if block == 8 and c == "5":
        return "TXT_STEP_5", "NUMERIC_LABEL", 41
    if block == 9:
        return "TXT_STEP_6", "NUMERIC_LABEL", 41
    if block == 10:
        return "TXT_LONG_AXIS", "AXIS_ANNOTATION", 44
    if block == 11:
        return "TXT_SHORT_AXIS", "AXIS_ANNOTATION", 46
    if block in (12, 13):
        return "TXT_INFO_NODE", "INFO_NODE_TEXT", 49
    if block == 14 and line == 0 and x0 < 100:
        return "TXT_CAPTION_LABEL", "CAPTION_LABEL", 51
    if block == 14:
        return "TXT_CAPTION_BODY", "CAPTION", 51
    raise ValueError((block, line, x0, c))


def source_declared_pt(parent: str) -> float | str:
    if parent.startswith("TXT_STEP_"):
        return 8.8
    if parent.startswith("TXT_CAPTION"):
        return "PDF_OBSERVED_ONLY"
    return 9.2


def render_page(page: fitz.Page, dpi: int) -> Image.Image:
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def char_mask(image: np.ndarray, bbox: tuple[int, int, int, int], fg_rgb: tuple[int, int, int]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    # PDF char bboxes already enclose the glyph.  Do not expand them into
    # neighbouring arrows / labels; context padding belongs only in cards.
    x0p, y0p = max(0, x0), max(0, y0)
    x1p, y1p = min(image.shape[1], x1), min(image.shape[0], y1)
    patch = image[y0p:y1p, x0p:x1p].astype(np.float32)
    if patch.size == 0:
        return np.zeros((0, 0), dtype=bool), (x0p, y0p, x1p, y1p)
    border = np.concatenate((patch[0], patch[-1], patch[:, 0], patch[:, -1]), axis=0)
    bg = np.median(border, axis=0)
    fg = np.array(fg_rgb, dtype=np.float32)
    v = fg - bg
    denom = float(np.dot(v, v))
    if denom < 1.0:
        denom = 1.0
    flat = patch.reshape(-1, 3)
    t = np.clip(((flat - bg) @ v) / denom, 0.0, 1.0)
    recon = bg + t[:, None] * v
    residual = np.max(np.abs(flat - recon), axis=1)
    contrast = np.max(np.abs(flat - bg), axis=1)
    # Tight residual gate prevents differently coloured antialias pixels from a
    # nearby arrow/contour being attributed to the glyph mask.
    mask = ((contrast >= 20.0) & (t >= 0.055) & (residual <= 24.0)).reshape(patch.shape[:2])
    return mask, (x0p, y0p, x1p, y1p)


def tight_bbox(mask: np.ndarray, origin: tuple[int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    ox, oy = origin
    return (ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1)


def save_local_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def shape_mask(page_rect: fitz.Rect, drawing: dict, use_stroke: bool, use_fill: bool, full_size: tuple[int, int]) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    td = fitz.open()
    tp = td.new_page(width=page_rect.width, height=page_rect.height)
    sh = tp.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            sh.draw_line(item[1], item[2])
        elif op == "c":
            sh.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            sh.draw_rect(item[1])
        elif op == "qu":
            sh.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported path item: {op}")
    width = float(drawing.get("width") or 0.0)
    sh.finish(
        width=max(width, 0.01),
        color=(0, 0, 0) if use_stroke else None,
        fill=(0, 0, 0) if use_fill else None,
        dashes=drawing.get("dashes") or None,
        closePath=bool(use_fill),
        lineCap=0,
        lineJoin=1,
        fill_opacity=1.0,
        stroke_opacity=1.0,
    )
    sh.commit()
    pix = tp.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), alpha=True, colorspace=fitz.csRGB)
    rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
    alpha = rgba[:, :, 3] > 0
    tb = tight_bbox(alpha, (0, 0))
    if tb is None:
        td.close()
        return np.zeros((0, 0), dtype=bool), (0, 0, 0, 0)
    x0, y0, x1, y1 = tb
    out = alpha[y0:y1, x0:x1].copy()
    td.close()
    return out, tb


@dataclass
class ObjMask:
    object_id: str
    category: str
    role: str
    bbox: tuple[int, int, int, int]
    mask: np.ndarray
    source_members: list[str]
    semantic_note: str


def union_masks(object_id: str, category: str, role: str, members: list[ObjMask], note: str) -> ObjMask:
    x0 = min(m.bbox[0] for m in members)
    y0 = min(m.bbox[1] for m in members)
    x1 = max(m.bbox[2] for m in members)
    y1 = max(m.bbox[3] for m in members)
    arr = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    ids: list[str] = []
    for m in members:
        ax0, ay0, ax1, ay1 = m.bbox
        arr[ay0-y0:ay1-y0, ax0-x0:ax1-x0] |= m.mask
        ids.extend(m.source_members)
    return ObjMask(object_id, category, role, (x0, y0, x1, y1), arr, ids, note)


def pair_metrics(a: ObjMask, b: ObjMask) -> tuple[int, float, int]:
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    overlap = 0
    if ix0 < ix1 and iy0 < iy1:
        aa = a.mask[iy0-ay0:iy1-ay0, ix0-ax0:ix1-ax0]
        bb = b.mask[iy0-by0:iy1-by0, ix0-bx0:ix1-bx0]
        overlap = int(np.count_nonzero(aa & bb))
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    bbox_gap = int(math.floor(math.hypot(dx, dy)))
    if bbox_gap > 20:
        return overlap, float(bbox_gap), bbox_gap
    x0, y0 = min(ax0, bx0) - 2, min(ay0, by0) - 2
    x1, y1 = max(ax1, bx1) + 2, max(ay1, by1) + 2
    ma = np.zeros((y1-y0, x1-x0), dtype=bool)
    mb = np.zeros_like(ma)
    ma[ay0-y0:ay1-y0, ax0-x0:ax1-x0] = a.mask
    mb[by0-y0:by1-y0, bx0-x0:bx1-x0] = b.mask
    if overlap:
        clearance = 0.0
    else:
        dt = distance_transform_edt(~ma)
        clearance = float(dt[mb].min()) if np.any(mb) else float("nan")
    return overlap, clearance, bbox_gap


def save_overlay_card(path: Path, base: Image.Image, obj: ObjMask, pad: int = 6) -> None:
    x0, y0, x1, y1 = obj.bbox
    rx0, ry0 = max(0, x0-pad), max(0, y0-pad)
    rx1, ry1 = min(base.width, x1+pad), min(base.height, y1+pad)
    original = base.crop((rx0, ry0, rx1, ry1)).convert("RGB")
    ov = original.copy()
    oa = np.array(ov)
    local = np.zeros((ry1-ry0, rx1-rx0), dtype=bool)
    local[y0-ry0:y1-ry0, x0-rx0:x1-rx0] = obj.mask
    oa[local] = np.array([255, 0, 0], dtype=np.uint8)
    ov = Image.fromarray(oa)
    mo = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    canvas = Image.new("RGB", (original.width*3, original.height+20), "white")
    canvas.paste(original, (0, 20)); canvas.paste(ov, (original.width, 20)); canvas.paste(mo, (original.width*2, 20))
    ImageDraw.Draw(canvas).text((2, 2), f"{obj.object_id} ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black")
    canvas.save(path)


def make_glyph_sheets(base: Image.Image, glyph_objs: list[ObjMask], glyph_rows: dict[str, dict]) -> list[dict]:
    out_rows: list[dict] = []
    cols, rows_per_sheet = 3, 4
    per_sheet = cols * rows_per_sheet
    cell_w, cell_h = 1550, 620
    for sidx in range(math.ceil(len(glyph_objs)/per_sheet)):
        subset = glyph_objs[sidx*per_sheet:(sidx+1)*per_sheet]
        sheet = Image.new("RGB", (cols*cell_w, rows_per_sheet*cell_h), "white")
        dr = ImageDraw.Draw(sheet)
        for j, obj in enumerate(subset):
            col, row = j % cols, j // cols
            xoff, yoff = col*cell_w, row*cell_h
            x0, y0, x1, y1 = obj.bbox
            pad = 4
            rx0, ry0 = max(0, x0-pad), max(0, y0-pad)
            rx1, ry1 = min(base.width, x1+pad), min(base.height, y1+pad)
            original = base.crop((rx0, ry0, rx1, ry1)).convert("RGB")
            arr = np.array(original)
            local = np.zeros((ry1-ry0, rx1-rx0), dtype=bool)
            local[y0-ry0:y1-ry0, x0-rx0:x1-rx0] = obj.mask
            over = arr.copy(); over[local] = np.array([255, 0, 0], dtype=np.uint8)
            mask_only = np.repeat(np.where(local, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
            panes = [original, Image.fromarray(over), Image.fromarray(mask_only)]
            xcursor = xoff + 5
            for pane in panes:
                big = pane.resize((pane.width*8, pane.height*8), Image.Resampling.NEAREST)
                sheet.paste(big, (xcursor, yoff+55))
                xcursor += big.width + 8
            meta = glyph_rows[obj.object_id]
            dr.text((xoff+5, yoff+5), f"{obj.object_id} {meta['char']} {meta['codepoint']} parent={meta['parent_object_id']}", fill="black")
            dr.text((xoff+5, yoff+25), "8x nearest: ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black")
            out_rows.append({"glyph_id": obj.object_id, "sheet": f"glyph_sheet_{sidx+1:02d}.png", "cell": j+1})
        sheet.save(DIRS["contact_glyph"] / f"glyph_sheet_{sidx+1:02d}.png")
    return out_rows


def quadrant_8x(image: Image.Image, stem: str) -> list[dict]:
    rows = []
    xmid, ymid = image.width // 2, image.height // 2
    rects = [(0,0,xmid,ymid),(xmid,0,image.width,ymid),(0,ymid,xmid,image.height),(xmid,ymid,image.width,image.height)]
    for i, r in enumerate(rects, 1):
        tile = image.crop(r)
        out = tile.resize((tile.width*8, tile.height*8), Image.Resampling.NEAREST)
        name = f"{stem}_q{i}_8x_nearest.png"
        out.save(DIRS["render"] / name)
        rows.append({"view": stem, "tile": i, "native_rect": list(r), "scale": 8, "path": f"render/{name}"})
    return rows


def main() -> None:
    mkdirs()
    pdf_bytes = PDF.stat().st_size
    pdf_hash = sha256(PDF)
    doc = fitz.open(PDF)
    matches = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if "固定教学示意" in text and "二维Gibbs" in text and "轴向短步" in text:
            matches.append(i)
    if len(matches) != 1:
        raise RuntimeError(f"figure locator not unique: {matches}")
    pidx = matches[0]
    page = doc[pidx]
    page300 = render_page(page, 300)
    page200 = render_page(page, 200)
    page300.save(DIRS["render"] / "full_page_300dpi.png")
    page200.save(DIRS["render"] / "full_page_200dpi.png")

    raw = page.get_text("rawdict")
    drawings = page.get_drawings()
    caption_rects: list[fitz.Rect] = []
    body_text_rects: list[fitz.Rect] = []
    caption_top = None
    for b in raw["blocks"]:
        if b.get("type") != 0:
            continue
        txt = "".join(c["c"] for l in b["lines"] for s in l["spans"] for c in s["chars"])
        if txt.startswith("图33.4"):
            top = b["bbox"][1]
            caption_top = top if caption_top is None else min(caption_top, top)
    if caption_top is None:
        raise RuntimeError("caption not found")
    for b in raw["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                rr = fitz.Rect(s["bbox"])
                if rr.y0 >= 60 and rr.y1 < caption_top:
                    body_text_rects.append(rr)
                elif rr.y0 >= caption_top and rr.y1 <= caption_top + 35:
                    caption_rects.append(rr)
    body_draw_rects = [fitz.Rect(d["rect"]) for d in drawings if d["rect"].y0 >= 60 and d["rect"].y1 < caption_top]
    body_union = rect_union(body_text_rects + body_draw_rects)
    caption_union = rect_union(caption_rects)
    standalone_pt = fitz.Rect(
        body_union.x0-8, body_union.y0-8, body_union.x1+8,
        min(caption_top-0.5, body_union.y1+8),
    )
    figure_pt = fitz.Rect(min(body_union.x0, caption_union.x0)-4, body_union.y0-8, max(body_union.x1, caption_union.x1)+4, caption_union.y1+4)
    page_bounds = page300.size
    standalone_px = pix_rect(standalone_pt, SCALE300, page_bounds)
    figure_px = pix_rect(figure_pt, SCALE300, page_bounds)
    standalone = page300.crop(standalone_px)
    figure_crop = page300.crop(figure_px)
    standalone.save(DIRS["render"] / "standalone_300dpi.png")
    figure_crop.save(DIRS["render"] / "figure_crop_300dpi.png")
    standalone.convert("L").save(DIRS["render"] / "grayscale_300dpi.png")
    tiles = quadrant_8x(standalone, "standalone") + quadrant_8x(figure_crop, "figure_crop")
    save_csv(DIRS["machine"] / "render_8x_tiles.csv", tiles)

    full_arr = np.asarray(page300)
    glyph_rows: list[dict] = []
    whitespace_rows: list[dict] = []
    glyph_objects_full: list[ObjMask] = []
    text_members: dict[str, list[ObjMask]] = {}
    gid = 0
    for b in raw["blocks"]:
        if b.get("type") != 0:
            continue
        block = b["number"]
        for lidx, l in enumerate(b["lines"]):
            for sidx, s in enumerate(l["spans"]):
                for cidx, ch in enumerate(s["chars"]):
                    r = fitz.Rect(ch["bbox"])
                    if not (r.y0 >= 60 and r.y1 <= caption_top + 35):
                        continue
                    parent, role, source_line = group_for_char(block, lidx, r.x0, ch["c"])
                    if ch["c"].isspace():
                        whitespace_rows.append({"block": block, "line": lidx, "span": sidx, "char_index": cidx, "char": repr(ch["c"]), "parent_object_id": parent, "bbox_pt": list(r), "exclusion_reason": "WHITESPACE_NO_VISIBLE_FOREGROUND"})
                        continue
                    gid += 1
                    glyph_id = f"GLY_{gid:03d}_{safe_char(ch['c'])}"
                    bp = pix_rect(r, SCALE300, page_bounds)
                    mask, mb = char_mask(full_arr, bp, int_to_rgb(s["color"]))
                    tb = tight_bbox(mask, (mb[0], mb[1]))
                    if tb is None:
                        tb = mb
                        local = mask
                    else:
                        lx0, ly0, lx1, ly1 = tb
                        local = mask[ly0-mb[1]:ly1-mb[1], lx0-mb[0]:lx1-mb[0]]
                    gx0, gy0, gx1, gy1 = tb
                    safe_name = f"{glyph_id}.png"
                    save_local_mask(DIRS["mask_glyph"] / safe_name, local)
                    cls = classify_char(ch["c"], s["font"], parent)
                    h_ink = int(np.count_nonzero(np.any(local, axis=1))) if local.size else 0
                    area = int(np.count_nonzero(local))
                    threshold = threshold_for_class(cls)
                    threshold_state = "NOT_APPLICABLE" if threshold is None else ("MEETS_LEGACY_THRESHOLD" if h_ink >= threshold else "BELOW_LEGACY_THRESHOLD_ADVISORY_UNDER_R168")
                    row = {
                        "glyph_id": glyph_id, "safe_filename": safe_name, "char": ch["c"], "codepoint": f"U+{ord(ch['c']):04X}",
                        "parent_object_id": parent, "role": role, "block": block, "line": lidx, "span": sidx, "char_index": cidx,
                        "source_file": str(SOURCE), "source_line": source_line, "declared_pt": source_declared_pt(parent),
                        "pdf_observed_pt": round(float(s["size"]), 6), "font": s["font"], "color_rgb": int_to_rgb(s["color"]),
                        "script_class": cls, "bbox_pt": [round(v, 6) for v in r], "bbox_full_300px": list(tb),
                        "bbox_figure_crop_300px": [gx0-figure_px[0], gy0-figure_px[1], gx1-figure_px[0], gy1-figure_px[1]],
                        "h_ink_px": h_ink, "ink_area_px": area, "legacy_threshold_px": threshold,
                        "machine_threshold_state": threshold_state, "mask_nonempty": bool(area), "mask_path": f"masks/glyph/{safe_name}",
                    }
                    glyph_rows.append(row)
                    om = ObjMask(glyph_id, "GLYPH", role, tb, local, [glyph_id], f"glyph {ch['c']} of {parent}")
                    glyph_objects_full.append(om)
                    text_members.setdefault(parent, []).append(om)

    save_csv(DIRS["machine"] / "glyph_inventory.csv", glyph_rows)
    (DIRS["machine"] / "glyph_inventory.json").write_text(json.dumps(glyph_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    save_csv(DIRS["machine"] / "whitespace_exclusions.csv", whitespace_rows)

    # Raw PDF drawing/path inventory and isolated component masks.
    raw_drawing_rows: list[dict] = []
    comp_masks: dict[str, ObjMask] = {}
    relevant_draw_indices = [i for i,d in enumerate(drawings) if d["rect"].y0 >= 60 and d["rect"].y1 < caption_top]
    for i in relevant_draw_indices:
        d = drawings[i]
        raw_drawing_rows.append({
            "raw_drawing_index": i, "bbox_pt": [round(v,6) for v in d["rect"]], "item_count": len(d["items"]),
            "item_types": ",".join(it[0] for it in d["items"]), "stroke_color": d.get("color"), "fill_color": d.get("fill"),
            "width_pt": d.get("width"), "fill_opacity": d.get("fill_opacity"), "stroke_opacity": d.get("stroke_opacity"),
        })
        use_stroke = d.get("color") is not None
        use_fill = d.get("fill") is not None
        if i in (5, 31):
            if use_stroke:
                m,bp = shape_mask(page.rect,d,True,False,page_bounds); comp_masks[f"D{i:02d}_STROKE"] = ObjMask(f"D{i:02d}_STROKE","RAW_PATH_COMPONENT","STROKE",bp,m,[f"drawing:{i}:stroke"],"raw PDF stroke")
            if use_fill:
                m,bp = shape_mask(page.rect,d,False,True,page_bounds); comp_masks[f"D{i:02d}_FILL"] = ObjMask(f"D{i:02d}_FILL","BACKGROUND_COMPONENT","FILL",bp,m,[f"drawing:{i}:fill"],"mapped but excluded background fill")
        else:
            m,bp = shape_mask(page.rect,d,use_stroke,use_fill,page_bounds)
            comp_masks[f"D{i:02d}"] = ObjMask(f"D{i:02d}","RAW_PATH_COMPONENT","PATH",bp,m,[f"drawing:{i}"],"raw PDF path")
    save_csv(DIRS["machine"] / "raw_drawing_inventory.csv", raw_drawing_rows)

    graphic_specs = [
        ("GR_AXIS_X","AXIS_ARROW",["D01","D02"],"horizontal x1 axis shaft plus arrowhead"),
        ("GR_AXIS_Y","AXIS_ARROW",["D03","D04"],"vertical x2 axis shaft plus arrowhead"),
        ("GR_CONTOUR_OUTER","CONTOUR",["D05_STROKE"],"outer target-density ellipse contour; fill separately excluded"),
        ("GR_CONTOUR_MIDDLE","CONTOUR",["D06"],"middle target-density ellipse contour"),
        ("GR_CONTOUR_INNER","CONTOUR",["D07"],"inner target-density ellipse contour"),
        ("GR_MOVE_01","GIBBS_MOVE_ARROW",["D08","D09"],"horizontal move p0 to p1"),
        ("GR_MOVE_12","GIBBS_MOVE_ARROW",["D10","D11"],"vertical move p1 to p2"),
        ("GR_MOVE_23","GIBBS_MOVE_ARROW",["D12","D13"],"horizontal move p2 to p3"),
        ("GR_MOVE_34","GIBBS_MOVE_ARROW",["D14","D15"],"vertical move p3 to p4"),
        ("GR_MOVE_45","GIBBS_MOVE_ARROW",["D16","D17"],"horizontal move p4 to p5"),
        ("GR_MOVE_56","GIBBS_MOVE_ARROW",["D18","D19"],"vertical move p5 to p6"),
        ("GR_MARKER_0","MARKER",["D20"],"path state marker p0"),
        ("GR_MARKER_1","MARKER",["D21"],"path state marker p1"),
        ("GR_MARKER_2","MARKER",["D22"],"path state marker p2"),
        ("GR_MARKER_3","MARKER",["D23"],"path state marker p3"),
        ("GR_MARKER_4","MARKER",["D24"],"path state marker p4"),
        ("GR_MARKER_5","MARKER",["D25"],"path state marker p5"),
        ("GR_MARKER_6","MARKER",["D26"],"path state marker p6"),
        ("GR_LONG_AXIS","GEOMETRY_GUIDE_ARROW",["D27","D28"],"long-axis direction arrow"),
        ("GR_SHORT_AXIS","GEOMETRY_GUIDE_ARROW",["D29","D30"],"short-axis direction arrow"),
        ("GR_INFO_BORDER","NODE_BORDER",["D31_STROKE"],"rounded teaching-note border; white fill separately excluded"),
    ]
    graphic_objects_full: list[ObjMask] = []
    graphic_rows: list[dict] = []
    for oid, role, ids, note in graphic_specs:
        obj = union_masks(oid,"GRAPHIC",role,[comp_masks[x] for x in ids],note)
        graphic_objects_full.append(obj)
        safe_name = f"{oid}.png"
        save_local_mask(DIRS["mask_object"] / safe_name,obj.mask)
        graphic_rows.append({"object_id":oid,"category":"GRAPHIC","role":role,"bbox_full_300px":list(obj.bbox),"source_members":"|".join(obj.source_members),"semantic_note":note,"mask_pixels":int(obj.mask.sum()),"mask_path":f"masks/object/{safe_name}","included_in_pair_denominator":True})

    # Composite independent text objects from all glyph masks.
    text_objects_full: list[ObjMask] = []
    text_rows: list[dict] = []
    for oid, members in text_members.items():
        role = members[0].role
        obj = union_masks(oid,"TEXT",role,members,f"independent visible text object {oid}")
        text_objects_full.append(obj)
        safe_name = f"{oid}.png"
        save_local_mask(DIRS["mask_object"] / safe_name,obj.mask)
        text = "".join(next(r["char"] for r in glyph_rows if r["glyph_id"] == mid) for m in members for mid in m.source_members)
        text_rows.append({"object_id":oid,"category":"TEXT","role":role,"text":text,"bbox_full_300px":list(obj.bbox),"glyph_count":len(members),"source_members":"|".join(obj.source_members),"semantic_note":obj.semantic_note,"mask_pixels":int(obj.mask.sum()),"mask_path":f"masks/object/{safe_name}","included_in_pair_denominator":True})

    excluded = [
        {"element_id":"BG_OUTER_ELLIPSE_FILL","mapped_source":"drawing:5:fill","reason":"pale target-region fill is background, not an independent foreground collision object","mask_nonempty":bool(comp_masks["D05_FILL"].mask.any())},
        {"element_id":"BG_INFO_NODE_WHITE_FILL","mapped_source":"drawing:31:fill","reason":"opaque white node interior is background/occlusion layer, not border foreground","mask_nonempty":bool(comp_masks["D31_FILL"].mask.any())},
    ]
    for i,d in enumerate(drawings):
        if i not in relevant_draw_indices:
            excluded.append({"element_id":f"PAGE_DRAWING_{i:02d}","mapped_source":f"drawing:{i}","reason":"outside independently located FIG-P637-01 figure/caption bounds","mask_nonempty":"NOT_RENDERED_OUT_OF_SCOPE"})
    save_csv(DIRS["machine"] / "drawn_element_exclusions.csv", excluded)

    objects_full = text_objects_full + graphic_objects_full
    object_rows = text_rows + graphic_rows
    save_csv(DIRS["machine"] / "object_inventory.csv",object_rows)
    (DIRS["machine"] / "object_inventory.json").write_text(json.dumps(object_rows,ensure_ascii=False,indent=2),encoding="utf-8")

    clip_rows=[]
    for obj in objects_full:
        viewport_name = "FIGURE_CROP_300DPI" if obj.object_id.startswith("TXT_CAPTION") else "STANDALONE_300DPI"
        vx0,vy0,vx1,vy1 = figure_px if viewport_name=="FIGURE_CROP_300DPI" else standalone_px
        x0,y0,x1,y1=obj.bbox
        margins={"left":x0-vx0,"top":y0-vy0,"right":vx1-x1,"bottom":vy1-y1}
        clip_rows.append({"object_id":obj.object_id,"viewport":viewport_name,"left_ink_margin_px":margins["left"],"top_ink_margin_px":margins["top"],"right_ink_margin_px":margins["right"],"bottom_ink_margin_px":margins["bottom"],"min_ink_margin_px":min(margins.values()),"clip_pixel_count":0 if min(margins.values())>=0 else "NONZERO_REQUIRES_REVIEW","manual_decision":"UNSET_BY_MACHINE"})
    save_csv(DIRS["machine"] / "clip_clearance_inventory.csv",clip_rows)

    # Crop-coordinate object copies, overview, and graphics cards.
    fx0,fy0,fx1,fy1 = figure_px
    objects_crop: list[ObjMask] = []
    for obj in objects_full:
        x0,y0,x1,y1=obj.bbox
        objects_crop.append(ObjMask(obj.object_id,obj.category,obj.role,(x0-fx0,y0-fy0,x1-fx0,y1-fy0),obj.mask,obj.source_members,obj.semantic_note))
    overlay = figure_crop.copy()
    od = ImageDraw.Draw(overlay)
    for obj in objects_crop:
        x0,y0,x1,y1=obj.bbox
        color=(210,0,0) if obj.category=="TEXT" else (0,70,210)
        od.rectangle((x0,y0,x1-1,y1-1),outline=color,width=2)
        od.text((x0,max(0,y0-12)),obj.object_id,fill=color)
    overlay.save(DIRS["render"] / "object_measurement_overlay_300dpi.png")

    glyph_crop_objs=[]
    glyph_map={r["glyph_id"]:r for r in glyph_rows}
    for obj in glyph_objects_full:
        x0,y0,x1,y1=obj.bbox
        glyph_crop_objs.append(ObjMask(obj.object_id,obj.category,obj.role,(x0-fx0,y0-fy0,x1-fx0,y1-fy0),obj.mask,obj.source_members,obj.semantic_note))
    sheet_map=make_glyph_sheets(figure_crop,glyph_crop_objs,glyph_map)
    save_csv(DIRS["machine"] / "glyph_contact_sheet_map.csv",sheet_map)

    graphic_crop_by_id={o.object_id:o for o in objects_crop if o.category=="GRAPHIC"}
    graphic_card_rows=[]
    for i,(oid,obj) in enumerate(graphic_crop_by_id.items(),1):
        name=f"graphic_{i:02d}_{oid}.png"
        save_overlay_card(DIRS["contact_graphic"] / name,figure_crop,obj)
        graphic_card_rows.append({"object_id":oid,"card":f"contact_sheets/graphic/{name}","views":"ORIGINAL|TARGET_OVERLAY|MASK_ONLY","scale":"1x native"})
    save_csv(DIRS["machine"] / "graphic_contact_card_map.csv",graphic_card_rows)

    # All unordered pairs over independent foreground object denominator.
    pair_rows=[]
    critical=[]
    for k,(a,b) in enumerate(itertools.combinations(objects_full,2),1):
        overlap,clearance,bbox_gap=pair_metrics(a,b)
        if a.category=="TEXT" and b.category=="TEXT":
            rel="TEXT_TEXT"; threshold=4
        elif "TEXT" in (a.category,b.category):
            g=b if b.category=="GRAPHIC" else a
            if g.role=="NODE_BORDER": threshold=5; rel="TEXT_NODE_BORDER"
            elif g.role=="MARKER": threshold=3; rel="TEXT_MARKER"
            else: threshold=3; rel="TEXT_LINE_OR_GRAPHIC"
        else:
            rel="GRAPHIC_GRAPHIC"; threshold=0
        flag = overlap>0 or (threshold>0 and clearance < threshold)
        row={
            "pair_id":f"PAIR_{k:04d}","object_a":a.object_id,"object_b":b.object_id,"category_a":a.category,"category_b":b.category,
            "role_a":a.role,"role_b":b.role,"relation_class":rel,"raw_isolated_mask_intersection_px":overlap,
            "min_raw_mask_clearance_px":round(clearance,3),"bbox_gap_lower_bound_px":bbox_gap,"classification_threshold_px":threshold,
            "machine_review_flag":bool(flag),"manual_decision":"UNSET_BY_MACHINE","manual_note":"UNSET_BY_MACHINE",
        }
        pair_rows.append(row)
        if flag:
            critical.append((row,a,b))
    expected_pairs=len(objects_full)*(len(objects_full)-1)//2
    if len(pair_rows)!=expected_pairs:
        raise RuntimeError("pair denominator mismatch")
    save_csv(DIRS["machine"] / "all_unordered_pairs.csv",pair_rows)

    text_relation_rows=[r for r in pair_rows if r["relation_class"]!="GRAPHIC_GRAPHIC"]
    text_graphic_rows=[r for r in pair_rows if "TEXT" in (r["category_a"],r["category_b"]) and r["category_a"]!=r["category_b"]]
    text_text_rows=[r for r in pair_rows if r["relation_class"]=="TEXT_TEXT"]

    # Pair cards for every machine-flagged relation, native 1x plus exact 8x-nearest copy.
    pair_card_rows=[]
    for row,a,b in critical:
        ax0,ay0,ax1,ay1=a.bbox; bx0,by0,bx1,by1=b.bbox
        rx0=max(fx0,min(ax0,bx0)-8); ry0=max(fy0,min(ay0,by0)-8)
        rx1=min(fx1,max(ax1,bx1)+8); ry1=min(fy1,max(ay1,by1)+8)
        local=page300.crop((rx0,ry0,rx1,ry1)).convert("RGB")
        arr=np.array(local)
        ma=np.zeros((ry1-ry0,rx1-rx0),dtype=bool); mb=np.zeros_like(ma)
        ma[ay0-ry0:ay1-ry0,ax0-rx0:ax1-rx0]=a.mask
        mb[by0-ry0:by1-ry0,bx0-rx0:bx1-rx0]=b.mask
        ov=arr.copy(); ov[ma]=np.array([255,0,0],dtype=np.uint8); ov[mb]=np.array([0,90,255],dtype=np.uint8); ov[ma&mb]=np.array([255,0,255],dtype=np.uint8)
        im=Image.fromarray(ov)
        stem=f"{row['pair_id']}_{a.object_id}__{b.object_id}"
        one=DIRS["roi"]/(stem+"_1x.png"); eight=DIRS["roi"]/(stem+"_8x_nearest.png")
        im.save(one); im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(eight)
        pair_card_rows.append({"pair_id":row["pair_id"],"roi_full_300px":[rx0,ry0,rx1,ry1],"one_x":f"pair_rois/{one.name}","eight_x":f"pair_rois/{eight.name}"})
    save_csv(DIRS["machine"] / "pair_card_map.csv",pair_card_rows)

    # Machine cross-check. No reviewer fields or verdicts are generated here.
    role_counts={}
    for r in object_rows: role_counts[r["role"]]=role_counts.get(r["role"],0)+1
    machine_summary={
        "handoff_id":HANDOFF_ID,"uid":UID,"tex_execution":"DISABLED","source_writer":"NONE",
        "official_pdf":str(PDF),"official_pdf_bytes":pdf_bytes,"official_pdf_sha256":pdf_hash,"pdf_page_count":doc.page_count,
        "independent_locator_terms":["固定教学示意","二维Gibbs","轴向短步"],"locator_matches_physical_pages_1_based":[i+1 for i in matches],
        "located_physical_page_1_based":pidx+1,"printed_page_text":page.get_text("words",sort=True)[0][4],
        "page_pt":[page.rect.width,page.rect.height],"full_page_300px":list(page300.size),"full_page_200px":list(page200.size),
        "figure_crop_pt":[figure_pt.x0,figure_pt.y0,figure_pt.x1,figure_pt.y1],"figure_crop_full_page_300px":list(figure_px),"figure_crop_native_dimensions":list(figure_crop.size),
        "standalone_crop_pt":[standalone_pt.x0,standalone_pt.y0,standalone_pt.x1,standalone_pt.y1],"standalone_full_page_300px":list(standalone_px),"standalone_native_dimensions":list(standalone.size),
        "raw_pdf_drawing_count_on_page":len(drawings),"raw_pdf_drawings_mapped_to_figure":len(relevant_draw_indices),"raw_pdf_drawings_excluded_outside_figure":len(drawings)-len(relevant_draw_indices),
        "mapped_background_fill_exclusions":2,"independent_text_object_count":len(text_objects_full),"independent_graphic_object_count":len(graphic_objects_full),
        "pair_denominator_n":len(objects_full),"expected_unordered_pairs":expected_pairs,"actual_unordered_pair_rows":len(pair_rows),
        "visible_glyph_count":len(glyph_rows),"whitespace_exclusion_count":len(whitespace_rows),"glyph_mask_nonempty_count":sum(bool(r["mask_nonempty"]) for r in glyph_rows),
        "glyph_contact_sheet_cell_count":len(sheet_map),"glyph_contact_sheet_count":len(set(r["sheet"] for r in sheet_map)),
        "graphic_card_count":len(graphic_card_rows),"machine_flagged_pair_count":len(critical),"pair_card_count":len(pair_card_rows),
        "text_text_pair_count":len(text_text_rows),"text_graphic_pair_count":len(text_graphic_rows),
        "text_text_raw_intersection_total_px":sum(int(r["raw_isolated_mask_intersection_px"]) for r in text_text_rows),
        "text_graphic_raw_intersection_total_px":sum(int(r["raw_isolated_mask_intersection_px"]) for r in text_graphic_rows),
        "minimum_text_relation_raw_mask_clearance_px":min(float(r["min_raw_mask_clearance_px"]) for r in text_relation_rows),
        "clip_inventory_row_count":len(clip_rows),"clip_pixel_count_total":sum(int(r["clip_pixel_count"]) for r in clip_rows if str(r["clip_pixel_count"]).isdigit()),
        "minimum_assigned_viewport_ink_margin_px":min(int(r["min_ink_margin_px"]) for r in clip_rows),
        "math_rule_path_count":0,"math_rule_explanation":"No overline/underline/accent/radical/fraction/cancel rule occurs in the located figure or caption; x subscripts are PDF text glyphs and inventoried individually.",
        "object_role_counts":role_counts,
        "manual_fields_generated":False,"manual_decision_sentinel":"UNSET_BY_MACHINE",
    }
    (DIRS["machine"] / "machine_summary.json").write_text(json.dumps(machine_summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(machine_summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
