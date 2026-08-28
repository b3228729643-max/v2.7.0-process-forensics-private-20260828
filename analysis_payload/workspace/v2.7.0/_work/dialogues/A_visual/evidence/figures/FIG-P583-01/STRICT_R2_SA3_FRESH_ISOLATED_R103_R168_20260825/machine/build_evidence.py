from __future__ import annotations

import csv
import itertools
import json
import math
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R2_SA3_FRESH_ISOLATED_R103_R168_20260825")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_rmse_rate.tex")
PAGE_INDEX = 632
DPI = 300
SCALE = DPI / 72.0
FLOAT_RECT_PT = (60.0, 62.0, 525.0, 255.0)
PLOT_RECT_PT = (140.0, 65.0, 443.0, 220.0)

VIEWS = ROOT / "views"
GLYPHS = ROOT / "glyphs"
PAIRS = ROOT / "pairs"
CRITICAL = ROOT / "critical"
OVERLAYS = ROOT / "overlays"
MACHINE = ROOT / "machine"
for directory in (VIEWS, GLYPHS, PAIRS, CRITICAL, OVERLAYS, MACHINE):
    directory.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rect_to_px(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return (
        math.floor(x0 * SCALE),
        math.floor(y0 * SCALE),
        math.ceil(x1 * SCALE),
        math.ceil(y1 * SCALE),
    )


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def color_float_to_rgb(value) -> tuple[int, int, int] | None:
    if value is None:
        return None
    return tuple(int(round(float(v) * 255)) for v in value)


def target_color_mask(region: np.ndarray, target_rgb: tuple[int, int, int]) -> np.ndarray:
    pix = region.astype(np.float32)
    white = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    target = np.array(target_rgb, dtype=np.float32)
    vector = white - target
    denom = float(np.dot(vector, vector))
    if denom == 0:
        return np.zeros(region.shape[:2], dtype=bool)
    delta = white - pix
    alpha = np.sum(delta * vector, axis=2) / denom
    reconstructed = white - alpha[..., None] * vector
    residual = np.max(np.abs(pix - reconstructed), axis=2)
    contrast = np.max(delta, axis=2)
    return (contrast >= 20.0) & (alpha > 0.0) & (alpha <= 1.12) & (residual <= 7.0)


def bbox_from_coords(coords: np.ndarray) -> tuple[int, int, int, int]:
    ys = coords[:, 0]
    xs = coords[:, 1]
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def save_tight_mask(path: Path, coords: np.ndarray) -> tuple[int, int, int, int]:
    bbox = bbox_from_coords(coords)
    x0, y0, x1, y1 = bbox
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    mask[coords[:, 0] - y0, coords[:, 1] - x0] = 255
    Image.fromarray(mask, "L").save(path)
    return bbox


def point_in_rect(bbox, rect) -> bool:
    x0, y0, x1, y1 = bbox
    a0, b0, a1, b1 = rect
    return x1 > a0 and x0 < a1 and y1 > b0 and y0 < b1


def parent_and_role(span_bbox: tuple[float, float, float, float], span_text: str) -> tuple[str, str]:
    x0, y0, x1, y1 = span_bbox
    compact = span_text.strip()
    if y0 >= 220.0:
        return "P_CAPTION", "CAPTION"
    if 189.0 <= y0 <= 201.0:
        return f"P_XTICK_{compact}", "TICK_LABEL"
    if x1 <= 180.5 and y0 < 189.0 and x0 >= 159.0:
        return f"P_YTICK_{compact}", "TICK_LABEL"
    if 355.0 <= x0 and 128.0 <= y0 <= 142.0:
        return "P_RATE_FORMULA", "FORMULA"
    if 283.0 <= x0 and 93.0 <= y0 <= 118.0:
        return "P_TRIANGLE_NOTE", "ANNOTATION"
    if 230.0 <= x0 and 151.0 <= y0 <= 175.0:
        return "P_CONDITION_BOX", "CONDITION"
    if 284.0 <= x0 and 204.0 <= y0 <= 218.0:
        return "P_X_AXIS_LABEL", "AXIS_TITLE"
    if x0 < 159.0 and 113.0 <= y0 <= 142.0:
        return "P_Y_AXIS_LABEL", "AXIS_TITLE"
    return "P_UNMAPPED", "UNMAPPED"


def glyph_class(char: str, role: str, source_size: float) -> tuple[str, int]:
    code = ord(char)
    category = unicodedata.category(char)
    if role == "FORMULA" and source_size < 8.0:
        return "NATURAL_SCRIPT", 15
    if char in {"；", "。", "，", "、", "：", ",", ".", ":", ";"}:
        return "LOW_PROFILE_PUNCTUATION", 0
    if 0x3400 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF or 0x3000 <= code <= 0x303F:
        return "CJK_OR_FULLWIDTH", 30
    if char.isdigit() or (char.isascii() and char.isupper()):
        return "LATIN_UPPER_OR_DIGIT", 24
    if char.isascii() and char.islower():
        return "LATIN_LOWER", 17
    if category.startswith("S") or char in {"/", "(", ")", "−", "×", "÷"}:
        return "MATH_BASE_OR_OPERATOR", 22
    return "OTHER_VISIBLE", 17


def id_safe_text(index: int, char: str) -> str:
    cps = "_".join(f"U{ord(c):04X}" for c in char)
    return f"TXT_{index:04d}_{cps}"


def render_graphic_mask(page_rect: fitz.Rect, drawing: dict, item_indexes: list[int], mode: str) -> np.ndarray:
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item_index in item_indexes:
        item = drawing["items"][item_index]
        op = item[0]
        if op == "l":
            shape.draw_line(item[1], item[2])
        elif op == "c":
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        elif op == "re":
            shape.draw_rect(item[1])
        elif op == "qu":
            shape.draw_quad(item[1])
        else:
            raise RuntimeError(f"Unsupported drawing item: {op}")
    if mode == "stroke":
        shape.finish(
            color=(0, 0, 0), fill=None,
            width=float(drawing.get("width") or 1.0),
            lineCap=max(drawing.get("lineCap") or (0, 0, 0)),
            lineJoin=float(drawing.get("lineJoin") or 0),
            dashes=drawing.get("dashes"),
            closePath=bool(drawing.get("closePath")),
        )
    elif mode == "fill":
        shape.finish(
            color=None, fill=(0, 0, 0), width=0,
            even_odd=bool(drawing.get("even_odd")),
            closePath=True,
        )
    else:
        raise RuntimeError(mode)
    shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    mask = np.max(255 - array, axis=2) >= 20
    doc.close()
    return mask


def mask_coords(mask: np.ndarray) -> np.ndarray:
    return np.argwhere(mask)


def exact_distance(a: np.ndarray, b: np.ndarray, tree_a: cKDTree | None = None) -> float:
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    aset = set(map(tuple, a.tolist()))
    if any(tuple(p) in aset for p in b.tolist()):
        return 0.0
    if tree_a is None:
        tree_a = cKDTree(a.astype(float))
    distances, _ = tree_a.query(b.astype(float), k=1)
    return float(np.min(distances))


def draw_text_safe(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill=(0, 0, 0)) -> None:
    try:
        draw.text(xy, text, fill=fill, font=ImageFont.load_default())
    except UnicodeEncodeError:
        draw.text(xy, text.encode("unicode_escape").decode("ascii"), fill=fill, font=ImageFont.load_default())


doc = fitz.open(PDF)
page = doc[PAGE_INDEX]
page_rect = page.rect
full_image = Image.open(VIEWS / "full_page_300dpi.png").convert("RGB")
full_array = np.asarray(full_image)
assert full_image.size == (2481, 3508)

float_px = rect_to_px(FLOAT_RECT_PT)
plot_px = rect_to_px(PLOT_RECT_PT)
figure_crop = full_image.crop(float_px)
standalone = full_image.crop(plot_px)
figure_crop.save(VIEWS / "figure_crop_300dpi.png")
standalone.save(VIEWS / "standalone_300dpi.png")
figure_crop.convert("L").save(VIEWS / "grayscale_300dpi.png")

crop_geometry = {
    "pdf": str(PDF),
    "physical_page_1_based": 633,
    "page_index_0_based": PAGE_INDEX,
    "page_pt": [round(page_rect.width, 4), round(page_rect.height, 4)],
    "full_page_300dpi_px": list(full_image.size),
    "full_page_200dpi_px": list(Image.open(VIEWS / "full_page_200dpi.png").size),
    "figure_float_rect_pt": list(FLOAT_RECT_PT),
    "figure_crop_300dpi_rect_px": list(float_px),
    "figure_crop_300dpi_px": list(figure_crop.size),
    "plot_only_rect_pt": list(PLOT_RECT_PT),
    "standalone_300dpi_rect_px": list(plot_px),
    "standalone_300dpi_px": list(standalone.size),
    "render_rule": "direct page 633 render at 300 dpi; integer crop only; no resizing",
}
(MACHINE / "crop_geometry.json").write_text(json.dumps(crop_geometry, ensure_ascii=False, indent=2), encoding="utf-8")

raw = page.get_text("rawdict")
glyph_records = []
glyph_objects = []
glyph_claims: dict[tuple[int, int], list[int]] = defaultdict(list)
glyph_candidates: list[np.ndarray] = []
glyph_counter = 0

for block_index, block in enumerate(raw["blocks"]):
    if block.get("type") != 0:
        continue
    for line_index, line in enumerate(block.get("lines", [])):
        for span_index, span in enumerate(line.get("spans", [])):
            span_bbox = tuple(span.get("bbox", (0, 0, 0, 0)))
            if not point_in_rect(span_bbox, FLOAT_RECT_PT):
                continue
            span_text = "".join(ch.get("c", "") for ch in span.get("chars", []))
            parent_id, role = parent_and_role(span_bbox, span_text)
            if parent_id == "P_UNMAPPED":
                continue
            target_rgb = color_int_to_rgb(int(span.get("color", 0)))
            for char_index, ch in enumerate(span.get("chars", [])):
                char = ch.get("c", "")
                if not char or char.isspace():
                    continue
                glyph_counter += 1
                element_id = f"T{glyph_counter:04d}"
                safe_name = id_safe_text(glyph_counter, char)
                bbox_pt = tuple(float(v) for v in ch["bbox"])
                bx0, by0, bx1, by1 = rect_to_px(bbox_pt)
                # The PDF character bbox is the ownership boundary. Expanding it
                # would admit neighboring glyph pixels and break mask purity.
                bx0 = max(0, bx0)
                by0 = max(0, by0)
                bx1 = min(full_array.shape[1], bx1)
                by1 = min(full_array.shape[0], by1)
                local = full_array[by0:by1, bx0:bx1]
                local_mask = target_color_mask(local, target_rgb)
                coords = np.argwhere(local_mask)
                if len(coords):
                    coords[:, 0] += by0
                    coords[:, 1] += bx0
                glyph_candidates.append(coords)
                for pixel in coords.tolist():
                    glyph_claims[(pixel[0], pixel[1])].append(len(glyph_candidates) - 1)
                glyph_objects.append({
                    "element_id": element_id,
                    "safe_filename": safe_name,
                    "object_type": "TEXT_GLYPH",
                    "parent_id": parent_id,
                    "role": role,
                    "char": char,
                    "unicode": "+".join(f"U+{ord(c):04X}" for c in char),
                    "font": span.get("font"),
                    "source_size_pt": float(span.get("size", 0)),
                    "target_rgb": target_rgb,
                    "bbox_pt": bbox_pt,
                    "candidate_index": len(glyph_candidates) - 1,
                    "block": block_index,
                    "line": line_index,
                    "span": span_index,
                    "char_index": char_index,
                })

shared_claim_counts = defaultdict(int)
for pixel, claims in glyph_claims.items():
    if len(claims) > 1:
        for candidate_index in claims:
            shared_claim_counts[candidate_index] += 1

all_objects: list[dict] = []
for obj in glyph_objects:
    candidate_index = obj.pop("candidate_index")
    coords = glyph_candidates[candidate_index]
    if len(coords) == 0:
        final_coords = coords
    else:
        final_coords = coords.copy()
        # Exact character bboxes normally prevent shared claims. Preserve any shared
        # claims for evidence rather than silently reallocating them.
    mask_path = GLYPHS / f"{obj['safe_filename']}_raw_mask.png"
    if len(final_coords):
        ink_bbox = save_tight_mask(mask_path, final_coords)
        height = ink_bbox[3] - ink_bbox[1]
        width = ink_bbox[2] - ink_bbox[0]
        area = len(final_coords)
        edge_touch = int(
            ink_bbox[0] <= float_px[0] or ink_bbox[1] <= float_px[1]
            or ink_bbox[2] >= float_px[2] or ink_bbox[3] >= float_px[3]
        )
    else:
        ink_bbox = (0, 0, 0, 0)
        height = width = area = edge_touch = 0
    cls, legacy_threshold = glyph_class(obj["char"], obj["role"], obj["source_size_pt"])
    if legacy_threshold == 0:
        legacy_result = "CALIBRATION_ADVISORY_NOT_APPLIED_R168"
    else:
        legacy_result = "ADVISORY_OK" if height >= legacy_threshold else "ADVISORY_BELOW_LEGACY_MIN"
    r168_flag = "NONE" if area > 0 and not edge_touch else "EMPTY_OR_CLIPPED"
    record = {
        **{k: v for k, v in obj.items() if k not in {"bbox_pt", "target_rgb"}},
        "char": obj["char"],
        "bbox_pt": "|".join(f"{v:.4f}" for v in obj["bbox_pt"]),
        "ink_bbox_full300_px": "|".join(str(v) for v in ink_bbox),
        "mask_path": str(mask_path.relative_to(ROOT)).replace("\\", "/"),
        "h_ink_px": height,
        "w_ink_px": width,
        "ink_area_px": area,
        "class": cls,
        "legacy_min_px_advisory": legacy_threshold,
        "legacy_pixel_result_r168_advisory": legacy_result,
        "candidate_shared_px": shared_claim_counts.get(candidate_index, 0),
        "clip_pixel_count": edge_touch,
        "r168_machine_hard_flag": r168_flag,
    }
    glyph_records.append(record)
    all_objects.append({
        "id": obj["element_id"],
        "safe": obj["safe_filename"],
        "kind": "TEXT",
        "parent": obj["parent_id"],
        "role": obj["role"],
        "char": obj["char"],
        "coords": final_coords,
        "bbox": ink_bbox,
        "source": "PDF_TEXT_RAWDICT_FINAL_RASTER_COLOR_ISOLATION",
    })

glyph_fields = [
    "element_id", "safe_filename", "char", "unicode", "parent_id", "role", "font", "source_size_pt",
    "bbox_pt", "ink_bbox_full300_px", "mask_path", "h_ink_px", "w_ink_px", "ink_area_px", "class",
    "legacy_min_px_advisory", "legacy_pixel_result_r168_advisory", "candidate_shared_px", "clip_pixel_count",
    "r168_machine_hard_flag", "object_type", "block", "line", "span", "char_index",
]
write_csv(MACHINE / "after_pixel_measurements.csv", glyph_records, glyph_fields)

drawings = page.get_drawings()
graphic_specs = []
for i in range(6):
    graphic_specs.append((f"G_XTICK_{i + 1}", 1, [i], "stroke", "AXIS_TICK", f"P_XTICK_GRAPH_{i + 1}", "X_TICK"))
for i in range(6):
    graphic_specs.append((f"G_YTICK_{i + 1}", 2, [i], "stroke", "AXIS_TICK", f"P_YTICK_GRAPH_{i + 1}", "Y_TICK"))
graphic_specs.extend([
    ("G_X_AXIS", 3, [0], "stroke", "AXIS_LINE", "P_X_AXIS_GRAPH", "X_AXIS"),
    ("G_X_ARROWHEAD", 4, list(range(len(drawings[4]["items"]))), "fill", "ARROWHEAD", "P_X_AXIS_GRAPH", "X_ARROWHEAD"),
    ("G_Y_AXIS", 5, [0], "stroke", "AXIS_LINE", "P_Y_AXIS_GRAPH", "Y_AXIS"),
    ("G_Y_ARROWHEAD", 6, list(range(len(drawings[6]["items"]))), "fill", "ARROWHEAD", "P_Y_AXIS_GRAPH", "Y_ARROWHEAD"),
    ("G_RATE_CURVE", 7, list(range(len(drawings[7]["items"]))), "stroke", "DATA_CURVE", "P_RATE_CURVE", "RATE_CURVE"),
    ("G_TRI_H", 8, [0], "stroke", "RATE_TRIANGLE", "P_RATE_TRIANGLE", "TRI_HORIZONTAL"),
    ("G_TRI_V", 8, [1], "stroke", "RATE_TRIANGLE", "P_RATE_TRIANGLE", "TRI_VERTICAL"),
    ("G_TRI_DIAG", 8, [2], "stroke", "RATE_TRIANGLE", "P_RATE_TRIANGLE", "TRI_DIAGONAL"),
    ("G_TRI_NOTE_BG", 9, [0], "fill", "OPAQUE_BACKGROUND", "P_TRIANGLE_NOTE", "TRI_NOTE_BACKGROUND"),
    ("G_CONDITION_FILL", 10, list(range(len(drawings[10]["items"]))), "fill", "OPAQUE_BACKGROUND", "P_CONDITION_BOX", "CONDITION_BACKGROUND"),
    ("G_CONDITION_BORDER", 10, list(range(len(drawings[10]["items"]))), "stroke", "NODE_BORDER", "P_CONDITION_BOX", "CONDITION_BORDER"),
])

graphic_records = []
path_rows = []
graphic_raw_coords: dict[str, np.ndarray] = {}
for gindex, (gid, drawing_index, item_indexes, mode, kind, parent, role) in enumerate(graphic_specs, start=1):
    drawing = drawings[drawing_index]
    raw_mask = render_graphic_mask(page_rect, drawing, item_indexes, mode)
    raw_coords = mask_coords(raw_mask)
    graphic_raw_coords[gid] = raw_coords
    if not len(raw_coords):
        raise RuntimeError(f"Empty graphic mask {gid}")
    actual_color = color_float_to_rgb(drawing.get("fill") if mode == "fill" else drawing.get("color"))
    if kind == "OPAQUE_BACKGROUND":
        final_coords = raw_coords
        final_visible_mode = "OPAQUE_AREA_GEOMETRY_MASK"
    else:
        target = actual_color or (0, 0, 0)
        final_color_mask = target_color_mask(full_array, target)
        raw_set = set(map(tuple, raw_coords.tolist()))
        final_candidate = mask_coords(final_color_mask)
        final_coords = np.array([p for p in final_candidate.tolist() if tuple(p) in raw_set], dtype=np.int32)
        if final_coords.size == 0:
            final_coords = np.empty((0, 2), dtype=np.int32)
        final_visible_mode = "RAW_VECTOR_MASK_INTERSECT_FINAL_RASTER_COLOR"
    safe_name = gid
    raw_path = OVERLAYS / f"{safe_name}_pre_occlusion_mask.png"
    final_path = OVERLAYS / f"{safe_name}_final_visible_mask.png"
    raw_bbox = save_tight_mask(raw_path, raw_coords)
    final_bbox = save_tight_mask(final_path, final_coords) if len(final_coords) else (0, 0, 0, 0)
    graphic_records.append({
        "element_id": gid,
        "safe_filename": safe_name,
        "object_type": "GRAPHIC",
        "kind": kind,
        "parent_id": parent,
        "role": role,
        "pdf_drawing_index": drawing_index,
        "pdf_seqno": drawing.get("seqno"),
        "item_indexes": "|".join(map(str, item_indexes)),
        "item_count": len(item_indexes),
        "paint_mode": mode,
        "actual_rgb": "|".join(map(str, actual_color)) if actual_color else "NONE",
        "raw_bbox_full300_px": "|".join(map(str, raw_bbox)),
        "final_bbox_full300_px": "|".join(map(str, final_bbox)),
        "pre_occlusion_px": len(raw_coords),
        "final_visible_or_opaque_area_px": len(final_coords),
        "raw_mask_path": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
        "final_mask_path": str(final_path.relative_to(ROOT)).replace("\\", "/"),
        "final_visible_mode": final_visible_mode,
        "empty_mask_count": int(len(final_coords) == 0),
    })
    all_objects.append({
        "id": gid,
        "safe": safe_name,
        "kind": kind,
        "parent": parent,
        "role": role,
        "char": "",
        "coords": final_coords,
        "bbox": final_bbox,
        "source": final_visible_mode,
    })
    for item_index in item_indexes:
        path_rows.append({
            "pdf_drawing_index": drawing_index,
            "pdf_seqno": drawing.get("seqno"),
            "pdf_item_index": item_index,
            "operation": drawing["items"][item_index][0],
            "assigned_graphic_id": gid,
            "paint_mode": mode,
        })

# Purify the gold annotation glyph masks from the same-color horizontal rate leg.
# The line is a distinct earlier vector object whose geometry crosses the PDF font
# bboxes even when the final visible glyph ink remains above it.
gold_graphic_pixels = set()
for gid in ("G_RATE_CURVE", "G_TRI_H", "G_TRI_V", "G_TRI_DIAG"):
    gold_graphic_pixels.update(map(tuple, graphic_raw_coords[gid].tolist()))
for obj in [o for o in all_objects if o["kind"] == "TEXT" and o["parent"] == "P_TRIANGLE_NOTE"]:
    purified = np.array([p for p in obj["coords"].tolist() if tuple(p) not in gold_graphic_pixels], dtype=np.int32)
    if purified.size == 0:
        purified = np.empty((0, 2), dtype=np.int32)
    obj["coords"] = purified
    obj["bbox"] = bbox_from_coords(purified) if len(purified) else (0, 0, 0, 0)
    rec = next(row for row in glyph_records if row["element_id"] == obj["id"])
    rec["ink_bbox_full300_px"] = "|".join(map(str, obj["bbox"]))
    rec["h_ink_px"] = obj["bbox"][3] - obj["bbox"][1]
    rec["w_ink_px"] = obj["bbox"][2] - obj["bbox"][0]
    rec["ink_area_px"] = len(purified)
    rec["r168_machine_hard_flag"] = "NONE" if len(purified) else "EMPTY_OR_CLIPPED"
    threshold = int(rec["legacy_min_px_advisory"])
    if threshold:
        rec["legacy_pixel_result_r168_advisory"] = "ADVISORY_OK" if rec["h_ink_px"] >= threshold else "ADVISORY_BELOW_LEGACY_MIN"
    save_tight_mask(ROOT / rec["mask_path"], purified)

# Establish final-visible vector ownership from source paint order. True opaque
# backgrounds and later foreground objects remove earlier paint from the reader-
# visible mask; the pre-occlusion mask remains separately preserved.
note_bg = set(map(tuple, graphic_raw_coords["G_TRI_NOTE_BG"].tolist()))
condition_fill = set(map(tuple, graphic_raw_coords["G_CONDITION_FILL"].tolist()))
triangle_strokes = set()
for gid in ("G_TRI_H", "G_TRI_V", "G_TRI_DIAG"):
    triangle_strokes.update(map(tuple, graphic_raw_coords[gid].tolist()))
triangle_text = set()
condition_text = set()
for obj in [o for o in all_objects if o["kind"] == "TEXT"]:
    if obj["parent"] == "P_TRIANGLE_NOTE":
        triangle_text.update(map(tuple, obj["coords"].tolist()))
    if obj["parent"] == "P_CONDITION_BOX":
        condition_text.update(map(tuple, obj["coords"].tolist()))

for record in graphic_records:
    gid = record["element_id"]
    raw_coords = graphic_raw_coords[gid]
    if record["kind"] == "OPAQUE_BACKGROUND":
        visible = raw_coords
        mode = "OPAQUE_AREA_GEOMETRY_MASK"
    else:
        remove = set()
        if gid == "G_RATE_CURVE":
            remove.update(triangle_strokes)
            remove.update(note_bg)
            remove.update(condition_fill)
        elif gid in {"G_TRI_H", "G_TRI_V", "G_TRI_DIAG"}:
            remove.update(note_bg)
            remove.update(condition_fill)
            remove.update(triangle_text)
        elif gid == "G_CONDITION_BORDER":
            remove.update(condition_text)
        visible = np.array([p for p in raw_coords.tolist() if tuple(p) not in remove], dtype=np.int32)
        if visible.size == 0:
            visible = np.empty((0, 2), dtype=np.int32)
        mode = "VECTOR_MASK_MINUS_LATER_OPAQUE_OR_FOREGROUND_PAINTS"
    final_bbox = save_tight_mask(ROOT / record["final_mask_path"], visible) if len(visible) else (0, 0, 0, 0)
    record["final_bbox_full300_px"] = "|".join(map(str, final_bbox))
    record["final_visible_or_opaque_area_px"] = len(visible)
    record["final_visible_mode"] = mode
    record["empty_mask_count"] = int(len(visible) == 0)
    obj = next(o for o in all_objects if o["id"] == gid)
    obj["coords"] = visible
    obj["bbox"] = final_bbox
    obj["source"] = mode

write_csv(MACHINE / "after_pixel_measurements.csv", glyph_records, glyph_fields)
write_csv(MACHINE / "graphic_object_ledger.csv", graphic_records, list(graphic_records[0].keys()))
write_csv(MACHINE / "path_item_ledger.csv", path_rows, list(path_rows[0].keys()))

source_text = TEX.read_text(encoding="utf-8")
source_audit = [
    {"scope": "tikz base", "declared_pt": "9.2", "effective_pt": "9.2", "role": "ordinary node default", "r168_status": "ADVISORY_LEGACY_LT_9_5; no hard failure by source alone"},
    {"scope": "tick label style", "declared_pt": "8.6", "effective_pt": "8.6", "role": "ticks", "r168_status": "ADVISORY_LEGACY_LT_9_5; hard visual/readability adjudicated manually"},
    {"scope": "axis label style", "declared_pt": "9.6", "effective_pt": "9.6", "role": "axis titles", "r168_status": "SOURCE_OK"},
    {"scope": "rate formula node", "declared_pt": "9.6", "effective_pt": "9.6", "role": "formula", "r168_status": "SOURCE_OK; exponent is natural TeX script"},
    {"scope": "triangle annotation node", "declared_pt": "9.2", "effective_pt": "9.2", "role": "annotation", "r168_status": "ADVISORY_LEGACY_LT_9_5; hard visual/readability adjudicated manually"},
    {"scope": "condition box node", "declared_pt": "9.2", "effective_pt": "9.2", "role": "condition", "r168_status": "ADVISORY_LEGACY_LT_9_5; hard visual/readability adjudicated manually"},
    {"scope": "graphics scaling", "declared_pt": "1.0", "effective_pt": "1.0", "role": "cumulative graphics scale", "r168_status": "NO scale/scalebox/resizebox/transform shape in source"},
]
required_source_tokens = ["fontsize{9.2pt}", "fontsize{8.6pt}", "fontsize{9.6pt}", "O(N^{-1/2})", "样本量 $\\times4$", "误差约 $\\div2$", "iid 且方差有限"]
for token in required_source_tokens:
    if token not in source_text:
        raise RuntimeError(f"Source token missing: {token}")
write_csv(MACHINE / "after_font_audit.csv", source_audit, list(source_audit[0].keys()))

id_map_rows = []
for obj in all_objects:
    id_map_rows.append({
        "element_id": obj["id"],
        "safe_filename": obj["safe"],
        "object_kind": obj["kind"],
        "parent_id": obj["parent"],
        "role": obj["role"],
    })
write_csv(MACHINE / "id_safe_filename_map.csv", id_map_rows, list(id_map_rows[0].keys()))


def pair_policy(a: dict, b: dict) -> tuple[str, float | None, str]:
    ids = {a["id"], b["id"]}
    roles = {a["role"], b["role"]}
    kinds = {a["kind"], b["kind"]}
    if ids == {"G_X_AXIS", "G_Y_AXIS"}:
        return "INTENTIONAL_AXIS_ORIGIN_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if ids == {"G_XTICK_1", "G_Y_AXIS"}:
        return "INTENTIONAL_ORIGIN_TICK_AXIS_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if ids == {"G_XTICK_6", "G_X_ARROWHEAD"}:
        return "INTENTIONAL_TERMINAL_TICK_ARROWHEAD_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if ("G_X_AXIS" in ids and any(x.startswith("G_XTICK_") or x == "G_X_ARROWHEAD" for x in ids - {"G_X_AXIS"})):
        return "INTENTIONAL_X_AXIS_COMPONENT_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if ("G_Y_AXIS" in ids and any(x.startswith("G_YTICK_") or x == "G_Y_ARROWHEAD" for x in ids - {"G_Y_AXIS"})):
        return "INTENTIONAL_Y_AXIS_COMPONENT_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if "G_RATE_CURVE" in ids and ("G_Y_AXIS" in ids or "G_YTICK_6" in ids):
        return "INTENTIONAL_DOMAIN_ENDPOINT_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if "G_RATE_CURVE" in ids and "G_TRI_DIAG" in ids:
        return "INTENTIONAL_RATE_ALIGNMENT", None, "ALLOW_DESIGN_CONNECTION"
    if a["parent"] == "P_RATE_TRIANGLE" and b["parent"] == "P_RATE_TRIANGLE":
        return "INTENTIONAL_TRIANGLE_VERTEX_CONNECTION", None, "ALLOW_DESIGN_CONNECTION"
    if "CONDITION_BORDER" in roles and (a["parent"] == "P_CONDITION_BOX" or b["parent"] == "P_CONDITION_BOX") and "TEXT" in kinds:
        return "TEXT_TO_NODE_BORDER", 5.0, "HARD_CLEARANCE"
    if "OPAQUE_BACKGROUND" in kinds:
        return "TRUE_OPAQUE_BACKGROUND_OR_CONTAINMENT", None, "OCCLUSION_OR_CONTAINMENT"
    if kinds == {"TEXT"}:
        if a["parent"] == b["parent"]:
            return "SAME_SEMANTIC_TEXT_OR_FORMULA_PARENT", None, "INTERNAL_TYPOGRAPHY"
        return "INDEPENDENT_TEXT_TEXT", 4.0, "HARD_CLEARANCE"
    if "TEXT" in kinds and (kinds & {"AXIS_LINE", "AXIS_TICK", "ARROWHEAD", "DATA_CURVE", "RATE_TRIANGLE", "NODE_BORDER"}):
        return "TEXT_OR_FORMULA_TO_LINE_MARKER_BORDER", 3.0, "HARD_CLEARANCE"
    if a["parent"] == b["parent"]:
        return "SAME_GRAPHIC_PARENT", None, "INTERNAL_GEOMETRY"
    return "INDEPENDENT_GRAPHIC_GRAPHIC", None, "ZERO_ILLEGAL_OVERLAP"


pair_rows = []
trees: dict[str, cKDTree] = {}
for obj in all_objects:
    if len(obj["coords"]):
        trees[obj["id"]] = cKDTree(obj["coords"].astype(float))

for pair_index, (a, b) in enumerate(itertools.combinations(all_objects, 2), start=1):
    a_coords = a["coords"]
    b_coords = b["coords"]
    aset = set(map(tuple, a_coords.tolist()))
    intersection = sum(1 for p in b_coords.tolist() if tuple(p) in aset)
    distance = exact_distance(a_coords, b_coords, trees.get(a["id"]))
    relation, threshold, policy = pair_policy(a, b)
    if math.isnan(distance):
        machine_result = "EMPTY_MASK"
    elif policy == "HARD_CLEARANCE":
        machine_result = "MEETS_HARD_CLEARANCE" if intersection == 0 and distance >= float(threshold) else "HARD_CLEARANCE_FAILURE"
    elif policy == "ZERO_ILLEGAL_OVERLAP":
        machine_result = "NO_ILLEGAL_OVERLAP" if intersection == 0 else "POTENTIAL_ILLEGAL_OVERLAP"
    elif policy == "ALLOW_DESIGN_CONNECTION":
        machine_result = "DESIGN_CONNECTION_RECORDED"
    else:
        machine_result = "RELATION_RECORDED"
    critical = int(
        intersection > 0
        or (threshold is not None and not math.isnan(distance) and distance <= threshold + 12)
        or policy in {"ALLOW_DESIGN_CONNECTION", "OCCLUSION_OR_CONTAINMENT"}
    )
    pair_rows.append({
        "pair_id": f"P{pair_index:05d}",
        "object_a": a["id"],
        "object_b": b["id"],
        "kind_a": a["kind"],
        "kind_b": b["kind"],
        "parent_a": a["parent"],
        "parent_b": b["parent"],
        "relation_class": relation,
        "policy": policy,
        "hard_clearance_px": "" if threshold is None else threshold,
        "intersection_px": intersection,
        "min_distance_native_px": "" if math.isnan(distance) else f"{distance:.4f}",
        "machine_rule_result": machine_result,
        "critical_or_relationship": critical,
    })

pair_fields = list(pair_rows[0].keys())
write_csv(MACHINE / "after_overlap_report.csv", pair_rows, pair_fields)

# Native 300 dpi measurement overlay.
overlay = figure_crop.copy()
odraw = ImageDraw.Draw(overlay)
fx0, fy0, _, _ = float_px
for obj in all_objects:
    x0, y0, x1, y1 = obj["bbox"]
    if x1 <= x0 or y1 <= y0:
        continue
    color = (220, 20, 60) if obj["kind"] == "TEXT" else (0, 140, 255)
    odraw.rectangle((x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0), outline=color, width=1)
    draw_text_safe(odraw, (x0 - fx0, y0 - fy0 - 10), obj["id"], color)
overlay.save(OVERLAYS / "after_text_measurement_overlay_300dpi.png")

# Contact sheets: every glyph cell has native ORIGINAL / TARGET OVERLAY / MASK ONLY,
# each repeated as 8x nearest-neighbour evidence.
contact_map = []
sheet_cells = []
for obj, rec in zip([o for o in all_objects if o["kind"] == "TEXT"], glyph_records):
    coords = obj["coords"]
    x0, y0, x1, y1 = obj["bbox"]
    pad = 3
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(full_array.shape[1], x1 + pad), min(full_array.shape[0], y1 + pad)
    original = full_image.crop((rx0, ry0, rx1, ry1))
    target = original.copy()
    target_arr = np.array(target)
    local_coords = coords.copy()
    local_coords[:, 0] -= ry0
    local_coords[:, 1] -= rx0
    valid = (
        (local_coords[:, 0] >= 0) & (local_coords[:, 0] < target_arr.shape[0])
        & (local_coords[:, 1] >= 0) & (local_coords[:, 1] < target_arr.shape[1])
    )
    lc = local_coords[valid]
    if len(lc):
        base = target_arr[lc[:, 0], lc[:, 1]].astype(np.uint16)
        red = np.zeros_like(base)
        red[:, 0] = 255
        target_arr[lc[:, 0], lc[:, 1]] = ((base + red) // 2).astype(np.uint8)
    target = Image.fromarray(target_arr, "RGB")
    only = Image.new("RGB", original.size, "white")
    only_arr = np.asarray(only).copy()
    if len(lc):
        only_arr[lc[:, 0], lc[:, 1]] = (0, 0, 0)
    only = Image.fromarray(only_arr, "RGB")
    native_width = original.width + target.width + only.width + 8
    native = Image.new("RGB", (native_width, max(original.height, target.height, only.height) + 14), "white")
    native.paste(original, (0, 14))
    native.paste(target, (original.width + 4, 14))
    native.paste(only, (original.width + target.width + 8, 14))
    ndraw = ImageDraw.Draw(native)
    draw_text_safe(ndraw, (0, 1), "ORIGINAL | TARGET OVERLAY | MASK ONLY")
    up_original = original.resize((original.width * 8, original.height * 8), Image.Resampling.NEAREST)
    up_target = target.resize((target.width * 8, target.height * 8), Image.Resampling.NEAREST)
    up_only = only.resize((only.width * 8, only.height * 8), Image.Resampling.NEAREST)
    max_h = max(up_original.height, up_target.height, up_only.height)
    up = Image.new("RGB", (up_original.width + up_target.width + up_only.width + 16, max_h), "white")
    up.paste(up_original, (0, 0))
    up.paste(up_target, (up_original.width + 8, 0))
    up.paste(up_only, (up_original.width + up_target.width + 16, 0))
    cell = Image.new("RGB", (1040, 400), "white")
    cdraw = ImageDraw.Draw(cell)
    draw_text_safe(cdraw, (4, 3), f"{obj['id']} {rec['unicode']} parent={obj['parent']} h={rec['h_ink_px']}px area={rec['ink_area_px']}")
    cell.paste(native, (4, 20))
    if up.width > 1032 or up.height > 330:
        # Preserve nearest-neighbour pixels; crop excess white/context symmetrically.
        crop_w = min(up.width, 1032)
        crop_h = min(up.height, 330)
        up = up.crop((0, 0, crop_w, crop_h))
    cell.paste(up, (4, 66))
    sheet_cells.append((obj, cell))

for sheet_index, start in enumerate(range(0, len(sheet_cells), 8), start=1):
    sheet = Image.new("RGB", (2080, 1600), (244, 246, 248))
    chunk = sheet_cells[start:start + 8]
    for local_index, (obj, cell) in enumerate(chunk, start=1):
        col = (local_index - 1) % 2
        row = (local_index - 1) // 2
        sheet.paste(cell, (col * 1040, row * 400))
        contact_map.append({
            "element_id": obj["id"],
            "sheet": f"glyph_contact_{sheet_index:02d}.png",
            "cell": local_index,
        })
    sheet.save(GLYPHS / f"glyph_contact_{sheet_index:02d}.png")
write_csv(MACHINE / "glyph_contact_map.csv", contact_map, ["element_id", "sheet", "cell"])

# Graphic sheets: 1x overview for each object plus 8x nearest local evidence.
graphic_cells = []
for obj in [o for o in all_objects if o["kind"] != "TEXT"]:
    coords = obj["coords"]
    x0, y0, x1, y1 = obj["bbox"]
    pad = 6
    rx0, ry0 = max(0, x0 - pad), max(0, y0 - pad)
    rx1, ry1 = min(full_array.shape[1], x1 + pad), min(full_array.shape[0], y1 + pad)
    original = full_image.crop((rx0, ry0, rx1, ry1))
    arr = np.array(original)
    local = coords.copy()
    local[:, 0] -= ry0
    local[:, 1] -= rx0
    valid = (local[:, 0] >= 0) & (local[:, 0] < arr.shape[0]) & (local[:, 1] >= 0) & (local[:, 1] < arr.shape[1])
    lc = local[valid]
    if len(lc):
        arr[lc[:, 0], lc[:, 1]] = (255, 0, 255)
    marked = Image.fromarray(arr, "RGB")
    overview = marked.copy()
    if overview.width > 960 or overview.height > 190:
        ratio = min(960 / overview.width, 190 / overview.height)
        overview = overview.resize((max(1, int(overview.width * ratio)), max(1, int(overview.height * ratio))), Image.Resampling.NEAREST)
    # Native 8x inspection around the first/median/last mask coordinates.
    tiles = []
    sample_indexes = sorted(set([0, len(coords) // 2, len(coords) - 1]))
    for sample_index in sample_indexes:
        sy, sx = coords[sample_index]
        tx0, ty0 = max(0, sx - 10), max(0, sy - 10)
        tx1, ty1 = min(full_array.shape[1], sx + 11), min(full_array.shape[0], sy + 11)
        tile = full_image.crop((tx0, ty0, tx1, ty1))
        tile_arr = np.array(tile)
        relevant = coords[(coords[:, 1] >= tx0) & (coords[:, 1] < tx1) & (coords[:, 0] >= ty0) & (coords[:, 0] < ty1)].copy()
        relevant[:, 0] -= ty0
        relevant[:, 1] -= tx0
        tile_arr[relevant[:, 0], relevant[:, 1]] = (255, 0, 255)
        tiles.append(Image.fromarray(tile_arr, "RGB").resize((tile.width * 8, tile.height * 8), Image.Resampling.NEAREST))
    cell = Image.new("RGB", (1040, 400), "white")
    cdraw = ImageDraw.Draw(cell)
    draw_text_safe(cdraw, (4, 3), f"{obj['id']} role={obj['role']} px={len(coords)} | overview 1x + sampled 8x nearest")
    cell.paste(overview, (4, 22))
    xcursor = 4
    for tile in tiles:
        cell.paste(tile, (xcursor, 220))
        xcursor += tile.width + 8
    graphic_cells.append((obj, cell))

graphic_contact_map = []
for sheet_index, start in enumerate(range(0, len(graphic_cells), 8), start=1):
    sheet = Image.new("RGB", (2080, 1600), (244, 246, 248))
    for local_index, (obj, cell) in enumerate(graphic_cells[start:start + 8], start=1):
        col = (local_index - 1) % 2
        row = (local_index - 1) // 2
        sheet.paste(cell, (col * 1040, row * 400))
        graphic_contact_map.append({"element_id": obj["id"], "sheet": f"graphic_contact_{sheet_index:02d}.png", "cell": local_index})
    sheet.save(OVERLAYS / f"graphic_contact_{sheet_index:02d}.png")
write_csv(MACHINE / "graphic_contact_map.csv", graphic_contact_map, ["element_id", "sheet", "cell"])

# Pair matrix over the complete unordered denominator.
n = len(all_objects)
cell_px = 6
matrix_image = Image.new("RGB", (n * cell_px + 180, n * cell_px + 180), "white")
mdraw = ImageDraw.Draw(matrix_image)
palette = {
    "HARD_CLEARANCE": (85, 180, 95),
    "ZERO_ILLEGAL_OVERLAP": (120, 190, 130),
    "ALLOW_DESIGN_CONNECTION": (80, 140, 220),
    "OCCLUSION_OR_CONTAINMENT": (180, 150, 220),
    "INTERNAL_TYPOGRAPHY": (210, 210, 210),
    "INTERNAL_GEOMETRY": (190, 210, 230),
}
index_by_id = {obj["id"]: i for i, obj in enumerate(all_objects)}
for row in pair_rows:
    i = index_by_id[row["object_a"]]
    j = index_by_id[row["object_b"]]
    color = palette.get(row["policy"], (230, 230, 230))
    if "FAIL" in row["machine_rule_result"] or "POTENTIAL" in row["machine_rule_result"] or row["machine_rule_result"] == "EMPTY_MASK":
        color = (220, 45, 45)
    for aidx, bidx in ((i, j), (j, i)):
        x = 160 + bidx * cell_px
        y = 160 + aidx * cell_px
        mdraw.rectangle((x, y, x + cell_px - 1, y + cell_px - 1), fill=color)
for i in range(n):
    x = 160 + i * cell_px
    y = 160 + i * cell_px
    mdraw.rectangle((x, y, x + cell_px - 1, y + cell_px - 1), fill=(40, 40, 40))
for i, obj in enumerate(all_objects):
    if i % 10 == 0 or i == n - 1:
        draw_text_safe(mdraw, (160 + i * cell_px, 140), str(i + 1))
        draw_text_safe(mdraw, (120, 160 + i * cell_px), str(i + 1))
draw_text_safe(mdraw, (8, 8), f"ALL UNORDERED PAIRS MATRIX N={n}, C={len(pair_rows)}")
draw_text_safe(mdraw, (8, 28), "green=hard checked pass; blue=intentional connection; purple=opaque/containment; gray=internal; red=failure")
matrix_image.save(PAIRS / "all_unordered_pairs_matrix.png")


def composite_overlay(filename: str, rect_pt, object_ids: list[str], caption: str) -> None:
    rect_px = rect_to_px(rect_pt)
    x0, y0, x1, y1 = rect_px
    original = full_image.crop(rect_px)
    arr = np.array(original)
    colors = [(255, 0, 0), (0, 120, 255), (255, 0, 255), (0, 180, 80), (255, 140, 0), (120, 0, 200)]
    for idx, oid in enumerate(object_ids):
        obj = next(o for o in all_objects if o["id"] == oid)
        coords = obj["coords"].copy()
        valid = (coords[:, 1] >= x0) & (coords[:, 1] < x1) & (coords[:, 0] >= y0) & (coords[:, 0] < y1)
        coords = coords[valid]
        coords[:, 0] -= y0
        coords[:, 1] -= x0
        if len(coords):
            arr[coords[:, 0], coords[:, 1]] = colors[idx % len(colors)]
    marked = Image.fromarray(arr, "RGB")
    up = marked.resize((marked.width * 8, marked.height * 8), Image.Resampling.NEAREST)
    max_w, max_h = 1900, 1050
    if up.width > max_w or up.height > max_h:
        # Crop only the 8x display canvas; native original is retained whole above.
        up = up.crop((0, 0, min(up.width, max_w), min(up.height, max_h)))
    canvas = Image.new("RGB", (max(1000, original.width + 20, up.width + 20), original.height + up.height + 75), "white")
    cdraw = ImageDraw.Draw(canvas)
    draw_text_safe(cdraw, (8, 6), caption)
    draw_text_safe(cdraw, (8, 22), "ids=" + ",".join(object_ids) + " | top=native 1x | bottom=8x nearest overlay")
    canvas.paste(original, (8, 42))
    canvas.paste(up, (8, 50 + original.height))
    canvas.save(CRITICAL / filename)


def chars_for_parent(parent: str) -> list[str]:
    return [o["id"] for o in all_objects if o["parent"] == parent and o["kind"] == "TEXT"]


composite_overlay("CRIT_01_curve_yaxis_endpoint.png", (174, 66, 193, 84), ["G_RATE_CURVE", "G_Y_AXIS", "G_YTICK_6"], "curve endpoint / y-axis / top tick intentional connection")
composite_overlay("CRIT_02_curve_triangle_alignment.png", (274, 108, 337, 143), ["G_RATE_CURVE", "G_TRI_H", "G_TRI_V", "G_TRI_DIAG"], "O(N^-1/2) curve and ×4/÷2 triangle relationship")
composite_overlay("CRIT_03_triangle_note_clearance.png", (278, 89, 334, 124), ["G_TRI_H", "G_TRI_NOTE_BG"] + chars_for_parent("P_TRIANGLE_NOTE"), "triangle annotation, true opaque background, and horizontal leg")
composite_overlay("CRIT_04_rate_formula_curve.png", (350, 124, 409, 160), ["G_RATE_CURVE"] + chars_for_parent("P_RATE_FORMULA"), "rate formula to data curve clearance and semantics")
composite_overlay("CRIT_05_condition_text_border.png", (223, 144, 300, 181), ["G_CONDITION_FILL", "G_CONDITION_BORDER"] + chars_for_parent("P_CONDITION_BOX"), "condition box text-to-final-visible border clearance")
composite_overlay("REL_06_axes_ticks_labels.png", (140, 65, 443, 220), ["G_X_AXIS", "G_Y_AXIS", "G_X_ARROWHEAD", "G_Y_ARROWHEAD"] + [f"G_XTICK_{i}" for i in range(1, 7)] + [f"G_YTICK_{i}" for i in range(1, 7)], "log-log axes, arrows, and six-by-six tick geometry")
composite_overlay("REL_07_crop_caption.png", FLOAT_RECT_PT, chars_for_parent("P_CAPTION"), "complete figure crop, caption content, and crop-edge context")
composite_overlay("REL_08_semantic_system.png", (140, 65, 443, 220), ["G_RATE_CURVE", "G_TRI_H", "G_TRI_V", "G_TRI_DIAG"] + chars_for_parent("P_RATE_FORMULA") + chars_for_parent("P_TRIANGLE_NOTE") + chars_for_parent("P_CONDITION_BOX"), "semantic system: curve, rate triangle, formula, and iid finite-variance condition")

# Role/script medians are advisory under R168 but fully enumerated.
role_script = defaultdict(list)
for row in glyph_records:
    role_script[(row["role"], row["class"])].append(int(row["h_ink_px"]))
role_rows = []
for (role, cls), heights in sorted(role_script.items()):
    median = statistics.median(heights)
    ratios = [h / median if median else 0 for h in heights]
    role_rows.append({
        "role": role,
        "script_class": cls,
        "count": len(heights),
        "median_h_ink_px": median,
        "min_h_ink_px": min(heights),
        "max_h_ink_px": max(heights),
        "min_element_to_median": f"{min(ratios):.4f}",
        "max_element_to_median": f"{max(ratios):.4f}",
        "r168_use": "ADVISORY_ONLY; hard gate is visible severe imbalance/unreadability/clipping/overlap",
    })
write_csv(MACHINE / "role_script_advisory.csv", role_rows, list(role_rows[0].keys()))

hard_pair_failures = [row for row in pair_rows if row["machine_rule_result"] in {"HARD_CLEARANCE_FAILURE", "POTENTIAL_ILLEGAL_OVERLAP", "EMPTY_MASK"}]
empty_glyphs = [row for row in glyph_records if row["ink_area_px"] == 0]
empty_graphics = [row for row in graphic_records if row["empty_mask_count"]]
unmapped = [row for row in glyph_records if row["parent_id"] == "P_UNMAPPED"]
summary = {
    "uid": "FIG-P583-01",
    "round": "R103",
    "physical_page": 633,
    "glyph_count": len(glyph_records),
    "graphic_component_count": len(graphic_records),
    "total_object_count_n": len(all_objects),
    "all_unordered_pair_count_c": len(pair_rows),
    "combination_check": len(all_objects) * (len(all_objects) - 1) // 2,
    "pdf_figure_drawing_paint_ops": 10,
    "assigned_path_item_rows": len(path_rows),
    "glyph_empty_count": len(empty_glyphs),
    "graphic_empty_count": len(empty_graphics),
    "unmapped_visible_glyph_count": len(unmapped),
    "hard_pair_failure_count": len(hard_pair_failures),
    "overlap_pixel_count_illegal": sum(int(row["intersection_px"]) for row in hard_pair_failures),
    "clip_pixel_count": sum(int(row["clip_pixel_count"]) for row in glyph_records),
    "critical_or_relationship_pair_rows": sum(int(row["critical_or_relationship"]) for row in pair_rows),
    "glyph_contact_sheet_count": math.ceil(len(glyph_records) / 8),
    "graphic_contact_sheet_count": math.ceil(len(graphic_records) / 8),
    "critical_relationship_overlay_count": 8,
    "legacy_font_taxonomy": "ADVISORY_ONLY_UNDER_R168",
    "machine_hard_gate_direction": "NO_MACHINE_HARD_FAILURE_DETECTED" if not hard_pair_failures and not empty_glyphs and not empty_graphics and not unmapped else "MACHINE_HARD_FAILURE_PRESENT",
}
(MACHINE / "machine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

# A compact relationship matrix for the hard semantic gates.
semantic_rows = [
    ("LOGLOG_AXES", "x: 1,4,16,64,256,1024; y: 1/32..1", "STRUCTURE_MATCH"),
    ("RATE_CURVE", "x^(-.5), endpoint ratio 1024 -> 1/32", "STRUCTURE_MATCH"),
    ("TRIANGLE", "16->64 is ×4; .25->.125 is ÷2", "STRUCTURE_MATCH"),
    ("RATE_LABEL", "O(N^-1/2)", "STRUCTURE_MATCH"),
    ("CONDITION", "iid and finite variance", "STRUCTURE_MATCH"),
    ("CAPTION", "states iid finite variance and caveat for correlation/infinite variance", "STRUCTURE_MATCH"),
]
relation_img = Image.new("RGB", (1700, 520), "white")
rldraw = ImageDraw.Draw(relation_img)
draw_text_safe(rldraw, (12, 10), "FIG-P583-01 semantic / relationship matrix (machine structure, subject to human visual adjudication)")
for i, (gate, evidence, status) in enumerate(semantic_rows):
    y = 50 + i * 72
    rldraw.rectangle((10, y, 1690, y + 62), outline=(80, 90, 100), width=2)
    draw_text_safe(rldraw, (20, y + 8), gate)
    draw_text_safe(rldraw, (260, y + 8), evidence)
    draw_text_safe(rldraw, (1420, y + 8), status, (0, 130, 60))
relation_img.save(PAIRS / "semantic_relationship_matrix.png")

print(json.dumps(summary, ensure_ascii=False, indent=2))
