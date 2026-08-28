import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R2_SA3_FRESH_ISOLATED_R104_R168_20260826")
PAGE_PNG = ROOT / "renders" / "full_page_300dpi.png"
GRAY_PAGE_PNG = ROOT / "renders" / "full_page_grayscale_300dpi.png"

for name in ["crop", "contact_sheets", "matrices", "overlays", "raw_masks", "critical_relationships"]:
    (ROOT / name).mkdir(exist_ok=True)

page_img = Image.open(PAGE_PNG).convert("RGB")
gray_page = Image.open(GRAY_PAGE_PNG).convert("L")
img = np.asarray(page_img)
H, W = img.shape[:2]

doc = fitz.open(PDF)
page = doc[649]
PW, PH = page.rect.width, page.rect.height
SX, SY = W / PW, H / PH

def px_box(pt_box, pad=0):
    x0, y0, x1, y1 = pt_box
    return (
        max(0, math.floor(x0 * SX) - pad),
        max(0, math.floor(y0 * SY) - pad),
        min(W, math.ceil(x1 * SX) + pad),
        min(H, math.ceil(y1 * SY) + pad),
    )

FIGURE_CROP_PT = [68.0, 64.0, 538.0, 226.0]
FIGURE_ONLY_PT = [110.0, 64.0, 497.0, 192.0]
crop_px = px_box(FIGURE_CROP_PT)
figure_only_px = px_box(FIGURE_ONLY_PT)
page_img.crop(crop_px).save(ROOT / "crop" / "figure_crop_300dpi.png")
page_img.crop(figure_only_px).save(ROOT / "crop" / "standalone_300dpi.png")
gray_page.crop(crop_px).save(ROOT / "crop" / "grayscale_300dpi.png")

raw = page.get_text("rawdict")
drawings = page.get_drawings()

block_parent = {
    1: ("P_STEP1_HEADER", "heading", "step1"),
    2: ("P_STEP1_KERNEL_FORMULA", "formula", "step1"),
    3: ("P_STEP1_STATE_LABELS", "node_label", "step1"),
    4: ("P_STEP1_NOTE", "annotation", "step1"),
    5: ("P_STEP2_HEADER", "heading", "step2"),
    6: ("P_STEP2_SEGMENT_LABELS", "annotation", "step2"),
    7: ("P_STEP3_HEADER", "heading", "step3"),
    8: ("P_STEP3_ESTIMATOR", "formula", "step3"),
    9: ("P_STEP3_ESTIMATOR", "formula", "step3"),
    10: ("P_STEP3_ESTIMATOR", "formula_script", "step3"),
    11: ("P_STEP3_ESTIMATOR", "formula", "step3"),
    12: ("P_STEP3_ESTIMATOR", "formula_script", "step3"),
    13: ("P_STEP3_ESTIMATOR", "formula", "step3"),
    14: ("P_STEP3_NOTE", "annotation", "step3"),
    15: ("P_CAPTION", "caption", "caption"),
}

def int_rgb(value):
    value = int(value or 0)
    return np.array([(value >> 16) & 255, (value >> 8) & 255, value & 255], dtype=np.float32)

def float_rgb(value):
    if value is None:
        return np.array([31, 35, 40], dtype=np.float32)
    return np.array([round(255 * float(v)) for v in value], dtype=np.float32)

def local_background(box):
    x0, y0, x1, y1 = box
    ex0, ey0, ex1, ey1 = max(0, x0 - 3), max(0, y0 - 3), min(W, x1 + 3), min(H, y1 + 3)
    patch = img[ey0:ey1, ex0:ex1]
    ring = np.ones(patch.shape[:2], dtype=bool)
    ring[max(0, y0-ey0):min(patch.shape[0], y1-ey0), max(0, x0-ex0):min(patch.shape[1], x1-ex0)] = False
    values = patch[ring]
    if values.size == 0:
        values = patch.reshape(-1, 3)
    return np.median(values, axis=0)

def color_mask(box, target, edge_only=False):
    x0, y0, x1, y1 = box
    patch = img[y0:y1, x0:x1].astype(np.float32)
    bg = local_background(box)
    d_target = np.linalg.norm(patch - target, axis=2)
    d_bg = np.linalg.norm(patch - bg, axis=2)
    contrast = np.max(np.abs(patch - bg), axis=2)
    mask = (contrast >= 20.0) & (d_target <= d_bg + 5.0)
    if edge_only:
        edge = np.zeros(mask.shape, dtype=bool)
        band = min(8, max(2, min(mask.shape) // 3))
        edge[:band, :] = True
        edge[-band:, :] = True
        edge[:, :band] = True
        edge[:, -band:] = True
        mask &= edge
    return mask

def tight_bbox(mask, global_box):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return list(global_box), 0, 0, 0
    x0, y0, _, _ = global_box
    bb = [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)]
    return bb, int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1), int(mask.sum())

objects = []
masks = {}

