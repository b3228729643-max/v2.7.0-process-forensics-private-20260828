from __future__ import annotations

import csv
import copy
import hashlib
import io
import json
import math
from itertools import combinations
from pathlib import Path

import cairosvg
import fitz
import numpy as np
from lxml import etree
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa2_font_r1_direct_build_v1")
PDF = ROOT / "01_build" / "v260_FIG-P656-01_standalone.pdf"
PAGE_PNG = ROOT / "02_render" / "fullpage_native300.png"
MACHINE = ROOT / "03_machine"
VIEWS = ROOT / "05_views"
SCALE = 300.0 / 72.0
INK_THRESHOLD = 248


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def pt_rect_to_px(rect: fitz.Rect, width: int, height: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(rect.x0 * SCALE)) - 1)
    y0 = max(0, int(math.floor(rect.y0 * SCALE)) - 1)
    x1 = min(width, int(math.ceil(rect.x1 * SCALE)) + 1)
    y1 = min(height, int(math.ceil(rect.y1 * SCALE)) + 1)
    return x0, y0, x1, y1


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return round(math.hypot(dx, dy), 3)


def intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


page_image = Image.open(PAGE_PNG).convert("RGB")
page_array = np.asarray(page_image)
height, width = page_array.shape[:2]
gray = np.asarray(page_image.convert("L"))
ink = gray < INK_THRESHOLD

document = fitz.open(PDF)
page = document[0]
raw = page.get_text("rawdict")
svg_tree = etree.parse(str(MACHINE / "page.svg"))
svg_root = svg_tree.getroot()
svg_namespace = {"svg": "http://www.w3.org/2000/svg"}
svg_defs = svg_root.find("{http://www.w3.org/2000/svg}defs")
svg_uses = svg_root.xpath(".//svg:g[@id='surface1']//svg:use", namespaces=svg_namespace)


def render_independent_svg_glyph(use_element, pixel_bbox: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = pixel_bbox
    pixel_width = max(1, x1 - x0)
    pixel_height = max(1, y1 - y0)
    isolated = etree.Element(svg_root.tag, nsmap=svg_root.nsmap)
    isolated.set("width", f"{pixel_width}pt")
    isolated.set("height", f"{pixel_height}pt")
    isolated.set("viewBox", f"{x0 / SCALE:.8f} {y0 / SCALE:.8f} {pixel_width / SCALE:.8f} {pixel_height / SCALE:.8f}")
    isolated.set("version", svg_root.get("version", "1.2"))
    isolated.append(copy.deepcopy(svg_defs))
    surface = etree.SubElement(isolated, "{http://www.w3.org/2000/svg}g")
    parent = use_element.getparent()
    styled = etree.SubElement(surface, "{http://www.w3.org/2000/svg}g")
    for key, value in parent.attrib.items():
        styled.set(key, value)
    styled.append(copy.deepcopy(use_element))
    png = cairosvg.svg2png(bytestring=etree.tostring(isolated), output_width=pixel_width, output_height=pixel_height)
    rgba = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    return rgba[:, :, 3] > 0

glyph_rows: list[dict] = []
objects: list[dict] = []
glyph_index = 0
for block_index, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block["lines"]):
        for span_index, span in enumerate(line["spans"]):
            for char_index, char in enumerate(span["chars"]):
                value = char["c"]
                if not value.strip():
                    continue
                glyph_index += 1
                object_id = f"G{glyph_index:03d}"
                rect = fitz.Rect(char["bbox"])
                pixel_bbox = pt_rect_to_px(rect, width, height)
                x0, y0, x1, y1 = pixel_bbox
                if glyph_index > len(svg_uses):
                    raise RuntimeError("SVG_USE_DENOMINATOR_TOO_SMALL")
                local = render_independent_svg_glyph(svg_uses[glyph_index - 1], pixel_bbox)
                ys, xs = np.nonzero(local)
                flat = ((ys + y0) * width + (xs + x0)).astype(np.int64)
                row = {
                    "glyph_id": object_id,
                    "char": value,
                    "codepoint": f"U+{ord(value):04X}",
                    "font": span.get("font", ""),
                    "pdf_extracted_size_bp": round(float(span.get("size", 0.0)), 4),
                    "block_index": block_index,
                    "line_index": line_index,
                    "span_index": span_index,
                    "char_index": char_index,
                    "x0_pt": round(rect.x0, 4),
                    "y0_pt": round(rect.y0, 4),
                    "x1_pt": round(rect.x1, 4),
                    "y1_pt": round(rect.y1, 4),
                    "x0_px": x0,
                    "y0_px": y0,
                    "x1_px": x1,
                    "y1_px": y1,
                    "ink_pixels": int(flat.size),
                    "empty_mask": int(flat.size == 0),
                }
                glyph_rows.append(row)
                objects.append({"id": object_id, "kind": "glyph", "role": f"glyph:{value}", "bbox": pixel_bbox, "flat": np.unique(flat), "source_index": glyph_index - 1})

