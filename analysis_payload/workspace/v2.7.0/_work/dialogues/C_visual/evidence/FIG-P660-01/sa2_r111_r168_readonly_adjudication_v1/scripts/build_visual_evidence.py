from __future__ import annotations

import csv
import itertools
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.spatial import cKDTree


PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf"
)
ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1"
)
FULL_PAGE = ROOT / "03_renders" / "r111_p709_full_300dpi.png"
DENOMINATOR = ROOT / "07_manual" / "visible_object_denominator.csv"
SPAN_TABLE = ROOT / "06_machine_tables" / "page709_text_spans.csv"
PAGE_INDEX = 708
SCALE = 300.0 / 72.0
CROP_PT = (55.0, 60.0, 530.0, 340.0)


DECLARED_PT = {
    "O007": 8.7,
    "O008": 8.7,
    "O009": 8.7,
    **{f"O{i:03d}": 9.5 for i in range(10, 28)},
}


SCRIPT_CLASS = {
    "O007": "MATH_MIXED_WITH_SUBSCRIPT",
    "O008": "MATH_MIXED_WITH_SUBSCRIPT",
    "O009": "MATH_MIXED_WITH_SUBSCRIPT",
    "O010": "MATH_MIXED_WITH_SUBSCRIPT",
    "O011": "CJK_WITH_DIGIT",
    "O012": "MATH_MIXED_WITH_SUBSCRIPT",
    "O013": "CJK_WITH_DIGIT",
    "O014": "MATH_MIXED_WITH_SUBSCRIPT",
    "O015": "CJK_WITH_DIGIT",
    "O016": "MATH_MIXED",
    "O018": "MATH_MIXED_WITH_SUBSCRIPT",
    "O019": "MATH_MIXED_WITH_SUPERSCRIPT",
    "O021": "CJK",
    "O022": "CJK",
    "O023": "CJK_WITH_DIGIT",
    "O025": "CJK",
    "O026": "CJK",
    "O027": "CJK",
    "O028": "CJK_WITH_DIGITS",
    "O029": "CJK_WITH_DIGIT",
    "O030": "CJK_LATIN_MIXED",
}


COMPARISON_GROUPS = {
    "COMPONENT_LABEL": ["O007", "O008", "O009"],
    "VERTEX_COORDINATE": ["O010", "O012", "O014"],
    "VERTEX_MEANING": ["O011", "O013", "O015"],
    "REGION_STATEMENT": ["O021", "O022", "O023"],
    "CONCLUSION_LINE": ["O025", "O026", "O027"],
}


ROI_PT = {
    "R01_TOP_VERTEX": (145.0, 64.0, 225.0, 112.0),
    "R02_THETA2_RAY": (105.0, 140.0, 210.0, 198.0),
    "R03_THETA1_RAY": (190.0, 140.0, 278.0, 198.0),
    "R04_POINT_COORDINATE": (186.0, 170.0, 324.0, 205.0),
    "R05_BASE_THETA3": (182.0, 258.0, 244.0, 305.0),
    "R06_LEFT_VERTEX": (55.0, 258.0, 142.0, 305.0),
    "R07_RIGHT_VERTEX": (248.0, 258.0, 325.0, 305.0),
    "R08_CONSTRAINT_CARD": (348.0, 122.0, 527.0, 169.0),
    "R09_REGION_CARD": (348.0, 181.0, 527.0, 237.0),
    "R10_CONCLUSION_CARD": (348.0, 245.0, 527.0, 301.0),
    "R11_CAPTION": (55.0, 300.0, 530.0, 339.0),
}


def pt_to_px(value: float) -> int:
    return int(round(value * SCALE))


def bbox_pt_to_px(row: dict[str, str]) -> tuple[int, int, int, int]:
    return tuple(pt_to_px(float(row[key])) for key in ("x0_pt", "y0_pt", "x1_pt", "y1_pt"))  # type: ignore[return-value]


