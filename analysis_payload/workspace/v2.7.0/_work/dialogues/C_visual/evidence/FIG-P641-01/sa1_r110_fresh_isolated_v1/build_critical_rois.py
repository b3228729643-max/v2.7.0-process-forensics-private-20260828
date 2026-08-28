from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1")
OUT = ROOT / "critical_rois"
CONTACT = ROOT / "contact_sheets"
PAGE = Image.open(ROOT / "full_page_native300dpi.png").convert("RGB")
PAGE_ARR = np.array(PAGE)
PAGE_W, PAGE_H = PAGE.size


def local_mask(obj):
    folder = ROOT / "masks" / ("glyph" if obj["kind"] == "TEXT_GLYPH" else "graphic")
    return np.array(Image.open(folder / obj["safe_filename"]).convert("L")) == 0


def coords(obj):
    mask = local_mask(obj)
    ys, xs = np.nonzero(mask)
    x0, y0, _, _ = obj["mask_bbox_full_px"]
    return np.column_stack((xs + x0, ys + y0))


def make_global_roi_mask(obj, roi):
    rx0, ry0, rx1, ry1 = roi
    result = np.zeros((ry1 - ry0, rx1 - rx0), dtype=bool)
    mask = local_mask(obj)
    ox0, oy0, ox1, oy1 = obj["mask_bbox_full_px"]
    ix0, iy0 = max(rx0, ox0), max(ry0, oy0)
    ix1, iy1 = min(rx1, ox1), min(ry1, oy1)
    if ix0 < ix1 and iy0 < iy1:
        result[iy0 - ry0 : iy1 - ry0, ix0 - rx0 : ix1 - rx0] = mask[iy0 - oy0 : iy1 - oy0, ix0 - ox0 : ix1 - ox0]
    return result


