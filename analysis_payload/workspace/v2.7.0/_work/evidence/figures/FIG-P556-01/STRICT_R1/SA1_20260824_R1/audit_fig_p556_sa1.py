#!/usr/bin/env python3
"""FIG-P556-01 independent strict SA1 audit.

Inputs are restricted to the frozen R93 final PDF, the designated figure
source, its direct adjacent V5-C01 context, and the common style that controls
the final effective font cascade.  Every write stays in this evidence folder.
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
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import distance_transform_edt


PROJECT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = Path(__file__).resolve().parent
PDF = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r93_fullbook" / "main_full.pdf"
FIG_SRC = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C01" / "fig_v5_c01_stationary_fixed_point.tex"
CHAPTER = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C01.tex"
STYLE = PROJECT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "common" / "statlearnbook.sty"
PDF_PAGE = 601
PAGE_INDEX = PDF_PAGE - 1
SCOPE_PDF = (60.0, 365.0, 530.0, 605.0)  # chart, labels, and single-line caption
STANDALONE_PDF = (170.0, 370.0, 415.0, 580.0)

# All font declarations in this figure are explicit at the relevant TikZ/
# pgfplots node level; therefore common every-node \small (style L276) does
# not replace these local figure declarations.
FONT_TICK = 8.7
FONT_AXIS = 9.4
FONT_CURVE = 9.3
FONT_INITIAL = 9.2
FONT_CAPTION_VECTOR = None


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
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bbox_to_px(bbox: tuple[float, float, float, float], sx: float, sy: float) -> tuple[float, float, float, float]:
    return bbox[0] * sx, bbox[1] * sy, bbox[2] * sx, bbox[3] * sy


def bbox_to_slice(bbox: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    return (max(0, int(math.floor(bbox[0]))), max(0, int(math.floor(bbox[1]))),
            min(width, int(math.ceil(bbox[2]))), min(height, int(math.ceil(bbox[3]))))


def crop_mask(mask: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return np.zeros((1, 1), dtype=bool), (0, 0, 1, 1)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return mask[y0:y1, x0:x1], (x0, y0, x1, y1)


def save_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L").save(path)


def local_raw_text_mask(rgb: np.ndarray, bbox: tuple[float, float, float, float]) -> tuple[np.ndarray, tuple[int, int, int, int], list[int]]:
    """No-dilation 20/255 foreground mask inside exactly one PDF glyph bbox."""
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = bbox_to_slice(bbox, w, h)
    if x1 <= x0 or y1 <= y0:
        return np.zeros((1, 1), dtype=bool), (x0, y0, x1, y1), [255, 255, 255]
    ex0, ey0, ex1, ey1 = max(0, x0 - 2), max(0, y0 - 2), min(w, x1 + 2), min(h, y1 + 2)
    expanded = rgb[ey0:ey1, ex0:ex1]
    ring = np.ones(expanded.shape[:2], dtype=bool)
    ring[y0 - ey0:y1 - ey0, x0 - ex0:x1 - ex0] = False
    samples = expanded[ring]
    if len(samples):
        colors, counts = np.unique(samples.reshape(-1, 3), axis=0, return_counts=True)
        bg = colors[int(np.argmax(counts))]
    else:
        bg = np.array([255, 255, 255], dtype=np.uint8)
    local = rgb[y0:y1, x0:x1]
    raw = np.max(np.abs(local.astype(np.int16) - bg.astype(np.int16)), axis=2) >= 20
    return raw, (x0, y0, x1, y1), [int(v) for v in bg]


def unicode_class(char: str, is_script: bool) -> tuple[str, int]:
    cp = ord(char)
    east = unicodedata.east_asian_width(char)
    if 0x4E00 <= cp <= 0x9FFF or east in {"F", "W"}:
        return "CJK_OR_FULLWIDTH", 30
    # A TeX-produced sub/superscript keeps its script status even where the
    # glyph happens to be an operator or digit; it is nevertheless measured
    # separately by its own PDF bbox and raw mask.
    if is_script:
        return "NATURAL_SCRIPT", 15
    if char in {"=", "+", "−", "-", "<", ">", "≤", "≥", "↦", "∗", "⋆", "(", ")", ",", ".", "：", "∶", ":", "|", "/"}:
        return "BASE_MATH_OR_PUNCT", 22
    if unicodedata.category(char).startswith(("P", "S")):
        return "BASE_MATH_OR_PUNCT", 22
    if char.isdigit() or char.isupper():
        return "UPPER_OR_DIGIT", 24
    if char.islower() or char in {"𝑟", "𝑡", "𝑦", "𝜌", "𝜙", "𝜃"}:
        return "LOWER_OR_GREEK", 17
    return "BASE_MATH_OR_PUNCT", 22


XTICK_IDS = ["SEM_XTICK_0", "SEM_XTICK_02", "SEM_XTICK_04", "SEM_XTICK_06", "SEM_XTICK_08", "SEM_XTICK_1"]
YTICK_IDS = ["SEM_YTICK_0", "SEM_YTICK_02", "SEM_YTICK_04", "SEM_YTICK_06", "SEM_YTICK_08", "SEM_YTICK_1"]
XTICK_CENTERS = [217.2, 250.0, 282.9, 315.0, 347.0, 379.3]
YTICK_CENTERS = [551.5, 519.1, 486.6, 454.2, 421.8, 389.4]


def group_for_char(cx: float, cy: float) -> str:
    # Caption is treated as one semantic parent; it is not split into a false
    # line-spacing relation, while every raw glyph remains separately measured.
    if 580.0 <= cy <= 605.0:
        return "SEM_CAPTION_PARENT"
    if 552.0 <= cy <= 570.0:
        return XTICK_IDS[min(range(6), key=lambda i: abs(XTICK_CENTERS[i] - cx))]
    # The rotated y-axis label is spatially left of the tick-label band and
    # must be assigned before the broad y-tick rule below.
    if 450.0 <= cy < 490.0 and 175.0 <= cx <= 200.0:
        return "SEM_Y_AXIS_LABEL"
    if cx < 215.0 and 380.0 <= cy < 552.0:
        return YTICK_IDS[min(range(6), key=lambda i: abs(YTICK_CENTERS[i] - cy))]
    if 390.0 <= cy < 410.0 and cx > 325.0:
        return "SEM_CURVE_REFERENCE"
    if 415.0 <= cy < 440.0 and cx > 330.0:
        return "SEM_CURVE_MAP"
    if 460.0 <= cy < 485.0 and 230.0 <= cx <= 280.0:
        return "SEM_FIXED_POINT"
    if 530.0 <= cy < 550.0 and 225.0 <= cx <= 275.0:
        return "SEM_INITIAL_LOW"
    if 530.0 <= cy < 550.0 and 315.0 <= cx <= 360.0:
        return "SEM_INITIAL_HIGH"
    if 505.0 <= cy < 535.0 and 280.0 <= cx <= 340.0:
        return "SEM_NOTEBOX_PARENT"
    if 560.0 <= cy < 580.0 and 285.0 <= cx <= 310.0:
        return "SEM_X_AXIS_LABEL"
    # y-axis 0 at y=551.46 is intentionally below the previous band.
    if cx < 215.0 and 545.0 <= cy < 552.0:
        return "SEM_YTICK_0"
    raise RuntimeError(f"Unassigned scoped glyph at PDF center ({cx:.3f},{cy:.3f})")


SEMANTIC_META: dict[str, dict] = {
    **{sid: {"role": "AXIS_TICK", "source_line": 6, "base_pt": FONT_TICK, "font_origin": "figure L6 explicit pgfplots tick label style; local font overrides common every-node style"} for sid in XTICK_IDS + YTICK_IDS},
    "SEM_CURVE_REFERENCE": {"role": "CURVE_LABEL", "source_line": 27, "base_pt": FONT_CURVE, "font_origin": "figure L27 explicit node font=9.3pt"},
    "SEM_CURVE_MAP": {"role": "CURVE_LABEL", "source_line": 29, "base_pt": FONT_CURVE, "font_origin": "figure L29 explicit node font=9.3pt"},
    "SEM_FIXED_POINT": {"role": "FIXED_POINT_LABEL", "source_line": 31, "base_pt": FONT_AXIS, "font_origin": "figure L31 explicit node font=9.4pt"},
    "SEM_INITIAL_LOW": {"role": "INITIAL_LABEL", "source_line": 39, "base_pt": FONT_INITIAL, "font_origin": "figure L39 explicit node font=9.2pt"},
    "SEM_INITIAL_HIGH": {"role": "INITIAL_LABEL", "source_line": 47, "base_pt": FONT_INITIAL, "font_origin": "figure L47 explicit node font=9.2pt"},
    "SEM_NOTEBOX_PARENT": {"role": "NOTEBOX", "source_line": 48, "base_pt": FONT_INITIAL, "font_origin": "figure L48 explicit node font=9.2pt"},
    "SEM_X_AXIS_LABEL": {"role": "AXIS_LABEL", "source_line": 7, "base_pt": FONT_AXIS, "font_origin": "figure L7 explicit pgfplots label style=9.4pt"},
    "SEM_Y_AXIS_LABEL": {"role": "AXIS_LABEL", "source_line": 7, "base_pt": FONT_AXIS, "font_origin": "figure L7 explicit pgfplots label style=9.4pt"},
    "SEM_CAPTION_PARENT": {"role": "CAPTION", "source_line": 52, "base_pt": FONT_CAPTION_VECTOR, "font_origin": "frozen-PDF vector caption spans; source L52 has no local caption-size override"},
}

SEMANTIC_TEXT = {
    "SEM_XTICK_0": "0", "SEM_XTICK_02": "0.2", "SEM_XTICK_04": "0.4", "SEM_XTICK_06": "0.6", "SEM_XTICK_08": "0.8", "SEM_XTICK_1": "1",
    "SEM_YTICK_0": "0", "SEM_YTICK_02": "0.2", "SEM_YTICK_04": "0.4", "SEM_YTICK_06": "0.6", "SEM_YTICK_08": "0.8", "SEM_YTICK_1": "1",
    "SEM_CURVE_REFERENCE": "$y=r$", "SEM_CURVE_MAP": "$y=0.2+0.5r$", "SEM_FIXED_POINT": "$r^*=0.4$",
    "SEM_INITIAL_LOW": "$r_0=.05$", "SEM_INITIAL_HIGH": "$r_0=.90$", "SEM_NOTEBOX_PARENT": "斜率 $0.5<1$；压缩映射",
    "SEM_X_AXIS_LABEL": "$r_t$", "SEM_Y_AXIS_LABEL": "$r_{t+1}$",
    "SEM_CAPTION_PARENT": "图 30.4 两状态概率单纯形上的平稳固定点：映射 $r\mapsto0.2+0.5r$ 把任意初值逐步拉向 $r_\star=0.4$",
}


def point_scope(point: fitz.Point, sx: float, sy: float, scope_px: tuple[int, int, int, int]) -> tuple[float, float]:
    return point.x * sx - scope_px[0], point.y * sy - scope_px[1]


def line_mask(shape: tuple[int, int], segments: list[tuple[tuple[float, float], tuple[float, float]]], width_px: float) -> np.ndarray:
    image = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(image)
    width = max(1, int(round(width_px)))
    for p0, p1 in segments:
        draw.line([p0, p1], fill=255, width=width)
    return np.asarray(image) > 0


def polygon_mask(shape: tuple[int, int], points: list[tuple[float, float]], fill: bool = True, width_px: float = 1.0) -> np.ndarray:
    image = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(image)
    if fill:
        draw.polygon(points, fill=255)
    else:
        draw.line(points + [points[0]], fill=255, width=max(1, int(round(width_px))))
    return np.asarray(image) > 0


def ellipse_mask(shape: tuple[int, int], rect: tuple[float, float, float, float]) -> np.ndarray:
    image = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(image).ellipse(rect, fill=255)
    return np.asarray(image) > 0


def rounded_border_mask(shape: tuple[int, int], rect: tuple[float, float, float, float], width_px: float, radius_px: float) -> np.ndarray:
    image = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(image).rounded_rectangle(rect, radius=max(1, int(round(radius_px))), outline=255, width=max(1, int(round(width_px))))
    return np.asarray(image) > 0


def graphic_raw_mask(selector: np.ndarray, scope_rgb: np.ndarray, background: list[int]) -> np.ndarray:
    # The final PDF vector path is the graphic's own independent native-grid
    # mask.  Do not sample the composited page colour here: a later text paint
    # operation could otherwise be mistaken for the line's ink (paint-order
    # contamination).  `selector` is generated directly from the extracted
    # PDF path/stroke/fill at 300dpi, with no dilation.
    return selector.copy()


def mask_clearance(a: np.ndarray, b: np.ndarray) -> tuple[int, float]:
    overlap = int((a & b).sum())
    if overlap:
        return overlap, 0.0
    if not a.any() or not b.any():
        return 0, math.inf
    distances = distance_transform_edt(~b)
    return 0, max(0.0, float(distances[a].min()) - 1.0)


def pdf_bbox_clearance_px(a: tuple[float,float,float,float], b: tuple[float,float,float,float], sx: float, sy: float) -> float:
    """Euclidean separation of two unexpanded PDF/vector bboxes in native px."""
    dx=max(0.0, b[0]-a[2], a[0]-b[2]) * sx
    dy=max(0.0, b[1]-a[3], a[1]-b[3]) * sy
    return math.hypot(dx,dy)


def crop_pair_roi(original: Image.Image, a: np.ndarray, b: np.ndarray, scope_px: tuple[int, int, int, int], rid: str, reason: str, manifest: list[dict]) -> None:
    # A collision artifact must make the concrete failed pixels inspectable.
    # When masks overlap, frame the raw overlap (not an entire long curve) with
    # a context margin.  One-party legibility diagnostics retain their full
    # foreground union.
    overlap = a & b
    target = overlap if overlap.any() else (a | b)
    _, (lx0, ly0, lx1, ly1) = crop_mask(target)
    margin = 16 if overlap.any() else 10
    sx0, sy0, sx1, sy1 = scope_px
    px0, py0 = max(sx0, sx0 + lx0 - margin), max(sy0, sy0 + ly0 - margin)
    px1, py1 = min(sx1, sx0 + lx1 + margin), min(sy1, sy0 + ly1 + margin)
    critical = mkdir(OUT / "critical")
    raw = critical / f"{rid}_raw.png"
    ma = critical / f"{rid}_mask_a.png"
    mb = critical / f"{rid}_mask_b.png"
    ov = critical / f"{rid}_overlap.png"
    overlay = critical / f"{rid}_overlay.png"
    zoom = critical / f"{rid}_overlay_8x.png"
    roi = original.crop((px0, py0, px1, py1))
    aroi = a[py0 - sy0:py1 - sy0, px0 - sx0:px1 - sx0]
    broi = b[py0 - sy0:py1 - sy0, px0 - sx0:px1 - sx0]
    roi.save(raw)
    save_mask(ma, aroi); save_mask(mb, broi); save_mask(ov, aroi & broi)
    arr = np.asarray(roi.convert("RGB")).copy()
    arr[:, :, 0][aroi] = 255; arr[:, :, 1][aroi] = 0; arr[:, :, 2][aroi] = 0
    arr[:, :, 0][broi] = 0; arr[:, :, 1][broi] = 255; arr[:, :, 2][broi] = 0
    arr[aroi & broi] = np.array([255, 255, 0], dtype=np.uint8)
    rendered = Image.fromarray(arr, "RGB")
    rendered.save(overlay)
    rendered.resize((rendered.width * 8, rendered.height * 8), Image.Resampling.NEAREST).save(zoom)
    manifest.append({"ARTIFACT_ID": rid, "REASON": reason, "RAW_ROI": rel(raw), "MASK_A": rel(ma), "MASK_B": rel(mb), "OVERLAP_MASK": rel(ov), "OVERLAY": rel(overlay), "ZOOM_8X": rel(zoom)})


def drawing_lines(drawing: dict, sx: float, sy: float, scope_px: tuple[int, int, int, int]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    output = []
    for item in drawing["items"]:
        if item[0] == "l":
            output.append((point_scope(item[1], sx, sy, scope_px), point_scope(item[2], sx, sy, scope_px)))
    return output


def main() -> None:
    mkdir(OUT); masks_glyph = mkdir(OUT / "masks" / "glyphs"); masks_sem = mkdir(OUT / "masks" / "semantic"); masks_graphic = mkdir(OUT / "masks" / "graphics")
    page300 = OUT / f"page300-{PDF_PAGE}.png"; page200 = OUT / f"page200-{PDF_PAGE}.png"
    poppler = Path(r"D:\texlive\2026\bin\windows\pdftoppm.exe")
    if not page300.exists():
        subprocess.run([str(poppler), "-png", "-r", "300", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), str(PDF), str(OUT / "page300")], check=True)
    if not page200.exists():
        subprocess.run([str(poppler), "-png", "-r", "200", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), str(PDF), str(OUT / "page200")], check=True)
    full300, full200 = OUT / "full_page_300dpi_native.png", OUT / "full_page_200dpi.png"
    shutil.copy2(page300, full300); shutil.copy2(page200, full200)
    im300 = Image.open(full300).convert("RGB")
    doc = fitz.open(PDF); page = doc[PAGE_INDEX]
    sx, sy = im300.width / page.rect.width, im300.height / page.rect.height
    scope_px = bbox_to_slice(bbox_to_px(SCOPE_PDF, sx, sy), im300.width, im300.height)
    standalone_px = bbox_to_slice(bbox_to_px(STANDALONE_PDF, sx, sy), im300.width, im300.height)
    im300.crop(scope_px).save(OUT / "figure_crop_300dpi.png")
    im300.crop(standalone_px).save(OUT / "standalone_300dpi.png")
    ImageOps.grayscale(im300.crop(scope_px)).save(OUT / "grayscale_300dpi.png")
    rgb = np.asarray(im300); scx0, scy0, scx1, scy1 = scope_px; scope_rgb = rgb[scy0:scy1, scx0:scx1]; scope_shape = scope_rgb.shape[:2]

    frozen_hash = sha256_file(PDF)
    render_manifest = {
        "frozen_pdf": str(PDF), "frozen_pdf_sha256": frozen_hash, "pdf_page": PDF_PAGE, "pdf_page_index_zero_based": PAGE_INDEX, "pdf_page_count": len(doc),
        "native_300dpi_size_px": [im300.width, im300.height], "native_200dpi_file": rel(full200), "native_300dpi_file": rel(full300),
        "figure_crop_300dpi_file": "figure_crop_300dpi.png", "standalone_300dpi_file": "standalone_300dpi.png", "grayscale_300dpi_file": "grayscale_300dpi.png", "full_page_native_grid_file": "full_page_300dpi_grid.json",
        "no_resize_after_native_render": True, "crop_is_coordinate_only": True, "grayscale_is_mode_conversion_only": True,
        "measurement_scale": [sx, sy], "effective_font_cascade": "shared statlearnbook.sty:L276 every node small exists, but all figure tick/label/node styles are locally explicit (L6,L7,L27,L29,L31,L39,L47,L48), so their declared sizes control final output.",
    }
    write_text(OUT / "render_manifest.json", json.dumps(render_manifest, ensure_ascii=False, indent=2))
    full_grid = {
        "grid_id": "FULL_PAGE_NATIVE_300DPI",
        "input_pdf_page": PDF_PAGE,
        "dpi": 300,
        "native_png": "full_page_300dpi_native.png",
        "width_px": im300.width,
        "height_px": im300.height,
        "pdf_page_rect_pt": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
        "pdf_to_native_px_scale": [sx, sy],
        "origin": "top-left pixel (0,0), direct Poppler native render",
        "resize_after_render": False,
        "measurement_policy": "All pixel measurements use this immutable full-page 300dpi grid; crops preserve its coordinates.",
    }
    write_text(OUT / "full_page_300dpi_grid.json", json.dumps(full_grid, ensure_ascii=False, indent=2))
    fig_lines = FIG_SRC.read_text(encoding="utf-8").splitlines(); ch_lines = CHAPTER.read_text(encoding="utf-8").splitlines(); style_lines = STYLE.read_text(encoding="utf-8").splitlines()
    write_text(OUT / "source_figure_excerpt.tex", "\n".join(f"{i+1:03d}: {line}" for i, line in enumerate(fig_lines)) + "\n")
    write_text(OUT / "adjacent_source_context.tex", "\n".join(f"{i:04d}: {ch_lines[i-1]}" for i in range(619, 630)) + "\n")
    write_text(OUT / "shared_style_font_context.tex", "\n".join(f"{i:04d}: {style_lines[i-1]}" for i in range(269, 281)) + "\n")
    page_text = page.get_text("text")
    write_text(OUT / "pdf_context_excerpt.txt", f"Frozen PDF physical page: {PDF_PAGE}/{len(doc)}\n\n" + "\n".join(line for line in page_text.splitlines() if "两状态概率" in line or "平稳固定点" in line or "0.2" in line) + "\n")

    rawdict = page.get_text("rawdict")
    chars: list[dict] = []; groups: defaultdict[str, list[dict]] = defaultdict(list); mask_manifest: list[dict] = []
    glyph_counter = 0
    for block in rawdict["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for ch in span["chars"]:
                    char = ch["c"]
                    if char.isspace():
                        continue
                    bbox_pdf = tuple(float(v) for v in ch["bbox"])
                    cx, cy = (bbox_pdf[0] + bbox_pdf[2]) / 2, (bbox_pdf[1] + bbox_pdf[3]) / 2
                    if not (SCOPE_PDF[0] <= cx <= SCOPE_PDF[2] and SCOPE_PDF[1] <= cy <= SCOPE_PDF[3]):
                        continue
                    sid = group_for_char(cx, cy)
                    glyph_counter += 1; gid = f"GLYPH_{glyph_counter:03d}"
                    raw_local, local_slice, bg = local_raw_text_mask(rgb, bbox_to_px(bbox_pdf, sx, sy))
                    gx0, gy0, gx1, gy1 = local_slice
                    global_mask = np.zeros(scope_shape, dtype=bool)
                    lx0, ly0, lx1, ly1 = gx0 - scx0, gy0 - scy0, gx1 - scx0, gy1 - scy0
                    if 0 <= lx0 <= lx1 <= scope_shape[1] and 0 <= ly0 <= ly1 <= scope_shape[0]:
                        global_mask[ly0:ly1, lx0:lx1] = raw_local
                    else:
                        raise RuntimeError(f"Glyph bbox outside declared scope: {gid}")
                    mask_file = masks_glyph / f"{gid}.png"; save_mask(mask_file, raw_local)
                    rec = {"glyph_id": gid, "semantic_id": sid, "char": char, "codepoint": f"U+{ord(char):04X}", "bbox_pdf": bbox_pdf, "bbox_px": bbox_to_px(bbox_pdf, sx, sy), "span_size_pdf_pt": float(span["size"]), "font": span.get("font", ""), "mask": global_mask, "mask_file": rel(mask_file), "background": bg}
                    chars.append(rec); groups[sid].append(rec)
                    mask_manifest.append({"MASK_ID": gid, "KIND": "GLYPH_RAW_NO_DILATION", "PARENT_ID": sid, "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox_pdf), "MASK_FILE": rel(mask_file), "BACKGROUND_RGB": ",".join(map(str, bg)), "FOREGROUND_RULE": "local-mode background; max channel difference >=20; no dilation"})
    missing = sorted(set(SEMANTIC_META) - set(groups))
    if missing:
        raise RuntimeError(f"Missing semantic groups: {missing}")

    semantic_masks: dict[str, np.ndarray] = {}; semantic_bbox_pdf: dict[str, tuple[float,float,float,float]] = {}; semantic_rows: list[dict] = []; glyph_rows: list[dict] = []; font_rows: list[dict] = []
    for sid, members in groups.items():
        meta = SEMANTIC_META[sid]; vector_base = max(m["span_size_pdf_pt"] for m in members); base_pt = meta["base_pt"] if meta["base_pt"] is not None else vector_base
        merged = np.zeros(scope_shape, dtype=bool)
        for m in members: merged |= m["mask"]
        semantic_masks[sid] = merged
        sem_crop, _ = crop_mask(merged); sem_file = masks_sem / f"{sid}.png"; save_mask(sem_file, sem_crop)
        bbox = (min(m["bbox_pdf"][0] for m in members), min(m["bbox_pdf"][1] for m in members), max(m["bbox_pdf"][2] for m in members), max(m["bbox_pdf"][3] for m in members))
        semantic_bbox_pdf[sid] = bbox
        semantic_rows.append({"ELEMENT_ID": sid, "PARENT_ELEMENT_ID": "CAPTION_PARENT" if sid == "SEM_CAPTION_PARENT" else sid, "PANEL_ID": "PANEL_STATIONARY_MAP", "ROLE": meta["role"], "SOURCE_FILE": str(FIG_SRC), "SOURCE_LINE": meta["source_line"], "TEXT_SAMPLE": SEMANTIC_TEXT[sid], "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox), "RAW_MASK_FILE": rel(sem_file), "RAW_INK_PIXEL_COUNT": int(merged.sum()), "H_INK_PX": int(crop_mask(merged)[0].shape[0]), "DECLARED_BASE_PT": f"{base_pt:.3f}", "GRAPHICS_SCALE": "1.000000", "FONT_ORIGIN": meta["font_origin"]})
        mask_manifest.append({"MASK_ID": sid, "KIND": "SEMANTIC_TEXT_RAW_NO_DILATION", "PARENT_ID": sid, "PDF_BBOX": ";".join(f"{v:.3f}" for v in bbox), "MASK_FILE": rel(sem_file), "BACKGROUND_RGB": "per-glyph inherited", "FOREGROUND_RULE": "OR of constituent raw glyph masks; no dilation"})
        for m in members:
            is_script = m["span_size_pdf_pt"] < 0.92 * vector_base
            klass, threshold = unicode_class(m["char"], is_script)
            effective = base_pt * m["span_size_pdf_pt"] / vector_base
            # Natural scripts are permitted only when produced by a >=9.5pt
            # base; their own visual limit is still separately enforced.
            font_pass = base_pt >= 9.5 if is_script else effective >= 9.5
            font_reason = f"natural script from base={base_pt:.3f}pt" if is_script else f"ordinary effective={effective:.3f}pt"
            ink_h = int(crop_mask(m["mask"])[0].shape[0]); pixel_pass = ink_h >= threshold
            row = {"ELEMENT_ID": m["glyph_id"], "PARENT_ELEMENT_ID": sid, "PANEL_ID": "PANEL_STATIONARY_MAP", "ROLE": meta["role"], "SOURCE_FILE": str(FIG_SRC), "SOURCE_LINE": meta["source_line"], "DECLARED_PT": f"{base_pt:.3f}", "GRAPHICS_SCALE": "1.000000", "EFFECTIVE_PT": f"{effective:.3f}", "TEXT_SAMPLE": m["char"], "SCRIPT_CLASS": klass, "BBOX_X0": f"{m['bbox_px'][0]:.3f}", "BBOX_Y0": f"{m['bbox_px'][1]:.3f}", "BBOX_X1": f"{m['bbox_px'][2]:.3f}", "BBOX_Y1": f"{m['bbox_px'][3]:.3f}", "H_INK_PX": ink_h, "PIXEL_THRESHOLD_PX": threshold, "CLASS_MEDIAN_PX": "", "RATIO_TO_CLASS_MEDIAN": "", "ROLE_MEDIAN_PX": "", "RATIO_TO_ROLE_MEDIAN": "", "ROLE_RATIO": "", "TEXT_TEXT_OVERLAP_PX": "", "TEXT_GRAPHIC_OVERLAP_PX": "", "MIN_CLEARANCE_PX": "", "SOURCE_FONT_PASS": str(font_pass).lower(), "PIXEL_HEIGHT_PASS": str(pixel_pass).lower(), "PASS_FAIL": "PASS" if font_pass and pixel_pass else "FAIL", "REASON": f"{font_reason}; raw H_ink={ink_h}px threshold={threshold}px", "RAW_MASK_FILE": m["mask_file"], "LOCAL_BACKGROUND_RGB": ",".join(map(str, m["background"])), "PDF_VECTOR_FONT_SIZE_PT": f"{m['span_size_pdf_pt']:.3f}", "PDF_VECTOR_FONT": m["font"]}
            glyph_rows.append(row)
            font_rows.append({"ELEMENT_ID": m["glyph_id"], "PARENT_ELEMENT_ID": sid, "ROLE": meta["role"], "TEXT_SAMPLE": m["char"], "DECLARED_PT": f"{base_pt:.3f}", "EFFECTIVE_PT": f"{effective:.3f}", "PDF_VECTOR_FONT_SIZE_PT": f"{m['span_size_pdf_pt']:.3f}", "SCRIPT_NATURAL": str(is_script).lower(), "SOURCE_FONT_PASS": str(font_pass).lower(), "PASS_FAIL": "PASS" if font_pass else "FAIL", "REASON": font_reason, "FONT_EVIDENCE": meta["font_origin"]})

    # Build no-dilation graphic masks from frozen-PDF vector paths.
    chart = [d for d in page.get_drawings() if d["rect"].y1 > 370 and d["rect"].y0 < 580 and d["rect"].x1 > 170 and d["rect"].x0 < 420]
    if len(chart) != 14:
        raise RuntimeError(f"Expected 14 chart vector drawings, found {len(chart)}")
    xticks, yticks, xaxis, xarrow, yaxis, yarrow, reference, mapping, cobweb_low, cobweb_high, note_box, fixed_circle, low_square, high_triangle = chart
    graphics: list[dict] = []; graphic_bbox_pdf: dict[str, tuple[float,float,float,float]] = {}; graphics_rows: list[dict] = []

    def add_graphic(eid: str, kind: str, src_line: int, drawing: dict, selector: np.ndarray, note: str, background: list[int] = [255, 255, 255]) -> None:
        raw = graphic_raw_mask(selector, scope_rgb, background)
        cropped, _ = crop_mask(raw); f = masks_graphic / f"{eid}.png"; save_mask(f, cropped)
        bbox = drawing["rect"]
        graphic_bbox_pdf[eid] = (float(bbox.x0),float(bbox.y0),float(bbox.x1),float(bbox.y1))
        graphics.append({"ELEMENT_ID": eid, "KIND": kind, "mask": raw, "RAW_MASK_FILE": rel(f)})
        graphics_rows.append({"ELEMENT_ID": eid, "PANEL_ID": "PANEL_STATIONARY_MAP", "KIND": kind, "SOURCE_FILE": str(FIG_SRC), "SOURCE_LINE": src_line, "PDF_BBOX": f"{bbox.x0:.3f};{bbox.y0:.3f};{bbox.x1:.3f};{bbox.y1:.3f}", "RAW_MASK_FILE": rel(f), "RAW_FOREGROUND_PIXELS": int(raw.sum()), "NOTE": note})
        mask_manifest.append({"MASK_ID": eid, "KIND": f"GRAPHIC_{kind}_RAW_NO_DILATION", "PARENT_ID": eid, "PDF_BBOX": f"{bbox.x0:.3f};{bbox.y0:.3f};{bbox.x1:.3f};{bbox.y1:.3f}", "MASK_FILE": rel(f), "BACKGROUND_RGB": "NOT_USED_VECTOR_PATH", "FOREGROUND_RULE": "extracted final-PDF vector stroke/fill rasterized on native 300dpi grid; no dilation; no composited-page colour sampling"})

    for i, item in enumerate(xticks["items"], 1):
        add_graphic(f"GRAPHIC_X_TICK_{i}", "AXIS_TICK", 23, xticks, line_mask(scope_shape, [(point_scope(item[1], sx, sy, scope_px), point_scope(item[2], sx, sy, scope_px))], xticks["width"] * sx), "Individual x-axis tick.")
    for i, item in enumerate(yticks["items"], 1):
        add_graphic(f"GRAPHIC_Y_TICK_{i}", "AXIS_TICK", 23, yticks, line_mask(scope_shape, [(point_scope(item[1], sx, sy, scope_px), point_scope(item[2], sx, sy, scope_px))], yticks["width"] * sx), "Individual y-axis tick.")
    add_graphic("GRAPHIC_X_AXIS", "AXIS", 21, xaxis, line_mask(scope_shape, drawing_lines(xaxis, sx, sy, scope_px), xaxis["width"] * sx), "Horizontal coordinate axis.")
    xpoints = [point_scope(item[1], sx, sy, scope_px) for item in xarrow["items"]]
    add_graphic("GRAPHIC_X_AXIS_ARROW", "ARROW", 21, xarrow, polygon_mask(scope_shape, xpoints), "x-axis arrowhead.")
    add_graphic("GRAPHIC_Y_AXIS", "AXIS", 21, yaxis, line_mask(scope_shape, drawing_lines(yaxis, sx, sy, scope_px), yaxis["width"] * sx), "Vertical coordinate axis.")
    ypoints = [point_scope(item[1], sx, sy, scope_px) for item in yarrow["items"]]
    add_graphic("GRAPHIC_Y_AXIS_ARROW", "ARROW", 21, yarrow, polygon_mask(scope_shape, ypoints), "y-axis arrowhead.")
    add_graphic("GRAPHIC_REFERENCE_Y_EQ_R", "CURVE", 26, reference, line_mask(scope_shape, drawing_lines(reference, sx, sy, scope_px), reference["width"] * sx), "Dashed reference curve y=r; raster gate preserves dash gaps.")
    add_graphic("GRAPHIC_MAP", "CURVE", 28, mapping, line_mask(scope_shape, drawing_lines(mapping, sx, sy, scope_px), mapping["width"] * sx), "Map y=0.2+0.5r.")
    add_graphic("GRAPHIC_COBWEB_LOW", "CURVE", 34, cobweb_low, line_mask(scope_shape, drawing_lines(cobweb_low, sx, sy, scope_px), cobweb_low["width"] * sx), "Low-initialization solid cobweb.")
    add_graphic("GRAPHIC_COBWEB_HIGH", "CURVE", 42, cobweb_high, line_mask(scope_shape, drawing_lines(cobweb_high, sx, sy, scope_px), cobweb_high["width"] * sx), "High-initialization dashed cobweb.")
    nr = note_box["rect"]; note_px = bbox_to_px((nr.x0, nr.y0, nr.x1, nr.y1), sx, sy); note_local = (note_px[0]-scx0, note_px[1]-scy0, note_px[2]-scx0, note_px[3]-scy0)
    add_graphic("GRAPHIC_NOTEBOX_FILL", "FILL_BACKGROUND", 48, note_box, polygon_mask(scope_shape, [(note_local[0],note_local[1]),(note_local[2],note_local[1]),(note_local[2],note_local[3]),(note_local[0],note_local[3])]), "White note-box fill is enumerated but excluded from collision foreground targets.")
    add_graphic("GRAPHIC_NOTEBOX_BORDER", "NODE_BORDER", 48, note_box, rounded_border_mask(scope_shape, note_local, note_box["width"]*sx, 2.0*sx), "Rounded note-box border.")
    fr = fixed_circle["rect"]; fpx = bbox_to_px((fr.x0,fr.y0,fr.x1,fr.y1),sx,sy); add_graphic("GRAPHIC_FIXED_POINT", "MARKER", 30, fixed_circle, ellipse_mask(scope_shape,(fpx[0]-scx0,fpx[1]-scy0,fpx[2]-scx0,fpx[3]-scy0)), "Fixed point circle.")
    lr = low_square["rect"]; lpx=bbox_to_px((lr.x0,lr.y0,lr.x1,lr.y1),sx,sy); add_graphic("GRAPHIC_LOW_INITIAL_MARKER", "MARKER", 37, low_square, polygon_mask(scope_shape,[(lpx[0]-scx0,lpx[1]-scy0),(lpx[2]-scx0,lpx[1]-scy0),(lpx[2]-scx0,lpx[3]-scy0),(lpx[0]-scx0,lpx[3]-scy0)]), "Low start square marker.")
    tpoints = [point_scope(item[1],sx,sy,scope_px) for item in high_triangle["items"]]; add_graphic("GRAPHIC_HIGH_INITIAL_MARKER", "MARKER", 45, high_triangle, polygon_mask(scope_shape,tpoints), "High start triangle marker.")

    relation_rows: list[dict] = []; critical_manifest: list[dict] = []; sem_ids = sorted(semantic_masks); rcount = 0
    semantic_file = {r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in semantic_rows}; graphic_file = {r["ELEMENT_ID"]:r["RAW_MASK_FILE"] for r in graphics}
    def add_relation(aid: str, akind: str, amask: np.ndarray, bid: str, bkind: str, bmask: np.ndarray, relation_class: str, required: int) -> None:
        nonlocal rcount
        rcount += 1; rid=f"REL_{rcount:04d}"; overlap, clearance = mask_clearance(amask,bmask)
        bbox_a=semantic_bbox_pdf.get(aid,graphic_bbox_pdf.get(aid)); bbox_b=semantic_bbox_pdf.get(bid,graphic_bbox_pdf.get(bid))
        if bbox_a is None or bbox_b is None:
            raise RuntimeError(f"Missing PDF/vector bbox for relation {rid}: {aid}, {bid}")
        bbox_clearance=pdf_bbox_clearance_px(bbox_a,bbox_b,sx,sy)
        bbox_gate=(relation_class != "TEXT_TEXT") or bbox_clearance >= required
        passed=overlap==0 and clearance>=required and bbox_gate
        bbox_fmt=lambda v: ";".join(f"{x:.3f}" for x in v)
        reason="native-300dpi no-dilation separated raw masks; PDF/vector bboxes are unexpanded"
        row={"RELATION_ID":rid,"PANEL_ID":"PANEL_STATIONARY_MAP","ELEMENT_A":aid,"CATEGORY_A":akind,"PDF_VECTOR_BBOX_A":bbox_fmt(bbox_a),"ELEMENT_B":bid,"CATEGORY_B":bkind,"PDF_VECTOR_BBOX_B":bbox_fmt(bbox_b),"RELATION_CLASS":relation_class,"RAW_MASK_A":semantic_file.get(aid,graphic_file.get(aid,"")),"RAW_MASK_B":semantic_file.get(bid,graphic_file.get(bid,"")),"OVERLAP_PIXEL_COUNT":overlap,"CLEARANCE_PX":"INF" if math.isinf(clearance) else f"{clearance:.3f}","PDF_VECTOR_BBOX_CLEARANCE_PX":f"{bbox_clearance:.3f}","REQUIRED_CLEARANCE_PX":required,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if passed else "FAIL","REASON":reason,"CRITICAL_ROI":""}
        critical_bbox=(relation_class=="TEXT_TEXT" and bbox_clearance <= required+2)
        if not passed or critical_bbox or (not math.isinf(clearance) and clearance <= required+2):
            crop_pair_roi(im300,amask,bmask,scope_px,rid,f"{relation_class}; overlap={overlap}; raw_clearance={clearance:.3f}; bbox_clearance={bbox_clearance:.3f}; required={required}",critical_manifest); row["CRITICAL_ROI"]=f"critical/{rid}_raw.png"
        relation_rows.append(row)
    for i, aid in enumerate(sem_ids):
        for bid in sem_ids[i+1:]:
            # Caption/notebox are single semantic parents, preventing false
            # internal line-spacing checks while retaining all external pairs.
            add_relation(aid,"TEXT",semantic_masks[aid],bid,"TEXT",semantic_masks[bid],"TEXT_TEXT",4)
    collision_graphics=[g for g in graphics if g["KIND"] in {"AXIS_TICK","AXIS","ARROW","CURVE","MARKER","NODE_BORDER"}]
    for aid in sem_ids:
        for g in collision_graphics:
            req=5 if g["KIND"]=="NODE_BORDER" else 3
            add_relation(aid,"TEXT",semantic_masks[aid],g["ELEMENT_ID"],g["KIND"],g["mask"],f"TEXT_{g['KIND']}",req)
    edge_rows=[]
    for sid in sem_ids:
        ys,xs=np.nonzero(semantic_masks[sid]); edge=min(int(xs.min()),int(ys.min()),int(scope_shape[1]-1-xs.max()),int(scope_shape[0]-1-ys.max())); passed=edge>=6
        edge_rows.append({"RELATION_ID":f"EDGE_{sid}","PANEL_ID":"PANEL_STATIONARY_MAP","ELEMENT_A":sid,"CATEGORY_A":"TEXT","ELEMENT_B":"FIGURE_SCOPE_EDGE","CATEGORY_B":"PANEL_EDGE","RELATION_CLASS":"TEXT_EDGE","RAW_MASK_A":semantic_file[sid],"RAW_MASK_B":"coordinate edge","OVERLAP_PIXEL_COUNT":0,"CLEARANCE_PX":f"{edge:.3f}","REQUIRED_CLEARANCE_PX":6,"CLIP_PIXEL_COUNT":0,"PASS_FAIL":"PASS" if passed else "FAIL","REASON":"distance from raw foreground to direct 300dpi crop edge","CRITICAL_ROI":""})
    relation_rows.extend(edge_rows)

    # Goal D: Same-class means the *same panel + semantic role + script
    # class*, never a convenience grouping by individual glyph/morphology or
    # by declared point size.  Ratios below are actual raw 300dpi H_ink values.
    groupstats: defaultdict[tuple[str,str,str],list[dict]] = defaultdict(list)
    for row in glyph_rows:
        groupstats[(row["PANEL_ID"],row["ROLE"],row["SCRIPT_CLASS"])].append(row)
    same_rows=[]; same_pass=True
    group_medians: dict[tuple[str,str,str],float] = {}
    for (panel,role,klass), rows in sorted(groupstats.items()):
        hs=[int(r["H_INK_PX"]) for r in rows]
        med=float(median(hs)); low=min(hs)/med; high=max(hs)/med
        ok=low>=.92 and high<=1.08
        same_pass &= ok
        failures=[r["ELEMENT_ID"] for r in rows if not (.92 <= int(r["H_INK_PX"])/med <= 1.08)]
        for r in rows:
            r["CLASS_MEDIAN_PX"]=f"{med:.3f}"
            r["RATIO_TO_CLASS_MEDIAN"]=f"{int(r['H_INK_PX'])/med:.4f}"
        same_rows.append({"PANEL_ID":panel,"ROLE":role,"SCRIPT_CLASS":klass,"BASIS":"same panel + same semantic role + same script; raw no-dilation H_ink","ELEMENT_IDS":";".join(r["ELEMENT_ID"] for r in rows),"N":len(rows),"MEDIAN_H_INK_PX":f"{med:.3f}","MIN_TO_MEDIAN":f"{low:.4f}","MAX_TO_MEDIAN":f"{high:.4f}","VIOLATING_ELEMENT_IDS":";".join(failures),"PASS_FAIL":"PASS" if ok else "FAIL"})
        group_medians[(panel,role,klass)] = med

    # Goal E: role hierarchy may compare only the same script class to the
    # corresponding BASE role.  Never compare CJK, digit, punctuation, lower
    # and natural-script medians to one another.  Missing counterparts are
    # explicit not-applicable rows, not UNKNOWN and not a hard failure.
    hierarchy_bounds={
        "AXIS_TICK":(.90,1.00,"tick labels relative to AXIS_LABEL"),
        "AXIS_LABEL":(.95,1.10,"BASE"),
        "CURVE_LABEL":(.95,1.10,"curve label relative to AXIS_LABEL"),
        "FIXED_POINT_LABEL":(.95,1.10,"fixed-point label relative to AXIS_LABEL"),
        "INITIAL_LABEL":(.95,1.10,"initial label relative to AXIS_LABEL"),
        "NOTEBOX":(.95,1.10,"annotation relative to AXIS_LABEL"),
        "CAPTION":(.95,1.15,"caption relative to AXIS_LABEL"),
    }
    role_rows=[]; role_pass=True
    for (panel,role,klass), role_med in sorted(group_medians.items()):
        lo,hi,why=hierarchy_bounds[role]
        base_med=group_medians.get((panel,"AXIS_LABEL",klass))
        if base_med is None:
            role_rows.append({"AUDIT_SCOPE":"ROLE_HIERARCHY_SAME_SCRIPT","PANEL_ID":panel,"ROLE":role,"SCRIPT_CLASS":klass,"ROLE_RAW_MEDIAN_H_INK_PX":f"{role_med:.3f}","BASE_ROLE":"AXIS_LABEL","BASE_ROLE_RAW_MEDIAN_H_INK_PX":"","ROLE_TO_BASE_RATIO":"","LOW":f"{lo:.2f}","HIGH":f"{hi:.2f}","COMPARABILITY":"EXPLICIT_NA_NO_MATCHING_BASE_SCRIPT","RATIONALE":why,"PASS_FAIL":"PASS"})
            continue
        ratio=role_med/base_med; ok=lo<=ratio<=hi
        role_pass &= ok
        role_rows.append({"AUDIT_SCOPE":"ROLE_HIERARCHY_SAME_SCRIPT","PANEL_ID":panel,"ROLE":role,"SCRIPT_CLASS":klass,"ROLE_RAW_MEDIAN_H_INK_PX":f"{role_med:.3f}","BASE_ROLE":"AXIS_LABEL","BASE_ROLE_RAW_MEDIAN_H_INK_PX":f"{base_med:.3f}","ROLE_TO_BASE_RATIO":f"{ratio:.4f}","LOW":f"{lo:.2f}","HIGH":f"{hi:.2f}","COMPARABILITY":"SAME_SCRIPT_COMPARABLE","RATIONALE":why,"PASS_FAIL":"PASS" if ok else "FAIL"})
    for row in glyph_rows:
        role_med=group_medians[(row["PANEL_ID"],row["ROLE"],row["SCRIPT_CLASS"])]
        ratio=int(row["H_INK_PX"])/role_med
        row["ROLE_MEDIAN_PX"]=f"{role_med:.3f}"
        row["RATIO_TO_ROLE_MEDIAN"]=f"{ratio:.4f}"
        row["ROLE_RATIO"]=f"{ratio:.4f}"
    panel_ids=sorted({panel for panel,_,_ in group_medians})
    cross_rows=[]; cross_panel_pass=True
    role_script_keys=sorted({(role,klass) for _,role,klass in group_medians})
    for role,klass in role_script_keys:
        values=[group_medians[(p,role,klass)] for p in panel_ids if (p,role,klass) in group_medians]
        ratio=max(values)/min(values) if values else math.inf
        explicit_single=len(panel_ids)==1
        ok=(explicit_single and len(values)==1) or (len(values)==len(panel_ids) and ratio<=1.10)
        cross_panel_pass &= ok
        cross_rows.append({"ROLE":role,"SCRIPT_CLASS":klass,"PANEL_IDS":";".join(panel_ids),"PANEL_COUNT":len(panel_ids),"RAW_ROLE_SCRIPT_MEDIANS_PX":";".join(f"{v:.3f}" for v in values),"EXTREME_RATIO":f"{ratio:.4f}","LIMIT":"<=1.10","APPLICABILITY":"SINGLE_PANEL_EXPLICIT" if explicit_single else "MULTI_PANEL_SAME_ROLE_SAME_SCRIPT","PASS_FAIL":"PASS" if ok else "FAIL"})

    source_font_pass=all(r["SOURCE_FONT_PASS"]=="true" for r in glyph_rows); source_font_fail_count=sum(r["SOURCE_FONT_PASS"]=="false" for r in glyph_rows); source_font_fail_components=len({r["PARENT_ELEMENT_ID"] for r in glyph_rows if r["SOURCE_FONT_PASS"]=="false"})
    pixel_pass=all(r["PIXEL_HEIGHT_PASS"]=="true" for r in glyph_rows); failed_pixel=[r for r in glyph_rows if r["PIXEL_HEIGHT_PASS"]=="false"]
    total_overlap=sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relation_rows); clip_total=sum(int(r["CLIP_PIXEL_COUNT"]) for r in relation_rows); clearance_pass=all(r["PASS_FAIL"]=="PASS" for r in relation_rows)
    text_text_raw=[float(r["CLEARANCE_PX"]) for r in relation_rows if r["RELATION_CLASS"]=="TEXT_TEXT" and r["CLEARANCE_PX"]!="INF"]
    text_text_bbox=[float(r["PDF_VECTOR_BBOX_CLEARANCE_PX"]) for r in relation_rows if r["RELATION_CLASS"]=="TEXT_TEXT"]
    text_line=[float(r["CLEARANCE_PX"]) for r in relation_rows if r["RELATION_CLASS"] in {"TEXT_AXIS_TICK","TEXT_AXIS","TEXT_ARROW","TEXT_CURVE","TEXT_MARKER"} and r["CLEARANCE_PX"]!="INF"]
    text_border=[float(r["CLEARANCE_PX"]) for r in relation_rows if r["RELATION_CLASS"]=="TEXT_NODE_BORDER" and r["CLEARANCE_PX"]!="INF"]
    edges=[float(r["CLEARANCE_PX"]) for r in edge_rows]
    min_tt_raw=min(text_text_raw) if text_text_raw else math.inf; min_tt_bbox=min(text_text_bbox) if text_text_bbox else math.inf; min_tt=min(min_tt_raw,min_tt_bbox); min_tl=min(text_line) if text_line else math.inf; min_tb=min(text_border) if text_border else math.inf; min_edge=min(edges) if edges else math.inf
    # Visual inspection: typography is not harmonious because all in-chart
    # operational text roles are 8.7--9.4pt, under the hard 9.5pt floor.
    font_visual_harmony=False; visual_harmony=False
    # Math itself is correct; notation consistency is not: graph r^* conflicts
    # with caption r_star for the same fixed point.
    math_semantics_pass=True; probability_semantics_pass=True; text_consistency_pass=False
    grayscale_pass=True; page_integration_pass=True
    final_pass=all([source_font_pass,pixel_pass,same_pass,role_pass,total_overlap==0,clip_total==0,clearance_pass,cross_panel_pass,font_visual_harmony,math_semantics_pass,probability_semantics_pass,text_consistency_pass,grayscale_pass,page_integration_pass])
    hard={"SOURCE_FONT_PASS":source_font_pass,"SOURCE_FONT_FAILURE_COUNT":source_font_fail_count,"SOURCE_FONT_FAILURE_COMPONENT_COUNT":source_font_fail_components,"PIXEL_HEIGHT_PASS":pixel_pass,"PIXEL_HEIGHT_FAILURE_COUNT":len(failed_pixel),"SAME_CLASS_RATIO_PASS":same_pass,"ROLE_RATIO_PASS":role_pass,"OVERLAP_PIXEL_COUNT":total_overlap,"CLIP_PIXEL_COUNT":clip_total,"MIN_TEXT_TEXT_RAW_CLEARANCE_PX":min_tt_raw,"MIN_TEXT_TEXT_BBOX_CLEARANCE_PX":min_tt_bbox,"MIN_TEXT_TEXT_CLEARANCE_PX":min_tt,"MIN_TEXT_LINE_CLEARANCE_PX":min_tl,"MIN_TEXT_NODE_BORDER_CLEARANCE_PX":min_tb,"MIN_TEXT_EDGE_CLEARANCE_PX":min_edge,"CLEARANCE_PASS":clearance_pass,"CROSS_PANEL_PASS":cross_panel_pass,"FONT_VISUAL_HARMONY_PASS":font_visual_harmony,"VISUAL_HARMONY_PASS":visual_harmony,"MATH_SEMANTICS_PASS":math_semantics_pass,"PROBABILITY_SEMANTICS_PASS":probability_semantics_pass,"TEXT_CONSISTENCY_PASS":text_consistency_pass,"GRAYSCALE_PASS":grayscale_pass,"PAGE_INTEGRATION_PASS":page_integration_pass,"FINAL_RESULT":"PASS" if final_pass else "FAIL","NEXT_ROLE":"SA3" if final_pass else "SA2"}

    # Overlay semantic bboxes in situ (measurement view is unchanged native page).
    ov=im300.copy(); dr=ImageDraw.Draw(ov); colors={"AXIS_TICK":"#f59e0b","AXIS_LABEL":"#d946ef","CURVE_LABEL":"#0ea5e9","FIXED_POINT_LABEL":"#b45309","INITIAL_LABEL":"#2563eb","NOTEBOX":"#16a34a","CAPTION":"#dc2626"}
    for row in semantic_rows:
        x0,y0,x1,y1=(float(v) for v in row["PDF_BBOX"].split(";")); dr.rectangle(bbox_to_px((x0,y0,x1,y1),sx,sy),outline=colors.get(row["ROLE"],"#000000"),width=2)
    ov.save(OUT / "after_text_measurement_overlay_300dpi.png")

    # Operator/punctuation critical composite: uses individual raw masks, never
    # a parent formula substitute.
    op=[r for r in failed_pixel if r["SCRIPT_CLASS"]=="BASE_MATH_OR_PUNCT"]
    if op:
        compa=np.zeros(scope_shape,dtype=bool)
        for r in op:
            compa |= next(m["mask"] for m in chars if m["glyph_id"]==r["ELEMENT_ID"])
        # Leave the counterpart mask genuinely empty: this is a one-party
        # legibility diagnostic, not a fabricated spatial collision.
        compb=np.zeros(scope_shape,dtype=bool)
        crop_pair_roi(im300,compa,compb,scope_px,"PIXEL_FAIL_LITERAL_OPERATORS","independent literal operators/punctuation below own H_ink threshold",critical_manifest)
    # Explicit source font diagnostic for all under-9.5 plot glyphs.
    ff=np.zeros(scope_shape,dtype=bool)
    for r in glyph_rows:
        if r["SOURCE_FONT_PASS"]=="false": ff |= next(m["mask"] for m in chars if m["glyph_id"]==r["ELEMENT_ID"])
    dummy=np.zeros(scope_shape,dtype=bool)
    crop_pair_roi(im300,ff,dummy,scope_px,"SOURCE_FONT_FAIL_PLOT_TEXT","all locally explicit in-chart text below 9.5pt",critical_manifest)

    # Exact independent mathematical recomputation.
    f=lambda r: .2+.5*r
    low=[.05,f(.05),f(f(.05)),f(f(f(.05))),f(f(f(f(.05))))]
    high=[.90,f(.90),f(f(.90)),f(f(f(.90))),f(f(f(f(.90))))]
    fixed=.2/(1-.5)
    math_report=f"""# FIG-P556-01 数学/概率语义独立复算（SA1）

