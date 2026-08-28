from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
FULL = ROOT / "full_page_300dpi.png"

# Official R115 page geometry reported by pdfinfo; rendered PNG is 2481 x 3508.
PAGE_W_PT = 595.276
PAGE_H_PT = 841.89
CROP_PT = (60.0, 325.0, 525.0, 530.0)


OBJECTS = [
    # Reader-visible graphical objects. Repeated plot marks are one multipart
    # source-level object; every reader-visible text element remains separate.
    ("G01", "PANEL_BORDER", (88.0, 330.0, 282.0, 484.0), "left rounded panel border", "src:14"),
    ("G02", "PANEL_BORDER", (309.0, 330.0, 504.0, 484.0), "right rounded panel border", "src:31"),
    ("G03", "SEMANTIC_FILL", (107.0, 372.0, 222.0, 400.0), "ELBO blue background region", "src:17"),
    ("G04", "SEMANTIC_FILL", (222.0, 372.0, 268.0, 400.0), "KL orange background region", "src:18"),
    ("G05", "NODE_BORDER", (107.0, 372.0, 268.0, 400.0), "evidence total outline", "src:19"),
    ("G06", "DIVIDER", (221.5, 372.0, 222.5, 400.0), "ELBO/KL separator", "src:20"),
    ("G07", "LINE_ARROW", (107.0, 356.0, 268.0, 372.0), "bidirectional evidence-length arrow", "src:23-24"),
    ("G08", "AXIS", (317.0, 438.0, 490.0, 455.0), "x axis with tick marks", "src:34-41"),
    ("G09", "AXIS", (316.0, 345.0, 325.0, 451.0), "y axis", "src:34-41"),
    ("G10", "DATA_CURVE", (318.0, 390.0, 477.0, 440.0), "nondecreasing ELBO staircase", "src:42-43"),
    ("G11", "MARKER_SET", (316.0, 388.0, 479.0, 442.0), "seven circular staircase markers", "src:42-43"),
    ("G12", "REFERENCE_LINE", (321.0, 354.0, 477.0, 362.0), "dashed unknown-upper-bound reference", "src:44-45"),
    ("T01", "PANEL_TITLE", (144.653, 331.272456, 221.016630, 347.068818), "证据的长度分解", "src:15-16"),
    ("T02", "FORMULA_LABEL", (168.440, 348.550790, 202.898937, 357.716420), "log p(w)", "src:23-24"),
    ("T03", "BAR_LABEL", (129.978, 379.566790, 196.007150, 388.732420), "L(q)：证据下界", "src:21"),
    ("T04", "BAR_LABEL", (226.222, 379.727496, 258.503260, 389.543886), "KL 间隙", "src:22"),
    ("T05", "FORMULA_BLOCK", (99.212, 408.163790, 257.233068, 417.329420), "log p(w)=L(q)+KL(q(h)||p(h|w))", "src:25-27"),
    ("T06", "ANNOTATION", (99.212, 437.666790, 266.462033, 458.093886), "KL>=0 lower-bound explanation", "src:28-29"),
    ("T07", "PANEL_TITLE", (329.113, 331.272456, 473.091360, 347.068818), "坐标更新下的 ELBO 非降阶梯", "src:32-33"),
    ("T08", "ANNOTATION", (322.476, 359.500896, 376.274280, 369.103889), "未知全局上限", "src:46-47"),
    ("T09", "ANNOTATION", (394.575, 402.525896, 475.272420, 412.128889), "坐标稳定／局部驻点", "src:48-49"),
    ("T10", "TICK_LABEL", (312.171, 444.377872, 317.544851, 453.643132), "0", "src:39"),
    ("T11", "TICK_LABEL", (339.045, 444.358872, 343.761017, 453.624132), "1", "src:39"),
    ("T12", "TICK_LABEL", (365.521, 444.395872, 370.375996, 453.661132), "2", "src:39"),
    ("T13", "TICK_LABEL", (392.067, 444.395872, 396.921996, 453.661132), "3", "src:39"),
    ("T14", "TICK_LABEL", (418.427, 444.386872, 423.652607, 453.652132), "4", "src:39"),
    ("T15", "TICK_LABEL", (445.259, 444.256872, 449.910161, 453.522132), "5", "src:39"),
    ("T16", "TICK_LABEL", (471.610, 444.404872, 476.650301, 453.670132), "6", "src:39"),
    ("T17", "AXIS_LABEL", (371.577, 459.584896, 425.375280, 469.187889), "坐标更新轮次", "src:40"),
    ("T18", "CAPTION_NUMBER", (76.138, 483.734338, 107.435093, 498.160240), "图 35.5", "src:53"),
    ("T19", "CAPTION_BODY", (117.398, 487.320888, 507.797722, 524.770875), "full three-line figure caption", "src:53"),
]


ROIS = [
    ("roi01_left_bar_formula_note", (94.0, 344.0, 274.0, 463.0)),
    ("roi02_right_title_upper_bound", (312.0, 326.0, 486.0, 377.0)),
    ("roi03_right_staircase_local_label", (310.0, 376.0, 491.0, 444.0)),
    ("roi04_right_axis_ticks_label", (306.0, 436.0, 493.0, 474.0)),
    ("roi05_formula_codepoints", (94.0, 402.0, 265.0, 423.0)),
    ("roi06_left_lower_note", (94.0, 430.0, 274.0, 464.0)),
    ("roi07_caption_all_lines", (72.0, 480.0, 514.0, 529.0)),
    ("roi08_panel_gutter_boundaries", (270.0, 325.0, 321.0, 486.0)),
]


