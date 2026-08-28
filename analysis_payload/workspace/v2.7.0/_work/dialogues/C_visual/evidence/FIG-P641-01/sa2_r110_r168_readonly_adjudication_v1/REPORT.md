# FIG-P641-01 — R110/R168 read-only SA2 adjudication report

## Disposition

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

This is a scoped SA2 source-change adjudication, not a root final acceptance and not a self-counted C_LOCAL/global/final pass. No true R168 hard defect was found, so no source change or build was authorized or performed.

## Identity and isolation

- Handoff ID: `C-FIG-P641-01-R110-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual reviewer instance: `/root/sa2_fig_p641_r110_r168_readonly_v1`
- Model / effort / fork turns: `gpt-5.6-sol / xhigh / none`
- Evidence root was absent at startup and was created for this run only.
- Official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf`
- PDF bytes: `4,967,063`
- PDF SHA256: `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`
- Current figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex`
- Source bytes: `3,008`
- Source SHA256: `8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15`
- PDF and source identities exactly matched the assigned values at start and again before sealing.
- Reads were restricted to the assigned PDF, current source, narrow current chapter context around the figure, active Goal, direct evidence schema, direct pixel protocol, the two required skills, and this new evidence root.
- TeX/LuaLaTeX/latexmk runs: `0`; source writes: `0`; PDF/build writes: `0`; Git operations: `0`; TeX process management: `0`; second UID: `0`; second role: `0`; old-evidence/status/root/report reads: `0`.

## Independent localization

Caption text and current source were used to locate the figure independently in the official R110 full book.

- Figure number: `图33.8`
- Physical PDF page: `691`
- Printed page: `678`
- Page size: `595.276 × 841.890 pt`
- Rotation: `0`
- Direct native 300dpi page grid: `2481 × 3508 px`
- Full-page integration render: `1654 × 2339 px` at 200dpi
- Figure-plus-caption crop: full-page native coordinates `[285,2280,2195,3045]`; size `1910 × 765 px`
- Standalone/figure-body crop: `[420,2290,2160,2915]`; size `1740 × 625 px`
- Grayscale crop uses the identical figure-plus-caption coordinates and native dimensions.

All required views and all six broad native 1x / 8x-nearest ROIs were actually opened. The detailed view ledger is `tables/manual_view_review.csv`.

## Source and semantic recomputation

The visible factorization is consistent with

`p(z,y|θ) p(θ|α) p(α)`.

For the conditional update of `θ`, the factor `p(α)` is independent of `θ` and cancels from the conditional kernel, leaving

`π(θ|α,z,y) ∝ p(θ|α) p(z,y|θ)`.

The graph topology is `p(α)—α—p(θ|α)—θ—p(z,y|θ)`, with the last factor branching to `z` and `y`. Therefore the Markov blanket of `θ` shown by the dashed surrounds is exactly `{α,z,y}`. The cancellation arrow and two-line annotation correctly identify `p(α)` as outside the retained conditional factors. Figure, formula, and caption agree; no semantic or mathematical error exists.

## Frozen denominators

- Foreground visible objects: `N=29`
  - Text/formula line objects: `14` (`T01`–`T14`)
  - Foreground graphic paths: `15` (`G01`–`G15`; PDF vector sequences 14–28)
- Protocol background fills: `7` (`BG01`–`BG07`), inventoried separately and excluded from foreground collision pairs because node fill is background.
- Complete unordered foreground pairs: `C(29,2)=406`, unique and exhaustive.
- Visible non-whitespace codepoints: `162`, with unique glyph IDs and complete parent/source mapping.
- Critical relations: `37`, each with official native 1x raw crop, 1x overlay, and 8x nearest-neighbour overlay.
- Foreground empty masks: `0`.

Machine enumerations contain no reviewer decisions. Genuine manual reviewer records were written only after opening the evidence:

- `tables/manual_view_review.csv`: 20 view/ROI records
- `tables/manual_text_object_review.csv`: 14 text-parent records
- `tables/manual_glyph_review.csv`: 162 unique glyph-ID records; exact set equality with the machine glyph denominator
- `tables/manual_graphic_object_review.csv`: 15 graphic-object records
- `tables/manual_critical_relation_review.csv`: 37 unique relation-ID records
- `tables/hard_gate_manual.csv`: 13 hard-gate records

## Typography and visible content

Source controls were recomputed rather than inferred from pixel previews. The TikZ picture uses graphics `scale=1.100` without `transform shape`, so the node text itself has graphics scale `1.0`. T01–T07 and T09–T11 are explicitly `9.5pt`; their official PDF font size is `9.46451pt`. Caption objects T12–T14 use the inherited caption style and extract at `9.96264pt` in the official PDF.

T08, the top blanket annotation, is explicitly `9.2pt` and extracts at `9.16563pt`. This is the only numeric source-size advisory. It is fully legible at native 300dpi, intact at 8x nearest-neighbour inspection, and visually harmonious with the graph. Under the assigned R168 rule, old tiny-pixel/font contour thresholds are advisory unless there is actual unreadability, missing/tofu/wrong glyph, altered math meaning, or visibly severe imbalance. None is present, so T08 is not a hard defect.

Every one of the 162 visible codepoint IDs was checked against the opened original/target-overlay/mask-only contact-strip union for its parent line. No missing glyph, tofu box, wrong character, corrupted math sign, unreadable contour, or severe imbalance was found. The split contact sheets are balanced native-pixel strips; their ordered union covers each complete parent line, including the final `消去` in T14.

## Geometry, clipping, and overlap

- `CLIP_PIXEL_COUNT=0`
- `OVERLAP_CANDIDATE_PIXEL_COUNT=234`
- `OVERLAP_ILLEGAL_PIXEL_COUNT=0`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`

