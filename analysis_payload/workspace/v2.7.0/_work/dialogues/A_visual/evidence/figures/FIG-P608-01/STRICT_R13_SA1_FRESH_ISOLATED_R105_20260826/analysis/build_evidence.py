import csv
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R13_SA1_FRESH_ISOLATED_R105_20260826")
PAGE_PNG = ROOT / "page_661_300dpi_native.png"
FIGURE_PNG = ROOT / "figure_crop_300dpi.png"
ANALYSIS = ROOT / "analysis"
VIEWS = ROOT / "views"
MASKS = VIEWS / "masks"
CELLS = VIEWS / "contact_cells_1x"
SHEETS = VIEWS / "contact_sheets_8x"
REL = VIEWS / "critical_relations"
for d in (ANALYSIS, VIEWS, MASKS, CELLS, SHEETS, REL):
    d.mkdir(parents=True, exist_ok=True)
for stale_relation_view in REL.glob("REL-*.png"):
    stale_relation_view.unlink()

SCALE = 300.0 / 72.0
CROP_X, CROP_Y, CROP_W, CROP_H = 500, 930, 1460, 860
FIG_RECT_PT = fitz.Rect(120, 225, 465, 426)
page_rgb = np.array(Image.open(PAGE_PNG).convert("RGB"))
figure_rgb = np.array(Image.open(FIGURE_PNG).convert("RGB"))
assert tuple(figure_rgb.shape[:2]) == (CROP_H, CROP_W)


def rgb_from_int(value):
    return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], dtype=float)


def color_ray_mask(rgb, target, min_contrast=20, tolerance=16):
    """Pixels on the target-to-white antialias ray, with required visible contrast."""
    arr = rgb.astype(float)
    target = np.array(target, dtype=float)
    direction = target - 255.0
    denom = float(np.dot(direction, direction))
    alpha = np.sum((arr - 255.0) * direction, axis=2) / denom
    alpha = np.clip(alpha, 0.0, 1.0)
    predicted = 255.0 + alpha[:, :, None] * direction
    residual = np.sqrt(np.sum((arr - predicted) ** 2, axis=2))
    contrast = np.max(255.0 - arr, axis=2)
    return (contrast >= min_contrast) & (residual <= tolerance)


def union_color_masks(rgb, colors):
    # Assign each visible pixel to the closest known PDF palette ray first.
    # This prevents low-alpha gray hatch/text edges from being misassigned to
    # blue or dark geometry merely because every antialias ray converges at white.
    palette = [
        (31, 35, 40), (31, 78, 121), (107, 114, 128), (128, 128, 128),
        (183, 121, 31), (15, 118, 110), (184, 192, 200),
    ]
    arr = rgb.astype(float)
    residuals = []
    for target in palette:
        target = np.array(target, dtype=float)
        direction = target - 255.0
        denom = float(np.dot(direction, direction))
        alpha = np.sum((arr - 255.0) * direction, axis=2) / denom
        alpha = np.clip(alpha, 0.0, 1.0)
        predicted = 255.0 + alpha[:, :, None] * direction
        residuals.append(np.sqrt(np.sum((arr - predicted) ** 2, axis=2)))
    best = np.argmin(np.stack(residuals, axis=0), axis=0)
    accepted = {palette.index(tuple(int(v) for v in color)) for color in colors}
    contrast = np.max(255.0 - arr, axis=2)
    return (contrast >= 20) & np.isin(best, list(accepted))


def pt_rect_to_crop(rect, pad=0):
    x0 = max(0, math.floor(rect[0] * SCALE) - CROP_X - pad)
    y0 = max(0, math.floor(rect[1] * SCALE) - CROP_Y - pad)
    x1 = min(CROP_W, math.ceil(rect[2] * SCALE) - CROP_X + pad)
    y1 = min(CROP_H, math.ceil(rect[3] * SCALE) - CROP_Y + pad)
    return x0, y0, x1, y1


def pt_char_rect_to_crop(rect):
    # Shared PDF advance boundaries must map to one shared native-pixel edge;
    # floor/ceil on both neighbors would double-assign a raster column.
    x0 = max(0, round(rect[0] * SCALE) - CROP_X)
    y0 = max(0, math.floor(rect[1] * SCALE) - CROP_Y)
    x1 = min(CROP_W, round(rect[2] * SCALE) - CROP_X)
    y1 = min(CROP_H, math.ceil(rect[3] * SCALE) - CROP_Y)
    return x0, y0, x1, y1


