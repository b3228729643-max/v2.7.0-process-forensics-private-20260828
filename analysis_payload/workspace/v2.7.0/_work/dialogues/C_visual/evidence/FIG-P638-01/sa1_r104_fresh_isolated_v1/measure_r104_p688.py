from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_gibbs_vs_mh.tex")
OUT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P638-01\sa1_r104_fresh_isolated_v1")
PAGE_INDEX = 687
SCALE = 300.0 / 72.0


TEXT_ELEMENTS = [
    dict(id="E001", panel="P_TOP", role="NODE_HEADING", line=14, declared=9.2, sample="1 精确满条件提议", rect=(140, 251, 231, 269), bg=(255, 255, 255)),
    dict(id="E002", panel="P_TOP", role="FORMULA", line=14, declared=9.2, sample="q_j=π(x_j∣x_{−j})", rect=(145, 268, 221, 282), bg=(255, 255, 255)),
    dict(id="E003", panel="P_TOP", role="NODE_HEADING", line=15, declared=9.2, sample="2 MH 比值逐项抵消", rect=(255, 247, 351, 264), bg=(255, 255, 255)),
    dict(id="E004", panel="P_TOP", role="FORMULA", line=15, declared=9.2, sample="R=[π(y)π_j(x_j∣x_{−j})]/[π(x)π_j(y_j∣x_{−j})]=1", rect=(246, 261, 360, 289), bg=(255, 255, 255)),
    dict(id="E005", panel="P_TOP", role="NODE_HEADING", line=16, declared=9.2, sample="3 α=1", rect=(399, 251, 446, 269), bg=(255, 255, 255)),
    dict(id="E006", panel="P_TOP", role="NODE_ACTION", line=16, declared=9.2, sample="直接接受 x_j←y_j", rect=(382, 267, 462, 282), bg=(255, 255, 255)),
    dict(id="E007", panel="P_EXCEPTION", role="EXCEPTION_TEXT", line=20, declared=9.2, sample="近似满条件 / 其他提议 q_j", rect=(248, 312, 356, 327), bg=(255, 244, 244)),
    dict(id="E008", panel="P_EXCEPTION", role="EXCEPTION_TEXT", line=20, declared=9.2, sample="恢复 MH 接受率校正；拒绝时保持 x_j（自环）", rect=(208, 325, 403, 341), bg=(255, 244, 244)),
    dict(id="E009", panel="P_CAPTION", role="CAPTION", line=25, declared=9.96, sample="图 33.5 … Gibbs 更", rect=(85, 346, 522, 364), bg=(255, 255, 255)),
    dict(id="E010", panel="P_CAPTION", role="CAPTION", line=25, declared=9.96, sample="新无需拒绝；…拒绝自环", rect=(85, 363, 470, 378), bg=(255, 255, 255)),
]


GRAPHIC_OBJECTS = [
    dict(id="G001", panel="P_TOP", role="FLOW_PATH", line=17, sample="q--r--a, terminal Stealth", rect=(235.8, 267.7, 369.1, 271.2), color="blue"),
    dict(id="G002", panel="P_DIVIDER", role="DECORATIVE_DIVIDER", line=18, sample="horizontal separator", rect=(129.8, 292.7, 476.8, 294.4), color="gray"),
    dict(id="G003", panel="P_EXCEPTION", role="NODE_BORDER", line=19, sample="rounded exception border", rect=(191.8, 306.8, 414.8, 345.5), color="red"),
    dict(id="G004", panel="P_EXCEPTION", role="WARN_ARROW", line=21, sample="q.south to w.north west", rect=(183.3, 288.3, 192.5, 306.7), color="red"),
    dict(id="G005", panel="P_EXCEPTION", role="WARN_ARROW", line=22, sample="a.south to w.north east", rect=(414.1, 288.3, 423.3, 306.7), color="red"),
    dict(id="G006", panel="P_TOP", role="FORMULA_RULE", line=15, sample="fraction rule inside R", rect=(268.7, 273.8, 339.9, 275.2), color="dark"),
]


def px_rect(rect):
    x0, y0, x1, y1 = rect
    return (
        max(0, math.floor(x0 * SCALE)),
        max(0, math.floor(y0 * SCALE)),
        math.ceil(x1 * SCALE),
        math.ceil(y1 * SCALE),
    )


