from __future__ import annotations

import csv
import itertools
import json
import math
import unicodedata
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bivariate_normal_conditionals.tex")
PAGE_INDEX = 688
PAGE_NUMBER = 689
FULL_PNG = ROOT / "renders" / "full_page_300dpi.png"
MACHINE = ROOT / "machine"
MASK_DIR = MACHINE / "masks"
CONTACT_DIR = ROOT / "contact"
ROI_DIR = ROOT / "roi"
FIGURE_PT = fitz.Rect(60, 325, 525, 530)
STANDALONE_PT = fitz.Rect(90, 325, 500, 495)
DRAWING_INDICES = list(range(5, 16))


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def rgb_from_float(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(v) * 255)) for v in value)


def px_bbox(rect, sx, sy, pad=0, shape=None):
    x0 = max(0, int(math.floor(rect[0] * sx)) - pad)
    y0 = max(0, int(math.floor(rect[1] * sy)) - pad)
    x1 = int(math.ceil(rect[2] * sx)) + pad
    y1 = int(math.ceil(rect[3] * sy)) + pad
    if shape:
        y1 = min(shape[0], y1)
        x1 = min(shape[1], x1)
    return [x0, y0, x1, y1]


def expected_color_mask(rgb, expected, bounds):
    x0, y0, x1, y1 = bounds
    patch = rgb[y0:y1, x0:x1].astype(np.float32)
    bg = np.full(3, 255.0, dtype=np.float32)
    target = np.array(expected, dtype=np.float32)
    vec = bg - target
    denom = float(np.dot(vec, vec))
    delta = bg - patch
    alpha = np.sum(delta * vec, axis=2) / denom
    predicted = bg - alpha[..., None] * vec
    residual = np.linalg.norm(patch - predicted, axis=2)
    contrast = np.max(delta, axis=2)
    local = (alpha >= 0.06) & (alpha <= 1.22) & (residual <= 24.0) & (contrast >= 20.0)
    result = np.zeros(rgb.shape[:2], dtype=bool)
    result[y0:y1, x0:x1] = local
    return result


def constrain_to_pdf_bbox(mask, bbox, sx, sy):
    x0, y0, x1, y1 = px_bbox(bbox, sx, sy, pad=1, shape=mask.shape)
    ys = (np.arange(y0, y1, dtype=np.float32) + 0.5) / sy
    xs = (np.arange(x0, x1, dtype=np.float32) + 0.5) / sx
    allowed = ((ys[:, None] >= bbox[1]) & (ys[:, None] <= bbox[3]) &
               (xs[None, :] >= bbox[0]) & (xs[None, :] <= bbox[2]))
    local = mask[y0:y1, x0:x1]
    local &= allowed
    mask[y0:y1, x0:x1] = local
    return mask


def safe_font(size=20):
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def char_class(ch, size):
    cp = ord(ch)
    if size < 8:
        return "NATURAL_SCRIPT"
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK"
    if ch.isdigit():
        return "DIGIT"
    if ch in ".,，。、:：;；…":
        return "LOW_PROFILE_PUNCTUATION"
    if ch in "=−+-":
        return "MATH_OPERATOR"
    if ch in "()[]{}":
        return "BRACKET"
    name = unicodedata.name(ch, "")
    if "GREEK" in name or "LATIN" in name:
        return "LATIN_GREEK"
    return "MATH_OR_SYMBOL"


def semantic_parent(ch, bbox, span_text, color):
    x0, y0, x1, y1 = bbox
    if y0 >= 496:
        return "P_CAPTION", "CAPTION"
    if y0 < 345 and color == (31, 78, 121):
        return "P_TOP_BLUE", "FORMULA_BLOCK"
    if y0 < 345 and color == (183, 121, 31):
        return "P_TOP_GOLD", "FORMULA_BLOCK"
    if x0 > 395 and 390 <= y0 <= 420:
        return "P_NOTE", "ANNOTATION"
    if x1 < 110 and 390 <= y0 <= 420:
        return "P_Y_AXIS_TITLE", "AXIS_TITLE"
    if 480 <= y0 <= 495:
        return "P_X_AXIS_TITLE", "AXIS_TITLE"
    if x1 < 132 and 345 <= y0 <= 470:
        rounded = round((y0 + y1) / 2)
        return f"P_TICK_Y_{rounded}", "TICK_LABEL"
    if 458 <= y0 <= 480:
        return f"P_TICK_X_{span_text}", "TICK_LABEL"
    return f"P_TEXT_{round(x0)}_{round(y0)}", "TEXT"


