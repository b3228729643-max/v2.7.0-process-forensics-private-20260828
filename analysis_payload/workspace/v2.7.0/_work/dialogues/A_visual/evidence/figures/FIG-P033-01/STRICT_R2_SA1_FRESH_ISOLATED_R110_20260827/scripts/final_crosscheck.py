from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "payload"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C02\fig_v1_c02_projection.tex")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    with (PAYLOAD / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check_png(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except Exception:
        return False


def main() -> int:
    failures: list[str] = []

    identity = json.loads((PAYLOAD / "candidate_identity.json").read_text(encoding="utf-8"))
    summary = json.loads((PAYLOAD / "machine_summary.json").read_text(encoding="utf-8"))
    objects = read_csv("visible_object_ledger.csv")
    pairs = read_csv("after_overlap_report.csv")
    critical = read_csv("critical_relations_index.csv")
    glyph_manual = read_csv("manual_glyph_reviewer_ledger.csv")
    drawing_manual = read_csv("manual_drawing_reviewer_ledger.csv")
    relation_manual = read_csv("manual_critical_relation_reviewer_ledger.csv")
    view_manual = read_csv("manual_view_reviewer_ledger.csv")

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(PDF.stat().st_size == 4_967_063, "official PDF byte size mismatch")
    require(sha256(PDF) == "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3", "official PDF SHA-256 mismatch")
    require(SOURCE.stat().st_size == 2_383, "source byte size mismatch")
    require(sha256(SOURCE) == "4BCD50FE3BFDF1A3DCFC9089E103D256555949D859EC650F047CECB3A04EF6D4", "source SHA-256 mismatch")
    require(identity["pdf_pages"] == 817 and identity["physical_page"] == 29 and identity["printed_page"] == 16, "candidate page identity mismatch")

    object_ids = [row["element_id"] for row in objects]
    glyph_ids = [value for value in object_ids if value.startswith("G")]
    drawing_ids = [value for value in object_ids if value.startswith("D")]
    require(len(objects) == 99 and len(set(object_ids)) == 99, "visible object denominator is not 99 unique IDs")
    require(len(glyph_ids) == 85 and len(drawing_ids) == 14, "glyph/drawing split is not 85/14")
    require(sum(row["empty_mask"].lower() == "true" for row in objects) == 0, "empty mask found")
    require(sum(int(row["clip_pixel_count"]) for row in objects) == 0, "clip pixels found")
    foreign_removed_total = sum(int(row["foreign_pixel_px_removed_by_vector_selector"] or 0) for row in objects)
    require(all(int(row["foreign_pixel_px_removed_by_vector_selector"] or 0) >= 0 for row in objects), "invalid negative selector-removal count")

    expected_pairs = {tuple(sorted(pair)) for pair in itertools.combinations(object_ids, 2)}
    actual_pairs = {tuple(sorted((row["a_id"], row["b_id"]))) for row in pairs}
    require(len(pairs) == 4_851 and len(actual_pairs) == 4_851 and actual_pairs == expected_pairs, "unordered pair denominator is not exact C(99,2)=4851")

    hard = [row for row in pairs if row["machine_decision"].startswith("MACHINE_HARD_FAIL")]
    require(len(hard) == 1 and hard[0]["relation_id"] == "R2886", "final machine hard set is not exactly {R2886}")
    require(hard[0]["overlap_pixel_count"] == "24" and hard[0]["clearance_px"] == "0", "R2886 metrics are not 24 overlap / 0 clearance")
    require(len(critical) == 10 and len({row["relation_id"] for row in critical}) == 10, "critical relation denominator is not 10 unique IDs")

    require(summary["object_count"] == 99 and summary["unordered_pair_actual"] == 4_851, "machine summary denominator mismatch")
    require(summary["empty_mask_count"] == 0 and summary["foreign_or_unassigned_object_count"] == 0 and summary["clip_pixel_count_total"] == 0, "machine closure counts are not zero")
    require(summary["machine_hard_fail_relations"] == ["R2886"] and summary["critical_relation_count"] == 10, "machine summary hard/critical mismatch")
    require(summary["manual_fields_generated"] is False, "machine claims manual fields were generated")

    require(len(glyph_manual) == 85 and {row["element_id"] for row in glyph_manual} == set(glyph_ids), "manual glyph ledger incomplete")
    require(len(drawing_manual) == 14 and {row["element_id"] for row in drawing_manual} == set(drawing_ids), "manual drawing ledger incomplete")
    require(len(relation_manual) == 10 and {row["relation_id"] for row in relation_manual} == {row["relation_id"] for row in critical}, "manual critical relation ledger incomplete")
    require(len(view_manual) == 4 and all(row["opened"] == "TRUE" for row in view_manual), "manual view ledger incomplete")
    require(next(row for row in glyph_manual if row["element_id"] == "G036")["decision"] == "FAIL_RELATION_R2886", "G036 manual relation decision mismatch")
    require(next(row for row in drawing_manual if row["element_id"] == "D002")["decision"] == "FAIL_RELATION_R2886", "D002 manual relation decision mismatch")
    require(next(row for row in relation_manual if row["relation_id"] == "R2886")["decision"] == "FAIL_ILLEGAL_OVERLAP", "R2886 manual decision mismatch")
    require(all(row["decision"] == "PASS" for row in relation_manual if row["relation_id"] != "R2886"), "unexpected manual critical relation failure")

    selector_pngs = sorted((PAYLOAD / "vector_selectors").glob("U*.png"))
    final_mask_pngs = [
        PAYLOAD / "masks" / ("glyph" if element_id.startswith("G") else "drawing") / f"{element_id}.png"
        for element_id in object_ids
    ]
    contact_pngs = sorted((PAYLOAD / "contact_sheets").glob("*.png"))
    relation_dirs = sorted(path for path in (PAYLOAD / "relations").iterdir() if path.is_dir())
    require(len(selector_pngs) == 85 and all(check_png(path) for path in selector_pngs), "vector selector PNG set is not 85 valid files")
    require(len(final_mask_pngs) == 99 and all(path.is_file() and check_png(path) for path in final_mask_pngs), "final object mask set is not 99 valid PNGs")
    require(len(contact_pngs) == 20 and all(check_png(path) for path in contact_pngs), "contact sheet set is not 20 valid PNGs")
    require(len(relation_dirs) == 10, "relation evidence directory set is not 10")
    required_relation_files = {
        "raw_1x.png",
        "mask_A_1x.png",
        "mask_B_1x.png",
        "intersection_1x.png",
        "overlay_1x.png",
        "overlay_8x_nearest.png",
    }
    require(
        all({item.name for item in path.glob("*.png")} == required_relation_files and all(check_png(item) for item in path.glob("*.png")) for path in relation_dirs),
        "a critical relation lacks the required raw/mask/intersection/overlay 1x plus overlay 8x set",
    )

    payload_files = sorted(path for path in PAYLOAD.rglob("*") if path.is_file())
    require(all(":" not in part for path in payload_files for part in path.relative_to(PAYLOAD).parts), "alternate-data-stream-like filename found")
    require(all(path.stat().st_size > 0 for path in payload_files), "empty payload file found")

    final_decision = "FAIL" if not failures and len(hard) == 1 else "CROSSCHECK_FAIL"
    crosscheck = {
        "handoff_id": "A-R110-P033-SA1-FRESH-ISOLATED-20260827",
        "crosscheck_pass": not failures,
        "crosscheck_failures": failures,
        "official_pdf_identity_pass": not any("official PDF" in item for item in failures),
        "source_identity_pass": not any("source" in item for item in failures),
        "visible_denominator": 99,
        "glyph_manual_count": len(glyph_manual),
        "drawing_manual_count": len(drawing_manual),
        "critical_manual_count": len(relation_manual),
        "manual_view_count": len(view_manual),
        "unordered_pair_count": len(pairs),
        "machine_hard_relation_count": len(hard),
        "machine_hard_relations": [row["relation_id"] for row in hard],
        "critical_relation_count": len(critical),
        "contact_sheet_count": len(contact_pngs),
        "empty_mask_count": summary["empty_mask_count"],
        "foreign_or_unassigned_object_count": summary["foreign_or_unassigned_object_count"],
        "foreign_pixels_removed_by_exact_selector_total": foreign_removed_total,
        "clip_pixel_count_total": summary["clip_pixel_count_total"],
        "r168_advisory_not_hard": True,
        "manual_fields_generated_by_script": False,
        "preseal_crosscheck_history": [
            {
                "exit": 1,
                "status": "WITHDRAWN_CROSSCHECK_ASSERTIONS",
                "causes": [
                    "Misread foreign_pixel_px_removed_by_vector_selector as residual foreign pixels; it records pixels successfully removed.",
                    "Looked only at masks directory top level although final masks are organized in glyph and drawing subdirectories.",
                    "Hard-coded ten PNGs per relation although each ROI stores six native artifacts and the corresponding contact sheet supplies the combined 8x panels.",
                ],
                "candidate_machine_result_changed": False,
                "manual_ledgers_changed": False,
            }
        ],
        "final_decision": final_decision,
    }
    (PAYLOAD / "machine_crosscheck.json").write_text(json.dumps(crosscheck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PAYLOAD / "RESULT.txt").write_text(final_decision + "\n", encoding="ascii")

    manifest_rows = []
    for path in sorted(item for item in PAYLOAD.rglob("*") if item.is_file()):
        manifest_rows.append({
            "relative_path": path.relative_to(PAYLOAD).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest_path = ROOT / "PAYLOAD_MANIFEST.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(json.dumps({"exit": 0 if not failures else 1, "decision": final_decision, "payload_files": len(manifest_rows), **crosscheck}, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
