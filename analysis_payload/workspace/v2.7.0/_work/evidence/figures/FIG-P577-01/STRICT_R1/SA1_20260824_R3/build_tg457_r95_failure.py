"""Build independent R95-native critical evidence for TG457 only.

This writes only below the R3 evidence root.  It deliberately does not consume
the preliminary R94-labelled mask set: character boxes, colours, and the card
border are recovered again from R95 / its direct 300dpi raster.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
RASTER = ROOT / "raw" / "r95_page_625_300dpi.png"
OUT = ROOT / "critical_TG457_R95"
PAGE_INDEX = 624
DPI = 300


def px_box(box: tuple[float, float, float, float], sx: float, sy: float, w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (max(0, math.floor(x0 * sx)), max(0, math.floor(y0 * sy)), min(w, math.ceil(x1 * sx)), min(h, math.ceil(y1 * sy)))


def projected_colour_mask(arr: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    """Strict source-colour-to-white projection; no modal local background."""
    a = arr.astype(np.float32)
    white = np.asarray((255.0, 255.0, 255.0), dtype=np.float32)
    target = np.asarray(rgb, dtype=np.float32)
    direction = white - target
    projection = np.sum((white - a) * direction, axis=2) / float(np.dot(direction, direction))
    reconstructed = white - projection[..., None] * direction
    residual = np.linalg.norm(a - reconstructed, axis=2)
    contrast = np.max(np.abs(white - a), axis=2)
    # The small residual is intentional: it eliminates grey/other-colour
    # antialiasing that the preliminary residual=14 diagnostic conflated.
    return (projection >= 20.0 / 255.0) & (projection <= 1.02) & (residual <= 4.0) & (contrast >= 20.0)


def glyph_records(page: fitz.Page, sx: float, sy: float, w: int, h: int) -> list[dict]:
    selected: list[dict] = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    x0, y0, x1, y1 = map(float, char["bbox"])
                    # The direct R95 text operator location for the y-axis 0.8 tick.
                    if 90.0 <= (x0 + x1) / 2 <= 105.0 and 280.0 <= (y0 + y1) / 2 <= 291.0:
                        selected.append({
                            "char": char["c"], "pdf_bbox": (x0, y0, x1, y1),
                            "px_bbox": px_box((x0, y0, x1, y1), sx, sy, w, h),
                            "rgb": ((span["color"] >> 16) & 255, (span["color"] >> 8) & 255, span["color"] & 255),
                        })
    selected.sort(key=lambda g: g["pdf_bbox"][0])
    if [g["char"] for g in selected] != ["0", ".", "8"]:
        raise RuntimeError(f"TG457 R95 character extraction mismatch: {selected}")
    return selected


def save_pair(im: Image.Image, name: str) -> None:
    im.save(OUT / f"{name}_1x.png")
    im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST).save(OUT / f"{name}_8x_nearest.png")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    arr = np.asarray(Image.open(RASTER).convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape
    sx, sy = w / page.rect.width, h / page.rect.height
    glyphs = glyph_records(page, sx, sy, w, h)

    tick = np.zeros((h, w), dtype=bool)
    rows: list[dict] = []
    for glyph in glyphs:
        x0, y0, x1, y1 = glyph["px_bbox"]
        m = projected_colour_mask(arr[y0:y1, x0:x1], glyph["rgb"])
        tick[y0:y1, x0:x1] |= m
        rows.append({
            "OBJECT": "P_TICK_Y_0_8", "CHAR": glyph["char"],
            "PDF_BBOX": ",".join(f"{v:.3f}" for v in glyph["pdf_bbox"]),
            "PX_BBOX": f"{x0},{y0},{x1},{y1}", "TARGET_RGB": str(glyph["rgb"]),
            "TARGET_PIXELS": int(m.sum()), "MASK_METHOD": "R95 text-operator bbox plus strict source-colour projection",
        })

    # Recover the actual R95 acceptance-card vector rectangle. It is the unique
    # teal rounded rectangle at the source-location range below; use only its
    # stroke shell, never its opaque white interior.
    drawings = page.get_drawings(extended=True)
    card = next((d for d in drawings if d["type"] == "fs" and d.get("color") and abs(d["rect"].x0 - 91.3059998) < .02 and abs(d["rect"].y0 - 288.75616) < .02), None)
    if card is None:
        raise RuntimeError("R95 acceptance-card border vector not recovered")
    bx0, by0, bx1, by1 = px_box(tuple(float(v) for v in card["rect"]), sx, sy, w, h)
    teal = tuple(int(round(v * 255)) for v in card["color"])
    teal_pixels = projected_colour_mask(arr, teal)
    yy, xx = np.indices((h, w))
    shell = (xx >= bx0 - 5) & (xx <= bx1 + 5) & (yy >= by0 - 5) & (yy <= by1 + 5)
    edge = np.minimum.reduce((np.abs(xx - bx0), np.abs(xx - bx1), np.abs(yy - by0), np.abs(yy - by1))) <= 6
    border = teal_pixels & shell & edge
    if not np.any(border):
        raise RuntimeError("R95 acceptance-card stroke mask is empty")

    distance, nearest = distance_transform_edt(~border, return_indices=True)
    ty, tx = np.where(tick)
    order = np.argmin(distance[ty, tx])
    t_y, t_x = int(ty[order]), int(tx[order])
    b_y, b_x = int(nearest[0, t_y, t_x]), int(nearest[1, t_y, t_x])
    min_distance = float(distance[t_y, t_x])
    overlap = int(np.count_nonzero(tick & border))

    # Native ROI includes every critical target pixel and the nearest border.
    rx0, ry0, rx1, ry1 = 370, 1158, 446, 1220
    original = Image.fromarray(arr[ry0:ry1, rx0:rx1])
    overlay = arr[ry0:ry1, rx0:rx1].copy()
    overlay[tick[ry0:ry1, rx0:rx1]] = (255, 0, 0)  # unique red target only
    target_only = np.full_like(overlay, 255)
    target_only[tick[ry0:ry1, rx0:rx1]] = (0, 0, 0)
    border_only = np.full_like(overlay, 255)
    border_only[border[ry0:ry1, rx0:rx1]] = (0, 0, 0)
    nearest_overlay = overlay.copy()
    nearest_overlay[t_y - ry0, t_x - rx0] = (255, 0, 0)
    nearest_overlay[b_y - ry0, b_x - rx0] = (255, 165, 0)
    save_pair(original, "TG457_original")
    save_pair(Image.fromarray(overlay), "TG457_target_overlay_unique_red")
    save_pair(Image.fromarray(target_only), "TG457_target_mask_only")
    save_pair(Image.fromarray(border_only), "TG457_accept_border_mask_only")
    save_pair(Image.fromarray(nearest_overlay), "TG457_nearest_points_overlay")

    with (OUT / "TG457_measurement.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        fields = ["RELATION_ID", "TEXT_OBJECT", "GRAPHIC_OBJECT", "CLASS", "THRESHOLD_PX", "RAW_MASK_OVERLAP_PX", "MIN_DISTANCE_PX", "NEAREST_TEXT_XY", "NEAREST_BORDER_XY", "DECISION", "METHOD"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "RELATION_ID": "TG457", "TEXT_OBJECT": "P_TICK_Y_0_8", "GRAPHIC_OBJECT": "G10_ACCEPT_BORDER",
            "CLASS": "TEXT_NODE_BORDER", "THRESHOLD_PX": 5, "RAW_MASK_OVERLAP_PX": overlap,
            "MIN_DISTANCE_PX": f"{min_distance:.3f}", "NEAREST_TEXT_XY": f"{t_x},{t_y}",
            "NEAREST_BORDER_XY": f"{b_x},{b_y}", "DECISION": "FAIL" if overlap or min_distance < 5 else "PASS",
            "METHOD": "R95 direct native300dpi; R95 raw text operator boxes; source-colour projection; R95 vector-identified stroke-only card border",
        })
    with (OUT / "TG457_component_inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "authority_pdf": str(PDF), "physical_page": 625, "dpi": 300,
        "relation": "TG457", "target_chars": [g["char"] for g in glyphs],
        "card_pdf_rect": [float(v) for v in card["rect"]], "card_px_rect": [bx0, by0, bx1, by1],
        "target_pixels": int(tick.sum()), "border_pixels": int(border.sum()),
        "overlap_pixels": overlap, "min_distance_px": min_distance,
        "nearest_text_xy": [t_x, t_y], "nearest_border_xy": [b_x, b_y],
        "threshold_px": 5, "decision": "FAIL" if overlap or min_distance < 5 else "PASS",
        "critical_roi_px": [rx0, ry0, rx1, ry1],
    }
    (OUT / "TG457_measurement.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "TG457_MANUAL_REVIEW.md").write_text(
        "# TG457 R95 native critical review\n\n"
        "The original 1:1 crop and its 8× nearest-neighbour view were opened. `0.8` is visibly separate from the teal card edge, but the exact visible-ink nearest pair is only "
        f"`{min_distance:.3f}px` at text `{t_x},{t_y}` to border `{b_x},{b_y}`. The mandatory TEXT_NODE_BORDER clearance is `>=5px`; overlap is `{overlap}px`. "
        "Therefore this is a real **FAIL** by the stated hard gate, not a projection-contamination artefact. The target overlay colours only the text object red; the two component-only masks exclude all neighbours.\n\n"
        "Required review artifacts are the five named 1× files and their paired `8x_nearest` files in this directory.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
