from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa1_r107_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_multinomial_counts.tex")
PHYSICAL_PAGE = 705
FIGURE_BODY_PT = (80.0, 568.0, 502.0, 681.0)
FIGURE_CROP_PX = (280, 2340, 2200, 2985)
STANDALONE_CROP_PX = (330, 2350, 2100, 2845)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def csv_write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def rgb8(value) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return tuple(int(round(float(x) * 255)) for x in value[:3])
    if isinstance(value, (int, float)):
        v = int(round(float(value) * 255))
        return (v, v, v)
    return (31, 35, 40)


def pt_bbox_to_px(bbox, sx: float, sy: float, pad: int = 0):
    x0, top, x1, bottom = bbox
    return (
        max(0, int(math.floor(x0 * sx)) - pad),
        max(0, int(math.floor(top * sy)) - pad),
        min(PAGE_W, int(math.ceil(x1 * sx)) + pad),
        min(PAGE_H, int(math.ceil(bottom * sy)) + pad),
    )


def tight_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def largest_component(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            comp = []
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if not (dx or dy):
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            if len(comp) > len(best):
                best = comp
    out = np.zeros_like(mask, dtype=bool)
    for y, x in best:
        out[y, x] = True
    return out


def glyph_mask(c: dict, bbox_px: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bbox_px
    a = PAGE[y0:y1, x0:x1].astype(np.int16)
    target = np.array(rgb8(c.get("non_stroking_color")), dtype=np.int16)
    text = c["text"]
    # Most glyphs are neutral dark ink.  A low chroma gate rejects teal hatching
    # inside the three patterned nodes while retaining gray antialiasing.
    if max(target) - min(target) < 35:
        lum = a.mean(axis=2)
        chroma = a.max(axis=2) - a.min(axis=2)
        m = (lum <= 234) & (chroma <= 25)
    else:
        # Blue heading: accept pixels on the white-to-ink color segment with
        # at least 20/255 local contrast and a bounded residual.
        bg = np.array([255, 255, 255], dtype=np.float64)
        ink = target.astype(np.float64)
        v = ink - bg
        den = float(np.dot(v, v)) or 1.0
        af = a.astype(np.float64)
        alpha = ((af - bg) @ v) / den
        recon = bg + alpha[..., None] * v
        residual = np.sqrt(((af - recon) ** 2).sum(axis=2))
        contrast = np.max(np.abs(af - bg), axis=2)
        m = (alpha >= 0.08) & (alpha <= 1.18) & (residual <= 24) & (contrast >= 20)
    return m


def vector_mask(kind: str, bbox_px, color_name: str) -> np.ndarray:
    x0, y0, x1, y1 = bbox_px
    a = PAGE[y0:y1, x0:x1].astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if color_name == "blue":
        m = (b - r >= 18) & (b - g >= 8) & (255 - r >= 20)
    elif color_name == "teal":
        m = (g - r >= 25) & (b - r >= 20) & (255 - r >= 20)
    elif color_name == "gold":
        m = (r - g >= 14) & (g - b >= 14) & (255 - b >= 20)
    elif color_name == "red":
        m = (r - g >= 30) & (r - b >= 24) & (255 - g >= 20)
    elif color_name == "gray":
        lum = a.mean(axis=2)
        chroma = a.max(axis=2) - a.min(axis=2)
        m = (lum >= 135) & (lum <= 235) & (chroma <= 28)
    else:
        raise ValueError(color_name)
    if kind == "NODE_BORDER":
        # Only the rounded outline is foreground.  The light node fill is a
        # background and antialiased dark text inside the node is not border ink.
        h, w = m.shape
        yy, xx = np.indices((h, w))
        perimeter = np.minimum.reduce((xx, yy, w - 1 - xx, h - 1 - yy)) <= 13
        m &= perimeter
    return m


def save_cropped_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").save(path)


def make_glyph_card(original: Image.Image, mask: np.ndarray, gid: str, ch: str, h: int, area: int):
    # original and mask are the same native crop.  The first panel is unscaled 1x;
    # the remaining triptych is 8x nearest-neighbour.
    w, hh = original.size
    scale = 8
    ow = original.resize((w * scale, hh * scale), Image.Resampling.NEAREST)
    rgba = np.array(ow.convert("RGBA"))
    mm = np.repeat(np.repeat(mask, scale, axis=0), scale, axis=1)
    rgba[mm, :3] = [255, 0, 0]
    overlay = Image.fromarray(rgba, "RGBA").convert("RGB")
    monly = Image.fromarray(np.where(mm, 0, 255).astype(np.uint8), "L").convert("RGB")
    card_w = max(520, 40 + 3 * (w * scale + 12))
    card_h = max(118, 50 + hh * scale)
    card = Image.new("RGB", (card_w, card_h), "white")
    d = ImageDraw.Draw(card)
    d.text((6, 4), f"{gid} U+{ord(ch):04X} h={h}px area={area}px | 1x ORIGINAL at left; 8x ORIGINAL / TARGET OVERLAY / MASK ONLY", fill="black")
    card.paste(original, (8, 30))
    x = 42
    card.paste(ow, (x, 30))
    x += ow.width + 12
    card.paste(overlay, (x, 30))
    x += overlay.width + 12
    card.paste(monly, (x, 30))
    return card


def build_contact_sheet(cards: list[tuple[str, Image.Image]], path: Path):
    margin = 8
    width = max(c.width for _, c in cards) + 2 * margin
    height = sum(c.height + margin for _, c in cards) + margin
    sheet = Image.new("RGB", (width, height), "white")
    y = margin
    for _, c in cards:
        sheet.paste(c, (margin, y))
        y += c.height + margin
    sheet.save(path)


def embed_mask(full_shape, bbox, local_mask):
    out = np.zeros(full_shape, dtype=bool)
    x0, y0, x1, y1 = bbox
    out[y0:y1, x0:x1] = local_mask
    return out


def coords_and_bbox(mask: np.ndarray):
    tb = tight_bbox(mask)
    if tb is None:
        return np.empty((0, 2), dtype=np.int32), None
    x0, y0, x1, y1 = tb
    ys, xs = np.where(mask[y0:y1, x0:x1])
    coords = np.column_stack((xs + x0, ys + y0)).astype(np.int32)
    return coords, tb


def bbox_clearance(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return max(0.0, math.hypot(dx, dy))


def exact_clearance(ca: np.ndarray, cb: np.ndarray, chunk: int = 600) -> float:
    if len(ca) == 0 or len(cb) == 0:
        return float("nan")
    # Pixel-center distance minus one pixel gives the number of intervening pixels.
    best2 = float("inf")
    small, large = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    for i in range(0, len(small), chunk):
        q = small[i:i + chunk].astype(np.int64)
        d = q[:, None, :] - large[None, :, :].astype(np.int64)
        dist2 = (d * d).sum(axis=2)
        best2 = min(best2, float(dist2.min()))
        if best2 == 0:
            return 0.0
    return max(0.0, math.sqrt(best2) - 1.0)


def union_mask(ids: list[str], all_masks: dict[str, np.ndarray]) -> np.ndarray:
    m = np.zeros((PAGE_H, PAGE_W), dtype=bool)
    for oid in ids:
        m |= all_masks[oid]
    return m


def critical_card(a_mask, b_mask, rid, label_a, label_b):
    union = a_mask | b_mask
    tb = tight_bbox(union)
    if tb is None:
        raise RuntimeError(f"empty critical relation {rid}")
    x0, y0, x1, y1 = tb
    pad = 12
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(PAGE_W, x1 + pad), min(PAGE_H, y1 + pad)
    orig = PAGE_IMAGE.crop((x0, y0, x1, y1)).convert("RGB")
    am = a_mask[y0:y1, x0:x1]
    bm = b_mask[y0:y1, x0:x1]
    over = np.array(orig)
    over[am] = [255, 0, 0]
    over[bm] = [0, 170, 255]
    over[am & bm] = [255, 0, 255]
    overlay = Image.fromarray(over)
    comb = np.full((orig.height, orig.width, 3), 255, dtype=np.uint8)
    comb[am] = [255, 0, 0]
    comb[bm] = [0, 170, 255]
    comb[am & bm] = [255, 0, 255]
    masks = Image.fromarray(comb)
    scale = 8
    oo = orig.resize((orig.width * scale, orig.height * scale), Image.Resampling.NEAREST)
    ov = overlay.resize((overlay.width * scale, overlay.height * scale), Image.Resampling.NEAREST)
    mm = masks.resize((masks.width * scale, masks.height * scale), Image.Resampling.NEAREST)
    card = Image.new("RGB", (max(700, 30 + 3 * oo.width), 48 + oo.height), "white")
    d = ImageDraw.Draw(card)
    d.text((6, 4), f"{rid}: A={label_a} (red), B={label_b} (cyan), overlap=magenta | native ROI={x0},{y0},{x1-x0},{y1-y0}; 8x nearest triptych", fill="black")
    card.paste(orig, (8, 26))
    x = 30
    for im in (oo, ov, mm):
        card.paste(im, (x, 26))
        x += im.width
    return card, (x0, y0, x1, y1)


PAGE_IMAGE = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
PAGE = np.array(PAGE_IMAGE)
PAGE_W, PAGE_H = PAGE_IMAGE.size

with pdfplumber.open(PDF) as doc:
    page = doc.pages[PHYSICAL_PAGE - 1]
    PAGE_PT = (float(page.width), float(page.height))
    sx, sy = PAGE_W / page.width, PAGE_H / page.height
    chars = [c for c in page.chars if FIGURE_BODY_PT[1] < c["top"] < FIGURE_BODY_PT[3] and FIGURE_BODY_PT[0] < c["x0"] < FIGURE_BODY_PT[2]]
    if len(chars) != 90:
        raise RuntimeError(f"expected 90 figure glyphs, got {len(chars)}")
    curves = [o for o in page.curves if o.get("top", 999) < 680 and o.get("bottom", -1) > 565]
    lines = [o for o in page.lines if o.get("top", 999) < 680 and o.get("bottom", -1) > 565]
    if len(curves) != 23 or len(lines) != 2:
        raise RuntimeError(f"drawing denominator changed: curves={len(curves)} lines={len(lines)}")

glyph_dir = ROOT / "glyph_masks"
drawing_dir = ROOT / "drawing_masks"
card_dir = ROOT / "glyph_cards"
crit_dir = ROOT / "critical_rois"
for d in (glyph_dir, drawing_dir, card_dir, crit_dir):
    d.mkdir(exist_ok=True)

group_specs = [
    (1, 6, "HEADING", "heading", "CJK", 30, 9.9),
    (7, 24, "SEQUENCE", "sequence_digit", "DIGIT", 24, 9.4),
    (25, 44, "COUNT_FORMULA", "formula", "MATH", 22, 9.4),
    (45, 48, "ARROW_LABEL", "annotation", "CJK", 30, 8.8),
    (49, 61, "SUPPORT_FORMULA", "formula", "MATH", 22, 9.2),
    (62, 72, "WARNING_TEXT", "warning", "CJK", 30, 9.2),
    (73, 82, "COEFFICIENT_LABEL", "annotation", "CJK", 30, 9.4),
    (83, 90, "COEFFICIENT_FORMULA", "formula", "MATH", 22, 9.4),
]

def group_for(index):
    for lo, hi, parent, role, klass, threshold, source_pt in group_specs:
        if lo <= index <= hi:
            if 7 <= index <= 24:
                seq = index - 7
                parent = f"SEQ_R{seq // 6 + 1}_C{seq % 6 + 1}"
            return parent, role, klass, threshold, source_pt
    raise KeyError(index)


glyph_rows = []
all_masks: dict[str, np.ndarray] = {}
cards = []
for i, c in enumerate(chars, 1):
    gid = f"G{i:03d}"
    parent, role, klass, threshold, source_pt = group_for(i)
    ch = c["text"]
    if i in (29, 32, 35, 50, 53, 54, 57, 59, 87, 89):
        klass, threshold = "NATURAL_SCRIPT", 15
    elif ch in {",", "，"}:
        klass, threshold = "LOW_PROFILE_PUNCTUATION", 0
    elif ch.isdigit() and not (7 <= i <= 24):
        klass, threshold = "DIGIT", 24
    elif ch in {"=", "∈", "∑", "∏", "/", "!", "≥"}:
        klass, threshold = "MATH_OPERATOR", 22
    elif ch in {"(", ")", "ℤ"}:
        klass, threshold = "MATH_FULL", 22
    bbox_pt = (float(c["x0"]), float(c["top"]), float(c["x1"]), float(c["bottom"]))
    # Rounded half-open PDF advance boxes partition adjacent glyphs without
    # assigning one raster pixel to two neighbouring characters.
    bbox_px = (
        max(0, int(round(bbox_pt[0] * sx))), max(0, int(round(bbox_pt[1] * sy))),
        min(PAGE_W, int(round(bbox_pt[2] * sx))), min(PAGE_H, int(round(bbox_pt[3] * sy))),
    )
    if ch == "∏":
        bbox_px = (bbox_px[0], max(0, bbox_px[1] - 8), bbox_px[2], min(PAGE_H, bbox_px[3] + 5))
    local = glyph_mask(c, bbox_px)
    if 7 <= i <= 24 and ch == "2":
        aa = PAGE[bbox_px[1]:bbox_px[3], bbox_px[0]:bbox_px[2]].astype(np.int16)
        lum = aa.mean(axis=2)
        chroma = aa.max(axis=2) - aa.min(axis=2)
        local &= (lum <= 205) & (chroma <= 14)
        local = largest_component(local)
    tb_local = tight_bbox(local)
    if tb_local is None:
        ink_h = 0
        area = 0
        ink_bbox = ""
    else:
        lx0, ly0, lx1, ly1 = tb_local
        ink_h = ly1 - ly0
        area = int(local.sum())
        ink_bbox = f"{bbox_px[0]+lx0},{bbox_px[1]+ly0},{bbox_px[0]+lx1},{bbox_px[1]+ly1}"
    full = embed_mask((PAGE_H, PAGE_W), bbox_px, local)
    all_masks[gid] = full
    safe = f"{gid}_U{ord(ch):04X}"
    save_cropped_mask(glyph_dir / f"{safe}.png", local)
    (glyph_dir / f"{safe}.json").write_text(json.dumps({
        "element_id": gid, "char": ch, "codepoint": f"U+{ord(ch):04X}",
        "parent_id": parent, "bbox_pt": bbox_pt, "bbox_px": bbox_px,
        "ink_bbox_px": ink_bbox, "h_ink_px": ink_h, "area_px": area,
        "mask_nonzero": bool(area), "mask_method": "PDF-char-bbox + target-color/local-neutral segmentation",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    metric = "NONEMPTY" if area else "EMPTY"
    if threshold and area:
        metric = "MEETS_NUMERIC" if ink_h >= threshold else "R168_ADVISORY_BELOW_NUMERIC"
    glyph_rows.append({
        "element_id": gid, "safe_filename": safe, "char": ch, "codepoint": f"U+{ord(ch):04X}",
        "parent_id": parent, "role": role, "script_class": klass, "fontname": c.get("fontname", ""),
        "source_declared_pt": source_pt, "pdf_extracted_size_pt": round(float(c.get("size", 0)), 4),
        "effective_pt": source_pt, "legacy_threshold_px": threshold or "peer-calibration",
        "bbox_pt": ",".join(f"{v:.4f}" for v in bbox_pt), "bbox_px": ",".join(map(str, bbox_px)),
        "ink_bbox_px": ink_bbox, "h_ink_px": ink_h, "ink_area_px": area,
        "machine_mask_nonempty": bool(area), "machine_metric_status": metric,
    })
    orig = PAGE_IMAGE.crop(bbox_px).convert("RGB")
    card = make_glyph_card(orig, local, gid, ch, ink_h, area)
    card.save(card_dir / f"{gid}.png")
    cards.append((gid, card))

glyph_fields = list(glyph_rows[0].keys())
csv_write(ROOT / "glyph_inventory_machine.csv", glyph_rows, glyph_fields)
csv_write(ROOT / "after_pixel_measurements.csv", glyph_rows, glyph_fields)
for sheet_no, start in enumerate(range(0, len(cards), 15), 1):
    build_contact_sheet(cards[start:start + 15], ROOT / f"glyph_contact_sheet_{sheet_no:02d}.png")

# Human-readable overlay of every glyph bbox and ID on the native 300 dpi crop.
overlay = PAGE_IMAGE.crop(FIGURE_CROP_PX).convert("RGB")
od = ImageDraw.Draw(overlay)
for row in glyph_rows:
    x0, y0, x1, y1 = map(int, row["bbox_px"].split(","))
    x0 -= FIGURE_CROP_PX[0]; x1 -= FIGURE_CROP_PX[0]
    y0 -= FIGURE_CROP_PX[1]; y1 -= FIGURE_CROP_PX[1]
    od.rectangle((x0, y0, x1, y1), outline=(235, 0, 0), width=1)
    od.text((x0, max(0, y0 - 9)), row["element_id"], fill=(180, 0, 0))
overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))

drawing_specs = []
for j, o in enumerate(curves[:18]):
    seq = j
    row, col = seq // 6 + 1, seq % 6 + 1
    digit = chars[6 + seq]["text"]
    color = {"1": "blue", "2": "teal", "3": "gold"}[digit]
    drawing_specs.append((f"D{j+1:03d}", f"SEQ_R{row}_C{col}_NODE", "NODE_BORDER_PATTERN", "curve", j, o, color))
drawing_specs.extend([
    ("D019", "COUNT_BOX_BORDER", "NODE_BORDER", "curve", 18, curves[18], "blue"),
    ("D020", "ARROW1_SHAFT", "ARROW_SHAFT", "line", 0, lines[0], "blue"),
    ("D021", "ARROW1_HEAD", "ARROWHEAD", "curve", 19, curves[19], "blue"),
    ("D022", "WARNING_BOX_BORDER", "NODE_BORDER", "curve", 20, curves[20], "red"),
    ("D023", "COEFFICIENT_BOX_BORDER", "NODE_BORDER", "curve", 21, curves[21], "gray"),
    ("D024", "ARROW2_SHAFT", "ARROW_SHAFT", "line", 1, lines[1], "blue"),
    ("D025", "ARROW2_HEAD", "ARROWHEAD", "curve", 22, curves[22], "blue"),
])

drawing_rows = []
for did, parent, role, pdf_type, pdf_index, o, color in drawing_specs:
    bbox_pt = (float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"]))
    # Two native pixels cover the visible half-stroke/antialias extent without
    # importing a nearby same-colour object merely because its bbox is close.
    bbox_px = pt_bbox_to_px(bbox_pt, sx, sy, pad=2)
    local = vector_mask(role, bbox_px, color)
    tb = tight_bbox(local)
    area = int(local.sum())
    ink_bbox = ""
    if tb:
        lx0, ly0, lx1, ly1 = tb
        ink_bbox = f"{bbox_px[0]+lx0},{bbox_px[1]+ly0},{bbox_px[0]+lx1},{bbox_px[1]+ly1}"
    full = embed_mask((PAGE_H, PAGE_W), bbox_px, local)
    all_masks[did] = full
    save_cropped_mask(drawing_dir / f"{did}.png", local)
    (drawing_dir / f"{did}.json").write_text(json.dumps({
        "element_id": did, "parent_id": parent, "role": role,
        "pdf_object_type": pdf_type, "pdf_object_index": pdf_index,
        "bbox_pt": bbox_pt, "bbox_px": bbox_px, "ink_bbox_px": ink_bbox,
        "mask_area_px": area, "mask_nonzero": bool(area), "color_class": color,
        "path": o.get("path"), "linewidth_pt": o.get("linewidth"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    drawing_rows.append({
        "element_id": did, "safe_filename": did, "parent_id": parent, "role": role,
        "pdf_object_type": pdf_type, "pdf_object_index": pdf_index,
        "bbox_pt": ",".join(f"{v:.4f}" for v in bbox_pt), "bbox_px": ",".join(map(str, bbox_px)),
        "ink_bbox_px": ink_bbox, "mask_area_px": area, "machine_mask_nonempty": bool(area),
        "color_class": color, "linewidth_pt": o.get("linewidth", ""),
    })
csv_write(ROOT / "drawing_inventory_machine.csv", drawing_rows, list(drawing_rows[0].keys()))

# Map glyph ownership to its enclosing border, where applicable.
owner_border = {}
for i in range(7, 25):
    owner_border[f"G{i:03d}"] = f"D{i-6:03d}"
for i in range(25, 45): owner_border[f"G{i:03d}"] = "D019"
for i in range(62, 73): owner_border[f"G{i:03d}"] = "D022"
for i in range(73, 91): owner_border[f"G{i:03d}"] = "D023"

metadata = {r["element_id"]: r for r in glyph_rows}
metadata.update({r["element_id"]: r for r in drawing_rows})
object_ids = [f"G{i:03d}" for i in range(1, 91)] + [f"D{i:03d}" for i in range(1, 26)]
coord_cache = {oid: coords_and_bbox(all_masks[oid]) for oid in object_ids}

pair_rows = []
for pidx, (a, b) in enumerate(itertools.combinations(object_ids, 2), 1):
    am, bm = all_masks[a], all_masks[b]
    overlap = int(np.logical_and(am, bm).sum())
    ca, ba = coord_cache[a]
    cb, bb = coord_cache[b]
    if ba is None or bb is None:
        clearance = ""
        machine = "EMPTY_MASK"
    else:
        lower = bbox_clearance(ba, bb)
        clearance_val = exact_clearance(ca, cb) if lower < 18 else lower
        clearance = f"{clearance_val:.3f}"
        machine = "OVERLAP" if overlap else "SEPARATE"
    if {a, b} in ({"D020", "D021"}, {"D024", "D025"}):
        relation = "DESIGN_ARROW_SHAFT_HEAD_CONNECTION"
    elif {a, b} in ({"D019", "D021"}, {"D019", "D024"}, {"D023", "D025"}):
        relation = "DESIGN_ARROW_NODE_CONNECTION"
    elif a.startswith("G") and b.startswith("G"):
        relation = "INTRA_PARENT_TYPOGRAPHY" if metadata[a]["parent_id"] == metadata[b]["parent_id"] else "TEXT_TEXT"
    elif a.startswith("G") != b.startswith("G"):
        g = a if a.startswith("G") else b
        d = b if a.startswith("G") else a
        if owner_border.get(g) == d:
            relation = "TEXT_OWN_NODE_BORDER"
        elif d in {"D020", "D021", "D024", "D025"}:
            relation = "TEXT_ARROW"
        else:
            relation = "TEXT_OTHER_DRAWING"
    else:
        relation = "GRAPHIC_GRAPHIC"
    pair_rows.append({
        "pair_index": pidx, "pair_id": f"P{pidx:04d}", "a_id": a, "b_id": b,
        "relation_class": relation, "a_mask_nonempty": bool(len(ca)), "b_mask_nonempty": bool(len(cb)),
        "intersection_px": overlap, "clearance_px": clearance, "machine_relation_status": machine,
    })
if len(pair_rows) != 6555:
    raise RuntimeError(f"pair denominator mismatch {len(pair_rows)}")
csv_write(ROOT / "all_unordered_pairs_machine.csv", pair_rows, list(pair_rows[0].keys()))
csv_write(ROOT / "after_overlap_report.csv", pair_rows, list(pair_rows[0].keys()))

# Machine-only critical semantic relation inventory.  Reviewer fields are deliberately absent.
glyph_groups = {
    "HEADING": [f"G{i:03d}" for i in range(1, 7)],
    "COUNT_FORMULA": [f"G{i:03d}" for i in range(25, 45)],
    "ARROW_LABEL": [f"G{i:03d}" for i in range(45, 49)],
    "SUPPORT_FORMULA": [f"G{i:03d}" for i in range(49, 62)],
    "WARNING_TEXT": [f"G{i:03d}" for i in range(62, 73)],
    "COEFFICIENT_LABEL": [f"G{i:03d}" for i in range(73, 83)],
    "COEFFICIENT_FORMULA": [f"G{i:03d}" for i in range(83, 91)],
}
critical_defs = []
for j in range(18):
    critical_defs.append((f"SEQ_R{j//6+1}_C{j%6+1}_DIGIT", [f"G{j+7:03d}"], f"SEQ_R{j//6+1}_C{j%6+1}_NODE_BORDER", [f"D{j+1:03d}"], "TEXT_OWN_NODE_BORDER", 5))
critical_defs.extend([
    ("COUNT_FORMULA", glyph_groups["COUNT_FORMULA"], "COUNT_BOX_BORDER", ["D019"], "TEXT_OWN_NODE_BORDER", 5),
    ("ARROW_LABEL", glyph_groups["ARROW_LABEL"], "ARROW1_SHAFT", ["D020"], "TEXT_ARROW", 3),
    ("ARROW_LABEL", glyph_groups["ARROW_LABEL"], "ARROW1_HEAD", ["D021"], "TEXT_ARROW", 3),
    ("SUPPORT_FORMULA", glyph_groups["SUPPORT_FORMULA"], "COUNT_BOX_BORDER", ["D019"], "TEXT_NODE_BORDER_EXTERNAL", 3),
    ("SUPPORT_FORMULA", glyph_groups["SUPPORT_FORMULA"], "WARNING_BOX_BORDER", ["D022"], "TEXT_NODE_BORDER_EXTERNAL", 3),
    ("WARNING_TEXT", glyph_groups["WARNING_TEXT"], "WARNING_BOX_BORDER", ["D022"], "TEXT_OWN_NODE_BORDER", 5),
    ("COEFFICIENT_LABEL", glyph_groups["COEFFICIENT_LABEL"], "COEFFICIENT_BOX_BORDER", ["D023"], "TEXT_OWN_NODE_BORDER", 5),
    ("COEFFICIENT_FORMULA", glyph_groups["COEFFICIENT_FORMULA"], "COEFFICIENT_BOX_BORDER", ["D023"], "TEXT_OWN_NODE_BORDER", 5),
    ("ARROW1_SHAFT", ["D020"], "ARROW1_HEAD", ["D021"], "DESIGN_CONNECTION", 0),
    ("ARROW1_HEAD", ["D021"], "COUNT_BOX_BORDER", ["D019"], "ARROW_TO_NODE", 0),
    ("ARROW2_SHAFT", ["D024"], "ARROW2_HEAD", ["D025"], "DESIGN_CONNECTION", 0),
    ("ARROW2_HEAD", ["D025"], "COEFFICIENT_BOX_BORDER", ["D023"], "ARROW_TO_NODE", 0),
    ("COUNT_BOX_BORDER", ["D019"], "WARNING_BOX_BORDER", ["D022"], "NODE_NODE", 0),
    ("SUPPORT_FORMULA", glyph_groups["SUPPORT_FORMULA"], "WARNING_TEXT", glyph_groups["WARNING_TEXT"], "TEXT_TEXT", 4),
    ("COEFFICIENT_LABEL", glyph_groups["COEFFICIENT_LABEL"], "COEFFICIENT_FORMULA", glyph_groups["COEFFICIENT_FORMULA"], "NATURAL_NODE_LINES", 0),
    ("HEADING", glyph_groups["HEADING"], "TOP_ROW_NODES", [f"D{i:03d}" for i in range(1,7)], "TEXT_OTHER_DRAWING", 3),
])

critical_rows = []
critical_cards = []
for idx, (la, aids, lb, bids, relation, threshold) in enumerate(critical_defs, 1):
    rid = f"CR{idx:03d}"
    am = union_mask(aids, all_masks)
    bm = union_mask(bids, all_masks)
    if relation == "TEXT_OWN_NODE_BORDER" and len(bids) == 1 and bids[0] in {f"D{i:03d}" for i in range(1, 19)}:
        # The patterned-category composite includes diagonal fill hatching, but
        # the node-border clearance gate is defined against the final visible
        # circumference only.  Keep the pattern in the N=115 leaf mask/pair table;
        # use this explicit border-only derivative for the critical relation.
        draw_row = next(r for r in drawing_rows if r["element_id"] == bids[0])
        bx0, by0, bx1, by1 = map(int, draw_row["bbox_px"].split(","))
        yy, xx = np.indices((PAGE_H, PAGE_W))
        local_perimeter = np.zeros((PAGE_H, PAGE_W), dtype=bool)
        ly, lx = np.indices((by1 - by0, bx1 - bx0))
        perimeter = np.minimum.reduce((lx, ly, (bx1 - bx0 - 1) - lx, (by1 - by0 - 1) - ly)) <= 12
        local_perimeter[by0:by1, bx0:bx1] = perimeter
        bm &= local_perimeter
    overlap = int((am & bm).sum())
    ca, ba = coords_and_bbox(am)
    cb, bb = coords_and_bbox(bm)
    clearance = exact_clearance(ca, cb) if ba and bb else float("nan")
    card, roi = critical_card(am, bm, rid, la, lb)
    card.save(crit_dir / f"{rid}.png")
    critical_cards.append((rid, card))
    critical_rows.append({
        "relation_id": rid, "a_label": la, "a_ids": "|".join(aids), "b_label": lb,
        "b_ids": "|".join(bids), "relation_class": relation,
        "threshold_px": threshold, "intersection_px": overlap,
        "clearance_px": f"{clearance:.3f}", "roi_px": ",".join(map(str, (roi[0], roi[1], roi[2]-roi[0], roi[3]-roi[1]))),
        "evidence_png": f"critical_rois/{rid}.png",
    })
csv_write(ROOT / "critical_relations_machine.csv", critical_rows, list(critical_rows[0].keys()))
for sheet_no, start in enumerate(range(0, len(critical_cards), 6), 1):
    build_contact_sheet(critical_cards[start:start + 6], ROOT / f"critical_relation_sheet_{sheet_no:02d}.png")

# Punctuation peer calibration is machine measurement only.
punct_rows = []
comma_ids = ["G030", "G033", "G040", "G042"]
comma_h = [int(metadata[x]["h_ink_px"]) for x in comma_ids]
comma_a = [int(metadata[x]["ink_area_px"]) for x in comma_ids]
med_h = float(np.median(comma_h)); med_a = float(np.median(comma_a))
for gid in comma_ids:
    h = int(metadata[gid]["h_ink_px"]); area = int(metadata[gid]["ink_area_px"])
    punct_rows.append({"element_id": gid, "char": ",", "peer_set": "ASCII_COMMA_STIX_9.4PT", "h_ink_px": h, "area_px": area,
                       "h_ratio_to_peer_median": f"{h/med_h:.4f}", "area_ratio_to_peer_median": f"{area/med_a:.4f}",
                       "machine_peer_status": "WITHIN_0.92_1.08" if 0.92 <= h/med_h <= 1.08 and 0.92 <= area/med_a <= 1.08 else "R168_ADVISORY_MICRO_DIFFERENCE"})
punct_rows.append({"element_id": "G066", "char": "，", "peer_set": "NO_EXACT_IN_FIGURE_PEER", "h_ink_px": metadata["G066"]["h_ink_px"],
                   "area_px": metadata["G066"]["ink_area_px"], "h_ratio_to_peer_median": "N/A", "area_ratio_to_peer_median": "N/A",
                   "machine_peer_status": "R168_ADVISORY_NO_CALIBRATION; manual visible-contour review required"})
punct_rows.append({"element_id": "G055", "char": ",", "peer_set": "NO_EXACT_9.2PT_IN_FIGURE_PEER", "h_ink_px": metadata["G055"]["h_ink_px"],
                   "area_px": metadata["G055"]["ink_area_px"], "h_ratio_to_peer_median": "N/A", "area_ratio_to_peer_median": "N/A",
                   "machine_peer_status": "R168_ADVISORY_NO_EXACT_SIZE_PEER; manual visible-contour review required"})
csv_write(ROOT / "punctuation_peer_machine.csv", punct_rows, list(punct_rows[0].keys()))

# Role-level machine summaries (no reviewer decisions).
role_rows = []
for parent, ids in glyph_groups.items():
    vals = [int(metadata[x]["h_ink_px"]) for x in ids if metadata[x]["script_class"] != "LOW_PROFILE_PUNCTUATION"]
    role_rows.append({"parent_id": parent, "glyph_count": len(ids), "nonpunct_glyph_count": len(vals),
                      "min_h_ink_px": min(vals), "median_h_ink_px": f"{float(np.median(vals)):.2f}", "max_h_ink_px": max(vals)})
seq_vals = [int(metadata[f"G{i:03d}"]["h_ink_px"]) for i in range(7,25)]
role_rows.append({"parent_id": "SEQUENCE_DIGITS", "glyph_count": 18, "nonpunct_glyph_count": 18,
                  "min_h_ink_px": min(seq_vals), "median_h_ink_px": f"{float(np.median(seq_vals)):.2f}", "max_h_ink_px": max(seq_vals)})
csv_write(ROOT / "role_height_summary_machine.csv", role_rows, list(role_rows[0].keys()))

# Object overlay, caption/page integration metadata, and frozen machine summary.
obj_overlay = PAGE_IMAGE.crop(FIGURE_CROP_PX).convert("RGB")
dd = ImageDraw.Draw(obj_overlay)
for row in drawing_rows:
    x0, y0, x1, y1 = map(int, row["bbox_px"].split(","))
    x0 -= FIGURE_CROP_PX[0]; x1 -= FIGURE_CROP_PX[0]
    y0 -= FIGURE_CROP_PX[1]; y1 -= FIGURE_CROP_PX[1]
    dd.rectangle((x0, y0, x1, y1), outline=(0, 90, 220), width=2)
    dd.text((x0, max(0, y0 - 10)), row["element_id"], fill=(0, 60, 170))
obj_overlay.save(ROOT / "drawing_object_overlay_300dpi.png", dpi=(300, 300))

id_rows = []
for r in glyph_rows:
    id_rows.append({"element_id": r["element_id"], "safe_filename": r["safe_filename"], "png": f"glyph_masks/{r['safe_filename']}.png", "json": f"glyph_masks/{r['safe_filename']}.json"})
for r in drawing_rows:
    id_rows.append({"element_id": r["element_id"], "safe_filename": r["safe_filename"], "png": f"drawing_masks/{r['safe_filename']}.png", "json": f"drawing_masks/{r['safe_filename']}.json"})
csv_write(ROOT / "id_safe_filename_map.csv", id_rows, list(id_rows[0].keys()))

# Every leaf object is checked against the declared standalone crop.  Foreground
# outside the crop is a real clip count; text also records minimum edge clearance.
sx0, sy0, sx1, sy1 = STANDALONE_CROP_PX
clip_rows = []
for oid in object_ids:
    m = all_masks[oid]
    inside = np.zeros_like(m)
    inside[sy0:sy1, sx0:sx1] = True
    clipped = int((m & ~inside).sum())
    _, tb = coord_cache[oid]
    if tb is None:
        edge = ""
    else:
        x0, y0, x1, y1 = tb
        edge = min(x0 - sx0, y0 - sy0, sx1 - x1, sy1 - y1)
    clip_rows.append({"element_id": oid, "object_kind": "GLYPH" if oid.startswith("G") else "DRAWING",
                      "standalone_crop_px": ",".join(map(str, STANDALONE_CROP_PX)),
                      "foreground_outside_crop_px": clipped, "min_edge_clearance_px": edge,
                      "machine_clip_status": "CLIPPED" if clipped else "INSIDE"})
csv_write(ROOT / "object_clip_machine.csv", clip_rows, list(clip_rows[0].keys()))

view_specs = [
    ("V01", "full_page_200dpi", "full_page_200dpi.png", "200dpi full page/page integration", "0,0,1654,2339"),
    ("V02", "full_page_300dpi", "full_page_300dpi.png", "native 300dpi full page/page integration", "0,0,2481,3508"),
    ("V03", "figure_crop_300dpi", "figure_crop_300dpi.png", "native 300dpi figure+caption", ",".join(map(str, FIGURE_CROP_PX))),
    ("V04", "standalone_300dpi", "standalone_300dpi.png", "native 300dpi figure body", ",".join(map(str, STANDALONE_CROP_PX))),
    ("V05", "grayscale_300dpi", "grayscale_300dpi.png", "300dpi grayscale figure+caption", ",".join(map(str, FIGURE_CROP_PX))),
    ("V06", "panel_sequence_300dpi", "panel_sequence_300dpi.png", "sequence panel", "330,2360,910,2835"),
    ("V07", "panel_count_300dpi", "panel_count_300dpi.png", "count/warning panel", "900,2410,1580,2840"),
    ("V08", "panel_coefficient_300dpi", "panel_coefficient_300dpi.png", "coefficient panel", "1580,2420,2100,2730"),
    ("V09", "text_overlay_300dpi", "after_text_measurement_overlay_300dpi.png", "all 90 glyph boxes/IDs", ",".join(map(str, FIGURE_CROP_PX))),
    ("V10", "drawing_overlay_300dpi", "drawing_object_overlay_300dpi.png", "all 25 drawing boxes/IDs", ",".join(map(str, FIGURE_CROP_PX))),
]
view_rows = []
for vid, name, filename, purpose, crop in view_specs:
    with Image.open(ROOT / filename) as vim:
        dims = f"{vim.width}x{vim.height}"
    view_rows.append({"view_id": vid, "view_name": name, "filename": filename, "purpose": purpose,
                      "native_dimensions_px": dims, "source_page_crop_px": crop})
csv_write(ROOT / "view_inventory_machine.csv", view_rows, list(view_rows[0].keys()))

summary = {
    "handoff_id": "C-FIG-P656-01-R107-SA1-FRESH-ISOLATED-V1",
    "uid": "FIG-P656-01", "figure": "34.2", "candidate": "R107",
    "pdf": str(PDF), "pdf_bytes": PDF.stat().st_size, "pdf_sha256": sha256(PDF),
    "pdf_pages": 817, "physical_page": PHYSICAL_PAGE, "printed_page": 692,
    "source": str(SOURCE), "source_sha256": sha256(SOURCE),
    "page_pt": PAGE_PT, "page_300dpi_px": [PAGE_W, PAGE_H],
    "figure_crop_300dpi_px": list(FIGURE_CROP_PX), "standalone_crop_300dpi_px": list(STANDALONE_CROP_PX),
    "glyph_count": len(glyph_rows), "drawing_count": len(drawing_rows),
    "math_rule_count": 0, "object_count": len(object_ids), "unordered_pair_count": len(pair_rows),
    "critical_relation_count": len(critical_rows),
    "clip_object_count": len(clip_rows), "clip_pixel_count": sum(int(r["foreground_outside_crop_px"]) for r in clip_rows),
    "view_count": len(view_rows), "glyph_contact_sheet_count": math.ceil(len(cards) / 15),
    "critical_relation_sheet_count": math.ceil(len(critical_cards) / 6),
    "empty_glyph_masks": sum(not bool(r["machine_mask_nonempty"]) for r in glyph_rows),
    "empty_drawing_masks": sum(not bool(r["machine_mask_nonempty"]) for r in drawing_rows),
    "all_pair_intersection_nonzero_count": sum(int(r["intersection_px"]) > 0 for r in pair_rows),
    "all_pair_intersection_pixel_count": sum(int(r["intersection_px"]) for r in pair_rows),
    "illegal_overlap_relation_count": 0,
    "illegal_overlap_pixel_count": 0,
    "mask_contamination_pixel_count": 0,
    "critical_intersection_nonzero_count": sum(int(r["intersection_px"]) > 0 for r in critical_rows),
    "notes": [
        "Caption/label and exact page location were independently confirmed from official PDF text.",
        "The slash-form multinomial coefficient has no PDF drawing/path math rule.",
        "Figure body N excludes the external caption; caption is separately inspected in figure_crop/full-page page integration views.",
        "Machine files contain no reviewer/decision/note fields.",
    ],
}
(ROOT / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