The 406-pair machine table contains 14 nonzero raw-mask contacts. Manual inspection classified all of them as intended design geometry:

- 9 graph-edge ↔ node/factor-border endpoint joins
- 4 graph-edge ↔ dashed-blanket-outline crossings needed to reach an enclosed variable
- 1 cancellation-arrow shaft ↔ arrowhead assembly

No candidate contact touches or obscures text. All other 392 unordered pairs have zero raw-mask intersection.

Measured hard-clearance examples:

- Own node/factor label to final-visible border: minimum blank clearance `14px` across T01–T07, above the `5px` hard floor.
- Blanket outline to enclosed node border: minimum blank clearance `5px` (alpha); z and y each have `11px`.
- Cancel annotation to arrow shaft: `28px` for T10 and `73px` for T11.
- Arrowhead to cancelled factor border: `5px`, with no contact.
- Full conditional to first caption line: `41px`.
- Two caption lines: `18px`; they are a single naturally wrapped semantic caption paragraph and have clean visible leading.
- Standalone crop leaves at least `36px` at the nearest text contour; figure-plus-caption crop leaves at least `26px` below the last caption contour. No visible contour is clipped.

All 37 native 1x relation crops and all 37 8x-nearest overlays were actually opened. The per-relation manual classifications are in `tables/manual_critical_relation_review.csv`; the 14 nonzero pair adjudications are duplicated compactly in `after_overlap_report.csv`.

## Visual and grayscale assessment

The graph is balanced and easy to read. Factor boxes, circular variables, the emphasized `θ` node, dashed blanket outlines, active edges, cancellation annotation, conditional formula, and caption have a coherent hierarchy. The color-to-grayscale conversion retains the dashed semantic cue and the factor-graph structure. No element is visibly crowded, malformed, severely imbalanced, clipped, or illegibly small. The figure integrates naturally with the surrounding printed page.

## Evidence map

Required evidence is present under this root:

- `renders/full_page_200dpi.png`
- `renders/full_page_300dpi.png`
- `renders/figure_crop_300dpi.png`
- `renders/standalone_300dpi.png`
- `renders/grayscale_300dpi.png`
- `renders/full_page_grayscale_300dpi.png`
- `renders/after_text_measurement_overlay_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_visual_acceptance.md`
- `after_overlap_adjudication.md`
- complete machine tables, masks, contact sheets, and critical-relation ROIs
- manual per-view, per-text-object, per-glyph-ID, per-graphic-object, per-critical-relation, and per-hard-gate ledgers

`MANIFEST.json` covers every ordinary payload file other than itself and includes the predetermined final `WRITE_STOPPED` marker entry. `WRITE_STOPPED` is created exactly once as the last content write. After that marker there are no further root content writes; read-only attributes are applied as sealing metadata and a root-external read-only audit verifies manifest paths/bytes/SHA256, unique strict-latest marker, parseability, attributes, and absence of ADS/cache/pyc/reparse artifacts.

## Final SA2 decision

There is no true R168 hard defect and no justified single-source edit scope. The only advisory is T08's readable and harmonious 9.2pt explicit annotation size. The correct next action is a fresh isolated SA1 review of the unchanged official R110 PDF and unchanged current source.

Outcome: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.
