from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
WRAPPER = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex")
PDF = ROOT / "build" / "v260_FIG-P067-01_standalone.pdf"
EXPECTED = {
    "source": (4014, "11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144"),
    "wrapper": (388, "ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF"),
    "pdf": (34213, "586EFE2C968A05C014A9AD8D639A8CFF0EDD0B21306CA31183485A7C75A338A1"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def identity(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def assert_unique(rows: list[dict[str, str]], key: str, label: str) -> None:
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise RuntimeError(f"duplicate {label} {key}")


def assert_nonblank_notes(rows: list[dict[str, str]], label: str) -> None:
    if any(not row.get("note", "").strip() for row in rows):
        raise RuntimeError(f"blank {label} note")


def main() -> None:
    identities = {"source": identity(SOURCE), "wrapper": identity(WRAPPER), "pdf": identity(PDF)}
    for label, (expected_bytes, expected_hash) in EXPECTED.items():
        if identities[label]["bytes"] != expected_bytes or identities[label]["sha256"] != expected_hash:
            raise RuntimeError(f"{label} identity drift: {identities[label]}")

    glyphs = read_csv(ROOT / "03_objects" / "glyph_manifest.csv")
    graphics = read_csv(ROOT / "03_objects" / "graphic_manifest.csv")
    pairs = read_csv(ROOT / "06_ledgers" / "after_overlap_report.csv")
    critical = read_csv(ROOT / "05_pairs" / "critical_pair_manifest.csv")
    manual_objects = read_csv(ROOT / "06_ledgers" / "MANUAL_OBJECT_LEDGER.csv")
    manual_critical = read_csv(ROOT / "06_ledgers" / "MANUAL_CRITICAL_PAIR_LEDGER.csv")
    manual_targets = read_csv(ROOT / "06_ledgers" / "MANUAL_TARGET_RELATION_LEDGER.csv")
    manual_views = read_csv(ROOT / "06_ledgers" / "MANUAL_VIEW_LEDGER.csv")
    manual_typography = read_csv(ROOT / "06_ledgers" / "MANUAL_R168_TYPOGRAPHY_LEDGER.csv")
    manual_math = read_csv(ROOT / "06_ledgers" / "MANUAL_MATH_SEMANTIC_LEDGER.csv")
    machine = json.loads((ROOT / "07_validation" / "machine_summary.json").read_text(encoding="utf-8"))

    object_ids = [row["element_id"] for row in glyphs + graphics]
    assert len(glyphs) == 65
    assert len(graphics) == 35
    assert len(object_ids) == 100 and len(set(object_ids)) == 100
    assert len(pairs) == 4950 == 100 * 99 // 2
    assert_unique(pairs, "pair_id", "all-pair")
    observed_pair_keys = {tuple(sorted((row["a_id"], row["b_id"]))) for row in pairs}
    assert len(observed_pair_keys) == 4950
    assert len(critical) == 70
    assert_unique(critical, "pair_id", "critical")

    assert len(manual_objects) == 100
    assert_unique(manual_objects, "object_id", "manual object")
    assert set(row["object_id"] for row in manual_objects) == set(object_ids)
    assert all(row["decision"] == "PASS" for row in manual_objects)
    assert all(row["original_match"] == "TRUE" and row["overlay_complete"] == "TRUE" and row["mask_only_pure"] == "TRUE" for row in manual_objects)
    assert all(row["missing_stroke_px"] == "0" and row["foreign_pixel_px"] == "0" for row in manual_objects)
    assert_nonblank_notes(manual_objects, "object")

    assert len(manual_critical) == 70
    assert_unique(manual_critical, "pair_id", "manual critical")
    assert set(row["pair_id"] for row in manual_critical) == set(row["pair_id"] for row in critical)
    assert all(row["decision"] == "PASS" and row["illegal_overlap"] == "FALSE" for row in manual_critical)
    assert_nonblank_notes(manual_critical, "critical")

    expected_targets = {"P01436", "P01437", "P01449", "P01519", "P01520", "P01532"}
    assert len(manual_targets) == 6
    assert_unique(manual_targets, "pair_id", "manual target")
    assert set(row["pair_id"] for row in manual_targets) == expected_targets
    assert all(row["decision"] == "PASS" and row["shared_pixels"] == "0" for row in manual_targets)
    assert_nonblank_notes(manual_targets, "target")

    assert len(manual_views) == 34
    assert_unique(manual_views, "view_id", "manual view")
    assert all(row["decision"] == "PASS" for row in manual_views)
    assert all((ROOT / row["evidence_path"]).is_file() for row in manual_views)
    assert_nonblank_notes(manual_views, "view")

    assert len(manual_typography) == 9
    assert_unique(manual_typography, "source_font_id", "typography")
    assert all(row["decision"] == "ADVISORY" and row["hard_failure"] == "FALSE" for row in manual_typography)
    assert_nonblank_notes(manual_typography, "typography")

    assert len(manual_math) == 10
    assert_unique(manual_math, "check_id", "math")
    assert all(row["decision"] == "PASS" for row in manual_math)
    assert_nonblank_notes(manual_math, "math")

    assert machine["object_denominator"] == 100
    assert machine["unordered_pair_expected"] == machine["unordered_pair_actual"] == 4950
    assert machine["critical_pair_count"] == 70
    assert machine["empty_glyph_masks"] == machine["empty_graphic_masks"] == 0
    assert machine["independent_overlap_candidates"] == 0
    assert machine["numeric_clearance_failures_r168_manual_review_required"] == 0
    assert machine["glyph_numeric_threshold_failures_r168_advisory"] == 9
    assert machine["safe_filename_unique"] is True

    target_rows = {row["pair_id"]: row for row in pairs if row["pair_id"] in expected_targets}
    target_metrics = {
        pair_id: {
            "a_id": row["a_id"],
            "b_id": row["b_id"],
            "mask_intersection_px": int(row["mask_intersection_px"]),
            "clearance_px": float(row["clearance_px"]),
        }
        for pair_id, row in target_rows.items()
    }
    assert {key: value["clearance_px"] for key, value in target_metrics.items()} == {
        "P01436": 15.0,
        "P01437": 16.0,
        "P01449": 22.0,
        "P01519": 24.0,
        "P01520": 25.0,
        "P01532": 45.0,
    }
    assert all(value["mask_intersection_px"] == 0 for value in target_metrics.values())

    crosscheck = {
        "handoff_id": "A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827",
        "identity": identities,
        "denominator": {"glyphs": 65, "graphics": 35, "objects": 100, "unordered_pairs": 4950, "critical_pairs": 70},
        "manual": {"objects": 100, "critical_pairs": 70, "target_pairs": 6, "views": 34, "typography_advisories": 9, "math_semantic": 10},
        "hard_failures": 0,
        "r168_advisories": 9,
        "target_metrics": target_metrics,
        "machine_manual_crosscheck": "PASS",
    }
    (ROOT / "07_validation" / "FINAL_CROSSCHECK.json").write_text(json.dumps(crosscheck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "handoff_id": crosscheck["handoff_id"],
        "uid": "FIG-P067-01",
        "role": "SA2",
        "verdict": "LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH",
        "pdf": identities["pdf"],
        "source": identities["source"],
        "object_denominator": 100,
        "unordered_pairs": 4950,
        "critical_pairs": 70,
        "manual_object_rows": 100,
        "manual_critical_rows": 70,
        "manual_target_rows": 6,
        "manual_view_rows": 34,
        "hard_failures": 0,
        "r168_advisories": 9,
        "source_commit_authorized": False,
        "fresh_role_authorized": False,
    }
    (ROOT / "LOCAL_SA2_RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
