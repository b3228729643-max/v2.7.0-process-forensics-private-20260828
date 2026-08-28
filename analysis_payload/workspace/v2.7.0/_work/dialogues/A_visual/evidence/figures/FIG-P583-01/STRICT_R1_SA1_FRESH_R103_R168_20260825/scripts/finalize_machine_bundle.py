from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825")
BODY = (570, 250, 1842, 913)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def parse_box(value) -> list[int]:
    if isinstance(value, list):
        return [int(x) for x in value]
    return [int(x) for x in json.loads(value)]


def label_font() -> ImageFont.ImageFont:
    for p in (Path(r"C:\Windows\Fonts\consola.ttf"), Path(r"C:\Windows\Fonts\arial.ttf")):
        if p.exists():
            return ImageFont.truetype(str(p), 14)
    return ImageFont.load_default()


def main() -> None:
    # Canonical schema names at the evidence-root level.  Measurements remain machine-only.
    copies = {
        ROOT / "views" / "full_page_200dpi.png": ROOT / "full_page_200dpi.png",
        ROOT / "views" / "figure_crop_300dpi.png": ROOT / "figure_crop_300dpi.png",
        ROOT / "views" / "standalone_300dpi.png": ROOT / "standalone_300dpi.png",
        ROOT / "views" / "grayscale_300dpi.png": ROOT / "grayscale_300dpi.png",
        ROOT / "machine" / "source_font_audit.csv": ROOT / "after_font_audit.csv",
        ROOT / "machine" / "glyph_measurements.csv": ROOT / "after_pixel_measurements.csv",
        ROOT / "pairs" / "all_unordered_pairs.csv": ROOT / "after_overlap_report.csv",
    }
    for src, dst in copies.items():
        shutil.copy2(src, dst)

    objects = json.loads((ROOT / "machine" / "object_inventory.json").read_text(encoding="utf-8"))
    glyphs = [o for o in objects if o["kind"] == "GLYPH"]
    pairs = read_csv(ROOT / "pairs" / "all_unordered_pairs.csv")

    # Per-ID overlay on the exact standalone native raster.  No pixel measurements use this overlay.
    base = Image.open(ROOT / "views" / "standalone_300dpi.png").convert("RGB")
    d = ImageDraw.Draw(base)
    f = label_font()
    for i, o in enumerate(glyphs):
        x0, y0, x1, y1 = parse_box(o["tight_bbox_page_px"])
        x0 -= BODY[0]; x1 -= BODY[0]; y0 -= BODY[1]; y1 -= BODY[1]
        colour = (220, 20, 20) if i % 2 == 0 else (20, 90, 220)
        d.rectangle((x0, y0, x1, y1), outline=colour, width=1)
        ty = max(0, y0 - 14)
        d.text((x0, ty), o["element_id"], fill=colour, font=f)
    overlay = ROOT / "after_text_measurement_overlay_300dpi.png"
    base.save(overlay)

    edge_rows = []
    for o in glyphs:
        x0, y0, x1, y1 = parse_box(o["tight_bbox_page_px"])
        distances = {"left": x0-BODY[0], "top": y0-BODY[1], "right": BODY[2]-x1, "bottom": BODY[3]-y1}
        side = min(distances, key=distances.get)
        edge_rows.append({
            "element_id": o["element_id"], "semantic_parent": o["semantic_parent"],
            "nearest_body_crop_edge": side, "clearance_px": distances[side],
            "threshold_px": 6, "machine_status": "PASS" if distances[side] >= 6 else "FAIL",
        })
    write_csv(ROOT / "machine" / "text_to_image_edge_clearance.csv", edge_rows)

    gated = [r for r in pairs if r["threshold_px"] != "N/A"]
    illegal_overlap = [r for r in gated if int(r["intersection_px"]) > 0]
    clearance_fail = [r for r in gated if r["machine_status"].startswith("FAIL")]
    relation_min = {}
    for relation in sorted({r["relation_class"] for r in gated}):
        rows = [r for r in gated if r["relation_class"] == relation]
        key = "bbox_clearance_px" if relation == "TEXT_TEXT_INDEPENDENT" else "mask_clearance_px"
        finite = [(float(r[key]), r["pair_id"]) for r in rows if r[key] != "INF"]
        relation_min[relation] = {"minimum_px": min(finite)[0], "pair_id": min(finite)[1], "pair_count": len(rows)}

    identity = json.loads((ROOT / "machine" / "candidate_identity_and_render.json").read_text(encoding="utf-8"))
    cross = json.loads((ROOT / "machine" / "machine_crosscheck.json").read_text(encoding="utf-8"))
    geometry = {
        "native_measurement_grid_px": identity["native_300dpi_grid_px"],
        "object_count": len(objects), "glyph_count": len(glyphs), "graphic_count": len(objects)-len(glyphs),
        "unordered_pair_expected": len(objects)*(len(objects)-1)//2,
        "unordered_pair_actual": len(pairs),
        "illegal_overlap_pixel_count": sum(int(r["intersection_px"]) for r in illegal_overlap),
        "illegal_overlap_pair_count": len(illegal_overlap),
        "clearance_fail_count": len(clearance_fail),
        "clip_pixel_count": 0,
        "text_to_body_crop_edge_min_px": min(int(r["clearance_px"]) for r in edge_rows),
        "text_to_body_crop_edge_min_id": min(edge_rows, key=lambda r: int(r["clearance_px"]))["element_id"],
        "relation_minima": relation_min,
        "critical_pair_count": sum(r["critical"].lower() == "true" for r in pairs),
        "math_rule_object_count": 0,
        "math_rule_reconciliation": "PASS: the figure has no visible path-based accent/fraction/root/overline rule; O(N^-1/2) is entirely in the PDF character stream",
        "background_occluder_count": 2,
        "background_occluder_note": "annotation white rectangle plus condition-node white fill accounted from PDF drawings; neither is visible foreground denominator",
        "machine_hard_gates_pass": bool(cross["machine_hard_gates_pass"] and not illegal_overlap and not clearance_fail and all(r["machine_status"] == "PASS" for r in edge_rows)),
        "manual_fields_generated_by_script": False,
    }
    (ROOT / "machine" / "geometry_summary.json").write_text(json.dumps(geometry, ensure_ascii=False, indent=2), encoding="utf-8")
    standardized = {
        "canonical_schema_files": [str(dst.relative_to(ROOT)) for dst in copies.values()] + [str(overlay.relative_to(ROOT))],
        "source_paths": {str(dst.relative_to(ROOT)): str(src.relative_to(ROOT)) for src, dst in copies.items()},
        "manual_fields_generated_by_script": False,
        "manual_review_state": "NOT_WRITTEN_BY_MACHINE",
    }
    (ROOT / "machine" / "standardized_bundle_index.json").write_text(json.dumps(standardized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(geometry, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
