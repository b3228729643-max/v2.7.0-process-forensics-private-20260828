# FIG-P445-01 — SA1 strict R1 formal report

**Conclusion: FAIL. Next role: SA2.**

This is an independent, read-only requalification of the frozen final PDF. It does not rely on a legacy pass, legacy screenshot or a pre-existing measurement table.

## Scope and provenance

| Item | Value |
|---|---|
| Figure | `FIG-P445-01` / 图 25.1 |
| Frozen input | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf` |
| Physical PDF page / printed page | 485 / 472 |
| Source | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第04册_无监督学习与矩阵分解\V4-C02\fig_v4_c02_dendrogram.tex` |
| Adjacent body checked | `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第04册_无监督学习与矩阵分解\chapters\V4-C02.tex` lines 416--417 |
| Raw native render | 300 dpi, 2481×3508px, no post-render resize |
| Visible text elements | 69 independent glyph/substrings |
| Independent vector objects | 14 |
| All pair rows | 406 |

## Decision

The candidate is **not eligible for SA3**. Source-effective font failures are already conclusive. The audit nevertheless completed all visible figure/caption glyphs, independent vector bboxes/masks, all required object-pair checks, edge checks, four views and mathematical/text/page review.

| Gate | Result |
|---|---:|
| Source font | FAIL (28 failed elements) |
| 300dpi pixel height | FAIL (8 failed elements) |
| Same-class ratio | FAIL |
| Role ratio | FAIL |
| Illegal overlap pixels | 90 |
| Clip pixels | 0 |
| Minimum text clearance | 0.000px |
| Visual harmony | FAIL |
| Mathematical semantics | PASS |
| Text consistency | PASS |
| Grayscale | PASS |
| Page integration | PASS |

## Principal blockers

1. The source explicitly sets base 9.2pt (`slfig-FIG-P445-01`), 9.4pt axis/leaf labels, 8.6pt ticks, and 9.2pt cut annotation. Each is below the 9.5pt source-effective hard floor.
2. The vector extraction measures every glyph separately. Any small `h`, `c` subscript, `=`, decimal point or caption punctuation appears as its own traceable `ELEMENT_ID`; no enclosing formula bbox substitutes for it.
3. `after_overlap_report.csv` contains each text--text and text--graphic independent-mask relationship; failed/nearest pairs have raw + red/blue/magenta evidence under `critical_pairs/`. Tree-branch and cut-line crossings are separately retained as intentional graphical topology in `all_object_pair_audit.csv` and are not misclassified as text overlap.

## Deliverables

- `SA1_STRICT_R1_REPORT.md` (this report)
- `after_font_audit.csv`, `after_pixel_measurements.csv`
- `same_class_ratio_audit.csv`, `role_ratio_audit.csv`
- `after_overlap_report.csv`, `all_object_pair_audit.csv`, `after_edge_clip_report.csv`
- `after_text_measurement_overlay_300dpi.png` (+ detail), four native-render views, raw crop/full page
- `masks/`, `raw_objects/`, `overlays/objects/`, `isolated_svg/text/`, `isolated_svg/vector/`, `critical_pairs/`, `vector_object_manifest.csv`
- `after_visual_acceptance.md`
