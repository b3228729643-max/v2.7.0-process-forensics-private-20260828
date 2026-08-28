from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


HANDOFF_ID = "C-FIG-P667-01-R114-SA1-FRESH-ISOLATED-V1"
UID = "FIG-P667-01"
PDF_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE_PATH = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_conjugate_update.tex")
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa1_r114_fresh_isolated_v1")
OUT = ROOT / "machine"

EXPECTED_PDF_BYTES = 4_967_122
EXPECTED_PDF_SHA256 = "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6"
EXPECTED_SOURCE_BYTES = 3_252
EXPECTED_SOURCE_SHA256 = "1E2D755428EC466C6DF44B7684B81A354352653AE60476B4F717AD19F9D6CE15"

# Physical page is discovered from the current PDF by the caption semantics below.
SEARCH_NEEDLES = (
    "指数逐分量相加",
    "保留归一化常数还可得到",
    "Dirichlet– 多项共轭",
)
PAGE_INDEX = 713  # zero based; asserted against an independent whole-PDF semantic search
SCALE = 300.0 / 72.0
FIGURE_RECT_PT = fitz.Rect(84.0, 324.0, 516.0, 573.0)
FIGURE_CAPTION_RECT_PT = fitz.Rect(82.0, 322.0, 523.0, 603.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pt_rect(*vals: float) -> tuple[float, float, float, float]:
    return tuple(float(v) for v in vals)


# The denominator is frozen at semantic-object granularity. Formula constituents
# that are intentionally part of the same formula object remain one object; distinct
# explanatory labels, borders and arrows are separate objects.
OBJECTS = [
    {"id": "O01", "kind": "TEXT", "role": "row_label", "label": "先验核", "regions": [pt_rect(102.23, 341.96, 132.12, 356.38)]},
    {"id": "O02", "kind": "FORMULA", "role": "prior_kernel", "label": "p(theta|alpha) proportional product theta_i^(alpha_i-1)", "regions": [pt_rect(203.03, 351.02, 266.49, 363.62), pt_rect(266.54, 356.04, 268.92, 362.59), pt_rect(275.69, 336.86, 291.63, 344.83)]},
    {"id": "O03", "kind": "TEXT", "role": "formula_annotation", "label": "先验指数", "regions": [pt_rect(266.73, 346.80, 300.60, 355.87)]},
    {"id": "O04", "kind": "FORMULA", "role": "operator", "label": "multiplication sign", "regions": [pt_rect(247.72, 374.99, 258.48, 389.93)]},
    {"id": "O05", "kind": "LINE_ARROW", "role": "brace", "label": "prior-likelihood exponent brace", "regions": [pt_rect(358.75, 328.05, 362.65, 437.00)]},
    {"id": "O06", "kind": "TEXT", "role": "brace_annotation", "label": "指数逐分量相加", "regions": [pt_rect(368.67, 378.84, 430.04, 388.23)]},
    {"id": "O07", "kind": "TEXT", "role": "row_label", "label": "似然核", "regions": [pt_rect(102.23, 407.55, 132.12, 421.98)]},
    {"id": "O08", "kind": "FORMULA", "role": "likelihood_kernel", "label": "p(n|theta) proportional product theta_i^n_i", "regions": [pt_rect(211.99, 416.16, 274.47, 428.76), pt_rect(274.52, 421.18, 276.90, 427.73), pt_rect(279.75, 402.00, 286.45, 409.97)]},
    {"id": "O09", "kind": "TEXT", "role": "formula_annotation", "label": "计数", "regions": [pt_rect(274.70, 411.94, 291.64, 421.01)]},
    {"id": "O10", "kind": "TEXT", "role": "row_label", "label": "后验核", "regions": [pt_rect(102.23, 473.15, 132.12, 487.57)]},
    {"id": "O11", "kind": "FORMULA", "role": "posterior_kernel", "label": "p(theta|n,alpha) proportional product theta_i^(alpha_i+n_i-1)", "regions": [pt_rect(194.25, 482.67, 266.80, 495.27), pt_rect(266.85, 487.69, 269.24, 494.24), pt_rect(274.20, 467.59, 302.22, 475.57)]},
    {"id": "O12", "kind": "TEXT", "role": "formula_annotation", "label": "逐分量相加", "regions": [pt_rect(267.04, 478.45, 309.38, 487.52)]},
    {"id": "O13", "kind": "FORMULA", "role": "posterior_result", "label": "theta|n distributed Dir(alpha+n)", "regions": [pt_rect(431.87, 470.54, 483.32, 491.28)]},
    {"id": "O14", "kind": "NODE_BORDER", "role": "posterior_box", "label": "posterior result rounded box", "regions": [pt_rect(403.74, 461.08, 511.46, 500.76)], "vector": "rounded_rect"},
    {"id": "O15", "kind": "LINE_ARROW", "role": "main_update_arrow", "label": "posterior-kernel to posterior-result arrow", "regions": [pt_rect(351.00, 479.35, 402.25, 482.50)]},
    {"id": "O16", "kind": "FORMULA", "role": "marginal_formula", "label": "Dirichlet-multinomial marginal formula", "regions": [pt_rect(403.59, 538.20, 510.41, 561.90)]},
    {"id": "O17", "kind": "TEXT", "role": "formula_annotation", "label": "保留归一化常数", "regions": [pt_rect(426.91, 562.13, 488.28, 571.52)]},
    {"id": "O18", "kind": "LINE_ARROW", "role": "marginal_branch_arrow", "label": "posterior-result to marginal dashed arrow", "regions": [pt_rect(455.95, 500.85, 459.25, 532.00)]},
    {"id": "O19", "kind": "NODE_BORDER", "role": "prior_strip", "label": "prior row rounded border", "regions": [pt_rect(155.31, 328.47, 350.90, 370.99)], "vector": "rounded_rect"},
    {"id": "O20", "kind": "NODE_BORDER", "role": "likelihood_strip", "label": "likelihood row rounded border", "regions": [pt_rect(155.31, 394.06, 350.90, 436.58)], "vector": "rounded_rect"},
    {"id": "O21", "kind": "NODE_BORDER", "role": "posterior_strip", "label": "posterior row rounded border", "regions": [pt_rect(155.31, 459.66, 350.90, 502.18)], "vector": "rounded_rect"},
    {"id": "O22", "kind": "TEXT", "role": "caption_number", "label": "图 34.7", "regions": [pt_rect(87.48, 572.99, 117.32, 589.50)]},
    {"id": "O23", "kind": "TEXT", "role": "caption_text", "label": "caption conclusion", "regions": [pt_rect(127.29, 576.55, 519.14, 600.70), pt_rect(87.48, 589.90, 459.85, 600.70)]},
]


DECISIVE_ROIS = [
    ("R01_prior_script", fitz.Rect(196, 330, 306, 366), "O02/O03: prior formula, script, and underbrace annotation"),
    ("R02_brace_label", fitz.Rect(350, 323, 435, 442), "O05/O06: brace and exponent-addition annotation"),
    ("R03_posterior_arrow", fitz.Rect(344, 454, 516, 506), "O13/O14/O15/O21: update arrow into posterior box"),
    ("R04_marginal_branch", fitz.Rect(396, 496, 515, 574), "O16/O17/O18: branch arrow, marginal formula, and note"),
    ("R05_caption_math", fitz.Rect(82, 570, 522, 603), "O22/O23: caption text and math codepoints"),
    ("R06_posterior_script", fitz.Rect(188, 462, 314, 499), "O11/O12: posterior exponent and componentwise-addition annotation"),
]


def pdf_to_crop_px(rect: tuple[float, float, float, float] | fitz.Rect, crop: fitz.Rect) -> tuple[int, int, int, int]:
    r = fitz.Rect(rect)
    return (
        int(math.floor((r.x0 - crop.x0) * SCALE)),
        int(math.floor((r.y0 - crop.y0) * SCALE)),
        int(math.ceil((r.x1 - crop.x0) * SCALE)),
        int(math.ceil((r.y1 - crop.y0) * SCALE)),
    )


def threshold_region(gray: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(gray.shape[1], x1), min(gray.shape[0], y1)
    m = np.zeros_like(gray, dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return m
    sub = gray[y0:y1, x0:x1]
    # Figure/caption backgrounds are white or near-white. A 20/255 contrast
    # threshold implements the strict protocol's effective-foreground rule.
    bg = float(np.percentile(sub, 98.0))
    ink = np.abs(sub.astype(np.float32) - bg) >= 20.0
    m[y0:y1, x0:x1] = ink
    return m


def rounded_border_mask(shape: tuple[int, int], box: tuple[int, int, int, int]) -> np.ndarray:
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=max(3, round(2 * SCALE)), outline=255, width=max(2, round(0.55 * SCALE)))
    return np.asarray(canvas) > 0


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def classify_script(text: str, size: float) -> str:
    visible = "".join(c for c in text if not c.isspace())
    if not visible:
        return "WHITESPACE"
    if size < 7.0:
        return "MATH_SCRIPT"
    if any("CJK" in unicodedata.name(c, "") or "IDEOGRAPH" in unicodedata.name(c, "") for c in visible):
        return "CJK_OR_MIXED"
    if any(c in "∝∏∫∑−+×∼=|∣!⏟⎵" for c in visible):
        return "MATH_BASE_OR_OPERATOR"
    if any(c.isdigit() or (c.isalpha() and c.upper() == c and c.lower() != c) for c in visible):
        return "LATIN_CAP_OR_DIGIT"
    if any(c.isalpha() for c in visible):
        return "LATIN_OR_GREEK_XHEIGHT"
    return "SYMBOL"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    identities = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "pdf": {"path": str(PDF_PATH), "bytes": PDF_PATH.stat().st_size, "sha256": sha256(PDF_PATH)},
        "source": {"path": str(SOURCE_PATH), "bytes": SOURCE_PATH.stat().st_size, "sha256": sha256(SOURCE_PATH)},
    }
    if identities["pdf"]["bytes"] != EXPECTED_PDF_BYTES or identities["pdf"]["sha256"] != EXPECTED_PDF_SHA256:
        raise RuntimeError("official PDF identity mismatch")
    if identities["source"]["bytes"] != EXPECTED_SOURCE_BYTES or identities["source"]["sha256"] != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("source identity mismatch")

    doc = fitz.open(PDF_PATH)
    matches = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if all(needle in text for needle in SEARCH_NEEDLES):
            matches.append(i)
    if matches != [PAGE_INDEX]:
        raise RuntimeError(f"semantic page locator mismatch: {matches}")
    page = doc[PAGE_INDEX]
    page_text = page.get_text()
    identities["pdf"]["page_count"] = doc.page_count
    identities["located_physical_page_1based"] = PAGE_INDEX + 1
    identities["located_printed_page_text"] = "701"
    identities["semantic_locator_count"] = len(matches)
    identities["semantic_locator_needles"] = list(SEARCH_NEEDLES)
    (OUT / "input_identities.json").write_text(json.dumps(identities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    matrix = fitz.Matrix(SCALE, SCALE)
    full_pix = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
    full_path = OUT / "full_page_native300dpi.png"
    full_pix.save(full_path)

    crop_pix = page.get_pixmap(matrix=matrix, clip=FIGURE_CAPTION_RECT_PT, alpha=False, colorspace=fitz.csRGB)
    crop_path = OUT / "figure_caption_native300dpi.png"
    crop_pix.save(crop_path)
    crop_image = Image.open(crop_path).convert("RGB")
    gray_image = ImageOps.grayscale(crop_image)
    gray_image.save(OUT / "figure_caption_grayscale_native300dpi.png")
    gray = np.asarray(gray_image)

    fig_pix = page.get_pixmap(matrix=matrix, clip=FIGURE_RECT_PT, alpha=False, colorspace=fitz.csRGB)
    fig_pix.save(OUT / "figure_only_native300dpi.png")

    object_masks: dict[str, np.ndarray] = {}
    object_rows = []
    for obj in OBJECTS:
        mask = np.zeros_like(gray, dtype=bool)
        for region in obj["regions"]:
            box = pdf_to_crop_px(region, FIGURE_CAPTION_RECT_PT)
            if obj.get("vector") == "rounded_rect":
                mask |= rounded_border_mask(gray.shape, box)
            else:
                mask |= threshold_region(gray, box)
        bbox = mask_bbox(mask)
        object_masks[obj["id"]] = mask
        ink_pixels = int(mask.sum())
        object_rows.append({
            "object_id": obj["id"],
            "kind": obj["kind"],
            "role": obj["role"],
            "label": obj["label"],
            "region_count": len(obj["regions"]),
            "mask_ink_pixels": ink_pixels,
            "mask_bbox_x0": "" if bbox is None else bbox[0],
            "mask_bbox_y0": "" if bbox is None else bbox[1],
            "mask_bbox_x1": "" if bbox is None else bbox[2],
            "mask_bbox_y1": "" if bbox is None else bbox[3],
        })

    with (OUT / "object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(object_rows[0]))
        w.writeheader()
        w.writerows(object_rows)

    # Complete unordered-pair enumeration, with visible-ink intersection and
    # measured nearest-ink clearance. It contains no reviewer/verdict fields.
    pair_rows = []
    candidate_count = 0
    overlap_total = 0
    for i, left in enumerate(OBJECTS):
        lm = object_masks[left["id"]]
        edt = distance_transform_edt(~lm) if lm.any() else None
        for right in OBJECTS[i + 1 :]:
            rm = object_masks[right["id"]]
            overlap = int(np.logical_and(lm, rm).sum())
            if edt is None or not rm.any():
                clearance = ""
            else:
                clearance = max(0.0, float(edt[rm].min()) - 1.0)
            textish_left = left["kind"] in {"TEXT", "FORMULA"}
            textish_right = right["kind"] in {"TEXT", "FORMULA"}
            if textish_left and textish_right:
                rule = "TEXT_TEXT"
                required = 4
            elif (textish_left and right["kind"] in {"LINE_ARROW"}) or (textish_right and left["kind"] in {"LINE_ARROW"}):
                rule = "TEXT_GRAPHIC"
                required = 3
            elif (textish_left and right["kind"] == "NODE_BORDER") or (textish_right and left["kind"] == "NODE_BORDER"):
                rule = "TEXT_NODE_BORDER"
                required = 5
            else:
                rule = "NO_TEXT_CLEARANCE_RULE"
                required = 0
            candidate = overlap > 0 or (clearance != "" and required > 0 and clearance < required)
            if candidate:
                candidate_count += 1
            overlap_total += overlap
            pair_rows.append({
                "pair_id": f"{left['id']}__{right['id']}",
                "object_a": left["id"],
                "object_b": right["id"],
                "kind_a": left["kind"],
                "kind_b": right["kind"],
                "clearance_rule": rule,
                "required_clearance_px": required,
                "visible_ink_overlap_px": overlap,
                "nearest_visible_ink_clearance_px": "" if clearance == "" else f"{clearance:.3f}",
                "machine_candidate": int(candidate),
            })
    expected_pairs = len(OBJECTS) * (len(OBJECTS) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise RuntimeError("pair denominator is incomplete")
    with (OUT / "unordered_pair_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
        w.writeheader()
        w.writerows(pair_rows)

    # Per-span PDF/vector audit: actual PDF font size, text bbox, and native-300dpi
    # effective-foreground ink height. No generated PASS/FAIL field is present.
    span_rows = []
    unique_codepoints: Counter[str] = Counter()
    raw = page.get_text("dict", sort=True)
    sid = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                x0, y0, x1, y1 = span["bbox"]
                if y1 < FIGURE_CAPTION_RECT_PT.y0 or y0 > FIGURE_CAPTION_RECT_PT.y1:
                    continue
                sid += 1
                text = span["text"]
                for ch in text:
                    if not ch.isspace():
                        unique_codepoints[ch] += 1
                box = pdf_to_crop_px(span["bbox"], FIGURE_CAPTION_RECT_PT)
                smask = threshold_region(gray, box)
                bb = mask_bbox(smask)
                h_ink = 0 if bb is None else bb[3] - bb[1]
                span_rows.append({
                    "span_id": f"S{sid:03d}",
                    "text": text,
                    "font": span["font"],
                    "pdf_font_size_pt": f"{span['size']:.3f}",
                    "script_class": classify_script(text, float(span["size"])),
                    "bbox_x0_pt": f"{x0:.3f}",
                    "bbox_y0_pt": f"{y0:.3f}",
                    "bbox_x1_pt": f"{x1:.3f}",
                    "bbox_y1_pt": f"{y1:.3f}",
                    "h_ink_px_native300": h_ink,
                    "mask_ink_pixels": int(smask.sum()),
                })
    with (OUT / "pdf_text_span_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(span_rows[0]))
        w.writeheader()
        w.writerows(span_rows)

    cp_rows = []
    suspicious = {"\ufffd", "\u25a1", "\u25af", "\u2610", "\u0000"}
    suspicious_count = 0
    for ch, count in sorted(unique_codepoints.items(), key=lambda kv: ord(kv[0])):
        flag = int(ch in suspicious)
        suspicious_count += flag * count
        cp_rows.append({
            "codepoint": f"U+{ord(ch):04X}",
            "character": ch,
            "unicode_name": unicodedata.name(ch, "UNNAMED"),
            "count": count,
            "suspicious_missing_glyph_marker": flag,
        })
    with (OUT / "codepoint_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(cp_rows[0]))
        w.writeheader()
        w.writerows(cp_rows)

    # Source declarations are recorded mechanically; adjudication belongs only in
    # the post-observation manual ledger.
    source_lines = SOURCE_PATH.read_text(encoding="utf-8").splitlines()
    declarations = []
    for n, line in enumerate(source_lines, 1):
        if "fontsize" in line or "\\small" in line or "scale" in line or "resizebox" in line or "scalebox" in line:
            declarations.append({"source_line": n, "source_text": line.strip()})
    with (OUT / "source_font_declarations.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["source_line", "source_text"])
        w.writeheader()
        w.writerows(declarations)

    # Page-edge clip evidence per semantic object.
    page_w_px = round(page.rect.width * SCALE)
    page_h_px = round(page.rect.height * SCALE)
    clip_rows = []
    for row in object_rows:
        if row["mask_bbox_x0"] == "":
            continue
        # Convert crop-relative mask bbox to page-relative pixels.
        ox = round(FIGURE_CAPTION_RECT_PT.x0 * SCALE)
        oy = round(FIGURE_CAPTION_RECT_PT.y0 * SCALE)
        x0, y0 = int(row["mask_bbox_x0"]) + ox, int(row["mask_bbox_y0"]) + oy
        x1, y1 = int(row["mask_bbox_x1"]) + ox, int(row["mask_bbox_y1"]) + oy
        distances = (x0, y0, page_w_px - x1, page_h_px - y1)
        clip_rows.append({
            "object_id": row["object_id"],
            "left_page_edge_clearance_px": distances[0],
            "top_page_edge_clearance_px": distances[1],
            "right_page_edge_clearance_px": distances[2],
            "bottom_page_edge_clearance_px": distances[3],
            "visible_ink_pixels_on_page_edge": 0 if min(distances) > 0 else row["mask_ink_pixels"],
        })
    with (OUT / "clip_metrics.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(clip_rows[0]))
        w.writeheader()
        w.writerows(clip_rows)

    # Bounding-box and categorical-mask overlays.
    overlay = crop_image.copy()
    draw = ImageDraw.Draw(overlay)
    palette = [(215, 35, 35), (0, 105, 190), (0, 145, 90), (180, 100, 0), (120, 50, 170)]
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for idx, row in enumerate(object_rows):
        if row["mask_bbox_x0"] == "":
            continue
        color = palette[idx % len(palette)]
        box = (int(row["mask_bbox_x0"]), int(row["mask_bbox_y0"]), int(row["mask_bbox_x1"]), int(row["mask_bbox_y1"]))
        draw.rectangle(box, outline=color, width=2)
        draw.rectangle((box[0], max(0, box[1] - 20), box[0] + 45, box[1]), fill=(255, 255, 255))
        draw.text((box[0] + 2, max(0, box[1] - 19)), row["object_id"], fill=color, font=font)
    overlay.save(OUT / "object_bbox_overlay_native300dpi.png")

    mask_rgb = np.full((gray.shape[0], gray.shape[1], 3), 255, dtype=np.uint8)
    for idx, obj in enumerate(OBJECTS):
        color = np.array(palette[idx % len(palette)], dtype=np.uint8)
        mask_rgb[object_masks[obj["id"]]] = color
    Image.fromarray(mask_rgb, mode="RGB").save(OUT / "semantic_object_masks_native300dpi.png")

    # Native-1x crops are direct crops from the unresized native-300dpi figure+caption.
    # Their 8x companions use nearest-neighbor only.
    roi_index_rows = []
    for roi_id, roi_pt, purpose in DECISIVE_ROIS:
        box = pdf_to_crop_px(roi_pt, FIGURE_CAPTION_RECT_PT)
        native = crop_image.crop(box)
        native_path = OUT / f"{roi_id}_native1x.png"
        native.save(native_path)
        nn8 = native.resize((native.width * 8, native.height * 8), resample=Image.Resampling.NEAREST)
        nn8_path = OUT / f"{roi_id}_nearest8x.png"
        nn8.save(nn8_path)
        roi_index_rows.append({
            "roi_id": roi_id,
            "purpose": purpose,
            "source_rect_pt": ",".join(f"{v:.2f}" for v in roi_pt),
            "native_width_px": native.width,
            "native_height_px": native.height,
            "scale_variant": "native1x; nearest8x",
        })
    with (OUT / "decisive_roi_index.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(roi_index_rows[0]))
        w.writeheader()
        w.writerows(roi_index_rows)

    metrics = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "physical_page_1based": PAGE_INDEX + 1,
        "native_render_dpi": 300,
        "full_page_dimensions_px": [full_pix.width, full_pix.height],
        "figure_caption_dimensions_px": [crop_pix.width, crop_pix.height],
        "object_count": len(OBJECTS),
        "unordered_pair_count": len(pair_rows),
        "expected_unordered_pair_count": expected_pairs,
        "machine_candidate_pair_count": candidate_count,
        "sum_pair_visible_ink_overlap_px": overlap_total,
        "suspicious_codepoint_occurrences": suspicious_count,
        "page_edge_clip_pixel_count": sum(int(r["visible_ink_pixels_on_page_edge"]) for r in clip_rows),
        "text_span_count": len(span_rows),
        "source_declaration_count": len(declarations),
        "roi_count": len(DECISIVE_ROIS),
    }
    (OUT / "machine_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Record script identity after all generation logic is fixed.
    (OUT / "machine_script_identity.json").write_text(
        json.dumps({"path": str(Path(__file__)), "sha256": sha256(Path(__file__))}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
