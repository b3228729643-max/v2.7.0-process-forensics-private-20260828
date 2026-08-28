from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_rmse_rate.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825")
PAGE_INDEX = 632
PHYSICAL_PAGE = 633
SCALE300 = 300.0 / 72.0
SCALE200 = 200.0 / 72.0
FIGURE_RECT_PT = (60.0, 60.0, 523.0, 253.0)  # chart + caption
BODY_RECT_PT = (137.0, 60.0, 442.0, 219.0)  # chart body only
EXPECTED_PDF_SIZE = 4_967_184
EXPECTED_PDF_SHA256 = "9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23"

VIEWS = ROOT / "views"
MACHINE = ROOT / "machine"
GLYPH_DIR = ROOT / "objects" / "glyphs"
GRAPHIC_DIR = ROOT / "objects" / "graphics"
CONTACTS = ROOT / "contacts"
PAIRS = ROOT / "pairs"
CRITICAL = ROOT / "critical"


def mkdirs() -> None:
    for p in (VIEWS, MACHINE, GLYPH_DIR, GRAPHIC_DIR, CONTACTS, PAIRS, CRITICAL):
        p.mkdir(parents=True, exist_ok=True)
    # Rebuild only machine-owned outputs.  The script never opens or touches manual/.
    for p in (VIEWS, MACHINE, GLYPH_DIR, GRAPHIC_DIR, CONTACTS, PAIRS, CRITICAL):
        for child in p.iterdir():
            if child.is_file():
                child.unlink()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rect_px(rect_pt: tuple[float, float, float, float], scale: float) -> tuple[int, int, int, int]:
    return (
        math.floor(rect_pt[0] * scale),
        math.floor(rect_pt[1] * scale),
        math.ceil(rect_pt[2] * scale),
        math.ceil(rect_pt[3] * scale),
    )


def int_color_to_rgb(v: int) -> tuple[int, int, int]:
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def fitz_color_to_rgb(v) -> tuple[int, int, int] | None:
    if v is None:
        return None
    return tuple(int(round(float(x) * 255.0)) for x in v)


def color_line_mask(arr: np.ndarray, color: tuple[int, int, int], residual_limit: float = 34.0) -> np.ndarray:
    """Pixels on the antialias blend line from white to the declared foreground colour."""
    a = arr.astype(np.float32)
    c = np.asarray(color, dtype=np.float32)
    direction = 255.0 - c
    denom = float(np.dot(direction, direction))
    if denom < 1.0:
        return np.zeros(a.shape[:2], dtype=bool)
    delta = 255.0 - a
    alpha = np.clip(np.tensordot(delta, direction, axes=([2], [0])) / denom, 0.0, 1.0)
    pred = 255.0 - alpha[..., None] * direction
    residual = np.sqrt(np.sum((a - pred) ** 2, axis=2))
    contrast = np.max(delta, axis=2)
    return (contrast >= 20.0) & (residual <= residual_limit)


def foreground_mask(arr: np.ndarray) -> np.ndarray:
    return np.max(255 - arr.astype(np.int16), axis=2) >= 20


def tight_bbox(mask: np.ndarray, origin: tuple[int, int]) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    ox, oy = origin
    return (int(xs.min() + ox), int(ys.min() + oy), int(xs.max() + ox + 1), int(ys.max() + oy + 1))


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def semantic_for(block_text: str, line_index: int) -> tuple[str, str]:
    text = block_text.replace("\n", "")
    if text == "1416642561024":
        return f"TXT_XTICK_{line_index + 1:02d}", "TICK_LABEL"
    if text in {"1/32", "1/16", "1/8", "1/4", "1/2", "1"}:
        return f"TXT_YTICK_{text.replace('/', '_')}", "TICK_LABEL"
    if "𝑂(𝑁" in text:
        return "TXT_RATE_FORMULA", "FORMULA"
    if "样本量×4" in text:
        return "TXT_TRIANGLE_NOTE", "ANNOTATION"
    if "理论速率条件" in text:
        return "TXT_CONDITION_NODE", "NODE_TEXT"
    if "样本量𝑁" in text:
        return "TXT_X_AXIS_LABEL", "AXIS_TITLE"
    if text == "RMSE":
        return "TXT_Y_AXIS_LABEL", "AXIS_TITLE"
    return f"TXT_UNMAPPED_L{line_index:02d}", "UNKNOWN_TEXT"


def glyph_category(char: str, size_pt: float, parent: str) -> tuple[str, int]:
    cp = ord(char)
    if parent == "TXT_RATE_FORMULA" and size_pt < 8.0:
        return "NATURAL_SCRIPT", 15
    if 0x3400 <= cp <= 0x9FFF:
        return "CJK", 30
    if char in "×÷−/+()":
        return "MATH_BASE_OR_OPERATOR", 22
    if char.isdigit() or char.isupper() or 0x1D400 <= cp <= 0x1D7FF:
        return "UPPER_DIGIT_MATH_LETTER", 24
    if char.islower():
        return "LOWER_LATIN", 17
    return "OTHER_VISIBLE", 17


