"""Final structural cross-check and terminal package writer for independent R5 SA1.

This is deliberately a final-delivery (R09) hash/checkpoint operation.  It
checks only R5's own evidence plus the two frozen identities, then writes the
machine cross-check, manifest, final report, and terminal status.  It never
modifies the frozen source, final PDF, build entry, or central status files.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image


WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
WORK_ROOT = WORKSPACE / "v2.7.0" / "_work"
OUT = Path(__file__).resolve().parent
REPORTS = OUT / "reports"
PDF = WORK_ROOT / "source" / "v2.7.0" / "src" / "build" / "strict_current_r96_fullbook" / "main_full.pdf"
SOURCE = WORK_ROOT / "source" / "v2.7.0" / "src" / "绘图源码" / "第05册_采样方法主题模型与图排序" / "V5-C03" / "fig_v5_c03_mh_accept_reject.tex"
EXPECTED_PDF = "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"
EXPECTED_SOURCE = "18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def require(condition: bool, message: str, assertions: list[tuple[str, bool, str]]) -> None:
    assertions.append((message, condition, "PASS" if condition else "FAIL"))
    if not condition:
        raise RuntimeError(message)


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    Image.MAX_IMAGE_PIXELS = None
    assertions: list[tuple[str, bool, str]] = []
    require(sha256(PDF) == EXPECTED_PDF, "official PDF SHA-256 matches frozen R96", assertions)
    require(sha256(SOURCE) == EXPECTED_SOURCE, "figure source SHA-256 matches frozen source", assertions)

    glyph_map = rows(OUT / "glyph_map.csv")
    ledger = rows(OUT / "glyph_reviewer_ledger.csv")
    pixels = rows(OUT / "after_pixel_measurements.csv")
    fonts = rows(OUT / "after_font_audit.csv")
    pairs = rows(OUT / "after_overlap_report.csv")
    occlusion = rows(OUT / "occlusion_inversion.csv")
    calibration = rows(OUT / "calibration" / "low_profile_calibration.csv")

    require(len(glyph_map) == 175 and len({r["GLYPH_ID"] for r in glyph_map}) == 175, "175 unique glyph-map rows", assertions)
    require(len(ledger) == 175 and len({r["GLYPH_ID"] for r in ledger}) == 175, "175 unique completed ledger rows", assertions)
    require(len(pixels) == 175 and len({r["GLYPH_ID"] for r in pixels}) == 175, "175 unique after-pixel rows", assertions)
    require(all(r["DECISION"] != "PENDING" for r in ledger), "no pending manual glyph review", assertions)
    require(len(list((OUT / "glyph_masks").glob("*_mask.png"))) == 175, "175 raw glyph masks", assertions)
    require(len(list((OUT / "glyph_views").glob("*_original_1x.png"))) == 175, "175 native original 1x glyph views", assertions)
    require(len(list((OUT / "glyph_views").glob("*_target_overlay_1x.png"))) == 175, "175 native target-overlay 1x glyph views", assertions)
    require(len(list((OUT / "contact_sheets").glob("contact_sheet_*.png"))) == 20, "20 8x-nearest O/T/M contact sheets", assertions)
    require(len(fonts) == 175 and all(truth(r["SOURCE_FONT_PASS"]) for r in fonts), "175-row source-font audit passes", assertions)

    failed = [r for r in ledger if r["DECISION"] == "FAIL"]
    hard = [r for r in ledger if int(r["H_INK_PX"]) < int(r["MIN_REQUIRED_PX"])]
    impure = [r for r in ledger if r["MASK_ONLY_PURE"] == "FAIL"]
    require(len(failed) == 23, "23 glyph ledger failures retained", assertions)
    require(len(hard) == 10, "10 mandatory raw pixel-floor failures retained", assertions)
    require(len(impure) == 15, "15 raw mask-purity failures retained", assertions)

    require(len(rows(OUT / "foreground_objects.csv")) == 35, "35 primary foreground objects", assertions)
    require(len(pairs) == 595, "all 595 unordered TT/TG/GG pairs", assertions)
    pair_counts = Counter(r["STATUS"] for r in pairs)
    require(pair_counts == Counter({"PASS_NO_OVERLAP": 578, "INTENTIONAL_CONTACT": 12, "SAME_PARENT_LAYOUT": 5}), "pair status partition 578/12/5", assertions)
    require(sum(r["SA1_DECISION"] == "FAIL_ILLEGAL_OVERLAP" for r in pairs) == 0, "no nonwhitelisted final foreground overlap", assertions)
    contacts = rows(OUT / "intentional_contact_ledger.csv")
    require(len(contacts) == 12, "12 intentional-contact ledger rows", assertions)
    require(len(list((OUT / "pairs" / "intentional_contact_details").glob("*_contact_8x_nearest.png"))) == 12, "12 native 8x intentional-contact details", assertions)

    require(len(occlusion) == 6 and all(r["STATUS"] == "PASS" for r in occlusion), "six opaque-background source-order checks pass", assertions)
    require(len(calibration) == 6 and all(r["DECISION"] == "PASS" for r in calibration), "six independent low-profile calibrations pass", assertions)

    native = Image.open(OUT / "official_R96_physical_651_full_page_300dpi.png")
    crop = Image.open(OUT / "figure_crop_300dpi.png")
    gray = Image.open(OUT / "grayscale_300dpi.png")
    require(native.size == (2481, 3508), "direct native 300 dpi page dimensions 2481x3508", assertions)
    require(crop.size == (1980, 1584) and gray.size == crop.size, "official crop and grayscale dimensions match", assertions)
    for name in [
        "GLYPH_REVIEW_SUMMARY.md", "OVERLAP_AND_OCCLUSION_REVIEW.md", "D_E_COORDINATION_REVIEW.md",
        "MATH_AND_SEMANTICS_REVIEW.md", "PAGE_VISUAL_INTEGRITY_REVIEW.md", "CLEANUP_EXCEPTION.md",
    ]:
        require((REPORTS / name).is_file(), f"required report exists: reports/{name}", assertions)

    # Full hash inventory is recorded before the manifest/terminal write so it
    # reflects every substantive R5 evidence artifact and scripts, not itself.
    exclusions = {
        "artifact_inventory.csv", "evidence_manifest.json", "TERMINAL_STATUS.md", "WRITE_STOPPED",
        "reports/MACHINE_CROSSCHECK.md", "reports/R5_SA1_FINAL_REPORT.md",
    }
    inventory_rows: list[dict[str, object]] = []
    for path in sorted((p for p in OUT.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower()):
        rel = path.relative_to(OUT).as_posix()
        if rel in exclusions:
            continue
        inventory_rows.append({"RELATIVE_PATH": rel, "BYTES": path.stat().st_size, "SHA256": sha256(path)})
    with (OUT / "artifact_inventory.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["RELATIVE_PATH", "BYTES", "SHA256"])
        writer.writeheader()
        writer.writerows(inventory_rows)

    final_status = "FAIL_TO_SA2" if failed else "PASS_TO_SA3"
    blocking = [
        {
            "gate": "native final-PDF glyph floors and raw mask ownership",
            "hard_floor_count": len(hard),
            "mask_purity_count": len(impure),
            "union_failed_glyph_count": len(failed),
            "glyph_ids": [r["GLYPH_ID"] for r in failed],
        }
    ] if failed else []
    assertion_lines = "\n".join(f"- [{status}] {message}" for message, _, status in assertions)
    crosscheck = f"""# R5 SA1 machine cross-check

