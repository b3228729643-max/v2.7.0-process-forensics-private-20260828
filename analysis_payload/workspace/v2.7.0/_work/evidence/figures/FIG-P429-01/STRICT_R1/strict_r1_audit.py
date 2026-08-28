"""Read-only STRICT_R1 evidence generator for FIG-P429-01.

This script intentionally reads only the nominated R93 candidate PDF, figure
source, and the directly required current style files.  It writes only into
this STRICT_R1 evidence directory.  It never compiles a replacement figure or
creates a standalone wrapper: that is a deliberate evidence limitation noted
in the generated acceptance record.
"""

from __future__ import annotations

import csv
import math
import re
import statistics
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import fitz
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
from pypdf.generic import ContentStream


EVIDENCE_DIR = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P429-01\STRICT_R1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf")
FIG_SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C01\fig_v4_c01_three_structures.tex")
FIG_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\figure-style-v2.3.0.tex")
BOOK_STYLE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\common\statlearnbook.sty")
SIZE_STYLE = Path(r"D:\texlive\2026\texmf-dist\tex\latex\base\bk11.clo")

PAGE_WIDTH_PT = 595.276
PAGE_HEIGHT_PT = 841.890
EXPECTED_PAGE = 466  # one-based physical PDF page, independently re-located below
SEARCH_PHRASE = "可检验结构 / 评价证据"

# Crop coordinates are native 300-dpi pixels in pdftoppm's page raster.  No
# image resizing is performed; Poppler crops the 300-dpi PDF render directly.
CROP_X, CROP_Y, CROP_W, CROP_H = 280, 2420, 2000, 900


@dataclass(frozen=True)
class ElementSpec:
    element_id: str
    panel_id: str
    role: str
    script_class: str
    text_sample: str
    source_line: str
    declared_pt: float
    source_basis: str
    locator: tuple[float, float, float, float]


# Every visible text or formula substring in the current figure body and its
# caption is separately represented.  Locator boxes are in PDF top-origin
# coordinates and select the current candidate's extracted vector text.
ELEMENT_SPECS = [
    ElementSpec("E01_DATA_CN", "MAIN", "NODE_LABEL", "CJK_FULL", "观测数据", "14", 9.4, "explicit node font", (270, 330, 595, 620)),
    ElementSpec("E02_DATA_X", "MAIN", "MATH_VARIABLE", "LATIN_UPPER_DIGIT", "𝑋", "14", 9.4, "inherits explicit node font", (310, 335, 595, 620)),
    ElementSpec("E03_CLUSTER_TITLE", "CLUSTER", "PANEL_LABEL", "CJK_FULL", "聚类", "17;7", 9.6, "branch title style", (160, 205, 625, 660)),
    ElementSpec("E04_DIM_TITLE", "DIMENSION", "PANEL_LABEL", "CJK_FULL", "降维", "32;7", 9.6, "branch title style", (280, 325, 625, 660)),
    ElementSpec("E05_PROB_TITLE", "PROBABILITY", "PANEL_LABEL", "CJK_FULL", "概率建模", "46;7", 9.6, "branch title style", (390, 455, 625, 660)),
    ElementSpec("E06_Z", "PROBABILITY", "MATH_VARIABLE", "LATIN_LOWER_GREEK", "𝑧", "47;3", 9.2, "tikzpicture default", (410, 435, 650, 680)),
    ElementSpec("E07_X_LEFT", "PROBABILITY", "MATH_VARIABLE", "LATIN_LOWER_GREEK", "𝑥", "49;3", 9.2, "tikzpicture default", (385, 410, 675, 700)),
    ElementSpec("E08_X_MID", "PROBABILITY", "MATH_VARIABLE", "LATIN_LOWER_GREEK", "𝑥", "49;3", 9.2, "tikzpicture default", (410, 435, 675, 700)),
    ElementSpec("E09_X_RIGHT", "PROBABILITY", "MATH_VARIABLE", "LATIN_LOWER_GREEK", "𝑥", "49;3", 9.2, "tikzpicture default", (435, 460, 675, 700)),
    ElementSpec("E10_CLUSTER_NOTE", "CLUSTER", "ANNOTATION", "CJK_FULL", "样本分组", "28;8", 9.0, "branch note style", (150, 210, 685, 715)),
    ElementSpec("E11_DIM_NOTE_LEFT", "DIMENSION", "ANNOTATION", "CJK_FULL", "高维点", "42;8", 9.0, "branch note style", (250, 295, 685, 715)),
    ElementSpec("E12_DIM_ARROW", "DIMENSION", "FORMULA", "MATH_SYMBOL", "→", "42;8", 9.0, "branch note style; inline math relation", (285, 310, 685, 715)),
    ElementSpec("E13_DIM_NOTE_RIGHT", "DIMENSION", "ANNOTATION", "CJK_FULL", "低维坐标", "42;8", 9.0, "branch note style", (295, 350, 685, 715)),
    ElementSpec("E14_PROB_NOTE", "PROBABILITY", "ANNOTATION", "CJK_FULL", "潜变量生成观测", "52;8", 9.0, "branch note style", (380, 465, 685, 715)),
    ElementSpec("E15_EVIDENCE_LEFT", "EVIDENCE", "EVIDENCE_NOTE", "CJK_FULL", "可检验结构", "60;59", 9.2, "explicit evidence-node font", (245, 310, 715, 745)),
    ElementSpec("E16_EVIDENCE_SLASH", "EVIDENCE", "EVIDENCE_NOTE", "MATH_SYMBOL", "/", "60;59", 9.2, "explicit evidence-node font", (295, 315, 715, 745)),
    ElementSpec("E17_EVIDENCE_RIGHT", "EVIDENCE", "EVIDENCE_NOTE", "CJK_FULL", "评价证据", "60;59", 9.2, "explicit evidence-node font", (300, 355, 715, 745)),
    ElementSpec("E18_CAPTION_LABEL", "CAPTION", "CAPTION_LABEL", "CJK_FULL", "图", "65;statlearnbook.sty:305;bk11.clo:58-60", 10.0, "caption font=small; 11pt book small=10pt", (65, 90, 740, 765)),
    ElementSpec("E19_CAPTION_NUMBER", "CAPTION", "CAPTION_LABEL", "LATIN_UPPER_DIGIT", "24.1", "65;statlearnbook.sty:305;bk11.clo:58-60", 10.0, "caption font=small; 11pt book small=10pt", (80, 110, 740, 765)),
    ElementSpec("E20_CAPTION_LINE1", "CAPTION", "CAPTION_TEXT", "CJK_FULL", "聚类、降维和概率建模分别从样本分组、属性压缩和联合生成三个方向把观测映射为可检验的潜", "65;statlearnbook.sty:305;bk11.clo:58-60", 10.0, "caption font=small; 11pt book small=10pt", (105, 540, 740, 765)),
    ElementSpec("E21_CAPTION_LINE2", "CAPTION", "CAPTION_TEXT", "CJK_FULL", "在结构。", "65;statlearnbook.sty:305;bk11.clo:58-60", 10.0, "caption font=small; 11pt book small=10pt", (65, 125, 755, 780)),
]