def flatten_figure_chars(page) -> tuple[list[dict], list[dict]]:
    rd = page.get_text("rawdict")
    chars: list[dict] = []
    blocks_out: list[dict] = []
    bx0, by0, bx1, by1 = BODY_RECT_PT
    for bi, block in enumerate(rd["blocks"]):
        if block.get("type") != 0:
            continue
        block_chars = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_chars.extend(ch.get("c", "") for ch in span.get("chars", []))
        block_text = "".join(block_chars)
        visible_in_body = False
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                for ci, ch in enumerate(span.get("chars", [])):
                    c = ch.get("c", "")
                    x0, y0, x1, y1 = [float(v) for v in ch["bbox"]]
                    if x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1:
                        continue
                    if not c or c.isspace():
                        continue
                    visible_in_body = True
                    parent, role = semantic_for(block_text, li)
                    chars.append({
                        "char": c,
                        "codepoint": f"U+{ord(c):04X}",
                        "bbox_pt": [x0, y0, x1, y1],
                        "origin_pt": [float(v) for v in ch.get("origin", (x0, y1))],
                        "font": span.get("font", ""),
                        "pdf_size_pt": float(span.get("size", 0.0)),
                        "color_rgb": list(int_color_to_rgb(int(span.get("color", 0)))),
                        "block_index": bi,
                        "line_index": li,
                        "span_index": si,
                        "char_index": ci,
                        "semantic_parent": parent,
                        "role": role,
                    })
        if visible_in_body:
            blocks_out.append({"block_index": bi, "text": block_text, "bbox_pt": list(block.get("bbox", ()))})
    for i, row in enumerate(chars, 1):
        row["element_id"] = f"G{i:03d}"
        row["safe_filename"] = f"glyph_G{i:03d}"
    return chars, blocks_out


def draw_item_candidate(draw: ImageDraw.ImageDraw, item, ox: int, oy: int, scale: float, width_px: int, fill: bool = False) -> None:
    kind = item[0]
    def pt(p):
        return ((float(p.x) * scale) - ox, (float(p.y) * scale) - oy)
    if kind == "l":
        draw.line([pt(item[1]), pt(item[2])], fill=255, width=width_px)
    elif kind == "c":
        p0, p1, p2, p3 = [np.asarray(pt(p), dtype=float) for p in item[1:5]]
        pts = []
        for t in np.linspace(0.0, 1.0, 65):
            q = (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t*t*p2 + t**3*p3
            pts.append(tuple(q))
        draw.line(pts, fill=255, width=width_px)
    elif kind == "re":
        r = item[1]
        xy = [(r.x0 * scale - ox, r.y0 * scale - oy), (r.x1 * scale - ox, r.y1 * scale - oy)]
        if fill:
            draw.rectangle(xy, fill=255)
        else:
            draw.rectangle(xy, outline=255, width=width_px)


def graphic_specs(drawings: list[dict]) -> list[dict]:
    specs: list[dict] = []
    for item_index in range(6):
        specs.append({"drawing_index": 1, "item_indices": [item_index], "role": "AXIS_TICK", "parent": "GFX_X_AXIS_SYSTEM", "label": f"x_tick_{item_index+1}"})
    for item_index in range(6):
        specs.append({"drawing_index": 2, "item_indices": [item_index], "role": "AXIS_TICK", "parent": "GFX_Y_AXIS_SYSTEM", "label": f"y_tick_{item_index+1}"})
    specs.extend([
        {"drawing_index": 3, "item_indices": [0], "role": "AXIS_LINE", "parent": "GFX_X_AXIS_SYSTEM", "label": "x_axis_line"},
        {"drawing_index": 4, "item_indices": [0, 1, 2], "role": "ARROWHEAD", "parent": "GFX_X_AXIS_SYSTEM", "label": "x_axis_arrowhead", "filled": True},
        {"drawing_index": 5, "item_indices": [0], "role": "AXIS_LINE", "parent": "GFX_Y_AXIS_SYSTEM", "label": "y_axis_line"},
        {"drawing_index": 6, "item_indices": [0, 1, 2], "role": "ARROWHEAD", "parent": "GFX_Y_AXIS_SYSTEM", "label": "y_axis_arrowhead", "filled": True},
        {"drawing_index": 7, "item_indices": list(range(len(drawings[7].get("items", [])))), "role": "DATA_CURVE", "parent": "GFX_RATE_CURVE", "label": "rate_curve"},
        {"drawing_index": 8, "item_indices": list(range(len(drawings[8].get("items", [])))), "role": "CONSTRUCTION_TRIANGLE", "parent": "GFX_RATE_TRIANGLE", "label": "rate_triangle"},
        {"drawing_index": 10, "item_indices": list(range(len(drawings[10].get("items", [])))), "role": "NODE_BORDER", "parent": "GFX_CONDITION_NODE", "label": "condition_node_border"},
    ])
    for i, spec in enumerate(specs, 1):
        spec["element_id"] = f"P{i:03d}"
        spec["safe_filename"] = f"graphic_P{i:03d}"
    return specs


def extract_graphic_mask(page_arr: np.ndarray, drawing: dict, spec: dict) -> tuple[np.ndarray, tuple[int, int, int, int], dict]:
    body_px = rect_px(BODY_RECT_PT, SCALE300)
    bx0, by0, bx1, by1 = body_px
    local = page_arr[by0:by1, bx0:bx1]
    canvas = Image.new("L", (bx1 - bx0, by1 - by0), 0)
    d = ImageDraw.Draw(canvas)
    width_pt = float(drawing.get("width") or 0.75)
    # Stroke centreline + one antialias pixel per side.  A wider candidate band can
    # wrongly capture later text of a similar colour near (but not on) the path.
    width_px = max(2, int(math.ceil(width_pt * SCALE300)) + 2)
    selected = [drawing.get("items", [])[i] for i in spec["item_indices"]]
    if spec.get("filled"):
        pts = []
        for item in selected:
            if item[0] == "l":
                for p in item[1:3]:
                    xy = (float(p.x) * SCALE300 - bx0, float(p.y) * SCALE300 - by0)
                    if not pts or pts[-1] != xy:
                        pts.append(xy)
        if pts:
            d.polygon(pts, fill=255)
    else:
        for item in selected:
            draw_item_candidate(d, item, bx0, by0, SCALE300, width_px, fill=False)
    candidate = np.asarray(canvas) > 0
    color = fitz_color_to_rgb(drawing.get("color")) or fitz_color_to_rgb(drawing.get("fill")) or (0, 0, 0)
    cmask = color_line_mask(local, color, residual_limit=40.0)
    mask = candidate & cmask
    tb = tight_bbox(mask, (bx0, by0))
    if tb is None:
        tb = (bx0, by0, bx0, by0)
    meta = {"declared_color_rgb": list(color), "candidate_pixel_count": int(candidate.sum()), "mask_pixel_count": int(mask.sum())}
    return mask, tb, meta


def object_coords(mask_local: np.ndarray, local_origin: tuple[int, int]) -> np.ndarray:
    ys, xs = np.nonzero(mask_local)
    return np.column_stack([ys + local_origin[1], xs + local_origin[0]]).astype(np.int32)


def save_object_mask(mask_local: np.ndarray, bbox_page: tuple[int, int, int, int], origin: tuple[int, int], path: Path) -> None:
    x0, y0, x1, y1 = bbox_page
    ox, oy = origin
    crop = mask_local[y0-oy:y1-oy, x0-ox:x1-ox]
    save_mask(crop, path)


def font() -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, 18)
    return ImageFont.load_default()


