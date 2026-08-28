from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
SEAL.mkdir(exist_ok=True)
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
WORKTREE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
EXPECTED_SHA = "01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB"
EXPECTED_COMMIT = "7f65bd75ce94aee876aa25735e92214bb5ebe004"


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def norm_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode()).hexdigest().upper()


checks: dict[str, object] = {}
failures: list[str] = []


def check(name: str, ok: bool, detail: object) -> None:
    checks[name] = {"pass": bool(ok), "detail": detail}
    if not ok:
        failures.append(name)


glyphs = rows("inventory/glyph_inventory.csv")
graphics = rows("inventory/graphic_path_inventory.csv")
pairs = rows("ledgers/all_unordered_pairs.csv")
gm = rows("ledgers/glyph_manual_review.csv")
pm = rows("ledgers/graphic_manual_review.csv")
critical = rows("ledgers/critical_pair_manual_review.csv")
low = rows("inventory/low_profile_reference_results.csv")
elements = rows("inventory/semantic_elements.csv")
visual = rows("ledgers/visual_review.csv")
font = rows("after_font_audit.csv")
matrix = json.loads((ROOT / "reports/final_matrix.json").read_text(encoding="utf-8"))
summary = json.loads((ROOT / "reports/denominator_and_machine_summary.json").read_text(encoding="utf-8"))

