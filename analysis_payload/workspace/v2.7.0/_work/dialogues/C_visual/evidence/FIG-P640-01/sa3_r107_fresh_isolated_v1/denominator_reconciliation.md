# Frozen overlap denominator reconciliation

The provisional checkpoint value `5993` preceded the final glyph-ownership partition. It was not a sealed denominator and is superseded transparently here.

The final machine pass partitions tightly kerned/rotated character pixels by PDF line direction and same-parent nearest ownership before unioning glyph masks into semantic text objects. That refinement changed exactly two background-to-own-text candidates:

| Pair | Provisional raw px | Final frozen raw px | Delta |
|---|---:|---:|---:|
| PAIR-0021 BG-B-LIMIT-ANNOTATION / TXT-B-LIMIT-ANNOTATION | 2170 | 2070 | -100 |
| PAIR-0048 BG-B-POINT-ANNOTATION / TXT-B-POINT-ANNOTATION | 1432 | 1382 | -50 |

The other ten raw-overlap candidates total `2391` pixels in both versions. Therefore `5993 - 150 = 5843`.

Final frozen definition: sum of `raw_mask_overlap_px` over the 378 rows in `machine/machine_all_unordered_pairs.csv`, where masks use the final native 300 dpi per-glyph ownership partition and current semantic object unions. The machine table, `machine/machine_summary.json`, `after_overlap_report.csv`, `after_overlap_adjudication.md`, and all final reports use `5843`. This is a detector-candidate count only; canonical `OVERLAP_PIXEL_COUNT` after manual adjudication is `0`.