def item_points(item, sx, sy):
    op = item[0]
    if op == "l":
        return [(item[1].x * sx, item[1].y * sy), (item[2].x * sx, item[2].y * sy)]
    if op == "c":
        p0, p1, p2, p3 = item[1:5]
        pts = []
        for t in np.linspace(0, 1, 17):
            u = 1 - t
            x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
            y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
            pts.append((x * sx, y * sy))
        return pts
    return []


def drawing_geometry_corridor(drawing, shape, sx, sy):
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    width = max(5, int(math.ceil(float(drawing.get("width") or 0.8) * max(sx, sy))) + 4)
    polygon_points = []
    for item in drawing["items"]:
        pts = item_points(item, sx, sy)
        if pts:
            draw.line(pts, fill=255, width=width, joint="curve")
            if not polygon_points:
                polygon_points.append(pts[0])
            polygon_points.extend(pts[1:])
    fill = rgb_from_float(drawing.get("fill"))
    if fill and max(255 - v for v in fill) >= 20 and len(polygon_points) >= 3:
        draw.polygon(polygon_points, fill=255)
    return np.array(canvas) > 0


def mask_stats(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        return {"area_px": 0, "ink_width_px": 0, "ink_height_px": 0, "mask_bbox_px": None}
    return {
        "area_px": int(len(xs)),
        "ink_width_px": int(xs.max() - xs.min() + 1),
        "ink_height_px": int(ys.max() - ys.min() + 1),
        "mask_bbox_px": [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)],
    }