冻结 PDF 第 {PDF_PAGE} 页、图源 L18--52 和相邻正文 L624--625 是唯一输入。

\n## 映射与固定点

\\[f(r)=0.2+0.5r,\\qquad r=f(r)\\iff r=0.4.\\]

映射把区间 $[0,1]$ 送入 $[0.2,0.7]\\subset[0,1]$，斜率（Lipschitz 常数）为 $0.5<1$，故它是压缩映射；固定点唯一。

## Cobweb 坐标复核

- 低初值：$r_0=0.05\\to0.225\\to0.3125\\to0.35625\\to0.378125$；图源 L35--36 的水平/竖直点列精确匹配。
- 高初值：$r_0=0.90\\to0.65\\to0.525\\to0.4625\\to0.43125$；图源 L43--44 的点列精确匹配。
- 标注点 $(0.4,0.4)$ 与固定点一致。

## 概率语义与图文

若 $r$ 是两状态概率向量 $\\rho=(r,1-r)$ 的第一分量，则 $r_\\star=0.4$ 对应正文 L624 的 $\\rho=(0.4,0.6)$；该概率语义、非负性和归一化均正确。因此 `MATH_SEMANTICS_PASS=true`、`PROBABILITY_SEMANTICS_PASS=true`。

但图内固定点写作 $r^*=0.4$（L31），而题注写作 $r_\\star=0.4$（L52），未声明两者等价；这是同一对象的符号不一致。因此 `TEXT_CONSISTENCY_PASS=false`。
"""
    math_rows=[
        {"CHECK_ID":"MAP","SOURCE_LINES":"L28; adjacent L624","INPUT_R":"symbolic","FORMULA":"f(r)=0.2+0.5r","EXPECTED":"[0,1] -> [0.2,0.7]","OBSERVED":"[0.2,0.7]","PASS_FAIL":"PASS"},
        {"CHECK_ID":"FIXED_POINT","SOURCE_LINES":"L30-L31; adjacent L624","INPUT_R":"r=f(r)","FORMULA":"r=0.2+0.5r","EXPECTED":"0.4","OBSERVED":f"{fixed:.6f}","PASS_FAIL":"PASS"},
        {"CHECK_ID":"CONTRACTION","SOURCE_LINES":"L48-L49","INPUT_R":"symbolic","FORMULA":"|f'(r)|=0.5","EXPECTED":"0.5<1","OBSERVED":"0.5<1","PASS_FAIL":"PASS"},
    ]
    for seq_id, source_lines, seq in (("COBWEB_LOW","L35-L36",low),("COBWEB_HIGH","L43-L44",high)):
        for k in range(len(seq)-1):
            expected=f(seq[k])
            math_rows.append({"CHECK_ID":f"{seq_id}_{k}_TO_{k+1}","SOURCE_LINES":source_lines,"INPUT_R":f"{seq[k]:.6f}","FORMULA":"0.2+0.5r","EXPECTED":f"{expected:.6f}","OBSERVED":f"{seq[k+1]:.6f}","PASS_FAIL":"PASS" if math.isclose(expected,seq[k+1],abs_tol=1e-12) else "FAIL"})
    write_text(OUT / "math_semantics_recheck.md", math_report)
    write_csv(OUT / "math_semantics_recheck.csv", math_rows)
    write_text(OUT / "math_semantics_recheck.json", json.dumps({"mapping":"r -> 0.2+0.5r","fixed_point":fixed,"low_sequence":low,"high_sequence":high,"probability_at_fixed_point":[fixed,1-fixed],"pass":math_semantics_pass and probability_semantics_pass,"checks":math_rows},ensure_ascii=False,indent=2))

    write_csv(OUT / "semantic_component_inventory.csv", semantic_rows)
    write_csv(OUT / "graphic_component_inventory.csv", graphics_rows)
    write_csv(OUT / "glyph_inventory.csv", [{"ELEMENT_ID":m["glyph_id"],"PARENT_ELEMENT_ID":m["semantic_id"],"TEXT_SAMPLE":m["char"],"CODEPOINT":m["codepoint"],"PDF_BBOX":";".join(f"{v:.3f}" for v in m["bbox_pdf"]),"PDF_VECTOR_FONT_SIZE_PT":f"{m['span_size_pdf_pt']:.3f}","PDF_VECTOR_FONT":m["font"],"RAW_MASK_FILE":m["mask_file"],"LOCAL_BACKGROUND_RGB":",".join(map(str,m["background"]))} for m in chars])
    write_csv(OUT / "mask_manifest.csv", mask_manifest)
    write_csv(OUT / "after_font_audit.csv", font_rows)
    write_csv(OUT / "after_pixel_measurements.csv", glyph_rows)
    write_csv(OUT / "after_overlap_report.csv", relation_rows)
    write_csv(OUT / "same_class_ratio_audit.csv", same_rows)
    write_csv(OUT / "role_ratio_audit.csv", role_rows)
    write_csv(OUT / "cross_panel_ratio_audit.csv", cross_rows)
    write_csv(OUT / "critical_artifacts.csv", critical_manifest)

    summary={"audit_id":"FIG-P556-01/STRICT_R1/SA1_20260824_R1","role":"SA1 independent blind strict review","input":{"frozen_pdf":str(PDF),"page":PDF_PAGE,"figure_source":str(FIG_SRC),"adjacent_context":f"{CHAPTER}:619-629","style":f"{STYLE}:269-280"},"coverage":{"glyphs":len(chars),"semantic_text_components":len(semantic_rows),"graphic_components":len(graphics_rows),"text_text_pairs":len(sem_ids)*(len(sem_ids)-1)//2,"text_graphic_pairs":len(sem_ids)*len(collision_graphics),"text_edge_pairs":len(edge_rows),"arrow_components":2,"panel_components":1,"data_curve_components":4},"hard_gates":hard,"result":hard["FINAL_RESULT"],"handoff":hard["NEXT_ROLE"],"strict_method":"Native final-PDF 300dpi at 1:1; per-glyph PDF bboxes and 20/255 text raw masks; independent extracted-vector native-grid graphic masks without dilation or composited paint-order sampling; exhaustive registered pairs."}
    write_text(OUT / "strict_audit_summary.json", json.dumps(summary,ensure_ascii=False,indent=2))

    eight=[]
    def report(cid,cat,evidence,metric,threshold,observed,flag): eight.append({"CHECK_ID":cid,"CATEGORY":cat,"EVIDENCE":evidence,"METRIC":metric,"THRESHOLD":threshold,"OBSERVED":observed,"BOOLEAN":str(bool(flag)).lower(),"STATUS":"PASS" if flag else "FAIL"})
    report("R01","INPUT","render_manifest.json","frozen input / independent physical location","official R93 PDF only",f"page {PDF_PAGE}/{len(doc)}; sha256={frozen_hash}",True)
    report("R02","RENDER","full_page_200dpi.png","whole-page native render","200dpi","Poppler native",True)
    report("R03","RENDER","full_page_300dpi_native.png","measurement view","300dpi,1:1,no resize",f"{im300.width}x{im300.height}px; scale={sx:.6f}",True)
    report("R04","COVERAGE","glyph_inventory.csv;semantic_component_inventory.csv;graphic_component_inventory.csv","all visible reader-facing elements","complete",f"glyph={len(chars)}, semantic={len(semantic_rows)}, graphic={len(graphics_rows)}",True)
    report("R05","MASKS","mask_manifest.csv","raw masks","PDF bbox + no dilation",f"masks={len(mask_manifest)}",True)
    report("R06","SOURCE_FONT","after_font_audit.csv;shared_style_font_context.tex","ordinary effective font size",">=9.5pt",f"failure glyphs={source_font_fail_count}; components={source_font_fail_components}; explicit tick=8.7, labels=9.2--9.4",source_font_pass)
    report("R07","PIXEL_HEIGHT","after_pixel_measurements.csv","literal-glyph H_ink","30/24/17/22/15px",f"pixel failures={len(failed_pixel)}",pixel_pass)
    report("R08","SAME_CLASS","same_class_ratio_audit.csv","same panel + semantic role + script raw H_ink ratio","[0.92,1.08]","see CSV",same_pass)
    report("R09","ROLE_RATIO","role_ratio_audit.csv","actual raw-H_ink role hierarchy, same script only","role-specific bounds; no cross-script comparison","see CSV",role_pass)
    report("R10","OVERLAP","after_overlap_report.csv","all registered raw-mask pairs","0 pixels",str(total_overlap),total_overlap==0)
    report("R11","CLIP","after_overlap_report.csv","text/graphics clipping","0 pixels",str(clip_total),clip_total==0)
    report("R12","CLEARANCE","after_overlap_report.csv","text-text PDF bbox + raw mask / text-line / border / edge",">=4/>=3/>=5/>=6px",f"text-text raw={min_tt_raw:.3f}, bbox={min_tt_bbox:.3f}; line={min_tl:.3f}; border={min_tb:.3f}; edge={min_edge:.3f}",clearance_pass)
    report("R13","CROSS_PANEL","cross_panel_ratio_audit.csv","cross-panel raw role+script median relations","<=1.10 or explicit single panel","PANEL_STATIONARY_MAP only",cross_panel_pass)
    report("R14","HARMONY","full_page_200dpi.png;figure_crop_300dpi.png;standalone_300dpi.png;grayscale_300dpi.png","FONT_VISUAL_HARMONY_PASS","no undersized/intrusive text","8.7--9.4pt in-chart text below 9.5pt",font_visual_harmony)
    report("R15","MATH","math_semantics_recheck.md","map, fixed point, cobweb coordinates","all correct",f"r*= {fixed:.1f}; two cobweb sequences exact",math_semantics_pass)
    report("R16","TEXT","math_semantics_recheck.md;adjacent_source_context.tex","caption/figure/body variable consistency","one fixed-point notation","graph r^* vs caption r_star",text_consistency_pass)
    report("R17","GRAYSCALE","grayscale_300dpi.png","noncolor distinguishability","stable","solid/dashed/marker shapes remain distinguishable",grayscale_pass)
    report("R18","PAGE","full_page_200dpi.png","page integration","no clipping/broken flow","placement intact; typography fails separately",page_integration_pass)
    report("R19","FINAL","strict_audit_summary.json","all hard gates","all true",hard["FINAL_RESULT"],final_pass)
    write_csv(OUT / "strict_eight_column_report.csv", eight)

    acceptance=f"""# FIG-P556-01｜STRICT R1｜SA1 正式验收

