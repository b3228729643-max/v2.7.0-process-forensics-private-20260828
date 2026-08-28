#!/usr/bin/env python3
"""Resolve same-line padded-bbox ambiguity on the already rendered peer page.

This never selects a new glyph and never rerenders the PDF.  It applies the R6
bare-bbox containment / centre-distance ownership rule to the preselected
FIG 32.5 period and its line siblings on the existing 300 dpi page raster.
"""
from __future__ import annotations

import csv
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf")
ORIGIN_R6 = ROOT.parent / "STRICT_R6_SA2_REPAIR_R99_LOCAL_20260825"
SCALE = 300.0 / 72.0
COLOR = (31, 35, 40)
LOWER = 0.92
UPPER = 1.08


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rect_px(rect: list[float], width: int, height: int, pad: int = 0) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect[0] * SCALE)) - pad)
    y0 = max(0, int(math.floor(rect[1] * SCALE)) - pad)
    x1 = min(width, int(math.ceil(rect[2] * SCALE)) + pad)
    y1 = min(height, int(math.ceil(rect[3] * SCALE)) + pad)
    return x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)


def rgb_int_to_u8(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def directed_color_mask(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    rgb = image.astype(np.float32)
    vector = 255.0 - rgb
    target = 255.0 - np.asarray(color, dtype=np.float32)
    alpha = (vector @ target) / float(np.dot(target, target))
    residual = np.linalg.norm(vector - alpha[:, :, None] * target[None, None, :], axis=2)
    return (
        (np.max(np.abs(rgb - 255.0), axis=2) >= 20.0)
        & (alpha >= 0.02)
        & (alpha <= 1.12)
        & (residual <= 2.5)
    )


def encode(mask: np.ndarray, box: tuple[int, int, int, int], width: int) -> set[int]:
    ys, xs = np.nonzero(mask)
    return set(((ys + box[1]) * width + (xs + box[0])).astype(np.int64).tolist())


def component_count(mask: np.ndarray) -> int:
    seen = np.zeros(mask.shape, dtype=bool)
    count = 0
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        count += 1
        queue: deque[tuple[int, int]] = deque([(int(y), int(x))])
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
    return count


def main() -> None:
    output = ROOT / "peer_measurement_final_ownership.json"
    if output.exists():
        raise RuntimeError("ownership adjudication already exists; no repeat permitted")
    selection = json.loads((ROOT / "peer_selection_metadata.json").read_text(encoding="utf-8"))
    preliminary = json.loads((ROOT / "peer_measurement.json").read_text(encoding="utf-8"))
    peer = selection["selected_peer_identity"]
    if peer["figure_label"] != "图32.5" or int(peer["physical_page"]) != 652:
        raise RuntimeError("frozen peer identity changed")
    page_path = ROOT / preliminary["peer_artifacts"]["page_300dpi"]
    image = Image.open(page_path).convert("RGB")
    rgb = np.asarray(image)
    width, height = image.width, image.height

    doc = fitz.open(PDF)
    try:
        page = doc.load_page(int(peer["page_index_zero_based"]))
        raw = page.get_text("rawdict")
        block = raw["blocks"][int(peer["block_index"])]
        line = block["lines"][int(peer["line_index"])]
        siblings: list[dict[str, Any]] = []
        for span in line["spans"]:
            color = rgb_int_to_u8(int(span["color"]))
            for char_index, char in enumerate(span["chars"]):
                bbox = [float(v) for v in char["bbox"]]
                bare = rect_px(bbox, width, height, pad=0)
                crop = rect_px(bbox, width, height, pad=1)
                local = rgb[crop[1]:crop[3], crop[0]:crop[2]]
                pre = encode(directed_color_mask(local, color), crop, width)
                siblings.append({
                    "stable_id": f"{len(siblings):03d}_{ord(char['c']):04X}",
                    "char": char["c"],
                    "bbox_pt": bbox,
                    "bare": bare,
                    "crop": crop,
                    "pre": pre,
                    "font": span["font"],
                    "size_pt": round(float(span["size"]), 4),
                    "color": color,
                })
    finally:
        doc.close()

    target_candidates = [
        row for row in siblings
        if row["char"] == "."
        and row["font"].split("+", 1)[-1] == peer["font"]
        and all(abs(float(a) - float(b)) <= 1e-5 for a, b in zip(row["bbox_pt"], peer["glyph_bbox_pt"]))
    ]
    if len(target_candidates) != 1:
        raise RuntimeError(f"target sibling count={len(target_candidates)}")
    target = target_candidates[0]
    final: set[int] = set()
    ownership_rows: list[dict[str, Any]] = []
    for pixel in sorted(target["pre"]):
        y, x = divmod(pixel, width)
        candidates = [row for row in siblings if pixel in row["pre"]]
        contained = [
            row for row in candidates
            if row["bare"][0] <= x < row["bare"][2] and row["bare"][1] <= y < row["bare"][3]
        ]
        chosen = min(
            contained or candidates,
            key=lambda row: (
                (x - (row["bare"][0] + row["bare"][2]) / 2.0) ** 2
                + (y - (row["bare"][1] + row["bare"][3]) / 2.0) ** 2,
                row["stable_id"],
            ),
        )
        if chosen is target:
            final.add(pixel)
        elif len(candidates) > 1:
            ownership_rows.append({
                "pixel_x": x,
                "pixel_y": y,
                "removed_from_period": True,
                "assigned_to_char": chosen["char"],
                "assigned_to_stable_id": chosen["stable_id"],
                "reason": "same-line padded-bbox ambiguity resolved by bare-bbox containment then centre distance",
            })

    crop_box = tuple(target["crop"])
    final_mask = np.zeros((crop_box[3] - crop_box[1], crop_box[2] - crop_box[0]), dtype=bool)
    for pixel in final:
        y, x = divmod(pixel, width)
        final_mask[y - crop_box[1], x - crop_box[0]] = True
    ys, xs = np.nonzero(final_mask)
    if len(ys) == 0:
        raise RuntimeError("owned period mask is empty")
    h_ink = int(ys.max() - ys.min() + 1)
    area = int(final_mask.sum())
    components = component_count(final_mask)
    mask_path = ROOT / "peer_32_5_u002e__final_owned_raw_mask.png"
    mask8_path = ROOT / "peer_32_5_u002e__final_owned_raw_mask_8x.png"
    Image.fromarray((final_mask * 255).astype(np.uint8)).save(mask_path)
    Image.fromarray((final_mask * 255).astype(np.uint8)).resize(
        (final_mask.shape[1] * 8, final_mask.shape[0] * 8), Image.Resampling.NEAREST
    ).save(mask8_path)

    target_h = int(preliminary["target"]["H_INK_PX"])
    target_area = int(preliminary["target"]["INK_AREA_PX"])
    h_ratio = target_h / h_ink
    area_ratio = target_area / area
    in_range = LOWER <= h_ratio <= UPPER and LOWER <= area_ratio <= UPPER
    payload = {
        "frozen_peer": peer,
        "same_preselected_peer": True,
        "same_existing_page_raster": page_path.name,
        "pdf_was_not_rerendered": True,
        "ownership_rule": "R6 rule: bare-bbox containment, then centre-distance, then stable ID",
        "line_text": "".join(row["char"] for row in siblings),
        "line_sibling_count": len(siblings),
        "pre_ownership_metrics": preliminary["peer_metrics"],
        "removed_foreign_pixel_count": len(target["pre"] - final),
        "removed_foreign_pixels": ownership_rows,
        "final_owned_mask": mask_path.name,
        "final_owned_mask_8x": mask8_path.name,
        "final_mask_component_count_8_connected": components,
        "final_mask_complete_and_pure": components == 1 and len(ownership_rows) == len(target["pre"] - final),
        "peer_metrics": {"H_INK_PX": h_ink, "INK_AREA_PX": area},
        "target_metrics": {"H_INK_PX": target_h, "INK_AREA_PX": target_area},
        "strict_comparison": {
            "ratio_direction": "target / preselected official peer after deterministic glyph ownership",
            "allowed_interval": [LOWER, UPPER],
            "H_RATIO": round(h_ratio, 6),
            "AREA_RATIO": round(area_ratio, 6),
            "in_range": in_range,
            "verdict": "IN_RANGE" if in_range else "OUT_OF_RANGE",
        },
        "no_new_candidate": True,
        "no_tex_invoked": True,
        "not_a_pass_seal": True,
    }
    write_json(output, payload)
    with (ROOT / "peer_comparison_final_ownership.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "TARGET_ID", "PEER_FIGURE", "PEER_PHYSICAL_PAGE", "TARGET_H", "PEER_H", "H_RATIO",
            "TARGET_AREA", "PEER_AREA", "AREA_RATIO", "REMOVED_FOREIGN_PX", "MASK_COMPONENTS",
            "LOWER", "UPPER", "VERDICT",
        ])
        writer.writeheader()
        writer.writerow({
            "TARGET_ID": "GLYPH_0072",
            "PEER_FIGURE": peer["figure_label"],
            "PEER_PHYSICAL_PAGE": peer["physical_page"],
            "TARGET_H": target_h,
            "PEER_H": h_ink,
            "H_RATIO": round(h_ratio, 6),
            "TARGET_AREA": target_area,
            "PEER_AREA": area,
            "AREA_RATIO": round(area_ratio, 6),
            "REMOVED_FOREIGN_PX": len(target["pre"] - final),
            "MASK_COMPONENTS": components,
            "LOWER": LOWER,
            "UPPER": UPPER,
            "VERDICT": "IN_RANGE" if in_range else "OUT_OF_RANGE",
        })


if __name__ == "__main__":
    main()
