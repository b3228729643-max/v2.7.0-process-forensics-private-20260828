from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa2_r115_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r115_fullbook\main_full.pdf")
PAGE_INDEX = 731
DPI = 300
SCALE = DPI / 72.0
CROP_PT = (85.0, 185.0, 525.0, 413.0)
CROP_PX = tuple(round(v * SCALE) for v in CROP_PT)


# The denominator is frozen directly from the current source: 18 visible TikZ
# node constructs and 5 visible directed draw constructs.  The caption is
# audited in the native crop and text overlay but is not a TikZ graph object.
OBJECTS = [
    ("O01", "NODE_HYPER", 17, "alpha", (92.5, 227.0, 100.5, 240.0)),
    ("O02", "NODE_LATENT", 18, "theta_m", (166.5, 221.5, 190.8, 246.0)),
    ("O03", "NODE_LATENT", 19, "z_mn", (234.5, 221.5, 258.8, 246.0)),
    ("O04", "NODE_OBSERVED", 20, "w_mn", (299.7, 221.5, 324.0, 246.0)),
    ("O05", "NODE_HYPER", 21, "beta", (92.5, 322.0, 100.5, 335.0)),
    ("O06", "NODE_LATENT", 22, "varphi_k", (234.5, 316.5, 258.8, 340.8)),
    ("O07", "NODE_PLATE", 24, "N_m plate", (221.0, 208.5, 337.5, 258.8)),
    ("O08", "NODE_PLATE", 25, "M plate", (151.3, 189.0, 352.6, 278.4)),
    ("O09", "NODE_PLATE", 26, "K plate", (221.3, 306.1, 272.0, 351.2)),
    ("O10", "NODE_PLABEL", 34, "N_m words", (287.5, 193.8, 333.5, 206.2)),
    ("O11", "NODE_PLABEL", 35, "M documents", (312.0, 283.9, 352.8, 295.0)),
    ("O12", "NODE_PLABEL", 36, "K topics", (233.3, 356.7, 272.2, 367.7)),
    ("O13", "NODE_LEGEND_OBS", 37, "legend observed swatch", (410.0, 232.6, 429.1, 251.8)),
    ("O14", "NODE_LEGEND_TEXT", 38, "observed variable", (441.8, 237.6, 479.8, 249.0)),
    ("O15", "NODE_LEGEND_LATENT", 39, "legend latent swatch", (410.0, 259.5, 429.1, 278.8)),
    ("O16", "NODE_LEGEND_TEXT", 40, "latent variable", (441.8, 264.5, 470.6, 276.0)),
    ("O17", "NODE_LEGEND_HYPER", 41, "legend alpha,beta", (411.3, 290.4, 427.5, 301.6)),
    ("O18", "NODE_LEGEND_TEXT", 42, "hyperparameters outside plate", (441.8, 291.0, 519.3, 302.2)),
    ("O19", "DRAW_EDGE", 28, "alpha to theta_m", (100.0, 231.8, 165.7, 235.5)),
    ("O20", "DRAW_EDGE", 29, "theta_m to z_mn", (190.0, 231.8, 233.7, 235.5)),
    ("O21", "DRAW_EDGE", 30, "z_mn to w_mn", (258.0, 231.8, 298.9, 235.5)),
    ("O22", "DRAW_EDGE", 31, "beta to varphi_k", (100.0, 326.8, 233.7, 330.5)),
    ("O23", "DRAW_EDGE", 32, "varphi_k to w_mn", (252.8, 244.0, 304.8, 319.3)),
]


SEMANTIC_REGIONS = [
    ("S01", "document-generation path", (90.0, 185.0, 356.0, 300.0)),
    ("S02", "topic-word path", (90.0, 238.0, 326.0, 369.0)),
    ("S03", "legend", (404.0, 225.0, 522.0, 307.0)),
    ("S04", "caption", (85.0, 368.0, 522.0, 412.0)),
]


ROIS = [
    ("ROI01", "alpha-theta arrowhead and glyph clearance", (91.0, 218.0, 194.0, 249.0)),
    ("ROI02", "theta-z arrowhead and node borders", (162.0, 217.0, 263.0, 250.0)),
    ("ROI03", "z-w arrowhead and observed-node text", (230.0, 216.0, 329.0, 251.0)),
    ("ROI04", "varphi-w diagonal arrowhead convergence", (231.0, 238.0, 310.0, 344.0)),
    ("ROI05", "beta-varphi arrowhead and glyph clearance", (91.0, 310.0, 263.0, 343.0)),
    ("ROI06", "nested N_m and M plates with labels", (145.0, 184.0, 359.0, 300.0)),
    ("ROI07", "K plate and replication label", (215.0, 301.0, 279.0, 370.0)),
    ("ROI08", "legend swatches and labels", (402.0, 225.0, 523.0, 307.0)),
    ("ROI09", "caption glyphs and line wrapping", (84.0, 366.0, 523.0, 412.0)),
    ("ROI10", "observed w node with two incoming arrows", (292.0, 216.0, 329.0, 253.0)),
]


def pt_box_to_crop_px(box):
    x0, y0, x1, y1 = box
    cx0, cy0, _, _ = CROP_PT
    return tuple(round((v - o) * SCALE) for v, o in zip((x0, y0, x1, y1), (cx0, cy0, cx0, cy0)))


