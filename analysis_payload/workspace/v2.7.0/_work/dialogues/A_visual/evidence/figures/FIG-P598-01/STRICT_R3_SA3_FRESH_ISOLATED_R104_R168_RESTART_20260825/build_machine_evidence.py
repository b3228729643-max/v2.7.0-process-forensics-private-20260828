from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_markov_chain_path.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R3_SA3_FRESH_ISOLATED_R104_R168_RESTART_20260825")
PAGE_INDEX = 648
PAGE_PHYSICAL = 649
SCALE300 = 300.0 / 72.0
SCALE200 = 200.0 / 72.0

# Integer coordinates on the native 300 dpi whole-page raster.
FIGURE_CROP_PX = (220, 2040, 2210, 2760)
STANDALONE_CROP_PX = (390, 2040, 2010, 2620)

GRAPHIC_NAMES = {
    2: "TIME_AXIS_SHAFT",
    3: "TIME_AXIS_HEAD",
    4: "NODE_X0_BORDER",
    5: "NODE_X1_DOUBLE_OUTER",
    6: "NODE_X1_DOUBLE_SEPARATOR",
    7: "NODE_X2_DOUBLE_OUTER",
    8: "NODE_X2_DOUBLE_SEPARATOR",
    9: "NODE_X3_DOUBLE_OUTER",
    10: "NODE_X3_DOUBLE_SEPARATOR",
    11: "NODE_X4_DOUBLE_OUTER",
    12: "NODE_X4_DOUBLE_SEPARATOR",
    13: "NODE_X5_BORDER",
    14: "NODE_XT_BORDER",
    15: "TRANS_01_SHAFT",
    16: "TRANS_01_HEAD",
    17: "TRANS_12_SHAFT",
    18: "TRANS_12_HEAD",
    19: "TRANS_23_SHAFT",
    20: "TRANS_23_HEAD",
    21: "TRANS_34_SHAFT",
    22: "TRANS_34_HEAD",
    23: "TRANS_45_SHAFT",
    24: "TRANS_45_HEAD",
    25: "TRANS_5T_SHAFT",
    26: "TRANS_5T_HEAD",
    27: "REPEAT_RELATION_ARC",
}

FONT = ImageFont.load_default()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rgb_from_pdf_int(value: int) -> np.ndarray:
    return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], dtype=np.float32)


def pt_bbox_to_crop_px(bbox, crop_px):
    ax0 = math.floor(bbox[0] * SCALE300)
    ay0 = math.floor(bbox[1] * SCALE300)
    ax1 = math.ceil(bbox[2] * SCALE300)
    ay1 = math.ceil(bbox[3] * SCALE300)
    return (ax0 - crop_px[0], ay0 - crop_px[1], ax1 - crop_px[0], ay1 - crop_px[1])


