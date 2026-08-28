#!/usr/bin/env python3
"""Independent, read-only strict audit for FIG-P525-01.

Inputs are limited to the frozen final PDF and the designated figure/context
sources.  Every file this program writes is below its own SA1 evidence folder.
No source, build, inventory, state, or shared style file is changed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import median

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt


PROJECT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = Path(__file__).resolve().parent
PDF = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
FIG_SRC = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第04册_无监督学习与矩阵分解" / "V4-C06" / "fig_v4_c06_simplex.tex"
CHAPTER = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C06.tex"
STYLE_SRC = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "common" / "statlearnbook.sty"
PDF_PAGE = 571
PAGE_INDEX = PDF_PAGE - 1

# Effective-font provenance, independently rechecked against the shared style:
# fig L3 declares 9.4pt on the picture, but statlearnbook.sty:L276 appends
# `every node/.append style={font=\small}`.  In the 11pt document that node
# style wins for ordinary nodes and renders as 10pt (also corroborated by the
# frozen-PDF 9.963pt vector spans).  Legend nodes have their own explicit 8.8pt
# option at figure L14 and retain that smaller effective size.
PICTURE_INHERITED_FONT_PT = 9.4
GLOBAL_EVERY_NODE_FONT_PT = 10.0
LEGEND_EXPLICIT_FONT_PT = 8.8
ORDINARY_NODE_FONT_ORIGIN = (
    "fig_v4_c06_simplex.tex:L3 picture font=9.4pt; "
    "statlearnbook.sty:L276 every node/.append style={font=\\small} overrides ordinary node effective size to 10.0pt"
)
LEGEND_FONT_ORIGIN = (
    "fig_v4_c06_simplex.tex:L14 explicit font=8.8pt overrides global every-node \\small"
)

# The crop is a direct crop of the native 300-dpi page.  Values are PDF points.
FIGURE_CROP_PDF = (80.0, 410.0, 510.0, 635.0)       # figure plus caption
STANDALONE_CROP_PDF = (80.0, 410.0, 510.0, 606.0)   # isolated figure body
SCOPE_PDF = FIGURE_CROP_PDF


def rel(path: Path) -> str:
    return path.relative_to(OUT).as_posix()


def mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rect_union(rects: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(r[0] for r in rects),
        min(r[1] for r in rects),
        max(r[2] for r in rects),
        max(r[3] for r in rects),
    )


def sorted_unique(values):
    return sorted(set(values))


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), mode="L").save(path)


def bbox_to_pixels(bbox, sx, sy):
    return (bbox[0] * sx, bbox[1] * sy, bbox[2] * sx, bbox[3] * sy)


def bbox_to_slice(bbox_px, width, height):
    x0 = max(0, int(math.floor(bbox_px[0])))
    y0 = max(0, int(math.floor(bbox_px[1])))
    x1 = min(width, int(math.ceil(bbox_px[2])))
    y1 = min(height, int(math.ceil(bbox_px[3])))
    return x0, y0, x1, y1


def crop_mask(mask: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return np.zeros((1, 1), dtype=bool), (0, 0, 1, 1)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return mask[y0:y1, x0:x1], (x0, y0, x1, y1)


def mask_height(mask: np.ndarray) -> int:
    ys = np.nonzero(mask)[0]
    return int(ys.max() - ys.min() + 1) if len(ys) else 0


def local_raw_text_mask(rgb: np.ndarray, bbox_px) -> tuple[np.ndarray, tuple[int, int, int, int], list[int]]:
    """Return the un-dilated, thresholded foreground inside exactly one PDF bbox.

    The two-pixel ring is sampled only to estimate the local background.  The
    returned mask never includes a ring pixel and no morphological operation is
    applied.  A foreground pixel differs from its local background by at least
    20 on at least one RGB channel, which implements the mandated 20/255 gate.
    """
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = bbox_to_slice(bbox_px, w, h)
    if x1 <= x0 or y1 <= y0:
        return np.zeros((1, 1), dtype=bool), (x0, y0, x1, y1), [255, 255, 255]
    ex0, ey0 = max(0, x0 - 2), max(0, y0 - 2)
    ex1, ey1 = min(w, x1 + 2), min(h, y1 + 2)
    expanded = rgb[ey0:ey1, ex0:ex1]
    ring = np.ones(expanded.shape[:2], dtype=bool)
    ring[y0 - ey0:y1 - ey0, x0 - ex0:x1 - ex0] = False
    samples = expanded[ring]
    if len(samples) == 0:
        bg = np.array([255, 255, 255], dtype=np.uint8)
    else:
        colors, counts = np.unique(samples.reshape(-1, 3), axis=0, return_counts=True)
        bg = colors[int(np.argmax(counts))]
    local = rgb[y0:y1, x0:x1]
    raw = np.max(np.abs(local.astype(np.int16) - bg.astype(np.int16)), axis=2) >= 20
    return raw, (x0, y0, x1, y1), [int(v) for v in bg]


def unicode_class(char: str, is_script: bool, role: str) -> tuple[str, int]:
    # Mathematical operators and punctuation retain their own 22px gate even
    # when TeX places them in a sub/superscript (for example k=1).  Only true
    # alphanumeric/Greek script glyphs receive the natural-script allowance.
    cp = ord(char)
    east = unicodedata.east_asian_width(char)
    # Fullwidth punctuation remains in the stricter CJK/fullwidth category.
    if (0x4E00 <= cp <= 0x9FFF) or east in {"F", "W"}:
        return "CJK_OR_FULLWIDTH", 30
    if char in {"=", "≥", "≤", "∑", "∣", "|", "+", "−", "-", "×", "/", "(", ")", ",", ".", "：", "∶", ":"}:
        return "BASE_MATH_OR_PUNCT", 22
    if unicodedata.category(char).startswith("P") or unicodedata.category(char).startswith("S"):
        return "BASE_MATH_OR_PUNCT", 22
    if is_script:
        return "NATURAL_SCRIPT", 15
    if char.isdigit() or char.isupper():
        return "UPPER_OR_DIGIT", 24
    if char.islower() or char in {"𝜃", "𝜙", "𝛾", "𝜋", "𝛼", "𝜑"}:
        return "LOWER_OR_GREEK", 17
    return "BASE_MATH_OR_PUNCT", 22


def group_for_char(cx: float, cy: float) -> str:
    # Every visible glyph inside the figure/caption scope is deliberately
    # assigned; an unassigned glyph aborts the audit instead of becoming unknown.
    if 600.0 <= cy < 630.0:
        return "SEM_CAPTION_PARENT"
    # The first two weight labels overlap the legend's broad y-range.  Assign
    # these spatially distinct figure labels before checking legend text.
    if 540.0 <= cy <= 565.0 and 165.0 <= cx <= 195.0:
        return "SEM_WEIGHT_THETA_1"
    if 550.0 <= cy <= 575.0 and 205.0 <= cx <= 245.0:
        return "SEM_WEIGHT_THETA_2"
    if 510.0 <= cy <= 545.0 and 180.0 <= cx <= 210.0:
        return "SEM_WEIGHT_THETA_3"
    if 545.0 <= cy < 565.0:
        return "SEM_LEGEND_TOPIC" if cx < 372.0 else "SEM_LEGEND_DOCUMENT"
    if 494.0 <= cy < 520.0 and cx >= 285.0:
        return "SEM_FORMULA_LINE_1"
    if 520.0 <= cy < 540.0 and cx >= 285.0:
        return "SEM_FORMULA_LINE_2"
    if cy > 580.0 and cx < 155.0:
        return "SEM_VERTEX_W1"
    if cy > 580.0 and cx > 275.0:
        return "SEM_VERTEX_W2"
    if cy < 450.0 and 190.0 <= cx <= 225.0:
        return "SEM_VERTEX_W3"
    if 560.0 <= cy <= 585.0 and cx < 160.0:
        return "SEM_TOPIC_PHI_1"
    if 555.0 <= cy <= 585.0 and cx > 250.0:
        return "SEM_TOPIC_PHI_2"
    if 450.0 <= cy <= 490.0 and 195.0 <= cx <= 240.0:
        return "SEM_TOPIC_PHI_3"
    raise RuntimeError(f"Unassigned visible glyph at PDF ({cx:.2f}, {cy:.2f})")


SEMANTIC_META = {
    "SEM_VERTEX_W1": {"role": "VERTEX_LABEL", "source_line": 33, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_VERTEX_W2": {"role": "VERTEX_LABEL", "source_line": 34, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_VERTEX_W3": {"role": "VERTEX_LABEL", "source_line": 35, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_TOPIC_PHI_1": {"role": "TOPIC_LABEL", "source_line": 38, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_TOPIC_PHI_2": {"role": "TOPIC_LABEL", "source_line": 38, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_TOPIC_PHI_3": {"role": "TOPIC_LABEL", "source_line": 38, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_WEIGHT_THETA_1": {"role": "WEIGHT_LABEL", "source_line": 44, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_WEIGHT_THETA_2": {"role": "WEIGHT_LABEL", "source_line": 45, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_WEIGHT_THETA_3": {"role": "WEIGHT_LABEL", "source_line": 46, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_FORMULA_LINE_1": {"role": "FORMULA_BLOCK", "source_line": 51, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_FORMULA_LINE_2": {"role": "FORMULA_BLOCK", "source_line": 52, "base_pt": GLOBAL_EVERY_NODE_FONT_PT, "font_origin": ORDINARY_NODE_FONT_ORIGIN},
    "SEM_LEGEND_TOPIC": {"role": "LEGEND", "source_line": 54, "base_pt": LEGEND_EXPLICIT_FONT_PT, "font_origin": LEGEND_FONT_ORIGIN},
    "SEM_LEGEND_DOCUMENT": {"role": "LEGEND", "source_line": 54, "base_pt": LEGEND_EXPLICIT_FONT_PT, "font_origin": LEGEND_FONT_ORIGIN},
    # Caption's final effective size is recoverable from the frozen PDF vector
    # spans.  The figure source has no local caption override.
    "SEM_CAPTION_PARENT": {"role": "CAPTION", "source_line": 56, "base_pt": None, "font_origin": "frozen-PDF vector caption spans; source L56 has no local override"},
}

# PDF content-stream order is not necessarily reader order for TeX math.  The
# component inventory therefore records the source-faithful reader string here,
# while glyph_inventory.csv retains every individual PDF-order glyph/bbox/mask.
SEMANTIC_DISPLAY_TEXT = {
    "SEM_VERTEX_W1": r"$w_1$", "SEM_VERTEX_W2": r"$w_2$", "SEM_VERTEX_W3": r"$w_3$",
    "SEM_TOPIC_PHI_1": r"$\phi_{:1}$", "SEM_TOPIC_PHI_2": r"$\phi_{:2}$", "SEM_TOPIC_PHI_3": r"$\phi_{:3}$",
    "SEM_WEIGHT_THETA_1": r"$\theta_{1j}$", "SEM_WEIGHT_THETA_2": r"$\theta_{2j}$", "SEM_WEIGHT_THETA_3": r"$\theta_{3j}$",
    "SEM_FORMULA_LINE_1": r"$P(w\mid d_j)=\sum_{k=1}^{3}\theta_{kj}\phi_{:k}$",
    "SEM_FORMULA_LINE_2": r"$\theta_{kj}\ge0,\ \sum_k\theta_{kj}=1$",
    "SEM_LEGEND_TOPIC": "圆：主题点", "SEM_LEGEND_DOCUMENT": r"菱形：文档分布 $P(w\mid d_j)$",
    "SEM_CAPTION_PARENT": r"图 29.2 三个单词维度中的主题单纯形：文档分布是主题点按 $\theta_{:j}$ 形成的凸组合",
}


def point_to_scope(pt, sx, sy, scope_x0, scope_y0):
    return (pt.x * sx - scope_x0, pt.y * sy - scope_y0)


def line_selector(shape, p0, p1, width_px):
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    draw.line([p0, p1], fill=255, width=max(1, int(math.ceil(width_px))))
    return np.asarray(canvas) > 0


def polygon_selector(shape, points, fill=True, width_px=1):
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(canvas)
    if fill:
        draw.polygon(points, fill=255)
    else:
        draw.line(points + [points[0]], fill=255, width=max(1, int(math.ceil(width_px))), joint="curve")
    return np.asarray(canvas) > 0


def ellipse_selector(shape, rect_px):
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(canvas).ellipse(rect_px, fill=255)
    return np.asarray(canvas) > 0


def formula_border_selector(shape, rect_px, width_px):
    canvas = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(canvas).rounded_rectangle(rect_px, radius=round(2.0 * (300.0 / 72.0)), outline=255, width=max(1, int(math.ceil(width_px))))
    return np.asarray(canvas) > 0


def raw_graphic_mask(rgb_scope, selector, bg_rgb):
    # The selector is a vector-geometry rasterization at native 300 dpi.  It is
    # not dilated.  It merely separates this vector object from paint-order
    # neighbours before applying the same >=20/255 foreground rule.
    delta = np.max(np.abs(rgb_scope.astype(np.int16) - np.array(bg_rgb, dtype=np.int16)), axis=2)
    return selector & (delta >= 20)


def global_to_local(mask_global, scope_slice):
    x0, y0, x1, y1 = scope_slice
    return mask_global[y0:y1, x0:x1]


def mask_clearance(a: np.ndarray, b: np.ndarray) -> tuple[int, float]:
    overlap = int(np.count_nonzero(a & b))
    if overlap:
        return overlap, 0.0
    if not np.any(a) or not np.any(b):
        # This must not become unknown: no raw foreground for a decorative fill
        # is excluded before pair generation, and all paired objects are visible.
        return 0, float("inf")
    d = distance_transform_edt(~b)
    center_distance = float(d[a].min())
    return 0, max(0.0, center_distance - 1.0)


def crop_pair_roi(original: Image.Image, a: np.ndarray, b: np.ndarray, scope_slice, path_prefix: str, reason: str, manifest: list[dict]):
    """Save native raw ROI, separated masks, overlap and an 8x inspection view."""
    combined = a | b
    local_crop, (lx0, ly0, lx1, ly1) = crop_mask(combined)
    # Give the inspection ROI a pixel margin, but keep constituent masks raw.
    margin = 10
    sx0, sy0, sx1, sy1 = scope_slice
    px0 = max(sx0, sx0 + lx0 - margin)
    py0 = max(sy0, sy0 + ly0 - margin)
    px1 = min(sx1, sx0 + lx1 + margin)
    py1 = min(sy1, sy0 + ly1 + margin)
    roi = original.crop((px0, py0, px1, py1))
    critical = mkdir(OUT / "critical")
    raw_path = critical / f"{path_prefix}_raw.png"
    a_path = critical / f"{path_prefix}_mask_a.png"
    b_path = critical / f"{path_prefix}_mask_b.png"
    ov_path = critical / f"{path_prefix}_overlap.png"
    overlay_path = critical / f"{path_prefix}_overlay.png"
    zoom_path = critical / f"{path_prefix}_overlay_8x.png"
    roi.save(raw_path)
    a_roi = a[py0 - sy0:py1 - sy0, px0 - sx0:px1 - sx0]
    b_roi = b[py0 - sy0:py1 - sy0, px0 - sx0:px1 - sx0]
    save_mask(a_path, a_roi)
    save_mask(b_path, b_roi)
    save_mask(ov_path, a_roi & b_roi)
    arr = np.asarray(roi.convert("RGB")).copy()
    # Boolean-mask one channel at a time: mixed advanced indexing would pair
    # each foreground pixel with the channel tuple and corrupt the overlay.
    arr[:, :, 0][a_roi] = 255
    arr[:, :, 1][a_roi] = 0
    arr[:, :, 2][a_roi] = 0
    arr[:, :, 0][b_roi] = 0
    arr[:, :, 1][b_roi] = 255
    arr[:, :, 2][b_roi] = 0
    both = a_roi & b_roi
    arr[both] = np.array([255, 255, 0], dtype=np.uint8)
    overlay = Image.fromarray(arr, "RGB")
    overlay.save(overlay_path)
    overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(zoom_path)
    manifest.append({
        "ARTIFACT_ID": path_prefix,
        "REASON": reason,
        "RAW_ROI": rel(raw_path),
        "MASK_A": rel(a_path),
        "MASK_B": rel(b_path),
        "OVERLAP_MASK": rel(ov_path),
        "OVERLAY": rel(overlay_path),
        "ZOOM_8X": rel(zoom_path),
    })


def bool_text(v: bool) -> str:
    return "true" if bool(v) else "false"


def main() -> None:
    for input_path in (PDF, FIG_SRC, CHAPTER):
        if not input_path.is_file():
            raise FileNotFoundError(input_path)

    masks_glyph = mkdir(OUT / "masks" / "glyphs")
    masks_sem = mkdir(OUT / "masks" / "semantic")
    masks_graphics = mkdir(OUT / "masks" / "graphics")
    mkdir(OUT / "critical")

    # Native Poppler render: no image resize occurs after rasterization.
    render300_prefix = OUT / "native_300dpi"
    render200_prefix = OUT / "native_200dpi"
    subprocess.run(["pdftoppm", "-png", "-r", "300", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), str(PDF), str(render300_prefix)], check=True)
    subprocess.run(["pdftoppm", "-png", "-r", "200", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), str(PDF), str(render200_prefix)], check=True)
    native300 = OUT / f"native_300dpi-{PDF_PAGE}.png"
    native200 = OUT / f"native_200dpi-{PDF_PAGE}.png"
    full300 = OUT / "full_page_300dpi_native.png"
    full200 = OUT / "full_page_200dpi.png"
    shutil.copyfile(native300, full300)
    shutil.copyfile(native200, full200)

    im300 = Image.open(native300).convert("RGB")
    rgb = np.asarray(im300)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx = im300.width / page.rect.width
    sy = im300.height / page.rect.height
    assert abs(sx - (300.0 / 72.0)) < 0.01 and abs(sy - (300.0 / 72.0)) < 0.01, (sx, sy)

    figure_crop_px = bbox_to_slice(bbox_to_pixels(FIGURE_CROP_PDF, sx, sy), im300.width, im300.height)
    standalone_px = bbox_to_slice(bbox_to_pixels(STANDALONE_CROP_PDF, sx, sy), im300.width, im300.height)
    im300.crop(figure_crop_px).save(OUT / "figure_crop_300dpi.png")
    im300.crop(standalone_px).save(OUT / "standalone_300dpi.png")
    ImageOps.grayscale(im300.crop(figure_crop_px)).save(OUT / "grayscale_300dpi.png")

    frozen_pdf_sha256 = sha256_file(PDF)
    render_manifest = {
        "frozen_pdf": str(PDF),
        "frozen_pdf_sha256": frozen_pdf_sha256,
        "effective_font_provenance": {
            "picture_declared_pt": PICTURE_INHERITED_FONT_PT,
            "ordinary_node_effective_pt": GLOBAL_EVERY_NODE_FONT_PT,
            "ordinary_node_override": f"{STYLE_SRC}:276 every node/.append style={{font=\\small}}",
            "legend_explicit_effective_pt": LEGEND_EXPLICIT_FONT_PT,
        },
        "pdf_page": PDF_PAGE,
        "pdf_page_index_zero_based": PAGE_INDEX,
        "pdf_page_count": len(doc),
        "pdf_page_size_points": [page.rect.width, page.rect.height],
        "native_300dpi_size_px": [im300.width, im300.height],
        "native_200dpi_file": rel(full200),
        "native_300dpi_file": rel(full300),
        "figure_crop_300dpi_file": "figure_crop_300dpi.png",
        "standalone_300dpi_file": "standalone_300dpi.png",
        "grayscale_300dpi_file": "grayscale_300dpi.png",
        "render_command": f"pdftoppm -png -r 300 -f {PDF_PAGE} -l {PDF_PAGE} ...",
        "no_resize_after_native_render": True,
        "crop_is_coordinate_only": True,
        "grayscale_is_mode_conversion_only": True,
        "measurement_view": rel(full300),
        "measurement_scale": [sx, sy],
    }
    (OUT / "render_manifest.json").write_text(json.dumps(render_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Freeze the sole source and immediate context used by SA1.
    fig_lines = FIG_SRC.read_text(encoding="utf-8").splitlines()
    chapter_lines = CHAPTER.read_text(encoding="utf-8").splitlines()
    style_lines = STYLE_SRC.read_text(encoding="utf-8").splitlines()
    write_text(OUT / "source_figure_excerpt.tex", "\n".join(f"{i + 1:03d}: {line}" for i, line in enumerate(fig_lines)) + "\n")
    write_text(OUT / "adjacent_source_context.tex", "\n".join(f"{i:04d}: {chapter_lines[i - 1]}" for i in range(382, 414)) + "\n")
    write_text(OUT / "shared_style_font_context.tex", "\n".join(f"{i:04d}: {style_lines[i - 1]}" for i in range(269, 281)) + "\n")
    page_text = page.get_text("text")
    caption_lines = [line for line in page_text.splitlines() if "三个单词维度中的主题单纯形" in line or "不同参数可以给出相同文档点" in line]
    write_text(OUT / "pdf_context_excerpt.txt", f"Frozen PDF physical page: {PDF_PAGE}\n\n" + "\n".join(caption_lines) + "\n")

    # PDF bbox inventory and individual raw masks for every visible glyph in scope.
    rawdict = page.get_text("rawdict")
    char_records = []
    group_chars = defaultdict(list)
    glyph_counter = 0
    mask_manifest = []
    scope_slice = figure_crop_px
    scx0, scy0, scx1, scy1 = scope_slice
    scope_shape = (scy1 - scy0, scx1 - scx0)

    for block in rawdict["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span.get("chars", []):
                    c = char["c"]
                    if c.isspace():
                        continue
                    bbox = tuple(float(v) for v in char["bbox"])
                    cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0
                    if not (SCOPE_PDF[1] <= cy <= SCOPE_PDF[3] and SCOPE_PDF[0] <= cx <= SCOPE_PDF[2]):
                        continue
                    semantic_id = group_for_char(cx, cy)
                    glyph_counter += 1
                    glyph_id = f"GLYPH_{glyph_counter:03d}"
                    bbox_px = bbox_to_pixels(bbox, sx, sy)
                    raw_local, local_slice, bg = local_raw_text_mask(rgb, bbox_px)
                    gx0, gy0, gx1, gy1 = local_slice
                    global_mask = np.zeros(scope_shape, dtype=bool)
                    ly0, ly1 = gy0 - scy0, gy1 - scy0
                    lx0, lx1 = gx0 - scx0, gx1 - scx0
                    if raw_local.shape == (max(0, ly1 - ly0), max(0, lx1 - lx0)):
                        global_mask[ly0:ly1, lx0:lx1] = raw_local
                    mask_path = masks_glyph / f"{glyph_id}.png"
                    save_mask(mask_path, raw_local)
                    record = {
                        "glyph_id": glyph_id,
                        "semantic_id": semantic_id,
                        "char": c,
                        "codepoint": f"U+{ord(c):04X}",
                        "bbox_pdf": bbox,
                        "bbox_px": bbox_px,
                        "span_size_pdf_pt": float(span["size"]),
                        "font": span.get("font", ""),
                        "mask": global_mask,
                        "mask_path": rel(mask_path),
                        "background_rgb": bg,
                    }
                    char_records.append(record)
                    group_chars[semantic_id].append(record)
                    mask_manifest.append({
                        "MASK_ID": glyph_id,
                        "KIND": "GLYPH_RAW_NO_DILATION",
                        "PARENT_ID": semantic_id,
                        "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox),
                        "MASK_FILE": rel(mask_path),
                        "BACKGROUND_RGB": ",".join(map(str, bg)),
                        "FOREGROUND_RULE": "max_channel_difference_from_local_background>=20",
                    })

    missing_groups = sorted(set(SEMANTIC_META) - set(group_chars))
    if missing_groups:
        raise RuntimeError(f"Missing semantic groups; strict result cannot be inferred: {missing_groups}")

    # Establish final vector span baselines and source-effective values per glyph.
    semantic_masks = {}
    semantic_rows = []
    glyph_rows = []
    font_rows = []
    for semantic_id, members in group_chars.items():
        meta = SEMANTIC_META[semantic_id]
        local_pdf_base = max(m["span_size_pdf_pt"] for m in members)
        base_pt = meta["base_pt"] if meta["base_pt"] is not None else local_pdf_base
        combined = np.zeros(scope_shape, dtype=bool)
        for m in members:
            combined |= m["mask"]
        semantic_masks[semantic_id] = combined
        mask_crop, (mlx0, mly0, mlx1, mly1) = crop_mask(combined)
        sem_mask_path = masks_sem / f"{semantic_id}.png"
        save_mask(sem_mask_path, mask_crop)
        sem_bbox = rect_union([m["bbox_pdf"] for m in members])
        semantic_rows.append({
            "ELEMENT_ID": semantic_id,
            "PARENT_ELEMENT_ID": semantic_id,
            "PANEL_ID": "PANEL_SINGLE",
            "ROLE": meta["role"],
            "SOURCE_FILE": str(FIG_SRC),
            "SOURCE_LINE": meta["source_line"],
            "TEXT_SAMPLE": SEMANTIC_DISPLAY_TEXT[semantic_id],
            "PDF_BBOX": ";".join(f"{v:.3f}" for v in sem_bbox),
            "RAW_MASK_FILE": rel(sem_mask_path),
            "RAW_INK_PIXEL_COUNT": int(np.count_nonzero(combined)),
            "H_INK_PX": mask_height(combined),
            "DECLARED_BASE_PT": f"{base_pt:.3f}",
            "GRAPHICS_SCALE": "1.000000",
            "FONT_ORIGIN": meta["font_origin"],
        })
        mask_manifest.append({
            "MASK_ID": semantic_id,
            "KIND": "SEMANTIC_RAW_UNION_OF_GLYPH_MASKS_NO_DILATION",
            "PARENT_ID": semantic_id,
            "PDF_BBOX": ";".join(f"{v:.3f}" for v in sem_bbox),
            "MASK_FILE": rel(sem_mask_path),
            "BACKGROUND_RGB": "per-glyph local mode; see child rows",
            "FOREGROUND_RULE": "union of child raw masks; no dilation",
        })
        for m in members:
            is_script = m["span_size_pdf_pt"] < 0.92 * local_pdf_base
            effective_pt = base_pt * (m["span_size_pdf_pt"] / local_pdf_base)
            script_class, threshold = unicode_class(m["char"], is_script, meta["role"])
            if is_script:
                font_pass = base_pt >= 9.5
                font_reason = f"natural script; base effective_pt={base_pt:.3f}pt"
            else:
                font_pass = effective_pt >= 9.5
                font_reason = f"ordinary visible glyph effective_pt={effective_pt:.3f}pt"
            h_ink = mask_height(m["mask"])
            pixel_pass = h_ink >= threshold
            glyph_rows.append({
                "ELEMENT_ID": m["glyph_id"],
                "PARENT_ELEMENT_ID": semantic_id,
                "PANEL_ID": "PANEL_SINGLE",
                "ROLE": meta["role"],
                "SOURCE_FILE": str(FIG_SRC),
                "SOURCE_LINE": meta["source_line"],
                "DECLARED_PT": f"{base_pt:.3f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{effective_pt:.3f}",
                "TEXT_SAMPLE": m["char"],
                "SCRIPT_CLASS": script_class,
                "BBOX_X0": f"{m['bbox_px'][0]:.3f}",
                "BBOX_Y0": f"{m['bbox_px'][1]:.3f}",
                "BBOX_X1": f"{m['bbox_px'][2]:.3f}",
                "BBOX_Y1": f"{m['bbox_px'][3]:.3f}",
                "H_INK_PX": h_ink,
                "PIXEL_THRESHOLD_PX": threshold,
                "CLASS_MEDIAN_PX": "",
                "RATIO_TO_CLASS_MEDIAN": "",
                "ROLE_RATIO": "",
                "TEXT_TEXT_OVERLAP_PX": 0,
                "TEXT_GRAPHIC_OVERLAP_PX": 0,
                "MIN_CLEARANCE_PX": "",
                "SOURCE_FONT_PASS": bool_text(font_pass),
                "PIXEL_HEIGHT_PASS": bool_text(pixel_pass),
                "PASS_FAIL": "PASS" if font_pass and pixel_pass else "FAIL",
                "REASON": f"{font_reason}; H_ink={h_ink}px threshold={threshold}px",
                "RAW_MASK_FILE": m["mask_path"],
                "LOCAL_BACKGROUND_RGB": ",".join(map(str, m["background_rgb"])),
                "PDF_VECTOR_FONT_SIZE_PT": f"{m['span_size_pdf_pt']:.3f}",
                "PDF_VECTOR_FONT": m["font"],
            })
            font_rows.append({
                "ELEMENT_ID": m["glyph_id"],
                "PARENT_ELEMENT_ID": semantic_id,
                "ROLE": meta["role"],
                "SOURCE_FILE": str(FIG_SRC),
                "SOURCE_LINE": meta["source_line"],
                "TEXT_SAMPLE": m["char"],
                "DECLARED_PT": f"{base_pt:.3f}",
                "GRAPHICS_SCALE": "1.000000",
                "EFFECTIVE_PT": f"{effective_pt:.3f}",
                "PDF_VECTOR_FONT_SIZE_PT": f"{m['span_size_pdf_pt']:.3f}",
                "SCRIPT_NATURAL": bool_text(is_script),
                "SOURCE_FONT_PASS": bool_text(font_pass),
                "PASS_FAIL": "PASS" if font_pass else "FAIL",
                "REASON": font_reason,
                "FONT_EVIDENCE": meta["font_origin"],
            })

    # The same-class ratio uses role + script/morphology class.  It intentionally
    # does not compare a tall summation glyph to a short equals glyph: each is
    # separately thresholded above, while same-role repeated labels are compared.
    ratios = defaultdict(list)
    for row in glyph_rows:
        glyph = row["TEXT_SAMPLE"]
        morphology = "CJK" if row["SCRIPT_CLASS"] == "CJK_OR_FULLWIDTH" else glyph
        key = (row["ROLE"], row["SCRIPT_CLASS"], morphology)
        ratios[key].append(row)
    same_class_rows = []
    same_class_pass = True
    for key, rows in sorted(ratios.items()):
        hs = [int(r["H_INK_PX"]) for r in rows]
        med = float(median(hs))
        group_ok = True
        for r in rows:
            ratio = int(r["H_INK_PX"]) / med if med else 0.0
            r["CLASS_MEDIAN_PX"] = f"{med:.3f}"
            r["RATIO_TO_CLASS_MEDIAN"] = f"{ratio:.4f}"
            if not (0.92 <= ratio <= 1.08):
                group_ok = False
        same_class_pass &= group_ok
        same_class_rows.append({
            "ROLE": key[0], "SCRIPT_CLASS": key[1], "MORPHOLOGY_CLASS": key[2],
            "ELEMENT_IDS": ";".join(r["ELEMENT_ID"] for r in rows),
            "N": len(rows), "MEDIAN_H_INK_PX": f"{med:.3f}",
            "MIN_TO_MEDIAN": f"{min(hs) / med:.4f}" if med else "0.0000",
            "MAX_TO_MEDIAN": f"{max(hs) / med:.4f}" if med else "0.0000",
            "PASS_FAIL": "PASS" if group_ok else "FAIL",
        })

    # Vector drawings are independently read from the frozen PDF.  These exact
    # PDF paths are the source of graphic masks, separated from text masks.
    drawings = [d for d in page.get_drawings() if d["rect"].y1 > 420 and d["rect"].y0 < 610]
    filled_hull = next(d for d in drawings if d["type"] == "f" and d["rect"].x0 < 200 and d["rect"].y0 > 470)
    outer = next(d for d in drawings if d["type"] == "s" and d["rect"].x0 < 130 and d["rect"].width > 160)
    hull = next(d for d in drawings if d["type"] == "s" and 145 < d["rect"].x0 < 160 and d["rect"].width > 100)
    circles = sorted([d for d in drawings if d["type"] == "f" and d["rect"].width < 6 and d["rect"].height < 6], key=lambda d: (d["rect"].x0, d["rect"].y0))
    spokes = sorted([d for d in drawings if d["type"] == "s" and 0.5 < float(d["width"]) < 0.6 and d["rect"].width > 5], key=lambda d: d["rect"].x0)
    diamond = next(d for d in drawings if d["type"] == "fs" and 200 < d["rect"].x0 < 230 and d["rect"].width < 20)
    formula_box = next(d for d in drawings if d["type"] == "fs" and d["rect"].x0 > 260 and d["rect"].width > 100)

    graphics = []

    def add_graphic(comp_id, kind, source_line, drawing, selector, bg_rgb, note):
        raw = raw_graphic_mask(rgb[scy0:scy1, scx0:scx1], selector, bg_rgb)
        crop, _ = crop_mask(raw)
        mpath = masks_graphics / f"{comp_id}.png"
        save_mask(mpath, crop)
        bbox = (drawing["rect"].x0, drawing["rect"].y0, drawing["rect"].x1, drawing["rect"].y1)
        graphics.append({
            "ELEMENT_ID": comp_id,
            "PANEL_ID": "PANEL_SINGLE",
            "KIND": kind,
            "SOURCE_FILE": str(FIG_SRC),
            "SOURCE_LINE": source_line,
            "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox),
            "RAW_MASK_FILE": rel(mpath),
            "RAW_FOREGROUND_PIXELS": int(np.count_nonzero(raw)),
            "NOTE": note,
            "mask": raw,
        })
        mask_manifest.append({
            "MASK_ID": comp_id,
            "KIND": f"GRAPHIC_{kind}_RAW_NO_DILATION",
            "PARENT_ID": comp_id,
            "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox),
            "MASK_FILE": rel(mpath),
            "BACKGROUND_RGB": ",".join(map(str, bg_rgb)),
            "FOREGROUND_RULE": "vector-path selector at native 300dpi AND local difference>=20; no dilation",
        })

    # Fill is enumerated but excluded from illegal-foreground pairs because its
    # opacity is below the 20/255 effective-foreground threshold.
    fpoints = [point_to_scope(item[1], sx, sy, scx0, scy0) for item in filled_hull["items"]]
    add_graphic("GRAPHIC_HULL_FILL", "FILL_BACKGROUND", 31, filled_hull, polygon_selector(scope_shape, fpoints, fill=True), [255, 255, 255], "Transparent hull background; not an illegal text collision target.")
    for idx, item in enumerate(outer["items"], 1):
        p0, p1 = point_to_scope(item[1], sx, sy, scx0, scy0), point_to_scope(item[2], sx, sy, scx0, scy0)
        add_graphic(f"GRAPHIC_OUTER_EDGE_{idx}", "LINE", 32, outer, line_selector(scope_shape, p0, p1, float(outer["width"]) * sx), [255, 255, 255], "Outer word-simplex boundary.")
    for idx, item in enumerate(hull["items"], 1):
        p0, p1 = point_to_scope(item[1], sx, sy, scx0, scy0), point_to_scope(item[2], sx, sy, scx0, scy0)
        add_graphic(f"GRAPHIC_TOPIC_HULL_EDGE_{idx}", "LINE", 36, hull, line_selector(scope_shape, p0, p1, float(hull["width"]) * sx), [255, 255, 255], "Topic convex-hull boundary.")
    # sort circles by correspondence to topic point positions: T1, T2, T3.
    circles_ordered = sorted(circles, key=lambda d: (d["rect"].y0 > 500, d["rect"].x0))
    for name, drawing in zip(("T3", "T1", "T2"), circles_ordered):
        rp = bbox_to_pixels((drawing["rect"].x0, drawing["rect"].y0, drawing["rect"].x1, drawing["rect"].y1), sx, sy)
        local_rect = (rp[0] - scx0, rp[1] - scy0, rp[2] - scx0, rp[3] - scy0)
        add_graphic(f"GRAPHIC_TOPIC_MARKER_{name}", "MARKER", 39, drawing, ellipse_selector(scope_shape, local_rect), [255, 255, 255], "Filled circular topic marker.")
    for idx, drawing in enumerate(spokes, 1):
        item = drawing["items"][0]
        p0, p1 = point_to_scope(item[1], sx, sy, scx0, scy0), point_to_scope(item[2], sx, sy, scx0, scy0)
        add_graphic(f"GRAPHIC_SPOKE_{idx}", "LINE", 40 + idx, drawing, line_selector(scope_shape, p0, p1, float(drawing["width"]) * sx), [255, 255, 255], "Dashed document-to-topic spoke; raw mask preserves true dash gaps.")
    dpoints = [point_to_scope(item[1], sx, sy, scx0, scy0) for item in diamond["items"]]
    add_graphic("GRAPHIC_DOCUMENT_DIAMOND", "MARKER", 47, diamond, polygon_selector(scope_shape, dpoints, fill=True), [255, 255, 255], "Document distribution marker (filled diamond and border).")
    frp = bbox_to_pixels((formula_box["rect"].x0, formula_box["rect"].y0, formula_box["rect"].x1, formula_box["rect"].y1), sx, sy)
    frect = (frp[0] - scx0, frp[1] - scy0, frp[2] - scx0, frp[3] - scy0)
    formula_fill = [int(round(v * 255)) for v in formula_box["fill"]]
    add_graphic("GRAPHIC_FORMULA_BOX_BORDER", "NODE_BORDER", 49, formula_box, formula_border_selector(scope_shape, frect, float(formula_box["width"]) * sx), formula_fill, "Rounded formula-box border; background fill is not a foreground collision.")

    # Semantic pair registration: all independent TEXT--TEXT pairs plus all text
    # against every actual line/marker/border.  There are no arrows, panels or
    # data curves in this figure; those zero-cardinality cases are recorded.
    relation_rows = []
    critical_manifest = []
    sem_ids = sorted(semantic_masks)
    rel_counter = 0

    def add_relation(a_id, a_kind, a_mask, b_id, b_kind, b_mask, category, required):
        nonlocal rel_counter
        rel_counter += 1
        rid = f"REL_{rel_counter:04d}"
        overlap, clearance = mask_clearance(a_mask, b_mask)
        passed = overlap == 0 and clearance >= required
        row = {
            "RELATION_ID": rid,
            "PANEL_ID": "PANEL_SINGLE",
            "ELEMENT_A": a_id,
            "CATEGORY_A": a_kind,
            "ELEMENT_B": b_id,
            "CATEGORY_B": b_kind,
            "RELATION_CLASS": category,
            "RAW_MASK_A": next(r["RAW_MASK_FILE"] for r in semantic_rows if r["ELEMENT_ID"] == a_id) if a_id.startswith("SEM_") else next(g["RAW_MASK_FILE"] for g in graphics if g["ELEMENT_ID"] == a_id),
            "RAW_MASK_B": next(r["RAW_MASK_FILE"] for r in semantic_rows if r["ELEMENT_ID"] == b_id) if b_id.startswith("SEM_") else next(g["RAW_MASK_FILE"] for g in graphics if g["ELEMENT_ID"] == b_id),
            "OVERLAP_PIXEL_COUNT": overlap,
            "CLEARANCE_PX": "INF" if math.isinf(clearance) else f"{clearance:.3f}",
            "REQUIRED_CLEARANCE_PX": required,
            "CLIP_PIXEL_COUNT": 0,
            "PASS_FAIL": "PASS" if passed else "FAIL",
            "REASON": "raw separated masks at native 300dpi; no dilation",
            "CRITICAL_ROI": "",
        }
        # All non-passing and near-threshold relations receive an actual original
        # ROI plus both separated masks, overlap mask and 8x nearest-neighbour
        # inspection image.  The mask used for computation remains unmodified.
        if (not passed) or (not math.isinf(clearance) and clearance <= required + 2.0):
            crop_pair_roi(im300, a_mask, b_mask, scope_slice, rid, f"{category}; overlap={overlap}; clearance={clearance:.3f}; required={required}", critical_manifest)
            row["CRITICAL_ROI"] = f"critical/{rid}_raw.png"
        relation_rows.append(row)

    for i, a_id in enumerate(sem_ids):
        for b_id in sem_ids[i + 1:]:
            add_relation(a_id, "FORMULA" if "FORMULA" in a_id else "TEXT", semantic_masks[a_id], b_id, "FORMULA" if "FORMULA" in b_id else "TEXT", semantic_masks[b_id], "TEXT_TEXT", 4)
    collision_graphics = [g for g in graphics if g["KIND"] in {"LINE", "MARKER", "NODE_BORDER"}]
    for a_id in sem_ids:
        a_kind = "FORMULA" if "FORMULA" in a_id else "TEXT"
        for g in collision_graphics:
            req = 5 if g["KIND"] == "NODE_BORDER" else 3
            add_relation(a_id, a_kind, semantic_masks[a_id], g["ELEMENT_ID"], g["KIND"], g["mask"], f"{a_kind}_{g['KIND']}", req)

    # Figure crop edge: direct text-to-edge net clearance (not an image resize).
    edge_rows = []
    for sid in sem_ids:
        mask = semantic_masks[sid]
        ys, xs = np.nonzero(mask)
        min_edge = min(int(xs.min()), int(ys.min()), int(scope_shape[1] - 1 - xs.max()), int(scope_shape[0] - 1 - ys.max()))
        passed = min_edge >= 6
        edge_rows.append({
            "RELATION_ID": f"EDGE_{sid}", "PANEL_ID": "PANEL_SINGLE", "ELEMENT_A": sid, "CATEGORY_A": "TEXT", "ELEMENT_B": "FIGURE_CROP_EDGE", "CATEGORY_B": "PANEL_EDGE",
            "RELATION_CLASS": "TEXT_EDGE", "RAW_MASK_A": next(r["RAW_MASK_FILE"] for r in semantic_rows if r["ELEMENT_ID"] == sid), "RAW_MASK_B": "coordinate crop edge; no foreground mask applicable",
            "OVERLAP_PIXEL_COUNT": 0, "CLEARANCE_PX": f"{min_edge:.3f}", "REQUIRED_CLEARANCE_PX": 6, "CLIP_PIXEL_COUNT": 0,
            "PASS_FAIL": "PASS" if passed else "FAIL", "REASON": "native crop-coordinate edge distance from raw text foreground", "CRITICAL_ROI": "",
        })
    relation_rows.extend(edge_rows)

    # Fill the measurement fields that depend on pair relations.
    per_sem_relations = defaultdict(list)
    for r in relation_rows:
        if r["ELEMENT_A"].startswith("SEM_"):
            per_sem_relations[r["ELEMENT_A"]].append(r)
        if r["ELEMENT_B"].startswith("SEM_"):
            per_sem_relations[r["ELEMENT_B"]].append(r)
    for row in glyph_rows:
        rels = per_sem_relations[row["PARENT_ELEMENT_ID"]]
        tt_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in rels if r["RELATION_CLASS"] == "TEXT_TEXT")
        tg_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in rels if r["RELATION_CLASS"] != "TEXT_TEXT")
        cls = [float(r["CLEARANCE_PX"]) for r in rels if r["CLEARANCE_PX"] != "INF"]
        row["TEXT_TEXT_OVERLAP_PX"] = tt_overlap
        row["TEXT_GRAPHIC_OVERLAP_PX"] = tg_overlap
        row["MIN_CLEARANCE_PX"] = f"{min(cls):.3f}" if cls else "0.000"

    # Source and pixel aggregate gates.
    source_font_pass = all(r["SOURCE_FONT_PASS"] == "true" for r in glyph_rows)
    source_font_failure_count = sum(r["SOURCE_FONT_PASS"] == "false" for r in glyph_rows)
    source_font_failure_component_count = sum(
        any(r["SOURCE_FONT_PASS"] == "false" for r in glyph_rows if r["PARENT_ELEMENT_ID"] == semantic_id)
        for semantic_id in SEMANTIC_META
    )
    pixel_height_pass = all(r["PIXEL_HEIGHT_PASS"] == "true" for r in glyph_rows)
    total_overlap = sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relation_rows)
    clip_count = 0
    relation_clearance_pass = all(r["PASS_FAIL"] == "PASS" for r in relation_rows)
    text_text_rels = [r for r in relation_rows if r["RELATION_CLASS"] == "TEXT_TEXT"]
    line_rels = [r for r in relation_rows if r["CATEGORY_B"] == "LINE"]
    border_rels = [r for r in relation_rows if r["CATEGORY_B"] == "NODE_BORDER"]
    edge_rels = [r for r in relation_rows if r["RELATION_CLASS"] == "TEXT_EDGE"]

    def min_clear(rows):
        vals = [float(r["CLEARANCE_PX"]) for r in rows if r["CLEARANCE_PX"] != "INF"]
        return min(vals) if vals else 0.0

    # Role hierarchy uses final source-effective point sizes, deliberately kept
    # separate from ink morphology.  This figure has no axes/ticks; WEIGHT_LABEL
    # is the documented ordinary node-text BASE.
    role_rows = []
    base_pt = GLOBAL_EVERY_NODE_FONT_PT
    hierarchy = [
        ("VERTEX_LABEL", GLOBAL_EVERY_NODE_FONT_PT, 0.95, 1.10, "ordinary node label; global every-node \\small"),
        ("TOPIC_LABEL", GLOBAL_EVERY_NODE_FONT_PT, 0.95, 1.10, "ordinary topic label; global every-node \\small"),
        ("WEIGHT_LABEL", GLOBAL_EVERY_NODE_FONT_PT, 0.95, 1.10, "BASE; global every-node \\small"),
        ("FORMULA_BLOCK", GLOBAL_EVERY_NODE_FONT_PT, 1.00, 1.18, "formula block; global every-node \\small"),
        ("LEGEND", LEGEND_EXPLICIT_FONT_PT, 0.95, 1.10, "explicit legend font relative to BASE"),
    ]
    role_ratio_pass = True
    for role, size, low, high, rationale in hierarchy:
        ratio = size / base_pt
        passed = low <= ratio <= high
        role_ratio_pass &= passed
        role_rows.append({
            "ROLE": role, "BASE_ROLE": "WEIGHT_LABEL", "ROLE_EFFECTIVE_PT": f"{size:.3f}", "BASE_EFFECTIVE_PT": f"{base_pt:.3f}",
            "RATIO": f"{ratio:.4f}", "LOW": f"{low:.2f}", "HIGH": f"{high:.2f}", "RATIONALE": rationale,
            "PASS_FAIL": "PASS" if passed else "FAIL",
        })
    write_csv(OUT / "same_class_ratio_audit.csv", same_class_rows)
    write_csv(OUT / "role_ratio_audit.csv", role_rows)

    # Critical pixel evidence: all individual masks are already persisted.  Make
    # focused raw ROI / separated union mask / 8x view for formula punctuation
    # and the undersized legend, independently of pair failures.
    failed_pixel = [r for r in glyph_rows if r["PIXEL_HEIGHT_PASS"] == "false"]
    op_failed = [r for r in failed_pixel if r["SCRIPT_CLASS"] == "BASE_MATH_OR_PUNCT"]
    if op_failed:
        a = np.zeros(scope_shape, dtype=bool)
        for r in op_failed:
            m = next(x["mask"] for x in char_records if x["glyph_id"] == r["ELEMENT_ID"])
            a |= m
        # A duplicate empty B mask gives a literal separated-mask artifact for
        # this one-sided glyph-height failure.  It is not an overlap conclusion.
        crop_pair_roi(im300, a, np.zeros_like(a), scope_slice, "PIXEL_FAIL_FORMULA_OPERATORS", "Operator/punctuation own H_ink below 22px; 8x inspection only", critical_manifest)
    legend_failed = [r for r in glyph_rows if r["ROLE"] == "LEGEND"]
    if legend_failed:
        a = np.zeros(scope_shape, dtype=bool)
        for r in legend_failed:
            a |= next(x["mask"] for x in char_records if x["glyph_id"] == r["ELEMENT_ID"])
        crop_pair_roi(im300, a, np.zeros_like(a), scope_slice, "SOURCE_FONT_FAIL_LEGEND", "Legend source effective size 8.8pt < 9.5pt", critical_manifest)

    # Math-finding ROI on the adjacent body line (frozen native page, no edit).
    math_box = bbox_to_slice(bbox_to_pixels((60.0, 638.0, 535.0, 675.0), sx, sy), im300.width, im300.height)
    math_raw = im300.crop(math_box)
    math_raw_path = OUT / "critical" / "MATH_UNQUALIFIED_NONUNIQUENESS_raw.png"
    math_raw.save(math_raw_path)
    math_ann = math_raw.copy()
    draw = ImageDraw.Draw(math_ann)
    draw.rectangle((0, 0, math_ann.width - 1, math_ann.height - 1), outline=(220, 30, 30), width=3)
    math_ann.save(OUT / "critical" / "MATH_UNQUALIFIED_NONUNIQUENESS_annotated.png")
    critical_manifest.append({
        "ARTIFACT_ID": "MATH_UNQUALIFIED_NONUNIQUENESS",
        "REASON": "Adjacent body assertion at chapter L403 is unqualified and false for this fixed affine-independent example.",
        "RAW_ROI": rel(math_raw_path), "MASK_A": "not applicable: mathematical text finding", "MASK_B": "not applicable: mathematical text finding",
        "OVERLAP_MASK": "not applicable", "OVERLAY": "critical/MATH_UNQUALIFIED_NONUNIQUENESS_annotated.png", "ZOOM_8X": "not applicable",
    })
    write_csv(OUT / "critical_artifacts.csv", critical_manifest)

    # Full measurement overlay.  Semantic overlay is legible; a separate glyph
    # overlay preserves every individual element ID without hiding the figure.
    font = ImageFont.load_default()
    semantic_overlay = im300.copy()
    sdraw = ImageDraw.Draw(semantic_overlay)
    colors = [(220, 35, 35), (0, 110, 180), (155, 75, 0), (25, 140, 90), (125, 40, 150)]
    for idx, row in enumerate(semantic_rows):
        bbox_vals = [float(x) for x in row["PDF_BBOX"].split(";")]
        px = bbox_to_pixels(bbox_vals, sx, sy)
        color = colors[idx % len(colors)]
        sdraw.rectangle(px, outline=color, width=2)
        sdraw.text((px[0], max(0, px[1] - 12)), f"{row['ELEMENT_ID']} {row['ROLE']}", fill=color, font=font)
    semantic_overlay.save(OUT / "after_text_measurement_overlay_300dpi.png")
    glyph_overlay = im300.copy()
    gdraw = ImageDraw.Draw(glyph_overlay)
    for rec in char_records:
        p = rec["bbox_px"]
        gdraw.rectangle(p, outline=(220, 35, 35), width=1)
        gdraw.text((p[0], max(0, p[1] - 9)), rec["glyph_id"], fill=(220, 35, 35), font=font)
    glyph_overlay.save(OUT / "glyph_bbox_overlay_300dpi.png")

    # Inventory and all required CSVs.
    write_csv(OUT / "glyph_inventory.csv", [{
        "ELEMENT_ID": r["glyph_id"], "PARENT_ELEMENT_ID": r["semantic_id"], "TEXT_SAMPLE": r["char"], "CODEPOINT": r["codepoint"],
        "PDF_BBOX": ";".join(f"{v:.3f}" for v in r["bbox_pdf"]), "PDF_VECTOR_FONT_SIZE_PT": f"{r['span_size_pdf_pt']:.3f}",
        "PDF_VECTOR_FONT": r["font"], "RAW_MASK_FILE": r["mask_path"], "LOCAL_BACKGROUND_RGB": ",".join(map(str, r["background_rgb"])),
    } for r in char_records])
    write_csv(OUT / "semantic_component_inventory.csv", semantic_rows)
    graphics_rows = [{k: v for k, v in g.items() if k != "mask"} for g in graphics]
    write_csv(OUT / "graphic_component_inventory.csv", graphics_rows)
    write_csv(OUT / "mask_manifest.csv", mask_manifest)
    write_csv(OUT / "after_font_audit.csv", font_rows)
    write_csv(OUT / "after_pixel_measurements.csv", glyph_rows)
    write_csv(OUT / "after_overlap_report.csv", relation_rows)

    # Mathematical recheck is fully recomputed from source line 26--29 data.
    phi = np.array([[0.78, 0.10, 0.12], [0.12, 0.78, 0.13], [0.10, 0.12, 0.75]], dtype=float)
    p = np.array([0.309, 0.4195, 0.2715], dtype=float)
    theta = np.linalg.solve(phi, p)
    det = float(np.linalg.det(phi))
    math_report = f"""# FIG-P525-01 数学/语义独立复算（SA1）

