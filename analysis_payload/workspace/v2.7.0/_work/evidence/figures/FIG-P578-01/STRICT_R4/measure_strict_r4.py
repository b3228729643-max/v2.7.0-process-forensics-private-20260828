from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
R3 = ROOT.parent / "STRICT_R3"
BEFORE_PDF = R3 / "official_r90_page_626.pdf"
BEFORE_PNG = R3 / "full_page_300dpi.png"
BASELINE_PDF = R3 / "candidate_page.pdf"
BASELINE_PNG = ROOT / "baseline_r3_candidate_page_300dpi.png"
AFTER_PDF = ROOT / "candidate_page.pdf"
AFTER_PNG = ROOT / "candidate_page_300dpi.png"
STANDALONE_PDF = ROOT / "candidate_standalone.pdf"
STANDALONE_PNG = ROOT / "candidate_standalone_300dpi.png"
SOURCE = (
    ROOT.parents[3]
    / "source"
    / "v2.7.0"
    / "src"
    / "绘图源码"
    / "第05册_采样方法主题模型与图排序"
    / "V5-C02"
    / "fig_v5_c02_rejection_flow.tex"
)

TEXT = ((31, 35, 40), 35)
RULE_GRAY = ((184, 192, 200), 10)
BLUE = ((31, 78, 121), 35)


def flatten_spans(page: fitz.Page) -> list[dict]:
    spans: list[dict] = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            spans.extend(line.get("spans", []))
    return spans


def px_box_from_rect(rect: fitz.Rect, sx: float, sy: float, pad: int) -> list[int]:
    return [
        math.floor(rect.x0 * sx) - pad,
        math.floor(rect.y0 * sy) - pad,
        math.ceil(rect.x1 * sx) + pad,
        math.ceil(rect.y1 * sy) + pad,
    ]


def px_box_from_spans(spans: list[dict], sx: float, sy: float, pad: int) -> list[int]:
    boxes = [span["bbox"] for span in spans]
    rect = fitz.Rect(
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )
    return px_box_from_rect(rect, sx, sy, pad)


def drawing_box(drawings: list[dict], ids: list[int], sx: float, sy: float, pad: int) -> list[int]:
    rects = [drawings[index - 1]["rect"] for index in ids]
    rect = fitz.Rect(
        min(item.x0 for item in rects),
        min(item.y0 for item in rects),
        max(item.x1 for item in rects),
        max(item.y1 for item in rects),
    )
    return px_box_from_rect(rect, sx, sy, pad)


def color_pixels(
    image: np.ndarray, box: list[int], target: tuple[int, int, int], tolerance: int
) -> set[tuple[int, int]]:
    height, width = image.shape[:2]
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    delta = image[y0:y1, x0:x1].astype(np.int16) - np.array(target, dtype=np.int16)
    selected = np.all(np.abs(delta) <= tolerance, axis=2)
    ys, xs = np.where(selected)
    return set(zip((xs + x0).tolist(), (ys + y0).tolist()))


