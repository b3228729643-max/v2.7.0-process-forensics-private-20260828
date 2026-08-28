from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
import math
import re
import shutil
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")
PAGE_1BASED = 659
PAGE_INDEX = PAGE_1BASED - 1
EXPECTED_BYTES = 4_947_496
EXPECTED_SHA256 = "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1"
EXPECTED_PAGES = 814
HANDOFF_ID = "A-R101-P608-SA1-FRESH-20260825"
FIGURE_ID = "FIG-P608-01"

# Pixel-aligned FIG domain chosen from the R101 physical-page 659 vector inventory.
# It includes both panels plus the complete same-number caption natural paragraph,
# and excludes the preceding/following body prose.
CROP_PX_300 = (292, 920, 2146, 1875)
SCALE_300 = 300.0 / 72.0
CROP_PT = tuple(v / SCALE_300 for v in CROP_PX_300)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: object) -> object:
    if isinstance(value, (fitz.Rect, fitz.IRect, fitz.Point, fitz.Quad, fitz.Matrix)):
        return list(value)
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest().upper()}
    if isinstance(value, dict):
        return {str(k): norm(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [norm(v) for v in value]
    return value


def to_px_rect(rect: fitz.Rect, dpi: int) -> tuple[int, int, int, int]:
    scale = dpi / 72.0
    return tuple(round(v * scale) for v in (rect.x0, rect.y0, rect.x1, rect.y1))


def render_probe() -> None:
    if (ROOT / "WRITE_SEAL.json").exists():
        raise RuntimeError("evidence root is sealed")
    ROOT.mkdir(parents=True, exist_ok=True)
    identity = {
        "handoff_id": HANDOFF_ID,
        "figure_id": FIGURE_ID,
        "sa1_model": "gpt-5.6-sol",
        "sa1_reasoning": "xhigh",
        "pdf": str(PDF),
        "bytes": PDF.stat().st_size,
        "sha256": sha256_file(PDF),
        "expected_bytes": EXPECTED_BYTES,
        "expected_sha256": EXPECTED_SHA256,
        "expected_pages": EXPECTED_PAGES,
        "physical_page_1based": PAGE_1BASED,
        "page_mapping_basis": "current source caption/label independently located in frozen R101",
        "dispatch_correction": "initial dispatch said physical P608; corrected before evidence creation to current R101 physical page 659",
    }
    with fitz.open(PDF) as doc:
        identity["pages"] = doc.page_count
        page = doc[PAGE_INDEX]
        identity["page_rect_pt"] = list(page.rect)
        identity["a4_match"] = abs(page.rect.width - 595.276) < 0.01 and abs(page.rect.height - 841.89) < 0.01
        identity["identity_pass"] = (
            identity["bytes"] == EXPECTED_BYTES
            and identity["sha256"] == EXPECTED_SHA256
            and identity["pages"] == EXPECTED_PAGES
            and identity["a4_match"]
        )
        if not identity["identity_pass"]:
            raise RuntimeError(f"candidate identity mismatch: {identity}")

        full200 = page.get_pixmap(dpi=200, alpha=False, annots=False)
        full200.save(ROOT / "full_page_200dpi.png")
        full300 = page.get_pixmap(dpi=300, alpha=False, annots=False)
        full300.save(ROOT / "full_page_300dpi.png")
        gray300 = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY, alpha=False, annots=False)
        gray300.save(ROOT / "full_page_grayscale_300dpi.png")

        clip = fitz.Rect(CROP_PT)
        crop300 = page.get_pixmap(dpi=300, clip=clip, alpha=False, annots=False)
        crop300.save(ROOT / "figure_crop_300dpi.png")
        cropgray = page.get_pixmap(dpi=300, clip=clip, colorspace=fitz.csGRAY, alpha=False, annots=False)
        cropgray.save(ROOT / "grayscale_300dpi.png")
        # The official full-book crop is the only permitted standalone surrogate in this frozen-candidate audit.
        crop300.save(ROOT / "standalone_300dpi.png")

        raw = page.get_text("rawdict", sort=False)
        drawings = page.get_drawings()
        blocks = page.get_text("blocks", sort=True)
        write_json(ROOT / "page659_rawdict.json", norm(raw))
        write_json(ROOT / "page659_drawings_full.json", norm(drawings))

        block_rows = []
        for i, block in enumerate(blocks):
            block_rows.append({
                "BLOCK_ID": f"PAGE-BLOCK-{i:03d}",
                "X0_PT": block[0], "Y0_PT": block[1], "X1_PT": block[2], "Y1_PT": block[3],
                "TEXT": block[4].replace("\n", "\\n"), "BLOCK_TYPE": block[6],
            })
        write_csv(ROOT / "page659_text_blocks.csv", list(block_rows[0]), block_rows)

        draw_rows = []
        for i, drawing in enumerate(drawings):
            rect = fitz.Rect(drawing["rect"])
            draw_rows.append({
                "DRAW_ID": f"PAGE-DRAW-{i:03d}", "SEQNO": drawing.get("seqno"),
                "TYPE": drawing.get("type"), "X0_PT": rect.x0, "Y0_PT": rect.y0,
                "X1_PT": rect.x1, "Y1_PT": rect.y1, "WIDTH_PT": drawing.get("width"),
                "COLOR": repr(drawing.get("color")), "FILL": repr(drawing.get("fill")),
                "ITEM_COUNT": len(drawing.get("items", [])),
                "INTERSECTS_FIGURE_CROP": rect.intersects(clip),
            })
        write_csv(ROOT / "page659_drawings.csv", list(draw_rows[0]), draw_rows)

        page_text = page.get_text("text", sort=True)
        unique_needles = [
            "轨迹", "保留样本运行均值", "预热段", "目标值", "舍弃前5", "不构成收敛证明",
        ]
        locator = {needle: len(page.search_for(needle)) for needle in unique_needles}
        locator["page_text_contains_all_core_needles"] = all(locator[n] > 0 for n in unique_needles[:4])
        locator["page_text_excerpt"] = page_text[page_text.find("图32.8 展示"):page_text.find("图32.9 把")]
        write_json(ROOT / "page_mapping_locator.json", locator)

        geometry = {
            "page_pt": list(page.rect),
            "full_page_200dpi_native_px": [full200.width, full200.height],
            "full_page_300dpi_native_px": [full300.width, full300.height],
            "figure_crop_pt": list(CROP_PT),
            "figure_crop_integer_coords_in_full_300dpi": list(CROP_PX_300),
            "figure_crop_300dpi_native_px": [crop300.width, crop300.height],
            "grayscale_300dpi_native_px": [cropgray.width, cropgray.height],
            "standalone_300dpi_native_px": [crop300.width, crop300.height],
            "render_rule": "direct MuPDF render at requested dpi; no resize; 8x only later by nearest-neighbour",
        }
        write_json(ROOT / "render_geometry.json", geometry)

    write_json(ROOT / "candidate_identity.json", identity)

    img = Image.open(ROOT / "full_page_300dpi.png").convert("RGB")
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = CROP_PX_300
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(255, 0, 0), width=5)
    draw.text((x0 + 10, y0 + 10), "FIG-P608-01 / R101 physical page 659 / audit crop", fill=(255, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
    overlay.save(ROOT / "page659_figure_locator_overlay_300dpi.png")


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def color_float_to_rgb(value: object) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(max(0, min(255, round(float(v) * 255))) for v in value)  # type: ignore[arg-type]


def expected_color_mask(rgb: np.ndarray, colors: list[tuple[int, int, int]], min_contrast: int = 20) -> np.ndarray:
    arr = rgb.astype(np.float32)
    q = 255.0 - arr
    contrast = np.max(q, axis=2) >= min_contrast
    out = np.zeros(rgb.shape[:2], dtype=bool)
    for color in colors:
        v = 255.0 - np.array(color, dtype=np.float32)
        denom = float(np.dot(v, v))
        if denom < 1.0:
            continue
        alpha = np.sum(q * v[None, None, :], axis=2) / denom
        recon = alpha[:, :, None] * v[None, None, :]
        residual = np.sqrt(np.sum((q - recon) ** 2, axis=2))
        out |= contrast & (alpha >= 0.0) & (alpha <= 1.08) & (residual <= 9.0)
    return out


FOREGROUND_PALETTE = [
    (31, 35, 40), (107, 114, 128), (15, 118, 110), (127, 128, 127),
    (31, 78, 121), (183, 121, 31), (184, 192, 200), (183, 191, 199),
]


def exclusive_color_mask(rgb: np.ndarray, colors: list[tuple[int, int, int]], min_contrast: int = 20) -> np.ndarray:
    """Assign each nonwhite raster pixel to the closest declared foreground colour family."""
    arr = rgb.astype(np.float32)
    q = 255.0 - arr
    contrast = np.max(q, axis=2) >= min_contrast
    residuals = []
    for color in FOREGROUND_PALETTE:
        v = 255.0 - np.array(color, dtype=np.float32)
        alpha = np.sum(q * v[None, None, :], axis=2) / float(np.dot(v, v))
        recon = alpha[:, :, None] * v[None, None, :]
        residual = np.sqrt(np.sum((q - recon) ** 2, axis=2))
        residual[(alpha < 0.0) | (alpha > 1.08)] = np.inf
        residuals.append(residual)
    stack = np.stack(residuals, axis=0)
    winner = np.argmin(stack, axis=0)
    best = np.min(stack, axis=0)
    target_indices = {FOREGROUND_PALETTE.index(c) for c in colors}
    return contrast & (best <= 9.0) & np.isin(winner, list(target_indices))


def local_pixel_bbox(page_bbox: tuple[float, float, float, float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = math.floor(page_bbox[0] * SCALE_300) - CROP_PX_300[0] - pad
    y0 = math.floor(page_bbox[1] * SCALE_300) - CROP_PX_300[1] - pad
    x1 = math.ceil(page_bbox[2] * SCALE_300) - CROP_PX_300[0] + pad
    y1 = math.ceil(page_bbox[3] * SCALE_300) - CROP_PX_300[1] + pad
    return max(0, x0), max(0, y0), min(width, x1), min(height, y1)


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def safe_name(object_id: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", object_id).strip("._")
    return value or "OBJECT"


def text_parent_and_role(char: str, bbox: tuple[float, float, float, float]) -> tuple[str, str, str, int, float, float]:
    x0, y0, x1, y1 = bbox
    if y0 >= 427:
        return "P-CAPTION", "CAPTION", "CAPTION", 57, 9.6, 9.6
    if y0 < 246:
        return "P-TOP-TITLE", "PANEL_TITLE", "TOP", 24, 10.8, 10.8
    if x0 < 150 and 270 <= y0 < 290:
        return "P-TOP-YLABEL", "AXIS_LABEL", "TOP", 26, 10.8, 10.8
    if x0 < 200 and 246 <= y0 < 310:
        label = char if char.isdigit() else f"Y{round(y0, 1)}"
        return f"P-TOP-YTICK-{label}", "TICK", "TOP", 26, 9.6, 9.6
    if 250 <= y0 < 273 and x0 >= 240:
        if x0 < 300 and y0 < 271:
            return "P-TOP-ANNOT-WARMUP-TITLE", "ANNOTATION", "TOP", 39, 9.6, 9.6
        if x0 < 300:
            return "P-TOP-ANNOT-WARMUP-RANGE", "ANNOTATION", "TOP", 39, 9.6, 9.6
        return "P-TOP-ANNOT-RETAINED", "ANNOTATION", "TOP", 41, 9.6, 9.6
    if y0 < 333:
        return "P-BOTTOM-TITLE", "PANEL_TITLE", "BOTTOM", 44, 10.8, 10.8
    if x0 > 400 and 333 <= y0 < 347:
        return "P-BOTTOM-ANNOT-TARGET", "ANNOTATION", "BOTTOM", 54, 9.6, 9.6
    if x0 < 150 and 360 <= y0 < 380:
        return "P-BOTTOM-YLABEL", "AXIS_LABEL", "BOTTOM", 43, 10.8, 10.8
    if x0 < 200 and 340 <= y0 < 400:
        return f"P-BOTTOM-YTICK-Y{round(y0, 1)}", "TICK", "BOTTOM", 42, 9.6, 9.6
    if 398 <= y0 < 413:
        center = (x0 + x1) / 2
        tick = "1" if center < 200 else "5" if center < 275 else "10" if center < 350 else "15" if center < 420 else "20"
        return f"P-BOTTOM-XTICK-{tick}", "TICK", "BOTTOM", 42, 9.6, 9.6
    return "P-BOTTOM-XLABEL", "AXIS_LABEL", "BOTTOM", 43, 10.8, 10.8


LOW_PROFILE = {".", ",", "，", "、", ":", "：", ";", "；", "…"}


def script_class(char: str, pdf_size: float) -> tuple[str, int, str]:
    if char in LOW_PROFILE:
        return "LOW_PROFILE_PUNCTUATION", 0, "peer-calibrated"
    if pdf_size < 9.0:
        return "NATURAL_SCRIPT", 15, "natural TeX subscript from >=10.8pt base"
    if "\u4e00" <= char <= "\u9fff":
        return "CJK_FULL", 30, "CJK hard floor"
    if char.isdigit() or (char.isalpha() and char.upper() == char and char.lower() != char):
        return "LATIN_UPPER_DIGIT", 24, "uppercase/digit hard floor"
    if char in {"∶", "=", "+", "−", "-", "×"}:
        return "MATH_OPERATOR", 22, "baseline mathematical operator hard floor"
    return "LATIN_GREEK_XHEIGHT", 17, "lowercase/Greek x-height hard floor"


DRAW_OBJECTS: dict[int, tuple[str, str, str, str, int]] = {
    6: ("G-TOP-X-TICKS", "AXIS_TICK", "TOP", "P-TOP-AXIS", 20),
    7: ("G-TOP-Y-TICKS", "AXIS_TICK", "TOP", "P-TOP-AXIS", 20),
    8: ("G-TOP-X-AXIS", "LINE_ARROW", "TOP", "P-TOP-AXIS", 20),
    9: ("G-TOP-X-ARROWHEAD", "LINE_ARROW", "TOP", "P-TOP-AXIS", 20),
    10: ("G-TOP-Y-AXIS", "LINE_ARROW", "TOP", "P-TOP-AXIS", 20),
    11: ("G-TOP-Y-ARROWHEAD", "LINE_ARROW", "TOP", "P-TOP-AXIS", 20),
    13: ("G-TOP-DATA-CURVE", "DATA_CURVE", "TOP", "P-TOP-DATA", 30),
    14: ("G-TOP-BURNIN-SEPARATOR", "LINE_ARROW", "TOP", "P-TOP-BURNIN", 33),
    15: ("G-EQ-WARMUP-UPPER", "MATH_RULE", "TOP", "P-TOP-ANNOT-WARMUP-RANGE", 10),
    16: ("G-EQ-WARMUP-LOWER", "MATH_RULE", "TOP", "P-TOP-ANNOT-WARMUP-RANGE", 11),
    17: ("G-EQ-RETAINED-UPPER", "MATH_RULE", "TOP", "P-TOP-ANNOT-RETAINED", 10),
    18: ("G-EQ-RETAINED-LOWER", "MATH_RULE", "TOP", "P-TOP-ANNOT-RETAINED", 11),
    39: ("G-BOTTOM-X-TICKS", "AXIS_TICK", "BOTTOM", "P-BOTTOM-AXIS", 20),
    40: ("G-BOTTOM-Y-TICKS", "AXIS_TICK", "BOTTOM", "P-BOTTOM-AXIS", 20),
    41: ("G-BOTTOM-X-AXIS", "LINE_ARROW", "BOTTOM", "P-BOTTOM-AXIS", 20),
    42: ("G-BOTTOM-X-ARROWHEAD", "LINE_ARROW", "BOTTOM", "P-BOTTOM-AXIS", 20),
    43: ("G-BOTTOM-Y-AXIS", "LINE_ARROW", "BOTTOM", "P-BOTTOM-AXIS", 20),
    44: ("G-BOTTOM-Y-ARROWHEAD", "LINE_ARROW", "BOTTOM", "P-BOTTOM-AXIS", 20),
    46: ("G-BOTTOM-DATA-CURVE", "DATA_CURVE", "BOTTOM", "P-BOTTOM-DATA", 47),
    47: ("G-BOTTOM-BURNIN-SEPARATOR", "LINE_ARROW", "BOTTOM", "P-BOTTOM-BURNIN", 50),
    48: ("G-BOTTOM-TARGET-LINE", "REFERENCE_LINE", "BOTTOM", "P-BOTTOM-TARGET", 52),
    64: ("G-BOTTOM-YLABEL-OVERLINE", "MATH_RULE", "BOTTOM", "P-BOTTOM-YLABEL", 43),
    65: ("G-BOTTOM-TITLE-OVERLINE", "MATH_RULE", "BOTTOM", "P-BOTTOM-TITLE", 44),
}
for _i in range(19, 39):
    DRAW_OBJECTS[_i] = (f"G-TOP-MARKER-T{_i - 18:02d}", "MARKER", "TOP", "P-TOP-DATA", 30)
for _i in range(49, 64):
    DRAW_OBJECTS[_i] = (f"G-BOTTOM-MARKER-T{_i - 43:02d}", "MARKER", "BOTTOM", "P-BOTTOM-DATA", 47)


def save_object_masks(obj: dict[str, object], raw: np.ndarray, final: np.ndarray) -> None:
    """Persist tight native and exact nearest-neighbour 8x masks for one object."""
    raw_box = tight_bbox(raw)
    final_box = tight_bbox(final)
    if raw_box is None or final_box is None:
        raise RuntimeError(f"empty object mask: {obj['ELEMENT_ID']} raw={raw_box} final={final_box}")
    safe = str(obj["SAFE_FILENAME"])
    obj["RAW_MASK_BBOX_PX"] = list(raw_box)
    obj["FINAL_MASK_BBOX_PX"] = list(final_box)
    obj["RAW_PIXEL_COUNT"] = int(raw.sum())
    obj["FINAL_PIXEL_COUNT"] = int(final.sum())
    obj["OCCLUDED_PIXEL_COUNT"] = int(raw.sum() - final.sum())
    for kind, mask, box in (("pre", raw, raw_box), ("final", final, final_box)):
        x0, y0, x1, y1 = box
        roi = (mask[y0:y1, x0:x1].astype(np.uint8) * 255)
        npath = ROOT / "masks" / f"{kind}_native" / f"{safe}.png"
        xpath = ROOT / "masks" / f"{kind}_8x_nearest" / f"{safe}.png"
        npath.parent.mkdir(parents=True, exist_ok=True)
        xpath.parent.mkdir(parents=True, exist_ok=True)
        im = Image.fromarray(roi, mode="L")
        im.save(npath)
        im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST).save(xpath)
        obj[f"{kind.upper()}_NATIVE_MASK"] = str(npath.relative_to(ROOT)).replace("\\", "/")
        obj[f"{kind.upper()}_8X_MASK"] = str(xpath.relative_to(ROOT)).replace("\\", "/")


def object_context(rgb: np.ndarray, mask: np.ndarray, pad: int, upscale: int) -> tuple[Image.Image, Image.Image, Image.Image]:
    box = tight_bbox(mask)
    if box is None:
        raise RuntimeError("empty context mask")
    x0 = max(0, box[0] - pad)
    y0 = max(0, box[1] - pad)
    x1 = min(rgb.shape[1], box[2] + pad)
    y1 = min(rgb.shape[0], box[3] + pad)
    original = Image.fromarray(rgb[y0:y1, x0:x1]).convert("RGB")
    overlay = original.copy()
    overlay_arr = np.array(overlay)
    local = mask[y0:y1, x0:x1]
    overlay_arr[local] = np.array([255, 0, 0], dtype=np.uint8)
    overlay = Image.fromarray(overlay_arr)
    only = Image.new("RGB", original.size, (0, 0, 0))
    only_arr = np.array(only)
    only_arr[local] = np.array([255, 255, 255], dtype=np.uint8)
    only = Image.fromarray(only_arr)
    if upscale != 1:
        size = (original.width * upscale, original.height * upscale)
        original = original.resize(size, Image.Resampling.NEAREST)
        overlay = overlay.resize(size, Image.Resampling.NEAREST)
        only = only.resize(size, Image.Resampling.NEAREST)
    return original, overlay, only


def contact_sheets(objects: list[dict[str, object]], raw_masks: list[np.ndarray], rgb: np.ndarray) -> list[dict[str, object]]:
    out_rows: list[dict[str, object]] = []
    groups = [("glyph", [i for i, o in enumerate(objects) if o["CLASS"] == "GLYPH"], 8, 12),
              ("graphic", [i for i, o in enumerate(objects) if o["CLASS"] != "GLYPH"], 1, 20)]
    for group, indices, upscale, per_sheet in groups:
        directory = ROOT / "contact_sheets" / group
        directory.mkdir(parents=True, exist_ok=True)
        for page_no, start in enumerate(range(0, len(indices), per_sheet), 1):
            subset = indices[start:start + per_sheet]
            cells: list[tuple[int, list[Image.Image]]] = []
            max_h = 0
            max_w = 0
            for idx in subset:
                views = list(object_context(rgb, raw_masks[idx], 3 if group == "glyph" else 12, upscale))
                vw = sum(v.width for v in views) + 28
                vh = max(v.height for v in views) + 62
                max_w = max(max_w, vw)
                max_h = max(max_h, vh)
                cells.append((idx, views))
            cols = 2 if group == "glyph" else 1
            rows = math.ceil(len(cells) / cols)
            canvas = Image.new("RGB", (max_w * cols, max_h * rows), "white")
            pen = ImageDraw.Draw(canvas)
            for cell_no, (idx, views) in enumerate(cells, 1):
                col = (cell_no - 1) % cols
                row = (cell_no - 1) // cols
                ox, oy = col * max_w, row * max_h
                pen.rectangle((ox, oy, ox + max_w - 1, oy + max_h - 1), outline=(150, 150, 150), width=1)
                element_id = str(objects[idx]["ELEMENT_ID"])
                pen.text((ox + 6, oy + 5), f"{element_id} | ORIGINAL / TARGET OVERLAY / MASK ONLY", fill=(0, 0, 0))
                vx = ox + 6
                for view in views:
                    canvas.paste(view, (vx, oy + 30))
                    vx += view.width + 8
                out_rows.append({
                    "ELEMENT_ID": element_id, "CONTACT_GROUP": group,
                    "SHEET": f"{group}_contact_{page_no:03d}.png", "CELL": cell_no,
                    "UPSCALE": upscale, "RESAMPLING": "NEAREST",
                })
            canvas.save(directory / f"{group}_contact_{page_no:03d}.png")
    return out_rows


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    ay, ax = np.nonzero(a)
    by, bx = np.nonzero(b)
    if not len(ax) or not len(bx):
        return float("nan")
    pa = np.column_stack((ay, ax))
    pb = np.column_stack((by, bx))
    if len(pa) > len(pb):
        pa, pb = pb, pa
    distance, _ = cKDTree(pb).query(pa, k=1)
    # Centre-to-centre pixel distance minus one pixel width: adjacent pixels have 0 px clearance.
    return max(0.0, float(np.min(distance)) - 1.0)


def design_relation(a: dict[str, object], b: dict[str, object]) -> tuple[bool, str]:
    if a["SEMANTIC_PARENT"] == b["SEMANTIC_PARENT"]:
        if a["CLASS"] == "GLYPH" and b["CLASS"] == "GLYPH":
            return False, "same semantic text parent; clearance exempt but non-design ink overlap remains forbidden"
        return True, "same semantic parent / internal typography or assembled graphic"
    ca, cb = str(a["OBJECT_TYPE"]), str(b["OBJECT_TYPE"])
    pa, pb = str(a["PANEL"]), str(b["PANEL"])
    if pa == pb and {ca, cb} <= {"AXIS_TICK", "LINE_ARROW"}:
        return True, "axis/tick/arrow assembly"
    if pa == pb and ({ca, cb} <= {"DATA_CURVE", "MARKER"}):
        return True, "data curve and marker assembly"
    if pa == pb and "PATTERN" in {ca, cb} and "GLYPH" not in {ca, cb}:
        return True, "declared burn-in background pattern behind plot graphics"
    if pa == pb and "REFERENCE_LINE" in {ca, cb} and "GLYPH" not in {ca, cb}:
        return True, "declared target reference line crossing data graphics"
    if pa == "TOP" and pb == "TOP" and ({ca, cb} & {"LINE_ARROW"}) and ({ca, cb} & {"DATA_CURVE", "MARKER"}):
        names = {str(a["ELEMENT_ID"]), str(b["ELEMENT_ID"])}
        if any("BURNIN-SEPARATOR" in n for n in names):
            return True, "declared burn-in separator crossing the plotted series"
        if "G-TOP-MARKER-T01" in names and any(n in names for n in ("G-TOP-Y-AXIS", "G-TOP-Y-ARROWHEAD")):
            return True, "source-declared t=1 data marker is centred on the top-panel y-axis boundary"
    return False, ""


def pair_rule(a: dict[str, object], b: dict[str, object]) -> tuple[float, str]:
    if a["CLASS"] == "GLYPH" and b["CLASS"] == "GLYPH":
        if a["SEMANTIC_PARENT"] == b["SEMANTIC_PARENT"]:
            return 0.0, "SAME_TEXT_PARENT_OVERLAP_ONLY"
        return 4.0, "TEXT_TEXT_VECTOR_BBOX"
    if "GLYPH" in {a["CLASS"], b["CLASS"]}:
        return 3.0, "TEXT_GRAPHIC_RAW_MASK"
    return 0.0, "GRAPHIC_GRAPHIC_OVERLAP_ONLY"


def build_objects() -> None:
    if (ROOT / "WRITE_SEAL.json").exists():
        raise RuntimeError("evidence root is sealed")
    if not (ROOT / "figure_crop_300dpi.png").exists():
        render_probe()
    for name in ("masks", "contact_sheets", "low_profile_peers", "critical_pairs"):
        target = (ROOT / name).resolve()
        if target.parent != ROOT.resolve():
            raise RuntimeError(f"refusing cleanup outside evidence root: {target}")
        if target.exists():
            shutil.rmtree(target)
    rgb = np.array(Image.open(ROOT / "figure_crop_300dpi.png").convert("RGB"))
    height, width = rgb.shape[:2]
    full_rgb = np.array(Image.open(ROOT / "full_page_300dpi.png").convert("RGB"))
    crop_rect = fitz.Rect(CROP_PT)
    objects: list[dict[str, object]] = []
    raw_masks: list[np.ndarray] = []
    all_chars: list[dict[str, object]] = []

    with fitz.open(PDF) as doc:
        page = doc[PAGE_INDEX]
        raw = page.get_text("rawdict", sort=False)
        char_seq = 0
        domain_total = domain_space = 0
        page_total = page_space = 0
        for block_i, block in enumerate(raw.get("blocks", [])):
            if block.get("type") != 0:
                continue
            for line_i, line in enumerate(block.get("lines", [])):
                for span_i, span in enumerate(line.get("spans", [])):
                    span_color = color_int_to_rgb(int(span.get("color", 0)))
                    for char_i, char_entry in enumerate(span.get("chars", [])):
                        c = str(char_entry.get("c", ""))
                        bbox = tuple(float(v) for v in char_entry["bbox"])
                        record = {
                            "seq": char_seq, "char": c, "bbox": bbox,
                            "font": str(span.get("font", "")), "size": float(span.get("size", 0.0)),
                            "color": span_color, "block": block_i, "line": line_i, "span": span_i, "char_i": char_i,
                        }
                        all_chars.append(record)
                        char_seq += 1
                        page_total += 1
                        if c.isspace():
                            page_space += 1
                        center = fitz.Point((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                        if crop_rect.contains(center):
                            domain_total += 1
                            if c.isspace():
                                domain_space += 1
                                continue
                            parent, role, panel, source_line, declared_pt, effective_pt = text_parent_and_role(c, bbox)
                            obj_id = f"TXT-{len([o for o in objects if o.get('CLASS') == 'GLYPH']) + 1:03d}"
                            pxbox = local_pixel_bbox(bbox, width, height, pad=1)
                            x0, y0, x1, y1 = pxbox
                            local = exclusive_color_mask(rgb[y0:y1, x0:x1], [span_color])
                            mask = np.zeros((height, width), dtype=bool)
                            mask[y0:y1, x0:x1] = local
                            klass, floor, floor_basis = script_class(c, float(span.get("size", 0.0)))
                            obj = {
                                "ELEMENT_ID": obj_id, "SAFE_FILENAME": safe_name(obj_id), "CLASS": "GLYPH",
                                "OBJECT_TYPE": "GLYPH", "CHAR": c, "RAWDICT_SEQUENCE": record["seq"],
                                "RAWDICT_BLOCK": block_i, "RAWDICT_LINE": line_i, "RAWDICT_SPAN": span_i,
                                "RAWDICT_CHAR": char_i, "FONT": record["font"], "PDF_SPAN_SIZE_PT": record["size"],
                                "COLOR_RGB": list(span_color), "PDF_BBOX_PT": list(bbox), "PIXEL_SEARCH_BBOX": list(pxbox),
                                "SEMANTIC_PARENT": parent, "ROLE": role, "PANEL": panel, "SOURCE_LINE": source_line,
                                "DECLARED_PT": declared_pt, "EFFECTIVE_PT": effective_pt,
                                "SCRIPT_CLASS": klass, "HARD_FLOOR_PX": floor, "FLOOR_BASIS": floor_basis,
                                "Z_ORDER": 10000 + int(record["seq"]),
                            }
                            objects.append(obj)
                            raw_masks.append(mask)

        drawings = page.get_drawings()
        for draw_index in sorted(DRAW_OBJECTS):
            d = drawings[draw_index]
            obj_id, obj_type, panel, parent, source_line = DRAW_OBJECTS[draw_index]
            rect = tuple(float(v) for v in d["rect"])
            pxbox = local_pixel_bbox(rect, width, height, pad=3)
            colors = [x for x in (color_float_to_rgb(d.get("color")), color_float_to_rgb(d.get("fill"))) if x is not None]
            if not colors:
                raise RuntimeError(f"drawing {draw_index} has no foreground color")
            x0, y0, x1, y1 = pxbox
            local = exclusive_color_mask(rgb[y0:y1, x0:x1], colors)
            mask = np.zeros((height, width), dtype=bool)
            mask[y0:y1, x0:x1] = local
            obj = {
                "ELEMENT_ID": obj_id, "SAFE_FILENAME": safe_name(obj_id), "CLASS": "GRAPHIC",
                "OBJECT_TYPE": obj_type, "CHAR": "", "PDF_DRAW_INDEX": draw_index,
                "PDF_DRAW_SEQNO": int(d.get("seqno", -1)), "PDF_DRAW_TYPE": str(d.get("type")),
                "PDF_BBOX_PT": list(rect), "PIXEL_SEARCH_BBOX": list(pxbox), "COLOR_RGB": [list(c) for c in colors],
                "SEMANTIC_PARENT": parent, "ROLE": obj_type, "PANEL": panel, "SOURCE_LINE": source_line,
                "DECLARED_PT": "N/A", "EFFECTIVE_PT": "N/A", "SCRIPT_CLASS": "N/A",
                "HARD_FLOOR_PX": "N/A", "FLOOR_BASIS": "N/A", "Z_ORDER": int(d.get("seqno", -1)),
            }
            objects.append(obj)
            raw_masks.append(mask)

    # Hatch patterns are visible rasterized foreground layers not emitted by get_drawings().
    pattern_specs = [
        ("G-TOP-BURNIN-HATCH", "TOP", "P-TOP-BURNIN", (179.2, 254.0, 244.1, 308.8), 29),
        ("G-BOTTOM-BURNIN-HATCH", "BOTTOM", "P-BOTTOM-BURNIN", (179.2, 341.0, 244.1, 395.8), 46),
    ]
    for number, (obj_id, panel, parent, rect, source_line) in enumerate(pattern_specs):
        pxbox = local_pixel_bbox(rect, width, height, pad=0)
        x0, y0, x1, y1 = pxbox
        # Source-declared pattern colour gray!38!slate resolves to this official-candidate family.
        local = exclusive_color_mask(rgb[y0:y1, x0:x1], [(184, 192, 200), (183, 191, 199)], min_contrast=20)
        mask = np.zeros((height, width), dtype=bool)
        mask[y0:y1, x0:x1] = local
        obj = {
            "ELEMENT_ID": obj_id, "SAFE_FILENAME": safe_name(obj_id), "CLASS": "GRAPHIC",
            "OBJECT_TYPE": "PATTERN", "CHAR": "", "PDF_DRAW_INDEX": "NOT_EMITTED_BY_GET_DRAWINGS",
            "PDF_DRAW_SEQNO": "N/A", "PDF_DRAW_TYPE": "VISIBLE_HATCH_PATTERN_LAYER",
            "PDF_BBOX_PT": list(rect), "PIXEL_SEARCH_BBOX": list(pxbox),
            "COLOR_RGB": [[184, 192, 200], [183, 191, 199]], "SEMANTIC_PARENT": parent,
            "ROLE": "BURNIN_HATCH", "PANEL": panel, "SOURCE_LINE": source_line,
            "DECLARED_PT": "N/A", "EFFECTIVE_PT": "N/A", "SCRIPT_CLASS": "N/A",
            "HARD_FLOOR_PX": "N/A", "FLOOR_BASIS": "N/A", "Z_ORDER": -100 + number,
        }
        objects.append(obj)
        raw_masks.append(mask)

    glyph_count = sum(o["CLASS"] == "GLYPH" for o in objects)
    # Fractional PDF glyph bboxes can quantize to the same edge pixel. Resolve only such
    # glyph-to-glyph claims by a predeclared nearest-normalized-bbox-centre rule.
    claim_count = np.sum(np.stack(raw_masks[:glyph_count], axis=0), axis=0)
    oy, ox = np.nonzero(claim_count > 1)
    for py, px in zip(oy.tolist(), ox.tolist()):
        candidates = [k for k in range(glyph_count) if raw_masks[k][py, px]]
        def glyph_score(k: int) -> float:
            bx0, by0, bx1, by1 = (float(v) for v in objects[k]["PIXEL_SEARCH_BBOX"])
            return ((px + 0.5 - (bx0 + bx1) / 2) / max(1.0, bx1 - bx0)) ** 2 + ((py + 0.5 - (by0 + by1) / 2) / max(1.0, by1 - by0)) ** 2
        winner = min(candidates, key=lambda k: (glyph_score(k), k))
        for k in candidates:
            raw_masks[k][py, px] = (k == winner)
    graphic_count = len(objects) - glyph_count
    if glyph_count != 112 or graphic_count != 60:
        raise RuntimeError(f"denominator mismatch before masks: glyph={glyph_count}, graphic={graphic_count}")
    safe_values = [str(o["SAFE_FILENAME"]) for o in objects]
    if len(safe_values) != len(set(safe_values)):
        raise RuntimeError("safe filename collision")

    # Final-visible ownership is resolved from declared painting order. Later objects own shared pixels.
    owner = np.full((height, width), -1, dtype=np.int16)
    for idx in sorted(range(len(objects)), key=lambda i: (int(objects[i]["Z_ORDER"]), i)):
        owner[raw_masks[idx]] = idx
    final_masks = [(raw_masks[i] & (owner == i)) for i in range(len(objects))]
    for i, obj in enumerate(objects):
        save_object_masks(obj, raw_masks[i], final_masks[i])

    # Per-glyph actual ink geometry and hard gates.
    pixel_rows: list[dict[str, object]] = []
    hard_failures: list[dict[str, object]] = []
    for i, obj in enumerate(objects[:glyph_count]):
        box = tight_bbox(final_masks[i])
        assert box is not None
        h_ink = box[3] - box[1]
        w_ink = box[2] - box[0]
        area = int(final_masks[i].sum())
        obj["H_INK_PX"] = h_ink
        obj["W_INK_PX"] = w_ink
        obj["INK_AREA_PX"] = area
        floor = int(obj["HARD_FLOOR_PX"])
        decision = "PENDING_PEER" if obj["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION" else ("PASS" if h_ink >= floor else "FAIL")
        if decision == "FAIL":
            hard_failures.append({"FAIL_ID": f"FONT-{obj['ELEMENT_ID']}", "TYPE": "H_INK", "VALUE": h_ink, "THRESHOLD": floor})
        pixel_rows.append({
            "ELEMENT_ID": obj["ELEMENT_ID"], "CHAR": obj["CHAR"], "SEMANTIC_PARENT": obj["SEMANTIC_PARENT"],
            "ROLE": obj["ROLE"], "PANEL": obj["PANEL"], "SCRIPT_CLASS": obj["SCRIPT_CLASS"],
            "DECLARED_PT": obj["DECLARED_PT"], "EFFECTIVE_PT": obj["EFFECTIVE_PT"],
            "H_INK_PX": h_ink, "W_INK_PX": w_ink, "INK_AREA_PX": area,
            "HARD_FLOOR_PX": obj["HARD_FLOOR_PX"], "DECISION": decision,
        })

    peer_rows: list[dict[str, object]] = []
    peer_dir = ROOT / "low_profile_peers"
    peer_dir.mkdir(parents=True, exist_ok=True)
    for i, obj in enumerate(objects[:glyph_count]):
        if obj["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION":
            continue
        target_seq = int(obj["RAWDICT_SEQUENCE"])
        candidates = [c for c in all_chars if c["seq"] != target_seq and c["char"] == obj["CHAR"]
                      and c["font"] == obj["FONT"] and c["color"] == tuple(obj["COLOR_RGB"])
                      and abs(float(c["size"]) - float(obj["PDF_SPAN_SIZE_PT"])) <= 0.25]
        candidates.sort(key=lambda c: (abs(int(c["seq"]) - target_seq), int(c["seq"])))
        if not candidates:
            hard_failures.append({"FAIL_ID": f"PEER-{obj['ELEMENT_ID']}", "TYPE": "NO_SAME_PAGE_PEER", "VALUE": 0, "THRESHOLD": 1})
            peer_rows.append({"ELEMENT_ID": obj["ELEMENT_ID"], "DECISION": "FAIL", "NOTE": "no predeclared same-page exact peer"})
            continue
        peer = candidates[0]
        pb = tuple(float(v) for v in peer["bbox"])
        pbox = tuple(max(0, v) for v in to_px_rect(fitz.Rect(pb), 300))
        pbox = (max(0, pbox[0] - 1), max(0, pbox[1] - 1), min(full_rgb.shape[1], pbox[2] + 1), min(full_rgb.shape[0], pbox[3] + 1))
        px0, py0, px1, py1 = pbox
        pmask_local = exclusive_color_mask(full_rgb[py0:py1, px0:px1], [tuple(peer["color"])])
        pbox_tight = tight_bbox(pmask_local)
        if pbox_tight is None:
            hard_failures.append({"FAIL_ID": f"PEER-{obj['ELEMENT_ID']}", "TYPE": "EMPTY_PEER_MASK", "VALUE": 0, "THRESHOLD": 1})
            continue
        ph = pbox_tight[3] - pbox_tight[1]
        parea = int(pmask_local.sum())
        th = int(obj["H_INK_PX"])
        tarea = int(obj["INK_AREA_PX"])
        h_ratio = th / ph
        area_ratio = tarea / parea
        decision = "PASS" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL"
        if decision == "FAIL":
            hard_failures.append({"FAIL_ID": f"PEER-{obj['ELEMENT_ID']}", "TYPE": "LOW_PROFILE_RATIO", "VALUE": [h_ratio, area_ratio], "THRESHOLD": [0.92, 1.08]})
        pixel_rows[i]["DECISION"] = decision
        peer_native = Image.fromarray((pmask_local.astype(np.uint8) * 255), mode="L")
        peer_native_path = peer_dir / f"{obj['SAFE_FILENAME']}_peer_native.png"
        peer_8x_path = peer_dir / f"{obj['SAFE_FILENAME']}_peer_8x_nearest.png"
        peer_native.save(peer_native_path)
        peer_native.resize((peer_native.width * 8, peer_native.height * 8), Image.Resampling.NEAREST).save(peer_8x_path)
        context = full_rgb[max(0, py0 - 3):min(full_rgb.shape[0], py1 + 3), max(0, px0 - 3):min(full_rgb.shape[1], px1 + 3)]
        local_full = np.zeros(context.shape[:2], dtype=bool)
        oy, ox = py0 - max(0, py0 - 3), px0 - max(0, px0 - 3)
        local_full[oy:oy + pmask_local.shape[0], ox:ox + pmask_local.shape[1]] = pmask_local
        ori = Image.fromarray(context).resize((context.shape[1] * 8, context.shape[0] * 8), Image.Resampling.NEAREST)
        over_arr = context.copy(); over_arr[local_full] = [255, 0, 0]
        over = Image.fromarray(over_arr).resize(ori.size, Image.Resampling.NEAREST)
        only_arr = np.zeros_like(context); only_arr[local_full] = [255, 255, 255]
        only = Image.fromarray(only_arr).resize(ori.size, Image.Resampling.NEAREST)
        canvas = Image.new("RGB", (ori.width + over.width + only.width + 16, max(ori.height, over.height, only.height) + 30), "white")
        pen = ImageDraw.Draw(canvas); pen.text((4, 4), f"same-page peer for {obj['ELEMENT_ID']} | ORIGINAL / OVERLAY / MASK", fill="black")
        vx = 4
        for view in (ori, over, only): canvas.paste(view, (vx, 26)); vx += view.width + 4
        peer_contact_path = peer_dir / f"{obj['SAFE_FILENAME']}_peer_contact_8x.png"
        canvas.save(peer_contact_path)
        peer_rows.append({
            "ELEMENT_ID": obj["ELEMENT_ID"], "CHAR": obj["CHAR"], "SELECTION_POLICY": "same codepoint+font+color+size<=0.25pt; nearest raw sequence then lower sequence",
            "TARGET_RAW_SEQUENCE": target_seq, "PEER_RAW_SEQUENCE": peer["seq"], "PEER_PDF_BBOX_PT": list(pb),
            "TARGET_H_INK": th, "PEER_H_INK": ph, "H_RATIO": h_ratio,
            "TARGET_AREA": tarea, "PEER_AREA": parea, "AREA_RATIO": area_ratio,
            "PEER_NATIVE_MASK": str(peer_native_path.relative_to(ROOT)).replace("\\", "/"),
            "PEER_8X_MASK": str(peer_8x_path.relative_to(ROOT)).replace("\\", "/"),
            "PEER_CONTACT": str(peer_contact_path.relative_to(ROOT)).replace("\\", "/"), "DECISION": decision,
        })

    contacts = contact_sheets(objects, raw_masks, rgb)
    contact_by_id = {r["ELEMENT_ID"]: r for r in contacts}
    for obj in objects:
        obj.update(contact_by_id[str(obj["ELEMENT_ID"])])

    write_csv(ROOT / "after_pixel_measurements.csv", list(pixel_rows[0]), pixel_rows)
    write_csv(ROOT / "low_profile_peer_calibration.csv", list(peer_rows[0]), peer_rows)
    write_csv(ROOT / "safe_filename_map.csv", ["ELEMENT_ID", "SAFE_FILENAME"], objects)
    write_csv(ROOT / "object_inventory.csv", list(objects[0]), objects)
    write_json(ROOT / "object_inventory.json", objects)

    conservation = {
        "page_rawdict_total_chars": page_total, "page_rawdict_whitespace_chars": page_space,
        "page_rawdict_visible_nonspace_chars": page_total - page_space,
        "domain_total_chars": domain_total, "domain_whitespace_excluded": domain_space,
        "domain_final_glyphs": glyph_count, "outside_domain_total_chars": page_total - domain_total,
        "outside_domain_visible_nonspace": (page_total - page_space) - glyph_count,
        "equation_total": f"{page_total} = {domain_total} + {page_total - domain_total}",
        "equation_domain": f"{domain_total} = {glyph_count} + {domain_space}",
        "equation_nonspace": f"{page_total - page_space} = {glyph_count} + {(page_total - page_space) - glyph_count}",
        "page_get_drawings_total": 89, "target_explicit_drawings": 58,
        "outside_preceding_equations": 6, "outside_page_corner_artifacts": 2,
        "outside_following_prose_rules": 2, "outside_following_figure": 21,
        "drawing_equation": "89 = 6 + 58 + 2 + 2 + 21",
        "visible_pattern_layers_not_emitted_by_get_drawings": 2,
        "pattern_double_count_guard": "two patterns are separate visible layers; no get_drawings record exists; final-visible pattern masks cede shared pixels to later explicit graphics",
        "foreground_denominator_equation": f"{len(objects)} = {glyph_count} glyphs + 58 explicit drawings + 2 patterns",
    }
    write_json(ROOT / "denominator_conservation.json", conservation)

    # Every unordered pair is covered once. Raw overlap proves illegal intersection; final masks prove ownership.
    pair_rows: list[dict[str, object]] = []
    critical_rows: list[dict[str, object]] = []
    for i in range(len(objects)):
        a = objects[i]
        abox = tuple(int(v) for v in a["FINAL_MASK_BBOX_PX"])
        for j in range(i + 1, len(objects)):
            b = objects[j]
            bbox = tuple(int(v) for v in b["FINAL_MASK_BBOX_PX"])
            pair_id = f"PAIR-{i + 1:03d}-{j + 1:03d}"
            overlap = int(np.logical_and(raw_masks[i], raw_masks[j]).sum())
            final_overlap = int(np.logical_and(final_masks[i], final_masks[j]).sum())
            intended, reason = design_relation(a, b)
            threshold, rule = pair_rule(a, b)
            if rule == "TEXT_TEXT_VECTOR_BBOX":
                clearance = bbox_gap(tuple(a["PIXEL_SEARCH_BBOX"]), tuple(b["PIXEL_SEARCH_BBOX"]))
                mode = "PDF_VECTOR_BBOX_ON_NATIVE_GRID"
            else:
                lower = bbox_gap(abox, bbox)
                if lower <= max(12.0, threshold + 2.0):
                    clearance = mask_distance(final_masks[i], final_masks[j])
                    mode = "EXACT_FINAL_MASK_KDTREE"
                else:
                    clearance = lower
                    mode = "FINAL_MASK_TIGHT_BBOX_LOWER_BOUND"
            if overlap > 0 and not intended:
                decision = "TRUE_COLLISION"
                hard_failures.append({"FAIL_ID": pair_id, "TYPE": "ILLEGAL_OVERLAP", "VALUE": overlap, "THRESHOLD": 0})
            elif intended:
                decision = "INTENDED_DESIGN_OVERLAP" if overlap > 0 else "INTENDED_DESIGN_RELATION"
            elif threshold > 0 and clearance < threshold:
                decision = "CLEARANCE_FAIL"
                hard_failures.append({"FAIL_ID": pair_id, "TYPE": rule, "VALUE": clearance, "THRESHOLD": threshold})
            else:
                decision = "CLEAR"
            row = {
                "PAIR_ID": pair_id, "A_ID": a["ELEMENT_ID"], "B_ID": b["ELEMENT_ID"],
                "A_CLASS": a["CLASS"], "B_CLASS": b["CLASS"], "A_PARENT": a["SEMANTIC_PARENT"], "B_PARENT": b["SEMANTIC_PARENT"],
                "RAW_OVERLAP_PIXEL_COUNT": overlap, "FINAL_OVERLAP_PIXEL_COUNT": final_overlap,
                "CLEARANCE_PX": clearance, "DISTANCE_MODE": mode, "THRESHOLD_PX": threshold,
                "RULE": rule, "DESIGN_WHITELIST": intended, "WHITELIST_REASON": reason, "DECISION": decision,
            }
            pair_rows.append(row)
            if (not intended and threshold > 0 and clearance < threshold + 2.0) or (overlap > 0) or (a["OBJECT_TYPE"] == "MATH_RULE" and a["SEMANTIC_PARENT"] == b["SEMANTIC_PARENT"]) or (b["OBJECT_TYPE"] == "MATH_RULE" and a["SEMANTIC_PARENT"] == b["SEMANTIC_PARENT"]):
                critical_rows.append(dict(row))

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    if len(pair_rows) != expected_pairs or len({r["PAIR_ID"] for r in pair_rows}) != expected_pairs:
        raise RuntimeError("unordered-pair coverage failure")
    write_csv(ROOT / "all_unordered_pairs.csv", list(pair_rows[0]), pair_rows)
    write_csv(ROOT / "critical_pairs.csv", list(critical_rows[0]), critical_rows)

    # Dedicated evidence for every critical relation: raw A/B, intersection, original, overlay and exact 8x overlay.
    critical_dir = ROOT / "critical_pairs"
    critical_dir.mkdir(parents=True, exist_ok=True)
    id_to_index = {str(o["ELEMENT_ID"]): k for k, o in enumerate(objects)}
    for row in critical_rows:
        i, j = id_to_index[str(row["A_ID"])], id_to_index[str(row["B_ID"])]
        union = raw_masks[i] | raw_masks[j]
        box = tight_bbox(union)
        assert box is not None
        x0, y0, x1, y1 = max(0, box[0]-5), max(0, box[1]-5), min(width, box[2]+5), min(height, box[3]+5)
        aroi, broi = raw_masks[i][y0:y1, x0:x1], raw_masks[j][y0:y1, x0:x1]
        intersection = aroi & broi
        original = rgb[y0:y1, x0:x1].copy()
        overlay = original.copy(); overlay[aroi] = [255, 0, 0]; overlay[broi] = [0, 80, 255]; overlay[intersection] = [255, 0, 255]
        base = critical_dir / str(row["PAIR_ID"])
        Image.fromarray((aroi.astype(np.uint8)*255), mode="L").save(str(base) + "_A_raw.png")
        Image.fromarray((broi.astype(np.uint8)*255), mode="L").save(str(base) + "_B_raw.png")
        Image.fromarray((intersection.astype(np.uint8)*255), mode="L").save(str(base) + "_intersection.png")
        Image.fromarray(original).save(str(base) + "_original_1x.png")
        over_im = Image.fromarray(overlay); over_im.save(str(base) + "_overlay_1x.png")
        over_im.resize((over_im.width*8, over_im.height*8), Image.Resampling.NEAREST).save(str(base) + "_overlay_8x_nearest.png")
        row["RAW_A"] = str(Path(str(base) + "_A_raw.png").relative_to(ROOT)).replace("\\", "/")
        row["RAW_B"] = str(Path(str(base) + "_B_raw.png").relative_to(ROOT)).replace("\\", "/")
        row["INTERSECTION"] = str(Path(str(base) + "_intersection.png").relative_to(ROOT)).replace("\\", "/")
        row["ORIGINAL_1X"] = str(Path(str(base) + "_original_1x.png").relative_to(ROOT)).replace("\\", "/")
        row["OVERLAY_1X"] = str(Path(str(base) + "_overlay_1x.png").relative_to(ROOT)).replace("\\", "/")
        row["OVERLAY_8X"] = str(Path(str(base) + "_overlay_8x_nearest.png").relative_to(ROOT)).replace("\\", "/")
    if critical_rows:
        write_csv(ROOT / "critical_pairs_with_evidence.csv", list(critical_rows[0]), critical_rows)

    clip_count = sum(int(m[0, :].sum() + m[-1, :].sum() + m[:, 0].sum() + m[:, -1].sum()) for m in final_masks)
    text_edge = min(min(tuple(int(v) for v in o["FINAL_MASK_BBOX_PX"])[0], width - tuple(int(v) for v in o["FINAL_MASK_BBOX_PX"])[2],
                        tuple(int(v) for v in o["FINAL_MASK_BBOX_PX"])[1], height - tuple(int(v) for v in o["FINAL_MASK_BBOX_PX"])[3]) for o in objects[:glyph_count])
    math_rows = []
    for assembly, ids in (("EQ-WARMUP", ["G-EQ-WARMUP-UPPER", "G-EQ-WARMUP-LOWER"]), ("EQ-RETAINED", ["G-EQ-RETAINED-UPPER", "G-EQ-RETAINED-LOWER"])):
        indices = [id_to_index[x] for x in ids]
        union = final_masks[indices[0]] | final_masks[indices[1]]
        box = tight_bbox(union); assert box is not None
        h = box[3] - box[1]
        decision = "PASS" if h >= 22 else "FAIL"
        if decision == "FAIL": hard_failures.append({"FAIL_ID": f"MATH-{assembly}", "TYPE": "MATH_OPERATOR_H_INK", "VALUE": h, "THRESHOLD": 22})
        math_rows.append({"ASSEMBLY_ID": assembly, "MEMBER_RULE_IDS": ";".join(ids), "H_INK_PX": h, "HARD_FLOOR_PX": 22, "DECISION": decision})
    write_csv(ROOT / "math_assembly_measurements.csv", list(math_rows[0]), math_rows)

    outcome = "FAIL_TO_SA2" if hard_failures or clip_count or text_edge < 6 else "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3"
    summary = {
        "handoff_id": HANDOFF_ID, "sa1_model_route": "gpt-5.6-sol/xhigh", "figure_id": FIGURE_ID,
        "physical_page_1based": PAGE_1BASED, "N": len(objects), "glyphs": glyph_count,
        "explicit_pdf_drawings": 58, "visible_hatch_patterns": 2, "C_expected": expected_pairs,
        "C_covered": len(pair_rows), "critical_pair_count": len(critical_rows),
        "hard_failure_count": len(hard_failures), "hard_failures": hard_failures,
        "clip_pixel_count": clip_count, "minimum_text_crop_edge_clearance_px": text_edge,
        "empty_mask_count": sum(tight_bbox(m) is None for m in raw_masks) + sum(tight_bbox(m) is None for m in final_masks),
        "outcome": outcome,
    }
    write_json(ROOT / "denominator_and_pair_summary.json", summary)
    write_json(ROOT / "hard_failures.json", hard_failures)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["render-probe", "build-objects"])
    args = parser.parse_args()
    if args.mode == "render-probe":
        render_probe()
    elif args.mode == "build-objects":
        build_objects()


if __name__ == "__main__":
    main()