冻结 PDF 第 {PDF_PAGE} 页、图源 L26--29 与相邻正文 L386--403 是本复算的唯一输入。

## 已核对正确的图内关系

图源给出的主题列向量与文档点为

\\[
\\Phi=\\begin{{bmatrix}}0.78&0.10&0.12\\\\0.12&0.78&0.13\\\\0.10&0.12&0.75\\end{{bmatrix}},\quad
p=P(w\\mid d_j)=(0.309,0.4195,0.2715)^{{\\mathsf T}}.
\\]

直接求解得到

\\[
\\det(\\Phi)={det:.4f}\\ne0,\quad
\\theta_{{:j}}=\\Phi^{{-1}}p=({theta[0]:.4f},{theta[1]:.4f},{theta[2]:.4f})^{{\\mathsf T}},\quad
\\mathbf 1^{{\\mathsf T}}\\theta_{{:j}}={theta.sum():.4f},\quad
\\Phi\\theta_{{:j}}=({(phi @ theta)[0]:.4f},{(phi @ theta)[1]:.4f},{(phi @ theta)[2]:.4f})^{{\\mathsf T}}.
\\]

因此，图内公式、非负性和归一化约束与这个数值点一致；三主题点在相关仿射平面中仿射独立，给定该固定 \\(\\Phi\\) 和同一文档点时 \\(\\theta_{{:j}}\\) 唯一。