def occupied_box(points: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def format_box(points: set[tuple[int, int]]) -> str:
    return ",".join(str(value) for value in occupied_box(points))


def mask_relation(
    a: set[tuple[int, int]], b: set[tuple[int, int]]
) -> tuple[int, float, tuple[int, int], tuple[int, int]]:
    overlap = len(a & b)
    array_a = np.array([(y, x) for x, y in a], dtype=np.int32)
    array_b = np.array([(y, x) for x, y in b], dtype=np.int32)
    distances, indices = cKDTree(array_b).query(array_a, k=1)
    nearest_a = int(np.argmin(distances))
    nearest_b = int(indices[nearest_a])
    raw = max(0.0, float(distances[nearest_a]) - 1.0)
    point_a = (int(array_a[nearest_a, 1]), int(array_a[nearest_a, 0]))
    point_b = (int(array_b[nearest_b, 1]), int(array_b[nearest_b, 0]))
    return overlap, raw, point_a, point_b


def cluster_lines(spans: list[dict]) -> list[list[dict]]:
    ordered = sorted(spans, key=lambda item: (item["bbox"][1] + item["bbox"][3]) / 2)
    groups: list[list[dict]] = []
    centers: list[float] = []
    for span in ordered:
        center = (span["bbox"][1] + span["bbox"][3]) / 2
        if not groups or center - centers[-1] > 7:
            groups.append([span])
            centers.append(center)
        else:
            groups[-1].append(span)
            centers[-1] = sum(
                (item["bbox"][1] + item["bbox"][3]) / 2 for item in groups[-1]
            ) / len(groups[-1])
    return groups


def add_row(
    rows: list[dict],
    *,
    stage: str,
    check_id: str,
    check_class: str,
    a: set[tuple[int, int]],
    b: set[tuple[int, int]],
    required: int,
) -> None:
    overlap, raw, point_a, point_b = mask_relation(a, b)
    measured = int(round(raw))
    rows.append(
        {
            "STAGE": stage,
            "CHECK_ID": check_id,
            "CHECK_CLASS": check_class,
            "A_INK_BBOX_X0Y0X1Y1": format_box(a),
            "B_INK_BBOX_X0Y0X1Y1": format_box(b),
            "OVERLAP_PIXEL_COUNT": overlap,
            "MIN_CLEARANCE_RAW_PX": f"{raw:.6f}",
            "MIN_CLEARANCE_PX": measured,
            "REQUIRED_CLEARANCE_PX": required,
            "A_CLOSEST_XY": f"{point_a[0]},{point_a[1]}",
            "B_CLOSEST_XY": f"{point_b[0]},{point_b[1]}",
            "PASS_FAIL": "PASS" if overlap == 0 and measured >= required else "FAIL",
        }
    )


def measure_stage(
    stage: str,
    pdf_path: Path,
    png_path: Path,
    offset: int,
) -> tuple[list[dict], dict]:
    with fitz.open(pdf_path) as document:
        page = document[0]
        page_rect = fitz.Rect(page.rect)
        drawings = page.get_drawings()
        spans = flatten_spans(page)

    image = np.array(Image.open(png_path).convert("RGB"))
    height, width = image.shape[:2]
    sx, sy = width / page_rect.width, height / page_rect.height
    nodes = {
        "INIT": {
            "drawing": 5 + offset,
            "incoming": [32 + offset, 33 + offset],
            "outgoing": [35 + offset, 36 + offset],
        },
        "EVALUATE": {
            "drawing": 17 + offset,
            "incoming": [60 + offset, 61 + offset],
            "outgoing": [63 + offset, 64 + offset],
        },
    }

    rows: list[dict] = []
    details: dict = {
        "image_size": [width, height],
        "page_size_pt": [page_rect.width, page_rect.height],
        "drawing_count": len(drawings),
        "span_count": len(spans),
        "nodes": {},
    }
    for node_name, spec in nodes.items():
        node_rect = drawings[spec["drawing"] - 1]["rect"]
        node_spans = [
            span
            for span in spans
            if node_rect.x0 <= (span["bbox"][0] + span["bbox"][2]) / 2 <= node_rect.x1
            and node_rect.y0 <= (span["bbox"][1] + span["bbox"][3]) / 2 <= node_rect.y1
        ]
        line_groups = cluster_lines(node_spans)
        if len(line_groups) != 2:
            raise RuntimeError(f"{stage} {node_name}: expected 2 lines, got {len(line_groups)}")

        text_box = px_box_from_spans(node_spans, sx, sy, 2)
        text = color_pixels(image, text_box, *TEXT)
        line_masks = [
            color_pixels(image, px_box_from_spans(group, sx, sy, 1), *TEXT)
            for group in line_groups
        ]
        node_box = drawing_box(drawings, [spec["drawing"]], sx, sy, 2)
        x0, y0, x1, y1 = node_box
        side_boxes = {
            "TOP": [x0, y0, x1, min(y1, y0 + 12)],
            "BOTTOM": [x0, max(y0, y1 - 12), x1, y1],
            "LEFT": [x0, y0, min(x1, x0 + 12), y1],
            "RIGHT": [max(x0, x1 - 12), y0, x1, y1],
        }
        side_masks = {
            name: color_pixels(image, box, *RULE_GRAY) for name, box in side_boxes.items()
        }
        for side_name, border in side_masks.items():
            required = 8 if stage.startswith("AFTER") and side_name == "BOTTOM" else 5
            add_row(
                rows,
                stage=stage,
                check_id=f"N_{node_name}_TEXT_BORDER_{side_name}",
                check_class="TEXT-NODE_BORDER",
                a=text,
                b=border,
                required=required,
            )

        add_row(
            rows,
            stage=stage,
            check_id=f"T_{node_name}_LINE_1_2",
            check_class="TEXT-TEXT",
            a=line_masks[0],
            b=line_masks[1],
            required=4,
        )
        for direction in ("incoming", "outgoing"):
            arrow = color_pixels(
                image,
                drawing_box(drawings, spec[direction], sx, sy, 4),
                *BLUE,
            )
            add_row(
                rows,
                stage=stage,
                check_id=f"A_{node_name}_TEXT_{direction.upper()}_ARROW",
                check_class="TEXT-LINE_ARROW",
                a=text,
                b=arrow,
                required=3,
            )

        script_spans = [
            span for span in node_spans if 7.40 <= float(span.get("size", 0)) <= 7.50
        ]
        if node_name == "INIT" and script_spans:
            script = color_pixels(
                image, px_box_from_spans(script_spans, sx, sy, 1), *TEXT
            )
            add_row(
                rows,
                stage=stage,
                check_id="T_INIT_NATURAL_SCRIPT_LINE_1",
                check_class="NATURAL_SCRIPT-TEXT",
                a=line_masks[0],
                b=script,
                required=4,
            )
            add_row(
                rows,
                stage=stage,
                check_id="N_INIT_NATURAL_SCRIPT_BORDER_BOTTOM",
                check_class="NATURAL_SCRIPT-NODE_BORDER",
                a=script,
                b=side_masks["BOTTOM"],
                required=8 if stage.startswith("AFTER") else 5,
            )

        details["nodes"][node_name] = {
            "node_vector_rect_pt": [round(value, 6) for value in node_rect],
            "text_ink_bbox_px": list(occupied_box(text)),
            "line_ink_bboxes_px": [list(occupied_box(mask)) for mask in line_masks],
            "visible_font_sizes_pt": sorted(
                {round(float(span.get("size", 0)), 4) for span in node_spans}
            ),
        }
    return rows, details


def normalize_drawing(value):
    if isinstance(value, fitz.Point):
        return [round(value.x, 6), round(value.y, 6)]
    if isinstance(value, fitz.Rect):
        return [round(item, 6) for item in value]
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, tuple):
        return [normalize_drawing(item) for item in value]
    if isinstance(value, list):
        return [normalize_drawing(item) for item in value]
    return value