def bbox_from_mask(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def safe_crop(arr, bbox, pad=4, fill=255):
    x0, y0, x1, y1 = bbox
    x0p, y0p = max(0, x0 - pad), max(0, y0 - pad)
    x1p, y1p = min(CROP_W, x1 + pad), min(CROP_H, y1 + pad)
    return arr[y0p:y1p, x0p:x1p].copy(), [x0p, y0p, x1p, y1p]


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parent_for_span(text, bbox):
    x0, y0, x1, y1 = bbox
    if y0 < 310:
        if x1 < 180 and y0 >= 245:
            if x0 < 150:
                return "P1_YLABEL"
            return f"P1_YTICK_{text}"
        if y0 < 246:
            return "P1_TITLE"
        if x0 < 305:
            return "P1_WARMUP_ANNOTATION"
        return "P1_RETAINED_ANNOTATION"
    if y0 < 334:
        return "P2_TITLE"
    if x0 > 400 and y0 < 350:
        return "P2_TARGET_ANNOTATION"
    if x1 < 150:
        return "P2_YLABEL"
    if x1 < 180 and y0 < 400:
        return f"P2_YTICK_{text}"
    if y0 >= 412:
        return "P2_XLABEL"
    if y0 >= 399:
        return f"P2_XTICK_{text}"
    return "P2_OTHER"


def panel_for_parent(parent):
    return "P1" if parent.startswith("P1") else "P2"


def glyph_class(ch, pdf_size):
    if pdf_size < 9.0:
        return "NATURAL_SCRIPT", 15
    if ch in {".", ",", "…", "，", "。", "、", ":", ";"}:
        return "LOW_PROFILE_PUNCTUATION", None
    if unicodedata.east_asian_width(ch) in {"W", "F"} and not ch.startswith("𝑋"):
        return "CJK_FULL", 30
    cat = unicodedata.category(ch)
    if ch.isdigit() or cat == "Lu" or ch == "𝑋":
        return "LATIN_CAPITAL_OR_DIGIT", 24
    if ch in {"=", "+", "−", "∶", "-"} or cat.startswith("S"):
        return "MATH_OPERATOR", 22
    return "LATIN_GREEK_LOWER", 17


doc = fitz.open(PDF)
page = doc[660]
raw = page.get_text("rawdict")
drawings_all = page.get_drawings()

glyph_rows = []
objects = []
object_masks = {}
glyph_seq = 0
spaces_excluded = 0
for block in raw.get("blocks", []):
    if block.get("type") != 0:
        continue
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            sb = span.get("bbox")
            if not sb or not FIG_RECT_PT.intersects(fitz.Rect(sb)):
                continue
            text = "".join(ch.get("c", "") for ch in span.get("chars", []))
            parent = parent_for_span(text, sb)
            expected = rgb_from_int(span.get("color", 0))
            for ch_info in span.get("chars", []):
                ch = ch_info.get("c", "")
                if not ch or ch.isspace():
                    spaces_excluded += 1
                    continue
                cb = ch_info.get("bbox")
                if not cb or not FIG_RECT_PT.intersects(fitz.Rect(cb)):
                    continue
                glyph_seq += 1
                gid = f"G{glyph_seq:03d}"
                x0, y0, x1, y1 = pt_char_rect_to_crop(cb)
                local = figure_rgb[y0:y1, x0:x1]
                local_mask = union_color_masks(local, [tuple(int(v) for v in expected)])
                mask = np.zeros((CROP_H, CROP_W), dtype=bool)
                mask[y0:y1, x0:x1] = local_mask
                ink_bbox = bbox_from_mask(mask)
                ink_h = 0 if ink_bbox is None else ink_bbox[3] - ink_bbox[1]
                ink_w = 0 if ink_bbox is None else ink_bbox[2] - ink_bbox[0]
                ink_area = int(mask.sum())
                klass, threshold = glyph_class(ch, float(span.get("size", 0)))
                row = {
                    "element_id": gid,
                    "safe_filename": gid,
                    "char": ch,
                    "unicode": f"U+{ord(ch):04X}",
                    "parent_id": parent,
                    "panel": panel_for_parent(parent),
                    "font": span.get("font"),
                    "pdf_size_pt": round(float(span.get("size", 0)), 3),
                    "source_effective_pt": 7.56 if float(span.get("size", 0)) < 9 else (10.8 if float(span.get("size", 0)) > 10 else 9.6),
                    "class": klass,
                    "threshold_px": "CALIBRATION" if threshold is None else threshold,
                    "pdf_bbox_pt": json.dumps([round(float(v), 3) for v in cb]),
                    "crop_bbox_px": json.dumps([x0, y0, x1, y1]),
                    "ink_bbox_px": json.dumps(ink_bbox),
                    "h_ink_px": ink_h,
                    "w_ink_px": ink_w,
                    "ink_area_px": ink_area,
                    "mask_file": f"views/masks/{gid}.png",
                }
                glyph_rows.append(row)
                object_masks[gid] = mask
                objects.append({
                    "object_id": gid,
                    "safe_filename": gid,
                    "kind": "GLYPH",
                    "subkind": klass,
                    "parent_id": parent,
                    "panel": panel_for_parent(parent),
                    "source_refs": gid,
                })


DRAW_DARK = (31, 35, 40)
DRAW_BLUE = (31, 78, 121)
DRAW_GRAY = (107, 114, 128)
DRAW_TICK_GRAY = (128, 128, 128)
DRAW_GOLD = (183, 121, 31)
DRAW_TEAL = (15, 118, 110)
DRAW_HATCH = (184, 192, 200)

group_specs = {
    "P1_AXES": {"indices": [6, 7, 8, 9, 10, 11], "colors": [DRAW_DARK, DRAW_TICK_GRAY], "index_colors": {6: [DRAW_TICK_GRAY], 7: [DRAW_TICK_GRAY]}, "panel": "P1", "subkind": "AXIS_TICK_ARROW"},
    "P1_CURVE_MARKERS": {"indices": [13] + list(range(19, 39)), "colors": [DRAW_BLUE, DRAW_DARK], "index_colors": {13: [DRAW_BLUE]}, "panel": "P1", "subkind": "DATA_CURVE_MARKERS"},
    "P1_WARMUP_BOUNDARY": {"indices": [14], "colors": [DRAW_GOLD], "panel": "P1", "subkind": "BOUNDARY_LINE"},
    "P1_EQ_WARMUP_TOP": {"indices": [15], "colors": [DRAW_GRAY], "panel": "P1", "subkind": "MATH_RULE"},
    "P1_EQ_WARMUP_BOTTOM": {"indices": [16], "colors": [DRAW_GRAY], "panel": "P1", "subkind": "MATH_RULE"},
    "P1_EQ_RETAIN_TOP": {"indices": [17], "colors": [DRAW_GRAY], "panel": "P1", "subkind": "MATH_RULE"},
    "P1_EQ_RETAIN_BOTTOM": {"indices": [18], "colors": [DRAW_GRAY], "panel": "P1", "subkind": "MATH_RULE"},
    "P2_AXES": {"indices": [39, 40, 41, 42, 43, 44], "colors": [DRAW_DARK, DRAW_TICK_GRAY], "index_colors": {39: [DRAW_TICK_GRAY], 40: [DRAW_TICK_GRAY]}, "panel": "P2", "subkind": "AXIS_TICK_ARROW"},
    "P2_CURVE_MARKERS": {"indices": [46] + list(range(49, 64)), "colors": [DRAW_BLUE, DRAW_DARK], "index_colors": {46: [DRAW_BLUE]}, "panel": "P2", "subkind": "DATA_CURVE_MARKERS"},
    "P2_WARMUP_BOUNDARY": {"indices": [47], "colors": [DRAW_GOLD], "panel": "P2", "subkind": "BOUNDARY_LINE"},
    "P2_TARGET_LINE": {"indices": [48], "colors": [DRAW_TEAL], "panel": "P2", "subkind": "REFERENCE_LINE"},
    "P2_YLABEL_OVERLINE": {"indices": [64], "colors": [DRAW_DARK], "panel": "P2", "subkind": "MATH_RULE"},
    "P2_TITLE_OVERLINE": {"indices": [65], "colors": [DRAW_DARK], "panel": "P2", "subkind": "MATH_RULE"},
}

drawing_path_rows = []
for i, d in enumerate(drawings_all):
    r = d.get("rect")
    if not r or not FIG_RECT_PT.intersects(r):
        continue
    mapped = [gid for gid, spec in group_specs.items() if i in spec["indices"]]
    drawing_path_rows.append({
        "drawing_index": i,
        "mapped_object_id": mapped[0] if mapped else "UNMAPPED",
        "rect_pt": json.dumps([round(r.x0, 3), round(r.y0, 3), round(r.x1, 3), round(r.y1, 3)]),
        "type": d.get("type"),
        "stroke": json.dumps(d.get("color")),
        "fill": json.dumps(d.get("fill")),
        "width_pt": d.get("width"),
        "item_count": len(d.get("items", [])),
    })

for group_id, spec in group_specs.items():
    mask = np.zeros((CROP_H, CROP_W), dtype=bool)
    for idx in spec["indices"]:
        d = drawings_all[idx]
        r = d.get("rect")
        if not r:
            continue
        x0, y0, x1, y1 = pt_rect_to_crop([r.x0, r.y0, r.x1, r.y1], pad=5)
        colors = spec.get("index_colors", {}).get(idx, spec["colors"])
        selected = union_color_masks(figure_rgb[y0:y1, x0:x1], colors)
        mask[y0:y1, x0:x1] |= selected
    object_masks[group_id] = mask
    parent = {
        "P1_EQ_WARMUP_TOP": "P1_WARMUP_ANNOTATION",
        "P1_EQ_WARMUP_BOTTOM": "P1_WARMUP_ANNOTATION",
        "P1_EQ_RETAIN_TOP": "P1_RETAINED_ANNOTATION",
        "P1_EQ_RETAIN_BOTTOM": "P1_RETAINED_ANNOTATION",
        "P2_YLABEL_OVERLINE": "P2_YLABEL",
        "P2_TITLE_OVERLINE": "P2_TITLE",
    }.get(group_id, group_id)
    objects.append({
        "object_id": group_id,
        "safe_filename": group_id,
        "kind": "GRAPHIC",
        "subkind": spec["subkind"],
        "parent_id": parent,
        "panel": spec["panel"],
        "source_refs": ";".join(str(v) for v in spec["indices"]),
    })

for group_id, region_pt, panel in [
    ("P1_HATCH", [189.0, 253.0, 252.2, 309.5], "P1"),
    ("P2_HATCH", [189.0, 340.0, 252.2, 396.5], "P2"),
]:
    mask = np.zeros((CROP_H, CROP_W), dtype=bool)
    x0, y0, x1, y1 = pt_rect_to_crop(region_pt, pad=1)
    mask[y0:y1, x0:x1] = union_color_masks(figure_rgb[y0:y1, x0:x1], [DRAW_HATCH])
    object_masks[group_id] = mask
    objects.append({
        "object_id": group_id,
        "safe_filename": group_id,
        "kind": "GRAPHIC",
        "subkind": "PATTERN_HATCH",
        "parent_id": group_id,
        "panel": panel,
        "source_refs": "PDF_TILING_PATTERN_RASTER_ACCOUNTING",
    })


def save_mask_and_cell(obj):
    oid = obj["object_id"]
    mask = object_masks[oid]
    bbox = bbox_from_mask(mask)
    if bbox is None:
        Image.new("L", (1, 1), 0).save(MASKS / f"{oid}.png")
        return None
    x0, y0, x1, y1 = bbox
    tight = (mask[y0:y1, x0:x1].astype(np.uint8) * 255)
    Image.fromarray(tight, "L").save(MASKS / f"{oid}.png")
    original, context_box = safe_crop(figure_rgb, bbox, pad=5)
    cx0, cy0, cx1, cy1 = context_box
    local_mask = mask[cy0:cy1, cx0:cx1]
    overlay = original.copy()
    overlay[local_mask] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(original, 255)
    mask_only[local_mask] = np.array([0, 0, 0], dtype=np.uint8)
    h, w = original.shape[:2]
    cell = Image.new("RGB", (w * 3 + 20, h + 24), "white")
    cell.paste(Image.fromarray(original), (0, 24))
    cell.paste(Image.fromarray(overlay), (w + 10, 24))
    cell.paste(Image.fromarray(mask_only), (2 * w + 20, 24))
    draw = ImageDraw.Draw(cell)
    draw.text((2, 2), f"{oid} | ORIGINAL / TARGET OVERLAY / MASK ONLY | native 1x", fill="black")
    cell.save(CELLS / f"{oid}.png")
    return bbox


for obj in objects:
    mask = object_masks[obj["object_id"]]
    bbox = save_mask_and_cell(obj)
    obj["bbox_px"] = json.dumps(bbox)
    obj["pixel_count"] = int(mask.sum())
    obj["mask_file"] = f"views/masks/{obj['object_id']}.png"
    if bbox is None:
        obj["clip_pixel_count"] = 0
        obj["edge_clearance_px"] = -1
    else:
        x0, y0, x1, y1 = bbox
        obj["clip_pixel_count"] = int(x0 <= 0 or y0 <= 0 or x1 >= CROP_W or y1 >= CROP_H)
        obj["edge_clearance_px"] = min(x0, y0, CROP_W - x1, CROP_H - y1)


def make_contact_sheets(review_objects):
    cell_images = []
    for obj in review_objects:
        oid = obj["object_id"]
        mask = object_masks[oid]
        bbox = bbox_from_mask(mask)
        if bbox is None:
            continue
        original, cb = safe_crop(figure_rgb, bbox, pad=3)
        cx0, cy0, cx1, cy1 = cb
        local_mask = mask[cy0:cy1, cx0:cx1]
        overlay = original.copy()
        overlay[local_mask] = [255, 0, 0]
        mask_only = np.full_like(original, 255)
        mask_only[local_mask] = [0, 0, 0]
        imgs = [Image.fromarray(v).resize((v.shape[1] * 8, v.shape[0] * 8), Image.Resampling.NEAREST) for v in (original, overlay, mask_only)]
        maxh = max(im.height for im in imgs)
        width = sum(im.width for im in imgs) + 20
        row = Image.new("RGB", (max(1260, width), maxh + 42), "white")
        draw = ImageDraw.Draw(row)
        char = next((g["char"] for g in glyph_rows if g["element_id"] == oid), "GRAPHIC/MATH_RULE")
        draw.text((4, 3), f"{oid} {char} | ORIGINAL 8x NN | TARGET OVERLAY 8x NN | MASK ONLY 8x NN", fill="black")
        x = 0
        for im in imgs:
            row.paste(im, (x, 38))
            x += im.width + 10
        cell_images.append((oid, row))
    index_rows = []
    for sheet_no in range(0, len(cell_images), 3):
        chunk = cell_images[sheet_no:sheet_no + 3]
        sheet_w = max(im.width for _, im in chunk)
        sheet_h = sum(im.height for _, im in chunk)
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        y = 0
        for cell_no, (oid, im) in enumerate(chunk, start=1):
            sheet.paste(im, (0, y))
            index_rows.append({"element_id": oid, "sheet": f"contact_sheet_{sheet_no // 3 + 1:02d}.png", "cell": cell_no})
            y += im.height
        sheet.save(SHEETS / f"contact_sheet_{sheet_no // 3 + 1:02d}.png")
    return index_rows


review_objects = [o for o in objects if o["kind"] == "GLYPH" or o["subkind"] == "MATH_RULE"]
contact_index = make_contact_sheets(review_objects)
contact_lookup = {r["element_id"]: r for r in contact_index}
for row in glyph_rows:
    row["contact_sheet"] = contact_lookup[row["element_id"]]["sheet"]
    row["contact_cell"] = contact_lookup[row["element_id"]]["cell"]


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.sqrt(dx * dx + dy * dy)


def exact_distance(mask_a, mask_b):
    ya, xa = np.nonzero(mask_a)
    yb, xb = np.nonzero(mask_b)
    if len(xa) == 0 or len(xb) == 0:
        return None
    a = np.column_stack([xa, ya])
    b = np.column_stack([xb, yb])
    if len(a) > len(b):
        a, b = b, a
    tree = cKDTree(b)
    dist, _ = tree.query(a, k=1)
    return float(np.min(dist))


def classify_pair(a, b):
    if a["parent_id"] == b["parent_id"]:
        return "SAME_SEMANTIC_PARENT_DESIGN", 0
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["panel"] != b["panel"]:
            return "CROSS_PANEL_READER_ELEMENTS", 8
        return "TEXT_TEXT_INDEPENDENT", 4
    if (a["kind"] == "GLYPH") != (b["kind"] == "GLYPH"):
        return "TEXT_GRAPHIC", 3
    if a["panel"] == b["panel"]:
        return "PLOT_GEOMETRY_DESIGN_RELATION", 0
    return "CROSS_PANEL_GRAPHICS", 0


obj_by_id = {o["object_id"]: o for o in objects}
pair_rows = []
critical_rows = []
ids = [o["object_id"] for o in objects]
for i, aid in enumerate(ids):
    a = obj_by_id[aid]
    ma = object_masks[aid]
    ba = bbox_from_mask(ma)
    for bid in ids[i + 1:]:
        b = obj_by_id[bid]
        mb = object_masks[bid]
        bb = bbox_from_mask(mb)
        relation, threshold = classify_pair(a, b)
        if ba is None or bb is None:
            overlap = -1
            clearance = None
            metric = "EMPTY_MASK"
        else:
            if bbox_gap(ba, bb) > 0:
                overlap = 0
            else:
                overlap = int(np.logical_and(ma, mb).sum())
            gap = bbox_gap(ba, bb)
            if overlap > 0:
                clearance = 0.0
                metric = "RAW_MASK_INTERSECTION"
            elif threshold > 0 and gap <= max(14, threshold + 3):
                clearance = exact_distance(ma, mb)
                metric = "RAW_MASK_EXACT_KDTREE"
            else:
                clearance = gap
                metric = "BBOX_GAP_LOWER_BOUND"
        row = {
            "pair_id": f"PAIR-{i + 1:03d}-{ids.index(bid) + 1:03d}",
            "object_a": aid,
            "object_b": bid,
            "relation_class": relation,
            "required_clearance_px": threshold,
            "overlap_pixel_count": overlap,
            "clearance_px": "" if clearance is None else round(clearance, 3),
            "metric": metric,
        }
        pair_rows.append(row)
        if threshold > 0 and clearance is not None and clearance <= 12:
            critical_rows.append(dict(row))

# Preserve every threshold-near relation, plus the nearest hard-gate
# counterexamples and every visible raw-mask contact (including intentional
# plot geometry contacts). This selection is numeric only; manual disposition
# is deliberately recorded later in a separately authored reviewer ledger.
selected_ids = {r["pair_id"] for r in critical_rows}
hard_candidates = [
    r for r in pair_rows
    if int(r["required_clearance_px"]) > 0 and r["clearance_px"] != ""
]
hard_candidates.sort(key=lambda r: float(r["clearance_px"]) - float(r["required_clearance_px"]))
for r in hard_candidates[:12]:
    if r["pair_id"] not in selected_ids:
        critical_rows.append(dict(r)); selected_ids.add(r["pair_id"])
for r in pair_rows:
    if int(r["overlap_pixel_count"]) > 0 and r["pair_id"] not in selected_ids:
        critical_rows.append(dict(r)); selected_ids.add(r["pair_id"])


def relation_evidence(row, seq):
    aid, bid = row["object_a"], row["object_b"]
    ma, mb = object_masks[aid], object_masks[bid]
    ba, bb = bbox_from_mask(ma), bbox_from_mask(mb)
    ya, xa = np.nonzero(ma)
    yb, xb = np.nonzero(mb)
    overlap_points = np.column_stack(np.nonzero(ma & mb))
    if len(overlap_points):
        cy, cx = overlap_points[len(overlap_points) // 2]
        pa = pb = np.array([int(cx), int(cy)])
    else:
        apts = np.column_stack([xa, ya])
        bpts = np.column_stack([xb, yb])
        tree = cKDTree(bpts)
        dist, nearest = tree.query(apts, k=1)
        k = int(np.argmin(dist))
        pa, pb = apts[k], bpts[int(nearest[k])]
    c = ((pa + pb) // 2).astype(int)
    half_w = max(18, int(abs(pa[0] - pb[0]) // 2) + 10)
    half_h = max(18, int(abs(pa[1] - pb[1]) // 2) + 10)
    x0, x1 = max(0, int(c[0]) - half_w), min(CROP_W, int(c[0]) + half_w + 1)
    y0, y1 = max(0, int(c[1]) - half_h), min(CROP_H, int(c[1]) + half_h + 1)
    orig = figure_rgb[y0:y1, x0:x1].copy()
    la, lb = ma[y0:y1, x0:x1], mb[y0:y1, x0:x1]
    overlay = orig.copy()
    overlay[la] = [255, 0, 0]
    overlay[lb] = [0, 0, 255]
    overlap = la & lb
    overlay[overlap] = [255, 0, 255]
    aonly = np.full_like(orig, 255); aonly[la] = [0, 0, 0]
    bonly = np.full_like(orig, 255); bonly[lb] = [0, 0, 0]
    inter = np.full_like(orig, 255); inter[overlap] = [0, 0, 0]
    panels = [orig, aonly, bonly, inter, overlay]
    labels = ["ORIGINAL", "A MASK", "B MASK", "INTERSECTION", "OVERLAY"]
    w, h = orig.shape[1], orig.shape[0]
    sheet = Image.new("RGB", (w * 5, h + 24), "white")
    draw = ImageDraw.Draw(sheet)
    for j, (panel, label) in enumerate(zip(panels, labels)):
        sheet.paste(Image.fromarray(panel), (j * w, 24))
        draw.text((j * w + 2, 2), label, fill="black")
    stem = f"REL-{seq:03d}-{aid}-{bid}"
    sheet.save(REL / f"{stem}-1x.png")
    sheet.resize((sheet.width * 8, sheet.height * 8), Image.Resampling.NEAREST).save(REL / f"{stem}-8x-nearest.png")
    row["roi_px"] = json.dumps([int(x0), int(y0), int(x1 - x0), int(y1 - y0)])
    row["closest_a_px"] = json.dumps([int(pa[0]), int(pa[1])])
    row["closest_b_px"] = json.dumps([int(pb[0]), int(pb[1])])
    row["evidence_1x"] = f"views/critical_relations/{stem}-1x.png"
    row["evidence_8x"] = f"views/critical_relations/{stem}-8x-nearest.png"


for seq, row in enumerate(critical_rows, start=1):
    relation_evidence(row, seq)


# Low-profile punctuation peer calibration from the actual PDF render.
cal_groups = defaultdict(list)
for row in glyph_rows:
    if row["class"] == "LOW_PROFILE_PUNCTUATION":
        key = (row["char"], row["font"], row["pdf_size_pt"], row["panel"])
        cal_groups[key].append(row)
punct_rows = []
for key, members in cal_groups.items():
    heights = [int(r["h_ink_px"]) for r in members if int(r["h_ink_px"]) > 0]
    areas = [int(r["ink_area_px"]) for r in members if int(r["ink_area_px"]) > 0]
    h_med = float(np.median(heights)) if heights else 0
    a_med = float(np.median(areas)) if areas else 0
    for r in members:
        punct_rows.append({
            "element_id": r["element_id"],
            "char": r["char"],
            "peer_group": f"{ord(r['char']):04X}|{r['font']}|{r['pdf_size_pt']}|{r['panel']}",
            "peer_count": len(members),
            "h_ink_px": r["h_ink_px"],
            "area_px": r["ink_area_px"],
            "height_to_peer_median": round(float(r["h_ink_px"]) / h_med, 3) if h_med else "",
            "area_to_peer_median": round(float(r["ink_area_px"]) / a_med, 3) if a_med else "",
        })


# Text measurement overlay.
overlay_img = Image.fromarray(figure_rgb.copy())
odraw = ImageDraw.Draw(overlay_img)
for row in glyph_rows:
    x0, y0, x1, y1 = json.loads(row["crop_bbox_px"])
    odraw.rectangle([x0, y0, x1, y1], outline=(220, 0, 0), width=1)
    odraw.text((x0, max(0, y0 - 11)), row["element_id"], fill=(180, 0, 0))
overlay_img.save(ROOT / "after_text_measurement_overlay_300dpi.png")

# Native endpoint / crop-edge counterevidence. These are raw 1x crops and
# nearest-neighbour 8x views; no measurement is taken on the enlarged files.
endpoint_specs = [
    ("left_reader_edge", [0, 550, 100, 120], "left crop edge / P2 ylabel"),
    ("bottom_reader_edge", [780, 750, 170, 110], "bottom crop edge / x label"),
    ("p1_right_endpoint", [1300, 180, 160, 190], "P1 final marker / axis arrow"),
    ("p2_right_endpoint", [1300, 520, 160, 240], "P2 final marker / axis arrow"),
]
endpoint_rows = []
for stem, (x0, y0, w, h), label in endpoint_specs:
    roi = Image.fromarray(figure_rgb[y0:y0 + h, x0:x0 + w].copy())
    draw = ImageDraw.Draw(roi)
    if x0 == 0:
        draw.line([(0, 0), (0, h - 1)], fill=(255, 0, 0), width=1)
    if y0 + h == CROP_H:
        draw.line([(0, h - 1), (w - 1, h - 1)], fill=(255, 0, 0), width=1)
    roi.save(VIEWS / f"endpoint_{stem}_1x.png")
    roi.resize((w * 8, h * 8), Image.Resampling.NEAREST).save(VIEWS / f"endpoint_{stem}_8x_nearest.png")
    endpoint_rows.append({
        "endpoint_id": stem,
        "roi_px": json.dumps([x0, y0, w, h]),
        "label": label,
        "view_1x": f"views/endpoint_{stem}_1x.png",
        "view_8x": f"views/endpoint_{stem}_8x_nearest.png",
    })
write_csv(ROOT / "endpoint_clip_counterevidence.csv", endpoint_rows, [
    "endpoint_id", "roi_px", "label", "view_1x", "view_8x",
])


math_rules = []
for obj in objects:
    if obj["subkind"] != "MATH_RULE":
        continue
    mask = object_masks[obj["object_id"]]
    bbox = bbox_from_mask(mask)
    math_rules.append({
        "element_id": obj["object_id"],
        "safe_filename": obj["safe_filename"],
        "semantic_parent": obj["parent_id"],
        "drawing_indices": obj["source_refs"],
        "bbox_px": json.dumps(bbox),
        "pixel_count": int(mask.sum()),
        "contact_sheet": contact_lookup[obj["object_id"]]["sheet"],
        "contact_cell": contact_lookup[obj["object_id"]]["cell"],
        "mask_file": obj["mask_file"],
    })

for pair_name, top, bottom in [
    ("EQ_WARMUP", "P1_EQ_WARMUP_TOP", "P1_EQ_WARMUP_BOTTOM"),
    ("EQ_RETAIN", "P1_EQ_RETAIN_TOP", "P1_EQ_RETAIN_BOTTOM"),
]:
    union = object_masks[top] | object_masks[bottom]
    bb = bbox_from_mask(union)
    math_rules.append({
        "element_id": pair_name,
        "safe_filename": "N/A_AGGREGATE",
        "semantic_parent": obj_by_id[top]["parent_id"],
        "drawing_indices": f"{obj_by_id[top]['source_refs']};{obj_by_id[bottom]['source_refs']}",
        "bbox_px": json.dumps(bb),
        "pixel_count": int(union.sum()),
        "contact_sheet": "aggregate from two component rows",
        "contact_cell": "N/A",
        "mask_file": "component masks",
    })


glyph_fields = [
    "element_id", "safe_filename", "char", "unicode", "parent_id", "panel", "font", "pdf_size_pt",
    "source_effective_pt", "class", "threshold_px", "pdf_bbox_pt", "crop_bbox_px", "ink_bbox_px",
    "h_ink_px", "w_ink_px", "ink_area_px", "mask_file", "contact_sheet", "contact_cell",
]
write_csv(ROOT / "after_pixel_measurements.csv", glyph_rows, glyph_fields)
write_csv(ROOT / "glyph_machine_ledger.csv", glyph_rows, glyph_fields)
write_csv(ROOT / "object_ledger.csv", objects, [
    "object_id", "safe_filename", "kind", "subkind", "parent_id", "panel", "source_refs", "bbox_px",
    "pixel_count", "mask_file", "clip_pixel_count", "edge_clearance_px",
])
write_csv(ROOT / "drawing_path_ledger.csv", drawing_path_rows, [
    "drawing_index", "mapped_object_id", "rect_pt", "type", "stroke", "fill", "width_pt", "item_count",
])
write_csv(ROOT / "all_unordered_pairs.csv", pair_rows, [
    "pair_id", "object_a", "object_b", "relation_class", "required_clearance_px", "overlap_pixel_count",
    "clearance_px", "metric",
])
write_csv(ROOT / "after_overlap_report.csv", critical_rows, [
    "pair_id", "object_a", "object_b", "relation_class", "required_clearance_px", "overlap_pixel_count",
    "clearance_px", "metric", "closest_a_px", "closest_b_px", "roi_px", "evidence_1x", "evidence_8x",
])
write_csv(ROOT / "math_rule_ledger.csv", math_rules, [
    "element_id", "safe_filename", "semantic_parent", "drawing_indices", "bbox_px", "pixel_count",
    "contact_sheet", "contact_cell", "mask_file",
])
write_csv(ROOT / "low_profile_punctuation_calibration.csv", punct_rows, [
    "element_id", "char", "peer_group", "peer_count", "h_ink_px", "area_px", "height_to_peer_median", "area_to_peer_median",
])
write_csv(ROOT / "contact_sheet_index.csv", contact_index, ["element_id", "sheet", "cell"])

nonempty = sum(1 for o in objects if int(o["pixel_count"]) > 0)
empty = len(objects) - nonempty
overlap_positive_hard = sum(1 for r in pair_rows if int(r["required_clearance_px"]) > 0 and int(r["overlap_pixel_count"]) > 0)
clearance_below = sum(
    1 for r in pair_rows
    if int(r["required_clearance_px"]) > 0 and r["clearance_px"] != "" and float(r["clearance_px"]) < float(r["required_clearance_px"])
)
hard_height_below = sum(
    1 for r in glyph_rows
    if isinstance(r["threshold_px"], int) and int(r["h_ink_px"]) < int(r["threshold_px"])
)
summary = {
    "official_pdf": str(PDF),
    "physical_page": 661,
    "page_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
    "page_native_300dpi_px": [int(page_rgb.shape[1]), int(page_rgb.shape[0])],
    "figure_crop_px": [CROP_X, CROP_Y, CROP_W, CROP_H],
    "glyph_objects": len(glyph_rows),
    "whitespace_chars_excluded_as_nonvisible": spaces_excluded,
    "graphic_objects": len(objects) - len(glyph_rows),
    "total_object_denominator": len(objects),
    "nonempty_object_masks": nonempty,
    "empty_object_masks": empty,
    "unordered_pair_denominator": len(pair_rows),
    "expected_pair_denominator": len(objects) * (len(objects) - 1) // 2,
    "critical_relation_count": len(critical_rows),
    "hard_relation_overlap_positive_count": overlap_positive_hard,
    "hard_relation_clearance_below_count": clearance_below,
    "clip_pixel_count_sum": sum(int(o["clip_pixel_count"]) for o in objects),
    "glyph_hard_height_below_count": hard_height_below,
    "math_rule_component_count": sum(1 for o in objects if o["subkind"] == "MATH_RULE"),
    "drawing_paths_in_figure": len(drawing_path_rows),
    "unmapped_drawing_paths": sum(1 for r in drawing_path_rows if r["mapped_object_id"] == "UNMAPPED"),
    "contact_review_object_count": len(review_objects),
    "contact_sheet_count": len({r["sheet"] for r in contact_index}),
}
(ROOT / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
