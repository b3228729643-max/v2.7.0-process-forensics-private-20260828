from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa1_r114_fresh_isolated_v1")

RELATIVE_FILES = [
    "build_machine_evidence.py",
    "renders/full_page_200dpi.png",
    "renders/full_page_native_300dpi.png",
    "renders/figure_crop_native_300dpi.png",
    "renders/figure_crop_grayscale_300dpi.png",
    "renders/semantic_object_overlay_300dpi.png",
    "renders/key_roi_native1x_300dpi.png",
    "renders/key_roi_nearest_neighbor_8x.png",
    "machine/object_denominator.csv",
    "machine/unordered_pair_geometry.csv",
    "machine/pdf_text_spans.csv",
    "machine/pixel_ink_measurements.csv",
    "machine/pdf_vector_drawings.csv",
    "machine/render_metadata.json",
    "manual_object_review.csv",
    "manual_unordered_pair_review.csv",
    "manual_font_pixel_review.csv",
    "input_identity.md",
    "localization_and_context.md",
    "render_review.md",
    "after_overlap_adjudication.md",
    "after_visual_acceptance.md",
    "SA1_REPORT.md",
    "make_manifest.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


rows = []
for relative in RELATIVE_FILES:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(path)
    rows.append((relative.replace("\\", "/"), path.stat().st_size, sha256(path)))

manifest = ROOT / "MANIFEST.csv"
with manifest.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["RELATIVE_PATH", "BYTES", "SHA256"])
    writer.writerows(rows)

print(f"MANIFEST_ROWS={len(rows)}")
print(f"MANIFEST_SHA256={sha256(manifest)}")