def font():
    for candidate in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ):
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, 22)
    return ImageFont.load_default()


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main():
    if not ROOT.is_dir():
        raise RuntimeError("fixed root missing")
    full = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    gray_full = Image.open(ROOT / "full_page_grayscale_300dpi.png").convert("L")
    crop = full.crop(CROP_PX)
    gray_crop = gray_full.crop(CROP_PX)
    crop.save(ROOT / "figure_caption_native_300dpi.png")
    gray_crop.save(ROOT / "figure_caption_grayscale_300dpi.png")

    write_csv(
        ROOT / "object_inventory_machine.csv",
        ["OBJECT_ID", "KIND", "SOURCE_LINE", "SOURCE_REPR", "BBOX_PT_X0", "BBOX_PT_Y0", "BBOX_PT_X1", "BBOX_PT_Y1"],
        [(oid, kind, line, name, *box) for oid, kind, line, name, box in OBJECTS],
    )
    pair_rows = []
    for idx, (a, b) in enumerate(combinations([o[0] for o in OBJECTS], 2), 1):
        pair_rows.append((f"P{idx:03d}", a, b))
    if len(pair_rows) != 253 or pair_rows[-1] != ("P253", "O22", "O23"):
        raise RuntimeError("pair universe cardinality/order mismatch")
    write_csv(ROOT / "pair_universe_machine.csv", ["PAIR_ID", "OBJECT_A", "OBJECT_B"], pair_rows)

    overlay_font = font()
    palette = {
        "NODE_HYPER": "#8E44AD",
        "NODE_LATENT": "#00897B",
        "NODE_OBSERVED": "#005B96",
        "NODE_PLATE": "#7F8C8D",
        "NODE_PLABEL": "#A65E00",
        "NODE_LEGEND_OBS": "#005B96",
        "NODE_LEGEND_LATENT": "#00897B",
        "NODE_LEGEND_HYPER": "#8E44AD",
        "NODE_LEGEND_TEXT": "#C0392B",
        "DRAW_EDGE": "#D35400",
    }
    obj_overlay = crop.copy()
    draw = ImageDraw.Draw(obj_overlay)
    for oid, kind, _, _, box in OBJECTS:
        pb = pt_box_to_crop_px(box)
        color = palette[kind]
        draw.rectangle(pb, outline=color, width=4)
        draw.text((pb[0] + 2, max(0, pb[1] - 24)), oid, fill=color, font=overlay_font, stroke_width=1, stroke_fill="white")
    obj_overlay.save(ROOT / "figure_object_overlay_300dpi.png")

    sem_overlay = crop.copy()
    draw = ImageDraw.Draw(sem_overlay)
    sem_colors = ("#E74C3C", "#2980B9", "#27AE60", "#8E44AD")
    for (sid, name, box), color in zip(SEMANTIC_REGIONS, sem_colors):
        pb = pt_box_to_crop_px(box)
        draw.rectangle(pb, outline=color, width=6)
        draw.text((pb[0] + 4, pb[1] + 4), f"{sid} {name}", fill=color, font=overlay_font, stroke_width=2, stroke_fill="white")
    sem_overlay.save(ROOT / "figure_semantic_overlay_300dpi.png")

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    span_rows = []
    text_overlay = crop.copy()
    draw = ImageDraw.Draw(text_overlay)
    span_index = 0
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                x0, y0, x1, y1 = span["bbox"]
                if x1 < CROP_PT[0] or x0 > CROP_PT[2] or y1 < CROP_PT[1] or y0 > CROP_PT[3]:
                    continue
                span_index += 1
                tid = f"T{span_index:03d}"
                text = span["text"]
                size = float(span["size"])
                span_rows.append((tid, text, size, x0, y0, x1, y1))
                pb = pt_box_to_crop_px((x0, y0, x1, y1))
                draw.rectangle(pb, outline="#FF00AA", width=3)
                draw.text((pb[0] + 1, max(0, pb[1] - 22)), tid, fill="#FF00AA", font=overlay_font, stroke_width=1, stroke_fill="white")
    text_overlay.save(ROOT / "figure_text_overlay_300dpi.png")
    write_csv(
        ROOT / "text_spans_machine.csv",
        ["TEXT_ID", "TEXT", "PDF_SIZE_PT", "BBOX_PT_X0", "BBOX_PT_Y0", "BBOX_PT_X1", "BBOX_PT_Y1"],
        span_rows,
    )

    roi_rows = []
    for rid, purpose, box in ROIS:
        pb = pt_box_to_crop_px(box)
        roi = crop.crop(pb)
        roi.save(ROOT / f"{rid}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(ROOT / f"{rid}_nearest8x.png")
        roi_rows.append((rid, purpose, *box, *pb, roi.width, roi.height))
    write_csv(
        ROOT / "critical_roi_manifest_machine.csv",
        ["ROI_ID", "PURPOSE", "BBOX_PT_X0", "BBOX_PT_Y0", "BBOX_PT_X1", "BBOX_PT_Y1", "CROP_PX_X0", "CROP_PX_Y0", "CROP_PX_X1", "CROP_PX_Y1", "WIDTH_PX", "HEIGHT_PX"],
        roi_rows,
    )

    (ROOT / "mechanical_freeze.txt").write_text(
        "UID=FIG-P683-01\n"
        "R115_PHYSICAL_PAGE=732\n"
        "PRINTED_PAGE=719\n"
        "DENOMINATOR_SCOPE=18_VISIBLE_TIKZ_NODES_PLUS_5_VISIBLE_DIRECTED_DRAWS\n"
        "N=23\n"
        "UNORDERED_PAIR_COUNT=253\n"
        "PAIR_ORDER=LEXICOGRAPHIC_BY_OBJECT_ID\n"
        f"CROP_PT={CROP_PT}\n"
        f"CROP_PX={CROP_PX}\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