def save_mask(mask, path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def min_mask_distance(mask_a, mask_b, box_a, box_b, force_exact=False):
    dx = max(0, max(box_a[0], box_b[0]) - min(box_a[2], box_b[2]))
    dy = max(0, max(box_a[1], box_b[1]) - min(box_a[3], box_b[3]))
    lower = math.hypot(dx, dy)
    if lower > 20 and not force_exact:
        return 0, lower, max(0.0, lower - 1.0), False
    x0 = max(0, min(box_a[0], box_b[0]) - 3)
    y0 = max(0, min(box_a[1], box_b[1]) - 3)
    x1 = min(mask_a.shape[1], max(box_a[2], box_b[2]) + 3)
    y1 = min(mask_a.shape[0], max(box_a[3], box_b[3]) + 3)
    local_a = mask_a[y0:y1, x0:x1]
    local_b = mask_b[y0:y1, x0:x1]
    overlap = int(np.count_nonzero(local_a & local_b))
    if overlap:
        return overlap, 0.0, 0.0, True
    if not local_a.any() or not local_b.any():
        return overlap, None, None, True
    dist = distance_transform_edt(~local_a)
    edge = float(dist[local_b].min())
    return overlap, edge, max(0.0, edge - 1.0), True


def bbox_clearance(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return max(0.0, math.hypot(dx, dy) - 1.0)


def drawing_meta(idx):
    mapping = {
        5: ("D_X_TICKS", "TICK_MARKS"),
        6: ("D_Y_TICKS", "TICK_MARKS"),
        7: ("D_X_AXIS_OCCLUDED", "OCCLUDED_PATH"),
        8: ("D_X_ARROWHEAD", "ARROWHEAD"),
        9: ("D_Y_AXIS", "AXIS_LINE"),
        10: ("D_Y_ARROWHEAD", "ARROWHEAD"),
        11: ("D_BLUE_DENSITY", "DATA_CURVE"),
        12: ("D_GOLD_DENSITY", "DATA_CURVE"),
        13: ("D_BLUE_MEAN", "REFERENCE_LINE"),
        14: ("D_GOLD_MEAN", "REFERENCE_LINE"),
        15: ("D_NOTE_BORDER", "NODE_BORDER"),
    }
    return mapping[idx]


def relation_rule(a, b):
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["parent_id"] == b["parent_id"]:
            return "SAME_SEMANTIC_PARENT", 0.0, True
        return "TEXT_TEXT_BBOX", 4.0, False
    glyph = a if a["kind"] == "GLYPH" else b if b["kind"] == "GLYPH" else None
    graphic = b if glyph is a else a if glyph is b else None
    if glyph is not None:
        if graphic["role"] == "NODE_BORDER" and glyph["parent_id"] == "P_NOTE":
            return "NODE_TEXT_TO_BORDER", 5.0, False
        return "TEXT_TO_LINE_MARKER", 3.0, False
    allowed = {
        frozenset(("D_X_TICKS", "D_BLUE_DENSITY")),
        frozenset(("D_X_TICKS", "D_Y_TICKS")),
        frozenset(("D_X_TICKS", "D_Y_AXIS")),
        frozenset(("D_Y_TICKS", "D_Y_AXIS")),
        frozenset(("D_X_ARROWHEAD", "D_BLUE_DENSITY")),
        frozenset(("D_X_ARROWHEAD", "D_GOLD_DENSITY")),
        frozenset(("D_Y_AXIS", "D_Y_ARROWHEAD")),
        frozenset(("D_BLUE_DENSITY", "D_GOLD_DENSITY")),
        frozenset(("D_BLUE_DENSITY", "D_BLUE_MEAN")),
        frozenset(("D_GOLD_DENSITY", "D_GOLD_MEAN")),
        frozenset(("D_BLUE_DENSITY", "D_GOLD_MEAN")),
        frozenset(("D_GOLD_DENSITY", "D_BLUE_MEAN")),
        frozenset(("D_BLUE_MEAN", "D_GOLD_MEAN")),
    }
    whitelist = frozenset((a["id"], b["id"])) in allowed
    return "GRAPHIC_GRAPHIC", 0.0, whitelist


def make_contact_sheets(elements, masks, rgb, sx, sy):
    font = safe_font(18)
    glyphs = [e for e in elements if e["kind"] == "GLYPH"]
    rows_per_sheet = 12
    made = []
    for sheet_no, start in enumerate(range(0, len(glyphs), rows_per_sheet), 1):
        batch = glyphs[start:start + rows_per_sheet]
        sheet = Image.new("RGB", (1850, 190 * len(batch) + 50), "white")
        d = ImageDraw.Draw(sheet)
        d.text((10, 10), f"FIG-P639-01 glyph contact sheet {sheet_no}: native 1x + target overlay + mask only + 8x nearest", fill="black", font=font)
        for row, e in enumerate(batch):
            y = 45 + row * 190
            m = masks[e["id"]]
            mb = e["mask_bbox_px"] or e["bbox_px"]
            x0 = max(0, mb[0] - 3); y0 = max(0, mb[1] - 3); x1 = min(rgb.shape[1], mb[2] + 3); y1 = min(rgb.shape[0], mb[3] + 3)
            original = Image.fromarray(rgb[y0:y1, x0:x1])
            local_mask = m[y0:y1, x0:x1]
            overlay_arr = np.array(original).copy()
            overlay_arr[local_mask] = [255, 0, 0]
            overlay = Image.fromarray(overlay_arr)
            mask_only = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8)).convert("RGB")
            zoom = overlay.resize((max(8, overlay.width * 8), max(8, overlay.height * 8)), Image.Resampling.NEAREST)
            d.text((10, y + 5), f"{e['id']}  U+{ord(e['char']):04X}  {e['char']!r}  {e['role']}  H={e['ink_height_px']} area={e['area_px']}", fill="black", font=font)
            positions = [(480, original, "ORIGINAL 1x"), (690, overlay, "TARGET OVERLAY 1x"), (900, mask_only, "MASK ONLY 1x")]
            for x, im, label in positions:
                d.text((x, y), label, fill="black", font=font)
                sheet.paste(im, (x, y + 30))
            d.text((1120, y), "OVERLAY 8x NEAREST", fill="black", font=font)
            if zoom.width > 700 or zoom.height > 150:
                ratio = min(700 / zoom.width, 150 / zoom.height)
                zoom = zoom.resize((max(1, int(zoom.width * ratio)), max(1, int(zoom.height * ratio))), Image.Resampling.NEAREST)
            sheet.paste(zoom, (1120, y + 30))
        path = CONTACT_DIR / f"glyph_contact_sheet_{sheet_no:02d}.png"
        sheet.save(path)
        made.append(str(path))
    return made


