from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence"
    r"\figures\FIG-P049-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827"
)
MACHINE = ROOT / "machine"
VISUAL = ROOT / "visual"
SCOPE_X0_PT = 126.0
SCOPE_Y0_PT = 60.0
SCALE = 300.0 / 72.0


def load_atoms():
    with (MACHINE / "atomic_denominator_machine.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def bbox_px(atom):
    x0, y0, x1, y1 = json.loads(atom["pdf_bbox_pt"])
    return (
        (x0 - SCOPE_X0_PT) * SCALE,
        (y0 - SCOPE_Y0_PT) * SCALE,
        (x1 - SCOPE_X0_PT) * SCALE,
        (y1 - SCOPE_Y0_PT) * SCALE,
    )


def bbox_metrics(a, b):
    ax0, ay0, ax1, ay1 = bbox_px(a)
    bx0, by0, bx1, by1 = bbox_px(b)
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return ix * iy, math.hypot(dx, dy)


def main():
    atoms = load_atoms()
    by_id = {a["atom_id"]: a for a in atoms}
    relation_path = MACHINE / "all_unordered_pair_spatial_candidates_machine.csv"
    rows = []
    with (MACHINE / "all_unordered_pairs_machine.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        for pair in csv.DictReader(stream):
            a, b = by_id[pair["atom_id_a"]], by_id[pair["atom_id_b"]]
            area, clearance = bbox_metrics(a, b)
            rows.append(
                {
                    **pair,
                    "machine_bbox_intersection_area_px2": f"{area:.4f}",
                    "machine_bbox_clearance_px": f"{clearance:.4f}",
                    "machine_candidate_class": (
                        "BBOX_INTERSECTION" if area > 0 else "BBOX_WITHIN_8PX" if clearance < 8 else "BBOX_CLEAR"
                    ),
                }
            )
    fields = list(rows[0])
    with relation_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    n = len(atoms)
    cell = 4
    margin = 70
    matrix = Image.new("RGB", (margin + n * cell + 20, margin + n * cell + 20), "white")
    draw = ImageDraw.Draw(matrix)
    font = ImageFont.load_default()
    draw.text((8, 8), f"machine bbox relations; N={n}; C={len(rows)}", fill="black", font=font)
    for row in rows:
        i = int(row["atom_id_a"].split("-")[1]) - 1
        if row["atom_id_a"].startswith("P-"):
            i += 135
        j = int(row["atom_id_b"].split("-")[1]) - 1
        if row["atom_id_b"].startswith("P-"):
            j += 135
        cls = row["machine_candidate_class"]
        color = (210, 40, 40) if cls == "BBOX_INTERSECTION" else (245, 160, 50) if cls == "BBOX_WITHIN_8PX" else (225, 225, 225)
        for x, y in ((i, j), (j, i)):
            draw.rectangle(
                [margin + x * cell, margin + y * cell, margin + (x + 1) * cell - 1, margin + (y + 1) * cell - 1],
                fill=color,
            )
    draw.line((margin + 135 * cell, margin, margin + 135 * cell, margin + n * cell), fill=(0, 70, 210), width=2)
    draw.line((margin, margin + 135 * cell, margin + n * cell, margin + 135 * cell), fill=(0, 70, 210), width=2)
    draw.text((margin, 45), "G-001 .. G-135 | P-001 .. P-017", fill="black", font=font)
    matrix.save(VISUAL / "10_all_pair_bbox_relation_matrix.png")

    with Image.open(VISUAL / "07_atomic_scope_native300dpi_native1x.png") as source:
        source = source.convert("RGB")
        # Coordinates are in the complete scope (x=126..481 pt, y=60..247 pt).
        rois_pt = [
            (145, 126, 230, 156, "A: contour labels"),
            (286, 88, 360, 158, "B: P/gradient/tangent/right-angle"),
            (274, 72, 463, 135, "C: note guides and notes"),
            (146, 207, 354, 230, "D: inequality/formula/axis ending"),
            (124, 228, 483, 248, "E: caption"),
        ]
        panels = []
        for x0, y0, x1, y1, title in rois_pt:
            box = (
                round((x0 - SCOPE_X0_PT) * SCALE),
                round((y0 - SCOPE_Y0_PT) * SCALE),
                round((x1 - SCOPE_X0_PT) * SCALE),
                round((y1 - SCOPE_Y0_PT) * SCALE),
            )
            crop = source.crop(box)
            target_width = 1100
            scale_factor = target_width / crop.width
            crop = crop.resize((target_width, round(crop.height * scale_factor)), Image.Resampling.NEAREST)
            panel = Image.new("RGB", (crop.width, crop.height + 26), "white")
            panel.paste(crop, (0, 26))
            ImageDraw.Draw(panel).text((6, 6), title, fill="black", font=font)
            panels.append(panel)
        sheet_width = max(p.width for p in panels)
        sheet_height = sum(p.height for p in panels) + 12 * (len(panels) - 1)
        sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
        y = 0
        for panel in panels:
            sheet.paste(panel, (0, y))
            y += panel.height + 12
        sheet.save(VISUAL / "11_relation_roi_sheet_nearest_neighbor.png")

    summary = {
        "N": n,
        "C": len(rows),
        "bbox_intersection_pairs": sum(r["machine_candidate_class"] == "BBOX_INTERSECTION" for r in rows),
        "bbox_within_8px_pairs": sum(r["machine_candidate_class"] == "BBOX_WITHIN_8PX" for r in rows),
        "bbox_clear_pairs": sum(r["machine_candidate_class"] == "BBOX_CLEAR" for r in rows),
        "warning": "These are machine bbox candidates only, not pixel collisions and not manual conclusions.",
        "manual_fields": [],
    }
    (MACHINE / "pair_spatial_candidate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
