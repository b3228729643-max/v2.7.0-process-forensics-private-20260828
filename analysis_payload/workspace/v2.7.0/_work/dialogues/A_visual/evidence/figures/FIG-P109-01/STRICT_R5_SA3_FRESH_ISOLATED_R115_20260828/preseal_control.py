from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R5_SA3_FRESH_ISOLATED_R115_20260828")


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    errors: list[str] = []
    denominator = rows("denominator_freeze.csv")
    pair_denominator = rows("unordered_pair_denominator.csv")
    element_review = rows("manual_element_review.csv")
    pair_review = rows("manual_pair_review.csv")
    text_review = rows("manual_text_consistency_review.csv")

    element_ids = [row["ELEMENT_ID"] for row in denominator]
    expected_pairs = {tuple(pair) for pair in combinations(element_ids, 2)}
    frozen_pairs = {(row["ELEMENT_A"], row["ELEMENT_B"]) for row in pair_denominator}
    reviewed_pairs = {(row["ELEMENT_A"], row["ELEMENT_B"]) for row in pair_review}

    if len(element_ids) != len(set(element_ids)):
        errors.append("duplicate denominator element ID")
    if frozen_pairs != expected_pairs:
        errors.append("frozen unordered-pair set differs from denominator combination set")
    if reviewed_pairs != expected_pairs:
        errors.append("manual unordered-pair review set differs from denominator combination set")
    if {row["ELEMENT_ID"] for row in element_review} != set(element_ids):
        errors.append("manual element review coverage differs from denominator")
    if {row["ELEMENT_ID"] for row in text_review} != set(element_ids):
        errors.append("manual text consistency coverage differs from denominator")

    required_render_files = {
        "full_page_200dpi.png",
        "page_integration_300dpi.png",
        "figure_native1x_72dpi.png",
        "figure_nearest8x_from_72dpi.png",
        "figure_raw_300dpi.png",
        "figure_grayscale_300dpi.png",
        "reader_text_overlay_300dpi.png",
    }
    required_render_files.update({f"ROI_{kind}{index:02d}_raw_300dpi.png" for kind, count in (("T", 6), ("G", 2)) for index in range(1, count + 1)})
    required_render_files.update({f"ROI_{kind}{index:02d}_nearest8x.png" for kind, count in (("T", 6), ("G", 2)) for index in range(1, count + 1)})
    missing_renders = sorted(name for name in required_render_files if not (ROOT / "render" / name).is_file())
    empty_renders = sorted(name for name in required_render_files if (ROOT / "render" / name).is_file() and (ROOT / "render" / name).stat().st_size == 0)
    if missing_renders:
        errors.append("required render files missing")
    if empty_renders:
        errors.append("required render files empty")

    output = {
        "denominator_count": len(element_ids),
        "expected_unordered_pair_count": len(expected_pairs),
        "frozen_unordered_pair_count": len(frozen_pairs),
        "manual_element_review_count": len(element_review),
        "manual_pair_review_count": len(pair_review),
        "manual_text_consistency_count": len(text_review),
        "manual_math_semantics_count": len(rows("manual_math_semantics_review.csv")),
        "manual_geometry_count": len(rows("manual_geometry_review.csv")),
        "manual_page_integration_count": len(rows("manual_page_integration_review.csv")),
        "required_render_file_count": len(required_render_files),
        "missing_render_files": missing_renders,
        "empty_render_files": empty_renders,
        "control_errors": errors,
        "control_error_count": len(errors),
    }
    (ROOT / "preseal_control.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
