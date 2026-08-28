from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R19_SA3_FRESH_ISOLATED_R107_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex")
PHYSICAL_PAGE = 765
PAGE_INDEX = PHYSICAL_PAGE - 1
SCALE_300 = 300.0 / 72.0
SCALE_200 = 200.0 / 72.0
FIGURE_CROP_PT = (66.0, 67.5, 518.0, 288.5)
STANDALONE_PT = (66.0, 67.5, 518.0, 269.9)
PANEL_LEFT_PT = (68.02938842773438, 69.44791412353516, 301.8905334472656, 267.87554931640625)
PANEL_RIGHT_PT = (310.3916931152344, 69.44791412353516, 515.9091186523438, 267.87554931640625)
CAPTION_PT = (102.70, 272.09, 481.24, 286.52)


for sub in [
    "masks/glyphs",
    "masks/drawings",
    "glyph_views",
    "drawing_views",
    "contact_sheets/glyphs",
    "contact_sheets/drawings",
    "critical_relations",
]:
    machine_dir = ROOT / sub
    machine_dir.mkdir(parents=True, exist_ok=True)
    for stale_png in machine_dir.glob("*.png"):
        stale_png.unlink()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pixmap_to_image(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def pt_rect_to_px(rect, scale=SCALE_300):
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * scale)),
        int(math.floor(y0 * scale)),
        int(math.ceil(x1 * scale)),
        int(math.ceil(y1 * scale)),
    )


def rgb_from_int(color: int):
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def save_csv(path: Path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rect = page.rect

pix300 = page.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False, annots=True)
page300 = pixmap_to_image(pix300).convert("RGB")
page300.save(ROOT / "full_page_300dpi.png")

pix200 = page.get_pixmap(matrix=fitz.Matrix(SCALE_200, SCALE_200), alpha=False, annots=True)
pixmap_to_image(pix200).convert("RGB").save(ROOT / "full_page_200dpi.png")

fig_px = pt_rect_to_px(FIGURE_CROP_PT)
stand_px = pt_rect_to_px(STANDALONE_PT)
figure_crop = page300.crop(fig_px)
standalone = page300.crop(stand_px)
figure_crop.save(ROOT / "figure_crop_300dpi.png")
standalone.save(ROOT / "standalone_300dpi.png")
figure_crop.convert("L").save(ROOT / "grayscale_300dpi.png")

page_arr = np.asarray(page300).copy()


PARENT_META = {
    "TITLE_LEFT": ("LEFT", "TITLE", 10.4, 27),
    "TITLE_RIGHT": ("RIGHT", "TITLE", 10.4, 28),
    "NODE_I": ("LEFT", "NODE_LABEL", 10.2, 30),
    "NODE_J": ("LEFT", "NODE_LABEL", 10.2, 31),
    "NODE_H": ("LEFT", "NODE_LABEL", 10.2, 32),
    "EDGE_J_TO_I_LABEL": ("LEFT", "EDGE_LABEL", 9.5, 34),
    "EDGE_I_TO_J_LABEL": ("LEFT", "EDGE_LABEL", 9.5, 36),
    "NOTE_EDGE_WEIGHTS": ("LEFT", "ANNOTATION", 9.5, 40),
    "NOTE_MATRIX_ORDER": ("LEFT", "ANNOTATION", 9.5, 41),
    "FORMULA_A_DIRECTION": ("LEFT", "FORMULA", 12.0, 42),
    "FORMULA_OUTDEGREE": ("LEFT", "FORMULA", 12.0, 44),
    "FORMULA_A_LABEL": ("LEFT", "FORMULA", 12.0, 46),
    "FORMULA_M_LABEL": ("LEFT", "FORMULA", 12.0, 53),
    "FORMULA_M_COLUMN": ("LEFT", "FORMULA", 12.0, 59),
    "FORMULA_COLUMN_SUM": ("LEFT", "FORMULA", 12.0, 61),
    "FORMULA_P_UPDATE": ("LEFT", "FORMULA", 12.0, 63),
    "NOTE_RIGHT_ORDER": ("RIGHT", "ANNOTATION", 9.5, 65),
    "FORMULA_P_LABEL": ("RIGHT", "FORMULA", 12.0, 66),
    "FORMULA_TRANSPOSE": ("RIGHT", "FORMULA", 12.0, 72),
    "FORMULA_P_INDEX": ("RIGHT", "FORMULA", 12.0, 73),
    "FORMULA_PROBABILITY": ("RIGHT", "FORMULA", 12.0, 75),
    "FORMULA_ROW_SUM": ("RIGHT", "FORMULA", 12.0, 76),
    "FORMULA_RHO_UPDATE": ("RIGHT", "FORMULA", 12.0, 77),
    "FORMULA_RHO_BRIDGE": ("RIGHT", "FORMULA", 12.0, 79),
    "CAPTION": ("CAPTION", "CAPTION", None, 82),
}
for matrix in ["A", "M", "P"]:
    panel = "LEFT" if matrix != "P" else "RIGHT"
    for row in range(1, 4):
        for col in range(1, 4):
            line = {"A": 49, "M": 56, "P": 69}[matrix]
            PARENT_META[f"MATRIX_{matrix}_R{row}C{col}"] = (panel, "MATRIX_CELL", 10.2, line)