glyph_index = 0
for block_index, block in enumerate(raw.get("blocks", [])):
    if block_index not in block_parent or block.get("type") != 0:
        continue
    parent, role, panel = block_parent[block_index]
    for line_index, line in enumerate(block.get("lines", [])):
        for span_index, span in enumerate(line.get("spans", [])):
            target = int_rgb(span.get("color"))
            for char_index, ch in enumerate(span.get("chars", [])):
                char = ch.get("c", "")
                if not char.strip():
                    continue
                bpt = list(ch.get("bbox", []))
                if not bpt or bpt[1] < 75 or bpt[1] >= 226:
                    continue
                glyph_index += 1
                oid = f"GLYPH_{glyph_index:04d}"
                box = px_box(bpt, pad=0)
                local = color_mask(box, target)
                bb, ink_h, ink_w, ink_area = tight_bbox(local, box)
                canvas = np.zeros((H, W), dtype=bool)
                canvas[box[1]:box[3], box[0]:box[2]] = local
                masks[oid] = canvas
                if role == "formula_script":
                    glyph_class = "NATURAL_SCRIPT"
                elif char in "，。；：、,.…-–—":
                    glyph_class = "LOW_PROFILE_PUNCTUATION"
                elif "\u4e00" <= char <= "\u9fff" or char in "：，。；、【】（）":
                    glyph_class = "CJK_FULL"
                elif char.isdigit() or (len(char) == 1 and char.isupper()):
                    glyph_class = "LATIN_UPPER_DIGIT"
                elif char in "=+−∑[]()":
                    glyph_class = "MATH_OPERATOR"
                else:
                    glyph_class = "LATIN_GREEK_LOWER_OR_MATH"
                objects.append({
                    "object_id": oid,
                    "safe_filename": oid + ".png",
                    "kind": "GLYPH",
                    "subkind": glyph_class,
                    "char": char,
                    "parent": parent,
                    "role": role,
                    "panel": panel,
                    "source_block": block_index,
                    "source_line": line_index,
                    "source_span": span_index,
                    "source_char_index": char_index,
                    "font": span.get("font"),
                    "pdf_size_pt": round(float(span.get("size", 0)), 4),
                    "bbox_pt": [round(v, 4) for v in bpt],
                    "bbox_px": bb,
                    "raw_box_px": list(box),
                    "ink_height_px": ink_h,
                    "ink_width_px": ink_w,
                    "ink_area_px": ink_area,
                    "empty_mask_machine": ink_area == 0,
                })

# Resolve the raster-rounding overlap of adjacent same-color PDF character boxes.
# Each visible pixel is owned by exactly one glyph, chosen by nearest glyph bbox center.
glyph_objects = [o for o in objects if o["kind"] == "GLYPH"]
for gi, a in enumerate(glyph_objects):
    aid = a["object_id"]
    acx = (a["bbox_px"][0] + a["bbox_px"][2]) / 2.0
    acy = (a["bbox_px"][1] + a["bbox_px"][3]) / 2.0
    for b in glyph_objects[gi+1:]:
        bid = b["object_id"]
        ax0, ay0, ax1, ay1 = a["raw_box_px"]
        bx0, by0, bx1, by1 = b["raw_box_px"]
        x0, y0, x1, y1 = max(ax0,bx0), max(ay0,by0), min(ax1,bx1), min(ay1,by1)
        if x1 <= x0 or y1 <= y0:
            continue
        inter = masks[aid][y0:y1,x0:x1] & masks[bid][y0:y1,x0:x1]
        if not inter.any():
            continue
        yy, xx = np.nonzero(inter)
        gx, gy = xx + x0, yy + y0
        bcx = (b["bbox_px"][0] + b["bbox_px"][2]) / 2.0
        bcy = (b["bbox_px"][1] + b["bbox_px"][3]) / 2.0
        da = (gx-acx)**2 + (gy-acy)**2
        db = (gx-bcx)**2 + (gy-bcy)**2
        give_b = db < da
        masks[aid][gy[give_b],gx[give_b]] = False
        masks[bid][gy[~give_b],gx[~give_b]] = False

for o in glyph_objects:
    x0,y0,x1,y1=o["raw_box_px"]
    local=masks[o["object_id"]][y0:y1,x0:x1]
    bb,ink_h,ink_w,ink_area=tight_bbox(local,(x0,y0,x1,y1))
    o["bbox_px"],o["ink_height_px"],o["ink_width_px"],o["ink_area_px"],o["empty_mask_machine"]=bb,ink_h,ink_w,ink_area,ink_area==0

graphic_specs = [
    ("GRAPHIC_CARD1_BORDER", 1, "BORDER", "P_CARD1", "step1", True),
    ("GRAPHIC_CARD2_BORDER", 2, "BORDER", "P_CARD2", "step2", True),
    ("GRAPHIC_CARD3_BORDER", 3, "BORDER", "P_CARD3", "step3", True),
    ("GRAPHIC_NODE_X_BORDER", 4, "BORDER", "P_NODE_X", "step1", True),
    ("GRAPHIC_NODE_Y_BORDER", 5, "BORDER", "P_NODE_Y", "step1", True),
    ("GRAPHIC_KERNEL_XY_BODY", 6, "ARROW_LINE", "P_KERNEL_XY", "step1", False),
    ("GRAPHIC_KERNEL_XY_HEAD", 7, "ARROW_HEAD", "P_KERNEL_XY", "step1", False),
    ("GRAPHIC_KERNEL_YX_BODY", 8, "ARROW_LINE", "P_KERNEL_YX", "step1", False),
    ("GRAPHIC_KERNEL_YX_HEAD", 9, "ARROW_HEAD", "P_KERNEL_YX", "step1", False),
    ("GRAPHIC_CHAIN_BASELINE", 10, "LINE", "P_CHAIN", "step2", False),
    ("GRAPHIC_CHAIN_CURVE", 12, "CURVE", "P_CHAIN", "step2", False),
    ("GRAPHIC_CHAIN_DIVIDER", 13, "DIVIDER", "P_CHAIN", "step2", False),
    ("GRAPHIC_DOT_1", 14, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_2", 15, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_3", 16, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_4", 17, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_5", 18, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_6", 19, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_DOT_7", 20, "MARKER", "P_RETAINED_DOTS", "step3", False),
    ("GRAPHIC_FRACTION_BAR", 21, "MATH_RULE", "P_STEP3_ESTIMATOR", "step3", False),
    ("GRAPHIC_FLOW1_BODY", 22, "ARROW_LINE", "P_FLOW1", "between12", False),
    ("GRAPHIC_FLOW1_HEAD", 23, "ARROW_HEAD", "P_FLOW1", "between12", False),
    ("GRAPHIC_FLOW2_BODY", 24, "ARROW_LINE", "P_FLOW2", "between23", False),
    ("GRAPHIC_FLOW2_HEAD", 25, "ARROW_HEAD", "P_FLOW2", "between23", False),
]