def drawing_signature(path: Path) -> list[dict]:
    with fitz.open(path) as document:
        drawings = document[0].get_drawings()
    keys = (
        "items",
        "type",
        "closePath",
        "even_odd",
        "fill_opacity",
        "stroke_opacity",
        "color",
        "fill",
        "width",
        "lineCap",
        "lineJoin",
        "dashes",
        "rect",
    )
    return [
        {key: normalize_drawing(item.get(key)) for key in keys if key in item}
        for item in drawings
    ]


def make_visual_evidence(after_details: dict) -> dict:
    before = np.array(Image.open(BASELINE_PNG).convert("RGB"))
    after_image = Image.open(AFTER_PNG).convert("RGB")
    after = np.array(after_image)
    difference = np.any(before != after, axis=2)

    allowed = np.zeros(difference.shape, dtype=bool)
    allowed_boxes: dict[str, list[int]] = {}
    for node_name, before_box, after_box in (
        (
            "INIT",
            [850, 770, 1270, 825],
            [865, 760, 1255, 815],
        ),
        (
            "EVALUATE",
            [880, 1935, 1240, 1988],
            [895, 1925, 1225, 1978],
        ),
    ):
        union = [
            min(before_box[0], after_box[0]) - 6,
            min(before_box[1], after_box[1]) - 6,
            max(before_box[2], after_box[2]) + 6,
            max(before_box[3], after_box[3]) + 6,
        ]
        allowed_boxes[node_name] = union
        allowed[union[1] : union[3], union[0] : union[2]] = True

    outside = difference & ~allowed
    overlay = after_image.copy()
    overlay_pixels = np.array(overlay)
    overlay_pixels[difference] = [255, 0, 255]
    overlay = Image.fromarray(overlay_pixels)
    draw = ImageDraw.Draw(overlay)
    colors = {"INIT": "#00a878", "EVALUATE": "#ff7f11"}
    for node_name, box in allowed_boxes.items():
        draw.rectangle(box, outline=colors[node_name], width=5)
        draw.text((box[0] + 8, box[1] + 8), node_name, fill=colors[node_name])
    overlay.save(ROOT / "strict_r4_raster_diff_overlay_300dpi.png", dpi=(300, 300))

    measurement_overlay = after_image.copy()
    draw = ImageDraw.Draw(measurement_overlay)
    for node_name, detail in after_details["nodes"].items():
        text_box = detail["text_ink_bbox_px"]
        draw.rectangle(text_box, outline="#00a878", width=4)
        for line_box in detail["line_ink_bboxes_px"]:
            draw.rectangle(line_box, outline="#00b7eb", width=3)
        draw.text((text_box[0], text_box[1] - 18), node_name, fill="#00a878")
    measurement_overlay.save(
        ROOT / "strict_r4_measurement_overlay_300dpi.png", dpi=(300, 300)
    )

    crops = {
        "INIT": (760, 690, 1380, 840),
        "EVALUATE": (760, 1850, 1380, 2000),
    }
    for node_name, box in crops.items():
        before_crop = Image.fromarray(before).crop(box)
        after_crop = after_image.crop(box)
        montage = Image.new("RGB", (before_crop.width * 2, before_crop.height + 24), "white")
        montage.paste(before_crop, (0, 24))
        montage.paste(after_crop, (before_crop.width, 24))
        caption = ImageDraw.Draw(montage)
        caption.text((8, 6), f"{node_name} BEFORE (R3)", fill="black")
        caption.text((before_crop.width + 8, 6), f"{node_name} AFTER (R4)", fill="black")
        montage.save(
            ROOT / "roi" / f"N_{node_name}_TEXT_BORDER_BOTTOM_BEFORE_AFTER_300DPI_1to1.png",
            dpi=(300, 300),
        )

    ys, xs = np.where(difference)
    diff_bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    return {
        "baseline_image_size": list(reversed(before.shape[:2])),
        "after_image_size": list(reversed(after.shape[:2])),
        "changed_pixel_count": int(difference.sum()),
        "changed_pixel_bbox_px": diff_bbox,
        "allowed_target_boxes_px": allowed_boxes,
        "changed_pixels_outside_target_boxes": int(outside.sum()),
    }