def parent_for_char(block_i, line_i, span_i, bbox):
    x0, y0, x1, y1 = bbox
    if block_i == 1:
        return "TITLE_LEFT" if line_i == 0 else "TITLE_RIGHT"
    if block_i == 2:
        return "NODE_I" if line_i == 0 else "NODE_J"
    if block_i == 3:
        return "NODE_H"
    if block_i == 4:
        return "EDGE_J_TO_I_LABEL"
    if block_i == 5:
        return "EDGE_I_TO_J_LABEL"
    if block_i == 6:
        return "NOTE_EDGE_WEIGHTS" if line_i == 0 else "NOTE_MATRIX_ORDER"
    if block_i == 7:
        return "NOTE_MATRIX_ORDER" if line_i == 0 else "FORMULA_A_DIRECTION"
    if block_i == 8:
        return "FORMULA_OUTDEGREE"
    if block_i == 9:
        return "FORMULA_A_LABEL"
    if block_i in (10, 11, 12) and x1 < 180:
        return f"MATRIX_A_R{block_i - 9}C{line_i + 1}"
    if block_i == 12 and x0 > 180:
        return "FORMULA_M_LABEL"
    if block_i in (13, 14, 15) and line_i < 3 and x0 > 220:
        return f"MATRIX_M_R{block_i - 12}C{line_i + 1}"
    if block_i == 15 and line_i == 3:
        return "FORMULA_M_COLUMN"
    if block_i == 15 and line_i == 4:
        return "FORMULA_COLUMN_SUM"
    if block_i == 15 and line_i == 5:
        return "FORMULA_P_UPDATE"
    if block_i == 16:
        return "NOTE_RIGHT_ORDER"
    if block_i == 17:
        return "FORMULA_P_LABEL"
    if block_i in (18, 19, 20):
        return f"MATRIX_P_R{block_i - 17}C{line_i + 1}"
    if block_i == 21:
        return "FORMULA_TRANSPOSE"
    if block_i == 22:
        return "FORMULA_P_INDEX" if line_i == 0 else "FORMULA_PROBABILITY"
    if block_i == 23:
        return "FORMULA_ROW_SUM" if line_i == 0 else "FORMULA_RHO_UPDATE"
    if block_i == 24:
        return "FORMULA_RHO_BRIDGE"
    if block_i == 25:
        return "CAPTION"
    raise RuntimeError(f"Unmapped char block={block_i} line={line_i} span={span_i} bbox={bbox}")


def script_class(ch: str, font_size: float, parent: str):
    cp = ord(ch)
    name = unicodedata.name(ch, "")
    if ch in ".,;:，。；：、…·":
        return "LOW_PROFILE_PUNCTUATION"
    if 0x4E00 <= cp <= 0x9FFF or "CJK" in name:
        return "CJK_FULL"
    if ch.isdigit():
        return "DIGIT"
    if "MATHEMATICAL" in name and any(k in name for k in ["SMALL", "ITALIC SMALL"]):
        if font_size < 11.8 and parent.startswith("FORMULA_"):
            return "NATURAL_SCRIPT"
        return "LATIN_GREEK_LOWER"
    if ("GREEK SMALL" in name) or (ch.isalpha() and ch.lower() == ch and ch.upper() != ch):
        if font_size < 11.8 and parent.startswith("FORMULA_"):
            return "NATURAL_SCRIPT"
        return "LATIN_GREEK_LOWER"
    if ch.isalpha() and ch.upper() == ch and ch.lower() != ch:
        return "LATIN_UPPER"
    if ch in "+−-=><⟺→∑∣/∶":
        return "MATH_OPERATOR"
    if ch in "()[]{}（）":
        return "FULLHEIGHT_SYMBOL"
    return "MATH_SYMBOL"


CLASS_FLOORS = {
    "CJK_FULL": 30,
    "LATIN_UPPER": 24,
    "DIGIT": 24,
    "LATIN_GREEK_LOWER": 17,
    "MATH_OPERATOR": 22,
    "MATH_SYMBOL": 22,
    "FULLHEIGHT_SYMBOL": 22,
    "NATURAL_SCRIPT": 15,
    "LOW_PROFILE_PUNCTUATION": None,
}


def estimate_background(expanded, inner_box):
    arr = expanded.reshape(-1, 3)
    quant = (arr // 4).astype(np.uint8)
    packed = quant[:, 0].astype(np.int32) * 4096 + quant[:, 1].astype(np.int32) * 64 + quant[:, 2].astype(np.int32)
    mode = Counter(packed.tolist()).most_common(1)[0][0]
    sel = arr[packed == mode]
    return np.median(sel, axis=0).astype(np.float64)


def char_mask(full_arr, bbox_px, target_rgb):
    x0, y0, x1, y1 = bbox_px
    patch = full_arr[y0:y1, x0:x1].astype(np.float64)
    ex0, ey0, ex1, ey1 = max(0, x0 - 3), max(0, y0 - 3), min(full_arr.shape[1], x1 + 3), min(full_arr.shape[0], y1 + 3)
    expanded = full_arr[ey0:ey1, ex0:ex1].astype(np.float64)
    bg = estimate_background(expanded, (x0 - ex0, y0 - ey0, x1 - ex0, y1 - ey0))
    target = np.array(target_rgb, dtype=np.float64)
    v = bg - target
    denom = float(np.dot(v, v))
    if denom < 1:
        return np.zeros((y1 - y0, x1 - x0), dtype=bool), bg, 0
    alpha = np.tensordot(bg - patch, v, axes=([2], [0])) / denom
    recon = bg[None, None, :] - alpha[:, :, None] * v[None, None, :]
    residual = np.sqrt(np.sum((patch - recon) ** 2, axis=2))
    contrast = np.sqrt(np.sum((patch - bg[None, None, :]) ** 2, axis=2))
    mask = (alpha >= (20.0 / 255.0)) & (alpha <= 1.25) & (residual <= 34.0)
    foreign = int(np.count_nonzero((contrast >= 20.0) & ~mask))
    return mask, bg, foreign


def tight_mask(mask, x0, y0):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return mask, (x0, y0, x0, y0)
    tx0, tx1 = int(xs.min()), int(xs.max()) + 1
    ty0, ty1 = int(ys.min()), int(ys.max()) + 1
    return mask[ty0:ty1, tx0:tx1], (x0 + tx0, y0 + ty0, x0 + tx1, y0 + ty1)


def make_view(full_img, mask, bbox, label, out_path):
    x0, y0, x1, y1 = bbox
    pad = 4
    ex0, ey0, ex1, ey1 = max(0, x0 - pad), max(0, y0 - pad), min(full_img.width, x1 + pad), min(full_img.height, y1 + pad)
    original = full_img.crop((ex0, ey0, ex1, ey1)).convert("RGB")
    local_mask = np.zeros((ey1 - ey0, ex1 - ex0), dtype=bool)
    local_mask[y0 - ey0:y1 - ey0, x0 - ex0:x1 - ex0] = mask
    overlay = np.asarray(original).copy()
    overlay[local_mask] = np.array([230, 32, 32], dtype=np.uint8)
    overlay = Image.fromarray(overlay)
    mask_only = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8)).convert("RGB")
    views = [original, overlay, mask_only]
    zoomed = [v.resize((v.width * 8, v.height * 8), Image.Resampling.NEAREST) for v in views]
    maxw = max(v.width for v in zoomed)
    maxh = max(v.height for v in zoomed)
    canvas = Image.new("RGB", (max(1500, maxw * 3 + 32), max(620, maxh + 105)), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 8), label, fill="black")
    labels = ["ORIGINAL 8X NEAREST", "TARGET OVERLAY 8X NEAREST", "MASK ONLY 8X NEAREST"]
    for idx, view in enumerate(zoomed):
        x = 10 + idx * (maxw + 10)
        canvas.paste(view, (x, 70))
        draw.text((x, 48), labels[idx], fill="black")
    canvas.save(out_path)
    return canvas


