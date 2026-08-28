from __future__ import annotations

import csv
import json
import math
import os
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C01\fig_v5_c01_transition_graph.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P547-01\STRICT_R10_SA1_FRESH_R98_20260824")
RENDERS = ROOT / "renders"
CARDS = ROOT / "cards"
REPORTS = ROOT / "reports"
PAGE_INDEX = 590
DPI = 300

FIGURE_RECT = fitz.Rect(65, 295, 530, 423)
CAPTION_RECT = fitz.Rect(95, 423, 490, 443)
FIGURE_CAPTION_RECT = fitz.Rect(65, 295, 530, 443)
CONTEXT_RECT = fitz.Rect(55, 270, 540, 492)


def font(size: int = 16, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


FONT14 = font(14)
FONT16 = font(16)
FONT18 = font(18)
FONT18B = font(18, True)


def pdf_to_px_rect(rect: fitz.Rect, sx: float, sy: float, pad: int = 0):
    return (
        max(0, math.floor(rect.x0 * sx) - pad),
        max(0, math.floor(rect.y0 * sy) - pad),
        math.ceil(rect.x1 * sx) + pad,
        math.ceil(rect.y1 * sy) + pad,
    )


TEXT_DEFS = [
    ("T01", "LEFT_TITLE", "TITLE", (110, 298, 226, 316), 10.2, 32),
    ("T02", "LEFT_STATE_1", "NODE_LABEL", (124, 342, 137, 360), 10.2, 33),
    ("T03", "LEFT_STATE_2", "NODE_LABEL", (200, 342, 214, 360), 10.2, 34),
    ("T04", "LEFT_LOOP_07", "EDGE_LABEL", (74, 341, 95, 360), 11.6, 35),
    ("T05", "LEFT_LOOP_08", "EDGE_LABEL", (241, 341, 262, 360), 11.6, 36),
    ("T06", "LEFT_FOCUS_A12", "EDGE_LABEL_FOCUS", (143, 318, 194, 337), 11.6, 37),
    ("T07", "LEFT_BACK_A21", "EDGE_LABEL", (143, 360, 194, 377), 11.6, 38),
    ("T08", "LEFT_MATRIX", "FORMULA_MATRIX", (125, 375, 211, 405), 11.8, 41),
    ("T09", "LEFT_UPDATE_NOTE", "NOTE_FORMULA", (111, 406, 226, 423), 9.8, 42),
    ("T10", "BRIDGE_FORMULA", "FORMULA_BRIDGE", (269, 361, 313, 385), 12.0, 46),
    ("T11", "BRIDGE_PHYSICAL_EDGE", "NOTE_FORMULA", (229, 384, 352, 401), 11.6, 47),
    ("T12", "RIGHT_TITLE", "TITLE", (328, 298, 501, 316), 10.2, 52),
    ("T13", "RIGHT_STATE_1", "NODE_LABEL", (370, 342, 384, 360), 10.2, 53),
    ("T14", "RIGHT_STATE_2", "NODE_LABEL", (447, 342, 461, 360), 10.2, 54),
    ("T15", "RIGHT_LOOP_07", "EDGE_LABEL", (321, 341, 342, 360), 11.6, 55),
    ("T16", "RIGHT_LOOP_08", "EDGE_LABEL", (488, 341, 509, 360), 11.6, 56),
    ("T17", "RIGHT_FOCUS_P21", "EDGE_LABEL_FOCUS", (391, 318, 440, 337), 11.6, 57),
    ("T18", "RIGHT_BACK_P12", "EDGE_LABEL", (390, 360, 439, 377), 11.6, 58),
    ("T19", "RIGHT_MATRIX", "FORMULA_MATRIX", (372, 375, 458, 405), 11.8, 61),
    ("T20", "RIGHT_UPDATE_NOTE", "NOTE_FORMULA", (351, 406, 479, 423), 9.8, 62),
    ("T21", "CAPTION", "CAPTION", (96, 423, 487, 443), 10.0, 65),
]


# Candidate drawing-path indexes are local to the 71-path figure-region list.
GRAPHIC_DEFS = [
    ("V01", "LEFT_TITLE_EQ", "RELATION_EQ", [0, 1], 32),
    ("V02", "LEFT_TITLE_ARROW", "RELATION_ARROW", [2, 3], 32),
    ("V03", "LEFT_FOCUS_EQ", "RELATION_EQ", [15, 16], 37),
    ("V04", "LEFT_LOWER_EQ", "RELATION_EQ", [20, 21], 38),
    ("V05", "LEFT_MATRIX_EQ", "RELATION_EQ", [22, 23], 41),
    ("V06", "LEFT_NOTE_EQ", "RELATION_EQ", [28, 29], 42),
    ("V07", "BRIDGE_FORMULA_EQ", "RELATION_EQ", [31, 32], 46),
    ("V08", "BRIDGE_PHYSICAL_ARROW", "RELATION_ARROW", [33, 34], 47),
    ("V09", "BRIDGE_PHYSICAL_EQ", "RELATION_EQ", [35, 36], 47),
    ("V10", "RIGHT_TITLE_EQ", "RELATION_EQ", [41, 42], 52),
    ("V11", "RIGHT_TITLE_ARROW", "RELATION_ARROW", [43, 44], 52),
    ("V12", "RIGHT_FOCUS_EQ", "RELATION_EQ", [56, 57], 57),
    ("V13", "RIGHT_LOWER_EQ", "RELATION_EQ", [61, 62], 58),
    ("V14", "RIGHT_MATRIX_EQ", "RELATION_EQ", [63, 64], 61),
    ("V15", "RIGHT_NOTE_EQ", "RELATION_EQ", [69, 70], 62),
    ("V16", "LEFT_NODE_1_BORDER", "NODE_BORDER", [4], 33),
    ("V17", "LEFT_NODE_2_BORDER", "NODE_BORDER", [5], 34),
    ("V18", "LEFT_SELF_LOOP_1", "ARROW", [6, 7], 35),
    ("V19", "LEFT_LOOP_LABEL_PLATE_07", "BACKGROUND_PLATE", [8], 35),
    ("V20", "LEFT_SELF_LOOP_2", "ARROW", [9, 10], 36),
    ("V21", "LEFT_LOOP_LABEL_PLATE_08", "BACKGROUND_PLATE", [11], 36),
    ("V22", "LEFT_FORWARD_ARROW", "ARROW_FOCUS", [12, 13], 37),
    ("V23", "LEFT_FOCUS_LABEL_BOX", "BOX_BORDER", [14], 37),
    ("V24", "LEFT_BACK_ARROW", "ARROW", [17, 18], 38),
    ("V25", "LEFT_BACK_LABEL_PLATE", "BACKGROUND_PLATE", [19], 38),
    ("V26", "LEFT_MATRIX_HIGHLIGHT_BOX", "HIGHLIGHT_BORDER", [24, 25, 26, 27], 41),
    ("V27", "BRIDGE_BOX", "BOX_BORDER", [30], 45),
    ("V28", "BRIDGE_ARROW_LEFT", "ARROW_BRIDGE", [37, 38], 48),
    ("V29", "BRIDGE_ARROW_RIGHT", "ARROW_BRIDGE", [39, 40], 49),
    ("V30", "RIGHT_NODE_1_BORDER", "NODE_BORDER", [45], 53),
    ("V31", "RIGHT_NODE_2_BORDER", "NODE_BORDER", [46], 54),
    ("V32", "RIGHT_SELF_LOOP_1", "ARROW", [47, 48], 55),
    ("V33", "RIGHT_LOOP_LABEL_PLATE_07", "BACKGROUND_PLATE", [49], 55),
    ("V34", "RIGHT_SELF_LOOP_2", "ARROW", [50, 51], 56),
    ("V35", "RIGHT_LOOP_LABEL_PLATE_08", "BACKGROUND_PLATE", [52], 56),
    ("V36", "RIGHT_FORWARD_ARROW", "ARROW_FOCUS", [53, 54], 57),
    ("V37", "RIGHT_FOCUS_LABEL_BOX", "BOX_BORDER", [55], 57),
    ("V38", "RIGHT_BACK_ARROW", "ARROW", [58, 59], 58),
    ("V39", "RIGHT_BACK_LABEL_PLATE", "BACKGROUND_PLATE", [60], 58),
    ("V40", "RIGHT_MATRIX_HIGHLIGHT_BOX", "HIGHLIGHT_BORDER", [65, 66, 67, 68], 61),
]


RELATION_PARENT = {
    "V01": "T01", "V02": "T01", "V03": "T06", "V04": "T07",
    "V05": "T08", "V06": "T09", "V07": "T10", "V08": "T11",
    "V09": "T11", "V10": "T12", "V11": "T12", "V12": "T17",
    "V13": "T18", "V14": "T19", "V15": "T20",
}


EXPLICIT_RELATIONS = {}


def relation(a, b, intent, note):
    EXPLICIT_RELATIONS[frozenset((a, b))] = (intent, note)


for vector, text in RELATION_PARENT.items():
    relation(vector, text, "INTENTIONAL_COMPOSITION", "custom geometric relation is part of this text formula")

for node, text in [("V16", "T02"), ("V17", "T03"), ("V30", "T13"), ("V31", "T14")]:
    relation(node, text, "INTENTIONAL_ENCLOSURE", "node border encloses its state label; 5 px ink-to-border clearance required")

for box, text in [("V23", "T06"), ("V26", "T08"), ("V27", "T10"), ("V27", "T11"),
                  ("V37", "T17"), ("V40", "T19")]:
    relation(box, text, "INTENTIONAL_ENCLOSURE", "border encloses associated text/formula; foreground ink must not touch border")

for box, relation_path in [("V23", "V03"), ("V27", "V07"), ("V27", "V08"), ("V27", "V09"), ("V37", "V12")]:
    relation(box, relation_path, "INTENTIONAL_ENCLOSURE", "border encloses the custom geometric relation belonging to its formula")

for plate, text in [("V19", "T04"), ("V21", "T05"), ("V25", "T07"),
                    ("V33", "T15"), ("V35", "T16"), ("V39", "T18")]:
    relation(plate, text, "BACKGROUND_BEHIND_LABEL", "opaque white label plate is behind text and is not foreground")

for plate, relation_path in [("V25", "V04"), ("V39", "V13")]:
    relation(plate, relation_path, "BACKGROUND_BEHIND_LABEL", "opaque plate is also behind the custom equals bars in the label")

for plate, arrow in [("V19", "V18"), ("V21", "V20"), ("V25", "V24"),
                     ("V33", "V32"), ("V35", "V34"), ("V39", "V38")]:
    relation(plate, arrow, "INTENTIONAL_OCCLUSION", "label plate masks the underlying edge before the label is painted")

for arrow, label in [("V18", "T04"), ("V20", "T05"), ("V22", "T06"), ("V24", "T07"),
                     ("V32", "T15"), ("V34", "T16"), ("V36", "T17"), ("V38", "T18")]:
    relation(arrow, label, "ASSOCIATED_BUT_DISJOINT", "edge and assigned label must retain foreground clearance")

for arrow, box in [("V22", "V23"), ("V36", "V37")]:
    relation(arrow, box, "ASSOCIATED_BUT_DISJOINT", "focus edge passes below its label box")

for arrow, node in [
    ("V18", "V16"), ("V20", "V17"),
    ("V22", "V16"), ("V22", "V17"), ("V24", "V17"), ("V24", "V16"),
    ("V32", "V30"), ("V34", "V31"),
    ("V36", "V30"), ("V36", "V31"), ("V38", "V31"), ("V38", "V30"),
]:
    relation(arrow, node, "INTENTIONAL_ENDPOINT_CONTACT", "directed edge terminates on the node boundary; no penetration into label area")

for arrow in ["V28", "V29"]:
    relation(arrow, "V27", "INTENTIONAL_ENDPOINT_CONTACT", "bridge arrow terminates at the bridge box boundary")


def union_rect(rects):
    # fitz.Rect.include_rect ignores empty zero-height line rectangles.  Relation
    # glyphs contain exactly such paths, so aggregate numeric extrema explicitly.
    return fitz.Rect(
        min(r.x0 for r in rects), min(r.y0 for r in rects),
        max(r.x1 for r in rects), max(r.y1 for r in rects),
    )


def draw_primitive(page, primitive, include_fill):
    shape = page.new_shape()
    for item in primitive["items"]:
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
    color = primitive.get("color")
    fill = primitive.get("fill") if include_fill else None
    if color is None and fill is None:
        return
    line_cap = primitive.get("lineCap", (0, 0, 0))
    if isinstance(line_cap, (tuple, list)):
        line_cap = max(line_cap)
    shape.finish(
        color=color,
        fill=fill,
        width=primitive.get("width") or 0,
        lineCap=line_cap or 0,
        lineJoin=primitive.get("lineJoin") or 0,
        closePath=bool(primitive.get("closePath")),
        dashes=primitive.get("dashes"),
    )
    shape.commit()


def render_graphic_mask(page_rect, primitives, indexes, role, width_px, height_px):
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    include_fill = role in {"ARROW", "ARROW_FOCUS", "ARROW_BRIDGE", "RELATION_ARROW", "BACKGROUND_PLATE"}
    for index in indexes:
        draw_primitive(page, primitives[index], include_fill=include_fill)
    pix = page.get_pixmap(dpi=DPI, alpha=True)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.width != width_px or pix.height != height_px:
        raise RuntimeError("Graphic-mask render dimensions differ from canonical render")
    mask = arr[:, :, 3] >= 20
    doc.close()
    return mask


def tight_mask(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0), np.zeros((0, 0), dtype=bool)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return (x0, y0, x1, y1), mask[y0:y1, x0:x1].copy()


def mode_background(patch):
    flat = patch.reshape(-1, 3)
    quant = (flat // 8) * 8
    counts = Counter(map(tuple, quant.tolist()))
    q = np.array(counts.most_common(1)[0][0], dtype=np.int16)
    candidates = flat[np.all(quant == q, axis=1)]
    return np.median(candidates, axis=0).astype(np.int16)


def glyph_class(character, raw_size_bp, declared_pt):
    category = unicodedata.category(character)
    inferred_tex_pt = raw_size_bp * 72.27 / 72.0
    if inferred_tex_pt < declared_pt * 0.86:
        return "SCRIPT", 15
    cp = ord(character)
    name = unicodedata.name(character, "")
    if category.startswith("P") or character in {"/", "|"}:
        return "PUNCT_CONTEXT", 1
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK_FULL", 30
    if character.islower() or "SMALL" in name:
        return "XHEIGHT_LOWER_GREEK", 17
    if character.isdigit() or ("A" <= character <= "Z") or 0x1D400 <= cp <= 0x1D7FF and "CAPITAL" in name:
        return "LATIN_CAP_DIGIT", 24
    if category.startswith("S") or character in "[]=()+-":
        return "MATH_SYMBOL", 22
    return "GENERAL_GLYPH", 17


def mask_intersection(a, b):
    ax0, ay0, ax1, ay1 = a["mask_bbox"]
    bx0, by0, bx1, by1 = b["mask_bbox"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0 or not a["mask"].size or not b["mask"].size:
        return 0
    am = a["mask"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bm = b["mask"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(am & bm))


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def bbox_overlap_area(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def mask_points(obj):
    if not obj["mask"].size:
        return np.empty((0, 2), dtype=np.int32)
    ys, xs = np.where(obj["mask"])
    x0, y0, _, _ = obj["mask_bbox"]
    return np.column_stack((xs + x0, ys + y0))


def closest_clearance(a, b, lower_bound):
    if lower_bound > 30:
        return float(lower_bound), None, None, "BBOX_LOWER_BOUND"
    pa = mask_points(a)
    pb = mask_points(b)
    if not len(pa) or not len(pb):
        return float(lower_bound), None, None, "BBOX_FOR_NONFOREGROUND"
    try:
        from scipy.spatial import cKDTree
        if len(pa) <= len(pb):
            dist, idx = cKDTree(pb).query(pa, k=1)
            k = int(np.argmin(dist))
            p1, p2, center_dist = pa[k], pb[int(idx[k])], float(dist[k])
        else:
            dist, idx = cKDTree(pa).query(pb, k=1)
            k = int(np.argmin(dist))
            p1, p2, center_dist = pa[int(idx[k])], pb[k], float(dist[k])
        return max(0.0, center_dist - 1.0), tuple(map(int, p1)), tuple(map(int, p2)), "PIXEL_EXACT"
    except Exception:
        return float(lower_bound), None, None, "BBOX_FALLBACK"


def required_clearance(a, b, intent):
    if intent in {"INTENTIONAL_ENDPOINT_CONTACT", "INTENTIONAL_OCCLUSION", "BACKGROUND_BEHIND_LABEL"}:
        return 0
    roles = {a["role"], b["role"]}
    kinds = {a["kind"], b["kind"]}
    if "BACKGROUND_PLATE" in roles:
        return 0
    if kinds == {"TEXT"}:
        return 4
    if "TEXT" in kinds:
        graphic = b if a["kind"] == "TEXT" else a
        if graphic["role"] in {"NODE_BORDER", "BOX_BORDER"} and intent == "INTENTIONAL_ENCLOSURE":
            return 5
        if graphic["role"] == "HIGHLIGHT_BORDER" and intent == "INTENTIONAL_ENCLOSURE":
            return 3
        if graphic["role"] == "BACKGROUND_PLATE":
            return 0
        if graphic["role"].startswith("RELATION_") and intent == "INTENTIONAL_COMPOSITION":
            return 0
        return 3
    if intent == "INTENTIONAL_ENCLOSURE":
        return 3
    if roles & {"ARROW", "ARROW_FOCUS", "ARROW_BRIDGE"}:
        return 2
    return 1


def make_glyph_card(page_img, row, path):
    x0, y0, x1, y1 = [int(row[k]) for k in ("PX_X0", "PX_Y0", "PX_X1", "PX_Y1")]
    crop = page_img.crop((x0, y0, x1, y1))
    ix0, iy0, ix1, iy1 = [int(row[k]) for k in ("INK_PX_X0", "INK_PX_Y0", "INK_PX_X1", "INK_PX_Y1")]
    ink_crop = page_img.crop((ix0, iy0, ix1, iy1))
    zoom = ink_crop.resize((ink_crop.width * 8, ink_crop.height * 8), Image.Resampling.NEAREST)
    card = Image.new("RGB", (440, 610), "white")
    d = ImageDraw.Draw(card)
    d.text((10, 8), f"{row['GLYPH_ID']}  {row['ELEMENT_ID']}  U+{ord(row['CHAR']):04X}", fill="black", font=FONT16)
    d.text((10, 30), f"1x raw bbox {crop.width}x{crop.height}; full ink 8x {zoom.width}x{zoom.height}", fill="black", font=FONT14)
    d.rectangle((9, 52, 84, 127), outline=(160, 160, 160))
    card.paste(crop, (14, 57))
    d.text((100, 57), "native 1x full raw glyph bbox", fill="black", font=FONT14)
    if zoom.width > 420 or zoom.height > 420:
        raise RuntimeError(f"Full 8x glyph does not fit card: {row['GLYPH_ID']} {zoom.size}")
    d.text((10, 132), "native full-ink 8x (nearest-neighbor, no crop/no resize)", fill="black", font=FONT14)
    card.paste(zoom, ((440-zoom.width)//2, 158))
    d.text((10, 585), f"H_ink={row['H_INK_PX']} threshold={row['THRESHOLD_PX']} {row['PASS_FAIL']}", fill="black", font=FONT14)
    card.save(path)
    crop.save(path.with_name(path.stem.replace("_card_1x_8x", "_1x_full_bbox") + ".png"))
    zoom.save(path.with_name(path.stem.replace("_card_1x_8x", "_8x_full_ink") + ".png"))


def make_graphic_card(page_img, obj, path):
    x0, y0, x1, y1 = obj["bbox_px"]
    pad = 4
    crop = page_img.crop((max(0, x0-pad), max(0, y0-pad), min(page_img.width, x1+pad), min(page_img.height, y1+pad)))
    card = Image.new("RGB", (620, 600), "white")
    d = ImageDraw.Draw(card)
    d.text((10, 8), f"{obj['id']}  {obj['name']}", fill="black", font=FONT18B)
    d.text((10, 32), f"{obj['role']}  primitives={','.join(map(str,obj['primitive_indexes']))}", fill="black", font=FONT14)
    full = crop
    if full.width > 600 or full.height > 220:
        raise RuntimeError(f"Native 1x graphic does not fit card: {obj['id']} {full.size}")
    d.text((10, 52), "1x native full object below (no resize)", fill="black", font=FONT14)
    card.paste(full, (20, 75))
    # Three native 8x windows are centered on actual object-mask pixels:
    # first extent, centroid-nearest ink, and last extent.  This prevents a node
    # card from sampling only its empty bbox corners or its text-filled center.
    display_mask = obj["display_mask"]
    mx0, my0, _, _ = obj["display_mask_bbox"]
    ys, xs = np.where(display_mask)
    if len(xs):
        gx = xs + mx0; gy = ys + my0
        score = gx + gy
        k1, k3 = int(np.argmin(score)), int(np.argmax(score))
        cx, cy = float(gx.mean()), float(gy.mean())
        k2 = int(np.argmin((gx-cx)**2 + (gy-cy)**2))
        anchors = [(int(gx[k1]),int(gy[k1])),(int(gx[k2]),int(gy[k2])),(int(gx[k3]),int(gy[k3]))]
    else:
        anchors = [(x0, y0), ((x0+x1)//2, (y0+y1)//2), (x1-1, y1-1)]
    for idx, (cx, cy) in enumerate(anchors):
        half = 12
        tile = page_img.crop((max(0, cx-half), max(0, cy-half), min(page_img.width, cx+half), min(page_img.height, cy+half)))
        tile8 = tile.resize((tile.width*8, tile.height*8), Image.Resampling.NEAREST)
        if tile8.width > 184 or tile8.height > 184:
            tile8 = tile8.crop((0, 0, min(184, tile8.width), min(184, tile8.height)))
        px = 10 + idx*196
        d.text((px, 320), f"8x tile {idx+1}", fill="black", font=FONT14)
        card.paste(tile8, (px, 342))
    d.text((10, 575), "All 8x tiles are nearest-neighbor; no resize after 8x.", fill="black", font=FONT14)
    card.save(path)
    crop.save(path.with_name(path.stem.replace("_card", "_1x") + ".png"))


def compose_sheets(paths, out_dir, prefix, cell_size, cols, rows):
    out_dir.mkdir(parents=True, exist_ok=True)
    per = cols * rows
    sheets = []
    for start in range(0, len(paths), per):
        subset = paths[start:start+per]
        sheet = Image.new("RGB", (cell_size[0]*cols, cell_size[1]*rows), (235, 235, 235))
        for k, path in enumerate(subset):
            img = Image.open(path).convert("RGB")
            if img.size != cell_size:
                raise RuntimeError(f"Card size mismatch: {path} {img.size} != {cell_size}")
            sheet.paste(img, ((k % cols)*cell_size[0], (k // cols)*cell_size[1]))
        out = out_dir / f"{prefix}_{len(sheets)+1:02d}.png"
        sheet.save(out)
        sheets.append(out)
    return sheets


def colorblind_simulation(img, matrix):
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    out = arr @ np.asarray(matrix, dtype=np.float32).T
    return Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255))


def main():
    for directory in [RENDERS, CARDS / "glyph", CARDS / "graphic", CARDS / "pair", CARDS / "sheets", REPORTS]:
        directory.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF)
    if doc.page_count != 813:
        raise RuntimeError(f"Expected 813 pages, got {doc.page_count}")
    page = doc[PAGE_INDEX]
    pix = page.get_pixmap(dpi=DPI, alpha=False)
    page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    canonical_path = RENDERS / "page_591_mupdf_300dpi.png"
    page_img.save(canonical_path)
    sx, sy = pix.width / page.rect.width, pix.height / page.rect.height

    page_img.crop(pdf_to_px_rect(FIGURE_CAPTION_RECT, sx, sy)).save(RENDERS / "figure_crop_with_caption_300dpi.png")
    figure_img = page_img.crop(pdf_to_px_rect(FIGURE_RECT, sx, sy))
    figure_img.save(RENDERS / "standalone_figure_300dpi.png")
    page_img.crop(pdf_to_px_rect(CONTEXT_RECT, sx, sy)).save(RENDERS / "figure_context_300dpi.png")
    Image.fromarray(np.asarray(figure_img.convert("L"))).save(RENDERS / "standalone_figure_gray_300dpi.png")

    protan = [[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]]
    deutan = [[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]]
    tritan = [[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]
    colorblind_simulation(figure_img, protan).save(RENDERS / "standalone_figure_protanopia_300dpi.png")
    colorblind_simulation(figure_img, deutan).save(RENDERS / "standalone_figure_deuteranopia_300dpi.png")
    colorblind_simulation(figure_img, tritan).save(RENDERS / "standalone_figure_tritanopia_300dpi.png")

    drawings = []
    for d in page.get_drawings(extended=True):
        r = d["rect"]
        if r.x1 >= FIGURE_RECT.x0 and r.x0 <= FIGURE_RECT.x1 and r.y1 >= FIGURE_RECT.y0 and r.y0 <= FIGURE_RECT.y1:
            drawings.append(d)
    if len(drawings) != 71:
        raise RuntimeError(f"Expected 71 figure vector primitives, got {len(drawings)}")

    used_primitives = [i for _, _, _, indexes, _ in GRAPHIC_DEFS for i in indexes]
    if sorted(used_primitives) != list(range(71)):
        raise RuntimeError("Graphic definitions do not partition primitive indexes 0..70 exactly once")

    objects = []
    graphic_masks_global = []
    for gid, name, role, indexes, source_line in GRAPHIC_DEFS:
        rect = union_rect([drawings[i]["rect"] for i in indexes])
        mask_global = render_graphic_mask(page.rect, drawings, indexes, role, pix.width, pix.height)
        mask_bbox, local_mask = tight_mask(mask_global)
        del mask_global
        display_mask = local_mask.copy()
        if role == "BACKGROUND_PLATE":
            # The plate participates in occlusion-order review, but its white fill is background,
            # not an independent foreground mask under section 9.2.1-F.
            local_mask = np.zeros_like(local_mask)
        bbox_px = pdf_to_px_rect(rect, sx, sy, pad=2)
        object_row = {
            "id": gid, "name": name, "kind": "GRAPHIC", "role": role,
            "source_line": source_line, "bbox_pdf": tuple(rect), "bbox_px": bbox_px,
            "primitive_indexes": indexes, "mask_bbox": mask_bbox, "mask": local_mask,
            "display_mask_bbox": mask_bbox, "display_mask": display_mask,
        }
        objects.append(object_row)
        if role != "BACKGROUND_PLATE" and local_mask.size:
            graphic_masks_global.append(object_row)

    raw_chars = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    rect = fitz.Rect(ch["bbox"])
                    if rect.x1 >= FIGURE_CAPTION_RECT.x0 and rect.x0 <= FIGURE_CAPTION_RECT.x1 and rect.y1 >= FIGURE_CAPTION_RECT.y0 and rect.y0 <= FIGURE_CAPTION_RECT.y1 and not ch["c"].isspace():
                        raw_chars.append({"char": ch["c"], "rect": rect, "raw_size_bp": span["size"], "font": span["font"]})
    if len(raw_chars) != 193:
        raise RuntimeError(f"Expected 193 non-space glyphs, got {len(raw_chars)}")

    def matching_text_def(rect):
        cx, cy = (rect.x0+rect.x1)/2, (rect.y0+rect.y1)/2
        matches = [d for d in TEXT_DEFS if fitz.Rect(d[3]).contains(fitz.Point(cx, cy))]
        if len(matches) != 1:
            raise RuntimeError(f"Glyph center {cx,cy} assigned to {len(matches)} text objects")
        return matches[0]

    page_arr = np.asarray(page_img)
    # Full-page union of graphic foreground masks, used to prevent custom paths from entering text masks.
    graphics_union = np.zeros((pix.height, pix.width), dtype=bool)
    for g in graphic_masks_global:
        x0, y0, x1, y1 = g["mask_bbox"]
        graphics_union[y0:y1, x0:x1] |= g["mask"]

    glyph_rows = []
    chars_by_text = {d[0]: [] for d in TEXT_DEFS}
    for idx, raw in enumerate(raw_chars, 1):
        tid, name, role, bbox, declared_pt, source_line = matching_text_def(raw["rect"])
        x0, y0, x1, y1 = pdf_to_px_rect(raw["rect"], sx, sy, pad=1)
        patch = page_arr[y0:y1, x0:x1]
        bg = mode_background(patch)
        diff = np.max(np.abs(patch.astype(np.int16) - bg[None, None, :]), axis=2)
        mask = diff >= 20
        mask &= ~graphics_union[y0:y1, x0:x1]
        ys, xs = np.where(mask)
        h_ink = int(ys.max() - ys.min() + 1) if len(ys) else 0
        ink_x0 = x0 + int(xs.min()) if len(xs) else x0
        ink_y0 = y0 + int(ys.min()) if len(ys) else y0
        ink_x1 = x0 + int(xs.max()) + 1 if len(xs) else x0 + 1
        ink_y1 = y0 + int(ys.max()) + 1 if len(ys) else y0 + 1
        script_class, threshold = glyph_class(raw["char"], raw["raw_size_bp"], declared_pt)
        passed = h_ink >= threshold
        row = {
            "GLYPH_ID": f"C{idx:03d}", "ELEMENT_ID": tid, "ELEMENT_NAME": name,
            "ROLE": role, "SOURCE_LINE": source_line, "CHAR": raw["char"],
            "UNICODE": f"U+{ord(raw['char']):04X}", "FONT": raw["font"],
            "DECLARED_BASE_PT": f"{declared_pt:.2f}", "GRAPHICS_SCALE": "1.0000",
            "RAW_PDF_SIZE_BP": f"{raw['raw_size_bp']:.4f}",
            "INFERRED_TEX_PT": f"{raw['raw_size_bp']*72.27/72.0:.4f}",
            "SCRIPT_CLASS": script_class, "PDF_X0": f"{raw['rect'].x0:.3f}", "PDF_Y0": f"{raw['rect'].y0:.3f}",
            "PDF_X1": f"{raw['rect'].x1:.3f}", "PDF_Y1": f"{raw['rect'].y1:.3f}",
            "PX_X0": x0, "PX_Y0": y0, "PX_X1": x1, "PX_Y1": y1,
            "INK_PX_X0": ink_x0, "INK_PX_Y0": ink_y0, "INK_PX_X1": ink_x1, "INK_PX_Y1": ink_y1,
            "BG_RGB": ",".join(map(str, bg.tolist())), "H_INK_PX": h_ink,
            "THRESHOLD_PX": threshold, "PASS_FAIL": "PASS" if passed else "FAIL",
            "REASON": "meets per-glyph class floor" if passed else "below per-glyph class floor",
        }
        glyph_rows.append(row)
        chars_by_text[tid].append((row, mask, (x0, y0, x1, y1)))

    for tid, name, role, bbox, declared_pt, source_line in TEXT_DEFS:
        items = chars_by_text[tid]
        if not items:
            raise RuntimeError(f"Text object {tid} has no glyphs")
        px_bbox = pdf_to_px_rect(fitz.Rect(bbox), sx, sy, pad=1)
        x0, y0, x1, y1 = px_bbox
        local = np.zeros((y1-y0, x1-x0), dtype=bool)
        for row, mask, (cx0, cy0, cx1, cy1) in items:
            ix0, iy0, ix1, iy1 = max(x0,cx0),max(y0,cy0),min(x1,cx1),min(y1,cy1)
            if ix1 > ix0 and iy1 > iy0:
                local[iy0-y0:iy1-y0, ix0-x0:ix1-x0] |= mask[iy0-cy0:iy1-cy0, ix0-cx0:ix1-cx0]
        objects.append({
            "id": tid, "name": name, "kind": "TEXT", "role": role, "source_line": source_line,
            "bbox_pdf": bbox, "bbox_px": px_bbox, "primitive_indexes": [],
            "mask_bbox": px_bbox, "mask": local, "declared_pt": declared_pt,
            "glyph_count": len(items), "text": "".join(i[0]["CHAR"] for i in items),
        })

    objects.sort(key=lambda o: o["id"])
    if len(objects) != 61 or len({o["id"] for o in objects}) != 61:
        raise RuntimeError("Semantic object denominator must be exactly N=61")

    # Raw inventories.
    with (REPORTS / "glyph_inventory_193.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(glyph_rows[0].keys()))
        writer.writeheader(); writer.writerows(glyph_rows)

    font_rows = []
    for tid, name, role, bbox, declared_pt, source_line in TEXT_DEFS:
        rows = [r for r in glyph_rows if r["ELEMENT_ID"] == tid]
        inferred = [float(r["INFERRED_TEX_PT"]) for r in rows if r["SCRIPT_CLASS"] != "SCRIPT"]
        min_base = min(inferred) if inferred else declared_pt
        font_rows.append({
            "ELEMENT_ID":tid,"NAME":name,"ROLE":role,"SOURCE_FILE":str(SOURCE),"SOURCE_LINE":source_line,
            "DECLARED_PT":f"{declared_pt:.2f}","GRAPHICS_SCALE":"1.0000","EFFECTIVE_PT":f"{declared_pt:.2f}",
            "MIN_INFERRED_NON_SCRIPT_TEX_PT":f"{min_base:.3f}","GLYPH_COUNT":len(rows),
            "PASS_FAIL":"PASS" if declared_pt >= 9.5 and min_base >= 9.45 else "FAIL",
            "REASON":"no outer resize; PDF bp is TeX pt x 72/72.27; base >=9.5pt",
        })
    with (REPORTS / "font_audit_21_elements.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(font_rows[0].keys())); writer.writeheader(); writer.writerows(font_rows)

    primitive_rows=[]
    reverse={i:gid for gid,_,_,idxs,_ in GRAPHIC_DEFS for i in idxs}
    for i,d in enumerate(drawings):
        primitive_rows.append({
            "PRIMITIVE_INDEX":i,"SEMANTIC_GRAPHIC_ID":reverse[i],"TYPE":d.get("type"),
            "RECT_X0":f"{d['rect'].x0:.3f}","RECT_Y0":f"{d['rect'].y0:.3f}","RECT_X1":f"{d['rect'].x1:.3f}","RECT_Y1":f"{d['rect'].y1:.3f}",
            "STROKE":str(d.get("color")),"FILL":str(d.get("fill")),"WIDTH_BP":d.get("width"),"ITEM_COUNT":len(d.get("items",[])),
        })
    with (REPORTS/"vector_primitive_inventory_71.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(primitive_rows[0].keys())); w.writeheader(); w.writerows(primitive_rows)

    object_rows=[]
    for o in objects:
        object_rows.append({
            "OBJECT_ID":o["id"],"NAME":o["name"],"KIND":o["kind"],"ROLE":o["role"],"SOURCE_LINE":o["source_line"],
            "BBOX_PDF":";".join(f"{v:.3f}" for v in o["bbox_pdf"]),"BBOX_PX":";".join(map(str,o["bbox_px"])),
            "GLYPH_COUNT":o.get("glyph_count",0),"PRIMITIVE_INDEXES":";".join(map(str,o["primitive_indexes"])),
            "FOREGROUND_MASK_PIXELS":int(np.count_nonzero(o["mask"])),"TEXT":o.get("text","")
        })
    with (REPORTS/"semantic_object_inventory_N61.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(object_rows[0].keys())); w.writeheader(); w.writerows(object_rows)

    # Cards and sheets.
    glyph_card_paths=[]
    for row in glyph_rows:
        out=CARDS/"glyph"/f"{row['GLYPH_ID']}_{row['ELEMENT_ID']}_card_1x_8x.png"
        make_glyph_card(page_img,row,out); glyph_card_paths.append(out)
    glyph_sheets=compose_sheets(glyph_card_paths,CARDS/"sheets","glyph_cards_open_sheet",(440,610),3,3)

    graphic_card_paths=[]
    for o in [x for x in objects if x["kind"]=="GRAPHIC"]:
        out=CARDS/"graphic"/f"{o['id']}_card_1x_8x.png"
        make_graphic_card(page_img,o,out); graphic_card_paths.append(out)
    graphic_sheets=compose_sheets(graphic_card_paths,CARDS/"sheets","graphic_cards_open_sheet",(620,600),2,3)

    # All-pairs exact denominator and classification.
    pairs=[]
    critical=[]
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            key=frozenset((a["id"],b["id"]))
            intent,note=EXPLICIT_RELATIONS.get(key,("INTENDED_DISJOINT","independent semantic objects must remain disjoint"))
            gap=bbox_gap(a["bbox_px"],b["bbox_px"])
            overlap=mask_intersection(a,b)
            clearance,p1,p2,method=closest_clearance(a,b,gap)
            required=required_clearance(a,b,intent)
            allowed_overlap=intent in {"INTENTIONAL_ENDPOINT_CONTACT","INTENTIONAL_OCCLUSION","BACKGROUND_BEHIND_LABEL"}
            illegal_overlap=0 if allowed_overlap else overlap
            pair_pass=illegal_overlap==0 and (clearance+1e-6>=required or allowed_overlap)
            bbox_area=bbox_overlap_area(a["bbox_px"],b["bbox_px"])
            row={
                "PAIR_ID":f"P{len(pairs)+1:04d}","OBJECT_A":a["id"],"OBJECT_B":b["id"],
                "A_ROLE":a["role"],"B_ROLE":b["role"],"SEMANTIC_INTENT":intent,"INTENT_NOTE":note,
                "BBOX_OVERLAP_AREA_PX":bbox_area,"BBOX_GAP_PX":f"{gap:.3f}","FOREGROUND_OVERLAP_PX":overlap,
                "ILLEGAL_OVERLAP_PX":illegal_overlap,"MIN_CLEARANCE_PX":f"{clearance:.3f}","CLEARANCE_METHOD":method,
                "REQUIRED_CLEARANCE_PX":required,"TOUCH_CLASS":"OVERLAP" if overlap else ("TOUCH" if clearance<0.5 else "SEPARATE"),
                "Z_ORDER_CLASS":"PLATE_OCCLUDES_EDGE" if intent=="INTENTIONAL_OCCLUSION" else ("BORDER/EDGE_CONTACT" if intent=="INTENTIONAL_ENDPOINT_CONTACT" else "NO_OCCLUSION"),
                "CLOSEST_A":str(p1),"CLOSEST_B":str(p2),"AUTOMATED_GATE":"PASS" if pair_pass else "FAIL",
                "MANUAL_REVIEW":"PENDING_SA1_OPEN_VIEW",
            }
            pairs.append(row)
            if bbox_area>0 or clearance<12 or intent!="INTENDED_DISJOINT" or not pair_pass:
                critical.append((row,a,b,p1,p2))
    if len(pairs)!=1830:
        raise RuntimeError(f"Expected 1830 pairs, got {len(pairs)}")
    with (REPORTS/"all_pairs_1830_DRAFT.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0].keys())); w.writeheader(); w.writerows(pairs)

    # Key pair pixel cards: local 1x neighborhood plus 8x nearest-neighbor tile.
    pair_paths=[]
    for row,a,b,p1,p2 in critical:
        if p1 and p2:
            cx=(p1[0]+p2[0])//2; cy=(p1[1]+p2[1])//2
        else:
            ix0=max(a["bbox_px"][0],b["bbox_px"][0]); iy0=max(a["bbox_px"][1],b["bbox_px"][1])
            ix1=min(a["bbox_px"][2],b["bbox_px"][2]); iy1=min(a["bbox_px"][3],b["bbox_px"][3])
            if ix1>ix0 and iy1>iy0: cx,cy=(ix0+ix1)//2,(iy0+iy1)//2
            else: cx,cy=(a["bbox_px"][0]+a["bbox_px"][2]+b["bbox_px"][0]+b["bbox_px"][2])//4,(a["bbox_px"][1]+a["bbox_px"][3]+b["bbox_px"][1]+b["bbox_px"][3])//4
        tile=page_img.crop((max(0,cx-22),max(0,cy-22),min(page_img.width,cx+22),min(page_img.height,cy+22)))
        tile8=tile.resize((tile.width*8,tile.height*8),Image.Resampling.NEAREST)
        card=Image.new("RGB",(380,420),"white"); d=ImageDraw.Draw(card)
        d.text((8,6),f"{row['PAIR_ID']} {a['id']} / {b['id']}",fill="black",font=FONT16)
        d.text((8,28),row["SEMANTIC_INTENT"][:42],fill="black",font=FONT14)
        d.text((8,48),f"ov={row['FOREGROUND_OVERLAP_PX']} illegal={row['ILLEGAL_OVERLAP_PX']} clr={row['MIN_CLEARANCE_PX']}",fill="black",font=FONT14)
        card.paste(tile,(10,76))
        z=tile8.crop((0,0,min(352,tile8.width),min(300,tile8.height)))
        card.paste(z,(14,116))
        out=CARDS/"pair"/f"{row['PAIR_ID']}_{a['id']}_{b['id']}_card.png"; card.save(out); pair_paths.append(out)
    pair_sheets=compose_sheets(pair_paths,CARDS/"sheets","critical_pair_cards_open_sheet",(380,420),3,4)

    # Bounding-box overlay.
    overlay=page_img.crop(pdf_to_px_rect(FIGURE_CAPTION_RECT,sx,sy)).copy()
    od=ImageDraw.Draw(overlay); ox,oy,_,_=pdf_to_px_rect(FIGURE_CAPTION_RECT,sx,sy)
    for o in objects:
        x0,y0,x1,y1=o["bbox_px"]; color=(220,30,30) if o["kind"]=="TEXT" else (20,80,220)
        od.rectangle((x0-ox,y0-oy,x1-ox,y1-oy),outline=color,width=2)
        od.text((x0-ox,max(0,y0-oy-14)),o["id"],fill=color,font=FONT14)
    overlay.save(RENDERS/"object_bbox_overlay_N61_300dpi.png")

    # Pair matrix: color encodes intent/clearance and exposes every one of 1,830 cells.
    ids=[o["id"] for o in objects]; pos={v:i for i,v in enumerate(ids)}; cell=18; margin=90
    matrix=Image.new("RGB",(margin+cell*61+10,margin+cell*61+10),"white"); md=ImageDraw.Draw(matrix)
    colors={"INTENDED_DISJOINT":(220,240,220),"INTENTIONAL_COMPOSITION":(185,220,255),"INTENTIONAL_ENCLOSURE":(210,190,250),
            "BACKGROUND_BEHIND_LABEL":(240,220,170),"INTENTIONAL_OCCLUSION":(250,190,140),"ASSOCIATED_BUT_DISJOINT":(180,235,235),"INTENTIONAL_ENDPOINT_CONTACT":(250,160,160)}
    for k,objid in enumerate(ids):
        md.text((margin+k*cell,4),str(k+1),fill="black",font=FONT14)
        md.text((4,margin+k*cell),f"{k+1}:{objid}",fill="black",font=FONT14)
    for row in pairs:
        i=pos[row["OBJECT_A"]]; j=pos[row["OBJECT_B"]]; c=colors.get(row["SEMANTIC_INTENT"],(210,210,210))
        if row["AUTOMATED_GATE"]=="FAIL": c=(255,0,255)
        for x,y in [(i,j),(j,i)]: md.rectangle((margin+x*cell,margin+y*cell,margin+(x+1)*cell-1,margin+(y+1)*cell-1),fill=c)
    for i in range(61): md.rectangle((margin+i*cell,margin+i*cell,margin+(i+1)*cell-1,margin+(i+1)*cell-1),fill=(80,80,80))
    matrix.save(RENDERS/"all_pairs_matrix_61x61.png")

    summary={
        "pdf":str(PDF),"source":str(SOURCE),"page_physical":591,"page_printed":578,"figure":"30.2","figure_id":"FIG-P547-01",
        "dpi":DPI,"page_pixels":[pix.width,pix.height],"glyph_count_nonspace":len(glyph_rows),"text_object_count":len(TEXT_DEFS),
        "vector_primitive_count":len(drawings),"graphic_object_count":len(GRAPHIC_DEFS),"semantic_object_N":len(objects),
        "all_pairs_n_choose_2":len(pairs),"critical_pair_card_count":len(pair_paths),"glyph_card_count":len(glyph_card_paths),
        "graphic_card_count":len(graphic_card_paths),"glyph_open_sheet_count":len(glyph_sheets),"graphic_open_sheet_count":len(graphic_sheets),
        "critical_pair_open_sheet_count":len(pair_sheets),"glyph_fail_count":sum(r["PASS_FAIL"]=="FAIL" for r in glyph_rows),
        "pair_automated_fail_count":sum(r["AUTOMATED_GATE"]=="FAIL" for r in pairs),
        "set_equalities":{
            "glyph_ids_equal_C001_to_C193":[r["GLYPH_ID"] for r in glyph_rows]==[f"C{i:03d}" for i in range(1,194)],
            "primitive_indexes_equal_0_to_70":sorted(used_primitives)==list(range(71)),
            "semantic_object_ids_unique_61":len({o["id"] for o in objects})==61,
            "pair_ids_equal_P0001_to_P1830":[r["PAIR_ID"] for r in pairs]==[f"P{i:04d}" for i in range(1,1831)],
        },
    }
    (REPORTS/"denominator_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    doc.close()


if __name__ == "__main__":
    main()