def foreground_edge_clearance(path: Path) -> int:
    image = np.array(Image.open(path).convert("RGB"), dtype=np.int16)
    foreground = np.any(np.abs(image - 255) >= 20, axis=2)
    ys, xs = np.where(foreground)
    height, width = foreground.shape
    return int(min(xs.min(), ys.min(), width - 1 - xs.max(), height - 1 - ys.max()))


def target_pixel_heights() -> list[dict]:
    with fitz.open(AFTER_PDF) as document:
        page = document[0]
        page_rect = fitz.Rect(page.rect)
        drawings = page.get_drawings()
        spans = flatten_spans(page)
    image = np.array(Image.open(AFTER_PNG).convert("RGB"))
    height, width = image.shape[:2]
    sx, sy = width / page_rect.width, height / page_rect.height

    node_spans: dict[str, list[dict]] = {}
    for node_name, drawing_id in (("INIT", 5), ("EVALUATE", 17)):
        rect = drawings[drawing_id - 1]["rect"]
        node_spans[node_name] = [
            span
            for span in spans
            if rect.x0 <= (span["bbox"][0] + span["bbox"][2]) / 2 <= rect.x1
            and rect.y0 <= (span["bbox"][1] + span["bbox"][3]) / 2 <= rect.y1
        ]

    def glyph_heights(
        selected_spans: list[dict], accepted: set[str], expected_size: float
    ) -> list[int]:
        values: list[int] = []
        for span in selected_spans:
            if abs(float(span.get("size", 0)) - expected_size) > 0.02:
                continue
            for char in span.get("chars", []):
                if char.get("c") not in accepted:
                    continue
                box = px_box_from_rect(fitz.Rect(char["bbox"]), sx, sy, 1)
                pixels = color_pixels(image, box, *TEXT)
                values.append(occupied_box(pixels)[3] - occupied_box(pixels)[1] + 1)
        return values

    specs = [
        ("E04-INIT-CJK-R4", "INIT", set("初始化有效样本前缀"), 9.5641, 30),
        ("E04-INIT-MATH-R4", "INIT", set("𝑚𝑎0𝑋∅"), 10.6600, 22),
        ("E04-INIT-SCRIPT-R4", "INIT", set("1𝑎"), 7.4620, 15),
        ("E14-EVALUATE-CJK-R4", "EVALUATE", set("求与"), 9.5641, 30),
        ("E14-EVALUATE-MATH-R4", "EVALUATE", set("𝑝𝑞𝑌𝜌𝑐"), 10.6600, 22),
    ]
    records: list[dict] = []
    for element_id, node_name, accepted, expected_size, threshold in specs:
        values = glyph_heights(node_spans[node_name], accepted, expected_size)
        median = float(np.median(values))
        records.append(
            {
                "ELEMENT_ID": element_id,
                "SELECTED_GLYPH_HEIGHTS_PX": ";".join(str(value) for value in values),
                "MEDIAN_H_INK_PX": f"{median:.1f}",
                "REQUIRED_MEDIAN_PX": threshold,
                "PASS_FAIL": "PASS" if median >= threshold else "FAIL",
            }
        )
    return records