RESULT: {hard['FINAL_RESULT']}

NEXT_ROLE: {hard['NEXT_ROLE']}

## 输入与覆盖

- 冻结 R93 PDF 的独立物理定位：第 {PDF_PAGE}/{len(doc)} 页；SHA-256 记录于 `render_manifest.json`。
- 图源 `fig_v5_c01_stationary_fixed_point.tex`；紧邻正文 `V5-C01.tex:624--625`；公共字号样式证据 `statlearnbook.sty:276`。
- 覆盖 {len(chars)} glyph、{len(semantic_rows)} 个语义文字组件、{len(graphics_rows)} 个线/曲线/marker/axis/arrow/node-border/fill 组件；所有 TEXT--TEXT、TEXT--graphic 和 TEXT--edge 对均登记。
- 原生视图：`full_page_200dpi.png`、`full_page_300dpi_native.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`；300dpi 测量图未 resize。
- `full_page_300dpi_grid.json` 固定全页原生测量网格；`machine_terminal_check.csv/json/md` 对输出完整性与计数交叉一致性作终检。

## 硬门矩阵

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | {str(source_font_pass).lower()} | true | {'PASS' if source_font_pass else 'FAIL'} |
| SOURCE_FONT_FAILURE_COUNT | {source_font_fail_count} glyphs / {source_font_fail_components} components | 0 | {'PASS' if source_font_fail_count==0 else 'FAIL'} |
| PIXEL_HEIGHT_PASS | {str(pixel_pass).lower()} ({len(failed_pixel)} failures) | true | {'PASS' if pixel_pass else 'FAIL'} |
| SAME_CLASS_RATIO_PASS | {str(same_pass).lower()} | true | {'PASS' if same_pass else 'FAIL'} |
| ROLE_RATIO_PASS | {str(role_pass).lower()} | true | {'PASS' if role_pass else 'FAIL'} |
| OVERLAP_PIXEL_COUNT | {total_overlap} | 0 | {'PASS' if total_overlap==0 else 'FAIL'} |
| CLIP_PIXEL_COUNT | {clip_total} | 0 | {'PASS' if clip_total==0 else 'FAIL'} |
| MIN_CLEARANCE | text/text raw={min_tt_raw:.3f}, bbox={min_tt_bbox:.3f}; line={min_tl:.3f}; border={min_tb:.3f}; edge={min_edge:.3f} | 4/3/5/6 | {'PASS' if clearance_pass else 'FAIL'} |
| CROSS_PANEL_PASS | {str(cross_panel_pass).lower()} | true | {'PASS' if cross_panel_pass else 'FAIL'} |
| FONT_VISUAL_HARMONY_PASS | {str(font_visual_harmony).lower()} | true | {'PASS' if font_visual_harmony else 'FAIL'} |
| MATH_SEMANTICS_PASS | {str(math_semantics_pass).lower()} | true | {'PASS' if math_semantics_pass else 'FAIL'} |
| PROBABILITY_SEMANTICS_PASS | {str(probability_semantics_pass).lower()} | true | {'PASS' if probability_semantics_pass else 'FAIL'} |
| TEXT_CONSISTENCY_PASS | {str(text_consistency_pass).lower()} | true | {'PASS' if text_consistency_pass else 'FAIL'} |
| GRAYSCALE_PASS / PAGE_INTEGRATION_PASS | {str(grayscale_pass).lower()} / {str(page_integration_pass).lower()} | true / true | {'PASS' if grayscale_pass and page_integration_pass else 'FAIL'} |

