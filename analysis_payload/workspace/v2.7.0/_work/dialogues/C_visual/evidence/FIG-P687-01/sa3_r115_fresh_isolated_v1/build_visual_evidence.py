from __future__ import annotations

import csv
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa3_r115_fresh_isolated_v1")
PAGE = ROOT / "full_page_300dpi.png"
PAGE_W_PT = 595.276
PAGE_H_PT = 841.89
CROP_PT = (50.0, 377.0, 540.0, 645.0)


TEXT_ELEMENTS = [
    ("T01", "BADGE_TEXT", 9.0, "1", (181.749, 386.147, 186.187, 395.113)),
    ("T02", "NODE_TEXT", 9.2, "移除当前词位 i / 从两张计数表各减一", (219.558, 394.958, 305.981, 415.734)),
    ("T03", "BADGE_TEXT", 9.0, "2", (69.214, 443.452, 73.652, 452.418)),
    ("T04", "NODE_TEXT", 9.2, "读取文档--主题计数", (110.655, 444.163, 202.283, 453.980)),
    ("T05", "FORMULA", 9.2, "n_mk^{-i}+alpha_k", (134.309, 454.019, 178.270, 466.872)),
    ("T06", "FORMULA", 9.2, "n_mdot^{-i}+alpha_0", (135.527, 465.486, 177.051, 477.126)),
    ("T07", "BADGE_TEXT", 9.0, "3", (279.828, 443.402, 284.266, 452.368)),
    ("T08", "NODE_TEXT", 9.2, "读取主题--单词计数", (323.253, 443.553, 414.881, 453.370)),
    ("T09", "FORMULA", 9.2, "n_kv^{-i}+beta_v", (348.274, 453.409, 389.340, 466.262)),
    ("T10", "FORMULA", 9.2, "n_kdot^{-i}+beta_0", (349.119, 464.876, 388.656, 477.729)),
    ("T11", "BADGE_TEXT", 9.0, "4", (145.749, 500.410, 150.187, 509.376)),
    ("T12", "NODE_TEXT", 9.2, "相乘并对 k 归一化", (217.368, 500.669, 308.173, 510.486)),
    ("T13", "FORMULA", 9.2, "p(z_i=k|-i) proportional to document and word factors", (185.383, 509.141, 338.438, 536.834)),
    ("T14", "BADGE_TEXT", 9.0, "5", (174.663, 554.129, 179.101, 563.095)),
    ("T15", "NODE_TEXT", 9.2, "抽样 k* 并恢复计数 / 把词位 i 加回两张表", (218.111, 559.929, 307.431, 581.560)),
    ("T16", "ANNOTATION", 8.8, "下一词位：重新从‘移除’开始", (461.714, 473.057, 522.795, 503.369)),
    ("T17", "FOOTNOTE", 9.0, "上标 -i 始终保留到抽样完成，防止当前词位对自身重复计数。", (141.029, 596.112, 388.997, 605.715)),
    ("T18", "CAPTION_LABEL", 10.95, "图 35.4", (62.362, 610.794, 92.599, 625.220)),
    ("T19", "CAPTION_BODY", 10.95, "折叠 Gibbs 更新……上标负 i 防止当前词位对自身产生重复计数", (102.562, 614.381, 521.565, 638.440)),
]


OBJECTS = [
    ("O01", "CARD", "step-1 remove card", (203, 386, 323, 425)),
    ("O02", "BADGE", "step-1 numbered badge", (174, 378, 193, 399)),
    ("O03", "CARD", "step-2 document-theme evidence card", (85, 434, 229, 490)),
    ("O04", "BADGE", "step-2 numbered badge", (59, 435, 81, 457)),
    ("O05", "CARD", "step-3 topic-word evidence card", (300, 434, 444, 490)),
    ("O06", "BADGE", "step-3 numbered badge", (270, 435, 292, 457)),
    ("O07", "CARD", "step-4 full-conditional card", (169, 492, 361, 551)),
    ("O08", "BADGE", "step-4 numbered badge", (136, 492, 158, 514)),
    ("O09", "CARD", "step-5 sample-and-restore card", (196, 552, 333, 590)),
    ("O10", "BADGE", "step-5 numbered badge", (165, 545, 187, 568)),
    ("O11", "LINE_ARROW", "step-1 to step-2 connector", (155, 416, 225, 442)),
    ("O12", "LINE_ARROW", "step-1 to step-3 connector", (301, 416, 374, 442)),
    ("O13", "LINE_ARROW", "step-2 to step-4 connector", (156, 487, 185, 503)),
    ("O14", "LINE_ARROW", "step-3 to step-4 connector", (340, 487, 367, 503)),
    ("O15", "LINE_ARROW", "step-4 to step-5 connector", (258, 548, 267, 561)),
    ("O16", "LINE_ARROW", "return-loop connector", (322, 389, 458, 573)),
    ("O17", "ANNOTATION", "return-loop text", (458, 469, 526, 506)),
    ("O18", "FOOTNOTE", "leave-one-out explanatory line", (139, 593, 391, 608)),
    ("O19", "CAPTION_LABEL", "figure number", (60, 609, 96, 627)),
    ("O20", "CAPTION_BODY", "two-line caption body", (99, 609, 524, 641)),
]


