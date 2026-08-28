from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label as component_label


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P654-01\STRICT_R1_SA1_REQUAL_R98_20260824")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
REFS = ROOT / "references"
CRITICAL = ROOT / "critical"
REFS.mkdir(exist_ok=True)

SCALE = 300 / 72
SELECTIONS = (
    {
        "target_id": "G0063", "char": ",", "candidate_id": "R00018",
        "physical_page": 789, "printed_label": "776",
        "font": "STIXTwoMath-Regular", "trace_size_bp": 11.75592041,
        "declared_pt": 11.8, "effective_pt": 11.8, "color_rgb": (31, 35, 40),
        "raw_bbox": (373.0627746582031, 482.7980041503906, 375.9429626464844, 494.5539245605469),
        "role": "FORMULA_BLOCK inside a figure node; independent official-page mathematical argument separator",
        "target_h": 13, "target_area": 61,
    },
    {
        "target_id": "G0083", "char": "、", "candidate_id": "R00001",
        "physical_page": 742, "printed_label": "729",
        "font": "NotoSerifSC-ExtraLight", "trace_size_bp": 9.56414032,
        "declared_pt": 9.6, "effective_pt": 9.6, "color_rgb": (31, 35, 40),
        "raw_bbox": (131.2738494873047, 197.0386962890625, 140.83798217773438, 207.28189086914062),
        "role": "NODE_LABEL inside an independent official flowchart node; CJK list separator",
        "target_h": 10, "target_area": 41,
    },
)


def rgb_from_float(value) -> tuple[int, int, int]:
    return tuple(int(round(float(v) * 255)) for v in value[:3])


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise RuntimeError("empty reference mask")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def nearest8(image: Image.Image) -> Image.Image:
    return image.resize((image.width * 8, image.height * 8), Image.Resampling.NEAREST)


def labelled_strip(title: str, images: list[tuple[str, Image.Image]], scale: int) -> Image.Image:
    title_h = 20 * scale
    label_h = 14 * scale
    width = sum(im.width for _, im in images)
    height = title_h + label_h + max(im.height for _, im in images)
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)
    draw.text((2 * scale, 2 * scale), title, fill="black")
    x = 0
    for label, im in images:
        draw.text((x + 2 * scale, title_h), label, fill="black")
        card.paste(im.convert("RGB"), (x, title_h + label_h))
        x += im.width
    return card


