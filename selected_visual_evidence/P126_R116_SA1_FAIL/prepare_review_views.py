from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
COLOR = Image.open(ROOT / "full_page_native_300dpi.png").convert("RGB")
GRAY = Image.open(ROOT / "full_page_gray_300dpi.png").convert("RGB")

TARGET_BOX = (430, 220, 2050, 1160)
FIGURE_BOX = (780, 240, 1745, 1025)
CAPTION_BOX = (450, 1010, 2045, 1140)


# Approximate source-linked navigation boxes in full-page 300 dpi pixels.
# These boxes are not verdicts and are not used as overlap measurements.
BBOX = {
    "O001": (780, 560, 1650, 590),
    "O002": (1205, 265, 1235, 885),
    "O003": (805, 275, 1640, 870),
    "O004": (885, 335, 1560, 815),
    "O005": (960, 390, 1480, 760),
    "O006": (1075, 470, 1365, 680),
    "O007": (866, 325, 890, 415),
    "O008": (866, 390, 1060, 415),
    "O009": (1037, 390, 1060, 500),
    "O010": (1037, 475, 1147, 500),
    "O011": (1122, 475, 1147, 545),
    "O012": (1122, 518, 1190, 545),
    "O013": (1165, 518, 1190, 568),
    "O014": (867, 325, 889, 349),
    "O015": (894, 286, 960, 345),
    "O016": (820, 384, 852, 432),
    "O017": (1028, 342, 1068, 392),
    "O018": (990, 466, 1028, 520),
    "O019": (1115, 420, 1155, 475),
    "O020": (1080, 505, 1120, 558),
    "O021": (1155, 473, 1198, 527),
    "O022": (1110, 535, 1152, 590),
    "O023": (865, 390, 891, 416),
    "O024": (1035, 475, 1062, 502),
    "O025": (1120, 518, 1148, 546),
    "O026": (1163, 540, 1192, 570),
    "O027": (1037, 390, 1061, 415),
    "O028": (1122, 475, 1147, 500),
    "O029": (1165, 518, 1190, 544),
    "O030": (1178, 528, 1265, 618),
    "O031": (1237, 590, 1300, 652),
    "O032": (1555, 505, 1620, 568),
    "O033": (1222, 272, 1282, 334),
    "O034": (948, 965, 1080, 1002),
    "O035": (1060, 930, 1220, 1002),
    "O036": (1218, 965, 1355, 1002),
    "O037": (1290, 930, 1470, 1002),
    "O038": (455, 1012, 2040, 1135),
}


ROIS = [
    ("ROI-01", "start_steps_1_2", (800, 275, 1105, 470), "O003,O004,O007,O008,O014,O015,O016,O017,O023,O027"),
    ("ROI-02", "middle_steps_3_4", (950, 405, 1170, 535), "O004,O005,O009,O010,O018,O019,O024,O027,O028"),
    ("ROI-03", "inner_steps_5_6_7", (1055, 465, 1225, 605), "O005,O006,O011,O012,O013,O020,O021,O022,O025,O026,O028,O029"),
    ("ROI-04", "optimum_axes", (1160, 500, 1335, 675), "O001,O002,O006,O030,O031"),
    ("ROI-05", "x2_axis_label", (1185, 250, 1310, 365), "O002,O003,O033"),
    ("ROI-06", "x1_axis_label", (1500, 500, 1675, 610), "O001,O003,O032"),
    ("ROI-07", "legend", (930, 915, 1500, 1030), "O034,O035,O036,O037"),
    ("ROI-08", "caption_left", (450, 1005, 1280, 1145), "O038"),
    ("ROI-09", "caption_right", (1260, 1005, 2045, 1145), "O038"),
    ("ROI-10", "x0_outer_contour_clearance", (880, 265, 995, 370), "O003,O015"),
    ("ROI-11", "step7_xaxis_clearance", (1085, 520, 1175, 615), "O001,O022"),
    ("ROI-12", "step6_contour_clearance", (1140, 450, 1235, 535), "O005,O021"),
    ("ROI-13", "step5_contour_contact", (1035, 470, 1135, 575), "O006,O020"),
]


def font() -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), 18)
    return ImageFont.load_default()


def crop_and_save(image: Image.Image, box: tuple[int, int, int, int], name: str) -> None:
    image.crop(box).save(ROOT / name)


def main() -> None:
    crop_and_save(COLOR, TARGET_BOX, "target_with_caption_native_300dpi.png")
    crop_and_save(COLOR, FIGURE_BOX, "figure_native_300dpi.png")
    crop_and_save(GRAY, FIGURE_BOX, "figure_gray_native_300dpi.png")
    crop_and_save(COLOR, CAPTION_BOX, "caption_native_300dpi.png")

    overlay = COLOR.crop(TARGET_BOX).copy()
    draw = ImageDraw.Draw(overlay)
    label_font = font()
    for object_id, box in BBOX.items():
        x0, y0, x1, y1 = box
        shifted = (x0 - TARGET_BOX[0], y0 - TARGET_BOX[1], x1 - TARGET_BOX[0], y1 - TARGET_BOX[1])
        color = (205, 45, 45) if object_id in {
            "O015", "O016", "O017", "O018", "O019", "O020", "O021", "O022",
            "O031", "O032", "O033", "O035", "O037", "O038"
        } else (20, 90, 210)
        draw.rectangle(shifted, outline=color, width=2)
        tx, ty = shifted[0] + 2, max(0, shifted[1] - 20)
        draw.rectangle((tx - 1, ty - 1, tx + 55, ty + 20), fill=(255, 255, 255))
        draw.text((tx, ty), object_id, fill=color, font=label_font)
    overlay.save(ROOT / "target_object_navigation_overlay_300dpi.png")

    roi_rows = []
    for roi_id, name, box, object_ids in ROIS:
        native = COLOR.crop(box)
        native_name = f"{roi_id}_{name}_native1x.png"
        nearest_name = f"{roi_id}_{name}_nearest8x.png"
        native.save(ROOT / native_name)
        native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(ROOT / nearest_name)
        roi_rows.append(
            {
                "roi_id": roi_id,
                "name": name,
                "fullpage_bbox_300dpi": ",".join(map(str, box)),
                "object_ids": object_ids,
                "native1x_file": native_name,
                "nearest8x_file": nearest_name,
                "purpose": "manual visible-ink/glyph/geometry inspection; no machine verdict",
            }
        )

    with (ROOT / "machine_critical_rois.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(roi_rows[0]))
        writer.writeheader()
        writer.writerows(roi_rows)

    print(f"page_px={COLOR.size}; target={TARGET_BOX}; figure={FIGURE_BOX}; rois={len(ROIS)}")


if __name__ == "__main__":
    main()
