from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
R7 = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R7_SA1_FRESH_R101_20260825")
MACHINE = ROOT / "machine_reuse"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")
HANDOFF_ID = "A-R101-P608-SA1-FRESH-R7A-EVIDENCE-RESEAL-20260825"
PDF_SHA = "0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1"
SOURCE_SHA = "78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05"

TOP_FILES = [
    "candidate_identity.json",
    "object_inventory.csv",
    "object_inventory.json",
    "safe_filename_map.csv",
    "all_unordered_pairs.csv",
    "critical_pairs.csv",
    "critical_pairs_with_evidence.csv",
    "denominator_conservation.json",
    "render_geometry.json",
    "page_mapping_locator.json",
    "page659_rawdict.json",
    "page659_text_blocks.csv",
    "page659_drawings.csv",
    "page659_drawings_full.json",
    "fullbook_peer_candidates.csv",
    "fullbook_peer_candidates.json",
    "FULLBOOK_PEER_SELECTION_POLICY.json",
    "figure_crop_300dpi.png",
    "full_page_200dpi.png",
    "full_page_300dpi.png",
    "full_page_grayscale_300dpi.png",
    "grayscale_300dpi.png",
    "page659_figure_locator_overlay_300dpi.png",
    "standalone_300dpi.png",
]

TREE_DIRS = [
    "contact_sheets",
    "critical_pair_contact_sheets",
    "critical_pairs",
    "fullbook_peer_evidence",
    "low_profile_peers",
    "masks",
    "preliminary_run/before_after",
    "preliminary_run/navigation_contact_sheets",
]

PRELIM_FILES = [
    "preliminary_run/preliminary_64_failures.csv",
    "preliminary_run/preliminary_64_failures.json",
    "preliminary_run/preliminary_failure_raw_values.json",
    "preliminary_run/preliminary_replay_identity.json",
    "preliminary_run/tick_15_semantic_conservation.json",
    "preliminary_algorithm_v1_replay.py",
]

