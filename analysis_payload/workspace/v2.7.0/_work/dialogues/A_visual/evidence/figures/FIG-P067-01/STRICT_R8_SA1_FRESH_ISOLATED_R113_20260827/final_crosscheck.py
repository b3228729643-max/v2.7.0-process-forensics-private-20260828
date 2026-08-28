from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
issues: list[str] = []


def rows(name: str) -> list[dict]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


glyphs = rows("machine_glyph_inventory.csv")
manual_glyphs = rows("manual_glyph_review.csv")
drawings = rows("machine_drawing_inventory.csv")
halos = rows("machine_occlusion_background_inventory.csv")
pairs = rows("after_overlap_report.csv")
critical = rows("machine_critical_pair_index.csv")

expected_glyphs = {f"G{i:03d}" for i in range(1, 96)}
expected_drawings = {f"D{i:03d}" for i in range(1, 36)}
expected_pairs = {f"R{i:05d}" for i in range(1, 8386)}

if {row["element_id"] for row in glyphs} != expected_glyphs:
    issues.append("machine glyph ID set mismatch")
if {row["element_id"] for row in manual_glyphs} != expected_glyphs:
    issues.append("manual glyph ID set mismatch")
if len(manual_glyphs) != 95:
    issues.append("manual glyph row count mismatch")
if {row["element_id"] for row in drawings} != expected_drawings:
    issues.append("drawing ID set mismatch")
if {row["pair_id"] for row in pairs} != expected_pairs:
    issues.append("pair ID set mismatch")
if len(critical) != 99:
    issues.append("critical pair row count mismatch")
if len(halos) != 5:
    issues.append("opaque background row count mismatch")

for row in glyphs:
    for field in ("mask_path", "contact_path"):
        path = ROOT / row[field]
        if not path.is_file():
            issues.append(f"missing glyph evidence {path.name}")
        else:
            Image.open(path).verify()
for row in drawings:
    path = ROOT / row["mask_path"]
    if not path.is_file():
        issues.append(f"missing drawing mask {path.name}")
    else:
        Image.open(path).verify()
for row in critical:
    for field in (
        "evidence_original_1x",
        "evidence_overlay_1x",
        "evidence_mask_a",
        "evidence_mask_b",
        "evidence_intersection",
        "evidence_overlay_8x_nearest",
    ):
        path = ROOT / "critical_pairs" / row[field]
        if not path.is_file():
            issues.append(f"missing critical evidence {path.name}")
        else:
            Image.open(path).verify()

view_dims = {
    "page_300dpi.png": (2481, 3508),
    "full_page_200dpi.png": (1654, 2339),
    "figure_crop_300dpi.png": (1600, 670),
    "standalone_300dpi.png": (1600, 575),
    "grayscale_300dpi.png": (1600, 670),
    "figure_crop_300dpi_8x_nearest.png": (12800, 5360),
}
for name, expected in view_dims.items():
    path = ROOT / name
    if not path.is_file():
        issues.append(f"missing view {name}")
    else:
        actual = Image.open(path).size
        if actual != expected:
            issues.append(f"view dimension mismatch {name}: {actual} != {expected}")

manual_required = [
    "manual_view_review.md",
    "manual_glyph_review.csv",
    "manual_panel_role_ledger.csv",
    "manual_relationship_review.md",
    "manual_math_semantics.md",
    "source_font_audit.md",
    "after_visual_acceptance.md",
    "RESULT.txt",
]
for name in manual_required:
    if not (ROOT / name).is_file():
        issues.append(f"missing manual payload {name}")

if (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() != "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3":
    issues.append("RESULT status mismatch")

summary = {
    "uid": "FIG-P067-01",
    "machine_glyph_rows": len(glyphs),
    "manual_glyph_rows": len(manual_glyphs),
    "drawing_rows": len(drawings),
    "opaque_background_rows": len(halos),
    "pair_rows": len(pairs),
    "critical_pair_rows": len(critical),
    "glyph_contact_sheets": len(list((ROOT / "contact_sheets").glob("glyph_sheet_*.png"))),
    "pair_overview_sheets": len(list((ROOT / "pair_contact_sheets").glob("pair_overview_*.png"))),
    "critical_pair_pngs": len(list((ROOT / "critical_pairs").glob("*.png"))),
    "glyph_mask_pngs": len(list((ROOT / "glyph_masks").glob("*.png"))),
    "drawing_mask_pngs": len(list((ROOT / "drawing_masks").glob("*.png"))),
    "issues": issues,
    "machine_crosscheck_result": "CLEAN" if not issues else "ISSUES_PRESENT",
    "manual_fields_written_or_overwritten": 0,
}
(ROOT / "machine_final_crosscheck.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
if issues:
    raise SystemExit(1)
