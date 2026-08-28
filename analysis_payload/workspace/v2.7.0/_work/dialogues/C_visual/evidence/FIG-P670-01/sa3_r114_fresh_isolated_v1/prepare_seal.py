from __future__ import annotations

import csv
import hashlib
import os
import stat
from pathlib import Path


HANDOFF_ID = "C-FIG-P670-01-R114-SA3-FRESH-ISOLATED-V1"
UID = "FIG-P670-01"
VERDICT = "PASS"
ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa3_r114_fresh_isolated_v1")
MARKER_TEMP = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\WRITE_STOPPED_sa3_r114_fresh_isolated_v1.tmp")
MANIFEST = ROOT / "MANIFEST.csv"

FILES = [
    "generate_mechanical_evidence.py",
    "full_page_200dpi.png",
    "full_page_native_300dpi.png",
    "figure_crop_native_300dpi.png",
    "figure_caption_crop_native_300dpi.png",
    "grayscale_figure_caption_300dpi.png",
    "semantic_object_overlay_300dpi.png",
    "text_object_overlay_300dpi.png",
    "vector_object_overlay_300dpi.png",
    "ROI01_left_header_nodes_native1x_300dpi.png",
    "ROI01_left_header_nodes_nearest8x.png",
    "ROI02_left_formula_probability_native1x_300dpi.png",
    "ROI02_left_formula_probability_nearest8x.png",
    "ROI03_center_arrows_observation_native1x_300dpi.png",
    "ROI03_center_arrows_observation_nearest8x.png",
    "ROI04_right_header_nodes_native1x_300dpi.png",
    "ROI04_right_header_nodes_nearest8x.png",
    "ROI05_right_formula_probability_native1x_300dpi.png",
    "ROI05_right_formula_probability_nearest8x.png",
    "ROI06_summary_box_native1x_300dpi.png",
    "ROI06_summary_box_nearest8x.png",
    "ROI07_caption_native1x_300dpi.png",
    "ROI07_caption_nearest8x.png",
    "visible_object_inventory.csv",
    "source_visible_text_register.csv",
    "all_unordered_pairs.csv",
    "bbox_pair_candidates.csv",
    "text_raster_measurements.csv",
    "roi_register.csv",
    "input_identity.csv",
    "page_text_extract.txt",
    "denominator_freeze.json",
    "mechanical_environment.json",
    "manual_object_review.csv",
    "manual_pair_candidate_review.csv",
    "manual_semantic_review.md",
    "after_overlap_adjudication.md",
    "after_visual_acceptance.md",
    "README.md",
    "HANDOFF_REPORT.md",
    "prepare_seal.py",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_manifest(rows: list[dict]) -> None:
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ROW", "RELATIVE_PATH", "TYPE", "BYTES", "SHA256", "INTEGRITY_MODE"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def marker_bytes(manifest_rows: int, manifest_hash: str) -> bytes:
    text = (
        f"HANDOFF_ID={HANDOFF_ID}\n"
        f"UID={UID}\n"
        f"SEALED_ROOT={ROOT}\n"
        f"MANIFEST_ROWS={manifest_rows}\n"
        f"MANIFEST_SHA256={manifest_hash}\n"
        f"VERDICT={VERDICT}\n"
    )
    return text.encode("utf-8")


def set_readonly(path: Path) -> None:
    os.chmod(path, path.stat().st_mode & ~stat.S_IWRITE)


def main() -> None:
    if not ROOT.is_dir():
        raise RuntimeError("fixed root absent")
    if MARKER_TEMP.exists():
        raise RuntimeError("external marker temp already exists")
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("root marker already exists")
    rows = []
    for index, relative in enumerate(FILES, 1):
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing explicit file: {relative}")
        rows.append({
            "ROW": f"{index:04d}",
            "RELATIVE_PATH": relative,
            "TYPE": "FILE",
            "BYTES": f"{path.stat().st_size:010d}",
            "SHA256": sha256(path),
            "INTEGRITY_MODE": "CANDIDATE_FREEZE",
        })

    manifest_row_index = len(rows) + 1
    marker_row_index = len(rows) + 2
    total_rows = marker_row_index
    predicted_marker_size = len(marker_bytes(total_rows, "0" * 64))
    rows.append({
        "ROW": f"{manifest_row_index:04d}",
        "RELATIVE_PATH": "MANIFEST.csv",
        "TYPE": "FILE",
        "BYTES": "0000000000",
        "SHA256": "SELF_HASH_IN_WRITE_STOPPED",
        "INTEGRITY_MODE": "SELF_SIZE_AND_EXTERNAL_HASH",
    })
    rows.append({
        "ROW": f"{marker_row_index:04d}",
        "RELATIVE_PATH": "WRITE_STOPPED",
        "TYPE": "FILE",
        "BYTES": f"{predicted_marker_size:010d}",
        "SHA256": "SEALED_MARKER_CONTENT",
        "INTEGRITY_MODE": "MARKER_PARSE_AND_SIZE",
    })
    write_manifest(rows)
    manifest_size = MANIFEST.stat().st_size
    rows[manifest_row_index - 1]["BYTES"] = f"{manifest_size:010d}"
    write_manifest(rows)
    if MANIFEST.stat().st_size != manifest_size:
        raise RuntimeError("manifest self-size did not stabilize")
    manifest_hash = sha256(MANIFEST)
    payload = marker_bytes(total_rows, manifest_hash)
    if len(payload) != predicted_marker_size:
        raise RuntimeError("marker predicted size differs")
    MARKER_TEMP.write_bytes(payload)
    if MARKER_TEMP.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("marker has UTF-8 BOM")
    decoded_lines = MARKER_TEMP.read_text(encoding="utf-8").splitlines()
    if len(decoded_lines) != 6 or any((not line or line.count("=") != 1) for line in decoded_lines):
        raise RuntimeError("marker physical-line grammar differs")
    keys = [line.split("=", 1)[0] for line in decoded_lines]
    if keys != ["HANDOFF_ID", "UID", "SEALED_ROOT", "MANIFEST_ROWS", "MANIFEST_SHA256", "VERDICT"]:
        raise RuntimeError("marker keys differ")
    for relative in FILES:
        set_readonly(ROOT / relative)
    set_readonly(MANIFEST)
    set_readonly(MARKER_TEMP)
    set_readonly(ROOT)
    print(f"MANIFEST_ROWS={total_rows}")
    print(f"MANIFEST_SHA256={manifest_hash}")
    print(f"MARKER_TEMP={MARKER_TEMP}")
    print(f"MARKER_BYTES={len(payload)}")


if __name__ == "__main__":
    main()
