from __future__ import annotations

import csv
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


PDF_PATH = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf"
)
SOURCE_PATH = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_plate_graph.tex"
)
ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa1_r115_fresh_isolated_v1"
)
MACHINE = ROOT / "machine"
VIEWS = ROOT / "views"
PAGE_INDEX = 731
PHYSICAL_PAGE = 732
CROP_PT = (70.0, 183.0, 535.0, 416.0)


OBJECTS = [
    {"id": "N01_ALPHA", "kind": "TEXT_HYPER", "role": "hyperparameter", "source_line": 17, "bbox": (93.606, 228.610, 99.201, 238.174), "text": "α"},
    {"id": "N02_THETA", "kind": "NODE_LATENT", "role": "document_topic_proportion", "source_line": 18, "bbox": (166.98, 222.05, 190.23, 245.30), "text": "θ_m"},
    {"id": "N03_Z", "kind": "NODE_LATENT", "role": "topic_assignment", "source_line": 19, "bbox": (235.02, 222.05, 258.26, 245.30), "text": "z_mn"},
    {"id": "N04_W", "kind": "NODE_OBSERVED", "role": "observed_word", "source_line": 20, "bbox": (300.21, 222.05, 323.46, 245.30), "text": "w_mn"},
    {"id": "N05_BETA", "kind": "TEXT_HYPER", "role": "hyperparameter", "source_line": 21, "bbox": (93.630, 323.743, 98.890, 333.307), "text": "β"},
    {"id": "N06_PHI", "kind": "NODE_LATENT", "role": "topic_word_distribution", "source_line": 22, "bbox": (235.02, 317.01, 258.26, 340.26), "text": "φ_k"},
    {"id": "N07_PLATE_N", "kind": "PLATE_BORDER", "role": "token_replication", "source_line": 24, "bbox": (221.58, 209.16, 336.92, 258.19), "text": ""},
    {"id": "N08_PLATE_M", "kind": "PLATE_BORDER", "role": "document_replication", "source_line": 25, "bbox": (151.85, 189.55, 351.99, 277.80), "text": ""},
    {"id": "N09_PLATE_K", "kind": "PLATE_BORDER", "role": "topic_replication", "source_line": 26, "bbox": (221.86, 306.69, 271.42, 350.58), "text": ""},
    {"id": "N10_LABEL_N", "kind": "TEXT_PLATE_LABEL", "role": "token_replication_label", "source_line": 34, "bbox": (288.202, 194.901, 332.799, 205.685), "text": "N_m 个词位"},
    {"id": "N11_LABEL_M", "kind": "TEXT_PLATE_LABEL", "role": "document_replication_label", "source_line": 35, "bbox": (312.717, 284.443, 352.120, 294.260), "text": "M 篇文档"},
    {"id": "N12_LABEL_K", "kind": "TEXT_PLATE_LABEL", "role": "topic_replication_label", "source_line": 36, "bbox": (234.004, 357.224, 271.546, 367.041), "text": "K 个主题"},
    {"id": "N13_LEGEND_OBS_MARK", "kind": "LEGEND_MARKER_OBSERVED", "role": "legend_sample", "source_line": 37, "bbox": (410.48, 233.11, 428.63, 251.25), "text": ""},
    {"id": "N14_LEGEND_OBS_TEXT", "kind": "TEXT_LEGEND", "role": "legend_label", "source_line": 38, "bbox": (442.430, 238.329, 479.092, 248.145), "text": "观测变量"},
    {"id": "N15_LEGEND_LAT_MARK", "kind": "LEGEND_MARKER_LATENT", "role": "legend_sample", "source_line": 39, "bbox": (410.48, 260.04, 428.63, 278.18), "text": ""},
    {"id": "N16_LEGEND_LAT_TEXT", "kind": "TEXT_LEGEND", "role": "legend_label", "source_line": 40, "bbox": (442.430, 265.258, 469.927, 275.074), "text": "潜变量"},
    {"id": "N17_LEGEND_HYPER_MARK", "kind": "TEXT_LEGEND_SAMPLE", "role": "legend_sample", "source_line": 41, "bbox": (412.013, 291.144, 426.799, 300.708), "text": "α,β"},
    {"id": "N18_LEGEND_HYPER_TEXT", "kind": "TEXT_LEGEND", "role": "legend_label", "source_line": 42, "bbox": (442.430, 291.729, 518.587, 301.545), "text": "超参数（plate 外）"},
    {"id": "D01_ALPHA_THETA", "kind": "EDGE_ARROW", "role": "conditional_dependency", "source_line": 28, "bbox": (100.39, 232.60, 165.18, 234.75), "text": "α→θ_m"},
    {"id": "D02_THETA_Z", "kind": "EDGE_ARROW", "role": "conditional_dependency", "source_line": 29, "bbox": (190.63, 232.60, 233.21, 234.75), "text": "θ_m→z_mn"},
    {"id": "D03_Z_W", "kind": "EDGE_ARROW", "role": "conditional_dependency", "source_line": 30, "bbox": (258.66, 232.60, 298.38, 234.75), "text": "z_mn→w_mn"},
    {"id": "D04_BETA_PHI", "kind": "EDGE_ARROW", "role": "conditional_dependency", "source_line": 31, "bbox": (100.37, 327.56, 233.21, 329.71), "text": "β→φ_k"},
    {"id": "D05_PHI_W", "kind": "EDGE_ARROW", "role": "conditional_dependency", "source_line": 32, "bbox": (253.44, 244.76, 304.22, 318.73), "text": "φ_k→w_mn"},
    {"id": "C01_CAPTION", "kind": "TEXT_CAPTION", "role": "caption", "source_line": 45, "bbox": (87.477, 368.454, 519.144, 409.490), "text": "图35.2 完整Bayes LDA盘式图把超参数、潜变量和观测变量分开：每篇文档共享一个主题比例，每个词位拥有一个主题指派，所有文档共享带Dirichlet先验的主题词分布；盘框标明重复次数，箭头只表示条件依赖方向"},
]