def adaptive_ink_mask(
    full_rgb: np.ndarray, bbox: tuple[int, int, int, int]
) -> tuple[np.ndarray, float, float]:
    height, width = full_rgb.shape[:2]
    x0, y0, x1, y1 = bbox
    x0 = max(0, min(width - 1, x0))
    y0 = max(0, min(height - 1, y0))
    x1 = max(x0 + 1, min(width, x1 + 1))
    y1 = max(y0 + 1, min(height, y1 + 1))
    roi = full_rgb[y0:y1, x0:x1]
    lum = 0.2126 * roi[:, :, 0] + 0.7152 * roi[:, :, 1] + 0.0722 * roi[:, :, 2]
    background = float(np.quantile(lum, 0.88))
    threshold = max(0.0, background - 20.0)
    local = lum <= threshold
    mask = np.zeros((height, width), dtype=bool)
    mask[y0:y1, x0:x1] = local
    return mask, background, threshold


def draw_geometry_masks(
    size: tuple[int, int], rows: dict[str, dict[str, str]]
) -> dict[str, np.ndarray]:
    width, height = size
    masks: dict[str, np.ndarray] = {}

    def blank() -> Image.Image:
        return Image.new("1", (width, height), 0)

    def point(x: float, y: float) -> tuple[int, int]:
        return pt_to_px(x), pt_to_px(y)

    e1 = (90.5780, 271.5330)
    e2 = (289.0057, 271.5330)
    e3 = (189.79185, 99.6948)
    th = (199.7134, 185.6137)

    triangle = blank()
    draw = ImageDraw.Draw(triangle)
    draw.line([point(*e1), point(*e2), point(*e3), point(*e1)], fill=1, width=4, joint="curve")
    masks["O001"] = np.asarray(triangle, dtype=bool)

    grid = blank()
    draw = ImageDraw.Draw(grid)

    def interp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
        return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])

    for t in (0.2, 0.4, 0.6, 0.8):
        draw.line([point(*interp(e1, e2, t)), point(*interp(e3, e2, t))], fill=1, width=2)
        draw.line([point(*interp(e2, e3, t)), point(*interp(e1, e3, t))], fill=1, width=2)
        draw.line([point(*interp(e3, e1, t)), point(*interp(e2, e1, t))], fill=1, width=2)
    masks["O002"] = np.asarray(grid, dtype=bool)

    ray_endpoints = {
        "O003": (229.4790, 168.4313),
        "O004": (155.0654, 159.8392),
        "O005": (199.7134, 271.5330),
    }
    for object_id, endpoint in ray_endpoints.items():
        ray = blank()
        draw = ImageDraw.Draw(ray)
        start_px = point(*th)
        end_px = point(*endpoint)
        total = math.dist(start_px, end_px)
        dash = 16.0
        gap = 10.0
        direction = ((end_px[0] - start_px[0]) / total, (end_px[1] - start_px[1]) / total)
        cursor = 0.0
        while cursor < total:
            stop = min(total, cursor + dash)
            a = (round(start_px[0] + direction[0] * cursor), round(start_px[1] + direction[1] * cursor))
            b = (round(start_px[0] + direction[0] * stop), round(start_px[1] + direction[1] * stop))
            draw.line([a, b], fill=1, width=3)
            cursor += dash + gap
        masks[object_id] = np.asarray(ray, dtype=bool)

    marker = blank()
    draw = ImageDraw.Draw(marker)
    x0, y0, x1, y1 = bbox_pt_to_px(rows["O006"])
    draw.ellipse([x0, y0, x1, y1], fill=1)
    masks["O006"] = np.asarray(marker, dtype=bool)

    for object_id in ("O017", "O020", "O024"):
        card = blank()
        draw = ImageDraw.Draw(card)
        x0, y0, x1, y1 = bbox_pt_to_px(rows[object_id])
        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=1, width=3)
        masks[object_id] = np.asarray(card, dtype=bool)
    return masks


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def mask_clearance(
    coords_a: np.ndarray,
    coords_b: np.ndarray,
    tree_a: cKDTree | None,
    tree_b: cKDTree | None,
) -> float:
    if coords_a.size == 0 or coords_b.size == 0 or tree_a is None or tree_b is None:
        return math.inf
    if len(coords_a) <= len(coords_b):
        distances, _ = tree_b.query(coords_a, k=1, workers=-1)
    else:
        distances, _ = tree_a.query(coords_b, k=1, workers=-1)
    return float(np.min(distances))


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\consola.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def main() -> None:
    rows_list: list[dict[str, str]] = []
    with DENOMINATOR.open("r", encoding="utf-8-sig", newline="") as handle:
        rows_list = list(csv.DictReader(handle))
    rows = {row["object_id"]: row for row in rows_list}

    spans_list: list[dict[str, str]] = []
    with SPAN_TABLE.open("r", encoding="utf-8-sig", newline="") as handle:
        spans_list = list(csv.DictReader(handle))
    spans = {row["span_id"]: row for row in spans_list}

    full_image = Image.open(FULL_PAGE).convert("RGB")
    full_rgb = np.asarray(full_image)
    width, height = full_image.size
    crop_px = tuple(pt_to_px(value) for value in CROP_PT)
    crop = full_image.crop(crop_px)
    crop.save(ROOT / "03_renders" / "after_figure_crop_native_300dpi.png")
    ImageOps.grayscale(crop).save(ROOT / "03_renders" / "after_grayscale_native_300dpi.png")

    object_masks = draw_geometry_masks(full_image.size, rows)
    text_metrics: dict[str, dict[str, float | int]] = {}
    for row in rows_list:
        object_id = row["object_id"]
        if row["kind"] not in {"TEXT", "FORMULA"}:
            continue
        bbox = bbox_pt_to_px(row)
        mask, background, threshold = adaptive_ink_mask(full_rgb, bbox)
        object_masks[object_id] = mask
        ys, xs = np.where(mask)
        text_metrics[object_id] = {
            "foreground_px": int(mask.sum()),
            "ink_x0_px": int(xs.min()) if xs.size else -1,
            "ink_y0_px": int(ys.min()) if ys.size else -1,
            "ink_x1_px": int(xs.max()) if xs.size else -1,
            "ink_y1_px": int(ys.max()) if ys.size else -1,
            "h_ink_px": int(ys.max() - ys.min() + 1) if ys.size else 0,
            "background_luma": background,
            "threshold_luma": threshold,
        }

    crop_x0, crop_y0, crop_x1, crop_y1 = crop_px
    crop_width, crop_height = crop.size

    text_mask = np.zeros((height, width), dtype=bool)
    graphic_mask = np.zeros((height, width), dtype=bool)
    for row in rows_list:
        object_id = row["object_id"]
        if row["kind"] in {"TEXT", "FORMULA"}:
            text_mask |= object_masks[object_id]
        else:
            graphic_mask |= object_masks[object_id]

    crop_text_mask = text_mask[crop_y0:crop_y1, crop_x0:crop_x1]
    crop_graphic_mask = graphic_mask[crop_y0:crop_y1, crop_x0:crop_x1]
    Image.fromarray((crop_text_mask.astype(np.uint8) * 255), mode="L").save(
        ROOT / "04_overlays_masks" / "text_ink_mask_native_300dpi.png"
    )
    Image.fromarray((crop_graphic_mask.astype(np.uint8) * 255), mode="L").save(
        ROOT / "04_overlays_masks" / "graphic_foreground_mask_native_300dpi.png"
    )
    combined = np.zeros((crop_height, crop_width, 3), dtype=np.uint8)
    combined[crop_graphic_mask] = (0, 170, 255)
    combined[crop_text_mask] = (255, 255, 255)
    combined[np.logical_and(crop_graphic_mask, crop_text_mask)] = (255, 0, 0)
    Image.fromarray(combined, mode="RGB").save(
        ROOT / "04_overlays_masks" / "text_graphic_mask_composite_native_300dpi.png"
    )

    font = load_font(18)
    text_overlay = crop.copy()
    text_draw = ImageDraw.Draw(text_overlay)
    object_overlay = crop.copy()
    object_draw = ImageDraw.Draw(object_overlay)
    kind_colors = {
        "TEXT": (220, 40, 40),
        "FORMULA": (160, 40, 200),
        "GRAPHIC": (0, 110, 210),
        "MARKER": (0, 150, 100),
        "NODE_BORDER": (230, 130, 0),
    }
    for row in rows_list:
        object_id = row["object_id"]
        x0, y0, x1, y1 = bbox_pt_to_px(row)
        box = [x0 - crop_x0, y0 - crop_y0, x1 - crop_x0, y1 - crop_y0]
        color = kind_colors[row["kind"]]
        object_draw.rectangle(box, outline=color, width=2)
        object_draw.text((box[0] + 2, max(0, box[1] - 19)), object_id, fill=color, font=font)
        if row["kind"] in {"TEXT", "FORMULA"}:
            text_draw.rectangle(box, outline=color, width=2)
            text_draw.text((box[0] + 2, max(0, box[1] - 19)), object_id, fill=color, font=font)
    text_overlay.save(ROOT / "04_overlays_masks" / "text_measurement_overlay_native_300dpi.png")
    object_overlay.save(ROOT / "04_overlays_masks" / "all_object_overlay_native_300dpi.png")

    with (ROOT / "06_machine_tables" / "object_pixel_metrics.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "object_id",
                "kind",
                "semantic_role",
                "declared_pt_if_in_figure_source",
                "graphics_scale",
                "effective_pt_if_in_figure_source",
                "script_class",
                "bbox_x0_px",
                "bbox_y0_px",
                "bbox_x1_px",
                "bbox_y1_px",
                "foreground_px",
                "ink_x0_px",
                "ink_y0_px",
                "ink_x1_px",
                "ink_y1_px",
                "h_ink_px",
                "background_luma",
                "threshold_luma",
            ]
        )
        for row in rows_list:
            object_id = row["object_id"]
            if object_id not in text_metrics:
                continue
            metric = text_metrics[object_id]
            bbox = bbox_pt_to_px(row)
            declared = DECLARED_PT.get(object_id, "")
            writer.writerow(
                [
                    object_id,
                    row["kind"],
                    row["semantic_role"],
                    declared,
                    1.0 if declared != "" else "",
                    declared,
                    SCRIPT_CLASS.get(object_id, ""),
                    *bbox,
                    metric["foreground_px"],
                    metric["ink_x0_px"],
                    metric["ink_y0_px"],
                    metric["ink_x1_px"],
                    metric["ink_y1_px"],
                    metric["h_ink_px"],
                    f"{metric['background_luma']:.3f}",
                    f"{metric['threshold_luma']:.3f}",
                ]
            )

    with (ROOT / "06_machine_tables" / "same_class_ratio_metrics.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "comparison_group",
                "object_id",
                "h_ink_px",
                "group_median_h_ink_px",
                "ratio_to_group_median",
                "group_max_min_ratio",
            ]
        )
        for group, object_ids in COMPARISON_GROUPS.items():
            values = [float(text_metrics[object_id]["h_ink_px"]) for object_id in object_ids]
            median = float(np.median(values))
            max_min = max(values) / min(values)
            for object_id, value in zip(object_ids, values):
                writer.writerow([group, object_id, int(value), f"{median:.3f}", f"{value / median:.4f}", f"{max_min:.4f}"])

    flat_indices = {object_id: np.flatnonzero(mask) for object_id, mask in object_masks.items()}
    mask_coords = {object_id: np.argwhere(mask) for object_id, mask in object_masks.items()}
    mask_trees = {
        object_id: cKDTree(coords) if coords.size else None
        for object_id, coords in mask_coords.items()
    }

    pair_rows: list[dict[str, object]] = []
    for pair_number, (row_a, row_b) in enumerate(itertools.combinations(rows_list, 2), start=1):
        object_a = row_a["object_id"]
        object_b = row_b["object_id"]
        bbox_a = bbox_pt_to_px(row_a)
        bbox_b = bbox_pt_to_px(row_b)
        overlap = int(np.intersect1d(flat_indices[object_a], flat_indices[object_b], assume_unique=True).size)
        clearance = mask_clearance(
            mask_coords[object_a],
            mask_coords[object_b],
            mask_trees[object_a],
            mask_trees[object_b],
        )
        ax0, ay0, ax1, ay1 = bbox_a
        bx0, by0, bx1, by1 = bbox_b
        ix = max(0, min(ax1, bx1) - max(ax0, bx0) + 1)
        iy = max(0, min(ay1, by1) - max(ay0, by0) + 1)
        pair_rows.append(
            {
                "pair_id": f"P{pair_number:03d}",
                "object_a": object_a,
                "object_b": object_b,
                "kind_a": row_a["kind"],
                "kind_b": row_b["kind"],
                "semantic_role_a": row_a["semantic_role"],
                "semantic_role_b": row_b["semantic_role"],
                "bbox_intersection_px2": ix * iy,
                "bbox_clearance_px": bbox_clearance(bbox_a, bbox_b),
                "foreground_overlap_px_machine": overlap,
                "foreground_clearance_px_machine": clearance,
            }
        )

    pair_fields = list(pair_rows[0].keys())
    with (ROOT / "06_machine_tables" / "all_unordered_pairs_machine.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=pair_fields)
        writer.writeheader()
        for row in pair_rows:
            formatted = dict(row)
            formatted["bbox_clearance_px"] = f"{float(row['bbox_clearance_px']):.3f}"
            formatted["foreground_clearance_px_machine"] = (
                "INF" if math.isinf(float(row["foreground_clearance_px_machine"])) else f"{float(row['foreground_clearance_px_machine']):.3f}"
            )
            writer.writerow(formatted)

    near_rows = [
        row
        for row in pair_rows
        if int(row["foreground_overlap_px_machine"]) > 0
        or float(row["foreground_clearance_px_machine"]) <= 12.0
    ]
    with (ROOT / "06_machine_tables" / "near_or_overlap_pairs_machine.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=pair_fields)
        writer.writeheader()
        for row in near_rows:
            formatted = dict(row)
            formatted["bbox_clearance_px"] = f"{float(row['bbox_clearance_px']):.3f}"
            formatted["foreground_clearance_px_machine"] = f"{float(row['foreground_clearance_px_machine']):.3f}"
            writer.writerow(formatted)

    matrix_size = 44
    matrix_margin = 115
    matrix = Image.new("RGB", (matrix_margin + 30 * matrix_size + 20, matrix_margin + 30 * matrix_size + 20), "white")
    matrix_draw = ImageDraw.Draw(matrix)
    matrix_font = load_font(14)
    ids = [row["object_id"] for row in rows_list]
    pair_lookup = {(row["object_a"], row["object_b"]): row for row in pair_rows}
    for index, object_id in enumerate(ids):
        pos = matrix_margin + index * matrix_size
        matrix_draw.text((pos + 3, 90), object_id, fill="black", font=matrix_font)
        matrix_draw.text((5, pos + 12), object_id, fill="black", font=matrix_font)
    for i, object_a in enumerate(ids):
        for j, object_b in enumerate(ids):
            x0 = matrix_margin + j * matrix_size
            y0 = matrix_margin + i * matrix_size
            if i == j:
                color = (80, 80, 80)
            else:
                key = (object_a, object_b) if i < j else (object_b, object_a)
                row = pair_lookup[key]
                overlap = int(row["foreground_overlap_px_machine"])
                clearance = float(row["foreground_clearance_px_machine"])
                if overlap > 0:
                    color = (220, 50, 50)
                elif clearance <= 3:
                    color = (255, 150, 40)
                elif clearance <= 12:
                    color = (255, 225, 90)
                else:
                    color = (230, 245, 235)
            matrix_draw.rectangle([x0, y0, x0 + matrix_size - 1, y0 + matrix_size - 1], fill=color, outline=(180, 180, 180))
    matrix.save(ROOT / "04_overlays_masks" / "all_unordered_pairs_contact_matrix.png")

    with (ROOT / "06_machine_tables" / "span_pixel_metrics.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "span_id",
                "text",
                "font",
                "font_size_pdf_pt",
                "bbox_x0_px",
                "bbox_y0_px",
                "bbox_x1_px",
                "bbox_y1_px",
                "foreground_px",
                "h_ink_px",
                "background_luma",
                "threshold_luma",
            ]
        )
        for span in spans_list:
            span_number = int(span["span_id"][1:])
            if span_number < 11 or span_number > 79:
                continue
            bbox = (
                int(span["x0_px_300"]),
                int(span["y0_px_300"]),
                int(span["x1_px_300"]),
                int(span["y1_px_300"]),
            )
            mask, background, threshold = adaptive_ink_mask(full_rgb, bbox)
            ys, _ = np.where(mask)
            writer.writerow(
                [
                    span["span_id"],
                    span["text"],
                    span["font"],
                    span["font_size_pt"],
                    *bbox,
                    int(mask.sum()),
                    int(ys.max() - ys.min() + 1) if ys.size else 0,
                    f"{background:.3f}",
                    f"{threshold:.3f}",
                ]
            )

    region_text = "".join(
        span["text"] for span in spans_list if 11 <= int(span["span_id"][1:]) <= 79
    )
    codepoint_counts: dict[str, int] = defaultdict(int)
    for char in region_text:
        if not char.isspace():
            codepoint_counts[char] += 1
    with (ROOT / "06_machine_tables" / "rendered_codepoints.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["character", "codepoint", "unicode_name", "occurrence_count"])
        for char in sorted(codepoint_counts, key=ord):
            writer.writerow([char, f"U+{ord(char):04X}", unicodedata.name(char, "UNNAMED"), codepoint_counts[char]])

    for roi_id, roi_pt in ROI_PT.items():
        roi_px = tuple(pt_to_px(value) for value in roi_pt)
        roi = full_image.crop(roi_px)
        roi.save(ROOT / "05_roi" / f"{roi_id}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / "05_roi" / f"{roi_id}_nearest8x.png"
        )

    full_foreground = np.logical_or(text_mask, graphic_mask)
    crop_foreground = full_foreground[crop_y0:crop_y1, crop_x0:crop_x1]
    edge_counts = {
        "top_1px": int(crop_foreground[:1, :].sum()),
        "bottom_1px": int(crop_foreground[-1:, :].sum()),
        "left_1px": int(crop_foreground[:, :1].sum()),
        "right_1px": int(crop_foreground[:, -1:].sum()),
        "top_6px": int(crop_foreground[:6, :].sum()),
        "bottom_6px": int(crop_foreground[-6:, :].sum()),
        "left_6px": int(crop_foreground[:, :6].sum()),
        "right_6px": int(crop_foreground[:, -6:].sum()),
    }
    min_object_x0 = min(float(row["x0_pt"]) for row in rows_list)
    min_object_y0 = min(float(row["y0_pt"]) for row in rows_list)
    max_object_x1 = max(float(row["x1_pt"]) for row in rows_list)
    max_object_y1 = max(float(row["y1_pt"]) for row in rows_list)
    with (ROOT / "06_machine_tables" / "crop_edge_machine_metrics.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key, value in edge_counts.items():
            writer.writerow([key, value])
        writer.writerow(["object_margin_left_px", f"{(min_object_x0 - CROP_PT[0]) * SCALE:.3f}"])
        writer.writerow(["object_margin_top_px", f"{(min_object_y0 - CROP_PT[1]) * SCALE:.3f}"])
        writer.writerow(["object_margin_right_px", f"{(CROP_PT[2] - max_object_x1) * SCALE:.3f}"])
        writer.writerow(["object_margin_bottom_px", f"{(CROP_PT[3] - max_object_y1) * SCALE:.3f}"])

    with (ROOT / "06_machine_tables" / "machine_evidence_summary.txt").open(
        "w", encoding="utf-8"
    ) as handle:
        handle.write(f"OBJECT_COUNT={len(rows_list)}\n")
        handle.write(f"UNORDERED_PAIR_COUNT={len(pair_rows)}\n")
        handle.write(f"NEAR_OR_OVERLAP_PAIR_COUNT={len(near_rows)}\n")
        handle.write(f"TEXT_OBJECT_COUNT={sum(row['kind'] in {'TEXT', 'FORMULA'} for row in rows_list)}\n")
        handle.write(f"GRAPHIC_OBJECT_COUNT={sum(row['kind'] not in {'TEXT', 'FORMULA'} for row in rows_list)}\n")
        handle.write(f"TEXT_GRAPHIC_MASK_OVERLAP_PX={int(np.logical_and(text_mask, graphic_mask).sum())}\n")
        handle.write(f"CROP_SIZE_PX={crop_width}x{crop_height}\n")
        handle.write("MACHINE_FIELDS_ONLY=true\n")


if __name__ == "__main__":
    main()
