from __future__ import annotations

import csv
import itertools
import json
import math
import os
import unicodedata
from collections import Counter
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r104_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bivariate_normal_conditionals.tex")
CONTEXT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C04.tex")
PAGE_INDEX = 688
PHYSICAL_PAGE = 689
PRINTED_PAGE = 676
DPI = 300
SCALE = DPI / 72.0
FULL_PAGE = ROOT / "render" / "full_page_native_300dpi.png"
FIGURE_RECT_PT = (55.0, 325.0, 529.0, 530.0)
PLOT_RECT_PT = (90.0, 327.0, 500.0, 495.0)


def px_rect(rect_pt, pad=0):
    x0, y0, x1, y1 = rect_pt
    return (
        max(0, math.floor(x0 * SCALE) - pad),
        max(0, math.floor(y0 * SCALE) - pad),
        math.ceil(x1 * SCALE) + pad,
        math.ceil(y1 * SCALE) + pad,
    )


def csv_write(path, fieldnames, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def ink_mask_for_crop(rgb, bg=(255, 255, 255), threshold=20):
    arr = np.asarray(rgb).astype(np.int16)
    base = np.asarray(bg, dtype=np.int16)
    return np.max(np.abs(arr - base), axis=2) >= threshold


def ink_height(mask):
    ys = np.where(mask)[0]
    return int(ys.max() - ys.min() + 1) if ys.size else 0


def ink_width(mask):
    xs = np.where(mask)[1]
    return int(xs.max() - xs.min() + 1) if xs.size else 0


def bbox_union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def bbox_intersection_area(a, b):
    w = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h


TEXT_SPECS = [
    ("T01", "PLOT", "DISTRIBUTION_LABEL", "N(0.45,0.64)", (146.62,333.53,202.76,342.70), 9.2, 26),
    ("T02", "PLOT", "MEAN_LABEL", "mu_1=.45", (211.93,333.53,246.63,344.62), 9.2, 26),
    ("T03", "PLOT", "DISTRIBUTION_LABEL", "N(0.60,0.64)", (280.09,333.53,336.77,342.70), 9.2, 28),
    ("T04", "PLOT", "MEAN_LABEL", "mu_2=.60", (345.93,333.53,381.15,344.62), 9.2, 28),
    ("T05", "PLOT", "X_TICK_LABEL", "-2", (129.89,470.32,141.51,479.29), 8.5, 17),
    ("T06", "PLOT", "X_TICK_LABEL", "-1", (180.52,470.29,192.00,479.25), 8.5, 17),
    ("T07", "PLOT", "X_TICK_LABEL", "0", (234.22,470.31,239.42,479.27), 8.5, 17),
    ("T08", "PLOT", "X_TICK_LABEL", "1", (285.10,470.29,289.66,479.25), 8.5, 17),
    ("T09", "PLOT", "X_TICK_LABEL", "2", (335.60,470.32,340.29,479.29), 8.5, 17),
    ("T10", "PLOT", "X_TICK_LABEL", "3", (386.16,470.32,390.85,479.29), 8.5, 17),
    ("T11", "PLOT", "Y_TICK_LABEL", "0", (124.54,461.29,129.74,470.25), 8.5, 17),
    ("T12", "PLOT", "Y_TICK_LABEL", "0.25", (112.71,407.91,129.74,416.88), 8.5, 17),
    ("T13", "PLOT", "Y_TICK_LABEL", "0.5", (117.41,354.52,129.74,363.49), 8.5, 17),
    ("T14", "PLOT", "X_AXIS_LABEL", "t", (260.17,483.60,263.90,492.76), 9.2, 17),
    ("T15", "PLOT", "Y_AXIS_LABEL", "密度", (96.81,396.23,106.62,414.56), 9.2, 17),
    ("T16", "PLOT", "ANNOTATION", "共同方差 0.64", (415.52,396.06,472.49,405.88), 9.2, 30),
    ("T17", "PLOT", "ANNOTATION", "均值随另一坐标改变", (402.76,407.02,485.25,416.84), 9.2, 30),
    ("T18", "CAPTION", "CAPTION_LABEL", "图 33.6", (62.36,497.10,92.64,511.52), None, 33),
    ("T19", "CAPTION", "CAPTION_BODY", "取 rho=0.6、a=1、b=0.75 时，两个满条件分布分别为 N(0.45,0.64) 与 N(0.60,0.64)；图中曲线", (102.60,500.68,521.57,511.35), None, 33),
    ("T20", "CAPTION", "CAPTION_BODY", "按同一组参数直接计算。", (62.36,514.07,171.95,524.74), None, 33),
]

GRAPHIC_SPECS = [
    ("G01", "PLOT", "TICK_MARKS", "X_TICK_MARKS", (135.70,463.05,388.51,467.30), 18),
    ("G02", "PLOT", "TICK_MARKS", "Y_TICK_MARKS", (133.57,358.41,137.83,465.18), 18),
    ("G03", "PLOT", "AXIS_LINE", "X_AXIS_LINE", (135.70,465.18,386.14,465.18), 18),
    ("G04", "PLOT", "ARROWHEAD", "X_AXIS_ARROWHEAD", (384.72,463.29,388.51,467.07), 18),
    ("G05", "PLOT", "AXIS_LINE", "Y_AXIS_LINE", (135.70,347.97,135.70,465.18), 18),
    ("G06", "PLOT", "ARROWHEAD", "Y_AXIS_ARROWHEAD", (133.81,345.60,137.59,349.39), 18),
    ("G07", "PLOT", "DATA_CURVE", "BLUE_DENSITY_CURVE", (135.70,358.70,388.51,465.18), 19),
    ("G08", "PLOT", "BACKGROUND_FILL", "BLUE_DENSITY_FILL", (135.70,358.70,388.51,465.18), 19),
    ("G09", "PLOT", "DATA_CURVE", "GOLD_DENSITY_CURVE", (135.70,358.70,388.50,464.64), 21),
    ("G10", "PLOT", "LINE_MARKER", "BLUE_MEAN_LINE", (259.58,358.63,259.58,465.18), 23),
    ("G11", "PLOT", "LINE_MARKER", "GOLD_MEAN_LINE", (267.16,358.63,267.16,465.18), 24),
    ("G12", "PLOT", "NODE_BORDER", "ANNOTATION_BORDER", (396.78,391.34,491.23,419.44), 29),
]


def main():
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("sealed evidence root")
    for d in ("render", "masks", "crops_1x", "crops_8x", "inventory", "pairs"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)

    page_image = Image.open(FULL_PAGE).convert("RGB")
    page_arr = np.asarray(page_image)
    pdf_doc = fitz.open(PDF)
    page = pdf_doc[PAGE_INDEX]
    raw = page.get_text("rawdict")

    figure_crop = page_image.crop(px_rect(FIGURE_RECT_PT))
    plot_crop = page_image.crop(px_rect(PLOT_RECT_PT))
    figure_crop.save(ROOT / "render" / "figure_crop_native_300dpi.png")
    plot_crop.save(ROOT / "render" / "standalone_equivalent_native_300dpi.png")
    figure_crop.convert("L").save(ROOT / "render" / "figure_grayscale_native_300dpi.png")
    plot_crop.convert("L").save(ROOT / "render" / "standalone_equivalent_grayscale_native_300dpi.png")

    objects = []
    object_masks = {}
    object_points = {}

    for oid, panel, role, text, bbox_pt, declared_pt, source_line in TEXT_SPECS:
        bbox_px = px_rect(bbox_pt)
        crop = page_image.crop(bbox_px)
        mask = ink_mask_for_crop(crop)
        object_masks[oid] = (bbox_px, mask)
        ys, xs = np.where(mask)
        object_points[oid] = np.column_stack((ys + bbox_px[1], xs + bbox_px[0])) if ys.size else np.empty((0, 2), dtype=int)
        crop1 = page_image.crop(px_rect(bbox_pt, pad=8))
        crop1.save(ROOT / "crops_1x" / f"{oid}_object_1x.png")
        crop1.resize((crop1.width * 8, crop1.height * 8), Image.Resampling.NEAREST).save(ROOT / "crops_8x" / f"{oid}_object_8x.png")
        Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(ROOT / "masks" / f"{oid}_mask_native.png")
        objects.append({
            "object_id": oid, "object_family": "TEXT", "panel_id": panel, "role": role,
            "content": text, "source_line": source_line, "declared_pt": "" if declared_pt is None else declared_pt,
            "bbox_pt_x0": bbox_pt[0], "bbox_pt_y0": bbox_pt[1], "bbox_pt_x1": bbox_pt[2], "bbox_pt_y1": bbox_pt[3],
            "bbox_px_x0": bbox_px[0], "bbox_px_y0": bbox_px[1], "bbox_px_x1": bbox_px[2], "bbox_px_y1": bbox_px[3],
            "native_mask_pixels": int(mask.sum()), "native_ink_height_px": ink_height(mask), "native_ink_width_px": ink_width(mask),
            "crop_1x": f"crops_1x/{oid}_object_1x.png", "crop_8x": f"crops_8x/{oid}_object_8x.png",
            "mask_path": f"masks/{oid}_mask_native.png",
        })

    target_blue = np.array([31, 78, 121], dtype=np.int16)
    target_gold = np.array([183, 121, 31], dtype=np.int16)
    target_pale = np.array([239, 243, 246], dtype=np.int16)
    for oid, panel, role, content, bbox_pt, source_line in GRAPHIC_SPECS:
        bbox_px = px_rect(bbox_pt, pad=3)
        crop_arr = page_arr[bbox_px[1]:bbox_px[3], bbox_px[0]:bbox_px[2], :].astype(np.int16)
        yy, xx = np.indices(crop_arr.shape[:2])
        gx = xx + bbox_px[0]
        gy = yy + bbox_px[1]
        if oid in ("G01", "G02"):
            spread = crop_arr.max(axis=2) - crop_arr.min(axis=2)
            mask = (spread <= 4) & (crop_arr.mean(axis=2) >= 80) & (crop_arr.mean(axis=2) <= 225)
        elif oid in ("G03", "G04", "G05", "G06"):
            mask = crop_arr.mean(axis=2) < 130
        elif oid in ("G07", "G10"):
            color = np.linalg.norm(crop_arr - target_blue, axis=2) < 150
            if oid == "G07":
                xpt = gx / SCALE
                xdata = -2.0 + (xpt - 135.70) / (388.51 - 135.70) * 5.0
                yval = 0.498678 * np.exp(-0.78125 * (xdata - 0.45) ** 2)
                ypt = 465.18 - yval / 0.56 * (465.18 - 345.60)
                mask = color & (np.abs(gy - ypt * SCALE) <= 4.0)
            else:
                mask = color & (np.abs(gx - 259.58 * SCALE) <= 3.5)
        elif oid == "G08":
            dist = np.linalg.norm(crop_arr - target_pale, axis=2)
            mask = (dist < 35) & (crop_arr.min(axis=2) < 252)
        elif oid in ("G09", "G11"):
            color = np.linalg.norm(crop_arr - target_gold, axis=2) < 150
            if oid == "G09":
                xpt = gx / SCALE
                xdata = -2.0 + (xpt - 135.70) / (388.51 - 135.70) * 5.0
                yval = 0.498678 * np.exp(-0.78125 * (xdata - 0.60) ** 2)
                ypt = 465.18 - yval / 0.56 * (465.18 - 345.60)
                mask = color & (np.abs(gy - ypt * SCALE) <= 4.0)
            else:
                mask = color & (np.abs(gx - 267.16 * SCALE) <= 3.5)
        elif oid == "G12":
            spread = crop_arr.max(axis=2) - crop_arr.min(axis=2)
            mean = crop_arr.mean(axis=2)
            edge_band = (xx < 12) | (yy < 12) | (xx >= crop_arr.shape[1] - 12) | (yy >= crop_arr.shape[0] - 12)
            mask = edge_band & (spread <= 30) & (mean >= 135) & (mean <= 245)
        else:
            raise AssertionError(oid)
        object_masks[oid] = (bbox_px, mask)
        ys, xs = np.where(mask)
        object_points[oid] = np.column_stack((ys + bbox_px[1], xs + bbox_px[0])) if ys.size else np.empty((0, 2), dtype=int)
        crop1 = page_image.crop(px_rect(bbox_pt, pad=8))
        crop1.save(ROOT / "crops_1x" / f"{oid}_object_1x.png")
        crop1.resize((crop1.width * 8, crop1.height * 8), Image.Resampling.NEAREST).save(ROOT / "crops_8x" / f"{oid}_object_8x.png")
        Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(ROOT / "masks" / f"{oid}_mask_native.png")
        objects.append({
            "object_id": oid, "object_family": "GRAPHIC", "panel_id": panel, "role": role,
            "content": content, "source_line": source_line, "declared_pt": "",
            "bbox_pt_x0": bbox_pt[0], "bbox_pt_y0": bbox_pt[1], "bbox_pt_x1": bbox_pt[2], "bbox_pt_y1": bbox_pt[3],
            "bbox_px_x0": bbox_px[0], "bbox_px_y0": bbox_px[1], "bbox_px_x1": bbox_px[2], "bbox_px_y1": bbox_px[3],
            "native_mask_pixels": int(mask.sum()), "native_ink_height_px": ink_height(mask), "native_ink_width_px": ink_width(mask),
            "crop_1x": f"crops_1x/{oid}_object_1x.png", "crop_8x": f"crops_8x/{oid}_object_8x.png",
            "mask_path": f"masks/{oid}_mask_native.png",
        })

    object_fields = list(objects[0].keys())
    csv_write(ROOT / "inventory" / "actual_object_inventory.csv", object_fields, objects)

    # PDF-native glyph inventory for every non-whitespace character assigned to a text object.
    glyph_rows = []
    glyph_counter = Counter()
    text_by_id = {r[0]: r for r in TEXT_SPECS}
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    c = ch["c"]
                    if c.isspace():
                        continue
                    cb = tuple(ch["bbox"])
                    cx = (cb[0] + cb[2]) / 2
                    cy = (cb[1] + cb[3]) / 2
                    owner = None
                    for spec in TEXT_SPECS:
                        x0, y0, x1, y1 = spec[4]
                        if x0 - 0.4 <= cx <= x1 + 0.4 and y0 - 0.4 <= cy <= y1 + 0.4:
                            owner = spec[0]
                            break
                    if owner is None:
                        continue
                    glyph_counter[owner] += 1
                    gid = f"{owner}-GL{glyph_counter[owner]:03d}"
                    gbpx = px_rect(cb)
                    gcrop = page_image.crop(gbpx)
                    gmask = ink_mask_for_crop(gcrop)
                    gcrop1 = page_image.crop(px_rect(cb, pad=2))
                    gcrop1.save(ROOT / "crops_1x" / f"{gid}_glyph_1x.png")
                    gcrop1.resize((gcrop1.width * 8, gcrop1.height * 8), Image.Resampling.NEAREST).save(ROOT / "crops_8x" / f"{gid}_glyph_8x.png")
                    glyph_rows.append({
                        "glyph_id": gid, "object_id": owner, "character": c,
                        "unicode_codepoint": "+".join(f"U+{ord(k):04X}" for k in c),
                        "unicode_name": "+".join(unicodedata.name(k, "UNNAMED") for k in c),
                        "pdf_font": span["font"], "pdf_size_pt": round(span["size"], 4),
                        "bbox_pt_x0": round(cb[0], 4), "bbox_pt_y0": round(cb[1], 4), "bbox_pt_x1": round(cb[2], 4), "bbox_pt_y1": round(cb[3], 4),
                        "bbox_px_x0": gbpx[0], "bbox_px_y0": gbpx[1], "bbox_px_x1": gbpx[2], "bbox_px_y1": gbpx[3],
                        "native_ink_pixels": int(gmask.sum()), "native_ink_height_px": ink_height(gmask), "native_ink_width_px": ink_width(gmask),
                        "crop_1x": f"crops_1x/{gid}_glyph_1x.png", "crop_8x": f"crops_8x/{gid}_glyph_8x.png",
                    })
    glyph_fields = list(glyph_rows[0].keys())
    csv_write(ROOT / "inventory" / "glyph_inventory.csv", glyph_fields, glyph_rows)

    # PDF-native span/font facts corresponding to each text object.
    font_rows = []
    for obj in [o for o in objects if o["object_family"] == "TEXT"]:
        oid = obj["object_id"]
        rows = [g for g in glyph_rows if g["object_id"] == oid]
        sizes = [float(g["pdf_size_pt"]) for g in rows]
        fonts = sorted({g["pdf_font"] for g in rows})
        font_rows.append({
            "element_id": oid, "role": obj["role"], "source_line": obj["source_line"],
            "declared_pt": obj["declared_pt"], "graphics_scale": 1.0,
            "pdf_span_size_min_pt": min(sizes) if sizes else "", "pdf_span_size_max_pt": max(sizes) if sizes else "",
            "pdf_fonts": "|".join(fonts), "native_ink_height_px": obj["native_ink_height_px"],
            "native_mask_pixels": obj["native_mask_pixels"],
        })
    csv_write(ROOT / "inventory" / "source_and_pdf_font_facts.csv", list(font_rows[0].keys()), font_rows)

    # Mechanical all-unordered-pair measurements. No reviewer, Boolean, decision, or note columns are generated here.
    pair_rows = []
    critical_rows = []
    obj_by_id = {o["object_id"]: o for o in objects}
    for seq, (a, b) in enumerate(itertools.combinations(objects, 2), start=1):
        aid, bid = a["object_id"], b["object_id"]
        abox = (a["bbox_px_x0"], a["bbox_px_y0"], a["bbox_px_x1"], a["bbox_px_y1"])
        bbox = (b["bbox_px_x0"], b["bbox_px_y0"], b["bbox_px_x1"], b["bbox_px_y1"])
        overlap = 0
        ix0, iy0 = max(abox[0], bbox[0]), max(abox[1], bbox[1])
        ix1, iy1 = min(abox[2], bbox[2]), min(abox[3], bbox[3])
        if ix1 > ix0 and iy1 > iy0:
            ar, am = object_masks[aid]
            br, bm = object_masks[bid]
            asub = am[iy0-ar[1]:iy1-ar[1], ix0-ar[0]:ix1-ar[0]]
            bsub = bm[iy0-br[1]:iy1-br[1], ix0-br[0]:ix1-br[0]]
            overlap = int(np.logical_and(asub, bsub).sum())
        apoints, bpoints = object_points[aid], object_points[bid]
        if overlap:
            min_dist = 0.0
        elif len(apoints) and len(bpoints):
            if len(apoints) <= len(bpoints):
                tree = cKDTree(bpoints)
                min_dist = float(tree.query(apoints, k=1)[0].min())
            else:
                tree = cKDTree(apoints)
                min_dist = float(tree.query(bpoints, k=1)[0].min())
        else:
            min_dist = float("nan")
        pid = f"PAIR-{seq:04d}"
        row = {
            "pair_id": pid, "object_a": aid, "object_b": bid,
            "family_a": a["object_family"], "family_b": b["object_family"],
            "role_a": a["role"], "role_b": b["role"],
            "bbox_gap_px": round(bbox_gap(abox, bbox), 3),
            "bbox_intersection_area_px2": round(bbox_intersection_area(abox, bbox), 3),
            "native_mask_shared_pixels": overlap,
            "native_mask_min_distance_px": "" if math.isnan(min_dist) else round(min_dist, 3),
        }
        pair_rows.append(row)
        text_graphic = {a["object_family"], b["object_family"]} == {"TEXT", "GRAPHIC"}
        text_text = a["object_family"] == b["object_family"] == "TEXT"
        semantic_contact = {aid, bid} in [
            {"G01", "G03"}, {"G01", "G04"}, {"G02", "G05"}, {"G02", "G06"},
            {"G07", "G10"}, {"G09", "G11"}, {"G07", "G09"},
        ]
        near = (not math.isnan(min_dist) and min_dist <= 16.0) or overlap > 0
        if overlap > 0 or semantic_contact or ((text_graphic or text_text) and near):
            trigger = "native_shared_pixels" if overlap > 0 else ("semantic_contact" if semantic_contact else "near_native_pixels")
            crow = dict(row)
            crow["inventory_trigger"] = trigger
            critical_rows.append(crow)
            union = bbox_union(abox, bbox)
            c1 = page_image.crop((max(0, union[0]-12), max(0, union[1]-12), min(page_image.width, union[2]+12), min(page_image.height, union[3]+12)))
            c1.save(ROOT / "pairs" / f"{pid}_critical_1x.png")
            c1.resize((c1.width*8, c1.height*8), Image.Resampling.NEAREST).save(ROOT / "pairs" / f"{pid}_critical_8x.png")
    csv_write(ROOT / "pairs" / "all_unordered_pair_measurements.csv", list(pair_rows[0].keys()), pair_rows)
    csv_write(ROOT / "pairs" / "critical_pair_inventory.csv", list(critical_rows[0].keys()), critical_rows)

    # Same-role peer inventories are objective membership/pixel-ratio facts only.
    peer_rows = []
    seq = 0
    for role, members_it in itertools.groupby(sorted([o for o in objects if o["object_family"] == "TEXT"], key=lambda x: x["role"]), key=lambda x: x["role"]):
        members = list(members_it)
        for a, b in itertools.combinations(members, 2):
            seq += 1
            ha, hb = int(a["native_ink_height_px"]), int(b["native_ink_height_px"])
            ratio = max(ha, hb) / min(ha, hb) if min(ha, hb) else ""
            peer_rows.append({
                "peer_pair_id": f"PEER-{seq:03d}", "role": role, "object_a": a["object_id"], "object_b": b["object_id"],
                "native_ink_height_a_px": ha, "native_ink_height_b_px": hb,
                "max_to_min_native_ink_height_ratio": "" if ratio == "" else round(ratio, 4),
                "pdf_declared_pt_a": a["declared_pt"], "pdf_declared_pt_b": b["declared_pt"],
            })
    csv_write(ROOT / "pairs" / "peer_role_measurements.csv", list(peer_rows[0].keys()), peer_rows)

    clip_rows = []
    fig_px = px_rect(FIGURE_RECT_PT)
    plot_px = px_rect(PLOT_RECT_PT)
    for o in objects:
        b = (o["bbox_px_x0"], o["bbox_px_y0"], o["bbox_px_x1"], o["bbox_px_y1"])
        page_edges = (b[0], b[1], page_image.width-b[2], page_image.height-b[3])
        fig_edges = (b[0]-fig_px[0], b[1]-fig_px[1], fig_px[2]-b[2], fig_px[3]-b[3])
        plot_edges = (b[0]-plot_px[0], b[1]-plot_px[1], plot_px[2]-b[2], plot_px[3]-b[3])
        clip_rows.append({
            "clip_id": f"CLIP-{o['object_id']}", "object_id": o["object_id"], "panel_id": o["panel_id"],
            "page_left_px": page_edges[0], "page_top_px": page_edges[1], "page_right_px": page_edges[2], "page_bottom_px": page_edges[3],
            "figure_crop_left_px": fig_edges[0], "figure_crop_top_px": fig_edges[1], "figure_crop_right_px": fig_edges[2], "figure_crop_bottom_px": fig_edges[3],
            "standalone_equivalent_left_px": plot_edges[0], "standalone_equivalent_top_px": plot_edges[1], "standalone_equivalent_right_px": plot_edges[2], "standalone_equivalent_bottom_px": plot_edges[3],
        })
    csv_write(ROOT / "inventory" / "clip_edge_measurements.csv", list(clip_rows[0].keys()), clip_rows)

    overlay = page_image.copy()
    draw = ImageDraw.Draw(overlay)
    for o in objects:
        b = (o["bbox_px_x0"], o["bbox_px_y0"], o["bbox_px_x1"], o["bbox_px_y1"])
        color = (220, 20, 60) if o["object_family"] == "TEXT" else (0, 100, 220)
        draw.rectangle(b, outline=color, width=2)
        draw.rectangle((b[0], max(0,b[1]-14), b[0]+44, b[1]), fill=(255,255,255))
        draw.text((b[0]+1, max(0,b[1]-13)), o["object_id"], fill=color)
    overlay.crop(px_rect(FIGURE_RECT_PT)).save(ROOT / "render" / "actual_object_overlay_native_300dpi.png")

    def contact_sheet(paths, output, columns, cell_w, cell_h, title_h=24):
        paths = list(paths)
        rows = math.ceil(len(paths) / columns)
        sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
        sd = ImageDraw.Draw(sheet)
        for i, p in enumerate(paths):
            im = Image.open(p).convert("RGB")
            max_w, max_h = cell_w - 12, cell_h - title_h - 8
            ratio = min(max_w / im.width, max_h / im.height, 1.0)
            if ratio < 1.0:
                im = im.resize((max(1, round(im.width*ratio)), max(1, round(im.height*ratio))), Image.Resampling.NEAREST)
            x = (i % columns) * cell_w + (cell_w - im.width) // 2
            y = (i // columns) * cell_h + title_h + (cell_h - title_h - im.height) // 2
            sheet.paste(im, (x, y))
            sd.text(((i % columns) * cell_w + 4, (i // columns) * cell_h + 4), p.stem, fill=(0,0,0))
        sheet.save(output)

    contact_sheet(sorted((ROOT / "crops_8x").glob("T??_object_8x.png")), ROOT / "render" / "text_object_contact_sheet_8x.png", 4, 560, 210)
    glyph_paths = sorted((ROOT / "crops_8x").glob("T??-GL???_glyph_8x.png"))
    for sheet_no in range(math.ceil(len(glyph_paths) / 40)):
        chunk = glyph_paths[sheet_no*40:(sheet_no+1)*40]
        contact_sheet(chunk, ROOT / "render" / f"glyph_contact_sheet_8x_{sheet_no+1:02d}.png", 8, 220, 150)
    critical_paths = sorted((ROOT / "pairs").glob("PAIR-*_critical_8x.png"))
    for sheet_no in range(math.ceil(len(critical_paths) / 12)):
        chunk = critical_paths[sheet_no*12:(sheet_no+1)*12]
        contact_sheet(chunk, ROOT / "render" / f"critical_pair_contact_sheet_8x_{sheet_no+1:02d}.png", 3, 620, 330)

    mapping = {
        "figure_id": "FIG-P639-01",
        "canonical_label": "fig:V5-C04-bivariate-normal-conditionals",
        "official_r104_pdf": str(PDF),
        "pdf_page_count": pdf_doc.page_count,
        "physical_page_1_based": PHYSICAL_PAGE,
        "printed_page": PRINTED_PAGE,
        "figure_number": "33.6",
        "page_size_pt": [page.rect.width, page.rect.height],
        "native_dpi": DPI,
        "native_full_page_pixels": [page_image.width, page_image.height],
        "source_file": str(SOURCE),
        "context_file": str(CONTEXT),
        "caption_source_line": 33,
        "label_source_line": 34,
        "context_reference_lines": [408, 409],
        "figure_rect_pt": FIGURE_RECT_PT,
        "standalone_equivalent_rect_pt": PLOT_RECT_PT,
    }
    (ROOT / "inventory" / "page_mapping_and_render_geometry.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    multiview_rows = []
    for p in sorted((ROOT / "render").glob("*.png")):
        with Image.open(p) as im:
            multiview_rows.append({"view_id": p.stem, "relative_path": p.relative_to(ROOT).as_posix(), "width_px": im.width, "height_px": im.height, "dpi_basis": "300_native_or_crop_of_300_native"})
    csv_write(ROOT / "inventory" / "multiview_inventory.csv", list(multiview_rows[0].keys()), multiview_rows)

    summary = {
        "actual_objects": len(objects),
        "text_objects": sum(o["object_family"] == "TEXT" for o in objects),
        "graphic_objects": sum(o["object_family"] == "GRAPHIC" for o in objects),
        "glyphs": len(glyph_rows),
        "unordered_pairs": len(pair_rows),
        "expected_unordered_pairs": len(objects) * (len(objects)-1) // 2,
        "critical_pairs": len(critical_rows),
        "peer_role_pairs": len(peer_rows),
        "clip_rows": len(clip_rows),
    }
    (ROOT / "inventory" / "mechanical_counts.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