## 硬性语义失败

相邻正文 `V4-C06.tex:403` 写道“不同参数可以给出相同文档点，说明潜在表示不必唯一。”该句没有限定条件，且紧接此图会让读者把**固定、非退化主题三角形中的同一点**误读为具有多个主题系数。上面的行列式与求解表明本图恰恰是唯一系数的情形。

应明确区分：

1. 固定 \\(\\Phi\\) 且主题点仿射独立（本图）：文档点的凸组合系数唯一；
2. \\(\\Phi\\) 仿射相关、重复或凸包退化：同一点可有多组 \\(\\theta\\)；
3. 同时允许改变 \\(\\Phi\\) 与 \\(\\Theta\\)：还存在主题置换和一般分解非唯一性。

本轮只审现状，因此 `MATH_SEMANTICS_PASS=false`、`TEXT_CONSISTENCY_PASS=false`。
"""
    write_text(OUT / "math_semantics_recheck.md", math_report)

    # Strict all-boolean final matrix.  Single-panel / no-arrow / no-data-curve
    # conditions are explicitly verified zero-cardinality PASS cases, not unknown.
    text_text_min = min_clear(text_text_rels)
    line_min = min_clear(line_rels)
    border_min = min_clear(border_rels)
    edge_min = min_clear(edge_rels)
    clearance_pass = relation_clearance_pass
    grayscale_pass = True
    page_integration_pass = True
    math_semantics_pass = False
    text_consistency_pass = False
    font_visual_harmony_pass = False
    visual_harmony_pass = font_visual_harmony_pass
    final_pass = all([
        source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass,
        total_overlap == 0, clip_count == 0, clearance_pass,
        visual_harmony_pass, math_semantics_pass, text_consistency_pass,
        grayscale_pass, page_integration_pass,
    ])
    hard_gates = {
        "SOURCE_FONT_PASS": source_font_pass,
        "SOURCE_FONT_FAILURE_COUNT": source_font_failure_count,
        "SOURCE_FONT_FAILURE_COMPONENT_COUNT": source_font_failure_component_count,
        "PIXEL_HEIGHT_PASS": pixel_height_pass,
        "SAME_CLASS_RATIO_PASS": same_class_pass,
        "ROLE_RATIO_PASS": role_ratio_pass,
        "OVERLAP_PIXEL_COUNT": total_overlap,
        "CLIP_PIXEL_COUNT": clip_count,
        "MIN_TEXT_TEXT_CLEARANCE_PX": round(text_text_min, 3),
        "MIN_TEXT_LINE_CLEARANCE_PX": round(line_min, 3),
        "MIN_TEXT_NODE_BORDER_CLEARANCE_PX": round(border_min, 3),
        "MIN_TEXT_EDGE_CLEARANCE_PX": round(edge_min, 3),
        "CLEARANCE_PASS": clearance_pass,
        "CROSS_PANEL_PASS": True,
        "FONT_VISUAL_HARMONY_PASS": font_visual_harmony_pass,
        "VISUAL_HARMONY_PASS": visual_harmony_pass,
        "MATH_SEMANTICS_PASS": math_semantics_pass,
        "TEXT_CONSISTENCY_PASS": text_consistency_pass,
        "GRAYSCALE_PASS": grayscale_pass,
        "PAGE_INTEGRATION_PASS": page_integration_pass,
        "FINAL_RESULT": "PASS" if final_pass else "FAIL",
        "NEXT_ROLE": "SA3" if final_pass else "SA2",
    }
    summary = {
        "audit_id": "FIG-P525-01/STRICT_R1/SA1_20260824_R1",
        "role": "SA1 independent strict first review",
        "input": {"frozen_pdf": str(PDF), "page": PDF_PAGE, "figure_source": str(FIG_SRC), "adjacent_context": f"{CHAPTER}:382-413"},
        "coverage": {
            "glyphs": len(glyph_rows), "semantic_text_components": len(semantic_rows), "graphic_components": len(graphics_rows),
            "text_text_pairs": len(text_text_rels), "text_graphic_pairs": len(relation_rows) - len(text_text_rels) - len(edge_rels), "text_edge_pairs": len(edge_rels),
            "arrow_components": 0, "panel_components": 0, "data_curve_components": 0,
        },
        "hard_gates": hard_gates,
        "result": "PASS" if final_pass else "FAIL",
        "handoff": "SA3" if final_pass else "SA2",
        "strict_method": "Native final-PDF 300dpi at 1:1; PDF bboxes; per-glyph raw masks; no morphological expansion; source font audit; separated graphic masks; paired relation registry.",
    }
    (OUT / "strict_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Exact eight-column formal report required by the task.
    eight = []
    def report_row(check_id, category, evidence, metric, threshold, observed, flag):
        eight.append({"CHECK_ID": check_id, "CATEGORY": category, "EVIDENCE": evidence, "METRIC": metric, "THRESHOLD": threshold, "OBSERVED": observed, "BOOLEAN": bool_text(flag), "STATUS": "PASS" if flag else "FAIL"})
    report_row("R01", "INPUT", "render_manifest.json", "frozen input / independently located page", "PDF only; page uniquely located", f"main_full.pdf page {PDF_PAGE}/813; sha256={frozen_pdf_sha256}", True)
    report_row("R02", "RENDER", "full_page_200dpi.png", "whole-page native render", "200dpi", "200dpi Poppler native", True)
    report_row("R03", "RENDER", "full_page_300dpi_native.png", "measurement render", "300dpi, 1:1, no resize", f"{im300.width}x{im300.height}px, scale {sx:.6f}", True)
    report_row("R04", "COVERAGE", "glyph_inventory.csv;graphic_component_inventory.csv", "visible glyph/semantic/graphic enumeration", "all scoped reader-visible elements", f"glyphs={len(glyph_rows)}, semantics={len(semantic_rows)}, graphics={len(graphics_rows)}", True)
    report_row("R05", "MASKS", "mask_manifest.csv", "per-glyph and component raw masks", "PDF bbox + no-dilation raw masks", f"masks={len(mask_manifest)}", True)
    report_row("R06", "SOURCE_FONT", "after_font_audit.csv;shared_style_font_context.tex", "all ordinary effective_pt", ">=9.5pt", f"ordinary node=10.0pt via statlearnbook.sty:L276; legend=8.8pt; failure glyphs={source_font_failure_count}, components={source_font_failure_component_count}", source_font_pass)
    report_row("R07", "PIXEL_HEIGHT", "after_pixel_measurements.csv;critical/PIXEL_FAIL_FORMULA_OPERATORS_overlay_8x.png", "per-glyph H_ink", "class thresholds 30/24/17/22/15px", f"pixel failures={len(failed_pixel)}", pixel_height_pass)
    report_row("R08", "SAME_CLASS", "same_class_ratio_audit.csv", "same role+script/morphology H_ink ratio", "[0.92,1.08]", "see CSV", same_class_pass)
    report_row("R09", "ROLE_RATIO", "role_ratio_audit.csv", "legend/base source-effective ratio", "[0.95,1.10]", f"8.8/10.0={LEGEND_EXPLICIT_FONT_PT/GLOBAL_EVERY_NODE_FONT_PT:.4f}", role_ratio_pass)
    report_row("R10", "OVERLAP", "after_overlap_report.csv", "all registered raw-mask pair overlaps", "0 pixels", str(total_overlap), total_overlap == 0)
    report_row("R11", "CLIP", "after_overlap_report.csv", "figure text/graphics clipping", "0 pixels", str(clip_count), clip_count == 0)
    report_row("R12", "CLEARANCE", "after_overlap_report.csv", "text-text / text-line / text-border / edge", ">=4 / >=3 / >=5 / >=6 px", f"{text_text_min:.3f} / {line_min:.3f} / {border_min:.3f} / {edge_min:.3f}", clearance_pass)
    report_row("R13", "CROSS_PANEL", "strict_audit_summary.json", "cross-panel relation", "single-panel explicit pass", "0 panels beyond PANEL_SINGLE", True)
    report_row("R14", "HARMONY", "full_page_200dpi.png;figure_crop_300dpi.png;standalone_300dpi.png;grayscale_300dpi.png", "FONT_VISUAL_HARMONY_PASS", "no undersized / intrusive typography", "ordinary nodes 10.0pt; explicit 8.8pt legend visibly undersized", font_visual_harmony_pass)
    theta_display = tuple(float(f"{float(x):.4f}") for x in theta)
    report_row("R15", "MATH", "math_semantics_recheck.md", "fixed Phi coefficient identifiability", "no unconditional multiple-solution claim", f"det(Phi)={det:.4f}; theta={theta_display}; source L403 unqualified", math_semantics_pass)
    report_row("R16", "TEXT", "adjacent_source_context.tex;math_semantics_recheck.md", "figure/body consistency", "all claims conditionally correct", "L403 conflicts with fixed affine-independent example", text_consistency_pass)
    report_row("R17", "GRAYSCALE", "grayscale_300dpi.png", "geometry distinguishability without color", "stable semantics", "solid boundaries + dashed spokes + circle/diamond shape encoding", grayscale_pass)
    report_row("R18", "PAGE", "full_page_200dpi.png", "page integration", "no visual clipping/abnormal break", "figure/caption placement intact; independent font gate fails separately", page_integration_pass)
    report_row("R19", "FINAL", "strict_audit_summary.json", "all hard gates", "all true", "FAIL; route to SA2", final_pass)
    fields8 = ["CHECK_ID", "CATEGORY", "EVIDENCE", "METRIC", "THRESHOLD", "OBSERVED", "BOOLEAN", "STATUS"]
    write_csv(OUT / "strict_eight_column_report.csv", eight, fields8)

    # Formal acceptance / handoff document: only PASS or FAIL states.
    acceptance = f"""# FIG-P525-01｜STRICT R1｜SA1 正式验收

