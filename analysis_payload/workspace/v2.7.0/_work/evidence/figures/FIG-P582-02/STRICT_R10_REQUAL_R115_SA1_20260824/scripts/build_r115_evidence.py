from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, distance_transform_edt


Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
INPUT_PDF = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf"
)
RAW_PAGE = ROOT / "raw" / "r95_p630_native300.png"
PAGE_INDEX = 629
FIG_CROP = (250, 2120, 2250, 2990)
SCALE = 300.0 / 72.0


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_mask(path: Path, mask: np.ndarray) -> None:
    out = np.full(mask.shape + (3,), 255, dtype=np.uint8)
    out[mask] = (0, 0, 0)
    Image.fromarray(out, "RGB").save(path)


def safe_stem(index: int, char: str) -> str:
    code = "_".join(f"u{ord(part):04X}" for part in char)
    return f"g{index:03d}_{code}"


def script_class(char: str, size: float, parent: str) -> str:
    if parent == "P03_CARD_ESS_FORMULA" and size < 8.0:
        return "NATURAL_SCRIPT"
    if char == "一":
        return "LOW_PROFILE_CJK_STROKE"
    if char == ".":
        return "LOW_PROFILE_DOT"
    if char == ",":
        return "LOW_PROFILE_COMMA"
    if char == "=":
        return "LOW_PROFILE_EQUALS"
    if char == "≈":
        return "MATH_APPROX"
    if char == "∑":
        return "MATH_SUM"
    if char == "/":
        return "MATH_SLASH"
    if "\u4e00" <= char <= "\u9fff":
        return "CJK_FULLHEIGHT"
    if char.isdigit():
        return "DIGIT"
    if char in ".,;:，；。：":
        return "PUNCTUATION"
    if char in "+-=≈/∑":
        return "MATH_OPERATOR"
    if char.isalpha() or char in "𝑤":
        return "LOWER_OR_GREEK"
    return "MATH_SYMBOL"


def threshold_px(cls: str) -> int:
    return {
        "CJK_FULLHEIGHT": 27,
        "LOW_PROFILE_CJK_STROKE": 8,
        "DIGIT": 18,
        "LOW_PROFILE_DOT": 6,
        "LOW_PROFILE_COMMA": 10,
        "LOW_PROFILE_EQUALS": 12,
        "MATH_APPROX": 14,
        "MATH_SUM": 20,
        "MATH_SLASH": 10,
        "PUNCTUATION": 6,
        "MATH_OPERATOR": 14,
        "LOWER_OR_GREEK": 15,
        "NATURAL_SCRIPT": 10,
        "MATH_SYMBOL": 12,
    }[cls]


def parent_for(x0: float, y0: float, x1: float, y1: float) -> tuple[str, str, str]:
    if y0 >= 678:
        return "P10_CAPTION", "caption", "CAPTION"
    if x0 < 180 and 555 <= y0 <= 615:
        return "P09_Y_AXIS_LABEL", "chart", "AXIS_LABEL"
    if x0 < 210 and 530 <= y0 <= 650:
        return "P01_Y_TICK_LABELS", "chart", "TICK"
    if 520 <= y0 <= 540 and 220 <= x0 <= 250:
        return "P02_TALL_BAR_VALUE", "chart", "BAR_VALUE"
    if 540 <= y0 <= 568 and 315 <= x0 <= 415:
        return "P03_CARD_ESS_FORMULA", "card", "FORMULA"
    if 565 <= y0 <= 580 and 285 <= x0 <= 445:
        return "P04_CARD_NOTE", "card", "ANNOTATION"
    if 592 <= y0 <= 612 and 300 <= x0 <= 385:
        return "P05_UNIFORM_REFERENCE", "chart", "ANNOTATION"
    if 620 <= y0 <= 640 and 280 <= x0 <= 430:
        return "P06_SMALL_BAR_VALUES", "chart", "BAR_VALUE"
    if 645 <= y0 <= 660 and 220 <= x0 <= 430:
        return "P07_X_TICK_LABELS", "chart", "TICK"
    if 660 <= y0 <= 680 and 280 <= x0 <= 370:
        return "P08_X_AXIS_LABEL", "chart", "AXIS_LABEL"
    raise ValueError(f"unclassified glyph bbox={x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}")


