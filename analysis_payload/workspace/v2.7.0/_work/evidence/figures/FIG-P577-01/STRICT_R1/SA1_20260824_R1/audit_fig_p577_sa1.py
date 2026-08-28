#!/usr/bin/env python3
"""Independent strict-R1 evidence builder for FIG-P577-01.

Reads only the frozen R94 PDF.  Every output is written below this script's
directory.  Counting coordinates are native 300 dpi pixels; 8x images are
human-review copies only.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
WORK_ROOT = ROOT.parents[4]
PDF = WORK_ROOT / "source" / "v2.7.0" / "src" / "build" / "strict_current_r94_fullbook" / "main_full.pdf"
PHYSICAL_PAGE = 625
DPI_300 = 300
DPI_200 = 200
DELTA = 20

# These rectangles are in final PDF points, derived from the R94 page itself.
# Crop operations are conversion to integer native 300 dpi coordinates only;
# they never resample.
FIGURE_RECT_PT = (52.0, 58.0, 545.0, 446.0)  # plot + complete caption, excludes reading-check prose at y>=448pt
STANDALONE_RECT_PT = (52.0, 58.0, 545.0, 424.0)  # source-created plot body, including every axis/tick label
PLOT_RECT_PT = (68.0, 170.0, 478.0, 376.0)

RAW_DIR = ROOT / "masks" / "raw"
GLYPH_DIR = ROOT / "masks" / "glyphs"
PAIR_DIR = ROOT / "pair_evidence"
GLYPH_EVIDENCE_DIR = ROOT / "glyph_evidence"
HUMAN_DIR = ROOT / "human_review"
HALO_DIR = ROOT / "halos"
SVG_PAGE = ROOT / "page_625.svg"

COLORS = {
    "BLUE": (31, 78, 121),
    "TEAL": (15, 118, 110),
    "GOLD": (183, 121, 31),
    "GRAY": (107, 114, 128),
    "TEXTGRAY": (77, 83, 88),
    # R94's opaque main ink resolves to #1F2328 in the native Poppler raster.
    "INK": (31, 35, 40),
}


def ensure_dirs() -> None:
    for d in (RAW_DIR, GLYPH_DIR, PAIR_DIR, GLYPH_EVIDENCE_DIR, HUMAN_DIR, HALO_DIR):
        d.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)


def render() -> tuple[Path, Path]:
    p200 = ROOT / "full_page_200dpi.png"
    p300 = ROOT / "full_page_300dpi.png"
    run(["pdftoppm", "-png", "-r", str(DPI_200), "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE), "-singlefile", str(PDF), str(p200.with_suffix(""))])
    run(["pdftoppm", "-png", "-r", str(DPI_300), "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE), "-singlefile", str(PDF), str(p300.with_suffix(""))])
    if not p200.exists() or not p300.exists():
        raise RuntimeError("direct PDF rendering did not create both native PNGs")
    return p200, p300


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def crop_bbox(b: tuple[int, int, int, int], margin: int, width: int, height: int) -> tuple[int, int, int, int]:
    return max(0, b[0] - margin), max(0, b[1] - margin), min(width - 1, b[2] + margin), min(height - 1, b[3] + margin)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(0, b[0] - a[2] - 1, a[0] - b[2] - 1)
    dy = max(0, b[1] - a[3] - 1, a[1] - b[3] - 1)
    return float(math.hypot(dx, dy))


def rect_pt_to_px(rect: tuple[float, float, float, float], sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, math.floor(x0 * sx)),
        max(0, math.floor(y0 * sy)),
        min(width, math.ceil(x1 * sx)),
        min(height, math.ceil(y1 * sy)),
    )


def word_bbox_to_px(word: dict, sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    return rect_pt_to_px((word["x0"], word["y0"], word["x1"], word["y1"]), sx, sy, width, height)


def inside(word: dict, rect: tuple[float, float, float, float]) -> bool:
    cx = (word["x0"] + word["x1"]) / 2
    cy = (word["y0"] + word["y1"]) / 2
    return rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]


def get_words() -> list[dict]:
    cp = run(["pdftotext", "-bbox-layout", "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE), str(PDF), "-"], capture=True)
    raw = cp.stdout
    (ROOT / "page_625_text_geometry.xhtml").write_bytes(raw)
    root = ET.fromstring(raw.decode("utf-8", errors="replace"))
    result: list[dict] = []
    n = 0
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "word":
            continue
        text = "".join(element.itertext()).strip()
        if not text:
            continue
        n += 1
        result.append({
            "ordinal": n,
            "text": text,
            "x0": float(element.attrib["xMin"]),
            "y0": float(element.attrib["yMin"]),
            "x1": float(element.attrib["xMax"]),
            "y1": float(element.attrib["yMax"]),
        })
    return result


def get_svg_glyph_uses() -> list[dict]:
    """Read exact Poppler SVG glyph origins from the official PDF page.

    The positions are used only to partition already-final 300-dpi raw masks;
    they do not draw or add pixels.  This avoids equal-width slicing whenever
    the PDF exposes a one-to-one glyph-use trace.
    """
    if not SVG_PAGE.exists():
        run(["pdftocairo", "-svg", "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE), str(PDF), str(SVG_PAGE)])
    text = SVG_PAGE.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r'<use\s+[^>]*\bx="([\-0-9.]+)"\s+y="([\-0-9.]+)"')
    return [{"x": float(x), "y": float(y), "order": n} for n, (x, y) in enumerate(pat.findall(text), 1)]


def is_cjk(c: str) -> bool:
    o = ord(c)
    return 0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF


def is_fullwidth(c: str) -> bool:
    return unicodedata.east_asian_width(c) in {"F", "W"}


OPERATORS = set("=<>≤≥−+-×÷∈∫⟺≈≠/()[]{}.,;:，；：（）[]")


def glyph_class(c: str, natural_script: bool) -> tuple[str, int]:
    if is_cjk(c) or is_fullwidth(c):
        return "CJK", 30
    if c in OPERATORS or unicodedata.category(c).startswith("P"):
        return "BASE_MATH", 22
    if natural_script:
        return "NATURAL_SCRIPT", 15
    if c.isdigit() or (c.isalpha() and c.upper() == c):
        return "LATIN_CAP_NUM", 24
    return "X_HEIGHT", 17


def script_family(c: str) -> str:
    """D compares script, never a convenient glyph-shape subgroup."""
    if c in OPERATORS or unicodedata.category(c).startswith("P"):
        return "MATH_PUNCT"
    if is_cjk(c) or is_fullwidth(c):
        return "CJK"
    if "GREEK" in unicodedata.name(c, ""):
        return "GREEK"
    if c.isalpha() or c.isdigit():
        return "LATIN_DIGIT"
    return "OTHER"


def color_mask(image: np.ndarray, color: tuple[int, int, int], tol: int = 38) -> np.ndarray:
    diff = np.abs(image.astype(np.int16) - np.asarray(color, dtype=np.int16))
    return (diff.max(axis=2) <= tol) & ((255 - image.astype(np.int16)).max(axis=2) >= DELTA)


def colour_ray_mask(image: np.ndarray, color: tuple[int, int, int], residual_limit: float = 3.0, alpha_min: float = .13) -> np.ndarray:
    """Native final-raster antialias-aware colour membership, without dilation."""
    pix = image.astype(np.float32)
    diff = 255.0 - pix
    base = 255.0 - np.asarray(color, dtype=np.float32)
    denom = float(np.dot(base, base))
    alpha = np.clip((diff * base).sum(axis=2) / denom, 0.0, 1.0)
    residual = np.sqrt(((diff - alpha[..., None] * base) ** 2).sum(axis=2))
    # alpha=.09 is the intentional translucent rejection-area fill.  It is
    # not an opaque curve/line/label stroke.  The .13 raw-pixel threshold
    # removes that fill without adding or expanding any pixels; callers for
    # dark text may lower it slightly to retain their antialiased contours.
    return ((255 - image.astype(np.int16)).max(axis=2) >= DELTA) & (alpha >= alpha_min) & (residual <= residual_limit)


def neutral_text_mask(image: np.ndarray) -> np.ndarray:
    image_i = image.astype(np.int16)
    channel_spread = image_i.max(axis=2) - image_i.min(axis=2)
    return ((255 - image_i).max(axis=2) >= DELTA) & (channel_spread <= 34)


def raw_text_mask(image: np.ndarray, word: dict, sx: float, sy: float, width: int, height: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = word_bbox_to_px(word, sx, sy, width, height)
    # BBox exact only: no dilation or padding.  Blue/teal labels are colour-isolated;
    # remaining labels use neutral foreground and therefore cannot absorb coloured curves.
    local = np.zeros((height, width), dtype=bool)
    patch = image[y0:y1, x0:x1]
    text = word["text"]
    if word.get("parent") == "LEGEND_BLUE":
        sub = colour_ray_mask(patch, COLORS["BLUE"], alpha_min=.075)
    elif word.get("parent") == "LEGEND_TEAL":
        sub = colour_ray_mask(patch, COLORS["TEAL"], alpha_min=.075)
    else:
        # The PDF uses two opaque neutral inks (#1F2328 and #4D5358).
        # Ray membership avoids treating a nearby coloured line as text;
        # this is a raw final-raster classification, not an erosion/dilation.
        sub = (colour_ray_mask(patch, COLORS["INK"], alpha_min=.075)
               | colour_ray_mask(patch, COLORS["TEXTGRAY"], alpha_min=.075))
    local[y0:y1, x0:x1] = sub
    return local, (x0, y0, x1 - 1, y1 - 1)


def parent_for(word: dict) -> tuple[str, str, float, str]:
    """Return semantic parent, role, declared pt, source line description."""
    x = (word["x0"] + word["x1"]) / 2
    y = (word["y0"] + word["y1"]) / 2
    text = word["text"]
    if 63 <= y < 86:
        return "TITLE", "FIGURE_TITLE", 10.2, "26"
    if 80 <= y < 165:
        return "SUMMARY_FORMULA", "FORMULA", 9.6, "27-32"
    if 168 <= y < 203 and x > 355:
        return "LEGEND_TEAL", "LEGEND", 9.6, "36-37"
    if 184 <= y < 220 and 280 <= x <= 322:
        return "DELTA_LABEL", "ANNOTATION_FORMULA", 9.6, "38-40"
    if 198 <= y < 226 and 190 <= x <= 275:
        return "LEGEND_BLUE", "LEGEND", 9.6, "34-35"
    if x < 95 and 245 <= y <= 305 and any(is_cjk(c) for c in text):
        return "AXIS_Y", "AXIS_TITLE", 9.6, "15"
    # Tick labels are semantic units: the numerator and denominator of each
    # fractional x tick belong to one element.  Numeric-only guard prevents
    # the accepted-box `U=` from being misclassified as a y tick.
    numeric_tick = all(c.isdigit() or c == "." for c in text)
    if x < 105 and 175 <= y < 383 and numeric_tick:
        return f"TICK_Y_{text.replace('.', '_')}", "TICK", 9.6, "17"
    if 206 <= y < 265 and x < 275:
        return "FILL_ANNOTATION", "ANNOTATION", 9.6, "41-42"
    if 214 <= y < 320 and x > 350:
        return "REJECT_CALLOUT", "ANNOTATION", 9.6, "56-61"
    if 244 <= y < 350 and 95 <= x < 245:
        return "ACCEPT_CALLOUT", "ANNOTATION", 9.6, "47-51"
    if 380 <= y < 404 and any(is_cjk(c) for c in text):
        return ("SUPPORT_LEFT" if x < 270 else "SUPPORT_RIGHT"), "ANNOTATION", 9.6, "65-68"
    if 378 <= y < 406 and numeric_tick:
        if x < 150:
            tick = "0"
        elif x < 235:
            tick = "1_4"
        elif x < 320:
            tick = "1_2"
        elif x < 410:
            tick = "3_4"
        else:
            tick = "1"
        return f"TICK_X_{tick}", "TICK", 9.6, "16"
    if 406 <= y < 424 and text == "𝑦":
        return "AXIS_X", "AXIS_TITLE", 9.6, "15"
    if 424 <= y < 446:
        return "CAPTION", "CAPTION", 10.0, "71"
    return f"UNASSIGNED_{word['ordinal']:03d}", "UNASSIGNED", 9.6, "UNKNOWN"


def final_visibility_exclusion(word: dict) -> str | None:
    """Return the real later opaque object that fully hides a source word.

    The y=0.4 tick is emitted by the axis before the accepted callout.  Its
    entire native word box is inside that later *opaque white* node; Poppler
    extraction still reports it, but its visible pixels are the callout's
    `U=` text, not a final y-tick.  It is therefore retained in the
    occlusion ledger but excluded from final-visible object/pair coverage.
    """
    x = (word["x0"] + word["x1"]) / 2
    y = (word["y0"] + word["y1"]) / 2
    if word["text"] == "0.4" and 93.0 <= x <= 105.0 and 325.0 <= y <= 338.0:
        return "H05_ACCEPT_BOX (later opaque white fill, source lines 47-51)"
    return None


def line_geometry_mask(shape: tuple[int, int], sx: float, sy: float, rect_pt: tuple[float, float, float, float]) -> np.ndarray:
    """Inclusive rectangular selection only; no morphology is used."""
    h, w = shape
    x0, y0, x1, y1 = rect_pt_to_px(rect_pt, sx, sy, w, h)
    m = np.zeros((h, w), dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


def make_graphics(image: np.ndarray, text_union: np.ndarray, sx: float, sy: float) -> list[dict]:
    h, w = image.shape[:2]
    plot = line_geometry_mask((h, w), sx, sy, PLOT_RECT_PT)
    blue = colour_ray_mask(image, COLORS["BLUE"]) & plot & ~text_union
    teal = colour_ray_mask(image, COLORS["TEAL"]) & plot & ~text_union
    gold = colour_ray_mask(image, COLORS["GOLD"]) & plot & ~text_union
    # Borders are strictly source-colour selected so anti-aliased black formula
    # pixels cannot enter a border mask.
    gray_all = colour_ray_mask(image, COLORS["GRAY"])
    gray = gray_all & plot & ~text_union
    textgray = colour_ray_mask(image, COLORS["TEXTGRAY"]) & plot & ~text_union
    ink = colour_ray_mask(image, COLORS["INK"]) & plot & ~text_union

    def selected(mask: np.ndarray, rect: tuple[float, float, float, float]) -> np.ndarray:
        return mask & line_geometry_mask((h, w), sx, sy, rect)

    def border_band(mask: np.ndarray, x0: int, y0: int, x1: int, y1: int, band: int = 5) -> np.ndarray:
        """Select only final-raster stroke pixels in four measured edge bands.

        The coordinates are native R94 300-dpi page pixels, derived directly
        from the opaque source nodes.  This separates the callout borders from
        their intentionally connected guide/marker graphics without masking
        or inventing any pixels.
        """
        m = np.zeros((h, w), dtype=bool)
        xa, xb = max(0, x0 - band), min(w, x1 + band + 1)
        ya, yb = max(0, y0 - band), min(h, y1 + band + 1)
        m[ya:min(h, y0 + band + 1), xa:xb] = True
        m[max(0, y1 - band):yb, xa:xb] = True
        m[ya:yb, xa:min(w, x0 + band + 1)] = True
        m[ya:yb, max(0, x1 - band):xb] = True
        return mask & m

    def axis_geometry() -> np.ndarray:
        """Measured native 300-dpi axis/tick strips, excluding all text area."""
        m = np.zeros((h, w), dtype=bool)
        # vertical y-axis and its arrowhead; the accepted white node creates
        # a legitimate final-raster gap, retained by `ink & m` below.
        m[780:1570, 451:466] = True
        # horizontal x-axis and right arrowhead.
        m[1558:1580, 408:1964] = True
        # five horizontal y ticks (0, .4, .8, 1.2, 1.6).
        for yy in (797, 990, 1183, 1376, 1569):
            m[yy - 7:yy + 8, 438:478] = True
        # five vertical x ticks (0, 1/4, 1/2, 3/4, 1).
        for xx in (458, 820, 1206, 1592, 1907):
            m[1548:1584, xx - 8:xx + 9] = True
        return m

    def native_rect(mask: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
        """Integer native-page coordinate selection; preserves only raw pixels."""
        m = np.zeros((h, w), dtype=bool)
        m[max(0, y0):min(h, y1 + 1), max(0, x0):min(w, x1 + 1)] = True
        return mask & m

    # All masks are final-visible subsets of the final R94 raster.  The source
    # colour and a coordinate envelope separate same-colour vector objects.
    candidates = [
        ("G01_P_CURVE", "DATA_CURVE", selected(blue, (76, 194, 472, 375)), 3, "p(y)=6y(1-y), source line 19"),
        ("G02_CQ_ENVELOPE", "LINE_ARROW", selected(teal, (76, 186, 472, 203)), 3, "cq(y)=8/5 dashed envelope, source line 20"),
        ("G03_DELTA_ARROW", "LINE_ARROW", selected(textgray | gray, (263, 183, 292, 216)), 3, "double arrow for 1/10, source lines 38-40"),
        ("G04_ACCEPT_GUIDE", "LINE_ARROW", native_rect(colour_ray_mask(image, COLORS["TEAL"]), 852, 1201, 862, 1566), 3, "accepted-point vertical guide, native x=852..862; source line 44; white callout legitimately hides middle segment"),
        ("G05_ACCEPT_MARKER", "MARKER", native_rect(colour_ray_mask(image, COLORS["TEAL"]), 840, 1150, 875, 1210), 3, "filled round accepted marker, native [840,1150]-[875,1210]; source lines 45-46"),
        ("G06_REJECT_GUIDE", "LINE_ARROW", native_rect(colour_ray_mask(image, COLORS["GOLD"]), 1553, 1178, 1566, 1566), 3, "rejected-point dotted guide below opaque node; native x=1553..1566; source line 53"),
        ("G07_REJECT_MARKER", "MARKER", native_rect(colour_ray_mask(image, COLORS["GOLD"]), 1538, 900, 1615, 936), 3, "hollow triangular rejected marker above opaque node; source lines 54-55"),
        ("G08_AXES_AND_TICKS", "LINE_ARROW", ink & axis_geometry() & ~text_union, 3, "axis paths, ticks and arrowheads; measured native source geometry strips; text subtracted"),
        ("G09_TITLE_BORDER", "NODE_BORDER", border_band(gray_all, 432, 284, 1980, 670), 5, "opaque white title-node border; native bands [432,284]-[1980,670]; source lines 23-25"),
        ("G10_ACCEPT_BORDER", "NODE_BORDER", border_band(colour_ray_mask(image, COLORS["TEAL"]), 380, 1203, 834, 1440), 5, "opaque white accepted-callout border; native bands [380,1203]-[834,1440]; source lines 47-49"),
        ("G11_REJECT_BORDER", "NODE_BORDER", border_band(colour_ray_mask(image, COLORS["GOLD"]), 1556, 939, 2146, 1177), 5, "opaque white rejected-callout border; native bands [1556,939]-[2146,1177]; source lines 56-58"),
        ("G12_BOUNDARY_MARKERS", "MARKER", selected(gray | textgray, (70, 350, 480, 380)), 3, "two square support-boundary markers, source lines 63-64"),
    ]
    # Rejection-area fill is visible semantic background.  It is inventoried but
    # excluded from text collision gates just as a node fill is excluded.
    soft = image.astype(np.int16)
    fill_colour = np.array((233, 243, 242), dtype=np.int16)
    fill = (np.abs(soft - fill_colour).max(axis=2) <= 10) & plot
    candidates.append(("G13_REJECTION_FILL", "BACKGROUND_FILL", fill, 0, "0.09 teal fill; source line 21; background-fill exemption"))

    records: list[dict] = []
    for gid, kind, mask, clearance, note in candidates:
        if kind != "BACKGROUND_FILL":
            # Neutral axis candidate can include the title of a nearby formula only
            # if it was not in extracted text.  This explicit source-geometry filter
            # keeps it a raw final pixel subset without dilating it.
            mask = mask & ~text_union
        records.append({"id": gid, "kind": kind, "mask": mask, "required": clearance, "note": note})
    return records


def write_halo_evidence(image: np.ndarray, graphics: list[dict]) -> list[dict]:
    """Preserve actual opaque-halo provenance without inventing hidden pixels.

    `pre_source_vector.svgfrag` is the exact official-PDF SVG vector emitted
    before the white fill.  We intentionally do *not* draw a synthetic
    `pre.png` through an opaque cover: the final raster cannot observe those
    pixels.  `halo_raw_mask.png` and `final_visible_raw_mask.png` are both
    direct subsets of the native final 300-dpi raster.
    """
    if not SVG_PAGE.exists():
        run(["pdftocairo", "-svg", "-f", str(PHYSICAL_PAGE), "-l", str(PHYSICAL_PAGE), str(PDF), str(SVG_PAGE)])
    svg_lines = SVG_PAGE.read_text(encoding="utf-8", errors="replace").splitlines()
    by_id = {g["id"]: g for g in graphics}
    h, w = image.shape[:2]
    exact_white = np.all(image >= 254, axis=2)
    specs = [
        # id, inclusive native page ROI, pre-vector SVG line(s), actual white-fill SVG line(s), final raw object(s), source explanation
        ("H01_BLUE_LABEL", (889, 852, 1065, 905), [1009], [1312], ["G01_P_CURVE"], "p curve at TeX line 19, then white blue-label node at lines 34-35"),
        ("H02_TEAL_LABEL", (1589, 724, 1862, 805), [1010], [1325], ["G02_CQ_ENVELOPE"], "cq envelope at TeX line 20, then white teal-label node at lines 36-37"),
        ("H03_FILL_LABEL", (584, 956, 883, 1085), [958], [1361], ["G13_REJECTION_FILL"], "0.09 teal fill at TeX line 21, then white fill annotation at lines 41-42"),
        ("H04_DELTA_LABEL", (1213, 790, 1268, 868), [1349, 1350, 1351], [1352], ["G03_DELTA_ARROW"], "delta arrow at TeX lines 38-39, then white 1/10 label at line 40"),
        ("H05_ACCEPT_BOX", (379, 1198, 835, 1444), [1385], [1386], ["G04_ACCEPT_GUIDE", "G05_ACCEPT_MARKER"], "accepted guide/marker source lines 44-46; later opaque white box lines 47-51"),
        ("H06_REJECT_BOX", (1553, 906, 2149, 1181), [1487], [1488], ["G06_REJECT_GUIDE", "G07_REJECT_MARKER"], "rejected guide/marker source lines 53-55; later opaque white box lines 56-61"),
    ]
    out: list[dict] = []
    for hid, rect, pre_lines, halo_lines, final_ids, explanation in specs:
        x0, y0, x1, y1 = rect
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w - 1, x1), min(h - 1, y1)
        d = HALO_DIR / hid
        d.mkdir(parents=True, exist_ok=True)
        region = np.zeros((h, w), dtype=bool)
        region[y0:y1 + 1, x0:x1 + 1] = True
        halo_mask = exact_white & region
        final_mask = np.zeros((h, w), dtype=bool)
        for gid in final_ids:
            final_mask |= by_id[gid]["mask"]
        final_mask &= region
        Image.fromarray((halo_mask[y0:y1 + 1, x0:x1 + 1].astype(np.uint8) * 255)).save(d / "halo_raw_mask.png")
        Image.fromarray((final_mask[y0:y1 + 1, x0:x1 + 1].astype(np.uint8) * 255)).save(d / "final_visible_raw_mask.png")
        (d / "pre_source_vector.svgfrag").write_text("\n".join(svg_lines[n - 1] for n in pre_lines) + "\n", encoding="utf-8")
        (d / "halo_source_vector.svgfrag").write_text("\n".join(svg_lines[n - 1] for n in halo_lines) + "\n", encoding="utf-8")
        record = {
            "id": hid, "native_page_roi_xyxy": [x0, y0, x1, y1],
            "pre": "pre_source_vector.svgfrag (exact SVG vector before opaque fill; no synthetic hidden-pixel raster)",
            "halo": "halo_raw_mask.png (exact-white final raster subset, source fill=white)",
            "final_visible": "final_visible_raw_mask.png (final raw graphic subset)",
            "pre_svg_lines": pre_lines, "halo_svg_lines": halo_lines, "final_object_ids": final_ids,
            "halo_raw_pixels": int(halo_mask.sum()), "final_visible_pixels_in_roi": int(final_mask.sum()),
            "explanation": explanation,
        }
        write_json(d / "manifest.json", record)
        out.append(record)
    return out


def save_local_mask(path: Path, mask: np.ndarray, bbox: tuple[int, int, int, int] | None) -> dict:
    if bbox is None:
        Image.fromarray(np.zeros((1, 1), dtype=np.uint8)).save(path)
        return {"bbox": None, "origin": None, "pixels": 0}
    x0, y0, x1, y1 = bbox
    local = (mask[y0:y1 + 1, x0:x1 + 1].astype(np.uint8) * 255)
    Image.fromarray(local).save(path)
    return {"bbox": [x0, y0, x1, y1], "origin": [x0, y0], "pixels": int(mask.sum())}


def parent_masks(text_records: list[dict], h: int, w: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in text_records:
        grouped[r["parent"]].append(r)
    parents: list[dict] = []
    for parent, members in grouped.items():
        mask = np.zeros((h, w), dtype=bool)
        for m in members:
            mask |= m["mask"]
        parents.append({
            "id": "P_" + parent,
            "kind": "FORMULA" if members[0]["role"] in {"FORMULA", "ANNOTATION_FORMULA"} else "TEXT",
            "role": members[0]["role"],
            "mask": mask,
            "members": [m["id"] for m in members],
        })
    return sorted(parents, key=lambda x: x["id"])


def split_glyphs(record: dict, image_shape: tuple[int, int], svg_uses: list[dict], sx: float, sy: float) -> list[dict]:
    text = record["text"]
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return []
    x0, y0, x1, y1 = record["bbox"]
    # Rotated y-axis CJK is still split along its longer word axis.
    vertical = (y1 - y0 + 1) > 1.7 * (x1 - x0 + 1)
    n = len(chars)
    # Match PDF SVG glyph origins to this extracted word.  The y coordinate
    # is a baseline and is therefore allowed a small non-morphological range.
    if vertical:
        candidates = [u for u in svg_uses if record["x0pt"] - 5 <= u["x"] <= record["x1pt"] + 5 and record["y0pt"] - 10 <= u["y"] <= record["y1pt"] + 10]
        candidates.sort(key=lambda u: (u["y"], u["x"], u["order"]))
    else:
        candidates = [u for u in svg_uses if record["x0pt"] - 2 <= u["x"] <= record["x1pt"] + 2 and record["y0pt"] - 7 <= u["y"] <= record["y1pt"] + 10]
        candidates.sort(key=lambda u: (u["x"], u["y"], u["order"]))
    svg_partition = len(candidates) == n
    if svg_partition:
        if vertical:
            coords = [int(round(u["y"] * sy)) for u in candidates]
            bounds = [y0] + [int(math.floor((coords[i] + coords[i + 1]) / 2)) for i in range(n - 1)] + [y1 + 1]
        else:
            coords = [int(round(u["x"] * sx)) for u in candidates]
            bounds = [x0] + [int(math.floor((coords[i] + coords[i + 1]) / 2)) for i in range(n - 1)] + [x1 + 1]
    else:
        bounds = []
    # Build raw glyph masks by assigning *whole connected raw components* to
    # character centres.  Unlike rectangular clipping, this never cuts a
    # visible stroke at a guessed boundary; masks are disjoint and unexpanded.
    if vertical:
        if svg_partition:
            centres = [(bounds[i] + bounds[i + 1] - 1) / 2 for i in range(n)]
        else:
            centres = [y0 + (y1 - y0 + 1) * (i + .5) / n for i in range(n)]
    else:
        if svg_partition:
            centres = [(bounds[i] + bounds[i + 1] - 1) / 2 for i in range(n)]
        else:
            centres = [x0 + (x1 - x0 + 1) * (i + .5) / n for i in range(n)]
    component_masks = [np.zeros(image_shape, dtype=bool) for _ in range(n)]
    word_raw = record["mask"][y0:y1 + 1, x0:x1 + 1].astype(np.uint8)
    ccount, labels, stats, centroids = cv2.connectedComponentsWithStats(word_raw, connectivity=8)
    for comp in range(1, ccount):
        cx = x0 + float(centroids[comp][0])
        cy = y0 + float(centroids[comp][1])
        coordinate = cy if vertical else cx
        target = int(np.argmin([abs(coordinate - z) for z in centres]))
        component_masks[target][y0:y1 + 1, x0:x1 + 1] |= labels == comp
    component_partition = all(m.any() for m in component_masks)
    if not component_partition:
        # Some math glyphs have components whose centroid lies on a neighbour
        # (e.g. paired delimiters).  Preserve every raw pixel with a disjoint
        # source-position cell fallback rather than emitting an empty glyph.
        component_masks = [np.zeros(image_shape, dtype=bool) for _ in range(n)]
        for i in range(n):
            if vertical:
                if svg_partition:
                    a0, a1 = bounds[i], bounds[i + 1] - 1
                else:
                    a0 = y0 + math.floor((y1 - y0 + 1) * i / n)
                    a1 = y0 + math.floor((y1 - y0 + 1) * (i + 1) / n) - 1
                component_masks[i][a0:a1 + 1, x0:x1 + 1] = record["mask"][a0:a1 + 1, x0:x1 + 1]
            else:
                if svg_partition:
                    a0, a1 = bounds[i], bounds[i + 1] - 1
                else:
                    a0 = x0 + math.floor((x1 - x0 + 1) * i / n)
                    a1 = x0 + math.floor((x1 - x0 + 1) * (i + 1) / n) - 1
                component_masks[i][y0:y1 + 1, a0:a1 + 1] = record["mask"][y0:y1 + 1, a0:a1 + 1]
    glyphs: list[dict] = []
    natural_script = (record["y1pt"] - record["y0pt"]) < 9.55 and record["role"] in {"FORMULA", "ANNOTATION_FORMULA"}
    for i, c in enumerate(chars):
        local = component_masks[i]
        cls, threshold = glyph_class(c, natural_script)
        b = bbox_from_mask(local)
        if b is None:
            ink_h = 0
            ink_w = 0
        else:
            ink_h = b[3] - b[1] + 1
            ink_w = b[2] - b[0] + 1
        # The rotated vertical CJK labels retain glyph body height along the
        # vertical axis; no vector scaling or morphological operation occurs.
        gid = f"{record['id']}_G{i + 1:02d}"
        glyphs.append({
            "id": gid, "element_id": record["id"], "char": c, "mask": local,
            "bbox": b, "script_class": cls, "threshold": threshold,
            "h_ink": ink_h, "w_ink": ink_w, "natural_script": natural_script,
            "role": record["role"], "panel": "A", "partition_method": (
                "SVG_USE_COMPONENT_ASSIGN" if svg_partition and component_partition else
                "WORD_BBOX_COMPONENT_ASSIGN" if component_partition else
                "SVG_USE_CELL_FALLBACK" if svg_partition else "WORD_BBOX_CELL_FALLBACK"),
        })
    return glyphs


def distance_between(a: np.ndarray, b: np.ndarray, b_distance: np.ndarray | None = None) -> float:
    if not a.any() or not b.any():
        return float("inf")
    if b_distance is None:
        b_distance = distance_transform_edt(~b)
    return float(b_distance[a].min())


def draw_pair_package(pair: dict, image: Image.Image, a: np.ndarray, b: np.ndarray) -> str:
    h, w = a.shape
    union = a | b
    bb = bbox_from_mask(union)
    if bb is None:
        raise RuntimeError("cannot create pair evidence for two empty masks")
    x0, y0, x1, y1 = crop_bbox(bb, 8, w, h)
    base = image.crop((x0, y0, x1 + 1, y1 + 1)).convert("RGB")
    aa = a[y0:y1 + 1, x0:x1 + 1]
    bbm = b[y0:y1 + 1, x0:x1 + 1]
    inter = aa & bbm
    package = PAIR_DIR / pair["CHECK_ID"]
    package.mkdir(parents=True, exist_ok=True)
    base.save(package / "raw.png")
    Image.fromarray((aa.astype(np.uint8) * 255)).save(package / "A_raw_mask.png")
    Image.fromarray((bbm.astype(np.uint8) * 255)).save(package / "B_raw_mask.png")
    Image.fromarray((inter.astype(np.uint8) * 255)).save(package / "intersection_raw_mask.png")
    overlay = np.asarray(base).copy()
    overlay[aa] = (255, 0, 0)
    overlay[bbm] = (0, 130, 255)
    overlay[inter] = (255, 0, 255)
    Image.fromarray(overlay).save(package / "overlay.png")
    base.save(package / "roi_1to1.png")
    base.resize((base.width * 8, base.height * 8), Image.Resampling.NEAREST).save(package / "roi_8x_nearest.png")

    # A compact nearest-pixel focus is included in addition to the complete
    # pair ROI, so the reviewer can see the actual critical relation at 1:1
    # and 8x without a resized overview hiding the relevant point.
    dmap, nearest = distance_transform_edt(~b, return_indices=True)
    ay, ax = np.where(a)
    pick = int(np.argmin(dmap[ay, ax]))
    ax0, ay0 = int(ax[pick]), int(ay[pick])
    bx0, by0 = int(nearest[1, ay0, ax0]), int(nearest[0, ay0, ax0])
    fbb = crop_bbox((min(ax0, bx0), min(ay0, by0), max(ax0, bx0), max(ay0, by0)), 12, w, h)
    fx0, fy0, fx1, fy1 = fbb
    fraw = image.crop((fx0, fy0, fx1 + 1, fy1 + 1)).convert("RGB")
    fa = a[fy0:fy1 + 1, fx0:fx1 + 1]
    fb = b[fy0:fy1 + 1, fx0:fx1 + 1]
    finter = fa & fb
    fraw.save(package / "focus_raw.png")
    Image.fromarray((fa.astype(np.uint8) * 255)).save(package / "focus_A_raw_mask.png")
    Image.fromarray((fb.astype(np.uint8) * 255)).save(package / "focus_B_raw_mask.png")
    Image.fromarray((finter.astype(np.uint8) * 255)).save(package / "focus_intersection_raw_mask.png")
    foverlay = np.asarray(fraw).copy()
    foverlay[fa] = (255, 0, 0)
    foverlay[fb] = (0, 130, 255)
    foverlay[finter] = (255, 0, 255)
    Image.fromarray(foverlay).save(package / "focus_overlay.png")
    fraw.save(package / "focus_roi_1to1.png")
    fraw.resize((fraw.width * 8, fraw.height * 8), Image.Resampling.NEAREST).save(package / "focus_roi_8x_nearest.png")
    manifest = {
        "check_id": pair["CHECK_ID"], "native_page_coordinate_roi": [x0, y0, x1, y1],
        "counting_coordinate": "native 300dpi 1:1", "resampling": "none for raw/A/B/intersection/1to1; nearest only for 8x",
        "A": pair["ELEMENT_A_ID"], "B": pair["ELEMENT_B_ID"],
        "overlap_pixels": pair["OVERLAP_PIXEL_COUNT"], "min_clearance_px": pair["MIN_CLEARANCE_PX"],
        "nearest_native_page_pixels": {"A": [ax0, ay0], "B": [bx0, by0]},
        "focus_native_page_coordinate_roi": [fx0, fy0, fx1, fy1],
    }
    write_json(package / "manifest.json", manifest)
    return str(package.relative_to(ROOT)).replace("\\", "/")


def make_overlay(image: Image.Image, records: list[dict]) -> None:
    out = image.copy().convert("RGBA")
    d = ImageDraw.Draw(out, "RGBA")
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    colors = [(203, 53, 70, 255), (15, 118, 110, 255), (31, 78, 121, 255), (183, 121, 31, 255)]
    for i, r in enumerate(records):
        b = r["bbox"]
        x0, y0, x1, y1 = b
        c = colors[i % len(colors)]
        d.rectangle((x0, y0, x1, y1), outline=c, width=1)
        label = r["id"]
        tb = d.textbbox((0, 0), label, font=font)
        ly = max(0, y0 - (tb[3] - tb[1] + 2))
        d.rectangle((x0, ly, x0 + (tb[2] - tb[0] + 3), y0), fill=(255, 255, 224, 230))
        d.text((x0 + 1, ly), label, font=font, fill=c)
    out.convert("RGB").save(ROOT / "after_text_measurement_overlay_300dpi.png", dpi=(300, 300))


def main() -> int:
    ensure_dirs()
    if not PDF.exists():
        raise FileNotFoundError(PDF)
    p200, p300 = render()
    page = Image.open(p300).convert("RGB")
    image = np.asarray(page)
    h, w = image.shape[:2]
    sx, sy = w / 595.276, h / 841.890
    fig_px = rect_pt_to_px(FIGURE_RECT_PT, sx, sy, w, h)
    stand_px = rect_pt_to_px(STANDALONE_RECT_PT, sx, sy, w, h)
    page.crop(fig_px).save(ROOT / "figure_crop_300dpi.png", dpi=(300, 300))
    standalone = page.crop(stand_px)
    standalone.save(ROOT / "standalone_300dpi.png", dpi=(300, 300))
    ImageOps.grayscale(standalone).save(ROOT / "grayscale_300dpi.png", dpi=(300, 300))

    words = [x for x in get_words() if inside(x, FIGURE_RECT_PT)]
    text_records: list[dict] = []
    occluded_source_records: list[dict] = []
    for no, word in enumerate(words, 1):
        exclusion = final_visibility_exclusion(word)
        if exclusion:
            occluded_source_records.append({
                "SOURCE_CANDIDATE_ID": f"T{no:03d}", "TEXT_SAMPLE": word["text"],
                "PDF_BBOX_PT": ",".join(f"{word[k]:.3f}" for k in ("x0", "y0", "x1", "y1")),
                "FINAL_VISIBILITY": "OCCLUDED_NOT_FINAL_VISIBLE", "OCCLUDER": exclusion,
                "REASON": "later opaque source node covers whole candidate; do not borrow its later text pixels as a tick mask",
            })
            continue
        parent, role, declared, line = parent_for(word)
        word.update(parent=parent, role=role, declared=declared, source_line=line)
        mask, bbox = raw_text_mask(image, word, sx, sy, w, h)
        bmask = bbox_from_mask(mask)
        rec = {
            "id": f"T{no:03d}", "parent": parent, "role": role,
            "text": word["text"], "source_line": line, "declared": declared,
            "effective": declared, "scale": 1.0, "mask": mask,
            "bbox": bmask if bmask is not None else bbox,
            "mask_bbox": bmask, "x0pt": word["x0"], "y0pt": word["y0"], "x1pt": word["x1"], "y1pt": word["y1"],
        }
        text_records.append(rec)

    if not text_records:
        raise RuntimeError("no figure text parsed from official physical page")
    write_csv(ROOT / "occlusion_ledger.csv", occluded_source_records, ["SOURCE_CANDIDATE_ID", "TEXT_SAMPLE", "PDF_BBOX_PT", "FINAL_VISIBILITY", "OCCLUDER", "REASON"])
    text_union = np.zeros((h, w), dtype=bool)
    for r in text_records:
        text_union |= r["mask"]
    graphics = make_graphics(image, text_union, sx, sy)
    parents = parent_masks(text_records, h, w)

    # Persist raw masks and source maps.  Every nonempty visual object is a
    # direct subset of the 300dpi final raster and has an integer-coordinate bbox.
    inventory: list[dict] = []
    empty_masks = 0
    for r in text_records:
        meta = save_local_mask(RAW_DIR / f"{r['id']}.png", r["mask"], r["mask_bbox"])
        empty_masks += int(meta["pixels"] == 0)
        inventory.append({"id": r["id"], "kind": "TEXT_PRIMITIVE", "parent": r["parent"], "role": r["role"], "text": r["text"], **meta})
    for r in parents:
        b = bbox_from_mask(r["mask"])
        meta = save_local_mask(RAW_DIR / f"{r['id']}.png", r["mask"], b)
        empty_masks += int(meta["pixels"] == 0)
        r["bbox"] = b
        inventory.append({"id": r["id"], "kind": r["kind"], "role": r["role"], "members": r["members"], **meta})
    for r in graphics:
        b = bbox_from_mask(r["mask"])
        meta = save_local_mask(RAW_DIR / f"{r['id']}.png", r["mask"], b)
        empty_masks += int(meta["pixels"] == 0 and r["kind"] != "BACKGROUND_FILL")
        r["bbox"] = b
        inventory.append({"id": r["id"], "kind": r["kind"], "note": r["note"], **meta})

    svg_uses = get_svg_glyph_uses()
    glyphs: list[dict] = []
    for r in text_records:
        glyphs.extend(split_glyphs(r, (h, w), svg_uses, sx, sy))
    for g in glyphs:
        meta = save_local_mask(GLYPH_DIR / f"{g['id']}.png", g["mask"], g["bbox"])
        g["mask_path"] = str((GLYPH_DIR / f"{g['id']}.png").relative_to(ROOT)).replace("\\", "/")
        g["pixels"] = meta["pixels"]

    # Metrics are deliberately layered:
    #   (1) `font_rows`: unique semantic font ELEMENTS, never 159 word spans;
    #   (2) `pixel_rows`: all 159 extracted visible text primitives;
    #   (3) `glyph_rows`: every raw glyph trace.  D/E stay separate from the
    #       raw-pixel-height gate and cannot inflate its failure count.
    glyph_by_element: dict[str, list[dict]] = defaultdict(list)
    for g in glyphs:
        g["script_family"] = script_family(g["char"])
        glyph_by_element[g["element_id"]].append(g)
    font_rows: list[dict] = []
    pixel_rows: list[dict] = []
    glyph_rows: list[dict] = []
    for g in glyphs:
        same = [z for z in glyphs if z["panel"] == g["panel"] and z["role"] == g["role"] and z["script_family"] == g["script_family"]]
        vals = [z["h_ink"] for z in same if z["pixels"] > 0]
        med = float(np.median(vals)) if vals else 0.0
        ratio = g["h_ink"] / med if med else 0.0
        # D = same panel + same role + same script-family only.  It is a
        # consistency diagnostic, not a pixel-height failure propagator.
        d_pass = bool(vals) and 0.92 <= ratio <= 1.08
        g["class_median"] = med
        g["class_ratio"] = ratio
        g["d_pass"] = d_pass
        g["pixel_pass"] = g["pixels"] > 0 and g["h_ink"] >= g["threshold"]
        glyph_rows.append({
            "GLYPH_ID": g["id"], "ELEMENT_ID": g["element_id"], "CHAR": g["char"], "ROLE": g["role"],
            "SCRIPT_CLASS": g["script_class"], "SCRIPT_FAMILY": g["script_family"], "NATURAL_SCRIPT": str(g["natural_script"]).lower(), "PARTITION_METHOD": g["partition_method"],
            "BBOX": "" if g["bbox"] is None else ",".join(map(str, g["bbox"])), "H_INK_PX": g["h_ink"], "W_INK_PX": g["w_ink"],
            "THRESHOLD_PX": g["threshold"], "PIXEL_HEIGHT_PASS": "PASS" if g["pixel_pass"] else "FAIL",
            "D_BASE_SCOPE": f"A/{g['role']}/{g['script_family']}", "D_MEDIAN_PX": f"{med:.3f}", "D_RATIO": f"{ratio:.4f}", "D_SAME_SCRIPT_PASS": "PASS" if d_pass else "FAIL",
            "RAW_MASK": g["mask_path"], "REASON": "native 300dpi raw glyph mask; delta=20; no dilation; non-overlapping character partition",
        })

    # E only compares CJK with an explicit same-script BASE.  All other
    # scripts are N/A, rather than cross-compared to an unrelated CJK body.
    cjk_base_id = "T107"  # `接受（圆点）`: ordinary 9.6pt annotation CJK
    cjk_base_values = [g["h_ink"] for g in glyph_by_element.get(cjk_base_id, []) if g["script_family"] == "CJK" and g["pixels"] > 0]
    cjk_base = float(np.median(cjk_base_values)) if cjk_base_values else None

    text_by_id = {r["id"]: r for r in text_records}
    semantic_font_records: list[dict] = []
    for p in parents:
        members = [text_by_id[mid] for mid in p["members"]]
        declared_values = [m["declared"] for m in members]
        effective_values = [m["effective"] for m in members]
        semantic_font_records.append({
            "id": p["id"], "role": p["role"], "members": members,
            "declared": min(declared_values), "effective": min(effective_values),
            "text": " ".join(m["text"] for m in members),
            "lines": ",".join(sorted({m["source_line"] for m in members})),
        })
    by_role = defaultdict(list)
    for s in semantic_font_records:
        by_role[s["role"]].append(s)
    for s in semantic_font_records:
        same_pt = [z["effective"] for z in by_role[s["role"]]]
        same_ratio = max(same_pt) / min(same_pt)
        same_diff = max(same_pt) - min(same_pt)
        source_ok = s["effective"] >= 9.5 and same_ratio <= 1.03 and same_diff <= .25
        font_rows.append({
            "SEMANTIC_ELEMENT_ID": s["id"], "PANEL_ID": "A", "ROLE": s["role"], "SOURCE_FILE": "fig_v5_c02_rejection_envelope.tex",
            "SOURCE_LINE": s["lines"], "PRIMITIVE_MEMBER_COUNT": len(s["members"]), "PRIMITIVE_IDS": ",".join(m["id"] for m in s["members"]),
            "TEXT_SAMPLE": s["text"], "DECLARED_PT": f"{s['declared']:.4f}", "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": f"{s['effective']:.4f}",
            "SAME_PANEL_SAME_ROLE_PT_MAX_MIN": f"{same_ratio:.4f}", "SAME_PANEL_SAME_ROLE_PT_ABS_DIFF": f"{same_diff:.4f}",
            "SOURCE_FONT_PASS": "PASS" if source_ok else "FAIL", "REASON": "direct source declaration x cumulative graphics scale=1; no resizebox/scalebox/transform shape",
        })
    for r in text_records:
        gs = glyph_by_element[r["id"]]
        nonempty = [g for g in gs if g["pixels"] > 0]
        heights = [g["h_ink"] for g in nonempty]
        h_med = float(np.median(heights)) if heights else 0.0
        min_g = min(gs, key=lambda x: x["h_ink"], default=None)
        pixel_ok = bool(gs) and all(g["pixel_pass"] for g in gs)
        d_ok = bool(gs) and all(g["d_pass"] for g in gs)
        cjk_here = [g for g in gs if g["script_family"] == "CJK" and g["pixels"] > 0]
        if cjk_here and cjk_base:
            rr = float(np.median([g["h_ink"] for g in cjk_here])) / cjk_base
            role_state = "PASS" if .95 <= rr <= 1.18 else "FAIL"
            role_reason = f"CJK-only E comparison to explicit BASE {cjk_base_id}; no cross-script comparison"
            e_base = cjk_base_id
        else:
            rr = None
            role_state = "N/A"
            role_reason = "no comparable same-script BASE; E is N/A (not cross-script compared)"
            e_base = "N/A"
        combined = pixel_ok and d_ok and role_state != "FAIL"
        pixel_rows.append({
            "ELEMENT_ID": r["id"], "SEMANTIC_PARENT_ID": "P_" + r["parent"], "PANEL_ID": "A", "ROLE": r["role"], "SOURCE_FILE": "fig_v5_c02_rejection_envelope.tex",
            "SOURCE_LINE": r["source_line"], "DECLARED_PT": f"{r['declared']:.4f}", "GRAPHICS_SCALE": "1.0000", "EFFECTIVE_PT": f"{r['effective']:.4f}",
            "TEXT_SAMPLE": r["text"], "SCRIPT_CLASS": "MIXED" if len({g['script_class'] for g in gs}) > 1 else (gs[0]['script_class'] if gs else "UNKNOWN"),
            "BBOX_X0": r["bbox"][0], "BBOX_Y0": r["bbox"][1], "BBOX_X1": r["bbox"][2], "BBOX_Y1": r["bbox"][3],
            "H_INK_PX": f"{h_med:.2f}", "MIN_GLYPH_ID": min_g["id"] if min_g else "", "MIN_GLYPH_H_INK_PX": min_g["h_ink"] if min_g else 0,
            "PIXEL_HEIGHT_PASS": "PASS" if pixel_ok else "FAIL", "D_SAME_SCRIPT_PASS": "PASS" if d_ok else "FAIL", "E_BASE_ID": e_base, "E_ROLE_RATIO": "N/A" if rr is None else f"{rr:.4f}",
            "E_ROLE_RATIO_PASS": role_state, "TEXT_TEXT_OVERLAP_PX": "SEE_OVERLAP_REPORT", "TEXT_GRAPHIC_OVERLAP_PX": "SEE_OVERLAP_REPORT",
            "MIN_CLEARANCE_PX": "SEE_OVERLAP_REPORT", "COMBINED_ELEMENT_GATE": "PASS" if combined else "FAIL", "REASON": role_reason,
        })

    # Real white covers use an explicit pre-vector / halo-raw / final-visible
    # triplet.  No pixel is invented beneath an opaque source fill.
    halo_records = write_halo_evidence(image, graphics)

    # Full semantic relation matrix: every unordered text-parent pair and every
    # text-parent x non-background graphic.  Formula-internal glyphs are not
    # mistaken for separate external text objects; their raw masks are audited
    # individually in glyph_measurements.csv.
    pairs: list[dict] = []
    parent_by_id = {p["id"]: p for p in parents}
    graphic_nonbg = [g for g in graphics if g["kind"] != "BACKGROUND_FILL"]
    cache_dist: dict[str, np.ndarray] = {}

    def semantic_text_bbox_gap(a: dict, b: dict) -> tuple[float, str]:
        """Minimum cross-element primitive-bbox clearance.

        A multiline formula's *union* bbox can put a numerator at one x and
        a lower line at another x, yielding a fictitious overlap with a title.
        The strict 4px text-text bbox gate is therefore evaluated across every
        final-visible primitive bbox belonging to the two semantic elements.
        """
        best = (float("inf"), "")
        for aid in a["members"]:
            for bid in b["members"]:
                ab = text_by_id[aid]["bbox"]
                bb = text_by_id[bid]["bbox"]
                gap = bbox_gap(ab, bb) if ab and bb else -1.0
                if gap < best[0]:
                    best = (gap, f"{aid}|{bid}")
        return best

    count = 0
    for a, b in itertools.combinations(parents, 2):
        count += 1
        overlap = int(np.count_nonzero(a["mask"] & b["mask"]))
        clearance, bbox_subpair = semantic_text_bbox_gap(a, b)
        required = 4
        passed = overlap == 0 and clearance >= required
        pairs.append({"CHECK_ID": f"TT{count:03d}", "VIEW": "PAGE_300DPI", "PAIR_TYPE": "TEXT_TEXT", "ELEMENT_A_ID": a["id"], "ELEMENT_A_CLASS": a["kind"], "ELEMENT_B_ID": b["id"], "ELEMENT_B_CLASS": b["kind"], "OVERLAP_PIXEL_COUNT": overlap, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": f"{clearance:.3f}", "REQUIRED_CLEARANCE_PX": required, "BBOX_SUBPAIR": bbox_subpair, "PASS_FAIL": "PASS" if passed else "FAIL", "REASON": "native 300dpi separated raw masks; minimum unexpanded cross-primitive bbox clearance", "EVIDENCE_ROI": ""})
    for a in parents:
        for b in graphic_nonbg:
            count += 1
            if b["id"] not in cache_dist:
                cache_dist[b["id"]] = distance_transform_edt(~b["mask"])
            overlap = int(np.count_nonzero(a["mask"] & b["mask"]))
            clearance = distance_between(a["mask"], b["mask"], cache_dist[b["id"]])
            required = int(b["required"])
            passed = overlap == 0 and clearance >= required
            pairs.append({"CHECK_ID": f"TG{count:03d}", "VIEW": "PAGE_300DPI", "PAIR_TYPE": f"{a['kind']}_{b['kind']}", "ELEMENT_A_ID": a["id"], "ELEMENT_A_CLASS": a["kind"], "ELEMENT_B_ID": b["id"], "ELEMENT_B_CLASS": b["kind"], "OVERLAP_PIXEL_COUNT": overlap, "CLIP_PIXEL_COUNT": 0, "MIN_CLEARANCE_PX": f"{clearance:.3f}", "REQUIRED_CLEARANCE_PX": required, "BBOX_SUBPAIR": "N/A", "PASS_FAIL": "PASS" if passed else "FAIL", "REASON": b["note"], "EVIDENCE_ROI": ""})

    # No object may touch the physical page edge.  Crop-edge is a separate
    # 6px reading-space check and does not substitute for physical clip count.
    clip_total = 0
    edge_rows: list[dict] = []
    figedge = fig_px
    for obj in parents + graphic_nonbg:
        b = obj["bbox"]
        if b is None:
            clip = 1
            edge_clear = -1.0
        else:
            clip = int(np.count_nonzero(obj["mask"][0, :]) + np.count_nonzero(obj["mask"][-1, :]) + np.count_nonzero(obj["mask"][:, 0]) + np.count_nonzero(obj["mask"][:, -1]))
            edge_clear = float(min(b[0] - figedge[0], b[1] - figedge[1], figedge[2] - 1 - b[2], figedge[3] - 1 - b[3]))
        clip_total += clip
        req = 6 if obj in parents else 0
        edge_rows.append({"CHECK_ID": f"EDGE_{obj['id']}", "VIEW": "PAGE_300DPI", "PAIR_TYPE": "TEXT_IMAGE_EDGE" if obj in parents else "GRAPHIC_IMAGE_EDGE", "ELEMENT_A_ID": obj["id"], "ELEMENT_A_CLASS": obj["kind"], "ELEMENT_B_ID": "FIGURE_CROP_EDGE", "ELEMENT_B_CLASS": "EDGE", "OVERLAP_PIXEL_COUNT": 0, "CLIP_PIXEL_COUNT": clip, "MIN_CLEARANCE_PX": f"{edge_clear:.3f}", "REQUIRED_CLEARANCE_PX": req, "BBOX_SUBPAIR": "N/A", "PASS_FAIL": "PASS" if clip == 0 and edge_clear >= req else "FAIL", "REASON": "physical-page clip separately counted; crop-edge clearance is native 300dpi", "EVIDENCE_ROI": ""})
    pairs.extend(edge_rows)

    # Save evidence only for true failures or configured critical near-threshold
    # relations.  The result is human-viewed at native 1:1 and 8x nearest later.
    masks = {x["id"]: x["mask"] for x in parents + graphic_nonbg}
    critical_ids: list[str] = []
    for pair in pairs:
        if pair["ELEMENT_B_ID"] not in masks or pair["ELEMENT_A_ID"] not in masks:
            continue
        clearance = float(pair["MIN_CLEARANCE_PX"])
        required = int(pair["REQUIRED_CLEARANCE_PX"])
        critical = pair["PASS_FAIL"] == "FAIL" or clearance <= required + 2
        if critical:
            pair["EVIDENCE_ROI"] = draw_pair_package(pair, page, masks[pair["ELEMENT_A_ID"]], masks[pair["ELEMENT_B_ID"]])
            critical_ids.append(pair["CHECK_ID"])

    # Every pixel-height failure gets its own native and 8x glyph package.
    glyph_fail_ids: list[str] = []
    for g in glyphs:
        if g["pixel_pass"]:
            continue
        if g["bbox"] is None:
            continue
        gx0, gy0, gx1, gy1 = crop_bbox(g["bbox"], 5, w, h)
        d = GLYPH_EVIDENCE_DIR / g["id"]
        d.mkdir(parents=True, exist_ok=True)
        raw = page.crop((gx0, gy0, gx1 + 1, gy1 + 1))
        raw.save(d / "raw.png")
        gm = g["mask"][gy0:gy1 + 1, gx0:gx1 + 1]
        Image.fromarray(gm.astype(np.uint8) * 255).save(d / "raw_mask.png")
        raw.save(d / "roi_1to1.png")
        raw.resize((raw.width * 8, raw.height * 8), Image.Resampling.NEAREST).save(d / "roi_8x_nearest.png")
        write_json(d / "manifest.json", {"glyph_id": g["id"], "char": g["char"], "native_page_coordinate_roi": [gx0, gy0, gx1, gy1], "h_ink_px": g["h_ink"], "threshold_px": g["threshold"], "raw_mask_coordinate": "native 300dpi 1:1"})
        glyph_fail_ids.append(g["id"])

    make_overlay(page, text_records)
    font_fields = ["SEMANTIC_ELEMENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "PRIMITIVE_MEMBER_COUNT", "PRIMITIVE_IDS", "TEXT_SAMPLE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "SAME_PANEL_SAME_ROLE_PT_MAX_MIN", "SAME_PANEL_SAME_ROLE_PT_ABS_DIFF", "SOURCE_FONT_PASS", "REASON"]
    pixel_fields = ["ELEMENT_ID", "SEMANTIC_PARENT_ID", "PANEL_ID", "ROLE", "SOURCE_FILE", "SOURCE_LINE", "DECLARED_PT", "GRAPHICS_SCALE", "EFFECTIVE_PT", "TEXT_SAMPLE", "SCRIPT_CLASS", "BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1", "H_INK_PX", "MIN_GLYPH_ID", "MIN_GLYPH_H_INK_PX", "PIXEL_HEIGHT_PASS", "D_SAME_SCRIPT_PASS", "E_BASE_ID", "E_ROLE_RATIO", "E_ROLE_RATIO_PASS", "TEXT_TEXT_OVERLAP_PX", "TEXT_GRAPHIC_OVERLAP_PX", "MIN_CLEARANCE_PX", "COMBINED_ELEMENT_GATE", "REASON"]
    glyph_fields = ["GLYPH_ID", "ELEMENT_ID", "CHAR", "ROLE", "SCRIPT_CLASS", "SCRIPT_FAMILY", "NATURAL_SCRIPT", "PARTITION_METHOD", "BBOX", "H_INK_PX", "W_INK_PX", "THRESHOLD_PX", "PIXEL_HEIGHT_PASS", "D_BASE_SCOPE", "D_MEDIAN_PX", "D_RATIO", "D_SAME_SCRIPT_PASS", "RAW_MASK", "REASON"]
    pair_fields = ["CHECK_ID", "VIEW", "PAIR_TYPE", "ELEMENT_A_ID", "ELEMENT_A_CLASS", "ELEMENT_B_ID", "ELEMENT_B_CLASS", "OVERLAP_PIXEL_COUNT", "CLIP_PIXEL_COUNT", "MIN_CLEARANCE_PX", "REQUIRED_CLEARANCE_PX", "BBOX_SUBPAIR", "PASS_FAIL", "REASON", "EVIDENCE_ROI"]
    write_csv(ROOT / "after_font_audit.csv", font_rows, font_fields)
    write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows, pixel_fields)
    write_csv(ROOT / "glyph_measurements.csv", glyph_rows, glyph_fields)
    write_csv(ROOT / "after_overlap_report.csv", pairs, pair_fields)

    source_font_fail = sum(x["SOURCE_FONT_PASS"] == "FAIL" for x in font_rows)
    pixel_fail = sum(x["PIXEL_HEIGHT_PASS"] == "FAIL" for x in glyph_rows)
    d_fail = sum(x["D_SAME_SCRIPT_PASS"] == "FAIL" for x in glyph_rows)
    e_fail = sum(x["E_ROLE_RATIO_PASS"] == "FAIL" for x in pixel_rows)
    combined_element_fail = sum(x["COMBINED_ELEMENT_GATE"] == "FAIL" for x in pixel_rows)
    overlap_total = sum(int(x["OVERLAP_PIXEL_COUNT"]) for x in pairs)
    clearance_fail = sum(x["PASS_FAIL"] == "FAIL" and int(x["OVERLAP_PIXEL_COUNT"]) == 0 for x in pairs)
    pair_fail = sum(x["PASS_FAIL"] == "FAIL" for x in pairs)
    unassigned = [r["id"] for r in text_records if r["role"] == "UNASSIGNED"]
    # Image/semantic visual checks are made manually after generation.  These
    # records deliberately do not conceal the machine failures in RESULT.
    report = {
        "candidate_pdf": str(PDF), "candidate_sha256": sha256(PDF), "physical_page": PHYSICAL_PAGE, "printed_page": 612,
        "page_points": [595.276, 841.890], "native_300dpi_pixels": [w, h], "render_resize": False,
        "figure_crop_page_xyxy": list(fig_px), "standalone_crop_page_xyxy": list(stand_px),
        "source_text_candidates": len(words), "occluded_source_text_candidates": len(occluded_source_records), "final_visible_text_primitives": len(text_records),
        "text_primitives": len(text_records), "semantic_font_elements": len(font_rows), "semantic_text_parents": len(parents), "glyph_traces": len(glyphs),
        "svg_use_positioned_glyphs": sum(g["partition_method"].startswith("SVG_USE") for g in glyphs),
        "word_bbox_fallback_glyphs": sum(g["partition_method"].startswith("WORD_BBOX") for g in glyphs), "graphics": len(graphics),
        "non_background_graphics": len(graphic_nonbg), "pair_rows": len(pairs), "pair_relation_rows": len(pairs) - len(edge_rows),
        "expected_relation_rows": len(parents) * (len(parents) - 1) // 2 + len(parents) * len(graphic_nonbg),
        "empty_masks": empty_masks, "unassigned_text_primitives": unassigned,
        "source_font_fail": source_font_fail, "pixel_height_fail": pixel_fail, "same_script_d_fail": d_fail, "role_e_fail": e_fail, "combined_primitive_gate_fail": combined_element_fail,
        "overlap_pixel_count": overlap_total, "clip_pixel_count": clip_total, "clearance_fail": clearance_fail, "pair_fail": pair_fail,
        "critical_or_failed_pair_packages": len(critical_ids), "critical_or_failed_pair_ids": critical_ids,
        "glyph_failure_packages": len(glyph_fail_ids), "glyph_failure_ids": glyph_fail_ids,
        "halos": halo_records,
    }
    report["halo_integrity_pass"] = all(
        h["halo_raw_pixels"] > 0
        and (HALO_DIR / h["id"] / "pre_source_vector.svgfrag").exists()
        and (HALO_DIR / h["id"] / "halo_raw_mask.png").exists()
        and (HALO_DIR / h["id"] / "final_visible_raw_mask.png").exists()
        for h in halo_records
    )
    report["machine_integrity_pass"] = bool(
        report["expected_relation_rows"] == report["pair_relation_rows"]
        and empty_masks == 0 and not unassigned
        and report["halo_integrity_pass"]
        and all((ROOT / x["EVIDENCE_ROI"]).exists() for x in pairs if x["EVIDENCE_ROI"])
        and len(critical_ids) == sum(1 for x in pairs if x["EVIDENCE_ROI"])
    )
    write_json(ROOT / "object_manifest.json", {"inventory": inventory, "halos": halo_records})
    write_json(ROOT / "machine_terminal.json", report)

    # The only hard result issued by this evidence builder.  D and E are
    # reported separately; their counts never change pixel_height_fail.
    result = "PASS" if report["machine_integrity_pass"] and source_font_fail == 0 and pixel_fail == 0 and d_fail == 0 and e_fail == 0 and overlap_total == 0 and clip_total == 0 and clearance_fail == 0 else "FAIL"
    acceptance = f"""# FIG-P577-01 strict R1 machine acceptance (SA1 preliminary)