ids = [r["object_id"] for r in glyphs + graphics]
check("denominator_N124", len(glyphs) == 103 and len(graphics) == 21 and len(ids) == 124 and len(set(ids)) == 124, {"glyphs": len(glyphs), "graphics": len(graphics), "unique": len(set(ids))})
check("pair_denominator_7626", len(pairs) == 7626 and len({r["pair_id"] for r in pairs}) == 7626, len(pairs))
check("pair_endpoints_known", all(r["object_a"] in ids and r["object_b"] in ids for r in pairs), "all endpoints resolve")
check("math_rule_one", sum(r["graphic_class"] == "MATH_RULE" for r in graphics) == 1, [r["object_id"] for r in graphics if r["graphic_class"] == "MATH_RULE"])
check("empty_masks_zero", all(r["empty_mask"] == "0" for r in glyphs + graphics), "all nonempty")
check("mask_manual_purity", all(r["foreign_pixel_px"] == "0" and r["missing_stroke_px"] == "0" for r in glyphs + graphics), "all 124 foreign=0/missing=0")
check("coverage_closure", summary["unassigned_text_pixels"] == 0 and summary["foreground_coverage_residual_pixels"] == 0 and summary["foreground_coverage_excess_pixels"] == 0, {k: summary[k] for k in ("unassigned_text_pixels", "foreground_coverage_residual_pixels", "foreground_coverage_excess_pixels")})
check("glyph_manual_103", len(gm) == 103 and all(r["decision"] == "PASS_MASK" and "PENDING" not in "|".join(r.values()) for r in gm), len(gm))
check("graphic_manual_21", len(pm) == 21 and all(r["decision"] == "PASS_MASK" and "PENDING" not in "|".join(r.values()) for r in pm), len(pm))
check("critical_manual_37", len(critical) == 37 and all(r["opened_native_1x"] == "YES" and r["opened_8x"] == "YES" and r["decision"] != "PENDING" for r in critical), len(critical))
check("all_pair_manual_7626", all(r.get("manual_decision") and r.get("manual_note") and r.get("manual_reviewer") for r in pairs), "every pair has row-specific adjudication")
check("pair_results", sum(r["final_status"] == "FAIL" for r in pairs) == 17 and sum(r["intentional_contact"] == "1" for r in pairs) == 19 and sum(int(r["final_overlap_px"]) for r in pairs) == 0, {"failures": sum(r["final_status"] == "FAIL" for r in pairs), "intentional": sum(r["intentional_contact"] == "1" for r in pairs), "final_overlap_sum": sum(int(r["final_overlap_px"]) for r in pairs)})
check("low_profile_two_pass", len(low) == 2 and {r["target_id"] for r in low} == {"G0063", "G0083"} and all(r["status"] == "PASS_REFERENCE" and r["h_ratio_decimal"] == "1.0" and r["area_ratio_decimal"] == "1.0" for r in low), [(r["target_id"], r["status"]) for r in low])
check("glyph_hard_failures", {r["object_id"] for r in glyphs if r["numeric_status"] == "FAIL"} == {"G0017", "G0059", "G0066"}, [r["object_id"] for r in glyphs if r["numeric_status"] == "FAIL"])
check("D_E_failures_recorded", sum(r["D_status"] == "FAIL" for r in elements) == 5 and sum(r["E_status"] == "FAIL" for r in elements) == 5, {"D": sum(r["D_status"] == "FAIL" for r in elements), "E": sum(r["E_status"] == "FAIL" for r in elements)})
check("visual_ledger_complete", len(visual) >= 20 and all(r["opened"] == "YES" and r["decision"] and r["note"] for r in visual), len(visual))
check("font_ledger_no_pending", len(font) >= len(elements) + 6 and all("PENDING" not in "|".join(r.values()) for r in font), len(font))
check("matrix_route", matrix["SA1_PASS"] is False and matrix["route"] == "FAIL_TO_SA2" and matrix["OVERLAP_PIXEL_COUNT"] == 0 and matrix["CLIP_PIXEL_COUNT"] == 0, matrix["route"])
check("result_exact", (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip() == "FAIL_TO_SA2", (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip())
check("source_identity", norm_sha(SOURCE) == EXPECTED_SHA == matrix["source_normalized_sha256"], norm_sha(SOURCE))
target_rel = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex"
target_diff = subprocess.run(["git", "diff", "--", target_rel], cwd=WORKTREE, check=True, capture_output=True, text=True).stdout
target_staged = subprocess.run(["git", "diff", "--cached", "--", target_rel], cwd=WORKTREE, check=True, capture_output=True, text=True).stdout
unrelated_status = subprocess.run(["git", "status", "--porcelain"], cwd=WORKTREE, check=True, capture_output=True, text=True).stdout.splitlines()
check("business_source_read_only", target_diff == "" and target_staged == "", {"target_diff_empty": target_diff == "", "target_staged_empty": target_staged == "", "unrelated_concurrent_status": unrelated_status})
check("worktree_commit", subprocess.run(["git", "rev-parse", "HEAD"], cwd=WORKTREE, check=True, capture_output=True, text=True).stdout.strip() == EXPECTED_COMMIT, subprocess.run(["git", "rev-parse", "HEAD"], cwd=WORKTREE, check=True, capture_output=True, text=True).stdout.strip())

required_root = [
    "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png",
    "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv",
    "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md", "after_overlap_adjudication.md",
    "after_model_route.md", "SA1_REVIEW_REPORT.md", "SA1_HANDOFF.json", "RESULT.txt",
]
check("required_root_files", all((ROOT / name).is_file() for name in required_root), [name for name in required_root if not (ROOT / name).is_file()])

png_refs: set[Path] = set()
for row in glyphs:
    png_refs.update(ROOT / row[k] for k in ("original_1x", "overlay_1x", "mask_only_1x", "card_8x"))
for row in graphics:
    png_refs.update(ROOT / row[k] for k in ("original_1x", "overlay_1x", "mask_only_1x", "card_8x"))
for row in pairs:
    if row["critical_files"]:
        png_refs.update(ROOT / rel for rel in row["critical_files"].split("|"))
for row in critical:
    png_refs.add(ROOT / "critical" / f"{row['pair_id']}_native_1x_contact.png")
for row in low:
    png_refs.add(ROOT / row["native_1x_ratio"])
    png_refs.add(ROOT / row["card_8x_ratio"])
png_refs.update(ROOT / name for name in required_root if name.endswith(".png"))

bad_png = []
for path in sorted(png_refs):
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        bad_png.append(f"{path.relative_to(ROOT)}: {exc}")
check("referenced_png_openable", not bad_png, {"count": len(png_refs), "bad": bad_png})
check("safe_relative_names", all(":" not in p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()), "no NTFS ADS-style colon in relative names")
check("contact_sheet_counts", len(list((ROOT / "contacts").glob("glyph_native_1x_sheet_*.png"))) == 26 and len(list((ROOT / "contacts").glob("graphic_native_1x_sheet_*.png"))) == 6, {"glyph": len(list((ROOT / "contacts").glob("glyph_native_1x_sheet_*.png"))), "graphic": len(list((ROOT / "contacts").glob("graphic_native_1x_sheet_*.png")))})

result = {"terminal_check": "PASS" if not failures else "FAIL", "failures": failures, "checks": checks}
(SEAL / "terminal_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "reports" / "terminal_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"terminal_check": result["terminal_check"], "failure_count": len(failures), "check_count": len(checks), "png_opened": len(png_refs)}, ensure_ascii=False))
if failures:
    raise SystemExit(1)