for oid, di, subkind, parent, panel, edge_only in graphic_specs:
    d = drawings[di]
    bpt = list(d["rect"])
    box = px_box(bpt, pad=3)
    target = float_rgb(d.get("fill") if d.get("type") == "f" else d.get("color"))
    local = color_mask(box, target, edge_only=edge_only)
    bb, ink_h, ink_w, ink_area = tight_bbox(local, box)
    canvas = np.zeros((H, W), dtype=bool)
    canvas[box[1]:box[3], box[0]:box[2]] = local
    masks[oid] = canvas
    objects.append({
        "object_id": oid,
        "safe_filename": oid + ".png",
        "kind": "GRAPHIC",
        "subkind": subkind,
        "char": "",
        "parent": parent,
        "role": subkind.lower(),
        "panel": panel,
        "drawing_index": di,
        "drawing_seqno": d.get("seqno"),
        "bbox_pt": [round(v, 4) for v in bpt],
        "bbox_px": bb,
        "raw_box_px": list(box),
        "ink_height_px": ink_h,
        "ink_width_px": ink_w,
        "ink_area_px": ink_area,
        "empty_mask_machine": ink_area == 0,
    })

def add_custom_graphic(oid, subkind, parent, panel, bpt, target, subtract_ids=()):
    box = px_box(bpt, pad=2)
    local = color_mask(box, np.array(target, dtype=np.float32))
    if subkind == "PATTERN":
        # Keep diagonal hatch runs; reject horizontal baseline fragments.
        support = np.zeros_like(local)
        for delta in (1, 2, 3):
            support[delta:, :-delta] |= local[:-delta, delta:]
            support[:-delta, delta:] |= local[delta:, :-delta]
        local &= support
    canvas = np.zeros((H, W), dtype=bool)
    canvas[box[1]:box[3], box[0]:box[2]] = local
    for sid in subtract_ids:
        canvas &= ~masks[sid]
    local2 = canvas[box[1]:box[3], box[0]:box[2]]
    bb, ink_h, ink_w, ink_area = tight_bbox(local2, box)
    masks[oid] = canvas
    objects.append({
        "object_id": oid,
        "safe_filename": oid + ".png",
        "kind": "GRAPHIC",
        "subkind": subkind,
        "char": "",
        "parent": parent,
        "role": subkind.lower(),
        "panel": panel,
        "drawing_index": "CUSTOM_VISIBLE_PATH",
        "drawing_seqno": "CUSTOM_RASTER_RECONCILIATION",
        "bbox_pt": bpt,
        "bbox_px": bb,
        "raw_box_px": list(box),
        "ink_height_px": ink_h,
        "ink_width_px": ink_w,
        "ink_area_px": ink_area,
        "empty_mask_machine": ink_area == 0,
    })

add_custom_graphic("GRAPHIC_CHAIN_HATCH", "PATTERN", "P_CHAIN", "step2", [260.5, 113.3, 294.5, 149.8], [184, 192, 200], ("GRAPHIC_CHAIN_BASELINE","GRAPHIC_CHAIN_CURVE","GRAPHIC_CHAIN_DIVIDER"))
add_custom_graphic("GRAPHIC_WIDEHAT", "MATH_RULE", "P_STEP3_ESTIMATOR", "step3", [390.0, 131.0, 397.0, 136.2], [31, 35, 40], ("GLYPH_0037",))