LABEL_FONT = font()


def overlay_for_mask(page_img: Image.Image, bbox: tuple[int, int, int, int], coords: np.ndarray, pad: int = 6) -> tuple[Image.Image, Image.Image, Image.Image, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bbox
    roi = (max(0, x0-pad), max(0, y0-pad), min(page_img.width, x1+pad), min(page_img.height, y1+pad))
    original = page_img.crop(roi).convert("RGB")
    overlay = original.copy()
    oa = np.asarray(overlay).copy()
    mask = np.zeros((roi[3]-roi[1], roi[2]-roi[0]), dtype=bool)
    if len(coords):
        yy = coords[:, 0] - roi[1]
        xx = coords[:, 1] - roi[0]
        valid = (yy >= 0) & (yy < mask.shape[0]) & (xx >= 0) & (xx < mask.shape[1])
        mask[yy[valid], xx[valid]] = True
    oa[mask] = np.array([255, 0, 0], dtype=np.uint8)
    overlay = Image.fromarray(oa)
    mask_only = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).convert("RGB")
    return original, overlay, mask_only, roi


def contact_cell(page_img: Image.Image, obj: dict, cell_w: int = 1120, cell_h: int = 410) -> Image.Image:
    cell = Image.new("RGB", (cell_w, cell_h), "white")
    d = ImageDraw.Draw(cell)
    bbox = tuple(obj["tight_bbox_page_px"])
    coords = np.asarray(obj["_coords"], dtype=np.int32)
    original, overlay, mask_only, roi = overlay_for_mask(page_img, bbox, coords, pad=4)
    original8 = original.resize((original.width*8, original.height*8), Image.Resampling.NEAREST)
    overlay8 = overlay.resize((overlay.width*8, overlay.height*8), Image.Resampling.NEAREST)
    mask8 = mask_only.resize((mask_only.width*8, mask_only.height*8), Image.Resampling.NEAREST)
    maxh = 320
    maxw = 330
    def fit(im: Image.Image) -> Image.Image:
        # Every displayed 8x raster is first made by NEAREST; any further fit is navigation only.
        if im.width <= maxw and im.height <= maxh:
            return im
        ratio = min(maxw/im.width, maxh/im.height)
        return im.resize((max(1, int(im.width*ratio)), max(1, int(im.height*ratio))), Image.Resampling.NEAREST)
    panes = [fit(original8), fit(overlay8), fit(mask8)]
    header = f"{obj['element_id']} {obj.get('char', obj.get('label',''))} | bbox={bbox} | H={obj.get('h_ink_px','NA')} px | raw 1x ROI={roi}"
    d.text((10, 8), header, fill="black", font=LABEL_FONT)
    labels = ["ORIGINAL (8x NN)", "TARGET OVERLAY (8x NN)", "MASK ONLY (8x NN)"]
    x = 10
    for label, im in zip(labels, panes):
        d.text((x, 38), label, fill="black", font=LABEL_FONT)
        cell.paste(im, (x, 64))
        x += 365
    # Native 1x triplet is embedded at bottom-right for direct pixel reference.
    nx = cell_w - (original.width + overlay.width + mask_only.width + 30)
    if nx > 10:
        cell.paste(original, (nx, cell_h-original.height-6))
        cell.paste(overlay, (nx+original.width+5, cell_h-overlay.height-6))
        cell.paste(mask_only, (nx+original.width+overlay.width+10, cell_h-mask_only.height-6))
    return cell


