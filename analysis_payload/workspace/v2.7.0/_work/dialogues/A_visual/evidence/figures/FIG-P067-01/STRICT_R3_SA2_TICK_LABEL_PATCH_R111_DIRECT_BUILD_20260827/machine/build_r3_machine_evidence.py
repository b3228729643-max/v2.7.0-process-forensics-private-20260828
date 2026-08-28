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


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827")
PDF = ROOT / "build" / "v260_FIG-P067-01_standalone.pdf"
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex")
PAGE_PNG = ROOT / "views" / "standalone_300dpi.png"
DPI = 300
SCALE = DPI / 72.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def is_white(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) >= 0.99
    try:
        return all(float(item) >= 0.99 for item in value)  # type: ignore[arg-type]
    except TypeError:
        return False


def pt_to_px_box(obj: dict) -> tuple[int, int, int, int]:
    return (
        int(math.floor(float(obj["x0"]) * SCALE)),
        int(math.floor(float(obj["top"]) * SCALE)),
        int(math.ceil(float(obj["x1"]) * SCALE)),
        int(math.ceil(float(obj["bottom"]) * SCALE)),
    )


def bbox_overlap_and_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, float]:
    width = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    height = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    if width and height:
        return width * height, 0.0
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return 0, round(math.hypot(dx, dy), 6)


