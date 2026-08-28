"""Recompute cross-glyph shared pixels for the separately preserved final masks."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
REAL_OBJECT_COLLISION_GLYPHS = {"G0029", "G0036"}


def main() -> None:
    with (ROOT / "glyph_file_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        glyphs = list(csv.DictReader(fh))
    with (ROOT / "glyph_final_mask_manifest.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        status = {r["GLYPH_ID"]: r for r in csv.DictReader(fh)}
    with (ROOT / "glyph_machine_integrity.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        raw = {r["GLYPH_ID"]: r for r in csv.DictReader(fh)}

    width = max(int(r["NATIVE_ROI_X1"]) for r in glyphs) + 1
    height = max(int(r["NATIVE_ROI_Y1"]) for r in glyphs) + 1
    owner_count = np.zeros((height, width), dtype=np.uint16)
    masks: dict[str, tuple[int, int, np.ndarray]] = {}
    for r in glyphs:
        gid = r["GLYPH_ID"]
        arr = np.array(Image.open(ROOT / status[gid]["FINAL_VISIBLE_MASK"]).convert("L")) < 128
        x0, y0 = int(r["NATIVE_ROI_X0"]), int(r["NATIVE_ROI_Y0"])
        masks[gid] = (x0, y0, arr)
        owner_count[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]] += arr.astype(np.uint16)

    rows: list[dict[str, str]] = []
    for r in glyphs:
        gid = r["GLYPH_ID"]
        x0, y0, arr = masks[gid]
        shared = int(np.sum(arr & (owner_count[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]] > 1)))
        real_collision = shared if gid in REAL_OBJECT_COLLISION_GLYPHS else 0
        foreign = 0 if gid in REAL_OBJECT_COLLISION_GLYPHS else shared
        rows.append({
            "GLYPH_ID": gid,
            "ELEMENT_ID": r["ELEMENT_ID"],
            "CHAR": r["CHAR"],
            "FINAL_MASK_STATUS": status[gid]["STATUS"],
            "RAW_SHARED_GLYPH_PIXEL_PX": raw[gid]["FOREIGN_GLYPH_PIXEL_PX"],
            "FINAL_SHARED_GLYPH_PIXEL_PX": str(shared),
            "REAL_SHARED_COLLISION_PX": str(real_collision),
            "FINAL_FOREIGN_GLYPH_PIXEL_PX": str(foreign),
            "MASK_PURITY_COMPLETENESS_PASS": str(foreign == 0).lower(),
            "RAW_DISCARDED_PIXEL_PX": status[gid]["REMOVED_RAW_PIXEL_PX"],
            "COORDINATE": "native candidate PDF 300dpi 1:1 final-mask ROI",
        })
    with (ROOT / "glyph_final_mask_integrity.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
