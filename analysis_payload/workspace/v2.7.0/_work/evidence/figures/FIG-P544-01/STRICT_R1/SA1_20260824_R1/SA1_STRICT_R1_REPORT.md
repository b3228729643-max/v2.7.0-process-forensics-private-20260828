# Independent strict requalification: FIG-P544-01

## 1. Identity and scope

Decision: **FAIL — route to SA2**. Fresh read-only source, adjacent text and frozen-PDF evidence only; no prior SA/root result, screenshot, measurement or conclusion was used.

图30.1 is on frozen-PDF physical page 588 / printed page 575. The diagram is one panel, so cross-panel comparisons are explicitly not applicable rather than missing.

## 2. Source font audit

3 of 11 semantic reader-visible elements fail the 9.5pt source effective floor: the two legends and edge label retain explicit 8.8pt styles. The ordinary picture 9.4pt default is overridden by the global every-node small hook, giving 10.0pt effective node/formula text; see `after_font_audit.csv`.

## 3. Native 300dpi pixel audit

8 individual glyphs fail their own floor; punctuation/operators are measured as independent substrings, never through a parent formula or line. All visible glyphs map to a semantic owner (unmapped = 0).

## 4. Ratio and font harmony

SAME_CLASS_RATIO_PASS=true; ROLE_RATIO_PASS=false; VISUAL_HARMONY_PASS=false; FONT_VISUAL_HARMONY_PASS=false. The last value is explicitly false: visual plausibility cannot waive source floor, pixel, ratio, clearance or full-page gates.

## 5. Collision, clearance and clipping

OVERLAP_PIXEL_COUNT=6, CLIP_PIXEL_COUNT=0, minimum registered clearance=0.00px. The only illegal intersection is LEGEND_DASHED against its dashed legend arrow/arrowhead: 6 raw pixels, 0.00px clearance. `after_overlap_report.csv`, `after_edge_clip_report.csv`, raw masks, overlays and critical-pair ROIs provide separate-mask evidence.

## 6. Native views, reading path and grayscale

The four direct final-PDF views are present. Solid versus dashed edges and directed arrowheads remain distinguishable in grayscale; the bottom-to-top dependency reading route is visually traceable. PAGE_INTEGRATION_PASS=true.

## 7. Mathematical and text consistency

MATH_SEMANTICS_PASS=false and TEXT_CONSISTENCY_PASS=false. The graph's π=πP mixes the chapter's row-vector stationary equation ρ★=ρ★A with the separately introduced column convention P=Aᵀ, p★=Pp★. It also labels ‘返性’ where the chapter's condition is ‘正常返’, and joins time-average and stepwise convergence despite their different condition scopes.

## 8. Required SA2 action and evidence

Use one convention consistently: either replace the node with `ρ★=ρ★A` under the chapter's row convention, or introduce the explicit column vector and use `p★=Pp★`. Replace ‘返性’ with ‘正常返’; separate or annotate the time-average path from the additional nonperiodicity needed for stepwise convergence. Raise every visible source font to at least 9.5pt, then rebuild and obtain fresh full evidence before any new SA1/SA3. All evidence in this directory was generated from the frozen input without source changes.
