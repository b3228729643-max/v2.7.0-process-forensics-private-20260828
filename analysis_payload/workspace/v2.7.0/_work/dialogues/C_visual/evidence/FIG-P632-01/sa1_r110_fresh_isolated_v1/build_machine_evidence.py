from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_conditional_slice.tex")
PAGE_INDEX = 681
PAGE_NUMBER = 682
RENDER = ROOT / "page_682_native_300dpi.png"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
img = Image.open(RENDER).convert("RGB")
sx = img.width / page.rect.width
sy = img.height / page.rect.height


def pbox(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy))


def crop_pt(box: tuple[float, float, float, float]) -> Image.Image:
    return img.crop(pbox(box))


identity = {
    "uid": "FIG-P632-01",
    "figure_number": "33.2",
    "physical_page": PAGE_NUMBER,
    "printed_page": 669,
    "pdf_path": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "pdf_pages": len(doc),
    "pdf_page_width_pt": page.rect.width,
    "pdf_page_height_pt": page.rect.height,
    "render_path": str(RENDER),
    "render_width_px": img.width,
    "render_height_px": img.height,
    "render_dpi": 300,
    "source_path": str(SOURCE),
    "source_bytes": SOURCE.stat().st_size,
    "source_sha256": sha256(SOURCE),
    "source_label": "fig:V5-C04-conditional-slice",
    "source_caption": "同一二元正态联合密度的两条截面除以相应边缘密度后，得到方差16/25、全实线积分为1的满条件密度；零边缘处须使用预先指定的正则条件版本。",
}
(ROOT / "input_identity_machine.json").write_text(
    json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

# Native-resolution views. These are direct crops from the Poppler 300 dpi page;
# no resize is applied to any 1x or grayscale artifact.
crop_pt((70, 65, 535, 390.5)).save(ROOT / "figure_crop_native_300dpi.png")
crop_pt((70, 390.5, 535, 422)).save(ROOT / "caption_crop_native_300dpi.png")
crop_pt((70, 65, 535, 422)).save(ROOT / "figure_and_caption_native_300dpi.png")
ImageOps.grayscale(crop_pt((70, 65, 535, 390.5))).save(ROOT / "figure_grayscale_native_300dpi.png")

# Independent visible semantic objects. Bounds are in canonical PDF points.
# Geometry tables deliberately contain no reviewer decision, boolean, or note field.
objects = [
    ("O01", "TEXT_FORMULA", "joint model parameter and density formula block", (134, 69, 300, 136), "94-100"),
    ("O02", "AXIS", "joint-panel x1/x2 axes including arrowheads and axis labels", (116, 128, 307, 291), "72-74"),
    ("O03", "DATA_CURVE", "outer dotted joint-density contour", (140, 145, 281, 283), "76-77"),
    ("O04", "DATA_CURVE", "middle dashed joint-density contour", (163, 163, 265, 269), "78-79"),
    ("O05", "DATA_CURVE", "inner solid joint-density contour", (180, 181, 250, 253), "80-81"),
    ("O06", "LINE_ARROW_TEXT", "horizontal slice x2=b=4/5 with its label", (106, 158, 298, 208), "83-84"),
    ("O07", "LINE_ARROW_TEXT", "vertical slice x1=a=1 with its leader and label", (231, 126, 302, 289), "85-89"),
    ("O08", "MARKER_TEXT", "joint point marker and (a,b) leader label", (230, 156, 270, 195), "90-93"),
    ("O09", "TEXT", "joint-contour conclusion line", (101, 291, 309, 309), "99-100"),
    ("O10", "LINE_ARROW_TEXT", "horizontal-slice normalization arrow and label", (277, 145, 323, 195), "146-148"),
    ("O11", "TEXT_FORMULA", "upper conditional-density formula block", (337, 68, 506, 140), "115-122"),
    ("O12", "AXIS", "upper conditional-density axes and t label", (334, 126, 493, 187), "106-108"),
    ("O13", "DATA_CURVE", "upper conditional-density solid curve", (339, 141, 489, 190), "109-110"),
    ("O14", "LINE_TEXT", "upper density mean guide and 12/25 label", (411, 135, 427, 210), "111-113"),
    ("O15", "LINE_ARROW_TEXT", "vertical-slice normalization arrow and label", (231, 246, 323, 314), "149-151"),
    ("O16", "TEXT_FORMULA", "lower conditional-density formula block", (338, 198, 505, 270), "136-143"),
    ("O17", "AXIS", "lower conditional-density axes and t label", (334, 257, 493, 318), "127-129"),
    ("O18", "DATA_CURVE", "lower conditional-density dashed curve", (339, 271, 489, 320), "130-131"),
    ("O19", "LINE_TEXT", "lower density mean guide and 3/5 label", (418, 265, 427, 340), "132-134"),
    ("O20", "TEXT", "zero-marginal regular-conditional note text", (319, 351, 497, 389), "155"),
    ("O21", "PANEL_BORDER", "rounded red border of zero-marginal note", (309.4, 348.3, 501.7, 388.8), "153-155"),
    ("O22", "TEXT", "caption number 图33.2", (73, 391, 116, 408), "157"),
    ("O23", "TEXT", "two-line figure caption body", (118, 391, 534, 421), "157"),
]

object_rows = []
for oid, cls, desc, box, lines in objects:
    px = pbox(box)
    object_rows.append(
        {
            "OBJECT_ID": oid,
            "SEMANTIC_CLASS": cls,
            "DESCRIPTION": desc,
            "SOURCE_LINES": lines,
            "PDF_X0_PT": box[0],
            "PDF_Y0_PT": box[1],
            "PDF_X1_PT": box[2],
            "PDF_Y1_PT": box[3],
            "PX_X0": px[0],
            "PX_Y0": px[1],
            "PX_X1": px[2],
            "PX_Y1": px[3],
        }
    )
write_csv(
    ROOT / "object_denominator_machine.csv",
    object_rows,
    [
        "OBJECT_ID", "SEMANTIC_CLASS", "DESCRIPTION", "SOURCE_LINES",
        "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT",
        "PX_X0", "PX_Y0", "PX_X1", "PX_Y1",
    ],
)

pair_rows = []
for index, (a, b) in enumerate(itertools.combinations(object_rows, 2), start=1):
    ax0, ay0, ax1, ay1 = (a[k] for k in ("PX_X0", "PX_Y0", "PX_X1", "PX_Y1"))
    bx0, by0, bx1, by1 = (b[k] for k in ("PX_X0", "PX_Y0", "PX_X1", "PX_Y1"))
    gap_x = max(bx0 - ax1, ax0 - bx1, 0)
    gap_y = max(by0 - ay1, ay0 - by1, 0)
    pair_rows.append(
        {
            "PAIR_ID": f"P{index:03d}",
            "OBJECT_A": a["OBJECT_ID"],
            "OBJECT_B": b["OBJECT_ID"],
            "A_CLASS": a["SEMANTIC_CLASS"],
            "B_CLASS": b["SEMANTIC_CLASS"],
            "BBOX_INTERSECTS": str(gap_x == 0 and gap_y == 0).lower(),
            "BBOX_GAP_X_PX": gap_x,
            "BBOX_GAP_Y_PX": gap_y,
            "BBOX_AXIS_MIN_GAP_PX": min(gap_x, gap_y),
        }
    )
write_csv(
    ROOT / "pair_denominator_machine.csv",
    pair_rows,
    ["PAIR_ID", "OBJECT_A", "OBJECT_B", "A_CLASS", "B_CLASS", "BBOX_INTERSECTS", "BBOX_GAP_X_PX", "BBOX_GAP_Y_PX", "BBOX_AXIS_MIN_GAP_PX"],
)

# Text-element geometry and direct pixel measurements. Manual pass/fail fields are
# intentionally absent; the reviewer records those only after inspecting images.
texts = [
    ("T01", "joint", "formula", 94, "rho=3/5, a=1, b=4/5", "MATH_BASE", (154, 70, 254, 92)),
    ("T02", "joint", "formula", 96, "pi(x1,x2)=5/(8pi) exp[-25q/32]", "MATH_BASE", (133, 88, 299, 116)),
    ("T03", "joint", "formula", 98, "q=x1^2-(6/5)x1x2+x2^2", "MATH_BASE", (160, 111, 250, 136)),
    ("T04", "joint", "axis_label", 73, "x1", "MATH_BASE", (276, 214, 291, 231)),
    ("T05", "joint", "axis_label", 74, "x2", "MATH_BASE", (197, 137, 213, 154)),
    ("T06", "joint", "slice_label", 84, "x2=b=4/5", "MATH_BASE", (106, 162, 154, 190)),
    ("T07", "joint", "slice_label", 89, "x1=a=1", "MATH_BASE", (253, 128, 301, 146)),
    ("T08", "joint", "point_label", 93, "(a,b)", "MATH_BASE", (241, 158, 269, 174)),
    ("T09", "joint", "annotation", 100, "联合等高线：主轴45度，半轴...", "CJK_FULL", (101, 291, 309, 309)),
    ("T10", "map_top", "annotation", 147, "水平截面", "CJK_FULL", (277, 150, 320, 163)),
    ("T11", "map_top", "formula", 147, "÷m2(b)", "MATH_BASE", (280, 160, 318, 177)),
    ("T12", "cond_top", "formula", 116, "pi1(t|X2=b)=pi(t,b)/m2(b)", "MATH_BASE", (371, 69, 473, 95)),
    ("T13", "cond_top", "formula", 117, "N(12/25,16/25), m2(b)=phi(4/5)≈0.29>0", "MATH_BASE", (337, 91, 505, 116)),
    ("T14", "cond_top", "formula", 121, "integral pi1=1, max pi1=5/(4sqrt(2pi))", "MATH_BASE", (341, 112, 500, 141)),
    ("T15", "cond_top", "axis_label", 107, "t", "MATH_BASE", (487, 175, 493, 188)),
    ("T16", "cond_top", "numeric_label", 113, "12/25", "MATH_BASE", (412, 184, 426, 209)),
    ("T17", "map_bottom", "annotation", 150, "竖直截面", "CJK_FULL", (264, 248, 308, 260.2)),
    ("T18", "map_bottom", "formula", 150, "÷m1(a)", "MATH_BASE", (267, 258, 305, 274)),
    ("T19", "cond_bottom", "formula", 137, "pi2(t|X1=a)=pi(a,t)/m1(a)", "MATH_BASE", (370, 199, 474, 226)),
    ("T20", "cond_bottom", "formula", 138, "N(3/5,16/25), m1(a)=phi(1)≈0.242>0", "MATH_BASE", (339, 220, 505, 246)),
    ("T21", "cond_bottom", "formula", 142, "integral pi2=1, max pi2=5/(4sqrt(2pi))", "MATH_BASE", (341, 241, 500, 271)),
    ("T22", "cond_bottom", "axis_label", 128, "t", "MATH_BASE", (487, 305, 493, 318)),
    ("T23", "cond_bottom", "numeric_label", 134, "3/5", "MATH_BASE", (418, 314, 427, 340)),
    ("T24", "note", "annotation", 155, "若边缘分母为0：采用预先指定的可测", "CJK_FULL", (319, 351, 497, 364)),
    ("T25", "note", "annotation", 155, "正则条件版本，且仅在边缘几乎处处意", "CJK_FULL", (319, 363, 497, 376)),
    ("T26", "note", "annotation", 155, "义下唯一；本高斯例的两个分母均为正。", "CJK_FULL", (319, 375, 497, 387)),
    ("T27", "caption", "caption_number", 157, "图33.2", "CJK_FULL", (73, 390, 116, 409)),
    ("T28", "caption", "caption", 157, "同一二元正态联合密度...满条", "CJK_FULL", (117, 390, 534, 406)),
    ("T29", "caption", "caption", 157, "件密度；零边缘处须使用...版本。", "CJK_FULL", (73, 405, 429, 422)),
]

gray = ImageOps.grayscale(img)
pix = gray.load()


def ink_metrics(box: tuple[float, float, float, float]) -> tuple[int, int, int, int, int]:
    x0, y0, x1, y1 = pbox(box)
    # Local background is estimated from the four corners. A 20/255 contrast
    # threshold follows the Goal protocol and excludes very pale antialiasing.
    corners = [pix[x0, y0], pix[max(x0, x1 - 1), y0], pix[x0, max(y0, y1 - 1)], pix[max(x0, x1 - 1), max(y0, y1 - 1)]]
    bg = sorted(corners)[len(corners) // 2]
    ys = []
    xs = []
    for y in range(max(0, y0), min(gray.height, y1)):
        for x in range(max(0, x0), min(gray.width, x1)):
            if abs(int(pix[x, y]) - int(bg)) >= 20:
                xs.append(x)
                ys.append(y)
    if not ys:
        return bg, 0, x0, y0, 0
    return bg, max(ys) - min(ys) + 1, min(xs), min(ys), len(ys)


text_rows = []
for tid, panel, role, source_line, sample, script_class, box in texts:
    px = pbox(box)
    bg, h_ink, ink_x0, ink_y0, ink_count = ink_metrics(box)
    declared_pt = 9.6 if tid not in {"T27", "T28", "T29"} else "PDF_CAPTION_STYLE"
    effective_pt = 9.6 if tid not in {"T27", "T28", "T29"} else "PDF_EXTRACTED_SEPARATELY"
    text_rows.append(
        {
            "ELEMENT_ID": tid,
            "PANEL_ID": panel,
            "ROLE": role,
            "SOURCE_LINE": source_line,
            "DECLARED_PT": declared_pt,
            "GRAPHICS_SCALE": 1.0,
            "EFFECTIVE_PT": effective_pt,
            "TEXT_SAMPLE": sample,
            "SCRIPT_CLASS": script_class,
            "BBOX_X0": px[0],
            "BBOX_Y0": px[1],
            "BBOX_X1": px[2],
            "BBOX_Y1": px[3],
            "LOCAL_BG_GRAY": bg,
            "H_INK_PX_MACHINE": h_ink,
            "INK_TOP_X": ink_x0,
            "INK_TOP_Y": ink_y0,
            "FOREGROUND_PIXEL_COUNT": ink_count,
        }
    )
write_csv(
    ROOT / "text_elements_machine.csv",
    text_rows,
    [
        "ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_LINE", "DECLARED_PT",
        "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS",
        "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "LOCAL_BG_GRAY",
        "H_INK_PX_MACHINE", "INK_TOP_X", "INK_TOP_Y", "FOREGROUND_PIXEL_COUNT",
    ],
)

# Extracted vector spans provide an independent font/bbox machine record.
span_rows = []
for block_no, block in enumerate(page.get_text("dict")["blocks"]):
    for line_no, line in enumerate(block.get("lines", [])):
        for span_no, span in enumerate(line.get("spans", [])):
            x0, y0, x1, y1 = span["bbox"]
            if y0 <= 422:
                span_rows.append(
                    {
                        "BLOCK": block_no,
                        "LINE": line_no,
                        "SPAN": span_no,
                        "TEXT": span["text"],
                        "FONT": span["font"],
                        "SIZE_PT": round(span["size"], 4),
                        "FLAGS": span["flags"],
                        "PDF_X0_PT": round(x0, 3),
                        "PDF_Y0_PT": round(y0, 3),
                        "PDF_X1_PT": round(x1, 3),
                        "PDF_Y1_PT": round(y1, 3),
                    }
                )
write_csv(
    ROOT / "pdf_text_spans_machine.csv",
    span_rows,
    ["BLOCK", "LINE", "SPAN", "TEXT", "FONT", "SIZE_PT", "FLAGS", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT"],
)

# Semantic-object overlay.
overlay = img.copy()
draw = ImageDraw.Draw(overlay)
colors = {
    "TEXT_FORMULA": (190, 40, 40),
    "TEXT": (210, 90, 20),
    "AXIS": (80, 60, 190),
    "DATA_CURVE": (0, 135, 95),
    "LINE_ARROW_TEXT": (135, 60, 170),
    "MARKER_TEXT": (0, 100, 210),
    "LINE_TEXT": (30, 150, 180),
    "PANEL_BORDER": (210, 20, 120),
}
for row in object_rows:
    box = (row["PX_X0"], row["PX_Y0"], row["PX_X1"], row["PX_Y1"])
    color = colors[row["SEMANTIC_CLASS"]]
    draw.rectangle(box, outline=color, width=3)
    draw.rectangle((box[0], box[1], box[0] + 50, box[1] + 18), fill=(255, 255, 255))
    draw.text((box[0] + 2, box[1] + 1), row["OBJECT_ID"], fill=color)
overlay.crop(pbox((70, 65, 535, 422))).save(ROOT / "semantic_object_overlay_300dpi.png")

text_overlay = img.copy()
tdraw = ImageDraw.Draw(text_overlay)
for row in text_rows:
    box = (row["BBOX_X0"], row["BBOX_Y0"], row["BBOX_X1"], row["BBOX_Y1"])
    tdraw.rectangle(box, outline=(20, 145, 45), width=2)
    tdraw.rectangle((box[0], box[1], box[0] + 45, box[1] + 16), fill=(255, 255, 255))
    tdraw.text((box[0] + 1, box[1]), row["ELEMENT_ID"], fill=(20, 110, 35))
text_overlay.crop(pbox((70, 65, 535, 422))).save(ROOT / "text_measurement_overlay_300dpi.png")

# Critical native-pixel ROIs and exact nearest-neighbour 8x views.
rois = [
    ("R01_joint_point_and_slices", (228, 153, 274, 200)),
    ("R02_horizontal_arrowhead", (316, 171, 338, 193)),
    ("R03_vertical_arrowhead", (316, 301, 341, 324)),
    ("R04_upper_peak_curve_guide", (408, 139, 448, 190)),
    ("R05_lower_peak_curve_guide", (410, 268, 451, 321)),
    ("R06_note_border_text", (309, 345, 350, 374)),
    ("R07_caption_number_glyphs", (71, 388, 122, 412)),
    ("R08_upper_formula_fraction_radical", (454, 112, 503, 142)),
    ("R09_upper_mean_vs_lower_formula", (405, 180, 474, 226)),
]
roi_index_rows = []
for rid, box in rois:
    roi = crop_pt(box)
    p1 = ROOT / f"{rid}_1x_native_300dpi.png"
    p8 = ROOT / f"{rid}_8x_nearest.png"
    roi.save(p1)
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(p8)
    roi_index_rows.append(
        {
            "ROI_ID": rid,
            "PDF_X0_PT": box[0],
            "PDF_Y0_PT": box[1],
            "PDF_X1_PT": box[2],
            "PDF_Y1_PT": box[3],
            "ONE_X_FILE": p1.name,
            "EIGHT_X_FILE": p8.name,
            "ONE_X_WIDTH_PX": roi.width,
            "ONE_X_HEIGHT_PX": roi.height,
            "EIGHT_X_WIDTH_PX": roi.width * 8,
            "EIGHT_X_HEIGHT_PX": roi.height * 8,
        }
    )
write_csv(
    ROOT / "critical_roi_index_machine.csv",
    roi_index_rows,
    ["ROI_ID", "PDF_X0_PT", "PDF_Y0_PT", "PDF_X1_PT", "PDF_Y1_PT", "ONE_X_FILE", "EIGHT_X_FILE", "ONE_X_WIDTH_PX", "ONE_X_HEIGHT_PX", "EIGHT_X_WIDTH_PX", "EIGHT_X_HEIGHT_PX"],
)


def contact_sheet(paths: list[Path], output: Path, label: str) -> None:
    images = [Image.open(p).convert("RGB") for p in paths]
    tile_w = max(i.width for i in images) + 30
    tile_h = max(i.height for i in images) + 38
    rows = (len(images) + 1) // 2
    sheet = Image.new("RGB", (tile_w * 2, tile_h * rows), "white")
    d = ImageDraw.Draw(sheet)
    for idx, (path, im) in enumerate(zip(paths, images)):
        col, row = idx % 2, idx // 2
        x, y = col * tile_w + 15, row * tile_h + 24
        sheet.paste(im, (x, y))
        d.text((x, y - 18), f"{path.stem} [{label}]", fill="black")
    sheet.save(output)


contact_sheet([ROOT / r["ONE_X_FILE"] for r in roi_index_rows], ROOT / "critical_rois_1x_contact.png", "native 300 dpi")
contact_sheet([ROOT / r["EIGHT_X_FILE"] for r in roi_index_rows], ROOT / "critical_rois_8x_contact.png", "nearest-neighbour")

summary = {
    "objects": len(object_rows),
    "unordered_pairs": len(pair_rows),
    "text_elements": len(text_rows),
    "pdf_text_spans": len(span_rows),
    "critical_rois": len(roi_index_rows),
    "native_render_sha256": sha256(RENDER),
}
(ROOT / "machine_evidence_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print(json.dumps(summary, ensure_ascii=False))
