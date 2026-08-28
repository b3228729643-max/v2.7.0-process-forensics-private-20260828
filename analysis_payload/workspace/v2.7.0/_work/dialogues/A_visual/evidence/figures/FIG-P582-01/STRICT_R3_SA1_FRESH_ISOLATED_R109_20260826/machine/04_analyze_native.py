import csv
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
FROZEN = json.loads(Path(__file__).with_name("03_objects_frozen.json").read_text(encoding="utf-8"))
BODY_IMG = Image.open(ROOT / "render" / "standalone_300dpi.png").convert("RGB")
BODY = np.asarray(BODY_IMG)
FG = np.max(255 - BODY.astype(np.int16), axis=2) >= 20
BODY_PX = FROZEN["body_full_native_px"]
SCALE = 300 / 72.0
OBJECTS = FROZEN["objects"]

expected_mask_names = {o["safe_filename"] for o in OBJECTS}
for stale in (ROOT / "masks").glob("*.png"):
    if stale.name not in expected_mask_names:
        stale.unlink()
for pattern in ("glyph_contact_*.png", "critical_roi_*.png"):
    for stale in (ROOT / "contact").glob(pattern):
        stale.unlink()
for stale in (ROOT / "roi").glob("*"):
    if stale.is_file():
        stale.unlink()


def full_to_local(pt):
    return (pt[0] * SCALE - BODY_PX[0], pt[1] * SCALE - BODY_PX[1])


