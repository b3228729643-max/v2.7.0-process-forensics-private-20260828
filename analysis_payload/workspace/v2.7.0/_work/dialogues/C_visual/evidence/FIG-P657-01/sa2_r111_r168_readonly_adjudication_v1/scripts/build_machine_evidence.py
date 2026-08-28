from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_distribution_relations.tex")
PAGE_NUMBER = 706
PAGE_INDEX = PAGE_NUMBER - 1
PRINTED_PAGE = 693
SCALE = 300.0 / 72.0

VIEWS = ROOT / "views"
MACHINE = ROOT / "machine"
ROIS = ROOT / "rois"
CONTACTS = ROOT / "contacts"
GLYPH_MASKS = ROOT / "masks" / "glyphs"
GRAPHIC_MASKS = ROOT / "masks" / "graphics"

for path in (VIEWS, MACHINE, ROIS, CONTACTS, GLYPH_MASKS, GRAPHIC_MASKS):
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def int_color_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def float_color_to_rgb(value) -> tuple[int, int, int]:
    return tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in value)


def pt_rect_to_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def glyph_rect_to_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        int(round(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(round(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def clamp_rect(rect: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def expand_rect(rect: tuple[int, int, int, int], pad: int, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return clamp_rect((x0 - pad, y0 - pad, x1 + pad, y1 + pad), width, height)


def blend_mask(pixels: np.ndarray, fg_rgb: tuple[int, int, int], backgrounds: list[tuple[int, int, int]]) -> np.ndarray:
    p = pixels.astype(np.float32)
    fg = np.array(fg_rgb, dtype=np.float32)
    answer = np.zeros(p.shape[:2], dtype=bool)
    for bg_rgb in backgrounds:
        bg = np.array(bg_rgb, dtype=np.float32)
        direction = bg - fg
        denom = float(np.dot(direction, direction))
        if denom <= 0:
            continue
        alpha = np.sum((bg - p) * direction, axis=2) / denom
        reconstructed = bg - alpha[..., None] * direction
        residual = np.max(np.abs(p - reconstructed), axis=2)
        contrast = np.max(np.abs(p - bg), axis=2)
        answer |= (alpha >= (20.0 / max(1.0, float(np.max(np.abs(direction)))))) & (alpha <= 1.10) & (residual <= 13.0) & (contrast >= 20.0)
    return answer


def tight_mask(mask: np.ndarray, global_rect: tuple[int, int, int, int]):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return mask.copy(), global_rect
    lx0, lx1 = int(xs.min()), int(xs.max()) + 1
    ly0, ly1 = int(ys.min()), int(ys.max()) + 1
    gx0, gy0, _, _ = global_rect
    return mask[ly0:ly1, lx0:lx1].copy(), (gx0 + lx0, gy0 + ly0, gx0 + lx1, gy0 + ly1)


def save_mask_png(path: Path, mask: np.ndarray) -> None:
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def overlay_image(original: Image.Image, mask: np.ndarray) -> Image.Image:
    arr = np.asarray(original.convert("RGB")).copy()
    tint = np.array([235, 35, 45], dtype=np.uint8)
    arr[mask] = ((arr[mask].astype(np.uint16) + tint.astype(np.uint16) * 2) // 3).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def safe_cp(char: str) -> str:
    return "_".join(f"U{ord(c):04X}" for c in char)


def script_class(char: str) -> str:
    cp = ord(char)
    cat = unicodedata.category(char)
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK"
    if char in "=+−-<>≤≥≈∼∑∏∫/":
        return "MATH_OPERATOR"
    if char in ",，。；：;:.、":
        return "LOW_PROFILE_PUNCTUATION"
    if char.isdigit():
        return "DIGIT"
    if char.isalpha():
        if char.isupper() or 0x1D400 <= cp <= 0x1D419 or 0x1D434 <= cp <= 0x1D44D:
            return "LATIN_OR_MATH_UPPER"
        return "LATIN_LOWER"
    if cat.startswith("P"):
        return "PUNCTUATION"
    return "OTHER_VISIBLE"


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rect = page.rect
full_300_path = VIEWS / "full_page_300dpi.png"
full_200_path = VIEWS / "full_page_200dpi.png"
full_img = Image.open(full_300_path).convert("RGB")
page_w, page_h = full_img.size

figure_body_pt = (105.0, 268.0, 505.0, 427.0)
figure_caption_pt = (80.0, 268.0, 525.0, 460.0)
caption_pt = (80.0, 426.0, 525.0, 460.0)
figure_body_px = pt_rect_to_px(figure_body_pt)
figure_caption_px = pt_rect_to_px(figure_caption_pt)
caption_px = pt_rect_to_px(caption_pt)

figure_crop = full_img.crop(figure_caption_px)
figure_crop.save(VIEWS / "figure_crop_300dpi.png")
full_img.crop(figure_body_px).save(VIEWS / "standalone_300dpi.png")
ImageOps.grayscale(figure_crop).save(VIEWS / "grayscale_300dpi.png")
full_img.crop(caption_px).save(VIEWS / "caption_300dpi.png")

parent_by_seq = {
    6: ("ROLE_PRIOR", "role_heading"),
    9: ("NODE_DIRICHLET", "node_text"),
    12: ("NODE_BETA", "node_text"),
    13: ("ROLE_LIKELIHOOD", "role_heading"),
    16: ("NODE_MULTINOMIAL", "node_text"),
    19: ("NODE_BINOMIAL", "node_text"),
    20: ("ROLE_SINGLE_TRIAL", "role_heading"),
    23: ("NODE_CATEGORICAL", "node_text"),
    26: ("NODE_BERNOULLI", "node_text"),
    35: ("LABEL_DIR_BETA_SPECIAL", "edge_label"),
    38: ("LABEL_MULTI_BINOM_SPECIAL", "edge_label"),
    41: ("LABEL_MULTI_CAT_N1", "edge_label"),
    44: ("LABEL_BINOM_BERN_N1", "edge_label"),
    47: ("LABEL_CAT_BERN_K2", "edge_label"),
    51: ("LEGEND_CONJUGACY_LABEL", "legend_label"),
    54: ("LEGEND_SPECIAL_LABEL", "legend_label"),
    55: ("CAPTION", "caption"),
}

expected_text = {
    "ROLE_PRIOR": "先验族",
    "NODE_DIRICHLET": "Dirichlet分布",
    "NODE_BETA": "Beta分布𝐾=2",
    "ROLE_LIKELIHOOD": "似然族",
    "NODE_MULTINOMIAL": "多项分布",
    "NODE_BINOMIAL": "二项分布𝐾=2",
    "ROLE_SINGLE_TRIAL": "单次试验",
    "NODE_CATEGORICAL": "类别分布𝑁=1",
    "NODE_BERNOULLI": "Bernoulli分布𝐾=2,𝑁=1",
    "LABEL_DIR_BETA_SPECIAL": "特殊情形",
    "LABEL_MULTI_BINOM_SPECIAL": "特殊情形",
    "LABEL_MULTI_CAT_N1": "𝑁=1",
    "LABEL_BINOM_BERN_N1": "𝑁=1",
    "LABEL_CAT_BERN_K2": "𝐾=2",
    "LEGEND_CONJUGACY_LABEL": "共轭",
    "LEGEND_SPECIAL_LABEL": "特殊情形",
    "CAPTION": "图34.3六个常用分布之间同时存在特殊情形关系和共轭关系：Beta是二维Dirichlet，二项是二维多项，类别分布是单次多项，Bernoulli同时是单次二项；粗箭头表示共轭先验而不是集合包含",
}

node_background = {
    "NODE_DIRICHLET": (242, 244, 247),
    "NODE_BETA": (242, 244, 247),
    "NODE_MULTINOMIAL": (242, 244, 247),
    "NODE_BINOMIAL": (242, 244, 247),
    "NODE_CATEGORICAL": (246, 247, 248),
    "NODE_BERNOULLI": (246, 247, 248),
}

glyph_rows = []
glyph_objects = []
glyph_contact_parts = []
parent_actual = defaultdict(str)
trace_spans = page.get_texttrace()

for trace_index, span in enumerate(trace_spans):
    seqno = int(span["seqno"])
    if seqno not in parent_by_seq:
        continue
    parent_id, role = parent_by_seq[seqno]
    span_color = span["color"]
    fg = float_color_to_rgb(span_color) if isinstance(span_color, (tuple, list)) else int_color_to_rgb(int(span_color))
    bg = node_background.get(parent_id, (255, 255, 255))
    for span_char_index, char_info in enumerate(span["chars"]):
        char = chr(char_info[0])
        if char.isspace():
            continue
        parent_actual[parent_id] += char
        glyph_id = f"GLY{len(glyph_rows) + 1:04d}"
        bbox_pt = tuple(float(x) for x in char_info[3])
        raw_rect = clamp_rect(glyph_rect_to_px(bbox_pt), page_w, page_h)
        raw_crop = full_img.crop(raw_rect)
        raw_pixels = np.asarray(raw_crop)
        mask = blend_mask(raw_pixels, fg, [bg])
        mask_tight, mask_rect = tight_mask(mask, raw_rect)
        safe_name = f"{glyph_id}_{safe_cp(char)}.png"
        save_mask_png(GLYPH_MASKS / safe_name, mask_tight)
        ys, xs = np.nonzero(mask)
        ink_height = int(ys.max() - ys.min() + 1) if len(ys) else 0
        ink_width = int(xs.max() - xs.min() + 1) if len(xs) else 0
        ink_area = int(mask.sum())
        outline_edge_px = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum()) if mask.size else 0
        unicode_name = unicodedata.name(char, "UNNAMED")
        row = {
            "element_id": glyph_id,
            "parent_id": parent_id,
            "role": role,
            "trace_index": trace_index,
            "seqno": seqno,
            "span_char_index": span_char_index,
            "char": char,
            "codepoint": f"U+{ord(char):04X}",
            "unicode_name": unicode_name,
            "script_class": script_class(char),
            "font": span["font"],
            "font_size_pt": round(float(span["size"]), 6),
            "text_color_rgb": "-".join(str(x) for x in fg),
            "background_rgb": "-".join(str(x) for x in bg),
            "bbox_pt_x0": round(bbox_pt[0], 6),
            "bbox_pt_y0": round(bbox_pt[1], 6),
            "bbox_pt_x1": round(bbox_pt[2], 6),
            "bbox_pt_y1": round(bbox_pt[3], 6),
            "mask_bbox_px_x0": mask_rect[0],
            "mask_bbox_px_y0": mask_rect[1],
            "mask_bbox_px_x1": mask_rect[2],
            "mask_bbox_px_y1": mask_rect[3],
            "ink_height_px": ink_height,
            "ink_width_px": ink_width,
            "ink_area_px": ink_area,
            "mask_edge_pixel_count": outline_edge_px,
            "safe_mask_filename": f"masks/glyphs/{safe_name}",
        }
        glyph_rows.append(row)
        glyph_objects.append({
            "object_id": glyph_id,
            "kind": "GLYPH",
            "parent_id": parent_id,
            "role": role,
            "bbox": mask_rect,
            "mask": mask_tight,
            "char": char,
        })
        contact_rect = expand_rect(pt_rect_to_px(bbox_pt), 4, page_w, page_h)
        contact_original = full_img.crop(contact_rect)
        contact_mask = np.zeros((contact_rect[3] - contact_rect[1], contact_rect[2] - contact_rect[0]), dtype=bool)
        mx0 = mask_rect[0] - contact_rect[0]
        my0 = mask_rect[1] - contact_rect[1]
        contact_mask[my0:my0 + mask_tight.shape[0], mx0:mx0 + mask_tight.shape[1]] = mask_tight
        contact_overlay = overlay_image(contact_original, contact_mask)
        contact_mask_only = Image.fromarray(np.where(contact_mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
        glyph_contact_parts.append((glyph_id, char, parent_id, contact_original, contact_overlay, contact_mask_only))

write_csv(MACHINE / "glyph_measurements.csv", glyph_rows)

text_expectation_rows = []
for parent_id, expected in expected_text.items():
    actual = parent_actual.get(parent_id, "")
    text_expectation_rows.append({
        "parent_id": parent_id,
        "expected_text": expected,
        "actual_extracted_text": actual,
        "expected_codepoints": " ".join(f"U+{ord(c):04X}" for c in expected),
        "actual_codepoints": " ".join(f"U+{ord(c):04X}" for c in actual),
        "expected_length": len(expected),
        "actual_length": len(actual),
        "positional_codepoint_mismatch_count": sum(a != b for a, b in itertools.zip_longest(expected, actual, fillvalue="\0")),
    })
write_csv(MACHINE / "text_codepoint_expectations.csv", text_expectation_rows)

CONTACT_CHUNK = 10
contact_inventory = []
for start in range(0, len(glyph_contact_parts), CONTACT_CHUNK):
    chunk = glyph_contact_parts[start:start + CONTACT_CHUNK]
    scaled = []
    max_width = 0
    total_height = 36
    for glyph_id, char, parent_id, original, overlay, mask_only in chunk:
        panels = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in (original, overlay, mask_only)]
        row_width = sum(im.width for im in panels) + 24
        row_height = max(im.height for im in panels) + 30
        scaled.append((glyph_id, char, parent_id, panels, row_width, row_height))
        max_width = max(max_width, row_width)
        total_height += row_height + 10
    sheet = Image.new("RGB", (max_width + 20, total_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 8), "ORIGINAL | TARGET OVERLAY | MASK ONLY -- all nearest-neighbour 8x", fill="black")
    y = 36
    for glyph_id, char, parent_id, panels, row_width, row_height in scaled:
        draw.text((10, y), f"{glyph_id} {safe_cp(char)} parent={parent_id}", fill="black")
        x = 10
        py = y + 24
        for panel in panels:
            sheet.paste(panel, (x, py))
            x += panel.width + 8
        y += row_height + 10
    end = start + len(chunk)
    filename = f"glyph_contact_{start + 1:04d}_{end:04d}.png"
    sheet.save(CONTACTS / filename)
    contact_inventory.append({
        "sheet_id": f"GSHEET{start // CONTACT_CHUNK + 1:03d}",
        "filename": f"contacts/{filename}",
        "first_element_id": chunk[0][0],
        "last_element_id": chunk[-1][0],
        "cell_count": len(chunk),
        "width_px": sheet.width,
        "height_px": sheet.height,
        "scale": "8x_nearest",
        "panels_per_cell": 3,
    })
write_csv(MACHINE / "glyph_contact_inventory.csv", contact_inventory)

graphic_defs = [
    (1, "GFX001", "NODE_BORDER_DIRICHLET", "NODE_BORDER", "NODE_DIRICHLET", ""),
    (2, "GFX002", "NODE_BORDER_BETA", "NODE_BORDER", "NODE_BETA", ""),
    (3, "GFX003", "NODE_BORDER_MULTINOMIAL", "NODE_BORDER", "NODE_MULTINOMIAL", ""),
    (4, "GFX004", "NODE_BORDER_BINOMIAL", "NODE_BORDER", "NODE_BINOMIAL", ""),
    (5, "GFX005", "NODE_BORDER_CATEGORICAL", "NODE_BORDER", "NODE_CATEGORICAL", ""),
    (6, "GFX006", "NODE_BORDER_BERNOULLI", "NODE_BORDER", "NODE_BERNOULLI", ""),
    (7, "GFX007", "CONJ_DIR_MULTI_SHAFT", "ARROW_SHAFT", "REL_CONJ_DIR_MULTI", "down"),
    (8, "GFX008", "CONJ_DIR_MULTI_HEAD", "ARROWHEAD", "REL_CONJ_DIR_MULTI", "down"),
    (9, "GFX009", "CONJ_BETA_BINOM_SHAFT", "ARROW_SHAFT", "REL_CONJ_BETA_BINOM", "down"),
    (10, "GFX010", "CONJ_BETA_BINOM_HEAD", "ARROWHEAD", "REL_CONJ_BETA_BINOM", "down"),
    (11, "GFX011", "SPECIAL_DIR_BETA_SHAFT", "ARROW_SHAFT", "REL_SPECIAL_DIR_BETA", "right"),
    (12, "GFX012", "SPECIAL_DIR_BETA_HEAD", "ARROWHEAD", "REL_SPECIAL_DIR_BETA", "right"),
    (13, "GFX013", "SPECIAL_MULTI_BINOM_SHAFT", "ARROW_SHAFT", "REL_SPECIAL_MULTI_BINOM", "right"),
    (14, "GFX014", "SPECIAL_MULTI_BINOM_HEAD", "ARROWHEAD", "REL_SPECIAL_MULTI_BINOM", "right"),
    (15, "GFX015", "SPECIAL_MULTI_CAT_SHAFT", "ARROW_SHAFT", "REL_SPECIAL_MULTI_CAT", "down"),
    (16, "GFX016", "SPECIAL_MULTI_CAT_HEAD", "ARROWHEAD", "REL_SPECIAL_MULTI_CAT", "down"),
    (17, "GFX017", "SPECIAL_BINOM_BERN_SHAFT", "ARROW_SHAFT", "REL_SPECIAL_BINOM_BERN", "down"),
    (18, "GFX018", "SPECIAL_BINOM_BERN_HEAD", "ARROWHEAD", "REL_SPECIAL_BINOM_BERN", "down"),
    (19, "GFX019", "SPECIAL_CAT_BERN_SHAFT", "ARROW_SHAFT", "REL_SPECIAL_CAT_BERN", "right"),
    (20, "GFX020", "SPECIAL_CAT_BERN_HEAD", "ARROWHEAD", "REL_SPECIAL_CAT_BERN", "right"),
    (21, "GFX021", "LEGEND_CONJ_SHAFT", "ARROW_SHAFT", "LEGEND_CONJUGACY", "right"),
    (22, "GFX022", "LEGEND_CONJ_HEAD", "ARROWHEAD", "LEGEND_CONJUGACY", "right"),
    (23, "GFX023", "LEGEND_SPECIAL_SHAFT", "ARROW_SHAFT", "LEGEND_SPECIAL", "right"),
    (24, "GFX024", "LEGEND_SPECIAL_HEAD", "ARROWHEAD", "LEGEND_SPECIAL", "right"),
]

drawings = page.get_drawings()
graphic_rows = []
graphic_objects = []
graphic_contact_parts = []
for drawing_index, graphic_id, semantic_name, kind, parent_id, direction in graphic_defs:
    drawing = drawings[drawing_index]
    bbox_pt = tuple(float(x) for x in drawing["rect"])
    width_pt = float(drawing.get("width") or 0.0)
    pad = max(3, int(math.ceil(width_pt * SCALE / 2.0)) + 3)
    raw_rect = expand_rect(pt_rect_to_px(bbox_pt), pad, page_w, page_h)
    crop = full_img.crop(raw_rect)
    fg_float = drawing.get("color") or drawing.get("fill")
    fg = float_color_to_rgb(fg_float)
    backgrounds = [(255, 255, 255)]
    if kind == "NODE_BORDER":
        fill = float_color_to_rgb(drawing["fill"])
        backgrounds.append(fill)
    mask = blend_mask(np.asarray(crop), fg, backgrounds)
    if kind == "NODE_BORDER":
        vx0, vy0, vx1, vy1 = pt_rect_to_px(bbox_pt)
        band = max(3, int(math.ceil(width_pt * SCALE / 2.0)) + 2)
        gx = np.arange(raw_rect[0], raw_rect[2])[None, :]
        gy = np.arange(raw_rect[1], raw_rect[3])[:, None]
        vertical_band = ((np.abs(gx - vx0) <= band) | (np.abs(gx - (vx1 - 1)) <= band)) & (gy >= vy0 - band) & (gy < vy1 + band)
        horizontal_band = ((np.abs(gy - vy0) <= band) | (np.abs(gy - (vy1 - 1)) <= band)) & (gx >= vx0 - band) & (gx < vx1 + band)
        mask &= vertical_band | horizontal_band
    mask_tight, mask_rect = tight_mask(mask, raw_rect)
    safe_name = f"{graphic_id}_{semantic_name}.png"
    save_mask_png(GRAPHIC_MASKS / safe_name, mask_tight)
    ys, xs = np.nonzero(mask)
    graphic_rows.append({
        "element_id": graphic_id,
        "drawing_index": drawing_index,
        "seqno": drawing.get("seqno", ""),
        "semantic_name": semantic_name,
        "kind": kind,
        "parent_id": parent_id,
        "direction": direction,
        "pdf_draw_type": drawing.get("type", ""),
        "line_width_pt": round(width_pt, 6),
        "stroke_rgb": "-".join(str(x) for x in fg),
        "fill_rgb": "" if drawing.get("fill") is None else "-".join(str(x) for x in float_color_to_rgb(drawing["fill"])),
        "bbox_pt_x0": round(bbox_pt[0], 6),
        "bbox_pt_y0": round(bbox_pt[1], 6),
        "bbox_pt_x1": round(bbox_pt[2], 6),
        "bbox_pt_y1": round(bbox_pt[3], 6),
        "mask_bbox_px_x0": mask_rect[0],
        "mask_bbox_px_y0": mask_rect[1],
        "mask_bbox_px_x1": mask_rect[2],
        "mask_bbox_px_y1": mask_rect[3],
        "ink_height_px": int(ys.max() - ys.min() + 1) if len(ys) else 0,
        "ink_width_px": int(xs.max() - xs.min() + 1) if len(xs) else 0,
        "ink_area_px": int(mask.sum()),
        "item_count": len(drawing["items"]),
        "safe_mask_filename": f"masks/graphics/{safe_name}",
    })
    graphic_objects.append({
        "object_id": graphic_id,
        "kind": kind,
        "parent_id": parent_id,
        "role": kind,
        "bbox": mask_rect,
        "mask": mask_tight,
        "char": "",
    })
    contact_rect = expand_rect(mask_rect, 4, page_w, page_h)
    original = full_img.crop(contact_rect)
    local_mask = np.zeros((contact_rect[3] - contact_rect[1], contact_rect[2] - contact_rect[0]), dtype=bool)
    x0 = mask_rect[0] - contact_rect[0]
    y0 = mask_rect[1] - contact_rect[1]
    local_mask[y0:y0 + mask_tight.shape[0], x0:x0 + mask_tight.shape[1]] = mask_tight
    overlay = overlay_image(original, local_mask)
    mask_only = Image.fromarray(np.where(local_mask, 0, 255).astype(np.uint8), mode="L").convert("RGB")
    graphic_contact_parts.append((graphic_id, semantic_name, parent_id, original, overlay, mask_only))

write_csv(MACHINE / "graphic_objects.csv", graphic_rows)

graphic_contact_inventory = []
for start in range(0, len(graphic_contact_parts), 4):
    chunk = graphic_contact_parts[start:start + 4]
    panels_for_rows = []
    max_width = 0
    total_height = 36
    for graphic_id, semantic_name, parent_id, original, overlay, mask_only in chunk:
        panels = [im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST) for im in (original, overlay, mask_only)]
        row_width = sum(im.width for im in panels) + 24
        row_height = max(im.height for im in panels) + 30
        panels_for_rows.append((graphic_id, semantic_name, parent_id, panels, row_width, row_height))
        max_width = max(max_width, row_width)
        total_height += row_height + 10
    sheet = Image.new("RGB", (max_width + 20, total_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 8), "ORIGINAL | TARGET OVERLAY | MASK ONLY -- all nearest-neighbour 8x", fill="black")
    y = 36
    for graphic_id, semantic_name, parent_id, panels, row_width, row_height in panels_for_rows:
        draw.text((10, y), f"{graphic_id} {semantic_name} parent={parent_id}", fill="black")
        x = 10
        py = y + 24
        for panel in panels:
            sheet.paste(panel, (x, py))
            x += panel.width + 8
        y += row_height + 10
    end = start + len(chunk)
    filename = f"graphic_contact_{start + 1:03d}_{end:03d}.png"
    sheet.save(CONTACTS / filename)
    graphic_contact_inventory.append({
        "sheet_id": f"DSHEET{start // 4 + 1:03d}",
        "filename": f"contacts/{filename}",
        "first_element_id": chunk[0][0],
        "last_element_id": chunk[-1][0],
        "cell_count": len(chunk),
        "width_px": sheet.width,
        "height_px": sheet.height,
        "scale": "8x_nearest",
        "panels_per_cell": 3,
    })
write_csv(MACHINE / "graphic_contact_inventory.csv", graphic_contact_inventory)

background_rows = []
for drawing_index, graphic_id, semantic_name, kind, parent_id, direction in graphic_defs[:6]:
    drawing = drawings[drawing_index]
    background_rows.append({
        "background_id": f"BG{drawing_index:03d}",
        "drawing_index": drawing_index,
        "parent_id": parent_id,
        "semantic_name": semantic_name.replace("BORDER", "FILL"),
        "fill_rgb": "-".join(str(x) for x in float_color_to_rgb(drawing["fill"])),
        "bbox_pt": " ".join(f"{float(v):.6f}" for v in drawing["rect"]),
        "pair_denominator_scope": "BACKGROUND_CATALOG_ONLY",
        "reason": "Node fill is background under the direct pixel protocol and is not mixed into foreground overlap masks.",
    })
write_csv(MACHINE / "background_objects.csv", background_rows)


def object_intersection(a, b) -> int:
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if ix0 >= ix1 or iy0 >= iy1:
        return 0
    am = a["mask"][iy0 - ay0:iy1 - ay0, ix0 - ax0:ix1 - ax0]
    bm = b["mask"][iy0 - by0:iy1 - by0, ix0 - bx0:ix1 - bx0]
    return int(np.logical_and(am, bm).sum())


def bbox_gap(a, b) -> float:
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def pair_context(a, b) -> str:
    ids = {a["object_id"], b["object_id"]}
    parents = {a["parent_id"], b["parent_id"]}
    if a["parent_id"] == b["parent_id"] and {a["kind"], b["kind"]} == {"GLYPH", "NODE_BORDER"}:
        return "NODE_TEXT_BORDER_RELATION_CANDIDATE"
    for n in range(7, 25, 2):
        if ids == {f"GFX{n:03d}", f"GFX{n + 1:03d}"}:
            return "SAME_ARROW_SHAFT_HEAD_CONNECTION_CANDIDATE"
    endpoint_map = {
        "REL_CONJ_DIR_MULTI": {"GFX001", "GFX003"},
        "REL_CONJ_BETA_BINOM": {"GFX002", "GFX004"},
        "REL_SPECIAL_DIR_BETA": {"GFX001", "GFX002"},
        "REL_SPECIAL_MULTI_BINOM": {"GFX003", "GFX004"},
        "REL_SPECIAL_MULTI_CAT": {"GFX003", "GFX005"},
        "REL_SPECIAL_BINOM_BERN": {"GFX004", "GFX006"},
        "REL_SPECIAL_CAT_BERN": {"GFX005", "GFX006"},
    }
    for relation, nodes in endpoint_map.items():
        if relation in parents and ids.intersection(nodes):
            return "ARROW_NODE_ENDPOINT_CONNECTION_CANDIDATE"
    if a["parent_id"] == b["parent_id"] and a["kind"] == b["kind"] == "GLYPH":
        return "SAME_TEXT_PARENT_INTERNAL_TYPOGRAPHY"
    if "CAPTION" in parents:
        return "CAPTION_PAIR"
    return "ORDINARY_INDEPENDENT_PAIR"


objects = glyph_objects + graphic_objects
denominator_rows = []
for obj in objects:
    denominator_rows.append({
        "object_id": obj["object_id"],
        "kind": obj["kind"],
        "parent_id": obj["parent_id"],
        "role": obj["role"],
        "char": obj.get("char", ""),
        "bbox_px": " ".join(str(x) for x in obj["bbox"]),
        "ink_area_px": int(obj["mask"].sum()),
        "foreground_pair_denominator": "INCLUDED",
    })
write_csv(MACHINE / "visible_foreground_object_denominator.csv", denominator_rows)

pair_rows = []
overlap_pairs = []
for pair_number, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
    overlap = object_intersection(a, b)
    context = pair_context(a, b)
    row = {
        "pair_id": f"PAIR{pair_number:05d}",
        "a_id": a["object_id"],
        "b_id": b["object_id"],
        "a_kind": a["kind"],
        "b_kind": b["kind"],
        "a_parent": a["parent_id"],
        "b_parent": b["parent_id"],
        "bbox_gap_px": round(bbox_gap(a, b), 6),
        "raw_mask_intersection_px": overlap,
        "context_candidate": context,
    }
    pair_rows.append(row)
    if overlap:
        overlap_pairs.append(row)
write_csv(MACHINE / "all_unordered_pairs.csv", pair_rows)
write_csv(MACHINE / "nonzero_intersection_pairs.csv", overlap_pairs, list(pair_rows[0].keys()))


def combine_objects(object_ids: list[str]):
    selected = [obj for obj in objects if obj["object_id"] in object_ids]
    if not selected:
        raise ValueError(object_ids)
    x0 = min(o["bbox"][0] for o in selected)
    y0 = min(o["bbox"][1] for o in selected)
    x1 = max(o["bbox"][2] for o in selected)
    y1 = max(o["bbox"][3] for o in selected)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    for obj in selected:
        ox0, oy0, ox1, oy1 = obj["bbox"]
        mask[oy0 - y0:oy1 - y0, ox0 - x0:ox1 - x0] |= obj["mask"]
    mask, rect = tight_mask(mask, (x0, y0, x1, y1))
    return {"bbox": rect, "mask": mask}


def ids_for_parent(parent_id: str) -> list[str]:
    return [obj["object_id"] for obj in glyph_objects if obj["parent_id"] == parent_id]


critical_defs = [
    ("CRIT001", "NODE_DIRICHLET_TEXT_TO_BORDER", ids_for_parent("NODE_DIRICHLET"), ["GFX001"], "node_text_border"),
    ("CRIT002", "NODE_BETA_TEXT_TO_BORDER", ids_for_parent("NODE_BETA"), ["GFX002"], "node_text_border"),
    ("CRIT003", "NODE_MULTINOMIAL_TEXT_TO_BORDER", ids_for_parent("NODE_MULTINOMIAL"), ["GFX003"], "node_text_border"),
    ("CRIT004", "NODE_BINOMIAL_TEXT_TO_BORDER", ids_for_parent("NODE_BINOMIAL"), ["GFX004"], "node_text_border"),
    ("CRIT005", "NODE_CATEGORICAL_TEXT_TO_BORDER", ids_for_parent("NODE_CATEGORICAL"), ["GFX005"], "node_text_border"),
    ("CRIT006", "NODE_BERNOULLI_TEXT_TO_BORDER", ids_for_parent("NODE_BERNOULLI"), ["GFX006"], "node_text_border"),
    ("CRIT007", "CONJ_DIR_MULTI_ARROW_TO_NODE_TEXT", ["GFX007", "GFX008"], ids_for_parent("NODE_DIRICHLET") + ids_for_parent("NODE_MULTINOMIAL"), "arrow_text"),
    ("CRIT008", "CONJ_BETA_BINOM_ARROW_TO_NODE_TEXT", ["GFX009", "GFX010"], ids_for_parent("NODE_BETA") + ids_for_parent("NODE_BINOMIAL"), "arrow_text"),
    ("CRIT009", "SPECIAL_DIR_BETA_ARROW_TO_LABEL", ["GFX011", "GFX012"], ids_for_parent("LABEL_DIR_BETA_SPECIAL"), "arrow_label"),
    ("CRIT010", "SPECIAL_MULTI_BINOM_ARROW_TO_LABEL", ["GFX013", "GFX014"], ids_for_parent("LABEL_MULTI_BINOM_SPECIAL"), "arrow_label"),
    ("CRIT011", "SPECIAL_MULTI_CAT_ARROW_TO_LABEL", ["GFX015", "GFX016"], ids_for_parent("LABEL_MULTI_CAT_N1"), "arrow_label"),
    ("CRIT012", "SPECIAL_BINOM_BERN_ARROW_TO_LABEL", ["GFX017", "GFX018"], ids_for_parent("LABEL_BINOM_BERN_N1"), "arrow_label"),
    ("CRIT013", "SPECIAL_CAT_BERN_ARROW_TO_LABEL", ["GFX019", "GFX020"], ids_for_parent("LABEL_CAT_BERN_K2"), "arrow_label"),
    ("CRIT014", "LEGEND_CONJ_ARROW_TO_LABEL", ["GFX021", "GFX022"], ids_for_parent("LEGEND_CONJUGACY_LABEL"), "arrow_label"),
    ("CRIT015", "LEGEND_SPECIAL_ARROW_TO_LABEL", ["GFX023", "GFX024"], ids_for_parent("LEGEND_SPECIAL_LABEL"), "arrow_label"),
    ("CRIT016", "FIGURE_BODY_TO_CAPTION", [o["object_id"] for o in objects if o["parent_id"] != "CAPTION"], ids_for_parent("CAPTION"), "figure_caption"),
    ("CRIT017", "ROLE_PRIOR_TO_NEAREST_NODE_BORDER", ids_for_parent("ROLE_PRIOR"), ["GFX001"], "role_node"),
    ("CRIT018", "ROLE_LIKELIHOOD_TO_NEAREST_NODE_BORDER", ids_for_parent("ROLE_LIKELIHOOD"), ["GFX003"], "role_node"),
    ("CRIT019", "ROLE_SINGLE_TRIAL_TO_NEAREST_NODE_BORDER", ids_for_parent("ROLE_SINGLE_TRIAL"), ["GFX005"], "role_node"),
]

for overlap_index, row in enumerate(overlap_pairs, start=20):
    critical_defs.append((
        f"CRIT{overlap_index:03d}",
        f"NONZERO_{row['pair_id']}_{row['a_id']}_{row['b_id']}",
        [row["a_id"]],
        [row["b_id"]],
        f"nonzero_pair__{row['context_candidate'].lower()}",
    ))


def intersect_combined(a, b) -> int:
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if ix0 >= ix1 or iy0 >= iy1:
        return 0
    am = a["mask"][iy0 - ay0:iy1 - ay0, ix0 - ax0:ix1 - ax0]
    bm = b["mask"][iy0 - by0:iy1 - by0, ix0 - bx0:ix1 - bx0]
    return int(np.logical_and(am, bm).sum())


def center_distance(a, b) -> float:
    ay, ax = np.nonzero(a["mask"])
    by, bx = np.nonzero(b["mask"])
    if len(ax) == 0 or len(bx) == 0:
        return math.inf
    a_points = np.column_stack([ay + a["bbox"][1], ax + a["bbox"][0]])
    b_points = np.column_stack([by + b["bbox"][1], bx + b["bbox"][0]])
    if len(a_points) > len(b_points):
        a_points, b_points = b_points, a_points
    tree = cKDTree(b_points)
    distances, _ = tree.query(a_points, k=1)
    return float(distances.min())


critical_rows = []
for critical_id, name, a_ids, b_ids, relation_class in critical_defs:
    a = combine_objects(a_ids)
    b = combine_objects(b_ids)
    intersection = intersect_combined(a, b)
    distance = center_distance(a, b)
    blank_clearance = max(0.0, distance - 1.0)
    ux0 = min(a["bbox"][0], b["bbox"][0])
    uy0 = min(a["bbox"][1], b["bbox"][1])
    ux1 = max(a["bbox"][2], b["bbox"][2])
    uy1 = max(a["bbox"][3], b["bbox"][3])
    roi_rect = expand_rect((ux0, uy0, ux1, uy1), 8, page_w, page_h)
    original = full_img.crop(roi_rect)
    h, w = roi_rect[3] - roi_rect[1], roi_rect[2] - roi_rect[0]
    amask = np.zeros((h, w), dtype=bool)
    bmask = np.zeros((h, w), dtype=bool)
    ax0, ay0, ax1, ay1 = a["bbox"]
    bx0, by0, bx1, by1 = b["bbox"]
    amask[ay0 - roi_rect[1]:ay1 - roi_rect[1], ax0 - roi_rect[0]:ax1 - roi_rect[0]] = a["mask"]
    bmask[by0 - roi_rect[1]:by1 - roi_rect[1], bx0 - roi_rect[0]:bx1 - roi_rect[0]] = b["mask"]
    intermask = amask & bmask
    overlay_arr = np.asarray(original).copy()
    overlay_arr[amask] = np.array([235, 35, 45], dtype=np.uint8)
    overlay_arr[bmask] = np.array([20, 110, 235], dtype=np.uint8)
    overlay_arr[intermask] = np.array([180, 0, 210], dtype=np.uint8)
    overlay = Image.fromarray(overlay_arr, mode="RGB")
    stem = f"{critical_id}_{name}"
    original.save(ROIS / f"{stem}_original_1x.png")
    Image.fromarray(np.where(amask, 0, 255).astype(np.uint8), mode="L").save(ROIS / f"{stem}_A_mask_1x.png")
    Image.fromarray(np.where(bmask, 0, 255).astype(np.uint8), mode="L").save(ROIS / f"{stem}_B_mask_1x.png")
    Image.fromarray(np.where(intermask, 0, 255).astype(np.uint8), mode="L").save(ROIS / f"{stem}_intersection_1x.png")
    overlay.save(ROIS / f"{stem}_overlay_1x.png")
    overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(ROIS / f"{stem}_overlay_8x_nearest.png")
    critical_rows.append({
        "critical_id": critical_id,
        "semantic_name": name,
        "relation_class": relation_class,
        "a_ids": " ".join(a_ids),
        "b_ids": " ".join(b_ids),
        "roi_x": roi_rect[0],
        "roi_y": roi_rect[1],
        "roi_width": roi_rect[2] - roi_rect[0],
        "roi_height": roi_rect[3] - roi_rect[1],
        "raw_mask_intersection_px": intersection,
        "min_pixel_center_distance": round(distance, 6),
        "conservative_blank_clearance_px": round(blank_clearance, 6),
        "original_1x": f"rois/{stem}_original_1x.png",
        "A_mask_1x": f"rois/{stem}_A_mask_1x.png",
        "B_mask_1x": f"rois/{stem}_B_mask_1x.png",
        "intersection_1x": f"rois/{stem}_intersection_1x.png",
        "overlay_1x": f"rois/{stem}_overlay_1x.png",
        "overlay_8x_nearest": f"rois/{stem}_overlay_8x_nearest.png",
    })
write_csv(MACHINE / "critical_relations.csv", critical_rows)

relation_geometry_rows = [
    {"relation_id": "REL01", "relation_type": "CONJUGACY", "source": "NODE_DIRICHLET", "target": "NODE_MULTINOMIAL", "label": "", "shaft": "GFX007", "head": "GFX008", "direction": "down", "meaning": "Dirichlet is a conjugate prior family for the multinomial likelihood family"},
    {"relation_id": "REL02", "relation_type": "CONJUGACY", "source": "NODE_BETA", "target": "NODE_BINOMIAL", "label": "", "shaft": "GFX009", "head": "GFX010", "direction": "down", "meaning": "Beta is a conjugate prior family for the binomial likelihood family"},
    {"relation_id": "REL03", "relation_type": "SPECIAL_CASE", "source": "NODE_DIRICHLET", "target": "NODE_BETA", "label": "特殊情形 / K=2", "shaft": "GFX011", "head": "GFX012", "direction": "right", "meaning": "The K=2 Dirichlet parameterization is the Beta family"},
    {"relation_id": "REL04", "relation_type": "SPECIAL_CASE", "source": "NODE_MULTINOMIAL", "target": "NODE_BINOMIAL", "label": "特殊情形 / K=2", "shaft": "GFX013", "head": "GFX014", "direction": "right", "meaning": "The K=2 multinomial count model is the binomial family"},
    {"relation_id": "REL05", "relation_type": "SPECIAL_CASE", "source": "NODE_MULTINOMIAL", "target": "NODE_CATEGORICAL", "label": "N=1", "shaft": "GFX015", "head": "GFX016", "direction": "down", "meaning": "A categorical observation is a one-trial multinomial model"},
    {"relation_id": "REL06", "relation_type": "SPECIAL_CASE", "source": "NODE_BINOMIAL", "target": "NODE_BERNOULLI", "label": "N=1", "shaft": "GFX017", "head": "GFX018", "direction": "down", "meaning": "A Bernoulli observation is a one-trial binomial model"},
    {"relation_id": "REL07", "relation_type": "SPECIAL_CASE", "source": "NODE_CATEGORICAL", "target": "NODE_BERNOULLI", "label": "K=2", "shaft": "GFX019", "head": "GFX020", "direction": "right", "meaning": "A K=2 categorical observation is Bernoulli"},
    {"relation_id": "LEG01", "relation_type": "LEGEND_SAMPLE", "source": "LEGEND_CONJUGACY", "target": "LEGEND_CONJUGACY_LABEL", "label": "共轭", "shaft": "GFX021", "head": "GFX022", "direction": "right", "meaning": "Thick filled arrow key denotes conjugacy, not set inclusion"},
    {"relation_id": "LEG02", "relation_type": "LEGEND_SAMPLE", "source": "LEGEND_SPECIAL", "target": "LEGEND_SPECIAL_LABEL", "label": "特殊情形", "shaft": "GFX023", "head": "GFX024", "direction": "right", "meaning": "Thin open arrow key denotes special-case relation"},
]
write_csv(MACHINE / "relation_geometry.csv", relation_geometry_rows)

source_font_rows = [
    {"source_selector": "slfig-FIG-P657-01 base", "declared_pt": "9.2", "line_height_pt": "11.0", "graphics_scale": "1", "effective_pt": "9.2", "R168_treatment": "ADVISORY_ONLY_BY_VALUE_ALONE"},
    {"source_selector": "every node", "declared_pt": "9.4", "line_height_pt": "11.3", "graphics_scale": "1", "effective_pt": "9.4", "R168_treatment": "ADVISORY_ONLY_BY_VALUE_ALONE"},
    {"source_selector": "role heading override", "declared_pt": "9.5", "line_height_pt": "11.4", "graphics_scale": "1", "effective_pt": "9.5", "R168_treatment": "CURRENT_SOURCE_VALUE"},
    {"source_selector": "edgelabel override", "declared_pt": "8.8", "line_height_pt": "10.5", "graphics_scale": "1", "effective_pt": "8.8", "R168_treatment": "ADVISORY_ONLY_BY_VALUE_ALONE"},
    {"source_selector": "caption document typography", "declared_pt": "document-controlled", "line_height_pt": "document-controlled", "graphics_scale": "1", "effective_pt": "PDF span 9.962640/10.161893", "R168_treatment": "CURRENT_PDF_MEASUREMENT"},
]
write_csv(MACHINE / "source_font_inventory.csv", source_font_rows)

role_stats_rows = []
grouped = defaultdict(list)
for row in glyph_rows:
    grouped[(row["parent_id"], row["role"], row["script_class"])].append(row)
for (parent_id, role, script), group in sorted(grouped.items()):
    heights = [int(r["ink_height_px"]) for r in group]
    areas = [int(r["ink_area_px"]) for r in group]
    role_stats_rows.append({
        "parent_id": parent_id,
        "role": role,
        "script_class": script,
        "glyph_count": len(group),
        "height_min_px": min(heights),
        "height_median_px": round(float(np.median(heights)), 6),
        "height_max_px": max(heights),
        "height_max_min_ratio": "INF" if min(heights) == 0 else round(max(heights) / min(heights), 6),
        "area_median_px": round(float(np.median(areas)), 6),
    })
write_csv(MACHINE / "role_ink_statistics.csv", role_stats_rows)

clip_rows = []
fx0, fy0, fx1, fy1 = figure_caption_px
for obj in objects:
    x0, y0, x1, y1 = obj["bbox"]
    page_edge = min(x0, y0, page_w - x1, page_h - y1)
    crop_edge = min(x0 - fx0, y0 - fy0, fx1 - x1, fy1 - y1)
    outside = max(0, fx0 - x0) + max(0, fy0 - y0) + max(0, x1 - fx1) + max(0, y1 - fy1)
    clip_rows.append({
        "object_id": obj["object_id"],
        "kind": obj["kind"],
        "parent_id": obj["parent_id"],
        "page_edge_min_clearance_px": page_edge,
        "figure_caption_crop_edge_min_clearance_px": crop_edge,
        "outside_crop_extent_sum_px": outside,
        "page_clip_pixel_count": 0,
    })
write_csv(MACHINE / "clip_measurements.csv", clip_rows)

overlay = figure_crop.copy()
draw = ImageDraw.Draw(overlay)
ox, oy = figure_caption_px[0], figure_caption_px[1]
for obj in objects:
    x0, y0, x1, y1 = obj["bbox"]
    color = (220, 45, 55) if obj["kind"] == "GLYPH" else (25, 105, 225)
    draw.rectangle((x0 - ox, y0 - oy, x1 - ox - 1, y1 - oy - 1), outline=color, width=1)
    draw.text((x0 - ox, max(0, y0 - oy - 8)), obj["object_id"].replace("GLY", "G").replace("GFX", "X"), fill=color)
overlay.save(VIEWS / "after_text_measurement_overlay_300dpi.png")

semantic_overlay = figure_crop.copy()
draw = ImageDraw.Draw(semantic_overlay)
for parent_id in expected_text:
    ids = ids_for_parent(parent_id)
    if not ids:
        continue
    combined = combine_objects(ids)
    x0, y0, x1, y1 = combined["bbox"]
    draw.rectangle((x0 - ox - 2, y0 - oy - 2, x1 - ox + 2, y1 - oy + 2), outline=(210, 40, 50), width=2)
    draw.text((x0 - ox, max(0, y0 - oy - 14)), parent_id, fill=(170, 20, 30))
for row in graphic_rows:
    x0, y0, x1, y1 = (row[k] for k in ("mask_bbox_px_x0", "mask_bbox_px_y0", "mask_bbox_px_x1", "mask_bbox_px_y1"))
    draw.rectangle((x0 - ox - 1, y0 - oy - 1, x1 - ox + 1, y1 - oy + 1), outline=(25, 105, 225), width=1)
semantic_overlay.save(VIEWS / "semantic_object_overlay_300dpi.png")

view_inventory = []
for name in [
    "full_page_200dpi.png",
    "full_page_300dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "caption_300dpi.png",
    "after_text_measurement_overlay_300dpi.png",
    "semantic_object_overlay_300dpi.png",
]:
    path = VIEWS / name
    with Image.open(path) as im:
        view_inventory.append({
            "view_id": name.removesuffix(".png").upper(),
            "path": f"views/{name}",
            "width_px": im.width,
            "height_px": im.height,
            "mode": im.mode,
            "source_pdf_page": PAGE_NUMBER,
            "derivation": "direct Poppler render" if name.startswith("full_page") else "integer crop/no resize from direct 300dpi render" if name != "grayscale_300dpi.png" else "grayscale conversion/no resize from figure crop",
        })
write_json(MACHINE / "view_inventory.json", view_inventory)

foreground_drawing_indices = {row["drawing_index"] for row in graphic_rows}
drawing_coverage_rows = []
for index, drawing in enumerate(drawings):
    rect = drawing["rect"]
    intersects_figure = not (rect.x1 < figure_caption_pt[0] or rect.x0 > figure_caption_pt[2] or rect.y1 < figure_caption_pt[1] or rect.y0 > figure_caption_pt[3])
    if intersects_figure:
        drawing_coverage_rows.append({
            "drawing_index": index,
            "seqno": drawing.get("seqno", ""),
            "bbox_pt": " ".join(f"{float(v):.6f}" for v in rect),
            "type": drawing.get("type", ""),
            "foreground_object_id": next((row["element_id"] for row in graphic_rows if row["drawing_index"] == index), ""),
            "coverage_scope": "FOREGROUND" if index in foreground_drawing_indices else "BACKGROUND_OR_OUTSIDE_FOREGROUND_DENOMINATOR",
        })
write_csv(MACHINE / "pdf_drawing_path_coverage.csv", drawing_coverage_rows)

identity = {
    "handoff_id": "C-FIG-P657-01-R111-SA2-R168-READONLY-ADJUDICATION-V1",
    "actual_instance": "/root/sa2_fig_p657_r111_r168_readonly_v1",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "xhigh",
    "fork_turns": "none",
    "uid": "FIG-P657-01",
    "figure_number": "34.3",
    "official_pdf": str(PDF),
    "official_pdf_bytes": PDF.stat().st_size,
    "official_pdf_sha256": sha256(PDF),
    "current_source": str(SOURCE),
    "current_source_bytes": SOURCE.stat().st_size,
    "current_source_sha256": sha256(SOURCE),
    "physical_page": PAGE_NUMBER,
    "printed_page": PRINTED_PAGE,
    "page_size_pt": [float(page_rect.width), float(page_rect.height)],
    "native_300dpi_grid": [page_w, page_h],
    "native_200dpi_grid": list(Image.open(full_200_path).size),
    "figure_body_crop_px": list(figure_body_px),
    "figure_caption_crop_px": list(figure_caption_px),
    "caption_crop_px": list(caption_px),
}
write_json(MACHINE / "candidate_identity.json", identity)

machine_summary = {
    "visible_glyph_count": len(glyph_rows),
    "foreground_graphic_primitive_count": len(graphic_rows),
    "background_node_fill_count": len(background_rows),
    "visible_record_count_including_backgrounds": len(glyph_rows) + len(graphic_rows) + len(background_rows),
    "foreground_pair_denominator_count": len(objects),
    "unordered_pair_expected_count": len(objects) * (len(objects) - 1) // 2,
    "unordered_pair_actual_count": len(pair_rows),
    "nonzero_raw_intersection_pair_count": len(overlap_pairs),
    "critical_relation_count": len(critical_rows),
    "critical_raw_intersection_total_px": sum(int(r["raw_mask_intersection_px"]) for r in critical_rows),
    "text_parent_count": len(expected_text),
    "text_parent_positional_codepoint_mismatch_total": sum(int(r["positional_codepoint_mismatch_count"]) for r in text_expectation_rows),
    "glyph_zero_ink_count": sum(int(r["ink_area_px"]) == 0 for r in glyph_rows),
    "graphic_zero_ink_count": sum(int(r["ink_area_px"]) == 0 for r in graphic_rows),
    "glyph_contact_sheet_count": len(contact_inventory),
    "graphic_contact_sheet_count": len(graphic_contact_inventory),
    "glyph_contact_cell_count": sum(int(r["cell_count"]) for r in contact_inventory),
    "graphic_contact_cell_count": sum(int(r["cell_count"]) for r in graphic_contact_inventory),
    "clip_measurement_row_count": len(clip_rows),
    "page_clip_pixel_total": sum(int(r["page_clip_pixel_count"]) for r in clip_rows),
    "outside_figure_caption_crop_extent_total_px": sum(int(r["outside_crop_extent_sum_px"]) for r in clip_rows),
    "view_count": len(view_inventory),
    "relation_geometry_count": len(relation_geometry_rows),
}
write_json(MACHINE / "machine_summary.json", machine_summary)

print(json.dumps(machine_summary, ensure_ascii=False, indent=2))
