from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R1_SA2_R168_READONLY_R114_20260828")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
PAGE_INDEX = 115
DPI = 300
SCALE = DPI / 72.0
FIGURE_CAPTION_CROP_PT = (150.0, 365.0, 450.0, 575.0)


OBJECTS = [
    {"id": "O01", "role": "SET_REGION", "bbox_pt": [161.754, 375.126, 439.200, 520.546]},
    {"id": "O02", "role": "SEGMENT_XY", "bbox_pt": [213.416, 416.028, 398.298, 483.470]},
    {"id": "O03", "role": "ENDPOINT_X_MARKER", "bbox_pt": [211.075, 478.788, 215.757, 483.470]},
    {"id": "O04", "role": "LABEL_X", "bbox_pt": [197.900, 488.157, 203.469, 498.120]},
    {"id": "O05", "role": "ENDPOINT_Y_MARKER", "bbox_pt": [393.615, 416.028, 398.298, 420.710]},
    {"id": "O06", "role": "LABEL_Y", "bbox_pt": [405.804, 398.737, 410.885, 408.700]},
    {"id": "O07", "role": "INTERIOR_MARKER_025", "bbox_pt": [256.810, 463.198, 261.293, 467.681]},
    {"id": "O08", "role": "INTERIOR_MARKER_050", "bbox_pt": [302.445, 447.508, 306.928, 451.991]},
    {"id": "O09", "role": "INTERIOR_MARKER_075", "bbox_pt": [348.080, 431.817, 352.563, 436.301]},
    {"id": "O10", "role": "INTERPOLATION_FORMULA", "bbox_pt": [227.382, 429.443, 304.487, 441.046]},
    {"id": "O11", "role": "DOMAIN_LABEL", "bbox_pt": [375.820, 391.141, 421.511, 400.609]},
    {"id": "O12", "role": "STATEMENT_BOX_BORDER", "bbox_pt": [207.123, 531.152, 399.571, 548.682]},
    {"id": "O13", "role": "STATEMENT_FORMULA", "bbox_pt": [213.102, 535.714, 393.133, 544.879]},
    {"id": "O14", "role": "CAPTION", "bbox_pt": [201.195, 555.717, 405.419, 566.178]},
]


TEXT_OBJECTS = [
    {"id": "T01", "object_id": "O04", "text": "x", "bbox_pt": [197.900, 488.157, 203.469, 498.120]},
    {"id": "T02", "object_id": "O06", "text": "y", "bbox_pt": [405.804, 398.737, 410.885, 408.700]},
    {"id": "T03", "object_id": "O10", "text": "z=λx+(1−λ)y", "bbox_pt": [228.579, 430.868, 303.013, 440.033]},
    {"id": "T04", "object_id": "O11", "text": "凸可行域 C", "bbox_pt": [375.820, 391.141, 421.511, 400.609]},
    {"id": "T05", "object_id": "O13", "text": "x,y∈C, λ∈[0,1] ⇒ λx+(1−λ)y∈C", "bbox_pt": [213.102, 535.714, 393.133, 544.879]},
    {"id": "T06", "object_id": "O14", "text": "图 7.1 凸集中任意两点的线段仍位于可行域内", "bbox_pt": [201.195, 555.717, 405.419, 566.178]},
]


ROIS = [
    {"id": "R01", "purpose": "interpolation formula against segment and midpoint", "bbox_pt": [220.0, 422.0, 315.0, 458.0]},
    {"id": "R02", "purpose": "domain label and endpoint y", "bbox_pt": [366.0, 382.0, 427.0, 428.0]},
    {"id": "R03", "purpose": "endpoint x, label x, and set boundary clearance", "bbox_pt": [187.0, 467.0, 231.0, 508.0]},
    {"id": "R04", "purpose": "statement border and full formula", "bbox_pt": [198.0, 524.0, 408.0, 554.0]},
    {"id": "R05", "purpose": "caption glyph and page separation", "bbox_pt": [193.0, 549.0, 414.0, 573.0]},
    {"id": "R06", "purpose": "tight set-boundary crossing at domain-label C", "bbox_pt": [409.0, 385.0, 429.0, 407.0]},
]


COLORS = {
    "SET_REGION": "#0066cc",
    "SEGMENT_XY": "#005500",
    "ENDPOINT_X_MARKER": "#8b0000",
    "ENDPOINT_Y_MARKER": "#8b0000",
    "INTERIOR_MARKER_025": "#b06000",
    "INTERIOR_MARKER_050": "#b06000",
    "INTERIOR_MARKER_075": "#b06000",
    "LABEL_X": "#7f00ff",
    "LABEL_Y": "#7f00ff",
    "INTERPOLATION_FORMULA": "#cc0099",
    "DOMAIN_LABEL": "#cc0099",
    "STATEMENT_BOX_BORDER": "#333333",
    "STATEMENT_FORMULA": "#cc0099",
    "CAPTION": "#003399",
}


