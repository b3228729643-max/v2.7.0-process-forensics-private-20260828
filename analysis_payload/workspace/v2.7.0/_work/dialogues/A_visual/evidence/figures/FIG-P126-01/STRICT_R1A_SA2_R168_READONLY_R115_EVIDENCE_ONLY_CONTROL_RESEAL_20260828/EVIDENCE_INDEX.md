# FIG-P126-01 SA2/R168 evidence index

This is the sole fixed root for handoff `A-R115-P126-SA2-R168-READONLY-20260828`. It contains one read-only adjudication of the exact R115 candidate and does not incorporate any earlier P126 record.

## Identity and formal result

- `TASK_IDENTITY.txt`: instance, UID, exact hashes, and independent target location.
- `FORMAL_HANDOFF.txt`: formal result and narrowest single-source scope.
- `after_visual_acceptance.md`: R168 acceptance matrix and final verdict.

## Manual adjudication

- `MANUAL_ELEMENT_REVIEW.csv`: genuine manual per-ID glyph, readability, clipping, and text-graphic judgment for all 14 reader-visible text elements.
- `MANUAL_TEXT_PAIR_REVIEW.csv`: genuine manual judgment of all 91 unordered pairs, exactly `C(14,2)`.
- `after_pixel_measurements.csv`: per-ID final measurements and R168 classification.
- `after_overlap_adjudication.md`: candidate-to-true-collision adjudication with four confirmed object pairs and 51 shared native-pixel coordinates.
- `after_geometry_semantics.md`: coordinate-descent mathematics, caption/chapter consistency, grayscale, and page integration.

## Objective machine evidence

- `machine/reader_visible_denominator.csv`: frozen denominator with source locations, PDF bboxes, machine ink heights, and codepoints; no manual fields.
- `machine/all_unordered_text_pairs.csv`: exact 91-row pair skeleton; no manual fields.
- `machine/codepoint_inventory.csv`: character-level codepoint and bbox inventory.
- `machine/pdf_location_geometry.json`: unique page hit, page/crop geometry, denominator count, pair formula, and ROI manifest.
- `machine/page137_text_raw.json`: raw final-PDF text lines and character boxes.
- `machine/page137_drawings_summary.json`: final-PDF vector drawing inventory.
- `machine/all_text_vector_candidate_pixels.csv`: objective nonzero vector/text candidate scan.
- `machine/text_contour_candidate_pixels.json`: focused vector-mask counts used for manual review.

## Opened visual evidence

- `views/full_page_200dpi.png` and `views/full_page_300dpi.png`.
- `views/figure_only_native_300dpi.png` and `views/figure_caption_native_300dpi.png`.
- `views/figure_caption_grayscale_300dpi.png`.
- `views/text_overlay_300dpi.png`, `views/object_overlay_300dpi.png`, and `views/semantic_overlay_300dpi.png`.
- `views/rois/`: seven selected critical ROIs, each at native1x 300 dpi and nearest-neighbor 8x.
- `views/candidates/`: focused candidate overlays for T01, T04, T05, T07, and T08 at native1x and nearest8x.

`generate_objective_evidence.py` generated only objective artifacts and did not create reviewer, judgment, decision, note, or PASS fields. All manual adjudication files were authored after the required images were actually opened.
