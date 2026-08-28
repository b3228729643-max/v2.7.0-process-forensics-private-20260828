from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r113_fullbook\main_full.pdf"
)
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_exponential_family_moments.tex"
)
PAGE = 713
EXPECTED_PDF_BYTES = 4_967_121
EXPECTED_PDF_SHA256 = "6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D"
EXPECTED_SOURCE_BYTES = 2_800
EXPECTED_SOURCE_SHA256 = "65F9C440D3058569C920F8C2E7E7B50545241EDAA6B6DAD4AA27EEF858324E6B"

VIEWS = ROOT / "views"
MACHINE = ROOT / "machine"
RISKS = VIEWS / "risks"
MASKS = VIEWS / "masks"

FIGURE_CROP = (270, 260, 2215, 1085)
DIAGRAM_CROP = (270, 260, 2215, 930)
PAGE_INTEGRATION_CROP = (190, 170, 2290, 1600)


OBJECTS = [
    ("O01", "left_panel_title", "LEFT", "HEADER", (420, 278, 1070, 365)),
    ("O02", "dirichlet_exponential_family_density", "LEFT", "FORMULA", (365, 382, 1165, 470)),
    ("O03", "density_decomposition_brace", "LEFT", "STRUCTURE", (310, 452, 1195, 520)),
    ("O04", "brace_explanation", "LEFT", "ANNOTATION", (455, 500, 1060, 575)),
    ("O05", "base_measure_card", "LEFT", "TERM_CARD", (305, 570, 730, 705)),
    ("O06", "natural_parameter_card", "LEFT", "TERM_CARD", (770, 570, 1205, 705)),
    ("O07", "sufficient_statistic_card", "LEFT", "TERM_CARD", (540, 735, 970, 875)),
    ("O08", "vertical_panel_divider", "GLOBAL", "PANEL_BORDER", (1264, 278, 1277, 925)),
    ("O09", "right_panel_title", "RIGHT", "HEADER", (1460, 278, 2200, 365)),
    ("O10", "log_partition_formula", "RIGHT", "FORMULA", (1450, 382, 2180, 480)),
    ("O11", "downward_implication_arrow", "RIGHT", "LINE_ARROW", (1760, 465, 1855, 555)),
    ("O12", "partial_derivative_formula", "RIGHT", "FORMULA", (1720, 535, 1900, 625)),
    ("O13", "expected_log_moment_result_card", "RIGHT", "RESULT_CARD", (1455, 625, 2145, 775)),
    ("O14", "mean_log_nonidentity_warning_card", "RIGHT", "WARNING_CARD", (1425, 800, 2175, 940)),
    ("O15", "caption_label", "CAPTION", "CAPTION_LABEL", (300, 945, 465, 1070)),
    ("O16", "caption_body", "CAPTION", "CAPTION_TEXT", (465, 940, 2210, 1080)),
]


TEXT_REGIONS = [
    ("T01", "left_title", "LEFT", "HEADER", (420, 278, 1070, 365)),
    ("T02", "density_formula", "LEFT", "FORMULA", (365, 382, 1165, 470)),
    ("T03", "brace_explanation", "LEFT", "ANNOTATION", (455, 500, 1060, 575)),
    ("T04", "base_measure_card_text", "LEFT", "TERM_TEXT", (350, 585, 690, 695)),
    ("T05", "natural_parameter_card_text", "LEFT", "TERM_TEXT", (820, 585, 1160, 695)),
    ("T06", "sufficient_statistic_card_text", "LEFT", "TERM_TEXT", (585, 750, 935, 865)),
    ("T07", "right_title", "RIGHT", "HEADER", (1460, 278, 2200, 365)),
    ("T08", "log_partition_formula", "RIGHT", "FORMULA", (1450, 382, 2180, 480)),
    ("T09", "down_arrow_glyph", "RIGHT", "SYMBOL", (1760, 465, 1855, 555)),
    ("T10", "partial_derivative", "RIGHT", "FORMULA", (1720, 535, 1900, 625)),
    ("T11", "expected_log_formula", "RIGHT", "FORMULA", (1510, 655, 2100, 755)),
    ("T12", "nonidentity_formula", "RIGHT", "FORMULA", (1500, 830, 2110, 920)),
    ("T13", "caption_label", "CAPTION", "CAPTION_LABEL", (300, 945, 465, 1070)),
    ("T14", "caption_body", "CAPTION", "CAPTION_TEXT", (465, 940, 2210, 1080)),
]


