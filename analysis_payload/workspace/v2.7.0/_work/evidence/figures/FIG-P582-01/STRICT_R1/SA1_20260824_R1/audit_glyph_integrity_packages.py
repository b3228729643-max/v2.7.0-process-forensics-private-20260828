"""Build native 1:1 and observational 8x packages for every impure glyph.

No mask is repaired here.  The script preserves the existing final-visible
raw-mask evidence and supplies a per-glyph package for a human isolation
decision.  The 8x images use nearest-neighbour only and are never metrics.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "glyph_integrity_packages"


def save_variants(source: Path, destination_1x: Path, destination_8x: Path) -> None:
    im = Image.open(source)
    im.save(destination_1x)
    im.resize((im.width * 8, im.height * 8), Image.Resampling.NEAREST).save(destination_8x)


def main() -> None:
    with (ROOT / "glyph_machine_integrity.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        failures = [r for r in csv.DictReader(fh) if r["PASS_FAIL"] == "FAIL"]
    OUT.mkdir(exist_ok=True)
    for row in failures:
        gid = row["GLYPH_ID"]
        package = OUT / gid
        package.mkdir(exist_ok=True)
        save_variants(
            ROOT / "glyph_original" / f"{gid}_original_1x.png",
            package / "original_raw_1x.png",
            package / "original_raw_8x_nearest.png",
        )
        save_variants(
            ROOT / "glyph_target_overlay" / f"{gid}_target_overlay_1x.png",
            package / "target_overlay_1x.png",
            package / "target_overlay_8x_nearest.png",
        )
        save_variants(
            ROOT / "glyph_masks" / f"{gid}_mask_only_1x.png",
            package / "mask_only_1x.png",
            package / "mask_only_8x_nearest.png",
        )
        (package / "package_manifest.json").write_text(
            json.dumps(
                {
                    "glyph_id": gid,
                    "element_id": row["ELEMENT_ID"],
                    "char": row["CHAR"],
                    "native_count_coordinate": "final candidate PDF, native 300dpi, 1:1 raw mask",
                    "foreign_glyph_pixel_px": int(row["FOREIGN_GLYPH_PIXEL_PX"]),
                    "foreign_graphic_pixel_px": int(row["FOREIGN_GRAPHIC_PIXEL_PX"]),
                    "missing_stroke_px": int(row["MISSING_STROKE_PX"]),
                    "mask_repaired": False,
                    "isolation_status": "MANUAL_DECISION_RECORDED_IN_glyph_isolation_ledger.csv",
                    "files": [
                        "original_raw_1x.png", "target_overlay_1x.png", "mask_only_1x.png",
                        "original_raw_8x_nearest.png", "target_overlay_8x_nearest.png", "mask_only_8x_nearest.png",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
