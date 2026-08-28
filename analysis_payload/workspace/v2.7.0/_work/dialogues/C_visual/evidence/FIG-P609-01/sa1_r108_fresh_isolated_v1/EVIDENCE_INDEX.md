# Evidence index

## Decision and handoff

- `SA1_REPORT.md`: concise assigned-scope handoff.
- `after_visual_acceptance.md`: manual hard-gate decision and metrics.
- `HANDOFF.json`: structured handoff identity and next action.
- `manual_math_semantics.md`: independent ACF/ESS recomputation.
- `manual_source_font_audit.csv`: source/effective/font/pixel audit.
- `manual_object_observations.md`: manual observation for every one of 32 visible objects.
- `after_overlap_adjudication.md`: exhaustive pair review and candidate adjudication.

## Machine-only provenance and exhaustive tables

- `machine_identity.json`: official input identities and located page.
- `machine_denominator_summary.json`: denominator counts.
- `object_denominator.csv`: 32-object semantic denominator with source/PDF/raster coordinates.
- `all_unordered_pairs.csv`: all 496 unordered object pairs, exactly once, with objective bbox geometry only.
- `machine_pdf_text_spans.csv`: 62 PDF text spans.
- `machine_pdf_drawings.csv`: 15 vector drawings.
- `machine_pixel_span_measurements.csv` and `machine_pixel_summary.json`: objective 300 dpi span measurements.
- `make_machine_evidence.py` and `measure_and_micro_rois.py`: deterministic local evidence builders; neither writes manual decision fields.

## Opened visual evidence

- `views/r108_p661_full_300dpi.png`
- `views/r108_p661_full_200dpi.png`
- `views/r108_p661_figure_caption_300dpi.png`
- `views/r108_p661_figure_caption_grayscale_300dpi.png`
- `views/r108_p661_figure_caption_object_overlay_300dpi.png`
- `views/r108_p661_figure_caption_span_overlay_300dpi.png`
- Three broader critical ROI pairs at native1x and nearest8x.
- Six tighter micro ROI pairs at native1x and nearest8x for cutoff clearance, formula scripts/limits, panel-bottom clearance, and caption-top clearance.

All visual files are direct official-R108 renders or deterministic crops/nearest-neighbor enlargements of the native 300 dpi page. No TeX engine, LaTeX builder, Git action, source write, central-state write, or second UID/role was used.

