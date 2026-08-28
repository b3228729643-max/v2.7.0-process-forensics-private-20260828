from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    shutil.copyfile(ROOT / "glyph_machine.csv", ROOT / "after_pixel_measurements.csv")
    shutil.copyfile(ROOT / "critical_relations_machine.csv", ROOT / "after_overlap_report.csv")

    mapping: list[dict[str, str]] = []
    for row in rows("glyph_machine.csv"):
        identifier = row["glyph_id"]
        mapping.append(
            {
                "id_kind": "GLYPH",
                "element_id": identifier,
                "safe_filename": f"{identifier}.png",
                "ordinary_paths": "|".join(
                    [
                        f"glyph_masks/{identifier}.png",
                        f"glyph_rois_1x/{identifier}.png",
                        f"glyph_rois_8x/{identifier}.png",
                    ]
                ),
            }
        )
    for row in rows("object_inventory_machine.csv"):
        identifier = row["object_id"]
        mask_path = row.get("mask_path", "").strip()
        mapping.append(
            {
                "id_kind": "OBJECT",
                "element_id": identifier,
                "safe_filename": f"{identifier}.png" if mask_path else "N/A_OPAQUE_BACKGROUND",
                "ordinary_paths": mask_path or "N/A_OPAQUE_BACKGROUND",
            }
        )
    for row in rows("critical_relations_machine.csv"):
        identifier = row["pair_id"]
        paths = [row.get("roi_1x_path", "").strip(), row.get("roi_8x_path", "").strip()]
        paths = [path for path in paths if path]
        mapping.append(
            {
                "id_kind": "CRITICAL_RELATION",
                "element_id": identifier,
                "safe_filename": f"{identifier}.png" if paths else "N/A_NO_TARGETED_ROI",
                "ordinary_paths": "|".join(paths) if paths else "N/A_NO_TARGETED_ROI",
            }
        )

    with (ROOT / "id_safe_filename_machine.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id_kind", "element_id", "safe_filename", "ordinary_paths"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(mapping)


if __name__ == "__main__":
    main()