if len(svg_uses) != len(glyph_rows):
    raise RuntimeError(f"SVG_USE_DENOMINATOR_CHANGED:{len(svg_uses)}:{len(glyph_rows)}")

all_drawings = page.get_drawings()
excluded_drawings: list[dict] = []
visible_drawings: list[tuple[int, dict]] = []
for source_index, drawing in enumerate(all_drawings):
    rect = fitz.Rect(drawing["rect"])
    pixel_bbox = pt_rect_to_px(rect, width, height)
    x0, y0, x1, y1 = pixel_bbox
    raster_nonwhite = int(np.count_nonzero(ink[y0:y1, x0:x1]))
    if rect.y0 > 800 and rect.x1 < 10 and raster_nonwhite == 0:
        excluded_drawings.append({
            "source_drawing_index": source_index,
            "reason": "NONVISIBLE_PATTERN_CLIP_RECORD",
            "rect_pt": [round(rect.x0, 4), round(rect.y0, 4), round(rect.x1, 4), round(rect.y1, 4)],
            "raster_nonwhite_pixels": raster_nonwhite,
        })
    else:
        visible_drawings.append((source_index, drawing))

drawing_roles = [
    *[f"sequence_circle_{i:02d}" for i in range(1, 19)],
    "count_vector_box",
    "sequence_to_count_arrow_shaft",
    "sequence_to_count_arrow_head",
    "warning_box",
    "coefficient_box",
    "count_to_coefficient_arrow_shaft",
    "count_to_coefficient_arrow_head",
]
if len(visible_drawings) != len(drawing_roles):
    raise RuntimeError(f"VISIBLE_DRAWING_DENOMINATOR_CHANGED:{len(visible_drawings)}")

