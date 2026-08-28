#!/usr/bin/env python3
"""Deterministic official-R99 peer selection and one-shot measurement.

Phase ``select`` uses PDF text metadata only.  It writes the chosen identity
before any candidate pixels are rendered or measured.  Phase ``measure`` then
renders exactly that one preselected page at 300 dpi and applies the same
directed-colour raw-mask rule (20-level contrast threshold) as the R6 audit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf")
EXPECTED_PDF_SHA256 = "E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6"
ORIGIN_R6 = ROOT.parent / "STRICT_R6_SA2_REPAIR_R99_LOCAL_20260825"
SELECTION_FILE = ROOT / "peer_selection_metadata.json"
MEASUREMENT_FILE = ROOT / "peer_measurement.json"
TARGET_FIGURE = (32, 8)
TARGET_ID = "GLYPH_0072"
TARGET_CODEPOINT = "U+002E"
TARGET_FONT = "STIXTwoText-Bold"
TARGET_SIZE_PT = 9.9626
TARGET_COLOR = (31, 35, 40)
TARGET_DIRECTION = (1.0, 0.0)
SCALE = 300.0 / 72.0
LOWER = 0.92
UPPER = 1.08


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rgb_int_to_u8(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def base_font_name(name: str) -> str:
    return name.split("+", 1)[-1]


def exact_direction(value: Any) -> bool:
    return len(value) >= 2 and abs(float(value[0]) - 1.0) <= 1e-6 and abs(float(value[1])) <= 1e-6


def collect_exact_caption_candidates(doc: fitz.Document) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    caption_re = re.compile(r"图\s*32\.(\d+)")
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        raw = page.get_text("rawdict")
        font_entries = page.get_fonts(full=True)
        for block_index, block in enumerate(raw.get("blocks", [])):
            if block.get("type") != 0:
                continue
            for line_index, line in enumerate(block.get("lines", [])):
                chars: list[dict[str, Any]] = []
                for span in line.get("spans", []):
                    for char in span.get("chars", []):
                        chars.append({
                            "c": char.get("c", ""),
                            "bbox": [round(float(v), 6) for v in char.get("bbox", (0, 0, 0, 0))],
                            "font": base_font_name(str(span.get("font", ""))),
                            "size_pt": round(float(span.get("size", 0.0)), 4),
                            "color_rgb": list(rgb_int_to_u8(int(span.get("color", 0)))),
                        })
                text = "".join(item["c"] for item in chars)
                for match in caption_re.finditer(text):
                    figure_minor = int(match.group(1))
                    dot_index = text.find(".", match.start(), match.end())
                    if dot_index < 0 or dot_index >= len(chars):
                        continue
                    item = chars[dot_index]
                    direction = [round(float(v), 6) for v in line.get("dir", (0.0, 0.0))]
                    if not (
                        item["c"] == "."
                        and item["font"] == TARGET_FONT
                        and abs(float(item["size_pt"]) - TARGET_SIZE_PT) <= 0.0001
                        and tuple(item["color_rgb"]) == TARGET_COLOR
                        and exact_direction(direction)
                    ):
                        continue
                    matching_xrefs = sorted({
                        int(entry[0]) for entry in font_entries
                        if base_font_name(str(entry[3])) == TARGET_FONT
                    })
                    candidates.append({
                        "figure_label": f"图32.{figure_minor}",
                        "figure_major": 32,
                        "figure_minor": figure_minor,
                        "physical_page": page_index + 1,
                        "page_index_zero_based": page_index,
                        "block_index": block_index,
                        "line_index": line_index,
                        "line_text": text,
                        "line_bbox_pt": [round(float(v), 6) for v in line.get("bbox", (0, 0, 0, 0))],
                        "glyph_bbox_pt": item["bbox"],
                        "codepoint": TARGET_CODEPOINT,
                        "char": ".",
                        "font": item["font"],
                        "font_xrefs_on_page": matching_xrefs,
                        "font_weight": "Bold",
                        "size_pt": item["size_pt"],
                        "color_rgb": item["color_rgb"],
                        "direction": direction,
                        "orientation": "HORIZONTAL",
                    })
    return candidates


def selection_key(row: dict[str, Any]) -> tuple[Any, ...]:
    bbox = row["glyph_bbox_pt"]
    return (
        abs(int(row["figure_minor"]) - TARGET_FIGURE[1]),
        int(row["physical_page"]),
        float(bbox[1]),
        float(bbox[0]),
    )


def select_phase() -> None:
    if SELECTION_FILE.exists() or MEASUREMENT_FILE.exists():
        raise RuntimeError("selection or measurement already exists; one-shot staging cannot be reselected")
    if not PDF.is_file():
        raise RuntimeError(f"official R99 PDF missing: {PDF}")
    pdf_hash = sha256(PDF)
    if pdf_hash != EXPECTED_PDF_SHA256:
        raise RuntimeError(f"official R99 SHA mismatch: {pdf_hash}")
    doc = fitz.open(PDF)
    try:
        exact = collect_exact_caption_candidates(doc)
        alternatives = [row for row in exact if int(row["figure_minor"]) != TARGET_FIGURE[1]]
        alternatives.sort(key=selection_key)
        if not alternatives:
            selected = None
            status = "NO_UNIQUE_EXACT_PEER"
        else:
            selected = alternatives[0]
            best_key = selection_key(selected)
            tied = [row for row in alternatives if selection_key(row) == best_key]
            if len(tied) != 1:
                selected = None
                status = "NO_UNIQUE_EXACT_PEER"
            else:
                status = "IDENTITY_PRESELECTED_BEFORE_METRICS"
        write_json(SELECTION_FILE, {
            "selection_status": status,
            "selection_rule_predeclared": (
                "Exclude the FIG 32.8 semantic instance; require exact U+002E, "
                "STIXTwoText-Bold, 9.9626pt, RGB(31,35,40), horizontal; choose "
                "minimum absolute figure-number distance, then lower physical page, "
                "then earlier reading-order bbox. Pixel H/area are forbidden before selection."
            ),
            "target_figure": "图32.8",
            "official_pdf": str(PDF),
            "official_pdf_sha256": pdf_hash,
            "official_pdf_pages": doc.page_count,
            "exact_metadata_candidate_count_including_target": len(exact),
            "eligible_alternative_count": len(alternatives),
            "exact_metadata_candidates": exact,
            "selected_peer_identity": selected,
            "pixel_metrics_deliberately_absent": True,
            "cherry_pick_forbidden": True,
        })
    finally:
        doc.close()


def rect_px(rect: list[float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect[0] * SCALE)) - pad)
    y0 = max(0, int(math.floor(rect[1] * SCALE)) - pad)
    x1 = min(width, int(math.ceil(rect[2] * SCALE)) + pad)
    y1 = min(height, int(math.ceil(rect[3] * SCALE)) + pad)
    if x1 <= x0:
        x1 = min(width, x0 + 1)
    if y1 <= y0:
        y1 = min(height, y0 + 1)
    return x0, y0, x1, y1


def directed_color_mask(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    rgb = image.astype(np.float32)
    vector = 255.0 - rgb
    target = 255.0 - np.asarray(color, dtype=np.float32)
    target_sq = float(np.dot(target, target))
    alpha = (vector @ target) / target_sq
    residual = np.linalg.norm(vector - alpha[:, :, None] * target[None, None, :], axis=2)
    return (
        (np.max(np.abs(rgb - 255.0), axis=2) >= 20.0)
        & (alpha >= 0.02)
        & (alpha <= 1.12)
        & (residual <= 2.5)
    )


def load_target_row() -> dict[str, str]:
    with (ORIGIN_R6 / "after_pixel_measurements.csv").open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["ELEMENT_ID"] == TARGET_ID]
    if len(rows) != 1:
        raise RuntimeError(f"target row count is {len(rows)}, expected 1")
    return rows[0]


def measure_phase() -> None:
    if not SELECTION_FILE.is_file():
        raise RuntimeError("identity selection must be written before measurement")
    if MEASUREMENT_FILE.exists():
        raise RuntimeError("measurement already exists; candidate cannot be reselected or remeasured")
    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    if selection.get("selection_status") != "IDENTITY_PRESELECTED_BEFORE_METRICS":
        raise RuntimeError("no unique exact preselected peer")
    if not selection.get("pixel_metrics_deliberately_absent"):
        raise RuntimeError("selection file does not prove pre-metric identity freeze")
    peer = selection["selected_peer_identity"]
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm is required")
    page_no = int(peer["physical_page"])
    prefix = ROOT / f"official_r99_p{page_no:03d}_300dpi"
    page_png = prefix.with_suffix(".png")
    subprocess.run([
        pdftoppm, "-png", "-r", "300", "-f", str(page_no), "-l", str(page_no),
        "-singlefile", str(PDF), str(prefix),
    ], check=True)
    image = Image.open(page_png).convert("RGB")
    rgb = np.asarray(image)
    crop_box = rect_px(peer["glyph_bbox_pt"], image.width, image.height, pad=1)
    crop = rgb[crop_box[1]:crop_box[3], crop_box[0]:crop_box[2]]
    mask = directed_color_mask(crop, TARGET_COLOR)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        raise RuntimeError("preselected peer raw mask is empty")
    h_ink = int(ys.max() - ys.min() + 1)
    area = int(mask.sum())

    stem = f"peer_{peer['figure_major']}_{peer['figure_minor']}_u002e"
    native_path = ROOT / f"{stem}__native1x.png"
    nearest_path = ROOT / f"{stem}__nearest8x.png"
    mask_path = ROOT / f"{stem}__raw_mask.png"
    Image.fromarray(crop).save(native_path)
    Image.fromarray(crop).resize((crop.shape[1] * 8, crop.shape[0] * 8), Image.Resampling.NEAREST).save(nearest_path)
    Image.fromarray((mask * 255).astype(np.uint8)).save(mask_path)

    line_box = rect_px(peer["line_bbox_pt"], image.width, image.height, pad=12)
    context = rgb[line_box[1]:line_box[3], line_box[0]:line_box[2]]
    context_path = ROOT / f"{stem}__caption_context_300dpi.png"
    Image.fromarray(context).save(context_path)

    target = load_target_row()
    target_h = int(target["H_INK_PX"])
    target_area = int(target["INK_AREA_PX"])
    h_ratio = target_h / h_ink
    area_ratio = target_area / area
    in_range = LOWER <= h_ratio <= UPPER and LOWER <= area_ratio <= UPPER

    copied_target: dict[str, dict[str, Any]] = {}
    for field, rel in (
        ("RAW_MASK", target["RAW_MASK"]),
        ("NATIVE1X", target["NATIVE1X"]),
        ("NEAREST8X", target["NEAREST8X"]),
    ):
        source = ORIGIN_R6 / rel
        destination = ROOT / f"target_glyph_0072__{source.name.split('__', 1)[-1]}"
        shutil.copy2(source, destination)
        copied_target[field] = {
            "origin": str(source),
            "staged_copy": destination.name,
            "sha256": sha256(destination),
            "bytes": destination.stat().st_size,
        }

    result = {
        "selection_file": SELECTION_FILE.name,
        "selection_was_pre_metric": True,
        "selected_peer_identity": peer,
        "official_source": {
            "pdf": str(PDF),
            "sha256": selection["official_pdf_sha256"],
            "physical_page": page_no,
            "glyph_bbox_pt": peer["glyph_bbox_pt"],
        },
        "raster_rule": {
            "renderer": "Poppler pdftoppm",
            "dpi": 300,
            "contrast_threshold": 20,
            "paint_rgb": list(TARGET_COLOR),
            "mask": "directed white-to-paint compositing ray; no dilation or morphology",
        },
        "peer_artifacts": {
            "page_300dpi": page_png.name,
            "caption_context_300dpi": context_path.name,
            "raw_mask": mask_path.name,
            "native1x": native_path.name,
            "nearest8x": nearest_path.name,
        },
        "peer_metrics": {"H_INK_PX": h_ink, "INK_AREA_PX": area, "crop_box_px": list(crop_box)},
        "target": {
            "element_id": TARGET_ID,
            "H_INK_PX": target_h,
            "INK_AREA_PX": target_area,
            "copied_artifacts": copied_target,
        },
        "strict_comparison": {
            "ratio_direction": "target / preselected official peer",
            "allowed_interval": [LOWER, UPPER],
            "H_RATIO": round(h_ratio, 6),
            "AREA_RATIO": round(area_ratio, 6),
            "in_range": in_range,
            "verdict": "IN_RANGE" if in_range else "OUT_OF_RANGE",
        },
        "no_tex_invoked": True,
        "not_a_pass_seal": True,
    }
    write_json(MEASUREMENT_FILE, result)
    with (ROOT / "peer_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "TARGET_ID", "PEER_FIGURE", "PEER_PHYSICAL_PAGE", "TARGET_H", "PEER_H",
            "H_RATIO", "TARGET_AREA", "PEER_AREA", "AREA_RATIO", "LOWER", "UPPER", "VERDICT",
        ])
        writer.writeheader()
        writer.writerow({
            "TARGET_ID": TARGET_ID,
            "PEER_FIGURE": peer["figure_label"],
            "PEER_PHYSICAL_PAGE": page_no,
            "TARGET_H": target_h,
            "PEER_H": h_ink,
            "H_RATIO": round(h_ratio, 6),
            "TARGET_AREA": target_area,
            "PEER_AREA": area,
            "AREA_RATIO": round(area_ratio, 6),
            "LOWER": LOWER,
            "UPPER": UPPER,
            "VERDICT": "IN_RANGE" if in_range else "OUT_OF_RANGE",
        })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("select", "measure"))
    args = parser.parse_args()
    if args.phase == "select":
        select_phase()
    else:
        measure_phase()


if __name__ == "__main__":
    main()
