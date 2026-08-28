from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa3_r104_fresh_isolated_v1")


def rows(name: str):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def truth(v: str) -> bool:
    return v.strip().lower() == "true"


def main() -> None:
    checks: list[dict] = []

    def check(name: str, ok: bool, observed, expected) -> None:
        checks.append({"check": name, "pass": bool(ok), "observed": observed, "expected": expected})

    identity = json.loads((ROOT / "IDENTITY.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    objects = rows("machine_object_inventory.csv")
    pairs = rows("machine_pair_inventory.csv")
    candidates = rows("after_overlap_report.csv")
    glyph_manual = rows("manual_glyph_review.csv")
    graphic_manual = rows("manual_graphic_review.csv")
    pair_manual = rows("manual_candidate_pair_review.csv")
    role_manual = rows("manual_role_peer_review.csv")
    view_manual = rows("manual_view_review.csv")
    hard_manual = rows("manual_hard_gate_review.csv")

    check("identity_pdf_bytes", identity["pdf_bytes"] == 4967222, identity["pdf_bytes"], 4967222)
    check("identity_pdf_sha256", identity["pdf_sha256"] == "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641", identity["pdf_sha256"], "exact R104 hash")
    check("identity_pdf_pages", identity["pdf_pages"] == 817, identity["pdf_pages"], 817)
    check("identity_physical_page", identity["physical_page"] == 658, identity["physical_page"], 658)
    check("atomic_object_count", len(objects) == 173, len(objects), 173)
    ids = [r["object_id"] for r in objects]
    check("atomic_object_ids_unique", len(set(ids)) == len(ids), len(set(ids)), len(ids))
    check("glyph_object_count", sum(r["object_type"] == "GLYPH" for r in objects) == 150, sum(r["object_type"] == "GLYPH" for r in objects), 150)
    check("graphic_object_count", sum(r["object_type"] == "GRAPHIC" for r in objects) == 23, sum(r["object_type"] == "GRAPHIC" for r in objects), 23)
    check("empty_mask_count", sum(truth(r["empty_mask"]) for r in objects) == 0, sum(truth(r["empty_mask"]) for r in objects), 0)
    check("pair_denominator", len(pairs) == 173 * 172 // 2, len(pairs), 14878)
    check("pair_ids_unique", len({r["pair_id"] for r in pairs}) == len(pairs), len({r["pair_id"] for r in pairs}), len(pairs))
    check("candidate_pair_count", len(candidates) == 13, len(candidates), 13)
    check("manual_glyph_count", len(glyph_manual) == 150, len(glyph_manual), 150)
    check("manual_glyph_ids_exact", {r["object_id"] for r in glyph_manual} == {r["object_id"] for r in objects if r["object_type"] == "GLYPH"}, len({r["object_id"] for r in glyph_manual}), 150)
    check("manual_graphic_count", len(graphic_manual) == 23, len(graphic_manual), 23)
    check("manual_graphic_ids_exact", {r["object_id"] for r in graphic_manual} == {r["object_id"] for r in objects if r["object_type"] == "GRAPHIC"}, len({r["object_id"] for r in graphic_manual}), 23)
    check("manual_candidate_count", len(pair_manual) == 13, len(pair_manual), 13)
    check("manual_candidate_ids_exact", {r["pair_id"] for r in pair_manual} == {r["pair_id"] for r in candidates}, len({r["pair_id"] for r in pair_manual}), 13)

    glyph_bools = ["original_match", "overlay_complete", "mask_only_pure"]
    check("manual_glyph_booleans", all(all(truth(r[k]) for k in glyph_bools) for r in glyph_manual), "all true" if all(all(truth(r[k]) for k in glyph_bools) for r in glyph_manual) else "false row present", "all true")
    check("manual_glyph_decisions", all(r["decision"] == "PASS" for r in glyph_manual), sorted({r["decision"] for r in glyph_manual}), ["PASS"])
    check("manual_glyph_pixels", all(int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 for r in glyph_manual), "all zero" if all(int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 for r in glyph_manual) else "nonzero row present", "all zero")

    graphic_bools = ["original_match", "overlay_complete", "mask_only_pure"]
    check("manual_graphic_booleans", all(all(truth(r[k]) for k in graphic_bools) for r in graphic_manual), "all true" if all(all(truth(r[k]) for k in graphic_bools) for r in graphic_manual) else "false row present", "all true")
    check("manual_graphic_decisions", all(r["decision"] == "PASS" for r in graphic_manual), sorted({r["decision"] for r in graphic_manual}), ["PASS"])
    check("manual_graphic_pixels", all(int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 and int(r["clip_pixel_count"]) == 0 for r in graphic_manual), "all zero", "all zero")

    pair_bools = ["original_opened", "a_mask_opened", "b_mask_opened", "intersection_opened", "overlay_opened"]
    check("manual_pair_views", all(all(truth(r[k]) for k in pair_bools) for r in pair_manual), "all true", "all true")
    check("manual_pair_adjudication", all(r["decision"].startswith("PASS_") and int(r["illegal_overlap_px"]) == 0 and int(r["mask_contamination_px"]) == 0 for r in pair_manual), "all legal", "all legal")
    check("manual_pair_candidate_pixel_sum", sum(int(r["raw_intersection_px"]) for r in pair_manual) == 224, sum(int(r["raw_intersection_px"]) for r in pair_manual), 224)
    check("manual_role_decisions", all(r["decision"] in {"PASS", "ADVISORY"} for r in role_manual), sorted({r["decision"] for r in role_manual}), ["ADVISORY", "PASS"])
    check("manual_view_decisions", all(r["decision"] == "PASS" for r in view_manual), sorted({r["decision"] for r in view_manual}), ["PASS"])
    check("manual_hard_no_fail", all(r["decision"] in {"PASS", "ADVISORY"} for r in hard_manual), sorted({r["decision"] for r in hard_manual}), ["ADVISORY", "PASS"])

    # Open every referenced raster as an ordinary portable file.
    raster_paths = []
    for r in objects:
        raster_paths.extend([r["mask_path"], r["contact_1x"], r["contact_8x"]])
    for r in candidates:
        prefix = r["roi_bundle_prefix"]
        raster_paths.extend([prefix + "_quint_1x.png", prefix + "_quint_8x_nearest.png", prefix + "_intersection_1x.png"])
    raster_ok = True
    bad_rasters = []
    for rel in raster_paths:
        p = ROOT / rel
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception as exc:
            raster_ok = False
            bad_rasters.append(f"{rel}: {exc}")
    check("referenced_rasters_openable", raster_ok, len(raster_paths) - len(bad_rasters), len(raster_paths))
    check("referenced_raster_paths_unique", len(set(raster_paths)) == len(raster_paths), len(set(raster_paths)), len(raster_paths))

    cache_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and (p.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in p.parts or ".pytest_cache" in p.parts)]
    check("cache_pyc_zero", len(cache_files) == 0, cache_files, [])
    check("result_overlap", result["overlap_candidate_pixel_count"] == 224 and result["overlap_pixel_count"] == 0 and result["mask_contamination_pixel_count"] == 0, [result["overlap_candidate_pixel_count"], result["mask_contamination_pixel_count"], result["overlap_pixel_count"]], [224, 0, 0])
    check("result_clip", result["clip_pixel_count"] == 0, result["clip_pixel_count"], 0)
    check("result_booleans", all(result[k] for k in ["pair_denominator_complete", "font_visual_harmony_pass", "math_semantics_pass", "body_consistency_pass", "grayscale_pass", "page_integration_pass"]), "all true", "all true")
    check("result_local_only", result["result"] == "C_LOCAL_PASS_ONLY" and not result["global_pass_claimed"] and result["mainline_status"] == "AWAITING_MAINLINE", [result["result"], result["global_pass_claimed"], result["mainline_status"]], ["C_LOCAL_PASS_ONLY", False, "AWAITING_MAINLINE"])
    check("tex_and_writer", identity["tex_execution"] == "DISABLED" and identity["source_writer"] == "NONE", [identity["tex_execution"], identity["source_writer"]], ["DISABLED", "NONE"])

    output = {
        "uid": "FIG-P605-01",
        "handoff_id": "C-FIG-P605-01-R104-SA3-FRESH-ISOLATED-V1",
        "check_count": len(checks),
        "pass_count": sum(c["pass"] for c in checks),
        "fail_count": sum(not c["pass"] for c in checks),
        "status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
        "manual_decisions_generated_or_overwritten": False,
        "checks": checks,
    }
    (ROOT / "FINAL_MACHINE_CHECK.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if output["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
