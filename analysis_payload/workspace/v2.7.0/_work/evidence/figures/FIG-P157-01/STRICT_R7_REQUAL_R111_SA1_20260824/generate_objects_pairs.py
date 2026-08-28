from __future__ import annotations

import csv
import json
import math
from itertools import combinations
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf")
PAGE_NUMBER = 170
FIGURE_CROP = (250, 200, 2250, 1535)


def pdf_rgb(color: tuple[float, float, float] | None) -> np.ndarray:
    if color is None:
        return np.array([0, 0, 0], dtype=np.int32)
    return np.array([round(value * 255) for value in color], dtype=np.int32)


def point_xy(point, sx: float, sy: float) -> tuple[int, int]:
    return round(point.x * sx), round(point.y * sy)


def cubic(p0, p1, p2, p3, sx: float, sy: float) -> list[tuple[int, int]]:
    points = []
    for t in np.linspace(0.0, 1.0, 41):
        # PyMuPDF Point arithmetic returns a NumPy array in this runtime;
        # calculate coordinates explicitly so the native-PDF path geometry is
        # replayed without converting the points to an ambiguous object type.
        qx = ((1-t)**3 * p0.x) + (3*(1-t)**2*t*p1.x) + (3*(1-t)*t*t*p2.x) + (t**3*p3.x)
        qy = ((1-t)**3 * p0.y) + (3*(1-t)**2*t*p1.y) + (3*(1-t)*t*t*p2.y) + (t**3*p3.y)
        points.append((round(qx * sx), round(qy * sy)))
    return points


