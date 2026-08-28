# FIG-P660-01 independent overlap adjudication

HANDOFF_ID: `C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`

Scope: the 30 frozen visible semantic objects in `visible_object_denominator.csv`, covering the complete current Figure 34.4 graphic and its caption. The 30 objects produce exactly 435 unordered pairs, all enumerated once in `../06_machine_tables/all_unordered_pairs_machine.csv`.

Evidence actually opened before these judgments:

- native 300 dpi figure/caption crop and grayscale;
- text and all-object overlays;
- separated text-ink and graphic-foreground masks plus composite;
- the complete 30-by-30 unordered-pair contact matrix;
- native1x and nearest-neighbor8x critical ROIs R01 through R11;
- full-page and adjacent-page integration views for R111 physical pages 708, 709, and 710.

The machine screen produced 19 near/contact rows. Each has an individual manual row in `manual_pair_adjudication.csv`; no default or loop-authored manual verdicts were created. The remaining 416 pairs have machine overlap zero and machine foreground clearance greater than 12 px. They remain machine facts in the complete table, not bulk-authored manual PASS rows; their population was visually checked through the opened all-object overlay, masks, native crop, and complete pair matrix.

Raw screen accounting:

- 813 shared mask pixels across all highlighted pairs;
- 355 pixels belong to intended construction contacts inside the composite simplex object: grid endpoints at the triangle, grid/ray crossings, the three rays sharing the selected point, and the marker intentionally covering its local grid intersection;
- 458 pixels belong to four bbox-mask duplication rows (P226, P265, P300, P358). In each row, vertically overlapping extracted text bboxes cause the same native raster ink to be copied into both per-object masks. The opened native1x/nearest8x ROIs R01, R06, R07, and R08 show separate readable baselines and no glyph-on-glyph collision;
- no candidate remains unresolved.

Canonical independent-object collision accounting:

```text
OVERLAP_CANDIDATE_PIXEL_COUNT = 458
MASK_CONTAMINATION_PIXEL_COUNT = 458
OVERLAP_PIXEL_COUNT = 0
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED
UNRESOLVED_CANDIDATE_COUNT = 0
```

The legal geometric contacts are excluded from `OVERLAP_CANDIDATE_PIXEL_COUNT` because they join parts of the intended simplex construction rather than competing reader-visible semantic foreground. The four bbox-mask duplications are retained as the independent-object candidates and fully accounted for as mask contamination. Native evidence shows no true text-text, text-formula, text-line, text-marker, text-border, caption-border, or label-boundary collision.