def rect_distance(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0)
    dy = max(by0 - ay1, ay0 - by1, 0)
    return math.hypot(dx, dy)


def bbox_intersection_area(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def text_mask(rgb, element, owned_glyphs):
    mask = np.zeros(rgb.shape[:2], dtype=bool)
    bg = np.array(element["bg"], dtype=np.int16)
    for glyph in owned_glyphs:
        x0, y0, x1, y1 = px_rect(glyph["bbox"])
        tile = rgb[y0:y1, x0:x1].astype(np.int16)
        local = np.max(np.abs(tile - bg), axis=2) >= 20
        mask[y0:y1, x0:x1] |= local
    return mask


def graphic_mask(rgb, obj):
    mask = np.zeros(rgb.shape[:2], dtype=bool)
    x0, y0, x1, y1 = px_rect(obj["rect"])
    tile = rgb[y0:y1, x0:x1].astype(np.int16)
    r, g, b = tile[:, :, 0], tile[:, :, 1], tile[:, :, 2]
    if obj["color"] == "blue":
        local = (b - r >= 18) & (b - g >= 8) & (255 - b >= 20)
    elif obj["color"] == "red":
        local = (r - g >= 22) & (r - b >= 12) & (255 - r >= 8)
    elif obj["color"] == "gray":
        local = (np.max(tile, axis=2) - np.min(tile, axis=2) <= 28) & (np.mean(tile, axis=2) <= 235)
    else:
        local = np.mean(tile, axis=2) <= 225
    mask[y0:y1, x0:x1] = local
    return mask


def mask_bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return (None, None, None, None)
    return (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))


def mask_height(mask):
    ys = np.flatnonzero(mask.any(axis=1))
    return int(ys[-1] - ys[0] + 1) if len(ys) else 0


def write_mask(path, mask, crop):
    x0, y0, x1, y1 = crop
    im = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8), mode="L")
    im.save(path)


def collect_glyphs(page):
    glyphs = []
    raw = page.get_text("rawdict")
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    c = char["c"]
                    if not c or c.isspace():
                        continue
                    bbox = tuple(float(v) for v in char["bbox"])
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2
                    owner = None
                    for element in TEXT_ELEMENTS:
                        x0, y0, x1, y1 = element["rect"]
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            owner = element
                            break
                    if owner is None:
                        continue
                    glyphs.append(
                        dict(
                            element_id=owner["id"],
                            panel_id=owner["panel"],
                            role=owner["role"],
                            char=c,
                            codepoint=f"U+{ord(c):04X}",
                            font=span["font"],
                            pdf_size_pt=float(span["size"]),
                            bbox=bbox,
                        )
                    )
    for idx, glyph in enumerate(glyphs, 1):
        glyph["glyph_id"] = f"GL{idx:04d}"
    return glyphs