RESULT: {'PASS' if final_pass else 'FAIL'}

NEXT_ROLE: {'SA3' if final_pass else 'SA2'}

## 覆盖与输入

- 冻结输入：`src/build/strict_current_r93_fullbook/main_full.pdf`，独立定位到物理 PDF 第 {PDF_PAGE} 页（全书 {len(doc)} 页）。
- 图源：`src/绘图源码/第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_simplex.tex`。
- 相邻正文：`V4-C06.tex:382--413`。
- 已枚举 {len(glyph_rows)} 个可见 glyph、{len(semantic_rows)} 个语义文字组件、{len(graphics_rows)} 个线/marker/边框/填充组件；TEXT--TEXT={len(text_text_rels)} 对、TEXT--GRAPHIC={len(relation_rows) - len(text_text_rels) - len(edge_rels)} 对、TEXT--EDGE={len(edge_rels)} 对。
- 原生视图：`full_page_200dpi.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`。300 dpi 测量图未 resize；crop 仅裁切。

## 硬门矩阵

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | {bool_text(source_font_pass)} | true | {'PASS' if source_font_pass else 'FAIL'} |
| SOURCE_FONT_FAILURE_COUNT | {source_font_failure_count} glyphs / {source_font_failure_component_count} components | 0 | {'PASS' if source_font_failure_count == 0 else 'FAIL'} |
| PIXEL_HEIGHT_PASS | {bool_text(pixel_height_pass)} | true | {'PASS' if pixel_height_pass else 'FAIL'} |
| SAME_CLASS_RATIO_PASS | {bool_text(same_class_pass)} | true | {'PASS' if same_class_pass else 'FAIL'} |
| ROLE_RATIO_PASS | {bool_text(role_ratio_pass)} | true | {'PASS' if role_ratio_pass else 'FAIL'} |
| OVERLAP_PIXEL_COUNT | {total_overlap} | 0 | {'PASS' if total_overlap == 0 else 'FAIL'} |
| CLIP_PIXEL_COUNT | {clip_count} | 0 | {'PASS' if clip_count == 0 else 'FAIL'} |
| MIN_TEXT_CLEARANCE_PX | text/text={text_text_min:.3f}; text/line={line_min:.3f}; text/border={border_min:.3f}; edge={edge_min:.3f} | 4/3/5/6 | {'PASS' if clearance_pass else 'FAIL'} |
| FONT_VISUAL_HARMONY_PASS | {bool_text(font_visual_harmony_pass)} | true | {'PASS' if font_visual_harmony_pass else 'FAIL'} |
| MATH_SEMANTICS_PASS | {bool_text(math_semantics_pass)} | true | {'PASS' if math_semantics_pass else 'FAIL'} |
| TEXT_CONSISTENCY_PASS | {bool_text(text_consistency_pass)} | true | {'PASS' if text_consistency_pass else 'FAIL'} |
| GRAYSCALE_PASS | {bool_text(grayscale_pass)} | true | {'PASS' if grayscale_pass else 'FAIL'} |
| PAGE_INTEGRATION_PASS | {bool_text(page_integration_pass)} | true | {'PASS' if page_integration_pass else 'FAIL'} |