# Reconcile final-visible ownership by the source paint order. Earlier paths lose
# pixels covered by later paths; the junction remains continuous at zero clearance.
paint_order_subtractions = [
    ("GRAPHIC_CARD1_BORDER", "GRAPHIC_FLOW1_BODY"),
    ("GRAPHIC_CARD2_BORDER", "GRAPHIC_FLOW1_HEAD"),
    ("GRAPHIC_CARD2_BORDER", "GRAPHIC_FLOW2_BODY"),
    ("GRAPHIC_CARD3_BORDER", "GRAPHIC_FLOW2_HEAD"),
    ("GRAPHIC_NODE_X_BORDER", "GRAPHIC_KERNEL_XY_BODY"),
    ("GRAPHIC_NODE_X_BORDER", "GRAPHIC_KERNEL_YX_HEAD"),
    ("GRAPHIC_NODE_Y_BORDER", "GRAPHIC_KERNEL_XY_HEAD"),
    ("GRAPHIC_NODE_Y_BORDER", "GRAPHIC_KERNEL_YX_BODY"),
    ("GRAPHIC_KERNEL_XY_BODY", "GRAPHIC_KERNEL_XY_HEAD"),
    ("GRAPHIC_KERNEL_YX_BODY", "GRAPHIC_KERNEL_YX_HEAD"),
    ("GRAPHIC_FLOW1_BODY", "GRAPHIC_FLOW1_HEAD"),
    ("GRAPHIC_FLOW2_BODY", "GRAPHIC_FLOW2_HEAD"),
    ("GRAPHIC_CHAIN_BASELINE", "GRAPHIC_CHAIN_CURVE"),
    ("GRAPHIC_CHAIN_BASELINE", "GRAPHIC_CHAIN_DIVIDER"),
    ("GRAPHIC_CHAIN_HATCH", "GRAPHIC_CHAIN_CURVE"),
    ("GRAPHIC_CHAIN_HATCH", "GRAPHIC_CHAIN_DIVIDER"),
    ("GRAPHIC_CHAIN_CURVE", "GRAPHIC_CHAIN_DIVIDER"),
]
for early, later in paint_order_subtractions:
    masks[early] &= ~masks[later]

for o in objects:
    if o["kind"] != "GRAPHIC":
        continue
    x0,y0,x1,y1=o["raw_box_px"]
    local=masks[o["object_id"]][y0:y1,x0:x1]
    bb,ink_h,ink_w,ink_area=tight_bbox(local,(x0,y0,x1,y1))
    o["bbox_px"],o["ink_height_px"],o["ink_width_px"],o["ink_area_px"],o["empty_mask_machine"]=bb,ink_h,ink_w,ink_area,ink_area==0

obj_by_id = {o["object_id"]: o for o in objects}

# Save compact ordinary PNG masks; IDs are safe and cannot create ADS.
for o in objects:
    oid = o["object_id"]
    x0, y0, x1, y1 = o["raw_box_px"]
    local = masks[oid][y0:y1, x0:x1]
    Image.fromarray((local.astype(np.uint8) * 255), mode="L").save(ROOT / "raw_masks" / o["safe_filename"])

# Pair ledger: every unordered pair exactly once.
coords = {oid: np.column_stack(np.nonzero(mask)) for oid, mask in masks.items()}
trees = {oid: cKDTree(c[:, ::-1]) if len(c) else None for oid, c in coords.items()}

expected_parent_overlaps = {"P_KERNEL_XY", "P_KERNEL_YX", "P_FLOW1", "P_FLOW2", "P_STEP3_ESTIMATOR", "P_CHAIN"}
intentional_cross = {
    frozenset(("GRAPHIC_FLOW1_BODY", "GRAPHIC_CARD1_BORDER")),
    frozenset(("GRAPHIC_FLOW1_HEAD", "GRAPHIC_CARD2_BORDER")),
    frozenset(("GRAPHIC_FLOW2_BODY", "GRAPHIC_CARD2_BORDER")),
    frozenset(("GRAPHIC_FLOW2_HEAD", "GRAPHIC_CARD3_BORDER")),
    frozenset(("GRAPHIC_NODE_X_BORDER", "GRAPHIC_KERNEL_XY_BODY")),
    frozenset(("GRAPHIC_NODE_Y_BORDER", "GRAPHIC_KERNEL_XY_HEAD")),
    frozenset(("GRAPHIC_NODE_Y_BORDER", "GRAPHIC_KERNEL_YX_BODY")),
    frozenset(("GRAPHIC_NODE_X_BORDER", "GRAPHIC_KERNEL_YX_HEAD")),
}

def bbox_clearance(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0, max(ay0, by0) - min(ay1, by1))
    return math.hypot(dx, dy)

def required_clearance(a, b):
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH" and a["parent"] != b["parent"]:
        return 4.0, "TEXT_TEXT_BBOX"
    glyph, other = (a, b) if a["kind"] == "GLYPH" else (b, a)
    if glyph["kind"] == "GLYPH" and other["kind"] == "GRAPHIC":
        if other["subkind"] == "BORDER":
            return 5.0, "TEXT_BORDER_RAW"
        if other["subkind"] in {"ARROW_LINE", "ARROW_HEAD", "LINE", "CURVE", "DIVIDER", "MARKER", "MATH_RULE", "PATTERN"}:
            return 3.0, "TEXT_GRAPHIC_RAW"
    return 0.0, "NO_CLEARANCE_GATE"

def local_intersection_count(aid, bid):
    a = obj_by_id[aid]["bbox_px"]
    b = obj_by_id[bid]["bbox_px"]
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(np.count_nonzero(masks[aid][y0:y1, x0:x1] & masks[bid][y0:y1, x0:x1]))

