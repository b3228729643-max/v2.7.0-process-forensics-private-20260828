from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import sys
import unicodedata
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa3_r111_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_simplex_geometry.tex")
PAGE_NUMBER = 709
PAGE_INDEX = PAGE_NUMBER - 1

EXPECTED = {
    PDF: (4_967_076, "DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6"),
    SOURCE: (3_445, "B1EBE40A22D8A39C983C1BD70F208907B413F611EE0D40601AE44B6F4B66A224"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def bbox_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def crop_pdf(img: Image.Image, box: tuple[float, float, float, float], sx: float, sy: float) -> Image.Image:
    px = (
        max(0, int(math.floor(box[0] * sx))),
        max(0, int(math.floor(box[1] * sy))),
        min(img.width, int(math.ceil(box[2] * sx))),
        min(img.height, int(math.ceil(box[3] * sy))),
    )
    return img.crop(px)


def mask_bbox(shape: tuple[int, int], box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[int, int, int, int]:
    h, w = shape
    return (
        max(0, int(math.floor(box[0] * sx))),
        max(0, int(math.floor(box[1] * sy))),
        min(w, int(math.ceil(box[2] * sx))),
        min(h, int(math.ceil(box[3] * sy))),
    )


def color_mask(rgb: np.ndarray, box: tuple[float, float, float, float], sx: float, sy: float,
               colors: list[tuple[int, int, int]], tolerance: float) -> np.ndarray:
    h, w, _ = rgb.shape
    out = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = mask_bbox((h, w), box, sx, sy)
    roi = rgb[y0:y1, x0:x1].astype(np.float32)
    hit = np.zeros(roi.shape[:2], dtype=bool)
    for c in colors:
        dist = np.sqrt(np.sum((roi - np.array(c, dtype=np.float32)) ** 2, axis=2))
        hit |= dist <= tolerance
    out[y0:y1, x0:x1] = hit
    return out


def text_ink_mask(rgb: np.ndarray, box: tuple[float, float, float, float], sx: float, sy: float) -> tuple[np.ndarray, dict]:
    h, w, _ = rgb.shape
    out = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = mask_bbox((h, w), box, sx, sy)
    roi = rgb[y0:y1, x0:x1].astype(np.float32)
    bg = np.median(roi.reshape(-1, 3), axis=0)
    dist = np.sqrt(np.sum((roi - bg) ** 2, axis=2))
    gray = cv2.cvtColor(roi.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    ink = (dist >= 20.0) & (gray <= 215)
    # Remove isolated one-pixel noise while preserving antialiased glyph strokes.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
    clean = np.zeros_like(ink)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 2:
            clean[labels == i] = True
    out[y0:y1, x0:x1] = clean
    ys, xs = np.where(clean)
    if len(xs):
        h_ink = int(ys.max() - ys.min() + 1)
        w_ink = int(xs.max() - xs.min() + 1)
        ink_bbox = (int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1))
        pixel_count = int(clean.sum())
    else:
        h_ink = w_ink = pixel_count = 0
        ink_bbox = (x0, y0, x0, y0)
    return out, {
        "sample_bbox_px": f"{x0},{y0},{x1},{y1}",
        "ink_bbox_px": ",".join(map(str, ink_bbox)),
        "h_ink_px": h_ink,
        "w_ink_px": w_ink,
        "ink_pixel_count": pixel_count,
        "background_rgb": ",".join(str(int(round(v))) for v in bg),
    }


def extract_text(page: fitz.Page, box: tuple[float, float, float, float]) -> str:
    rect = fitz.Rect(box)
    spans: list[str] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                sb = fitz.Rect(span["bbox"])
                if rect.intersects(sb) and rect.contains(sb.tl + (sb.br - sb.tl) * 0.5):
                    spans.append(span["text"])
    return "".join(spans).strip()


def save_binary_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def straight_drawing_mask(page: fitz.Page, drawing_indices: list[int], shape: tuple[int, int], sx: float, sy: float) -> np.ndarray:
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    drawings = page.get_drawings()
    for idx in drawing_indices:
        d = drawings[idx]
        width = max(1, int(round(float(d["width"] or 0.5) * (sx + sy) / 2)))
        for item in d["items"]:
            if item[0] == "l":
                a, b = item[1], item[2]
                draw.line((a.x * sx, a.y * sy, b.x * sx, b.y * sy), fill=255, width=width)
    return np.asarray(canvas) > 0


def rounded_frame_mask(shape: tuple[int, int], box: tuple[float, float, float, float], sx: float, sy: float,
                       width_pt: float = 0.79701, radius_pt: float = 2.0) -> np.ndarray:
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = mask_bbox(shape, box, sx, sy)
    draw.rounded_rectangle(
        (x0, y0, x1 - 1, y1 - 1),
        radius=max(1, int(round(radius_pt * (sx + sy) / 2))),
        outline=255,
        width=max(1, int(round(width_pt * (sx + sy) / 2))),
    )
    return np.asarray(canvas) > 0


def object_roi(base: Image.Image, mask: np.ndarray, box: tuple[float, float, float, float], sx: float, sy: float,
               tint: tuple[int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = mask_bbox(mask.shape, box, sx, sy)
    pad = 14
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(base.width, x1 + pad), min(base.height, y1 + pad)
    arr = np.asarray(base.crop((x0, y0, x1, y1))).copy()
    sub = mask[y0:y1, x0:x1]
    overlay = np.zeros_like(arr)
    overlay[:] = tint
    arr[sub] = (0.35 * arr[sub] + 0.65 * overlay[sub]).astype(np.uint8)
    return Image.fromarray(arr)


def fit_into(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    out = Image.new("RGB", size, "white")
    cp = img.copy()
    cp.thumbnail(size, Image.Resampling.LANCZOS)
    out.paste(cp, ((size[0] - cp.width) // 2, (size[1] - cp.height) // 2))
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    for d in ("renders", "rois", "overlays", "masks", "tables"):
        if not (ROOT / d).is_dir():
            raise RuntimeError(f"precreated evidence directory missing: {d}")

    identity_rows = []
    for path, (expected_size, expected_hash) in EXPECTED.items():
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if actual_size != expected_size or actual_hash != expected_hash:
            raise RuntimeError(f"identity mismatch: {path}")
        identity_rows.append({
            "input_path": str(path),
            "bytes": actual_size,
            "sha256": actual_hash,
        })
    write_csv(ROOT / "tables" / "input_identity_machine.csv", ["input_path", "bytes", "sha256"], identity_rows)

    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    write_csv(
        ROOT / "tables" / "source_line_map_machine.csv",
        ["source_line", "source_text"],
        [{"source_line": i, "source_text": line} for i, line in enumerate(source_lines, 1)],
    )

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    page_text = page.get_text("text")
    caption_hit = "三类别概率向量位于二维单纯形上" in page_text and "Dirichlet" in page_text
    search_record = {
        "official_pdf": str(PDF),
        "physical_page": PAGE_NUMBER,
        "printed_page": 696,
        "figure_number": "34.4",
        "caption_phrase_found": caption_hit,
        "page_width_pt": page.rect.width,
        "page_height_pt": page.rect.height,
    }
    (ROOT / "tables" / "location_machine.json").write_text(
        json.dumps(search_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    native_path = ROOT / "renders" / "full_page_709_native300dpi.png"
    base = Image.open(native_path).convert("RGB")
    sx = base.width / page.rect.width
    sy = base.height / page.rect.height
    rgb = np.asarray(base)

    crops = {
        "local_figure_native300dpi.png": (55, 60, 530, 302),
        "local_figure_with_caption_native300dpi.png": (55, 60, 530, 338),
        "page_integration_top_native300dpi.png": (50, 28, 535, 430),
    }
    for name, box in crops.items():
        crop_pdf(base, box, sx, sy).save(ROOT / "renders" / name)
    Image.fromarray(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)).save(ROOT / "renders" / "full_page_709_grayscale_native300dpi.png")
    crop_pdf(Image.open(ROOT / "renders" / "full_page_709_grayscale_native300dpi.png"), (55, 60, 530, 338), sx, sy).save(
        ROOT / "renders" / "local_figure_with_caption_grayscale_native300dpi.png"
    )

    critical = {
        "simplex": (55, 60, 325, 305),
        "center_construction": (105, 125, 325, 295),
        "top_vertex_label": (145, 60, 235, 105),
        "bottom_vertex_labels": (55, 270, 325, 305),
        "cards": (345, 120, 530, 302),
        "caption": (55, 302, 530, 338),
    }
    for name, box in critical.items():
        one = crop_pdf(base, box, sx, sy)
        one.save(ROOT / "rois" / f"{name}_native1x.png")
        one.resize((one.width * 8, one.height * 8), Image.Resampling.NEAREST).save(
            ROOT / "rois" / f"{name}_nearest8x.png"
        )

    text_elements = [
        ("E01", "component_label", (236.0, 150.5, 265.2, 163.2), "θ₁=.2", "math_mixed", 8.7),
        ("E02", "component_label", (117.0, 150.5, 146.2, 163.2), "θ₂=.3", "math_mixed", 8.7),
        ("E03", "component_label", (207.5, 279.8, 236.8, 292.5), "θ₃=.5", "math_mixed", 8.7),
        ("E04", "point_vector", (247.2, 177.8, 316.0, 190.0), "θ=(0.2,0.3,0.5)", "math_mixed", 9.5),
        ("E05", "vertex_formula", (65.0, 278.8, 116.2, 290.75), "e₁=(1,0,0)", "math_mixed", 9.5),
        ("E06", "vertex_class", (65.8, 290.75, 115.2, 302.0), "类别1确定", "cjk_mixed", 9.5),
        ("E07", "vertex_formula", (263.4, 278.8, 314.6, 290.75), "e₂=(0,1,0)", "math_mixed", 9.5),
        ("E08", "vertex_class", (264.3, 290.75, 313.7, 302.0), "类别2确定", "cjk_mixed", 9.5),
        ("E09", "vertex_formula", (164.2, 70.4, 215.4, 82.30), "e₃=(0,0,1)", "math_mixed", 9.5),
        ("E10", "vertex_class", (165.1, 82.30, 214.5, 93.60), "类别3确定", "cjk_mixed", 9.5),
        ("E11", "definition_formula", (363.0, 130.2, 502.0, 147.60), "Δ²={θ∈ℝ³:θᵢ≥0,∑ᵢθᵢ=1}", "math_mixed", 9.5),
        ("E12", "dimension_formula", (363.0, 147.60, 414.5, 159.0), "dim(Δ²)=2", "math_mixed", 9.5),
        ("E13", "state_line", (363.0, 193.0, 469.5, 204.4), "内部：三个分量均为正；", "cjk", 9.5),
        ("E14", "state_line", (363.0, 204.7, 450.5, 215.9), "边：一个分量为零；", "cjk", 9.5),
        ("E15", "state_line", (363.0, 215.9, 476.3, 227.3), "顶点：一个类别概率为1。", "cjk_mixed", 9.5),
        ("E16", "conclusion_line", (363.0, 256.8, 509.5, 268.3), "三元概率向量有三个坐标，却只具", "cjk", 9.5),
        ("E17", "conclusion_line", (363.0, 268.3, 509.5, 279.7), "有两个自由度；三角形中的位置就", "cjk", 9.5),
        ("E18", "conclusion_line", (363.0, 279.7, 422.0, 291.1), "是重心坐标。", "cjk", 9.5),
        ("E19", "caption_line", (61.3, 305.0, 523.0, 321.5), "图34.4 三类别概率向量位于二维单纯形上，三个顶点分别代表一个类别概率为1；内部点的重心坐标就", "cjk_mixed", 10.0),
        ("E20", "caption_line", (61.3, 321.9, 405.0, 335.0), "是三个类别概率，因此Dirichlet分布虽写在三维坐标中，实际支撑集只有二维", "cjk_mixed", 10.0),
    ]

    element_masks: dict[str, np.ndarray] = {}
    measurement_rows = []
    glyph_rows = []
    for eid, role, box, expected_text, script_class, declared_pt in text_elements:
        mask, metrics = text_ink_mask(rgb, box, sx, sy)
        element_masks[eid] = mask
        extracted = extract_text(page, box)
        measurement_rows.append({
            "element_id": eid,
            "role": role,
            "bbox_pdf_pt": ",".join(f"{v:.2f}" for v in box),
            "declared_pt": f"{declared_pt:.2f}",
            "graphics_scale": "1.0000",
            "effective_pt": f"{declared_pt:.2f}",
            "script_class": script_class,
            "expected_text": expected_text,
            "extracted_text": extracted,
            **metrics,
        })
        norm_expected = unicodedata.normalize("NFKC", expected_text).replace(" ", "")
        norm_extracted = unicodedata.normalize("NFKC", extracted).replace(" ", "")
        glyph_rows.append({
            "element_id": eid,
            "expected_text": expected_text,
            "extracted_text": extracted,
            "expected_codepoints": " ".join(f"U+{ord(ch):04X}" for ch in expected_text),
            "extracted_codepoints": " ".join(f"U+{ord(ch):04X}" for ch in extracted),
            "nfkc_no_space_equal": int(norm_expected == norm_extracted),
        })
        save_binary_mask(ROOT / "masks" / f"text_{eid}.png", mask)

    write_csv(
        ROOT / "tables" / "text_measurements_machine.csv",
        list(measurement_rows[0].keys()), measurement_rows,
    )
    write_csv(
        ROOT / "tables" / "glyph_codepoints_machine.csv",
        list(glyph_rows[0].keys()), glyph_rows,
    )

    object_defs = [
        ("O01", "simplex_geometry", (88, 97, 292, 274), []),
        ("O02", "component_construction", (153, 157, 232, 274), []),
        ("O03", "theta1_label", (236, 150, 266, 164), ["E01"]),
        ("O04", "theta2_label", (116, 150, 147, 164), ["E02"]),
        ("O05", "theta3_label", (207, 279, 237, 293), ["E03"]),
        ("O06", "point_vector_label", (247, 177, 317, 191), ["E04"]),
        ("O07", "vertex1_label_block", (64, 278, 117, 303), ["E05", "E06"]),
        ("O08", "vertex2_label_block", (263, 278, 315, 303), ["E07", "E08"]),
        ("O09", "vertex3_label_block", (164, 70, 216, 94), ["E09", "E10"]),
        ("O10", "definition_card_frame", (353, 127, 523, 164), []),
        ("O11", "definition_card_text", (362, 130, 503, 160), ["E11", "E12"]),
        ("O12", "state_card_frame", (353, 186, 523, 233), []),
        ("O13", "state_card_text", (362, 192, 477, 229), ["E13", "E14", "E15"]),
        ("O14", "conclusion_card_frame", (353, 249, 523, 297), []),
        ("O15", "conclusion_card_text", (362, 256, 510, 293), ["E16", "E17", "E18"]),
        ("O16", "figure_caption", (61, 304, 524, 336), ["E19", "E20"]),
    ]

    object_masks: dict[str, np.ndarray] = {}
    object_boxes: dict[str, tuple[float, float, float, float]] = {}
    object_roles: dict[str, str] = {}
    for oid, role, box, eids in object_defs:
        if eids:
            m = np.zeros(rgb.shape[:2], dtype=bool)
            for eid in eids:
                m |= element_masks[eid]
        elif oid == "O01":
            m = straight_drawing_mask(page, list(range(1, 14)), rgb.shape[:2], sx, sy)
        elif oid == "O02":
            m = color_mask(rgb, box, sx, sy, [(15, 118, 110), (31, 78, 121)], 20)
        elif oid in ("O10", "O12"):
            m = rounded_frame_mask(rgb.shape[:2], box, sx, sy)
        elif oid == "O14":
            m = rounded_frame_mask(rgb.shape[:2], box, sx, sy)
        else:
            raise AssertionError(oid)
        object_masks[oid] = m
        object_boxes[oid] = box
        object_roles[oid] = role
        save_binary_mask(ROOT / "masks" / f"object_{oid}.png", m)

    inventory_rows = []
    for oid, role, box, eids in object_defs:
        inventory_rows.append({
            "object_id": oid,
            "machine_role": role,
            "bbox_pdf_pt": ",".join(str(v) for v in box),
            "member_element_ids": "|".join(eids),
            "foreground_pixel_count": int(object_masks[oid].sum()),
        })
    write_csv(
        ROOT / "tables" / "visible_object_inventory_machine.csv",
        list(inventory_rows[0].keys()), inventory_rows,
    )

    # Object and text measurement overlays.
    overlay = base.copy()
    odraw = ImageDraw.Draw(overlay)
    colors = [(220, 20, 60), (0, 120, 255), (255, 140, 0), (120, 50, 180)]
    font = ImageFont.load_default()
    for i, (oid, _, box, _) in enumerate(object_defs):
        x0, y0, x1, y1 = mask_bbox(rgb.shape[:2], box, sx, sy)
        c = colors[i % len(colors)]
        odraw.rectangle((x0, y0, x1, y1), outline=c, width=4)
        odraw.rectangle((x0, max(0, y0 - 16), x0 + 42, y0), fill="white")
        odraw.text((x0 + 2, max(0, y0 - 14)), oid, fill=c, font=font)
    crop_pdf(overlay, (55, 60, 530, 338), sx, sy).save(ROOT / "overlays" / "visible_object_overlay_native300dpi.png")

    toverlay = base.copy()
    tdraw = ImageDraw.Draw(toverlay)
    for i, (eid, _, box, _, _, _) in enumerate(text_elements):
        x0, y0, x1, y1 = mask_bbox(rgb.shape[:2], box, sx, sy)
        c = colors[i % len(colors)]
        tdraw.rectangle((x0, y0, x1, y1), outline=c, width=3)
        tdraw.text((x0 + 1, max(0, y0 - 12)), eid, fill=c, font=font)
    crop_pdf(toverlay, (55, 60, 530, 338), sx, sy).save(ROOT / "overlays" / "text_measurement_overlay_native300dpi.png")

    # Pairwise raster metrics for all 16 choose 2 = 120 unordered pairs.
    pairs = []
    pair_ids = []
    kernel1 = np.ones((3, 3), dtype=np.uint8)
    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    for seq, (a, b) in enumerate(itertools.combinations([o[0] for o in object_defs], 2), 1):
        ma, mb = object_masks[a], object_masks[b]
        exact = int(np.logical_and(ma, mb).sum())
        if exact:
            center_dist = 0.0
            edge_gap = 0.0
        else:
            dt = cv2.distanceTransform((~ma).astype(np.uint8), cv2.DIST_L2, 5)
            center_dist = float(dt[mb].min()) if mb.any() else float("nan")
            edge_gap = max(0.0, center_dist - 1.0)
        dil1a = cv2.dilate(ma.astype(np.uint8), kernel1, iterations=1).astype(bool)
        dil1b = cv2.dilate(mb.astype(np.uint8), kernel1, iterations=1).astype(bool)
        dil3a = cv2.dilate(ma.astype(np.uint8), kernel3, iterations=1).astype(bool)
        dil3b = cv2.dilate(mb.astype(np.uint8), kernel3, iterations=1).astype(bool)
        candidate1 = int(np.logical_and(dil1a, dil1b).sum())
        candidate3 = int(np.logical_and(dil3a, dil3b).sum())
        pid = f"P{seq:03d}"
        pair_ids.append((pid, a, b))
        pairs.append({
            "pair_id": pid,
            "object_a": a,
            "role_a": object_roles[a],
            "object_b": b,
            "role_b": object_roles[b],
            "bbox_gap_pt": f"{bbox_gap(object_boxes[a], object_boxes[b]):.3f}",
            "exact_shared_raster_px": exact,
            "minimum_foreground_edge_gap_px": f"{edge_gap:.3f}",
            "dilated_1px_candidate_px": candidate1,
            "dilated_3px_candidate_px": candidate3,
        })
    if len(pairs) != 120:
        raise AssertionError(len(pairs))
    write_csv(ROOT / "tables" / "all_unordered_pair_metrics_machine.csv", list(pairs[0].keys()), pairs)

    # Pair matrix visual.
    cell = 68
    labels = [o[0] for o in object_defs]
    matrix = Image.new("RGB", ((len(labels) + 1) * cell, (len(labels) + 1) * cell), "white")
    md = ImageDraw.Draw(matrix)
    for i, lab in enumerate(labels):
        md.text(((i + 1) * cell + 14, 24), lab, fill="black", font=font)
        md.text((14, (i + 1) * cell + 24), lab, fill="black", font=font)
    pair_lookup = {(r["object_a"], r["object_b"]): r for r in pairs}
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            x0, y0 = (j + 1) * cell, (i + 1) * cell
            if i == j:
                fill = (210, 210, 210)
                txt = "self"
            else:
                key = (a, b) if i < j else (b, a)
                rec = pair_lookup[key]
                c3 = int(rec["dilated_3px_candidate_px"])
                exact = int(rec["exact_shared_raster_px"])
                if exact:
                    fill = (255, 150, 150)
                elif c3:
                    fill = (255, 226, 150)
                else:
                    fill = (185, 235, 200)
                txt = str(c3)
            md.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=fill, outline=(100, 100, 100))
            md.text((x0 + 6, y0 + 24), txt, fill="black", font=font)
    matrix.save(ROOT / "overlays" / "all_pair_matrix_machine.png")

    # Pair evidence montages: 15 explicit pair tiles per sheet.
    local_box = (55, 60, 530, 338)
    local = crop_pdf(base, local_box, sx, sy)
    lx0, ly0, _, _ = mask_bbox(rgb.shape[:2], local_box, sx, sy)
    for sheet_index in range(8):
        sheet = Image.new("RGB", (2160, 1500), (245, 245, 245))
        sd = ImageDraw.Draw(sheet)
        for slot in range(15):
            idx = sheet_index * 15 + slot
            rec = pairs[idx]
            pid, a, b = rec["pair_id"], rec["object_a"], rec["object_b"]
            col, row = slot % 3, slot // 3
            tx, ty = col * 720, row * 300
            tile = Image.new("RGB", (716, 296), "white")
            td = ImageDraw.Draw(tile)
            td.text((8, 6), f"{pid}  {a}-{b}", fill="black", font=font)
            td.text((8, 22), f"edge_gap_px={rec['minimum_foreground_edge_gap_px']} exact={rec['exact_shared_raster_px']} d3={rec['dilated_3px_candidate_px']}", fill="black", font=font)

            overview = local.copy()
            oa = object_masks[a][ly0:ly0 + local.height, lx0:lx0 + local.width]
            ob = object_masks[b][ly0:ly0 + local.height, lx0:lx0 + local.width]
            arr = np.asarray(overview).copy()
            arr[oa] = (0.35 * arr[oa] + 0.65 * np.array((255, 40, 40))).astype(np.uint8)
            arr[ob] = (0.35 * arr[ob] + 0.65 * np.array((20, 80, 255))).astype(np.uint8)
            tile.paste(fit_into(Image.fromarray(arr), (340, 240)), (4, 48))
            aroi = object_roi(base, object_masks[a], object_boxes[a], sx, sy, (255, 40, 40))
            broi = object_roi(base, object_masks[b], object_boxes[b], sx, sy, (20, 80, 255))
            tile.paste(fit_into(aroi, (180, 215)), (350, 65))
            tile.paste(fit_into(broi, (180, 215)), (532, 65))
            td.text((405, 48), a, fill=(220, 20, 20), font=font)
            td.text((590, 48), b, fill=(20, 60, 220), font=font)
            sheet.paste(tile, (tx + 2, ty + 2))
        sheet.save(ROOT / "overlays" / f"all_pair_montage_{sheet_index + 1:02d}.png")

    # Source-coordinate mathematics recomputation.
    e1 = np.array([0.0, 0.0])
    e2 = np.array([7.0, 0.0])
    e3 = np.array([3.5, 6.062])
    th = np.array([3.85, 3.031])
    mat = np.column_stack((e1 - e3, e2 - e3))
    l1, l2 = np.linalg.solve(mat, th - e3)
    l3 = 1.0 - l1 - l2

    def projection(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        v = b - a
        return a + v * np.dot(p - a, v) / np.dot(v, v)

    q1 = projection(th, e2, e3)
    q2 = projection(th, e1, e3)
    q3 = projection(th, e1, e2)
    altitude = 6.062
    dist_to_sides = [np.linalg.norm(th - q1), np.linalg.norm(th - q2), np.linalg.norm(th - q3)]
    math_record = {
        "source_coordinates": {"e1": e1.tolist(), "e2": e2.tolist(), "e3": e3.tolist(), "theta_point": th.tolist()},
        "barycentric_weights": [float(l1), float(l2), float(l3)],
        "weight_sum": float(l1 + l2 + l3),
        "nonnegative": bool(min(l1, l2, l3) >= -1e-12),
        "side_projections": {"q1_on_e2e3": q1.tolist(), "q2_on_e1e3": q2.tolist(), "q3_on_e1e2": q3.tolist()},
        "perpendicular_distances": [float(v) for v in dist_to_sides],
        "normalized_distances_by_altitude": [float(v / altitude) for v in dist_to_sides],
        "simplex_dimension": 2,
        "ambient_dimension": 3,
        "affine_constraint_rank": 1,
    }
    (ROOT / "tables" / "simplex_math_recomputation_machine.json").write_text(
        json.dumps(math_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    vector_rows = []
    for i, d in enumerate(page.get_drawings()):
        if d["rect"].y0 < 305 and d["rect"].y1 > 50:
            vector_rows.append({
                "drawing_index": i,
                "bbox_pdf_pt": ",".join(f"{v:.3f}" for v in (d["rect"].x0, d["rect"].y0, d["rect"].x1, d["rect"].y1)),
                "paint_type": d["type"],
                "stroke_rgb01": "" if d["color"] is None else ",".join(f"{v:.5f}" for v in d["color"]),
                "fill_rgb01": "" if d["fill"] is None else ",".join(f"{v:.5f}" for v in d["fill"]),
                "stroke_width_pt": "" if d["width"] is None else f"{d['width']:.5f}",
                "path_item_count": len(d["items"]),
            })
    write_csv(ROOT / "tables" / "vector_drawings_machine.csv", list(vector_rows[0].keys()), vector_rows)

    print(json.dumps({
        "status": "machine_evidence_generated",
        "physical_page": PAGE_NUMBER,
        "render_px": [base.width, base.height],
        "scale_px_per_pt": [sx, sy],
        "text_elements": len(text_elements),
        "visible_objects": len(object_defs),
        "unordered_pairs": len(pairs),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
