# FIG-P067-01 R114 fresh isolated SA3 evidence index

Handoff: `A-R114-P067-SA3-FRESH-ISOLATED-20260827`

- `00_control/input_identity.json`: exact read-only input identities and startup-absence gate.
- `00_control/build_mechanical_evidence.py`: deterministic crop, overlay, measurement, denominator, and pair-universe builder; it contains no manual reviewer/boolean/decision/note fields.
- `00_control/build_preseal_controls.py`: mechanical preseal consistency audit and finite SHA-256 manifest builder; it does not author manual review fields.
- `00_control/seal_once.ps1`: one-shot ReadOnly recursion verifier and sole-final marker mover.
- `00_control/external_postseal_auditor.ps1`: root-read-only double-snapshot auditor that writes only root-external controls after sealing.
- `00_control/visible_object_denominator_mechanical.csv`: frozen 63-object figure-interior semantic denominator.
- `00_control/all_unordered_pairs_mechanical.csv`: exhaustive 1,953 unordered pairs.
- `00_control/mechanical_summary.json`: geometry and count summary.
- `01_locator/fullbook_layout.txt`: fresh official-PDF layout extraction used for caption search.
- `01_locator/physical_page_derived_bbox.xhtml`: fresh bounding-box extraction for the derived page.
- `01_locator/locator_record.md`: independent locator narrative.
- `01_locator/text_bbox_mechanical.csv`: 21 logical text/formula bboxes and native 300-dpi measurements.
- `02_page/page_300dpi.png`: official page rendered directly at 300 dpi.
- `02_page/full_page_200dpi.png`: full-page integration evidence required by the visual protocol.
- `03_figure/figure_native1x_300dpi.png`: native figure-interior 300-dpi crop with no resizing.
- `03_figure/figure_nearest8x.png`: exact nearest-neighbour 8x enlargement of the native crop.
- `03_figure/figure_grayscale_300dpi.png`: grayscale conversion of the native crop.
- `03_figure/text_bbox_overlay_300dpi.png`: 21-ID vector-bbox traceability overlay.
- `04_critical/critical_contact_sheet_native1x.png`: contact sheet for upper-note/axis, jump-marker/label, and lower-PMF regions.
- `04_critical/roi01_upper_note_axis_native1x.png`: upper left note/axis critical ROI.
- `04_critical/roi02_jump_markers_labels_native1x.png`: CDF jump-marker/label critical ROI.
- `04_critical/roi03_lower_pmf_annotation_native1x.png`: PMF/annotation critical ROI.
- `05_manual/manual_visible_object_ledger.csv`: 63 genuine post-observation per-ID manual decisions.
- `05_manual/manual_pair_adjudication.md`: manual coverage of all 1,953 pair IDs and exact 68-ID legal-contact subset.
- `05_manual/manual_math_geometry_caption_page_ledger.md`: independent math, right-continuity, endpoint, tick, caption, and page review.
- `05_manual/manual_r168_visual_acceptance.md`: resolved SA3 verdict under the controlling R168 hard-failure rule.

Boundary: the 63-object denominator is the complete reader-visible figure interior. Caption and adjacent-page objects are reviewed separately in the page-integration ledger and full-page evidence rather than silently mixed into the figure-interior pair universe.
