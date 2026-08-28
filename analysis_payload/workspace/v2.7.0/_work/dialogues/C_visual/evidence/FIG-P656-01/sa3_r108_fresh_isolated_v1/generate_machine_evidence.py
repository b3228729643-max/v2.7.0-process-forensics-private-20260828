from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa3_r108_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_multinomial_counts.tex")
FULL = ROOT / "r108_physical_705_fullpage_300dpi.png"
SCALE = 300.0 / 72.0
FIG_BODY_PT = (74.0, 565.0, 501.0, 682.0)
FIG_CAP_PT = (72.0, 565.0, 512.0, 715.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pt_box_to_px(box: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        int(math.floor(x0 * SCALE)),
        int(math.floor(y0 * SCALE)),
        int(math.ceil(x1 * SCALE)),
        int(math.ceil(y1 * SCALE)),
    )


def px_box_local(box: tuple[float, float, float, float], crop_px: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = pt_box_to_px(box)
    return x0 - crop_px[0], y0 - crop_px[1], x1 - crop_px[0], y1 - crop_px[1]


def union_box(*boxes: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def text_mask(image: Image.Image, box_px: tuple[int, int, int, int]) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.int16)
    x0, y0, x1, y1 = box_px
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(arr.shape[1], x1)
    y1 = min(arr.shape[0], y1)
    mask = np.zeros(arr.shape[:2], dtype=bool)
    if x1 <= x0 or y1 <= y0:
        return mask
    roi = arr[y0:y1, x0:x1]
    bg = np.median(roi.reshape(-1, 3), axis=0)
    delta = np.max(np.abs(roi - bg), axis=2)
    lum = roi.mean(axis=2)
    bg_lum = float(bg.mean())
    ink = (delta >= 20) | (lum <= bg_lum - 20)
    mask[y0:y1, x0:x1] = ink
    return mask


def raster_foreground_mask(image: Image.Image, box_px: tuple[int, int, int, int]) -> np.ndarray:
    return text_mask(image, box_px)


def neutral_dark_text_mask(image: Image.Image, box_px: tuple[int, int, int, int]) -> np.ndarray:
    """Separate neutral black glyph ink from the teal hatch behind category-2 labels."""
    arr = np.asarray(image.convert("RGB"), dtype=np.int16)
    x0, y0, x1, y1 = box_px
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(arr.shape[1], x1)
    y1 = min(arr.shape[0], y1)
    mask = np.zeros(arr.shape[:2], dtype=bool)
    roi = arr[y0:y1, x0:x1]
    chroma = roi.max(axis=2) - roi.min(axis=2)
    lum = roi.mean(axis=2)
    ink = (chroma <= 20) & (lum <= 235)
    mask[y0:y1, x0:x1] = ink
    return mask


def shape_mask(size: tuple[int, int], kind: str, box_px: tuple[int, int, int, int], width: int = 4) -> np.ndarray:
    canvas = Image.new("1", size, 0)
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box_px
    if kind == "ellipse":
        draw.ellipse((x0, y0, x1 - 1, y1 - 1), outline=1, width=width)
    elif kind == "rounded_rectangle":
        draw.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=max(2, width * 2), outline=1, width=width)
    else:
        raise ValueError(kind)
    return np.asarray(canvas, dtype=bool)


def bbox_clearance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def exact_min_distance(mask_a: np.ndarray, mask_b: np.ndarray, bbox_gap: float) -> str:
    if bbox_gap > 12:
        return ">12"
    ya, xa = np.nonzero(mask_a)
    yb, xb = np.nonzero(mask_b)
    if not len(xa) or not len(xb):
        return "EMPTY_MASK"
    best = float("inf")
    points_b = np.column_stack((xb, yb)).astype(np.int32)
    for start in range(0, len(xa), 128):
        points_a = np.column_stack((xa[start:start + 128], ya[start:start + 128])).astype(np.int32)
        diff = points_a[:, None, :] - points_b[None, :, :]
        d2 = np.sum(diff * diff, axis=2)
        best = min(best, float(d2.min()))
        if best == 0:
            break
    return f"{math.sqrt(best):.3f}"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


source_rel = r"src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_multinomial_counts.tex"

objects: list[dict] = []


def add(oid: str, name: str, role: str, kind: str, box: tuple[float, float, float, float], source_line: str, panel: str = "figure") -> None:
    objects.append({
        "object_id": oid,
        "name": name,
        "role": role,
        "kind": kind,
        "bbox_pt": box,
        "source_file": source_rel,
        "source_line": source_line,
        "panel": panel,
    })


add("O01", "title_multiple_ordered_sequences", "TITLE", "text", (119.15, 573.37, 178.33, 583.23), "22")
circle_boxes = [
    (87.09, 587.98, 104.09, 604.99), (108.35, 587.98, 125.35, 604.99),
    (129.61, 587.98, 146.61, 604.99), (150.87, 587.98, 167.87, 604.99),
    (172.13, 587.98, 189.13, 604.99), (193.39, 587.98, 210.39, 604.99),
    (87.09, 617.74, 104.09, 634.75), (108.35, 617.74, 125.35, 634.75),
    (129.61, 617.74, 146.61, 634.75), (150.87, 617.74, 167.87, 634.75),
    (172.13, 617.74, 189.13, 634.75), (193.39, 617.74, 210.39, 634.75),
    (87.09, 647.51, 104.09, 664.52), (108.35, 647.51, 125.35, 664.52),
    (129.61, 647.51, 146.61, 664.52), (150.87, 647.51, 167.87, 664.52),
    (172.13, 647.51, 189.13, 664.52), (193.39, 647.51, 210.39, 664.52),
]
label_boxes = [
    (93.25, 592.30, 97.93, 601.76), (114.51, 592.30, 119.19, 601.76),
    (135.77, 592.30, 140.45, 601.76), (157.03, 592.32, 161.71, 601.78),
    (178.29, 592.26, 182.97, 601.72), (199.55, 592.26, 204.23, 601.72),
    (93.25, 622.06, 97.93, 631.53), (114.51, 622.02, 119.19, 631.49),
    (135.77, 622.06, 140.45, 631.53), (157.03, 622.08, 161.71, 631.55),
    (178.29, 622.06, 182.97, 631.53), (199.55, 622.02, 204.23, 631.49),
    (93.25, 651.79, 97.93, 661.25), (114.51, 651.82, 119.19, 661.29),
    (135.77, 651.85, 140.45, 661.31), (157.03, 651.82, 161.71, 661.29),
    (178.29, 651.79, 182.97, 661.25), (199.55, 651.82, 204.23, 661.29),
]
seq_values = [1, 1, 1, 2, 3, 3, 1, 3, 1, 2, 1, 3, 3, 1, 2, 1, 3, 1]
for idx, (cb, lb, value) in enumerate(zip(circle_boxes, label_boxes, seq_values), start=1):
    row = (idx - 1) // 6 + 1
    col = (idx - 1) % 6 + 1
    circle_id = f"O{2 + (idx - 1) * 2:02d}"
    label_id = f"O{3 + (idx - 1) * 2:02d}"
    add(circle_id, f"sequence_r{row}c{col}_category_{value}_circle", "TOKEN_CONTAINER", "circle", cb, "23-27")
    add(label_id, f"sequence_r{row}c{col}_digit_{value}", "TOKEN_LABEL", "text", lb, "23-27")

add("O38", "flow_sequence_to_count", "FLOW_ARROW", "arrow", (222.30, 615.18, 255.29, 617.48), "30-31")
add("O39", "flow_label_same_count", "ARROW_LABEL", "text", (215.42, 603.04, 253.28, 612.50), "30-31")
add("O40", "count_vector_box", "NODE_CONTAINER", "rounded_rectangle", (257.17, 592.23, 376.22, 640.42), "14-15,28-29")
add("O41", "count_vector_formula", "FORMULA", "text", (266.24, 611.56, 367.14, 622.34), "28-29")
add("O42", "support_constraint_formula", "FORMULA", "text", (268.33, 646.18, 364.43, 658.92), "32-33")
add("O43", "warning_box", "NODE_CONTAINER", "rounded_rectangle", (257.67, 663.12, 375.72, 678.96), "16-17,34-35")
add("O44", "warning_count_not_probability", "WARNING_TEXT", "text", (264.64, 667.73, 368.75, 677.20), "34-35")
add("O45", "flow_count_to_coefficient", "FLOW_ARROW", "arrow", (376.67, 615.18, 389.85, 617.48), "38")
add("O46", "coefficient_box", "NODE_CONTAINER", "rounded_rectangle", (391.66, 596.48, 496.85, 636.17), "18-19,36-37")
add("O47", "coefficient_label", "NODE_LABEL", "text", (396.26, 602.72, 492.25, 612.18), "36-37")
add("O48", "multinomial_coefficient_formula", "FORMULA", "text", (423.55, 613.72, 465.23, 632.84), "36-37")
add("O49", "caption_number_Fig_34_2", "CAPTION_NUMBER", "text", (76.14, 686.11, 106.60, 696.57), "40-42", "caption")
add("O50", "caption_text", "CAPTION_TEXT", "text", (116.56, 686.44, 507.80, 709.79), "40-42", "caption")


containment_pairs = {(f"O{3 + (i - 1) * 2:02d}", f"O{2 + (i - 1) * 2:02d}") for i in range(1, 19)}
containment_pairs |= {("O41", "O40"), ("O44", "O43"), ("O47", "O46"), ("O48", "O46")}
containment_pairs = {tuple(sorted(p)) for p in containment_pairs}
attachment_pairs = {tuple(sorted(p)) for p in [("O38", "O40"), ("O45", "O40"), ("O45", "O46")]}
related_pairs = {tuple(sorted(("O38", "O39"))), tuple(sorted(("O41", "O42"))), tuple(sorted(("O42", "O43")))}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    masks_dir = ROOT / "object_masks"
    masks_dir.mkdir(exist_ok=True)
    rois_dir = ROOT / "critical_rois"
    rois_dir.mkdir(exist_ok=True)

    full = Image.open(FULL).convert("RGB")
    cap_px = pt_box_to_px(FIG_CAP_PT)
    body_px = pt_box_to_px(FIG_BODY_PT)
    figure_caption = full.crop(cap_px)
    figure_body = full.crop(body_px)
    figure_caption.save(ROOT / "r108_p705_figure_caption_300dpi.png")
    figure_body.save(ROOT / "r108_p705_figure_body_local_300dpi.png")
    figure_caption.convert("L").save(ROOT / "r108_p705_figure_caption_grayscale_300dpi.png")
    full.convert("L").save(ROOT / "r108_p705_fullpage_grayscale_300dpi.png")

    object_masks: dict[str, np.ndarray] = {}
    object_rows: list[dict] = []
    circle_label_map = {f"O{2 + (i - 1) * 2:02d}": f"O{3 + (i - 1) * 2:02d}" for i in range(1, 19)}
    by_id = {o["object_id"]: o for o in objects}
    patterned_label_ids = {"O09", "O21", "O31"}

    for obj in objects:
        oid = obj["object_id"]
        local_box = px_box_local(obj["bbox_pt"], cap_px)
        if obj["kind"] == "text":
            mask = neutral_dark_text_mask(figure_caption, local_box) if oid in patterned_label_ids else text_mask(figure_caption, local_box)
        elif obj["kind"] == "circle":
            mask = shape_mask(figure_caption.size, "ellipse", local_box, 4)
            if "category_2" in obj["name"]:
                raster = raster_foreground_mask(figure_caption, local_box)
                paired_label = by_id[circle_label_map[oid]]
                label_mask = neutral_dark_text_mask(figure_caption, px_box_local(paired_label["bbox_pt"], cap_px))
                raster[label_mask] = False
                mask = np.logical_or(mask, raster)
        elif obj["kind"] == "rounded_rectangle":
            width = 4 if oid == "O40" else 3
            mask = shape_mask(figure_caption.size, "rounded_rectangle", local_box, width)
        elif obj["kind"] == "arrow":
            mask = raster_foreground_mask(figure_caption, local_box)
        else:
            raise ValueError(obj["kind"])
        object_masks[oid] = mask
        mask_img = Image.fromarray((mask.astype(np.uint8) * 255), mode="L")
        mask_img.save(masks_dir / f"{oid}_{obj['name']}.png")
        ys, xs = np.nonzero(mask)
        object_rows.append({
            "object_id": oid,
            "name": obj["name"],
            "role": obj["role"],
            "kind": obj["kind"],
            "panel": obj["panel"],
            "source_file": obj["source_file"],
            "source_line": obj["source_line"],
            "bbox_pdf_pt": ";".join(f"{v:.2f}" for v in obj["bbox_pt"]),
            "bbox_crop_px": ";".join(str(v) for v in local_box),
            "foreground_pixel_count": int(mask.sum()),
            "foreground_empty": str(not len(xs)).lower(),
            "foreground_bbox_px": "" if not len(xs) else f"{xs.min()};{ys.min()};{xs.max()+1};{ys.max()+1}",
            "mask_method": "neutral_dark_color_separation" if oid in patterned_label_ids else ("local_background_delta_20" if obj["kind"] in {"text", "arrow"} else "vector_geometry_or_hatch_separation"),
        })

    write_csv(
        ROOT / "objects_machine.csv",
        object_rows,
        ["object_id", "name", "role", "kind", "panel", "source_file", "source_line", "bbox_pdf_pt", "bbox_crop_px", "foreground_pixel_count", "foreground_empty", "foreground_bbox_px", "mask_method"],
    )

    overlay = figure_caption.copy()
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    colors = {"text": "#b00020", "circle": "#00695c", "rounded_rectangle": "#6a1b9a", "arrow": "#1565c0"}
    for obj in objects:
        box = px_box_local(obj["bbox_pt"], cap_px)
        color = colors[obj["kind"]]
        draw.rectangle(box, outline=color, width=2)
        draw.text((box[0] + 2, max(0, box[1] - 19)), obj["object_id"], fill=color, font=font)
    overlay.save(ROOT / "r108_p705_object_overlay_300dpi.png")

    pair_rows: list[dict] = []
    candidate_pair_pixels = 0
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            a = objects[i]
            b = objects[j]
            aid, bid = a["object_id"], b["object_id"]
            pair = tuple(sorted((aid, bid)))
            ma, mb = object_masks[aid], object_masks[bid]
            overlap = int(np.logical_and(ma, mb).sum())
            abox = px_box_local(a["bbox_pt"], cap_px)
            bbox = px_box_local(b["bbox_pt"], cap_px)
            gap = bbox_clearance(abox, bbox)
            distance = "0.000" if overlap else exact_min_distance(ma, mb, gap)
            if pair in containment_pairs:
                expected = "INTENDED_CONTAINMENT"
                observed = "CONTAINMENT_BOUNDARY_OVERLAP" if overlap else "INTENDED_CONTAINMENT_CLEAR"
            elif pair in attachment_pairs:
                expected = "INTENDED_ATTACHMENT"
                observed = "INTENDED_ATTACHMENT_PIXEL_CONNECTED" if overlap else "INTENDED_ATTACHMENT_WITH_RENDERED_TIP_GAP"
            elif pair in related_pairs:
                expected = "RELATED_CLEARANCE"
                observed = "RELATED_CANDIDATE_OVERLAP" if overlap else "RELATED_CLEAR"
            else:
                expected = "SEPARATE"
                observed = "CANDIDATE_OVERLAP" if overlap else "CLEAR_SEPARATE"
            if expected == "SEPARATE":
                candidate_pair_pixels += overlap
            pair_rows.append({
                "pair_id": f"P{len(pair_rows)+1:04d}",
                "object_a": aid,
                "object_b": bid,
                "expected_relation": expected,
                "machine_observed_relation": observed,
                "mask_overlap_pixels": overlap,
                "bbox_clearance_px": f"{gap:.3f}",
                "ink_min_distance_px": distance,
                "requires_manual_adjudication": str(observed in {"CANDIDATE_OVERLAP", "RELATED_CANDIDATE_OVERLAP", "CONTAINMENT_BOUNDARY_OVERLAP"}).lower(),
            })

    write_csv(
        ROOT / "all_pairs_machine.csv",
        pair_rows,
        ["pair_id", "object_a", "object_b", "expected_relation", "machine_observed_relation", "mask_overlap_pixels", "bbox_clearance_px", "ink_min_distance_px", "requires_manual_adjudication"],
    )

    critical_relations = []
    for idx in range(1, 19):
        circle = f"O{2 + (idx - 1) * 2:02d}"
        label = f"O{3 + (idx - 1) * 2:02d}"
        row = (idx - 1) // 6 + 1
        col = (idx - 1) % 6 + 1
        critical_relations.append({
            "relation_id": f"CR{idx:02d}",
            "relation": f"sequence_r{row}c{col}_label_inside_circle",
            "object_a": label,
            "object_b": circle,
            "expected": "label centered inside its category circle; boundary is legal container, no ink-border collision",
        })
    critical_relations.extend([
        {"relation_id": "CR19", "relation": "left_flow_to_count_box", "object_a": "O38", "object_b": "O40", "expected": "source path terminates at count.west; rendered arrowhead may preserve a small anti-alias/tip gap but direction must be unambiguous"},
        {"relation_id": "CR20", "relation": "left_flow_label_clearance", "object_a": "O39", "object_b": "O38", "expected": "label above arrow with >=3 px ink-to-line clearance"},
        {"relation_id": "CR21", "relation": "count_formula_inside_count_box", "object_a": "O41", "object_b": "O40", "expected": "legal containment with >=5 px ink-to-border clearance"},
        {"relation_id": "CR22", "relation": "count_formula_to_support_formula", "object_a": "O41", "object_b": "O42", "expected": "separate stacked formulas with no overlap and readable vertical clearance"},
        {"relation_id": "CR23", "relation": "support_formula_to_warning_box", "object_a": "O42", "object_b": "O43", "expected": "separate with no overlap; warning is visually subordinate"},
        {"relation_id": "CR24", "relation": "warning_text_inside_warning_box", "object_a": "O44", "object_b": "O43", "expected": "legal containment with >=5 px ink-to-border clearance"},
        {"relation_id": "CR25", "relation": "right_flow_from_count_box", "object_a": "O45", "object_b": "O40", "expected": "source path begins at count.east; rendered tail must read as attached"},
        {"relation_id": "CR26", "relation": "right_flow_to_coefficient_box", "object_a": "O45", "object_b": "O46", "expected": "source path terminates at coef.west; rendered arrowhead direction must be unambiguous"},
        {"relation_id": "CR27", "relation": "coefficient_label_inside_box", "object_a": "O47", "object_b": "O46", "expected": "legal containment with >=5 px ink-to-border clearance"},
        {"relation_id": "CR28", "relation": "coefficient_formula_inside_box", "object_a": "O48", "object_b": "O46", "expected": "legal containment with >=5 px ink-to-border clearance"},
        {"relation_id": "CR29", "relation": "caption_number_to_caption_text", "object_a": "O49", "object_b": "O50", "expected": "same caption baseline/continuation, no glyph collision"},
    ])
    pair_by_objects = {tuple(sorted((r["object_a"], r["object_b"]))): r for r in pair_rows}
    for cr in critical_relations:
        key = tuple(sorted((cr["object_a"], cr["object_b"])))
        pr = pair_by_objects[key]
        cr["machine_observed_relation"] = pr["machine_observed_relation"]
        cr["mask_overlap_pixels"] = pr["mask_overlap_pixels"]
        cr["ink_min_distance_px"] = pr["ink_min_distance_px"]
        cr["container_boundary_clearance_px"] = "NOT_APPLICABLE"
        cr["measurement_scope"] = "independent semantic masks"
    for idx in range(1, 19):
        cr = critical_relations[idx - 1]
        circle_id = cr["object_b"]
        label_id = cr["object_a"]
        circle_obj = by_id[circle_id]
        boundary = shape_mask(figure_caption.size, "ellipse", px_box_local(circle_obj["bbox_pt"], cap_px), 4)
        gap = bbox_clearance(px_box_local(by_id[circle_id]["bbox_pt"], cap_px), px_box_local(by_id[label_id]["bbox_pt"], cap_px))
        cr["container_boundary_clearance_px"] = exact_min_distance(boundary, object_masks[label_id], gap)
        cr["measurement_scope"] = "circle boundary clearance separated from legal internal fill/hatch texture"
    for cr in critical_relations:
        if cr["relation_id"] in {"CR21", "CR24", "CR27", "CR28"}:
            cr["container_boundary_clearance_px"] = cr["ink_min_distance_px"]
            cr["measurement_scope"] = "container boundary versus contained text/formula ink"
        elif cr["relation_id"] in {"CR19", "CR25", "CR26"}:
            cr["measurement_scope"] = "rendered arrow tip/tail gap; source anchor relation recorded separately"
    write_csv(
        ROOT / "critical_relations_machine.csv",
        critical_relations,
        ["relation_id", "relation", "object_a", "object_b", "expected", "machine_observed_relation", "mask_overlap_pixels", "ink_min_distance_px", "container_boundary_clearance_px", "measurement_scope"],
    )

    font_runs = []
    def fr(fid: str, parent: str, name: str, box: tuple[float, float, float, float], source_tex_pt: str, pdf_bp: float, script_class: str, threshold: int, derivation: str) -> None:
        local = px_box_local(box, cap_px)
        mask = neutral_dark_text_mask(figure_caption, local) if parent in patterned_label_ids else text_mask(figure_caption, local)
        ys, xs = np.nonzero(mask)
        h = 0 if not len(ys) else int(ys.max() - ys.min() + 1)
        font_runs.append({
            "font_run_id": fid, "parent_object_id": parent, "name": name,
            "source_declared_or_derived_tex_pt": source_tex_pt,
            "pdf_reported_bp": f"{pdf_bp:.2f}",
            "pdf_bp_converted_to_tex_pt": f"{pdf_bp * 72.27 / 72.0:.3f}",
            "script_class": script_class, "bbox_pdf_pt": ";".join(f"{v:.2f}" for v in box),
            "ink_height_px_at_300dpi": h, "protocol_min_ink_px": threshold,
            "machine_threshold_observation": "MEETS" if h >= threshold else "BELOW",
            "size_derivation": derivation,
            "measurement_mask_method": "neutral_dark_color_separation" if parent in patterned_label_ids else "local_background_delta_20",
        })
    fr("F001", "O01", "title_Chinese", (119.15, 573.37, 178.33, 583.23), "9.9", 9.86, "CJK_FULL", 30, "explicit source line 22")
    for idx, lb in enumerate(label_boxes, start=1):
        parent = f"O{3 + (idx - 1) * 2:02d}"
        fr(f"F{idx+1:03d}", parent, f"token_digit_r{(idx-1)//6+1}c{(idx-1)%6+1}", lb, "9.5", 9.46, "LATIN_DIGIT", 24, "every node source line 9")
    fr("F020", "O39", "same_count_Chinese", (215.42, 603.04, 253.28, 612.50), "9.5", 9.46, "CJK_FULL", 30, "explicit source lines 30-31")
    fr("F021", "O41", "count_formula_base", (266.24, 611.56, 367.14, 622.34), "9.5", 9.46, "MATH_BASE", 22, "every node source line 9")
    fr("F022", "O41", "count_subscript_1", (292.33, 615.71, 296.05, 622.34), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F023", "O41", "count_subscript_2", (305.67, 615.71, 309.37, 622.34), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F024", "O41", "count_subscript_3", (319.00, 615.71, 322.71, 622.34), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F025", "O42", "support_formula_base", (268.33, 646.18, 364.43, 658.92), "9.5", 9.46, "MATH_BASE", 22, "explicit source lines 32-33")
    fr("F026", "O42", "support_n_subscript_k", (273.68, 650.33, 278.26, 656.96), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F027", "O42", "support_Z_subscript_ge0", (296.85, 650.33, 306.16, 656.96), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F028", "O42", "support_sum_lower_k", (328.76, 652.29, 333.35, 658.92), "natural limit from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural lower limit")
    fr("F029", "O42", "support_second_n_subscript_k", (340.65, 650.33, 345.23, 656.96), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F030", "O44", "warning_Chinese", (264.64, 667.73, 368.75, 677.20), "9.5", 9.46, "CJK_FULL", 30, "explicit source lines 34-35")
    fr("F031", "O47", "coefficient_label_Chinese", (396.26, 602.72, 492.25, 612.18), "9.5", 9.46, "CJK_FULL", 30, "every node source line 9")
    fr("F032", "O48", "coefficient_formula_base", (423.55, 613.72, 465.23, 624.54), "9.5", 9.46, "MATH_BASE", 22, "every node source line 9")
    fr("F033", "O48", "coefficient_product_lower_k", (441.66, 626.21, 446.25, 632.84), "natural limit from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural lower limit")
    fr("F034", "O48", "coefficient_n_subscript_k", (457.58, 617.91, 462.17, 624.54), "natural script from 9.5", 6.63, "MATH_SCRIPT", 15, "TeX natural subscript")
    fr("F035", "O49", "caption_number", (76.14, 686.11, 106.60, 696.57), "inherited; PDF confirms about 10.0", 9.96, "CJK_AND_DIGIT", 30, "caption context, PDF bp converted to TeX pt")
    fr("F036", "O50", "caption_line_1_Chinese", (116.56, 686.44, 507.80, 696.40), "inherited; PDF confirms about 10.0", 9.96, "CJK_FULL", 30, "caption context, PDF bp converted to TeX pt")
    fr("F037", "O50", "caption_line_2_Chinese", (76.14, 699.83, 434.79, 709.79), "inherited; PDF confirms about 10.0", 9.96, "CJK_FULL", 30, "caption context, PDF bp converted to TeX pt")
    write_csv(ROOT / "font_runs_machine.csv", font_runs, list(font_runs[0].keys()))

    roi_defs = {
        "roi_tokens": (82.0, 568.0, 214.0, 669.0),
        "roi_left_arrow_count": (210.0, 585.0, 383.0, 643.0),
        "roi_count_support_warning": (250.0, 588.0, 380.0, 682.0),
        "roi_right_arrow_coefficient": (370.0, 590.0, 502.0, 641.0),
        "roi_caption": (72.0, 681.0, 512.0, 714.0),
    }
    roi_rows = []
    for name, ptbox in roi_defs.items():
        pxbox = pt_box_to_px(ptbox)
        roi = full.crop(pxbox)
        one = rois_dir / f"{name}_native_1x_300dpi.png"
        eight = rois_dir / f"{name}_pixel_8x_nearest.png"
        roi.save(one)
        roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(eight)
        roi_rows.append({"roi_id": name, "bbox_pdf_pt": ";".join(str(v) for v in ptbox), "native_1x": one.name, "pixel_8x": eight.name})
    write_csv(ROOT / "critical_rois_index.csv", roi_rows, ["roi_id", "bbox_pdf_pt", "native_1x", "pixel_8x"])

    cap_arr = np.asarray(figure_caption.convert("RGB"), dtype=np.int16)
    edge = np.concatenate((cap_arr[0], cap_arr[-1], cap_arr[:, 0], cap_arr[:, -1]), axis=0)
    edge_bg = np.median(edge, axis=0)
    edge_fg = int((np.max(np.abs(edge - edge_bg), axis=1) >= 20).sum())
    machine_summary = {
        "object_denominator_N": len(objects),
        "unordered_pair_denominator_C_N_2": len(pair_rows),
        "expected_pair_formula": len(objects) * (len(objects) - 1) // 2,
        "pair_ids_unique": len({r["pair_id"] for r in pair_rows}),
        "object_ids_unique": len({o["object_id"] for o in objects}),
        "empty_object_masks": [r["object_id"] for r in object_rows if r["foreground_empty"] == "true"],
        "separate_pair_candidate_overlap_pixels_sum": candidate_pair_pixels,
        "pairs_requiring_manual_adjudication": [r["pair_id"] for r in pair_rows if r["requires_manual_adjudication"] == "true"],
        "font_run_count": len(font_runs),
        "font_runs_below_protocol_ink_threshold": [r["font_run_id"] for r in font_runs if r["machine_threshold_observation"] == "BELOW"],
        "figure_caption_crop_edge_foreground_pixels": edge_fg,
        "render_native_dpi": 300,
        "fullpage_pixel_dimensions": list(full.size),
        "figure_body_pixel_dimensions": list(figure_body.size),
        "figure_caption_pixel_dimensions": list(figure_caption.size),
        "input_sha256": {"official_pdf": sha256(PDF), "sole_source": sha256(SOURCE), "fullpage_render": sha256(FULL)},
        "manual_fields_generated": False,
    }
    (ROOT / "machine_gate_summary.json").write_text(json.dumps(machine_summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