def glyph_ink_height(rgb, glyph, bg):
    x0, y0, x1, y1 = px_rect(glyph["bbox"])
    x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
    x1, y1 = min(rgb.shape[1], x1 + 1), min(rgb.shape[0], y1 + 1)
    tile = rgb[y0:y1, x0:x1].astype(np.int16)
    background = np.array(bg, dtype=np.int16)
    local = np.max(np.abs(tile - background), axis=2) >= 20
    return mask_height(local)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(OUT / "full_page_300dpi.png").convert("RGB")
    rgb = np.asarray(image)
    if image.size != (2481, 3508):
        raise RuntimeError(f"unexpected 300 dpi page size: {image.size}")

    # Direct 300 dpi crops. Only the explicitly named 8x files are enlarged,
    # with nearest-neighbour sampling, and are never used for measurement.
    figure_crop = (320, 1000, 2200, 1585)
    standalone_crop = (500, 1015, 2000, 1445)
    image.crop(figure_crop).save(OUT / "figure_crop_300dpi.png")
    image.crop(figure_crop).save(OUT / "figure_crop_1x.png")
    image.crop(standalone_crop).save(OUT / "standalone_equivalent_300dpi.png")
    image.crop(figure_crop).convert("L").save(OUT / "grayscale_300dpi.png")

    zones = {
        "critical_top_flow_8x.png": (540, 1025, 1960, 1195),
        "critical_exception_8x.png": (735, 1190, 1745, 1450),
        "critical_caption_8x.png": (340, 1435, 2180, 1580),
    }
    for name, crop in zones.items():
        z = image.crop(crop)
        z.resize((z.width * 8, z.height * 8), Image.Resampling.NEAREST).save(OUT / name)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    glyphs = collect_glyphs(page)

    masks = {}
    raw_candidate_masks = {}
    inventory_rows = []
    for element in TEXT_ELEMENTS:
        mask = text_mask(rgb, element, [g for g in glyphs if g["element_id"] == element["id"]])
        if element["id"] in {"E003", "E004"}:
            raw_candidate_masks[element["id"]] = mask.copy()
        # The two PDF text bboxes overlap by 0.16 pt, so direct bbox-derived
        # masks duplicate pixels from the adjacent run. Native 300 dpi row
        # occupancy has E003 ending at y=1085 and E004 starting at y=1092;
        # y=1089 is therefore a neutral separation plane for layer masks.
        if element["id"] == "E003":
            mask[1089:, :] = False
        elif element["id"] == "E004":
            mask[:1089, :] = False
        masks[element["id"]] = mask
        ib = mask_bbox(mask)
        inventory_rows.append(
            dict(
                object_id=element["id"], object_class="TEXT", panel_id=element["panel"], role=element["role"],
                source_file=str(SOURCE), source_line=element["line"], text_or_description=element["sample"],
                bbox_x0_px=px_rect(element["rect"])[0], bbox_y0_px=px_rect(element["rect"])[1],
                bbox_x1_px=px_rect(element["rect"])[2], bbox_y1_px=px_rect(element["rect"])[3],
                ink_x0_px=ib[0], ink_y0_px=ib[1], ink_x1_px=ib[2], ink_y1_px=ib[3],
                ink_pixel_count=int(mask.sum()), h_ink_px=mask_height(mask),
            )
        )
    for obj in GRAPHIC_OBJECTS:
        mask = graphic_mask(rgb, obj)
        masks[obj["id"]] = mask
        ib = mask_bbox(mask)
        inventory_rows.append(
            dict(
                object_id=obj["id"], object_class="GRAPHIC", panel_id=obj["panel"], role=obj["role"],
                source_file=str(SOURCE), source_line=obj["line"], text_or_description=obj["sample"],
                bbox_x0_px=px_rect(obj["rect"])[0], bbox_y0_px=px_rect(obj["rect"])[1],
                bbox_x1_px=px_rect(obj["rect"])[2], bbox_y1_px=px_rect(obj["rect"])[3],
                ink_x0_px=ib[0], ink_y0_px=ib[1], ink_x1_px=ib[2], ink_y1_px=ib[3],
                ink_pixel_count=int(mask.sum()), h_ink_px=mask_height(mask),
            )
        )

    with (OUT / "object_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=inventory_rows[0].keys())
        writer.writeheader()
        writer.writerows(inventory_rows)

    mask_dir = OUT / "object_masks"
    mask_dir.mkdir(exist_ok=True)
    mask_crop = figure_crop
    for oid, mask in masks.items():
        write_mask(mask_dir / f"{oid}_mask_300dpi.png", mask, mask_crop)
    for oid, mask in raw_candidate_masks.items():
        write_mask(mask_dir / f"{oid}_raw_bbox_mask_300dpi.png", mask, mask_crop)
    raw_overlap = raw_candidate_masks["E003"] & raw_candidate_masks["E004"]
    write_mask(mask_dir / "E003_E004_raw_bbox_overlap_300dpi.png", raw_overlap, mask_crop)
    with (OUT / "raw_mask_candidate_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "object_a", "object_b", "raw_bbox_derived_overlap_px", "native_last_ink_row_a", "native_first_ink_row_b", "blank_rows_between"])
        writer.writeheader()
        writer.writerow(dict(candidate_id="MC001", object_a="E003", object_b="E004", raw_bbox_derived_overlap_px=int(raw_overlap.sum()), native_last_ink_row_a=1085, native_first_ink_row_b=1092, blank_rows_between=6))

    # Element and glyph measurements: numeric facts only, with no reviewer decision.
    element_measurements = []
    for element in TEXT_ELEMENTS:
        owned = [g for g in glyphs if g["element_id"] == element["id"]]
        sizes = sorted({round(g["pdf_size_pt"], 4) for g in owned})
        heights = [glyph_ink_height(rgb, g, element["bg"]) for g in owned]
        element_measurements.append(
            dict(
                element_id=element["id"], panel_id=element["panel"], role=element["role"], source_file=str(SOURCE),
                source_line=element["line"], declared_pt=element["declared"], graphics_scale=1.0,
                effective_pt=element["declared"], text_sample=element["sample"], pdf_font_sizes_pt="|".join(map(str, sizes)),
                glyph_count=len(owned), object_h_ink_px=mask_height(masks[element["id"]]),
                min_glyph_h_ink_px=min(heights) if heights else "", median_glyph_h_ink_px=round(float(np.median(heights)), 3) if heights else "",
                max_glyph_h_ink_px=max(heights) if heights else "",
            )
        )
    with (OUT / "element_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=element_measurements[0].keys())
        writer.writeheader()
        writer.writerows(element_measurements)

    glyph_rows = []
    owner_by_id = {e["id"]: e for e in TEXT_ELEMENTS}
    for glyph in glyphs:
        owner = owner_by_id[glyph["element_id"]]
        r = px_rect(glyph["bbox"])
        glyph_rows.append(
            dict(
                glyph_id=glyph["glyph_id"], element_id=glyph["element_id"], panel_id=glyph["panel_id"], role=glyph["role"],
                glyph=glyph["char"], codepoint=glyph["codepoint"], font=glyph["font"], pdf_size_pt=round(glyph["pdf_size_pt"], 4),
                bbox_x0_px=r[0], bbox_y0_px=r[1], bbox_x1_px=r[2], bbox_y1_px=r[3],
                h_ink_px=glyph_ink_height(rgb, glyph, owner["bg"]),
                distance_to_page_edge_px=min(r[0], r[1], image.width - r[2], image.height - r[3]),
            )
        )
    with (OUT / "glyph_inventory.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=glyph_rows[0].keys())
        writer.writeheader()
        writer.writerows(glyph_rows)

    glyph_pair_fields = ["pair_id", "glyph_a", "glyph_b", "element_a", "element_b", "same_element", "bbox_intersection_area_px", "bbox_clearance_px"]
    with (OUT / "all_unordered_glyph_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=glyph_pair_fields)
        writer.writeheader()
        for idx, (a, b) in enumerate(itertools.combinations(glyph_rows, 2), 1):
            ra = (a["bbox_x0_px"], a["bbox_y0_px"], a["bbox_x1_px"], a["bbox_y1_px"])
            rb = (b["bbox_x0_px"], b["bbox_y0_px"], b["bbox_x1_px"], b["bbox_y1_px"])
            writer.writerow(dict(
                pair_id=f"GP{idx:06d}", glyph_a=a["glyph_id"], glyph_b=b["glyph_id"], element_a=a["element_id"], element_b=b["element_id"],
                same_element=str(a["element_id"] == b["element_id"]).lower(), bbox_intersection_area_px=bbox_intersection_area(ra, rb),
                bbox_clearance_px=round(rect_distance(ra, rb), 3),
            ))

    object_by_id = {row["object_id"]: row for row in inventory_rows}
    mask_coords = {oid: np.column_stack(np.nonzero(mask)) for oid, mask in masks.items()}
    mask_trees = {oid: cKDTree(coords) if len(coords) else None for oid, coords in mask_coords.items()}
    object_pair_rows = []
    for idx, (a_id, b_id) in enumerate(itertools.combinations(masks.keys(), 2), 1):
        a, b = masks[a_id], masks[b_id]
        overlap = int(np.logical_and(a, b).sum())
        if a.any() and b.any():
            if overlap:
                clearance = 0.0
            else:
                ca, cb = mask_coords[a_id], mask_coords[b_id]
                if len(ca) <= len(cb):
                    clearance = float(mask_trees[b_id].query(ca, k=1, workers=-1)[0].min())
                else:
                    clearance = float(mask_trees[a_id].query(cb, k=1, workers=-1)[0].min())
        else:
            clearance = float("nan")
        ar = object_by_id[a_id]
        br = object_by_id[b_id]
        ra = (ar["bbox_x0_px"], ar["bbox_y0_px"], ar["bbox_x1_px"], ar["bbox_y1_px"])
        rb = (br["bbox_x0_px"], br["bbox_y0_px"], br["bbox_x1_px"], br["bbox_y1_px"])
        object_pair_rows.append(dict(
            pair_id=f"OP{idx:04d}", object_a=a_id, object_b=b_id, class_a=ar["object_class"], class_b=br["object_class"],
            role_a=ar["role"], role_b=br["role"], bbox_intersection_area_px=bbox_intersection_area(ra, rb),
            bbox_clearance_px=round(rect_distance(ra, rb), 3), exact_mask_overlap_px=overlap,
            exact_ink_center_clearance_px="" if math.isnan(clearance) else round(clearance, 3),
        ))
    with (OUT / "all_unordered_object_pairs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=object_pair_rows[0].keys())
        writer.writeheader()
        writer.writerows(object_pair_rows)

    # Mechanical list of pairs close enough to warrant human inspection.
    critical = [row for row in object_pair_rows if row["bbox_clearance_px"] <= 35 or row["exact_mask_overlap_px"] > 0]
    with (OUT / "critical_pair_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=critical[0].keys())
        writer.writeheader()
        writer.writerows(critical)

    # Role-level numeric summaries only; R168 reviewer treatment is documented manually.
    by_role = {}
    for row in element_measurements:
        by_role.setdefault(row["role"], []).append(row)
    peer_rows = []
    for role, rows in by_role.items():
        median = float(np.median([r["object_h_ink_px"] for r in rows]))
        for row in rows:
            peer_rows.append(dict(
                element_id=row["element_id"], panel_id=row["panel_id"], role=role,
                object_h_ink_px=row["object_h_ink_px"], role_median_h_ink_px=round(median, 3),
                ratio_to_role_median=round(row["object_h_ink_px"] / median, 6) if median else "",
            ))
    with (OUT / "peer_role_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=peer_rows[0].keys())
        writer.writeheader()
        writer.writerows(peer_rows)

    # Element/glyph clip distances are geometric facts, not a PASS/FAIL decision.
    clip_rows = []
    fig = figure_crop
    for row in inventory_rows:
        r = (row["ink_x0_px"], row["ink_y0_px"], row["ink_x1_px"], row["ink_y1_px"])
        if None in r:
            d = ""
        else:
            d = min(r[0] - fig[0], r[1] - fig[1], fig[2] - r[2], fig[3] - r[3])
        clip_rows.append(dict(object_id=row["object_id"], ink_distance_to_figure_crop_edge_px=d, ink_pixel_count=row["ink_pixel_count"]))
    with (OUT / "clip_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=clip_rows[0].keys())
        writer.writeheader()
        writer.writerows(clip_rows)

    # Overlay object boxes and IDs for traceability.
    overlay = image.crop(figure_crop).copy()
    draw = ImageDraw.Draw(overlay)
    colors = {"TEXT": (0, 100, 230), "GRAPHIC": (220, 60, 20)}
    for row in inventory_rows:
        x0 = row["bbox_x0_px"] - figure_crop[0]
        y0 = row["bbox_y0_px"] - figure_crop[1]
        x1 = row["bbox_x1_px"] - figure_crop[0]
        y1 = row["bbox_y1_px"] - figure_crop[1]
        color = colors[row["object_class"]]
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        draw.text((x0 + 2, max(0, y0 - 14)), row["object_id"], fill=color)
    overlay.save(OUT / "object_measurement_overlay_300dpi.png")

    # A combined class mask for visual inspection.
    combined = Image.new("RGB", (figure_crop[2] - figure_crop[0], figure_crop[3] - figure_crop[1]), "white")
    c = np.asarray(combined).copy()
    text_union = np.zeros(rgb.shape[:2], dtype=bool)
    graphics_union = np.zeros(rgb.shape[:2], dtype=bool)
    for oid, mask in masks.items():
        if oid.startswith("E"):
            text_union |= mask
        else:
            graphics_union |= mask
    local_t = text_union[figure_crop[1]:figure_crop[3], figure_crop[0]:figure_crop[2]]
    local_g = graphics_union[figure_crop[1]:figure_crop[3], figure_crop[0]:figure_crop[2]]
    c[local_t] = (0, 90, 230)
    c[local_g] = (230, 70, 20)
    c[local_t & local_g] = (180, 0, 180)
    Image.fromarray(c).save(OUT / "combined_object_mask_300dpi.png")


if __name__ == "__main__":
    main()