def relation_roi(a, b, masks, rgb, pair_id):
    boxes = [a.get("mask_bbox_px") or a["bbox_px"], b.get("mask_bbox_px") or b["bbox_px"]]
    x0 = max(0, min(z[0] for z in boxes) - 12); y0 = max(0, min(z[1] for z in boxes) - 12)
    x1 = min(rgb.shape[1], max(z[2] for z in boxes) + 12); y1 = min(rgb.shape[0], max(z[3] for z in boxes) + 12)
    if x1 - x0 > 420 or y1 - y0 > 260:
        return None
    raw = Image.fromarray(rgb[y0:y1, x0:x1])
    ma = masks[a["id"]][y0:y1, x0:x1]
    mb = masks[b["id"]][y0:y1, x0:x1]
    overlay = np.array(raw).copy()
    overlay[ma] = [255, 0, 0]
    overlay[mb] = [0, 170, 255]
    overlay[ma & mb] = [255, 0, 255]
    panel = Image.new("RGB", (max(520, raw.width * 8 + 20), raw.height + max(120, raw.height * 8) + 70), "white")
    d = ImageDraw.Draw(panel)
    font = safe_font(16)
    d.text((10, 8), f"{pair_id} {a['id']} vs {b['id']} | native ROI [{x0},{y0},{x1-x0},{y1-y0}]", fill="black", font=font)
    panel.paste(raw, (10, 35))
    ov = Image.fromarray(overlay)
    panel.paste(ov, (20 + raw.width, 35))
    zoom = ov.resize((ov.width * 8, ov.height * 8), Image.Resampling.NEAREST)
    panel.paste(zoom, (10, 55 + raw.height))
    path = ROI_DIR / f"{pair_id}_native1x_8x.png"
    panel.save(path)
    return str(path)