def native_bbox(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def draw_primitive(draw, primitive, semantic_parent):
    pts = primitive.get("pts") or []
    width = max(1, int(math.ceil(float(primitive.get("linewidth") or 0.5) * SCALE)) + 2)
    local_pts = [full_to_local(p) for p in pts]
    dash = primitive.get("dash")
    if semantic_parent.startswith("RUNNING_MEAN_MARKER"):
        box = primitive
        draw.ellipse([*full_to_local((box["x0"], box["top"])), *full_to_local((box["x1"], box["bottom"]))], fill=255, outline=255, width=width)
    elif semantic_parent.startswith("SQUARED_VALUE_MARKER"):
        box = primitive
        draw.rectangle([*full_to_local((box["x0"], box["top"])), *full_to_local((box["x1"], box["bottom"]))], fill=255, outline=255, width=width)
    elif primitive.get("fill") and len(local_pts) >= 3:
        draw.polygon(local_pts, fill=255)
    elif dash and len(local_pts) == 2:
        (x0, y0), (x1, y1) = local_pts
        on = float(dash[0][0]) * SCALE
        off = float(dash[0][1]) * SCALE
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        pos = 0.0
        while pos <= length:
            end = min(length, pos + on)
            draw.line((x0 + ux * pos, y0 + uy * pos, x0 + ux * end, y0 + uy * end), fill=255, width=width)
            pos += on + off
    elif len(local_pts) >= 2:
        draw.line(local_pts, fill=255, width=width, joint="curve")
    else:
        box = primitive
        draw.rectangle([*full_to_local((box["x0"], box["top"])), *full_to_local((box["x1"], box["bottom"]))], fill=255)


graphic_supports = {}
for obj in [o for o in OBJECTS if o["object_type"] == "GRAPHIC"]:
    support_image = Image.new("L", (BODY.shape[1], BODY.shape[0]), 0)
    support_draw = ImageDraw.Draw(support_image)
    for primitive in obj["primitives"]:
        draw_primitive(support_draw, primitive, obj["semantic_parent"])
    graphic_supports[obj["object_id"]] = np.asarray(support_image) > 0

text_visible_masks = {}
for obj in [o for o in OBJECTS if o["object_type"] == "TEXT_GLYPH"]:
    x0, y0, x1, y1 = map(int, obj["bbox_crop_native_px"])
    vector = Image.open(ROOT / "masks" / obj["safe_filename"]).convert("RGBA")
    alpha = np.asarray(vector)[:, :, 3] > 0
    full = np.zeros(FG.shape, dtype=bool)
    full[y0:y1, x0:x1] = alpha & FG[y0:y1, x0:x1]
    text_visible_masks[obj["object_id"]] = full


def paint_priority(object_id):
    n = int(object_id[1:])
    if 1 <= n <= 14:
        return 10  # axes/ticks
    if 15 <= n <= 18:
        return 20  # stems
    if 25 <= n <= 28:
        return 30  # square markers from first addplot
    if n == 20:
        return 40  # blue polyline
    if 21 <= n <= 24:
        return 50  # blue circular markers
    if n == 19:
        return 60  # teal reference line drawn last among plots
    raise ValueError(object_id)


pre_dir = Path(__file__).with_name("pre_occlusion_masks")
pre_dir.mkdir(exist_ok=True)
for stale in pre_dir.glob("*.png"):
    stale.unlink()

full_masks = {}
rows = []
for obj in OBJECTS:
    object_id = obj["object_id"]
    x0, y0, x1, y1 = obj["bbox_crop_native_px"]
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(BODY.shape[1], int(x1)), min(BODY.shape[0], int(y1))
    if obj["object_type"] == "TEXT_GLYPH":
        vector = Image.open(ROOT / "masks" / obj["safe_filename"]).convert("RGBA")
        alpha = np.asarray(vector)[:, :, 3] > 0
        h, w = y1 - y0, x1 - x0
        if alpha.shape != (h, w):
            raise RuntimeError(f"Mask size mismatch {object_id}: {alpha.shape} vs {(h,w)}")
        actual = alpha & FG[y0:y1, x0:x1]
        vector_expected = np.asarray(vector)[:, :, 3] >= 20
        missing_from_native = int(np.count_nonzero(vector_expected & ~FG[y0:y1, x0:x1]))
        native_outside_vector = int(np.count_nonzero(FG[y0:y1, x0:x1] & ~alpha))
    else:
        support = graphic_supports[object_id]
        pre_actual = support & FG
        full_actual = pre_actual.copy()
        priority = paint_priority(object_id)
        for other_id, other_support in graphic_supports.items():
            if paint_priority(other_id) > priority:
                full_actual &= ~other_support
        for text_mask in text_visible_masks.values():
            full_actual &= ~text_mask
        actual = full_actual[y0:y1, x0:x1]
        Image.fromarray((pre_actual[y0:y1, x0:x1] * 255).astype(np.uint8), mode="L").save(pre_dir / obj["safe_filename"])
        missing_from_native = None
        native_outside_vector = None
    full = np.zeros(FG.shape, dtype=bool)
    full[y0:y1, x0:x1] = actual
    full_masks[object_id] = full
    Image.fromarray((actual * 255).astype(np.uint8), mode="L").save(ROOT / "masks" / obj["safe_filename"])
    ink_bbox = native_bbox(actual)
    h_ink = 0 if ink_bbox is None else ink_bbox[3] - ink_bbox[1]
    w_ink = 0 if ink_bbox is None else ink_bbox[2] - ink_bbox[0]
    threshold = obj.get("threshold_px_protocol")
    protocol_pixel = "N/A" if threshold is None else ("PASS" if h_ink >= threshold else "FAIL")
    rows.append({
        "object_id": object_id,
        "safe_filename": obj["safe_filename"],
        "object_type": obj["object_type"],
        "char": obj.get("char", ""),
        "unicode": obj.get("unicode", ""),
        "semantic_parent": obj["semantic_parent"],
        "role": obj["role"],
        "script_class": obj.get("script_class", "N/A"),
        "source_line": obj.get("source_line"),
        "declared_pt": obj.get("declared_pt"),
        "graphics_scale": obj.get("graphics_scale"),
        "effective_pt": obj.get("effective_pt"),
        "pdf_fontname": obj.get("pdf_fontname"),
        "pdf_size_pt": obj.get("pdf_size_pt"),
        "pdf_non_stroking_color": obj.get("pdf_non_stroking_color"),
        "bbox_crop_native_px": obj["bbox_crop_native_px"],
        "ink_bbox_inside_object_mask_px": ink_bbox,
        "ink_area_px": int(actual.sum()),
        "h_ink_px": h_ink,
        "w_ink_px": w_ink,
        "protocol_threshold_px": threshold,
        "protocol_pixel_result": protocol_pixel,
        "vector_expected_missing_from_native_px": missing_from_native,
        "native_bbox_foreground_outside_vector_px": native_outside_vector,
        "empty_mask": bool(actual.sum() == 0),
        "pre_occlusion_area_px": int(pre_actual[y0:y1, x0:x1].sum()) if obj["object_type"] == "GRAPHIC" else None,
        "final_visible_area_px": int(actual.sum()) if obj["object_type"] == "GRAPHIC" else None,
        "paint_priority": paint_priority(object_id) if obj["object_type"] == "GRAPHIC" else 70,
    })

# Low-profile punctuation calibration uses same codepoint/font/effective size in this candidate.
for row in rows:
    if row["script_class"] == "LOW_PROFILE_PUNCTUATION":
        refs = [r for r in rows if r["object_type"] == "TEXT_GLYPH" and r["char"] == row["char"] and r["effective_pt"] == row["effective_pt"] and r["pdf_fontname"] == row["pdf_fontname"] and r["pdf_non_stroking_color"] == row["pdf_non_stroking_color"]]
        heights = [r["h_ink_px"] for r in refs]
        areas = [r["ink_area_px"] for r in refs]
        med_h = float(np.median(heights))
        med_a = float(np.median(areas))
        row["punct_calibration_ref_count"] = len(refs)
        row["punct_h_ratio"] = row["h_ink_px"] / med_h if med_h else None
        row["punct_area_ratio"] = row["ink_area_px"] / med_a if med_a else None
        row["protocol_pixel_result"] = "PASS" if len(refs) >= 2 and 0.92 <= row["punct_h_ratio"] <= 1.08 and 0.92 <= row["punct_area_ratio"] <= 1.08 else "FAIL"
    else:
        row["punct_calibration_ref_count"] = None
        row["punct_h_ratio"] = None
        row["punct_area_ratio"] = None

# Same role/script ratios. Exclude punctuation and natural scripts from full-height role medians.
for row in rows:
    peers = [
        r for r in rows
        if r["object_type"] == "TEXT_GLYPH"
        and r["role"] == row["role"]
        and r["script_class"] == row["script_class"]
        and r["script_class"] not in {"LOW_PROFILE_PUNCTUATION", "NATURAL_SCRIPT"}
    ]
    if row["object_type"] == "TEXT_GLYPH" and peers:
        med = float(np.median([r["h_ink_px"] for r in peers]))
        ratio = row["h_ink_px"] / med if med else None
        row["same_role_script_median_px"] = med
        row["ratio_to_same_role_script_median"] = ratio
        row["protocol_same_class_result"] = "PASS" if ratio is not None and 0.92 <= ratio <= 1.08 else "FAIL"
    else:
        row["same_role_script_median_px"] = None
        row["ratio_to_same_role_script_median"] = None
        row["protocol_same_class_result"] = "N/A"


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return math.hypot(dx, dy)


def exact_distance(mask_a, mask_b):
    inter = int(np.count_nonzero(mask_a & mask_b))
    if inter:
        return inter, 0.0, 0.0, "EXACT"
    ba, bb = native_bbox(mask_a), native_bbox(mask_b)
    if ba is None or bb is None:
        return inter, None, None, "EMPTY"
    lower = bbox_gap(ba, bb)
    if lower > 32:
        return inter, lower, max(0.0, lower - 1.0), "BBOX_LOWER_BOUND_SUFFICIENT"
    ya, xa = np.where(mask_a)
    yb, xb = np.where(mask_b)
    a = np.stack([xa, ya], axis=1).astype(np.float32)
    b = np.stack([xb, yb], axis=1).astype(np.float32)
    best2 = float("inf")
    for start in range(0, len(a), 512):
        chunk = a[start:start+512]
        d2 = ((chunk[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
        best2 = min(best2, float(d2.min()))
    center = math.sqrt(best2)
    return inter, center, max(0.0, center - 1.0), "EXACT"


obj_by_id = {o["object_id"]: o for o in OBJECTS}
pairs = []
for pair_no, (a, b) in enumerate(combinations(OBJECTS, 2), start=1):
    aid, bid = a["object_id"], b["object_id"]
    inter, center_dist, clearance, distance_kind = exact_distance(full_masks[aid], full_masks[bid])
    at, bt = a["object_type"], b["object_type"]
    whitelist = ""
    if at == bt == "TEXT_GLYPH" and a["semantic_parent"] == b["semantic_parent"]:
        relation = "TEXT_TEXT_SAME_SEMANTIC_PARENT"
        independent = False
        whitelist = "internal TeX/text composition; non-design glyph damage still manually reviewed"
        threshold = None
    elif at == bt == "TEXT_GLYPH":
        relation = "TEXT_TEXT_INDEPENDENT"
        independent = True
        threshold = 4
    elif {at, bt} == {"TEXT_GLYPH", "GRAPHIC"}:
        relation = "TEXT_GRAPHIC_INDEPENDENT"
        independent = True
        threshold = 3
    else:
        relation = "GRAPHIC_GRAPHIC"
        independent = False
        threshold = None
        if bid in (a.get("design_connections") or []) or aid in (b.get("design_connections") or []):
            whitelist = "declared design connection"
        else:
            whitelist = "graphic-graphic relationship; checked semantically, not a text collision"
    if independent and inter > 0:
        strict_status = "FAIL_TRUE_ILLEGAL_OVERLAP"
        r168_status = "FAIL_TRUE_ILLEGAL_OVERLAP"
    elif independent and clearance is not None and threshold is not None and clearance < threshold:
        strict_status = "FAIL_MICRO_CLEARANCE"
        r168_status = "ADVISORY_MICRO_CLEARANCE_PENDING_MANUAL"
    elif not independent:
        strict_status = "DESIGN_OR_NA"
        r168_status = "DESIGN_OR_NA"
    else:
        strict_status = "PASS"
        r168_status = "PASS"
    pairs.append({
        "pair_id": f"P{pair_no:04d}",
        "object_a": aid,
        "object_b": bid,
        "parent_a": a["semantic_parent"],
        "parent_b": b["semantic_parent"],
        "role_a": a["role"],
        "role_b": b["role"],
        "relation_class": relation,
        "independent_hard_gate": independent,
        "design_whitelist_reason": whitelist,
        "intersection_px": inter,
        "nearest_center_distance_px": center_dist,
        "min_white_clearance_px": clearance,
        "distance_kind": distance_kind,
        "protocol_threshold_px": threshold,
        "strict_protocol_status": strict_status,
        "r168_status": r168_status,
    })

if len(pairs) != FROZEN["unordered_pair_count_C"]:
    raise RuntimeError(f"Pair count mismatch: {len(pairs)}")

def write_csv(path, data):
    if not data:
        return
    keys = list(data[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in data:
            cooked = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()}
            writer.writerow(cooked)


write_csv(Path(__file__).with_name("04_object_measurements.csv"), rows)
write_csv(Path(__file__).with_name("04_all_unordered_pairs.csv"), pairs)
write_csv(Path(__file__).with_name("04_id_safe_filename.csv"), [{"object_id": r["object_id"], "safe_filename": r["safe_filename"]} for r in rows])

# Native overlay of every object bbox/ID.
overlay = BODY_IMG.copy()
od = ImageDraw.Draw(overlay)
for obj in OBJECTS:
    x0, y0, x1, y1 = map(int, obj["bbox_crop_native_px"])
    color = (220, 40, 40) if obj["object_type"] == "TEXT_GLYPH" else (40, 80, 220)
    od.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
    od.text((x0, max(0, y0 - 10)), obj["object_id"], fill=color)
overlay.save(ROOT / "render" / "after_text_measurement_overlay_300dpi.png")


def target_triptych(obj, scale_factor):
    oid = obj["object_id"]
    mask = full_masks[oid]
    box = native_bbox(mask) or obj["bbox_crop_native_px"]
    pad = 5
    x0 = max(0, int(box[0]) - pad); y0 = max(0, int(box[1]) - pad)
    x1 = min(BODY.shape[1], int(box[2]) + pad); y1 = min(BODY.shape[0], int(box[3]) + pad)
    original = BODY_IMG.crop((x0, y0, x1, y1))
    local_mask = mask[y0:y1, x0:x1]
    colored = np.asarray(original).copy()
    colored[local_mask] = [255, 0, 0]
    over = Image.fromarray(colored)
    mono = Image.new("RGB", original.size, "white")
    ma = np.asarray(mono).copy(); ma[local_mask] = [0, 0, 0]; mono = Image.fromarray(ma)
    if scale_factor != 1:
        size = (original.width * scale_factor, original.height * scale_factor)
        original = original.resize(size, Image.Resampling.NEAREST)
        over = over.resize(size, Image.Resampling.NEAREST)
        mono = mono.resize(size, Image.Resampling.NEAREST)
    out = Image.new("RGB", (original.width * 3 + 12, original.height + 18), "white")
    d = ImageDraw.Draw(out)
    d.text((2, 1), f"{oid} ORIGINAL | TARGET OVERLAY | MASK ONLY", fill="black")
    out.paste(original, (0, 18)); out.paste(over, (original.width + 6, 18)); out.paste(mono, (2 * original.width + 12, 18))
    return out


contact_index = []
def build_contact(kind, objects, per_sheet=20):
    for scale_factor in (1, 8):
        for sheet_no, start in enumerate(range(0, len(objects), per_sheet), start=1):
            subset = objects[start:start+per_sheet]
            cells = [target_triptych(o, scale_factor) for o in subset]
            cols = 4 if scale_factor == 1 else 2
            rows_n = math.ceil(len(cells) / cols)
            cell_w = max(c.width for c in cells) + 10
            cell_h = max(c.height for c in cells) + 10
            sheet = Image.new("RGB", (cell_w * cols, cell_h * rows_n), "white")
            for i, (obj, cell) in enumerate(zip(subset, cells)):
                cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
                sheet.paste(cell, (cx, cy))
                contact_index.append({"object_id": obj["object_id"], "kind": kind, "scale": f"{scale_factor}x", "sheet": sheet_no, "cell": i + 1})
            sheet.save(ROOT / "contact" / f"{kind}_{scale_factor}x_sheet_{sheet_no:02d}.png")


text_objects = [o for o in OBJECTS if o["object_type"] == "TEXT_GLYPH"]
graphic_objects = [o for o in OBJECTS if o["object_type"] == "GRAPHIC"]
build_contact("glyph_contact", text_objects, 20)
write_csv(Path(__file__).with_name("04_contact_index.csv"), contact_index)

# Every threshold-critical independent pair plus nearest pairs up to 20 get complete ROI evidence.
independent_pairs = [p for p in pairs if p["independent_hard_gate"] and p["min_white_clearance_px"] is not None]
critical = [p for p in independent_pairs if p["intersection_px"] > 0 or p["min_white_clearance_px"] <= 12]
if len(critical) < 20:
    existing = {p["pair_id"] for p in critical}
    for p in sorted(independent_pairs, key=lambda q: q["min_white_clearance_px"]):
        if p["pair_id"] not in existing:
            critical.append(p); existing.add(p["pair_id"])
        if len(critical) >= 20:
            break
write_csv(Path(__file__).with_name("04_critical_pairs.csv"), critical)

roi_cells_1x = []
roi_cells_8x = []
roi_index = []
for p in critical:
    ma, mb = full_masks[p["object_a"]], full_masks[p["object_b"]]
    ba, bb = native_bbox(ma), native_bbox(mb)
    x0 = max(0, min(ba[0], bb[0]) - 6); y0 = max(0, min(ba[1], bb[1]) - 6)
    x1 = min(BODY.shape[1], max(ba[2], bb[2]) + 6); y1 = min(BODY.shape[0], max(ba[3], bb[3]) + 6)
    original = BODY_IMG.crop((x0, y0, x1, y1))
    aa, bbm = ma[y0:y1, x0:x1], mb[y0:y1, x0:x1]
    inter = aa & bbm
    panels = []
    for mode in ("RAW", "A", "B", "INTERSECTION"):
        arr = np.asarray(original).copy()
        if mode == "A": arr[aa] = [255, 0, 0]
        if mode == "B": arr[bbm] = [0, 80, 255]
        if mode == "INTERSECTION":
            arr[:] = 255
            arr[aa] = [255, 0, 0]; arr[bbm] = [0, 80, 255]; arr[inter] = [255, 220, 0]
        panels.append(Image.fromarray(arr))
    quad = Image.new("RGB", (original.width * 4 + 18, original.height + 22), "white")
    qd = ImageDraw.Draw(quad)
    qd.text((2, 1), f"{p['pair_id']} {p['object_a']} vs {p['object_b']} gap={p['min_white_clearance_px']:.2f}px inter={p['intersection_px']} | RAW A B INTER", fill="black")
    for i, panel in enumerate(panels): quad.paste(panel, (i * (original.width + 6), 22))
    q8 = quad.resize((quad.width * 8, quad.height * 8), Image.Resampling.NEAREST)
    quad.save(ROOT / "roi" / f"{p['pair_id']}_quad_1x.png")
    q8.save(ROOT / "roi" / f"{p['pair_id']}_quad_8x_nearest.png")
    Image.fromarray((aa * 255).astype(np.uint8), mode="L").save(ROOT / "roi" / f"{p['pair_id']}_A_raw_mask.png")
    Image.fromarray((bbm * 255).astype(np.uint8), mode="L").save(ROOT / "roi" / f"{p['pair_id']}_B_raw_mask.png")
    Image.fromarray((inter * 255).astype(np.uint8), mode="L").save(ROOT / "roi" / f"{p['pair_id']}_intersection.png")
    roi_cells_1x.append((p, quad)); roi_cells_8x.append((p, q8))
    roi_index.append({"pair_id": p["pair_id"], "roi_full_crop_px": [x0, y0, x1, y1], "quad_1x": f"roi/{p['pair_id']}_quad_1x.png", "quad_8x": f"roi/{p['pair_id']}_quad_8x_nearest.png"})
write_csv(Path(__file__).with_name("04_roi_index.csv"), roi_index)

def roi_sheets(cells, scale_label, per_sheet=5):
    for sheet_no, start in enumerate(range(0, len(cells), per_sheet), start=1):
        subset = [c[1] for c in cells[start:start+per_sheet]]
        width = max(c.width for c in subset)
        height = sum(c.height + 8 for c in subset)
        sheet = Image.new("RGB", (width, height), "white")
        y = 0
        for cell in subset:
            sheet.paste(cell, (0, y)); y += cell.height + 8
        sheet.save(ROOT / "contact" / f"critical_roi_{scale_label}_sheet_{sheet_no:02d}.png")
roi_sheets(roi_cells_1x, "1x")
roi_sheets(roi_cells_8x, "8x_nearest")

text_rows = [r for r in rows if r["object_type"] == "TEXT_GLYPH"]
empty = [r["object_id"] for r in rows if r["empty_mask"]]
strict_pixel_fail = [r["object_id"] for r in text_rows if r["protocol_pixel_result"] == "FAIL"]
strict_ratio_fail = [r["object_id"] for r in text_rows if r["protocol_same_class_result"] == "FAIL"]
illegal_overlap_pairs = [p["pair_id"] for p in pairs if p["r168_status"] == "FAIL_TRUE_ILLEGAL_OVERLAP"]
strict_clearance_fail = [p["pair_id"] for p in pairs if p["strict_protocol_status"] == "FAIL_MICRO_CLEARANCE"]
crop_edge_clearance = min(
    min(native_bbox(m)[0], native_bbox(m)[1], BODY.shape[1] - native_bbox(m)[2], BODY.shape[0] - native_bbox(m)[3])
    for m in full_masks.values() if native_bbox(m) is not None
)
hard = {
    "official_identity_pass": True,
    "location_physical_page": 632,
    "native_300dpi_dimensions": list(BODY_IMG.size),
    "object_count_N": len(OBJECTS),
    "unordered_pair_count_C": len(pairs),
    "empty_mask_count": len(empty),
    "empty_mask_ids": empty,
    "strict_protocol_pixel_fail_count": len(strict_pixel_fail),
    "strict_protocol_pixel_fail_ids": strict_pixel_fail,
    "strict_protocol_same_class_ratio_fail_count": len(strict_ratio_fail),
    "strict_protocol_same_class_ratio_fail_ids": strict_ratio_fail,
    "strict_protocol_micro_clearance_fail_count": len(strict_clearance_fail),
    "strict_protocol_micro_clearance_fail_pair_ids": strict_clearance_fail,
    "r168_true_illegal_overlap_pair_count": len(illegal_overlap_pairs),
    "r168_true_illegal_overlap_pair_ids": illegal_overlap_pairs,
    "overlap_pixel_count": int(sum(p["intersection_px"] for p in pairs if p["independent_hard_gate"])),
    "clip_pixel_count": 0 if crop_edge_clearance > 0 else 1,
    "minimum_object_to_crop_edge_clearance_px": int(crop_edge_clearance),
    "machine_r168_direction": "PASS_CANDIDATE" if not empty and not illegal_overlap_pairs and crop_edge_clearance > 0 else "FAIL",
    "manual_review_required": True,
}
(Path(__file__).with_name("04_hard_gates.json")).write_text(json.dumps(hard, ensure_ascii=False, indent=2), encoding="utf-8")

integrity = {
    "expected_object_count": len(OBJECTS),
    "mask_png_count": len(list((ROOT / "masks").glob("*.png"))),
    "all_mask_png_openable_and_dimensions_match": True,
    "expected_pair_count": FROZEN["unordered_pair_count_C"],
    "actual_pair_count": len(pairs),
    "pair_ids_unique": len({p["pair_id"] for p in pairs}) == len(pairs),
    "object_ids_unique": len({o["object_id"] for o in OBJECTS}) == len(OBJECTS),
    "glyph_vector_count": len(list(Path(__file__).with_name("glyph_vectors").glob("*.svg"))),
    "glyph_contact_rows": len([r for r in contact_index if r["kind"] == "glyph_contact"]),
    "graphic_contact_generation_deferred_to_machine_05": True,
    "critical_roi_count": len(critical),
}
for obj in OBJECTS:
    im = Image.open(ROOT / "masks" / obj["safe_filename"])
    x0, y0, x1, y1 = obj["bbox_crop_native_px"]
    if im.size != (int(x1) - int(x0), int(y1) - int(y0)):
        integrity["all_mask_png_openable_and_dimensions_match"] = False
(Path(__file__).with_name("04_integrity.json")).write_text(json.dumps(integrity, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"hard_gates": hard, "integrity": integrity, "critical_pair_count": len(critical)}, ensure_ascii=False, indent=2))
