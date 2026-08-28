from __future__ import annotations

import csv
import hashlib
import json
import math
import unicodedata
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_markov_chain_path.tex")
PAGE_INDEX = 648
SCALE = 300.0 / 72.0
CROP = (250, 2054, 2180, 2760)
CROP_ORIGIN = (CROP[0], CROP[1])


def mkdirs() -> None:
    for name in ["masks/glyph", "masks/graphic", "masks/occlusion", "contact_glyph", "contact_graphic", "critical"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def rgb_from_int(v: int) -> tuple[int, int, int]:
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def pt_bbox_to_crop_px(bbox) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    # Assign raster pixels by their centers. This keeps abutting glyph boxes
    # half-open and prevents one antialiased boundary column from being
    # attributed to both neighboring glyph IDs.
    return (
        math.ceil(x0 * SCALE - CROP_ORIGIN[0] - 0.5),
        math.ceil(y0 * SCALE - CROP_ORIGIN[1] - 0.5),
        math.ceil(x1 * SCALE - CROP_ORIGIN[0] - 0.5),
        math.ceil(y1 * SCALE - CROP_ORIGIN[1] - 0.5),
    )


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def tight_mask_save(mask: np.ndarray, path: Path) -> tuple[int, int, int, int] | None:
    b = bbox_from_mask(mask)
    if b is None:
        Image.new("L", (1, 1), 0).save(path)
        return None
    x0, y0, x1, y1 = b
    Image.fromarray((mask[y0:y1, x0:x1].astype(np.uint8) * 255), "L").save(path)
    return b


def expected_color_mask(arr: np.ndarray, support: np.ndarray, target: tuple[int, int, int], bg_hint=None) -> np.ndarray:
    p = arr.astype(np.float32)
    if bg_hint is None:
        bg = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    else:
        bg = np.array(bg_hint, dtype=np.float32)
    tgt = np.array(target, dtype=np.float32)
    vec = bg - tgt
    denom = float(np.dot(vec, vec))
    if denom < 1:
        return np.zeros(support.shape, dtype=bool)
    alpha = np.tensordot(bg - p, vec, axes=([2], [0])) / denom
    recon = bg[None, None, :] - alpha[:, :, None] * vec[None, None, :]
    residual = np.max(np.abs(p - recon), axis=2)
    contrast = np.max(np.abs(p - bg[None, None, :]), axis=2)
    return support & (alpha >= 0.055) & (alpha <= 1.35) & (residual <= 26.0) & (contrast >= 20.0)


def parent_role(block: int, line: int) -> tuple[str, str]:
    table = {
        23: ("axis_title", "axis_title"),
        24: ("state_t0", "state_label"),
        27: ("state_t5", "state_label"),
        28: ("state_tT", "state_label"),
        29: ("time_t0", "time_label"),
        32: ("time_t5", "time_label"),
        33: ("time_tT", "time_label"),
        34: ("keep_b", "annotation"),
        36: ("repeat_correlation", "annotation"),
        37: ("spacing_double_circle", "annotation"),
    }
    if block == 25:
        return (("state_t1", "state_label") if line == 0 else ("state_t2", "state_label"))
    if block == 26:
        return (("state_t3", "state_label") if line == 0 else ("state_t4", "state_label"))
    if block == 30:
        return (("time_t1", "time_label") if line == 0 else ("time_t2", "time_label"))
    if block == 31:
        return (("time_t3", "time_label") if line == 0 else ("time_t4", "time_label"))
    if block == 35:
        return (("kernel_formula", "formula") if line == 0 else ("keep_c", "annotation"))
    if block == 38:
        return (("figure_number", "caption_label") if line == 0 else ("caption", "caption_text"))
    return table[block]


LOW_PUNCT = set(",.，。；;：:、…")
MATH_OPS = set("=+−-→×÷<>()[]")


def glyph_class(ch: str, size: float, parent: str) -> tuple[str, int]:
    if size < 7.0 and parent == "kernel_formula":
        return "NATURAL_SCRIPT", 15
    if ch in LOW_PUNCT:
        return "LOW_PROFILE_PUNCTUATION", 0
    if ch in MATH_OPS:
        return "MATH_OPERATOR", 22
    eaw = unicodedata.east_asian_width(ch)
    if eaw in {"W", "F"} and unicodedata.category(ch)[0] in {"L", "N"}:
        return "CJK_FULLHEIGHT", 30
    folded = unicodedata.normalize("NFKD", ch)
    if folded and folded[0].isdigit() or (folded and folded[0].isalpha() and folded[0].isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    if unicodedata.category(ch).startswith("L"):
        return "LATIN_OR_GREEK_LOWER", 17
    return "BASE_MATH", 22


def build_glyphs(page, crop_img: Image.Image):
    arr = np.array(crop_img.convert("RGB"))
    rd = page.get_text("rawdict")
    glyphs = []
    seq = 0
    for bi, block in enumerate(rd["blocks"]):
        if block.get("type") != 0 or not (23 <= bi <= 38):
            continue
        for li, line in enumerate(block["lines"]):
            parent, role = parent_role(bi, li)
            for si, span in enumerate(line["spans"]):
                color = rgb_from_int(span["color"])
                for ci, char in enumerate(span["chars"]):
                    ch = char["c"]
                    if ch.isspace():
                        continue
                    seq += 1
                    eid = f"G{seq:04d}"
                    raw_box = pt_bbox_to_crop_px(char["bbox"])
                    x0, y0, x1, y1 = raw_box
                    x0 = max(0, x0)
                    y0 = max(0, y0)
                    x1 = min(arr.shape[1], x1)
                    y1 = min(arr.shape[0], y1)
                    support = np.zeros(arr.shape[:2], dtype=bool)
                    support[y0:y1, x0:x1] = True
                    roi = arr[y0:y1, x0:x1]
                    bright = roi[np.max(roi, axis=2) > 215]
                    bg = np.percentile(bright, 90, axis=0) if len(bright) else np.array([255, 255, 255])
                    mask = expected_color_mask(arr, support, color, bg)
                    ink = bbox_from_mask(mask)
                    safe = f"{eid}.png"
                    tight_mask_save(mask, ROOT / "masks/glyph" / safe)
                    cls, advisory_min = glyph_class(ch, float(span["size"]), parent)
                    h = 0 if ink is None else ink[3] - ink[1]
                    w = 0 if ink is None else ink[2] - ink[0]
                    glyphs.append({
                        "element_id": eid,
                        "safe_filename": safe,
                        "kind": "GLYPH",
                        "char": ch,
                        "codepoint": f"U+{ord(ch):04X}",
                        "semantic_parent": parent,
                        "role": role,
                        "block": bi,
                        "line": li,
                        "span": si,
                        "char_index": ci,
                        "font": span["font"],
                        "pdf_size_pt": round(float(span["size"]), 6),
                        "color_rgb": color,
                        "bbox_pt": [round(float(v), 6) for v in char["bbox"]],
                        "bbox_px": [x0, y0, x1, y1],
                        "ink_bbox_px": list(ink) if ink else None,
                        "ink_width_px": w,
                        "ink_height_px": h,
                        "ink_pixel_count": int(mask.sum()),
                        "glyph_class": cls,
                        "legacy_advisory_min_px": advisory_min,
                        "legacy_advisory_delta_px": h - advisory_min if advisory_min else "N/A",
                        "empty_mask_machine_flag": bool(mask.sum() == 0),
                        "replacement_or_tofu_codepoint_machine_flag": ch in {"�", "□", "■"},
                        "mask_relpath": f"masks/glyph/{safe}",
                        "mask": mask,
                    })
    return glyphs


VISIBLE_DRAWINGS = {
    2: ("axis_line", "AXIS_LINE"),
    3: ("axis_arrowhead", "ARROWHEAD"),
    4: ("node_border_t0", "NODE_BORDER"),
    5: ("node_border_t1_repeat", "NODE_BORDER"),
    7: ("node_border_t2_repeat", "NODE_BORDER"),
    9: ("node_border_t3_repeat", "NODE_BORDER"),
    11: ("node_border_t4_repeat", "NODE_BORDER"),
    13: ("node_border_t5", "NODE_BORDER"),
    14: ("node_border_tT", "NODE_BORDER"),
    15: ("transition_line_0_1", "TRANSITION_LINE"),
    16: ("transition_arrow_0_1", "ARROWHEAD"),
    17: ("transition_line_1_2", "TRANSITION_LINE"),
    18: ("transition_arrow_1_2", "ARROWHEAD"),
    19: ("transition_line_2_3", "TRANSITION_LINE"),
    20: ("transition_arrow_2_3", "ARROWHEAD"),
    21: ("transition_line_3_4", "TRANSITION_LINE"),
    22: ("transition_arrow_3_4", "ARROWHEAD"),
    23: ("transition_line_4_5", "TRANSITION_LINE"),
    24: ("transition_arrow_4_5", "ARROWHEAD"),
    25: ("transition_line_5_T", "TRANSITION_LINE"),
    26: ("transition_arrow_5_T", "ARROWHEAD"),
    27: ("repeat_correlation_arc", "RELATION_ARC"),
}
OCCLUDERS = {6: "double_gap_t1", 8: "double_gap_t2", 10: "double_gap_t3", 12: "double_gap_t4"}


def bezier(p0, p1, p2, p3, n=96):
    t = np.linspace(0.0, 1.0, n)
    omt = 1.0 - t
    pts = (omt[:, None] ** 3) * p0 + 3 * (omt[:, None] ** 2) * t[:, None] * p1 + 3 * omt[:, None] * (t[:, None] ** 2) * p2 + (t[:, None] ** 3) * p3
    return [(int(round(x * SCALE - CROP_ORIGIN[0])), int(round(y * SCALE - CROP_ORIGIN[1]))) for x, y in pts]


def drawing_support(d, shape, fill_small: bool) -> np.ndarray:
    h, w = shape
    im = Image.new("1", (w, h), 0)
    dr = ImageDraw.Draw(im)
    stroke_w = max(3, int(math.ceil(float(d.get("width") or 0.6) * SCALE + 4)))
    all_pts = []
    current = None
    for item in d["items"]:
        if item[0] == "l":
            p0 = item[1]
            p1 = item[2]
            pts = [(round(p0.x * SCALE - CROP_ORIGIN[0]), round(p0.y * SCALE - CROP_ORIGIN[1])), (round(p1.x * SCALE - CROP_ORIGIN[0]), round(p1.y * SCALE - CROP_ORIGIN[1]))]
        elif item[0] == "c":
            p0, p1, p2, p3 = item[1:5]
            pts = bezier(np.array([p0.x, p0.y]), np.array([p1.x, p1.y]), np.array([p2.x, p2.y]), np.array([p3.x, p3.y]))
        else:
            continue
        dr.line(pts, fill=1, width=stroke_w, joint="curve")
        if current and pts:
            dr.line([current, pts[0]], fill=1, width=stroke_w)
        current = pts[-1] if pts else current
        all_pts.extend(pts)
    if fill_small and len(all_pts) >= 3:
        dr.polygon(all_pts, fill=1)
    return np.array(im, dtype=bool)


def build_graphics(page, crop_img: Image.Image):
    arr = np.array(crop_img.convert("RGB"))
    drawings = page.get_drawings()
    graphics = []
    occlusion_rows = []
    seq = 0
    for di, (semantic, role) in VISIBLE_DRAWINGS.items():
        d = drawings[di]
        seq += 1
        eid = f"V{seq:04d}"
        rect = d["rect"]
        fill_small = role == "ARROWHEAD"
        support = drawing_support(d, arr.shape[:2], fill_small)
        colorf = d.get("color") or d.get("fill")
        target = tuple(int(round(v * 255)) for v in colorf)
        mask = expected_color_mask(arr, support, target)
        ink = bbox_from_mask(mask)
        safe = f"{eid}.png"
        tight_mask_save(mask, ROOT / "masks/graphic" / safe)
        graphics.append({
            "element_id": eid,
            "safe_filename": safe,
            "kind": "GRAPHIC",
            "char": "",
            "codepoint": "",
            "semantic_parent": semantic,
            "role": role,
            "draw_index": di,
            "draw_type": d["type"],
            "stroke_width_pt": round(float(d.get("width") or 0.0), 6),
            "color_rgb": target,
            "bbox_pt": [round(float(v), 6) for v in rect],
            "bbox_px": list(pt_bbox_to_crop_px(rect)),
            "ink_bbox_px": list(ink) if ink else None,
            "ink_width_px": 0 if ink is None else ink[2] - ink[0],
            "ink_height_px": 0 if ink is None else ink[3] - ink[1],
            "ink_pixel_count": int(mask.sum()),
            "empty_mask_machine_flag": bool(mask.sum() == 0),
            "mask_relpath": f"masks/graphic/{safe}",
            "mask": mask,
        })
    for di, semantic in OCCLUDERS.items():
        d = drawings[di]
        support = drawing_support(d, arr.shape[:2], False)
        raw_white = support & (np.min(arr, axis=2) >= 245)
        safe = f"OCC{len(occlusion_rows)+1:03d}.png"
        tight_mask_save(raw_white, ROOT / "masks/occlusion" / safe)
        occlusion_rows.append({
            "occlusion_id": safe[:-4],
            "semantic_parent": semantic,
            "draw_index": di,
            "draw_type": d["type"],
            "stroke_width_pt": round(float(d.get("width") or 0.0), 6),
            "bbox_pt": json.dumps([round(float(v), 6) for v in d["rect"]]),
            "geometry_support_pixel_count": int(support.sum()),
            "raw_white_pixel_count": int(raw_white.sum()),
            "role": "OPAQUE_DOUBLE_BORDER_SEPARATOR",
            "mask_relpath": f"masks/occlusion/{safe}",
        })
    return graphics, occlusion_rows


def obj_public(o: dict) -> dict:
    return {k: v for k, v in o.items() if k != "mask"}


def coords(o):
    ys, xs = np.nonzero(o["mask"])
    return np.column_stack((xs, ys)).astype(np.float32)


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def threshold_for(a, b):
    if a["kind"] == b["kind"] == "GLYPH":
        if a["semantic_parent"] == b["semantic_parent"]:
            return "INTRA_SEMANTIC_PARENT", None
        return "TEXT_TEXT", 4.0
    if {a["kind"], b["kind"]} == {"GLYPH", "GRAPHIC"}:
        t = a if a["kind"] == "GLYPH" else b
        g = b if a["kind"] == "GLYPH" else a
        if g["role"] == "NODE_BORDER" and t["semantic_parent"].replace("state_", "node_border_") in g["semantic_parent"]:
            return "TEXT_NODE_BORDER", 5.0
        if g["role"] in {"TRANSITION_LINE", "ARROWHEAD", "AXIS_LINE", "RELATION_ARC", "NODE_BORDER"}:
            return "TEXT_GRAPHIC", 3.0
        return "TEXT_GRAPHIC", 3.0
    return "GRAPHIC_GRAPHIC", None


def structural_relation(a, b):
    s = {a["semantic_parent"], b["semantic_parent"]}
    expected = [
        {"axis_line", "axis_arrowhead"},
        {"transition_line_0_1", "transition_arrow_0_1"},
        {"transition_line_1_2", "transition_arrow_1_2"},
        {"transition_line_2_3", "transition_arrow_2_3"},
        {"transition_line_3_4", "transition_arrow_3_4"},
        {"transition_line_4_5", "transition_arrow_4_5"},
        {"transition_line_5_T", "transition_arrow_5_T"},
    ]
    for pair in expected:
        if s == pair:
            return "LINE_ARROWHEAD_CONNECTION_CANDIDATE"
    arc_nodes = ["node_border_t1_repeat", "node_border_t2_repeat"]
    if "repeat_correlation_arc" in s and any(x in s for x in arc_nodes):
        return "RELATION_ARC_NODE_CONNECTION_CANDIDATE"
    for t0, t1 in [("0", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "5"), ("5", "T")]:
        line = f"transition_line_{t0}_{t1}"
        if line in s and any(x.startswith(f"node_border_t{t0}") or x.startswith(f"node_border_t{t1}") for x in s):
            return "LINE_NODE_CONNECTION_CANDIDATE"
        arrow = f"transition_arrow_{t0}_{t1}"
        if arrow in s and any(x.startswith(f"node_border_t{t1}") for x in s):
            return "ARROWHEAD_TARGET_NODE_CONNECTION_CANDIDATE"
    return "NONE"


def build_pairs(objects):
    packed = {}
    points = {}
    trees = {}
    for o in objects:
        p = coords(o)
        points[o["element_id"]] = p
        packed[o["element_id"]] = set((p[:, 1].astype(np.int64) * 1930 + p[:, 0].astype(np.int64)).tolist()) if len(p) else set()
        trees[o["element_id"]] = cKDTree(p) if len(p) else None
    rows = []
    raw_overlap_pairs = []
    below = []
    for idx, (a, b) in enumerate(combinations(objects, 2), start=1):
        aid, bid = a["element_id"], b["element_id"]
        inter = len(packed[aid].intersection(packed[bid]))
        ag = bbox_gap(a["ink_bbox_px"], b["ink_bbox_px"]) if a["ink_bbox_px"] and b["ink_bbox_px"] else math.inf
        if inter:
            clear = 0.0
            method = "exact_raw_mask_intersection"
        elif ag <= 30 and trees[aid] is not None and trees[bid] is not None:
            pa, pb = points[aid], points[bid]
            if len(pa) <= len(pb):
                dist = float(trees[bid].query(pa, k=1)[0].min())
            else:
                dist = float(trees[aid].query(pb, k=1)[0].min())
            clear = max(0.0, dist - 1.0)
            method = "exact_raw_mask_kdtree"
        else:
            clear = float(ag)
            method = "raw_bbox_lower_bound"
        rel_class, hard_min = threshold_for(a, b)
        low = hard_min is not None and clear < hard_min
        row = {
            "pair_id": f"P{idx:05d}",
            "element_a": aid,
            "element_b": bid,
            "kind_a": a["kind"],
            "kind_b": b["kind"],
            "parent_a": a["semantic_parent"],
            "parent_b": b["semantic_parent"],
            "relationship_class": rel_class,
            "structural_relation": structural_relation(a, b),
            "raw_intersection_pixel_count": inter,
            "clearance_px": round(clear, 4) if math.isfinite(clear) else "INF",
            "distance_method": method,
            "hard_min_px": "N/A" if hard_min is None else hard_min,
            "below_numeric_gate_machine_flag": bool(low),
        }
        rows.append(row)
        if inter:
            raw_overlap_pairs.append(row)
        if low:
            below.append(row)
    return rows, raw_overlap_pairs, below


def make_overlay(crop_img, glyphs, graphics):
    im = crop_img.convert("RGB").copy()
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=10)
    for o in glyphs:
        b = o["ink_bbox_px"]
        if not b:
            continue
        d.rectangle(b, outline=(220, 30, 30), width=1)
        d.text((b[0], max(0, b[1] - 10)), o["element_id"], fill=(180, 0, 0), font=font)
    for o in graphics:
        b = o["ink_bbox_px"]
        if not b:
            continue
        d.rectangle(b, outline=(0, 90, 220), width=1)
        d.text((b[0], min(im.height - 10, b[3])), o["element_id"], fill=(0, 70, 180), font=font)
    im.save(ROOT / "after_text_measurement_overlay_300dpi.png")
    im.save(ROOT / "all_objects_overlay_300dpi.png")


def glyph_cell(crop_img, o):
    b = o["bbox_px"]
    x0, y0, x1, y1 = max(0, b[0]-3), max(0, b[1]-3), min(crop_img.width, b[2]+3), min(crop_img.height, b[3]+3)
    orig = crop_img.crop((x0, y0, x1, y1)).convert("RGB")
    local = o["mask"][y0:y1, x0:x1]
    ov = orig.copy()
    oa = np.array(ov)
    oa[local] = np.array([255, 0, 0], dtype=np.uint8)
    ov = Image.fromarray(oa)
    mo = Image.new("RGB", orig.size, "white")
    ma = np.array(mo)
    ma[local] = np.array([0, 0, 0], dtype=np.uint8)
    mo = Image.fromarray(ma)
    parts = [x.resize((x.width*8, x.height*8), Image.Resampling.NEAREST) for x in (orig, ov, mo)]
    cell = Image.new("RGB", (1240, 500), "white")
    dr = ImageDraw.Draw(cell)
    font = ImageFont.load_default(size=22)
    dr.text((8, 5), f"{o['element_id']} {o['codepoint']} h={o['ink_height_px']} px  O | TARGET | MASK", fill="black", font=font)
    for i, part in enumerate(parts):
        px = i*410 + 8
        py = 48
        cell.paste(part, (px, py))
    cell.paste(orig, (1120, 5))
    return cell


def make_glyph_sheets(crop_img, glyphs):
    index_rows = []
    per = 12
    for sn, start in enumerate(range(0, len(glyphs), per), start=1):
        chunk = glyphs[start:start+per]
        sheet = Image.new("RGB", (2480, 3000), (245, 245, 245))
        for k, o in enumerate(chunk):
            cell = glyph_cell(crop_img, o)
            x = (k % 2) * 1240
            y = (k // 2) * 500
            sheet.paste(cell, (x, y))
            index_rows.append({"element_id": o["element_id"], "sheet": f"glyph_contact_{sn:02d}.png", "cell": k+1})
        sheet.save(ROOT / "contact_glyph" / f"glyph_contact_{sn:02d}.png")
    write_csv(ROOT / "glyph_contact_index.csv", index_rows)


def graphic_cell(crop_img, o):
    b = o["ink_bbox_px"]
    x0, y0, x1, y1 = max(0, b[0]-5), max(0, b[1]-5), min(crop_img.width, b[2]+5), min(crop_img.height, b[3]+5)
    orig = crop_img.crop((x0, y0, x1, y1)).convert("RGB")
    local = o["mask"][y0:y1, x0:x1]
    oa = np.array(orig.copy())
    oa[local] = np.array([255, 0, 0], dtype=np.uint8)
    overlay = Image.fromarray(oa)
    maskim = Image.fromarray((~local * 255).astype(np.uint8), "L").convert("RGB")
    cell = Image.new("RGB", (1240, 520), "white")
    dr = ImageDraw.Draw(cell)
    font = ImageFont.load_default(size=20)
    dr.text((8, 5), f"{o['element_id']} draw={o['draw_index']} {o['semantic_parent']}  O | TARGET | MASK", fill="black", font=font)
    for i, part in enumerate((orig, overlay, maskim)):
        limw, limh = 390, 260
        scale = min(limw/part.width, limh/part.height, 1.0)
        if scale < 1:
            part = part.resize((max(1,int(part.width*scale)), max(1,int(part.height*scale))), Image.Resampling.NEAREST)
        cell.paste(part, (8+i*410, 48))
    cx, cy = ((x0+x1)//2, (y0+y1)//2)
    rx0, ry0, rx1, ry1 = max(0,cx-24), max(0,cy-24), min(crop_img.width,cx+24), min(crop_img.height,cy+24)
    detail = crop_img.crop((rx0,ry0,rx1,ry1)).resize(((rx1-rx0)*8,(ry1-ry0)*8), Image.Resampling.NEAREST)
    cell.paste(detail, (8, 320))
    dr.text((400, 330), "8x nearest center detail", fill="black", font=font)
    return cell


def make_graphic_sheets(crop_img, graphics):
    index_rows = []
    per = 4
    for sn, start in enumerate(range(0, len(graphics), per), start=1):
        chunk = graphics[start:start+per]
        sheet = Image.new("RGB", (2480, 1040), (245, 245, 245))
        for k, o in enumerate(chunk):
            cell = graphic_cell(crop_img, o)
            x = (k % 2) * 1240
            y = (k // 2) * 520
            sheet.paste(cell, (x, y))
            index_rows.append({"element_id": o["element_id"], "sheet": f"graphic_contact_{sn:02d}.png", "cell": k+1})
        sheet.save(ROOT / "contact_graphic" / f"graphic_contact_{sn:02d}.png")
    write_csv(ROOT / "graphic_contact_index.csv", index_rows)


def make_pair_matrix(objects, pair_rows):
    n = len(objects)
    scale = 4
    margin = 150
    im = Image.new("RGB", (margin+n*scale+30, margin+n*scale+120), "white")
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=16)
    d.text((10,10), "Pair clearance matrix: red=raw overlap; orange=below numeric gate; yellow=<=8px; blue=safe/lower-bound; gray=N/A", fill="black", font=font)
    for i in range(n):
        d.rectangle((margin+i*scale, margin+i*scale, margin+(i+1)*scale-1, margin+(i+1)*scale-1), fill=(40,40,40))
    lookup = {(r["element_a"],r["element_b"]): r for r in pair_rows}
    ids = [o["element_id"] for o in objects]
    for i in range(n):
        for j in range(i+1,n):
            r = lookup[(ids[i],ids[j])]
            if r["raw_intersection_pixel_count"]:
                c=(220,30,30)
            elif r["below_numeric_gate_machine_flag"]:
                c=(245,130,25)
            elif r["clearance_px"] != "INF" and float(r["clearance_px"]) <= 8:
                c=(245,220,70)
            elif r["hard_min_px"] == "N/A":
                c=(190,190,190)
            else:
                c=(80,140,220)
            for a,b in ((i,j),(j,i)):
                d.rectangle((margin+b*scale,margin+a*scale,margin+(b+1)*scale-1,margin+(a+1)*scale-1),fill=c)
    for i,o in enumerate(objects):
        if i%10==0 or i==n-1:
            d.text((margin+i*scale-8, margin-20), o["element_id"], fill="black", font=font)
            d.text((4, margin+i*scale-8), o["element_id"], fill="black", font=font)
    im.save(ROOT / "pair_clearance_matrix.png")


def make_role_matrix(objects, pair_rows):
    roles = sorted(set(o["role"] for o in objects))
    idx = {r:i for i,r in enumerate(roles)}
    counts = [[0]*len(roles) for _ in roles]
    mins = [[math.inf]*len(roles) for _ in roles]
    byid = {o["element_id"]:o for o in objects}
    for r in pair_rows:
        a,b=byid[r["element_a"]],byid[r["element_b"]]
        i,j=idx[a["role"]],idx[b["role"]]
        counts[i][j]+=1; counts[j][i]+=1
        if r["clearance_px"] != "INF":
            v=float(r["clearance_px"]); mins[i][j]=min(mins[i][j],v); mins[j][i]=min(mins[j][i],v)
    cellw,cellh=180,72
    im=Image.new("RGB",(260+len(roles)*cellw,160+len(roles)*cellh),"white")
    d=ImageDraw.Draw(im); font=ImageFont.load_default(size=15)
    d.text((10,10),"Role relationship matrix: pair count / minimum raw-mask clearance px",fill="black",font=font)
    for i,r in enumerate(roles):
        d.text((260+i*cellw,70),r,fill="black",font=font)
        d.text((5,160+i*cellh),r,fill="black",font=font)
    for i in range(len(roles)):
        for j in range(len(roles)):
            x0,y0=250+j*cellw,150+i*cellh
            d.rectangle((x0,y0,x0+cellw-2,y0+cellh-2),outline=(150,150,150))
            m="INF" if not math.isfinite(mins[i][j]) else f"{mins[i][j]:.1f}"
            d.text((x0+8,y0+18),f"n={counts[i][j]} / min={m}",fill="black",font=font)
    im.save(ROOT / "role_relationship_matrix.png")


def union_parent(glyphs, parent):
    m=np.zeros_like(glyphs[0]["mask"])
    ids=[]
    for g in glyphs:
        if g["semantic_parent"]==parent:
            m |= g["mask"]
            ids.append(g["element_id"])
    return m, ids


def closest_metrics(ma,mb):
    ya,xa=np.nonzero(ma); yb,xb=np.nonzero(mb)
    if len(xa)==0 or len(xb)==0: return math.inf,None,None,0
    sa=set((ya.astype(np.int64)*1930+xa.astype(np.int64)).tolist()); sb=set((yb.astype(np.int64)*1930+xb.astype(np.int64)).tolist())
    inter=len(sa.intersection(sb))
    pa=np.column_stack((xa,ya)).astype(np.float32); pb=np.column_stack((xb,yb)).astype(np.float32)
    tb=cKDTree(pb); ds,ix=tb.query(pa,k=1); k=int(np.argmin(ds)); dist=max(0.0,float(ds[k])-1.0)
    return dist,tuple(map(int,pa[k])),tuple(map(int,pb[int(ix[k])])),inter


def relation_quad(crop_img, ma, mb, title, pa, pb):
    ua=ma|mb; b=bbox_from_mask(ua)
    if b is None: b=(0,0,1,1)
    x0,y0,x1,y1=max(0,b[0]-12),max(0,b[1]-12),min(crop_img.width,b[2]+12),min(crop_img.height,b[3]+12)
    orig=crop_img.crop((x0,y0,x1,y1)).convert("RGB")
    oa=np.array(orig.copy()); la=ma[y0:y1,x0:x1]; lb=mb[y0:y1,x0:x1]
    oa[la]=np.array([255,0,0],dtype=np.uint8); oa[lb]=np.array([0,90,255],dtype=np.uint8); oa[la&lb]=np.array([255,0,255],dtype=np.uint8)
    ov=Image.fromarray(oa)
    maxw,maxh=900,420
    sc=min(maxw/orig.width,maxh/orig.height,1.0)
    def fit(z):
        return z if sc>=1 else z.resize((max(1,int(z.width*sc)),max(1,int(z.height*sc))),Image.Resampling.NEAREST)
    f1,f2=fit(orig),fit(ov)
    canvas=Image.new("RGB",(1900,950),"white"); d=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=20)
    d.text((10,5),title+" | red=A blue=B magenta=intersection",fill="black",font=font)
    canvas.paste(f1,(10,45)); canvas.paste(f2,(950,45))
    if pa and pb:
        cx=int(round((pa[0]+pb[0])/2)); cy=int(round((pa[1]+pb[1])/2))
    else: cx,cy=(x0+x1)//2,(y0+y1)//2
    rx0,ry0,rx1,ry1=max(0,cx-28),max(0,cy-28),min(crop_img.width,cx+28),min(crop_img.height,cy+28)
    det=crop_img.crop((rx0,ry0,rx1,ry1)).convert("RGB")
    da=np.array(det); dla=ma[ry0:ry1,rx0:rx1]; dlb=mb[ry0:ry1,rx0:rx1]
    da[dla]=np.array([255,0,0],dtype=np.uint8); da[dlb]=np.array([0,90,255],dtype=np.uint8); da[dla&dlb]=np.array([255,0,255],dtype=np.uint8)
    detov=Image.fromarray(da).resize((det.width*8,det.height*8),Image.Resampling.NEAREST)
    canvas.paste(detov,(10,500)); d.text((480,510),"8x nearest closest-point detail",fill="black",font=font)
    return canvas


def make_critical(crop_img,glyphs,graphics):
    gm={g["semantic_parent"]:g["mask"] for g in graphics}
    rels=[]
    for t in ["0","1","2","3","4","5","T"]:
        pm,ids=union_parent(glyphs,f"state_t{t}")
        gb=next(g for g in graphics if g["semantic_parent"].startswith(f"node_border_t{t}"))
        rels.append((f"state_t{t}_to_border",pm,gb["mask"],ids,[gb["element_id"]],5.0))
    for t in ["1","2"]:
        pm,ids=union_parent(glyphs,f"time_t{t}")
        gb=next(g for g in graphics if g["semantic_parent"]=="repeat_correlation_arc")
        rels.append((f"time_t{t}_to_repeat_arc",pm,gb["mask"],ids,[gb["element_id"]],3.0))
    specs=[
        ("repeat_annotation_to_arc","repeat_correlation","repeat_correlation_arc",3.0),
        ("keep_b_to_transition","keep_b","transition_line_1_2",3.0),
        ("kernel_formula_to_transition","kernel_formula","transition_line_2_3",3.0),
        ("kernel_formula_to_arrowhead","kernel_formula","transition_arrow_2_3",3.0),
        ("keep_c_to_transition","keep_c","transition_line_3_4",3.0),
        ("bottom_note_to_axis","spacing_double_circle","axis_line",3.0),
        ("axis_title_to_axis","axis_title","axis_line",3.0),
        ("axis_title_to_axis_arrowhead","axis_title","axis_arrowhead",3.0),
    ]
    for name,parent,gsem,thr in specs:
        pm,ids=union_parent(glyphs,parent); gb=next(g for g in graphics if g["semantic_parent"]==gsem)
        rels.append((name,pm,gb["mask"],ids,[gb["element_id"]],thr))
    rows=[]
    for i,(name,ma,mb,aids,bids,thr) in enumerate(rels,start=1):
        dist,pa,pb,inter=closest_metrics(ma,mb); rid=f"C{i:03d}"; fn=f"{rid}_{name}.png"
        relation_quad(crop_img,ma,mb,f"{rid} {name} distance={dist:.3f}px intersection={inter}",pa,pb).save(ROOT/"critical"/fn)
        rows.append({"critical_id":rid,"relationship":name,"element_ids_a":"|".join(aids),"element_ids_b":"|".join(bids),"raw_intersection_pixel_count":inter,"clearance_px":round(dist,4),"numeric_gate_px":thr,"below_numeric_gate_machine_flag":bool(dist<thr),"overlay_relpath":f"critical/{fn}"})
    write_csv(ROOT/"critical_index.csv",rows)
    return rows


def semantic_overlay(crop_img, graphics):
    im=crop_img.convert("RGB").copy(); d=ImageDraw.Draw(im); font=ImageFont.load_default(size=18)
    nodes=[next(g for g in graphics if g["semantic_parent"].startswith(f"node_border_t{t}")) for t in ["0","1","2","3","4","5","T"]]
    centers=[]
    for i,g in enumerate(nodes):
        b=g["ink_bbox_px"]; cx=(b[0]+b[2])//2; cy=(b[1]+b[3])//2; centers.append((cx,cy))
        d.ellipse((cx-10,cy-10,cx+10,cy+10),outline=(255,0,180),width=2); d.text((cx+12,cy-10),f"S{i}",fill=(180,0,120),font=font)
    for a,b in zip(centers,centers[1:]): d.line((a[0],a[1],b[0],b[1]),fill=(0,180,0),width=2)
    for i in range(6):
        dx=centers[i+1][0]-centers[i][0]; d.text(((centers[i][0]+centers[i+1][0])//2-25,420),f"dx={dx}px",fill=(0,120,0),font=font)
    d.rectangle((0,560,im.width-1,im.height-1),outline=(160,0,220),width=3)
    d.text((10,565),"caption semantics region: K; x->y; K(x,dy); positive mass; self-loop wording",fill=(120,0,170),font=font)
    d.text((10,10),"states=a,b,b,c,c,b,a | times=0,1,2,3,4,5,T | six directed transitions",fill=(0,80,160),font=font)
    im.save(ROOT/"semantic_checks_overlay_300dpi.png")
    return centers


def source_font_rows():
    text=SOURCE.read_text(encoding="utf-8")
    rows=[]
    import re
    for n,line in enumerate(text.splitlines(),start=1):
        for m in re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}",line):
            size=float(m.group(1)); base=float(m.group(2))
            rows.append({"source_line":n,"declared_pt":size,"baseline_pt":base,"cumulative_graphics_scale":1.0,"effective_pt":size,"legacy_9_5_delta_pt":round(size-9.5,3),"r168_status":"ADVISORY_MEASUREMENT_ONLY","source_excerpt":line.strip()})
    scale_hits=[]
    for token in ["resizebox","scalebox","transform shape","scale="]:
        if token in text: scale_hits.append(token)
    rows.append({"source_line":"scan","declared_pt":"N/A","baseline_pt":"N/A","cumulative_graphics_scale":1.0,"effective_pt":"N/A","legacy_9_5_delta_pt":"N/A","r168_status":"ADVISORY_MEASUREMENT_ONLY","source_excerpt":"scale/resize tokens="+("|".join(scale_hits) if scale_hits else "NONE")})
    return rows


def main():
    mkdirs()
    crop_img=Image.open(ROOT/"figure_crop_300dpi.png").convert("RGB")
    assert crop_img.size==(1930,706)
    doc=fitz.open(PDF); page=doc[PAGE_INDEX]
    glyphs=build_glyphs(page,crop_img)
    graphics,occlusions=build_graphics(page,crop_img)
    objects=glyphs+graphics
    assert len(glyphs)==142, len(glyphs)
    assert len(graphics)==22, len(graphics)
    pairs,overlaps,below=build_pairs(objects)
    assert len(pairs)==len(objects)*(len(objects)-1)//2==13366
    make_overlay(crop_img,glyphs,graphics)
    make_glyph_sheets(crop_img,glyphs)
    make_graphic_sheets(crop_img,graphics)
    make_pair_matrix(objects,pairs)
    make_role_matrix(objects,pairs)
    critical=make_critical(crop_img,glyphs,graphics)
    centers=semantic_overlay(crop_img,graphics)
    idmap=[{"element_id":o["element_id"],"safe_filename":o["safe_filename"],"ordinary_file_relpath":o["mask_relpath"]} for o in objects]
    write_csv(ROOT/"id_filename_map.csv",idmap)
    pixel_fields=["element_id","kind","char","codepoint","semantic_parent","role","bbox_pt","bbox_px","ink_bbox_px","ink_width_px","ink_height_px","ink_pixel_count","empty_mask_machine_flag","mask_relpath"]
    write_csv(ROOT/"after_pixel_measurements.csv",[{k:(json.dumps(o[k],ensure_ascii=False) if isinstance(o.get(k),(list,tuple,dict)) else o.get(k,"")) for k in pixel_fields} for o in objects],pixel_fields)
    font_fields=["element_id","char","codepoint","semantic_parent","role","font","pdf_size_pt","glyph_class","ink_height_px","ink_pixel_count","legacy_advisory_min_px","legacy_advisory_delta_px","empty_mask_machine_flag","replacement_or_tofu_codepoint_machine_flag"]
    write_csv(ROOT/"glyph_machine_measurements.csv",[{k:o.get(k,"") for k in font_fields} for o in glyphs],font_fields)
    write_csv(ROOT/"after_font_audit.csv",source_font_rows())
    write_csv(ROOT/"after_overlap_report.csv",pairs)
    write_csv(ROOT/"raw_overlap_pairs.csv",overlaps)
    write_csv(ROOT/"below_numeric_gate_pairs.csv",below)
    write_csv(ROOT/"occlusion_path_inventory.csv",occlusions)
    draw_rows=[]
    for g in graphics:
        draw_rows.append({"draw_index":g["draw_index"],"coverage_class":"VISIBLE_FOREGROUND","element_id":g["element_id"],"semantic_parent":g["semantic_parent"],"raw_mask_pixel_count":g["ink_pixel_count"],"mask_relpath":g["mask_relpath"]})
    for o in occlusions:
        draw_rows.append({"draw_index":o["draw_index"],"coverage_class":"OPAQUE_OCCLUSION_AUXILIARY","element_id":o["occlusion_id"],"semantic_parent":o["semantic_parent"],"raw_mask_pixel_count":o["raw_white_pixel_count"],"mask_relpath":o["mask_relpath"]})
    write_csv(ROOT/"drawing_path_coverage.csv",sorted(draw_rows,key=lambda r:int(r["draw_index"])))
    text_sequence="".join(g["char"] for g in glyphs)
    dx=[centers[i+1][0]-centers[i][0] for i in range(6)]
    sem={"state_sequence":["a","b","b","c","c","b","a"],"time_sequence":["0","1","2","3","4","5","T"],"node_center_px":centers,"adjacent_center_dx_px":dx,"adjacent_center_dx_range_px":max(dx)-min(dx),"visible_transition_line_count":6,"visible_transition_arrowhead_count":6,"axis_line_count":1,"axis_arrowhead_count":1,"repeat_double_border_nodes":["t1","t2","t3","t4"],"kernel_formula_pdf_text":"K(x_t, d x_{t+1})","caption_semantic_tokens":["K","x→y","K(x,dy)","y","positive mass","self-loop wording"],"page_text_sequence":text_sequence}
    write_json(ROOT/"semantic_machine_metrics.json",sem)
    objman=[obj_public(o) for o in objects]
    write_json(ROOT/"object_manifest.json",objman)
    page_sha=hashlib.sha256(PDF.read_bytes()).hexdigest().upper()
    crop_edges=[]
    for o in objects:
        b=o["ink_bbox_px"]
        edge=min(b[0],b[1],crop_img.width-b[2],crop_img.height-b[3]) if b else -1
        crop_edges.append({"element_id":o["element_id"],"crop_edge_clearance_px":edge,"touches_crop_edge_machine_flag":edge<=0})
    write_csv(ROOT/"crop_edge_clearance.csv",crop_edges)
    summary={
        "uid":"FIG-P598-01","candidate":"R104","physical_page":649,"pdf_sha256":page_sha,"pdf_bytes":PDF.stat().st_size,
        "page_pt":[float(page.rect.width),float(page.rect.height)],"page_native_300dpi_px":[2481,3508],"page_context_200dpi_px":[1654,2339],
        "figure_crop_300dpi_box_xywh":[250,2054,1930,706],"standalone_300dpi_box_xywh":[408,2058,1602,567],
        "glyph_count":len(glyphs),"visible_foreground_graphic_count":len(graphics),"occlusion_auxiliary_path_count":len(occlusions),
        "total_visible_object_count":len(objects),"unordered_pair_count":len(pairs),"expected_unordered_pair_count":13366,
        "empty_visible_masks":sum(bool(o["empty_mask_machine_flag"]) for o in objects),"replacement_or_tofu_codepoint_flags":sum(bool(g["replacement_or_tofu_codepoint_machine_flag"]) for g in glyphs),
        "raw_overlap_pair_count":len(overlaps),"below_numeric_gate_pair_count_machine":len(below),"critical_relation_count":len(critical),
        "minimum_crop_edge_clearance_px":min(r["crop_edge_clearance_px"] for r in crop_edges),
        "script_authored_human_fields":False,"r168_font_policy":"Legacy pt/pixel/taxonomy ratios recorded as advisory. Hard font gate reserved for missing/tofu, wrong glyph/codepoint/math semantics, genuinely unreadable, obvious severe visible imbalance, real clipping/overlap.",
    }
    write_json(ROOT/"machine_summary.json",summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