drawing_rows: list[dict] = []
for drawing_index, ((source_index, drawing), role) in enumerate(zip(visible_drawings, drawing_roles), start=1):
    object_id = f"D{drawing_index:03d}"
    rect = fitz.Rect(drawing["rect"])
    pixel_bbox = pt_rect_to_px(rect, width, height)
    x0, y0, x1, y1 = pixel_bbox
    local = ink[y0:y1, x0:x1].copy()
    # Remove all text-character regions from the drawing mask. Glyph masks are independently
    # rendered from the SVG <use> records, so no full-page crop ink is duplicated into glyphs.
    for glyph_object in objects:
        if glyph_object["kind"] != "glyph":
            continue
        gx0, gy0, gx1, gy1 = glyph_object["bbox"]
        ix0, iy0 = max(x0, gx0 - 1), max(y0, gy0 - 1)
        ix1, iy1 = min(x1, gx1 + 1), min(y1, gy1 + 1)
        if ix1 > ix0 and iy1 > iy0:
            local[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = False
    ys, xs = np.nonzero(local)
    flat = ((ys + y0) * width + (xs + x0)).astype(np.int64)
    row = {
        "drawing_id": object_id,
        "role": role,
        "source_drawing_index": source_index,
        "drawing_type": drawing["type"],
        "item_count": len(drawing["items"]),
        "x0_pt": round(rect.x0, 4),
        "y0_pt": round(rect.y0, 4),
        "x1_pt": round(rect.x1, 4),
        "y1_pt": round(rect.y1, 4),
        "x0_px": x0,
        "y0_px": y0,
        "x1_px": x1,
        "y1_px": y1,
        "ink_pixels": int(flat.size),
        "empty_mask": int(flat.size == 0),
        "stroke_rgb": json.dumps(drawing.get("color")),
        "fill_rgb": json.dumps(drawing.get("fill")),
    }
    drawing_rows.append(row)
    objects.append({"id": object_id, "kind": "drawing", "role": role, "bbox": pixel_bbox, "flat": np.unique(flat), "source_index": source_index})

object_rows: list[dict] = []
for item in objects:
    x0, y0, x1, y1 = item["bbox"]
    object_rows.append({
        "object_id": item["id"],
        "kind": item["kind"],
        "role": item["role"],
        "source_index": item["source_index"],
        "x0_px": x0,
        "y0_px": y0,
        "x1_px": x1,
        "y1_px": y1,
        "bbox_width_px": x1 - x0,
        "bbox_height_px": y1 - y0,
        "ink_pixels": int(item["flat"].size),
        "empty_mask": int(item["flat"].size == 0),
        "page_width_px": width,
        "page_height_px": height,
        "clip_outside_page": int(x0 < 0 or y0 < 0 or x1 > width or y1 > height),
    })

pair_rows: list[dict] = []
for pair_index, (left, right) in enumerate(combinations(objects, 2), start=1):
    shared = int(np.intersect1d(left["flat"], right["flat"], assume_unique=True).size)
    area = intersection_area(left["bbox"], right["bbox"])
    gap = bbox_gap(left["bbox"], right["bbox"])
    relation = "SHARED_RASTER_INK" if shared else ("BBOX_OVERLAP_NO_SHARED_RASTER_INK" if area else "DISJOINT_BBOX")
    pair_rows.append({
        "pair_id": f"PAIR_{pair_index:04d}",
        "object_a": left["id"],
        "object_b": right["id"],
        "kind_a": left["kind"],
        "kind_b": right["kind"],
        "bbox_gap_px": gap,
        "bbox_intersection_area_px": area,
        "shared_raster_ink_px": shared,
        "machine_relation": relation,
    })

critical_sorted = sorted(pair_rows, key=lambda row: (0 if row["shared_raster_ink_px"] > 0 else 1, row["bbox_gap_px"], -row["bbox_intersection_area_px"], row["pair_id"]))
critical_ids = {row["pair_id"] for row in critical_sorted[:34]}
critical_rows = [{**row, "critical_rank": rank} for rank, row in enumerate(critical_sorted[:34], start=1)]

write_csv(MACHINE / "glyph_machine_ledger.csv", list(glyph_rows[0]), glyph_rows)
write_csv(MACHINE / "drawing_machine_ledger.csv", list(drawing_rows[0]), drawing_rows)
write_csv(MACHINE / "object_machine_ledger.csv", list(object_rows[0]), object_rows)
write_csv(MACHINE / "unordered_pair_machine_ledger.csv", list(pair_rows[0]), pair_rows)
write_csv(MACHINE / "critical_pair_machine_ledger.csv", list(critical_rows[0]), critical_rows)
write_csv(MACHINE / "clip_machine_ledger.csv", ["object_id", "clip_outside_page", "empty_mask"], [{"object_id": row["object_id"], "clip_outside_page": row["clip_outside_page"], "empty_mask": row["empty_mask"]} for row in object_rows])
(MACHINE / "excluded_nonvisible_pdf_drawing_records.json").write_text(json.dumps(excluded_drawings, ensure_ascii=False, indent=2), encoding="utf-8")

content_x0 = max(0, min(row["x0_px"] for row in object_rows) - 80)
content_y0 = max(0, min(row["y0_px"] for row in object_rows) - 80)
content_x1 = min(width, max(row["x1_px"] for row in object_rows) + 80)
content_y1 = min(height, max(row["y1_px"] for row in object_rows) + 80)
crop_box = (content_x0, content_y0, content_x1, content_y1)
figure_crop = page_image.crop(crop_box)
figure_crop.save(VIEWS / "figure_crop_native300_color.png")
figure_crop.convert("L").save(VIEWS / "figure_crop_native300_grayscale.png")

overlay = page_image.copy()
draw = ImageDraw.Draw(overlay)
font = ImageFont.load_default()
for item in objects:
    x0, y0, x1, y1 = item["bbox"]
    color = (0, 80, 220) if item["kind"] == "glyph" else (220, 40, 30)
    draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
    draw.text((x0, max(0, y0 - 12)), item["id"], fill=color, font=font, stroke_width=2, stroke_fill=(255, 255, 255))
overlay.crop(crop_box).save(VIEWS / "object_id_overlay_native300.png")

object_lookup = {item["id"]: item for item in objects}
tiles: list[Image.Image] = []
for row in critical_rows:
    left = object_lookup[row["object_a"]]
    right = object_lookup[row["object_b"]]
    x0 = max(0, min(left["bbox"][0], right["bbox"][0]) - 24)
    y0 = max(0, min(left["bbox"][1], right["bbox"][1]) - 24)
    x1 = min(width, max(left["bbox"][2], right["bbox"][2]) + 24)
    y1 = min(height, max(left["bbox"][3], right["bbox"][3]) + 24)
    tile = page_image.crop((x0, y0, x1, y1))
    tile.thumbnail((360, 180))
    panel = Image.new("RGB", (380, 215), "white")
    panel.paste(tile, ((380 - tile.width) // 2, 28))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.text((5, 5), f'{row["critical_rank"]:02d} {row["pair_id"]} {row["object_a"]}/{row["object_b"]} shared={row["shared_raster_ink_px"]} gap={row["bbox_gap_px"]}', fill="black", font=font)
    tiles.append(panel)
sheet = Image.new("RGB", (760, 215 * 17), "white")
for index, tile in enumerate(tiles):
    sheet.paste(tile, ((index % 2) * 380, (index // 2) * 215))
sheet.save(VIEWS / "critical_pairs_contact_sheet_native300.png")

risk_regions = {
    "sequence_panel": (350, 285, 940, 740),
    "arrow_label": (920, 390, 1270, 610),
    "count_box": (1070, 330, 1650, 690),
    "constraint_warning": (1060, 640, 1670, 950),
    "coefficient_box": (1580, 340, 2200, 700),
}
for name, region in risk_regions.items():
    roi = page_image.crop(region)
    roi.save(VIEWS / f"risk_{name}_1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(VIEWS / f"risk_{name}_8x.png")

summary = {
    "schema": "P656_R1_MACHINE_EVIDENCE_V1",
    "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF), "pages": document.page_count},
    "render": {"path": str(PAGE_PNG), "bytes": PAGE_PNG.stat().st_size, "sha256": sha256(PAGE_PNG), "dpi": 300, "width_px": width, "height_px": height},
    "denominators": {
        "glyphs": len(glyph_rows),
        "visible_drawings": len(drawing_rows),
        "objects": len(object_rows),
        "unordered_pairs": len(pair_rows),
        "critical_pairs": len(critical_rows),
        "clip_rows": len(object_rows),
        "excluded_nonvisible_pdf_drawing_records": len(excluded_drawings),
    },
    "raw_machine_counts": {
        "empty_object_masks": sum(row["empty_mask"] for row in object_rows),
        "clip_outside_page": sum(row["clip_outside_page"] for row in object_rows),
        "pairs_with_shared_raster_ink": sum(row["shared_raster_ink_px"] > 0 for row in pair_rows),
        "pairs_with_bbox_overlap_no_shared_raster_ink": sum(row["machine_relation"] == "BBOX_OVERLAP_NO_SHARED_RASTER_INK" for row in pair_rows),
    },
    "content_crop_px": list(crop_box),
    "machine_script_contains_manual_fields": False,
    "critical_selection": "all shared-raster pairs first, then ascending bbox gap, fixed denominator 34",
}
(MACHINE / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
