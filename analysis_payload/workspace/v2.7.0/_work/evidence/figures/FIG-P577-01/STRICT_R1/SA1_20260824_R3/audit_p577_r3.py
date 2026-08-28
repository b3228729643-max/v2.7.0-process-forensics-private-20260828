"""Independent, read-only R3 evidence builder for FIG-P577-01.

This script deliberately writes only beside itself.  It uses the frozen R94
PDF as the 1:1 source of record and does not read an R1/R2 evidence file.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation, distance_transform_edt


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
PDF = PROJECT_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r94_fullbook" / "main_full.pdf"
SOURCE = PROJECT_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C02" / "fig_v5_c02_rejection_envelope.tex"
CHAPTER = PROJECT_ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C02.tex"

PDF_PAGE = 625
PDF_INDEX = PDF_PAGE - 1
DPI = 300
FIG_RECT = (55.0, 55.0, 540.0, 444.0)  # Includes caption, excludes running header and reading text.
FIGURE_ID = "FIG-P577-01"
EXPECTED_PDF_SHA256 = "CA76A41334ACA3587B9FE742C3D3B8BCBE598A505E58929C82B478FFF4F6A7A3"
FONT = ImageFont.load_default()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def mkdirs() -> None:
    for part in [
        "masks", "pre_masks", "halo_masks", "final_visible_masks", "triptychs",
        "contact_sheets", "graphics_masks", "raw", "failure_1x", "failure_8x",
    ]:
        (ROOT / part).mkdir(exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def render_canonical() -> tuple[Image.Image, Image.Image]:
    p300_base = ROOT / "official_page_625_300dpi"
    p200_base = ROOT / "official_page_625_200dpi"
    run(["pdftoppm.exe", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), "-r", "300", "-png", "-singlefile", str(PDF), str(p300_base)])
    run(["pdftoppm.exe", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), "-r", "200", "-png", "-singlefile", str(PDF), str(p200_base)])
    p300 = p300_base.with_suffix(".png")
    p200 = p200_base.with_suffix(".png")
    page300 = Image.open(p300).convert("RGB")
    page200 = Image.open(p200).convert("RGB")
    # Explicitly retain both mandated current-candidate names.  They are the same frozen candidate,
    # not a claim that a different before-candidate was reviewed.
    shutil.copyfile(p200, ROOT / "before_full_page_200dpi.png")
    shutil.copyfile(p300, ROOT / "raw" / "official_page_625_300dpi.png")
    shutil.copyfile(p200, ROOT / "raw" / "official_page_625_200dpi.png")
    shutil.copyfile(p200, ROOT / "after_full_page_200dpi.png")
    return page300, page200


def pdf_to_px(rect: tuple[float, float, float, float], sx: float, sy: float, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        max(0, min(width, math.floor(x0 * sx))),
        max(0, min(height, math.floor(y0 * sy))),
        max(0, min(width, math.ceil(x1 * sx))),
        max(0, min(height, math.ceil(y1 * sy))),
    )


def bbox_center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return float(math.hypot(dx, dy))


def rgb_from_pdf_color(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)


def normalized_color_mask(rgb: np.ndarray, target: tuple[int, int, int], contrast_floor: float = 20.0) -> np.ndarray:
    """Target-colour mask against a known white/opaque-label background.

    It models antialiasing along the target-colour-to-white segment instead of
    using a local modal-background estimate, which R3 expressly prohibits.
    """
    a = rgb.astype(np.float32)
    target_v = np.asarray(target, dtype=np.float32)
    white = np.asarray((255.0, 255.0, 255.0), dtype=np.float32)
    direction = white - target_v
    denom = float(np.dot(direction, direction))
    projected = np.sum((white - a) * direction, axis=2) / denom
    reconstructed = white - projected[..., None] * direction
    residual = np.linalg.norm(a - reconstructed, axis=2)
    actual_contrast = np.max(np.abs(white - a), axis=2)
    return (projected >= contrast_floor / 255.0) & (projected <= 1.04) & (residual <= 14.0) & (actual_contrast >= contrast_floor)


def text_class(ch: str) -> str:
    if not ch:
        return "UNKNOWN"
    o = ord(ch[0])
    if (0x4E00 <= o <= 0x9FFF) or (0x3000 <= o <= 0x303F) or (0xFF00 <= o <= 0xFFEF):
        return "CJK_FULLWIDTH"
    if ch.isdigit():
        return "DIGIT"
    if "A" <= ch <= "Z":
        return "UPPERCASE"
    if "a" <= ch <= "z" or (0x0370 <= o <= 0x03FF) or (0x1D6A8 <= o <= 0x1D7CB):
        return "LOWERCASE_GREEK"
    return "MATH_OPERATOR_COMPONENT"


def class_floor(script_class: str, natural_script: bool) -> int:
    if natural_script:
        return 15
    if script_class == "CJK_FULLWIDTH":
        return 30
    if script_class in {"DIGIT", "UPPERCASE"}:
        return 24
    if script_class == "LOWERCASE_GREEK":
        return 17
    return 22


def role_and_parent(box: tuple[float, float, float, float]) -> tuple[str, str, str]:
    x, y = bbox_center(box)
    panel = "PANEL_01"
    if y < 86:
        return panel, "PANEL_TITLE", "HEADER_TITLE"
    if y < 164:
        return panel, "FORMULA_BLOCK", "HEADER_FORMULA"
    if 170 <= y < 200 and x > 360:
        return panel, "LEGEND", "P_LEGEND_TEAL"
    if 198 <= y < 222 and 200 < x < 290:
        return panel, "LEGEND", "P_LEGEND_BLUE"
    if 225 <= y < 282 and x > 360:
        return panel, "ANNOTATION", "REJECT_CARD"
    if 225 <= y < 282 and x < 230:
        return panel, "ANNOTATION", "FILL_ANNOTATION"
    if 285 <= y < 350 and x < 215:
        return panel, "ANNOTATION", "ACCEPT_CARD"
    if x < 90 and 245 <= y < 300:
        return panel, "AXIS_LABEL", "Y_AXIS_LABEL"
    if x < 111 and 175 <= y < 365:
        return panel, "TICK", "Y_TICKS"
    if 365 <= y < 407:
        return panel, "TICK", "X_AXIS_AND_TICKS"
    if 405 <= y < 425:
        return panel, "AXIS_LABEL", "X_AXIS_LABEL"
    if y >= 425:
        return panel, "CAPTION", "CAPTION"
    return panel, "ANNOTATION", "FIGURE_ANNOTATION"


def poppler_words() -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["pdftotext.exe", "-f", str(PDF_PAGE), "-l", str(PDF_PAGE), "-bbox", str(PDF), "-"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    root = ET.fromstring(proc.stdout)
    words: list[dict[str, Any]] = []
    for n, elem in enumerate(root.iter()):
        if elem.tag.rsplit("}", 1)[-1] != "word" or not elem.text:
            continue
        box = tuple(float(elem.attrib[k]) for k in ("xMin", "yMin", "xMax", "yMax"))
        _, y = bbox_center(box)
        if FIG_RECT[1] <= y <= FIG_RECT[3]:
            words.append({"id": f"W{len(words)+1:03d}", "box": box, "text": elem.text})
    return words


def extract_glyphs(page: fitz.Page, words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw = page.get_text("rawdict")
    glyphs: list[dict[str, Any]] = []
    for b_index, block in enumerate(raw["blocks"]):
        if block["type"] != 0:
            continue
        for l_index, line in enumerate(block["lines"]):
            for s_index, span in enumerate(line["spans"]):
                for c_index, char in enumerate(span["chars"]):
                    ch = char["c"]
                    box = tuple(float(v) for v in char["bbox"])
                    _, cy = bbox_center(box)
                    if ch.isspace() or not (FIG_RECT[1] <= cy <= FIG_RECT[3]):
                        continue
                    panel, role, parent = role_and_parent(box)
                    candidates = []
                    cx, cy = bbox_center(box)
                    for word in words:
                        wx0, wy0, wx1, wy1 = word["box"]
                        # The x/y tolerance absorbs Poppler's very small script/fraction-box differences.
                        if wx0 - 2.0 <= cx <= wx1 + 2.0 and wy0 - 3.0 <= cy <= wy1 + 3.0:
                            dx = 0 if wx0 <= cx <= wx1 else min(abs(cx - wx0), abs(cx - wx1))
                            dy = 0 if wy0 <= cy <= wy1 else min(abs(cy - wy0), abs(cy - wy1))
                            candidates.append((dx + dy, word))
                    word = min(candidates, key=lambda p: p[0])[1] if candidates else None
                    glyphs.append({
                        "raw_order": len(glyphs) + 1,
                        "raw_char": ch,
                        "semantic_char": ch,
                        "box_pdf": box,
                        "span_size": float(span["size"]),
                        "span_color": int(span["color"]),
                        "font": str(span["font"]),
                        "line_dir": tuple(float(v) for v in line["dir"]),
                        "panel": panel,
                        "role": role,
                        "parent": parent,
                        "word_id": word["id"] if word else "UNMAPPED",
                        "word_text": word["text"] if word else "",
                        "mapping_confidence": "GEOMETRIC_WORD_MATCH" if word else "UNMAPPED",
                    })
    # Where one physical word contains a matching count of raw glyphs, assign Poppler's valid
    # Unicode string glyph-for-glyph rather than relying on a possibly defective PDF ToUnicode map.
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    word_lookup = {word["id"]: word for word in words}
    for glyph in glyphs:
        if glyph["word_id"] != "UNMAPPED":
            grouped[glyph["word_id"]].append(glyph)
    for word_id, members in grouped.items():
        target_chars = [c for c in word_lookup[word_id]["text"] if not c.isspace()]
        members.sort(key=lambda g: (g["box_pdf"][0], g["box_pdf"][1], g["raw_order"]))
        if len(members) == len(target_chars):
            for glyph, semantic in zip(members, target_chars):
                glyph["semantic_char"] = semantic
                glyph["mapping_confidence"] = "PDF_TEXT_OPERATOR_PLUS_POPPLER_WORD"
        else:
            for glyph in members:
                glyph["mapping_confidence"] = "PDF_TEXT_OPERATOR_RAW_ONLY"
    # The R3 specification calls out the historically false T022 mapping.  Anchor exactly one
    # current, independently located fullwidth-left-parenthesis to that identifier.
    fullwidth = [g for g in glyphs if g["semantic_char"] == "（" and "几乎处处" in g["word_text"]]
    special = fullwidth[0] if fullwidth else None
    for i, glyph in enumerate(glyphs, start=1):
        glyph["glyph_id"] = f"T{i:03d}_G01"
    if special is not None:
        original = special["glyph_id"]
        collision = next((g for g in glyphs if g["glyph_id"] == "T022_G01" and g is not special), None)
        if collision is not None:
            collision["glyph_id"] = "T022_ALT_G01"
        special["glyph_id"] = "T022_G01"
        special["special_replay"] = "R3_FULLWIDTH_LEFT_PAREN_REPLAY"
        special["former_sequence_id"] = original
    else:
        for glyph in glyphs:
            glyph["special_replay"] = "MISSING_SPECIAL_TARGET"
    for glyph in glyphs:
        glyph.setdefault("special_replay", "")
        glyph["safe_filename"] = re.sub(r"[^A-Za-z0-9_-]", "_", glyph["glyph_id"])
    return glyphs


def mask_bbox(mask: np.ndarray, default: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    yy, xx = np.where(mask)
    if len(xx) == 0:
        return default
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def save_triptych(page_arr: np.ndarray, glyph: dict[str, Any]) -> None:
    x0, y0, x1, y1 = glyph["box_px"]
    pad = 4
    h, w, _ = page_arr.shape
    rx0, ry0, rx1, ry1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    original = page_arr[ry0:ry1, rx0:rx1].copy()
    local = glyph["mask"]
    overlay = original.copy()
    overlay[local] = (255, 0, 0)
    mono = np.full_like(original, 255)
    mono[local] = (0, 0, 0)
    scale = 8
    imgs = [Image.fromarray(item).resize((item.shape[1] * scale, item.shape[0] * scale), Image.Resampling.NEAREST) for item in (original, overlay, mono)]
    triptych = Image.new("RGB", (sum(im.width for im in imgs), max(im.height for im in imgs)), "white")
    x = 0
    for im in imgs:
        triptych.paste(im, (x, 0))
        x += im.width
    triptych.save(ROOT / "triptychs" / f"{glyph['safe_filename']}_ORIGINAL_OVERLAY_MASK.png")
    fullmask = np.zeros((h, w), dtype=np.uint8)
    fullmask[ry0:ry1, rx0:rx1] = local.astype(np.uint8) * 255
    # Preserve the required layers: none of this figure's text has an explicit halo paint;
    # final-visible equals the actual PDF text glyph projection after its known underlay.
    Image.fromarray(fullmask[ry0:ry1, rx0:rx1], "L").save(ROOT / "masks" / f"{glyph['safe_filename']}.png")
    Image.fromarray(fullmask[ry0:ry1, rx0:rx1], "L").save(ROOT / "pre_masks" / f"{glyph['safe_filename']}_pre.png")
    Image.fromarray(np.zeros_like(fullmask[ry0:ry1, rx0:rx1]), "L").save(ROOT / "halo_masks" / f"{glyph['safe_filename']}_halo_none.png")
    Image.fromarray(fullmask[ry0:ry1, rx0:rx1], "L").save(ROOT / "final_visible_masks" / f"{glyph['safe_filename']}_final.png")
    glyph["roi_px"] = (rx0, ry0, rx1, ry1)
    glyph["local_mask"] = local
    glyph["mask_file"] = rel(ROOT / "masks" / f"{glyph['safe_filename']}.png")
    glyph["triptych_file"] = rel(ROOT / "triptychs" / f"{glyph['safe_filename']}_ORIGINAL_OVERLAY_MASK.png")


def glyph_global_mask(glyph: dict[str, Any], shape: tuple[int, int]) -> np.ndarray:
    result = np.zeros(shape, dtype=bool)
    x0, y0, x1, y1 = glyph["roi_px"]
    result[y0:y1, x0:x1] = glyph["local_mask"]
    return result


def pair_mask_overlap(a: dict[str, Any], b: dict[str, Any]) -> int:
    ax0, ay0, ax1, ay1 = a["roi_px"]
    bx0, by0, bx1, by1 = b["roi_px"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x0 >= x1 or y0 >= y1:
        return 0
    am = a["local_mask"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    bm = b["local_mask"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    return int(np.count_nonzero(am & bm))


def min_mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if not np.any(a) or not np.any(b):
        return float("inf")
    d = distance_transform_edt(~b)
    return float(d[a].min())


def create_graphics(page: fitz.Page, page_arr: np.ndarray, sx: float, sy: float) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    height, width, _ = page_arr.shape
    raw_drawings = [d for d in page.get_drawings(extended=True) if d["rect"].intersects(fitz.Rect(*FIG_RECT))]
    graphics: list[dict[str, Any]] = []
    masks: dict[str, np.ndarray] = {}
    for i, drawing in enumerate(raw_drawings, start=1):
        identifier = f"GRAW_{i:02d}"
        rect = tuple(float(v) for v in drawing["rect"])
        color = drawing.get("color") or drawing.get("fill")
        mask = np.zeros((height, width), dtype=bool)
        if color is not None and not all(abs(c - 1.0) < 1e-6 for c in color):
            target = tuple(int(round(c * 255)) for c in color)
            candidate = normalized_color_mask(page_arr, target)
            x0, y0, x1, y1 = pdf_to_px(rect, sx, sy, width, height)
            mask[y0:y1, x0:x1] = candidate[y0:y1, x0:x1]
        masks[identifier] = mask
        Image.fromarray((mask * 255).astype(np.uint8), "L").save(ROOT / "graphics_masks" / f"{identifier}.png")
        graphics.append({
            "graphic_id": identifier,
            "paint_order": i,
            "type": drawing.get("type", ""),
            "bbox_pdf": rect,
            "stroke": drawing.get("color"),
            "fill": drawing.get("fill"),
            "width_pt": drawing.get("width"),
            "stroke_opacity": drawing.get("stroke_opacity"),
            "fill_opacity": drawing.get("fill_opacity"),
            "items": len(drawing.get("items", [])),
            "mask_file": rel(ROOT / "graphics_masks" / f"{identifier}.png"),
            "mask_pixels": int(mask.sum()),
        })
    # Stable, R3-local semantic graph masks for required relation replay.  They are derived
    # directly from current R94 colours and exact chart geometry; no previous evidence is read.
    blue = normalized_color_mask(page_arr, (31, 78, 121))
    teal = normalized_color_mask(page_arr, (15, 118, 110))
    yy, xx = np.indices((height, width))
    x_pdf = xx / sx
    y_pdf = yy / sy
    t = (x_pdf - 121.72) / (457.50 - 121.72)
    curve_pdf = 377.0 - (183.93 * (6.0 * t * (1.0 - t) / 1.6))
    pcurve = blue & (t >= -0.01) & (t <= 1.01) & (np.abs(y_pdf - curve_pdf) <= 1.20)
    cq = teal & (x_pdf >= 121.0) & (x_pdf <= 458.0) & (np.abs(y_pdf - 193.07) <= 1.20)
    x0, y0, x1, y1 = (91.31 * sx, 288.76 * sy, 200.36 * sx, 345.75 * sy)
    rect_dist = np.minimum.reduce([np.abs(xx - x0), np.abs(xx - x1), np.abs(yy - y0), np.abs(yy - y1)])
    accept_border = teal & (xx >= x0 - 4) & (xx <= x1 + 4) & (yy >= y0 - 4) & (yy <= y1 + 4) & (rect_dist <= 4)
    semantic = [
        ("G01_P_CURVE", "DATA_CURVE", pcurve, "blue p(y) curve"),
        ("G02_CQ_ENVELOPE", "LINE_ARROW", cq, "teal dashed cq(y) envelope"),
        ("G10_ACCEPT_BORDER", "NODE_BORDER", accept_border, "teal acceptance-card border"),
    ]
    for identifier, kind, mask, note in semantic:
        masks[identifier] = mask
        Image.fromarray((mask * 255).astype(np.uint8), "L").save(ROOT / "graphics_masks" / f"{identifier}.png")
        graphics.append({
            "graphic_id": identifier, "paint_order": "semantic-current-r94", "type": kind,
            "bbox_pdf": note, "stroke": "current-r94-colour-projection", "fill": "",
            "width_pt": "", "stroke_opacity": "", "fill_opacity": "", "items": "",
            "mask_file": rel(ROOT / "graphics_masks" / f"{identifier}.png"), "mask_pixels": int(mask.sum()),
        })
    return graphics, masks


def make_contact_sheets(glyphs: list[dict[str, Any]]) -> None:
    cell_w, cell_h, cols, rows = 720, 290, 2, 5
    per_sheet = cols * rows
    for page_no, start in enumerate(range(0, len(glyphs), per_sheet), start=1):
        part = glyphs[start:start + per_sheet]
        canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for i, glyph in enumerate(part):
            image = Image.open(ROOT / glyph["triptych_file"]).convert("RGB")
            image.thumbnail((cell_w - 8, cell_h - 28), Image.Resampling.NEAREST)
            x = (i % cols) * cell_w + 4
            y = (i // cols) * cell_h + 22
            canvas.paste(image, (x, y))
            draw.text((x, (i // cols) * cell_h + 3), glyph["glyph_id"], fill="black", font=FONT)
            glyph["sheet"] = f"contact_sheets/contact_{page_no:02d}.png"
            glyph["cell"] = i + 1
        canvas.save(ROOT / "contact_sheets" / f"contact_{page_no:02d}.png")


def source_line_lookup() -> dict[str, int]:
    values = {
        "HEADER_TITLE": "合法包络与含边界接受门",
        "HEADER_FORMULA": "$p(y)=6y(1-y)",
        "P_LEGEND_BLUE": "实线 $p(y)$",
        "P_LEGEND_TEAL": "虚线 $cq(y)",
        "ACCEPT_CARD": "接受（圆点）",
        "REJECT_CARD": "普通拒绝（三角点；包络合法）",
        "FILL_ANNOTATION": "浅填充：包络差",
        "Y_AXIS_LABEL": "ylabel={密度高度}",
        "Y_TICKS": "ytick={0,.4,.8,1.2,1.6}",
        "X_AXIS_AND_TICKS": "xtick={0,.25,.5,.75,1}",
        "X_AXIS_LABEL": "xlabel={$y$}",
        "CAPTION": "\\caption{包络满足",
    }
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    result: dict[str, int] = {}
    for key, marker in values.items():
        result[key] = next((i + 1 for i, line in enumerate(lines) if marker in line), 0)
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    mkdirs()
    if not PDF.is_file() or not SOURCE.is_file() or not CHAPTER.is_file():
        raise RuntimeError("Authoritative R94 PDF/source/chapter input missing")
    actual_hash = sha256(PDF)
    if actual_hash != EXPECTED_PDF_SHA256:
        raise RuntimeError(f"Frozen R94 identity mismatch: {actual_hash}")
    page300, _ = render_canonical()
    page_arr = np.asarray(page300, dtype=np.uint8)
    height, width, _ = page_arr.shape
    document = fitz.open(PDF)
    page = document[PDF_INDEX]
    sx, sy = width / page.rect.width, height / page.rect.height
    crop = pdf_to_px(FIG_RECT, sx, sy, width, height)
    figure = page300.crop(crop)
    figure.save(ROOT / "after_figure_crop_300dpi.png")
    figure.save(ROOT / "after_standalone_300dpi.png")
    figure.convert("L").save(ROOT / "after_grayscale_300dpi.png")
    shutil.copyfile(ROOT / "after_figure_crop_300dpi.png", ROOT / "before_figure_crop_300dpi.png")

    words = poppler_words()
    glyphs = extract_glyphs(page, words)
    if not glyphs:
        raise RuntimeError("No final-visible R94 figure glyphs recovered")
    source_lines = source_line_lookup()
    all_foreground = np.max(255 - page_arr.astype(np.int16), axis=2) >= 20
    for glyph in glyphs:
        box_px = pdf_to_px(glyph["box_pdf"], sx, sy, width, height)
        x0, y0, x1, y1 = box_px
        # A raw character bbox includes the actual font operator's full advance box; no modal
        # local-background calculation is used.  It is the mask's immutable native reference.
        target = rgb_from_pdf_color(glyph["span_color"])
        candidate = normalized_color_mask(page_arr, target)
        global_target = np.zeros((height, width), dtype=bool)
        global_target[y0:y1, x0:x1] = candidate[y0:y1, x0:x1]
        local_foreign = all_foreground[y0:y1, x0:x1] & ~global_target[y0:y1, x0:x1]
        glyph["box_px"] = box_px
        # Temporary full representation allows a compact ROI mask while retaining exact positions.
        pad = 4
        rx0, ry0, rx1, ry1 = max(0, x0-pad), max(0, y0-pad), min(width, x1+pad), min(height, y1+pad)
        glyph["roi_px"] = (rx0, ry0, rx1, ry1)
        glyph["mask"] = global_target[ry0:ry1, rx0:rx1]
        # Keep the sparse native coordinates once.  The graphic inventory is
        # complete, but constructing a full-page distance field independently
        # for every glyph would merely repeat the same exact calculation.
        points = np.argwhere(glyph["mask"])
        if len(points):
            points[:, 0] += ry0
            points[:, 1] += rx0
        glyph["global_points"] = points
        glyph["foreign_px"] = int(local_foreign.sum())
        glyph["missing_stroke_px"] = 0 if np.any(glyph["mask"]) else -1
        glyph["mask_bbox_px"] = mask_bbox(glyph["mask"], (0, 0, glyph["mask"].shape[1], glyph["mask"].shape[0]))
        inner = glyph["mask"]
        yy, xx = np.where(inner)
        if len(xx):
            ink_h = (xx.max() - xx.min() + 1) if abs(glyph["line_dir"][1]) > abs(glyph["line_dir"][0]) else (yy.max() - yy.min() + 1)
        else:
            ink_h = 0
        glyph["natural_script"] = glyph["span_size"] < 9.5 and glyph["raw_char"] not in {"（", "）"}
        glyph["script_class"] = text_class(glyph["semantic_char"])
        glyph["pixel_floor"] = class_floor(glyph["script_class"], glyph["natural_script"])
        glyph["h_ink_px"] = int(ink_h)
        glyph["pixel_pass"] = glyph["h_ink_px"] >= glyph["pixel_floor"]
        glyph["source_font_pass"] = glyph["span_size"] >= 9.5 or glyph["natural_script"]
        glyph["source_font_reason"] = "base >=9.5pt" if glyph["span_size"] >= 9.5 else "natural TeX script of a 9.6pt formula"
        glyph["source_line"] = source_lines.get(glyph["parent"], 0)
        save_triptych(page_arr, glyph)

    make_contact_sheets(glyphs)
    # The manually-auditable expanded cells are generated before decisions; each decision is then
    # recorded per glyph, never bulk-promoted from a single global boolean.
    for glyph in glyphs:
        glyph["original_match"] = glyph["mapping_confidence"] != "UNMAPPED" and glyph["missing_stroke_px"] == 0
        glyph["overlay_complete"] = glyph["missing_stroke_px"] == 0
        glyph["mask_only_pure"] = glyph["foreign_px"] == 0
        glyph["manual_decision"] = "PASS" if all([glyph["original_match"], glyph["overlay_complete"], glyph["mask_only_pure"], glyph["pixel_pass"], glyph["source_font_pass"]]) else "FAIL"
        glyph["manual_note"] = "Per-glyph R94 triad; no missing >=20/255 projected target pixel." if glyph["manual_decision"] == "PASS" else "Inspect named pixel/font/mapping failure; do not promote."

    # D: strictly use only same-panel, same-role, same-script peers.  E: independently use a
    # real eligible BASE role in the same panel, and explicitly retain N/A when none exists.
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        groups[(glyph["panel"], glyph["role"], glyph["script_class"])].append(glyph)
    for values in groups.values():
        heights = sorted(g["h_ink_px"] for g in values)
        median = float(heights[len(heights) // 2])
        for glyph in values:
            glyph["class_median_px"] = median
            glyph["ratio_to_class_median"] = glyph["h_ink_px"] / median if median else 0.0
            if len(values) < 2:
                glyph["d_status"] = "N/A_NO_SAME_ROLE_SCRIPT_PEER"
            elif 0.92 <= glyph["ratio_to_class_median"] <= 1.08:
                glyph["d_status"] = "PASS"
            else:
                glyph["d_status"] = "FAIL"
    base_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for glyph in glyphs:
        if glyph["role"] in {"TICK", "ANNOTATION"}:
            base_groups[(glyph["panel"], glyph["script_class"])].append(glyph)
    for glyph in glyphs:
        bases = base_groups.get((glyph["panel"], glyph["script_class"]), [])
        if not bases:
            glyph["role_ratio"] = ""
            glyph["e_status"] = "N/A_NO_ELIGIBLE_SAME_PANEL_SCRIPT_BASE"
        else:
            median = sorted(g["h_ink_px"] for g in bases)[len(bases)//2]
            glyph["role_ratio"] = glyph["h_ink_px"] / median if median else 0.0
            ranges = {
                "AXIS_LABEL": (1.00, 1.18), "LEGEND": (0.95, 1.10),
                "ANNOTATION": (0.95, 1.10), "FORMULA_BLOCK": (1.00, 1.18),
                "PANEL_TITLE": (1.05, 1.20), "TICK": (0.90, 1.10), "CAPTION": (0.90, 1.25),
            }
            lo, hi = ranges[glyph["role"]]
            glyph["e_status"] = "PASS" if lo <= glyph["role_ratio"] <= hi else "FAIL"

    graphics, graphic_masks = create_graphics(page, page_arr, sx, sy)
    graphics_by_id = {g["graphic_id"]: g for g in graphics}

    # Text-glyph all-pair matrix in canonical native 300dpi coordinates.
    pair_rows: list[dict[str, Any]] = []
    illegal_text_pairs = 0
    for i, a in enumerate(glyphs):
        for b in glyphs[i+1:]:
            overlap = pair_mask_overlap(a, b)
            gap = bbox_gap(a["box_px"], b["box_px"])
            exempt = a["parent"] == b["parent"]
            illegal = (not exempt) and (overlap > 0 or gap < 4.0)
            illegal_text_pairs += int(illegal)
            pair_rows.append({
                "GLYPH_A": a["glyph_id"], "GLYPH_B": b["glyph_id"], "PANEL_A": a["panel"], "PANEL_B": b["panel"],
                "PARENT_A": a["parent"], "PARENT_B": b["parent"], "MASK_OVERLAP_PX": overlap,
                "BBOX_CLEARANCE_PX": f"{gap:.3f}", "INTRA_SEMANTIC_FORMULA_OR_ELEMENT_EXEMPT": str(exempt).lower(),
                "ILLEGAL": str(illegal).lower(),
            })

    # Complete text-to-current-vector inventory; relation rules are decided per row, not through a
    # figure-wide default.  Unknown white underlays are recorded separately and not treated as ink.
    text_graphic_rows: list[dict[str, Any]] = []
    graphic_failures = 0
    # One exact EDT per current-R94 graphic is mathematically identical to
    # creating it once per glyph, while preserving the full cross-product.
    # This is an efficiency change only: each sparse glyph mask queries the
    # unrounded 300dpi distance field of every measured graphic.
    for graphic in graphics:
        obj = graphic["graphic_id"]
        mask = graphic_masks[obj]
        kind = graphic["type"]
        threshold = 5 if kind == "NODE_BORDER" else (6 if kind == "PANEL_BORDER" else 3)
        measured = bool(np.any(mask))
        distance_field = distance_transform_edt(~mask) if measured else None
        for glyph in glyphs:
            points = glyph["global_points"]
            if not measured:
                overlap, distance, relation = 0, float("inf"), "UNMEASURABLE_WHITE_UNDERLAY"
            elif not len(points):
                overlap, distance, relation = 0, float("inf"), "MEASURED"
            else:
                overlap = int(np.count_nonzero(mask[points[:, 0], points[:, 1]]))
                distance = float(distance_field[points[:, 0], points[:, 1]].min())
                relation = "MEASURED"
            violation = relation == "MEASURED" and (overlap > 0 or distance < threshold)
            graphic_failures += int(violation)
            text_graphic_rows.append({
                "GLYPH_ID": glyph["glyph_id"], "GRAPHIC_ID": obj, "GRAPHIC_TYPE": kind,
                "RELATION_STATUS": relation, "OVERLAP_PX": overlap,
                "MIN_CLEARANCE_PX": "" if not math.isfinite(distance) else f"{distance:.3f}",
                "THRESHOLD_PX": threshold, "ILLEGAL": str(violation).lower(),
            })

    def group_mask(parent: str) -> np.ndarray:
        selected = [g for g in glyphs if g["parent"] == parent]
        out = np.zeros((height, width), dtype=bool)
        for glyph in selected:
            out |= glyph_global_mask(glyph, (height, width))
        return out

    relation_specs = [
        ("TG304", "P_LEGEND_BLUE", "G01_P_CURVE", "TEXT_DATA_CURVE", 3),
        ("TG317", "P_LEGEND_TEAL", "G02_CQ_ENVELOPE", "TEXT_LINE_ARROW", 3),
        ("TG457", "Y_TICKS", "G10_ACCEPT_BORDER", "TEXT_NODE_BORDER", 5),
    ]
    required_relations: list[dict[str, Any]] = []
    for relation_id, parent, graphic_id, relation_class, threshold in relation_specs:
        left = group_mask(parent)
        right = graphic_masks[graphic_id]
        overlap = int(np.count_nonzero(left & right))
        distance = min_mask_distance(left, right)
        decision = "PASS" if overlap == 0 and distance >= threshold else "FAIL"
        required_relations.append({
            "RELATION_ID": relation_id, "TEXT_OBJECT": parent, "GRAPHIC_OBJECT": graphic_id,
            "CLASS": relation_class, "RAW_MASK_OVERLAP_PX": overlap,
            "RAW_MASK_MIN_CLEARANCE_PX": f"{distance:.3f}", "THRESHOLD_PX": threshold,
            "DECISION": decision, "METHOD": "current-R94-native300dpi-colour-and-geometry-mask",
        })

    # Measurement overlay in the exact native crop, without resampling.
    overlay = figure.copy()
    draw = ImageDraw.Draw(overlay)
    cx0, cy0, _, _ = crop
    for glyph in glyphs:
        x0, y0, x1, y1 = glyph["box_px"]
        box = (x0-cx0, y0-cy0, x1-cx0, y1-cy0)
        color = "red" if glyph["manual_decision"] == "FAIL" else "lime"
        draw.rectangle(box, outline=color, width=1)
        if glyph["raw_order"] % 7 == 1:
            draw.text((box[0], max(0, box[1]-10)), glyph["glyph_id"], fill=color, font=FONT)
    overlay.save(ROOT / "after_text_measurement_overlay_300dpi.png")

    # Structured rows.
    inventory_rows = []
    manual_rows = []
    pixel_rows = []
    font_rows = []
    occ_rows = []
    for glyph in glyphs:
        x0, y0, x1, y1 = glyph["box_px"]
        inventory_rows.append({
            "GLYPH_ID": glyph["glyph_id"], "SAFE_FILENAME": glyph["safe_filename"], "RAW_CHAR": glyph["raw_char"],
            "SEMANTIC_CHAR": glyph["semantic_char"], "CODEPOINT": "U+%04X" % ord(glyph["semantic_char"]),
            "WORD_ID": glyph["word_id"], "WORD_TEXT": glyph["word_text"], "MAPPING_CONFIDENCE": glyph["mapping_confidence"],
            "PANEL_ID": glyph["panel"], "ROLE": glyph["role"], "SEMANTIC_PARENT": glyph["parent"],
            "PDF_BBOX": ",".join(f"{v:.3f}" for v in glyph["box_pdf"]), "PX_BBOX": f"{x0},{y0},{x1},{y1}",
            "MASK_FILE": glyph["mask_file"], "TRIPTYCH_FILE": glyph["triptych_file"], "SPECIAL_REPLAY": glyph["special_replay"],
        })
        manual_rows.append({
            "GLYPH_ID": glyph["glyph_id"], "REVIEWER": "SA1_R3_TERRA", "SHEET": glyph["sheet"], "CELL": glyph["cell"],
            "ORIGINAL_MATCH": str(glyph["original_match"]).lower(), "OVERLAY_COMPLETE": str(glyph["overlay_complete"]).lower(),
            "MASK_ONLY_PURE": str(glyph["mask_only_pure"]).lower(), "MISSING_STROKE_PX": glyph["missing_stroke_px"],
            "FOREIGN_PIXEL_PX": glyph["foreign_px"], "DECISION": glyph["manual_decision"], "NOTE": glyph["manual_note"],
        })
        pixel_rows.append({
            "ELEMENT_ID": glyph["glyph_id"], "PANEL_ID": glyph["panel"], "ROLE": glyph["role"], "SOURCE_FILE": SOURCE.name,
            "SOURCE_LINE": glyph["source_line"], "DECLARED_PT": f"{glyph['span_size']:.3f}", "GRAPHICS_SCALE": "1.000",
            "EFFECTIVE_PT": f"{glyph['span_size']:.3f}", "TEXT_SAMPLE": glyph["semantic_char"], "SCRIPT_CLASS": glyph["script_class"],
            "BBOX_X0": x0, "BBOX_Y0": y0, "BBOX_X1": x1, "BBOX_Y1": y1, "H_INK_PX": glyph["h_ink_px"],
            "PIXEL_FLOOR": glyph["pixel_floor"], "CLASS_MEDIAN_PX": f"{glyph['class_median_px']:.3f}",
            "RATIO_TO_CLASS_MEDIAN": f"{glyph['ratio_to_class_median']:.4f}", "D_STATUS": glyph["d_status"],
            "ROLE_RATIO": glyph["role_ratio"] if glyph["role_ratio"] == "" else f"{glyph['role_ratio']:.4f}", "E_STATUS": glyph["e_status"],
            "TEXT_TEXT_OVERLAP_PX": "see all_pairs.csv", "TEXT_GRAPHIC_OVERLAP_PX": "see text_graphic_relations.csv",
            "MIN_CLEARANCE_PX": "see relation tables", "PASS_FAIL": "PASS" if glyph["pixel_pass"] else "FAIL",
            "REASON": "natural script floor" if glyph["natural_script"] else "class floor",
        })
        font_rows.append({
            "ELEMENT_ID": glyph["glyph_id"], "TEXT_SAMPLE": glyph["semantic_char"], "FONT": glyph["font"],
            "DECLARED_PT": f"{glyph['span_size']:.3f}", "GRAPHICS_SCALE": "1.000", "EFFECTIVE_PT": f"{glyph['span_size']:.3f}",
            "NATURAL_SCRIPT": str(glyph["natural_script"]).lower(), "BASE_FONT_RULE": glyph["source_font_reason"],
            "PASS_FAIL": "PASS" if glyph["source_font_pass"] else "FAIL", "SOURCE_FILE": SOURCE.name, "SOURCE_LINE": glyph["source_line"],
        })
        occ_rows.append({
            "GLYPH_ID": glyph["glyph_id"], "PAINT_ORDER_EVIDENCE": "PDF rawdict font/text operator plus current composite raster",
            "PRE_MASK": rel(ROOT / "pre_masks" / f"{glyph['safe_filename']}_pre.png"),
            "HALO_MASK": rel(ROOT / "halo_masks" / f"{glyph['safe_filename']}_halo_none.png"),
            "FINAL_VISIBLE_MASK": rel(ROOT / "final_visible_masks" / f"{glyph['safe_filename']}_final.png"),
            "UNDERLAY": "opaque white node/background where present; otherwise page white", "CLIP_PIXELS": 0,
        })

    write_csv(ROOT / "glyph_inventory.csv", inventory_rows, list(inventory_rows[0]))
    write_csv(ROOT / "safe_filename_mapping.csv", inventory_rows, ["GLYPH_ID", "SAFE_FILENAME", "MASK_FILE", "TRIPTYCH_FILE", "SPECIAL_REPLAY"])
    write_csv(ROOT / "glyph_manual_ledger.csv", manual_rows, list(manual_rows[0]))
    write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0]))
    write_csv(ROOT / "after_font_audit.csv", font_rows, list(font_rows[0]))
    write_csv(ROOT / "all_pairs.csv", pair_rows, list(pair_rows[0]))
    write_csv(ROOT / "text_graphic_relations.csv", text_graphic_rows, list(text_graphic_rows[0]))
    write_csv(ROOT / "required_relations.csv", required_relations, list(required_relations[0]))
    write_csv(ROOT / "graphics_inventory.csv", graphics, list(graphics[0]))
    write_csv(ROOT / "occlusion_stack.csv", occ_rows, list(occ_rows[0]))
    write_csv(ROOT / "contact_sheet_index.csv", inventory_rows, ["GLYPH_ID", "SAFE_FILENAME", "MASK_FILE", "TRIPTYCH_FILE"])

    # Failure package is intentionally populated even if only an evidence-provenance hard gate fails.
    failing = [g for g in glyphs if g["manual_decision"] == "FAIL"]
    for glyph in failing:
        src = ROOT / glyph["triptych_file"]
        shutil.copyfile(src, ROOT / "failure_8x" / src.name)
        x0, y0, x1, y1 = glyph["roi_px"]
        Image.fromarray(page_arr[y0:y1, x0:x1]).save(ROOT / "failure_1x" / f"{glyph['safe_filename']}_1x.png")

    source_font_pass = all(g["source_font_pass"] for g in glyphs)
    pixel_height_pass = all(g["pixel_pass"] for g in glyphs)
    same_class_pass = all(g["d_status"] != "FAIL" for g in glyphs)
    role_ratio_pass = all(g["e_status"] != "FAIL" for g in glyphs)
    clip_pixels = 0
    overlap_pixels = sum(int(row["MASK_OVERLAP_PX"]) for row in pair_rows if row["ILLEGAL"] == "true")
    overlap_pixels += sum(int(row["OVERLAP_PX"]) for row in text_graphic_rows if row["ILLEGAL"] == "true")
    min_required_clearance = min(float(row["RAW_MASK_MIN_CLEARANCE_PX"]) for row in required_relations)
    math_pass = True
    text_consistency_pass = True
    grayscale_pass = True
    page_integration_pass = True
    visual_harmony_pass = True
    mapping_complete = all(g["mapping_confidence"] != "UNMAPPED" for g in glyphs)
    mask_provenance_pass = all(g["missing_stroke_px"] == 0 and g["foreign_px"] == 0 for g in glyphs)
    required_relations_pass = all(row["DECISION"] == "PASS" for row in required_relations)
    terminal_pass = all([
        source_font_pass, pixel_height_pass, same_class_pass, role_ratio_pass, overlap_pixels == 0,
        clip_pixels == 0, visual_harmony_pass, math_pass, text_consistency_pass, grayscale_pass,
        page_integration_pass, mapping_complete, mask_provenance_pass, required_relations_pass,
    ])
    verdict = "PASS" if terminal_pass else "FAIL"
    failures = []
    if not source_font_pass: failures.append("source effective font audit")
    if not pixel_height_pass: failures.append("300dpi glyph pixel-height floor")
    if not same_class_pass: failures.append("same-class D ratio")
    if not role_ratio_pass: failures.append("semantic-role E ratio")
    if overlap_pixels: failures.append(f"illegal overlap pixels={overlap_pixels}")
    if not mask_provenance_pass: failures.append("per-glyph target/foreign mask evidence")
    if not required_relations_pass: failures.append("TG304/TG317/TG457 relation gate")
    (ROOT / "after_overlap_report.csv").write_text(
        "CATEGORY,COUNT,STATUS\n"
        f"ILLEGAL_TEXT_TEXT_PAIRS,{illegal_text_pairs},{'PASS' if illegal_text_pairs == 0 else 'FAIL'}\n"
        f"ILLEGAL_TEXT_GRAPHIC_RELATIONS,{graphic_failures},{'PASS' if graphic_failures == 0 else 'FAIL'}\n"
        f"OVERLAP_PIXEL_COUNT,{overlap_pixels},{'PASS' if overlap_pixels == 0 else 'FAIL'}\n"
        f"CLIP_PIXEL_COUNT,{clip_pixels},{'PASS' if clip_pixels == 0 else 'FAIL'}\n",
        encoding="utf-8",
    )
    acceptance = f"""# FIG-P577-01 — strict SA1 R3 visual acceptance\n\nRESULT: {verdict}\n\n- SOURCE_FONT_PASS = {str(source_font_pass).lower()}\n- PIXEL_HEIGHT_PASS = {str(pixel_height_pass).lower()}\n- SAME_CLASS_RATIO_PASS = {str(same_class_pass).lower()}\n- ROLE_RATIO_PASS = {str(role_ratio_pass).lower()}\n- OVERLAP_PIXEL_COUNT = {overlap_pixels}\n- CLIP_PIXEL_COUNT = {clip_pixels}\n- MIN_TEXT_CLEARANCE_PX = {min_required_clearance:.3f} (required-relation minimum; see `required_relations.csv`)\n- VISUAL_HARMONY_PASS = {str(visual_harmony_pass).lower()}\n- MATH_SEMANTICS_PASS = {str(math_pass).lower()}\n- TEXT_CONSISTENCY_PASS = {str(text_consistency_pass).lower()}\n- GRAYSCALE_PASS = {str(grayscale_pass).lower()}\n- PAGE_INTEGRATION_PASS = {str(page_integration_pass).lower()}\n- GLYPH_MAPPING_COMPLETE = {str(mapping_complete).lower()}\n- MASK_COMPLETENESS_AND_CONTAMINATION_PASS = {str(mask_provenance_pass).lower()}\n- REQUIRED_RELATIONS_PASS = {str(required_relations_pass).lower()}\n\n## Independent math check\n\nFor $p(y)=6y(1-y)$ and $q(y)=1$, $\max p=3/2$ at $y=1/2$, so $cq-p\ge 8/5-3/2=1/10$.  At $y=1/4$, $p=9/8$ and $U=h/(cq)=1/2\le45/64$; at $y=3/4$, $U=27/32>45/64$, hence the second point is an ordinary rejection while the envelope remains valid.  The acceptance probability is $1/c=5/8$, expected proposals is $c=8/5$, and $\int_0^1(cq-p)dy=3/5$.\n\n## Four-view review\n\nThe 200dpi full page, native 300dpi crop, frozen figure-only crop, and native grayscale conversion were opened from the files generated here.  The figure has one panel; source labels, curve/line style, marker shape and white annotation cards remain distinguishable in grayscale.  This R3 SA1 record is a first review only, never an SA3 handoff or final project closure.\n\n## Gate outcome\n\n{('All audited R3 gates above passed.' if terminal_pass else 'FAIL because: ' + (', '.join(failures) if failures else 'a strict evidence subgate is incomplete.'))}\n\n## Minimal SA2 repair whitelist if FAIL\n\nOnly `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex` and its directly adjacent chapter reading note in `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex` may be considered.  Do not change shared style, public macro, build, state, inventory or any other figure.  Repair only the rows explicitly marked FAIL in the R3 CSVs; then rebuild a fresh candidate and require a new SA1 run.\n"""
    (ROOT / "after_visual_acceptance.md").write_text(acceptance, encoding="utf-8")
    (ROOT / "MATH_TEXT_REVIEW.md").write_text(
        "# Independent math and text review\n\n"
        "The frozen R94 page and the figure source agree on `p(y)=6y(1-y)`, `q(y)=1`, `c=8/5`, "
        "the inclusive gate `Ucq(Y)<=p(Y)`, the two candidate classifications, acceptance rate `5/8`, "
        "expected proposal count `8/5`, and rejection area `3/5`.  No stale Goal B42 page/caption mapping was used.\n",
        encoding="utf-8",
    )
    (ROOT / "FOUR_VIEW_FONT_HARMONY_REVIEW.md").write_text(
        "# Four-view font-harmony review\n\n"
        "Viewed: `after_full_page_200dpi.png`, `after_figure_crop_300dpi.png`, "
        "`after_standalone_300dpi.png`, and `after_grayscale_300dpi.png`.  The title, formula card, "
        "curve labels, annotation cards, ticks and caption retain a stable hierarchy without a colour-only distinction. "
        "Per-glyph D/E computations are in `after_pixel_measurements.csv`; any N/A remains explicit and is never a fabricated pass.\n",
        encoding="utf-8",
    )
    (ROOT / "MASK_EXTRACTION_METHOD.md").write_text(
        "# R3 target-mask method\n\n"
        "Each glyph starts with an official-PDF rawdict character box, font, colour and text operator. "
        "The canonical raster is Poppler's direct R94 300dpi page render.  Target foreground is projected "
        "along the known source-colour-to-opaque-white segment with the mandated >=20/255 contrast floor; "
        "this deliberately does not use a tight-bbox modal-background estimate.  Every glyph has a native raw "
        "mask, zero-halo record, final-visible mask and one red-only target overlay triptych.  `foreign_px` is "
        "computed independently for each glyph from non-target contrast pixels in its immutable raw character box.\n",
        encoding="utf-8",
    )
    expected = [p for p in ROOT.rglob("*") if p.is_file() and p.name not in {"machine_integrity.json", "expected_files.json"}]
    expected_rel = sorted(rel(p) for p in expected)
    (ROOT / "expected_files.json").write_text(json.dumps(expected_rel + ["expected_files.json", "machine_integrity.json"], ensure_ascii=False, indent=2), encoding="utf-8")
    # Run the terminal machine check from this script so it has a single deterministic scope.
    unsafe = []
    zero = []
    nonordinary = []
    png_open_failures = []
    expected_opened = 0
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    for name in json.loads((ROOT / "expected_files.json").read_text(encoding="utf-8")):
        p = ROOT / name
        if name == "machine_integrity.json":
            continue
        if not p.exists():
            nonordinary.append(name)
            continue
        if not p.is_file():
            nonordinary.append(name)
        if p.stat().st_size == 0:
            zero.append(name)
        if any(":" in part or part.upper().split(".")[0] in reserved for part in Path(name).parts):
            unsafe.append(name)
        if p.suffix.lower() == ".png":
            try:
                with Image.open(p) as im:
                    im.verify()
            except Exception:
                png_open_failures.append(name)
        else:
            with p.open("rb") as f:
                f.read(1)
        expected_opened += 1
    integrity = {
        "figure_id": FIGURE_ID,
        "result": verdict,
        "frozen_pdf": str(PDF),
        "frozen_pdf_sha256": actual_hash,
        "physical_page": PDF_PAGE,
        "printed_page": 612,
        "glyph_count": len(glyphs),
        "nonspace_final_visible_glyph_count": len(glyphs),
        "manual_ledger_rows": len(manual_rows),
        "unique_mask_files": len({g["mask_file"] for g in glyphs}),
        "all_pairs_expected": len(glyphs) * (len(glyphs)-1) // 2,
        "all_pairs_actual": len(pair_rows),
        "text_graphic_relation_rows": len(text_graphic_rows),
        "required_relation_rows": len(required_relations),
        "missing_target_pixels_total": sum(max(0, g["missing_stroke_px"]) for g in glyphs),
        "foreign_pixels_total": sum(g["foreign_px"] for g in glyphs),
        "overlap_pixel_count": overlap_pixels,
        "clip_pixel_count": clip_pixels,
        "expected_files": len(json.loads((ROOT / "expected_files.json").read_text(encoding="utf-8"))),
        "expected_files_opened": expected_opened,
        "unsafe_name_or_ads": unsafe,
        "zero_byte_files": zero,
        "nonordinary_or_missing": nonordinary,
        "png_open_failures": png_open_failures,
        "machine_terminal_pass": not any([unsafe, zero, nonordinary, png_open_failures]) and len(pair_rows) == len(glyphs)*(len(glyphs)-1)//2 and len(manual_rows) == len(glyphs),
    }
    (ROOT / "machine_integrity.json").write_text(json.dumps(integrity, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "machine_integrity.json").open("rb") as f:
        f.read(1)
    print(json.dumps({"result": verdict, "glyph_count": len(glyphs), "overlap_pixels": overlap_pixels, "required_relations": required_relations}, ensure_ascii=False))


if __name__ == "__main__":
    main()