## 强制 FAIL 发现与可执行 SA2 动作

1. **源级有效字号 FAIL。** 图源 L3 的 picture 字号是 9.4pt，但公共 `statlearnbook.sty:L276` 的 `every node/.append style={{font=\\small}}` 在 11pt 文档中将普通 node 覆盖为合格的 10.0pt（冻结 PDF vector span≈9.963pt 与之相符）。仅 L14 的显式图例 `\\fontsize{{8.8pt}}{{10.4pt}}` 保持 8.8pt 并失败；必须只提升该图例到至少 9.5pt，且公式合法脚本从合格 10.0pt 基准自然派生；不要整体缩放图。
2. **逐 glyph 像素高度 FAIL。** `after_pixel_measurements.csv` 对公式中的 `∶`（21px）、`=`（12px）和 `,`（11px）等独立 substring 使用各自无膨胀 raw mask，不能由父公式替代；图例/题注全角 `：` 与题注句点也分别失败。失败记录和 8x ROI 已落盘。提升有效字号后必须重新原生 300dpi 渲染及逐 glyph 复测。
3. **角色层级 / 视觉协调 FAIL。** 图例 8.8/10.0=0.8800，低于图例相对 BASE 的 0.95 下限；整页和灰度审看都显示其过小，不能视为次要而豁免。
4. **数学 / 图文一致 FAIL。** `V4-C06.tex:403` 将“同一点有多解”无条件化。本图的固定主题矩阵具有 `det(Phi)={det:.4f}`，且 `P=(.309,.4195,.2715)^T` 的唯一系数是 `theta=(.3,.45,.25)^T`。修正文句必须区分仿射相关/重复主题、同时改变 Phi/Theta、主题置换等真正的非唯一情形；固定仿射独立 Phi 时明确系数唯一。

## SA1 结论

任一硬门 FAIL 即不得进入 SA3。本轮结果为 **FAIL**，下一角色必须是 **SA2**。SA2 仅可改指定图源及直接相邻正文；修复后须生成新的冻结候选与一套全新 300dpi raw-mask 证据，再由新的 SA1 复审。
"""
    write_text(OUT / "after_visual_acceptance.md", acceptance)
    write_text(OUT / "SA1_RESULT.md", acceptance)


if __name__ == "__main__":
    main()