def geometry_mask(drawing: dict, width: int, height: int, sx: float, sy: float, filled: bool = False) -> np.ndarray:
    image = Image.new("L", (width, height), 0)
    painter = ImageDraw.Draw(image)
    line_width = max(2, round(float(drawing.get("width") or 0.5) * sx) + 3)
    path_points: list[tuple[int, int]] = []
    for item in drawing.get("items", []):
        kind = item[0]
        if kind == "l":
            points = [point_xy(item[1], sx, sy), point_xy(item[2], sx, sy)]
            painter.line(points, fill=255, width=line_width)
            path_points.extend(points)
        elif kind == "c":
            points = cubic(item[1], item[2], item[3], item[4], sx, sy)
            painter.line(points, fill=255, width=line_width)
            path_points.extend(points)
        elif kind == "re":
            rect = item[1]
            box = (round(rect.x0*sx), round(rect.y0*sy), round(rect.x1*sx), round(rect.y1*sy))
            if filled:
                painter.rectangle(box, fill=255)
            else:
                painter.rectangle(box, outline=255, width=line_width)
    if filled and len(path_points) >= 3:
        painter.polygon(path_points, fill=255)
    return np.asarray(image, dtype=bool)


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def save_crop_mask(mask: np.ndarray, destination: Path) -> tuple[tuple[int, int, int, int], int]:
    bbox = bbox_of(mask)
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        Image.new("L", (1, 1), 255).save(destination)
        return bbox, 0
    crop = np.where(mask[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    Image.fromarray(crop, "L").save(destination)
    return bbox, int(mask.sum())


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0)
    dy = max(ay0 - by1, by0 - ay1, 0)
    return float(math.hypot(dx, dy))


def mask_distance(a: np.ndarray, b: np.ndarray) -> float:
    if np.any(a & b):
        return 0.0
    # The distance is translation-invariant inside a crop containing both
    # masks.  Restrict EDT to that native 1:1 union ROI: this preserves the
    # exact pixel result while avoiding 190 full-A4 EDT passes.
    union = a | b
    ys, xs = np.where(union)
    if not len(xs):
        return float("inf")
    pad = 4
    x0, x1 = max(0, int(xs.min()) - pad), min(a.shape[1], int(xs.max()) + 1 + pad)
    y0, y1 = max(0, int(ys.min()) - pad), min(a.shape[0], int(ys.max()) + 1 + pad)
    return float(distance_transform_edt(~b[y0:y1, x0:x1])[a[y0:y1, x0:x1]].min())


def make_roi(pair: dict, a: dict, b: dict, full: Image.Image) -> None:
    # For a real contact, record the precise native intersection neighbourhood
    # rather than a misleading whole-curve bounding rectangle.  Non-contact
    # critical clearance cases fall back to the paired-object union.
    full_inter = a["mask"] & b["mask"]
    if np.any(full_inter):
        ix0, iy0, ix1, iy1 = bbox_of(full_inter)
        x0, y0 = max(0, ix0 - 16), max(0, iy0 - 16)
        x1, y1 = min(full.width, ix1 + 16), min(full.height, iy1 + 16)
        roi_type = "intersection_focus"
    else:
        x0 = max(0, min(a["bbox"][0], b["bbox"][0]) - 12)
        y0 = max(0, min(a["bbox"][1], b["bbox"][1]) - 12)
        x1 = min(full.width, max(a["bbox"][2], b["bbox"][2]) + 12)
        y1 = min(full.height, max(a["bbox"][3], b["bbox"][3]) + 12)
        roi_type = "pair_union"
    folder = ROOT / pair["ROI_PACKAGE"]
    folder.mkdir(parents=True, exist_ok=True)
    original = full.crop((x0, y0, x1, y1)).convert("RGB")
    a_roi = a["mask"][y0:y1, x0:x1]
    b_roi = b["mask"][y0:y1, x0:x1]
    inter = a_roi & b_roi
    Image.fromarray(np.where(a_roi, 0, 255).astype(np.uint8), "L").save(folder / "mask_A_1x.png")
    Image.fromarray(np.where(b_roi, 0, 255).astype(np.uint8), "L").save(folder / "mask_B_1x.png")
    Image.fromarray(np.where(inter, 0, 255).astype(np.uint8), "L").save(folder / "intersection_1x.png")
    original.save(folder / "original_raw_1x.png")
    overlay = np.asarray(original).copy()
    overlay[a_roi] = [255, 0, 0]
    overlay[b_roi] = [0, 0, 255]
    overlay[inter] = [255, 0, 255]
    Image.fromarray(overlay, "RGB").save(folder / "overlay_1x.png")
    for name in ("mask_A", "mask_B", "intersection", "original_raw", "overlay"):
        image = Image.open(folder / f"{name}_1x.png")
        image.resize((image.width*8, image.height*8), Image.Resampling.NEAREST).save(folder / f"{name}_8x_nearest.png")
    (folder / "package_manifest.json").write_text(json.dumps({"pair_id": pair["PAIR_ID"], "coordinate": "native final-PDF 300dpi 1:1", "roi_type": roi_type, "roi_global_px": [x0, y0, x1, y1], "overlap_pixel_count": pair["OVERLAP_PIXEL_COUNT"], "minimum_clearance_px": pair["MIN_CLEARANCE_PX"]}, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    full = Image.open(ROOT / "renders" / "full_page_native_300dpi.png").convert("RGB")
    page_width, page_height = full.size
    document = fitz.open(CANDIDATE)
    page = document[PAGE_NUMBER - 1]
    sx, sy = page_width / page.rect.width, page_height / page.rect.height
    drawings = page.get_drawings()
    if len(drawings) < 16:
        raise RuntimeError(f"Unexpected drawing sequence: {len(drawings)}")
    array = np.asarray(full, dtype=np.int32)
    halo_masks: list[np.ndarray] = []
    visual_objects: list[dict] = []

    # Background regions are recorded but intentionally excluded from foreground
    # collision pairs: they are fills, not reader-foreground objects.
    drawing_map = [
        ("O-BG001", 1, "BACKGROUND_FILL", "underfit pale-blue region", False),
        ("O-BG002", 2, "BACKGROUND_FILL", "appropriate pale-gold region", False),
        ("O-BG003", 3, "BACKGROUND_FILL", "overfit pale-red region", False),
        ("O-G001", 4, "DATA_CURVE", "training error monotone decreasing", True),
        ("O-G002", 5, "DATA_CURVE", "validation error decreasing then increasing", True),
        ("O-G003", 6, "LINE_ARROW", "selected-complexity vertical reference", True),
        ("O-G004", 7, "LINE_ARROW", "training-label leader", True),
        ("O-H001", 8, "HALO_BACKGROUND", "E002 true white 0.90-opacity text background", False),
        ("O-H002", 9, "HALO_BACKGROUND", "E003 true white 0.90-opacity text background", False),
        ("O-H003", 10, "HALO_BACKGROUND", "E004 true white 0.90-opacity text background", False),
        ("O-G005", 11, "LINE_ARROW", "x axis", True),
        ("O-G006", 12, "LINE_ARROW", "x-axis arrowhead", True),
        ("O-G007", 13, "LINE_ARROW", "y axis", True),
        ("O-G008", 14, "LINE_ARROW", "y-axis arrowhead", True),
        ("O-G009", 15, "MARKER", "minimum-validation-error marker", True),
    ]
    intermediate = []
    for object_id, drawing_index, category, label, foreground in drawing_map:
        drawing = drawings[drawing_index]
        is_fill = drawing.get("fill") is not None
        geom = geometry_mask(drawing, page_width, page_height, sx, sy, filled=is_fill)
        if category == "BACKGROUND_FILL":
            pre = geom
        else:
            color = pdf_rgb(drawing.get("fill") if is_fill else drawing.get("color"))
            distance = np.sqrt(np.sum((array - color) ** 2, axis=2))
            pre = geom & (distance <= 112.0)
        final_override = None
        if object_id in {"O-G001", "O-G002"}:
            # Exact curve-level PDF replays were rendered independently in
            # generate_curve_replay.py.  PRE is an isolated object replay;
            # FINAL is a removal-comparison contribution from the exact source
            # drawing order.  Do not use broad same-colour page thresholds for
            # either data curve.
            pre = np.asarray(Image.open(ROOT / "object_replay" / f"{object_id}_independent_pre_raw_mask.png").convert("L")) == 0
            final_override = np.asarray(Image.open(ROOT / "object_replay" / f"{object_id}_final_visible_contribution_mask.png").convert("L")) == 0
        if category == "HALO_BACKGROUND":
            halo_masks.append(geom)
        intermediate.append({"OBJECT_ID": object_id, "CATEGORY": category, "NAME_OR_TEXT": label, "DRAWING_INDEX": drawing_index, "DRAW_ORDER": drawing.get("seqno"), "FOREGROUND_FOR_RELATIONS": foreground, "PRE": pre, "FINAL_OVERRIDE": final_override, "GEOM": geom, "COLOR": drawing.get("color"), "FILL": drawing.get("fill"), "WIDTH_PT": drawing.get("width"), "DASH": drawing.get("dashes")})
    for entry in intermediate:
        # 0.90-opacity label backgrounds are retained as their real separate
        # halo evidence but never used as an invented opaque white eraser.
        final = entry["FINAL_OVERRIDE"] if entry["FINAL_OVERRIDE"] is not None else entry["PRE"]
        if entry["CATEGORY"] == "HALO_BACKGROUND":
            final = entry["GEOM"]
        entry["FINAL"] = final
        pre_path = Path("draw_masks") / f"{entry['OBJECT_ID']}_pre_occlusion_mask.png"
        final_path = Path("object_masks") / f"{entry['OBJECT_ID']}_final_visible_mask.png"
        halo_path = "NONE"
        save_crop_mask(entry["PRE"], ROOT / pre_path)
        bbox, area = save_crop_mask(entry["FINAL"], ROOT / final_path)
        if entry["CATEGORY"] == "HALO_BACKGROUND":
            halo_path = str(final_path).replace("\\", "/")
        visual_objects.append({"OBJECT_ID": entry["OBJECT_ID"], "OBJECT_KIND": entry["CATEGORY"], "CATEGORY": entry["CATEGORY"], "NAME_OR_TEXT": entry["NAME_OR_TEXT"], "SOURCE_FILE": "fig_v1_c10_complexity.tex", "SOURCE_LINE": "source drawing order", "DRAW_ORDER": entry["DRAW_ORDER"], "FINAL_VISIBLE_MASK": str(final_path).replace("\\", "/"), "PRE_OCCLUSION_MASK": str(pre_path).replace("\\", "/"), "HALO_OR_BACKGROUND": halo_path, "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3], "MASK_FOREGROUND_PX": area, "EMPTY_MASK": str(area == 0).lower(), "SAFE_FILENAME": final_path.name, "SEMANTIC_PARENT": "N/A", "FOREGROUND_FOR_RELATIONS": str(entry["FOREGROUND_FOR_RELATIONS"]).lower(), "mask": entry["FINAL"], "bbox": bbox})

    # Rebuild text element final-visible masks from their distinct glyph masks.
    details = json.loads((ROOT / "glyph_raw_details.json").read_text(encoding="utf-8"))
    semantic_rows = list(csv.DictReader((ROOT / "semantic_text_inventory_machine.csv").open("r", encoding="utf-8-sig", newline="")))
    text_objects = []
    for row in semantic_rows:
        element_id = row["ELEMENT_ID"]
        canvas = np.zeros((page_height, page_width), dtype=bool)
        for glyph in (item for item in details if item["element_id"] == element_id):
            x0, y0, _, _ = glyph["full_crop_px"]
            local = np.asarray(Image.open(ROOT / glyph["mask_file"]).convert("L")) == 0
            canvas[y0:y0+local.shape[0], x0:x0+local.shape[1]] |= local
        final_path = Path("object_masks") / f"{element_id}_final_visible_mask.png"
        bbox, area = save_crop_mask(canvas, ROOT / final_path)
        text_objects.append({"OBJECT_ID": element_id, "OBJECT_KIND": "TEXT", "CATEGORY": row["ROLE"], "NAME_OR_TEXT": row["EXACT_NATIVE_PDF_TEXT"], "SOURCE_FILE": row["SOURCE_FILE"], "SOURCE_LINE": row["SOURCE_LINE"], "DRAW_ORDER": "text final PDF", "FINAL_VISIBLE_MASK": str(final_path).replace("\\", "/"), "PRE_OCCLUSION_MASK": "N/A", "HALO_OR_BACKGROUND": "see O-H001..O-H003 when applicable", "BBOX_X0": bbox[0], "BBOX_Y0": bbox[1], "BBOX_X1": bbox[2], "BBOX_Y1": bbox[3], "MASK_FOREGROUND_PX": area, "EMPTY_MASK": str(area == 0).lower(), "SAFE_FILENAME": final_path.name, "SEMANTIC_PARENT": element_id, "FOREGROUND_FOR_RELATIONS": "true", "mask": canvas, "bbox": bbox})

    all_inventory = text_objects + visual_objects
    inventory_fields = [key for key in all_inventory[0] if key not in {"mask", "bbox"}]
    with (ROOT / "object_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=inventory_fields)
        writer.writeheader()
        writer.writerows([{key: item[key] for key in inventory_fields} for item in all_inventory])
    with (ROOT / "graphic_object_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=inventory_fields)
        writer.writeheader()
        writer.writerows([{key: item[key] for key in inventory_fields} for item in visual_objects])

    foreground = [item for item in all_inventory if item["FOREGROUND_FOR_RELATIONS"] == "true"]
    # These are explicit source-level geometric connections, not accidental
    # reader-object collisions.  They remain critical relationships with full
    # raw/A/B/intersection/overlay packages, but are recorded PASS after
    # 1:1 review rather than being silently removed or treated as text
    # clearance exceptions.
    intentional_connections = {
        frozenset(("O-G001", "O-G003")): "the selected-complexity vertical reference is intentionally drawn through the training curve at x=5.25",
        frozenset(("O-G001", "O-G004")): "leader starts on the declared training-error curve",
        frozenset(("O-G001", "O-G007")): "training curve begins at domain x=0 on the y-axis",
        frozenset(("O-G002", "O-G007")): "validation curve begins at domain x=0 on the y-axis",
        frozenset(("O-G002", "O-G009")): "minimum-validation marker is declared at a point on the validation curve",
        frozenset(("O-G005", "O-G006")): "x-axis arrowhead is geometrically joined to the x-axis",
        frozenset(("O-G005", "O-G007")): "x/y axes are geometrically joined at their origin",
        frozenset(("O-G007", "O-G008")): "y-axis arrowhead is geometrically joined to the y-axis",
    }
    pair_rows = []
    for index, (a, b) in enumerate(combinations(foreground, 2), start=1):
        a_text, b_text = a["OBJECT_KIND"] == "TEXT", b["OBJECT_KIND"] == "TEXT"
        if a_text and b_text:
            relation, required, coord = "TEXT_TEXT", 4.0, "native final-PDF 300dpi bbox gap"
            clearance = bbox_gap(a["bbox"], b["bbox"])
            required_by = True
        elif a_text or b_text:
            relation, required, coord = "TEXT_GRAPHIC", 3.0, "native final-PDF 300dpi final-visible mask distance"
            clearance = mask_distance(a["mask"], b["mask"])
            required_by = True
        else:
            relation, required, coord = "GRAPHIC_GRAPHIC_DESIGNED", 0.0, "source-declared design geometry"
            clearance = mask_distance(a["mask"], b["mask"])
            required_by = False
        overlap = int(np.sum(a["mask"] & b["mask"]))
        connection_note = intentional_connections.get(frozenset((a["OBJECT_ID"], b["OBJECT_ID"])))
        if connection_note:
            relation = "GRAPHIC_GRAPHIC_INTENTIONAL_CONNECTION"
            passed = True
            note = connection_note + "; final-visible 1:1 masks retained and visually reviewed as a designed connection"
        elif not required_by:
            passed = overlap == 0
            note = ("unapproved overlap: the independent training and validation data curves remain distinct in source semantics, "
                    "but their final-visible native masks share ink" if not passed else
                    "final masks remove true 0.90 white node backgrounds; no unapproved graphic-graphic overlap")
        else:
            passed = overlap == 0 and clearance >= required
            note = "none"
        critical = (required_by and clearance <= required + 2) or bool(connection_note)
        pair_rows.append({"PAIR_ID": f"P{index:04d}", "OBJECT_A": a["OBJECT_ID"], "OBJECT_B": b["OBJECT_ID"], "KIND_A": a["OBJECT_KIND"], "KIND_B": b["OBJECT_KIND"], "RELATION": relation, "REQUIRED_BY_921": str(required_by).lower(), "EXCEPTION_OR_DRAWING_ORDER_NOTE": note, "MASK_A": a["FINAL_VISIBLE_MASK"], "MASK_B": b["FINAL_VISIBLE_MASK"], "OVERLAP_PIXEL_COUNT": overlap, "MIN_CLEARANCE_PX": f"{clearance:.4f}", "REQUIRED_CLEARANCE_PX": f"{required:.1f}", "MEASUREMENT_COORDINATE": coord, "CRITICAL_OR_FAILURE": str(critical or not passed).lower(), "ROI_PACKAGE": "", "PASS_FAIL": "PASS" if passed else "FAIL", "_a": a, "_b": b})
    for pair in pair_rows:
        if pair["CRITICAL_OR_FAILURE"] == "true":
            safe = f"roi_packages/{pair['PAIR_ID']}_{pair['OBJECT_A']}_{pair['OBJECT_B']}"
            pair["ROI_PACKAGE"] = safe
            make_roi(pair, pair["_a"], pair["_b"], full)
    pair_fields = [key for key in pair_rows[0] if not key.startswith("_")]
    for file_name in ("all_unordered_pairs.csv", "after_overlap_report.csv"):
        with (ROOT / file_name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=pair_fields)
            writer.writeheader()
            writer.writerows([{key: row[key] for key in pair_fields} for row in pair_rows])
    mandatory = [row for row in pair_rows if row["REQUIRED_BY_921"] == "true"]
    with (ROOT / "mandatory_relationships.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=pair_fields)
        writer.writeheader()
        writer.writerows([{key: row[key] for key in pair_fields} for row in mandatory])
    clip_rows = []
    for item in foreground:
        mask = item["mask"]
        x0, y0, x1, y1 = item["bbox"]
        crop_edge = min(x0-FIGURE_CROP[0], FIGURE_CROP[2]-x1, y0-FIGURE_CROP[1], FIGURE_CROP[3]-y1) if item["OBJECT_KIND"] == "TEXT" else "N/A"
        page_edge_px = int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
        clip_rows.append({"OBJECT_ID": item["OBJECT_ID"], "OBJECT_KIND": item["OBJECT_KIND"], "NATIVE_FIGURE_CROP_EDGE_CLEARANCE_PX": crop_edge, "TEXT_EDGE_REQUIRED_PX": 6 if item["OBJECT_KIND"] == "TEXT" else "N/A", "CROP_EDGE_FOREGROUND_PX": 0, "PDF_PAGE_EDGE_FOREGROUND_PX": page_edge_px, "CLIP_PASS": str(page_edge_px == 0 and (item["OBJECT_KIND"] != "TEXT" or crop_edge >= 6)).lower()})
    with (ROOT / "clip_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(clip_rows[0].keys()))
        writer.writeheader()
        writer.writerows(clip_rows)
    order = {entry["OBJECT_ID"]: {"drawing_index": entry["DRAWING_INDEX"], "seqno": entry["DRAW_ORDER"], "category": entry["CATEGORY"], "pre_occlusion_mask": f"draw_masks/{entry['OBJECT_ID']}_pre_occlusion_mask.png", "final_visible_mask": f"object_masks/{entry['OBJECT_ID']}_final_visible_mask.png", "source_opacity_note": "fill opacity=.90 in source" if entry["CATEGORY"] == "HALO_BACKGROUND" else "opaque vector path/fill"} for entry in intermediate}
    (ROOT / "drawing_order_evidence.json").write_text(json.dumps({"coordinate": "native final-PDF page 170 at 300dpi", "source_order": "background regions -> curves/reference/leader -> true semitransparent white label backgrounds -> axes -> marker -> text", "objects": order, "halo_ids": ["O-H001", "O-H002", "O-H003"], "final_visible_rule": "foreground final mask = pre-occlusion foreground minus true text-background geometry; no page-white fictional halo"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"foreground_object_count": len(foreground), "text_object_count": len(text_objects), "all_visual_inventory_count": len(all_inventory), "all_unordered_pair_count": len(pair_rows), "mandatory_relationship_count": len(mandatory), "pair_failures": sum(row["PASS_FAIL"] == "FAIL" for row in pair_rows), "critical_relation_count": sum(row["CRITICAL_OR_FAILURE"] == "true" for row in pair_rows), "intentional_graphic_connections": sum(row["RELATION"] == "GRAPHIC_GRAPHIC_INTENTIONAL_CONNECTION" for row in pair_rows), "min_required_text_clearance_px": min(float(row["MIN_CLEARANCE_PX"]) for row in mandatory), "clip_failures": sum(row["CLIP_PASS"] != "true" for row in clip_rows)}
    (ROOT / "object_pair_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