pair_rows = []
ids = [o["object_id"] for o in objects]
for i, aid in enumerate(ids):
    a = obj_by_id[aid]
    for bid in ids[i+1:]:
        b = obj_by_id[bid]
        inter = local_intersection_count(aid, bid)
        same_parent = a["parent"] == b["parent"]
        intentional = same_parent and a["parent"] in expected_parent_overlaps
        intentional = intentional or frozenset((aid, bid)) in intentional_cross
        if trees[aid] is None or trees[bid] is None:
            min_center = None
            raw_clear = None
        else:
            ca, cb = coords[aid], coords[bid]
            if len(ca) <= len(cb):
                distances, _ = trees[bid].query(ca[:, ::-1], k=1)
            else:
                distances, _ = trees[aid].query(cb[:, ::-1], k=1)
            min_center = float(np.min(distances))
            raw_clear = max(0.0, min_center - 1.0)
        req, gate_class = required_clearance(a, b)
        bc = bbox_clearance(a["bbox_px"], b["bbox_px"])
        applicable = not same_parent or a["kind"] == "GRAPHIC" or b["kind"] == "GRAPHIC"
        if intentional:
            machine_status = "INTENTIONAL_DESIGN_RELATION"
        elif inter > 0:
            machine_status = "MACHINE_INTERSECTION_REQUIRES_HUMAN"
        elif req > 0 and applicable:
            actual = bc if gate_class == "TEXT_TEXT_BBOX" else raw_clear
            machine_status = "MACHINE_CLEAR" if actual is not None and actual >= req else "MACHINE_CRITICAL_CLEARANCE"
        else:
            machine_status = "MACHINE_CLEAR"
        pair_rows.append({
            "pair_id": f"PAIR_{len(pair_rows)+1:05d}",
            "object_a": aid,
            "object_b": bid,
            "kind_a": a["subkind"],
            "kind_b": b["subkind"],
            "parent_a": a["parent"],
            "parent_b": b["parent"],
            "same_parent": same_parent,
            "intentional_design_relation": intentional,
            "intersection_px": inter,
            "min_center_distance_px": None if min_center is None else round(min_center, 4),
            "raw_clearance_px": None if raw_clear is None else round(raw_clear, 4),
            "bbox_clearance_px": round(bc, 4),
            "required_clearance_px": req,
            "gate_class": gate_class,
            "machine_status": machine_status,
        })