Canonical evidence directory: `{OUT}`.

## Structural assertions

{assertion_lines}

All structural/integrity assertions passed.  The separate acceptance result is `{final_status}` because the completed glyph ledger contains {len(failed)} failures; that is a substantive gate result, not a missing-evidence condition.
"""
    write_text(REPORTS / "MACHINE_CROSSCHECK.md", crosscheck)

    final_report = f"""# FIG-P602-01 — R5 independent SA1 terminal report

Canonical evidence directory: `{OUT}`.

Frozen official PDF: `{PDF}`  
PDF SHA-256: `{EXPECTED_PDF}`  
Frozen figure source: `{SOURCE}`  
Source SHA-256: `{EXPECTED_SOURCE}`  
Identity: physical page 651 / printed page 638 / Figure 32.5.

| Gate | Result | Evidence |
|---|---|---|
| Frozen PDF/source identity | PASS | `evidence_manifest.json`, `reports/MACHINE_CROSSCHECK.md` |
| Source >=9.5 pt proof | PASS | `after_font_audit.csv`, `reports/D_E_COORDINATION_REVIEW.md` |
| 175-glyph native 1x+8x review and pixel floors | FAIL | `glyph_reviewer_ledger.csv`, `after_pixel_measurements.csv`, `reports/GLYPH_REVIEW_SUMMARY.md` |
| Low-profile same-codepoint calibration | PASS | `calibration/low_profile_calibration.csv` |
| 35 objects / 595 unordered pairs / intent whitelist | PASS | `after_overlap_report.csv`, `intentional_contact_ledger.csv` |
| Opaque-background inverse/source-order review | PASS | `occlusion_inversion.csv`, `occlusion/occlusion_reverse_render_manifest.json` |
| D/E coordination | PASS, no waiver of C | `reports/D_E_COORDINATION_REVIEW.md` |
| Mathematical/semantic review | PASS | `reports/MATH_AND_SEMANTICS_REVIEW.md` |
| Full page/crop/grayscale visual integrity | PASS | `reports/PAGE_VISUAL_INTEGRITY_REVIEW.md` |
| Calibration cleanup process exception | RECORDED, separate | `reports/CLEANUP_EXCEPTION.md` |

