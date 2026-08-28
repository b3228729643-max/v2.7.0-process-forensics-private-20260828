from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
PAGE_NUMBER = 69
ROI_PT = (100.0, 60.0, 485.0, 222.0)  # x0, top, x1, bottom; figure body + caption only
DPI = 300
SCALE = DPI / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def rgb_is_white(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) >= 0.99
    try:
        return all(float(v) >= 0.99 for v in value)
    except TypeError:
        return False


def intersects(obj: dict, roi: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = roi
    return obj["x1"] > x0 and obj["x0"] < x1 and obj["bottom"] > top and obj["top"] < bottom


def pt_box_to_page_px(obj: dict) -> tuple[int, int, int, int]:
    return (
        int(math.floor(obj["x0"] * SCALE)),
        int(math.floor(obj["top"] * SCALE)),
        int(math.ceil(obj["x1"] * SCALE)),
        int(math.ceil(obj["bottom"] * SCALE)),
    )


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int]:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    overlap = ix * iy
    if overlap:
        return overlap, 0
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return 0, int(round(math.hypot(dx, dy)))


def ink_metrics(page_rgb: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = box
    h, w = page_rgb.shape[:2]
    x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
    x1, y1 = min(w, x1 + 1), min(h, y1 + 1)
    crop = page_rgb[y0:y1, x0:x1]
    if crop.size == 0:
        return 0, 0
    foreground = np.min(crop, axis=2) <= 235  # >=20/255 contrast from white
    ys, xs = np.where(foreground)
    if len(xs) == 0:
        return 0, 0
    return int(ys.max() - ys.min() + 1), int(foreground.sum())


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def contact_sheets(image: Image.Image, atoms: list[dict], prefix: str, per_sheet: int = 24) -> list[str]:
    out_names: list[str] = []
    font = ImageFont.load_default()
    for sheet_no, start in enumerate(range(0, len(atoms), per_sheet), 1):
        subset = atoms[start : start + per_sheet]
        tile_w, tile_h, cols = 240, 128, 4
        rows = math.ceil(len(subset) / cols)
        sheet = Image.new("RGB", (tile_w * cols, tile_h * rows), "white")
        draw = ImageDraw.Draw(sheet)
        for pos, atom in enumerate(subset):
            col, row = pos % cols, pos // cols
            ox, oy = col * tile_w, row * tile_h
            x0, y0, x1, y1 = (int(atom[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
            pad = 8
            crop = image.crop((max(0, x0 - pad), max(0, y0 - pad), min(image.width, x1 + pad), min(image.height, y1 + pad)))
            if crop.width and crop.height:
                factor = min((tile_w - 12) / crop.width, (tile_h - 28) / crop.height)
                factor = max(1.0, min(8.0, factor))
                resized = crop.resize((max(1, round(crop.width * factor)), max(1, round(crop.height * factor))), Image.Resampling.NEAREST)
                px = ox + (tile_w - resized.width) // 2
                py = oy + 18 + (tile_h - 20 - resized.height) // 2
                sheet.paste(resized, (px, py))
            label = f"{atom['atom_id']} {atom['kind']} {atom.get('text','')}"
            draw.text((ox + 4, oy + 3), label[:38], fill="black", font=font)
            draw.rectangle((ox, oy, ox + tile_w - 1, oy + tile_h - 1), outline=(180, 180, 180), width=1)
        name = f"{prefix}_{sheet_no:02d}.png"
        sheet.save(ROOT / "views" / name)
        out_names.append(name)
    return out_names


def main() -> None:
    (ROOT / "machine").mkdir(parents=True, exist_ok=True)
    (ROOT / "views").mkdir(parents=True, exist_ok=True)

    identity = {
        "pdf_path": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source_path": str(SOURCE),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "located_physical_page": PAGE_NUMBER,
        "locator_method": "global pdftotext UTF-8 exact-caption substring search; unique hit",
        "roi_pdf_points_x0_top_x1_bottom": ROI_PT,
        "render_dpi": DPI,
    }
    (ROOT / "machine" / "input_identity_and_locator.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    page_image = Image.open(ROOT / "views" / "full_page_300dpi.png").convert("RGB")
    page_array = np.asarray(page_image)
    roi_px = tuple(int(round(v * SCALE)) for v in ROI_PT)
    native = page_image.crop(roi_px)
    native.save(ROOT / "views" / "figure_caption_native1x_300dpi.png")
    native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "views" / "figure_caption_nearest8x.png"
    )
    ImageOps.grayscale(native).save(ROOT / "views" / "figure_caption_grayscale_300dpi.png")
    body_roi_px = tuple(int(round(v * SCALE)) for v in (100.0, 60.0, 485.0, 203.0))
    page_image.crop(body_roi_px).save(ROOT / "views" / "figure_body_native_crop_300dpi.png")
    critical_roi_px = tuple(int(round(v * SCALE)) for v in (118.0, 130.0, 151.0, 153.0))
    critical = page_image.crop(critical_roi_px)
    critical.save(ROOT / "views" / "critical_bottom_y_ticks_native1x_300dpi.png")
    critical.resize((critical.width * 8, critical.height * 8), Image.Resampling.NEAREST).save(
        ROOT / "views" / "critical_bottom_y_ticks_nearest8x.png"
    )

    with pdfplumber.open(PDF) as pdf:
        page = pdf.pages[PAGE_NUMBER - 1]
        raw: list[dict] = []
        g_index = 0
        p_index = 0
        b_index = 0
        for char in page.chars:
            if not (char.get("text") or "").strip() or not intersects(char, ROI_PT):
                continue
            g_index += 1
            atom = dict(char)
            atom_id = f"G{g_index:03d}"
            px_box = pt_box_to_page_px(atom)
            h_ink, ink_pixels = ink_metrics(page_array, px_box)
            raw.append(
                {
                    "atom_id": atom_id,
                    "kind": "GLYPH",
                    "subtype": "PDF_CHAR",
                    "text": atom.get("text", ""),
                    "fontname": atom.get("fontname", ""),
                    "declared_size_pt": atom.get("size", ""),
                    "x0_pt": atom["x0"],
                    "top_pt": atom["top"],
                    "x1_pt": atom["x1"],
                    "bottom_pt": atom["bottom"],
                    "page_px_x0": px_box[0],
                    "page_px_y0": px_box[1],
                    "page_px_x1": px_box[2],
                    "page_px_y1": px_box[3],
                    "h_ink_px": h_ink,
                    "foreground_px_in_local_bbox": ink_pixels,
                    "stroke_color": atom.get("stroking_color"),
                    "fill_color": atom.get("non_stroking_color"),
                    "machine_exclusion_code": "",
                }
            )
        for subtype, objects in (("LINE", page.lines), ("RECT", page.rects), ("CURVE", page.curves)):
            for obj in objects:
                if not intersects(obj, ROI_PT):
                    continue
                exclusion = subtype == "RECT" and obj.get("fill") and not obj.get("stroke") and rgb_is_white(obj.get("non_stroking_color"))
                if exclusion:
                    b_index += 1
                    atom_id = f"BG{b_index:03d}"
                else:
                    p_index += 1
                    atom_id = f"P{p_index:03d}"
                px_box = pt_box_to_page_px(obj)
                h_ink, ink_pixels = ink_metrics(page_array, px_box)
                raw.append(
                    {
                        "atom_id": atom_id,
                        "kind": "PATH",
                        "subtype": subtype,
                        "text": "",
                        "fontname": "",
                        "declared_size_pt": "",
                        "x0_pt": obj["x0"],
                        "top_pt": obj["top"],
                        "x1_pt": obj["x1"],
                        "bottom_pt": obj["bottom"],
                        "page_px_x0": px_box[0],
                        "page_px_y0": px_box[1],
                        "page_px_x1": px_box[2],
                        "page_px_y1": px_box[3],
                        "h_ink_px": h_ink,
                        "foreground_px_in_local_bbox": ink_pixels,
                        "stroke_color": obj.get("stroking_color"),
                        "fill_color": obj.get("non_stroking_color"),
                        "machine_exclusion_code": "WHITE_FILL_NO_STROKE" if exclusion else "",
                    }
                )

        words = [w for w in page.extract_words(use_text_flow=True, keep_blank_chars=False) if intersects(w, ROI_PT)]

    atom_fields = [
        "atom_id", "kind", "subtype", "text", "fontname", "declared_size_pt",
        "x0_pt", "top_pt", "x1_pt", "bottom_pt",
        "page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1",
        "h_ink_px", "foreground_px_in_local_bbox", "stroke_color", "fill_color",
        "machine_exclusion_code",
    ]
    write_csv(ROOT / "machine" / "atomic_candidates.csv", raw, atom_fields)
    included = [a for a in raw if not a["machine_exclusion_code"]]
    excluded = [a for a in raw if a["machine_exclusion_code"]]
    write_csv(ROOT / "machine" / "atomic_denominator.csv", included, atom_fields)
    write_csv(ROOT / "machine" / "provisional_background_exclusions.csv", excluded, atom_fields)

    word_rows = []
    for i, w in enumerate(words, 1):
        box = pt_box_to_page_px(w)
        word_rows.append(
            {
                "run_id": f"R{i:03d}", "text": w["text"], "x0_pt": w["x0"], "top_pt": w["top"],
                "x1_pt": w["x1"], "bottom_pt": w["bottom"],
                "page_px_x0": box[0], "page_px_y0": box[1], "page_px_x1": box[2], "page_px_y1": box[3],
            }
        )
    write_csv(
        ROOT / "machine" / "text_runs.csv", word_rows,
        ["run_id", "text", "x0_pt", "top_pt", "x1_pt", "bottom_pt", "page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"],
    )
    word_03 = next(w for w in word_rows if w["text"] == "0.3")
    word_035 = next(w for w in word_rows if w["text"] == "0.35")
    box_03 = tuple(int(word_03[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
    box_035 = tuple(int(word_035[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
    intersection = (
        max(box_03[0], box_035[0]), max(box_03[1], box_035[1]),
        min(box_03[2], box_035[2]), min(box_03[3], box_035[3]),
    )
    iw = max(0, intersection[2] - intersection[0])
    ih = max(0, intersection[3] - intersection[1])
    shared_region = page_array[intersection[1]:intersection[3], intersection[0]:intersection[2]]
    shared_foreground = int((np.min(shared_region, axis=2) <= 235).sum()) if shared_region.size else 0
    critical_geometry = {
        "label_0.3_bbox_native1x_300dpi": box_03,
        "label_0.35_bbox_native1x_300dpi": box_035,
        "shared_bbox_native1x_300dpi": intersection,
        "shared_bbox_width_px": iw,
        "shared_bbox_height_px": ih,
        "shared_bbox_area_px2": iw * ih,
        "foreground_px_in_shared_bbox": shared_foreground,
        "nearest8x_shared_bbox_width_px": iw * 8,
        "nearest8x_shared_bbox_height_px": ih * 8,
        "nearest8x_shared_bbox_area_px2": iw * ih * 64,
        "nearest8x_foreground_px_in_shared_bbox": shared_foreground * 64,
    }
    (ROOT / "machine" / "critical_label_geometry.json").write_text(
        json.dumps(critical_geometry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    pairs: list[dict] = []
    for pair_no, (a, b) in enumerate(itertools.combinations(included, 2), 1):
        abox = tuple(int(a[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        bbox = tuple(int(b[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        overlap, clearance = bbox_gap(abox, bbox)
        ix0, iy0 = max(abox[0], bbox[0]), max(abox[1], bbox[1])
        ix1, iy1 = min(abox[2], bbox[2]), min(abox[3], bbox[3])
        region_foreground = 0
        if ix1 > ix0 and iy1 > iy0:
            region = page_array[iy0:iy1, ix0:ix1]
            region_foreground = int((np.min(region, axis=2) <= 235).sum())
        pairs.append(
            {
                "pair_id": f"Q{pair_no:05d}",
                "atom_a": a["atom_id"], "atom_b": b["atom_id"],
                "kind_a": a["kind"], "kind_b": b["kind"],
                "text_a": a["text"], "text_b": b["text"],
                "native1x_bbox_overlap_px2": overlap,
                "native1x_bbox_clearance_px": clearance,
                "native1x_intersection_region_foreground_px": region_foreground,
                "nearest8x_bbox_overlap_px2": overlap * 64,
                "nearest8x_bbox_clearance_px": clearance * 8,
                "nearest8x_intersection_region_foreground_px": region_foreground * 64,
            }
        )
    pair_fields = [
        "pair_id", "atom_a", "atom_b", "kind_a", "kind_b", "text_a", "text_b",
        "native1x_bbox_overlap_px2", "native1x_bbox_clearance_px", "native1x_intersection_region_foreground_px",
        "nearest8x_bbox_overlap_px2", "nearest8x_bbox_clearance_px", "nearest8x_intersection_region_foreground_px",
    ]
    write_csv(ROOT / "machine" / "all_unordered_pairs.csv", pairs, pair_fields)

    overlay = native.copy()
    draw = ImageDraw.Draw(overlay)
    ox, oy = roi_px[0], roi_px[1]
    for atom in raw:
        x0, y0, x1, y1 = (int(atom[k]) for k in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        box = (x0 - ox, y0 - oy, x1 - ox, y1 - oy)
        if atom["atom_id"].startswith("BG"):
            color = (255, 128, 0)
        elif atom["kind"] == "GLYPH":
            color = (220, 20, 60)
        elif atom["subtype"] == "CURVE":
            color = (0, 80, 220)
        else:
            color = (0, 150, 60)
        draw.rectangle(box, outline=color, width=1)
    overlay.save(ROOT / "views" / "atomic_bbox_overlay_300dpi.png")

    glyphs = [a for a in included if a["kind"] == "GLYPH"]
    paths = [a for a in included if a["kind"] == "PATH"]
    glyph_sheets = contact_sheets(page_image, glyphs, "glyph_roi_sheet")
    path_sheets = contact_sheets(page_image, paths, "path_roi_sheet")

    src_rows = []
    for lineno, line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), 1):
        for m in re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", line):
            src_rows.append({"source_line": lineno, "declared_pt": m.group(1), "leading_pt": m.group(2), "source_text": line.strip()})
    write_csv(ROOT / "machine" / "source_font_facts.csv", src_rows, ["source_line", "declared_pt", "leading_pt", "source_text"])

    expected_pairs = len(included) * (len(included) - 1) // 2
    summary = {
        "roi_points": ROI_PT,
        "roi_pixels_300dpi": roi_px,
        "raw_nonempty_glyph_path_candidates": len(raw),
        "included_atomic_denominator_N": len(included),
        "glyph_atoms": len(glyphs),
        "path_atoms": len(paths),
        "provisional_background_exclusions": len(excluded),
        "unordered_pairs_expected_C_N_2": expected_pairs,
        "unordered_pairs_written": len(pairs),
        "pair_duplicate_count": len(pairs) - len({tuple(sorted((r["atom_a"], r["atom_b"]))) for r in pairs}),
        "pair_self_pair_count": sum(r["atom_a"] == r["atom_b"] for r in pairs),
        "glyph_contact_sheets": glyph_sheets,
        "path_contact_sheets": path_sheets,
    }
    (ROOT / "machine" / "denominator_and_pair_closure.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