def tight_relation_roi(a, b):
    ac, bc = coords(a), coords(b)
    aset = set(map(tuple, ac.tolist()))
    bset = set(map(tuple, bc.tolist()))
    overlap = np.array(list(aset.intersection(bset)), dtype=int)
    if len(overlap):
        centre = overlap[len(overlap) // 2]
        pa = pb = centre
    else:
        if len(ac) <= len(bc):
            distances, indices = cKDTree(bc).query(ac, k=1)
            pick = int(np.argmin(distances))
            pa, pb = ac[pick], bc[int(indices[pick])]
        else:
            distances, indices = cKDTree(ac).query(bc, k=1)
            pick = int(np.argmin(distances))
            pb, pa = bc[pick], ac[int(indices[pick])]
    pad = 24
    x0 = max(0, int(min(pa[0], pb[0]) - pad))
    y0 = max(0, int(min(pa[1], pb[1]) - pad))
    x1 = min(PAGE_W, int(max(pa[0], pb[0]) + pad + 1))
    y1 = min(PAGE_H, int(max(pa[1], pb[1]) + pad + 1))
    return [x0, y0, x1, y1], pa.tolist(), pb.tolist(), int(len(overlap))


def save_binary(mask, path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CONTACT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "machine_objects.json").read_text(encoding="utf-8"))
    objects = {obj["element_id"]: obj for obj in data["glyphs"] + data["graphics"]}
    with (ROOT / "critical_relations.csv").open("r", newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))

    index_rows = []
    contact_payload = []
    for row in rows:
        pair_id = row["pair_id"]
        a, b = objects[row["a_id"]], objects[row["b_id"]]
        roi, nearest_a, nearest_b, overlap_points = tight_relation_roi(a, b)
        x0, y0, x1, y1 = roi
        original = PAGE.crop(tuple(roi))
        amask = make_global_roi_mask(a, roi)
        bmask = make_global_roi_mask(b, roi)
        intersection = amask & bmask
        overlay = np.array(original)
        overlay[amask] = [255, 0, 0]
        overlay[bmask] = [0, 80, 255]
        overlay[intersection] = [255, 0, 255]
        overlay_img = Image.fromarray(overlay)
        names = {
            "original_native1x": f"{pair_id.lower()}_original_native1x.png",
            "a_mask_native1x": f"{pair_id.lower()}_a_mask_native1x.png",
            "b_mask_native1x": f"{pair_id.lower()}_b_mask_native1x.png",
            "intersection_native1x": f"{pair_id.lower()}_intersection_native1x.png",
            "overlay_native1x": f"{pair_id.lower()}_overlay_native1x.png",
            "overlay_8x_nearest": f"{pair_id.lower()}_overlay_8x_nearest.png",
        }
        original.save(OUT / names["original_native1x"])
        save_binary(amask, OUT / names["a_mask_native1x"])
        save_binary(bmask, OUT / names["b_mask_native1x"])
        save_binary(intersection, OUT / names["intersection_native1x"])
        overlay_img.save(OUT / names["overlay_native1x"])
        overlay_img.resize((overlay_img.width * 8, overlay_img.height * 8), Image.Resampling.NEAREST).save(OUT / names["overlay_8x_nearest"])
        out_row = dict(row)
        out_row.update(
            {
                "roi_full_page_px": json.dumps(roi),
                "nearest_a_pixel": json.dumps(nearest_a),
                "nearest_b_pixel": json.dumps(nearest_b),
                "actual_intersection_point_count": overlap_points,
                **names,
            }
        )
        index_rows.append(out_row)
        contact_payload.append((out_row, original, overlay_img))

    fields = list(index_rows[0])
    with (ROOT / "critical_roi_index.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(index_rows)

    per_sheet = 10
    sheet_names = []
    for sheet_index in range(math.ceil(len(contact_payload) / per_sheet)):
        chunk = contact_payload[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        canvas = Image.new("RGB", (2400, 1900), "white")
        draw = ImageDraw.Draw(canvas)
        for cell_index, (row, original, overlay) in enumerate(chunk):
            col, rr = cell_index % 2, cell_index // 2
            ox, oy = col * 1200, rr * 380
            draw.text((ox + 8, oy + 8), f"{row['pair_id']} {row['a_id']} vs {row['b_id']} ov={row['raw_mask_intersection_px']} d={row['raw_mask_min_distance_px']}", fill="black")
            one = original.copy()
            one.thumbnail((360, 290), Image.Resampling.NEAREST)
            eight = overlay.resize((overlay.width * 8, overlay.height * 8), Image.Resampling.NEAREST)
            if eight.width > 700 or eight.height > 290:
                cx, cy = eight.width // 2, eight.height // 2
                eight = eight.crop((max(0, cx - 350), max(0, cy - 145), min(eight.width, cx + 350), min(eight.height, cy + 145)))
            canvas.paste(one, (ox + 10, oy + 55))
            canvas.paste(eight, (ox + 410, oy + 55))
            draw.text((ox + 10, oy + 350), "ORIGINAL native1x", fill="black")
            draw.text((ox + 410, oy + 350), "A red / B blue / intersection magenta - nearest8x", fill="black")
            row["contact_sheet"] = f"critical_contact_sheet_{sheet_index + 1:02d}.png"
            row["contact_cell"] = cell_index + 1
        name = f"critical_contact_sheet_{sheet_index + 1:02d}.png"
        canvas.save(CONTACT / name)
        sheet_names.append(name)

    (ROOT / "machine_critical_roi_summary.json").write_text(
        json.dumps(
            {
                "critical_relation_count": len(rows),
                "files_per_relation": 6,
                "ordinary_relation_file_count": len(rows) * 6,
                "contact_sheet_count": len(sheet_names),
                "contact_sheets": sheet_names,
                "machine_decisions_generated": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"critical_relations": len(rows), "roi_files": len(rows) * 6, "contact_sheets": len(sheet_names)}))


if __name__ == "__main__":
    main()
