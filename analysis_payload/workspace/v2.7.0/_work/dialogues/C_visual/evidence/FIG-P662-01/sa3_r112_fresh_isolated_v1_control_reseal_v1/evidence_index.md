# Evidence index

## Native rendered views

- `full_page_300dpi.png`: frozen full page at native 300 dpi.
- `full_page_200dpi.png`: full-page integration view at normal review scale.
- `figure_crop_300dpi.png`: artwork-only native crop, without resizing.
- `figure_with_caption_300dpi.png`: artwork plus full caption at native 300 dpi.
- `grayscale_300dpi.png`: direct grayscale conversion of the native artwork crop.
- `page_integration_300dpi.png`: surrounding proof/figure/following-heading integration crop.

## Overlays

- `semantic_object_overlay_300dpi.png`: frozen authored-object denominator O01--O26.
- `text_glyph_overlay_300dpi.png`: reader-visible text/glyph denominator T01--T31.

## Native1x and nearest-neighbor8x risk pairs

- `risk_roi_fanin_native1x.png`, `risk_roi_fanin_nearest8x.png`
- `risk_roi_aux_native1x.png`, `risk_roi_aux_nearest8x.png`
- `risk_roi_simplex_native1x.png`, `risk_roi_simplex_nearest8x.png`
- `risk_roi_sumtext_native1x.png`, `risk_roi_sumtext_nearest8x.png`
- `risk_roi_resulttext_native1x.png`, `risk_roi_resulttext_nearest8x.png`
- `risk_roi_bottomtext_native1x.png`, `risk_roi_bottomtext_nearest8x.png`

## Machine-only evidence

- `generate_machine_evidence.py`: deterministic crop/overlay/measurement/enumeration generator; it does not write manual decisions or verdicts.
- `machine_objects.csv`: 26 authored visible objects.
- `machine_pairs.csv`: all 325 unordered pairs and machine-only bbox/mask measurements.
- `machine_text_measurements.csv`: machine-only span geometry and native ink measurements.

## Manual adjudication

- `manual_object_adjudication.csv`: per-object semantic and geometry decisions.
- `manual_pair_adjudication.md`: explicit per-ID P001--P325 decisions and candidate reconciliation.
- `manual_text_glyph_adjudication.csv`: per-ID T01--T31 codepoint/readability decisions.
- `manual_view_adjudication.md`: per-view V01--V20 adjudication.
- `manual_geometry_adjudication.csv`: geometry, clearance, clipping, and page-placement decisions.
- `manual_source_font_audit.csv`: current source declaration/effective-size audit under active R168 policy.
- `manual_ratio_harmony_adjudication.csv`: native role consistency and visual hierarchy review.
- `manual_hard_gate_adjudication.csv`: explicit R168 hard-defect gate.
- `mathematics_semantics_recomputation.md`: independent recomputation of every displayed mathematical/semantic claim.
- `after_visual_acceptance.md`: consolidated isolated SA3 result.

The final manifest closes over every payload file above. `WSTOP.txt` is intentionally excluded from the manifest rows and is authenticated by the marker's manifest hash.