with (ROOT / "all_unordered_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(pair_rows[0].keys()))
    w.writeheader(); w.writerows(pair_rows)

with (ROOT / "object_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = sorted({k for o in objects for k in o})
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(objects)

(ROOT / "object_manifest.json").write_text(json.dumps({
    "figure_uid": "FIG-P598-02",
    "pdf": str(PDF),
    "physical_page": 650,
    "page_size_pt": [PW, PH],
    "native_300dpi_grid": [W, H],
    "scale_px_per_pt": [SX, SY],
    "figure_crop_pt": FIGURE_CROP_PT,
    "figure_crop_px": list(crop_px),
    "figure_only_pt": FIGURE_ONLY_PT,
    "figure_only_px": list(figure_only_px),
    "glyph_count": glyph_index,
    "graphic_count": len(objects) - glyph_index,
    "object_count": len(objects),
    "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
    "actual_unordered_pair_count": len(pair_rows),
    "objects": objects,
}, ensure_ascii=False, indent=2), encoding="utf-8")

# Labeled overview overlay.
overlay = page_img.crop(crop_px).copy()
od = ImageDraw.Draw(overlay)
for o in objects:
    x0, y0, x1, y1 = o["bbox_px"]
    x0 -= crop_px[0]; x1 -= crop_px[0]; y0 -= crop_px[1]; y1 -= crop_px[1]
    color = (220, 40, 40) if o["kind"] == "GLYPH" else (20, 160, 40)
    od.rectangle((x0, y0, x1, y1), outline=color, width=1)
    if o["kind"] == "GRAPHIC":
        od.text((x0, max(0, y0 - 11)), o["object_id"].replace("GRAPHIC_", "G_"), fill=color)
overlay.save(ROOT / "overlays" / "all_objects_overlay_300dpi.png")

def object_patch(oid, pad=6):
    o = obj_by_id[oid]
    x0, y0, x1, y1 = o["bbox_px"]
    box = (max(0, x0-pad), max(0, y0-pad), min(W, x1+pad), min(H, y1+pad))
    orig = page_img.crop(box)
    m = masks[oid][box[1]:box[3], box[0]:box[2]]
    over = np.array(orig).copy()
    over[m] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(over, 255)
    mask_only[m] = np.array([0, 0, 0], dtype=np.uint8)
    return box, orig, Image.fromarray(over), Image.fromarray(mask_only), m

font = ImageFont.load_default()
contact_index = []

# Glyph contact sheets: 24 cells/sheet, each cell shows native 1x context/overlay/mask and 8x nearest target.
glyph_ids = [o["object_id"] for o in objects if o["kind"] == "GLYPH"]
for sheet_no, start in enumerate(range(0, len(glyph_ids), 24), 1):
    batch = glyph_ids[start:start+24]
    sheet = Image.new("RGB", (1800, 840), "white")
    sd = ImageDraw.Draw(sheet)
    for j, oid in enumerate(batch):
        row, col = divmod(j, 6)
        cell_x, cell_y = col * 300, row * 210
        box, orig, over, monly, m = object_patch(oid, 6)
        views = [orig, over, monly]
        labels = ["ORIGINAL 1x", "TARGET OVERLAY 1x", "MASK ONLY 1x"]
        for k, (view, label) in enumerate(zip(views, labels)):
            sheet.paste(view, (cell_x + k*75 + 4, cell_y + 38))
            sd.text((cell_x + k*75 + 4, cell_y + 25), label, fill="black", font=font)
        tight = Image.fromarray((m.astype(np.uint8)*255), mode="L")
        if tight.width and tight.height:
            zoom = tight.resize((tight.width*8, tight.height*8), resample=Image.Resampling.NEAREST).convert("RGB")
            zoom.thumbnail((70, 135), resample=Image.Resampling.NEAREST)
            sheet.paste(zoom, (cell_x + 229, cell_y + 38))
        sd.text((cell_x + 229, cell_y + 25), "8x NN", fill="black", font=font)
        o = obj_by_id[oid]
        sd.text((cell_x + 4, cell_y + 4), f"{oid} char={o['char']} H={o['ink_height_px']} A={o['ink_area_px']}", fill="black", font=font)
        sd.rectangle((cell_x, cell_y, cell_x+299, cell_y+209), outline=(150,150,150), width=1)
        contact_index.append({"object_id": oid, "sheet": f"glyph_contact_sheet_{sheet_no:02d}.png", "cell": j+1})
    sheet.save(ROOT / "contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png")

# Graphic contact sheets: two objects/page, full native 1x triptychs plus a nearest-neighbour detail tile.
graphic_ids = [o["object_id"] for o in objects if o["kind"] == "GRAPHIC"]
for sheet_no, start in enumerate(range(0, len(graphic_ids), 2), 1):
    batch = graphic_ids[start:start+2]
    prepared = []
    max_h = 0
    for oid in batch:
        data = object_patch(oid, 8)
        prepared.append((oid, data))
        max_h = max(max_h, data[1].height)
    sheet = Image.new("RGB", (2100, max(500, 2*(max_h+90))), "white")
    sd = ImageDraw.Draw(sheet)
    y = 0
    for j, (oid, (box, orig, over, monly, m)) in enumerate(prepared):
        sd.text((5, y+5), oid, fill="black", font=font)
        x = 5
        for view, label in [(orig,"ORIGINAL 1x"),(over,"TARGET OVERLAY 1x"),(monly,"MASK ONLY 1x")]:
            sd.text((x, y+22), label, fill="black", font=font)
            sheet.paste(view, (x, y+38)); x += view.width + 15
        yy, xx = np.nonzero(m)
        if len(xx):
            cx, cy = int(np.median(xx)), int(np.median(yy))
            x0, y0 = max(0,cx-12), max(0,cy-12)
            detail = monly.crop((x0,y0,min(m.shape[1],x0+25),min(m.shape[0],y0+25)))
            detail = detail.resize((detail.width*8,detail.height*8),resample=Image.Resampling.NEAREST)
            sd.text((x, y+22), "REPRESENTATIVE 8x NN", fill="black", font=font)
            sheet.paste(detail,(x,y+38))
        contact_index.append({"object_id": oid, "sheet": f"graphic_contact_sheet_{sheet_no:02d}.png", "cell": j+1})
        y += max_h + 90
    sheet.save(ROOT / "contact_sheets" / f"graphic_contact_sheet_{sheet_no:02d}.png")

with (ROOT / "contact_sheet_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["object_id","sheet","cell"])
    w.writeheader(); w.writerows(contact_index)

# Global overlap status matrix and object-kind matrix.
n = len(objects)
cell = 6
mat = Image.new("RGB", (n*cell, n*cell), "white")
md = ImageDraw.Draw(mat)
pair_map = {(r["object_a"], r["object_b"]): r for r in pair_rows}
for i, a in enumerate(ids):
    for j, b in enumerate(ids):
        if i == j:
            color = (30,30,30)
        else:
            r = pair_map.get((a,b)) or pair_map.get((b,a))
            if r["machine_status"] == "INTENTIONAL_DESIGN_RELATION": color = (70,120,230)
            elif r["intersection_px"] > 0: color = (230,50,50)
            elif r["machine_status"] == "MACHINE_CRITICAL_CLEARANCE": color = (245,170,40)
            else: color = (235,245,235)
        md.rectangle((j*cell,i*cell,(j+1)*cell-1,(i+1)*cell-1),fill=color)
mat.save(ROOT / "matrices" / "all_pairs_overlap_status_matrix.png")

kind_colors = {"GLYPH":(60,110,220),"BORDER":(100,100,100),"ARROW_LINE":(30,150,80),"ARROW_HEAD":(30,180,100),"LINE":(120,120,40),"CURVE":(180,80,180),"DIVIDER":(230,150,20),"MARKER":(20,120,180),"MATH_RULE":(180,40,40),"PATTERN":(140,140,160)}
kind_mat = Image.new("RGB", (n*cell, n*cell), "white")
kd = ImageDraw.Draw(kind_mat)
for i,a in enumerate(objects):
    for j,b in enumerate(objects):
        ca = kind_colors.get(a["kind"] if a["kind"]=="GLYPH" else a["subkind"],(0,0,0))
        cb = kind_colors.get(b["kind"] if b["kind"]=="GLYPH" else b["subkind"],(0,0,0))
        color=tuple((ca[k]+cb[k])//2 for k in range(3))
        kd.rectangle((j*cell,i*cell,(j+1)*cell-1,(i+1)*cell-1),fill=color)
kind_mat.save(ROOT / "matrices" / "all_pairs_object_kind_matrix.png")

# Critical relationship overlays: selected semantic hard/near-hard relations.
critical_specs = [
    ("REL01", "step1 header to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP1_HEADER"], ["GRAPHIC_CARD1_BORDER"]),
    ("REL02", "kernel equation to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP1_KERNEL_FORMULA"], ["GRAPHIC_CARD1_BORDER"]),
    ("REL03", "state labels to node borders", [o["object_id"] for o in objects if o["parent"]=="P_STEP1_STATE_LABELS"], ["GRAPHIC_NODE_X_BORDER","GRAPHIC_NODE_Y_BORDER"]),
    ("REL04", "step1 note to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP1_NOTE"], ["GRAPHIC_CARD1_BORDER"]),
    ("REL05", "step2 header to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP2_HEADER"], ["GRAPHIC_CARD2_BORDER"]),
    ("REL06", "segment labels to chain graphics", [o["object_id"] for o in objects if o["parent"]=="P_STEP2_SEGMENT_LABELS"], ["GRAPHIC_CHAIN_BASELINE","GRAPHIC_CHAIN_HATCH","GRAPHIC_CHAIN_CURVE","GRAPHIC_CHAIN_DIVIDER"]),
    ("REL07", "step3 header to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP3_HEADER"], ["GRAPHIC_CARD3_BORDER"]),
    ("REL08", "estimator to dots and card", [o["object_id"] for o in objects if o["parent"]=="P_STEP3_ESTIMATOR"], ["GRAPHIC_DOT_1","GRAPHIC_DOT_2","GRAPHIC_DOT_3","GRAPHIC_DOT_4","GRAPHIC_DOT_5","GRAPHIC_DOT_6","GRAPHIC_DOT_7","GRAPHIC_CARD3_BORDER"]),
    ("REL09", "step3 note to card border", [o["object_id"] for o in objects if o["parent"]=="P_STEP3_NOTE"], ["GRAPHIC_CARD3_BORDER"]),
    ("REL10", "caption to figure bottom", [o["object_id"] for o in objects if o["parent"]=="P_CAPTION"], ["GRAPHIC_CARD1_BORDER","GRAPHIC_CARD2_BORDER","GRAPHIC_CARD3_BORDER"]),
    ("REL11", "flow arrow one continuity", ["GRAPHIC_FLOW1_BODY","GRAPHIC_FLOW1_HEAD"], ["GRAPHIC_CARD1_BORDER","GRAPHIC_CARD2_BORDER"]),
    ("REL12", "flow arrow two continuity", ["GRAPHIC_FLOW2_BODY","GRAPHIC_FLOW2_HEAD"], ["GRAPHIC_CARD2_BORDER","GRAPHIC_CARD3_BORDER"]),
    ("REL13", "kernel bidirectional arrows", ["GRAPHIC_KERNEL_XY_BODY","GRAPHIC_KERNEL_XY_HEAD","GRAPHIC_KERNEL_YX_BODY","GRAPHIC_KERNEL_YX_HEAD"], ["GRAPHIC_NODE_X_BORDER","GRAPHIC_NODE_Y_BORDER"]),
    ("REL14", "widehat rule to estimator I", ["GRAPHIC_WIDEHAT"], [o["object_id"] for o in objects if o["parent"]=="P_STEP3_ESTIMATOR" and o["char"]=="𝐼"]),
    ("REL15", "fraction rule to numerator denominator", ["GRAPHIC_FRACTION_BAR"], [o["object_id"] for o in objects if o["parent"]=="P_STEP3_ESTIMATOR" and o["char"] in {"1","𝑛"}]),
    ("REL16", "chain curve pattern divider baseline", ["GRAPHIC_CHAIN_CURVE","GRAPHIC_CHAIN_HATCH"], ["GRAPHIC_CHAIN_DIVIDER","GRAPHIC_CHAIN_BASELINE"]),
]