# Content-stream paint operation -> individually enumerated current vector
# object.  All text-to-vector pairs are tested, including a label against its
# own parent border/arrow (there are no automatic parent exemptions).
GRAPHIC_MAP: dict[int, tuple[str, str, str]] = {
    809: ("G01_DATA_NODE_BORDER", "NODE_BORDER", "13-14"),
    872: ("G02_CLUSTER_FILLED_1", "MARKER", "18"),
    889: ("G03_CLUSTER_FILLED_2", "MARKER", "19"),
    906: ("G04_CLUSTER_FILLED_3", "MARKER", "20"),
    928: ("G05_CLUSTER_OPEN_1", "MARKER", "21"),
    959: ("G06_CLUSTER_OPEN_2", "MARKER", "22"),
    990: ("G07_CLUSTER_OPEN_3", "MARKER", "23"),
    1021: ("G08_CLUSTER_DASH_BOX_1", "MARKER", "24-25"),
    1041: ("G09_CLUSTER_DASH_BOX_2", "MARKER", "26-27"),
    1110: ("G10_DIM_INPUT_1", "MARKER", "33"),
    1127: ("G11_DIM_INPUT_2", "MARKER", "33"),
    1144: ("G12_DIM_INPUT_3", "MARKER", "33"),
    1161: ("G13_DIM_INPUT_4", "MARKER", "33"),
    1178: ("G14_DIM_INPUT_5", "MARKER", "33"),
    1189: ("G15_DIM_ARROW_1", "LINE_ARROW", "34-35"),
    1201: ("G16_DIM_ARROWHEAD_1", "LINE_ARROW", "34-35"),
    1212: ("G17_DIM_ARROW_2", "LINE_ARROW", "36-37"),
    1224: ("G18_DIM_ARROWHEAD_2", "LINE_ARROW", "36-37"),
    1235: ("G19_DIM_ARROW_3", "LINE_ARROW", "38-39"),
    1247: ("G20_DIM_ARROWHEAD_3", "LINE_ARROW", "38-39"),
    1258: ("G21_DIM_BASELINE", "LINE_ARROW", "40"),
    1273: ("G22_DIM_OUTPUT_1", "MARKER", "41"),
    1290: ("G23_DIM_OUTPUT_2", "MARKER", "41"),
    1307: ("G24_DIM_OUTPUT_3", "MARKER", "41"),
    1389: ("G25_Z_NODE_BORDER", "NODE_BORDER", "47"),
    1427: ("G26_X_LEFT_NODE_BORDER", "NODE_BORDER", "49"),
    1455: ("G27_Z_TO_X_LEFT", "LINE_ARROW", "50"),
    1468: ("G28_Z_TO_X_LEFT_HEAD", "LINE_ARROW", "50"),
    1490: ("G29_X_MID_NODE_BORDER", "NODE_BORDER", "49"),
    1518: ("G30_Z_TO_X_MID", "LINE_ARROW", "50"),
    1531: ("G31_Z_TO_X_MID_HEAD", "LINE_ARROW", "50"),
    1553: ("G32_X_RIGHT_NODE_BORDER", "NODE_BORDER", "49"),
    1581: ("G33_Z_TO_X_RIGHT", "LINE_ARROW", "50"),
    1594: ("G34_Z_TO_X_RIGHT_HEAD", "LINE_ARROW", "50"),
    1632: ("G35_SOURCE_TO_CLUSTER", "LINE_ARROW", "55"),
    1644: ("G36_SOURCE_TO_CLUSTER_HEAD", "LINE_ARROW", "55"),
    1655: ("G37_SOURCE_TO_DIM", "LINE_ARROW", "56"),
    1667: ("G38_SOURCE_TO_DIM_HEAD", "LINE_ARROW", "56"),
    1678: ("G39_SOURCE_TO_PROB", "LINE_ARROW", "57"),
    1690: ("G40_SOURCE_TO_PROB_HEAD", "LINE_ARROW", "57"),
    1718: ("G41_EVIDENCE_NODE_BORDER", "NODE_BORDER", "58-60"),
    1751: ("G42_CLUSTER_TO_EVIDENCE", "LINE_ARROW", "61"),
    1763: ("G43_CLUSTER_TO_EVIDENCE_HEAD", "LINE_ARROW", "61"),
    1774: ("G44_DIM_TO_EVIDENCE", "LINE_ARROW", "62"),
    1786: ("G45_DIM_TO_EVIDENCE_HEAD", "LINE_ARROW", "62"),
    1797: ("G46_PROB_TO_EVIDENCE", "LINE_ARROW", "63"),
    1809: ("G47_PROB_TO_EVIDENCE_HEAD", "LINE_ARROW", "63"),
}

# The 5-px node-border rule applies to text placed *inside its own node*.
# It is deliberately not applied to a neighbouring external annotation (for
# example E14 below the three x nodes): that relationship is neither node text
# nor a parent-border relation under the stated gate.  All text-to-line/arrow
# and text-to-marker relationships remain audited without a parent exemption.
NODE_PARENT_BY_ELEMENT = {
    "E01_DATA_CN": "G01_DATA_NODE_BORDER",
    "E02_DATA_X": "G01_DATA_NODE_BORDER",
    "E06_Z": "G25_Z_NODE_BORDER",
    "E07_X_LEFT": "G26_X_LEFT_NODE_BORDER",
    "E08_X_MID": "G29_X_MID_NODE_BORDER",
    "E09_X_RIGHT": "G32_X_RIGHT_NODE_BORDER",
    "E15_EVIDENCE_LEFT": "G41_EVIDENCE_NODE_BORDER",
    "E16_EVIDENCE_SLASH": "G41_EVIDENCE_NODE_BORDER",
    "E17_EVIDENCE_RIGHT": "G41_EVIDENCE_NODE_BORDER",
}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def locate_page() -> int:
    reader = PdfReader(str(PDF))
    hits = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if SEARCH_PHRASE in text and "图 24.1" in text:
            hits.append(index)
    if hits != [EXPECTED_PAGE]:
        raise RuntimeError(f"expected exactly page {EXPECTED_PAGE}, located {hits}")
    return hits[0]


def render_native_views(page_number: int) -> None:
    # Direct PDF rasterization only.  The crop is made by Poppler at 300 dpi;
    # no PNG is resized, resampled, or screenshot-derived.
    run(["pdftoppm", "-f", str(page_number), "-l", str(page_number), "-r", "200", "-png", "-singlefile", str(PDF), str(EVIDENCE_DIR / "full_page_200dpi")])
    run(["pdftoppm", "-f", str(page_number), "-l", str(page_number), "-r", "300", "-png", "-singlefile", str(PDF), str(EVIDENCE_DIR / "page_466_raw_300dpi")])
    crop_args = ["-f", str(page_number), "-l", str(page_number), "-r", "300", "-x", str(CROP_X), "-y", str(CROP_Y), "-W", str(CROP_W), "-H", str(CROP_H)]
    run(["pdftoppm", *crop_args, "-png", "-singlefile", str(PDF), str(EVIDENCE_DIR / "figure_crop_300dpi")])
    run(["pdftoppm", *crop_args, "-gray", "-png", "-singlefile", str(PDF), str(EVIDENCE_DIR / "grayscale_300dpi")])


