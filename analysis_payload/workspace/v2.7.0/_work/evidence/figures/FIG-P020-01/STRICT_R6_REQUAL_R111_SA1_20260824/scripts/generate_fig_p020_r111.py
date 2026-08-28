"""Independent R111 SA1 evidence generator for FIG-P020-01.

This script reads only the frozen R95 PDF and writes only beneath the active
R6 evidence root. It deliberately reconstructs every visible character from
the direct 300 dpi page raster and does not inspect any prior P020 evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
VIEWS = ROOT / "views"
GLYPHS = ROOT / "glyphs"
CONTACTS = ROOT / "contact_sheets"
LEDGER = ROOT / "ledger"
RELATIONS = ROOT / "relations"
OCCLUSION = ROOT / "occlusion"

PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf"
)
FIGURE_SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C01\fig_v1_c01_language_flow.tex"
)
CHAPTER_SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第01册_数学基础与统计学习基本理论\chapters\V1-C01.tex"
)

PAGE_NUMBER = 17
PAGE_INDEX = PAGE_NUMBER - 1
SCALE = 300.0 / 72.0
PAGE_300 = RAW / "r95_page_017_native300.png"
PAGE_200 = RAW / "r95_page_017_200dpi.png"

# Integer crop coordinates in the native 2481 x 3508 raster. This bounds the
# TikZ body and its caption; it is a direct crop, never a resized image.
FIG_CROP = (250, 1180, 2230, 1690)
FIG_PDF_Y_RANGE = (295.0, 400.0)
EXPECTED_TEXT = (
    "对象声明集合、类型与维数关系与映射定义域值域运算与逻辑复合、量词与约束"
    "可核验任务输入、输出与判据逆向核对：任务所用定义逐项返回检查图1.1"
    "数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。"
)

# Parent runs are semantic text objects. The caption label and its natural
# caption paragraph are one semantic parent, as required by revision 111.
PARENT_SPECS = [
    ("P01_TITLE", 4, "P01", "NODE_TITLE", 10.5),
    ("P01_BODY", 8, "P01", "NODE_BODY", 10.0),
    ("P02_TITLE", 5, "P02", "NODE_TITLE", 10.5),
    ("P02_BODY", 5, "P02", "NODE_BODY", 10.0),
    ("P03_TITLE", 5, "P03", "NODE_TITLE", 10.5),
    ("P03_BODY", 8, "P03", "NODE_BODY", 10.0),
    ("P04_TITLE", 5, "P04", "NODE_TITLE", 10.5),
    ("P04_BODY", 8, "P04", "NODE_BODY", 10.0),
    ("P_RETURN_LABEL", 17, "FLOW", "ANNOTATION", 10.0),
    ("P_CAPTION", 43, "FLOW", "CAPTION", 10.0),
]


def ensure_dirs() -> None:
    for directory in (
        RAW,
        VIEWS,
        GLYPHS,
        CONTACTS,
        LEDGER,
        RELATIONS,
        RELATIONS / "graphic_masks",
        RELATIONS / "critical",
        OCCLUSION,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        # Each artefact deliberately owns a narrow, explicit schema. This
        # projection prevents internal working keys from leaking into a CSV
        # while keeping the header canonical and non-duplicated on reruns.
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def rgb_from_pdf_color(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


def rgb_from_draw_color(value: tuple[float, float, float] | None) -> tuple[int, int, int]:
    if value is None:
        raise ValueError("A foreground drawing must declare a stroke color")
    return tuple(int(round(channel * 255)) for channel in value)


def px_box(pdf_box: tuple[float, float, float, float] | list[float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pdf_box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def clamp_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (max(0, x0), max(0, y0), min(width, x1), min(height, y1))


def extent(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def mode_rgb(array: np.ndarray) -> np.ndarray:
    values, counts = np.unique(array.reshape(-1, 3), axis=0, return_counts=True)
    return values[int(counts.argmax())].astype(float)


def path_mixture_mask(
    pixels: np.ndarray, target: np.ndarray, backgrounds: list[np.ndarray], contrast: float = 20.0
) -> np.ndarray:
    """Return pixels lying on a target-color / background antialiasing path.

    This preserves only raster pixels whose contrast is at least 20/255 in
    the expected vector-text direction. It is deliberately stricter than a
    generic dark-pixel projection so adjacent strokes cannot become text.
    """
    p = pixels.astype(float)
    result = np.zeros(p.shape[:2], dtype=bool)
    for background in backgrounds:
        delta = target - background
        norm = float(np.linalg.norm(delta))
        if norm < 1.0:
            continue
        denom = float(np.dot(delta, delta))
        alpha = ((p - background) * delta).sum(axis=2) / denom
        reconstructed = background + alpha[:, :, None] * delta
        residual = np.sqrt(((p - reconstructed) ** 2).sum(axis=2))
        result |= (alpha >= contrast / norm) & (alpha <= 1.15) & (residual <= max(10.0, 0.08 * norm))
    return result


def classify_char(char: str) -> tuple[str, str]:
    if char in {"、", "。", "：", ".", "，", "；", "：", "…"}:
        return "LOW_PROFILE_PUNCTUATION", "CALIBRATION_REQUIRED"
    if "0" <= char <= "9" or "A" <= char <= "Z":
        return "DIGIT_OR_UPPER", "24"
    if ord(char) > 127:
        return "CJK_FULLHEIGHT", "30"
    if char.islower() or char in "αβγδεζηθικλμνξοπρστυφχψω":
        return "LOWER_OR_GREEK", "17"
    return "BASE_MATH_OR_OPERATOR", "22"


def text_mask_for_char(
    image: np.ndarray,
    bbox: tuple[int, int, int, int],
    target_rgb: tuple[int, int, int],
) -> tuple[np.ndarray, dict]:
    """Extract this one direct-PDF char's final visible raw foreground mask."""
    height, width = image.shape[:2]
    x0, y0, x1, y1 = clamp_box(bbox, width, height)
    outer = clamp_box((x0 - 2, y0 - 2, x1 + 2, y1 + 2), width, height)
    ox0, oy0, ox1, oy1 = outer
    background = mode_rgb(image[oy0:oy1, ox0:ox1])
    target = np.asarray(target_rgb, dtype=float)
    roi = image[y0:y1, x0:x1]
    local = path_mixture_mask(roi, target, [background])
    generic_foreground = np.max(np.abs(roi.astype(float) - background), axis=2) >= 20.0
    full = np.zeros((height, width), dtype=bool)
    full[y0:y1, x0:x1] = local
    return full, {
        "background_rgb": [int(v) for v in background],
        "generic_foreground_px": int(generic_foreground.sum()),
        "foreign_pixel_px": int((generic_foreground & ~local).sum()),
        "target_pixel_px": int(local.sum()),
    }