def pt_to_px_bbox(bbox: list[float] | tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(int(round(value * SCALE)) for value in bbox)  # type: ignore[return-value]


def crop_relative_bbox(bbox_pt: list[float]) -> tuple[int, int, int, int]:
    x0, top, _, _ = FIGURE_CAPTION_CROP_PT
    bx0, by0, bx1, by1 = bbox_pt
    return pt_to_px_bbox([bx0 - x0, by0 - top, bx1 - x0, by1 - top])


def render_page() -> Image.Image:
    document = pdfium.PdfDocument(str(PDF))
    page = document[PAGE_INDEX]
    bitmap = page.render(scale=SCALE)
    image = bitmap.to_pil().convert("RGB")
    bitmap.close()
    page.close()
    document.close()
    return image


def bbox_gap(a: list[float], b: list[float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy)


def dark_bbox_metrics(image: Image.Image, bbox_pt: list[float]) -> dict[str, object]:
    box = pt_to_px_bbox(bbox_pt)
    crop = image.crop(box).convert("L")
    histogram = crop.histogram()
    dark_count = sum(histogram[:220])
    nonwhite_count = sum(histogram[:250])
    return {
        "bbox_px": list(box),
        "width_px": crop.width,
        "height_px": crop.height,
        "dark_pixels_lt220": dark_count,
        "nonwhite_pixels_lt250": nonwhite_count,
    }


def draw_overlay(base: Image.Image, entries: list[dict[str, object]], filename: str, text_only: bool = False) -> None:
    overlay = base.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=18)
    for entry in entries:
        bbox = crop_relative_bbox(entry["bbox_pt"])  # type: ignore[arg-type]
        role = str(entry.get("role", "TEXT"))
        color = "#e60000" if text_only else COLORS.get(role, "#e60000")
        draw.rectangle(bbox, outline=color, width=3)
        tag = f"{entry['id']} {role}" if not text_only else f"{entry['id']}"
        tx = bbox[0]
        ty = max(0, bbox[1] - 22)
        label_bbox = draw.textbbox((tx, ty), tag, font=font)
        draw.rectangle(label_bbox, fill="white")
        draw.text((tx, ty), tag, fill=color, font=font)
    overlay.save(ROOT / filename, dpi=(DPI, DPI))


def main() -> None:
    page = render_page()
    crop_box = pt_to_px_bbox(FIGURE_CAPTION_CROP_PT)
    figure = page.crop(crop_box)
    figure.save(ROOT / "figure_caption_native300dpi.png", dpi=(DPI, DPI))
    ImageOps.grayscale(figure).save(ROOT / "figure_caption_grayscale_native300dpi.png", dpi=(DPI, DPI))

    draw_overlay(figure, OBJECTS, "object_overlay_native300dpi.png")
    draw_overlay(figure, TEXT_OBJECTS, "text_overlay_native300dpi.png", text_only=True)

    semantic = figure.copy()
    draw = ImageDraw.Draw(semantic)
    font = ImageFont.load_default(size=18)
    semantic_groups = {
        "GEOMETRY": ["O01", "O02", "O03", "O05", "O07", "O08", "O09"],
        "LABELS": ["O04", "O06", "O10", "O11", "O13"],
        "FRAME": ["O12"],
        "CAPTION": ["O14"],
    }
    group_colors = {"GEOMETRY": "#0066cc", "LABELS": "#e60000", "FRAME": "#008000", "CAPTION": "#7f00ff"}
    by_id = {entry["id"]: entry for entry in OBJECTS}
    for group, ids in semantic_groups.items():
        for object_id in ids:
            bbox = crop_relative_bbox(by_id[object_id]["bbox_pt"])  # type: ignore[arg-type]
            draw.rectangle(bbox, outline=group_colors[group], width=3)
        draw.text((12, 12 + 24 * list(semantic_groups).index(group)), group, fill=group_colors[group], font=font, stroke_width=2, stroke_fill="white")
    semantic.save(ROOT / "semantic_overlay_native300dpi.png", dpi=(DPI, DPI))

    for roi in ROIS:
        roi_box = pt_to_px_bbox(roi["bbox_pt"])  # type: ignore[arg-type]
        native = page.crop(roi_box)
        native_name = f"{roi['id']}_native1x.png"
        enlarged_name = f"{roi['id']}_nearest8x.png"
        native.save(ROOT / native_name, dpi=(DPI, DPI))
        native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST).save(ROOT / enlarged_name)

    object_metrics = []
    for entry in OBJECTS:
        object_metrics.append(
            {
                **entry,
                **dark_bbox_metrics(page, entry["bbox_pt"]),  # type: ignore[arg-type]
            }
        )
    pair_geometry = []
    for pair_index, (left, right) in enumerate(combinations(OBJECTS, 2), start=1):
        pair_geometry.append(
            {
                "pair_id": f"P{pair_index:03d}",
                "left_id": left["id"],
                "right_id": right["id"],
                "bbox_gap_pt": round(bbox_gap(left["bbox_pt"], right["bbox_pt"]), 3),  # type: ignore[arg-type]
            }
        )
    payload = {
        "physical_page_one_based": PAGE_INDEX + 1,
        "render_dpi": DPI,
        "figure_caption_crop_pt": list(FIGURE_CAPTION_CROP_PT),
        "object_count": len(OBJECTS),
        "unordered_pair_count": len(pair_geometry),
        "objects": object_metrics,
        "text_objects": TEXT_OBJECTS,
        "rois": ROIS,
        "pair_geometry": pair_geometry,
    }
    (ROOT / "mechanical_metrics.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"object_count": len(OBJECTS), "unordered_pair_count": len(pair_geometry), "roi_count": len(ROIS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
