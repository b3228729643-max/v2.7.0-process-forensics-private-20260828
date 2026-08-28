from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa1_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex")
PHYSICAL_PAGE = 690
PRINTED_PAGE = 677
SCALE = 300.0 / 72.0


def px(v: float) -> int:
    return int(round(v * SCALE))


def crop_pt(image: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    return image.crop(tuple(px(v) for v in box))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def classify_char(ch: str) -> str:
    if not ch.strip():
        return "SPACE"
    cp = ord(ch[0])
    if 0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF:
        return "CJK_FULL"
    if ch.isdigit() or (ch.isalpha() and ch.upper() == ch and ch.lower() != ch):
        return "LATIN_UPPER_OR_DIGIT"
    if ch.isalpha():
        return "LATIN_OR_GREEK_LOWER"
    return "MATH_OR_SYMBOL"


def bbox_gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float]:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return dx, dy, math.hypot(dx, dy)


def bbox_intersection(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


def main() -> None:
    doc = fitz.open(PDF)
    page = doc[PHYSICAL_PAGE - 1]
    page_img = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    gray = np.asarray(page_img.convert("L"))

    figure_box_pt = (80.0, 65.0, 530.0, 295.0)
    standalone_box_pt = (88.0, 65.0, 522.0, 260.0)
    critical_box_pt = (365.0, 65.0, 520.0, 220.0)
    figure = crop_pt(page_img, figure_box_pt)
    standalone = crop_pt(page_img, standalone_box_pt)
    critical = crop_pt(page_img, critical_box_pt)
    figure.save(ROOT / "figure_crop_300dpi.png", dpi=(300, 300))
    standalone.save(ROOT / "standalone_equivalent_300dpi.png", dpi=(300, 300))
    standalone.convert("L").save(ROOT / "grayscale_300dpi.png", dpi=(300, 300))
    critical.save(ROOT / "critical_right_panel_1x_native_300dpi.png", dpi=(300, 300))
    critical.resize((critical.width * 8, critical.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "critical_right_panel_8x_nearest.png"
    )
    for stem, box in [
        ("critical_limit_note", (444.0, 108.0, 505.0, 145.0)),
        ("critical_point_label", (450.0, 164.0, 511.0, 190.0)),
        ("critical_panel_title_fraction", (412.0, 67.0, 505.0, 104.0)),
    ]:
        local = crop_pt(page_img, box)
        local.save(ROOT / f"{stem}_1x_native_300dpi.png", dpi=(300, 300))
        local.resize((local.width * 8, local.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{stem}_8x_nearest.png"
        )

    # Logical reader-visible text elements. Bboxes are recovered from the authorized
    # R104 PDF text spans, in PDF points. No PASS/FAIL is generated here.
    elements = [
        ("TXT_A_TITLE", "A", "PANEL_TITLE", "(a) 轮末 ACF：ρ^{2k}", 19, 9.6, (199.34, 71.78, 275.81, 82.92)),
        ("TXT_A_XTICK_0", "A", "TICK", "0", 17, 9.6, (135.92, 211.63, 140.66, 221.20)),
        ("TXT_A_XTICK_2", "A", "TICK", "2", 17, 9.6, (169.08, 211.65, 173.82, 221.22)),
        ("TXT_A_XTICK_4", "A", "TICK", "4", 17, 9.6, (202.24, 211.66, 206.98, 221.23)),
        ("TXT_A_XTICK_6", "A", "TICK", "6", 17, 9.6, (235.40, 211.67, 240.14, 221.24)),
        ("TXT_A_XTICK_8", "A", "TICK", "8", 17, 9.6, (268.55, 211.68, 273.29, 221.25)),
        ("TXT_A_XTICK_10", "A", "TICK", "10", 17, 9.6, (299.34, 211.63, 308.82, 221.20)),
        ("TXT_A_XTICK_12", "A", "TICK", "12", 17, 9.6, (332.50, 211.65, 341.98, 221.22)),
        ("TXT_A_YTICK_0", "A", "TICK", "0", 18, 9.6, (129.72, 204.68, 134.46, 214.25)),
        ("TXT_A_YTICK_025", "A", "TICK", "0.25", 18, 9.6, (117.91, 176.88, 134.46, 186.45)),
        ("TXT_A_YTICK_05", "A", "TICK", "0.5", 18, 9.6, (122.64, 149.08, 134.46, 158.64)),
        ("TXT_A_YTICK_075", "A", "TICK", "0.75", 18, 9.6, (117.91, 121.28, 134.46, 130.85)),
        ("TXT_A_YTICK_1", "A", "TICK", "1", 18, 9.6, (129.72, 93.53, 134.46, 103.10)),
        ("TXT_A_XLABEL", "A", "AXIS_LABEL", "滞后 k", 20, 9.8, (224.23, 227.34, 251.26, 237.80)),
        ("TXT_A_YLABEL", "A", "AXIS_LABEL", "Corr(X₂^(t),X₂^(t+k))=ρ^(2k)", 21, 9.8, (97.77, 102.28, 112.77, 199.27)),
        ("TXT_A_LEGEND_095", "A", "LEGEND", "|ρ|=.95", 28, 9.6, (164.30, 245.26, 200.09, 255.23)),
        ("TXT_A_LEGEND_070", "A", "LEGEND", "|ρ|=.70", 30, 9.6, (228.90, 245.26, 264.68, 255.23)),
        ("TXT_A_LEGEND_020", "A", "LEGEND", "|ρ|=.20", 32, 9.6, (293.44, 245.26, 329.23, 255.23)),
        ("TXT_B_TITLE", "B", "PANEL_TITLE", "(b) 渐近 ESS 比例：(1-ρ²)/(1+ρ²)", 37, 9.6, (417.58, 72.43, 499.34, 100.38)),
        ("TXT_B_XTICK_0", "B", "TICK", "0", 39, 9.6, (406.67, 189.21, 411.41, 198.78)),
        ("TXT_B_XTICK_05", "B", "TICK", ".5", 39, 9.6, (453.00, 189.09, 460.09, 198.66)),
        ("TXT_B_XTICK_099", "B", "TICK", ".99", 39, 9.6, (497.19, 189.24, 509.01, 198.82)),
        ("TXT_B_YTICK_0", "B", "TICK", "0", 39, 9.6, (398.34, 180.12, 403.08, 189.69)),
        ("TXT_B_YTICK_05", "B", "TICK", "0.5", 39, 9.6, (391.26, 143.00, 403.08, 152.57)),
        ("TXT_B_YTICK_1", "B", "TICK", "1", 39, 9.6, (398.34, 105.94, 403.08, 115.51)),
        ("TXT_B_XLABEL", "B", "AXIS_LABEL", "|ρ|", 38, 9.8, (450.79, 203.58, 461.35, 213.35)),
        ("TXT_B_YLABEL", "B", "AXIS_LABEL", "N_eff/N", 38, 9.8, (374.23, 134.86, 385.36, 160.34)),
        ("TXT_B_LIMIT_NOTE", "B", "ANNOTATION", "|ρ|→1⁻: N_eff/N→0", 48, 9.6, (452.69, 115.18, 497.39, 138.79)),
        ("TXT_B_POINT_LABEL", "B", "ANNOTATION", "(.99,.010)", 46, 9.6, (459.19, 171.29, 499.91, 180.87)),
        ("TXT_CAPTION", "CAPTION", "CAPTION", "图33.7 二元正态系统Gibbs…统计效率仍会显著下降", 52, 10.0, (87.47, 262.17, 519.15, 289.83)),
    ]

    element_rows: list[dict] = []
    for element_id, panel, role, text, line_no, declared_pt, bbox in elements:
        x0, y0, x1, y1 = (px(v) for v in bbox)
        region = gray[max(0, y0):min(gray.shape[0], y1 + 1), max(0, x0):min(gray.shape[1], x1 + 1)]
        fg = region <= 235
        ys, xs = np.where(fg)
        ink_h = int(ys.max() - ys.min() + 1) if ys.size else 0
        ink_w = int(xs.max() - xs.min() + 1) if xs.size else 0
        element_rows.append({
            "element_id": element_id,
            "panel_id": panel,
            "role": role,
            "source_file": str(SOURCE),
            "source_line": line_no,
            "declared_pt": declared_pt,
            "graphics_scale": 1.0,
            "effective_pt_from_source": declared_pt,
            "text_sample": text,
            "bbox_x0_pt": bbox[0], "bbox_y0_pt": bbox[1], "bbox_x1_pt": bbox[2], "bbox_y1_pt": bbox[3],
            "bbox_x0_px": x0, "bbox_y0_px": y0, "bbox_x1_px": x1, "bbox_y1_px": y1,
            "ink_bbox_height_px": ink_h,
            "ink_bbox_width_px": ink_w,
        })
    write_csv(ROOT / "machine_logical_element_inventory.csv", list(element_rows[0].keys()), element_rows)

    # Every extracted glyph/character in the logical figure region, with actual native
    # 300 dpi ink extent measured at contrast >=20/255. Spaces remain inventoried.
    raw = page.get_text("rawdict")
    glyph_rows: list[dict] = []
    gid = 0
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            direction = tuple(line.get("dir", (1.0, 0.0)))
            for span in line.get("spans", []):
                sx0, sy0, sx1, sy1 = span["bbox"]
                if sy1 < 65 or sy0 > 290 or sx1 < 80 or sx0 > 530:
                    continue
                for char in span.get("chars", []):
                    gid += 1
                    ch = char["c"]
                    bx = tuple(float(v) for v in char["bbox"])
                    x0, y0, x1, y1 = (px(v) for v in bx)
                    region = gray[max(0, y0):min(gray.shape[0], y1 + 1), max(0, x0):min(gray.shape[1], x1 + 1)]
                    fg = region <= 235
                    ys, xs = np.where(fg)
                    ink_h = int(ys.max() - ys.min() + 1) if ys.size else 0
                    ink_w = int(xs.max() - xs.min() + 1) if xs.size else 0
                    normal_extent = ink_h if abs(direction[0]) >= abs(direction[1]) else ink_w
                    glyph_rows.append({
                        "glyph_id": f"GLY_{gid:04d}",
                        "char": ch,
                        "unicode_codepoints": "+".join(f"U+{ord(c):04X}" for c in ch),
                        "script_class": classify_char(ch),
                        "font": span["font"],
                        "pdf_font_size_pt": round(float(span["size"]), 6),
                        "recovered_tex_effective_pt": round(float(span["size"]) * 72.27 / 72.0, 6),
                        "line_dir_x": direction[0], "line_dir_y": direction[1],
                        "bbox_x0_pt": bx[0], "bbox_y0_pt": bx[1], "bbox_x1_pt": bx[2], "bbox_y1_pt": bx[3],
                        "bbox_x0_px": x0, "bbox_y0_px": y0, "bbox_x1_px": x1, "bbox_y1_px": y1,
                        "ink_bbox_height_px": ink_h,
                        "ink_bbox_width_px": ink_w,
                        "ink_normal_extent_px": normal_extent,
                        "is_space": str(not ch.strip()).lower(),
                    })
    write_csv(ROOT / "machine_glyph_inventory.csv", list(glyph_rows[0].keys()), glyph_rows)

    # Raw text span inventory retains font names, recovered effective sizes and exact
    # PDF bboxes; it is independent of source declarations.
    span_rows: list[dict] = []
    sid = 0
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bx = tuple(float(v) for v in span["bbox"])
                if bx[3] < 65 or bx[1] > 290 or bx[2] < 80 or bx[0] > 530:
                    continue
                sid += 1
                span_rows.append({
                    "span_id": f"SPAN_{sid:03d}", "text": span["text"], "font": span["font"],
                    "pdf_font_size_pt": round(float(span["size"]), 6),
                    "recovered_tex_effective_pt": round(float(span["size"]) * 72.27 / 72.0, 6),
                    "bbox_x0_pt": bx[0], "bbox_y0_pt": bx[1], "bbox_x1_pt": bx[2], "bbox_y1_pt": bx[3],
                })
    write_csv(ROOT / "machine_pdf_span_inventory.csv", list(span_rows[0].keys()), span_rows)

    # Semantic vector objects recovered directly from the R104 PDF drawing list.
    graphics = [
        ("GFX_A_AXIS_AND_TICKS", "A", "AXIS_LINE", (138.28, 92.20, 337.25, 208.96)),
        ("GFX_A_CURVE_RHO095", "A", "DATA_CURVE", (138.28, 97.76, 337.25, 176.49)),
        ("GFX_A_CURVE_RHO070", "A", "DATA_CURVE", (138.28, 97.76, 337.25, 208.94)),
        ("GFX_A_CURVE_RHO020", "A", "DATA_CURVE", (138.28, 97.76, 337.25, 208.96)),
        ("GFX_A_LEGEND_SWATCH_095", "A", "LEGEND_SWATCH", (144.80, 249.65, 161.82, 250.66)),
        ("GFX_A_LEGEND_SWATCH_070", "A", "LEGEND_SWATCH", (209.47, 249.65, 226.49, 250.66)),
        ("GFX_A_LEGEND_SWATCH_020", "A", "LEGEND_SWATCH", (274.04, 249.65, 291.06, 250.66)),
        ("GFX_B_AXIS_AND_TICKS", "B", "AXIS_LINE", (406.90, 105.90, 503.12, 198.85)),
        ("GFX_B_CURVE", "B", "DATA_CURVE", (409.03, 110.16, 503.11, 183.66)),
        ("GFX_B_POINT_MARKER", "B", "MARKER", (501.30, 181.84, 504.91, 185.45)),
    ]
    all_objects = [
        {"object_id": r[0], "panel_id": r[1], "object_class": "TEXT", "role": r[2], "bbox": r[6]}
        for r in elements
    ] + [
        {"object_id": r[0], "panel_id": r[1], "object_class": r[2], "role": r[2], "bbox": r[3]}
        for r in graphics
    ]
    object_rows = []
    for obj in all_objects:
        b = obj["bbox"]
        object_rows.append({
            "object_id": obj["object_id"], "panel_id": obj["panel_id"],
            "object_class": obj["object_class"], "role": obj["role"],
            "bbox_x0_pt": b[0], "bbox_y0_pt": b[1], "bbox_x1_pt": b[2], "bbox_y1_pt": b[3],
            "bbox_x0_px": px(b[0]), "bbox_y0_px": px(b[1]), "bbox_x1_px": px(b[2]), "bbox_y1_px": px(b[3]),
        })
    write_csv(ROOT / "machine_actual_object_inventory.csv", list(object_rows[0].keys()), object_rows)

    # Complete unordered pair inventory: n*(n-1)/2 rows, no omitted/defaulted pairs.
    pair_rows: list[dict] = []
    for pair_index, (a, b) in enumerate(itertools.combinations(all_objects, 2), start=1):
        dx, dy, gap = bbox_gap(a["bbox"], b["bbox"])
        inter = bbox_intersection(a["bbox"], b["bbox"])
        classes = {a["object_class"], b["object_class"]}
        critical = (
            ("TEXT" in classes and bool(classes.intersection({"AXIS_LINE", "DATA_CURVE", "MARKER", "LEGEND_SWATCH"})))
            or (a["object_class"] == "TEXT" and b["object_class"] == "TEXT")
        )
        pair_rows.append({
            "pair_id": f"PAIR_{pair_index:04d}",
            "object_a": a["object_id"], "class_a": a["object_class"], "panel_a": a["panel_id"],
            "object_b": b["object_id"], "class_b": b["object_class"], "panel_b": b["panel_id"],
            "bbox_dx_px": round(dx * SCALE, 3), "bbox_dy_px": round(dy * SCALE, 3),
            "bbox_euclidean_gap_px": round(gap * SCALE, 3),
            "bbox_intersection_area_px2": round(inter * SCALE * SCALE, 3),
            "critical_pair": str(critical).lower(),
        })
    write_csv(ROOT / "machine_all_unordered_pairs.csv", list(pair_rows[0].keys()), pair_rows)

    # Full overlay: bboxes + stable IDs. It is deliberately measurement-only.
    overlay = page_img.copy()
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    for row in element_rows:
        box = (row["bbox_x0_px"], row["bbox_y0_px"], row["bbox_x1_px"], row["bbox_y1_px"])
        draw.rectangle(box, outline=(220, 20, 60), width=2)
        draw.text((box[0], max(0, box[1] - 13)), row["element_id"], fill=(180, 0, 40), font=font)
    overlay.crop(tuple(px(v) for v in figure_box_pt)).save(ROOT / "machine_text_measurement_overlay_300dpi.png", dpi=(300, 300))

    # Clip guard bands: six native pixels inside each standalone-equivalent edge.
    clip = standalone.copy()
    cd = ImageDraw.Draw(clip)
    cd.rectangle((6, 6, clip.width - 7, clip.height - 7), outline=(255, 0, 255), width=2)
    clip.save(ROOT / "machine_clip_guard_overlay_300dpi.png", dpi=(300, 300))

    # Separate native-resolution vector masks for the only real foreground
    # intersection candidate: the right-panel positive-x axis arrow and the
    # open data marker at (.99,.010). This is measurement only; classification
    # remains the manual reviewer's responsibility.
    mask_shape = (page_img.height, page_img.width)
    axis_mask = np.zeros(mask_shape, dtype=np.uint8)
    marker_mask = np.zeros(mask_shape, dtype=np.uint8)
    pxy = lambda x, y: (px(x), px(y))
    cv2.line(axis_mask, pxy(409.039978, 184.393021), pxy(500.736084, 184.393021), 255, 3, cv2.LINE_AA)
    arrow = np.array([
        pxy(503.102173, 184.393021), pxy(499.316437, 182.500137),
        pxy(500.736084, 184.393021), pxy(499.316437, 186.285904),
    ], dtype=np.int32)
    cv2.fillPoly(axis_mask, [arrow], 255, cv2.LINE_AA)
    cv2.ellipse(
        marker_mask, pxy(503.104736, 183.647079),
        (round(1.7933 * SCALE), round(1.7933 * SCALE)), 0, 0, 360, 255, 4, cv2.LINE_AA,
    )
    axis_fg = axis_mask > 20
    marker_fg = marker_mask > 20
    overlap_fg = axis_fg & marker_fg
    Image.fromarray((axis_fg * 255).astype(np.uint8)).save(ROOT / "machine_axis_mask_300dpi.png")
    Image.fromarray((marker_fg * 255).astype(np.uint8)).save(ROOT / "machine_marker_mask_300dpi.png")
    Image.fromarray((overlap_fg * 255).astype(np.uint8)).save(ROOT / "machine_axis_marker_overlap_mask_300dpi.png")
    local_box = (2070, 748, 2110, 790)
    native_local = page_img.crop(local_box)
    ov = np.asarray(native_local).copy()
    local_overlap = overlap_fg[local_box[1]:local_box[3], local_box[0]:local_box[2]]
    ov[local_overlap] = (255, 0, 255)
    ov_img = Image.fromarray(ov)
    ov_img.save(ROOT / "machine_axis_marker_overlap_overlay_1x.png")
    ov_img.resize((ov_img.width * 8, ov_img.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "machine_axis_marker_overlap_overlay_8x.png"
    )
    overlap_rows = [{
        "cluster_id": "CAND_001",
        "object_a": "GFX_B_AXIS_AND_TICKS",
        "object_b": "GFX_B_POINT_MARKER",
        "candidate_pixel_count": int(overlap_fg.sum()),
        "native_dpi": 300,
        "mask_threshold": "vector mask antialias >20/255",
        "bbox_x0_px": int(np.where(overlap_fg)[1].min()),
        "bbox_y0_px": int(np.where(overlap_fg)[0].min()),
        "bbox_x1_px": int(np.where(overlap_fg)[1].max()),
        "bbox_y1_px": int(np.where(overlap_fg)[0].max()),
        "axis_mask": "machine_axis_mask_300dpi.png",
        "marker_mask": "machine_marker_mask_300dpi.png",
        "overlap_mask": "machine_axis_marker_overlap_mask_300dpi.png",
        "overlay_8x": "machine_axis_marker_overlap_overlay_8x.png",
    }]
    write_csv(ROOT / "machine_overlap_candidate_clusters.csv", list(overlap_rows[0].keys()), overlap_rows)

    clearance_rows = [
        {
            "measurement_id": "CLR_001", "object_a": "TXT_B_LIMIT_NOTE[first N]", "object_b": "GFX_B_CURVE",
            "minimum_center_distance_px_low": 1.0, "minimum_center_distance_px_high": 1.414,
            "method": "same-font peer N translated by 75/76 native pixels against vector curve mask",
            "evidence": "critical_limit_note_1x_native_300dpi.png;critical_limit_note_8x_nearest.png",
        },
        {
            "measurement_id": "CLR_002", "object_a": "TXT_B_XTICK_099", "object_b": "GFX_B_AXIS_AND_TICKS",
            "minimum_center_distance_px_low": round((189.244171 - 186.518936) * SCALE, 3),
            "minimum_center_distance_px_high": round((189.244171 - 186.518936) * SCALE, 3),
            "method": "R104 PDF vector/text bbox vertical separation",
            "evidence": "critical_right_panel_8x_nearest.png",
        },
    ]
    write_csv(ROOT / "machine_clearance_measurements.csv", list(clearance_rows[0].keys()), clearance_rows)

    # Multiview inventory is a mechanical mapping, not a reviewer verdict.
    views = [
        {"view_id": "FULL_PAGE_200", "path": "full_page_200dpi.png", "native_dpi": 200, "post_resize": "none"},
        {"view_id": "FULL_PAGE_300", "path": "full_page_300dpi.png", "native_dpi": 300, "post_resize": "none"},
        {"view_id": "FIGURE_CROP_300", "path": "figure_crop_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "STANDALONE_EQUIV_300", "path": "standalone_equivalent_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "GRAYSCALE_300", "path": "grayscale_300dpi.png", "native_dpi": 300, "post_resize": "crop_then_grayscale"},
        {"view_id": "CRITICAL_RIGHT_1X", "path": "critical_right_panel_1x_native_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "CRITICAL_RIGHT_8X", "path": "critical_right_panel_8x_nearest.png", "native_dpi": 300, "post_resize": "nearest_8x_for_pixel_inspection"},
        {"view_id": "CRITICAL_LIMIT_1X", "path": "critical_limit_note_1x_native_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "CRITICAL_LIMIT_8X", "path": "critical_limit_note_8x_nearest.png", "native_dpi": 300, "post_resize": "nearest_8x_for_pixel_inspection"},
        {"view_id": "CRITICAL_POINT_1X", "path": "critical_point_label_1x_native_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "CRITICAL_POINT_8X", "path": "critical_point_label_8x_nearest.png", "native_dpi": 300, "post_resize": "nearest_8x_for_pixel_inspection"},
        {"view_id": "CRITICAL_TITLE_1X", "path": "critical_panel_title_fraction_1x_native_300dpi.png", "native_dpi": 300, "post_resize": "crop_only"},
        {"view_id": "CRITICAL_TITLE_8X", "path": "critical_panel_title_fraction_8x_nearest.png", "native_dpi": 300, "post_resize": "nearest_8x_for_pixel_inspection"},
        {"view_id": "TEXT_OVERLAY_300", "path": "machine_text_measurement_overlay_300dpi.png", "native_dpi": 300, "post_resize": "crop_only_plus_overlay"},
        {"view_id": "CLIP_GUARD_300", "path": "machine_clip_guard_overlay_300dpi.png", "native_dpi": 300, "post_resize": "crop_only_plus_overlay"},
        {"view_id": "AXIS_MARKER_OVERLAP_1X", "path": "machine_axis_marker_overlap_overlay_1x.png", "native_dpi": 300, "post_resize": "crop_only_plus_overlap_overlay"},
        {"view_id": "AXIS_MARKER_OVERLAP_8X", "path": "machine_axis_marker_overlap_overlay_8x.png", "native_dpi": 300, "post_resize": "nearest_8x_for_pixel_inspection"},
    ]
    write_csv(ROOT / "machine_multiview_inventory.csv", list(views[0].keys()), views)

    # Independent page/figure mapping record, mechanically tied to the caption text.
    mapping = [{
        "figure_uid": "FIG-P640-01", "figure_number": "33.7",
        "physical_pdf_page": PHYSICAL_PAGE, "printed_page": PRINTED_PAGE,
        "source_label": "fig:V5-C04-mixing-rho-comparison",
        "caption_anchor": "二元正态系统Gibbs的轮末解析自相关为",
        "mapping_method": "current source caption+label matched against authorized R104 PDF text",
    }]
    write_csv(ROOT / "machine_independent_page_mapping.csv", list(mapping[0].keys()), mapping)


if __name__ == "__main__":
    main()