RISK_ROIS = [
    ("roi01_density_brace", (300, 350, 1220, 585)),
    ("roi02_left_cards", (285, 555, 1225, 900)),
    ("roi03_right_derivative_stack", (1405, 360, 2205, 955)),
    ("roi04_caption", (285, 925, 2215, 1090)),
    ("roi05_panel_gutter", (1125, 255, 1450, 955)),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ensure_input_identity() -> dict[str, object]:
    pdf_identity = {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)}
    source_identity = {"path": str(SOURCE), "bytes": SOURCE.stat().st_size, "sha256": sha256(SOURCE)}
    if pdf_identity["bytes"] != EXPECTED_PDF_BYTES or pdf_identity["sha256"] != EXPECTED_PDF_SHA256:
        raise RuntimeError("Frozen R113 PDF identity mismatch")
    if source_identity["bytes"] != EXPECTED_SOURCE_BYTES or source_identity["sha256"] != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Current figure-source identity mismatch")
    return {"physical_page": PAGE, "pdf": pdf_identity, "source": source_identity}


def font() -> ImageFont.ImageFont:
    for candidate in (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\consola.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), 24)
    return ImageFont.load_default()


def relbox(box: tuple[int, int, int, int], crop: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return box[0] - crop[0], box[1] - crop[1], box[2] - crop[0], box[3] - crop[1]


def bbox_metrics(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, float]:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = ix * iy
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    gap = (dx * dx + dy * dy) ** 0.5
    return intersection, gap


def foreground_measure(image: Image.Image, box: tuple[int, int, int, int]) -> dict[str, int | float]:
    roi = image.crop(box).convert("RGB")
    pixels = list(roi.getdata())
    border = []
    w, h = roi.size
    for x in range(w):
        border.append(roi.getpixel((x, 0)))
        border.append(roi.getpixel((x, h - 1)))
    for y in range(h):
        border.append(roi.getpixel((0, y)))
        border.append(roi.getpixel((w - 1, y)))
    bg = tuple(sorted(channel)[len(channel) // 2] for channel in zip(*border))
    coords = []
    for idx, px in enumerate(pixels):
        if max(abs(px[i] - bg[i]) for i in range(3)) >= 20:
            coords.append((idx % w, idx // w))
    if not coords:
        return {"foreground_pixels": 0, "ink_x0": 0, "ink_y0": 0, "ink_x1": 0, "ink_y1": 0, "ink_width_px": 0, "ink_height_px": 0, "background_r": bg[0], "background_g": bg[1], "background_b": bg[2]}
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    return {"foreground_pixels": len(coords), "ink_x0": x0, "ink_y0": y0, "ink_x1": x1, "ink_y1": y1, "ink_width_px": x1 - x0, "ink_height_px": y1 - y0, "background_r": bg[0], "background_g": bg[1], "background_b": bg[2]}


def main() -> None:
    RISKS.mkdir(parents=True, exist_ok=True)
    MASKS.mkdir(parents=True, exist_ok=True)
    identity = ensure_input_identity()
    (MACHINE / "input_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    full = Image.open(VIEWS / "full_page_300dpi.png").convert("RGB")
    if full.size != (2481, 3508):
        raise RuntimeError(f"Unexpected 300 dpi page size: {full.size}")
    figure = full.crop(FIGURE_CROP)
    diagram = full.crop(DIAGRAM_CROP)
    integration = full.crop(PAGE_INTEGRATION_CROP)
    figure.save(VIEWS / "native_figure_300dpi.png")
    diagram.save(VIEWS / "native_diagram_300dpi.png")
    integration.save(VIEWS / "page_integration_300dpi.png")
    ImageOps.grayscale(figure).save(VIEWS / "native_figure_grayscale_300dpi.png")
    ImageOps.grayscale(full).save(VIEWS / "full_page_grayscale_300dpi.png")

    for roi_id, box in RISK_ROIS:
        roi = full.crop(box)
        roi.save(RISKS / f"{roi_id}_native1x.png")
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(RISKS / f"{roi_id}_nn8x.png")

    label_font = font()
    object_overlay = figure.copy()
    od = ImageDraw.Draw(object_overlay)
    palette = {"LEFT": "#0067b1", "RIGHT": "#a33b20", "GLOBAL": "#663399", "CAPTION": "#138a55"}
    for oid, name, panel, role, box in OBJECTS:
        rb = relbox(box, FIGURE_CROP)
        color = palette[panel]
        od.rectangle(rb, outline=color, width=4)
        od.rectangle((rb[0], rb[1], rb[0] + 66, rb[1] + 28), fill="white", outline=color, width=2)
        od.text((rb[0] + 3, rb[1] + 1), oid, fill=color, font=label_font)
    object_overlay.save(VIEWS / "semantic_object_overlay_300dpi.png")

    text_overlay = figure.copy()
    td = ImageDraw.Draw(text_overlay)
    for tid, name, panel, role, box in TEXT_REGIONS:
        rb = relbox(box, FIGURE_CROP)
        td.rectangle(rb, outline="#c000c0", width=3)
        td.rectangle((rb[0], rb[3] - 30, rb[0] + 66, rb[3]), fill="white", outline="#c000c0", width=2)
        td.text((rb[0] + 3, rb[3] - 28), tid, fill="#8b008b", font=label_font)
    text_overlay.save(VIEWS / "text_glyph_overlay_300dpi.png")

    reading = figure.copy()
    rd = ImageDraw.Draw(reading)
    routes = [
        ("L", ["O01", "O02", "O03", "O04", "O05", "O06", "O07"]),
        ("R", ["O09", "O10", "O11", "O12", "O13", "O14"]),
        ("C", ["O15", "O16"]),
    ]
    object_map = {row[0]: row[4] for row in OBJECTS}
    route_colors = {"L": "#0067b1", "R": "#a33b20", "C": "#138a55"}
    for rid, ids in routes:
        color = route_colors[rid]
        for sequence, oid in enumerate(ids, start=1):
            b = object_map[oid]
            x = b[0] - FIGURE_CROP[0] + 4
            y = b[1] - FIGURE_CROP[1] + 4
            rd.rectangle((x, y, x + 54, y + 30), fill="white", outline=color, width=3)
            rd.text((x + 3, y + 1), f"{rid}{sequence}", fill=color, font=label_font)
    reading.save(VIEWS / "reading_order_overlay_300dpi.png")

    gray = ImageOps.grayscale(figure)
    threshold = gray.point(lambda value: 255 if value < 235 else 0)
    threshold.save(MASKS / "foreground_threshold_mask_300dpi.png")

    with (MACHINE / "object_bboxes_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["object_id", "machine_name", "panel", "machine_role", "x0_px", "y0_px", "x1_px", "y1_px"])
        for oid, name, panel, role, box in OBJECTS:
            writer.writerow([oid, name, panel, role, *box])

    with (MACHINE / "all_unordered_object_pairs_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["pair_id", "object_a", "object_b", "bbox_intersection_px2", "bbox_edge_gap_px"])
        for idx, (a, b) in enumerate(itertools.combinations(OBJECTS, 2), start=1):
            intersection, gap = bbox_metrics(a[4], b[4])
            writer.writerow([f"P{idx:03d}", a[0], b[0], intersection, f"{gap:.3f}"])

    with (MACHINE / "text_region_measurements_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        header = ["text_id", "machine_name", "panel", "machine_role", "region_x0_px", "region_y0_px", "region_x1_px", "region_y1_px", "foreground_threshold_delta_255", "foreground_pixels", "ink_x0_local", "ink_y0_local", "ink_x1_local", "ink_y1_local", "ink_width_px", "ink_height_px", "background_r", "background_g", "background_b"]
        writer.writerow(header)
        for tid, name, panel, role, box in TEXT_REGIONS:
            measure = foreground_measure(full, box)
            writer.writerow([tid, name, panel, role, *box, 20, *measure.values()])

    with (MACHINE / "image_properties_machine.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["view", "width_px", "height_px", "mode"])
        for path in sorted(VIEWS.rglob("*.png")):
            with Image.open(path) as image:
                writer.writerow([path.relative_to(ROOT).as_posix(), image.width, image.height, image.mode])

    pdftotext = Path(r"D:\texlive\2026\bin\windows\pdftotext.exe")
    result = subprocess.run(
        [str(pdftotext), "-f", str(PAGE), "-l", str(PAGE), "-layout", str(PDF), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    text = result.stdout.decode("utf-8", errors="strict").replace("\r\n", "\n")
    (MACHINE / "page_713_text.txt").write_text(text, encoding="utf-8", newline="\n")
    fingerprint = {
        "replacement_character_count": text.count("\ufffd"),
        "caption_anchor_count": text.count("图 34.6"),
        "dirichlet_count": text.count("Dirichlet"),
        "expected_log_theta_count": text.count("𝔼[log Θ"),
        "page_form_feed_count": text.count("\f"),
    }
    (MACHINE / "page_713_text_fingerprint.json").write_text(json.dumps(fingerprint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