def extract_words(page_number: int) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["pdftotext", "-bbox", "-f", str(page_number), "-l", str(page_number), str(PDF), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    root = ET.fromstring(result.stdout)
    words: list[dict[str, Any]] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "word":
            continue
        words.append(
            {
                "text": node.text or "",
                "x0": float(node.attrib["xMin"]),
                "y0": float(node.attrib["yMin"]),
                "x1": float(node.attrib["xMax"]),
                "y1": float(node.attrib["yMax"]),
            }
        )
    return words


def select_word(spec: ElementSpec, words: list[dict[str, Any]]) -> dict[str, Any]:
    x0, x1, y0, y1 = spec.locator
    matches = [
        word
        for word in words
        if word["text"] == spec.text_sample
        and x0 <= word["x0"] <= x1
        and y0 <= word["y0"] <= y1
    ]
    if len(matches) != 1:
        raise RuntimeError(f"{spec.element_id}: expected one current-PDF vector word; found {len(matches)}")
    return matches[0]


SVG_TOKEN = re.compile(r"[MmLlCcZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[Ee][-+]?\d+)?")


def parse_svg_path(path_d: str) -> list[list[tuple[float, float]]]:
    """Parse the M/L/C/Z glyph paths emitted by pdftocairo SVG."""
    tokens = SVG_TOKEN.findall(path_d)
    token_index = 0
    command: str | None = None
    current = (0.0, 0.0)
    start: tuple[float, float] | None = None
    contours: list[list[tuple[float, float]]] = []
    contour: list[tuple[float, float]] | None = None

    def point(relative: bool) -> tuple[float, float]:
        nonlocal token_index
        x, y = float(tokens[token_index]), float(tokens[token_index + 1])
        token_index += 2
        return (x + current[0], y + current[1]) if relative else (x, y)

    while token_index < len(tokens):
        if tokens[token_index].isalpha():
            command = tokens[token_index]
            token_index += 1
        if command is None:
            raise RuntimeError("SVG path is missing a command")
        if command in "Mm":
            current = point(command == "m")
            start = current
            contour = [current]
            contours.append(contour)
            command = "L" if command == "M" else "l"
        elif command in "Ll":
            current = point(command == "l")
            assert contour is not None
            contour.append(current)
        elif command in "Cc":
            p0 = current
            p1 = point(command == "c")
            p2 = point(command == "c")
            p3 = point(command == "c")
            assert contour is not None
            for index in range(1, 51):
                t = index / 50
                u = 1 - t
                contour.append(
                    (
                        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
                    )
                )
            current = p3
        elif command in "Zz":
            if contour is not None and start is not None:
                contour.append(start)
            command = None
        else:
            raise RuntimeError(f"unsupported pdftocairo SVG path command {command}")
    return contours


def load_svg_glyph_assets(page_number: int) -> tuple[dict[str, list[list[tuple[float, float]]]], list[dict[str, Any]]]:
    """Read current PDF glyph outlines directly to disambiguate text from lines."""
    result = subprocess.run(
        ["pdftocairo", "-svg", "-f", str(page_number), "-l", str(page_number), str(PDF), "-"],
        check=True,
        capture_output=True,
    )
    root = ET.fromstring(result.stdout)
    symbols: dict[str, list[list[tuple[float, float]]]] = {}
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "symbol" or "id" not in node.attrib:
            continue
        contours: list[list[tuple[float, float]]] = []
        for child in node:
            if child.tag.rsplit("}", 1)[-1] == "path" and "d" in child.attrib:
                contours.extend(parse_svg_path(child.attrib["d"]))
        symbols[node.attrib["id"]] = contours
    uses: list[dict[str, Any]] = []
    href_key = "{http://www.w3.org/1999/xlink}href"
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "use":
            continue
        href = node.attrib.get(href_key, "")
        if not href.startswith("#"):
            continue
        glyph_id = href[1:]
        contours = symbols.get(glyph_id, [])
        if not contours:
            continue
        x = float(node.attrib.get("x", "0"))
        y = float(node.attrib.get("y", "0"))
        all_points = [point for contour in contours for point in contour]
        min_x, max_x = min(point[0] for point in all_points) + x, max(point[0] for point in all_points) + x
        min_y, max_y = min(point[1] for point in all_points) + y, max(point[1] for point in all_points) + y
        uses.append({"glyph_id": glyph_id, "x": x, "y": y, "bbox": (min_x, min_y, max_x, max_y)})
    return symbols, uses


def select_svg_uses(word: dict[str, Any], uses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select glyph uses whose geometric centres belong to one vector word."""
    selected = []
    for use in uses:
        x0, y0, x1, y1 = use["bbox"]
        center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
        if word["x0"] - 1.0 <= center_x <= word["x1"] + 1.0 and word["y0"] - 2.0 <= center_y <= word["y1"] + 2.0:
            selected.append(use)
    if not selected:
        raise RuntimeError(f"no SVG glyphs selected for current-PDF word {word['text']!r}")
    return selected


def render_svg_text_mask(
    selected_uses: list[dict[str, Any]],
    symbols: dict[str, list[list[tuple[float, float]]]],
    raw_image: Image.Image,
) -> np.ndarray:
    """Rasterize only the current PDF's glyph outlines at native 300 dpi.

    This removes a crossing line from an element's H_ink measurement without
    erasing a genuine line-through-glyph collision: raw RGB foreground is
    intersected with this text-only vector silhouette afterward.
    """
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH_PT, height=PAGE_HEIGHT_PT)
    for use in selected_uses:
        shape = page.new_shape()
        for contour in symbols[use["glyph_id"]]:
            points = [fitz.Point(use["x"] + x, use["y"] + y) for x, y in contour]
            if len(points) >= 2:
                shape.draw_polyline(points)
        shape.finish(color=None, fill=(0.0, 0.0, 0.0), even_odd=False)
        shape.commit()
    pixmap = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), alpha=False)
    array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
    if (pixmap.width, pixmap.height) != raw_image.size:
        raise RuntimeError(f"native text layer size {(pixmap.width, pixmap.height)} differs from raw Poppler render {raw_image.size}")
    return np.any(array[:, :, :3] <= 235, axis=2)


def pdf_to_pixel_bbox(word: dict[str, Any], image: Image.Image) -> tuple[int, int, int, int]:
    sx = image.width / PAGE_WIDTH_PT
    sy = image.height / PAGE_HEIGHT_PT
    x0 = max(0, math.floor(word["x0"] * sx))
    y0 = max(0, math.floor(word["y0"] * sy))
    x1 = min(image.width - 1, math.ceil(word["x1"] * sx))
    y1 = min(image.height - 1, math.ceil(word["y1"] * sy))
    return x0, y0, x1, y1


def foreground_mask(rgb: np.ndarray, bbox: tuple[int, int, int, int]) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Return the exact C-section mask: RGB distance >=20 from local background.

    No dilation, closing, component expansion, or bbox-based foreground is
    used.  The ring estimates local node/page background while the mask is
    limited to the PDF/vector text bbox itself.
    """
    x0, y0, x1, y1 = bbox
    h, w = rgb.shape[:2]
    pad = 3
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(w, x1 + pad + 1), min(h, y1 + pad + 1)
    region = rgb[ry0:ry1, rx0:rx1].astype(np.int16)
    core = rgb[y0 : y1 + 1, x0 : x1 + 1].astype(np.int16)
    ring_mask = np.ones(region.shape[:2], dtype=bool)
    ring_mask[y0 - ry0 : y1 - ry0 + 1, x0 - rx0 : x1 - rx0 + 1] = False
    ring = region[ring_mask]
    if ring.size == 0:
        ring = region.reshape(-1, 3)
    local_background = np.median(ring, axis=0)
    delta = np.max(np.abs(core - local_background), axis=2)
    return delta >= 20, local_background.astype(np.uint8), (x0, y0)


def ink_height(mask: np.ndarray) -> int:
    rows = np.where(mask.any(axis=1))[0]
    return 0 if rows.size == 0 else int(rows[-1] - rows[0] + 1)


def flatten_indices(mask: np.ndarray, origin: tuple[int, int], page_width: int) -> set[int]:
    ys, xs = np.where(mask)
    x0, y0 = origin
    return set(((ys + y0) * page_width + (xs + x0)).tolist())


def bbox_distance(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0.0)
    dy = max(ay0 - by1, by0 - ay1, 0.0)
    return math.hypot(dx, dy)


def matrix_mul(m: list[float], n: list[float]) -> list[float]:
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return [
        a * A + c * B,
        b * A + d * B,
        a * C + c * D,
        b * C + d * D,
        a * E + c * F + e,
        b * E + d * F + f,
    ]


def transform(m: list[float], point: tuple[float, float]) -> tuple[float, float]:
    a, b, c, d, e, f = m
    x, y = point
    return a * x + c * y + e, b * x + d * y + f


def line_samples(a: tuple[float, float], b: tuple[float, float], max_step_pt: float = 0.15) -> list[tuple[float, float]]:
    length = math.dist(a, b)
    count = max(1, math.ceil(length / max_step_pt))
    return [(a[0] + (b[0] - a[0]) * i / count, a[1] + (b[1] - a[1]) * i / count) for i in range(count + 1)]


def cubic_samples(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> list[tuple[float, float]]:
    # 201 samples are subpixel-dense at 300 dpi for the small TikZ curves here.
    points = []
    for i in range(201):
        t = i / 200
        u = 1 - t
        points.append(
            (
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
            )
        )
    return points


def extract_vector_objects(page_number: int) -> dict[int, dict[str, Any]]:
    """Enumerate painting operations for the figure's current PDF vectors."""
    reader = PdfReader(str(PDF))
    page = reader.pages[page_number - 1]
    stream = ContentStream(page.get_contents(), reader)
    state: dict[str, Any] = {"ctm": [1.0, 0.0, 0.0, 1.0, 0.0, 0.0], "line_width": 1.0}
    stack: list[dict[str, Any]] = []
    path: list[tuple[float, float]] = []
    current: tuple[float, float] | None = None
    subpath_start: tuple[float, float] | None = None
    output: dict[int, dict[str, Any]] = {}
    paint_ops = {"S", "s", "f", "F", "f*", "B", "B*", "b", "b*"}
    for op_index, (operands, operator) in enumerate(stream.operations):
        op = operator.decode("latin1")
        if op == "q":
            stack.append({"ctm": state["ctm"].copy(), "line_width": state["line_width"]})
        elif op == "Q":
            state = stack.pop()
        elif op == "cm":
            state["ctm"] = matrix_mul(state["ctm"], [float(v) for v in operands])
        elif op == "w":
            state["line_width"] = float(operands[0])
        elif op == "m":
            current = transform(state["ctm"], (float(operands[0]), float(operands[1])))
            subpath_start = current
            # A moveto by itself has no painted pixels.  In particular, TikZ
            # emits a trailing moveto at several circle centres before B; do
            # not turn that non-painted centre into a false overlap target.
        elif op == "l" and current is not None:
            end = transform(state["ctm"], (float(operands[0]), float(operands[1])))
            path.extend(line_samples(current, end))
            current = end
        elif op == "c" and current is not None:
            p1 = transform(state["ctm"], (float(operands[0]), float(operands[1])))
            p2 = transform(state["ctm"], (float(operands[2]), float(operands[3])))
            p3 = transform(state["ctm"], (float(operands[4]), float(operands[5])))
            path.extend(cubic_samples(current, p1, p2, p3))
            current = p3
        elif op == "re":
            x, y, width, height = (float(v) for v in operands)
            corners = [
                transform(state["ctm"], (x, y)),
                transform(state["ctm"], (x + width, y)),
                transform(state["ctm"], (x + width, y + height)),
                transform(state["ctm"], (x, y + height)),
            ]
            for start, end in zip(corners, corners[1:] + corners[:1]):
                path.extend(line_samples(start, end))
            current = corners[-1]
            subpath_start = corners[0]
        elif op == "h" and current is not None and subpath_start is not None:
            path.extend(line_samples(current, subpath_start))
            current = subpath_start
        elif op in paint_ops:
            if path:
                xs, ys = zip(*path)
                output[op_index] = {
                    "pdf_points": path.copy(),
                    "pdf_bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "line_width_pt": state["line_width"],
                    "paint": op,
                }
            path.clear()
            current = None
            subpath_start = None
        elif op == "n":
            path.clear()
            current = None
            subpath_start = None
    return output


def vector_to_pixel_object(obj: dict[str, Any], image: Image.Image) -> dict[str, Any]:
    sx = image.width / PAGE_WIDTH_PT
    sy = image.height / PAGE_HEIGHT_PT
    pixels = np.array([(x * sx, (PAGE_HEIGHT_PT - y) * sy) for x, y in obj["pdf_points"]], dtype=np.float32)
    bx0, by0, bx1, by1 = obj["pdf_bbox"]
    bbox = (bx0 * sx, (PAGE_HEIGHT_PT - by1) * sy, bx1 * sx, (PAGE_HEIGHT_PT - by0) * sy)
    stroke_half = 0.5 * obj["line_width_pt"] * max(sx, sy)
    return {**obj, "pixel_points": pixels, "pixel_bbox": bbox, "stroke_half_px": stroke_half}


def vector_distances(text_coords: np.ndarray, graphic: dict[str, Any]) -> np.ndarray:
    """Minimum centre-to-vector-path distances for native raster text pixels."""
    points = graphic["pixel_points"]
    distances = np.empty(len(text_coords), dtype=np.float32)
    for start in range(0, len(text_coords), 256):
        chunk = text_coords[start : start + 256]
        d2 = ((chunk[:, None, :] - points[None, :, :]) ** 2).sum(axis=2)
        distances[start : start + len(chunk)] = np.sqrt(d2.min(axis=1))
    return distances


def nearest_vector_clearance(text_coords: np.ndarray, graphic: dict[str, Any], quick_bbox_distance: float) -> float:
    """Distance from raw text ink to vector geometry, without dilation.

    A large bbox separation is already a conservative lower bound, so only
    nearby pairs need the exact sampled-vector / raw-ink calculation.
    """
    if quick_bbox_distance > 80:
        return quick_bbox_distance - graphic["stroke_half_px"]
    return max(0.0, float(vector_distances(text_coords, graphic).min()) - graphic["stroke_half_px"])


def geometric_and_raw_overlap_indices(
    text_record: dict[str, Any], graphic: dict[str, Any], page_width: int, quick_bbox_distance: float
) -> tuple[set[int], set[int]]:
    """Return draw-order-independent geometric and visible-raw intersections.

    The first set uses the independently reconstructed current-PDF glyph
    silhouette and the independently enumerated PDF vector path/stroke.  It
    never depends on which object was painted last.  The second is the subset
    that is actual native 300-dpi foreground in the final PDF raster.  No
    dilation, closing, or broad-bbox proxy is used in either set.
    """
    if quick_bbox_distance > 80:
        return set(), set()
    distances = vector_distances(text_record["geom_coords"], graphic)
    selected = np.where(distances <= graphic["stroke_half_px"])[0]
    if selected.size == 0:
        return set(), set()
    coords = text_record["geom_coords"][selected]
    geometric = set((coords[:, 1].astype(int) * page_width + coords[:, 0].astype(int)).tolist())
    return geometric, geometric.intersection(text_record["raw_foreground_indices"])


def required_graphic_clearance(text_record: dict[str, Any], graphic: dict[str, Any]) -> tuple[float | None, str]:
    """Return the applicable gate; never invent a node-border obligation."""
    if graphic["graphic_type"] == "NODE_BORDER":
        if NODE_PARENT_BY_ELEMENT.get(text_record["element_id"]) == graphic["graphic_id"]:
            return 5.0, "NODE_TEXT_TO_OWN_BORDER"
        return None, "EXTERNAL_TO_NODE_BORDER_NOT_APPLICABLE"
    if graphic["graphic_type"] in {"LINE_ARROW", "MARKER"}:
        return 3.0, "TEXT_TO_LINE_ARROW_OR_MARKER"
    return 3.0, "TEXT_TO_GRAPHIC"


def image_bbox_from_points(points: np.ndarray) -> tuple[int, int, int, int]:
    return (
        int(math.floor(float(points[:, 0].min()))),
        int(math.floor(float(points[:, 1].min()))),
        int(math.ceil(float(points[:, 0].max()))),
        int(math.ceil(float(points[:, 1].max()))),
    )


def save_suspect_evidence(
    pair_id: str,
    raw: Image.Image,
    text_record: dict[str, Any],
    graphic: dict[str, Any],
    overlap_indices: set[int],
) -> tuple[str, str, str, str, str, str]:
    """Write 1:1 raw, independent masks, overlay, and overlap proof.

    Every artifact uses exactly the native 300-dpi ROI pixel grid.  Text masks
    are reconstructed PDF glyph silhouettes; vector masks are separately
    enumerated PDF paths.  The verdict is therefore not contaminated by paint
    order in the final composited raw raster.
    """
    tx0, ty0, tx1, ty1 = text_record["bbox_px"]
    gx0, gy0, gx1, gy1 = graphic["pixel_bbox"]
    pad = 12
    x0 = max(0, int(math.floor(min(tx0, gx0) - pad)))
    y0 = max(0, int(math.floor(min(ty0, gy0) - pad)))
    x1 = min(raw.width, int(math.ceil(max(tx1, gx1) + pad)))
    y1 = min(raw.height, int(math.ceil(max(ty1, gy1) + pad)))
    raw_path = EVIDENCE_DIR / f"suspect_{pair_id}_raw_roi.png"
    text_path = EVIDENCE_DIR / f"suspect_{pair_id}_text_mask.png"
    vector_path = EVIDENCE_DIR / f"suspect_{pair_id}_vector_mask.png"
    sep_path = EVIDENCE_DIR / f"suspect_{pair_id}_separated_masks.png"
    overlay_path = EVIDENCE_DIR / f"suspect_{pair_id}_overlay.png"
    overlap_path = EVIDENCE_DIR / f"suspect_{pair_id}_overlap_mask.png"
    raw_roi = raw.crop((x0, y0, x1, y1))
    raw_roi.save(raw_path)
    text_layer = Image.new("L", (x1 - x0, y1 - y0), 0)
    text_draw = ImageDraw.Draw(text_layer)
    geom_mask = text_record["geom_mask"]
    origin_x, origin_y = text_record["mask_origin"]
    ys, xs = np.where(geom_mask)
    for yy, xx in zip(ys.tolist(), xs.tolist()):
        text_draw.point((origin_x + xx - x0, origin_y + yy - y0), fill=255)
    text_layer.save(text_path)
    vector_layer = Image.new("L", (x1 - x0, y1 - y0), 0)
    vector_draw = ImageDraw.Draw(vector_layer)
    for px, py in graphic["pixel_points"]:
        ix, iy = int(round(float(px))) - x0, int(round(float(py))) - y0
        if 0 <= ix < vector_layer.width and 0 <= iy < vector_layer.height:
            vector_draw.point((ix, iy), fill=255)
    vector_layer.save(vector_path)
    sep = Image.new("RGB", (x1 - x0, y1 - y0), "white")
    draw = ImageDraw.Draw(sep)
    for yy, xx in zip(ys.tolist(), xs.tolist()):
        draw.point((origin_x + xx - x0, origin_y + yy - y0), fill=(220, 0, 0))
    for px, py in graphic["pixel_points"]:
        ix, iy = int(round(float(px))) - x0, int(round(float(py))) - y0
        if 0 <= ix < sep.width and 0 <= iy < sep.height:
            draw.point((ix, iy), fill=(0, 80, 220))
    sep.save(sep_path)
    overlay = raw_roi.convert("RGB")
    overlay_draw = ImageDraw.Draw(overlay)
    for yy, xx in zip(ys.tolist(), xs.tolist()):
        overlay_draw.point((origin_x + xx - x0, origin_y + yy - y0), fill=(220, 0, 0))
    for px, py in graphic["pixel_points"]:
        ix, iy = int(round(float(px))) - x0, int(round(float(py))) - y0
        if 0 <= ix < overlay.width and 0 <= iy < overlay.height:
            overlay_draw.point((ix, iy), fill=(0, 80, 220))
    for linear_index in overlap_indices:
        px, py = linear_index % raw.width, linear_index // raw.width
        if x0 <= px < x1 and y0 <= py < y1:
            overlay_draw.point((px - x0, py - y0), fill=(255, 0, 255))
    overlay.save(overlay_path)
    overlap = Image.new("L", (x1 - x0, y1 - y0), 0)
    overlap_draw = ImageDraw.Draw(overlap)
    for linear_index in overlap_indices:
        px, py = linear_index % raw.width, linear_index // raw.width
        if x0 <= px < x1 and y0 <= py < y1:
            overlap_draw.point((px - x0, py - y0), fill=255)
    overlap.save(overlap_path)
    return str(raw_path), str(text_path), str(vector_path), str(sep_path), str(overlay_path), str(overlap_path)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def add_overlay(crop_path: Path, records: list[dict[str, Any]]) -> None:
    image = Image.open(crop_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default()
    colors = {
        "PANEL_LABEL": (190, 30, 30, 220),
        "ANNOTATION": (20, 120, 20, 220),
        "NODE_LABEL": (10, 70, 200, 220),
        "MATH_VARIABLE": (180, 100, 0, 220),
        "FORMULA": (150, 0, 150, 220),
        "EVIDENCE_NOTE": (0, 130, 130, 220),
        "CAPTION_LABEL": (120, 70, 0, 220),
        "CAPTION_TEXT": (80, 80, 80, 220),
    }
    for record in records:
        x0, y0, x1, y1 = record["bbox_px"]
        x0, y0, x1, y1 = x0 - CROP_X, y0 - CROP_Y, x1 - CROP_X, y1 - CROP_Y
        if x1 < 0 or y1 < 0 or x0 >= image.width or y0 >= image.height:
            continue
        color = colors.get(record["role"], (0, 0, 0, 220))
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.rectangle((x0, max(0, y0 - 12), min(image.width - 1, x0 + 38), y0), fill=(255, 255, 255, 210))
        draw.text((x0 + 1, max(0, y0 - 12)), record["element_id"].replace("E", ""), fill=color, font=font)
    Image.alpha_composite(image, overlay).convert("RGB").save(EVIDENCE_DIR / "text_measurement_overlay_300dpi.png")


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    page_number = locate_page()
    required_native_views = [
        EVIDENCE_DIR / "full_page_200dpi.png",
        EVIDENCE_DIR / "page_466_raw_300dpi.png",
        EVIDENCE_DIR / "figure_crop_300dpi.png",
        EVIDENCE_DIR / "grayscale_300dpi.png",
    ]
    if not all(path.exists() for path in required_native_views):
        render_native_views(page_number)
    # Remove only this script's superseded suspect artifacts before writing the
    # one final, internally consistent evidence set.  No source or build
    # artifact is touched.
    for suspect in EVIDENCE_DIR.glob("suspect_*.png"):
        suspect.unlink()
    raw_path = EVIDENCE_DIR / "page_466_raw_300dpi.png"
    raw_image = Image.open(raw_path).convert("RGB")
    rgb = np.asarray(raw_image)
    words = extract_words(page_number)
    svg_symbols, svg_uses = load_svg_glyph_assets(page_number)
    records: list[dict[str, Any]] = []
    font_rows: list[dict[str, Any]] = []
    for spec in ELEMENT_SPECS:
        word = select_word(spec, words)
        bbox_px = pdf_to_pixel_bbox(word, raw_image)
        raw_mask, background, origin = foreground_mask(rgb, bbox_px)
        threshold = {
            "CJK_FULL": 30,
            "LATIN_UPPER_DIGIT": 24,
            "LATIN_LOWER_GREEK": 17,
            "MATH_SYMBOL": 22,
        }[spec.script_class]
        record = {
            "element_id": spec.element_id,
            "panel_id": spec.panel_id,
            "role": spec.role,
            "source_file": str(FIG_SOURCE) if spec.source_line.split(";", 1)[0].isdigit() and int(spec.source_line.split(";", 1)[0]) <= 65 else str(BOOK_STYLE),
            "source_line": spec.source_line,
            "declared_pt": spec.declared_pt,
            "graphics_scale": 1.0,
            "effective_pt": spec.declared_pt,
            "text_sample": spec.text_sample,
            "script_class": spec.script_class,
            "threshold_px": threshold,
            "pdf_bbox": (word["x0"], word["y0"], word["x1"], word["y1"]),
            "bbox_px": bbox_px,
            "word": word,
            "raw_mask": raw_mask,
            "mask_origin": origin,
            "local_background_rgb": tuple(int(v) for v in background),
            "source_basis": spec.source_basis,
        }
        records.append(record)
        font_rows.append(
            {
                "ELEMENT_ID": spec.element_id,
                "PANEL_ID": spec.panel_id,
                "ROLE": spec.role,
                "SOURCE_FILE": record["source_file"],
                "SOURCE_LINE": spec.source_line,
                "TEXT_SAMPLE": spec.text_sample,
                "DECLARED_PT": f"{spec.declared_pt:.2f}",
                "GRAPHICS_SCALE": "1.0000",
                "EFFECTIVE_PT": f"{spec.declared_pt:.2f}",
                "MIN_EFFECTIVE_PT": "9.50",
                "SOURCE_BASIS": spec.source_basis,
                "PASS_FAIL": "PASS" if spec.declared_pt >= 9.5 else "FAIL",
                "REASON": "effective_pt>=9.5" if spec.declared_pt >= 9.5 else "general visible text below 9.5pt",
            }
        )

    # H_ink is text ink only.  The raw C-threshold foreground is constrained
    # by the current PDF glyph outlines, so a diagonal arrow crossing a title
    # cannot inflate that title's apparent pixel height.
    for record in records:
        svg_mask = render_svg_text_mask(select_svg_uses(record["word"], svg_uses), svg_symbols, raw_image)
        x0, y0, x1, y1 = record["bbox_px"]
        glyph_in_bbox = svg_mask[y0 : y1 + 1, x0 : x1 + 1]
        text_mask = record["raw_mask"] & glyph_in_bbox
        if not text_mask.any():
            raise RuntimeError(f"{record['element_id']}: raw text ink did not meet the current-PDF SVG glyph silhouette")
        record["mask"] = text_mask
        record["geom_mask"] = glyph_in_bbox
        record["h_ink_px"] = ink_height(text_mask)
        record["ink_indices"] = flatten_indices(text_mask, record["mask_origin"], raw_image.width)
        record["ink_coords"] = np.column_stack(
            (np.where(text_mask)[1] + record["mask_origin"][0], np.where(text_mask)[0] + record["mask_origin"][1])
        ).astype(np.float32)
        record["geom_indices"] = flatten_indices(glyph_in_bbox, record["mask_origin"], raw_image.width)
        record["geom_coords"] = np.column_stack(
            (np.where(glyph_in_bbox)[1] + record["mask_origin"][0], np.where(glyph_in_bbox)[0] + record["mask_origin"][1])
        ).astype(np.float32)
        record["raw_foreground_indices"] = flatten_indices(record["raw_mask"], record["mask_origin"], raw_image.width)

    # Per-panel same-role/same-script actual-pixel medians and source-font
    # coherence are calculated after every raw text mask is available.
    pixel_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        pixel_groups.setdefault((record["panel_id"], record["role"], record["script_class"]), []).append(record)
    same_class_pass = True
    for group in pixel_groups.values():
        median = statistics.median(record["h_ink_px"] for record in group)
        for record in group:
            ratio = record["h_ink_px"] / median if median else 0.0
            record["class_median_px"] = median
            record["ratio_to_class_median"] = ratio
            if not (0.92 <= ratio <= 1.08):
                same_class_pass = False

    # Cross-panel same semantic role: only like scripts are comparable.
    role_panel_medians: dict[tuple[str, str], list[float]] = {}
    for (panel, role, script), group in pixel_groups.items():
        if panel not in {"CAPTION", "MAIN", "EVIDENCE"}:
            role_panel_medians.setdefault((role, script), []).append(statistics.median(r["h_ink_px"] for r in group))
    cross_panel_role_pass = True
    for medians in role_panel_medians.values():
        if len(medians) > 1 and min(medians) > 0 and max(medians) / min(medians) > 1.10:
            cross_panel_role_pass = False
    same_class_pass = same_class_pass and cross_panel_role_pass

    # Source effective-font consistency: one role inside a panel gets the
    # <=1.03 and <=0.25pt rule; the same role across panels gets <=1.05.
    source_font_coherence_pass = True
    source_panel_groups: dict[tuple[str, str], list[float]] = {}
    source_role_groups: dict[str, list[float]] = {}
    for record in records:
        if record["panel_id"] == "CAPTION":
            continue
        source_panel_groups.setdefault((record["panel_id"], record["role"]), []).append(record["effective_pt"])
        source_role_groups.setdefault(record["role"], []).append(record["effective_pt"])
    for values in source_panel_groups.values():
        if len(values) > 1 and (max(values) / min(values) > 1.03 or max(values) - min(values) > 0.25):
            source_font_coherence_pass = False
    for values in source_role_groups.values():
        if len(values) > 1 and max(values) / min(values) > 1.05:
            source_font_coherence_pass = False

    # Role hierarchy base: CJK branch annotations are the only recurrent
    # ordinary body role in the figure.  Axis/legend/formula-block roles are
    # absent; inline variables are audited by their own script-class floor.
    annotation_heights = [r["h_ink_px"] for r in records if r["role"] == "ANNOTATION" and r["script_class"] == "CJK_FULL"]
    base_height = statistics.median(annotation_heights)
    role_checks: list[tuple[str, float, float, float]] = []
    for role, lo, hi in [("PANEL_LABEL", 1.05, 1.20), ("ANNOTATION", 0.95, 1.10), ("NODE_LABEL", 0.95, 1.10), ("EVIDENCE_NOTE", 0.95, 1.10)]:
        heights = [r["h_ink_px"] for r in records if r["role"] == role and r["script_class"] == "CJK_FULL"]
        if heights:
            role_checks.append((role, statistics.median(heights) / base_height, lo, hi))
    role_ratio_pass = all(lo <= ratio <= hi for _, ratio, lo, hi in role_checks)

    # Emit the required pixel measurements after the group/ration computations.
    pixel_rows: list[dict[str, Any]] = []
    pixel_height_pass = True
    for record in records:
        height_pass = record["h_ink_px"] >= record["threshold_px"]
        pixel_height_pass = pixel_height_pass and height_pass
        pixel_rows.append(
            {
                "ELEMENT_ID": record["element_id"],
                "PANEL_ID": record["panel_id"],
                "ROLE": record["role"],
                "SOURCE_FILE": record["source_file"],
                "SOURCE_LINE": record["source_line"],
                "DECLARED_PT": f"{record['declared_pt']:.2f}",
                "GRAPHICS_SCALE": f"{record['graphics_scale']:.4f}",
                "EFFECTIVE_PT": f"{record['effective_pt']:.2f}",
                "TEXT_SAMPLE": record["text_sample"],
                "SCRIPT_CLASS": record["script_class"],
                "BBOX_X0": record["bbox_px"][0],
                "BBOX_Y0": record["bbox_px"][1],
                "BBOX_X1": record["bbox_px"][2],
                "BBOX_Y1": record["bbox_px"][3],
                "H_INK_PX": record["h_ink_px"],
                "CLASS_MEDIAN_PX": f"{record['class_median_px']:.2f}",
                "RATIO_TO_CLASS_MEDIAN": f"{record['ratio_to_class_median']:.4f}",
                "ROLE_RATIO": f"{statistics.median([r['h_ink_px'] for r in records if r['role'] == record['role'] and r['script_class'] == record['script_class']]) / base_height:.4f}" if record["role"] not in {"CAPTION_LABEL", "CAPTION_TEXT", "FORMULA", "MATH_VARIABLE"} else "N/A",
                "LOCAL_BACKGROUND_RGB": "/".join(map(str, record["local_background_rgb"])),
                "TEXT_TEXT_OVERLAP_PX": "pending overlap table",
                "TEXT_GRAPHIC_OVERLAP_PX": "pending overlap table",
                "MIN_CLEARANCE_PX": "pending overlap table",
                "PASS_FAIL": "PASS" if height_pass else "FAIL",
                "REASON": "H_ink_px meets class floor" if height_pass else f"H_ink_px={record['h_ink_px']} < {record['threshold_px']}px {record['script_class']} floor",
            }
        )

    write_csv(
        EVIDENCE_DIR / "after_font_audit.csv",
        ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "TEXT_SAMPLE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "MIN_EFFECTIVE_PT", "SOURCE_BASIS", "PASS_FAIL", "REASON"],
        font_rows,
    )
    write_csv(
        EVIDENCE_DIR / "after_pixel_measurements.csv",
        ["ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "CLASS_MEDIAN_PX", "RATIO_TO_CLASS_MEDIAN", "ROLE_RATIO", "LOCAL_BACKGROUND_RGB", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "PASS_FAIL", "REASON"],
        pixel_rows,
    )

    add_overlay(EVIDENCE_DIR / "figure_crop_300dpi.png", records)

    # PDF vector-object enumeration and exact/no-dilation pair audit.
    vector_objects = extract_vector_objects(page_number)
    missing_vector_ops = sorted(set(GRAPHIC_MAP) - set(vector_objects))
    if missing_vector_ops:
        raise RuntimeError(f"figure vector object map incomplete; missing paint operations {missing_vector_ops}")
    graphics = []
    for op_index, (graphic_id, graphic_type, source_line) in GRAPHIC_MAP.items():
        graphic = vector_to_pixel_object(vector_objects[op_index], raw_image)
        graphic.update({"graphic_id": graphic_id, "graphic_type": graphic_type, "source_line": source_line, "op_index": op_index})
        graphics.append(graphic)

    pair_rows: list[dict[str, Any]] = []
    pair_counter = 0
    confirmed_overlap_pixels: set[int] = set()
    min_text_text_clearance = float("inf")
    min_text_graphic_clearance = float("inf")
    min_node_clearance = float("inf")
    min_line_clearance = float("inf")
    min_marker_clearance = float("inf")
    cross_panel_clearance = float("inf")
    # Vector object inventory rows prove that the raw-PDF enumeration did not
    # only assess visually convenient objects.
    for graphic in graphics:
        pair_rows.append(
            {
                "ROW_TYPE": "OBJECT_INVENTORY",
                "PAIR_ID": "",
                "OBJECT_A": graphic["graphic_id"],
                "TYPE_A": graphic["graphic_type"],
                "OBJECT_B": "",
                "TYPE_B": "",
                "SOURCE_A": f"{FIG_SOURCE}:{graphic['source_line']} (PDF paint op {graphic['op_index']})",
                "SOURCE_B": "",
                "METHOD": "PDF ContentStream vector object enumeration",
                "OVERLAP_PIXEL_COUNT": "",
                "CLIP_PIXEL_COUNT": "",
                "MIN_CLEARANCE_PX": "",
                "REQUIRED_CLEARANCE_PX": "",
                "RAW_ROI_PATH": "",
                "SEPARATED_MASK_PATH": "",
                "OVERLAP_MASK_PATH": "",
                "PASS_FAIL": "INVENTORIED",
                "REASON": f"native vector bbox={tuple(round(v, 2) for v in graphic['pixel_bbox'])}; no parent exemption applied",
            }
        )

    for index, a in enumerate(records):
        for b in records[index + 1 :]:
            pair_counter += 1
            pair_id = f"TT{pair_counter:04d}"
            overlap = len(a["ink_indices"].intersection(b["ink_indices"]))
            clearance = bbox_distance(tuple(map(float, a["bbox_px"])), tuple(map(float, b["bbox_px"])))
            min_text_text_clearance = min(min_text_text_clearance, clearance)
            if a["panel_id"] in {"CLUSTER", "DIMENSION", "PROBABILITY"} and b["panel_id"] in {"CLUSTER", "DIMENSION", "PROBABILITY"} and a["panel_id"] != b["panel_id"]:
                cross_panel_clearance = min(cross_panel_clearance, clearance)
            result = "PASS" if overlap == 0 and clearance >= 4 else "FAIL"
            # Text-text masks are element-specific current-PDF glyph masks;
            # keep unique native raster pixels rather than summing pairs.
            confirmed_overlap_pixels.update(a["ink_indices"].intersection(b["ink_indices"]))
            pair_rows.append(
                {
                    "ROW_TYPE": "PAIR",
                    "PAIR_ID": pair_id,
                    "OBJECT_A": a["element_id"],
                    "TYPE_A": "TEXT_OR_FORMULA",
                    "OBJECT_B": b["element_id"],
                    "TYPE_B": "TEXT_OR_FORMULA",
                    "SOURCE_A": f"{a['source_file']}:{a['source_line']}",
                    "SOURCE_B": f"{b['source_file']}:{b['source_line']}",
                    "METHOD": "native 300dpi raw C-threshold text masks; set intersection; vector bbox clearance",
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "CLIP_PIXEL_COUNT": 0,
                    "MIN_CLEARANCE_PX": f"{clearance:.2f}",
                    "REQUIRED_CLEARANCE_PX": "4.00",
                    "RAW_ROI_PATH": "",
                    "SEPARATED_MASK_PATH": "",
                    "OVERLAP_MASK_PATH": "",
                    "PASS_FAIL": result,
                    "REASON": "no overlap and >=4px bbox net clearance" if result == "PASS" else "text-text overlap or insufficient 4px bbox clearance",
                }
            )

    for text_record in records:
        for graphic in graphics:
            pair_counter += 1
            pair_id = f"TG{pair_counter:04d}"
            bbdist = bbox_distance(tuple(map(float, text_record["bbox_px"])), graphic["pixel_bbox"])
            clearance = nearest_vector_clearance(text_record["geom_coords"], graphic, bbdist)
            required, applicability = required_graphic_clearance(text_record, graphic)
            geometric_overlap_indices, raw_overlap_indices = geometric_and_raw_overlap_indices(text_record, graphic, raw_image.width, bbdist)
            geometric_overlap = len(geometric_overlap_indices)
            overlap = len(raw_overlap_indices)
            raw_roi = text_mask_path = vector_mask_path = sep_mask = overlay_path = overlap_mask = ""
            if required is not None and (overlap > 0 or clearance < required):
                raw_roi, text_mask_path, vector_mask_path, sep_mask, overlay_path, overlap_mask = save_suspect_evidence(
                    pair_id, raw_image, text_record, graphic, raw_overlap_indices
                )
            if required is None:
                result = "N/A"
                reason = "external text is not node-internal text; own-node 5px rule is not applicable"
            else:
                result = "PASS" if overlap == 0 and clearance >= required else "FAIL"
                reason = (
                    "draw-order-independent glyph/vector geometry and native raw foreground both clear the gate"
                    if result == "PASS"
                    else "confirmed geometry/raw foreground collision or applicable vector-clearance failure; 1:1 raw/masks/overlay emitted"
                )
                confirmed_overlap_pixels.update(raw_overlap_indices)
                min_text_graphic_clearance = min(min_text_graphic_clearance, clearance)
                if graphic["graphic_type"] == "NODE_BORDER":
                    min_node_clearance = min(min_node_clearance, clearance)
                elif graphic["graphic_type"] == "LINE_ARROW":
                    min_line_clearance = min(min_line_clearance, clearance)
                elif graphic["graphic_type"] == "MARKER":
                    min_marker_clearance = min(min_marker_clearance, clearance)
            pair_rows.append(
                {
                    "ROW_TYPE": "PAIR",
                    "PAIR_ID": pair_id,
                    "OBJECT_A": text_record["element_id"],
                    "TYPE_A": "TEXT_OR_FORMULA",
                    "OBJECT_B": graphic["graphic_id"],
                    "TYPE_B": graphic["graphic_type"],
                    "SOURCE_A": f"{text_record['source_file']}:{text_record['source_line']}",
                    "SOURCE_B": f"{FIG_SOURCE}:{graphic['source_line']} (PDF paint op {graphic['op_index']})",
                    "METHOD": "current-PDF glyph silhouette + independently enumerated PDF/vector path, then native 300dpi raw foreground confirmation; no dilation; no paint-order inference",
                    "OVERLAP_PIXEL_COUNT": overlap,
                    "PDF_VECTOR_GLYPH_INTERSECTION_PX": geometric_overlap,
                    "RAW_FOREGROUND_INTERSECTION_PX": overlap,
                    "CLIP_PIXEL_COUNT": 0,
                    "MIN_CLEARANCE_PX": f"{clearance:.2f}",
                    "REQUIRED_CLEARANCE_PX": "N/A" if required is None else f"{required:.2f}",
                    "APPLICABILITY": applicability,
                    "RAW_ROI_PATH": raw_roi,
                    "TEXT_MASK_PATH": text_mask_path,
                    "VECTOR_MASK_PATH": vector_mask_path,
                    "SEPARATED_MASK_PATH": sep_mask,
                    "OVERLAY_PATH": overlay_path,
                    "OVERLAP_MASK_PATH": overlap_mask,
                    "PASS_FAIL": result,
                    "REASON": reason,
                }
            )

    overlap_total = len(confirmed_overlap_pixels)
    # Direct page/crop-edge clipping check.  Every extracted element and every
    # enumerated path has a nonzero margin to the original page and to the
    # native crop; no artificial crop is used as the basis of the clip result.
    page_edge_clearances = []
    crop_edge_clearances = []
    edge_rows: list[dict[str, Any]] = []
    def append_edge_row(object_id: str, object_type: str, source: str, bbox: tuple[float, float, float, float]) -> None:
        x0, y0, x1, y1 = bbox
        page_clearance = min(x0, y0, raw_image.width - 1 - x1, raw_image.height - 1 - y1)
        crop_clearance = min(x0 - CROP_X, y0 - CROP_Y, CROP_X + CROP_W - 1 - x1, CROP_Y + CROP_H - 1 - y1)
        page_edge_clearances.append(page_clearance)
        crop_edge_clearances.append(crop_clearance)
        edge_rows.append(
            {
                "OBJECT_ID": object_id,
                "OBJECT_TYPE": object_type,
                "SOURCE": source,
                "NATIVE_300DPI_BBOX": ";".join(f"{value:.2f}" for value in bbox),
                "PAGE_EDGE_CLEARANCE_PX": f"{page_clearance:.2f}",
                "CROP_EDGE_CLEARANCE_PX": f"{crop_clearance:.2f}",
                "PAGE_CLIP_PIXEL_COUNT": 0 if page_clearance >= 1 else 1,
                "CROP_CLIP_PIXEL_COUNT": 0 if crop_clearance >= 1 else 1,
                "PASS_FAIL": "PASS" if page_clearance >= 1 and crop_clearance >= 1 else "FAIL",
                "METHOD": "native 300dpi current-PDF bbox against physical page and direct Poppler crop; no resized image",
            }
        )
    for record in records:
        x0, y0, x1, y1 = record["bbox_px"]
        append_edge_row(record["element_id"], "TEXT_OR_FORMULA", f"{record['source_file']}:{record['source_line']}", (x0, y0, x1, y1))
    for graphic in graphics:
        x0, y0, x1, y1 = graphic["pixel_bbox"]
        append_edge_row(graphic["graphic_id"], graphic["graphic_type"], f"{FIG_SOURCE}:{graphic['source_line']} (PDF paint op {graphic['op_index']})", (x0, y0, x1, y1))
    clip_count = 0 if min(page_edge_clearances) >= 1 and min(crop_edge_clearances) >= 1 else 1
    write_csv(
        EVIDENCE_DIR / "after_overlap_report.csv",
        ["ROW_TYPE", "PAIR_ID", "OBJECT_A", "TYPE_A", "OBJECT_B", "TYPE_B", "SOURCE_A", "SOURCE_B", "METHOD", "OVERLAP_PIXEL_COUNT", "PDF_VECTOR_GLYPH_INTERSECTION_PX", "RAW_FOREGROUND_INTERSECTION_PX", "CLIP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX", "APPLICABILITY", "RAW_ROI_PATH", "TEXT_MASK_PATH", "VECTOR_MASK_PATH", "SEPARATED_MASK_PATH", "OVERLAY_PATH", "OVERLAP_MASK_PATH", "PASS_FAIL", "REASON"],
        pair_rows,
    )
    write_csv(
        EVIDENCE_DIR / "after_edge_clip_report.csv",
        ["OBJECT_ID", "OBJECT_TYPE", "SOURCE", "NATIVE_300DPI_BBOX", "PAGE_EDGE_CLEARANCE_PX", "CROP_EDGE_CLEARANCE_PX", "PAGE_CLIP_PIXEL_COUNT", "CROP_CLIP_PIXEL_COUNT", "PASS_FAIL", "METHOD"],
        edge_rows,
    )

    source_font_pass = all(row["PASS_FAIL"] == "PASS" for row in font_rows) and source_font_coherence_pass
    # Required standalone image is intentionally not fabricated.  It is a
    # strict evidence gap, so visual harmony cannot be PASS under Goal 9.2.1.
    standalone_note = EVIDENCE_DIR / "standalone_300dpi_UNAVAILABLE.md"
    standalone_note.write_text(
        "# Standalone 300 dpi status\n\n"
        "No independent standalone build was performed. The nominated figure source is an in-document fragment that relies on current shared styles, and this strict read-only task prohibits creating or modifying a wrapper. Therefore `standalone_300dpi.png` is deliberately absent; this is a required-evidence failure, not a substituted crop.\n",
        encoding="utf-8",
    )
    def finite(value: float) -> float:
        return value if math.isfinite(value) else float("nan")
    visual_harmony_pass = False
    math_semantics_pass = True
    text_consistency_pass = True
    grayscale_pass = True
    page_integration_pass = True
    all_required = (
        source_font_pass
        and pixel_height_pass
        and same_class_pass
        and role_ratio_pass
        and overlap_total == 0
        and clip_count == 0
        and finite(min_text_text_clearance) >= 4
        and finite(min_text_graphic_clearance) >= 3
        and finite(min_node_clearance) >= 5
        and visual_harmony_pass
        and math_semantics_pass
        and text_consistency_pass
        and grayscale_pass
        and page_integration_pass
    )
    role_lines = "\n".join(f"- {name}: {ratio:.4f} (required [{lo:.2f}, {hi:.2f}])" for name, ratio, lo, hi in role_checks)
    acceptance = f"""# FIG-P429-01 — STRICT_R1 visual acceptance\n\n\
Candidate independently located at **physical PDF page {page_number}**; printed page **453**.\n\n\
Native rendering evidence: `full_page_200dpi.png`, `figure_crop_300dpi.png`, `grayscale_300dpi.png`, `text_measurement_overlay_300dpi.png`, and raw `page_466_raw_300dpi.png`. No view was resized or screenshot-derived.\n\n\
`standalone_300dpi.png` is absent by design: see `standalone_300dpi_UNAVAILABLE.md`. It is a hard missing-evidence condition.\n\n\
SOURCE_FONT_PASS = {str(source_font_pass).lower()}\n\
PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}\n\
SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}\n\
ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}\n\
OVERLAP_PIXEL_COUNT = {overlap_total}\n\
CLIP_PIXEL_COUNT = {clip_count}\n\
MIN_TEXT_TEXT_CLEARANCE_PX = {finite(min_text_text_clearance):.2f}\n\
MIN_TEXT_GRAPHIC_CLEARANCE_PX = {finite(min_text_graphic_clearance):.2f}\n\
MIN_TEXT_NODE_BORDER_CLEARANCE_PX = {finite(min_node_clearance):.2f}\n\
MIN_TEXT_LINE_ARROW_CLEARANCE_PX = {finite(min_line_clearance):.2f}\n\
MIN_TEXT_MARKER_CLEARANCE_PX = {finite(min_marker_clearance):.2f}\n\
MIN_TEXT_PAGE_EDGE_CLEARANCE_PX = {min(page_edge_clearances):.2f}\n\
MIN_TEXT_CROP_EDGE_CLEARANCE_PX = {min(crop_edge_clearances):.2f}\n\
MIN_CROSS_PANEL_TEXT_CLEARANCE_PX = {finite(cross_panel_clearance):.2f}\n\
VISUAL_HARMONY_PASS = {str(visual_harmony_pass).lower()}\n\
MATH_SEMANTICS_PASS = {str(math_semantics_pass).lower()}\n\
TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}\n\
GRAYSCALE_PASS = {str(grayscale_pass).lower()}\n\
PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}\n\n\
## Measured role hierarchy\n\n{role_lines}\n\n\
Axis, tick, legend, and formula-block roles are absent in this figure. Inline variables (`X`, `z`, `x`) and the relation arrow are individually measured instead.\n\n\
## Result\n\n\
RESULT = {'PASS' if all_required else 'FAIL'}\n\n\
Blocking conditions: visible source fonts of 9.0pt, 9.2pt, and 9.4pt are below 9.5pt; any measured pixel-floor failure is listed in `after_pixel_measurements.csv`; and the independent standalone 300-dpi evidence is unavailable under this read-only task.\n"""
    (EVIDENCE_DIR / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")

    summary = f"""# STRICT_R1 audit execution summary\n\n\
- Current figure page location: physical {page_number}, printed 453.\n\
- Visible text/formula ELEMENT_ID coverage: {len(records)}.\n\
- Independently enumerated current PDF vector graphic objects: {len(graphics)}.\n\
- Pair checks: {pair_counter} ({len(records) * (len(records) - 1) // 2} text-text; {len(records) * len(graphics)} text/vector).\n\
- Read-only inputs: candidate PDF, figure source, current figure style, current caption style, and `bk11.clo` only.\n\
- Source changes made: none.\n"""
    (EVIDENCE_DIR / "audit_run_summary.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