def make_contact_sheets(page_img: Image.Image, objects: list[dict], prefix: str, per_sheet: int = 8) -> list[str]:
    paths = []
    for si in range(0, len(objects), per_sheet):
        chunk = objects[si:si+per_sheet]
        sheet = Image.new("RGB", (2240, 1640), (238, 238, 238))
        for j, obj in enumerate(chunk):
            cell = contact_cell(page_img, obj)
            sheet.paste(cell, ((j % 2) * 1120, (j // 2) * 410))
        out = CONTACTS / f"{prefix}_{si//per_sheet+1:02d}.png"
        sheet.save(out)
        paths.append(str(out.relative_to(ROOT)))
    return paths


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def exact_mask_distance(a: np.ndarray, b: np.ndarray) -> tuple[int, float]:
    if len(a) == 0 or len(b) == 0:
        return 0, float("inf")
    sa = set(map(tuple, a.tolist()))
    inter = sum(1 for p in map(tuple, b.tolist()) if p in sa)
    if inter:
        return inter, 0.0
    small, large = (a, b) if len(a) <= len(b) else (b, a)
    tree = cKDTree(large.astype(float))
    dist, _ = tree.query(small.astype(float), k=1)
    center = float(np.min(dist))
    return 0, max(0.0, center - 1.0)


def pair_policy(a: dict, b: dict) -> tuple[str, float | None, str]:
    ta, tb = a["kind"], b["kind"]
    if a["semantic_parent"] == b["semantic_parent"]:
        return "DESIGN_INTERNAL", None, "same semantic parent"
    if ta == "GRAPHIC" and tb == "GRAPHIC":
        axis_parents = {"GFX_X_AXIS_SYSTEM", "GFX_Y_AXIS_SYSTEM"}
        parents = {a["semantic_parent"], b["semantic_parent"]}
        if parents <= axis_parents or (parents & axis_parents and ("GFX_RATE_CURVE" in parents or "GFX_RATE_TRIANGLE" in parents)):
            return "INTENTIONAL_COORDINATE_GEOMETRY", None, "axis/tick/arrow/curve coordinate connection"
        if parents == {"GFX_RATE_CURVE", "GFX_RATE_TRIANGLE"}:
            return "INTENTIONAL_RATE_CONSTRUCTION", None, "triangle endpoints encode x4/y2 relation on curve"
        return "GRAPHIC_GRAPHIC", None, "visible foreground graphic pair"
    if ta == "GLYPH" and tb == "GLYPH":
        return "TEXT_TEXT_INDEPENDENT", 4.0, "independent semantic text objects use bbox clearance"
    text = a if ta == "GLYPH" else b
    graphic = b if ta == "GLYPH" else a
    if graphic["role"] == "NODE_BORDER" and text["semantic_parent"] == "TXT_CONDITION_NODE":
        return "NODE_TEXT_TO_BORDER", 5.0, "node text to final-visible border"
    return "TEXT_FORMULA_TO_LINE_MARKER", 3.0, "text/formula ink to line/arrow/marker"


def pair_status(policy: str, threshold: float | None, overlap: int, mask_gap: float, bbox_clear: float) -> str:
    if policy.startswith("DESIGN_") or policy.startswith("INTENTIONAL_"):
        return "DESIGN_OR_INTENTIONAL"
    if overlap > 0:
        return "FAIL_ILLEGAL_OVERLAP"
    if threshold is None:
        return "PASS"
    value = bbox_clear if policy == "TEXT_TEXT_INDEPENDENT" else mask_gap
    return "PASS" if value + 1e-9 >= threshold else "FAIL_CLEARANCE"


def make_pair_matrix(objects: list[dict], pair_rows: list[dict]) -> str:
    n = len(objects)
    mat = np.full((n, n, 3), 255, dtype=np.uint8)
    index = {o["element_id"]: i for i, o in enumerate(objects)}
    for row in pair_rows:
        i, j = index[row["a_id"]], index[row["b_id"]]
        status = row["machine_status"]
        if status.startswith("FAIL"):
            color = (210, 35, 35)
        elif row["critical"]:
            color = (240, 170, 40)
        elif status == "DESIGN_OR_INTENTIONAL":
            color = (80, 130, 210)
        else:
            color = (205, 225, 205)
        mat[i, j] = mat[j, i] = color
    for i in range(n):
        mat[i, i] = (40, 40, 40)
    im = Image.fromarray(mat).resize((n*10, n*10), Image.Resampling.NEAREST)
    out = PAIRS / "all_unordered_pairs_matrix_10x.png"
    im.save(out)
    return str(out.relative_to(ROOT))


def make_relation_overlay(page_img: Image.Image, objects: list[dict]) -> str:
    crop = rect_px(BODY_RECT_PT, SCALE300)
    im = page_img.crop(crop).convert("RGB")
    d = ImageDraw.Draw(im)
    parent_boxes: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    for o in objects:
        x0, y0, x1, y1 = o["tight_bbox_page_px"]
        parent_boxes[o["semantic_parent"]].append((x0-crop[0], y0-crop[1], x1-crop[0], y1-crop[1]))
    colours = [(230,20,20),(20,100,230),(20,160,80),(180,60,180),(230,120,20),(60,160,180)]
    for i, (parent, boxes) in enumerate(sorted(parent_boxes.items())):
        x0=min(b[0] for b in boxes); y0=min(b[1] for b in boxes); x1=max(b[2] for b in boxes); y1=max(b[3] for b in boxes)
        colour=colours[i%len(colours)]
        d.rectangle((x0,y0,x1,y1), outline=colour, width=2)
        d.text((x0,max(0,y0-20)),parent,fill=colour,font=LABEL_FONT)
    out = PAIRS / "semantic_relationship_overlay_1x.png"
    im.save(out)
    return str(out.relative_to(ROOT))


def critical_pair_image(page_img: Image.Image, a: dict, b: dict, row: dict, suffix: str) -> tuple[str, str]:
    ax0, ay0, ax1, ay1 = a["tight_bbox_page_px"]
    bx0, by0, bx1, by1 = b["tight_bbox_page_px"]
    pad = 10
    roi=(max(0,min(ax0,bx0)-pad),max(0,min(ay0,by0)-pad),min(page_img.width,max(ax1,bx1)+pad),min(page_img.height,max(ay1,by1)+pad))
    orig=np.asarray(page_img.crop(roi).convert("RGB")).copy()
    ma=np.zeros(orig.shape[:2],bool); mb=np.zeros(orig.shape[:2],bool)
    for coords,m in ((np.asarray(a["_coords"]),ma),(np.asarray(b["_coords"]),mb)):
        yy=coords[:,0]-roi[1]; xx=coords[:,1]-roi[0]
        ok=(yy>=0)&(yy<m.shape[0])&(xx>=0)&(xx<m.shape[1]); m[yy[ok],xx[ok]]=True
    overlay=orig.copy(); overlay[ma]=[255,0,0]; overlay[mb]=[0,80,255]; overlay[ma&mb]=[255,0,255]
    panel=Image.new("RGB",(orig.shape[1]*4,orig.shape[0]+32),"white")
    panel.paste(Image.fromarray(orig),(0,32))
    aa=np.full_like(orig,255); aa[ma]=[0,0,0]; panel.paste(Image.fromarray(aa),(orig.shape[1],32))
    bb=np.full_like(orig,255); bb[mb]=[0,0,0]; panel.paste(Image.fromarray(bb),(orig.shape[1]*2,32))
    panel.paste(Image.fromarray(overlay),(orig.shape[1]*3,32))
    ImageDraw.Draw(panel).text((4,4),f"{a['element_id']} / {b['element_id']} gap={row['mask_clearance_px']} overlap={row['intersection_px']}",fill="black",font=LABEL_FONT)
    p1=CRITICAL/f"{suffix}_1x.png"; p8=CRITICAL/f"{suffix}_8x_nearest.png"
    panel.save(p1)
    panel.resize((panel.width*8,panel.height*8),Image.Resampling.NEAREST).save(p8)
    return str(p1.relative_to(ROOT)),str(p8.relative_to(ROOT))


def make_critical_contact_sheets(entries: list[tuple[dict,dict,dict,str,str]]) -> list[str]:
    outs=[]
    for si in range(0,len(entries),6):
        chunk=entries[si:si+6]
        sheet=Image.new("RGB",(1800,1200),(238,238,238))
        for j,(a,b,row,p1,p8) in enumerate(chunk):
            im=Image.open(ROOT/p1).convert("RGB")
            im8=Image.open(ROOT/p8).convert("RGB")
            # Contact cell keeps the exact 1x panel and a nearest-neighbour 8x centre crop.
            cell=Image.new("RGB",(900,400),"white"); d=ImageDraw.Draw(cell)
            d.text((5,5),f"{row['pair_id']} {a['element_id']}/{b['element_id']} {row['relation_class']} status={row['machine_status']}",fill="black",font=LABEL_FONT)
            nav=im.copy(); nav.thumbnail((880,180),Image.Resampling.NEAREST); cell.paste(nav,(5,32))
            cx=max(0,(im8.width-880)//2); cy=max(0,(im8.height-160)//2)
            detail=im8.crop((cx,cy,min(im8.width,cx+880),min(im8.height,cy+160)))
            cell.paste(detail,(5,225))
            sheet.paste(cell,((j%2)*900,(j//2)*400))
        out=CONTACTS/f"critical_pairs_contact_{si//6+1:02d}.png"; sheet.save(out); outs.append(str(out.relative_to(ROOT)))
    return outs


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def main() -> None:
    mkdirs()
    pdf_size = PDF.stat().st_size
    pdf_hash = sha256(PDF)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = [float(v) for v in page.rect]
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), alpha=False, colorspace=fitz.csRGB)
    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE200, SCALE200), alpha=False, colorspace=fitz.csRGB)
    p300=VIEWS/"full_page_300dpi.png"; p200=VIEWS/"full_page_200dpi.png"
    pix300.save(p300); pix200.save(p200)
    page_img=Image.open(p300).convert("RGB"); page_arr=np.asarray(page_img)
    fig_px=rect_px(FIGURE_RECT_PT,SCALE300); body_px=rect_px(BODY_RECT_PT,SCALE300)
    figure=page_img.crop(fig_px); body=page_img.crop(body_px)
    figure.save(VIEWS/"figure_crop_300dpi.png")
    body.save(VIEWS/"standalone_300dpi.png")
    body.convert("L").save(VIEWS/"grayscale_300dpi.png")

    chars, blocks = flatten_figure_chars(page)
    glyph_objects=[]
    for row in chars:
        x0,y0,x1,y1=rect_px(tuple(row["bbox_pt"]),SCALE300)
        arr=page_arr[y0:y1,x0:x1]
        target=color_line_mask(arr,tuple(row["color_rgb"]),residual_limit=34.0)
        allfg=foreground_mask(arr)
        foreign=allfg & ~target
        tb=tight_bbox(target,(x0,y0))
        category,minimum=glyph_category(row["char"],row["pdf_size_pt"],row["semantic_parent"])
        if tb is None:
            h=w=0; tb=(x0,y0,x0,y0)
        else:
            w=tb[2]-tb[0]; h=tb[3]-tb[1]
        save_object_mask(target,tb,(x0,y0),GLYPH_DIR/f"{row['safe_filename']}_raw_mask.png")
        coords=object_coords(target,(x0,y0))
        obj={**row,"kind":"GLYPH","source_bbox_page_px":[x0,y0,x1,y1],"tight_bbox_page_px":list(tb),"w_ink_px":w,"h_ink_px":h,"pixel_count":int(target.sum()),"foreign_pixel_count_in_source_bbox":int(foreign.sum()),"category":category,"protocol_reference_min_px":minimum,"r168_size_advisory":bool(h<minimum or row["pdf_size_pt"]<9.5),"mask_path":str((GLYPH_DIR/f"{row['safe_filename']}_raw_mask.png").relative_to(ROOT)),"_coords":coords.tolist()}
        glyph_objects.append(obj)

    drawings=page.get_drawings(extended=False)
    specs=graphic_specs(drawings)
    graphic_objects=[]
    body_origin=(body_px[0],body_px[1])
    for spec in specs:
        drawing=drawings[spec["drawing_index"]]
        mask,tb,meta=extract_graphic_mask(page_arr,drawing,spec)
        save_object_mask(mask,tb,body_origin,GRAPHIC_DIR/f"{spec['safe_filename']}_raw_mask.png")
        coords=object_coords(mask,body_origin)
        obj={**spec,"kind":"GRAPHIC","semantic_parent":spec["parent"],"tight_bbox_page_px":list(tb),"pixel_count":int(mask.sum()),"drawing_seqno":drawing.get("seqno"),"drawing_rect_pt":[float(v) for v in drawing["rect"]],"drawing_width_pt":drawing.get("width"),"mask_path":str((GRAPHIC_DIR/f"{spec['safe_filename']}_raw_mask.png").relative_to(ROOT)),**meta,"_coords":coords.tolist()}
        graphic_objects.append(obj)

    # Refine glyph masks against the independently reconstructed PDF drawing masks.
    # This is necessary where a char bbox contains a nearby same-hue line (notably the
    # gold rate triangle immediately below the second annotation line).  The removed
    # pixels remain fully represented by their GRAPHIC object; no foreground is lost
    # from the object denominator.
    graphic_union = np.zeros((body_px[3]-body_px[1], body_px[2]-body_px[0]), dtype=bool)
    for g in graphic_objects:
        coords = np.asarray(g["_coords"], dtype=np.int32)
        yy = coords[:, 0] - body_px[1]
        xx = coords[:, 1] - body_px[0]
        ok = (yy >= 0) & (yy < graphic_union.shape[0]) & (xx >= 0) & (xx < graphic_union.shape[1])
        graphic_union[yy[ok], xx[ok]] = True
    for obj in glyph_objects:
        x0, y0, x1, y1 = obj["source_bbox_page_px"]
        arr = page_arr[y0:y1, x0:x1]
        provisional = color_line_mask(arr, tuple(obj["color_rgb"]), residual_limit=34.0)
        gy0, gy1 = y0-body_px[1], y1-body_px[1]
        gx0, gx1 = x0-body_px[0], x1-body_px[0]
        known_graphic = graphic_union[gy0:gy1, gx0:gx1]
        target = provisional & ~known_graphic
        allfg = foreground_mask(arr)
        foreign = allfg & ~(target | known_graphic)
        tb = tight_bbox(target, (x0, y0))
        if tb is None:
            tb = (x0, y0, x0, y0); w = h = 0
        else:
            w = tb[2]-tb[0]; h = tb[3]-tb[1]
        path = GLYPH_DIR/f"{obj['safe_filename']}_raw_mask.png"
        save_object_mask(target, tb, (x0, y0), path)
        obj.update({
            "tight_bbox_page_px": list(tb), "w_ink_px": w, "h_ink_px": h,
            "pixel_count": int(target.sum()),
            "foreign_pixel_count_in_source_bbox": int(foreign.sum()),
            "graphic_pixels_separated_from_source_bbox": int((provisional & known_graphic).sum()),
            "separation_basis": "PDF drawing geometry plus final 300dpi foreground; separated pixels remain in GRAPHIC denominator",
            "r168_size_advisory": bool(h < obj["protocol_reference_min_px"] or obj["pdf_size_pt"] < 9.5),
            "mask_path": str(path.relative_to(ROOT)),
            "_coords": object_coords(target, (x0, y0)).tolist(),
        })

    all_objects=glyph_objects+graphic_objects
    object_public=[]
    for o in all_objects:
        q={k:v for k,v in o.items() if not k.startswith("_") and k not in {"parent","filled","item_indices"}}
        object_public.append(q)
    write_csv(MACHINE/"glyph_measurements.csv",[{k:v for k,v in o.items() if not k.startswith("_")} for o in glyph_objects])
    write_csv(MACHINE/"graphic_objects.csv",[{k:v for k,v in o.items() if not k.startswith("_")} for o in graphic_objects])
    (MACHINE/"object_inventory.json").write_text(json.dumps(object_public,ensure_ascii=False,indent=2),encoding="utf-8")
    (MACHINE/"figure_text_blocks.json").write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding="utf-8")

    drawing_rows=[]
    used_drawings=defaultdict(list)
    for spec in specs: used_drawings[spec["drawing_index"]].append(spec["element_id"])
    for i,drawing in enumerate(drawings):
        r=tuple(float(v) for v in drawing["rect"])
        in_body=not (r[2]<BODY_RECT_PT[0] or r[0]>BODY_RECT_PT[2] or r[3]<BODY_RECT_PT[1] or r[1]>BODY_RECT_PT[3])
        if not in_body: continue
        if i==9: classification="BACKGROUND_OCCLUDER_WHITE"
        elif i==10: classification="FOREGROUND_BORDER_PLUS_BACKGROUND_FILL"
        elif i in used_drawings: classification="FOREGROUND_OBJECTS"
        else: classification="UNASSIGNED_VISIBLE_PATH"
        drawing_rows.append({"drawing_index":i,"seqno":drawing.get("seqno"),"rect_pt":json.dumps(r),"type":drawing.get("type"),"item_count":len(drawing.get("items",[])),"classification":classification,"mapped_object_ids":"|".join(used_drawings.get(i,[]))})
    write_csv(MACHINE/"drawing_path_reconciliation.csv",drawing_rows)

    source_audit=[
        {"selector":"tikz style global","declared_pt":9.2,"effective_pt":9.2,"roles":"default/triangle note/condition node","r168_disposition":"ADVISORY_IF_CLEAR"},
        {"selector":"tick label style","declared_pt":8.6,"effective_pt":8.6,"roles":"x/y tick labels","r168_disposition":"ADVISORY_IF_CLEAR"},
        {"selector":"label style","declared_pt":9.6,"effective_pt":9.6,"roles":"axis titles","r168_disposition":"PASS"},
        {"selector":"rate formula node","declared_pt":9.6,"effective_pt":9.6,"roles":"O(N^-1/2)","r168_disposition":"PASS"},
        {"selector":"triangle note node","declared_pt":9.2,"effective_pt":9.2,"roles":"sample x4/error /2","r168_disposition":"ADVISORY_IF_CLEAR"},
        {"selector":"condition node","declared_pt":9.2,"effective_pt":9.2,"roles":"iid finite variance","r168_disposition":"ADVISORY_IF_CLEAR"},
    ]
    write_csv(MACHINE/"source_font_audit.csv",source_audit)

    pair_rows=[]; critical_entries=[]
    for i,a in enumerate(all_objects):
        ac=np.asarray(a["_coords"],dtype=np.int32)
        for j in range(i+1,len(all_objects)):
            b=all_objects[j]; bc=np.asarray(b["_coords"],dtype=np.int32)
            overlap,gap=exact_mask_distance(ac,bc)
            bgap=bbox_gap(tuple(a["tight_bbox_page_px"]),tuple(b["tight_bbox_page_px"]))
            relation,threshold,note=pair_policy(a,b)
            status=pair_status(relation,threshold,overlap,gap,bgap)
            value=bgap if relation=="TEXT_TEXT_INDEPENDENT" else gap
            critical=bool(threshold is not None and value <= threshold+10.0)
            row={"pair_id":f"PAIR-{i+1:03d}-{j+1:03d}","a_id":a["element_id"],"b_id":b["element_id"],"a_kind":a["kind"],"b_kind":b["kind"],"relation_class":relation,"policy_note":note,"intersection_px":overlap,"mask_clearance_px":round(gap,3) if math.isfinite(gap) else "INF","bbox_clearance_px":round(bgap,3),"threshold_px":"N/A" if threshold is None else threshold,"critical":critical,"machine_status":status}
            pair_rows.append(row)
    write_csv(PAIRS/"all_unordered_pairs.csv",pair_rows)
    matrix_path=make_pair_matrix(all_objects,pair_rows)
    relation_overlay=make_relation_overlay(page_img,all_objects)

    by_id={o["element_id"]:o for o in all_objects}
    for row in pair_rows:
        if row["critical"]:
            a=by_id[row["a_id"]]; b=by_id[row["b_id"]]
            p1,p8=critical_pair_image(page_img,a,b,row,row["pair_id"])
            critical_entries.append((a,b,row,p1,p8))
    critical_sheets=make_critical_contact_sheets(critical_entries)
    glyph_sheets=make_contact_sheets(page_img,glyph_objects,"glyph_contact_sheet",8)
    graphic_sheets=make_contact_sheets(page_img,graphic_objects,"graphic_contact_sheet",8)

    # Font D/E machine summaries. Ratios are reported as R168 advisory, never a machine FAIL by themselves.
    groups=defaultdict(list)
    for o in glyph_objects:
        groups[(o["role"],o["category"])].append(o["h_ink_px"])
    ratio_rows=[]
    for (role,cat),vals in sorted(groups.items()):
        med=float(np.median(vals)); ratios=[v/med if med else 0 for v in vals]
        ratio_rows.append({"role":role,"category":cat,"count":len(vals),"median_h_px":round(med,3),"min_h_px":min(vals),"max_h_px":max(vals),"min_ratio":round(min(ratios),3),"max_ratio":round(max(ratios),3),"r168_disposition":"ADVISORY" if (min(ratios)<0.92 or max(ratios)>1.08) else "WITHIN_MICRO_BAND"})
    write_csv(MACHINE/"font_role_ratio_advisories.csv",ratio_rows)

    hard_pair_fails=[r for r in pair_rows if r["machine_status"].startswith("FAIL")]
    empty=[o["element_id"] for o in all_objects if o["pixel_count"]==0]
    foreign=[o["element_id"] for o in glyph_objects if o["foreign_pixel_count_in_source_bbox"]>0]
    expected_pairs=len(all_objects)*(len(all_objects)-1)//2
    hard_pass=(pdf_size==EXPECTED_PDF_SIZE and pdf_hash==EXPECTED_PDF_SHA256 and len(doc)==817 and len(pair_rows)==expected_pairs and not empty and not hard_pair_fails and not foreign and all(r["classification"]!="UNASSIGNED_VISIBLE_PATH" for r in drawing_rows))
    metadata={
        "handoff_id":"A-R103-P583-SA1-FRESH-20260825","uid":"FIG-P583-01","model_effort":"gpt-5.6-sol/xhigh","official_pdf":str(PDF),"physical_page":PHYSICAL_PAGE,"page_index_zero_based":PAGE_INDEX,"pdf_page_count":len(doc),"pdf_size_bytes":pdf_size,"pdf_sha256":pdf_hash,"page_rect_pt":page_rect,"native_300dpi_grid_px":[page_img.width,page_img.height],"native_200dpi_grid_px":[pix200.width,pix200.height],"figure_crop_rect_pt":list(FIGURE_RECT_PT),"figure_crop_rect_page_px":list(fig_px),"figure_crop_dimensions_px":[figure.width,figure.height],"standalone_rect_pt":list(BODY_RECT_PT),"standalone_rect_page_px":list(body_px),"standalone_dimensions_px":[body.width,body.height],"render_rule":"direct PyMuPDF native 300/200 dpi render; integer crop only; no resize for measurement views","source_tex":str(SOURCE),"tex_execution":"none; source read-only; no TeX engine invoked"
    }
    (MACHINE/"candidate_identity_and_render.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    expected_pngs=len(all_objects)
    mask_pngs=len(list(GLYPH_DIR.glob("*.png")))+len(list(GRAPHIC_DIR.glob("*.png")))
    cross={
        "machine_hard_gates_pass":hard_pass,
        "glyph_object_count":len(glyph_objects),"graphic_object_count":len(graphic_objects),"total_object_count":len(all_objects),"expected_unordered_pairs":expected_pairs,"actual_unordered_pairs":len(pair_rows),"critical_pair_count":len(critical_entries),"hard_pair_fail_count":len(hard_pair_fails),"hard_pair_fail_ids":[r["pair_id"] for r in hard_pair_fails],"empty_mask_count":len(empty),"empty_mask_ids":empty,"foreign_pixel_bbox_count":len(foreign),"foreign_pixel_bbox_ids":foreign,"expected_mask_png_count":expected_pngs,"actual_mask_png_count":mask_pngs,"drawing_path_rows":len(drawing_rows),"unassigned_visible_path_count":sum(r["classification"]=="UNASSIGNED_VISIBLE_PATH" for r in drawing_rows),"glyph_contact_sheet_paths":glyph_sheets,"graphic_contact_sheet_paths":graphic_sheets,"critical_contact_sheet_paths":critical_sheets,"pair_matrix_path":matrix_path,"relationship_overlay_path":relation_overlay,"r168_font_advisory_count":sum(o["r168_size_advisory"] for o in glyph_objects),"manual_fields_generated_by_script":False,"manual_review_state":"NOT_WRITTEN_BY_MACHINE"
    }
    (MACHINE/"machine_crosscheck.json").write_text(json.dumps(cross,ensure_ascii=False,indent=2),encoding="utf-8")
    (MACHINE/"MACHINE_RESULT.txt").write_text(("MACHINE_HARD_GATES=PASS\n" if hard_pass else "MACHINE_HARD_GATES=FAIL\n")+json.dumps(cross,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"metadata":metadata,"crosscheck":cross},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