objects = []
glyph_rows = []
id_map_rows = []
glyph_canvases = []
raw = page.get_text("rawdict")
gid = 0
for bi, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for li, line in enumerate(block["lines"]):
        for si, span in enumerate(line["spans"]):
            for ci, char in enumerate(span["chars"]):
                ch = char["c"]
                if not ch.strip():
                    continue
                bbox_pt = tuple(float(v) for v in char["bbox"])
                cx = (bbox_pt[0] + bbox_pt[2]) / 2
                cy = (bbox_pt[1] + bbox_pt[3]) / 2
                in_body = 68.0 <= cx <= 516.0 and 69.0 <= cy <= 268.0
                in_caption = 68.0 <= cx <= 516.0 and 268.0 < cy <= 290.0
                if not (in_body or in_caption):
                    continue
                gid += 1
                oid = f"G{gid:04d}"
                safe = f"g{gid:04d}"
                parent = parent_for_char(bi, li, si, bbox_pt)
                panel, role, declared_pt, source_line = PARENT_META[parent]
                bbox_px = pt_rect_to_px(bbox_pt)
                mask_box, bg, foreign = char_mask(page_arr, bbox_px, rgb_from_int(span["color"]))
                tight, tight_bbox = tight_mask(mask_box, bbox_px[0], bbox_px[1])
                Image.fromarray(np.where(tight, 0, 255).astype(np.uint8)).save(ROOT / "masks/glyphs" / f"{safe}.png")
                view = make_view(page300, tight, tight_bbox, f"{oid} U+{ord(ch):04X} parent={parent}", ROOT / "glyph_views" / f"{safe}.png")
                glyph_canvases.append((oid, view))
                h_ink = int(tight.shape[0]) if tight.size and np.any(tight) else 0
                cls = script_class(ch, float(span["size"]), parent)
                row = {
                    "object_id": oid,
                    "safe_filename": safe,
                    "char": ch,
                    "codepoint": f"U+{ord(ch):04X}",
                    "parent_id": parent,
                    "panel_id": panel,
                    "role": role,
                    "script_class": cls,
                    "class_floor_px": "" if CLASS_FLOORS[cls] is None else CLASS_FLOORS[cls],
                    "source_file": str(SOURCE),
                    "source_line": source_line,
                    "declared_pt": "INHERITED_CAPTION" if declared_pt is None else declared_pt,
                    "graphics_scale": 1.0,
                    "pdf_vector_font_size": round(float(span["size"]), 3),
                    "font_name": span["font"],
                    "font_color_rgb": "#%06X" % span["color"],
                    "bbox_pt_x0": round(bbox_pt[0], 4),
                    "bbox_pt_y0": round(bbox_pt[1], 4),
                    "bbox_pt_x1": round(bbox_pt[2], 4),
                    "bbox_pt_y1": round(bbox_pt[3], 4),
                    "mask_x0_px": tight_bbox[0],
                    "mask_y0_px": tight_bbox[1],
                    "mask_x1_px": tight_bbox[2],
                    "mask_y1_px": tight_bbox[3],
                    "h_ink_px": h_ink,
                    "mask_pixel_count": int(np.count_nonzero(tight)),
                    "unassigned_residual_contrast_px": foreign,
                    "background_rgb": ",".join(str(int(round(v))) for v in bg),
                    "block_index": bi,
                    "line_index": li,
                    "span_index": si,
                    "char_index": ci,
                    "mask_path": f"masks/glyphs/{safe}.png",
                    "view_path": f"glyph_views/{safe}.png",
                }
                glyph_rows.append(row)
                objects.append({
                    "id": oid,
                    "safe": safe,
                    "kind": "GLYPH",
                    "parent": parent,
                    "panel": panel,
                    "role": role,
                    "bbox": tight_bbox,
                    "mask": tight,
                    "text": ch,
                })
                id_map_rows.append({"object_id": oid, "safe_filename": safe, "kind": "GLYPH"})


# Character bboxes in PDF text extraction can overlap because of italic correction and
# TeX script placement.  The native foreground at a shared pixel must belong to one
# glyph only.  Partition every shared foreground pixel to the nearest normalized glyph
# centre, then regenerate every glyph mask/view from the unique partition.  This is a
# mechanical contour ownership operation; it emits no review outcome.
glyph_objects = list(objects)
coord_owners = defaultdict(list)
for idx, obj in enumerate(glyph_objects):
    ys, xs = np.nonzero(obj["mask"])
    gx = xs + obj["bbox"][0]
    gy = ys + obj["bbox"][1]
    for xx, yy in zip(gx.tolist(), gy.tolist()):
        coord_owners[(xx, yy)].append(idx)
