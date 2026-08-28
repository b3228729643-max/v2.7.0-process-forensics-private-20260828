from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, label


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P077-01\STRICT_R2_SA1_FRESH_ISOLATED_R114_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
PAGE_INDEX = 78


def load_csv(name):
    with (ROOT / "machine" / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(name, rows, fields):
    with (ROOT / "machine" / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_items(page_rect, items, width, fill, dpi=300):
    doc = fitz.open()
    page = doc.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    for item in items:
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
            raise ValueError(f"unsupported drawing item: {item!r}")
    shape.finish(color=(0, 0, 0) if not fill else None,
                 fill=(0, 0, 0) if fill else None,
                 width=max(float(width or 0.5), 0.25), closePath=bool(fill))
    shape.commit()
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    return arr < 245


def mask_distance(a, b):
    shared = int(np.logical_and(a, b).sum())
    if shared:
        return shared, 0.0
    if not a.any() or not b.any():
        return 0, math.inf
    dist_to_b = distance_transform_edt(~b)
    return 0, float(dist_to_b[a].min())


def main():
    objects = load_csv("visible_object_geometry.csv")
    pairs = load_csv("all_unordered_pairs_geometry.csv")
    pair_lookup = {(p["object_a"], p["object_b"]): p["pair_id"] for p in pairs}
    obj = {o["object_id"]: o for o in objects}

    full = np.asarray(Image.open(ROOT / "visual" / "full_page_native300dpi.png").convert("L"))
    with (ROOT / "machine" / "page_locator.json").open("r", encoding="utf-8") as stream:
        locator = json.load(stream)
    cx0, cy0, cx1, cy1 = locator["figure_crop_pixels_on_page"]

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    drawings = page.get_drawings()

    drawing_map = {
        "G01": [(14, None), (15, None)],
        "G02": [(16, None), (17, None)],
        "G03": [(12, 0)], "G04": [(12, 1)], "G05": [(12, 2)],
        "G06": [(13, 0)], "G07": [(13, 1)], "G08": [(13, 2)],
        "G09": [(20, None)], "G10": [(19, None)],
        "G11": [(21, None)], "G12": [(18, None)],
        "G13": [(22, None)], "G14": [(27, None)],
        "G15": [(23, None)], "G16": [(25, None)], "G17": [(28, None)],
    }
    masks = {}
    for oid, selections in drawing_map.items():
        merged = np.zeros(full.shape, dtype=bool)
        for draw_idx, item_idx in selections:
            drawing = drawings[draw_idx]
            items = drawing["items"] if item_idx is None else [drawing["items"][item_idx]]
            merged |= render_items(page.rect, items, drawing.get("width"), drawing.get("type") in ("f", "fs"))
        masks[oid] = merged

    # Logical text masks come from final page pixels within vector-derived boxes.
    for oid in [f"T{i:02d}" for i in range(1, 14)]:
        o = obj[oid]
        x0, y0, x1, y1 = (int(o[k]) for k in ("px_x0", "px_y0", "px_x1", "px_y1"))
        m = np.zeros(full.shape, dtype=bool)
        m[max(0, y0 - 2):min(full.shape[0], y1 + 3), max(0, x0 - 2):min(full.shape[1], x1 + 3)] = \
            full[max(0, y0 - 2):min(full.shape[0], y1 + 3), max(0, x0 - 2):min(full.shape[1], x1 + 3)] <= 205
        masks[oid] = m

    # White label backgrounds remove underlying graphics in the final visible raster.
    bg = masks["G15"] | masks["G16"] | masks["G17"]
    for oid in ["G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G11", "G13", "G14"]:
        masks[oid] &= ~bg

    mask_dir = ROOT / "visual" / "masks"
    mask_dir.mkdir(exist_ok=True)
    for oid, mask in masks.items():
        crop = (mask[cy0:cy1, cx0:cx1] * 255).astype(np.uint8)
        Image.fromarray(crop, mode="L").save(mask_dir / f"{oid}_native300dpi_mask.png")

    foreground_ids = [f"T{i:02d}" for i in range(1, 14)] + [
        "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G11", "G13", "G14"
    ]
    clearance_rows = []
    candidate_rows = []
    candidate_union = np.zeros(full.shape, dtype=bool)
    pairwise_candidate_pixels = 0
    for i, a in enumerate(foreground_ids):
        for b in foreground_ids[i + 1:]:
            shared, gap = mask_distance(masks[a], masks[b])
            pid = pair_lookup.get((a, b)) or pair_lookup.get((b, a))
            clearance_rows.append({
                "pair_id": pid, "object_a": a, "object_b": b,
                "foreground_pixels_a": int(masks[a].sum()),
                "foreground_pixels_b": int(masks[b].sum()),
                "shared_visible_foreground_pixels": shared,
                "minimum_visible_ink_distance_px": "INF" if math.isinf(gap) else round(gap, 3),
            })
            if shared:
                inter = masks[a] & masks[b]
                _, clusters = label(inter)
                candidate_rows.append({
                    "pair_id": pid, "object_a": a, "object_b": b,
                    "shared_visible_foreground_pixels": shared,
                    "connected_cluster_count": int(clusters),
                })
                pairwise_candidate_pixels += shared
                candidate_union |= inter
    write_csv("foreground_pair_pixel_clearance.csv", clearance_rows,
              ["pair_id", "object_a", "object_b", "foreground_pixels_a", "foreground_pixels_b",
               "shared_visible_foreground_pixels", "minimum_visible_ink_distance_px"])
    write_csv("mechanical_overlap_candidates.csv", candidate_rows,
              ["pair_id", "object_a", "object_b", "shared_visible_foreground_pixels", "connected_cluster_count"])

    text_ids = [f"T{i:02d}" for i in range(1, 14)]
    text_text = [r for r in clearance_rows if r["object_a"] in text_ids and r["object_b"] in text_ids]
    text_graphic = [r for r in clearance_rows if (r["object_a"] in text_ids) != (r["object_b"] in text_ids)]
    finite_tt = [float(r["minimum_visible_ink_distance_px"]) for r in text_text if r["minimum_visible_ink_distance_px"] != "INF"]
    finite_tg = [float(r["minimum_visible_ink_distance_px"]) for r in text_graphic if r["minimum_visible_ink_distance_px"] != "INF"]

    text_bbox_edge_clearances = []
    for oid in text_ids:
        o = obj[oid]
        x0, y0, x1, y1 = (int(o[k]) for k in ("px_x0", "px_y0", "px_x1", "px_y1"))
        text_bbox_edge_clearances.append(min(x0 - cx0, y0 - cy0, cx1 - x1, cy1 - y1))
    summary = {
        "foreground_object_count_analyzed": len(foreground_ids),
        "foreground_pair_count_analyzed": len(clearance_rows),
        "mechanical_nonzero_shared_foreground_pair_count": len(candidate_rows),
        "mechanical_pairwise_candidate_pixel_sum": pairwise_candidate_pixels,
        "mechanical_unique_candidate_pixel_count": int(candidate_union.sum()),
        "minimum_text_text_visible_ink_distance_px": min(finite_tt),
        "minimum_text_graphic_visible_ink_distance_px_including_intended_label_geometry": min(finite_tg),
        "minimum_text_bbox_to_figure_crop_edge_px": min(text_bbox_edge_clearances),
        "note": "Machine values are observations only; manual semantic adjudication is maintained outside this script.",
    }
    (ROOT / "machine" / "pixel_clearance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