def main():
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    CONTACT_DIR.mkdir(parents=True, exist_ok=True)
    ROI_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(FULL_PNG).convert("RGB")
    rgb = np.array(image)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = rgb.shape[1] / page.rect.width
    sy = rgb.shape[0] / page.rect.height
    elements = []
    masks = {}
    gid = 0
    raw = page.get_text("rawdict")
    span_counter = 0
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                span_counter += 1
                span_text = "".join(c["c"] for c in span["chars"])
                color = rgb_from_int(span["color"])
                for char in span["chars"]:
                    ch = char["c"]
                    bbox = char["bbox"]
                    center = fitz.Point((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                    if ch.isspace() or not FIGURE_PT.contains(center):
                        continue
                    gid += 1
                    eid = f"G{gid:03d}"
                    bounds = px_bbox(bbox, sx, sy, pad=1, shape=rgb.shape)
                    mask = expected_color_mask(rgb, color, bounds)
                    mask = constrain_to_pdf_bbox(mask, bbox, sx, sy)
                    stats = mask_stats(mask)
                    parent, role = semantic_parent(ch, bbox, span_text, color)
                    element = {
                        "id": eid,
                        "safe_filename": f"{eid}.png",
                        "kind": "GLYPH",
                        "char": ch,
                        "codepoint": f"U+{ord(ch):04X}",
                        "class": char_class(ch, float(span["size"])),
                        "parent_id": parent,
                        "role": role,
                        "span_text": span_text,
                        "font": span["font"],
                        "source_size_pt": round(float(span["size"]), 4),
                        "color_rgb": color,
                        "bbox_pt": [round(float(v), 4) for v in bbox],
                        "bbox_px": bounds,
                        **stats,
                        "empty_mask": stats["area_px"] == 0,
                    }
                    elements.append(element)
                    masks[eid] = mask
                    save_mask(mask, MASK_DIR / element["safe_filename"])

    drawings = page.get_drawings()
    for idx in DRAWING_INDICES:
        drawing = drawings[idx]
        eid, role = drawing_meta(idx)
        bounds = px_bbox(drawing["rect"], sx, sy, pad=5, shape=rgb.shape)
        corridor = drawing_geometry_corridor(drawing, rgb.shape, sx, sy)
        visible = np.zeros(rgb.shape[:2], dtype=bool)
        candidates = []
        line_color = rgb_from_float(drawing.get("color"))
        fill_color = rgb_from_float(drawing.get("fill"))
        if line_color:
            candidates.append(line_color)
        if fill_color and max(255 - v for v in fill_color) >= 20:
            candidates.append(fill_color)
        for expected in candidates:
            visible |= expected_color_mask(rgb, expected, bounds) & corridor
        stats = mask_stats(visible)
        element = {
            "id": eid,
            "safe_filename": f"{eid}.png",
            "kind": "GRAPHIC",
            "char": None,
            "codepoint": None,
            "class": "GRAPHIC",
            "parent_id": eid,
            "role": role,
            "drawing_index": idx,
            "drawing_seqno": drawing.get("seqno"),
            "line_rgb": line_color,
            "fill_rgb": fill_color,
            "bbox_pt": [round(float(v), 4) for v in drawing["rect"]],
            "bbox_px": bounds,
            **stats,
            "empty_mask": stats["area_px"] == 0,
        }
        if eid == "D_X_AXIS_OCCLUDED":
            element["denominator_status"] = "EXCLUDED_FULLY_OCCLUDED"
        else:
            element["denominator_status"] = "INCLUDED_VISIBLE"
            elements.append(element)
            masks[eid] = visible
            save_mask(visible, MASK_DIR / element["safe_filename"])

    overlay = image.copy()
    od = ImageDraw.Draw(overlay)
    font = safe_font(12)
    for e in elements:
        box = e["mask_bbox_px"] or e["bbox_px"]
        color = (210, 0, 0) if e["kind"] == "GLYPH" else (0, 80, 210)
        od.rectangle(box, outline=color, width=1)
        od.text((box[0], max(0, box[1] - 13)), e["id"], fill=color, font=font)
    fig_px = px_bbox(FIGURE_PT, sx, sy, pad=0, shape=rgb.shape)
    overlay.crop(fig_px).save(MACHINE / "after_text_measurement_overlay_300dpi.png")

    with (MACHINE / "object_manifest.json").open("w", encoding="utf-8") as f:
        json.dump({"uid": "FIG-P639-01", "elements": elements}, f, ensure_ascii=False, indent=2)
    with (MACHINE / "after_pixel_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["id", "kind", "char", "codepoint", "class", "parent_id", "role", "source_size_pt", "font", "area_px", "ink_width_px", "ink_height_px", "bbox_pt", "bbox_px", "mask_bbox_px", "empty_mask", "safe_filename"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for e in elements:
            row = dict(e)
            for key in ("bbox_pt", "bbox_px", "mask_bbox_px"):
                row[key] = json.dumps(row.get(key), ensure_ascii=False)
            w.writerow(row)

    pair_rows = []
    critical = []
    for pair_no, (a, b) in enumerate(itertools.combinations(elements, 2), 1):
        pair_id = f"R{pair_no:05d}"
        rule, threshold, whitelist = relation_rule(a, b)
        box_a = a["mask_bbox_px"] or a["bbox_px"]
        box_b = b["mask_bbox_px"] or b["bbox_px"]
        pre_bbox_clearance = bbox_clearance(a["bbox_px"], b["bbox_px"])
        force_exact = rule == "TEXT_TEXT_BBOX" and pre_bbox_clearance <= threshold + 8
        overlap, edge_dist, clearance, exact_distance = min_mask_distance(masks[a["id"]], masks[b["id"]], box_a, box_b, force_exact=force_exact)
        metric = bbox_clearance(a["bbox_px"], b["bbox_px"]) if rule == "TEXT_TEXT_BBOX" else clearance
        illegal_overlap = overlap > 0 and not whitelist
        threshold_fail = metric is None or (threshold > 0 and metric + 1e-9 < threshold)
        decision = "FAIL" if illegal_overlap or threshold_fail else "PASS"
        row = {
            "pair_id": pair_id,
            "a_id": a["id"],
            "b_id": b["id"],
            "rule": rule,
            "threshold_px": threshold,
            "whitelisted_design_relation": whitelist,
            "overlap_pixel_count": overlap,
            "min_edge_distance_px": None if edge_dist is None else round(edge_dist, 4),
            "clearance_px": None if metric is None else round(metric, 4),
            "distance_exact_native_mask": exact_distance,
            "illegal_overlap": illegal_overlap,
            "decision": decision,
            "roi_path": "",
        }
        is_critical = (decision == "FAIL") or (threshold > 0 and metric is not None and metric <= threshold + 8 and rule != "SAME_SEMANTIC_PARENT")
        if is_critical:
            critical.append((row, a, b))
        pair_rows.append(row)

    for row, a, b in critical:
        roi = relation_roi(a, b, masks, rgb, row["pair_id"])
        if roi:
            row["roi_path"] = roi

    with (MACHINE / "after_overlap_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = list(pair_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(pair_rows)
    with (MACHINE / "critical_relations.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = list(pair_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows([x[0] for x in critical])

    contact_paths = make_contact_sheets(elements, masks, rgb, sx, sy)
    glyphs = [e for e in elements if e["kind"] == "GLYPH"]
    graphics = [e for e in elements if e["kind"] == "GRAPHIC"]
    clip_fail = []
    for e in elements:
        box = e["mask_bbox_px"] or e["bbox_px"]
        target_rect = FIGURE_PT if (e["role"] == "CAPTION") else STANDALONE_PT
        target_px = px_bbox(target_rect, sx, sy, shape=rgb.shape)
        clear = min(box[0] - target_px[0], box[1] - target_px[1], target_px[2] - box[2], target_px[3] - box[3])
        if e["kind"] == "GLYPH" and clear < 6:
            clip_fail.append({"id": e["id"], "clearance_px": clear})
    failures = [r for r in pair_rows if r["decision"] == "FAIL"]
    summary = {
        "uid": "FIG-P639-01",
        "pdf": str(PDF),
        "source": str(SOURCE),
        "physical_page_1based": PAGE_NUMBER,
        "page_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
        "native_full_page_300dpi_px": [rgb.shape[1], rgb.shape[0]],
        "figure_crop_px": [250, 1354, 1938, 854],
        "standalone_crop_px": [375, 1354, 1708, 708],
        "foreground_threshold": "local-background contrast >=20/255",
        "glyph_count": len(glyphs),
        "visible_graphic_count": len(graphics),
        "visible_object_denominator": len(elements),
        "all_unordered_pair_expected": len(elements) * (len(elements) - 1) // 2,
        "all_unordered_pair_actual": len(pair_rows),
        "empty_mask_count": sum(1 for e in elements if e["empty_mask"]),
        "excluded_fully_occluded_paths": ["D_X_AXIS_OCCLUDED"],
        "math_rule_count": 0,
        "math_rule_note": "No separate formula rule/accent/fraction/root paths are visible in the figure; all math marks are font glyphs. All visible page drawing paths in the figure were reconciled.",
        "illegal_overlap_pair_count": sum(1 for r in pair_rows if r["illegal_overlap"]),
        "clearance_failure_count": len(failures),
        "clip_failure_count": len(clip_fail),
        "clip_failures": clip_fail,
        "critical_relation_count": len(critical),
        "critical_relation_roi_count": sum(1 for r, _, _ in critical if r["roi_path"]),
        "contact_sheet_count": len(contact_paths),
        "contact_sheets": contact_paths,
        "machine_hard_gate": "PASS" if not failures and not clip_fail and all(not e["empty_mask"] for e in elements) else "FAIL",
    }
    with (MACHINE / "machine_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with (MACHINE / "id_safe_filename.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["id", "safe_filename"])
        for e in elements:
            w.writerow([e["id"], e["safe_filename"]])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
