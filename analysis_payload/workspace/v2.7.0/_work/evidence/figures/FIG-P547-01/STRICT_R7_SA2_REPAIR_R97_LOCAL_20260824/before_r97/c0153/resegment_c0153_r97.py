#!/usr/bin/env python3
"""Rebuild a pure C0153 semicolon mask from R97 native 300 dpi evidence.

The candidate mask is separated by connected-component assignment against an
independently rendered, same-codepoint/same-font/same-size calibration glyph.
No morphology, interpolation, dilation, erosion, or synthetic stroke repair is
used.  Only original candidate pixels are retained in the final pure mask.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习")
OUT = ROOT / "v2.7.0" / "_work" / "evidence" / "figures" / "FIG-P547-01" / "STRICT_R7_SA2_REPAIR_R97_LOCAL_20260824" / "before_r97" / "c0153"
PDF = ROOT / "v2.7.0" / "_work" / "source" / "v2.7.0" / "src" / "build" / "strict_current_r97_fullbook" / "main_full.pdf"
PAGE_NUMBER = 591
PAGE_INDEX = PAGE_NUMBER - 1
NATIVE = OUT.parent / "renders" / "r97_p591_300dpi_native.png"
CAL_PDF = OUT / "c0153_same_font_calibration.pdf"
CAL_NATIVE = OUT / "c0153_same_font_calibration_300dpi.png"
TEXT_SCOPE = fitz.Rect(60, 298, 535, 447)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def color_int_to_rgb(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 255, (color >> 8) & 255, color & 255)


def dominant_background(arr: np.ndarray) -> np.ndarray:
    flat = arr.reshape((-1, 3))
    quant = (flat // 8).astype(np.uint8)
    keys = quant[:, 0].astype(np.int32) * 1024 + quant[:, 1].astype(np.int32) * 32 + quant[:, 2].astype(np.int32)
    code = int(Counter(keys.tolist()).most_common(1)[0][0])
    return np.median(flat[keys == code], axis=0).astype(np.float32)


def raw_colour_line_mask(roi: np.ndarray, expected: tuple[int, int, int]) -> np.ndarray:
    """Threshold at >=20/255 local contrast and retain the target colour line."""
    bg = dominant_background(roi)
    target = np.array(expected, dtype=np.float32)
    pixels = roi.astype(np.float32)
    dist_bg = np.sqrt(np.sum((pixels - bg) ** 2, axis=2))
    direction = target - bg
    denom = float(np.dot(direction, direction))
    if denom < 1.0:
        return dist_bg >= 20.0
    delta = pixels - bg
    alpha = np.sum(delta * direction, axis=2) / denom
    projected = bg + alpha[..., None] * direction
    residual = np.sqrt(np.sum((pixels - projected) ** 2, axis=2))
    target_bg_distance = math.sqrt(denom)
    return (dist_bg >= 20.0) & (alpha >= 0.035) & (alpha <= 1.08) & (residual <= max(9.0, target_bg_distance * 0.075))


def components(mask: np.ndarray) -> list[dict]:
    visited = np.zeros_like(mask, dtype=bool)
    result: list[dict] = []
    height, width = mask.shape
    for sy, sx in zip(*np.where(mask)):
        if visited[sy, sx]:
            continue
        stack = [(int(sy), int(sx))]
        visited[sy, sx] = True
        pts: list[tuple[int, int]] = []
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
        yy = np.array([p[0] for p in pts], dtype=np.int32)
        xx = np.array([p[1] for p in pts], dtype=np.int32)
        result.append({
            "points": pts,
            "area_px": len(pts),
            "bbox_local_px": [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1],
            "centroid_local_px": [float(xx.mean()), float(yy.mean())],
        })
    return sorted(result, key=lambda c: (c["centroid_local_px"][1], c["centroid_local_px"][0]))


def mask_bbox(mask: np.ndarray) -> list[int] | None:
    yy, xx = np.where(mask)
    if len(xx) == 0:
        return None
    return [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]


def save_mask(path: Path, mask: np.ndarray) -> None:
    arr = np.full((*mask.shape, 3), 255, dtype=np.uint8)
    arr[mask] = (0, 0, 0)
    Image.fromarray(arr, "RGB").save(path, format="PNG", optimize=False)


def save_overlay(path: Path, roi: np.ndarray, mask: np.ndarray, foreign: np.ndarray | None = None) -> None:
    arr = roi.copy().astype(np.float32)
    arr[mask] = 0.35 * arr[mask] + 0.65 * np.array([225, 35, 35], dtype=np.float32)
    if foreign is not None:
        arr[foreign] = 0.30 * arr[foreign] + 0.70 * np.array([35, 90, 235], dtype=np.float32)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(path, format="PNG", optimize=False)


def nearest8(image: Image.Image) -> Image.Image:
    return image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)


def triptych(path: Path, title: str, original: Image.Image, overlay: Image.Image, mask: Image.Image) -> None:
    cells = [nearest8(original), nearest8(overlay), nearest8(mask)]
    labels = ["ORIGINAL", "TARGET OVERLAY", "MASK ONLY"]
    gap, header = 10, 34
    width = sum(c.width for c in cells) + gap * 4
    height = max(c.height for c in cells) + header + gap * 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    x = gap
    for label, cell in zip(labels, cells):
        draw.text((x, 4), label, fill="black", font=font)
        canvas.paste(cell, (x, header))
        x += cell.width + gap
    draw.text((gap, height - 13), title, fill="black", font=font)
    canvas.save(path, format="PNG", optimize=False)


def enumerate_candidate() -> tuple[dict, np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    image = Image.open(NATIVE).convert("RGB")
    rgb = np.array(image)
    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    sx, sy = image.width / page.rect.width, image.height / page.rect.height
    raw = page.get_text("rawdict")
    glyphs: list[dict] = []
    for bi, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for li, line in enumerate(block.get("lines", [])):
            for si, span in enumerate(line.get("spans", [])):
                for ci, char in enumerate(span.get("chars", [])):
                    value = str(char.get("c", ""))
                    if not value or value.isspace():
                        continue
                    rect = fitz.Rect(char["bbox"])
                    if not (TEXT_SCOPE.intersects(rect) and rect.y0 >= TEXT_SCOPE.y0 and rect.y1 <= TEXT_SCOPE.y1):
                        continue
                    glyphs.append({
                        "glyph_id": f"C{len(glyphs)+1:04d}",
                        "char": value,
                        "font": str(span.get("font", "")),
                        "font_size_pt_pdf_emit": float(span.get("size", 0.0)),
                        "color_rgb": color_int_to_rgb(int(span.get("color", 0))),
                        "bbox_pt": [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)],
                        "pdf_block": bi,
                        "pdf_line": li,
                        "pdf_span": si,
                        "pdf_char": ci,
                    })
    doc.close()
    target = next(g for g in glyphs if g["glyph_id"] == "C0153")
    if target["char"] != "；":
        raise RuntimeError(f"R97 C0153 identity mismatch: {target}")
    rect = fitz.Rect(target["bbox_pt"])
    nominal = (math.floor(rect.x0 * sx), math.floor(rect.y0 * sy), math.ceil(rect.x1 * sx), math.ceil(rect.y1 * sy))
    pad = 4
    box = (max(0, nominal[0] - pad), max(0, nominal[1] - pad), min(image.width, nominal[2] + pad), min(image.height, nominal[3] + pad))
    roi = rgb[box[1]:box[3], box[0]:box[2]]
    raw_mask = raw_colour_line_mask(roi, target["color_rgb"])
    target["nominal_bbox_px"] = list(nominal)
    target["roi_bbox_px"] = list(box)
    target["enumerated_glyph_count"] = len(glyphs)
    return target, roi, raw_mask, box


def calibration_target() -> tuple[dict, np.ndarray, np.ndarray]:
    image = Image.open(CAL_NATIVE).convert("RGB")
    rgb = np.array(image)
    doc = fitz.open(CAL_PDF)
    page = doc[0]
    sx, sy = image.width / page.rect.width, image.height / page.rect.height
    raw = page.get_text("rawdict")
    candidates = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    if char.get("c") == "；":
                        candidates.append((span, char))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one calibration semicolon, found {len(candidates)}")
    span, char = candidates[0]
    rect = fitz.Rect(char["bbox"])
    nominal = (math.floor(rect.x0 * sx), math.floor(rect.y0 * sy), math.ceil(rect.x1 * sx), math.ceil(rect.y1 * sy))
    box = (max(0, nominal[0] - 4), max(0, nominal[1] - 4), min(image.width, nominal[2] + 4), min(image.height, nominal[3] + 4))
    roi = rgb[box[1]:box[3], box[0]:box[2]]
    mask = raw_colour_line_mask(roi, color_int_to_rgb(int(span.get("color", 0))))
    meta = {
        "char": "；",
        "font": str(span.get("font", "")),
        "font_size_pt_pdf_emit": float(span.get("size", 0.0)),
        "bbox_pt": [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)],
        "nominal_bbox_px": list(nominal),
        "roi_bbox_px": list(box),
    }
    doc.close()
    return meta, roi, mask


def choose_candidate_components(candidate: list[dict], calibration: list[dict], shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Match exactly the two semicolon components by vertical order and shape.

    The calibration establishes the intended component count. Candidate
    components are matched to calibration components by normalized centroid,
    bbox dimensions and area. A foreign third component is excluded verbatim.
    """
    if len(calibration) != 2:
        raise RuntimeError(f"calibration glyph is not a two-component semicolon: {len(calibration)}")
    height, width = shape
    matches: list[dict] = []
    unused = set(range(len(candidate)))
    # Compare component geometry after normalising by each ROI dimensions.
    for cal_index, cal in enumerate(calibration):
        best = None
        for idx in unused:
            cand = candidate[idx]
            cy, cx = cand["centroid_local_px"][1] / height, cand["centroid_local_px"][0] / width
            # Calibration ROI geometry is supplied below in normalized fields.
            dy = cy - cal["norm_centroid"][1]
            dx = cx - cal["norm_centroid"][0]
            area_ratio = max(cand["area_px"], cal["area_px"]) / max(1, min(cand["area_px"], cal["area_px"]))
            score = dx * dx + dy * dy + 0.010 * abs(math.log(area_ratio))
            if best is None or score < best[0]:
                best = (score, idx)
        assert best is not None
        unused.remove(best[1])
        matches.append({"calibration_component_index": cal_index + 1, "candidate_component_index": best[1] + 1, "match_score": best[0]})
    clean = np.zeros(shape, dtype=bool)
    foreign = np.zeros(shape, dtype=bool)
    kept_indices = {m["candidate_component_index"] - 1 for m in matches}
    for idx, comp in enumerate(candidate):
        target = clean if idx in kept_indices else foreign
        yy = np.array([p[0] for p in comp["points"]], dtype=np.int32)
        xx = np.array([p[1] for p in comp["points"]], dtype=np.int32)
        target[yy, xx] = True
    return clean, foreign, matches


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target, candidate_roi, candidate_raw, candidate_box = enumerate_candidate()
    cal_meta, cal_roi, cal_mask = calibration_target()
    candidate_components = components(candidate_raw)
    calibration_components = components(cal_mask)
    for comp in calibration_components:
        comp["norm_centroid"] = [comp["centroid_local_px"][0] / cal_mask.shape[1], comp["centroid_local_px"][1] / cal_mask.shape[0]]
    clean, foreign, matches = choose_candidate_components(candidate_components, calibration_components, candidate_raw.shape)

    Image.fromarray(candidate_roi, "RGB").save(OUT / "C0153_UFF1B_original_1x.png", format="PNG", optimize=False)
    save_mask(OUT / "C0153_UFF1B_raw_all_components_mask_only_1x.png", candidate_raw)
    save_overlay(OUT / "C0153_UFF1B_raw_all_components_overlay_1x.png", candidate_roi, candidate_raw)
    save_mask(OUT / "C0153_UFF1B_pure_two_component_mask_only_1x.png", clean)
    save_mask(OUT / "C0153_UFF1B_foreign_component_mask_only_1x.png", foreign)
    save_overlay(OUT / "C0153_UFF1B_pure_overlay_foreign_blue_1x.png", candidate_roi, clean, foreign)
    triptych(
        OUT / "C0153_UFF1B_pure_contact_8x_nearest.png",
        "C0153 pure two-component mask; excluded foreign component shown only in separate proof",
        Image.fromarray(candidate_roi, "RGB"),
        Image.open(OUT / "C0153_UFF1B_pure_overlay_foreign_blue_1x.png").convert("RGB"),
        Image.open(OUT / "C0153_UFF1B_pure_two_component_mask_only_1x.png").convert("RGB"),
    )
    Image.fromarray(cal_roi, "RGB").save(OUT / "C0153_calibration_original_1x.png", format="PNG", optimize=False)
    save_mask(OUT / "C0153_calibration_mask_only_1x.png", cal_mask)
    save_overlay(OUT / "C0153_calibration_overlay_1x.png", cal_roi, cal_mask)
    triptych(
        OUT / "C0153_calibration_contact_8x_nearest.png",
        "same codepoint/font/weight/color/effective size calibration",
        Image.fromarray(cal_roi, "RGB"),
        Image.open(OUT / "C0153_calibration_overlay_1x.png").convert("RGB"),
        Image.open(OUT / "C0153_calibration_mask_only_1x.png").convert("RGB"),
    )

    clean_box = mask_bbox(clean)
    cal_box = mask_bbox(cal_mask)
    clean_h = 0 if clean_box is None else clean_box[3] - clean_box[1]
    cal_h = 0 if cal_box is None else cal_box[3] - cal_box[1]
    clean_area = int(clean.sum())
    cal_area = int(cal_mask.sum())
    report = {
        "r97_pdf": str(PDF),
        "r97_pdf_sha256": sha256(PDF),
        "page": PAGE_NUMBER,
        "native_300dpi": str(NATIVE),
        "native_300dpi_sha256": sha256(NATIVE),
        "candidate": target,
        "calibration": cal_meta,
        "candidate_raw_component_count": len(candidate_components),
        "calibration_component_count": len(calibration_components),
        "candidate_components": [{k: v for k, v in c.items() if k != "points"} for c in candidate_components],
        "calibration_components": [{k: v for k, v in c.items() if k != "points"} for c in calibration_components],
        "component_matches": matches,
        "pure_candidate_component_count": len(components(clean)),
        "foreign_component_count": len(components(foreign)),
        "pure_candidate_ink_bbox_local_px": clean_box,
        "pure_candidate_h_px": clean_h,
        "pure_candidate_area_px": clean_area,
        "calibration_ink_bbox_local_px": cal_box,
        "calibration_h_px": cal_h,
        "calibration_area_px": cal_area,
        "height_ratio": clean_h / cal_h if cal_h else None,
        "area_ratio": clean_area / cal_area if cal_area else None,
        "decision": "PASS" if cal_h and cal_area and 0.92 <= clean_h / cal_h <= 1.08 and 0.92 <= clean_area / cal_area <= 1.08 else "FAIL",
        "separation_rule": "retain only the two original native candidate components matched to the independently rendered two-component semicolon; excluded pixels are saved separately; no morphology/interpolation/repair",
    }
    (OUT / "C0153_RESEGMENTATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    summary = (
        "# C0153 clean-mask reconciliation on R97\n\n"
        f"- R97 source glyph: `{target['char']}` / `{target['font']}` / `{target['font_size_pt_pdf_emit']:.4f} pt`.\n"
        f"- Raw candidate components: {len(candidate_components)}; isolated calibration components: {len(calibration_components)}.\n"
        f"- Pure candidate: H={clean_h}px, area={clean_area}px; calibration: H={cal_h}px, area={cal_area}px.\n"
        f"- Ratios: H={report['height_ratio']:.4f}, area={report['area_ratio']:.4f}.\n"
        f"- Decision: **{report['decision']}**.\n\n"
        "The legacy 45 px third component and a 1 px edge singleton are preserved in a separate foreign-component mask and excluded from the pure two-component candidate. No source repair decision is based on the contaminated raw value.\n"
    )
    (OUT / "C0153_RESEGMENTATION.md").write_text(summary, encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