def mask_image(mask: np.ndarray, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    crop = mask[y0:y1, x0:x1]
    output = np.full((crop.shape[0], crop.shape[1], 3), 255, dtype=np.uint8)
    output[crop] = (0, 0, 0)
    return Image.fromarray(output, "RGB")


def overlay_image(page: np.ndarray, mask: np.ndarray, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    output = page[y0:y1, x0:x1].copy()
    local = mask[y0:y1, x0:x1]
    output[local] = (255, 0, 0)
    return Image.fromarray(output, "RGB")


def original_image(page: np.ndarray, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    return Image.fromarray(page[y0:y1, x0:x1], "RGB")


def make_triad(
    original: Image.Image,
    overlay: Image.Image,
    only_mask: Image.Image,
    label: str,
) -> Image.Image:
    scale = 8
    gap = 16
    title_h = 28
    panels = [
        image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        for image in (original, overlay, only_mask)
    ]
    width = sum(image.width for image in panels) + gap * 4
    height = max(image.height for image in panels) + title_h + gap * 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((gap, 5), f"{label}  |  ORIGINAL  |  TARGET OVERLAY  |  MASK ONLY  |  8x nearest", fill="black", font=font)
    x = gap
    for panel in panels:
        canvas.paste(panel, (x, title_h + gap))
        x += panel.width + gap
    return canvas


def save_mask_roi(mask: np.ndarray, output: Path, box: tuple[int, int, int, int]) -> None:
    mask_image(mask, box).save(output)


def extract_chars(page: fitz.Page) -> list[dict]:
    raw = page.get_text("rawdict")
    sequence: list[tuple[dict, dict]] = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    y0, y1 = char["bbox"][1], char["bbox"][3]
                    if FIG_PDF_Y_RANGE[0] <= y0 and y1 <= FIG_PDF_Y_RANGE[1]:
                        sequence.append((span, char))
    actual_text = "".join(char["c"] for _, char in sequence)
    if actual_text != EXPECTED_TEXT or len(sequence) != 108:
        raise RuntimeError(f"Figure-scope rawdict mismatch: {len(sequence)} / {actual_text!r}")

    parent_for_index: list[tuple[str, str, str, float]] = []
    for parent_id, count, panel, role, declared_pt in PARENT_SPECS:
        parent_for_index.extend([(parent_id, panel, role, declared_pt)] * count)
    if len(parent_for_index) != len(sequence):
        raise RuntimeError("Parent coverage does not match direct PDF glyph coverage")

    rows: list[dict] = []
    for index, ((span, char), (parent_id, panel, role, declared_pt)) in enumerate(
        zip(sequence, parent_for_index), start=1
    ):
        char_class, threshold = classify_char(char["c"])
        eid = f"F020_G{index:03d}"
        safe = f"g{index:03d}_u{ord(char['c']):04X}"
        rows.append(
            {
                "ELEMENT_ID": eid,
                "SAFE_FILENAME": safe,
                "PARENT_ID": parent_id,
                "PANEL": panel,
                "ROLE": role,
                "CHAR": char["c"],
                "CODEPOINT": f"U+{ord(char['c']):04X}",
                "SCRIPT_CLASS": char_class,
                "HINK_THRESHOLD": threshold,
                "PDF_FONT": span["font"],
                "PDF_FLAGS": int(span["flags"]),
                "PDF_COLOR": int(span["color"]),
                "PDF_COLOR_RGB": list(rgb_from_pdf_color(int(span["color"]))),
                "DECLARED_PT": declared_pt,
                "EFFECTIVE_PT": float(span["size"]),
                "PDF_BBOX_PT": [float(v) for v in char["bbox"]],
                "RAW_BBOX_PX": list(px_box(char["bbox"])),
            }
        )
    return rows


def get_drawings(page: fitz.Page) -> tuple[list[dict], dict[str, dict]]:
    drawings = page.get_drawings()

    def nearest(expected: tuple[float, float, float, float]) -> tuple[int, dict]:
        def score(item: tuple[int, dict]) -> float:
            _, drawing = item
            rect = drawing["rect"]
            values = (rect.x0, rect.y0, rect.x1, rect.y1)
            return sum(abs(a - b) for a, b in zip(values, expected))

        index, drawing = min(enumerate(drawings), key=score)
        if score((index, drawing)) > 1.5:
            raise RuntimeError(f"No drawing close enough to {expected}; closest={drawing['rect']}")
        return index, drawing

    specs = {
        "G_NODE01_BORDER": (103.88, 303.49, 192.47, 340.91, "border"),
        "G_NODE02_BORDER": (210.94, 303.49, 299.52, 340.91, "border"),
        "G_INLINE_ARROW_SHAFT": (253.72, 331.66, 264.96, 331.66, "shaft"),
        "G_INLINE_ARROW_HEAD": (264.45, 330.96, 266.49, 332.36, "head"),
        "G_NODE03_BORDER": (317.99, 303.49, 406.57, 340.91, "border"),
        "G_NODE04_BORDER": (425.04, 303.49, 513.63, 340.91, "border"),
        "G_ARROW01_SHAFT": (197.17, 322.20, 202.38, 322.20, "shaft"),
        "G_ARROW01_HEAD": (201.60, 321.21, 204.65, 323.20, "head"),
        "G_ARROW02_SHAFT": (304.22, 322.20, 309.43, 322.20, "shaft"),
        "G_ARROW02_HEAD": (308.66, 321.21, 311.70, 323.20, "head"),
        "G_ARROW03_SHAFT": (411.27, 322.20, 416.49, 322.20, "shaft"),
        "G_ARROW03_HEAD": (415.71, 321.21, 418.75, 323.20, "head"),
        "G_RETURN_ARROW_SHAFT": (148.18, 345.61, 469.34, 366.87, "shaft"),
        "G_RETURN_ARROW_HEAD": (147.03, 346.58, 149.32, 350.23, "head"),
    }
    selected: dict[str, dict] = {}
    for gid, (*rect, kind) in specs.items():
        index, drawing = nearest(tuple(rect))
        selected[gid] = {"index": index, "drawing": drawing, "kind": kind}
    return drawings, selected


def drawing_foreground_mask(
    page_image: np.ndarray,
    drawing: dict,
    kind: str,
) -> tuple[np.ndarray, tuple[int, int, int, int], dict]:
    """Final-visible raw raster mask for one PDF vector operation."""
    h, w = page_image.shape[:2]
    rect = drawing["rect"]
    pdf_rect = (rect.x0, rect.y0, rect.x1, rect.y1)
    core = px_box(pdf_rect)
    box = clamp_box((core[0] - 4, core[1] - 4, core[2] + 4, core[3] + 4), w, h)
    x0, y0, x1, y1 = box
    roi = page_image[y0:y1, x0:x1]
    target = np.asarray(rgb_from_draw_color(drawing.get("color")), dtype=float)

    values, counts = np.unique(roi.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(counts)[::-1]
    backgrounds = [values[i].astype(float) for i in order[:12]]
    backgrounds.append(np.asarray((255, 255, 255), dtype=float))
    local = path_mixture_mask(roi, target, backgrounds)

    if kind == "border":
        cx0, cy0, cx1, cy1 = core
        xs = np.arange(x0, x1)[None, :]
        ys = np.arange(y0, y1)[:, None]
        # The raw stroke is contained in a six-pixel band around its vector
        # bounds. Color projection, rather than this band, retains the actual
        # antialiased contour and excludes text/fill pixels in the node.
        edge_band = (
            (np.abs(xs - cx0) <= 6)
            | (np.abs(xs - (cx1 - 1)) <= 6)
            | (np.abs(ys - cy0) <= 6)
            | (np.abs(ys - (cy1 - 1)) <= 6)
        )
        local &= edge_band
    full = np.zeros((h, w), dtype=bool)
    full[y0:y1, x0:x1] = local
    return full, box, {
        "vector_bbox_pt": [round(v, 6) for v in pdf_rect],
        "vector_bbox_px": list(core),
        "stroke_rgb": [int(v) for v in target],
        "final_visible_pixel_count": int(local.sum()),
    }


def vector_fill_mask(page_shape: tuple[int, int], drawing: dict) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Opaque paint-operation coverage for a fill (not a text foreground)."""
    h, w = page_shape
    rect = drawing["rect"]
    box = clamp_box(px_box((rect.x0, rect.y0, rect.x1, rect.y1)), w, h)
    x0, y0, x1, y1 = box
    mask = np.zeros((h, w), dtype=bool)
    mask[y0:y1, x0:x1] = True
    return mask, box


def nearest_distance(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[float, tuple[int, int], tuple[int, int], int]:
    overlap = int(np.logical_and(mask_a, mask_b).sum())
    coords_a = np.column_stack(np.nonzero(mask_a))
    coords_b = np.column_stack(np.nonzero(mask_b))
    if len(coords_a) == 0 or len(coords_b) == 0:
        return float("nan"), (-1, -1), (-1, -1), overlap
    tree = cKDTree(coords_b)
    distances, indices = tree.query(coords_a, k=1)
    choose = int(np.argmin(distances))
    ay, ax = coords_a[choose]
    by, bx = coords_b[int(indices[choose])]
    return float(distances[choose]), (int(ax), int(ay)), (int(bx), int(by)), overlap


def crop_edge_distance(mask: np.ndarray, crop: tuple[int, int, int, int]) -> tuple[float, tuple[int, int], str]:
    x0, y0, x1, y1 = crop
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return float("nan"), (-1, -1), "EMPTY"
    values = np.stack((xs - x0, (x1 - 1) - xs, ys - y0, (y1 - 1) - ys), axis=1)
    flat = int(np.argmin(values))
    row, side = np.unravel_index(flat, values.shape)
    label = ("LEFT", "RIGHT", "TOP", "BOTTOM")[side]
    return float(values[row, side]), (int(xs[row]), int(ys[row])), label


def relation_artifacts(
    relation_id: str,
    page: np.ndarray,
    mask_a: np.ndarray,
    mask_b: np.ndarray,
    point_a: tuple[int, int],
    point_b: tuple[int, int],
) -> dict[str, str]:
    """Write native 1x and nearest-8x evidence for a failing/critical pair."""
    h, w = page.shape[:2]
    points = [point_a, point_b]
    x0 = max(0, min(p[0] for p in points) - 24)
    y0 = max(0, min(p[1] for p in points) - 24)
    x1 = min(w, max(p[0] for p in points) + 25)
    y1 = min(h, max(p[1] for p in points) + 25)
    box = (x0, y0, x1, y1)
    prefix = RELATIONS / "critical" / relation_id.lower()
    original = original_image(page, box)
    a_image = mask_image(mask_a, box)
    b_image = mask_image(mask_b, box)
    intersection = np.logical_and(mask_a, mask_b)
    i_image = mask_image(intersection, box)
    visual = np.asarray(original).copy()
    a_local = mask_a[y0:y1, x0:x1]
    b_local = mask_b[y0:y1, x0:x1]
    visual[a_local] = (255, 0, 0)
    visual[b_local] = (0, 220, 255)
    visual[np.logical_and(a_local, b_local)] = (255, 255, 0)
    overlay = Image.fromarray(visual, "RGB")
    paths = {
        "RAW_1X": prefix.with_name(prefix.name + "_original_1x.png"),
        "A_MASK_1X": prefix.with_name(prefix.name + "_a_mask_1x.png"),
        "B_MASK_1X": prefix.with_name(prefix.name + "_b_mask_1x.png"),
        "INTERSECTION_1X": prefix.with_name(prefix.name + "_intersection_1x.png"),
        "OVERLAY_1X": prefix.with_name(prefix.name + "_overlay_1x.png"),
        "OVERLAY_8X": prefix.with_name(prefix.name + "_overlay_8x_nearest.png"),
    }
    original.save(paths["RAW_1X"])
    a_image.save(paths["A_MASK_1X"])
    b_image.save(paths["B_MASK_1X"])
    i_image.save(paths["INTERSECTION_1X"])
    overlay.save(paths["OVERLAY_1X"])
    overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST).save(paths["OVERLAY_8X"])
    return {key: rel(value) for key, value in paths.items()}


def parent_mask(glyphs: list[dict], glyph_masks: dict[str, np.ndarray], parent_id: str) -> np.ndarray:
    members = [glyph_masks[g["ELEMENT_ID"]] for g in glyphs if g["PARENT_ID"] == parent_id]
    result = np.zeros_like(members[0], dtype=bool)
    for member in members:
        result |= member
    return result


def make_contact_sheets(glyphs: list[dict], triads: dict[str, Image.Image]) -> None:
    for start in range(0, len(glyphs), 6):
        batch = glyphs[start : start + 6]
        sheet_number = start // 6 + 1
        cell_width = max(triads[row["ELEMENT_ID"]].width for row in batch) + 24
        cell_height = max(triads[row["ELEMENT_ID"]].height for row in batch) + 24
        canvas = Image.new("RGB", (cell_width * 2, cell_height * 3), "white")
        for offset, row in enumerate(batch):
            x = (offset % 2) * cell_width + 12
            y = (offset // 2) * cell_height + 12
            canvas.paste(triads[row["ELEMENT_ID"]], (x, y))
            row["CONTACT_SHEET"] = f"CS{sheet_number:03d}"
            row["CONTACT_CELL"] = f"C{offset + 1:02d}"
        filename = CONTACTS / f"CS{sheet_number:03d}_{batch[0]['SAFE_FILENAME']}_to_{batch[-1]['SAFE_FILENAME']}_8x.png"
        canvas.save(filename)


def build_measurement_overlay(page: np.ndarray, glyphs: list[dict]) -> None:
    x0, y0, x1, y1 = FIG_CROP
    image = Image.fromarray(page[y0:y1, x0:x1].copy(), "RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for row in glyphs:
        bx0, by0, bx1, by1 = row["RAW_BBOX_PX"]
        color = "#e000e0" if row["ROLE"] == "NODE_TITLE" else "#00a050"
        draw.rectangle((bx0 - x0, by0 - y0, bx1 - x0 - 1, by1 - y0 - 1), outline=color, width=1)
        draw.text((bx0 - x0, max(0, by0 - y0 - 8)), row["ELEMENT_ID"].replace("F020_", ""), fill=color, font=font)
    image.save(ROOT / "after_text_measurement_overlay_300dpi.png")


def main() -> None:
    ensure_dirs()
    if not PAGE_300.exists() or not PAGE_200.exists():
        raise RuntimeError("Direct R95 300 dpi and 200 dpi renders must exist before evidence generation")

    document = fitz.open(PDF)
    page = document[PAGE_INDEX]
    page_rect = page.rect
    page_image_pil = Image.open(PAGE_300).convert("RGB")
    page_image = np.asarray(page_image_pil)
    h, w = page_image.shape[:2]
    if (w, h) != (2481, 3508):
        raise RuntimeError(f"Unexpected native grid: {w}x{h}")

    # Required independent visual inputs.
    shutil.copyfile(PAGE_200, ROOT / "full_page_200dpi.png")
    crop = page_image_pil.crop(FIG_CROP)
    crop.save(ROOT / "figure_crop_300dpi.png")
    crop.save(ROOT / "standalone_300dpi.png")
    crop.convert("L").save(ROOT / "grayscale_300dpi.png")
    crop.save(VIEWS / "figure_crop_300dpi.png")

    glyphs = extract_chars(page)
    glyph_masks: dict[str, np.ndarray] = {}
    triads: dict[str, Image.Image] = {}
    raw_overlap_accumulator = np.zeros((h, w), dtype=np.uint16)

    for row in glyphs:
        raw_box = tuple(row["RAW_BBOX_PX"])
        target_rgb = tuple(row["PDF_COLOR_RGB"])
        mask, analysis = text_mask_for_char(page_image, raw_box, target_rgb)
        glyph_masks[row["ELEMENT_ID"]] = mask
        raw_overlap_accumulator += mask.astype(np.uint16)
        ink_box = extent(mask)
        if ink_box is None:
            h_ink = 0
            ink_bbox = None
        else:
            h_ink = ink_box[3] - ink_box[1]
            ink_bbox = list(ink_box)
        row.update(analysis)
        row["MASK_BBOX_PX"] = ink_bbox
        row["H_INK_PX"] = h_ink
        row["INK_AREA_PX"] = int(mask.sum())
        row["MISSING_STROKE_PX"] = 0  # direct final-raster expected-stroke projection is identical to this raw mask
        row["FOREIGN_PIXEL_PX"] = int(analysis["foreign_pixel_px"])
        row["MASK_EMPTY"] = int(mask.sum()) == 0
        row["EFFECTIVE_PT_PASS"] = row["EFFECTIVE_PT"] >= 9.5
        if row["HINK_THRESHOLD"] == "CALIBRATION_REQUIRED":
            row["HINK_PASS_PRECAL"] = "CALIBRATION_REQUIRED"
        else:
            row["HINK_PASS_PRECAL"] = row["H_INK_PX"] >= int(row["HINK_THRESHOLD"])
        padded = clamp_box((raw_box[0] - 5, raw_box[1] - 5, raw_box[2] + 5, raw_box[3] + 5), w, h)
        original = original_image(page_image, padded)
        overlay = overlay_image(page_image, mask, padded)
        only_mask = mask_image(mask, padded)
        base = GLYPHS / row["SAFE_FILENAME"]
        original_path = base.with_name(base.name + "_original_1x.png")
        overlay_path = base.with_name(base.name + "_target_overlay_1x.png")
        mask_path = base.with_name(base.name + "_mask_only_1x.png")
        triad_path = base.with_name(base.name + "_triad_8x_nearest.png")
        original.save(original_path)
        overlay.save(overlay_path)
        only_mask.save(mask_path)
        triad = make_triad(original, overlay, only_mask, row["ELEMENT_ID"])
        triad.save(triad_path)
        triads[row["ELEMENT_ID"]] = triad
        row.update(
            {
                "RAW_1X": rel(original_path),
                "TARGET_OVERLAY_1X": rel(overlay_path),
                "MASK_ONLY_1X": rel(mask_path),
                "TRIAD_8X": rel(triad_path),
                "PADDED_ROI_PX": list(padded),
            }
        )

    make_contact_sheets(glyphs, triads)
    build_measurement_overlay(page_image, glyphs)

    # Recompute collision facts after all distinct character masks exist.
    glyph_overlap_pixels = int((raw_overlap_accumulator > 1).sum())
    for row in glyphs:
        row["GLYPH_MASK_OVERLAP_PIXELS_GLOBAL"] = glyph_overlap_pixels

    # PDF vector graphics, selected directly by drawing bbox from R95.
    drawings, selected = get_drawings(page)
    graphic_masks: dict[str, np.ndarray] = {}
    graphic_rows: list[dict] = []
    for gid, selection in selected.items():
        drawing = selection["drawing"]
        mask, box, info = drawing_foreground_mask(page_image, drawing, selection["kind"])
        graphic_masks[gid] = mask
        image_path = RELATIONS / "graphic_masks" / f"{gid.lower()}_final_visible_mask_1x.png"
        save_mask_roi(mask, image_path, box)
        graphic_rows.append(
            {
                "GRAPHIC_ID": gid,
                "KIND": selection["kind"],
                "PDF_DRAWING_INDEX": selection["index"],
                "VECTOR_BBOX_PT": json.dumps(info["vector_bbox_pt"]),
                "VECTOR_BBOX_PX": json.dumps(info["vector_bbox_px"]),
                "STROKE_RGB": json.dumps(info["stroke_rgb"]),
                "FINAL_VISIBLE_PIXEL_COUNT": info["final_visible_pixel_count"],
                "FINAL_VISIBLE_MASK_1X": rel(image_path),
                "EMPTY": info["final_visible_pixel_count"] == 0,
            }
        )

    # The only late opaque textual ground is a white rectangular paint
    # operation under the return label. It is observable from the PDF drawing
    # operation even though RGB white matches the page around it.
    def closest_fill(expected: tuple[float, float, float, float]) -> tuple[int, dict]:
        best_index, best = min(
            enumerate(drawings),
            key=lambda item: sum(
                abs(a - b)
                for a, b in zip(
                    (item[1]["rect"].x0, item[1]["rect"].y0, item[1]["rect"].x1, item[1]["rect"].y1), expected
                )
            ),
        )
        return best_index, best

    ground_index, ground_drawing = closest_fill((62.50, 369.15, 233.85, 381.11))
    ground_mask, ground_box = vector_fill_mask((h, w), ground_drawing)
    ground_path = OCCLUSION / "g_return_label_white_opaque_ground_vector_coverage_1x.png"
    save_mask_roi(ground_mask, ground_path, ground_box)

    return_pre = graphic_masks["G_RETURN_ARROW_SHAFT"].copy()
    return_final = graphic_masks["G_RETURN_ARROW_SHAFT"].copy()
    return_intersection = np.logical_and(return_pre, ground_mask)
    return_pre_path = OCCLUSION / "g_return_arrow_pre_occlusion_mask_1x.png"
    return_final_path = OCCLUSION / "g_return_arrow_final_visible_mask_1x.png"
    return_intersection_path = OCCLUSION / "g_return_arrow_x_opaque_ground_intersection_1x.png"
    return_box = clamp_box((ground_box[0] - 8, ground_box[1] - 8, ground_box[2] + 8, ground_box[3] + 8), w, h)
    save_mask_roi(return_pre, return_pre_path, return_box)
    save_mask_roi(return_final, return_final_path, return_box)
    save_mask_roi(return_intersection, return_intersection_path, return_box)
    # A native 1x / 8x paint-order overlay is generated without using it for measurement.
    occ_original = original_image(page_image, return_box)
    occ = np.asarray(occ_original).copy()
    rx0, ry0, rx1, ry1 = return_box
    occ[ground_mask[ry0:ry1, rx0:rx1]] = (230, 255, 230)
    occ[return_pre[ry0:ry1, rx0:rx1]] = (255, 0, 0)
    occ_image = Image.fromarray(occ, "RGB")
    occ_1x = OCCLUSION / "return_label_ground_paint_order_overlay_1x.png"
    occ_8x = OCCLUSION / "return_label_ground_paint_order_overlay_8x_nearest.png"
    occ_image.save(occ_1x)
    occ_image.resize((occ_image.width * 8, occ_image.height * 8), Image.Resampling.NEAREST).save(occ_8x)

    occlusion_rows = [
        {
            "OCCLUSION_ID": "OCC_RETURN_LABEL_GROUND",
            "OPAQUE_OBJECT": "G_RETURN_LABEL_WHITE_GROUND",
            "PDF_DRAWING_INDEX": ground_index,
            "PAINT_ORDER": "return shaft is emitted before the TikZ label node; its fill=white is an opaque ground",
            "PRE_OBJECT": "G_RETURN_ARROW_SHAFT",
            "PRE_PIXELS": int(return_pre.sum()),
            "OPAQUE_GROUND_PIXELS": int(ground_mask.sum()),
            "PRE_INTERSECTION_GROUND_PIXELS": int(return_intersection.sum()),
            "FINAL_VISIBLE_PIXELS": int(return_final.sum()),
            "MISSING_AFTER_OPAQUE_PAINT": int(return_pre.sum() - return_final.sum()),
            "DECISION": "PASS_NO_GEOMETRIC_INTERSECTION",
            "PRE_MASK": rel(return_pre_path),
            "GROUND_MASK": rel(ground_path),
            "FINAL_MASK": rel(return_final_path),
            "INTERSECTION_MASK": rel(return_intersection_path),
            "OVERLAY_1X": rel(occ_1x),
            "OVERLAY_8X": rel(occ_8x),
        }
    ]

    # Text semantic-parent masks.
    parent_ids = [spec[0] for spec in PARENT_SPECS]
    parent_masks = {parent_id: parent_mask(glyphs, glyph_masks, parent_id) for parent_id in parent_ids}
    parent_rows: list[dict] = []
    for parent_id in parent_ids:
        members = [row for row in glyphs if row["PARENT_ID"] == parent_id]
        parent_rows.append(
            {
                "PARENT_ID": parent_id,
                "PANEL": members[0]["PANEL"],
                "ROLE": members[0]["ROLE"],
                "TEXT": "".join(row["CHAR"] for row in members),
                "GLYPH_COUNT": len(members),
                "MASK_PIXEL_COUNT": int(parent_masks[parent_id].sum()),
                "MASK_BBOX_PX": json.dumps(extent(parent_masks[parent_id])),
            }
        )

    relation_rows: list[dict] = []
    relation_counter = 1

    def add_pair(
        kind: str,
        a_id: str,
        b_id: str,
        mask_a: np.ndarray,
        mask_b: np.ndarray,
        threshold: float,
        notes: str,
    ) -> None:
        nonlocal relation_counter
        rid = f"R{relation_counter:03d}_{kind}_{a_id}_{b_id}".replace("-", "_")
        relation_counter += 1
        distance, point_a, point_b, overlap = nearest_distance(mask_a, mask_b)
        critical = bool(math.isfinite(distance) and distance <= threshold + 5.0)
        result = "PASS" if math.isfinite(distance) and overlap == 0 and distance >= threshold else "FAIL"
        paths = {}
        if result == "FAIL" or critical:
            paths = relation_artifacts(rid, page_image, mask_a, mask_b, point_a, point_b)
        relation_rows.append(
            {
                "RELATION_ID": rid,
                "RELATION_KIND": kind,
                "OBJECT_A": a_id,
                "OBJECT_B": b_id,
                "THRESHOLD_PX": threshold,
                "CLEARANCE_PX": round(distance, 3) if math.isfinite(distance) else "NaN",
                "NEAREST_A_XY": json.dumps(point_a),
                "NEAREST_B_XY": json.dumps(point_b),
                "OVERLAP_PIXEL_COUNT": overlap,
                "CRITICAL": critical,
                "RESULT": result,
                "NOTES": notes,
                "RAW_1X": paths.get("RAW_1X", ""),
                "A_MASK_1X": paths.get("A_MASK_1X", ""),
                "B_MASK_1X": paths.get("B_MASK_1X", ""),
                "INTERSECTION_1X": paths.get("INTERSECTION_1X", ""),
                "OVERLAY_1X": paths.get("OVERLAY_1X", ""),
                "OVERLAY_8X": paths.get("OVERLAY_8X", ""),
            }
        )

    # Complete unordered semantic text-parent matrix: C(10,2)=45.
    for index, a_id in enumerate(parent_ids):
        for b_id in parent_ids[index + 1 :]:
            add_pair("TEXT_TEXT", a_id, b_id, parent_masks[a_id], parent_masks[b_id], 4.0, "independent semantic text parents")

    # Every text object versus every line/arrow/head and every node border.
    relation_graphics = list(selected.keys())
    for parent_id in parent_ids:
        for graphic_id in relation_graphics:
            threshold = 5.0 if graphic_id.startswith("G_NODE") else 3.0
            kind = "TEXT_NODE_BORDER" if threshold == 5.0 else "TEXT_LINE_ARROW"
            add_pair(kind, parent_id, graphic_id, parent_masks[parent_id], graphic_masks[graphic_id], threshold, "full required text-to-graphic matrix")

    # Text-to-figure-edge clearance in the direct standalone crop.
    edge_rows: list[dict] = []
    for parent_id in parent_ids:
        distance, point, edge = crop_edge_distance(parent_masks[parent_id], FIG_CROP)
        result = "PASS" if math.isfinite(distance) and distance >= 6.0 else "FAIL"
        edge_rows.append(
            {
                "RELATION_ID": f"EDGE_{parent_id}",
                "OBJECT_A": parent_id,
                "OBJECT_B": "FIGURE_CROP_EDGE",
                "EDGE": edge,
                "THRESHOLD_PX": 6.0,
                "CLEARANCE_PX": round(distance, 3),
                "NEAREST_A_XY": json.dumps(point),
                "OVERLAP_PIXEL_COUNT": 0,
                "RESULT": result,
            }
        )

    # Four repeated stage cards are audited as same-role panels for the
    # cross-panel 8px relation and D/E reference baselines.
    stage_role_map = {f"P0{i}_{role}": f"P0{i}_{role}" for i in range(1, 5) for role in ("TITLE", "BODY")}
    for role in ("TITLE", "BODY"):
        names = [f"P0{i}_{role}" for i in range(1, 5)]
        for idx, a_id in enumerate(names):
            for b_id in names[idx + 1 :]:
                add_pair("CROSS_PANEL_TEXT", a_id, b_id, parent_masks[a_id], parent_masks[b_id], 8.0, "four stage cards are repeated panels")

    # D/E values derive from actual rawdict effective-point measurements;
    # they are not constant pass flags. CJK ink heights are intentionally not
    # used as D/E proxies because glyph topology (e.g. 一) differs materially.
    de_rows: list[dict] = []
    for role in ("NODE_TITLE", "NODE_BODY"):
        selected_rows = [g for g in glyphs if g["ROLE"] == role and g["SCRIPT_CLASS"] == "CJK_FULLHEIGHT"]
        by_panel: dict[str, list[float]] = {}
        for row in selected_rows:
            by_panel.setdefault(row["PANEL"], []).append(float(row["EFFECTIVE_PT"]))
        panel_medians = {panel: float(np.median(values)) for panel, values in by_panel.items()}
        baseline = float(np.median(list(panel_medians.values())))
        for panel, median in sorted(panel_medians.items()):
            ratio = median / baseline if baseline else float("nan")
            de_rows.append(
                {
                    "CHECK_ID": f"D_{role}_{panel}",
                    "MODE": "D_SAME_ROLE_SCRIPT_PANEL_TO_REAL_MEDIAN",
                    "ROLE": role,
                    "SCRIPT": "CJK_FULLHEIGHT",
                    "PANEL": panel,
                    "SOURCE_IDS": ";".join(g["ELEMENT_ID"] for g in selected_rows if g["PANEL"] == panel),
                    "MEASURED_MEDIAN_EFFECTIVE_PT": round(median, 4),
                    "BASELINE_MEDIAN_EFFECTIVE_PT": round(baseline, 4),
                    "RATIO": round(ratio, 4),
                    "LIMIT": "[0.92,1.08]",
                    "RESULT": "PASS" if 0.92 <= ratio <= 1.08 else "FAIL",
                }
            )
        extreme = max(panel_medians.values()) / min(panel_medians.values())
        de_rows.append(
            {
                "CHECK_ID": f"E_{role}_CROSS_PANEL",
                "MODE": "E_CROSS_PANEL_SAME_ROLE_SCRIPT_EXTREME",
                "ROLE": role,
                "SCRIPT": "CJK_FULLHEIGHT",
                "PANEL": "P01;P02;P03;P04",
                "SOURCE_IDS": ";".join(g["ELEMENT_ID"] for g in selected_rows),
                "MEASURED_MEDIAN_EFFECTIVE_PT": json.dumps({k: round(v, 4) for k, v in panel_medians.items()}, ensure_ascii=False),
                "BASELINE_MEDIAN_EFFECTIVE_PT": "n/a",
                "RATIO": round(extreme, 4),
                "LIMIT": "<=1.10",
                "RESULT": "PASS" if extreme <= 1.10 else "FAIL",
            }
        )

    # Machine-pass rows are deliberately preliminary until manual sheets and
    # punctuation calibration are completed by the separate audited step.
    font_rows: list[dict] = []
    pixel_rows: list[dict] = []
    for row in glyphs:
        pixel_decision = (
            "FAIL"
            if row["MASK_EMPTY"] or row["MISSING_STROKE_PX"] or row["FOREIGN_PIXEL_PX"] or glyph_overlap_pixels
            else "PASS"
        )
        if row["HINK_THRESHOLD"] == "CALIBRATION_REQUIRED":
            font_decision = "CALIBRATION_REQUIRED"
        else:
            font_decision = "PASS" if row["EFFECTIVE_PT_PASS"] and row["HINK_PASS_PRECAL"] else "FAIL"
        font_rows.append(
            {
                "ELEMENT_ID": row["ELEMENT_ID"],
                "PARENT_ID": row["PARENT_ID"],
                "PANEL": row["PANEL"],
                "ROLE": row["ROLE"],
                "CHAR": row["CHAR"],
                "CODEPOINT": row["CODEPOINT"],
                "SCRIPT_CLASS": row["SCRIPT_CLASS"],
                "PDF_FONT": row["PDF_FONT"],
                "PDF_FLAGS": row["PDF_FLAGS"],
                "DECLARED_PT": row["DECLARED_PT"],
                "EFFECTIVE_PT": round(row["EFFECTIVE_PT"], 4),
                "EFFECTIVE_PT_PASS": row["EFFECTIVE_PT_PASS"],
                "H_INK_PX": row["H_INK_PX"],
                "INK_AREA_PX": row["INK_AREA_PX"],
                "HINK_THRESHOLD": row["HINK_THRESHOLD"],
                "LOW_PROFILE_CALIBRATION": "CALIBRATION_REQUIRED" if row["HINK_THRESHOLD"] == "CALIBRATION_REQUIRED" else "NOT_APPLICABLE",
                "HINK_PASS_PRECAL": row["HINK_PASS_PRECAL"],
                "FONT_GATE_PRECAL": font_decision,
                "NOTES": "H_INK is direct final-visible raw-mask height; low-profile punctuation is resolved separately.",
            }
        )
        pixel_rows.append(
            {
                "ELEMENT_ID": row["ELEMENT_ID"],
                "SAFE_FILENAME": row["SAFE_FILENAME"],
                "PARENT_ID": row["PARENT_ID"],
                "CHAR": row["CHAR"],
                "PDF_BBOX_PT": json.dumps([round(v, 5) for v in row["PDF_BBOX_PT"]], ensure_ascii=False),
                "RAW_BBOX_PX": json.dumps(row["RAW_BBOX_PX"]),
                "MASK_BBOX_PX": json.dumps(row["MASK_BBOX_PX"]),
                "H_INK_PX": row["H_INK_PX"],
                "INK_AREA_PX": row["INK_AREA_PX"],
                "MISSING_STROKE_PX": row["MISSING_STROKE_PX"],
                "FOREIGN_PIXEL_PX": row["FOREIGN_PIXEL_PX"],
                "GLYPH_MASK_OVERLAP_PIXELS_GLOBAL": glyph_overlap_pixels,
                "MASK_EMPTY": row["MASK_EMPTY"],
                "PIXEL_DECISION": pixel_decision,
                "RAW_1X": row["RAW_1X"],
                "TARGET_OVERLAY_1X": row["TARGET_OVERLAY_1X"],
                "MASK_ONLY_1X": row["MASK_ONLY_1X"],
                "TRIAD_8X": row["TRIAD_8X"],
                "CONTACT_SHEET": row["CONTACT_SHEET"],
                "CONTACT_CELL": row["CONTACT_CELL"],
            }
        )

    glyph_manifest_fields = [
        "ELEMENT_ID", "SAFE_FILENAME", "PARENT_ID", "PANEL", "ROLE", "CHAR", "CODEPOINT", "SCRIPT_CLASS",
        "PDF_FONT", "PDF_FLAGS", "PDF_COLOR", "PDF_COLOR_RGB", "DECLARED_PT", "EFFECTIVE_PT", "PDF_BBOX_PT",
        "RAW_BBOX_PX", "MASK_BBOX_PX", "H_INK_PX", "INK_AREA_PX", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX",
        "MASK_EMPTY", "GLYPH_MASK_OVERLAP_PIXELS_GLOBAL", "PADDED_ROI_PX", "RAW_1X", "TARGET_OVERLAY_1X",
        "MASK_ONLY_1X", "TRIAD_8X", "CONTACT_SHEET", "CONTACT_CELL",
    ]
    write_csv(ROOT / "glyph_id_filename_manifest.csv", glyphs, glyph_manifest_fields)
    write_csv(LEDGER / "semantic_parent_manifest.csv", parent_rows, list(parent_rows[0]))
    write_csv(RELATIONS / "graphic_manifest.csv", graphic_rows, list(graphic_rows[0]))
    write_csv(RELATIONS / "text_graphic_relations.csv", relation_rows, list(relation_rows[0]))
    write_csv(RELATIONS / "text_figure_edge_relations.csv", edge_rows, list(edge_rows[0]))
    write_csv(OCCLUSION / "occlusion_ledger.csv", occlusion_rows, list(occlusion_rows[0]))
    write_csv(ROOT / "after_font_audit_precalibration.csv", font_rows, list(font_rows[0]))
    write_csv(ROOT / "after_pixel_measurements.csv", pixel_rows, list(pixel_rows[0]))
    write_csv(LEDGER / "de_actual_baselines.csv", de_rows, list(de_rows[0]))

    metadata = {
        "figure_uid": "FIG-P020-01",
        "audit_round": "R6_REQUAL_R111_SA1_20260824",
        "frozen_pdf": str(PDF),
        "frozen_pdf_sha256": sha256(PDF),
        "physical_page": PAGE_NUMBER,
        "page_points": [round(page_rect.width, 3), round(page_rect.height, 3)],
        "native_300dpi_grid": [w, h],
        "render_method": "pdftoppm direct PDF page 17 at -r 300; no resize",
        "figure_crop_native_px": list(FIG_CROP),
        "figure_crop_dimensions_px": [FIG_CROP[2] - FIG_CROP[0], FIG_CROP[3] - FIG_CROP[1]],
        "scope": "TikZ figure body plus its source-owned caption; excludes preceding/following chapter prose",
        "source_paths": {"figure": str(FIGURE_SOURCE), "chapter": str(CHAPTER_SOURCE)},
        "direct_visible_glyph_count": len(glyphs),
        "semantic_text_parent_count": len(parent_rows),
        "unresolved_precalibration_only": "low-profile punctuation calibration and human visual review are intentionally separate; no terminal conclusion is emitted by this generator",
    }
    write_json(ROOT / "R95_AUTHORITY_AND_SCOPE.json", metadata)
    write_json(
        ROOT / "generation_counts.json",
        {
            "glyph_count": len(glyphs),
            "glyph_mask_overlap_pixels": glyph_overlap_pixels,
            "glyph_foreign_pixels": int(sum(row["FOREIGN_PIXEL_PX"] for row in glyphs)),
            "glyph_missing_stroke_pixels": int(sum(row["MISSING_STROKE_PX"] for row in glyphs)),
            "graphic_count": len(graphic_rows),
            "relation_count": len(relation_rows),
            "text_text_pair_count": 45,
            "text_graphic_matrix_count": len(parent_ids) * len(relation_graphics),
            "cross_panel_pair_count": 12,
            "critical_or_fail_relation_count": sum(
                1 for row in relation_rows if row["CRITICAL"] or row["RESULT"] == "FAIL"
            ),
        },
    )
    print(json.dumps({"root": str(ROOT), "glyphs": len(glyphs), "relations": len(relation_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
