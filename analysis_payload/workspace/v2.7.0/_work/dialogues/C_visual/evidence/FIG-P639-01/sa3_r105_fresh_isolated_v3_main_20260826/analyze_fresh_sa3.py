from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r105_fresh_isolated_v3_main_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf")
PAGE_INDEX = 688
SCALE = 300.0 / 72.0
CROP_X = 380
CROP_Y = 1350
CROP_W = 1695
CROP_H = 720
FIG_RECT_PT = fitz.Rect(CROP_X / SCALE, CROP_Y / SCALE, (CROP_X + CROP_W) / SCALE, (CROP_Y + CROP_H) / SCALE)


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)


def rgb_from_int(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def pt_bbox_to_px(rect: fitz.Rect, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, math.floor(rect.x0 * SCALE - CROP_X) - pad)
    y0 = max(0, math.floor(rect.y0 * SCALE - CROP_Y) - pad)
    x1 = min(CROP_W, math.ceil(rect.x1 * SCALE - CROP_X) + pad)
    y1 = min(CROP_H, math.ceil(rect.y1 * SCALE - CROP_Y) + pad)
    return x0, y0, x1, y1


def actual_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def role_for_block(block_index: int) -> str:
    return {
        15: "X_TICK_LABEL",
        16: "Y_TICK_LABEL",
        17: "Y_TICK_LABEL",
        18: "TOP_FORMULA_LABEL",
        19: "NOTE_TEXT",
        20: "X_AXIS_TITLE",
        21: "Y_AXIS_TITLE",
    }[block_index]


def classify_char(char: str, extracted_size: float) -> tuple[str, int]:
    cp = ord(char)
    if extracted_size < 8.0:
        return "NATURAL_SCRIPT", 15
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK", 30
    if char in ".,，。；：、…":
        return "LOW_PROFILE_PUNCTUATION", 0
    if char in "−+=<>≤≥×÷":
        return "BASE_MATH_OPERATOR", 22
    if char.isdigit() or (char.isascii() and char.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    if char.islower() or 0x0370 <= cp <= 0x03FF or 0x1D400 <= cp <= 0x1D7FF:
        return "LATIN_GREEK_LOWER_OR_MATH_LETTER", 17
    return "BASE_MATH", 22


def source_pt_for_role(role: str) -> float:
    return 8.5 if role in {"X_TICK_LABEL", "Y_TICK_LABEL"} else 9.2


def color_mask(arr: np.ndarray, rgb: tuple[int, int, int], bbox: tuple[int, int, int, int], tolerance: float = 72.0) -> np.ndarray:
    out = np.zeros((CROP_H, CROP_W), dtype=bool)
    x0, y0, x1, y1 = bbox
    sub = arr[y0:y1, x0:x1].astype(np.int32)
    target = np.array(rgb, dtype=np.int32)
    distance = np.sqrt(np.sum((sub - target) ** 2, axis=2))
    contrast = 255 - sub.min(axis=2)
    out[y0:y1, x0:x1] = (distance <= tolerance) & (contrast >= 20)
    return out


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def exact_clearance(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    pa = np.argwhere(mask_a)
    pb = np.argwhere(mask_b)
    if len(pa) == 0 or len(pb) == 0:
        return math.inf
    if len(pa) > len(pb):
        pa, pb = pb, pa
    return float(cKDTree(pb).query(pa, k=1)[0].min())


def make_contact(original: Image.Image, mask: np.ndarray, obj: dict, out: Path) -> None:
    x0, y0, x1, y1 = obj["pixel_bbox"]
    pad = 4
    ax0, ay0 = max(0, x0 - pad), max(0, y0 - pad)
    ax1, ay1 = min(CROP_W, x1 + pad), min(CROP_H, y1 + pad)
    patch = original.crop((ax0, ay0, ax1, ay1)).convert("RGB")
    local = mask[ay0:ay1, ax0:ax1]
    overlay = np.array(patch).copy()
    overlay[local] = np.array([255, 0, 0], dtype=np.uint8)
    mask_only = np.full_like(overlay, 255)
    mask_only[local] = np.array([0, 0, 0], dtype=np.uint8)
    pieces = [patch, Image.fromarray(overlay), Image.fromarray(mask_only)]
    scale = max(1, min(8, 192 // max(1, max(patch.size))))
    pieces = [p.resize((p.width * scale, p.height * scale), Image.Resampling.NEAREST) for p in pieces]
    canvas = Image.new("RGB", (720, 150), "white")
    draw = ImageDraw.Draw(canvas)
    header = f"{obj['id']}  U+{ord(obj['char']):04X}  {obj['char']}  H={obj['h_ink_px']}  {obj['pixel_decision']}"
    draw.text((8, 4), header, fill="black")
    for i, (label, piece) in enumerate(zip(("ORIGINAL", "TARGET OVERLAY", "MASK ONLY"), pieces)):
        px = 8 + i * 236
        draw.text((px, 24), label, fill="black")
        canvas.paste(piece, (px, 43))
    canvas.save(out)


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
image = Image.open(ROOT / "figure_crop_300dpi.png").convert("RGB")
if image.size != (CROP_W, CROP_H):
    raise RuntimeError(f"unexpected crop size {image.size}")
arr = np.array(image)
foreground = (255 - arr.min(axis=2)) >= 20

mask_dir = ROOT / "object_masks"
contact_dir = ROOT / "glyph_contacts"
sheet_dir = ROOT / "contact_sheets"
roi_dir = ROOT / "pair_roi"
for directory in (mask_dir, contact_dir, sheet_dir, roi_dir):
    safe_mkdir(directory)

objects: list[dict] = []
masks: dict[str, np.ndarray] = {}
raw = page.get_text("rawdict")
glyph_index = 0
for block_index, block in enumerate(raw["blocks"]):
    if block.get("type") != 0 or block_index not in {15, 16, 17, 18, 19, 20, 21}:
        continue
    for line_index, line in enumerate(block.get("lines", [])):
        parent = f"TEXT_B{block_index:02d}_L{line_index:02d}"
        for span_index, span in enumerate(line.get("spans", [])):
            for char_index, char_info in enumerate(span.get("chars", [])):
                char = char_info["c"]
                if char.isspace():
                    continue
                rect = fitz.Rect(char_info["bbox"])
                if not rect.intersects(FIG_RECT_PT):
                    continue
                glyph_index += 1
                obj_id = f"GLYPH_{glyph_index:03d}"
                pb = pt_bbox_to_px(rect)
                x0, y0, x1, y1 = pb
                mask = np.zeros((CROP_H, CROP_W), dtype=bool)
                mask[y0:y1, x0:x1] = foreground[y0:y1, x0:x1]
                ab = actual_bbox(mask)
                h_ink = 0 if ab is None else ab[3] - ab[1]
                w_ink = 0 if ab is None else ab[2] - ab[0]
                category, threshold = classify_char(char, float(span["size"]))
                pixel_decision = "PENDING_CALIBRATION" if category == "LOW_PROFILE_PUNCTUATION" else ("PASS" if h_ink >= threshold and h_ink > 0 else "FAIL")
                role = role_for_block(block_index)
                declared_pt = source_pt_for_role(role)
                obj = {
                    "id": obj_id,
                    "kind": "GLYPH",
                    "char": char,
                    "unicode": f"U+{ord(char):04X}",
                    "parent": parent,
                    "role": role,
                    "block": block_index,
                    "line": line_index,
                    "span": span_index,
                    "char_index": char_index,
                    "font": span["font"],
                    "pdf_extracted_size_bp_advisory": round(float(span["size"]), 6),
                    "pdf_color_rgb": rgb_from_int(int(span["color"])),
                    "source_effective_pt": declared_pt,
                    "source_pt_decision": "FAIL" if declared_pt < 9.5 else "PASS",
                    "category": category,
                    "threshold_px": threshold,
                    "pdf_bbox_pt": [round(v, 6) for v in rect],
                    "pixel_bbox": list(pb),
                    "raw_mask_bbox": list(ab) if ab else None,
                    "mask_pixel_count": int(mask.sum()),
                    "h_ink_px": h_ink,
                    "w_ink_px": w_ink,
                    "pixel_decision": pixel_decision,
                    "safe_filename": f"{obj_id}.png",
                }
                objects.append(obj)
                masks[obj_id] = mask
                save_mask(mask, mask_dir / obj["safe_filename"])

# Low-profile punctuation calibration against same codepoint/font/size/color peers.
punct_groups: dict[tuple, list[dict]] = {}
for obj in objects:
    if obj["category"] == "LOW_PROFILE_PUNCTUATION":
        key = (obj["char"], obj["font"], round(obj["pdf_extracted_size_bp_advisory"], 3), tuple(obj["pdf_color_rgb"]))
        punct_groups.setdefault(key, []).append(obj)
for group in punct_groups.values():
    heights = [o["h_ink_px"] for o in group]
    areas = [o["mask_pixel_count"] for o in group]
    med_h = float(np.median(heights)) if heights else 0.0
    med_a = float(np.median(areas)) if areas else 0.0
    for obj in group:
        obj["calibration_peer_count"] = len(group) - 1
        obj["calibration_h_ratio"] = None if med_h == 0 else round(obj["h_ink_px"] / med_h, 6)
        obj["calibration_area_ratio"] = None if med_a == 0 else round(obj["mask_pixel_count"] / med_a, 6)
        ok = len(group) >= 2 and med_h > 0 and med_a > 0 and 0.92 <= obj["calibration_h_ratio"] <= 1.08 and 0.92 <= obj["calibration_area_ratio"] <= 1.08
        obj["pixel_decision"] = "PASS" if ok else "FAIL_CALIBRATION_MISSING_OR_RATIO"

for obj in objects:
    make_contact(image, masks[obj["id"]], obj, contact_dir / f"{obj['id']}_contact.png")

# Graphic masks: each is tied to a visible PDF drawing/path semantic object.
graphics_specs = [
    ("GFX_TICKS", "TICKS", (127, 128, 127), (133.572, 357.323, 388.509, 466.214)),
    ("GFX_X_AXIS", "LINE_ARROW", (31, 35, 40), (135.699, 462.194, 388.509, 465.980)),
    ("GFX_Y_AXIS", "LINE_ARROW", (31, 35, 40), (133.806, 344.511, 137.592, 464.088)),
    ("GFX_BLUE_CURVE", "DATA_CURVE", (31, 78, 121), (135.699, 357.609, 388.509, 464.088)),
    ("GFX_GOLD_CURVE", "DATA_CURVE", (183, 121, 31), (135.699, 357.609, 388.509, 464.088)),
    ("GFX_BLUE_GUIDE", "MEAN_GUIDE", (31, 78, 121), (259.575, 357.537, 259.576, 464.088)),
    ("GFX_GOLD_GUIDE", "MEAN_GUIDE", (183, 121, 31), (267.159, 357.537, 267.161, 464.088)),
    ("GFX_NOTE_BORDER", "NODE_BORDER", (184, 192, 200), (396.782, 390.251, 491.230, 418.347)),
]
for obj_id, role, rgb, rect_pt_tuple in graphics_specs:
    rect = fitz.Rect(*rect_pt_tuple)
    pb = pt_bbox_to_px(rect, pad=3)
    mask = color_mask(arr, rgb, pb)
    if obj_id == "GFX_TICKS":
        mask = np.zeros((CROP_H, CROP_W), dtype=bool)
        for tick_rect in (
            fitz.Rect(135.699, 461.960, 388.509, 466.214),
            fitz.Rect(133.572, 357.323, 137.826, 464.088),
        ):
            tick_bbox = pt_bbox_to_px(tick_rect, pad=3)
            mask |= color_mask(arr, rgb, tick_bbox, tolerance=48.0)
        neutral = (arr.max(axis=2).astype(np.int16) - arr.min(axis=2).astype(np.int16)) <= 5
        mask &= neutral
    if obj_id == "GFX_NOTE_BORDER":
        chroma = arr.astype(np.int16)
        blue_gray = ((chroma[:, :, 2] - chroma[:, :, 0]) >= 4) & ((chroma[:, :, 1] - chroma[:, :, 0]) >= 2)
        mask &= blue_gray
        bx0, by0, bx1, by1 = pb
        yy, xx = np.indices((CROP_H, CROP_W))
        edge_band = ((xx <= bx0 + 12) | (xx >= bx1 - 13) | (yy <= by0 + 12) | (yy >= by1 - 13))
        mask &= edge_band
    if obj_id == "GFX_BLUE_CURVE":
        gx0, _, gx1, _ = pt_bbox_to_px(fitz.Rect(259.0, 356, 260.2, 465), pad=1)
        peak_y = int(round(357.54 * SCALE - CROP_Y))
        mask[max(0, peak_y + 6):, gx0:gx1] = False
    if obj_id == "GFX_GOLD_CURVE":
        gx0, _, gx1, _ = pt_bbox_to_px(fitz.Rect(266.6, 356, 267.8, 465), pad=1)
        peak_y = int(round(357.54 * SCALE - CROP_Y))
        mask[max(0, peak_y + 6):, gx0:gx1] = False
    ab = actual_bbox(mask)
    obj = {
        "id": obj_id,
        "kind": "GRAPHIC",
        "char": None,
        "parent": obj_id,
        "role": role,
        "source_pdf_drawing_semantics": role,
        "target_rgb": list(rgb),
        "pdf_bbox_pt": [round(v, 6) for v in rect],
        "pixel_bbox": list(pb),
        "raw_mask_bbox": list(ab) if ab else None,
        "mask_pixel_count": int(mask.sum()),
        "safe_filename": f"{obj_id}.png",
    }
    objects.append(obj)
    masks[obj_id] = mask
    save_mask(mask, mask_dir / obj["safe_filename"])

# Contact sheets are derived from already-created per-glyph evidence and do not set manual fields.
glyph_objects = [o for o in objects if o["kind"] == "GLYPH"]
for sheet_index, start in enumerate(range(0, len(glyph_objects), 16), start=1):
    subset = glyph_objects[start:start + 16]
    sheet = Image.new("RGB", (720, 150 * len(subset)), "white")
    for row, obj in enumerate(subset):
        contact = Image.open(contact_dir / f"{obj['id']}_contact.png").convert("RGB")
        sheet.paste(contact, (0, row * 150))
        obj["contact_sheet"] = f"contact_sheets/glyph_contact_sheet_{sheet_index:03d}.png"
        obj["contact_cell"] = row + 1
    sheet.save(sheet_dir / f"glyph_contact_sheet_{sheet_index:03d}.png")

# All-pairs ledger over the frozen visible-object denominator.
allow_graphic_pairs = {
    frozenset(("GFX_X_AXIS", "GFX_Y_AXIS")),
    frozenset(("GFX_TICKS", "GFX_X_AXIS")),
    frozenset(("GFX_TICKS", "GFX_Y_AXIS")),
    frozenset(("GFX_BLUE_CURVE", "GFX_GOLD_CURVE")),
    frozenset(("GFX_BLUE_CURVE", "GFX_BLUE_GUIDE")),
    frozenset(("GFX_BLUE_CURVE", "GFX_GOLD_GUIDE")),
    frozenset(("GFX_GOLD_CURVE", "GFX_GOLD_GUIDE")),
    frozenset(("GFX_GOLD_CURVE", "GFX_BLUE_GUIDE")),
    frozenset(("GFX_X_AXIS", "GFX_BLUE_CURVE")),
    frozenset(("GFX_X_AXIS", "GFX_GOLD_CURVE")),
    frozenset(("GFX_X_AXIS", "GFX_BLUE_GUIDE")),
    frozenset(("GFX_X_AXIS", "GFX_GOLD_GUIDE")),
    frozenset(("GFX_Y_AXIS", "GFX_BLUE_CURVE")),
}
pair_rows = []
critical_pairs = []
for pair_index, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
    ma, mb = masks[a["id"]], masks[b["id"]]
    overlap = int(np.count_nonzero(ma & mb))
    aa, bb = actual_bbox(ma), actual_bbox(mb)
    lower_bound = math.inf if aa is None or bb is None else bbox_gap(aa, bb)
    if overlap:
        clearance = 0.0
        method = "raw_mask_intersection"
    elif lower_bound <= 16:
        clearance = exact_clearance(ma, mb)
        method = "raw_mask_kdtree_exact"
    else:
        clearance = lower_bound
        method = "raw_mask_bbox_lower_bound_gt_16"
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        relation = "TEXT_INTERNAL_SAME_PARENT" if a["parent"] == b["parent"] else "TEXT_TEXT_INDEPENDENT"
        threshold = 0 if a["parent"] == b["parent"] else 4
    elif a["kind"] == "GLYPH" or b["kind"] == "GLYPH":
        text_obj, graphic_obj = (a, b) if a["kind"] == "GLYPH" else (b, a)
        if graphic_obj["id"] == "GFX_NOTE_BORDER" and text_obj["block"] == 19:
            relation, threshold = "TEXT_NODE_BORDER", 5
        else:
            relation, threshold = "TEXT_GRAPHIC", 3
    else:
        relation, threshold = "GRAPHIC_GRAPHIC", 0
    allowed_overlap = False
    allow_reason = ""
    if relation == "TEXT_INTERNAL_SAME_PARENT":
        allowed_overlap = True
        allow_reason = "same semantic text/formula parent; only destructive glyph overlap would fail"
    elif a["kind"] == b["kind"] == "GRAPHIC" and frozenset((a["id"], b["id"])) in allow_graphic_pairs:
        allowed_overlap = True
        allow_reason = "designed data/axis/tick connection or data-curve crossing"
    hard_overlap_fail = overlap > 0 and not allowed_overlap
    clearance_fail = not hard_overlap_fail and threshold > 0 and clearance < threshold
    decision = "FAIL" if hard_overlap_fail or clearance_fail else "PASS"
    pair_id = f"PAIR_{pair_index:04d}"
    row = {
        "pair_id": pair_id,
        "object_a": a["id"],
        "object_b": b["id"],
        "relation": relation,
        "overlap_pixel_count": overlap,
        "clearance_px": None if math.isinf(clearance) else round(clearance, 6),
        "clearance_method": method,
        "hard_threshold_px": threshold,
        "allowed_overlap": allowed_overlap,
        "allow_reason": allow_reason,
        "decision": decision,
    }
    pair_rows.append(row)
    if decision == "FAIL" or (threshold > 0 and clearance <= threshold + 3) or overlap > 0:
        critical_pairs.append((row, a, b, ma, mb))

for row, a, b, ma, mb in critical_pairs:
    union = ma | mb
    ub = actual_bbox(union)
    if ub is None:
        continue
    x0, y0, x1, y1 = ub
    pad = 8
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(CROP_W, x1 + pad), min(CROP_H, y1 + pad)
    original_roi = image.crop((x0, y0, x1, y1)).convert("RGB")
    a_local, b_local = ma[y0:y1, x0:x1], mb[y0:y1, x0:x1]
    inter_local = a_local & b_local
    overlay = np.array(original_roi).copy()
    overlay[a_local] = np.array([255, 0, 0], dtype=np.uint8)
    overlay[b_local] = np.array([0, 160, 255], dtype=np.uint8)
    overlay[inter_local] = np.array([255, 0, 255], dtype=np.uint8)
    base = roi_dir / row["pair_id"]
    original_roi.save(base.with_name(base.name + "_original_1x.png"))
    Image.fromarray(np.where(a_local, 0, 255).astype(np.uint8)).save(base.with_name(base.name + "_mask_a_1x.png"))
    Image.fromarray(np.where(b_local, 0, 255).astype(np.uint8)).save(base.with_name(base.name + "_mask_b_1x.png"))
    Image.fromarray(np.where(inter_local, 0, 255).astype(np.uint8)).save(base.with_name(base.name + "_intersection_1x.png"))
    overlay_im = Image.fromarray(overlay)
    overlay_im.save(base.with_name(base.name + "_overlay_1x.png"))
    overlay_im.resize((overlay_im.width * 8, overlay_im.height * 8), Image.Resampling.NEAREST).save(base.with_name(base.name + "_overlay_8x_nearest.png"))

# Figure-wide glyph overlay.
overlay = image.copy()
draw = ImageDraw.Draw(overlay)
for obj in glyph_objects:
    x0, y0, x1, y1 = obj["pixel_bbox"]
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 0, 0), width=1)
    draw.text((x0, max(0, y0 - 10)), obj["id"].replace("GLYPH_", "G"), fill=(180, 0, 0))
overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

with (ROOT / "object_manifest.json").open("w", encoding="utf-8") as f:
    json.dump(objects, f, ensure_ascii=False, indent=2)
with (ROOT / "object_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
    fields = ["id", "kind", "char", "unicode", "parent", "role", "font", "pdf_extracted_size_bp_advisory", "source_effective_pt", "source_pt_decision", "category", "threshold_px", "pdf_bbox_pt", "pixel_bbox", "raw_mask_bbox", "mask_pixel_count", "h_ink_px", "w_ink_px", "pixel_decision", "safe_filename", "contact_sheet", "contact_cell"]
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(objects)
with (ROOT / "after_pixel_measurements.csv").open("w", encoding="utf-8-sig", newline="") as f:
    fields = ["id", "char", "unicode", "parent", "role", "font", "pdf_extracted_size_bp_advisory", "source_effective_pt", "source_pt_decision", "category", "threshold_px", "h_ink_px", "w_ink_px", "mask_pixel_count", "calibration_peer_count", "calibration_h_ratio", "calibration_area_ratio", "pixel_decision", "contact_sheet", "contact_cell"]
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(glyph_objects)
with (ROOT / "after_overlap_report.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
    writer.writeheader()
    writer.writerows(pair_rows)

source_failures = sum(o["source_pt_decision"] == "FAIL" for o in glyph_objects)
pixel_failures = sum(o["pixel_decision"] != "PASS" for o in glyph_objects)
pair_failures = sum(r["decision"] == "FAIL" for r in pair_rows)
empty_masks = sum(o["mask_pixel_count"] == 0 for o in objects)
clip_count = sum(
    1
    for o in objects
    if o["raw_mask_bbox"] is not None
    and (o["raw_mask_bbox"][0] == 0 or o["raw_mask_bbox"][1] == 0 or o["raw_mask_bbox"][2] == CROP_W or o["raw_mask_bbox"][3] == CROP_H)
)
summary = {
    "uid": "FIG-P639-01",
    "handoff_id": "MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826",
    "official_pdf": str(PDF),
    "physical_page": 689,
    "page_index_zero_based": PAGE_INDEX,
    "page_points": [page.rect.width, page.rect.height],
    "full_page_300dpi_native_grid": [2481, 3508],
    "figure_crop_integer_xywh": [CROP_X, CROP_Y, CROP_W, CROP_H],
    "visible_object_denominator": len(objects),
    "glyph_object_count": len(glyph_objects),
    "graphic_object_count": len(objects) - len(glyph_objects),
    "all_unordered_pair_count_expected": len(objects) * (len(objects) - 1) // 2,
    "all_unordered_pair_count_actual": len(pair_rows),
    "critical_pair_evidence_count": len(critical_pairs),
    "source_effective_pt_failure_count": source_failures,
    "pixel_failure_count": pixel_failures,
    "pair_geometry_failure_count": pair_failures,
    "empty_mask_count": empty_masks,
    "clip_pixel_count": clip_count,
    "overlap_pixel_count_illegal": sum(r["overlap_pixel_count"] for r in pair_rows if r["decision"] == "FAIL" and r["overlap_pixel_count"] > 0),
    "machine_geometry_decision": "PASS" if pair_failures == 0 and empty_masks == 0 and clip_count == 0 else "FAIL",
    "machine_typography_decision": "PASS" if source_failures == 0 and pixel_failures == 0 else "FAIL",
    "overall_machine_decision": "PASS" if source_failures == pixel_failures == pair_failures == empty_masks == clip_count == 0 else "FAIL",
}
with (ROOT / "machine_summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
