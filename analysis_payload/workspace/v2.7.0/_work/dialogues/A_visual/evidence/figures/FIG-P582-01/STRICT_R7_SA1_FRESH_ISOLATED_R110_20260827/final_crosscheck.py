from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
HANDOFF = "A-R110-P582-SA1-FRESH-ISOLATED-20260827"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def check(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def main() -> None:
    issues: list[str] = []
    identity = json.loads((ROOT / "identity_manifest.json").read_text(encoding="utf-8"))
    machine = json.loads((ROOT / "machine_crosscheck.json").read_text(encoding="utf-8"))
    glyphs = json.loads((ROOT / "glyph_manifest.json").read_text(encoding="utf-8"))
    objects = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
    pairs = json.loads((ROOT / "pair_manifest.json").read_text(encoding="utf-8"))
    drawings = json.loads((ROOT / "drawing_path_manifest.json").read_text(encoding="utf-8"))
    sheets = json.loads((ROOT / "contact_sheet_manifest.json").read_text(encoding="utf-8"))
    relations = json.loads((ROOT / "relation_evidence_manifest.json").read_text(encoding="utf-8"))
    pixels = read_csv("after_pixel_measurements.csv")
    overlap = read_csv("after_overlap_report.csv")
    manual_glyphs = read_csv("manual_glyph_reviewer_ledger.csv")
    manual_objects = read_csv("manual_object_reviewer_ledger.csv")
    manual_pairs = read_csv("manual_critical_pair_reviewer_ledger.csv")
    manual_views = read_csv("manual_view_role_ledger.csv")

    check(sha256(PDF) == "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3", "official PDF hash mismatch", issues)
    check(PDF.stat().st_size == 4_967_063, "official PDF size mismatch", issues)
    check(sha256(SOURCE) == "989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57", "source hash mismatch", issues)
    check(identity["handoff_id"] == HANDOFF, "handoff identity mismatch", issues)
    check(identity["physical_page"] == 632 and identity["printed_page"] == 619, "page identity mismatch", issues)

    glyph_ids = [g["glyph_id"] for g in glyphs]
    check(len(glyphs) == len(pixels) == len(manual_glyphs) == 139, "glyph row count mismatch", issues)
    check(len(set(glyph_ids)) == 139, "duplicate glyph ID", issues)
    check(len({g["safe_filename"] for g in glyphs}) == 139, "duplicate safe filename", issues)
    check({r["glyph_id"] for r in manual_glyphs} == set(glyph_ids), "manual glyph coverage mismatch", issues)
    check(all(r["reviewer"] == HANDOFF for r in manual_glyphs), "manual glyph reviewer mismatch", issues)
    check(all(r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" for r in manual_glyphs), "manual glyph visual boolean not true", issues)
    check(all(r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" for r in manual_glyphs), "manual glyph missing/foreign pixels", issues)
    check(all(r["decision"].startswith("PASS") for r in manual_glyphs), "manual glyph non-PASS decision", issues)
    short = [r for r in pixels if r["threshold_px"] and int(r["ink_height_px"]) < int(r["threshold_px"])]
    check([r["glyph_id"] for r in short] == ["GLY-032"], "unexpected hard-threshold shortfall set", issues)

    object_ids = [o["object_id"] for o in objects]
    check(len(objects) == len(manual_objects) == 44, "object count mismatch", issues)
    check(len(set(object_ids)) == 44, "duplicate object ID", issues)
    check({r["object_id"] for r in manual_objects} == set(object_ids), "manual object coverage mismatch", issues)
    check(all(r["reviewer"] == HANDOFF and r["decision"].startswith("PASS") for r in manual_objects), "manual object decision/reviewer mismatch", issues)
    check({g["parent_id"] for g in glyphs} == {o["object_id"] for o in objects if o["kind"] == "TEXT"}, "glyph-parent to text-object mismatch", issues)
    check(len(drawings) == 17 and {d["draw_no"] for d in drawings} == set(range(1, 18)), "drawing/path denominator mismatch", issues)
    check(all(d["final_visible_pixel_count"] > 0 for d in drawings), "empty final-visible drawing mask", issues)

    expected_pairs = len(objects) * (len(objects) - 1) // 2
    pair_ids = [p["pair_id"] for p in pairs]
    pair_keys = {tuple(sorted((p["object_a"], p["object_b"]))) for p in pairs}
    check(expected_pairs == len(pairs) == len(overlap) == 946, "unordered pair row count mismatch", issues)
    check(len(set(pair_ids)) == 946 and len(pair_keys) == 946, "duplicate pair ID/key", issues)
    check(pair_ids == [f"PAIR-{i:04d}" for i in range(1, 947)], "pair ID sequence mismatch", issues)
    check(sum(int(p["final_visible_overlap_px"]) > 0 for p in pairs) == 0, "final-visible overlap present", issues)
    check(sum(p["threshold_px"] > 0 and p["blank_clearance_px"] is not None and p["blank_clearance_px"] < p["threshold_px"] for p in pairs) == 0, "text-related clearance failure", issues)
    critical_ids = {r["pair_id"] for r in relations}
    check(len(relations) == len(manual_pairs) == 35, "critical relation count mismatch", issues)
    check({r["pair_id"] for r in manual_pairs} == critical_ids, "manual critical pair coverage mismatch", issues)
    check(all(r["reviewer"] == HANDOFF and r["evidence_opened"] == "TRUE" and r["decision"].startswith("PASS") for r in manual_pairs), "manual critical pair decision/reviewer mismatch", issues)

    sheet_cells = [cell for sheet in sheets for cell in sheet["cells"]]
    check(len(sheets) == 14 and len(sheet_cells) == 139, "contact sheet count/cell mismatch", issues)
    check({cell["glyph_id"] for cell in sheet_cells} == set(glyph_ids), "contact sheet glyph coverage mismatch", issues)
    for sheet in sheets:
        path = ROOT / "glyph_contact_sheets" / sheet["sheet"]
        check(path.is_file(), f"missing contact sheet {sheet['sheet']}", issues)
        if path.is_file():
            with Image.open(path) as img:
                check(list(img.size) == sheet["dimensions_px"], f"contact sheet dimension mismatch {sheet['sheet']}", issues)
    for relation in relations:
        path = ROOT / relation["file"]
        check(path.is_file(), f"missing relation evidence {relation['file']}", issues)
        if path.is_file():
            with Image.open(path) as img:
                check(list(img.size) == relation["dimensions_px"], f"relation dimension mismatch {relation['file']}", issues)

    image_expectations = {
        "full_page_200dpi.png": (1654, 2339),
        "page_300dpi.png": (2481, 3508),
        "figure_crop_300dpi.png": (1943, 788),
        "standalone_300dpi.png": (1201, 651),
        "grayscale_300dpi.png": (1201, 651),
        "after_text_measurement_overlay_300dpi.png": (1943, 788),
    }
    for name, dims in image_expectations.items():
        with Image.open(ROOT / name) as img:
            check(img.size == dims, f"image dimension mismatch {name}: {img.size}", issues)

    check(len(list((ROOT / "object_masks").glob("*.png"))) == 44, "object mask file count mismatch", issues)
    check(len(list((ROOT / "graphic_pre_occlusion_masks").glob("*.png"))) == 17, "pre-occlusion mask file count mismatch", issues)
    check(len(list((ROOT / "relation_evidence").glob("*.png"))) == 35, "relation evidence file count mismatch", issues)
    check(len(manual_views) == 13 and all(r["reviewer"] == HANDOFF and r["opened"] == "TRUE" and r["decision"].startswith("PASS") for r in manual_views), "manual view/role ledger mismatch", issues)
    check(machine["empty_glyph_masks"] == 0, "machine empty glyph mask count nonzero", issues)
    check(machine["unassigned_drawing_path_count"] == 0 and machine["math_rule_path_count"] == 0, "drawing/math-rule accounting mismatch", issues)
    check(machine["expected_unordered_pair_count"] == machine["actual_unordered_pair_count"] == 946, "machine pair crosscheck mismatch", issues)

    report = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    result = (ROOT / "RESULT.txt").read_text(encoding="utf-8")
    for token in ["RESULT=PASS", "FONT_VISUAL_HARMONY_PASS=true", "OVERLAP_PIXEL_COUNT=0", "CLIP_PIXEL_COUNT=0"]:
        check(token in report or token in result, f"missing final token {token}", issues)
    for path in [
        ROOT / "source_font_override_audit.md",
        ROOT / "low_profile_punctuation_audit.md",
        ROOT / "manual_pair_denominator_review.md",
        ROOT / "after_visual_acceptance.md",
        ROOT / "RESULT.txt",
    ]:
        check(path.is_file() and path.stat().st_size > 0, f"missing/empty required manual payload {path.name}", issues)

    summary = {
        "official_pdf_sha256": sha256(PDF),
        "source_sha256": sha256(SOURCE),
        "glyph_rows": len(glyphs),
        "manual_glyph_rows": len(manual_glyphs),
        "object_rows": len(objects),
        "manual_object_rows": len(manual_objects),
        "unordered_pair_rows": len(pairs),
        "critical_relation_rows": len(relations),
        "manual_critical_relation_rows": len(manual_pairs),
        "manual_view_role_rows": len(manual_views),
        "contact_sheets": len(sheets),
        "contact_cells": len(sheet_cells),
        "object_mask_files": len(list((ROOT / "object_masks").glob("*.png"))),
        "pre_occlusion_mask_files": len(list((ROOT / "graphic_pre_occlusion_masks").glob("*.png"))),
        "relation_evidence_files": len(list((ROOT / "relation_evidence").glob("*.png"))),
        "final_visible_overlap_pairs": sum(int(p["final_visible_overlap_px"]) > 0 for p in pairs),
        "clearance_failure_pairs": sum(p["threshold_px"] > 0 and p["blank_clearance_px"] is not None and p["blank_clearance_px"] < p["threshold_px"] for p in pairs),
        "r168_shortfall_glyphs": [r["glyph_id"] for r in short],
        "issue_count": len(issues),
        "issues": issues,
        "crosscheck_result": "PASS" if not issues else "FAIL",
    }
    (ROOT / "machine_final_crosscheck.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
