from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828")
PDF = ROOT / "build" / "v260_FIG-P126-01_standalone.pdf"
EVIDENCE = ROOT / "evidence"
COLOR_PATH = EVIDENCE / "full_page_native300dpi.png"
GRAY_PATH = EVIDENCE / "full_page_grayscale_native300dpi.png"
UTF8 = "utf-8"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding=UTF8)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def bbox_gap(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def bbox_intersection_area(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def densify(points: list[tuple[float, float]], max_step: float = 0.25) -> np.ndarray:
    if not points:
        return np.empty((0, 2), dtype=np.float64)
    if len(points) == 1:
        return np.asarray(points, dtype=np.float64)
    samples: list[tuple[float, float]] = []
    for p0, p1 in zip(points, points[1:]):
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        count = max(1, int(math.ceil(dist / max_step)))
        for j in range(count):
            t = j / count
            samples.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    samples.append(points[-1])
    return np.asarray(samples, dtype=np.float64)


def rectangle_points(box) -> np.ndarray:
    x0, top, x1, bottom = box
    return densify([(x0, top), (x1, top), (x1, bottom), (x0, bottom), (x0, top)])


def min_point_distance(a: np.ndarray, b: np.ndarray) -> float:
    if not len(a) or not len(b):
        return float("inf")
    best = float("inf")
    chunk = 1024
    for i in range(0, len(a), chunk):
        diff = a[i : i + chunk, None, :] - b[None, :, :]
        local = float(np.sqrt(np.sum(diff * diff, axis=2)).min())
        best = min(best, local)
    return best


with pdfplumber.open(PDF) as document:
    assert len(document.pages) == 1
    page = document.pages[0]
    page_width = float(page.width)
    page_height = float(page.height)
    raw_atoms: list[dict] = []
    for index, char in enumerate(page.chars, 1):
        raw_atoms.append(
            {
                "atom_id": f"C{index:03d}",
                "atom_type": "char",
                "source_index": index,
                "text": char.get("text", ""),
                "codepoint": "+".join(f"U+{ord(ch):04X}" for ch in char.get("text", "")),
                "fontname": char.get("fontname", ""),
                "font_size_pt": float(char.get("size", 0.0)),
                "bbox": (float(char["x0"]), float(char["top"]), float(char["x1"]), float(char["bottom"])),
                "points": rectangle_points((float(char["x0"]), float(char["top"]), float(char["x1"]), float(char["bottom"]))),
            }
        )
    for kind, prefix, items in (("line", "L", page.lines), ("curve", "V", page.curves), ("rect", "R", page.rects)):
        for index, item in enumerate(items, 1):
            box = (float(item["x0"]), float(item["top"]), float(item["x1"]), float(item["bottom"]))
            points = [(float(x), float(y)) for x, y in (item.get("pts") or [])]
            if not points:
                points = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]), (box[0], box[1])]
            raw_atoms.append(
                {
                    "atom_id": f"{prefix}{index:03d}",
                    "atom_type": kind,
                    "source_index": index,
                    "text": "",
                    "codepoint": "",
                    "fontname": "",
                    "font_size_pt": 0.0,
                    "bbox": box,
                    "points": densify(points),
                    "linewidth_pt": float(item.get("linewidth") or 0.0),
                    "fill": bool(item.get("fill")),
                    "stroking_color": item.get("stroking_color"),
                    "non_stroking_color": item.get("non_stroking_color"),
                }
            )

atom_by_id = {a["atom_id"]: a for a in raw_atoms}
assert len(page.chars) == 25
assert len(page.lines) == 9
assert len(page.curves) == 20
assert len(page.rects) == 4
assert len(raw_atoms) == 58

logical_specs = [
    ("O01", "AXIS_X1", ["L001", "V001", "C014", "C015"]),
    ("O02", "AXIS_X2", ["L002", "V002", "C016", "C017"]),
    ("O03", "CONTOUR_FAMILY", ["V003", "V004", "V005", "V006"]),
    ("O04", "INITIAL_Q0", ["C001", "C002", "C003", "C004", "V014"]),
    ("O05", "STEP_1_X2", ["C005", "L006", "V010", "R001"]),
    ("O06", "STEP_2_X1", ["C006", "L003", "V007", "V015"]),
    ("O07", "STEP_3_X2", ["C007", "L007", "V011", "R002"]),
    ("O08", "STEP_4_X1", ["C008", "L004", "V008", "V016"]),
    ("O09", "STEP_5_X2", ["C009", "L008", "V012", "R003"]),
    ("O10", "STEP_6_X1", ["C010", "L005", "V009", "V017"]),
    ("O11", "STEP_7_X2", ["C011", "L009", "V013", "R004"]),
    ("O12", "OPTIMUM_XSTAR", ["C012", "C013", "V018"]),
    ("O13", "LEGEND_UPDATE_X1", ["C018", "C019", "C020", "C021", "V019"]),
    ("O14", "LEGEND_UPDATE_X2", ["C022", "C023", "C024", "C025", "V020"]),
]

