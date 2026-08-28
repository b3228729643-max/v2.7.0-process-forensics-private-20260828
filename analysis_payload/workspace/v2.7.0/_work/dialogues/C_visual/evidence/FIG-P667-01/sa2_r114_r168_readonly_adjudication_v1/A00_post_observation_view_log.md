# Post-observation view log

HANDOFF_ID: `C-FIG-P667-01-R114-SA2-R168-READONLY-ADJUDICATION-V1`

UID: `FIG-P667-01`

This log was authored only after every decisive final view below was opened at original detail in the isolated adjudicator instance.

## Final views opened

1. `M01_full_page_p714_300dpi.png` — page integration, surrounding proof, prefigure sentence, figure, caption, following heading, and proof-ending square inspected.
2. `M05_figure_caption_native300dpi.png` — all figure objects and full caption inspected at the native 300 dpi raster.
3. `M06_figure_caption_grayscale_native300dpi.png` — hierarchy, line styles, filled result node, and caption inspected without color dependence.
4. `M11_object_bbox_overlay_native300dpi.png` — all 22 IDs and their scopes inspected.
5. `M12_visible_ink_mask_gray_lt200.png` — dark semantic ink inspected.
6. `M13_nonwhite_structure_mask_gray_lt245.png` — pale borders/fill structure and dark ink inspected together.

## Every decisive ROI pair opened

1. `R01_low_annotations_native1x_300dpi.png` and `R01_low_annotations_nearest8x.png`.
2. `R02_posterior_flow_native1x_300dpi.png` and `R02_posterior_flow_nearest8x.png`.
3. `R03_marginal_clearance_native1x_300dpi.png` and `R03_marginal_clearance_nearest8x.png`.
4. `R04_caption_left_native1x_300dpi.png` and `R04_caption_left_nearest8x.png`.
5. `R05_caption_right_native1x_300dpi.png` and `R05_caption_right_nearest8x.png`.
6. `R06_qed_square_native1x_300dpi.png` and `R06_qed_square_nearest8x.png`.

## Genuine observations made before ledgers

- The 8.5/8.8/9.4 pt material is visibly readable at native 300 dpi and in the full-page composition; R168 therefore keeps it advisory-only.
- The underbrace labels are visually separate from the exponent glyphs; the machine intersections come from compound bounding scopes, not shared visible ink.
- Text inside strip/result-node containers has ample visible clearance from borders.
- The solid arrow terminates at the result node without passing through text; the dashed branch reaches the marginal formula without touching it.
- The marginal label remains visibly separated from its formula. The later exact thresholded-ink calculation found 15 empty pixels at the nearest aligned points.
- The caption is complete, correctly encoded, readable, and consistent with both the diagram and adjacent prose.
- The hollow square at the right of the preceding proof is a clean proof-ending QED square; its shape and page position distinguish it from a missing-glyph tofu box.
- No true clipping, unreadability, severe imbalance, semantic reversal, or illegal visible-ink overlap was observed.