doc = fitz.open(PDF)
result_rows: list[dict[str, object]] = []
for spec in SELECTIONS:
    page = doc[spec["physical_page"] - 1]
    if page.get_label() != spec["printed_label"]:
        raise RuntimeError(f"page-label mismatch for {spec['candidate_id']}")
    if spec["physical_page"] == 702:
        raise RuntimeError("target page cannot be a reference")

    raw_rect = fitz.Rect(spec["raw_bbox"])
    candidates = []
    for span in page.get_texttrace():
        if span.get("font") != spec["font"]:
            continue
        if abs(float(span.get("size", 0)) - float(spec["trace_size_bp"])) > 0.0001:
            continue
        if rgb_from_float(span.get("color", (0, 0, 0))) != spec["color_rgb"]:
            continue
        for cp, _, _, bbox in span.get("chars", []):
            if chr(cp) != spec["char"]:
                continue
            rect = fitz.Rect(bbox)
            distance = abs(rect.x0 - raw_rect.x0) + abs(rect.y0 - raw_rect.y0)
            candidates.append((distance, rect, int(span.get("seqno", -1))))
    if not candidates:
        raise RuntimeError(f"no texttrace match for {spec['candidate_id']}")
    _, rect, seqno = min(candidates, key=lambda item: item[0])

    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), colorspace=fitz.csRGB, alpha=False)
    full = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3].copy()
    px0 = max(0, math.floor(rect.x0 * SCALE) - 6)
    py0 = max(0, math.floor(rect.y0 * SCALE) - 6)
    px1 = min(pix.width, math.ceil(rect.x1 * SCALE) + 6)
    py1 = min(pix.height, math.ceil(rect.y1 * SCALE) + 6)
    roi = full[py0:py1, px0:px1].copy()

    lx0 = max(0, math.floor(rect.x0 * SCALE) - px0 - 1)
    ly0 = max(0, math.floor(rect.y0 * SCALE) - py0 - 1)
    lx1 = min(roi.shape[1], math.ceil(rect.x1 * SCALE) - px0 + 1)
    ly1 = min(roi.shape[0], math.ceil(rect.y1 * SCALE) - py0 + 1)
    geom = np.zeros(roi.shape[:2], dtype=bool)
    geom[ly0:ly1, lx0:lx1] = True

    border = np.ones(roi.shape[:2], dtype=bool)
    border[max(0, ly0 - 1):min(roi.shape[0], ly1 + 1), max(0, lx0 - 1):min(roi.shape[1], lx1 + 1)] = False
    color_counts = Counter(map(tuple, roi[border].reshape(-1, 3)))
    background_rgb = np.array(color_counts.most_common(1)[0][0], dtype=np.int16)
    foreground = np.max(np.abs(roi.astype(np.int16) - background_rgb), axis=2) >= 20
    provisional = foreground & geom
    labels, count = component_label(provisional, structure=np.ones((3, 3), dtype=np.uint8))
    if count < 1:
        raise RuntimeError(f"no component for {spec['candidate_id']}")
    components = []
    for component in range(1, count + 1):
        cmask = labels == component
        components.append((int(cmask.sum()), component))
    # Neighboring antialias fringes can enter the logical bbox.  Both selected punctuation
    # codepoints have one reader-visible connected component in this render stack, so the
    # dominant whole component is the unique owner; smaller disjoint intrusions are excluded.
    dominant_area, dominant_component = max(components)
    if dominant_area < 2:
        raise RuntimeError(f"only single-pixel noise for {spec['candidate_id']}")
    mask = labels == dominant_component
    bbox = tight_bbox(mask)
    h = bbox[3] - bbox[1]
    area = int(mask.sum())
    if area == 0:
        raise RuntimeError(f"empty mask for {spec['candidate_id']}")

    original = Image.fromarray(roi)
    overlay_arr = roi.copy()
    overlay_arr[mask] = np.array([255, 0, 0], dtype=np.uint8)
    overlay = Image.fromarray(overlay_arr)
    mask_only = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L")
    original.save(REFS / f"{spec['candidate_id']}_original_1x.png")
    overlay.save(REFS / f"{spec['candidate_id']}_overlay_1x.png")
    mask_only.save(REFS / f"{spec['candidate_id']}_mask_only_1x.png")
    ref_card = labelled_strip(
        f"{spec['candidate_id']} {spec['char']} p{spec['physical_page']}/label{spec['printed_label']}",
        [("original", nearest8(original)), ("overlay", nearest8(overlay)), ("mask", nearest8(mask_only))],
        1,
    )
    ref_card.save(REFS / f"{spec['candidate_id']}_card_8x.png")

    target_original = Image.open(ROOT / "glyphs" / f"{spec['target_id']}_original_1x.png").convert("RGB")
    target_overlay = Image.open(ROOT / "glyphs" / f"{spec['target_id']}_overlay_1x.png").convert("RGB")
    target_mask = Image.open(ROOT / "glyphs" / f"{spec['target_id']}_mask_only_1x.png").convert("L")
    width = max(target_original.width, original.width)
    height = max(target_original.height, original.height)

    def canvas(im: Image.Image) -> Image.Image:
        out = Image.new(im.mode, (width, height), 255 if im.mode == "L" else "white")
        out.paste(im, (0, 0))
        return out

    native = labelled_strip(
        (f"{spec['target_id']} vs {spec['candidate_id']} | H {spec['target_h']}/{h} | "
         f"area {spec['target_area']}/{area}"),
        [("target original", canvas(target_original)), ("target overlay", canvas(target_overlay)),
         ("target mask", canvas(target_mask)), ("reference original", canvas(original)),
         ("reference overlay", canvas(overlay)), ("reference mask", canvas(mask_only))],
        1,
    )
    native_path = CRITICAL / f"{spec['target_id']}_vs_{spec['candidate_id']}_native_1x_ratio.png"
    native.save(native_path)
    card8 = labelled_strip(
        (f"{spec['target_id']} vs {spec['candidate_id']} | H ratio={spec['target_h']}/{h} | "
         f"area ratio={spec['target_area']}/{area}"),
        [("target original", nearest8(canvas(target_original))),
         ("target overlay", nearest8(canvas(target_overlay))),
         ("target mask", nearest8(canvas(target_mask))),
         ("reference original", nearest8(canvas(original))),
         ("reference overlay", nearest8(canvas(overlay))),
         ("reference mask", nearest8(canvas(mask_only)))],
        1,
    )
    card_path = CRITICAL / f"{spec['target_id']}_vs_{spec['candidate_id']}_card_8x_ratio.png"
    card8.save(card_path)

    h_ratio = spec["target_h"] / h
    area_ratio = spec["target_area"] / area
    result_rows.append({
        "target_id": spec["target_id"], "char": spec["char"],
        "codepoint": f"U+{ord(spec['char']):04X}", "reference_id": spec["candidate_id"],
        "reference_physical_page": spec["physical_page"], "reference_printed_label": spec["printed_label"],
        "target_page_excluded": 702, "font": spec["font"],
        "target_trace_size_bp": spec["trace_size_bp"], "reference_trace_size_bp": spec["trace_size_bp"],
        "declared_pt": spec["declared_pt"], "effective_pt": spec["effective_pt"],
        "color_rgb": json.dumps(spec["color_rgb"]), "reference_seqno": seqno,
        "reference_bbox_pt": json.dumps([round(v, 6) for v in rect]),
        "background_rgb": json.dumps(background_rgb.tolist()), "role_basis": spec["role"],
        "target_h_ink_px": spec["target_h"], "reference_h_ink_px": h,
        "h_ratio_exact_expression": f"{spec['target_h']}/{h}", "h_ratio_decimal": repr(h_ratio),
        "target_area_px": spec["target_area"], "reference_area_px": area,
        "area_ratio_exact_expression": f"{spec['target_area']}/{area}", "area_ratio_decimal": repr(area_ratio),
        "ratio_gate": "[0.92,1.08] inclusive; no rounding",
        "status": "PASS_REFERENCE" if 0.92 <= h_ratio <= 1.08 and 0.92 <= area_ratio <= 1.08 else "FAIL_REFERENCE",
        "native_1x_ratio": str(native_path.relative_to(ROOT)).replace("\\", "/"),
        "card_8x_ratio": str(card_path.relative_to(ROOT)).replace("\\", "/"),
    })

fields = list(result_rows[0])
with (ROOT / "inventory" / "low_profile_reference_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(result_rows)

print(json.dumps(result_rows, ensure_ascii=False, indent=2))