critical_rows = []
for rid, desc, aset, bset in critical_specs:
    valid_a=[x for x in aset if x in masks]; valid_b=[x for x in bset if x in masks]
    union_a=np.zeros((H,W),dtype=bool); union_b=np.zeros((H,W),dtype=bool)
    for x in valid_a: union_a |= masks[x]
    for x in valid_b: union_b |= masks[x]
    ys,xs=np.nonzero(union_a|union_b)
    if len(xs)==0: continue
    box=(max(0,int(xs.min())-20),max(0,int(ys.min())-20),min(W,int(xs.max())+21),min(H,int(ys.max())+21))
    roi=np.array(page_img.crop(box)).copy()
    ma=union_a[box[1]:box[3],box[0]:box[2]]; mb=union_b[box[1]:box[3],box[0]:box[2]]
    roi[ma]=np.array([255,0,0],dtype=np.uint8)
    roi[mb]=np.array([0,220,0],dtype=np.uint8)
    roi[ma&mb]=np.array([255,0,255],dtype=np.uint8)
    roi_img=Image.fromarray(roi)
    # nearest point detail
    ca=np.column_stack(np.nonzero(union_a)); cb=np.column_stack(np.nonzero(union_b))
    min_dist=None; closest=None
    if len(ca) and len(cb):
        tb=cKDTree(cb[:,::-1]); dist,idx=tb.query(ca[:,::-1],k=1); q=int(np.argmin(dist)); min_dist=float(dist[q]); closest=(ca[q],cb[int(idx[q])])
    if closest:
        cy=int(round((closest[0][0]+closest[1][0])/2)); cx=int(round((closest[0][1]+closest[1][1])/2))
        db=(max(0,cx-18),max(0,cy-18),min(W,cx+19),min(H,cy+19))
        detail=np.array(page_img.crop(db)).copy(); da=union_a[db[1]:db[3],db[0]:db[2]]; dbm=union_b[db[1]:db[3],db[0]:db[2]]
        detail[da]=np.array([255,0,0],dtype=np.uint8); detail[dbm]=np.array([0,220,0],dtype=np.uint8); detail[da&dbm]=np.array([255,0,255],dtype=np.uint8)
        detail_img=Image.fromarray(detail).resize((detail.shape[1]*8,detail.shape[0]*8),resample=Image.Resampling.NEAREST)
    else:
        detail_img=Image.new("RGB",(296,296),"white")
    canvas=Image.new("RGB",(roi_img.width+detail_img.width+20,max(roi_img.height,detail_img.height)+45),"white")
    cd=ImageDraw.Draw(canvas); cd.text((5,5),f"{rid}: {desc} RED=A GREEN=B MAGENTA=intersection; right=8x NN",fill="black",font=font)
    canvas.paste(roi_img,(5,35)); canvas.paste(detail_img,(roi_img.width+15,35))
    fname=f"{rid}_{desc.replace(' ','_')}.png"
    canvas.save(ROOT/"critical_relationships"/fname)
    critical_rows.append({"relationship_id":rid,"description":desc,"objects_a":"|".join(valid_a),"objects_b":"|".join(valid_b),"overlay_file":fname,"union_a_px":int(union_a.sum()),"union_b_px":int(union_b.sum()),"intersection_px":int((union_a&union_b).sum()),"min_center_distance_px":None if min_dist is None else round(min_dist,4),"raw_clearance_px":None if min_dist is None else round(max(0,min_dist-1),4)})