PALETTE = {
    "TEXT_HYPER": (214, 39, 40),
    "NODE_LATENT": (44, 160, 44),
    "NODE_OBSERVED": (31, 119, 180),
    "PLATE_BORDER": (148, 103, 189),
    "TEXT_PLATE_LABEL": (140, 86, 75),
    "LEGEND_MARKER_OBSERVED": (23, 190, 207),
    "LEGEND_MARKER_LATENT": (23, 190, 207),
    "TEXT_LEGEND_SAMPLE": (188, 189, 34),
    "TEXT_LEGEND": (188, 189, 34),
    "EDGE_ARROW": (255, 127, 14),
    "TEXT_CAPTION": (227, 119, 194),
}


def px_box(pt_box, sx, sy, crop_origin=None):
    x0, y0, x1, y1 = pt_box
    vals = [round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy)]
    if crop_origin is not None:
        vals[0] -= crop_origin[0]
        vals[2] -= crop_origin[0]
        vals[1] -= crop_origin[1]
        vals[3] -= crop_origin[1]
    return tuple(vals)


def bbox_gap(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy), dx, dy


def bbox_intersection(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def choose_font(size=16):
    candidates = [
        Path(r"C:\Windows\Fonts\consola.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def save_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def nearest_zoom(image, box, out_native, out_zoom):
    crop = image.crop(box)
    crop.save(out_native)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(out_zoom)


def foreground_height(image, box):
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(image.width, x1 + 2)
    y1 = min(image.height, y1 + 2)
    tile = image.crop((x0, y0, x1, y1)).convert("RGB")
    if tile.width == 0 or tile.height == 0:
        return 0, 0
    border = []
    pix = tile.load()
    for x in range(tile.width):
        border.append(pix[x, 0])
        border.append(pix[x, tile.height - 1])
    for y in range(tile.height):
        border.append(pix[0, y])
        border.append(pix[tile.width - 1, y])
    bg = Counter(border).most_common(1)[0][0]
    ys = []
    count = 0
    for y in range(tile.height):
        for x in range(tile.width):
            rgb = pix[x, y]
            delta = max(abs(rgb[c] - bg[c]) for c in range(3))
            if delta >= 20:
                ys.append(y)
                count += 1
    return (max(ys) - min(ys) + 1 if ys else 0), count


def main():
    page_image = Image.open(VIEWS / "full_page_300dpi.png").convert("RGB")
    doc = fitz.open(PDF_PATH)
    page = doc[PAGE_INDEX]
    sx = page_image.width / page.rect.width
    sy = page_image.height / page.rect.height
    crop_px = px_box(CROP_PT, sx, sy)
    figure_caption = page_image.crop(crop_px)
    figure_caption.save(VIEWS / "figure_caption_native_300dpi.png")
    figure_caption.convert("L").save(VIEWS / "figure_caption_grayscale_300dpi.png")

    binary = figure_caption.convert("L").point(lambda p: 0 if p < 245 else 255, mode="1")
    binary.save(VIEWS / "foreground_binary_300dpi.png")

    registry_rows = []
    for obj in OBJECTS:
        pxb = px_box(obj["bbox"], sx, sy, (crop_px[0], crop_px[1]))
        registry_rows.append(
            {
                "object_id": obj["id"],
                "kind": obj["kind"],
                "role": obj["role"],
                "source_file": str(SOURCE_PATH),
                "source_line": obj["source_line"],
                "text_or_relation": obj["text"],
                "bbox_pt_x0": obj["bbox"][0],
                "bbox_pt_y0": obj["bbox"][1],
                "bbox_pt_x1": obj["bbox"][2],
                "bbox_pt_y1": obj["bbox"][3],
                "crop_px_x0": pxb[0],
                "crop_px_y0": pxb[1],
                "crop_px_x1": pxb[2],
                "crop_px_y1": pxb[3],
            }
        )
    save_csv(MACHINE / "object_registry.csv", list(registry_rows[0].keys()), registry_rows)

    pair_rows = []
    geometry_rows = []
    for index, (left, right) in enumerate(combinations(OBJECTS, 2), start=1):
        pair_id = f"P{index:03d}"
        pair_rows.append({"pair_id": pair_id, "object_a": left["id"], "object_b": right["id"]})
        gap, dx, dy = bbox_gap(left["bbox"], right["bbox"])
        geometry_rows.append(
            {
                "pair_id": pair_id,
                "object_a": left["id"],
                "object_b": right["id"],
                "bbox_gap_pt": f"{gap:.4f}",
                "bbox_dx_pt": f"{dx:.4f}",
                "bbox_dy_pt": f"{dy:.4f}",
                "bbox_intersection_pt2": f"{bbox_intersection(left['bbox'], right['bbox']):.4f}",
            }
        )
    save_csv(MACHINE / "pair_denominator.csv", list(pair_rows[0].keys()), pair_rows)
    save_csv(MACHINE / "pair_geometry.csv", list(geometry_rows[0].keys()), geometry_rows)

    with (MACHINE / "denominator_summary.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("UID=FIG-P683-01\n")
        handle.write(f"PHYSICAL_PAGE={PHYSICAL_PAGE}\n")
        handle.write("PRINTED_PAGE=719\n")
        handle.write("NODE_COUNT=18\n")
        handle.write("DRAW_COUNT=5\n")
        handle.write("CAPTION_OBJECT_COUNT=1\n")
        handle.write(f"N={len(OBJECTS)}\n")
        handle.write(f"C_N_2={len(pair_rows)}\n")
        handle.write("FORMULA=N*(N-1)/2\n")

    raw = page.get_text("rawdict")
    glyph_rows = []
    span_rows = []
    span_index = 0
    glyph_index = 0
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = tuple(span["bbox"])
                if bbox[3] < 183 or bbox[1] > 410:
                    continue
                mid = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                candidates = [o for o in OBJECTS if o["bbox"][0] - 0.6 <= mid[0] <= o["bbox"][2] + 0.6 and o["bbox"][1] - 0.6 <= mid[1] <= o["bbox"][3] + 0.6]
                text_candidates = [o for o in candidates if o["kind"].startswith("TEXT") or o["kind"].startswith("NODE")]
                owner = min(text_candidates or candidates, key=lambda o: (o["bbox"][2] - o["bbox"][0]) * (o["bbox"][3] - o["bbox"][1])) if (text_candidates or candidates) else None
                if owner is None:
                    continue
                chars = span.get("chars", [])
                text = "".join(ch.get("c", "") for ch in chars)
                span_index += 1
                pb = px_box(bbox, sx, sy)
                h_ink, foreground_px = foreground_height(page_image, pb)
                span_rows.append(
                    {
                        "span_id": f"S{span_index:03d}",
                        "object_id": owner["id"],
                        "text": text,
                        "font": span.get("font", ""),
                        "pdf_size_pt": f"{span.get('size', 0):.4f}",
                        "bbox_pt_x0": f"{bbox[0]:.3f}",
                        "bbox_pt_y0": f"{bbox[1]:.3f}",
                        "bbox_pt_x1": f"{bbox[2]:.3f}",
                        "bbox_pt_y1": f"{bbox[3]:.3f}",
                        "bbox_height_px": pb[3] - pb[1],
                        "machine_foreground_height_px": h_ink,
                        "machine_foreground_pixel_count": foreground_px,
                    }
                )
                for ch in chars:
                    glyph_index += 1
                    cb = tuple(ch["bbox"])
                    c = ch.get("c", "")
                    glyph_rows.append(
                        {
                            "glyph_id": f"G{glyph_index:04d}",
                            "object_id": owner["id"],
                            "span_id": f"S{span_index:03d}",
                            "char": c,
                            "unicode_scalars": "+".join(f"U+{ord(unit):04X}" for unit in c),
                            "font": span.get("font", ""),
                            "pdf_size_pt": f"{span.get('size', 0):.4f}",
                            "bbox_pt_x0": f"{cb[0]:.3f}",
                            "bbox_pt_y0": f"{cb[1]:.3f}",
                            "bbox_pt_x1": f"{cb[2]:.3f}",
                            "bbox_pt_y1": f"{cb[3]:.3f}",
                        }
                    )
    save_csv(MACHINE / "text_spans.csv", list(span_rows[0].keys()), span_rows)
    save_csv(MACHINE / "glyph_codepoints.csv", list(glyph_rows[0].keys()), glyph_rows)

    font = choose_font(15)
    overlay = figure_caption.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    for obj in OBJECTS:
        box = px_box(obj["bbox"], sx, sy, (crop_px[0], crop_px[1]))
        color = PALETTE[obj["kind"]]
        draw.rectangle(box, outline=color + (255,), width=3)
        tx, ty = box[0] + 2, max(0, box[1] - 17)
        label_box = draw.textbbox((tx, ty), obj["id"], font=font)
        draw.rectangle(label_box, fill=(255, 255, 255, 225))
        draw.text((tx, ty), obj["id"], fill=color + (255,), font=font)
    overlay.save(VIEWS / "semantic_object_overlay_300dpi.png")
    overlay.save(VIEWS / "object_id_overlay_300dpi.png")

    class_overlay = figure_caption.copy()
    cdraw = ImageDraw.Draw(class_overlay, "RGBA")
    for obj in OBJECTS:
        box = px_box(obj["bbox"], sx, sy, (crop_px[0], crop_px[1]))
        color = PALETTE[obj["kind"]]
        cdraw.rectangle(box, outline=color + (255,), width=4)
        label = obj["kind"]
        tx, ty = box[0] + 2, max(0, box[1] - 17)
        label_box = cdraw.textbbox((tx, ty), label, font=font)
        cdraw.rectangle(label_box, fill=(255, 255, 255, 225))
        cdraw.text((tx, ty), label, fill=color + (255,), font=font)
    class_overlay.save(VIEWS / "semantic_class_overlay_300dpi.png")

    text_overlay = figure_caption.copy()
    tdraw = ImageDraw.Draw(text_overlay, "RGBA")
    for row in span_rows:
        box = px_box(
            (float(row["bbox_pt_x0"]), float(row["bbox_pt_y0"]), float(row["bbox_pt_x1"]), float(row["bbox_pt_y1"])),
            sx,
            sy,
            (crop_px[0], crop_px[1]),
        )
        tdraw.rectangle(box, outline=(220, 20, 60, 255), width=2)
        tdraw.text((box[0], max(0, box[1] - 14)), row["span_id"], fill=(220, 20, 60, 255), font=choose_font(12))
    text_overlay.save(VIEWS / "text_measurement_overlay_300dpi.png")

    roi_specs = {
        "roi_nested_plates_labels": (145.0, 186.0, 358.0, 300.0),
        "roi_nodes_horizontal_arrows": (88.0, 214.0, 330.0, 251.0),
        "roi_phi_diagonal_arrow": (220.0, 238.0, 313.0, 345.0),
        "roi_legend": (402.0, 226.0, 525.0, 307.0),
        "roi_caption": (82.0, 364.0, 524.0, 412.0),
    }
    roi_rows = []
    for name, pt_box in roi_specs.items():
        box = px_box(pt_box, sx, sy)
        nearest_zoom(
            page_image,
            box,
            VIEWS / f"{name}_native1x_300dpi.png",
            VIEWS / f"{name}_nearest8x.png",
        )
        roi_rows.append(
            {
                "roi_id": name,
                "bbox_pt_x0": pt_box[0],
                "bbox_pt_y0": pt_box[1],
                "bbox_pt_x1": pt_box[2],
                "bbox_pt_y1": pt_box[3],
                "native_width_px": box[2] - box[0],
                "native_height_px": box[3] - box[1],
                "zoom_method": "nearest-neighbor",
                "zoom_factor": 8,
            }
        )
    save_csv(MACHINE / "roi_registry.csv", list(roi_rows[0].keys()), roi_rows)

    metadata = {
        "uid": "FIG-P683-01",
        "handoff_id": "C-FIG-P683-01-R115-SA1-FRESH-ISOLATED-V1",
        "physical_page": PHYSICAL_PAGE,
        "printed_page": 719,
        "pdf_page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "full_page_300dpi_px": [page_image.width, page_image.height],
        "px_per_pt": [sx, sy],
        "figure_caption_crop_pt": list(CROP_PT),
        "figure_caption_crop_px": list(crop_px),
        "reader_visible_object_count": len(OBJECTS),
        "unordered_pair_count": len(pair_rows),
        "glyph_count": len(glyph_rows),
        "span_count": len(span_rows),
    }
    (MACHINE / "render_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