BANNED_NAMES = {
    "manual_critical_pair_ledger.csv",
    "manual_hard_failure_ledger.csv",
    "manual_low_profile_peer_ledger.csv",
    "manual_object_ledger.csv",
    "manual_preliminary_ledger.csv",
    "manual_role_ledger.csv",
    "manual_view_ledger.csv",
    "MANUAL_REVIEW_EVENT_LOG.json",
    "SA1_REVIEW.md",
    "RESULT.txt",
    "hard_failures.json",
    "denominator_and_pair_summary.json",
    "after_visual_acceptance.md",
    "after_overlap_adjudication.md",
    "after_overlap_report.csv",
    "after_font_audit.csv",
    "after_pixel_measurements.csv",
    "fullbook_peer_calibration.csv",
    "low_profile_peer_calibration.csv",
    "MODEL_ROUTE.md",
    "TERMINAL_STOP.json",
    "WRITE_SEAL.json",
    "FINAL_PAYLOAD_MANIFEST.json",
    "manifest_parse_check.json",
    "machine_preseal_check.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ordinary_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def selected_files() -> list[Path]:
    selected = [R7 / rel for rel in TOP_FILES + PRELIM_FILES]
    for rel in TREE_DIRS:
        selected.extend(sorted(p for p in (R7 / rel).rglob("*") if p.is_file()))
    for path in selected:
        if path.name in BANNED_NAMES or path.name.lower().endswith(".pyc") or "__pycache__" in path.parts:
            raise RuntimeError(f"banned R7 artifact selected: {path}")
        if not ordinary_file(path):
            raise RuntimeError(f"not ordinary source file: {path}")
    if len(selected) != len(set(selected)):
        raise RuntimeError("duplicate machine source path")
    return selected


def parse_source() -> dict:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    interesting = []
    needles = ("fontsize", "scale", "transform shape", "resizebox", "scalebox", "scriptstyle", "caption", "label")
    for line_no, line in enumerate(lines, 1):
        if any(needle in line for needle in needles):
            interesting.append({"line": line_no, "text": line})
    return {
        "line_count": len(lines),
        "interesting_source_lines": interesting,
        "declared_roles": {
            "every_node_pt": 9.6,
            "tick_label_pt": 9.6,
            "axis_label_pt": 10.8,
            "panel_title_pt": 10.8,
            "annotation_pt": 9.6,
            "caption_inherited_pt": 9.6,
            "natural_script_command": "\\scriptstyle t",
        },
        "graphics_scale_commands_found": [line for line in interesting if any(k in line["text"] for k in ("scale", "resizebox", "scalebox", "transform shape"))],
    }


def main() -> None:
    if MACHINE.exists() and any(MACHINE.rglob("*")):
        raise RuntimeError("machine_reuse already populated; refuse overwrite")
    if sha256(PDF) != PDF_SHA or PDF.stat().st_size != 4_947_496:
        raise RuntimeError("R101 identity mismatch")
    if sha256(SOURCE) != SOURCE_SHA or SOURCE.stat().st_size != 3_429 or not ordinary_file(SOURCE):
        raise RuntimeError("P608 source identity mismatch")
    with fitz.open(PDF) as doc:
        if doc.page_count != 814:
            raise RuntimeError("R101 page count mismatch")
        page_rect = list(doc[658].rect)

    selected = selected_files()
    entries = []
    for index, src in enumerate(selected, 1):
        rel = src.relative_to(R7)
        dst = MACHINE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        src_stat = src.stat()
        dst_stat = dst.stat()
        src_hash = sha256(src)
        dst_hash = sha256(dst)
        if src_stat.st_size != dst_stat.st_size or src_hash != dst_hash:
            raise RuntimeError(f"copy identity mismatch: {rel}")
        entries.append({
            "reuse_id": f"REUSE-{index:04d}",
            "r7_source_path": str(src),
            "r7_relative_path": rel.as_posix(),
            "r7_bytes": src_stat.st_size,
            "r7_sha256": src_hash,
            "r7_mtime_ns": src_stat.st_mtime_ns,
            "r7a_destination_path": str(dst),
            "r7a_relative_path": dst.relative_to(ROOT).as_posix(),
            "r7a_bytes": dst_stat.st_size,
            "r7a_sha256": dst_hash,
            "r7a_mtime_ns": dst_stat.st_mtime_ns,
            "bound_r101_pdf_sha256": PDF_SHA,
            "bound_r101_physical_page_1based": 659,
            "bound_p608_source_sha256": SOURCE_SHA,
        })

    source_identity = {
        "handoff_id": HANDOFF_ID,
        "route": "SA1=gpt-5.6-sol/xhigh",
        "figure_id": "FIG-P608-01",
        "source": {
            "absolute_path": str(SOURCE),
            "ordinary_file": ordinary_file(SOURCE),
            "bytes": SOURCE.stat().st_size,
            "sha256": sha256(SOURCE),
            "read_only_audit_boundary": True,
            "parsed": parse_source(),
        },
        "r101": {
            "absolute_path": str(PDF),
            "ordinary_file": ordinary_file(PDF),
            "bytes": PDF.stat().st_size,
            "sha256": sha256(PDF),
            "pages": 814,
            "physical_page_1based": 659,
            "page_rect_pt": page_rect,
            "read_only_audit_boundary": True,
        },
        "prohibited_build_tools_used": [],
        "source_and_pdf_identity_pass": True,
    }
    (ROOT / "source_identity_and_parse.json").write_text(
        json.dumps(source_identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    reuse = {
        "handoff_id": HANDOFF_ID,
        "reuse_policy": "R7 machine-only; R7 manual ledgers, review notes, PASS/FAIL summaries, result and handoff artifacts excluded",
        "source_r7_root": str(R7),
        "destination_machine_root": str(MACHINE),
        "entry_count": len(entries),
        "entries": entries,
        "global_bindings": {
            "r101_pdf_path": str(PDF),
            "r101_pdf_bytes": PDF.stat().st_size,
            "r101_pdf_sha256": PDF_SHA,
            "r101_pages": 814,
            "r101_physical_page_1based": 659,
            "p608_source_path": str(SOURCE),
            "p608_source_bytes": SOURCE.stat().st_size,
            "p608_source_sha256": SOURCE_SHA,
        },
    }
    (ROOT / "reuse_identity_ledger.json").write_text(
        json.dumps(reuse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "R7_ROOT_REJECT_PROVENANCE.md").write_text(
        "# R7 rejection provenance\n\n"
        "The formal root audit rejected R7 for bulk-generated manual ledgers, unresolved primary preliminary manual fields, missing source identity, peer-purity conflicts, and an auditor-created pyc cache incident. R7A reuses only the explicitly hashed machine layer. No R7 manual decision, human note, SA1 review, result, handoff, or PASS/FAIL summary is migrated. The pyc incident is provenance only and is not treated as a figure-quality conclusion.\n",
        encoding="utf-8",
    )
    print(json.dumps({"copied_machine_files": len(entries), "source_identity": "PASS", "pdf_identity": "PASS"}))


if __name__ == "__main__":
    main()