def tight_bbox(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def classify_char(ch: str, parent: str, size: float) -> str:
    cp = ord(ch)
    if ch in ".,，。、；：;:…":
        return "LOW_PROFILE_PUNCTUATION"
    if ch in "0123456789T𝐾𝐼𝑋𝒳MHC":
        return "LATIN_CAPITAL_OR_DIGIT"
    if ch in "+=≥→∑∫":
        return "BASE_MATH_OPERATOR"
    if parent == "KERNEL_LABEL" and size < 7.0:
        return "NATURAL_MATH_SCRIPT"
    if (0x4E00 <= cp <= 0x9FFF) or (0x3000 <= cp <= 0x303F) or (0xFF00 <= cp <= 0xFFEF):
        return "CJK_FULLWIDTH"
    if ch.islower() or cp > 0xFFFF:
        return "LATIN_GREEK_LOWER"
    return "BASE_MATH_OR_VISIBLE"


def advisory_threshold(category: str) -> int | None:
    return {
        "CJK_FULLWIDTH": 30,
        "LATIN_CAPITAL_OR_DIGIT": 24,
        "LATIN_GREEK_LOWER": 17,
        "BASE_MATH_OPERATOR": 22,
        "BASE_MATH_OR_VISIBLE": 22,
        "NATURAL_MATH_SCRIPT": 15,
    }.get(category)


def assign_parent(ch_bbox) -> str:
    x0, y0, x1, y1 = ch_bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    if y0 >= 630:
        return "CAPTION"
    if y0 >= 615:
        return "BOTTOM_NOTE"
    if y0 >= 606 and x0 > 445:
        return "AXIS_TITLE"
    if 498 <= y0 <= 510:
        return "RELATION_ANNOTATION"
    if 511 <= y0 <= 523:
        if cx < 200:
            return "TIME_1"
        if cx < 300:
            return "TIME_2"
        return "TIME_5"
    if 529 <= y0 <= 541:
        if cx < 140:
            return "TIME_0"
        if 150 < cx < 190 and y0 > 534:
            return "STATE_1"
        if 210 < cx < 245 and y0 > 534:
            return "STATE_2"
        if 370 < cx < 405 and y0 > 534:
            return "STATE_5"
        if cx > 420:
            return "TIME_T"
    if 545 <= y0 <= 557:
        if cx < 140:
            return "STATE_0"
        if 185 < cx < 215:
            return "HOLD_12"
        if 260 < cx < 300:
            return "TIME_3"
        if 315 < cx < 350:
            return "TIME_4"
        if 370 < cx < 405:
            return "STATE_5"
        if cx > 420:
            return "STATE_T"
    if 556 <= y0 <= 575:
        if 190 < cx < 255:
            return "KERNEL_LABEL"
        if 270 < cx < 292:
            return "STATE_3"
        if 295 < cx < 320:
            return "HOLD_34"
        if 320 < cx < 350:
            return "STATE_4"
    raise RuntimeError(f"Unassigned visible character bbox: {ch_bbox}")


def glyph_mask_from_page(crop_rgb: np.ndarray, bbox_px, fg_rgb):
    h, w = crop_rgb.shape[:2]
    x0, y0, x1, y1 = bbox_px
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        return np.zeros((0, 0), dtype=bool), (x0, y0, x1, y1), np.array([255, 255, 255])
    roi = crop_rgb[y0:y1, x0:x1].astype(np.float32)
    lum = roi.mean(axis=2)
    bright = roi[lum >= np.percentile(lum, 70)]
    bg = np.median(bright, axis=0) if len(bright) else np.array([255, 255, 255], dtype=np.float32)
    direction = bg - fg_rgb
    denom = float(np.dot(direction, direction))
    if denom < 1:
        return np.zeros(roi.shape[:2], dtype=bool), (x0, y0, x1, y1), bg
    delta = bg[None, None, :] - roi
    alpha = np.sum(delta * direction[None, None, :], axis=2) / denom
    recon = bg[None, None, :] - np.clip(alpha, 0, 1)[..., None] * direction[None, None, :]
    residual = np.sqrt(np.sum((roi - recon) ** 2, axis=2))
    contrast = np.max(np.abs(delta), axis=2)
    mask = (alpha > 0.03) & (alpha < 1.25) & (residual <= 22.0) & (contrast >= 20.0)
    return mask, (x0, y0, x1, y1), bg


def reconstruct_drawing_mask(page_rect, drawing, full_dims, crop_px):
    doc = fitz.open()
    pg = doc.new_page(width=page_rect.width, height=page_rect.height)
    sh = pg.new_shape()
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
            raise RuntimeError(f"Unsupported drawing opcode: {op}")
    is_solid_fg_fill = drawing["fill"] is not None and drawing["fill"] != (1.0, 1.0, 1.0) and drawing["fill"] == drawing["color"]
    sh.finish(
        color=(0, 0, 0) if drawing["color"] is not None else None,
        fill=(0, 0, 0) if is_solid_fg_fill else None,
        width=drawing["width"],
        dashes=drawing.get("dashes"),
        closePath=drawing.get("closePath", False),
        lineJoin=drawing.get("lineJoin", 0),
    )
    sh.commit()
    pix = pg.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    if (pix.width, pix.height) != full_dims:
        raise RuntimeError((pix.width, pix.height, full_dims))
    x0, y0, x1, y1 = crop_px
    return arr[y0:y1, x0:x1] <= 235


def save_tight_mask(mask: np.ndarray, path: Path):
    bb = tight_bbox(mask)
    if bb is None:
        Image.new("L", (1, 1), 0).save(path)
        return (0, 0, 0, 0)
    x0, y0, x1, y1 = bb
    Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8), mode="L").save(path)
    return bb


def object_coords(obj):
    y, x = np.nonzero(obj["mask"])
    return np.column_stack([y, x]).astype(np.float32)


def cheb_metrics(a, b):
    ca, cb = a["coords"], b["coords"]
    if len(ca) == 0 or len(cb) == 0:
        return None, 0
    sa = {tuple(v) for v in ca.astype(np.int32)}
    sb = {tuple(v) for v in cb.astype(np.int32)}
    overlap = len(sa.intersection(sb))
    if overlap:
        return 0.0, overlap
    if len(ca) <= len(cb):
        dist, _ = b["tree"].query(ca, k=1, p=np.inf)
    else:
        dist, _ = a["tree"].query(cb, k=1, p=np.inf)
    return max(0.0, float(np.min(dist)) - 1.0), 0


def allowed_graphic_pair(name_a, name_b):
    s = {name_a, name_b}
    if s == {"TIME_AXIS_SHAFT", "TIME_AXIS_HEAD"}:
        return "INTENDED_AXIS_CONNECTION"
    for k in ("X1", "X2", "X3", "X4"):
        if s == {f"NODE_{k}_DOUBLE_OUTER", f"NODE_{k}_DOUBLE_SEPARATOR"}:
            return "INTENDED_DOUBLE_CIRCLE_COMPOSITION"
    if "REPEAT_RELATION_ARC" in s and any(
        member in s
        for member in (
            "NODE_X1_DOUBLE_OUTER", "NODE_X1_DOUBLE_SEPARATOR",
            "NODE_X2_DOUBLE_OUTER", "NODE_X2_DOUBLE_SEPARATOR",
        )
    ):
        return "INTENDED_RELATION_ARC_NODE_CONNECTION"
    transitions = [
        ("TRANS_01", "NODE_X0_BORDER", "NODE_X1_DOUBLE_OUTER"),
        ("TRANS_12", "NODE_X1_DOUBLE_OUTER", "NODE_X2_DOUBLE_OUTER"),
        ("TRANS_23", "NODE_X2_DOUBLE_OUTER", "NODE_X3_DOUBLE_OUTER"),
        ("TRANS_34", "NODE_X3_DOUBLE_OUTER", "NODE_X4_DOUBLE_OUTER"),
        ("TRANS_45", "NODE_X4_DOUBLE_OUTER", "NODE_X5_BORDER"),
        ("TRANS_5T", "NODE_X5_BORDER", "NODE_XT_BORDER"),
    ]
    for stem, src, dst in transitions:
        if s == {f"{stem}_SHAFT", f"{stem}_HEAD"}:
            return "INTENDED_ARROW_COMPOSITION"
        if s == {f"{stem}_SHAFT", src} or s == {f"{stem}_HEAD", dst}:
            return "INTENDED_NODE_ARROW_CONNECTION"
        for node in (src, dst):
            if node.endswith("DOUBLE_OUTER"):
                separator = node.replace("DOUBLE_OUTER", "DOUBLE_SEPARATOR")
                if s == {f"{stem}_SHAFT", separator} or s == {f"{stem}_HEAD", separator}:
                    return "INTENDED_NODE_ARROW_CONNECTION"
    return "NONE"