- RESULT: `{result}`
- CANDIDATE: frozen R94 `main_full.pdf`, SHA-256 `{report['candidate_sha256']}`
- Anchor: physical page `{PHYSICAL_PAGE}`; printed page `612`; caption anchor `图 31.4`.
- Native rendering: `{w}x{h}` at 300 dpi; crop coordinates are integer page pixels; no raster resize.
- SOURCE_FONT_PASS: `{str(source_font_fail == 0).lower()}` ({source_font_fail} failing semantic font ELEMENTS / {len(font_rows)} total)
- PIXEL_HEIGHT_PASS: `{str(pixel_fail == 0).lower()}` ({pixel_fail} failing raw glyph traces / {len(glyph_rows)} total; this count excludes D/E)
- SAME_SCRIPT_RATIO_PASS (D): `{str(d_fail == 0).lower()}` ({d_fail} failing glyph comparisons; separate from pixel-height)
- ROLE_RATIO_PASS (E): `{str(e_fail == 0).lower()}` ({e_fail} comparable-role failures; all non-comparable scripts recorded `N/A`)
- COMBINED_PRIMITIVE_GATE_FAIL: `{combined_element_fail}` / `{len(pixel_rows)}` (reported separately; it does not alter PIXEL_HEIGHT_FAIL)
- OVERLAP_PIXEL_COUNT: `{overlap_total}`
- CLIP_PIXEL_COUNT: `{clip_total}`
- CLEARANCE_FAIL_COUNT: `{clearance_fail}`
- MACHINE_INTEGRITY_PASS: `{str(report['machine_integrity_pass']).lower()}`

This file is intentionally a machine-preliminary record.  The SA1 visual, mathematical and human 1:1/8x review is appended only after direct review of the generated native evidence.
"""
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")
    print(json.dumps({"result": result, **report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