ROIS = [
    ("roi01_step2_badge_card_arrow", (55, 414, 238, 497)),
    ("roi02_step3_badge_card_arrow", (267, 414, 449, 497)),
    ("roi03_conditional_formula_connectors", (132, 484, 392, 557)),
    ("roi04_loop_text_vertical_arrow", (425, 438, 535, 525)),
    ("roi05_sample_footnote_loop", (135, 538, 470, 614)),
    ("roi06_footnote_caption_clearance", (55, 585, 530, 643)),
]


def pt_box_to_px(box, sx, sy):
    return tuple(round(v * (sx if i % 2 == 0 else sy)) for i, v in enumerate(box))


def crop_relative_box(box, crop_px):
    x0, y0, x1, y1 = box
    return (x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0], y1 - crop_px[1])


def ink_height(gray, box):
    region = gray.crop(box)
    # Difference >=20/255 from the white local page background.
    mask = region.point(lambda p: 255 if p <= 235 else 0, mode="1")
    bounds = mask.getbbox()
    return 0 if bounds is None else bounds[3] - bounds[1]


def main():
    page = Image.open(PAGE).convert("RGB")
    sx = page.width / PAGE_W_PT
    sy = page.height / PAGE_H_PT
    crop_px = pt_box_to_px(CROP_PT, sx, sy)
    figure = page.crop(crop_px)
    figure.save(ROOT / "figure_caption_native300dpi.png")
    figure.save(ROOT / "after_figure_crop_300dpi.png")
    shutil.copyfile(ROOT / "full_page_200dpi.png", ROOT / "after_full_page_200dpi.png")

    standalone_px = pt_box_to_px((50.0, 377.0, 540.0, 610.0), sx, sy)
    page.crop(standalone_px).save(ROOT / "after_standalone_300dpi.png")

    gray = figure.convert("L")
    gray.save(ROOT / "figure_caption_grayscale_native300dpi.png")
    gray.save(ROOT / "after_grayscale_300dpi.png")
    all_ink = gray.point(lambda p: 0 if p <= 235 else 255, mode="1")
    all_ink.save(ROOT / "visible_ink_mask_all.png")

    text_mask = Image.new("1", figure.size, 255)
    text_mask_draw = ImageDraw.Draw(text_mask)
    text_overlay = figure.copy()
    text_draw = ImageDraw.Draw(text_overlay)
    font = ImageFont.load_default()
    colors = {
        "BADGE_TEXT": "#ff00ff",
        "NODE_TEXT": "#d00000",
        "FORMULA": "#ff7f00",
        "ANNOTATION": "#7a00cc",
        "FOOTNOTE": "#008000",
        "CAPTION_LABEL": "#0055ff",
        "CAPTION_BODY": "#00a0a0",
    }

    measurement_rows = []
    for eid, role, declared_pt, sample, box_pt in TEXT_ELEMENTS:
        page_box_px = pt_box_to_px(box_pt, sx, sy)
        box = crop_relative_box(page_box_px, crop_px)
        color = colors[role]
        text_draw.rectangle(box, outline=color, width=3)
        text_draw.rectangle((box[0], max(0, box[1] - 14), box[0] + 28, box[1]), fill="white")
        text_draw.text((box[0] + 1, max(0, box[1] - 13)), eid, fill=color, font=font)
        local_ink = all_ink.crop(box)
        text_mask.paste(local_ink, box)
        measurement_rows.append(
            [eid, role, declared_pt, 1.0, declared_pt, sample, *page_box_px, ink_height(gray, box)]
        )
    text_overlay.save(ROOT / "text_measurement_overlay_native300dpi.png")
    text_overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")
    text_mask.save(ROOT / "visible_ink_mask_text_bbox_intersection.png")

    nontext = Image.new("1", figure.size, 255)
    all_px = all_ink.load()
    text_px = text_mask.load()
    non_px = nontext.load()
    for y in range(figure.height):
        for x in range(figure.width):
            if all_px[x, y] == 0 and text_px[x, y] != 0:
                non_px[x, y] = 0
    nontext.save(ROOT / "visible_ink_mask_nontext_candidate.png")

    with (ROOT / "raw_text_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "ELEMENT_ID", "ROLE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT",
                "TEXT_SAMPLE", "PAGE_BBOX_X0", "PAGE_BBOX_Y0", "PAGE_BBOX_X1", "PAGE_BBOX_Y1",
                "H_INK_PX_THRESHOLD235",
            ]
        )
        writer.writerows(measurement_rows)

    object_overlay = figure.copy()
    object_draw = ImageDraw.Draw(object_overlay)
    class_colors = {
        "CARD": "#e00000",
        "BADGE": "#ff00ff",
        "LINE_ARROW": "#0055ff",
        "ANNOTATION": "#7a00cc",
        "FOOTNOTE": "#008000",
        "CAPTION_LABEL": "#00a0a0",
        "CAPTION_BODY": "#7f5f00",
    }
    with (ROOT / "semantic_object_denominator.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["OBJECT_ID", "CLASS", "DESCRIPTION", "PAGE_X0_PT", "PAGE_Y0_PT", "PAGE_X1_PT", "PAGE_Y1_PT"])
        for oid, cls, desc, box_pt in OBJECTS:
            writer.writerow([oid, cls, desc, *box_pt])
            page_box_px = pt_box_to_px(box_pt, sx, sy)
            box = crop_relative_box(page_box_px, crop_px)
            color = class_colors[cls]
            object_draw.rectangle(box, outline=color, width=3)
            object_draw.rectangle((box[0], box[1], box[0] + 30, box[1] + 14), fill="white")
            object_draw.text((box[0] + 1, box[1] + 1), oid, fill=color, font=font)
    object_overlay.save(ROOT / "semantic_object_overlay_native300dpi.png")

    with (ROOT / "pair_skeleton.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "PAIR_ID", "OBJECT_A", "OBJECT_B", "MANUAL_NATIVE_VIEW", "MANUAL_NEAREST8X_VIEW",
                "MANUAL_RELATION", "MANUAL_VISIBLE_INK_COLLISION", "MANUAL_CLEARANCE_OR_EXEMPTION",
                "MANUAL_VERDICT", "MANUAL_NOTES",
            ]
        )
        pair_no = 0
        for i, a in enumerate(OBJECTS):
            for b in OBJECTS[i + 1:]:
                pair_no += 1
                writer.writerow([f"P{pair_no:03d}", a[0], b[0], "", "", "", "", "", "", ""])

    for name, roi_pt in ROIS:
        roi_page_px = pt_box_to_px(roi_pt, sx, sy)
        roi = page.crop(roi_page_px)
        roi.save(ROOT / f"{name}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(
            ROOT / f"{name}_nearest8x.png"
        )

    with (ROOT / "render_geometry.txt").open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"PAGE_WIDTH_PX={page.width}\n")
        f.write(f"PAGE_HEIGHT_PX={page.height}\n")
        f.write(f"PAGE_WIDTH_PT={PAGE_W_PT}\n")
        f.write(f"PAGE_HEIGHT_PT={PAGE_H_PT}\n")
        f.write(f"SCALE_X_PX_PER_PT={sx:.9f}\n")
        f.write(f"SCALE_Y_PX_PER_PT={sy:.9f}\n")
        f.write(f"FIGURE_CAPTION_CROP_PT={CROP_PT}\n")
        f.write(f"FIGURE_CAPTION_CROP_PX={crop_px}\n")
        f.write(f"DENOMINATOR_N={len(OBJECTS)}\n")
        f.write(f"UNORDERED_PAIR_COUNT={len(OBJECTS) * (len(OBJECTS) - 1) // 2}\n")


if __name__ == "__main__":
    main()