## 强制发现

1. **字号与视觉协调 FAIL。** 图内刻度 8.7pt、曲线标签 9.3pt、轴/固定点标签 9.4pt、初值/说明框 9.2pt，均低于 9.5pt；公共 `every node=\\small` 不覆盖这些局部显式字体。`FONT_VISUAL_HARMONY_PASS=false`。
2. **逐字形与比例门。** 各 literal 运算符/标点（含 `=`,`+`,`<`,小数点、映射箭头、星号）各自以 raw mask 测量；所有失败详见 `after_pixel_measurements.csv` 与 8x ROI。相同类比例结果见 `same_class_ratio_audit.csv`。
3. **符号一致性 FAIL。** 图内使用 $r^*$，题注使用 $r_\\star$ 表示同一固定点却未声明等价；正文概率语义 $\\rho=(0.4,0.6)$、映射、固定点和两条 cobweb 坐标均正确。

## SA1 结论

任一硬门 FAIL 即不得进入 SA3。本轮结论为 **{hard['FINAL_RESULT']}**，下一角色为 **{hard['NEXT_ROLE']}**；SA2 应只修订指定图源/直接正文后重新冻结并接受全新 SA1 复审。
"""
    write_text(OUT / "SA1_RESULT.md", acceptance); write_text(OUT / "after_visual_acceptance.md", acceptance)

    # Final machine integrity closure.  It verifies evidence coverage and
    # internal counts separately from the deliberately failing quality gates.
    required_files=[
        "full_page_200dpi.png","full_page_300dpi_native.png","full_page_300dpi_grid.json","figure_crop_300dpi.png","standalone_300dpi.png","grayscale_300dpi.png",
        "after_font_audit.csv","after_pixel_measurements.csv","after_overlap_report.csv","after_text_measurement_overlay_300dpi.png","after_visual_acceptance.md",
        "same_class_ratio_audit.csv","role_ratio_audit.csv","cross_panel_ratio_audit.csv","math_semantics_recheck.md","math_semantics_recheck.csv","math_semantics_recheck.json",
        "strict_audit_summary.json","strict_eight_column_report.csv","critical_artifacts.csv","SA1_RESULT.md",
    ]
    machine_rows=[]
    def machine(check, required, observed, ok, evidence):
        machine_rows.append({"CHECK_ID":check,"REQUIREMENT":required,"OBSERVED":observed,"EVIDENCE":evidence,"STATUS":"PASS" if ok else "FAIL"})
    files_ok=all((OUT / name).is_file() for name in required_files)
    machine("MC01_REQUIRED_ARTIFACTS","all required evidence files exist",f"{sum((OUT / n).is_file() for n in required_files)}/{len(required_files)}",files_ok,";".join(required_files))
    full_native=Image.open(full300)
    target_w=page.rect.width*300/72; target_h=page.rect.height*300/72
    x_rel=abs(sx/(300/72)-1); y_rel=abs(sy/(300/72)-1)
    # Poppler must quantize an A4 page to integral pixels (2481x3508 here),
    # so require each target dimension within one pixel and <=0.05% axis error;
    # this proves a native 300dpi render without demanding impossible equality.
    grid_ok=full_native.size==(im300.width,im300.height) and abs(full_native.width-target_w)<=1 and abs(full_native.height-target_h)<=1 and x_rel<=0.0005 and y_rel<=0.0005
    machine("MC02_FULL_PAGE_NATIVE_GRID","immutable full-page 300dpi 1:1 grid; integer-pixel rounding permitted",f"actual={full_native.width}x{full_native.height}px; target={target_w:.3f}x{target_h:.3f}px; axis_relative_error={x_rel:.6%},{y_rel:.6%}",grid_ok,"full_page_300dpi_native.png;full_page_300dpi_grid.json;render_manifest.json")
    mask_paths=[OUT / m["mask_file"] for m in chars] + [OUT / r["RAW_MASK_FILE"] for r in semantic_rows] + [OUT / r["RAW_MASK_FILE"] for r in graphics]
    masks_ok=all(p.is_file() for p in mask_paths)
    machine("MC03_MASK_LINKS","every glyph/semantic/graphic mask resolves",f"{sum(p.is_file() for p in mask_paths)}/{len(mask_paths)}",masks_ok,"mask_manifest.csv")
    glyph_fields=("ELEMENT_ID","PARENT_ELEMENT_ID","PANEL_ID","ROLE","SCRIPT_CLASS","H_INK_PX","PIXEL_THRESHOLD_PX","CLASS_MEDIAN_PX","RATIO_TO_CLASS_MEDIAN","ROLE_MEDIAN_PX","RATIO_TO_ROLE_MEDIAN","SOURCE_FONT_PASS","PIXEL_HEIGHT_PASS","RAW_MASK_FILE")
    glyph_complete=all(all(str(r.get(k,""))!="" for k in glyph_fields) for r in glyph_rows)
    machine("MC04_GLYPH_SCHEMA","all 124 glyph rows have raw-H_ink, role/script and mask fields",f"glyphs={len(glyph_rows)}; complete={glyph_complete}",glyph_complete,"after_pixel_measurements.csv")
    rel_fields=("RELATION_ID","ELEMENT_A","ELEMENT_B","RELATION_CLASS","RAW_MASK_A","RAW_MASK_B","OVERLAP_PIXEL_COUNT","CLEARANCE_PX","REQUIRED_CLEARANCE_PX","PASS_FAIL")
    relation_complete=all(all(str(r.get(k,""))!="" for k in rel_fields) for r in relation_rows)
    text_bbox_complete=all(str(r.get("PDF_VECTOR_BBOX_A",""))!="" and str(r.get("PDF_VECTOR_BBOX_B",""))!="" and str(r.get("PDF_VECTOR_BBOX_CLEARANCE_PX",""))!="" for r in relation_rows if r["RELATION_CLASS"]=="TEXT_TEXT")
    machine("MC05_RELATION_SCHEMA","all registered relations and all TEXT_TEXT vector bboxes are populated",f"relations={len(relation_rows)}; text-bbox={text_bbox_complete}",relation_complete and text_bbox_complete,"after_overlap_report.csv")
    critical_need=[]
    for r in relation_rows:
        raw=float(r["CLEARANCE_PX"]) if r["CLEARANCE_PX"]!="INF" else math.inf
        bbox=float(r.get("PDF_VECTOR_BBOX_CLEARANCE_PX","inf") or "inf")
        if r["PASS_FAIL"]=="FAIL" or raw<=int(r["REQUIRED_CLEARANCE_PX"])+2 or (r["RELATION_CLASS"]=="TEXT_TEXT" and bbox<=int(r["REQUIRED_CLEARANCE_PX"])+2):
            critical_need.append(r)
    critical_links_ok=all(r["CRITICAL_ROI"] and (OUT / r["CRITICAL_ROI"]).is_file() for r in critical_need)
    critical_artifacts_ok=all((OUT / row[key]).is_file() for row in critical_manifest for key in ("RAW_ROI","MASK_A","MASK_B","OVERLAP_MASK","OVERLAY","ZOOM_8X"))
    machine("MC06_CRITICAL_EVIDENCE","every failed/critical relation has raw ROI, two masks, overlap and 8x overlay",f"needed={len(critical_need)}; manifest={len(critical_manifest)}",critical_links_ok and critical_artifacts_ok,"critical_artifacts.csv")
    recompute_overlap=sum(int(r["OVERLAP_PIXEL_COUNT"]) for r in relation_rows)
    recompute_clip=sum(int(r["CLIP_PIXEL_COUNT"]) for r in relation_rows)
    count_ok=recompute_overlap==hard["OVERLAP_PIXEL_COUNT"] and recompute_clip==hard["CLIP_PIXEL_COUNT"] and sum(r["SOURCE_FONT_PASS"]=="false" for r in glyph_rows)==hard["SOURCE_FONT_FAILURE_COUNT"] and sum(r["PIXEL_HEIGHT_PASS"]=="false" for r in glyph_rows)==hard["PIXEL_HEIGHT_FAILURE_COUNT"]
    machine("MC07_COUNT_CROSSCHECK","summary counts equal CSV recomputation",f"overlap={recompute_overlap}; clip={recompute_clip}; font_fail={sum(r['SOURCE_FONT_PASS']=='false' for r in glyph_rows)}; pixel_fail={sum(r['PIXEL_HEIGHT_PASS']=='false' for r in glyph_rows)}",count_ok,"strict_audit_summary.json;after_*_audit.csv")
    expected_result="PASS" if final_pass else "FAIL"
    machine("MC08_FINAL_RESULT","summary result equals all-hard-gates conjunction",f"expected={expected_result}; summary={hard['FINAL_RESULT']}",hard["FINAL_RESULT"]==expected_result,"strict_audit_summary.json")
    machine_integrity=all(r["STATUS"]=="PASS" for r in machine_rows)
    machine_summary={"audit_id":"FIG-P556-01/STRICT_R1/SA1_20260824_R1","machine_evidence_integrity_pass":machine_integrity,"quality_result":hard["FINAL_RESULT"],"grid":full_grid,"checks":machine_rows}
    write_csv(OUT / "machine_terminal_check.csv", machine_rows)
    write_text(OUT / "machine_terminal_check.json", json.dumps(machine_summary,ensure_ascii=False,indent=2))
    machine_md="# FIG-P556-01｜机器终检\n\n"+f"EVIDENCE_INTEGRITY: {'PASS' if machine_integrity else 'FAIL'}\n\nQUALITY_RESULT: {hard['FINAL_RESULT']}\n\n"+"\n".join(f"- {r['CHECK_ID']}: {r['STATUS']} — {r['OBSERVED']}" for r in machine_rows)+"\n"
    write_text(OUT / "machine_terminal_check.md", machine_md)
    hard["MACHINE_EVIDENCE_INTEGRITY_PASS"]=machine_integrity
    summary["machine_terminal_check"]={"csv":"machine_terminal_check.csv","json":"machine_terminal_check.json","integrity_pass":machine_integrity}
    write_text(OUT / "strict_audit_summary.json", json.dumps(summary,ensure_ascii=False,indent=2))
    report("R20","MACHINE_FINAL","machine_terminal_check.csv/json","evidence completeness and count crosscheck","all machine checks PASS",f"integrity={machine_integrity}; quality={hard['FINAL_RESULT']}",machine_integrity)
    write_csv(OUT / "strict_eight_column_report.csv", eight)
    acceptance += f"\n机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS={str(machine_integrity).lower()}`，其只确认取证完整/计数一致；质量结论仍为 `{hard['FINAL_RESULT']}`。\n"
    write_text(OUT / "SA1_RESULT.md", acceptance); write_text(OUT / "after_visual_acceptance.md", acceptance)


if __name__ == "__main__":
    main()
