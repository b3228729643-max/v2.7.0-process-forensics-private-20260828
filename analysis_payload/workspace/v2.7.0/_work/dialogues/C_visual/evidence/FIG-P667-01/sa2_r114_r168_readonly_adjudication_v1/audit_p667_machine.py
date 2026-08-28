from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont


HANDOFF_ID = "C-FIG-P667-01-R114-SA2-R168-READONLY-ADJUDICATION-V1"
UID = "FIG-P667-01"
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa2_r114_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_conjugate_update.tex")
EXPECTED = {
    "pdf_bytes": 4967122,
    "pdf_sha256": "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6",
    "source_bytes": 3252,
    "source_sha256": "1E2D755428EC466C6DF44B7684B81A354352653AE60476B4F717AD19F9D6CE15",
}
SCALE = 300.0 / 72.0
TARGET_PHYSICAL_PAGE = 714
FIGURE_CROP_PT = (70.0, 315.0, 525.0, 610.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pt_box_to_px(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, top, x1, bottom = box
    return (
        math.floor(x0 * SCALE),
        math.floor(top * SCALE),
        math.ceil(x1 * SCALE),
        math.ceil(bottom * SCALE),
    )


def crop_page(page_image: Image.Image, box_pt: tuple[float, float, float, float]) -> Image.Image:
    return page_image.crop(pt_box_to_px(box_pt))


def normalize_pdf_text(text: str) -> str:
    return "".join(text.replace("\r", "").replace("\n", "").split())


OBJECTS = [
    dict(object_id="T01", kind="TEXT", role="ROW_HEADING", panel="MAIN", source_line="16", declared_pt="10.0", bbox=(102.23, 346.42, 132.12, 356.38), text="先验核"),
    dict(object_id="T02", kind="FORMULA", role="KERNEL_FORMULA", panel="MAIN", source_line="18-19", declared_pt="9.4", bbox=(203.03, 336.86, 302.22, 363.62), text="p(θ|α)∝∏ᵢθᵢ^(αᵢ−1)"),
    dict(object_id="T03", kind="TEXT", role="UNDERBRACE_LABEL", panel="MAIN", source_line="19", declared_pt="8.5", bbox=(266.73, 347.40, 300.60, 355.87), text="先验指数"),
    dict(object_id="T04", kind="TEXT", role="ROW_HEADING", panel="MAIN", source_line="16", declared_pt="10.0", bbox=(102.23, 412.02, 132.12, 421.98), text="似然核"),
    dict(object_id="T05", kind="FORMULA", role="KERNEL_FORMULA", panel="MAIN", source_line="20-21", declared_pt="9.4", bbox=(211.99, 402.00, 291.64, 428.76), text="p(n|θ)∝∏ᵢθᵢ^nᵢ"),
    dict(object_id="T06", kind="TEXT", role="UNDERBRACE_LABEL", panel="MAIN", source_line="21", declared_pt="8.5", bbox=(274.70, 412.54, 291.64, 421.01), text="计数"),
    dict(object_id="T07", kind="TEXT", role="ROW_HEADING", panel="MAIN", source_line="16", declared_pt="10.0", bbox=(102.23, 477.61, 132.12, 487.57), text="后验核"),
    dict(object_id="T08", kind="FORMULA", role="KERNEL_FORMULA", panel="MAIN", source_line="22-23", declared_pt="9.4", bbox=(194.25, 467.59, 309.38, 495.27), text="p(θ|n,α)∝∏ᵢθᵢ^(αᵢ+nᵢ−1)"),
    dict(object_id="T09", kind="TEXT", role="UNDERBRACE_LABEL", panel="MAIN", source_line="23", declared_pt="8.5", bbox=(267.04, 479.05, 309.38, 487.52), text="逐分量相加"),
    dict(object_id="T10", kind="TEXT", role="OPERATOR", panel="MAIN", source_line="25-26", declared_pt="15.0", bbox=(247.72, 374.99, 258.48, 389.93), text="×"),
    dict(object_id="T11", kind="TEXT", role="BRACE_LABEL", panel="MAIN", source_line="29-30", declared_pt="8.8", bbox=(368.67, 379.47, 430.04, 388.23), text="指数逐分量相加"),
    dict(object_id="T12", kind="FORMULA", role="POSTERIOR_RESULT", panel="MAIN", source_line="31-34", declared_pt="9.4", bbox=(431.87, 470.54, 483.32, 491.28), text="θ|n; ∼Dir(α+n)"),
    dict(object_id="T13", kind="FORMULA", role="MARGINAL_FORMULA", panel="MAIN", source_line="36-39", declared_pt="8.8", bbox=(403.59, 538.23, 510.41, 561.83), text="p(n|α)=N!/∏ᵢnᵢ! · B(α+n)/B(α)"),
    dict(object_id="T14", kind="TEXT", role="MARGINAL_LABEL", panel="MAIN", source_line="39", declared_pt="8.8", bbox=(426.91, 562.75, 488.28, 571.52), text="保留归一化常数"),
    dict(object_id="T15", kind="CAPTION", role="CAPTION", panel="PAGE", source_line="43", declared_pt="10.0", bbox=(87.48, 576.95, 519.14, 600.64), text="图34.7 Dirichlet–多项共轭…边缘分布"),
    dict(object_id="G01", kind="GRAPHIC", role="STRIP_BORDER", panel="MAIN", source_line="9-10", declared_pt="", bbox=(155.31, 328.47, 350.90, 370.99), text="先验核容器边框"),
    dict(object_id="G02", kind="GRAPHIC", role="STRIP_BORDER", panel="MAIN", source_line="9-10", declared_pt="", bbox=(155.31, 394.06, 350.90, 436.58), text="似然核容器边框"),
    dict(object_id="G03", kind="GRAPHIC", role="STRIP_BORDER", panel="MAIN", source_line="9-10", declared_pt="", bbox=(155.31, 459.66, 350.90, 502.18), text="后验核容器边框"),
    dict(object_id="G04", kind="GRAPHIC", role="BRACE", panel="MAIN", source_line="27-30", declared_pt="", bbox=(358.95, 328.27, 362.44, 436.78), text="先验与似然合并括号"),
    dict(object_id="G05", kind="GRAPHIC", role="MAIN_ARROW", panel="MAIN", source_line="35", declared_pt="", bbox=(351.10, 479.49, 402.12, 482.35), text="后验核到后验分布"),
    dict(object_id="G06", kind="GRAPHIC", role="RESULT_NODE_BORDER", panel="MAIN", source_line="31-34", declared_pt="", bbox=(403.74, 461.08, 511.46, 500.76), text="后验分布结论框"),
    dict(object_id="G07", kind="GRAPHIC", role="BRANCH_ARROW", panel="MAIN", source_line="40", declared_pt="", bbox=(456.20, 500.76, 459.00, 531.79), text="后验结论到边际分布"),
]


ROIS = [
    ("R01_low_annotations", (245.0, 328.0, 315.0, 432.0), "8.5pt underbrace labels and multiplication"),
    ("R02_posterior_flow", (185.0, 452.0, 515.0, 505.0), "posterior row, main arrow, and result node"),
    ("R03_marginal_clearance", (395.0, 530.0, 515.0, 575.0), "branch arrow, marginal formula, and label clearance"),
    ("R04_caption_left", (80.0, 572.0, 310.0, 605.0), "caption label and first line"),
    ("R05_caption_right", (300.0, 572.0, 525.0, 605.0), "caption continuation and second line"),
    ("R06_qed_square", (520.0, 205.0, 545.0, 235.0), "proof-ending hollow square outside figure; distinguish from tofu"),
]


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("This fixed audit accepts no arguments.")
    if not ROOT.is_dir():
        raise SystemExit("Required evidence root is missing.")

    write_text(
        ROOT / "M00_startup_absence_gate.txt",
        "\n".join(
            [
                f"HANDOFF_ID={HANDOFF_ID}",
                f"UID={UID}",
                f"EXACT_ROOT={ROOT}",
                "PRE_WRITE_TEST_PATH_LEAF=False",
                "PRE_WRITE_TEST_PATH_CONTAINER=False",
                "PRE_WRITE_TEST_PATH_ANY=False",
                "ROOT_CREATION_COUNT=1",
                "RECORD_BASIS=independent PowerShell Test-Path output observed before any artifact write",
                "",
            ]
        ),
    )

    identity = {
        "handoff_id": HANDOFF_ID,
        "uid": UID,
        "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
        "source": {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)},
        "expected": EXPECTED,
    }
    if identity["pdf"]["bytes"] != EXPECTED["pdf_bytes"] or identity["pdf"]["sha256"] != EXPECTED["pdf_sha256"]:
        raise SystemExit("PDF identity mismatch")
    if identity["source"]["bytes"] != EXPECTED["source_bytes"] or identity["source"]["sha256"] != EXPECTED["source_sha256"]:
        raise SystemExit("source identity mismatch")
    write_json(ROOT / "M02_input_identity.json", identity)

    document = pdfium.PdfDocument(str(PDF))
    needle = "保留归一化常数还可得到Dirichlet–多项边缘分布"
    hits: list[int] = []
    for index, page in enumerate(document):
        text = normalize_pdf_text(page.get_textpage().get_text_range())
        if needle in text:
            hits.append(index + 1)
    if hits != [TARGET_PHYSICAL_PAGE]:
        raise SystemExit(f"target caption location is not unique: {hits}")

    target_page = document[TARGET_PHYSICAL_PAGE - 1]
    raw_text = target_page.get_textpage().get_text_range()
    normalized = normalize_pdf_text(raw_text)
    required_tokens = [
        "先验核",
        "似然核",
        "后验核",
        "先验指数",
        "计数",
        "逐分量相加",
        "指数逐分量相加",
        "保留归一化常数",
        "Dir(𝜶+𝒏)",
    ]
    token_occurrences = {token: normalized.count(normalize_pdf_text(token)) for token in required_tokens}
    write_json(
        ROOT / "M03_pdf_location.json",
        {
            "caption_search_needle": needle,
            "matching_physical_pages": hits,
            "physical_page": TARGET_PHYSICAL_PAGE,
            "printed_page": 701,
            "section_header": "34.5 Dirichlet–多项共轭",
            "page_count": len(document),
            "required_token_occurrences": token_occurrences,
        },
    )
    write_text(ROOT / "M04_page714_text_extract.txt", raw_text)

    page_image = target_page.render(scale=SCALE).to_pil().convert("RGB")
    page_image.save(ROOT / "M01_full_page_p714_300dpi.png", dpi=(300, 300), optimize=True)
    figure = crop_page(page_image, FIGURE_CROP_PT)
    figure.save(ROOT / "M05_figure_caption_native300dpi.png", dpi=(300, 300), optimize=True)
    grayscale = figure.convert("L")
    grayscale.save(ROOT / "M06_figure_caption_grayscale_native300dpi.png", dpi=(300, 300), optimize=True)

    crop_x0_px, crop_y0_px, _, _ = pt_box_to_px(FIGURE_CROP_PT)
    object_rows: list[dict] = []
    measurement_rows: list[dict] = []
    page_gray = np.asarray(page_image.convert("L"))
    for obj in OBJECTS:
        x0, top, x1, bottom = obj["bbox"]
        px = pt_box_to_px(obj["bbox"])
        local = page_gray[px[1] : px[3], px[0] : px[2]]
        ink = local < 200
        ys, xs = np.where(ink)
        ink_height = int(ys.max() - ys.min() + 1) if ys.size else 0
        ink_width = int(xs.max() - xs.min() + 1) if xs.size else 0
        row = {
            "object_id": obj["object_id"],
            "kind": obj["kind"],
            "role": obj["role"],
            "panel": obj["panel"],
            "source_line": obj["source_line"],
            "declared_pt": obj["declared_pt"],
            "graphics_scale": "1.000",
            "text": obj["text"],
            "bbox_x0_pt": f"{x0:.2f}",
            "bbox_top_pt": f"{top:.2f}",
            "bbox_x1_pt": f"{x1:.2f}",
            "bbox_bottom_pt": f"{bottom:.2f}",
            "bbox_x0_px": px[0],
            "bbox_top_px": px[1],
            "bbox_x1_px": px[2],
            "bbox_bottom_px": px[3],
        }
        object_rows.append(row)
        measurement_rows.append(
            {
                "object_id": obj["object_id"],
                "kind": obj["kind"],
                "role": obj["role"],
                "threshold_gray_lt": 200,
                "bbox_width_px": px[2] - px[0],
                "bbox_height_px": px[3] - px[1],
                "foreground_pixel_count": int(ink.sum()),
                "foreground_ink_width_px": ink_width,
                "foreground_ink_height_px": ink_height,
            }
        )
    write_csv(ROOT / "M07_object_denominator.csv", object_rows, list(object_rows[0].keys()))
    write_csv(ROOT / "M08_pixel_measurements_machine.csv", measurement_rows, list(measurement_rows[0].keys()))

    pair_rows: list[dict] = []
    for pair_index, (left, right) in enumerate(itertools.combinations(OBJECTS, 2), 1):
        ax0, ay0, ax1, ay1 = left["bbox"]
        bx0, by0, bx1, by1 = right["bbox"]
        dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
        dy = max(0.0, max(ay0, by0) - min(ay1, by1))
        gap_px = math.hypot(dx, dy) * SCALE
        ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
        if ix1 > ix0 and iy1 > iy0:
            relation = "BBOX_INTERSECTION"
            ipx = pt_box_to_px((ix0, iy0, ix1, iy1))
            intersection_ink = int((page_gray[ipx[1] : ipx[3], ipx[0] : ipx[2]] < 200).sum())
            area_px2 = (ix1 - ix0) * SCALE * (iy1 - iy0) * SCALE
        else:
            relation = "BBOX_DISJOINT"
            intersection_ink = 0
            area_px2 = 0.0
        pair_rows.append(
            {
                "pair_id": f"P{pair_index:03d}",
                "left_id": left["object_id"],
                "right_id": right["object_id"],
                "relation_code": relation,
                "bbox_min_gap_px": f"{gap_px:.3f}",
                "bbox_intersection_area_px2": f"{area_px2:.3f}",
                "intersection_foreground_px": intersection_ink,
            }
        )
    expected_pairs = len(OBJECTS) * (len(OBJECTS) - 1) // 2
    if len(pair_rows) != expected_pairs:
        raise SystemExit("unordered pair denominator mismatch")
    write_csv(ROOT / "M09_all_unordered_pairs.csv", pair_rows, list(pair_rows[0].keys()))
    write_json(
        ROOT / "M10_pair_summary.json",
        {
            "object_count": len(OBJECTS),
            "expected_unordered_pairs": expected_pairs,
            "enumerated_unordered_pairs": len(pair_rows),
            "bbox_intersection_pairs": sum(r["relation_code"] == "BBOX_INTERSECTION" for r in pair_rows),
            "intersection_foreground_nonzero_pairs": sum(int(r["intersection_foreground_px"]) > 0 for r in pair_rows),
        },
    )

    overlay = figure.copy()
    draw = ImageDraw.Draw(overlay)
    colors = {"TEXT": "#d62728", "FORMULA": "#2ca02c", "CAPTION": "#9467bd", "GRAPHIC": "#1f77b4"}
    try:
        label_font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        label_font = ImageFont.load_default()
    for obj in OBJECTS:
        px = pt_box_to_px(obj["bbox"])
        local_box = (px[0] - crop_x0_px, px[1] - crop_y0_px, px[2] - crop_x0_px, px[3] - crop_y0_px)
        color = colors[obj["kind"]]
        draw.rectangle(local_box, outline=color, width=3)
        draw.text((local_box[0] + 2, max(0, local_box[1] - 20)), obj["object_id"], fill=color, font=label_font)
    overlay.save(ROOT / "M11_object_bbox_overlay_native300dpi.png", dpi=(300, 300), optimize=True)

    figure_array = np.asarray(figure.convert("L"))
    visible_ink = (figure_array < 200).astype(np.uint8) * 255
    nonwhite_structure = (figure_array < 245).astype(np.uint8) * 255
    Image.fromarray(visible_ink, mode="L").save(ROOT / "M12_visible_ink_mask_gray_lt200.png", optimize=True)
    Image.fromarray(nonwhite_structure, mode="L").save(ROOT / "M13_nonwhite_structure_mask_gray_lt245.png", optimize=True)

    vector_rows: list[dict] = []
    with pdfplumber.open(str(PDF)) as plumb:
        page = plumb.pages[TARGET_PHYSICAL_PAGE - 1]
        vector_index = 0
        for vector_type, items in (("line", page.lines), ("curve", page.curves), ("rect", page.rects)):
            for item in items:
                if item.get("x1", 0) < FIGURE_CROP_PT[0] or item.get("x0", 0) > FIGURE_CROP_PT[2]:
                    continue
                if item.get("bottom", 0) < FIGURE_CROP_PT[1] or item.get("top", 0) > FIGURE_CROP_PT[3]:
                    continue
                vector_index += 1
                vector_rows.append(
                    {
                        "vector_id": f"V{vector_index:03d}",
                        "vector_type": vector_type,
                        "x0_pt": f"{item.get('x0', 0):.3f}",
                        "top_pt": f"{item.get('top', 0):.3f}",
                        "x1_pt": f"{item.get('x1', 0):.3f}",
                        "bottom_pt": f"{item.get('bottom', 0):.3f}",
                        "linewidth_pt": f"{item.get('linewidth', 0):.3f}",
                        "stroking_color": repr(item.get("stroking_color")),
                        "non_stroking_color": repr(item.get("non_stroking_color")),
                    }
                )
        write_csv(ROOT / "M14_pdf_vector_inventory.csv", vector_rows, list(vector_rows[0].keys()))

        codepoint_rows: list[dict] = []
        char_index = 0
        for char in page.chars:
            if char["x1"] < FIGURE_CROP_PT[0] or char["x0"] > FIGURE_CROP_PT[2]:
                continue
            if char["bottom"] < FIGURE_CROP_PT[1] or char["top"] > FIGURE_CROP_PT[3]:
                continue
            for codepoint in char["text"]:
                char_index += 1
                codepoint_rows.append(
                    {
                        "occurrence_id": f"C{char_index:04d}",
                        "character": codepoint,
                        "codepoint": f"U+{ord(codepoint):04X}",
                        "unicode_name": unicodedata.name(codepoint, "UNNAMED"),
                        "x0_pt": f"{char['x0']:.3f}",
                        "top_pt": f"{char['top']:.3f}",
                        "x1_pt": f"{char['x1']:.3f}",
                        "bottom_pt": f"{char['bottom']:.3f}",
                        "fontname": char["fontname"],
                        "size_pt_pdf": f"{char['size']:.3f}",
                    }
                )
        write_csv(ROOT / "M15_codepoint_inventory.csv", codepoint_rows, list(codepoint_rows[0].keys()))
        suspicious = [r for r in codepoint_rows if r["codepoint"] in {"U+0000", "U+FFFD"}]
        write_json(
            ROOT / "M16_codepoint_summary.json",
            {
                "occurrence_count": len(codepoint_rows),
                "unique_codepoint_count": len({r["codepoint"] for r in codepoint_rows}),
                "u_fffd_occurrences": sum(r["codepoint"] == "U+FFFD" for r in codepoint_rows),
                "u_0000_occurrences": sum(r["codepoint"] == "U+0000" for r in codepoint_rows),
                "suspicious_rows": suspicious,
                "required_token_occurrences": token_occurrences,
            },
        )

    crop_edge_count = int(visible_ink[0, :].sum() // 255 + visible_ink[-1, :].sum() // 255 + visible_ink[:, 0].sum() // 255 + visible_ink[:, -1].sum() // 255)
    object_crop_margins = []
    for obj in OBJECTS:
        x0, top, x1, bottom = obj["bbox"]
        margins_px = [
            (x0 - FIGURE_CROP_PT[0]) * SCALE,
            (top - FIGURE_CROP_PT[1]) * SCALE,
            (FIGURE_CROP_PT[2] - x1) * SCALE,
            (FIGURE_CROP_PT[3] - bottom) * SCALE,
        ]
        object_crop_margins.append({"object_id": obj["object_id"], "min_crop_margin_px": round(min(margins_px), 3)})
    write_json(
        ROOT / "M17_clip_geometry_check.json",
        {
            "figure_crop_pt": FIGURE_CROP_PT,
            "figure_crop_px": pt_box_to_px(FIGURE_CROP_PT),
            "crop_edge_foreground_pixel_count_gray_lt200": crop_edge_count,
            "objects_crossing_crop_boundary_count": sum(r["min_crop_margin_px"] < 0 for r in object_crop_margins),
            "minimum_object_to_crop_margin_px": min(r["min_crop_margin_px"] for r in object_crop_margins),
            "object_crop_margins": object_crop_margins,
        },
    )

    roi_rows = []
    for roi_id, roi_box, purpose in ROIS:
        native = crop_page(page_image, roi_box)
        native_name = f"{roi_id}_native1x_300dpi.png"
        zoom_name = f"{roi_id}_nearest8x.png"
        native.save(ROOT / native_name, dpi=(300, 300), optimize=True)
        zoom = native.resize((native.width * 8, native.height * 8), resample=Image.Resampling.NEAREST)
        zoom.save(ROOT / zoom_name, optimize=True)
        roi_rows.append(
            {
                "roi_id": roi_id,
                "purpose": purpose,
                "bbox_pt": repr(roi_box),
                "native_file": native_name,
                "native_width_px": native.width,
                "native_height_px": native.height,
                "zoom_file": zoom_name,
                "zoom_width_px": zoom.width,
                "zoom_height_px": zoom.height,
                "zoom_resampling": "NEAREST",
            }
        )
    write_csv(ROOT / "M18_decisive_roi_index.csv", roi_rows, list(roi_rows[0].keys()))

    source_rows = [
        {"object_id": "T01/T04/T07", "source_line": "16", "source_declaration": "\\bfseries\\small", "declared_or_effective_pt": "10.0", "r168_category": "not-low"},
        {"object_id": "T02/T05/T08", "source_line": "3,8,18-23", "source_declaration": "\\fontsize{9.4pt}{11.3pt}", "declared_or_effective_pt": "9.4", "r168_category": "advisory-low"},
        {"object_id": "T03/T06/T09", "source_line": "19,21,23", "source_declaration": "\\fontsize{8.5pt}{10.2pt}", "declared_or_effective_pt": "8.5", "r168_category": "advisory-low"},
        {"object_id": "T10", "source_line": "25", "source_declaration": "\\fontsize{15pt}{18pt}", "declared_or_effective_pt": "15.0", "r168_category": "intentional-operator"},
        {"object_id": "T11/T13/T14", "source_line": "29,36", "source_declaration": "\\fontsize{8.8pt}{10.6pt}", "declared_or_effective_pt": "8.8", "r168_category": "advisory-low"},
        {"object_id": "T12", "source_line": "33", "source_declaration": "\\fontsize{9.4pt}{11.3pt}", "declared_or_effective_pt": "9.4", "r168_category": "advisory-low"},
        {"object_id": "T15", "source_line": "43", "source_declaration": "document caption font", "declared_or_effective_pt": "10.0", "r168_category": "not-low"},
    ]
    write_csv(ROOT / "M19_source_font_inventory.csv", source_rows, list(source_rows[0].keys()))

    write_json(
        ROOT / "M20_machine_run_summary.json",
        {
            "handoff_id": HANDOFF_ID,
            "uid": UID,
            "physical_page": TARGET_PHYSICAL_PAGE,
            "printed_page": 701,
            "page_image_px": page_image.size,
            "figure_image_px": figure.size,
            "object_count": len(OBJECTS),
            "unordered_pair_count": len(pair_rows),
            "roi_count": len(ROIS),
            "machine_scope": "measurements and enumerations only; no manual verdict, reviewer, decision, note, or global PASS fields",
        },
    )
    print(json.dumps({"physical_page": TARGET_PHYSICAL_PAGE, "objects": len(OBJECTS), "pairs": len(pair_rows), "rois": len(ROIS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
