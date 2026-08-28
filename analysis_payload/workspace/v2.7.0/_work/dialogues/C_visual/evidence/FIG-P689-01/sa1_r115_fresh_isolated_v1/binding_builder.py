from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa1_r115_fresh_isolated_v1")
OUTPUT = ROOT / "MATERIAL_BINDING.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


EXACT_FILES = [
    "current_r115_text.txt",
    "full_page_200dpi.png",
    "full_page_300dpi.png",
    "full_page_grayscale_300dpi.png",
    "figure_caption_native_300dpi.png",
    "figure_caption_grayscale_native_300dpi.png",
    "DENOMINATOR_FREEZE.md",
    "evidence_builder.py",
    "denominator.csv",
    "pair_index.csv",
    "raw_pair_geometry.csv",
    "raw_text_metrics.csv",
    "text_measurement_overlay_300dpi.png",
    "object_overlay_300dpi.png",
    "semantic_overlay_300dpi.png",
    "roi_A_left_total_native1x.png",
    "roi_A_left_total_nearest8x.png",
    "roi_B_left_bar_native1x.png",
    "roi_B_left_bar_nearest8x.png",
    "roi_C_left_identity_native1x.png",
    "roi_C_left_identity_nearest8x.png",
    "roi_D_left_nonneg_note_native1x.png",
    "roi_D_left_nonneg_note_nearest8x.png",
    "roi_E_right_title_upper_native1x.png",
    "roi_E_right_title_upper_nearest8x.png",
    "roi_F_right_stair_local_native1x.png",
    "roi_F_right_stair_local_nearest8x.png",
    "roi_G_right_ticks_xlabel_native1x.png",
    "roi_G_right_ticks_xlabel_nearest8x.png",
    "roi_H_caption_native1x.png",
    "roi_H_caption_nearest8x.png",
    "roi_I_panel_gap_edges_native1x.png",
    "roi_I_panel_gap_edges_nearest8x.png",
    "manual_element_ledger.csv",
    "manual_ratio_ledger.csv",
    "manual_text_graphic_collision_ledger.csv",
    "manual_object_semantic_ledger.csv",
    "glyph_codepoint_review.md",
    "math_semantic_review.md",
    "page_integration_review.md",
    "manual_overlap_adjudication.md",
    "manual_pair_ledger.csv",
    "source_audit.md",
    "after_model_route.md",
    "after_visual_acceptance.md",
    "SA1_RESULT.md",
    "binding_builder.py",
]
files = [ROOT / name for name in EXACT_FILES]
missing = [path.name for path in files if not path.is_file()]
if missing:
    raise FileNotFoundError(f"exact binding input missing: {missing}")
with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["RELATIVE_PATH", "SIZE_BYTES", "SHA256"])
    for path in files:
        w.writerow([path.relative_to(ROOT).as_posix(), path.stat().st_size, sha256(path)])
print(f"BOUND_FILE_COUNT={len(files)}")
