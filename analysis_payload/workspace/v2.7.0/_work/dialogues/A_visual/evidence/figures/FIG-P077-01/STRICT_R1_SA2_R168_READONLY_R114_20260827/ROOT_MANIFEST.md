# Root manifest

Expected sealed root file count: **33**, including the final `WRITE_STOPPED` marker.

## Required visual evidence (15)

1. `full_page_200dpi.png`
2. `full_page_native_300dpi.png`
3. `figure_crop_native_300dpi.png`
4. `figure_crop_grayscale_300dpi.png`
5. `object_id_overlay_300dpi.png`
6. `critical_roi_narrow_label_native1x.png`
7. `critical_roi_narrow_label_nearest8x.png`
8. `critical_roi_wide_label_native1x.png`
9. `critical_roi_wide_label_nearest8x.png`
10. `critical_roi_area_annotation_native1x.png`
11. `critical_roi_area_annotation_nearest8x.png`
12. `critical_roi_y_ticks_native1x.png`
13. `critical_roi_y_ticks_nearest8x.png`
14. `critical_roi_x_ticks_caption_native1x.png`
15. `critical_roi_x_ticks_caption_nearest8x.png`

## Machine-only geometry/identity support (8)

16. `machine_input_identity.json`
17. `machine_caption_location.json`
18. `machine_render_geometry.json`
19. `machine_visible_object_geometry.csv`
20. `machine_text_pixel_measurements.csv`
21. `machine_unordered_pair_denominator.csv`
22. `derive_evidence.py`
23. `inspect_pdf_geometry.py`

Machine artifacts contain no reviewer, boolean, decision, or note fields.

## Post-observation manual evidence and decision (9)

24. `manual_object_observation_ledger.csv`
25. `manual_unordered_pair_adjudication.csv`
26. `manual_source_font_audit.csv`
27. `manual_r168_visual_acceptance.md`
28. `manual_ledger_coverage_audit.md`
29. `SCOPE_AND_METHOD.md`
30. `DECISION.json`
31. `PRESEAL_AUDIT.md`
32. `ROOT_MANIFEST.md`

## Sole final root operation (1)

33. `WRITE_STOPPED` — fully resolved and set ReadOnly outside the root; moved into place only after every existing root file and directory and the root itself verified ReadOnly.

Sealed decision: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.