ROLE_COLORS = {
    "PANEL_BORDER": (90, 90, 90, 255),
    "SEMANTIC_FILL": (0, 150, 150, 255),
    "NODE_BORDER": (50, 90, 220, 255),
    "DIVIDER": (160, 60, 190, 255),
    "LINE_ARROW": (80, 80, 220, 255),
    "AXIS": (120, 60, 210, 255),
    "DATA_CURVE": (0, 120, 80, 255),
    "MARKER_SET": (0, 80, 180, 255),
    "REFERENCE_LINE": (230, 120, 0, 255),
    "PANEL_TITLE": (210, 0, 0, 255),
    "FORMULA_LABEL": (210, 0, 0, 255),
    "BAR_LABEL": (210, 0, 0, 255),
    "FORMULA_BLOCK": (210, 0, 0, 255),
    "ANNOTATION": (230, 80, 0, 255),
    "TICK_LABEL": (180, 0, 160, 255),
    "AXIS_LABEL": (180, 0, 160, 255),
    "CAPTION_NUMBER": (140, 0, 180, 255),
    "CAPTION_BODY": (140, 0, 180, 255),
}


def pt_box_to_px(box, sx, sy):
    x0, y0, x1, y1 = box
    return tuple(round(v) for v in (x0 * sx, y0 * sy, x1 * sx, y1 * sy))


def crop_relative(box_px, crop_px):
    x0, y0, x1, y1 = box_px
    cx0, cy0, _, _ = crop_px
    return x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0


def safe_text(draw, xy, text, fill):
    draw.text(xy, text, fill=fill, font=ImageFont.load_default(), stroke_width=1, stroke_fill=(255, 255, 255, 255))


def main():
    full = Image.open(FULL).convert("RGB")
    sx = full.width / PAGE_W_PT
    sy = full.height / PAGE_H_PT
    crop_px = pt_box_to_px(CROP_PT, sx, sy)
    crop = full.crop(crop_px)
    crop.save(ROOT / "figure_caption_native_300dpi.png")
    ImageOps.grayscale(crop).save(ROOT / "figure_caption_grayscale_300dpi.png")

    gray = ImageOps.grayscale(crop)
    # Auxiliary foreground candidate mask only; it is not an adjudication.
    mask = gray.point(lambda p: 255 if p < 238 else 0)
    mask.save(ROOT / "foreground_candidate_mask_300dpi.png")

    overlays = {}
    for name in ("object_overlay_300dpi", "semantic_overlay_300dpi", "text_overlay_300dpi"):
        overlays[name] = crop.convert("RGBA")

    obj_draw = ImageDraw.Draw(overlays["object_overlay_300dpi"])
    sem_draw = ImageDraw.Draw(overlays["semantic_overlay_300dpi"])
    txt_draw = ImageDraw.Draw(overlays["text_overlay_300dpi"])

    rows = []
    metrics = []
    for oid, role, box_pt, description, source_ref in OBJECTS:
        full_box_px = pt_box_to_px(box_pt, sx, sy)
        box_px = crop_relative(full_box_px, crop_px)
        rows.append((oid, role, source_ref, description, *box_pt, *full_box_px, *box_px))

        obj_draw.rectangle(box_px, outline=(0, 180, 0, 255), width=3)
        safe_text(obj_draw, (box_px[0] + 2, box_px[1] + 2), oid, (0, 120, 0, 255))
        color = ROLE_COLORS[role]
        sem_draw.rectangle(box_px, outline=color, width=3)
        safe_text(sem_draw, (box_px[0] + 2, box_px[1] + 2), f"{oid}:{role}", color)
        if oid.startswith("T"):
            txt_draw.rectangle(box_px, outline=(220, 0, 0, 255), width=3)
            safe_text(txt_draw, (box_px[0] + 2, box_px[1] + 2), oid, (220, 0, 0, 255))

            local = gray.crop(box_px)
            dark = local.point(lambda p: 255 if p < 215 else 0)
            ink_box = dark.getbbox()
            if ink_box is None:
                ink_h = 0
                ink_w = 0
                dark_count = 0
            else:
                ink_w = ink_box[2] - ink_box[0]
                ink_h = ink_box[3] - ink_box[1]
                dark_count = sum(1 for p in dark.getdata() if p)
            metrics.append((oid, role, box_px[0], box_px[1], box_px[2], box_px[3], ink_w, ink_h, dark_count))

    for name, image in overlays.items():
        image.convert("RGB").save(ROOT / f"{name}.png")

    with (ROOT / "object_index.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([
            "OBJECT_ID", "ROLE", "SOURCE_REF", "DESCRIPTION",
            "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT",
            "FULL_X0_PX", "FULL_Y0_PX", "FULL_X1_PX", "FULL_Y1_PX",
            "CROP_X0_PX", "CROP_Y0_PX", "CROP_X1_PX", "CROP_Y1_PX",
        ])
        writer.writerows(rows)

    with (ROOT / "text_geometry_metrics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["ELEMENT_ID", "ROLE", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "INK_WIDTH_PX", "INK_HEIGHT_PX", "DARK_PIXEL_COUNT"])
        writer.writerows(metrics)

    for roi_name, roi_pt in ROIS:
        roi_full_px = pt_box_to_px(roi_pt, sx, sy)
        roi = full.crop(roi_full_px)
        roi.save(ROOT / f"{roi_name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), resample=Image.Resampling.NEAREST).save(ROOT / f"{roi_name}_nearest8x.png")

    print(f"page_px={full.width}x{full.height}")
    print(f"crop_px={crop_px}; crop_size={crop.width}x{crop.height}")
    print(f"objects={len(OBJECTS)}; unordered_pairs={len(OBJECTS) * (len(OBJECTS) - 1) // 2}")
    print(f"rois={len(ROIS)}; roi_files={len(ROIS) * 2}")


if __name__ == "__main__":
    main()