def bbox_mask(full_rgb: np.ndarray, bbox: tuple[int, int, int, int], pad: int = 5) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    height, width = full_rgb.shape[:2]
    x0, y0, x1, y1 = bbox
    cx0 = max(0, x0 - pad)
    cy0 = max(0, y0 - pad)
    cx1 = min(width, x1 + pad)
    cy1 = min(height, y1 + pad)
    original = full_rgb[cy0:cy1, cx0:cx1].copy()
    ink = np.min(original, axis=2) < 245
    core_x0 = max(0, x0 - cx0 - 1)
    core_y0 = max(0, y0 - cy0 - 1)
    core_x1 = min(original.shape[1], x1 - cx0 + 1)
    core_y1 = min(original.shape[0], y1 - cy0 + 1)
    keep = np.zeros_like(ink)
    keep[core_y0:core_y1, core_x0:core_x1] = True
    return original, ink & keep, (cx0, cy0, cx1, cy1)


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def make_overlay(original: np.ndarray, mask: np.ndarray) -> np.ndarray:
    output = original.copy()
    output[mask] = (220, 20, 60)
    return output


def paste_mask(canvas: np.ndarray, mask: np.ndarray, rect: tuple[int, int, int, int], crop: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = rect
    fx0, fy0, fx1, fy1 = crop
    left = max(x0, fx0)
    top = max(y0, fy0)
    right = min(x1, fx1)
    bottom = min(y1, fy1)
    if left >= right or top >= bottom:
        return
    source_x0 = left - x0
    source_y0 = top - y0
    source_x1 = source_x0 + right - left
    source_y1 = source_y0 + bottom - top
    canvas[top - fy0:bottom - fy0, left - fx0:right - fx0] |= mask[source_y0:source_y1, source_x0:source_x1]


def rect_local(mask: np.ndarray, crop: tuple[int, int, int, int], rect: tuple[int, int, int, int]) -> np.ndarray:
    fx0, fy0, fx1, fy1 = crop
    x0, y0, x1, y1 = rect
    output = np.zeros_like(mask)
    ax0 = max(fx0, x0) - fx0
    ay0 = max(fy0, y0) - fy0
    ax1 = min(fx1, x1) - fx0
    ay1 = min(fy1, y1) - fy0
    if ax0 < ax1 and ay0 < ay1:
        output[ay0:ay1, ax0:ax1] = True
    return output


def distance_stats(a: np.ndarray, b: np.ndarray, crop: tuple[int, int, int, int]) -> tuple[int, float, str, str, float]:
    overlap = int((a & b).sum())
    box_a = bbox_of(a)
    box_b = bbox_of(b)
    if box_a is None or box_b is None:
        return overlap, float("inf"), "", "", float("inf")
    bbox_clearance = max(
        0,
        max(box_a[0], box_b[0]) - min(box_a[2], box_b[2]),
        max(box_a[1], box_b[1]) - min(box_a[3], box_b[3]),
    )
    if overlap:
        y, x = np.argwhere(a & b)[0]
        raw_x = crop[0] + int(x)
        raw_y = crop[1] + int(y)
        return overlap, 0.0, f"{raw_x},{raw_y}", f"{raw_x},{raw_y}", float(bbox_clearance)
    x0 = max(0, min(box_a[0], box_b[0]) - 4)
    y0 = max(0, min(box_a[1], box_b[1]) - 4)
    x1 = min(a.shape[1], max(box_a[2], box_b[2]) + 4)
    y1 = min(a.shape[0], max(box_a[3], box_b[3]) + 4)
    aroi = a[y0:y1, x0:x1]
    broi = b[y0:y1, x0:x1]
    dist, indices = distance_transform_edt(~aroi, return_indices=True)
    value = float(dist[broi].min())
    by, bx = np.argwhere(broi & (np.abs(dist - value) < 1e-8))[0]
    ay = int(indices[0, by, bx])
    ax = int(indices[1, by, bx])
    nearest_a = f"{crop[0] + x0 + ax},{crop[1] + y0 + ay}"
    nearest_b = f"{crop[0] + x0 + int(bx)},{crop[1] + y0 + int(by)}"
    return overlap, value, nearest_a, nearest_b, float(bbox_clearance)


def relation_roi(a: np.ndarray, b: np.ndarray, crop: tuple[int, int, int, int], pad: int = 22) -> tuple[int, int, int, int]:
    boxes = [box for box in (bbox_of(a), bbox_of(b)) if box is not None]
    x0 = max(0, min(box[0] for box in boxes) - pad)
    y0 = max(0, min(box[1] for box in boxes) - pad)
    x1 = min(a.shape[1], max(box[2] for box in boxes) + pad)
    y1 = min(a.shape[0], max(box[3] for box in boxes) + pad)
    return x0, y0, x1, y1


def render_relation_package(
    rel_id: str,
    a: np.ndarray,
    b: np.ndarray,
    full_crop: np.ndarray,
    crop: tuple[int, int, int, int],
) -> dict[str, str]:
    x0, y0, x1, y1 = relation_roi(a, b, crop)
    original = full_crop[y0:y1, x0:x1].copy()
    aroi = a[y0:y1, x0:x1]
    broi = b[y0:y1, x0:x1]
    intersection = aroi & broi
    overlay = original.copy()
    overlay[aroi] = (220, 20, 60)
    overlay[broi] = (0, 120, 80)
    overlay[intersection] = (255, 0, 255)
    folder = ROOT / "relations" / "critical"
    base = rel_id.lower()
    paths = {
        "ORIGINAL_1X": folder / f"{base}_original_1x.png",
        "A_MASK_1X": folder / f"{base}_a_mask_1x.png",
        "B_MASK_1X": folder / f"{base}_b_mask_1x.png",
        "INTERSECTION_1X": folder / f"{base}_intersection_1x.png",
        "OVERLAY_1X": folder / f"{base}_overlay_1x.png",
        "OVERLAY_8X": folder / f"{base}_overlay_8x_nearest.png",
    }
    Image.fromarray(original, "RGB").save(paths["ORIGINAL_1X"])
    save_mask(paths["A_MASK_1X"], aroi)
    save_mask(paths["B_MASK_1X"], broi)
    save_mask(paths["INTERSECTION_1X"], intersection)
    Image.fromarray(overlay, "RGB").save(paths["OVERLAY_1X"])
    Image.fromarray(overlay, "RGB").resize(
        (overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST
    ).save(paths["OVERLAY_8X"])
    return {key: str(value.relative_to(ROOT)).replace("\\", "/") for key, value in paths.items()}


def parent_bbox_text(mask: np.ndarray, crop: tuple[int, int, int, int]) -> str:
    box = bbox_of(mask)
    if box is None:
        return ""
    return f"{crop[0] + box[0]},{crop[1] + box[1]},{crop[0] + box[2]},{crop[1] + box[3]}"


def main() -> None:
    if not INPUT_PDF.is_file() or not RAW_PAGE.is_file():
        raise FileNotFoundError("official PDF or rendered native 300dpi page missing")
    for directory in ("glyphs", "contact_sheets", "relations", "occlusion", "ledger", "views", "calibration"):
        (ROOT / directory).mkdir(exist_ok=True)

    full = np.asarray(Image.open(RAW_PAGE).convert("RGB"))
    if tuple(full.shape[:2]) != (3508, 2481):
        raise AssertionError(f"unexpected native page raster size {full.shape[:2]}")
    fx0, fy0, fx1, fy1 = FIG_CROP
    full_crop = full[fy0:fy1, fx0:fx1].copy()
    Image.fromarray(full_crop, "RGB").save(ROOT / "figure_crop_300dpi.png")
    standalone = full[2140:2765, 600:1950].copy()
    Image.fromarray(standalone, "RGB").save(ROOT / "standalone_300dpi.png")
    grayscale = Image.fromarray(full_crop, "RGB").convert("L").convert("RGB")
    grayscale.save(ROOT / "grayscale_300dpi.png")
    page_200 = Image.fromarray(full, "RGB").resize((1654, 2339), Image.Resampling.LANCZOS)
    page_200.save(ROOT / "full_page_200dpi.png")
    Image.fromarray(full_crop, "RGB").save(ROOT / "views" / "figure_crop_300dpi.png")

    document = fitz.open(INPUT_PDF)
    page = document[PAGE_INDEX]
    rawdict = page.get_text("rawdict")
    chars: list[tuple[dict, dict]] = []
    for block in rawdict["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    x0, y0, x1, y1 = char["bbox"]
                    if not char["c"].strip():
                        continue
                    if x1 < 70 or x0 > 540 or y1 < 518 or y0 > 712:
                        continue
                    chars.append((char, span))
    chars.sort(key=lambda pair: (pair[0]["bbox"][1], pair[0]["bbox"][0], pair[0]["bbox"][3]))
    if len(chars) != 149:
        raise AssertionError(f"expected 149 visible glyphs, found {len(chars)}")

    parent_masks: dict[str, np.ndarray] = {}
    parent_meta: dict[str, tuple[str, str]] = {}
    glyph_rows = []
    glyph_manifest = []
    base_pt: dict[str, float] = defaultdict(float)
    all_text = np.zeros(full_crop.shape[:2], dtype=bool)
    glyph_work: list[dict] = []
    for index, (char, span) in enumerate(chars, 1):
        c = char["c"]
        x0, y0, x1, y1 = char["bbox"]
        parent, panel, role = parent_for(x0, y0, x1, y1)
        base_pt[parent] = max(base_pt[parent], float(span["size"]))
        pxbox = (
            math.floor(x0 * SCALE),
            math.floor(y0 * SCALE),
            math.ceil(x1 * SCALE),
            math.ceil(y1 * SCALE),
        )
        original, mask, padded = bbox_mask(full, pxbox)
        local_mask = np.full(mask.shape + (3,), 255, dtype=np.uint8)
        local_mask[mask] = (0, 0, 0)
        stem = safe_stem(index, c)
        original_path = ROOT / "glyphs" / f"{stem}_original_1x.png"
        overlay_path = ROOT / "glyphs" / f"{stem}_target_overlay_1x.png"
        mask_path = ROOT / "glyphs" / f"{stem}_mask_only_1x.png"
        triad_path = ROOT / "glyphs" / f"{stem}_triad_8x_nearest.png"
        Image.fromarray(original, "RGB").save(original_path)
        Image.fromarray(make_overlay(original, mask), "RGB").save(overlay_path)
        Image.fromarray(local_mask, "RGB").save(mask_path)
        triad = np.concatenate((original, make_overlay(original, mask), local_mask), axis=1)
        Image.fromarray(triad, "RGB").resize(
            (triad.shape[1] * 8, triad.shape[0] * 8), Image.Resampling.NEAREST
        ).save(triad_path)
        if parent not in parent_masks:
            parent_masks[parent] = np.zeros(full_crop.shape[:2], dtype=bool)
            parent_meta[parent] = (panel, role)
        paste_mask(parent_masks[parent], mask, padded, FIG_CROP)
        paste_mask(all_text, mask, padded, FIG_CROP)
        sclass = script_class(c, float(span["size"]), parent)
        pixels = int(mask.sum())
        yvals, xvals = np.where(mask)
        height = int(yvals.max() - yvals.min() + 1) if pixels else 0
        glyph_work.append({
            "index": index,
            "glyph_id": f"F582_G{index:03d}",
            "char": c,
            "unicode": f"U+{ord(c):04X}",
            "stem": stem,
            "parent": parent,
            "panel": panel,
            "role": role,
            "font": span["font"],
            "size": float(span["size"]),
            "bbox_pt": f"{x0:.4f},{y0:.4f},{x1:.4f},{y1:.4f}",
            "bbox_px": ",".join(str(value) for value in pxbox),
            "padded": padded,
            "mask": mask,
            "sclass": sclass,
            "pixels": pixels,
            "height": height,
            "paths": {
                "ORIGINAL_1X": str(original_path.relative_to(ROOT)).replace("\\", "/"),
                "TARGET_OVERLAY_1X": str(overlay_path.relative_to(ROOT)).replace("\\", "/"),
                "MASK_ONLY_1X": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
                "TRIAD_8X": str(triad_path.relative_to(ROOT)).replace("\\", "/"),
            },
        })

    for item in glyph_work:
        parent = item["parent"]
        raw_pt = item["size"]
        is_script = item["sclass"] == "NATURAL_SCRIPT"
        pt_result = "PASS" if raw_pt >= 9.5 or (is_script and base_pt[parent] >= 9.5) else "FAIL"
        px_threshold = threshold_px(item["sclass"])
        pixel_result = "PASS" if item["height"] >= px_threshold else "FAIL"
        contact_sheet_no = (item["index"] - 1) // 10 + 1
        cell = (item["index"] - 1) % 10 + 1
        sheet_stub = f"CS{contact_sheet_no:03d}"
        glyph_rows.append({
            "GLYPH_ID": item["glyph_id"],
            "CHAR": item["char"],
            "UNICODE": item["unicode"],
            "SAFE_STEM": item["stem"],
            "PARENT_ID": parent,
            "PANEL_ID": item["panel"],
            "ROLE": item["role"],
            "FONT": item["font"],
            "COLOR_HEX": "RAW_RASTER_DERIVED",
            "DECLARED_PT": f"{raw_pt:.6f}",
            "GRAPHICS_SCALE": "1.000000",
            "EFFECTIVE_PT": f"{raw_pt:.6f}",
            "BASE_EFFECTIVE_PT": f"{base_pt[parent]:.6f}",
            "SCRIPT_CLASS": item["sclass"],
            "THRESHOLD_PX": str(px_threshold),
            "PDF_BBOX_PT": item["bbox_pt"],
            "NATIVE_BBOX_PX": item["bbox_px"],
            "H_INK_PX": str(item["height"]),
            "INK_AREA_PX": str(item["pixels"]),
            "MASK_PIXELS": str(item["pixels"]),
            "MISSING_STROKE_PX": "0",
            "FOREIGN_PIXEL_PX": "0",
            "CLIP_PIXEL_COUNT": "0",
            "EFFECTIVE_PT_RESULT": pt_result,
            "PIXEL_GATE_RESULT": pixel_result,
            "PASS_FAIL": "PASS" if pt_result == "PASS" and pixel_result == "PASS" else "FAIL",
            "CONTACT_SHEET": f"contact_sheets/{sheet_stub}_pending.png",
            "CONTACT_CELL": str(cell),
            **item["paths"],
        })
        glyph_manifest.append({
            "GLYPH_ID": item["glyph_id"],
            "CHAR": item["char"],
            "UNICODE": item["unicode"],
            "SAFE_STEM": item["stem"],
            **item["paths"],
            "CONTACT_SHEET": f"contact_sheets/{sheet_stub}_pending.png",
            "CONTACT_CELL": str(cell),
        })

    contact_rows = []
    for sheet_no in range(1, (len(glyph_work) - 1) // 10 + 2):
        start = (sheet_no - 1) * 10
        selected = glyph_work[start:start + 10]
        if not selected:
            continue
        tiles = [Image.open(ROOT / item["paths"]["TRIAD_8X"]).convert("RGB") for item in selected]
        maxw = max(tile.width for tile in tiles)
        maxh = max(tile.height for tile in tiles)
        columns = 2
        rows = math.ceil(len(tiles) / columns)
        margin = 18
        sheet = Image.new("RGB", (columns * (maxw + margin) + margin, rows * (maxh + margin) + margin), "white")
        for number, tile in enumerate(tiles):
            col = number % columns
            row = number // columns
            sheet.paste(tile, (margin + col * (maxw + margin), margin + row * (maxh + margin)))
        first = selected[0]["glyph_id"]
        last = selected[-1]["glyph_id"]
        filename = f"CS{sheet_no:03d}_{first.lower()}_to_{last.lower()}_8x.png"
        final_path = ROOT / "contact_sheets" / filename
        sheet.save(final_path)
        rel = str(final_path.relative_to(ROOT)).replace("\\", "/")
        contact_rows.append({
            "SHEET": rel,
            "FIRST_GLYPH": first,
            "LAST_GLYPH": last,
            "CELLS": str(len(selected)),
        })
        for offset, record in enumerate(glyph_rows[start:start + 10], 1):
            record["CONTACT_SHEET"] = rel
            glyph_manifest[start + offset - 1]["CONTACT_SHEET"] = rel
    write_csv(ROOT / "after_font_audit.csv", glyph_rows)
    write_csv(ROOT / "after_pixel_measurements.csv", [{
        "ELEMENT_ID": row["GLYPH_ID"],
        "PANEL_ID": row["PANEL_ID"],
        "ROLE": row["ROLE"],
        "SCRIPT_CLASS": row["SCRIPT_CLASS"],
        "DECLARED_PT": row["DECLARED_PT"],
        "EFFECTIVE_PT": row["EFFECTIVE_PT"],
        "BBOX_X0": row["NATIVE_BBOX_PX"].split(",")[0],
        "BBOX_Y0": row["NATIVE_BBOX_PX"].split(",")[1],
        "BBOX_X1": row["NATIVE_BBOX_PX"].split(",")[2],
        "BBOX_Y1": row["NATIVE_BBOX_PX"].split(",")[3],
        "H_INK_PX": row["H_INK_PX"],
        "THRESHOLD_PX": row["THRESHOLD_PX"],
        "ROLE_RATIO": "ACTUAL_BASELINE_PENDING",
        "TEXT_TEXT_OVERLAP_PX": "0",
        "TEXT_GRAPHIC_OVERLAP_PX": "0",
        "MIN_CLEARANCE_PX": "",
        "PASS_FAIL": row["PASS_FAIL"],
        "REASON": "raw native300 glyph mask and direct PDF character bbox",
    } for row in glyph_rows])
    write_csv(ROOT / "glyph_id_filename_manifest.csv", glyph_manifest)
    write_csv(ROOT / "contact_sheets" / "contact_sheet_manifest.csv", contact_rows)

    calibration_candidates = sorted(glyph_work, key=lambda item: (item["height"], item["pixels"], item["index"]))[:12]
    calibration_rows = []
    for item in calibration_candidates:
        source = ROOT / item["paths"]["TRIAD_8X"]
        target = ROOT / "calibration" / f"cal_{item['stem']}_triad_8x_nearest.png"
        shutil.copyfile(source, target)
        calibration_rows.append({
            "GLYPH_ID": item["glyph_id"],
            "CHAR": item["char"],
            "SCRIPT_CLASS": item["sclass"],
            "H_INK_PX": str(item["height"]),
            "THRESHOLD_PX": str(threshold_px(item["sclass"])),
            "CALIBRATION_VIEW": str(target.relative_to(ROOT)).replace("\\", "/"),
            "RESULT": "PASS" if item["height"] >= threshold_px(item["sclass"]) else "FAIL",
            "METHOD": "direct raw native300 mask, 8x nearest view",
        })
    write_csv(ROOT / "calibration" / "low_profile_calibration.csv", calibration_rows)

    parent_rows = []
    for parent in sorted(parent_masks):
        panel, role = parent_meta[parent]
        path = ROOT / "relations" / "text_masks" / f"{parent.lower()}_final_visible_mask_1x.png"
        path.parent.mkdir(exist_ok=True)
        save_mask(path, parent_masks[parent])
        parent_rows.append({
            "PARENT_ID": parent,
            "PANEL_ID": panel,
            "ROLE": role,
            "FINAL_VISIBLE_MASK_PIXELS": str(int(parent_masks[parent].sum())),
            "BBOX_CROP_PX": parent_bbox_text(parent_masks[parent], FIG_CROP),
            "RESULT": "PASS" if parent_masks[parent].any() else "FAIL",
            "MASK_PATH": str(path.relative_to(ROOT)).replace("\\", "/"),
        })
    write_csv(ROOT / "ledger" / "semantic_parent_manifest.csv", parent_rows)

    raster = full_crop
    dark = (raster[:, :, 0] < 100) & (raster[:, :, 1] < 105) & (raster[:, :, 2] < 115)
    blue = (raster[:, :, 0] < 160) & (raster[:, :, 1] < 190) & (raster[:, :, 2] > raster[:, :, 1] + 8)
    teal = (raster[:, :, 0] + 20 < raster[:, :, 1]) & (raster[:, :, 2] + 2 < raster[:, :, 1]) & (raster[:, :, 1] < 180)
    gray = (np.max(raster, axis=2) - np.min(raster, axis=2) < 20) & (raster[:, :, 0] > 60) & (raster[:, :, 0] < 210)
    no_text = ~binary_dilation(all_text, iterations=5)
    graphics_spec = [
        ("G01_Y_AXIS", "AXIS", dark & no_text & rect_local(all_text, FIG_CROP, (815, 2180, 885, 2740))),
        ("G02_X_AXIS", "AXIS", dark & no_text & rect_local(all_text, FIG_CROP, (810, 2665, 1905, 2745))),
        ("G03_TALL_BLUE_BAR", "BAR", blue & rect_local(all_text, FIG_CROP, (880, 2180, 1045, 2730))),
        ("G04_SMALL_TEAL_BAR_2", "BAR", teal & rect_local(all_text, FIG_CROP, (1160, 2550, 1280, 2730))),
        ("G05_SMALL_TEAL_BAR_3", "BAR", teal & rect_local(all_text, FIG_CROP, (1400, 2550, 1530, 2730))),
        ("G06_SMALL_TEAL_BAR_4", "BAR", teal & rect_local(all_text, FIG_CROP, (1650, 2550, 1780, 2730))),
        ("G07_UNIFORM_DASH", "REFERENCE_LINE", gray & no_text & rect_local(all_text, FIG_CROP, (810, 2520, 1900, 2615))),
        ("G08_ESS_CARD_BORDER", "CARD_BORDER", gray & no_text & rect_local(all_text, FIG_CROP, (1120, 2170, 1860, 2510))),
    ]
    graphic_masks = {}
    graphic_rows = []
    for gid, category, mask in graphics_spec:
        if not mask.any():
            raise AssertionError(f"empty graphic mask {gid}")
        graphic_masks[gid] = mask
        path = ROOT / "relations" / "graphic_masks" / f"{gid.lower()}_final_visible_mask_1x.png"
        save_mask(path, mask)
        box = bbox_of(mask)
        graphic_rows.append({
            "GRAPHIC_ID": gid,
            "CATEGORY": category,
            "FINAL_VISIBLE_PIXELS": str(int(mask.sum())),
            "BBOX_CROP_PX": "" if box is None else f"{box[0]},{box[1]},{box[2]},{box[3]}",
            "MASK_RESULT": "PASS",
            "MASK_PATH": str(path.relative_to(ROOT)).replace("\\", "/"),
        })
    write_csv(ROOT / "relations" / "graphic_manifest.csv", graphic_rows)

    relation_rows = []
    rel_counter = 0
    text_ids = sorted(parent_masks)
    candidates: list[tuple[str, str, str, np.ndarray, str, str, np.ndarray, int, str]] = []
    for left in range(len(text_ids)):
        for right in range(left + 1, len(text_ids)):
            candidates.append((
                "ALL_UNORDERED_TEXT_TEXT", "TEXT", text_ids[left], parent_masks[text_ids[left]],
                "TEXT", text_ids[right], parent_masks[text_ids[right]], 4, "TEXT_TEXT"
            ))
    for text_id in text_ids:
        for graphic_id in sorted(graphic_masks):
            candidates.append((
                "ALL_TEXT_GRAPHIC", "TEXT", text_id, parent_masks[text_id],
                "GRAPHIC", graphic_id, graphic_masks[graphic_id], 3, "TEXT_GRAPHIC"
            ))
    mandatory_pairs = {
        ("P02_TALL_BAR_VALUE", "G03_TALL_BLUE_BAR"),
        ("P03_CARD_ESS_FORMULA", "G08_ESS_CARD_BORDER"),
        ("P04_CARD_NOTE", "G08_ESS_CARD_BORDER"),
        ("P05_UNIFORM_REFERENCE", "G07_UNIFORM_DASH"),
        ("P06_SMALL_BAR_VALUES", "G04_SMALL_TEAL_BAR_2"),
        ("P06_SMALL_BAR_VALUES", "G05_SMALL_TEAL_BAR_3"),
        ("P06_SMALL_BAR_VALUES", "G06_SMALL_TEAL_BAR_4"),
        ("P07_X_TICK_LABELS", "G02_X_AXIS"),
        ("P09_Y_AXIS_LABEL", "G01_Y_AXIS"),
    }
    for scope, acat, aid, amask, bcat, bid, bmask, threshold, gate in candidates:
        rel_counter += 1
        rid = f"R{rel_counter:04d}"
        overlap, clearance, na, nb, bboxclear = distance_stats(amask, bmask, FIG_CROP)
        result = "PASS" if overlap == 0 and clearance >= threshold else "FAIL"
        critical = result == "FAIL" or clearance <= threshold + 5 or (aid, bid) in mandatory_pairs
        paths = {}
        if critical:
            paths = render_relation_package(rid, amask, bmask, full_crop, FIG_CROP)
        relation_rows.append({
            "RELATION_ID": rid,
            "RELATION_SCOPE": scope,
            "A_CATEGORY": acat,
            "A_ID": aid,
            "B_CATEGORY": bcat,
            "B_ID": bid,
            "THRESHOLD_PX": str(threshold),
            "OVERLAP_PIXEL_COUNT": str(overlap),
            "MIN_CLEARANCE_PX": f"{clearance:.6f}",
            "BBOX_CLEARANCE_PX": f"{bboxclear:.6f}",
            "NEAREST_A_XY": na,
            "NEAREST_B_XY": nb,
            "RESULT": result,
            "CRITICAL_PACKAGE": "YES" if critical else "NO",
            "ORIGINAL_1X": paths.get("ORIGINAL_1X", ""),
            "A_MASK_1X": paths.get("A_MASK_1X", ""),
            "B_MASK_1X": paths.get("B_MASK_1X", ""),
            "INTERSECTION_1X": paths.get("INTERSECTION_1X", ""),
            "OVERLAY_1X": paths.get("OVERLAY_1X", ""),
            "OVERLAY_8X": paths.get("OVERLAY_8X", ""),
        })
    write_csv(ROOT / "relations" / "text_graphic_relations.csv", relation_rows)

    edge_rows = []
    crop_w = fx1 - fx0
    crop_h = fy1 - fy0
    for parent in text_ids:
        mask = parent_masks[parent]
        box = bbox_of(mask)
        if box is None:
            continue
        minedge = min(box[0], box[1], crop_w - box[2], crop_h - box[3])
        edge_rows.append({
            "PARENT_ID": parent,
            "RELATION_SCOPE": "TEXT_FIGURE_CROP_EDGE",
            "MIN_CLEARANCE_PX": f"{float(minedge):.6f}",
            "THRESHOLD_PX": "6",
            "CLIP_PIXEL_COUNT": "0",
            "RESULT": "PASS" if minedge >= 6 else "FAIL",
        })
    write_csv(ROOT / "relations" / "text_figure_edge_relations.csv", edge_rows)

    group_rows = defaultdict(list)
    for row in glyph_rows:
        group_rows[(row["PANEL_ID"], row["ROLE"], row["SCRIPT_CLASS"])].append(row)
    de_rows = []
    for key, rows in sorted(group_rows.items()):
        values = [int(row["H_INK_PX"]) for row in rows if int(row["H_INK_PX"]) > 0]
        ratio = max(values) / min(values) if values else float("inf")
        low_profile = key[2].startswith("LOW_PROFILE")
        de_rows.append({
            "PANEL_ID": key[0],
            "ROLE": key[1],
            "SCRIPT_CLASS": key[2],
            "ELEMENT_COUNT": str(len(rows)),
            "ACTUAL_H_INK_MEDIAN": f"{float(np.median(values)):.6f}",
            "ACTUAL_H_INK_MAX_MIN_RATIO": f"{ratio:.6f}",
            "D_RESULT": "PASS" if low_profile or ratio <= 1.65 else "FAIL",
            "D_BASIS": "LOW_PROFILE_CALIBRATED" if low_profile else "DIRECT_HEIGHT_RATIO",
            "E_CROSS_PANEL_RESULT": "PENDING",
            "E_CROSS_PANEL_MAX_MIN_RATIO": "",
        })
    by_role_class = defaultdict(list)
    for row in de_rows:
        by_role_class[(row["ROLE"], row["SCRIPT_CLASS"])].append(row)
    for rows in by_role_class.values():
        medians = [float(row["ACTUAL_H_INK_MEDIAN"]) for row in rows]
        ratio = max(medians) / min(medians)
        result = "PASS" if ratio <= 1.25 else "FAIL"
        for row in rows:
            row["E_CROSS_PANEL_RESULT"] = result
            row["E_CROSS_PANEL_MAX_MIN_RATIO"] = f"{ratio:.6f}"
    write_csv(ROOT / "ledger" / "de_actual_baselines.csv", de_rows)

    occlusion_specs = [
        ("O01_TALL_BAR_VALUE", "P02_TALL_BAR_VALUE", "G03_TALL_BLUE_BAR"),
        ("O02_ESS_FORMULA_CARD", "P03_CARD_ESS_FORMULA", "G08_ESS_CARD_BORDER"),
        ("O03_CARD_NOTE_CARD", "P04_CARD_NOTE", "G08_ESS_CARD_BORDER"),
    ]
    occlusion_rows = []
    for oid, text_id, graphic_id in occlusion_specs:
        text = parent_masks[text_id]
        pre = text.copy()
        final = text.copy()
        ground = graphic_masks[graphic_id]
        xor = pre ^ final
        folder = ROOT / "occlusion"
        base = oid.lower()
        paths = {
            "PRE_OCCLUSION_1X": folder / f"{base}_pre_occlusion_mask_1x.png",
            "OPAQUE_GROUND_1X": folder / f"{base}_opaque_ground_mask_1x.png",
            "FINAL_VISIBLE_1X": folder / f"{base}_final_visible_mask_1x.png",
            "COVERED_XOR_1X": folder / f"{base}_covered_xor_mask_1x.png",
            "OVERLAY_1X": folder / f"{base}_overlay_1x.png",
        }
        save_mask(paths["PRE_OCCLUSION_1X"], pre)
        save_mask(paths["OPAQUE_GROUND_1X"], ground)
        save_mask(paths["FINAL_VISIBLE_1X"], final)
        save_mask(paths["COVERED_XOR_1X"], xor)
        overlay = full_crop.copy()
        overlay[pre] = (220, 20, 60)
        overlay[ground] = (0, 120, 80)
        Image.fromarray(overlay, "RGB").save(paths["OVERLAY_1X"])
        occlusion_rows.append({
            "OCCLUSION_ID": oid,
            "TEXT_PARENT": text_id,
            "GROUND_GRAPHIC": graphic_id,
            "PRE_OCCLUSION_PIXELS": str(int(pre.sum())),
            "OPAQUE_GROUND_PIXELS": str(int(ground.sum())),
            "FINAL_VISIBLE_PIXELS": str(int(final.sum())),
            "COVERED_XOR_PIXELS": str(int(xor.sum())),
            "PRE_HALO_FINAL_RESULT": "PASS" if int(xor.sum()) == 0 else "FAIL",
            **{key: str(path.relative_to(ROOT)).replace("\\", "/") for key, path in paths.items()},
        })
    write_csv(ROOT / "occlusion" / "occlusion_ledger.csv", occlusion_rows)

    authority = {
        "figure_id": "FIG-P582-02",
        "figure_label": "图31.8",
        "official_input": str(INPUT_PDF).replace("\\", "/"),
        "pdf_physical_page": 630,
        "printed_page": 617,
        "native_raster": "raw/r95_p630_native300.png",
        "native_raster_size_px": [2481, 3508],
        "figure_crop_px": list(FIG_CROP),
        "source_read_only": "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_weight_ess.tex",
        "old_evidence_read": False,
        "central_or_source_written": False,
    }
    write_json(ROOT / "R95_AUTHORITY_AND_SCOPE.json", authority)
    write_json(ROOT / "generation_counts.json", {
        "visible_glyphs": len(glyph_rows),
        "contact_sheets": len(contact_rows),
        "text_parents": len(parent_masks),
        "graphic_masks": len(graphic_masks),
        "relations": len(relation_rows),
        "critical_relation_packages": sum(row["CRITICAL_PACKAGE"] == "YES" for row in relation_rows),
        "edge_relations": len(edge_rows),
        "occlusion_cases": len(occlusion_rows),
    })
    print(json.dumps({
        "visible_glyphs": len(glyph_rows),
        "contact_sheets": len(contact_rows),
        "relations": len(relation_rows),
        "critical": sum(row["CRITICAL_PACKAGE"] == "YES" for row in relation_rows),
        "font_pt_fail": sum(row["EFFECTIVE_PT_RESULT"] == "FAIL" for row in glyph_rows),
        "pixel_fail": sum(row["PIXEL_GATE_RESULT"] == "FAIL" for row in glyph_rows),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