def pair_rule(a, b):
    if a["kind"] == "TEXT_GLYPH" and b["kind"] == "TEXT_GLYPH":
        if a["parent"] == b["parent"]:
            return "SAME_SEMANTIC_PARENT_INTERNAL", 0
        return "TEXT_TEXT", 4
    if a["kind"] == "GRAPHIC" and b["kind"] == "GRAPHIC":
        allowed = allowed_graphic_pair(a["name"], b["name"])
        return (allowed if allowed != "NONE" else "GRAPHIC_GRAPHIC_UNRELATED"), 0
    t = a if a["kind"] == "TEXT_GLYPH" else b
    g = b if a["kind"] == "TEXT_GLYPH" else a
    node_map = {
        "STATE_0": "NODE_X0_BORDER",
        "STATE_1": "NODE_X1_DOUBLE_OUTER",
        "STATE_2": "NODE_X2_DOUBLE_OUTER",
        "STATE_3": "NODE_X3_DOUBLE_OUTER",
        "STATE_4": "NODE_X4_DOUBLE_OUTER",
        "STATE_5": "NODE_X5_BORDER",
        "STATE_T": "NODE_XT_BORDER",
    }
    if node_map.get(t["parent"]) == g["name"]:
        return "NODE_TEXT_BORDER", 5
    return "TEXT_GRAPHIC", 3


def object_contact_cell(crop_rgb, obj, title, size=(560, 150)):
    canvas = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(canvas)
    d.text((6, 4), title, fill="black", font=FONT)
    bb = obj["bbox"]
    x0, y0, x1, y1 = bb
    pad = 4
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(crop_rgb.shape[1], x1 + pad), min(crop_rgb.shape[0], y1 + pad)
    roi = crop_rgb[ry0:ry1, rx0:rx1]
    m = obj["mask"][ry0:ry1, rx0:rx1]
    if roi.size == 0:
        return canvas
    panels = []
    original = Image.fromarray(roi)
    overlay = roi.copy()
    overlay[m] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.repeat(np.where(m[..., None], 0, 255).astype(np.uint8), 3, axis=2)
    panels.extend([original, Image.fromarray(overlay), Image.fromarray(mask_only)])
    labels = ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"]
    max_w, max_h = 165, 102
    for i, (panel, lab) in enumerate(zip(panels, labels)):
        scale = min(max_w / panel.width, max_h / panel.height)
        factor = max(1, int(math.floor(scale)))
        shown = panel.resize((panel.width * factor, panel.height * factor), Image.Resampling.NEAREST)
        px = 6 + i * 182
        py = 32
        canvas.paste(shown, (px, py))
        d.text((px, 20), lab, fill="black", font=FONT)
        d.rectangle((px - 1, py - 1, px + shown.width, py + shown.height), outline=(100, 100, 100))
    d.text((6, 136), f"native bbox={bb}; 8x/equivalent nearest only", fill="black", font=FONT)
    return canvas


def make_contact_sheets(crop_rgb, objects, prefix, per_sheet=20):
    index_rows = []
    for sheet_i in range(0, len(objects), per_sheet):
        subset = objects[sheet_i:sheet_i + per_sheet]
        rows = math.ceil(len(subset) / 2)
        sheet = Image.new("RGB", (1120, rows * 150), (235, 235, 235))
        for j, obj in enumerate(subset):
            cell = object_contact_cell(crop_rgb, obj, f"{obj['id']} | {obj.get('char', obj.get('name'))}")
            col, row = j % 2, j // 2
            sheet.paste(cell, (col * 560, row * 150))
            index_rows.append({"object_id": obj["id"], "sheet": f"{prefix}_{sheet_i // per_sheet + 1:02d}.png", "cell": j + 1})
        sheet.save(ROOT / f"{prefix}_{sheet_i // per_sheet + 1:02d}.png")
    return index_rows


def group_mask(objects, parent=None, graphic_names=None):
    out = np.zeros_like(objects[0]["mask"])
    for o in objects:
        if parent is not None and o.get("parent") == parent:
            out |= o["mask"]
        if graphic_names is not None and o.get("name") in graphic_names:
            out |= o["mask"]
    return out


