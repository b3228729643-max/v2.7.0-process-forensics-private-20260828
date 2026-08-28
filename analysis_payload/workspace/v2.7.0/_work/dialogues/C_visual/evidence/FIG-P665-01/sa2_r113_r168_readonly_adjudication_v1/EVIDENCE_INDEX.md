# Evidence index

- `ADJUDICATION_SCOPE.md`: fixed identity, whitelist, frozen inputs, page location, denominator, and active R168 rule.
- `ADJUDICATION.md`: independent result and exact handoff verdict.
- `ledgers/`: genuine manual per-ID object, all-unordered-pair, text/glyph, geometry, view, hard-gate, mathematics, and semantic/reading-order adjudications.
- `machine/input_identity.json`: frozen PDF/source byte and hash identities.
- `machine/object_bboxes_machine.csv`: machine-only visible-object envelopes for O01-O16.
- `machine/all_unordered_object_pairs_machine.csv`: machine-only enumeration and bbox geometry for all 120 unordered pairs.
- `machine/text_region_measurements_machine.csv`: machine-only 300 dpi region measurements at a 20/255 local-background delta.
- `machine/page_713_text.txt` and fingerprint JSON: independently extracted physical-page text and glyph-risk counts.
- `views/full_page_200dpi.png`, `views/full_page_300dpi.png`, and `views/full_page_grayscale_300dpi.png`: page-scale integration evidence.
- `views/native_figure_300dpi.png`, `views/native_diagram_300dpi.png`, and `views/native_figure_grayscale_300dpi.png`: native figure evidence.
- `views/semantic_object_overlay_300dpi.png`, `views/text_glyph_overlay_300dpi.png`, and `views/reading_order_overlay_300dpi.png`: denominator, text/glyph, and reading-order traceability.
- `views/risks/`: five risk ROIs, each preserved at native1x and enlarged only by nearest-neighbor 8x.
- `views/masks/foreground_threshold_mask_300dpi.png`: machine-only foreground-risk mask; manual decisions use the native pixels and overlays, not this mask alone.
- `SEALED_MANIFEST.csv`: produced once by `machine/seal_once.ps1`; it enumerates every payload file existing before the manifest. The manifest itself and the final marker are self-referential control records and are the only set-comparison exclusions.
- `FINAL_MARKER.txt`: created outside the root after all premarker root operations, made read-only with a strictly later timestamp, and single-moved into the root as the unique last root-content operation.

No standalone TeX build was performed: all views derive from the official frozen R113 PDF.