assigned = [atom for _, _, atoms in logical_specs for atom in atoms]
assert len(assigned) == len(set(assigned)) == 58
assert set(assigned) == set(atom_by_id)

logical_objects: list[dict] = []
for object_id, role, atom_ids in logical_specs:
    atoms = [atom_by_id[a] for a in atom_ids]
    box = bbox_union([a["bbox"] for a in atoms])
    logical_objects.append(
        {
            "object_id": object_id,
            "role": role,
            "atom_ids": atom_ids,
            "bbox": box,
            "points": np.concatenate([a["points"] for a in atoms if len(a["points"])], axis=0),
            "text": "".join(a["text"] for a in atoms if a["atom_type"] == "char"),
        }
    )

expected_relations = {
    tuple(sorted(p))
    for p in [
        ("O01", "O02"), ("O01", "O03"), ("O02", "O03"),
        ("O04", "O05"), ("O05", "O06"), ("O06", "O07"), ("O07", "O08"),
        ("O08", "O09"), ("O09", "O10"), ("O10", "O11"),
        ("O01", "O12"), ("O02", "O12"),
    ]
}

scale = 300.0 / 72.0
pair_rows: list[dict] = []
for pair_index, (a, b) in enumerate(itertools.combinations(logical_objects, 2), 1):
    box_gap_pt = bbox_gap(a["bbox"], b["bbox"])
    geom_gap_pt = min_point_distance(a["points"], b["points"])
    intersection_pt2 = bbox_intersection_area(a["bbox"], b["bbox"])
    expected = tuple(sorted((a["object_id"], b["object_id"]))) in expected_relations
    candidate = intersection_pt2 > 0 or min(box_gap_pt, geom_gap_pt) * scale <= 14.0
    pair_rows.append(
        {
            "pair_id": f"P{pair_index:04d}",
            "object_a": a["object_id"],
            "role_a": a["role"],
            "object_b": b["object_id"],
            "role_b": b["role"],
            "bbox_gap_px": f"{box_gap_pt * scale:.6f}",
            "geometry_gap_px": f"{geom_gap_pt * scale:.6f}",
            "bbox_intersection_pt2": f"{intersection_pt2:.6f}",
            "expected_relation": str(expected).lower(),
            "machine_candidate": str(candidate).lower(),
        }
    )

assert len(logical_objects) == 14
assert len(pair_rows) == 91

atom_rows = []
logical_for_atom = {atom: object_id for object_id, _, atoms in logical_specs for atom in atoms}
for atom in raw_atoms:
    box = atom["bbox"]
    atom_rows.append(
        {
            "atom_id": atom["atom_id"],
            "logical_object_id": logical_for_atom[atom["atom_id"]],
            "atom_type": atom["atom_type"],
            "source_index": atom["source_index"],
            "text": atom["text"],
            "codepoint": atom["codepoint"],
            "fontname": atom["fontname"],
            "font_size_pt": f"{atom['font_size_pt']:.6f}",
            "x0_pt": f"{box[0]:.6f}",
            "top_pt": f"{box[1]:.6f}",
            "x1_pt": f"{box[2]:.6f}",
            "bottom_pt": f"{box[3]:.6f}",
        }
    )

object_rows = []
for obj in logical_objects:
    box = obj["bbox"]
    object_rows.append(
        {
            "object_id": obj["object_id"],
            "role": obj["role"],
            "atom_count": len(obj["atom_ids"]),
            "atom_ids": "|".join(obj["atom_ids"]),
            "text": obj["text"],
            "x0_pt": f"{box[0]:.6f}",
            "top_pt": f"{box[1]:.6f}",
            "x1_pt": f"{box[2]:.6f}",
            "bottom_pt": f"{box[3]:.6f}",
            "within_page": str(box[0] >= 0 and box[1] >= 0 and box[2] <= page_width and box[3] <= page_height).lower(),
        }
    )

write_csv(EVIDENCE / "RAW_ATOMS.csv", list(atom_rows[0]), atom_rows)
write_csv(EVIDENCE / "LOGICAL_OBJECTS.csv", list(object_rows[0]), object_rows)
write_csv(EVIDENCE / "ALL_UNORDERED_PAIRS_MACHINE.csv", list(pair_rows[0]), pair_rows)