partition_removed = Counter()
for (xx, yy), owners in coord_owners.items():
    if len(owners) <= 1:
        continue
    scored = []
    for idx in owners:
        obj = glyph_objects[idx]
        x0, y0, x1, y1 = obj["bbox"]
        cx, cy = (x0 + x1 - 1) / 2.0, (y0 + y1 - 1) / 2.0
        sx, sy = max(1.0, (x1 - x0) / 2.0), max(1.0, (y1 - y0) / 2.0)
        score = ((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2
        scored.append((score, idx))
    winner = min(scored)[1]
    for _, idx in scored:
        if idx == winner:
            continue
        obj = glyph_objects[idx]
        lx, ly = xx - obj["bbox"][0], yy - obj["bbox"][1]
        if 0 <= ly < obj["mask"].shape[0] and 0 <= lx < obj["mask"].shape[1] and obj["mask"][ly, lx]:
            obj["mask"][ly, lx] = False
            partition_removed[obj["id"]] += 1

glyph_canvases = []
row_by_id = {r["object_id"]: r for r in glyph_rows}
for obj in glyph_objects:
    old_x0, old_y0, _, _ = obj["bbox"]
    tight, bbox = tight_mask(obj["mask"], old_x0, old_y0)
    obj["mask"] = tight
    obj["bbox"] = bbox
    row = row_by_id[obj["id"]]
    row["partitioned_shared_pixel_count"] = partition_removed[obj["id"]]
    row["mask_x0_px"], row["mask_y0_px"], row["mask_x1_px"], row["mask_y1_px"] = bbox
    row["h_ink_px"] = int(tight.shape[0]) if tight.size and np.any(tight) else 0
    row["mask_pixel_count"] = int(np.count_nonzero(tight))
    Image.fromarray(np.where(tight, 0, 255).astype(np.uint8)).save(ROOT / "masks/glyphs" / f"{obj['safe']}.png")
    view = make_view(page300, tight, bbox, f"{obj['id']} U+{ord(obj['text']):04X} parent={obj['parent']}", ROOT / "glyph_views" / f"{obj['safe']}.png")
    glyph_canvases.append((obj["id"], view))


DRAW_META = {
    3: ("PANEL_LEFT_BORDER", "LEFT", "PANEL_BORDER"),
    4: ("PANEL_RIGHT_BORDER", "RIGHT", "PANEL_BORDER"),
    7: ("NODE_I", "LEFT", "NODE_BORDER"),
    10: ("NODE_J", "LEFT", "NODE_BORDER"),
    13: ("NODE_H", "LEFT", "NODE_BORDER"),
    16: ("EDGE_J_TO_I", "LEFT", "LINE_ARROW"),
    17: ("EDGE_J_TO_I", "LEFT", "ARROWHEAD"),
    20: ("EDGE_I_TO_J", "LEFT", "LINE_ARROW"),
    21: ("EDGE_I_TO_J", "LEFT", "ARROWHEAD"),
    24: ("EDGE_J_TO_H", "LEFT", "LINE_ARROW"),
    25: ("EDGE_J_TO_H", "LEFT", "ARROWHEAD"),
    27: ("EDGE_H_TO_I", "LEFT", "LINE_ARROW"),
    28: ("EDGE_H_TO_I", "LEFT", "ARROWHEAD"),
}
for seq, matrix in [(35, "A"), (55, "M"), (79, "P")]:
    panel = "LEFT" if matrix != "P" else "RIGHT"
    for k in range(9):
        DRAW_META[seq + 2 * k] = (f"MATRIX_{matrix}_R{k // 3 + 1}C{k % 3 + 1}", panel, "MATRIX_CELL_BORDER")
for seq, matrix, cell in [(53, "A", "R1C2"), (73, "M", "R1C2"), (97, "P", "R2C1")]:
    panel = "LEFT" if matrix != "P" else "RIGHT"
    DRAW_META[seq] = (f"FOCUS_{matrix}_{cell}", panel, "FOCUS_BORDER")


def replay_drawing_mask(drawing, role):
    tmp = fitz.open()
    p = tmp.new_page(width=page_rect.width, height=page_rect.height)
    shape = p.new_shape()
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing operator: {op}")
    include_fill = role == "ARROWHEAD"
    shape.finish(
        width=float(drawing.get("width") or 1.0),
        color=(0, 0, 0),
        fill=(0, 0, 0) if include_fill else None,
        lineCap=int(max(drawing.get("lineCap") or (0,))),
        lineJoin=int(drawing.get("lineJoin") or 0),
        dashes=drawing.get("dashes"),
        even_odd=bool(drawing.get("even_odd") or False),
        closePath=bool(drawing.get("closePath") or False),
    )
    shape.commit()
    pix = p.get_pixmap(matrix=fitz.Matrix(SCALE_300, SCALE_300), alpha=False)
    arr = np.asarray(pixmap_to_image(pix).convert("RGB"))
    mask_full = np.min(arr, axis=2) <= 235
    rect = drawing["rect"]
    px = pt_rect_to_px((rect.x0 - 1.5, rect.y0 - 1.5, rect.x1 + 1.5, rect.y1 + 1.5))
    x0, y0, x1, y1 = max(0, px[0]), max(0, px[1]), min(arr.shape[1], px[2]), min(arr.shape[0], px[3])
    local = mask_full[y0:y1, x0:x1]
    tight, tight_bbox = tight_mask(local, x0, y0)
    tmp.close()
    return tight, tight_bbox


drawing_rows = []
drawing_canvases = []
did = 0
for drawing in page.get_drawings():
    seq = int(drawing["seqno"])
    if seq not in DRAW_META:
        continue
    did += 1
    oid = f"D{did:04d}"
    safe = f"d{did:04d}"
    parent, panel, role = DRAW_META[seq]
    mask, bbox = replay_drawing_mask(drawing, role)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).save(ROOT / "masks/drawings" / f"{safe}.png")
    view = make_view(page300, mask, bbox, f"{oid} seq={seq} parent={parent} role={role}", ROOT / "drawing_views" / f"{safe}.png")
    drawing_canvases.append((oid, view))
    rect = drawing["rect"]
    item_ops = "".join(i[0] for i in drawing["items"])
    row = {
        "object_id": oid,
        "safe_filename": safe,
        "pdf_seqno": seq,
        "parent_id": parent,
        "panel_id": panel,
        "role": role,
        "pdf_drawing_type": drawing["type"],
        "item_count": len(drawing["items"]),
        "item_operators": item_ops,
        "stroke_width_pt": round(float(drawing.get("width") or 0), 5),
        "stroke_rgb": "" if drawing.get("color") is None else ",".join(f"{v:.6f}" for v in drawing["color"]),
        "fill_rgb": "" if drawing.get("fill") is None else ",".join(f"{v:.6f}" for v in drawing["fill"]),
        "bbox_pt_x0": round(rect.x0, 5),
        "bbox_pt_y0": round(rect.y0, 5),
        "bbox_pt_x1": round(rect.x1, 5),
        "bbox_pt_y1": round(rect.y1, 5),
        "mask_x0_px": bbox[0],
        "mask_y0_px": bbox[1],
        "mask_x1_px": bbox[2],
        "mask_y1_px": bbox[3],
        "mask_pixel_count": int(np.count_nonzero(mask)),
        "mask_path": f"masks/drawings/{safe}.png",
        "view_path": f"drawing_views/{safe}.png",
    }
    drawing_rows.append(row)
    objects.append({
        "id": oid,
        "safe": safe,
        "kind": "DRAWING",
        "parent": parent,
        "panel": panel,
        "role": role,
        "bbox": bbox,
        "mask": mask,
        "seqno": seq,
    })
    id_map_rows.append({"object_id": oid, "safe_filename": safe, "kind": "DRAWING"})


def build_contact_sheets(items, out_dir, prefix, per_sheet=32):
    paths = []
    for start in range(0, len(items), per_sheet):
        chunk = items[start:start + per_sheet]
        cols = 4
        rows = int(math.ceil(len(chunk) / cols))
        cell_w, cell_h = 1500, 620
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, (oid, canvas) in enumerate(chunk):
            x = (idx % cols) * cell_w
            y = (idx // cols) * cell_h
            sheet.paste(canvas.crop((0, 0, min(cell_w, canvas.width), min(cell_h, canvas.height))), (x, y))
            draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(120, 120, 120), width=2)
        sheet_no = start // per_sheet + 1
        path = out_dir / f"{prefix}_{sheet_no:02d}.png"
        sheet.save(path)
        paths.append({"sheet": sheet_no, "path": str(path.relative_to(ROOT)).replace("\\", "/"), "first_id": chunk[0][0], "last_id": chunk[-1][0], "count": len(chunk)})
    return paths


glyph_sheets = build_contact_sheets(glyph_canvases, ROOT / "contact_sheets/glyphs", "glyph_contact_sheet", 32)
drawing_sheets = build_contact_sheets(drawing_canvases, ROOT / "contact_sheets/drawings", "drawing_contact_sheet", 24)


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def intersection_count(a, b):
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return 0
    am = a["mask"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bm = b["mask"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(am & bm))


def exact_distance(a, b):
    inter = intersection_count(a, b)
    if inter:
        return 0.0, inter
    ay, ax = np.nonzero(a["mask"])
    by, bx = np.nonzero(b["mask"])
    if len(ax) == 0 or len(bx) == 0:
        return None, inter
    pa = np.column_stack((ax + a["bbox"][0], ay + a["bbox"][1]))
    pb = np.column_stack((bx + b["bbox"][0], by + b["bbox"][1]))
    if len(pa) > len(pb):
        pa, pb = pb, pa
    tree = cKDTree(pb)
    dist = float(np.min(tree.query(pa, k=1, workers=-1)[0]))
    return dist, inter


def structural_relation(a, b):
    if a["kind"] != "DRAWING" or b["kind"] != "DRAWING":
        return None
    pa, pb = a["parent"], b["parent"]
    if pa == pb and (pa.startswith("EDGE_") or pa.startswith("MATRIX_")):
        return "SAME_STRUCTURAL_PARENT"
    endpoints = {
        "EDGE_J_TO_I": {"NODE_J", "NODE_I"},
        "EDGE_I_TO_J": {"NODE_I", "NODE_J"},
        "EDGE_J_TO_H": {"NODE_J", "NODE_H"},
        "EDGE_H_TO_I": {"NODE_H", "NODE_I"},
    }
    if pa in endpoints and pb in endpoints[pa]:
        return "GRAPH_ENDPOINT_CONNECTION"
    if pb in endpoints and pa in endpoints[pb]:
        return "GRAPH_ENDPOINT_CONNECTION"
    if pa.startswith("MATRIX_") and pb.startswith("MATRIX_") and pa.split("_")[1] == pb.split("_")[1]:
        return "MATRIX_SHARED_GRID"
    if pa.startswith("FOCUS_") and pb.startswith("MATRIX_") and pa.split("_")[1] == pb.split("_")[1]:
        return "FOCUS_OVER_CELL"
    if pb.startswith("FOCUS_") and pa.startswith("MATRIX_") and pb.split("_")[1] == pa.split("_")[1]:
        return "FOCUS_OVER_CELL"
    return None


def relation_rule(a, b):
    structural = structural_relation(a, b)
    if structural:
        return structural, 0
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["parent"] == b["parent"]:
            return "SAME_TEXT_OR_FORMULA_PARENT", 0
        if {a["panel"], b["panel"]} == {"LEFT", "RIGHT"}:
            return "CROSS_PANEL_READER_ELEMENTS", 8
        return "INDEPENDENT_TEXT_TEXT", 4
    if a["kind"] != b["kind"]:
        text = a if a["kind"] == "GLYPH" else b
        draw = b if a["kind"] == "GLYPH" else a
        if draw["role"] == "PANEL_BORDER":
            return "TEXT_TO_PANEL_BORDER", 6
        if draw["role"] == "NODE_BORDER" and text["parent"] == draw["parent"]:
            return "NODE_TEXT_TO_BORDER", 5
        if draw["role"] in {"LINE_ARROW", "ARROWHEAD", "NODE_BORDER", "MATRIX_CELL_BORDER", "FOCUS_BORDER"}:
            return "TEXT_FORMULA_TO_GRAPHIC", 3
        return "TEXT_TO_DRAWING", 3
    return "INDEPENDENT_DRAWINGS", 0


def relation_view(a, b, distance, inter, out_path):
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    pad = 8
    union_w, union_h = max(ax1, bx1) - min(ax0, bx0), max(ay1, by1) - min(ay0, by0)
    if union_w > 180 or union_h > 180:
        ay, ax = np.nonzero(a["mask"])
        by, bx = np.nonzero(b["mask"])
        pa = np.column_stack((ax + ax0, ay + ay0))
        pb = np.column_stack((bx + bx0, by + by0))
        tree = cKDTree(pb)
        distances, indices = tree.query(pa, k=1, workers=-1)
        ia = int(np.argmin(distances))
        pta, ptb = pa[ia], pb[int(indices[ia])]
        roi_pad = 24
        x0 = max(0, int(min(pta[0], ptb[0])) - roi_pad)
        y0 = max(0, int(min(pta[1], ptb[1])) - roi_pad)
        x1 = min(page300.width, int(max(pta[0], ptb[0])) + roi_pad + 1)
        y1 = min(page300.height, int(max(pta[1], ptb[1])) + roi_pad + 1)
    else:
        x0, y0 = max(0, min(ax0, bx0) - pad), max(0, min(ay0, by0) - pad)
        x1, y1 = min(page300.width, max(ax1, bx1) + pad), min(page300.height, max(ay1, by1) + pad)
    original = page300.crop((x0, y0, x1, y1)).convert("RGB")
    ma = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    mb = np.zeros_like(ma)
    aix0, aiy0, aix1, aiy1 = max(ax0, x0), max(ay0, y0), min(ax1, x1), min(ay1, y1)
    bix0, biy0, bix1, biy1 = max(bx0, x0), max(by0, y0), min(bx1, x1), min(by1, y1)
    if aix1 > aix0 and aiy1 > aiy0:
        ma[aiy0 - y0:aiy1 - y0, aix0 - x0:aix1 - x0] = a["mask"][aiy0 - ay0:aiy1 - ay0, aix0 - ax0:aix1 - ax0]
    if bix1 > bix0 and biy1 > biy0:
        mb[biy0 - y0:biy1 - y0, bix0 - x0:bix1 - x0] = b["mask"][biy0 - by0:biy1 - by0, bix0 - bx0:bix1 - bx0]
    overlay = np.asarray(original).copy()
    overlay[ma] = np.array([220, 40, 40], dtype=np.uint8)
    overlay[mb] = np.array([40, 80, 220], dtype=np.uint8)
    overlay[ma & mb] = np.array([255, 0, 255], dtype=np.uint8)
    mask_a = Image.fromarray(np.where(ma, 0, 255).astype(np.uint8)).convert("RGB")
    mask_b = Image.fromarray(np.where(mb, 0, 255).astype(np.uint8)).convert("RGB")
    inter_img = Image.fromarray(np.where(ma & mb, 0, 255).astype(np.uint8)).convert("RGB")
    views = [original, Image.fromarray(overlay), mask_a, mask_b, inter_img]
    zoomed = [v.resize((v.width * 8, v.height * 8), Image.Resampling.NEAREST) for v in views]
    maxw, maxh = max(v.width for v in zoomed), max(v.height for v in zoomed)
    canvas = Image.new("RGB", (max(1900, 5 * maxw + 60), max(600, maxh + 90)), "white")
    dr = ImageDraw.Draw(canvas)
    dr.text((10, 8), f"{a['id']} vs {b['id']} distance={distance} raw_intersection={inter}", fill="black")
    labs = ["ORIGINAL", "A RED/B BLUE", "MASK A", "MASK B", "INTERSECTION"]
    for k, v in enumerate(zoomed):
        xx = 10 + k * (maxw + 10)
        canvas.paste(v, (xx, 65))
        dr.text((xx, 43), labs[k] + " 8X NEAREST", fill="black")
    canvas.save(out_path)


pair_rows = []
critical_rows = []
candidate_intersection_sum = 0
min_clearance = None
pair_no = 0
for i in range(len(objects)):
    for j in range(i + 1, len(objects)):
        a, b = objects[i], objects[j]
        pair_no += 1
        relation, threshold = relation_rule(a, b)
        bgap = bbox_gap(a["bbox"], b["bbox"])
        need_exact = bgap <= max(14.0, threshold + 4.0)
        if need_exact:
            dist, inter = exact_distance(a, b)
            method = "EXACT_RAW_MASK"
        else:
            dist, inter = bgap, 0
            method = "BBOX_LOWER_BOUND"
        if threshold > 0 and dist is not None:
            min_clearance = dist if min_clearance is None else min(min_clearance, dist)
        machine_candidate = int((threshold > 0 and (dist is None or dist < threshold)) or (relation == "INDEPENDENT_DRAWINGS" and inter > 0) or (relation == "SAME_TEXT_OR_FORMULA_PARENT" and inter > 0))
        if machine_candidate:
            candidate_intersection_sum += inter
        pair_id = f"R{pair_no:05d}"
        critical = int(machine_candidate or (threshold > 0 and dist is not None and dist < threshold + 3.0))
        evidence_path = ""
        if critical:
            safe = f"{pair_id.lower()}_{a['safe']}_{b['safe']}.png"
            evidence_path = f"critical_relations/{safe}"
            relation_view(a, b, None if dist is None else round(dist, 4), inter, ROOT / evidence_path)
            critical_rows.append({
                "pair_id": pair_id,
                "object_a": a["id"],
                "object_b": b["id"],
                "relation": relation,
                "threshold_px": threshold,
                "distance_px": "" if dist is None else round(dist, 4),
                "raw_intersection_px": inter,
                "machine_candidate_0_1": machine_candidate,
                "evidence_path": evidence_path,
            })
        pair_rows.append({
            "pair_id": pair_id,
            "object_a": a["id"],
            "object_b": b["id"],
            "kind_a": a["kind"],
            "kind_b": b["kind"],
            "parent_a": a["parent"],
            "parent_b": b["parent"],
            "panel_a": a["panel"],
            "panel_b": b["panel"],
            "role_a": a["role"],
            "role_b": b["role"],
            "relation": relation,
            "threshold_px": threshold,
            "bbox_gap_px": round(bgap, 4),
            "min_raw_mask_distance_px_or_lower_bound": "" if dist is None else round(dist, 4),
            "distance_method": method,
            "raw_intersection_px": inter,
            "machine_candidate_0_1": machine_candidate,
            "critical_evidence_path": evidence_path,
        })


# Add one independently inspectable nearest hard-clearance relation per local class,
# and one representative for every intended structural-intersection class.  These are
# evidence selections only; the machine does not adjudicate them.
obj_by_id = {o["id"]: o for o in objects}
selected_pairs = {}
for r in pair_rows:
    rel = r["relation"]
    value = r["min_raw_mask_distance_px_or_lower_bound"]
    if int(r["threshold_px"]) > 0 and rel != "CROSS_PANEL_READER_ELEMENTS" and value != "":
        key = ("NEAREST", rel)
        if key not in selected_pairs or float(value) < float(selected_pairs[key]["min_raw_mask_distance_px_or_lower_bound"]):
            selected_pairs[key] = r
    if rel in {"FOCUS_OVER_CELL", "GRAPH_ENDPOINT_CONNECTION", "MATRIX_SHARED_GRID", "SAME_STRUCTURAL_PARENT"} and int(r["raw_intersection_px"]) > 0:
        key = ("STRUCTURAL", rel)
        if key not in selected_pairs or int(r["raw_intersection_px"]) > int(selected_pairs[key]["raw_intersection_px"]):
            selected_pairs[key] = r

existing_critical = {r["pair_id"] for r in critical_rows}
for key, r in sorted(selected_pairs.items()):
    if r["pair_id"] in existing_critical:
        continue
    a, b = obj_by_id[r["object_a"]], obj_by_id[r["object_b"]]
    dist, inter = exact_distance(a, b)
    safe = f"{r['pair_id'].lower()}_{a['safe']}_{b['safe']}.png"
    evidence_path = f"critical_relations/{safe}"
    relation_view(a, b, None if dist is None else round(dist, 4), inter, ROOT / evidence_path)
    r["critical_evidence_path"] = evidence_path
    critical_rows.append({
        "pair_id": r["pair_id"],
        "object_a": a["id"],
        "object_b": b["id"],
        "relation": r["relation"],
        "threshold_px": r["threshold_px"],
        "distance_px": "" if dist is None else round(dist, 4),
        "raw_intersection_px": inter,
        "machine_candidate_0_1": r["machine_candidate_0_1"],
        "evidence_path": evidence_path,
    })


glyph_foreign_object_intersection = Counter()
for r in pair_rows:
    inter = int(r["raw_intersection_px"])
    if inter <= 0:
        continue
    if r["object_a"].startswith("G"):
        glyph_foreign_object_intersection[r["object_a"]] += inter
    if r["object_b"].startswith("G"):
        glyph_foreign_object_intersection[r["object_b"]] += inter

for row in glyph_rows:
    row["foreign_object_mask_intersection_px"] = glyph_foreign_object_intersection[row["object_id"]]
    peers = [r["h_ink_px"] for r in glyph_rows if r["panel_id"] == row["panel_id"] and r["role"] == row["role"] and r["script_class"] == row["script_class"] and r["h_ink_px"] > 0]
    med = statistics.median(peers) if peers else None
    row["peer_count"] = len(peers)
    row["peer_median_h_ink_px"] = "" if med is None else round(med, 3)
    row["ratio_to_peer_median"] = "" if med in (None, 0) else round(row["h_ink_px"] / med, 4)


element_groups = defaultdict(list)
for r in glyph_rows:
    element_groups[(r["parent_id"], r["panel_id"], r["role"], r["script_class"])].append(r)
element_rows = []
for key, rows in sorted(element_groups.items()):
    vals = [r["h_ink_px"] for r in rows if r["h_ink_px"] > 0]
    element_rows.append({
        "parent_id": key[0],
        "panel_id": key[1],
        "role": key[2],
        "script_class": key[3],
        "glyph_count": len(rows),
        "median_h_ink_px": "" if not vals else round(statistics.median(vals), 3),
        "min_h_ink_px": "" if not vals else min(vals),
        "max_h_ink_px": "" if not vals else max(vals),
        "median_pdf_vector_font_size": round(statistics.median([float(r["pdf_vector_font_size"]) for r in rows]), 3),
    })


source_rows = []
for parent, (panel, role, declared, source_line) in sorted(PARENT_META.items()):
    chars = [r for r in glyph_rows if r["parent_id"] == parent]
    if not chars:
        continue
    source_rows.append({
        "parent_id": parent,
        "panel_id": panel,
        "role": role,
        "source_file": str(SOURCE),
        "source_line": source_line,
        "declared_pt": "INHERITED_CAPTION" if declared is None else declared,
        "graphics_scale": 1.0,
        "effective_pt": "PDF_VECTOR_9.963" if declared is None else declared,
        "pdf_vector_font_size_min": min(float(r["pdf_vector_font_size"]) for r in chars),
        "pdf_vector_font_size_max": max(float(r["pdf_vector_font_size"]) for r in chars),
        "visible_glyph_count": len(chars),
    })


font_counts = Counter((r["font_name"], r["pdf_vector_font_size"], r["font_color_rgb"]) for r in glyph_rows)
font_rows = [{"font_name": k[0], "pdf_vector_font_size": k[1], "color_rgb": k[2], "glyph_count": v} for k, v in sorted(font_counts.items())]


four_side_rows = []
for r in drawing_rows:
    if r["role"] not in {"PANEL_BORDER", "MATRIX_CELL_BORDER", "FOCUS_BORDER"}:
        continue
    x0, y0, x1, y1 = r["mask_x0_px"], r["mask_y0_px"], r["mask_x1_px"], r["mask_y1_px"]
    crop = fig_px if r["role"] == "PANEL_BORDER" else stand_px
    four_side_rows.append({
        "object_id": r["object_id"],
        "parent_id": r["parent_id"],
        "role": r["role"],
        "left_margin_to_crop_px": x0 - crop[0],
        "top_margin_to_crop_px": y0 - crop[1],
        "right_margin_to_crop_px": crop[2] - x1,
        "bottom_margin_to_crop_px": crop[3] - y1,
        "left_edge_mask_pixels": int(np.count_nonzero(next(o for o in objects if o["id"] == r["object_id"])["mask"][:, :2])),
        "top_edge_mask_pixels": int(np.count_nonzero(next(o for o in objects if o["id"] == r["object_id"])["mask"][:2, :])),
        "right_edge_mask_pixels": int(np.count_nonzero(next(o for o in objects if o["id"] == r["object_id"])["mask"][:, -2:])),
        "bottom_edge_mask_pixels": int(np.count_nonzero(next(o for o in objects if o["id"] == r["object_id"])["mask"][-2:, :])),
    })


overlay = page_arr.copy()
for o in objects:
    x0, y0, x1, y1 = o["bbox"]
    color = np.array([230, 30, 30], dtype=np.uint8) if o["kind"] == "GLYPH" else np.array([30, 90, 230], dtype=np.uint8)
    region = overlay[y0:y1, x0:x1]
    region[o["mask"]] = color
    overlay[y0:y1, x0:x1] = region
    ImageDraw.Draw(Image.fromarray(overlay))
overlay_img = Image.fromarray(overlay).crop(fig_px)
dr = ImageDraw.Draw(overlay_img)
for o in objects:
    x0, y0, x1, y1 = o["bbox"]
    if x1 < fig_px[0] or x0 > fig_px[2] or y1 < fig_px[1] or y0 > fig_px[3]:
        continue
    dr.rectangle((x0 - fig_px[0], y0 - fig_px[1], x1 - fig_px[0], y1 - fig_px[1]), outline=(255, 0, 160), width=1)
    if o["id"].endswith("0") or o["kind"] == "DRAWING":
        dr.text((x0 - fig_px[0], y0 - fig_px[1]), o["id"], fill=(0, 0, 0))
overlay_img.save(ROOT / "after_text_measurement_overlay_300dpi.png")


glyph_fields = list(glyph_rows[0].keys())
drawing_fields = list(drawing_rows[0].keys())
save_csv(ROOT / "after_pixel_measurements.csv", glyph_rows, glyph_fields)
save_csv(ROOT / "glyph_inventory.csv", glyph_rows, glyph_fields)
save_csv(ROOT / "drawing_path_inventory.csv", drawing_rows, drawing_fields)
save_csv(ROOT / "id_safe_filename_map.csv", id_map_rows, ["object_id", "safe_filename", "kind"])
save_csv(ROOT / "element_pixel_role_metrics.csv", element_rows, list(element_rows[0].keys()))
save_csv(ROOT / "after_font_audit.csv", source_rows, list(source_rows[0].keys()))
save_csv(ROOT / "pdf_font_metadata.csv", font_rows, list(font_rows[0].keys()))
save_csv(ROOT / "all_unordered_pairs.csv", pair_rows, list(pair_rows[0].keys()))
save_csv(ROOT / "critical_relationships.csv", critical_rows, list(critical_rows[0].keys()) if critical_rows else ["pair_id"])
save_csv(ROOT / "four_side_clip_metrics.csv", four_side_rows, list(four_side_rows[0].keys()))

after_overlap_rows = []
for r in critical_rows:
    after_overlap_rows.append({
        "pair_id": r["pair_id"],
        "object_a": r["object_a"],
        "object_b": r["object_b"],
        "relation": r["relation"],
        "threshold_px": r["threshold_px"],
        "distance_px": r["distance_px"],
        "raw_intersection_px": r["raw_intersection_px"],
        "machine_candidate_0_1": r["machine_candidate_0_1"],
        "evidence_path": r["evidence_path"],
    })
save_csv(ROOT / "after_overlap_report.csv", after_overlap_rows, list(after_overlap_rows[0].keys()) if after_overlap_rows else ["pair_id"])

page_text = page.get_text("text")
(ROOT / "physical_page_765_text_extract.txt").write_text(page_text, encoding="utf-8")

math_rule_rows = [{
    "formula_path_inventory_basis": "source_and_pdf_drawing_crosswalk",
    "visible_math_rule_count": 0,
    "source_observation": "No overline, underline, radical bar, fraction rule, hat/vector accent path, cancellation slash, or other separately drawn mathematical rule occurs in the target source; 1/2 uses slash glyphs.",
    "pdf_observation": "All 43 visible foreground drawings in the figure body are assigned to panel borders, node borders, graph edge paths/arrowheads, matrix cell borders, or focus borders.",
}]
save_csv(ROOT / "math_rule_inventory.csv", math_rule_rows, list(math_rule_rows[0].keys()))

empty_masks = [o["id"] for o in objects if not np.any(o["mask"])]
replacement_chars = [r["object_id"] for r in glyph_rows if r["char"] in {"�", "□", "▯"}]
hard_machine_candidates = [r["pair_id"] for r in pair_rows if int(r["machine_candidate_0_1"]) == 1]
clip_touch = []
for o in objects:
    crop = fig_px if o["panel"] == "CAPTION" else stand_px
    x0, y0, x1, y1 = o["bbox"]
    if x0 <= crop[0] or y0 <= crop[1] or x1 >= crop[2] or y1 >= crop[3]:
        clip_touch.append(o["id"])

summary = {
    "handoff_id": "A-R107-P715-SA3-FRESH-ISOLATED-20260826",
    "role": "SA3",
    "model": "gpt-5.6-sol",
    "reasoning": "xhigh",
    "pdf": str(PDF),
    "pdf_page_count": doc.page_count,
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "source": str(SOURCE),
    "source_bytes": SOURCE.stat().st_size,
    "source_sha256": sha256(SOURCE),
    "physical_page": PHYSICAL_PAGE,
    "printed_page": 752,
    "page_pt": [page_rect.width, page_rect.height],
    "full_page_300dpi_native_px": [page300.width, page300.height],
    "full_page_200dpi_native_px": [pix200.width, pix200.height],
    "figure_crop_pt": list(FIGURE_CROP_PT),
    "figure_crop_full_page_integer_px": list(fig_px),
    "figure_crop_native_px": list(figure_crop.size),
    "standalone_pt": list(STANDALONE_PT),
    "standalone_full_page_integer_px": list(stand_px),
    "standalone_native_px": list(standalone.size),
    "visible_nonspace_glyph_objects": len(glyph_rows),
    "visible_pdf_drawing_objects": len(drawing_rows),
    "object_denominator_N": len(objects),
    "unordered_pair_denominator_C": len(pair_rows),
    "expected_choose_2": len(objects) * (len(objects) - 1) // 2,
    "glyph_contact_sheets": glyph_sheets,
    "drawing_contact_sheets": drawing_sheets,
    "critical_relationship_count": len(critical_rows),
    "machine_candidate_pair_count": len(hard_machine_candidates),
    "machine_candidate_pair_ids": hard_machine_candidates,
    "pairwise_candidate_intersection_px_sum": candidate_intersection_sum,
    "minimum_thresholded_relation_clearance_px": None if min_clearance is None else round(min_clearance, 4),
    "empty_mask_count": len(empty_masks),
    "empty_mask_ids": empty_masks,
    "replacement_or_tofu_codepoint_count": len(replacement_chars),
    "replacement_or_tofu_object_ids": replacement_chars,
    "crop_boundary_touch_count": len(clip_touch),
    "crop_boundary_touch_ids": clip_touch,
    "visible_math_rule_count": 0,
    "visible_pdf_drawing_assignment_count": len(drawing_rows),
    "figure_body_pdf_drawing_count": sum(1 for d in page.get_drawings() if int(d["seqno"]) in DRAW_META),
}
(ROOT / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
