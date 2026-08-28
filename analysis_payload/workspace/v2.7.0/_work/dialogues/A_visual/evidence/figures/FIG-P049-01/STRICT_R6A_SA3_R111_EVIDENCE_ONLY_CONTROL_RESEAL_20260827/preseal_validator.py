from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C03\fig_v1_c03_gradient_contour.tex")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rows(name: str):
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    denominator = rows("machine_atomic_denominator.csv")
    pairs = rows("machine_all_unordered_pairs.csv")
    candidates = rows("machine_relation_candidates.csv")
    exclusions = rows("machine_background_exclusions.csv")
    manual_glyphs = rows("manual_glyph_ledger.csv")
    manual_paths = rows("manual_path_ledger.csv")
    manual_relations = rows("manual_relation_candidate_ledger.csv")
    hard = json.loads((ROOT / "machine_hard_gates.json").read_text(encoding="utf-8"))
    controls = json.loads((ROOT / "controls_resolved.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "manual_review_summary.json").read_text(encoding="utf-8"))

    ids = [r["object_id"] for r in denominator]
    glyph_ids = [r["object_id"] for r in denominator if r["kind"] == "GLYPH"]
    path_ids = [r["object_id"] for r in denominator if r["kind"] == "PATH"]
    expected_pairs = {(a, b) for a, b in itertools.combinations(ids, 2)}
    actual_pairs = {(r["object_a_id"], r["object_b_id"]) for r in pairs}
    manual_glyph_ids = {r["object_id"] for r in manual_glyphs}
    manual_path_ids = {r["object_id"] for r in manual_paths}
    candidate_ids = {r["pair_id"] for r in candidates}
    manual_candidate_ids = {r["pair_id"] for r in manual_relations}

    image_expectations = {
        "page_048_native300dpi.png": (2481, 3508),
        "figure_crop_native300dpi.png": (1543, 792),
        "figure_crop_native1x.png": (1543, 792),
        "atomic_overlay_native1x.png": (1543, 792),
        "atomic_overlay_nearest8x.png": (12344, 6336),
        "glyph_sheet_native1x.png": (1320, 984),
        "figure_crop_grayscale_native300dpi.png": (1543, 792),
    }
    image_dimensions = {name: Image.open(ROOT / name).size for name in image_expectations}
    relation_sheets = sorted(ROOT.glob("relation_hotspots_nearest8x_part*.png"))
    glyph_zoom_sheets = sorted(ROOT.glob("glyph_sheet_nearest8x_part*.png"))

    checks = {
        "pdf_identity_exact": PDF.stat().st_size == 4_967_076 and digest(PDF) == "DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6",
        "tex_identity_exact": TEX.stat().st_size == 4_189 and digest(TEX) == "27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E",
        "machine_gate_clear": hard["machine_hard_gate_state"] == "CLEAR",
        "denominator_n_152": len(denominator) == 152 and len(set(ids)) == 152,
        "glyph_count_135": len(glyph_ids) == 135,
        "path_count_17": len(path_ids) == 17,
        "background_exclusion_count_11": len(exclusions) == 11 and all("opaque white" in r["machine_exclusion_basis"] for r in exclusions),
        "all_pairs_c_11476": len(pairs) == 11_476 and len(actual_pairs) == 11_476,
        "all_pairs_exact_no_omission": actual_pairs == expected_pairs,
        "manual_glyph_ids_exact": len(manual_glyphs) == 135 and manual_glyph_ids == set(glyph_ids),
        "manual_path_ids_exact": len(manual_paths) == 17 and manual_path_ids == set(path_ids),
        "manual_candidate_ids_exact": len(manual_relations) == 122 and manual_candidate_ids == candidate_ids,
        "manual_glyph_decisions_complete": all(r["manual_decision"] == "ACCEPT" and r["manual_legibility"] == "clear" and r["manual_tofu"] == "no" and r["manual_clip"] == "no" for r in manual_glyphs),
        "manual_path_decisions_complete": all(r["manual_decision"] == "ACCEPT" and r["manual_geometry_integrity"] == "intact" and r["manual_clipping"] == "no" and r["manual_illegal_overlap"] == "no" for r in manual_paths),
        "manual_relation_decisions_complete": all(r["manual_relation_decision"] and r["manual_illegal_overlap"] == "no" and r["manual_observation"] for r in manual_relations),
        "manual_summary_counts_exact": summary["manual_glyph_rows"] == 135 and summary["manual_path_rows"] == 17 and summary["manual_relation_candidate_rows"] == 122,
        "manual_authority_boundary_respected": summary["sa3_result"] == "PASS" and "does not grant A_LOCAL_PASS" in summary["authority_boundary"],
        "machine_builder_has_no_manual_fields": "manual_" not in (ROOT / "build_machine_evidence.py").read_text(encoding="utf-8"),
        "resolved_controls_empty": controls["unresolved_control_values"] == [],
        "image_dimensions_exact": image_dimensions == image_expectations,
        "nearest8x_glyph_sheet_count_4": len(glyph_zoom_sheets) == 4,
        "nearest8x_relation_sheet_count_5": len(relation_sheets) == 5,
        "native_crop_alias_byte_identical": digest(ROOT / "figure_crop_native300dpi.png") == digest(ROOT / "figure_crop_native1x.png"),
    }
    result = {
        "audit_kind": "preseal payload consistency",
        "uid": "FIG-P049-01",
        "audit_checks": checks,
        "audit_state": "CLEAR" if all(checks.values()) else "NOT_CLEAR",
        "counts": {
            "N": len(denominator), "C": len(pairs), "glyphs": len(glyph_ids), "paths": len(path_ids),
            "background_exclusions": len(exclusions), "manual_relation_candidates": len(manual_relations),
        },
        "image_dimensions": {k: list(v) for k, v in image_dimensions.items()},
        "write_behavior": "This validator reads manual ledgers but never creates, edits, fills, or overwrites any manual reviewer/observed/decision/note field.",
    }
    (ROOT / "preseal_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["audit_state"] == "CLEAR" else 1)


if __name__ == "__main__":
    main()