## Terminal decision

**{final_status}**

The decision is required by the final-PDF glyph gate: {len(hard)} mandatory raw-ink floor failures and {len(impure)} raw mask-purity failures, with {len(failed)} unique failed glyphs.  No business source, central state, build entry, or other evidence directory was changed by this R5 SA1 review.  The cleanup exception is fully disclosed and is not used to suppress or create the figure verdict.
"""
    write_text(REPORTS / "R5_SA1_FINAL_REPORT.md", final_report)

    manifest = {
        "task_id": "FIG-P602-01",
        "review_role": "SA1 independent R5 continuation",
        "terminal_status": final_status,
        "canonical_evidence_directory": str(OUT),
        "frozen_official_pdf": str(PDF),
        "frozen_official_pdf_sha256": EXPECTED_PDF,
        "frozen_figure_source": str(SOURCE),
        "frozen_figure_source_sha256": EXPECTED_SOURCE,
        "physical_page": 651,
        "printed_page": 638,
        "figure_number": "32.5",
        "native_render": {"dpi": 300, "page_pixels": [2481, 3508], "crop_pixels": [1980, 1584], "crop_rect": [250, 1416, 2230, 3000]},
        "glyph_review": {
            "glyph_count": 175,
            "ledger_rows": len(ledger),
            "manual_pending": 0,
            "native_original_1x": 175,
            "native_target_overlay_1x": 175,
            "contact_sheets_8x": 20,
            "pass_count": len(ledger) - len(failed),
            "fail_count": len(failed),
            "hard_floor_fail_count": len(hard),
            "mask_purity_fail_count": len(impure),
        },
        "low_profile_calibration": {"contexts": 6, "pass": 6, "fail": 0},
        "overlap": {"foreground_objects": 35, "unordered_pairs": 595, "status_counts": dict(pair_counts), "nonwhitelisted_overlap_count": 0, "intentional_contacts": 12},
        "occlusion": {"opaque_label_backgrounds": 6, "pass": 6, "true_occlusions": 0, "h06_reverse_render": "PASS_NO_TRUE_OCCLUSION"},
        "independent_review": {"math_semantics": "PASS", "source_size_D": "PASS", "coordination_E": "PASS", "page_crop_grayscale": "PASS"},
        "cleanup_exception": {"record": "reports/CLEANUP_EXCEPTION.md", "separate_from_figure_verdict": True},
        "blocking_gates": blocking,
        "artifact_inventory": {"path": "artifact_inventory.csv", "record_count": len(inventory_rows)},
        "scripts": {
            "evidence_generator_sha256": sha256(OUT / "r5_generate_evidence.py"),
            "low_profile_calibration_sha256": sha256(OUT / "r5_low_profile_calibration.py"),
            "occlusion_inverse_sha256": sha256(OUT / "r5_occlusion_inverse_corrected.py"),
            "native_evidence_finalizer_sha256": sha256(OUT / "r5_finalize_native_evidence.py"),
            "final_crosscheck_sha256": sha256(Path(__file__)),
        },
        "legacy_draft_notice": "evidence_manifest_draft.json and reports/machine_gate_draft.md are chronological drafts superseded by this final manifest and terminal status.",
    }
    write_text(OUT / "evidence_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    terminal = f"""# FIG-P602-01 R5 SA1 terminal status

STATUS: {final_status}

Canonical evidence directory: `{OUT}`

Terminal reason: 175/175 native glyph review is complete, but {len(hard)} mandatory raw-pixel floor failures and {len(impure)} raw mask-purity failures produce {len(failed)} unique failed glyphs.  All other mandatory R5 gates are complete and documented in `reports/R5_SA1_FINAL_REPORT.md`.

This terminal is superseded only by a future authorized corrective/requalification task; it does not authorize a modification to the frozen source or official PDF.
"""
    write_text(OUT / "TERMINAL_STATUS.md", terminal)


if __name__ == "__main__":
    main()