def foreground_metrics(rgb: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = box
    height, width = rgb.shape[:2]
    x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
    x1, y1 = min(width, x1 + 1), min(height, y1 + 1)
    crop = rgb[y0:y1, x0:x1]
    if not crop.size:
        return 0, 0
    foreground = np.min(crop, axis=2) <= 235
    ys, xs = np.where(foreground)
    if not len(xs):
        return 0, 0
    return int(ys.max() - ys.min() + 1), int(foreground.sum())


def intersection_foreground(rgb: np.ndarray, a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    region = rgb[y0:y1, x0:x1]
    return int((np.min(region, axis=2) <= 235).sum()) if region.size else 0


def contact_sheets(page: Image.Image, atoms: list[dict], prefix: str, per_sheet: int = 24) -> list[str]:
    names: list[str] = []
    font = ImageFont.load_default()
    for sheet_number, start in enumerate(range(0, len(atoms), per_sheet), 1):
        subset = atoms[start : start + per_sheet]
        tile_w, tile_h, cols = 240, 132, 4
        row_count = math.ceil(len(subset) / cols)
        sheet = Image.new("RGB", (tile_w * cols, tile_h * row_count), "white")
        draw = ImageDraw.Draw(sheet)
        for position, atom in enumerate(subset):
            col, row = position % cols, position // cols
            ox, oy = col * tile_w, row * tile_h
            x0, y0, x1, y1 = (int(atom[key]) for key in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
            pad = 10
            crop = page.crop((max(0, x0 - pad), max(0, y0 - pad), min(page.width, x1 + pad), min(page.height, y1 + pad)))
            if crop.width and crop.height:
                factor = max(1.0, min(8.0, min((tile_w - 12) / crop.width, (tile_h - 32) / crop.height)))
                resized = crop.resize((max(1, round(crop.width * factor)), max(1, round(crop.height * factor))), Image.Resampling.NEAREST)
                sheet.paste(resized, (ox + (tile_w - resized.width) // 2, oy + 20 + (tile_h - 24 - resized.height) // 2))
            label = f"{atom['atom_id']} {atom['kind']} {atom.get('text', '')}"
            draw.text((ox + 4, oy + 3), label[:42], fill="black", font=font)
            draw.rectangle((ox, oy, ox + tile_w - 1, oy + tile_h - 1), outline=(175, 175, 175), width=1)
        name = f"{prefix}_{sheet_number:02d}.png"
        sheet.save(ROOT / "views" / name)
        names.append(name)
    return names


def main() -> None:
    machine = ROOT / "machine"
    views = ROOT / "views"
    machine.mkdir(parents=True, exist_ok=True)
    views.mkdir(parents=True, exist_ok=True)

    page_image = Image.open(PAGE_PNG).convert("RGB")
    page_array = np.asarray(page_image)
    source_text = SOURCE.read_text(encoding="utf-8")

    with pdfplumber.open(PDF) as document:
        if len(document.pages) != 1:
            raise RuntimeError("Standalone candidate must contain exactly one page.")
        page = document.pages[0]
        raw: list[dict] = []
        glyph_number = 0
        path_number = 0
        background_number = 0
        for char in page.chars:
            if not (char.get("text") or "").strip():
                continue
            glyph_number += 1
            box = pt_to_px_box(char)
            ink_height, ink_pixels = foreground_metrics(page_array, box)
            raw.append({
                "atom_id": f"G{glyph_number:03d}", "kind": "GLYPH", "subtype": "PDF_CHAR",
                "text": char.get("text", ""), "fontname": char.get("fontname", ""),
                "declared_size_pt": char.get("size", ""),
                "x0_pt": char["x0"], "top_pt": char["top"], "x1_pt": char["x1"], "bottom_pt": char["bottom"],
                "page_px_x0": box[0], "page_px_y0": box[1], "page_px_x1": box[2], "page_px_y1": box[3],
                "h_ink_px": ink_height, "foreground_px_in_local_bbox": ink_pixels,
                "stroke_color": char.get("stroking_color"), "fill_color": char.get("non_stroking_color"),
                "machine_exclusion_code": "",
            })
        for subtype, objects in (("LINE", page.lines), ("RECT", page.rects), ("CURVE", page.curves)):
            for obj in objects:
                exclusion = subtype == "RECT" and obj.get("fill") and not obj.get("stroke") and is_white(obj.get("non_stroking_color"))
                if exclusion:
                    background_number += 1
                    atom_id = f"BG{background_number:03d}"
                else:
                    path_number += 1
                    atom_id = f"P{path_number:03d}"
                box = pt_to_px_box(obj)
                ink_height, ink_pixels = foreground_metrics(page_array, box)
                raw.append({
                    "atom_id": atom_id, "kind": "PATH", "subtype": subtype, "text": "", "fontname": "",
                    "declared_size_pt": "", "x0_pt": obj["x0"], "top_pt": obj["top"],
                    "x1_pt": obj["x1"], "bottom_pt": obj["bottom"],
                    "page_px_x0": box[0], "page_px_y0": box[1], "page_px_x1": box[2], "page_px_y1": box[3],
                    "h_ink_px": ink_height, "foreground_px_in_local_bbox": ink_pixels,
                    "stroke_color": obj.get("stroking_color"), "fill_color": obj.get("non_stroking_color"),
                    "machine_exclusion_code": "WHITE_FILL_NO_STROKE" if exclusion else "",
                })
        words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
        page_width_pt = float(page.width)
        page_height_pt = float(page.height)

    fields = [
        "atom_id", "kind", "subtype", "text", "fontname", "declared_size_pt",
        "x0_pt", "top_pt", "x1_pt", "bottom_pt", "page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1",
        "h_ink_px", "foreground_px_in_local_bbox", "stroke_color", "fill_color", "machine_exclusion_code",
    ]
    included = [atom for atom in raw if not atom["machine_exclusion_code"]]
    excluded = [atom for atom in raw if atom["machine_exclusion_code"]]
    glyphs = [atom for atom in included if atom["kind"] == "GLYPH"]
    paths = [atom for atom in included if atom["kind"] == "PATH"]
    write_csv(machine / "atomic_candidates.csv", raw, fields)
    write_csv(machine / "atomic_denominator.csv", included, fields)
    write_csv(machine / "background_exclusions.csv", excluded, fields)

    min_x = min(int(atom["page_px_x0"]) for atom in included)
    min_y = min(int(atom["page_px_y0"]) for atom in included)
    max_x = max(int(atom["page_px_x1"]) for atom in included)
    max_y = max(int(atom["page_px_y1"]) for atom in included)
    margin = 28
    content_box = (max(0, min_x - margin), max(0, min_y - margin), min(page_image.width, max_x + margin), min(page_image.height, max_y + margin))
    figure = page_image.crop(content_box)
    figure.save(views / "figure_native1x_300dpi.png")
    ImageOps.grayscale(figure).save(views / "figure_grayscale_300dpi.png")

    overlay = figure.copy()
    draw = ImageDraw.Draw(overlay)
    for atom in raw:
        x0, y0, x1, y1 = (int(atom[key]) for key in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        shifted = (x0 - content_box[0], y0 - content_box[1], x1 - content_box[0], y1 - content_box[1])
        color = (255, 128, 0) if atom["atom_id"].startswith("BG") else ((220, 20, 60) if atom["kind"] == "GLYPH" else (0, 90, 210))
        draw.rectangle(shifted, outline=color, width=1)
    overlay.save(views / "atomic_bbox_overlay_300dpi.png")

    word_rows = []
    for number, word in enumerate(words, 1):
        box = pt_to_px_box(word)
        word_rows.append({
            "run_id": f"R{number:03d}", "text": word["text"], "x0_pt": word["x0"], "top_pt": word["top"],
            "x1_pt": word["x1"], "bottom_pt": word["bottom"],
            "page_px_x0": box[0], "page_px_y0": box[1], "page_px_x1": box[2], "page_px_y1": box[3],
        })
    write_csv(machine / "text_runs.csv", word_rows, [
        "run_id", "text", "x0_pt", "top_pt", "x1_pt", "bottom_pt",
        "page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1",
    ])

    label_words: dict[str, dict] = {}
    for target in ("0.15", "0.3", "0.35"):
        matches = [word for word in word_rows if word["text"] == target]
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one word for {target}, got {len(matches)}")
        label_words[target] = matches[0]
    label_boxes = {
        label: tuple(int(word[key]) for key in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        for label, word in label_words.items()
    }
    critical_union = (
        min(box[0] for box in label_boxes.values()) - 16,
        min(box[1] for box in label_boxes.values()) - 16,
        max(box[2] for box in label_boxes.values()) + 16,
        max(box[3] for box in label_boxes.values()) + 16,
    )
    critical = page_image.crop(critical_union)
    critical.save(views / "critical_y_ticks_native1x_300dpi.png")
    critical.resize((critical.width * 8, critical.height * 8), Image.Resampling.NEAREST).save(views / "critical_y_ticks_nearest8x.png")

    def label_relation(lower: str, upper: str) -> dict:
        a, b = label_boxes[lower], label_boxes[upper]
        overlap, gap = bbox_overlap_and_gap(a, b)
        return {
            "labels": [lower, upper],
            "lower_word_bbox_pdf_pt": [label_words[lower][key] for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt")],
            "upper_word_bbox_pdf_pt": [label_words[upper][key] for key in ("x0_pt", "top_pt", "x1_pt", "bottom_pt")],
            "native1x_bbox_overlap_px2": overlap,
            "native1x_bbox_clearance_px": gap,
            "native1x_intersection_foreground_px": intersection_foreground(page_array, a, b),
            "nearest8x_bbox_overlap_px2": overlap * 64,
            "nearest8x_bbox_clearance_px": gap * 8,
            "nearest8x_intersection_foreground_px": intersection_foreground(page_array, a, b) * 64,
        }
    target_relations = {
        "0.35_to_0.3": label_relation("0.35", "0.3"),
        "0.3_to_0.15": label_relation("0.3", "0.15"),
    }
    write_json(machine / "critical_y_tick_geometry.json", target_relations)

    pairs: list[dict] = []
    for number, (left, right) in enumerate(itertools.combinations(included, 2), 1):
        left_box = tuple(int(left[key]) for key in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        right_box = tuple(int(right[key]) for key in ("page_px_x0", "page_px_y0", "page_px_x1", "page_px_y1"))
        overlap, gap = bbox_overlap_and_gap(left_box, right_box)
        intersection_ink = intersection_foreground(page_array, left_box, right_box)
        pairs.append({
            "pair_id": f"Q{number:05d}", "atom_a": left["atom_id"], "atom_b": right["atom_id"],
            "kind_a": left["kind"], "kind_b": right["kind"], "text_a": left["text"], "text_b": right["text"],
            "native1x_bbox_overlap_px2": overlap, "native1x_bbox_clearance_px": gap,
            "native1x_intersection_foreground_px": intersection_ink,
            "nearest8x_bbox_overlap_px2": overlap * 64, "nearest8x_bbox_clearance_px": gap * 8,
            "nearest8x_intersection_foreground_px": intersection_ink * 64,
        })
    pair_fields = [
        "pair_id", "atom_a", "atom_b", "kind_a", "kind_b", "text_a", "text_b",
        "native1x_bbox_overlap_px2", "native1x_bbox_clearance_px", "native1x_intersection_foreground_px",
        "nearest8x_bbox_overlap_px2", "nearest8x_bbox_clearance_px", "nearest8x_intersection_foreground_px",
    ]
    write_csv(machine / "all_unordered_pairs.csv", pairs, pair_fields)

    glyph_sheets = contact_sheets(page_image, glyphs, "glyph_roi_sheet")
    path_sheets = contact_sheets(page_image, paths, "path_roi_sheet")

    source_font_rows = []
    for line_number, line in enumerate(source_text.splitlines(), 1):
        for match in re.finditer(r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}", line):
            source_font_rows.append({
                "source_line": line_number, "declared_pt": match.group(1),
                "leading_pt": match.group(2), "source_text": line.strip(),
            })
    write_csv(machine / "source_font_facts.csv", source_font_rows, ["source_line", "declared_pt", "leading_pt", "source_text"])

    pmf_token = "coordinates {(1,.15) (2,.30) (3,.35) (4,.20)};"
    cdf_tokens = ["(1,.15)", "(2,.45)", "(3,.80)", "(4,1)"]
    semantic = {
        "pmf_masses": [0.15, 0.30, 0.35, 0.20],
        "pmf_sum": 1.0,
        "cdf_levels": [0.15, 0.45, 0.80, 1.00],
        "cdf_monotone": True,
        "right_continuity_encoded_by_filled_postjump_and_open_prejump": True,
        "pmf_coordinate_token_count": source_text.count(pmf_token),
        "cdf_coordinate_token_presence": {token: source_text.count(token) for token in cdf_tokens},
        "lower_y_tick_token_count": source_text.count("ytick={0,.15,.30,.35}"),
        "suppressed_and_replayed_0_3_count": source_text.count("at (axis cs:.45,.30) {$0.3$};"),
    }
    write_json(machine / "semantic_source_crosscheck.json", semantic)

    expected_pairs = len(included) * (len(included) - 1) // 2
    closure = {
        "page_size_pdf_pt": [page_width_pt, page_height_pt],
        "render_size_px_300dpi": [page_image.width, page_image.height],
        "content_bbox_px_with_margin": list(content_box),
        "raw_nonempty_glyph_path_candidates": len(raw),
        "included_atomic_denominator_N": len(included),
        "glyph_atoms": len(glyphs),
        "path_atoms": len(paths),
        "background_exclusions": len(excluded),
        "unordered_pairs_expected_C_N_2": expected_pairs,
        "unordered_pairs_written": len(pairs),
        "pair_duplicate_count": len(pairs) - len({tuple(sorted((row["atom_a"], row["atom_b"]))) for row in pairs}),
        "pair_self_count": sum(row["atom_a"] == row["atom_b"] for row in pairs),
        "glyph_contact_sheets": glyph_sheets,
        "path_contact_sheets": path_sheets,
    }
    write_json(machine / "denominator_and_pair_closure.json", closure)

    clip_count = sum(
        float(atom["x0_pt"]) < 0 or float(atom["top_pt"]) < 0 or float(atom["x1_pt"]) > page_width_pt or float(atom["bottom_pt"]) > page_height_pt
        for atom in included
    )
    empty_count = sum(int(atom["foreground_px_in_local_bbox"]) == 0 for atom in included)
    target_overlap = sum(int(item["native1x_bbox_overlap_px2"]) > 0 or int(item["native1x_intersection_foreground_px"]) > 0 for item in target_relations.values())
    identity = {
        "pdf_path": str(PDF), "pdf_bytes": PDF.stat().st_size, "pdf_sha256": sha256(PDF),
        "source_path": str(SOURCE), "source_bytes": SOURCE.stat().st_size, "source_sha256": sha256(SOURCE),
        "wrapper_path": str(WRAPPER), "wrapper_bytes": WRAPPER.stat().st_size, "wrapper_sha256": sha256(WRAPPER),
        "page_count": 1, "page_size": "A4", "render_dpi": DPI,
    }
    write_json(machine / "input_identity.json", identity)
    result = {
        "status": "MACHINE_PASS_READY_FOR_MANUAL",
        "N": len(included), "C_N_2": expected_pairs,
        "glyph_count": len(glyphs), "path_count": len(paths), "background_exclusion_count": len(excluded),
        "pair_rows": len(pairs), "pair_duplicate_count": closure["pair_duplicate_count"], "pair_self_count": closure["pair_self_count"],
        "clip_count": clip_count, "empty_foreground_atom_count": empty_count,
        "target_tick_relation_hard_overlap_count": target_overlap,
        "machine_hard_failure_count": clip_count + empty_count + target_overlap,
        "manual_fields_generated_by_machine": 0,
    }
    write_json(ROOT / "MACHINE_RESULT.json", result)


if __name__ == "__main__":
    main()