with (ROOT/"critical_relationships_machine.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(critical_rows[0].keys())); w.writeheader(); w.writerows(critical_rows)

# Typography machine ledger, with R168 thresholds recorded as advisory only.
thresholds={"CJK_FULL":30,"LATIN_UPPER_DIGIT":24,"LATIN_GREEK_LOWER_OR_MATH":17,"MATH_OPERATOR":22,"NATURAL_SCRIPT":15,"LOW_PROFILE_PUNCTUATION":None}
typo=[]
for o in objects:
    if o["kind"]!="GLYPH": continue
    t=thresholds[o["subkind"]]
    typo.append({"object_id":o["object_id"],"char":o["char"],"parent":o["parent"],"role":o["role"],"font":o["font"],"pdf_size_pt":o["pdf_size_pt"],"ink_height_px":o["ink_height_px"],"ink_area_px":o["ink_area_px"],"legacy_threshold_px_advisory_under_R168":t,"legacy_numeric_status_advisory":("N/A_LOW_PROFILE" if t is None else ("MEETS" if o["ink_height_px"]>=t else "BELOW_ADVISORY")),"R168_hard_font_gate_scope":"missing/tofu/wrong glyph or codepoint/math semantics/genuinely unreadable/severe visible imbalance/real clipping-overlap"})
with (ROOT/"after_pixel_measurements.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(typo[0].keys())); w.writeheader(); w.writerows(typo)

source_rows=[
    {"scope":"tikzset base","declaration":"font=\\fontsize{9.2pt}{11.0pt}\\selectfont","effective_pt":9.2,"R168_status":"ADVISORY_ONLY"},
    {"scope":"every node","declaration":"font=\\fontsize{9.2pt}{11.0pt}\\selectfont","effective_pt":9.2,"R168_status":"ADVISORY_ONLY"},
    {"scope":"step headings","declaration":"\\fontsize{9.4pt}{11.2pt}\\selectfont\\bfseries","effective_pt":9.4,"R168_status":"ADVISORY_ONLY"},
    {"scope":"kernel/estimator formula","declaration":"\\fontsize{9.2pt}{11.0pt}\\selectfont","effective_pt":9.2,"R168_status":"ADVISORY_ONLY"},
    {"scope":"notes/segment labels","declaration":"\\fontsize{8.6pt}{10.2pt}\\selectfont","effective_pt":8.6,"R168_status":"ADVISORY_ONLY"},
    {"scope":"graphics scale","declaration":"none; tikz coordinates unscaled","effective_pt":1.0,"R168_status":"NO_TEXT_SCALE"},
]
with (ROOT/"after_font_audit.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(source_rows[0].keys())); w.writeheader(); w.writerows(source_rows)

# Machine summary intentionally contains no human review/decision/note fields.
summary={
    "pdf_sha256":hashlib.sha256(PDF.read_bytes()).hexdigest().upper(),
    "pdf_bytes":PDF.stat().st_size,
    "pdf_pages":len(doc),
    "physical_page":650,
    "page_size_pt":[PW,PH],
    "native_300dpi_grid":[W,H],
    "crop_px":list(crop_px),
    "glyph_count":glyph_index,
    "graphic_count":len(objects)-glyph_index,
    "object_count":len(objects),
    "unordered_pair_count":len(pair_rows),
    "expected_unordered_pair_count":len(objects)*(len(objects)-1)//2,
    "empty_mask_count":sum(bool(o["empty_mask_machine"]) for o in objects),
    "machine_intersection_pair_count":sum(r["intersection_px"]>0 for r in pair_rows),
    "machine_nonintentional_intersection_pair_count":sum(r["intersection_px"]>0 and not r["intentional_design_relation"] for r in pair_rows),
    "critical_relationship_count":len(critical_rows),
    "contact_sheet_count":len(list((ROOT/"contact_sheets").glob("*.png"))),
    "matrix_count":len(list((ROOT/"matrices").glob("*.png"))),
}
(ROOT/"machine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