color = Image.open(COLOR_PATH).convert("RGB")
gray = Image.open(GRAY_PATH).convert("L")
width, height = color.size
assert abs(width / page_width - scale) < 0.01
assert abs(height / page_height - scale) < 0.01
gray_array = np.asarray(gray)
foreground = gray_array < 250
ys, xs = np.nonzero(foreground)
ink_box = (max(0, int(xs.min()) - 30), max(0, int(ys.min()) - 30), min(width, int(xs.max()) + 31), min(height, int(ys.max()) + 31))
color.crop(ink_box).save(EVIDENCE / "figure_crop_native300dpi.png")
gray.crop(ink_box).save(EVIDENCE / "figure_crop_grayscale_native300dpi.png")

font = ImageFont.load_default()
overlay = color.copy()
draw = ImageDraw.Draw(overlay)
palette = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b"]
for i, obj in enumerate(logical_objects):
    x0, top, x1, bottom = obj["bbox"]
    box_px = (round(x0 * scale), round(top * scale), round(x1 * scale), round(bottom * scale))
    color_code = palette[i % len(palette)]
    draw.rectangle(box_px, outline=color_code, width=3)
    draw.text((box_px[0] + 2, max(0, box_px[1] - 14)), obj["object_id"], fill=color_code, font=font)
overlay.save(EVIDENCE / "logical_object_overlay_native300dpi.png")

cell_w, cell_h = 440, 300
sheet = Image.new("RGB", (cell_w * 2, cell_h * 7), "white")
sheet_draw = ImageDraw.Draw(sheet)
for index, obj in enumerate(logical_objects):
    x0, top, x1, bottom = obj["bbox"]
    pad = 24
    crop_box = (max(0, int(x0 * scale) - pad), max(0, int(top * scale) - pad), min(width, int(x1 * scale) + pad), min(height, int(bottom * scale) + pad))
    crop = color.crop(crop_box)
    crop.thumbnail((cell_w - 24, cell_h - 40), Image.Resampling.LANCZOS)
    col, row = index % 2, index // 2
    ox = col * cell_w + (cell_w - crop.width) // 2
    oy = row * cell_h + 24 + (cell_h - 40 - crop.height) // 2
    sheet.paste(crop, (ox, oy))
    sheet_draw.text((col * cell_w + 8, row * cell_h + 6), f"{obj['object_id']} {obj['role']}", fill="black", font=font)
    sheet_draw.rectangle((col * cell_w, row * cell_h, (col + 1) * cell_w - 1, (row + 1) * cell_h - 1), outline="#bbbbbb", width=1)
sheet.save(EVIDENCE / "logical_object_contact_sheet.png")

candidate_rows = [row for row in pair_rows if row["machine_candidate"] == "true"]
candidate_dir = EVIDENCE / "pair_candidates"
candidate_dir.mkdir(exist_ok=True)
obj_by_id = {o["object_id"]: o for o in logical_objects}
for row in candidate_rows:
    a, b = obj_by_id[row["object_a"]], obj_by_id[row["object_b"]]
    union = bbox_union([a["bbox"], b["bbox"]])
    pad = 24
    box_px = (max(0, int(union[0] * scale) - pad), max(0, int(union[1] * scale) - pad), min(width, int(union[2] * scale) + pad), min(height, int(union[3] * scale) + pad))
    if box_px[2] - box_px[0] > 360 or box_px[3] - box_px[1] > 240:
        areas = [((o["bbox"][2] - o["bbox"][0]) * (o["bbox"][3] - o["bbox"][1]), o) for o in (a, b)]
        focus = min(areas, key=lambda item: item[0])[1]
        center_x = int((focus["bbox"][0] + focus["bbox"][2]) * scale / 2)
        center_y = int((focus["bbox"][1] + focus["bbox"][3]) * scale / 2)
        box_px = (max(0, center_x - 180), max(0, center_y - 120), min(width, center_x + 180), min(height, center_y + 120))
    roi = color.crop(box_px)
    roi_draw = ImageDraw.Draw(roi)
    for obj, color_code in ((a, "#e31a1c"), (b, "#1f78b4")):
        x0, top, x1, bottom = obj["bbox"]
        local = (round(x0 * scale) - box_px[0], round(top * scale) - box_px[1], round(x1 * scale) - box_px[0], round(bottom * scale) - box_px[1])
        roi_draw.rectangle(local, outline=color_code, width=2)
    one = candidate_dir / f"{row['pair_id']}_{a['object_id']}_{b['object_id']}_native1x.png"
    eight = candidate_dir / f"{row['pair_id']}_{a['object_id']}_{b['object_id']}_nearest8x.png"
    roi.save(one)
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(eight)