def main() -> None:
    before_rows, before_details = measure_stage(
        "BEFORE", BEFORE_PDF, BEFORE_PNG, offset=1
    )
    after_rows, after_details = measure_stage(
        "AFTER", AFTER_PDF, AFTER_PNG, offset=0
    )
    standalone_rows, standalone_details = measure_stage(
        "AFTER_STANDALONE", STANDALONE_PDF, STANDALONE_PNG, offset=0
    )
    rows = before_rows + after_rows + standalone_rows
    csv_path = ROOT / "strict_r4_measurements.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    source_text = SOURCE.read_text(encoding="utf-8")
    state_nodes = len(re.findall(r"(?m)^\s*\\node\[", source_text))
    before_return_paths = source_text.split("\\draw[returnarr]", 1)[0]
    branch_labels = len(
        re.findall(r"node\[(?:edgeword|vedgeword(?:upper)?)", before_return_paths)
    )
    declared_fonts = Counter(
        re.findall(r"\\fontsize\{([0-9.]+pt)\}", source_text)
    )
    geometry_before = drawing_signature(BASELINE_PDF)
    geometry_after = drawing_signature(AFTER_PDF)
    visual = make_visual_evidence(after_details)
    pixel_height_rows = target_pixel_heights()
    with (ROOT / "strict_r4_target_pixel_heights.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pixel_height_rows[0]))
        writer.writeheader()
        writer.writerows(pixel_height_rows)

    after_failures = [
        f"{row['STAGE']}:{row['CHECK_ID']}"
        for row in after_rows + standalone_rows
        if row["PASS_FAIL"] != "PASS"
    ]
    summary = {
        "candidate": "FIG-P578-01-SA2-STRICT-R4",
        "result": "FIXED" if not after_failures else "NOT_FIXED",
        "rendering": {
            "dpi": 300,
            "resampled": False,
            "page_png": AFTER_PNG.name,
            "standalone_png": "candidate_standalone_300dpi.png",
            "page_edge_clearance_px": foreground_edge_clearance(AFTER_PNG),
            "baseline_page_edge_clearance_px": foreground_edge_clearance(BASELINE_PNG),
        },
        "source_static": {
            "state_node_count": state_nodes,
            "branch_label_count": branch_labels,
            "declared_font_occurrences": dict(declared_fonts),
            "whole_figure_scale_commands": len(
                re.findall(r"\\(?:resizebox|scalebox)\b", source_text)
            ),
        },
        "vector_regression": {
            "baseline_drawing_count": len(geometry_before),
            "after_drawing_count": len(geometry_after),
            "all_drawing_geometry_and_styles_identical": geometry_before == geometry_after,
        },
        "raster_regression": visual,
        "target_pixel_height_regression": pixel_height_rows,
        "before": before_details,
        "after": after_details,
        "after_standalone": standalone_details,
        "after_failures": after_failures,
    }
    (ROOT / "strict_r4_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
