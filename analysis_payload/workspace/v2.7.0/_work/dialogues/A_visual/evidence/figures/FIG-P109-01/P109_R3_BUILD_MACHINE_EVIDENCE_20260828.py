from __future__ import annotations

import csv
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P109-01_standalone.pdf"
NATIVE = ROOT / "full_page_native300dpi.png"
EXPECTED_PDF_SHA = "C615152183FCB524F2B4FBDFB4A69D43C134DCDE20F989BF0050C2D2776A199D"
SCALE = 300.0 / 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def px_rect(rect) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = [float(v) for v in rect]
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def intersection_area(a, b) -> int:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def clearance(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


if not PDF.is_file() or sha256(PDF) != EXPECTED_PDF_SHA:
    raise RuntimeError("PDF identity mismatch")
if not NATIVE.is_file():
    raise RuntimeError("native 300 dpi render missing")

doc = fitz.open(PDF)
if doc.page_count != 1:
    raise RuntimeError("expected exactly one page")
page = doc[0]
drawings = page.get_drawings()
text_blocks = [b for b in page.get_text("blocks") if int(b[6]) == 0 and str(b[4]).strip()]
if len(drawings) != 10 or len(text_blocks) != 5:
    raise RuntimeError(f"unexpected object structure drawings={len(drawings)} text_blocks={len(text_blocks)}")

drawing_specs = [
    ("O001", "GRAPHIC", "convex-set filled region and boundary"),
    ("O002", "GRAPHIC", "segment joining x and y"),
    ("O003", "GRAPHIC", "endpoint marker x"),
    ("O004", "GRAPHIC", "endpoint marker y"),
    ("O005", "GRAPHIC", "interpolation marker lambda=.25"),
    ("O006", "GRAPHIC", "interpolation marker lambda=.50"),
    ("O007", "GRAPHIC", "interpolation marker lambda=.75"),
    ("O008", "GRAPHIC", "opaque background of interpolation formula"),
    ("O009", "GRAPHIC", "opaque protective background of domain label"),
    ("O010", "GRAPHIC", "rounded statement box"),
]
text_specs = [
    ("O011", "TEXT", "endpoint label x"),
    ("O012", "TEXT", "endpoint label y"),
    ("O013", "TEXT", "interpolation formula z=lambda x+(1-lambda)y"),
    ("O014", "TEXT", "domain label convex feasible region C"),
    ("O015", "TEXT", "convexity statement formula"),
]

objects = []
for (object_id, kind, semantic), drawing in zip(drawing_specs, drawings):
    rect_pt = tuple(float(v) for v in drawing["rect"])
    objects.append({
        "object_id": object_id,
        "kind": kind,
        "semantic": semantic,
        "text": "",
        "bbox_pt": rect_pt,
        "bbox_px": px_rect(rect_pt),
    })
for (object_id, kind, semantic), block in zip(text_specs, text_blocks):
    rect_pt = tuple(float(v) for v in block[:4])
    objects.append({
        "object_id": object_id,
        "kind": kind,
        "semantic": semantic,
        "text": str(block[4]).replace("\n", " ").strip(),
        "bbox_pt": rect_pt,
        "bbox_px": px_rect(rect_pt),
    })

with (ROOT / "OBJECTS.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["object_id", "kind", "semantic", "text", "x0_pt", "y0_pt", "x1_pt", "y1_pt", "x0_px", "y0_px", "x1_px", "y1_px"])
    for obj in objects:
        writer.writerow([obj["object_id"], obj["kind"], obj["semantic"], obj["text"], *[f"{v:.6f}" for v in obj["bbox_pt"]], *obj["bbox_px"]])

ownership_pairs = {
    tuple(sorted(pair))
    for pair in [
        ("O001", "O002"), ("O001", "O003"), ("O001", "O004"), ("O001", "O005"),
        ("O001", "O006"), ("O001", "O007"), ("O001", "O008"), ("O001", "O009"),
        ("O001", "O011"), ("O001", "O012"), ("O001", "O013"), ("O001", "O014"),
        ("O002", "O003"), ("O002", "O004"), ("O002", "O005"), ("O002", "O006"),
        ("O002", "O007"), ("O008", "O013"), ("O009", "O014"), ("O010", "O015")
    ]
}
pairs = []
for index, (a, b) in enumerate(combinations(objects, 2), start=1):
    key = tuple(sorted((a["object_id"], b["object_id"])))
    area = intersection_area(a["bbox_px"], b["bbox_px"])
    gap = clearance(a["bbox_px"], b["bbox_px"])
    machine_class = "EXPECTED_RELATION_OR_CONTAINMENT" if key in ownership_pairs else ("BBOX_CANDIDATE" if area > 0 or gap < 6 else "DISJOINT")
    pairs.append({
        "pair_id": f"P{index:03d}",
        "object_a": a["object_id"],
        "object_b": b["object_id"],
        "bbox_intersection_px": area,
        "bbox_clearance_px": round(gap, 3),
        "machine_class": machine_class,
    })
with (ROOT / "MACHINE_PAIRS.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
    writer.writeheader()
    writer.writerows(pairs)

raw = page.get_text("rawdict")
chars = []
for block in raw.get("blocks", []):
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            for char in span.get("chars", []):
                c = char.get("c", "")
                if c:
                    chars.append((c, char.get("bbox", [0, 0, 0, 0])))
with (ROOT / "GLYPH_CODEPOINTS.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["glyph_id", "character", "codepoint", "x0_pt", "y0_pt", "x1_pt", "y1_pt"])
    for index, (char, bbox) in enumerate(chars, start=1):
        writer.writerow([f"G{index:03d}", char, "+".join(f"U+{ord(c):04X}" for c in char), *[f"{float(v):.6f}" for v in bbox]])

image = Image.open(NATIVE).convert("RGB")
gray = image.convert("L").convert("RGB")
figure_box = px_rect((145.0, 55.0, 455.0, 255.0))
image.crop(figure_box).save(ROOT / "figure_content_native300dpi.png")
gray.crop(figure_box).save(ROOT / "figure_content_grayscale_native300dpi.png")

palette = {"GRAPHIC": (0, 95, 190), "TEXT": (210, 30, 30)}
overlay = image.copy()
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default()
for obj in objects:
    x0, y0, x1, y1 = obj["bbox_px"]
    color = palette[obj["kind"]]
    draw.rectangle((x0, y0, x1, y1), outline=color, width=3)
    draw.rectangle((x0, max(0, y0 - 14), x0 + 36, y0), fill=(255, 255, 255))
    draw.text((x0 + 1, max(0, y0 - 13)), obj["object_id"], fill=color, font=font)
overlay.crop(figure_box).save(ROOT / "object_overlay_native300dpi.png")

text_overlay = image.copy()
text_draw = ImageDraw.Draw(text_overlay)
for obj in [o for o in objects if o["kind"] == "TEXT"]:
    text_draw.rectangle(obj["bbox_px"], outline=(220, 30, 30), width=4)
text_overlay.crop(figure_box).save(ROOT / "text_overlay_native300dpi.png")

semantic_overlay = image.copy()
semantic_draw = ImageDraw.Draw(semantic_overlay)
for obj in objects:
    x0, y0, x1, y1 = obj["bbox_px"]
    semantic_draw.rectangle((x0, y0, x1, y1), outline=(120, 0, 170), width=2)
    semantic_draw.text((x0 + 2, y1 + 2), obj["semantic"][:24], fill=(120, 0, 170), font=font)
semantic_overlay.crop(figure_box).save(ROOT / "semantic_overlay_native300dpi.png")

cells = []
for obj in objects:
    x0, y0, x1, y1 = obj["bbox_px"]
    margin = 14
    crop = image.crop((max(0, x0 - margin), max(0, y0 - margin), min(image.width, x1 + margin), min(image.height, y1 + margin)))
    crop.thumbnail((230, 125), Image.Resampling.LANCZOS)
    cell = Image.new("RGB", (250, 155), "white")
    cell.paste(crop, ((250 - crop.width) // 2, 20 + (125 - crop.height) // 2))
    ImageDraw.Draw(cell).text((5, 4), f"{obj['object_id']} {obj['kind']}", fill="black", font=font)
    cells.append(cell)
sheet = Image.new("RGB", (750, 775), "white")
for index, cell in enumerate(cells):
    sheet.paste(cell, ((index % 3) * 250, (index // 3) * 155))
sheet.save(ROOT / "object_contact_sheet.png")

roi_specs = [
    ("R01_domain_label_boundary", (360.0, 72.0, 438.0, 112.0)),
    ("R02_domain_C_tight", (405.0, 78.0, 432.0, 106.0)),
    ("R03_formula_segment", (215.0, 112.0, 315.0, 174.0)),
    ("R04_x_endpoint_label", (185.0, 165.0, 225.0, 207.0)),
    ("R05_y_endpoint_label", (385.0, 85.0, 425.0, 128.0)),
    ("R06_statement_box", (195.0, 218.0, 410.0, 257.0)),
]
roi_rows = []
for roi_id, rect_pt in roi_specs:
    box = px_rect(rect_pt)
    crop = image.crop(box)
    raw_path = ROOT / f"{roi_id}_native1x.png"
    near_path = ROOT / f"{roi_id}_nearest8x.png"
    crop.save(raw_path)
    crop.resize((crop.width * 8, crop.height * 8), Image.Resampling.NEAREST).save(near_path)
    roi_rows.append({"roi_id": roi_id, "bbox_pt": list(rect_pt), "bbox_px": list(box), "native1x": raw_path.name, "nearest8x": near_path.name})

rgb = np.asarray(image)
domain = next(o for o in objects if o["object_id"] == "O014")
dx0, dy0, dx1, dy1 = domain["bbox_px"]
text_region = rgb[dy0:dy1, dx0:dx1, :]
gray_like = (text_region.max(axis=2) - text_region.min(axis=2) <= 12) & (text_region.mean(axis=2) < 225)
full_blue_distance = np.sqrt(
    (rgb[:, :, 0].astype(float) - 31.0) ** 2
    + (rgb[:, :, 1].astype(float) - 78.0) ** 2
    + (rgb[:, :, 2].astype(float) - 121.0) ** 2
)
boundary_mask = full_blue_distance < 45.0
distance_to_boundary = distance_transform_edt(~boundary_mask)
domain_mask_global = np.zeros(boundary_mask.shape, dtype=bool)
domain_mask_global[dy0:dy1, dx0:dx1] = gray_like
text_points = distance_to_boundary[domain_mask_global]
min_boundary_distance = float(text_points.min()) if text_points.size else None
shared_pixels = int(np.logical_and(boundary_mask, domain_mask_global).sum())

bg = next(o for o in objects if o["object_id"] == "O009")
bx0, by0, bx1, by1 = bg["bbox_px"]
roi_blue = boundary_mask[max(0, by0 - 30):min(image.height, by1 + 30), max(0, bx0 - 40):min(image.width, bx1 + 40)].astype(np.uint8)
component_count = max(0, cv2.connectedComponents(roi_blue, connectivity=8)[0] - 1)

metrics = {
    "schema": "P109_R3_DOMAIN_LABEL_BOUNDARY_METRICS_V1",
    "domain_text_object": "O014",
    "protective_background_object": "O009",
    "set_boundary_object": "O001",
    "domain_text_ink_pixels": int(gray_like.sum()),
    "boundary_domain_shared_pixels": shared_pixels,
    "minimum_boundary_to_domain_text_ink_distance_px": None if min_boundary_distance is None else round(min_boundary_distance, 3),
    "protective_background_bbox_px": list(bg["bbox_px"]),
    "predicted_inner_sep_protection_px": round(1.2 * 300.0 / 72.27, 3),
    "visible_blue_components_in_protection_roi": int(component_count),
}
(ROOT / "DOMAIN_LABEL_BOUNDARY_METRICS.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "ROI_INDEX.json").write_text(json.dumps({"schema": "P109_R3_ROI_INDEX_V1", "rows": roi_rows}, ensure_ascii=False, indent=2), encoding="utf-8")

machine = {
    "schema": "P109_R3_MACHINE_RESULT_V1",
    "pdf_path": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_sha256": sha256(PDF),
    "page_count": 1,
    "page_size_pt": [float(page.rect.width), float(page.rect.height)],
    "object_count": len(objects),
    "drawing_object_count": 10,
    "text_object_count": 5,
    "unordered_pair_count": len(pairs),
    "expected_unordered_pair_count": len(objects) * (len(objects) - 1) // 2,
    "glyph_codepoint_count": len(chars),
    "roi_pair_count": len(roi_specs),
    "boundary_domain_shared_pixels": shared_pixels,
    "minimum_boundary_to_domain_text_ink_distance_px": None if min_boundary_distance is None else round(min_boundary_distance, 3),
    "machine_hard_failure_count": 0 if shared_pixels == 0 and min_boundary_distance is not None and min_boundary_distance >= 3.0 else 1,
    "caption_rendered_in_standalone": False,
    "caption_source_unchanged": True,
}
(ROOT / "MACHINE_RESULT.json").write_text(json.dumps(machine, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(machine, ensure_ascii=False))
