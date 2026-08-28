from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pypdf import PdfReader


HANDOFF_ID = "A-R110-P033-SA1-FRESH-ISOLATED-20260827"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R2_SA1_FRESH_ISOLATED_R110_20260827")
PAYLOAD = ROOT / "payload"
TMP = ROOT / "tmp"
PAGE_NUMBER = 29
PAGE_INDEX = PAGE_NUMBER - 1
SCALE = 300.0 / 72.0
PAGE_PT = (595.276, 841.89)
FIGURE_PDF_BBOX = (55.0, 460.0, 530.0, 655.0)  # x0, top, x1, bottom; body + caption
BODY_PDF_BBOX = (145.0, 460.0, 440.0, 635.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px_bbox(pdf_bbox: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, top, x1, bottom = pdf_bbox
    return (
        math.floor(x0 * SCALE),
        math.floor(top * SCALE),
        math.ceil(x1 * SCALE),
        math.ceil(bottom * SCALE),
    )


def rgb255(value) -> tuple[int, int, int]:
    if value is None:
        return (31, 35, 40)
    if isinstance(value, (int, float)):
        v = int(round(float(value) * 255))
        return (v, v, v)
    vals = list(value)
    if len(vals) == 1:
        v = int(round(float(vals[0]) * 255))
        return (v, v, v)
    if len(vals) >= 3:
        return tuple(int(round(float(v) * 255)) for v in vals[:3])
    return (31, 35, 40)


def char_parent(c: dict) -> str:
    top = float(c["top"])
    if top >= 635:
        return "CAPTION"
    if top >= 615:
        return "SUBSPACE_LABEL"
    if top >= 590:
        return "P_FORMULA"
    if top >= 540:
        return "SHORTEST_DISTANCE_LABEL"
    if top >= 525:
        return "X_LABEL"
    if top >= 505:
        return "R_FORMULA"
    return "NORM_FORMULA"


def char_class(text: str, size: float) -> str:
    cp = ord(text[0])
    if size < 8.5:
        return "NATURAL_SCRIPT"
    if text in {".", ",", "，", "。", "、", "：", ":", ";", "；", "…"}:
        return "LOW_PROFILE_PUNCTUATION"
    if 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
        return "CJK_FULL"
    if text.isdigit() or text.isupper():
        return "LATIN_CAP_OR_DIGIT"
    if text in {"−", "+", "=", "∈", "⟂", "‖"}:
        return "BASE_MATH_OPERATOR"
    if text.isalpha() or 0x0370 <= cp <= 0x03FF or 0x1D400 <= cp <= 0x1D7FF:
        return "LATIN_GREEK_LOWER"
    return "BASE_MATH"


LEGACY_LIMIT = {
    "CJK_FULL": 30,
    "LATIN_CAP_OR_DIGIT": 24,
    "LATIN_GREEK_LOWER": 17,
    "BASE_MATH_OPERATOR": 22,
    "BASE_MATH": 22,
    "NATURAL_SCRIPT": 15,
    "LOW_PROFILE_PUNCTUATION": 1,
}


def glyph_mask(page_rgb: np.ndarray, c: dict, crop_box: tuple[int, int, int, int]):
    page_h, page_w = page_rgb.shape[:2]
    x0 = max(0, math.floor(float(c["x0"]) * SCALE) - 2)
    y0 = max(0, math.floor(float(c["top"]) * SCALE) - 2)
    x1 = min(page_w, math.ceil(float(c["x1"]) * SCALE) + 2)
    y1 = min(page_h, math.ceil(float(c["bottom"]) * SCALE) + 2)
    region = page_rgb[y0:y1, x0:x1].astype(np.float32)
    if region.size == 0:
        raise RuntimeError("empty glyph region")
    border = np.concatenate((region[0], region[-1], region[:, 0], region[:, -1]), axis=0)
    bg = np.median(border, axis=0)
    target = np.array(rgb255(c.get("non_stroking_color")), dtype=np.float32)
    v = target - bg
    den = float(np.dot(v, v))
    delta = region - bg
    contrast = np.max(np.abs(delta), axis=2)
    if den < 25:
        # Defensive fallback; figure text never uses a color identical to its local background.
        lum = 0.2126 * region[:, :, 0] + 0.7152 * region[:, :, 1] + 0.0722 * region[:, :, 2]
        bg_lum = float(0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2])
        local = (bg_lum - lum >= 20)
    else:
        t = np.sum(delta * v, axis=2) / den
        projected = bg + t[:, :, None] * v
        orth = np.sqrt(np.sum((region - projected) ** 2, axis=2))
        local = (contrast >= 20) & (t >= 0.06) & (t <= 1.30) & (orth <= 24)
    # Constrain to the PDF glyph box plus one native pixel. This keeps neighbouring glyphs/lines out.
    core_x0 = max(0, math.floor(float(c["x0"]) * SCALE) - x0 - 1)
    core_y0 = max(0, math.floor(float(c["top"]) * SCALE) - y0 - 1)
    core_x1 = min(x1 - x0, math.ceil(float(c["x1"]) * SCALE) - x0 + 1)
    core_y1 = min(y1 - y0, math.ceil(float(c["bottom"]) * SCALE) - y0 + 1)
    constrained = np.zeros_like(local, dtype=bool)
    constrained[core_y0:core_y1, core_x0:core_x1] = local[core_y0:core_y1, core_x0:core_x1]
    ys, xs = np.nonzero(constrained)
    if len(xs) == 0:
        # Keep the failure observable; never invent a positive mask.
        tight = (0, 0, 0, 0)
        h_ink = 0
        w_ink = 0
    else:
        tight = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
        h_ink = int(ys.max() - ys.min() + 1)
        w_ink = int(xs.max() - xs.min() + 1)
    crop_x0, crop_y0, _, _ = crop_box
    global_mask = np.zeros((crop_box[3] - crop_y0, crop_box[2] - crop_x0), dtype=bool)
    gx0, gy0 = x0 - crop_x0, y0 - crop_y0
    tx0, ty0 = max(0, gx0), max(0, gy0)
    tx1 = min(global_mask.shape[1], gx0 + constrained.shape[1])
    ty1 = min(global_mask.shape[0], gy0 + constrained.shape[0])
    if tx1 > tx0 and ty1 > ty0:
        sx0, sy0 = tx0 - gx0, ty0 - gy0
        global_mask[ty0:ty1, tx0:tx1] = constrained[sy0:sy0 + (ty1 - ty0), sx0:sx0 + (tx1 - tx0)]
    return global_mask, {
        "page_region_px": [x0, y0, x1, y1],
        "local_tight_px": list(tight),
        "target_rgb": list(map(int, target)),
        "background_rgb_median": [round(float(x), 2) for x in bg],
        "h_ink_px": h_ink,
        "w_ink_px": w_ink,
        "area_px": int(constrained.sum()),
    }


def vector_isolate_glyph(candidate: np.ndarray, selector_meta: dict, crop_box: tuple[int, int, int, int]):
    selector_path = PAYLOAD / "vector_selectors" / selector_meta["filename"]
    selector_rgba = np.array(Image.open(selector_path).convert("RGBA"))
    selector_local = selector_rgba[:, :, 3] > 0
    base_x = int(round(float(selector_meta["clip"]["x"]) * SCALE)) - crop_box[0]
    base_y = int(round(float(selector_meta["clip"]["y"]) * SCALE)) - crop_box[1]
    best = None
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            canvas = np.zeros_like(candidate)
            x0, y0 = base_x + dx, base_y + dy
            tx0, ty0 = max(0, x0), max(0, y0)
            tx1, ty1 = min(canvas.shape[1], x0 + selector_local.shape[1]), min(canvas.shape[0], y0 + selector_local.shape[0])
            if tx1 <= tx0 or ty1 <= ty0:
                continue
            sx0, sy0 = tx0 - x0, ty0 - y0
            canvas[ty0:ty1, tx0:tx1] = selector_local[sy0:sy0 + (ty1 - ty0), sx0:sx0 + (tx1 - tx0)]
            expanded = np.array(Image.fromarray((canvas * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
            intersection = int(np.logical_and(candidate, expanded).sum())
            score = intersection / max(1, int(expanded.sum()))
            if best is None or (score, intersection) > (best[0], best[1]):
                best = (score, intersection, dx, dy, canvas, expanded)
    if best is None:
        raise RuntimeError(f"cannot place vector selector {selector_meta['filename']}")
    score, intersection, dx, dy, exact_selector, expanded = best
    final = candidate & expanded
    foreign = candidate & ~expanded
    return final, exact_selector, {
        "vector_selector_file": f"vector_selectors/{selector_meta['filename']}",
        "vector_use_index": int(selector_meta["index"]),
        "selector_alignment_shift_px": [int(dx), int(dy)],
        "selector_alignment_score": round(float(score), 6),
        "selector_native_area_px": int(exact_selector.sum()),
        "candidate_pre_selector_area_px": int(candidate.sum()),
        "foreign_pixel_px_removed_by_vector_selector": int(foreign.sum()),
    }


def sample_path(path_ops, scale: float, crop_box):
    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    cur = (0.0, 0.0)

    def cv(pt):
        return (float(pt[0]) * scale - crop_box[0], float(pt[1]) * scale - crop_box[1])

    for op in path_ops:
        code = op[0]
        if code == "m":
            if current:
                subpaths.append(current)
            cur = cv(op[1])
            current = [cur]
        elif code == "l":
            cur = cv(op[1])
            current.append(cur)
        elif code == "c":
            p0 = cur
            p1, p2, p3 = cv(op[1]), cv(op[2]), cv(op[3])
            for step in range(1, 25):
                t = step / 24.0
                mt = 1.0 - t
                x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
                y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
                current.append((x, y))
            cur = p3
        elif code == "h":
            if current and current[-1] != current[0]:
                current.append(current[0])
    if current:
        subpaths.append(current)
    return subpaths


def drawing_geometry_mask(obj: dict, role: str, crop_box, crop_rgb: np.ndarray):
    w, h = crop_rgb.shape[1], crop_rgb.shape[0]
    geom_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(geom_img)
    subpaths = sample_path(obj.get("path", []), SCALE, crop_box)
    width = max(1, int(math.ceil(float(obj.get("linewidth") or 0.5) * SCALE)))
    fill_is_foreground = role in {"PLANE_FILL", "OPAQUE_HALO"}
    stroke_is_foreground = role not in {"PLANE_FILL", "OPAQUE_HALO"}
    if fill_is_foreground and obj.get("fill"):
        for pts in subpaths:
            if len(pts) >= 3:
                draw.polygon(pts, fill=255)
    if stroke_is_foreground and obj.get("stroke"):
        for pts in subpaths:
            if len(pts) >= 2:
                draw.line(pts, fill=255, width=width, joint="curve")
    geom = np.array(geom_img) > 0
    if role in {"PLANE_FILL", "OPAQUE_HALO"}:
        return geom, geom.copy(), int(width)

    # Geometry is only the selector. Final raw pixels are retained from the official
    # pdftoppm 300 dpi raster; the 1 px expansion compensates rasterizer edge phase.
    selector = np.array(geom_img.filter(ImageFilter.MaxFilter(3))) > 0
    color = rgb255(obj.get("stroking_color"))
    target = np.array(color, dtype=np.float32)
    # float32 avoids signed-integer overflow while preserving the native raster values.
    diff = np.sqrt(np.sum((crop_rgb.astype(np.float32) - target) ** 2, axis=2))
    visible = selector & (diff <= 115)
    if not visible.any():
        visible = geom.copy()
    return geom, visible, int(width)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))


def save_mask(mask: np.ndarray, path: Path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def overlay_image(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    arr = rgb.copy()
    arr[mask] = np.array([255, 0, 0], dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def make_glyph_cell(crop_img: Image.Image, mask: np.ndarray, obj: dict) -> Image.Image:
    bx = mask_bbox(mask)
    if bx == (0, 0, 0, 0):
        bx = obj["bbox_crop_px"]
    pad = 4
    x0, y0, x1, y1 = bx
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(crop_img.width, x1 + pad), min(crop_img.height, y1 + pad)
    original = crop_img.crop((x0, y0, x1, y1))
    local_mask = mask[y0:y1, x0:x1]
    over_arr = np.array(original).copy()
    over_arr[local_mask] = [255, 0, 0]
    overlay = Image.fromarray(over_arr)
    monly = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    panels = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in (original, overlay, monly)]
    font = ImageFont.load_default()
    cw, ch = 1500, 460
    cell = Image.new("RGB", (cw, ch), "white")
    d = ImageDraw.Draw(cell)
    codepoints = "+".join(f"U+{ord(x):04X}" for x in obj["text"])
    d.text((10, 8), f"{obj['element_id']} {codepoints} parent={obj['parent']} H={obj['h_ink_px']} A={obj['area_px']}", fill="black", font=font)
    labels = ["ORIGINAL 8x NN", "TARGET OVERLAY 8x NN", "MASK ONLY 8x NN"]
    x = 10
    for label, panel in zip(labels, panels):
        d.text((x, 28), label, fill="black", font=font)
        max_w, max_h = 470, 410
        # No resize here: the target evidence stays physical 8x. Clip only if a pathological bbox exceeds cell.
        cell.paste(panel.crop((0, 0, min(panel.width, max_w), min(panel.height, max_h))), (x, 45))
        x += 495
    return cell


def make_drawing_cell(crop_img: Image.Image, mask: np.ndarray, obj: dict) -> Image.Image:
    bx = mask_bbox(mask)
    x0, y0, x1, y1 = bx
    pad = 8
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(crop_img.width, x1 + pad), min(crop_img.height, y1 + pad)
    original = crop_img.crop((x0, y0, x1, y1))
    local = mask[y0:y1, x0:x1]
    over = np.array(original).copy()
    over[local] = [255, 0, 0]
    monly = Image.fromarray(np.where(local, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    cell = Image.new("RGB", (1800, 420), "white")
    d = ImageDraw.Draw(cell)
    d.text((10, 8), f"{obj['element_id']} role={obj['role']} raw_px={obj['area_px']} bbox={obj['bbox_crop_px']}", fill="black", font=ImageFont.load_default())
    for j, (label, im) in enumerate((("ORIGINAL 1x", original), ("TARGET OVERLAY 1x", Image.fromarray(over)), ("MASK ONLY 1x", monly))):
        x = 10 + j * 590
        d.text((x, 26), label, fill="black", font=ImageFont.load_default())
        # Preserve native pixels; long objects are clipped only at the cell display edge, while their full raw masks are separate files.
        cell.paste(im.crop((0, 0, min(im.width, 570), min(im.height, 370))), (x, 44))
    return cell


def sparse(mask: np.ndarray):
    ys, xs = np.nonzero(mask)
    return np.column_stack((ys, xs)).astype(np.int32)


def bbox_clearance(a, b) -> int:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0, bx0 - ax1, ax0 - bx1)
    dy = max(0, by0 - ay1, ay0 - by1)
    return max(dx, dy)


def exact_clearance(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[int, int]:
    overlap = int(np.logical_and(mask_a, mask_b).sum())
    if overlap:
        return overlap, 0
    ba, bb = mask_bbox(mask_a), mask_bbox(mask_b)
    lower = bbox_clearance(ba, bb)
    if lower > 24:
        return 0, int(lower)
    aa, bbp = sparse(mask_a), sparse(mask_b)
    if len(aa) == 0 or len(bbp) == 0:
        return 0, -1
    # Only near pairs reach this branch. Chunked Chebyshev distance keeps memory bounded.
    best = 10**9
    for start in range(0, len(aa), 256):
        d = np.max(np.abs(aa[start:start + 256, None, :] - bbp[None, :, :]), axis=2)
        best = min(best, int(d.min()))
        if best <= 1:
            break
    return 0, max(0, best - 1)


def relation_policy(a: dict, b: dict):
    if a["kind"] == "DRAWING" and b["kind"] == "GLYPH":
        a, b = b, a
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH":
        if a["parent"] == b["parent"]:
            return False, 0, "SAME_SEMANTIC_PARENT_INTERNAL_TYPOGRAPHY"
        return True, 4, "TEXT_TEXT_INDEPENDENT_PARENT"
    if a["kind"] == "GLYPH" and b["kind"] == "DRAWING":
        if b["role"] in {"PLANE_FILL", "OPAQUE_HALO"}:
            return False, 0, "BACKGROUND_OR_REAL_OPAQUE_HALO"
        if b["role"] == "NORM_CARD_BORDER" and a["parent"] == "NORM_FORMULA":
            return True, 5, "NODE_TEXT_TO_FINAL_VISIBLE_BORDER"
        return True, 3, "TEXT_OR_FORMULA_TO_LINE_ARROW_MARKER"
    # Drawing/drawing: every pair remains in the denominator. Source-designed joins are explicit.
    design_pairs = {
        frozenset(x) for x in [
            ("D001", "D006"), ("D002", "D006"),
            ("D003", "D007"), ("D004", "D008"), ("D005", "D009"),
            ("D003", "D004"), ("D003", "D005"), ("D004", "D005"),
            ("D004", "D010"), ("D005", "D010"),
            ("D005", "D013"), ("D011", "D014"),
            # The vector/residual/orthogonality construction intentionally crosses or
            # terminates on the visible upper boundary of the drawn subspace band.
            ("D001", "D003"), ("D001", "D005"),
            ("D001", "D010"), ("D001", "D011"),
        ]
    }
    pair = frozenset((a["element_id"], b["element_id"]))
    if a["role"] in {"PLANE_FILL", "OPAQUE_HALO"} or b["role"] in {"PLANE_FILL", "OPAQUE_HALO"}:
        return False, 0, "BACKGROUND_OR_OCCLUSION_COMPONENT"
    if pair in design_pairs:
        return False, 0, "SOURCE_DESIGNED_GEOMETRIC_JOIN"
    return True, 0, "INDEPENDENT_DRAWING_PAIR_NO_SHARED_PIXEL"


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def relation_evidence(crop_rgb: np.ndarray, masks: dict[str, np.ndarray], row: dict, out_dir: Path):
    a, b = row["a_id"], row["b_id"]
    union = masks[a] | masks[b]
    inter_full = masks[a] & masks[b]
    # For a provisional overlap, centre the ROI on the actual intersecting pixels;
    # otherwise centre on the union. This prevents a long line from displacing the evidence.
    focus = inter_full if inter_full.any() else union
    x0, y0, x1, y1 = mask_bbox(focus)
    pad = 10
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(crop_rgb.shape[1], x1 + pad), min(crop_rgb.shape[0], y1 + pad)
    # Cap very long distant relations; critical selection normally keeps this tight.
    if x1 - x0 > 420:
        mid = (x0 + x1) // 2
        x0, x1 = max(0, mid - 210), min(crop_rgb.shape[1], mid + 210)
    if y1 - y0 > 260:
        mid = (y0 + y1) // 2
        y0, y1 = max(0, mid - 130), min(crop_rgb.shape[0], mid + 130)
    raw = crop_rgb[y0:y1, x0:x1]
    ma, mb = masks[a][y0:y1, x0:x1], masks[b][y0:y1, x0:x1]
    inter = ma & mb
    over = raw.copy()
    over[ma] = [255, 0, 0]
    over[mb] = [0, 96, 255]
    over[inter] = [255, 0, 255]
    base = out_dir / row["relation_id"]
    base.mkdir(parents=True, exist_ok=True)
    Image.fromarray(raw).save(base / "raw_1x.png")
    Image.fromarray(np.where(ma, 0, 255).astype(np.uint8), mode="L").save(base / "mask_A_1x.png")
    Image.fromarray(np.where(mb, 0, 255).astype(np.uint8), mode="L").save(base / "mask_B_1x.png")
    Image.fromarray(np.where(inter, 0, 255).astype(np.uint8), mode="L").save(base / "intersection_1x.png")
    Image.fromarray(over).save(base / "overlay_1x.png")
    Image.fromarray(over).resize((over.shape[1] * 8, over.shape[0] * 8), Image.Resampling.NEAREST).save(base / "overlay_8x_nearest.png")
    row["evidence_dir"] = str(base.relative_to(PAYLOAD)).replace("\\", "/")


def main():
    for p in [PAYLOAD, TMP, PAYLOAD / "masks" / "glyph", PAYLOAD / "masks" / "drawing", PAYLOAD / "contact_sheets", PAYLOAD / "relations"]:
        p.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(PDF))
    identity = {
        "handoff_id": HANDOFF_ID,
        "model_effort": "gpt-5.6-sol/xhigh",
        "fork_turns": "none",
        "official_pdf": str(PDF),
        "pdf_pages": len(reader.pages),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "physical_page": PAGE_NUMBER,
        "printed_page": 16,
        "figure_number": "2.1",
        "uid": "FIG-P033-01",
        "page_pt": list(PAGE_PT),
        "locator_query": "向量的正交分解",
        "locator_hits": [{"physical_page": 29, "text_offset_in_pdftotext_page": 1048}],
        "independence": "fresh isolated; no prior FIG-P033 evidence, role report, state, inventory, chat, git-history conclusion, or main acceptance read",
    }
    (PAYLOAD / "candidate_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

    full_200 = Image.open(PAYLOAD / "full_page_200dpi.png").convert("RGB")
    full_300 = Image.open(TMP / "full_page_300dpi.png").convert("RGB")
    full_gray = Image.open(TMP / "full_page_gray_300dpi.png").convert("L")
    crop_box = px_bbox(FIGURE_PDF_BBOX)
    body_box = px_bbox(BODY_PDF_BBOX)
    crop = full_300.crop(crop_box)
    body = full_300.crop(body_box)
    gray_crop = full_gray.crop(crop_box)
    crop.save(PAYLOAD / "figure_crop_300dpi.png")
    body.save(PAYLOAD / "standalone_300dpi.png")
    gray_crop.save(PAYLOAD / "grayscale_300dpi.png")
    render_meta = {
        "renderer": "Poppler pdftoppm",
        "source_pdf": str(PDF),
        "physical_page": PAGE_NUMBER,
        "page_pt": list(PAGE_PT),
        "full_page_200dpi_native_px": list(full_200.size),
        "full_page_300dpi_native_px": list(full_300.size),
        "figure_pdf_bbox_x0_top_x1_bottom": list(FIGURE_PDF_BBOX),
        "figure_crop_integer_page_px": list(crop_box),
        "figure_crop_300dpi_native_px": list(crop.size),
        "standalone_pdf_bbox_x0_top_x1_bottom": list(BODY_PDF_BBOX),
        "standalone_integer_page_px": list(body_box),
        "standalone_300dpi_native_px": list(body.size),
        "grayscale_300dpi_native_px": list(gray_crop.size),
        "resized_after_render": False,
    }
    (PAYLOAD / "render_metadata.json").write_text(json.dumps(render_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    crop_rgb = np.array(crop)
    page_rgb = np.array(full_300)
    objects: list[dict] = []
    masks: dict[str, np.ndarray] = {}
    glyph_rows: list[dict] = []

    with pdfplumber.open(str(PDF)) as pdf:
        page = pdf.pages[PAGE_INDEX]
        selected_chars = [
            (char_index, c) for char_index, c in enumerate(page.chars)
            if c.get("text", "").strip()
            and FIGURE_PDF_BBOX[1] <= float(c["top"])
            and float(c["bottom"]) <= FIGURE_PDF_BBOX[3]
            and FIGURE_PDF_BBOX[0] <= (float(c["x0"]) + float(c["x1"])) / 2 <= FIGURE_PDF_BBOX[2]
        ]
        selected_chars.sort(key=lambda item: (round(float(item[1]["top"]), 3), float(item[1]["x0"]), float(item[1]["bottom"])))
        selector_payload = json.loads((PAYLOAD / "vector_selectors" / "vector_selector_metadata.json").read_text(encoding="utf-8"))
        selector_by_index = {int(x["index"]): x for x in selector_payload["items"]}
        if len(selector_by_index) != 85:
            raise RuntimeError("vector selector denominator mismatch")
        pre_dir = PAYLOAD / "masks" / "glyph_pre_color_candidate"
        selector_dir = PAYLOAD / "masks" / "glyph_aligned_vector_selector"
        pre_dir.mkdir(parents=True, exist_ok=True)
        selector_dir.mkdir(parents=True, exist_ok=True)
        for i, (char_index, c) in enumerate(selected_chars, 1):
            eid = f"G{i:03d}"
            candidate, meta = glyph_mask(page_rgb, c, crop_box)
            save_mask(candidate, pre_dir / f"{eid}.png")
            if char_index not in selector_by_index:
                raise RuntimeError(f"missing vector selector for PDF char index {char_index}")
            mask, exact_selector, selector_stats = vector_isolate_glyph(candidate, selector_by_index[char_index], crop_box)
            save_mask(exact_selector, selector_dir / f"{eid}.png")
            tight = mask_bbox(mask)
            meta.update({
                "h_ink_px": tight[3] - tight[1] if tight != (0, 0, 0, 0) else 0,
                "w_ink_px": tight[2] - tight[0] if tight != (0, 0, 0, 0) else 0,
                "area_px": int(mask.sum()),
                **selector_stats,
            })
            masks[eid] = mask
            cls = char_class(c["text"], float(c["size"]))
            bbox_crop = [
                math.floor(float(c["x0"]) * SCALE) - crop_box[0],
                math.floor(float(c["top"]) * SCALE) - crop_box[1],
                math.ceil(float(c["x1"]) * SCALE) - crop_box[0],
                math.ceil(float(c["bottom"]) * SCALE) - crop_box[1],
            ]
            obj = {
                "element_id": eid,
                "safe_filename": f"{eid}.png",
                "kind": "GLYPH",
                "text": c["text"],
                "unicode": "+".join(f"U+{ord(x):04X}" for x in c["text"]),
                "parent": char_parent(c),
                "role": "CAPTION_TEXT" if char_parent(c) == "CAPTION" else "FIGURE_TEXT_OR_FORMULA",
                "class": cls,
                "fontname": c.get("fontname", ""),
                "pdf_extracted_size_pt": round(float(c.get("size", 0)), 4),
                "pdf_char_index": char_index,
                "pdf_bbox": [round(float(c[k]), 5) for k in ("x0", "top", "x1", "bottom")],
                "bbox_crop_px": bbox_crop,
                **meta,
                "clip_pixel_count": int(mask[0].sum() + mask[-1].sum() + mask[:, 0].sum() + mask[:, -1].sum()),
                "empty_mask": not bool(mask.any()),
                "legacy_pixel_min": LEGACY_LIMIT[cls],
                "r168_pixel_disposition": "ADVISORY_ONLY" if meta["h_ink_px"] < LEGACY_LIMIT[cls] else "MEETS_LEGACY_NUMERIC_REFERENCE",
            }
            objects.append(obj)
            glyph_rows.append(obj)
            save_mask(mask, PAYLOAD / "masks" / "glyph" / f"{eid}.png")

        drawing_role = {
            ("lines", 8): "PLANE_BOUNDARY",
            ("lines", 9): "PLANE_BOUNDARY",
            ("lines", 10): "X_VECTOR_LINE",
            ("lines", 11): "P_VECTOR_LINE",
            ("lines", 12): "R_RESIDUAL_DASHED_LINE",
            ("curves", 6): "PLANE_FILL",
            ("curves", 7): "X_VECTOR_ARROWHEAD",
            ("curves", 8): "P_VECTOR_ARROWHEAD",
            ("curves", 9): "R_RESIDUAL_ARROWHEAD",
            ("curves", 10): "RIGHT_ANGLE_MARKER",
            ("curves", 11): "DISTANCE_BRACE",
            ("curves", 12): "NORM_CARD_BORDER",
            ("rects", 0): "OPAQUE_HALO",
            ("rects", 1): "OPAQUE_HALO",
        }
        selected_drawings = []
        for kind in ("lines", "curves", "rects"):
            for source_index, obj in enumerate(getattr(page, kind)):
                if (
                    float(obj.get("bottom", -1)) >= FIGURE_PDF_BBOX[1]
                    and float(obj.get("top", 9999)) <= FIGURE_PDF_BBOX[3]
                    and float(obj.get("x1", -1)) >= FIGURE_PDF_BBOX[0]
                    and float(obj.get("x0", 9999)) <= FIGURE_PDF_BBOX[2]
                ):
                    selected_drawings.append((kind, source_index, obj))
        drawing_rows = []
        for i, (kind, source_index, d) in enumerate(selected_drawings, 1):
            eid = f"D{i:03d}"
            role = drawing_role[(kind, source_index)]
            geom, visible, width = drawing_geometry_mask(d, role, crop_box, crop_rgb)
            masks[eid] = visible
            bbox = mask_bbox(visible)
            obj = {
                "element_id": eid,
                "safe_filename": f"{eid}.png",
                "kind": "DRAWING",
                "text": "",
                "unicode": "",
                "parent": role,
                "role": role,
                "class": "BACKGROUND_OR_HALO" if role in {"PLANE_FILL", "OPAQUE_HALO"} else "GEOMETRIC_FOREGROUND",
                "pdf_object_kind": kind,
                "pdf_object_index": source_index,
                "pdf_bbox": [round(float(d[k]), 5) for k in ("x0", "top", "x1", "bottom")],
                "bbox_crop_px": list(bbox),
                "linewidth_pt": round(float(d.get("linewidth") or 0), 5),
                "native_stroke_width_px": width,
                "stroking_color": rgb255(d.get("stroking_color")),
                "non_stroking_color": rgb255(d.get("non_stroking_color")),
                "fill": bool(d.get("fill")),
                "stroke": bool(d.get("stroke")),
                "path_command_count": len(d.get("path", [])),
                "area_px": int(visible.sum()),
                "geometry_selector_area_px": int(geom.sum()),
                "h_ink_px": bbox[3] - bbox[1] if bbox != (0, 0, 0, 0) else 0,
                "w_ink_px": bbox[2] - bbox[0] if bbox != (0, 0, 0, 0) else 0,
                "clip_pixel_count": int(visible[0].sum() + visible[-1].sum() + visible[:, 0].sum() + visible[:, -1].sum()),
                "empty_mask": not bool(visible.any()),
            }
            objects.append(obj)
            drawing_rows.append(obj)
            save_mask(visible, PAYLOAD / "masks" / "drawing" / f"{eid}.png")
            save_mask(geom, PAYLOAD / "masks" / "drawing" / f"{eid}_pre_selector.png")

    # Restore final-visible drawing masks where real opaque white label backgrounds
    # cover earlier geometry in the PDF paint order. Keep pre-occlusion masks alongside.
    occlusion_map = {
        "D001": ["D014"],
        "D005": ["D013"],
        "D011": ["D013", "D014"],
    }
    drawing_by_id = {o["element_id"]: o for o in drawing_rows}
    for did, halo_ids in occlusion_map.items():
        pre = masks[did].copy()
        final = pre.copy()
        for hid in halo_ids:
            final &= ~masks[hid]
        masks[did] = final
        save_mask(pre, PAYLOAD / "masks" / "drawing" / f"{did}_pre_occlusion.png")
        save_mask(final, PAYLOAD / "masks" / "drawing" / f"{did}.png")
        row = drawing_by_id[did]
        bx = mask_bbox(final)
        row.update({
            "bbox_crop_px": list(bx),
            "area_px": int(final.sum()),
            "h_ink_px": bx[3] - bx[1] if bx != (0, 0, 0, 0) else 0,
            "w_ink_px": bx[2] - bx[0] if bx != (0, 0, 0, 0) else 0,
            "clip_pixel_count": int(final[0].sum() + final[-1].sum() + final[:, 0].sum() + final[:, -1].sum()),
            "empty_mask": not bool(final.any()),
            "occlusion_subtracted_by": "+".join(halo_ids),
            "pre_occlusion_area_px": int(pre.sum()),
        })

    # Exact denominator freeze.
    expected_n = 99
    if len(objects) != expected_n or len(glyph_rows) != 85 or len(drawing_rows) != 14:
        raise RuntimeError(f"denominator mismatch: N={len(objects)}, glyph={len(glyph_rows)}, drawing={len(drawing_rows)}")
    if len({o["element_id"] for o in objects}) != len(objects):
        raise RuntimeError("duplicate element IDs")
    if any(o["empty_mask"] for o in objects):
        raise RuntimeError("empty object mask present")

    object_fields = [
        "element_id", "safe_filename", "kind", "text", "unicode", "parent", "role", "class",
        "fontname", "pdf_extracted_size_pt", "pdf_char_index", "pdf_object_kind", "pdf_object_index", "pdf_bbox",
        "bbox_crop_px", "h_ink_px", "w_ink_px", "area_px", "legacy_pixel_min",
        "r168_pixel_disposition", "clip_pixel_count", "empty_mask", "path_command_count",
        "linewidth_pt", "native_stroke_width_px", "fill", "stroke", "vector_selector_file", "vector_use_index",
        "selector_alignment_shift_px", "selector_alignment_score", "selector_native_area_px",
        "candidate_pre_selector_area_px", "foreign_pixel_px_removed_by_vector_selector",
        "occlusion_subtracted_by", "pre_occlusion_area_px",
    ]
    write_csv(PAYLOAD / "visible_object_ledger.csv", objects, object_fields)
    (PAYLOAD / "visible_object_ledger.json").write_text(json.dumps(objects, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(PAYLOAD / "after_pixel_measurements.csv", glyph_rows, object_fields)
    write_csv(PAYLOAD / "foreground_drawing_path_ledger.csv", drawing_rows, object_fields)

    # Machine-only mask overlay for all objects. Human acceptance is written separately and never by this script.
    all_foreground = np.zeros((crop.height, crop.width), dtype=bool)
    for o in objects:
        if o["role"] not in {"PLANE_FILL", "OPAQUE_HALO"}:
            all_foreground |= masks[o["element_id"]]
    overlay_image(crop_rgb, all_foreground).save(PAYLOAD / "after_text_measurement_overlay_300dpi.png")

    # Contact sheets: fixed, deterministic mapping; no reviewer or decision fields are generated here.
    glyph_cells = [make_glyph_cell(crop, masks[o["element_id"]], o) for o in glyph_rows]
    glyph_index_rows = []
    per_sheet = 8
    for s0 in range(0, len(glyph_cells), per_sheet):
        chunk = glyph_cells[s0:s0 + per_sheet]
        sheet_no = s0 // per_sheet + 1
        sheet = Image.new("RGB", (3000, 1840), (238, 238, 238))
        for j, cell in enumerate(chunk):
            x = (j % 2) * 1500
            y = (j // 2) * 460
            sheet.paste(cell, (x, y))
            glyph_index_rows.append({
                "element_id": glyph_rows[s0 + j]["element_id"],
                "sheet": f"glyph_contact_sheet_{sheet_no:02d}.png",
                "cell": j + 1,
            })
        sheet.save(PAYLOAD / "contact_sheets" / f"glyph_contact_sheet_{sheet_no:02d}.png")
    write_csv(PAYLOAD / "glyph_contact_index.csv", glyph_index_rows, ["element_id", "sheet", "cell"])

    drawing_cells = [make_drawing_cell(crop, masks[o["element_id"]], o) for o in drawing_rows]
    drawing_index_rows = []
    for s0 in range(0, len(drawing_cells), 4):
        chunk = drawing_cells[s0:s0 + 4]
        sheet_no = s0 // 4 + 1
        sheet = Image.new("RGB", (1800, 1680), (238, 238, 238))
        for j, cell in enumerate(chunk):
            sheet.paste(cell, (0, j * 420))
            drawing_index_rows.append({
                "element_id": drawing_rows[s0 + j]["element_id"],
                "sheet": f"drawing_contact_sheet_{sheet_no:02d}.png",
                "cell": j + 1,
            })
        sheet.save(PAYLOAD / "contact_sheets" / f"drawing_contact_sheet_{sheet_no:02d}.png")
    write_csv(PAYLOAD / "drawing_contact_index.csv", drawing_index_rows, ["element_id", "sheet", "cell"])

    # All N choose 2 unordered relations, including design-whitelisted/background pairs.
    relations = []
    critical = []
    for n, (a, b) in enumerate(itertools.combinations(objects, 2), 1):
        aid, bid = a["element_id"], b["element_id"]
        applicable, required, rationale = relation_policy(a, b)
        if applicable:
            overlap, clearance = exact_clearance(masks[aid], masks[bid])
        else:
            # Non-quality background/design pairs remain fully enumerated, but do not
            # spend quadratic distance work on large fills. Shared raw pixels are still counted.
            overlap = int(np.logical_and(masks[aid], masks[bid]).sum())
            clearance = 0 if overlap else bbox_clearance(mask_bbox(masks[aid]), mask_bbox(masks[bid]))
        empty = a["empty_mask"] or b["empty_mask"]
        if empty:
            decision = "MACHINE_EVIDENCE_FAIL_EMPTY_MASK"
        elif applicable and overlap > 0:
            decision = "MACHINE_HARD_FAIL_ILLEGAL_OVERLAP"
        elif applicable and required > 0 and clearance < required:
            decision = "MACHINE_HARD_FAIL_CLEARANCE"
        elif applicable:
            decision = "MACHINE_PASS"
        else:
            decision = "SEMANTIC_WHITELIST_OR_BACKGROUND"
        row = {
            "relation_id": f"R{n:04d}",
            "a_id": aid,
            "b_id": bid,
            "a_kind": a["kind"],
            "b_kind": b["kind"],
            "a_parent_role": f"{a['parent']}|{a['role']}",
            "b_parent_role": f"{b['parent']}|{b['role']}",
            "quality_applicable": applicable,
            "required_clearance_px": required,
            "overlap_pixel_count": overlap,
            "clearance_px": clearance,
            "policy_rationale": rationale,
            "machine_decision": decision,
            "evidence_dir": "",
        }
        # Every machine fail and every applicable relation within a 12 px safety band is critical.
        is_critical = applicable and (decision.startswith("MACHINE_HARD_FAIL") or (clearance >= 0 and clearance < max(12, required + 4)))
        if is_critical:
            critical.append(row)
        relations.append(row)
    if len(relations) != expected_n * (expected_n - 1) // 2:
        raise RuntimeError("unordered pair denominator mismatch")
    for row in critical:
        relation_evidence(crop_rgb, masks, row, PAYLOAD / "relations")

    relation_fields = [
        "relation_id", "a_id", "b_id", "a_kind", "b_kind", "a_parent_role", "b_parent_role",
        "quality_applicable", "required_clearance_px", "overlap_pixel_count", "clearance_px",
        "policy_rationale", "machine_decision", "evidence_dir",
    ]
    write_csv(PAYLOAD / "after_overlap_report.csv", relations, relation_fields)
    (PAYLOAD / "after_overlap_report.json").write_text(json.dumps(relations, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(PAYLOAD / "critical_relations_index.csv", critical, relation_fields)

    # Machine facts only. R168 reserves 9.5 pt and 1--2 px micro-threshold deltas as advisory.
    source_audit = [
        {
            "scope": "tikzset slfig-FIG-P033-01 / tikzpicture font",
            "declaration": "font=\\fontsize{9.4pt}{11.2pt}\\selectfont",
            "declared_pt": "9.4",
            "graphics_scale": "1.0",
            "effective_pt": "9.4",
            "r168_disposition": "ADVISORY_ONLY",
            "note": "Below legacy 9.5 pt threshold; not a hard failure under the R168 boundary without actual unreadability/harm.",
        },
        {
            "scope": "residual label; shortest-distance label; norm note",
            "declaration": "font=\\fontsize{9.2pt}{10.9pt}\\selectfont",
            "declared_pt": "9.2",
            "graphics_scale": "1.0",
            "effective_pt": "9.2",
            "r168_disposition": "ADVISORY_ONLY",
            "note": "Below legacy 9.5 pt threshold; not a hard failure under the R168 boundary without actual unreadability/harm.",
        },
        {
            "scope": "caption",
            "declaration": "document figure caption style (outside TikZ source-local font override)",
            "declared_pt": "N/A",
            "graphics_scale": "1.0",
            "effective_pt": "PDF extracted 9.96",
            "r168_disposition": "REFERENCE",
            "note": "Caption is in the visible denominator and measured glyph by glyph.",
        },
    ]
    write_csv(PAYLOAD / "after_font_audit.csv", source_audit, ["scope", "declaration", "declared_pt", "graphics_scale", "effective_pt", "r168_disposition", "note"])

    math_semantics = {
        "objects": {
            "X_LABEL": "bold x is the original vector",
            "P_FORMULA": "p = P_S x in S is the orthogonal projection",
            "R_FORMULA": "r = x - p in S^perp is the residual",
            "NORM_FORMULA": "||x||^2 = ||p||^2 + ||r||^2 is the Pythagorean identity",
            "RIGHT_ANGLE_MARKER": "marks residual orthogonal to the subspace direction at p",
            "DISTANCE_BRACE": "labels the residual segment as the shortest distance",
        },
        "caption_consistency": "Caption states the same projection/residual/orthogonal-complement/shortest-distance relations shown in the figure.",
        "unassigned_math_rule_count": 0,
        "math_rule_explanation": "No separately drawn TeX fraction, radical bar, overline, underline, hat/vector accent, or cancellation rule occurs. Norm bars, operators, and superscripts are PDF glyphs G001-G019; all 14 non-text paths are assigned geometric/background/halo roles D001-D014.",
    }
    (PAYLOAD / "math_semantics_machine_ledger.json").write_text(json.dumps(math_semantics, ensure_ascii=False, indent=2), encoding="utf-8")

    machine_summary = {
        "object_count": len(objects),
        "glyph_count": len(glyph_rows),
        "drawing_path_count": len(drawing_rows),
        "unordered_pair_expected": len(objects) * (len(objects) - 1) // 2,
        "unordered_pair_actual": len(relations),
        "empty_mask_count": sum(int(o["empty_mask"]) for o in objects),
        "foreign_or_unassigned_object_count": 0,
        "clip_pixel_count_total": sum(int(o["clip_pixel_count"]) for o in objects),
        "machine_hard_fail_relation_count": sum(r["machine_decision"].startswith("MACHINE_HARD_FAIL") for r in relations),
        "machine_hard_fail_relations": [r["relation_id"] for r in relations if r["machine_decision"].startswith("MACHINE_HARD_FAIL")],
        "critical_relation_count": len(critical),
        "legacy_font_or_pixel_advisory_count": sum(o.get("r168_pixel_disposition") == "ADVISORY_ONLY" for o in glyph_rows) + 2,
        "r168_hard_boundary": "Only actual missing/tofu/wrong-code, unreadability, obvious imbalance, true clipping, illegal overlap, or geometric/mathematical semantic error is hard FAIL. Legacy 9.5 pt and 1--2 px micro differences are advisory.",
        "manual_fields_generated": False,
    }
    (PAYLOAD / "machine_summary.json").write_text(json.dumps(machine_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(machine_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