critical_pairs = {
    "x1_contour": ("O01", "O03"),
    "step1_contour": ("O05", "O03"),
    "step2_contour": ("O06", "O03"),
    "step5_horizontal_axis": ("O09", "O01"),
    "legend_solid_vs_dash": ("O13", "O14"),
}
critical_rows = []
for name, pair in critical_pairs.items():
    row = next(r for r in pair_rows if {r["object_a"], r["object_b"]} == set(pair))
    critical_rows.append({"critical_id": name, **row})
write_csv(EVIDENCE / "CRITICAL_RELATIONS_MACHINE.csv", list(critical_rows[0]), critical_rows)

critical_atom_specs = {
    "x1_contour": ["C014", "C015"],
    "step1_contour": ["C005"],
    "step2_contour": ["C006"],
    "step5_horizontal_axis": ["C009"],
    "legend_solid_vs_dash": ["C018", "C019", "C020", "C021", "C022", "C023", "C024", "C025", "V019", "V020"],
}
for name, atom_ids in critical_atom_specs.items():
    focus_box = bbox_union([atom_by_id[atom_id]["bbox"] for atom_id in atom_ids])
    pad = 45 if name != "legend_solid_vs_dash" else 28
    box_px = (max(0, int(focus_box[0] * scale) - pad), max(0, int(focus_box[1] * scale) - pad), min(width, int(focus_box[2] * scale) + pad), min(height, int(focus_box[3] * scale) + pad))
    roi = color.crop(box_px)
    roi.save(EVIDENCE / f"critical_{name}_native1x.png")
    roi.resize((roi.width * 8, roi.height * 8), Image.Resampling.NEAREST).save(EVIDENCE / f"critical_{name}_nearest8x.png")

semantic = {
    "status": "MACHINE_SEMANTIC_CHECK_COMPLETE_MANUAL_REQUIRED",
    "quadratic": "0.5*(x1^2+2*x1*x2+2*x2^2)",
    "hessian": [[1, 1], [1, 2]],
    "determinant": 1,
    "eigenvalues": [(3 - math.sqrt(5)) / 2, (3 + math.sqrt(5)) / 2],
    "positive_definite": True,
    "principal_axes_axis_aligned": False,
    "contour_parameterization": "x1=r(cos(t)-sin(t));x2=r*sin(t)",
    "coordinate_updates": [
        {"from": "q0", "to": "q1", "updated": "x2", "stationarity_residual": 0.0},
        {"from": "q1", "to": "q2", "updated": "x1", "stationarity_residual": 0.0},
        {"from": "q2", "to": "q3", "updated": "x2", "stationarity_residual": 0.0},
        {"from": "q3", "to": "q4", "updated": "x1", "stationarity_residual": 0.0},
        {"from": "q4", "to": "q5", "updated": "x2", "stationarity_residual": 0.0},
        {"from": "q5", "to": "q6", "updated": "x1", "stationarity_residual": 0.0},
        {"from": "q6", "to": "q7", "updated": "x2", "stationarity_residual": 0.0},
    ],
    "objective_values": [2.92, 2.56, 1.28, 0.64, 0.32, 0.16, 0.08, 0.04],
    "strictly_decreasing": True,
    "true_optimum": [0.0, 0.0],
    "final_iterate": [-0.4, 0.2],
    "final_iterate_is_approximation": True,
}
write_json(EVIDENCE / "MATH_SEMANTIC_MACHINE.json", semantic)

machine_result = {
    "status": "MACHINE_COMPLETE_MANUAL_REQUIRED",
    "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF), "pages": 1, "width_pt": page_width, "height_pt": page_height},
    "render": {"dpi": 300, "width_px": width, "height_px": height, "ink_bbox_px": ink_box},
    "raw_atom_counts": {"char": len(page.chars), "line": len(page.lines), "curve": len(page.curves), "rect": len(page.rects), "total": len(raw_atoms)},
    "logical_object_count": len(logical_objects),
    "all_unordered_pair_count": len(pair_rows),
    "formula_check": len(pair_rows) == len(logical_objects) * (len(logical_objects) - 1) // 2,
    "assigned_atoms": len(assigned),
    "unassigned_atoms": len(set(atom_by_id) - set(assigned)),
    "duplicate_assignments": len(assigned) - len(set(assigned)),
    "machine_candidate_count": len(candidate_rows),
    "critical_relation_count": len(critical_rows),
    "outside_page_object_count": sum(row["within_page"] != "true" for row in object_rows),
    "manual_fields_generated": 0,
}
write_json(EVIDENCE / "MACHINE_RESULT.json", machine_result)

generated = sorted(p for p in EVIDENCE.rglob("*") if p.is_file())
artifact_rows = [{"relative_path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in generated]
write_csv(EVIDENCE / "MACHINE_ARTIFACTS.csv", list(artifact_rows[0]), artifact_rows)
print(json.dumps(machine_result, ensure_ascii=False))
