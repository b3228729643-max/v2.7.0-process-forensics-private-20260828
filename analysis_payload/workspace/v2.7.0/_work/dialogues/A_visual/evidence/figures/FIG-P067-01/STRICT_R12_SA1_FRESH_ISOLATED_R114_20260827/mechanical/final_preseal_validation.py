from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
OUTPUT = ROOT / "mechanical" / "FINAL_PRESEAL_VALIDATION.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def image_size(name: str) -> tuple[int, int]:
    with Image.open(ROOT / "rendered" / name) as image:
        return image.size


def main() -> None:
    manifest = csv_rows(ROOT / "denominator" / "object_manifest.csv")
    pairs = csv_rows(ROOT / "denominator" / "all_unordered_pairs.csv")
    objects_manual = csv_rows(ROOT / "manual" / "manual_object_review.csv")
    pairs_manual = csv_rows(ROOT / "manual" / "manual_pair_adjudication.csv")
    pixels_manual = csv_rows(ROOT / "manual" / "after_pixel_measurements.csv")
    acceptance = (ROOT / "manual" / "after_visual_acceptance.md").read_text(encoding="utf-8")
    math_review = (ROOT / "manual" / "math_caption_page_review.md").read_text(encoding="utf-8")
    pair_validation = json.loads(
        (ROOT / "mechanical" / "manual_ledger_validation.json").read_text(encoding="utf-8")
    )

    required_acceptance_tokens = [
        "RESULT = `PASS`",
        "OVERLAP_CANDIDATE_PIXEL_COUNT = `17244`",
        "OVERLAP_PIXEL_COUNT = `0`",
        "CLIP_PIXEL_COUNT = `0`",
        "MIN_TEXT_CLEARANCE_PX = `1`",
        "MATH_SEMANTICS_PASS = `true`",
        "TEXT_CONSISTENCY_PASS = `true`",
        "GRAYSCALE_PASS = `true`",
        "PAGE_INTEGRATION_PASS = `true`",
        "different fresh isolated R114 SA3",
    ]
    expected_sizes = {
        "page_069_200dpi.png": (1654, 2339),
        "page_069_300dpi.png": (2481, 3508),
        "figure_native1x_300dpi.png": (1640, 670),
        "figure_nearest8x.png": (13120, 5360),
        "figure_grayscale_300dpi.png": (1640, 670),
    }
    observed_sizes = {name: image_size(name) for name in expected_sizes}
    checks = {
        "pdf_bytes": PDF.stat().st_size == 4_967_122,
        "pdf_sha256": sha256(PDF) == "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6",
        "source_bytes": SOURCE.stat().st_size == 4_014,
        "source_sha256": sha256(SOURCE) == "11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144",
        "object_count": len(manifest) == 69,
        "unordered_pair_count": len(pairs) == 2346,
        "manual_object_count": len(objects_manual) == 69,
        "manual_pair_count": len(pairs_manual) == 97,
        "manual_pixel_element_count": len(pixels_manual) == 23,
        "manual_pair_candidate_total": sum(int(row["COMPOSITE_CANDIDATE_PX"]) for row in pairs_manual) == 17244,
        "manual_true_overlap_zero": sum(int(row["TRUE_ILLEGAL_OVERLAP_PX"]) for row in pairs_manual) == 0,
        "manual_unresolved_zero": all(row["UNRESOLVED"].lower() == "false" for row in pairs_manual),
        "manual_crosscheck_pass": pair_validation["all_checks_pass"] is True,
        "acceptance_tokens_complete": all(token in acceptance for token in required_acceptance_tokens),
        "math_sum_recorded": "\\sum_{i=1}^4 p_i=1.00" in math_review,
        "right_continuity_recorded": "Manual right-continuity decision: `PASS`" in math_review,
        "image_sizes_exact": observed_sizes == expected_sizes,
        "nearest_detail_tile_count": len(list((ROOT / "rendered").glob("nearest8x_*.png"))) == 12,
        "write_stopped_absent_preseal": not (ROOT / "WRITE_STOPPED").exists(),
        "seal_manifest_absent_preseal": not (ROOT / "SEAL_MANIFEST.json").exists(),
    }
    result = {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "observed_image_sizes": {name: list(size) for name, size in observed_sizes.items()},
        "nearest_detail_tile_count": len(list((ROOT / "rendered").glob("nearest8x_*.png"))),
        "manual_fields_generated_or_overwritten": False,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not result["all_checks_pass"]:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
