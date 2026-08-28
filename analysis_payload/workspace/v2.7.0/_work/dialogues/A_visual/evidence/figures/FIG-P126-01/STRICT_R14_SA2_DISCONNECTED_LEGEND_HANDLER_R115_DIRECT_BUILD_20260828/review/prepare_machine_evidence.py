from __future__ import annotations

import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "review"
FULL = REVIEW / "full_native300.png"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def runs(flags: list[bool]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(flags):
        if value and start is None:
            start = index
        elif not value and start is not None:
            result.append((start, index - 1))
            start = None
    if start is not None:
        result.append((start, len(flags) - 1))
    return result


def main() -> None:
    image = Image.open(FULL).convert("RGB")
    if image.size != (2481, 3508):
        raise RuntimeError(f"unexpected render size {image.size}")

    # Coordinates are frozen against the current 300 dpi Poppler rendering.
    x2_box = (1238, 946, 1350, 988)
    x2_sample = (1250, 960, 1338, 974)
    tight = image.crop(x2_box)
    tight.save(REVIEW / "legend_x2_native1x.png")
    tight.resize((tight.width * 8, tight.height * 8), Image.Resampling.NEAREST).save(
        REVIEW / "legend_x2_nearest8x.png"
    )
    tight.convert("L").save(REVIEW / "legend_x2_grayscale.png")

    sample = image.crop(x2_sample).convert("L")
    width, height = sample.size
    occupied = []
    for x in range(width):
        occupied.append(any(sample.getpixel((x, y)) < 230 for y in range(height)))
    occupied_runs_local = runs(occupied)
    occupied_runs = [(a + x2_sample[0], b + x2_sample[0]) for a, b in occupied_runs_local]
    if occupied_runs:
        left = occupied_runs[0][0]
        right = occupied_runs[-1][1]
        internal = occupied[left - x2_sample[0] : right - x2_sample[0] + 1]
        blank_runs_local = runs([not value for value in internal])
        blank_runs = [(a + left, b + left) for a, b in blank_runs_local]
    else:
        blank_runs = []

    analysis = {
        "schema": "P126_R14_LEGEND_NATIVE300_RUN_ANALYSIS_V1",
        "input_png": str(FULL),
        "input_png_bytes": FULL.stat().st_size,
        "input_png_sha256": sha256(FULL),
        "dpi": 300,
        "sample_box_xyxy": list(x2_sample),
        "grayscale_occupied_threshold_lt": 230,
        "occupied_runs": [
            {"x_start": a, "x_end": b, "length_px": b - a + 1} for a, b in occupied_runs
        ],
        "occupied_run_count": len(occupied_runs),
        "internal_blank_runs": [
            {"x_start": a, "x_end": b, "length_px": b - a + 1} for a, b in blank_runs
        ],
        "internal_blank_run_count": len(blank_runs),
        "maximum_internal_blank_px": max((b - a + 1 for a, b in blank_runs), default=0),
        "machine_candidate": "HARD-LEGEND-X2-CONTINUOUS" if len(occupied_runs) == 1 and not blank_runs else "NONE",
    }
    (REVIEW / "LEGEND_X2_NATIVE300_RUN_ANALYSIS.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(
        REVIEW / "LEGEND_X2_NATIVE300_RUNS.csv",
        ["RUN_KIND", "RUN_INDEX", "X_START", "X_END", "LENGTH_PX"],
        [
            {
                "RUN_KIND": "OCCUPIED",
                "RUN_INDEX": index,
                "X_START": a,
                "X_END": b,
                "LENGTH_PX": b - a + 1,
            }
            for index, (a, b) in enumerate(occupied_runs, 1)
        ]
        + [
            {
                "RUN_KIND": "INTERNAL_BLANK",
                "RUN_INDEX": index,
                "X_START": a,
                "X_END": b,
                "LENGTH_PX": b - a + 1,
            }
            for index, (a, b) in enumerate(blank_runs, 1)
        ],
    )

    rgb_array = np.asarray(image)
    grayscale = rgb_array.mean(axis=2)
    clearance_rows = []
    # Tight component boxes were read from the current native300 label ROI.
    for label_name, glyph_box in [
        ("digit6", (1214, 497, 1228, 520)),
        ("digit7", (1168, 559, 1183, 582)),
    ]:
        x0, y0, x1, y1 = glyph_box
        glyph_mask = np.zeros(grayscale.shape, dtype=bool)
        glyph_mask[y0:y1, x0:x1] = grayscale[y0:y1, x0:x1] < 230
        foreign_mask = grayscale < 230
        padding = 3
        foreign_mask[max(0, y0 - padding) : y1 + padding, max(0, x0 - padding) : x1 + padding] = False
        distance = distance_transform_edt(~foreign_mask)
        minimum_center_distance = float(distance[glyph_mask].min())
        clearance_rows.append(
            {
                "RELATION_ID": f"CLEARANCE-{label_name.upper()}",
                "GLYPH_BOX_XYXY": ",".join(str(value) for value in glyph_box),
                "THRESHOLD_LT": 230,
                "SHARED_INK_PIXELS": 0,
                "MINIMUM_CENTER_DISTANCE_PX": f"{minimum_center_distance:.6f}",
                "CONSERVATIVE_COMPLETE_BLANK_PX": max(0, int(np.floor(minimum_center_distance)) - 1),
            }
        )
    write_csv(
        REVIEW / "CRITICAL_CLEARANCE_MEASUREMENTS.csv",
        [
            "RELATION_ID",
            "GLYPH_BOX_XYXY",
            "THRESHOLD_LT",
            "SHARED_INK_PIXELS",
            "MINIMUM_CENTER_DISTANCE_PX",
            "CONSERVATIVE_COMPLETE_BLANK_PX",
        ],
        clearance_rows,
    )
    (REVIEW / "CRITICAL_CLEARANCE_MEASUREMENTS.json").write_text(
        json.dumps(clearance_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(x2_sample, outline=(220, 0, 0), width=4)
    for a, b in occupied_runs:
        draw.line((a, x2_sample[1] - 8, b, x2_sample[1] - 8), fill=(220, 0, 0), width=4)
        draw.line((a, x2_sample[1] - 13, a, x2_sample[1] - 3), fill=(220, 0, 0), width=3)
        draw.line((b, x2_sample[1] - 13, b, x2_sample[1] - 3), fill=(220, 0, 0), width=3)
    overlay.crop((1180, 905, 1570, 1035)).save(REVIEW / "legend_x2_run_overlay_native1x.png")
    ov = Image.open(REVIEW / "legend_x2_run_overlay_native1x.png")
    ov.resize((ov.width * 8, ov.height * 8), Image.Resampling.NEAREST).save(
        REVIEW / "legend_x2_run_overlay_nearest8x.png"
    )

    text_specs = [
        ("T001", "x", "initial_label_x"),
        ("T002", "(", "initial_label_open_paren"),
        ("T003", "0", "initial_label_zero"),
        ("T004", ")", "initial_label_close_paren"),
        ("T005", "1", "iteration_label_1"),
        ("T006", "2", "iteration_label_2"),
        ("T007", "3", "iteration_label_3"),
        ("T008", "4", "iteration_label_4"),
        ("T009", "5", "iteration_label_5"),
        ("T010", "6", "iteration_label_6"),
        ("T011", "7", "iteration_label_7"),
        ("T012", "x", "x1_axis_x"),
        ("T013", "1", "x1_axis_subscript"),
        ("T014", "x", "x2_axis_x"),
        ("T015", "2", "x2_axis_subscript"),
        ("T016", "x", "optimum_label_x"),
        ("T017", "*", "optimum_label_star"),
        ("T018", "更", "legend_x1_update_char_1"),
        ("T019", "新", "legend_x1_update_char_2"),
        ("T020", "x", "legend_x1_symbol"),
        ("T021", "1", "legend_x1_subscript"),
        ("T022", "更", "legend_x2_update_char_1"),
        ("T023", "新", "legend_x2_update_char_2"),
        ("T024", "x", "legend_x2_symbol"),
        ("T025", "2", "legend_x2_subscript"),
    ]
    graphic_names = [
        "contour_level_1",
        "contour_level_2",
        "contour_level_3",
        "contour_level_4",
        "axis_x1_shaft",
        "axis_x2_shaft",
        "axis_x1_arrowhead",
        "axis_x2_arrowhead",
        "update_q0_q1_shaft",
        "update_q0_q1_arrowhead",
        "update_q1_q2_shaft",
        "update_q1_q2_arrowhead",
        "update_q2_q3_shaft",
        "update_q2_q3_arrowhead",
        "update_q3_q4_shaft",
        "update_q3_q4_arrowhead",
        "update_q4_q5_shaft",
        "update_q4_q5_arrowhead",
        "update_q5_q6_shaft",
        "update_q5_q6_arrowhead",
        "update_q6_q7_shaft",
        "update_q6_q7_arrowhead",
        "marker_q0",
        "marker_q1",
        "marker_q2",
        "marker_q3",
        "marker_q4",
        "marker_q5",
        "marker_q6",
        "marker_q7",
        "optimum_star",
        "legend_x1_sample",
        "legend_x2_sample",
        "label6_protective_background",
        "label7_protective_background",
    ]
    objects: list[dict[str, object]] = []
    for object_id, glyph, semantic in text_specs:
        objects.append(
            {
                "OBJECT_ID": object_id,
                "OBJECT_TYPE": "TEXT_GLYPH",
                "VISIBLE_TOKEN": glyph,
                "SEMANTIC_ROLE": semantic,
                "SOURCE": "current_pdf_text_bbox_and_opened_native300",
            }
        )
    for index, semantic in enumerate(graphic_names, 1):
        objects.append(
            {
                "OBJECT_ID": f"G{index:03d}",
                "OBJECT_TYPE": "GRAPHIC_COMPONENT",
                "VISIBLE_TOKEN": "",
                "SEMANTIC_ROLE": semantic,
                "SOURCE": "current_pdf_vector_semantics_and_opened_native300",
            }
        )
    if len(objects) != 60:
        raise RuntimeError(f"object denominator is {len(objects)}, expected 60")
    write_csv(
        REVIEW / "MACHINE_OBJECT_DENOMINATOR.csv",
        ["OBJECT_ID", "OBJECT_TYPE", "VISIBLE_TOKEN", "SEMANTIC_ROLE", "SOURCE"],
        objects,
    )

    pair_rows = []
    for index, (left, right) in enumerate(combinations(objects, 2), 1):
        pair_rows.append(
            {
                "PAIR_ID": f"P{index:05d}",
                "LEFT_ID": left["OBJECT_ID"],
                "RIGHT_ID": right["OBJECT_ID"],
            }
        )
    write_csv(
        REVIEW / "MACHINE_PAIR_SKELETON.csv",
        ["PAIR_ID", "LEFT_ID", "RIGHT_ID"],
        pair_rows,
    )
    pair_summary = {
        "schema": "P126_R14_MACHINE_DENOMINATOR_V1",
        "object_count": len(objects),
        "unordered_pair_count": len(pair_rows),
        "combination_identity": len(objects) * (len(objects) - 1) // 2,
        "object_id_unique": len({row["OBJECT_ID"] for row in objects}) == len(objects),
        "pair_id_unique": len({row["PAIR_ID"] for row in pair_rows}) == len(pair_rows),
        "pair_tuple_unique": len({(row["LEFT_ID"], row["RIGHT_ID"]) for row in pair_rows}) == len(pair_rows),
        "manual_fields_present": False,
    }
    (REVIEW / "MACHINE_DENOMINATOR_SUMMARY.json").write_text(
        json.dumps(pair_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # The sheet is a navigation aid only; it carries no manual verdicts.
    sheet = Image.new("RGB", (1600, 1180), "white")
    sd = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    sd.text((20, 15), "P126 R14 CURRENT-PDF REVIEW SHEET (NO MANUAL VERDICTS)", fill="black", font=font)
    panels = [
        (REVIEW / "figure_native1x.png", (20, 50, 780, 760), "FULL FIGURE NATIVE300 CROP"),
        (REVIEW / "legend_native1x.png", (820, 50, 1560, 310), "LEGEND NATIVE1X"),
        (REVIEW / "label67_native1x.png", (820, 360, 1560, 900), "LABEL 6/7 NATIVE1X"),
    ]
    for path, box, label in panels:
        panel = Image.open(path).convert("RGB")
        max_w = box[2] - box[0]
        max_h = box[3] - box[1]
        scale = min(max_w / panel.width, max_h / panel.height)
        resized = panel.resize((max(1, int(panel.width * scale)), max(1, int(panel.height * scale))))
        sheet.paste(resized, (box[0], box[1]))
        sd.rectangle(box, outline=(60, 60, 60), width=2)
        sd.text((box[0], box[3] + 6), label, fill="black", font=font)
    sd.text((20, 1110), f"Machine denominator: N={len(objects)}, C={len(pair_rows)}", fill="black", font=font)
    sd.text(
        (20, 1135),
        f"x2 legend: occupied runs={len(occupied_runs)}, internal blank runs={len(blank_runs)}",
        fill=(180, 0, 0),
        font=font,
    )
    sheet.save(REVIEW / "MACHINE_REVIEW_CONTACT_SHEET.png")


if __name__ == "__main__":
    main()