def closest_pair_roi(ma, mb, pad=12):
    ca = np.column_stack(np.nonzero(ma)).astype(np.float32)
    cb = np.column_stack(np.nonzero(mb)).astype(np.float32)
    if len(ca) == 0 or len(cb) == 0:
        return None
    tree = cKDTree(cb)
    distances, indices = tree.query(ca, k=1, p=np.inf)
    k = int(np.argmin(distances))
    ay, ax = ca[k].astype(int)
    by, bx = cb[int(indices[k])].astype(int)
    x0, x1 = min(ax, bx) - pad, max(ax, bx) + pad + 1
    y0, y1 = min(ay, by) - pad, max(ay, by) + pad + 1
    return x0, y0, x1, y1


def relation_cell(crop_rgb, label, ma, mb, size=(700, 220)):
    bb = closest_pair_roi(ma, mb, pad=12)
    canvas = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(canvas)
    d.text((6, 4), label, fill="black", font=FONT)
    if bb is None:
        return canvas
    x0, y0, x1, y1 = bb
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(crop_rgb.shape[1], x1), min(crop_rgb.shape[0], y1)
    roi = crop_rgb[y0:y1, x0:x1]
    aa, bbm = ma[y0:y1, x0:x1], mb[y0:y1, x0:x1]
    over = roi.copy()
    over[aa] = np.array([255, 0, 0], dtype=np.uint8)
    over[bbm] = np.array([0, 80, 255], dtype=np.uint8)
    over[aa & bbm] = np.array([255, 230, 0], dtype=np.uint8)
    inter = np.full_like(roi, 255)
    inter[aa & bbm] = np.array([0, 0, 0], dtype=np.uint8)
    panel_w = (size[0] - 30) // 3
    panel_h = size[1] - 70
    for i, (panel, lab) in enumerate([(roi, "ORIGINAL 1x"), (over, "A RED / B BLUE / OVERLAP YELLOW"), (inter, "INTERSECTION")]):
        im = Image.fromarray(panel)
        scale = min(panel_w / im.width, panel_h / im.height)
        factor = max(1, int(math.floor(scale)))
        shown = im.resize((im.width * factor, im.height * factor), Image.Resampling.NEAREST)
        px, py = 6 + i * (panel_w + 8), 40
        canvas.paste(shown, (px, py))
        d.text((px, 25), lab, fill="black", font=FONT)
        d.rectangle((px - 1, py - 1, px + shown.width, py + shown.height), outline=(100, 100, 100))
    d.text((6, size[1] - 15), f"native nearest-pair ROI=[{x0},{y0},{x1},{y1}]; nearest-neighbour review enlargement", fill="black", font=FONT)
    return canvas


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "glyph_masks").mkdir(exist_ok=True)
    (ROOT / "graphic_masks").mkdir(exist_ok=True)
    (ROOT / "critical_masks").mkdir(exist_ok=True)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_rect = page.rect
    pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE300, SCALE300), colorspace=fitz.csRGB, alpha=False)
    page300 = np.frombuffer(pix300.samples, dtype=np.uint8).reshape(pix300.height, pix300.width, 3).copy()
    Image.fromarray(page300).save(ROOT / "full_page_300dpi.png")
    pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE200, SCALE200), colorspace=fitz.csRGB, alpha=False)
    page200 = np.frombuffer(pix200.samples, dtype=np.uint8).reshape(pix200.height, pix200.width, 3).copy()
    Image.fromarray(page200).save(ROOT / "full_page_200dpi.png")

    fx0, fy0, fx1, fy1 = FIGURE_CROP_PX
    crop_rgb = page300[fy0:fy1, fx0:fx1].copy()
    Image.fromarray(crop_rgb).save(ROOT / "figure_crop_300dpi.png")
    Image.fromarray(crop_rgb).convert("L").save(ROOT / "grayscale_300dpi.png")
    sx0, sy0, sx1, sy1 = STANDALONE_CROP_PX
    standalone = page300[sy0:sy1, sx0:sx1].copy()
    Image.fromarray(standalone).save(ROOT / "standalone_300dpi.png")

    glyphs = []
    raw = page.get_text("rawdict")
    visible_chars = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span["chars"]:
                    c = char["c"]
                    x0, y0, x1, y1 = char["bbox"]
                    if c.isspace() or y1 <= 495 or y0 >= 660 or x1 <= 55 or x0 >= 530:
                        continue
                    visible_chars.append((char, span))
    visible_chars.sort(key=lambda z: (round(z[0]["bbox"][1], 1), z[0]["bbox"][0]))
    for idx, (char, span) in enumerate(visible_chars, 1):
        gid = f"TXT_{idx:03d}"
        bbox_px = pt_bbox_to_crop_px(char["bbox"], FIGURE_CROP_PX)
        fg = rgb_from_pdf_int(span["color"])
        mask_local, clipped_bbox, bg = glyph_mask_from_page(crop_rgb, bbox_px, fg)
        full_mask = np.zeros(crop_rgb.shape[:2], dtype=bool)
        x0, y0, x1, y1 = clipped_bbox
        if mask_local.size:
            full_mask[y0:y1, x0:x1] = mask_local
        parent = assign_parent(char["bbox"])
        category = classify_char(char["c"], parent, span["size"])
        bb = tight_bbox(full_mask)
        if bb is None:
            ink_w = ink_h = pixels = 0
            bb = (0, 0, 0, 0)
        else:
            ink_w, ink_h = bb[2] - bb[0], bb[3] - bb[1]
            pixels = int(full_mask.sum())
        mask_file = ROOT / "glyph_masks" / f"{gid}.png"
        stored_bb = save_tight_mask(full_mask, mask_file)
        glyphs.append({
            "id": gid,
            "safe_filename": f"glyph_masks/{gid}.png",
            "kind": "TEXT_GLYPH",
            "char": char["c"],
            "codepoint": f"U+{ord(char['c']):04X}",
            "parent": parent,
            "font": span["font"],
            "pdf_size_pt": float(span["size"]),
            "source_color_rgb": tuple(int(v) for v in fg),
            "local_bg_rgb": tuple(int(round(v)) for v in bg),
            "source_bbox_pt": tuple(float(v) for v in char["bbox"]),
            "bbox": stored_bb,
            "ink_width_px": ink_w,
            "ink_height_px": ink_h,
            "ink_pixels": pixels,
            "category": category,
            "advisory_threshold_px": advisory_threshold(category),
            "mask": full_mask,
        })

    # Resolve the only possible ambiguity created by overlapping adjacent PDF char bboxes.
    # A shared native pixel on the later glyph's left bbox boundary belongs to that later
    # glyph; it is removed from the preceding glyph so every final raw mask is unique.
    glyph_overlap_reassignments = []
    for i, earlier in enumerate(glyphs):
        for later in glyphs[i + 1:]:
            overlap = earlier["mask"] & later["mask"]
            if not overlap.any():
                continue
            later_left = math.floor(later["source_bbox_pt"][0] * SCALE300) - FIGURE_CROP_PX[0]
            oy, ox = np.nonzero(overlap)
            if earlier["parent"] == later["parent"] and np.all(ox >= later_left):
                earlier["mask"] &= ~overlap
                glyph_overlap_reassignments.append({
                    "from": earlier["id"], "to": later["id"],
                    "pixel_count": int(len(ox)), "coordinates_yx": [[int(y), int(x)] for y, x in zip(oy, ox)],
                    "basis": "shared pixels lie on/after the later glyph PDF bbox left boundary",
                })
            else:
                raise RuntimeError(f"Unresolved glyph mask ownership: {earlier['id']} / {later['id']}")
    for g in glyphs:
        bb = tight_bbox(g["mask"])
        if bb is None:
            g["bbox"] = (0, 0, 0, 0)
            g["ink_width_px"] = g["ink_height_px"] = g["ink_pixels"] = 0
        else:
            g["bbox"] = bb
            g["ink_width_px"], g["ink_height_px"] = bb[2] - bb[0], bb[3] - bb[1]
            g["ink_pixels"] = int(g["mask"].sum())
        save_tight_mask(g["mask"], ROOT / g["safe_filename"])
    (ROOT / "machine_glyph_overlap_ownership.json").write_text(
        json.dumps(glyph_overlap_reassignments, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    drawings = page.get_drawings()
    graphics = []
    for drawing_index, name in GRAPHIC_NAMES.items():
        drawing = drawings[drawing_index]
        mask = reconstruct_drawing_mask(page_rect, drawing, (pix300.width, pix300.height), FIGURE_CROP_PX)
        oid = f"GR_{drawing_index:03d}_{name}"
        stored_bb = save_tight_mask(mask, ROOT / "graphic_masks" / f"{oid}.png")
        graphics.append({
            "id": oid,
            "safe_filename": f"graphic_masks/{oid}.png",
            "kind": "GRAPHIC",
            "name": name,
            "parent": name,
            "drawing_index": drawing_index,
            "drawing_type": drawing["type"],
            "source_bbox_pt": tuple(float(v) for v in drawing["rect"]),
            "bbox": stored_bb,
            "ink_width_px": stored_bb[2] - stored_bb[0],
            "ink_height_px": stored_bb[3] - stored_bb[1],
            "ink_pixels": int(mask.sum()),
            "stroke_width_pt": float(drawing["width"]),
            "mask": mask,
        })

    objects = glyphs + graphics
    for obj in objects:
        obj["coords"] = object_coords(obj)
        obj["tree"] = cKDTree(obj["coords"]) if len(obj["coords"]) else None

    glyph_rows = []
    for g in glyphs:
        threshold = g["advisory_threshold_px"]
        glyph_rows.append({
            "element_id": g["id"], "safe_filename": g["safe_filename"], "char": g["char"],
            "codepoint": g["codepoint"], "semantic_parent": g["parent"], "font": g["font"],
            "pdf_size_pt": f"{g['pdf_size_pt']:.6f}", "category": g["category"],
            "bbox_crop_px": json.dumps(g["bbox"]), "h_ink_px": g["ink_height_px"],
            "w_ink_px": g["ink_width_px"], "ink_pixel_count": g["ink_pixels"],
            "advisory_threshold_px": "" if threshold is None else threshold,
            "r168_machine_flag": "EMPTY_MASK" if g["ink_pixels"] == 0 else ("ADVISORY_BELOW_LEGACY_THRESHOLD" if threshold and g["ink_height_px"] < threshold else "OBSERVABLE"),
        })
    write_csv(ROOT / "machine_glyph_ledger.csv", glyph_rows, list(glyph_rows[0]))

    graphic_rows = []
    for g in graphics:
        graphic_rows.append({
            "element_id": g["id"], "safe_filename": g["safe_filename"], "graphic_name": g["name"],
            "drawing_index": g["drawing_index"], "drawing_type": g["drawing_type"],
            "source_bbox_pt": json.dumps(g["source_bbox_pt"]), "bbox_crop_px": json.dumps(g["bbox"]),
            "stroke_width_pt": f"{g['stroke_width_pt']:.6f}", "ink_pixel_count": g["ink_pixels"],
            "r168_machine_flag": "EMPTY_MASK" if g["ink_pixels"] == 0 else "OBSERVABLE",
        })
    write_csv(ROOT / "machine_graphic_ledger.csv", graphic_rows, list(graphic_rows[0]))

    object_rows = []
    for o in objects:
        object_rows.append({
            "object_id": o["id"], "safe_filename": o["safe_filename"], "kind": o["kind"],
            "semantic_parent": o["parent"], "bbox_crop_px": json.dumps(o["bbox"]), "ink_pixel_count": o["ink_pixels"],
        })
    write_csv(ROOT / "machine_object_ledger.csv", object_rows, list(object_rows[0]))

    pair_rows = []
    matrix_codes = np.zeros((len(objects), len(objects)), dtype=np.uint8)
    hard_pair_failures = 0
    overlap_total_unallowed = 0
    critical_pair_count = 0
    for i, a in enumerate(objects):
        matrix_codes[i, i] = 1
        for j in range(i + 1, len(objects)):
            b = objects[j]
            clearance, overlap = cheb_metrics(a, b)
            rule, threshold = pair_rule(a, b)
            allowed = rule.startswith("SAME_") or rule.startswith("INTENDED_")
            hard = False
            if overlap > 0 and not allowed:
                hard = True
            if threshold and clearance is not None and clearance < threshold:
                hard = True
            if hard:
                hard_pair_failures += 1
                overlap_total_unallowed += overlap
                code = 4
            elif overlap > 0 and allowed:
                code = 3
            elif threshold and clearance is not None and clearance <= threshold + 2:
                code = 2
                critical_pair_count += 1
            else:
                code = 1
            matrix_codes[i, j] = matrix_codes[j, i] = code
            pair_rows.append({
                "pair_id": f"PAIR_{i+1:03d}_{j+1:03d}", "object_a": a["id"], "object_b": b["id"],
                "rule_class": rule, "threshold_px": threshold, "raw_overlap_pixel_count": overlap,
                "chebyshev_blank_clearance_px": "" if clearance is None else f"{clearance:.1f}",
                "machine_hard_flag": "HARD_GEOMETRY_FAILURE" if hard else "NO_MACHINE_HARD_FAILURE",
            })
    write_csv(ROOT / "machine_all_unordered_pairs.csv", pair_rows, list(pair_rows[0]))

    # Text measurement overlay; IDs are deliberately sparse labels while every bbox is drawn.
    overlay = Image.fromarray(crop_rgb.copy())
    od = ImageDraw.Draw(overlay)
    for idx, g in enumerate(glyphs):
        x0, y0, x1, y1 = g["bbox"]
        od.rectangle((x0, y0, x1, y1), outline=(220, 0, 0), width=1)
        if idx % 4 == 0:
            od.text((x0, max(0, y0 - 10)), g["id"].split("_")[1], fill=(180, 0, 0), font=FONT)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Pair matrix: 1=clear, 2=threshold-near, 3=intended overlap, 4=hard failure.
    colors = np.array([[255, 255, 255], [225, 245, 225], [255, 205, 90], [175, 110, 235], [235, 30, 30]], dtype=np.uint8)
    mat = colors[matrix_codes]
    mat_img = Image.fromarray(mat).resize((len(objects) * 5, len(objects) * 5), Image.Resampling.NEAREST)
    framed = Image.new("RGB", (mat_img.width + 220, mat_img.height + 80), "white")
    framed.paste(mat_img, (200, 50))
    md = ImageDraw.Draw(framed)
    md.text((10, 8), f"ALL UNORDERED PAIRS: N={len(objects)}, C(N,2)={len(pair_rows)}", fill="black", font=FONT)
    md.text((10, 24), "green=clear orange=near purple=intended overlap red=hard", fill="black", font=FONT)
    for k in range(0, len(objects), 10):
        md.text((5, 50 + k * 5), f"{k+1:03d} {objects[k]['id'][:20]}", fill="black", font=FONT)
    framed.save(ROOT / "pair_matrix_all.png")

    contact_index = []
    contact_index.extend(make_contact_sheets(crop_rgb, glyphs, "glyph_contact_sheet", per_sheet=20))
    contact_index.extend(make_contact_sheets(crop_rgb, graphics, "graphic_contact_sheet", per_sheet=18))
    write_csv(ROOT / "contact_sheet_index.csv", contact_index, ["object_id", "sheet", "cell"])

    # Semantic overview overlay.
    sem = Image.fromarray(crop_rgb.copy())
    sd = ImageDraw.Draw(sem)
    for g in graphics:
        x0, y0, x1, y1 = g["bbox"]
        sd.rectangle((x0, y0, x1, y1), outline=(0, 120, 255), width=1)
        sd.text((x0, max(0, y0 - 10)), f"D{g['drawing_index']}", fill=(0, 70, 220), font=FONT)
    parent_boxes = {}
    for parent in sorted({g["parent"] for g in glyphs}):
        gm = group_mask(objects, parent=parent)
        bb = tight_bbox(gm)
        if bb:
            parent_boxes[parent] = bb
            sd.rectangle(bb, outline=(255, 0, 80), width=2)
            sd.text((bb[0], max(0, bb[1] - 11)), parent, fill=(200, 0, 50), font=FONT)
    sem.save(ROOT / "semantic_relationship_overlay.png")

    # Critical group relationships, with masks saved separately and shown on two sheets.
    critical_specs = [
        ("CRIT_001_STATE0_BORDER", "STATE_0", ["NODE_X0_BORDER"]),
        ("CRIT_002_STATE1_BORDER", "STATE_1", ["NODE_X1_DOUBLE_OUTER"]),
        ("CRIT_003_STATE2_BORDER", "STATE_2", ["NODE_X2_DOUBLE_OUTER"]),
        ("CRIT_004_STATE3_BORDER", "STATE_3", ["NODE_X3_DOUBLE_OUTER"]),
        ("CRIT_005_STATE4_BORDER", "STATE_4", ["NODE_X4_DOUBLE_OUTER"]),
        ("CRIT_006_STATE5_BORDER", "STATE_5", ["NODE_X5_BORDER"]),
        ("CRIT_007_STATET_BORDER", "STATE_T", ["NODE_XT_BORDER"]),
        ("CRIT_008_KERNEL_TRANS23", "KERNEL_LABEL", ["TRANS_23_SHAFT", "TRANS_23_HEAD"]),
        ("CRIT_009_RELATION_ARC", "RELATION_ANNOTATION", ["REPEAT_RELATION_ARC"]),
        ("CRIT_010_BOTTOM_AXIS", "BOTTOM_NOTE", ["TIME_AXIS_SHAFT", "TIME_AXIS_HEAD"]),
        ("CRIT_011_AXIS_TITLE_AXIS", "AXIS_TITLE", ["TIME_AXIS_SHAFT", "TIME_AXIS_HEAD"]),
        ("CRIT_012_CAPTION_FIGURE", "CAPTION", ["@ALL_BODY_OBJECTS"]),
        ("CRIT_013_HOLD12_TRANS12", "HOLD_12", ["TRANS_12_SHAFT", "TRANS_12_HEAD"]),
        ("CRIT_014_HOLD34_TRANS34", "HOLD_34", ["TRANS_34_SHAFT", "TRANS_34_HEAD"]),
        ("CRIT_015_TRANS01_CONTINUITY", "@GRAPHIC:TRANS_01_SHAFT", ["TRANS_01_HEAD"]),
        ("CRIT_016_TRANS12_CONTINUITY", "@GRAPHIC:TRANS_12_SHAFT", ["TRANS_12_HEAD"]),
        ("CRIT_017_TRANS23_CONTINUITY", "@GRAPHIC:TRANS_23_SHAFT", ["TRANS_23_HEAD"]),
        ("CRIT_018_TRANS34_CONTINUITY", "@GRAPHIC:TRANS_34_SHAFT", ["TRANS_34_HEAD"]),
        ("CRIT_019_TRANS45_CONTINUITY", "@GRAPHIC:TRANS_45_SHAFT", ["TRANS_45_HEAD"]),
        ("CRIT_020_TRANS5T_CONTINUITY", "@GRAPHIC:TRANS_5T_SHAFT", ["TRANS_5T_HEAD"]),
    ]
    critical_rows = []
    critical_cells = []
    for cid, parent, gnames in critical_specs:
        if parent.startswith("@GRAPHIC:"):
            ma = group_mask(objects, graphic_names=[parent.split(":", 1)[1]])
        else:
            ma = group_mask(objects, parent=parent)
        if gnames == ["@ALL_BODY_OBJECTS"]:
            mb = np.zeros_like(ma)
            for obj in objects:
                if obj.get("parent") != "CAPTION":
                    mb |= obj["mask"]
        else:
            mb = group_mask(objects, graphic_names=gnames)
        oa = {"coords": np.column_stack(np.nonzero(ma)).astype(np.float32)}
        ob = {"coords": np.column_stack(np.nonzero(mb)).astype(np.float32)}
        oa["tree"] = cKDTree(oa["coords"]) if len(oa["coords"]) else None
        ob["tree"] = cKDTree(ob["coords"]) if len(ob["coords"]) else None
        clearance, overlap = cheb_metrics(oa, ob)
        save_tight_mask(ma, ROOT / "critical_masks" / f"{cid}_A.png")
        save_tight_mask(mb, ROOT / "critical_masks" / f"{cid}_B.png")
        save_tight_mask(ma & mb, ROOT / "critical_masks" / f"{cid}_INTERSECTION.png")
        critical_rows.append({
            "critical_id": cid, "semantic_text_parent": parent, "graphic_group": "+".join(gnames),
            "raw_overlap_pixel_count": overlap, "chebyshev_blank_clearance_px": "" if clearance is None else f"{clearance:.1f}",
            "sheet": f"critical_relationship_sheet_{len(critical_rows) // 7 + 1:02d}.png",
            "cell": (len(critical_rows) % 7) + 1,
        })
        critical_cells.append((cid, ma, mb))
        relation_cell(crop_rgb, cid, ma, mb, size=(1800, 520)).save(ROOT / f"critical_overlay_{cid}.png")
    write_csv(ROOT / "machine_critical_relationships.csv", critical_rows, list(critical_rows[0]))
    for sheet_no, start in enumerate(range(0, len(critical_cells), 7), 1):
        subset = critical_cells[start:start + 7]
        sheet = Image.new("RGB", (1400, math.ceil(len(subset) / 2) * 220), (235, 235, 235))
        for k, (cid, ma, mb) in enumerate(subset):
            cell = relation_cell(crop_rgb, cid, ma, mb)
            sheet.paste(cell, ((k % 2) * 700, (k // 2) * 220))
        sheet.save(ROOT / f"critical_relationship_sheet_{sheet_no:02d}.png")

    # Hard-semantics target list is machine inventory only; adjudication is intentionally absent.
    semantic_targets = {
        "state_sequence": ["a", "b", "b", "c", "c", "b", "a"],
        "time_labels": ["t=0", "t=1", "t=2", "t=3", "t=4", "t=5", "t=T"],
        "required_transition_count": 6,
        "required_labels": ["K(x_t,d x_{t+1})", "K(x,dy)", "保持", "重复状态形成相邻相关"],
        "required_visual_meanings": ["equal time spacing", "adjacent-state correlation", "double-circle repeat/stay", "continuous directed arrows", "caption/page integration"],
    }
    (ROOT / "machine_semantic_targets.json").write_text(json.dumps(semantic_targets, ensure_ascii=False, indent=2), encoding="utf-8")

    glyph_mask_files = list((ROOT / "glyph_masks").glob("*.png"))
    graphic_mask_files = list((ROOT / "graphic_masks").glob("*.png"))
    critical_mask_files = list((ROOT / "critical_masks").glob("*.png"))
    facts = {
        "figure_uid": "FIG-P598-01",
        "handoff_id": "A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART-20260825",
        "official_pdf": str(PDF),
        "official_pdf_bytes": PDF.stat().st_size,
        "official_pdf_sha256": sha256(PDF),
        "physical_page": PAGE_PHYSICAL,
        "page_index_zero_based": PAGE_INDEX,
        "page_count": doc.page_count,
        "page_rect_pt": [page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1],
        "full_page_300dpi_native_dimensions": [pix300.width, pix300.height],
        "full_page_200dpi_native_dimensions": [pix200.width, pix200.height],
        "figure_crop_300dpi_integer_xyxy": list(FIGURE_CROP_PX),
        "figure_crop_300dpi_dimensions": [crop_rgb.shape[1], crop_rgb.shape[0]],
        "standalone_crop_300dpi_integer_xyxy": list(STANDALONE_CROP_PX),
        "standalone_crop_300dpi_dimensions": [standalone.shape[1], standalone.shape[0]],
        "source_file": str(SOURCE),
        "glyph_object_count": len(glyphs),
        "graphic_object_count": len(graphics),
        "total_object_count": len(objects),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
        "critical_relationship_count": len(critical_rows),
        "machine_empty_glyph_masks": sum(g["ink_pixels"] == 0 for g in glyphs),
        "machine_empty_graphic_masks": sum(g["ink_pixels"] == 0 for g in graphics),
        "machine_hard_pair_failures": hard_pair_failures,
        "machine_unallowed_overlap_pixel_sum": overlap_total_unallowed,
        "machine_near_threshold_pair_count": critical_pair_count,
        "glyph_overlap_reassignment_count": len(glyph_overlap_reassignments),
        "ordinary_glyph_mask_png_count": len(glyph_mask_files),
        "ordinary_graphic_mask_png_count": len(graphic_mask_files),
        "ordinary_critical_mask_png_count": len(critical_mask_files),
        "source_declared_sizes_pt": {
            "tikz_style": 9.2,
            "every_node": 9.4,
            "axis_title": 8.6,
            "time_labels": 8.6,
            "hold_labels": 8.6,
            "kernel_label": 8.6,
            "relationship_annotation": 8.6,
            "bottom_note": 8.6,
        },
        "r168_font_rule": "Only missing/tofu, wrong glyph/codepoint/math semantics, genuinely unreadable, obvious severe visible imbalance, or real clipping/overlap are hard failures; fine ratios/metadata/readable absolute minimum/1-2px raster are advisory.",
    }
    (ROOT / "candidate_facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    cross = {
        "object_count_matches": len(objects) == len(object_rows),
        "glyph_ledger_matches_masks": len(glyphs) == len(glyph_rows) == len(glyph_mask_files),
        "graphic_ledger_matches_masks": len(graphics) == len(graphic_rows) == len(graphic_mask_files),
        "pair_denominator_matches": len(pair_rows) == len(objects) * (len(objects) - 1) // 2,
        "object_ids_unique": len({o["id"] for o in objects}) == len(objects),
        "safe_filenames_unique": len({o["safe_filename"] for o in objects}) == len(objects),
        "empty_masks": sum(o["ink_pixels"] == 0 for o in objects),
        "hard_pair_failures": hard_pair_failures,
        "unallowed_overlap_pixel_sum": overlap_total_unallowed,
        "contact_index_count": len(contact_index),
        "critical_count": len(critical_rows),
        "critical_mask_expected": len(critical_rows) * 3,
        "critical_mask_actual": len(critical_mask_files),
        "manual_fields_present": False,
    }
    (ROOT / "machine_crosscheck.json").write_text(json.dumps(cross, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
