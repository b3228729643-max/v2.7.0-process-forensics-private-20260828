RESULT: FAIL

# FIG-P109-01 independent SA1 strict requalification (R1)

## Scope and authority

- Assigned scope: requalify old-conversation figure FIG-P109-01 / 图 7.1 without using any old PASS or old subagent conclusion.
- Source audited read-only: `fig_v1_c07_convex_set.tex`.
- Final integration artifact: official R90 `main_full.pdf`, physical page 116 of 813.
- Goal gate: §9.2.1 A-I. Any failed or unmeasured gate forces FAIL.
- Files changed: evidence in this `STRICT_R1` directory only; no source, common style, inventory, or state file was modified.

## Rendering provenance and four-view inspection

The official page was extracted directly from R90. Poppler rendered the full A4 page at 200dpi (1654x2339) and native 300dpi (2481x3508). No 300dpi output was resized. The figure crop is [620,1200,1905,2055), 1285x855. The standalone wrapper was freshly compiled against the current source and directly rendered at 300dpi; its reviewed crop is [620,200,1905,1055), also 1285x855. The grayscale image preserves the same 1285x855 pixels. Exact commands and all ROI coordinates are in `render_commands.txt`.

Actually inspected views:

- `full_page_200dpi.png`: page flow and integration;
- `figure_crop_300dpi.png`: native crop;
- `standalone_figure_crop_300dpi.png`: fresh independent build;
- `grayscale_300dpi.png`: grayscale hierarchy;
- five native 1:1 ROIs plus `roi_region_boundary_overlap_overlay_300dpi_1to1.png`.

The standalone log contains zero matches for LaTeX Error, Package Error, Undefined control sequence, Emergency stop, Fatal error, Overfull, Underfull, undefined references, rerun warning, or lost floats.

## A. Source-level effective font audit — FAIL

There is no `scale`, `transform shape`, `resizebox`, or `scalebox`; `graphics_scale=1.0` for every element. PDF span sizes independently confirm the source resolution: 9.1656bp corresponds to 9.2 TeX pt, while 9.9626bp corresponds to 10.0 TeX pt.

| ELEMENT_ID | Source locus | Role | declared/effective pt | Result |
|---|---|---|---:|---|
| T_ENDPOINT_X | line 24; global `every node` `small` | point label | 10.0 / 10.0 | PASS |
| T_ENDPOINT_Y | line 25; global `every node` `small` | point label | 10.0 / 10.0 | PASS |
| T_FORMULA_Z | lines 6-7, 27-28 | formula block | 9.2 / 9.2 | **FAIL** |
| T_REGION_CJK | lines 29-30 | ordinary annotation | 9.2 / 9.2 | **FAIL** |
| T_REGION_C | lines 29-30 | ordinary annotation | 9.2 / 9.2 | **FAIL** |
| T_FORMULA_CONCLUSION | lines 8-10, 31-33 | formula block | 9.2 / 9.2 | **FAIL** |
| T_CAPTION_LABEL | line 35 + common style line 305 | caption | 10.0 / 10.0 | PASS |
| T_CAPTION_TEXT | line 35 + common style line 305 | caption | 10.0 / 10.0 | PASS |

Four reader-information elements are below the mandatory 9.5pt floor. `SOURCE_FONT_PASS=false` regardless of apparent readability.

## B-C. Native 300dpi text pixels — FAIL

The threshold uses local-background RGB difference >=20/255, and mixed formulas are split to traceable glyph IDs. Full per-glyph bboxes and ink counts are in `after_pixel_measurements.csv`.

| Script class | measured range | hard minimum | Result |
|---|---:|---:|---|
| CJK | 34-38px | 30px | PASS |
| digits / uppercase | 26-34px | 24px | PASS |
| lowercase / Greek | 20-36px | 17px | PASS |
| base math operators | 4-38px | 22px | **FAIL** |

The precise failures are `G_Z_003D_01` (`=`, 13px), `G_Z_2212_01` (minus, 4px), and `G_CONC_2212_01` (minus, 4px). They are source-controlled base-formula glyphs, not legal TeX scripts. `PIXEL_HEIGHT_PASS=false`.

## D. Same-class and cross-panel ratios — FAIL

There is one panel. Source-level same-role sizes are internally equal: point labels 10.0/10.0, formula blocks 9.2/9.2, and region annotation 9.2/9.2. At native pixels, however:

- `T_ENDPOINT_X`: H_ink=21px, point-label median=25px, ratio=0.84;
- `T_ENDPOINT_Y`: H_ink=29px, point-label median=25px, ratio=1.16.

Both are outside [0.92,1.08]. The two formula lines are both 39px and ratio 1.00. Because the endpoint-label group fails, `SAME_CLASS_RATIO_PASS=false`.

## E. Semantic-role hierarchy — PASS as a separate gate

The only ordinary annotation base is the region label at 9.2pt. Both formula blocks are also 9.2pt, source-role ratio 1.00; their whole-line H_ink=39px versus the CJK base H_ink=34px gives 1.147, within formula [1.00,1.18]. Endpoint labels are 10.0/9.2=1.087 of the source base, below the absolute emphasis cap 1.25. No normal label is abnormally enlarged. This does not cure the absolute source floor, glyph threshold, or same-class failure.

## F. Pixel overlap, clearance, and clipping — FAIL

Text masks were separated from visible blue/teal pixels. The convex boundary, line segment, five markers, and note border were independently rebuilt from the R90 PDF vector objects, so a later text draw or white background cannot hide a geometric intersection.

Critical results in full-page 300dpi coordinates:

- `T_REGION_C` vs `G_BOUNDARY`: **29 illegal overlap pixels**, intersection bbox [1726,1311,1753,1334), required 0.
- `T_REGION_CJK` vs `G_BOUNDARY`: overlap 0, nearest clearance **1px**, at text (1711,1306) / boundary (1711,1305), required >=3px.
- formula z vs segment: overlap 0, clearance 45.880px.
- endpoint x/y labels vs their markers: overlap 0, clearances 49.497px / 48.083px.
- conclusion formula vs note border: overlap 0, clearance 16px, required >=5px.
- region CJK vs region C text: overlap 0, clearance 7px, required >=4px.
- minimum reviewed text-text clearance is 7px; overall minimum is 0 because of the illegal C-boundary intersection.
- all audited reader masks remain inside the evidence crop; minimum crop-edge clearance is 25px. All PDF vector bboxes lie within the physical page. `CLIP_PIXEL_COUNT=0`.

The measured 29px intersection is visible in both the native color and grayscale crops: the upper-right convex boundary runs through the glyph C. `OVERLAP_PIXEL_COUNT=29`, so the figure cannot pass.

## G. Visual coordination and page integration

- Visual harmony: **FAIL** because the region label is fused with the subject boundary and the same-role endpoint-label ink ratio is 0.84/1.16. The 9.2pt elements are not visually huge, but are below the source contract; modest enlargement is required rather than further reduction.
- Grayscale: PASS. Luminance is approximately boundary 71, teal marker 96, ink 40, light fill 245, and note border 212 on white 255. Boundary, segment, endpoints, interior markers, and note remain structurally distinguishable without color.
- Page integration: PASS. The figure has balanced width and vertical spacing, the caption is attached, surrounding paragraphs are intact, and no abnormal blank area or clipping appears on physical page 116.

## Mathematics, text, caption, and reading order

- Math semantics: PASS. For lambda in [0,1], z=lambda*x+(1-lambda)*y lies on the endpoint segment; the 0.25/0.50/0.75 markers are collinear and the entire segment is inside C.
- Text consistency: PASS. Variables x, y, z, lambda, and C agree with source lines 24-33, chapter lines 246-252, and the caption.
- Reading order: PASS: region C and endpoints -> segment/interior points -> convex-combination formula -> conclusion note.
- Caption: PASS. It states one direct reading conclusion and agrees with the adjacent definition.

## Mandatory acceptance matrix

```text
SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = true
OVERLAP_PIXEL_COUNT = 29
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 0
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true
```

## SA2 executable repair instructions

1. Source lines 29-30: move the region-label anchor left, for example from `(3.20,1.86)` to `(2.45,1.86)` while retaining `anchor=north east`. This predicts roughly 0.75 x-units = 28.8pt = 120 native pixels of left shift and removes both the 29px C-boundary intersection and the 1px `域`-boundary clearance. Re-render and measure; do not accept the predicted clearance as evidence.
2. Source style lines 4, 6, 9 and the explicit font at line 29: raise all 9.2pt reader text to at least 9.6pt (with proportionate leading, e.g. 11.6pt). Keep the existing 10pt endpoint/caption text unless the ratio repair below requires a coordinated change. Do not shrink any reader text below 9.5pt.
3. The literal glyph audit still leaves the equals/minus operators below the 22px operator floor. After the 9.6pt rebuild, remeasure those exact glyph IDs. If still below threshold, SA2 must use an approved math-typography treatment or an equivalent formula layout whose operator ink satisfies the contract; ordinary font enlargement alone is not sufficient evidence.
4. The x/y endpoint-label whole-ink heights are 21/29px. If the strict same-role check remains literal after rebuild, use symmetric labels such as `点 x` and `点 y` at the same >=9.6pt effective size (or another semantically equivalent symmetric label design), then remeasure to [0.92,1.08]. Do not use invisible `vphantom` because it does not increase H_ink.
5. Rebuild an independent page and standalone candidate at native 300dpi, regenerate every font/pixel/ratio/overlap/clip file, and rerun SA1 from scratch. This R1 report is a FAIL and does not qualify the figure.

## Subagent handoff fields

- completed: official-page extraction, four-view inspection, source font trace, native glyph measurements, vector-mask overlap/clearance audit, math/text/caption/page checks, and strict FAIL report.
- decisions: old PASS was not read or reused; 29px C-boundary overlap and 9.2pt floor violations are hard blockers.
- unresolved: SA2 source correction and a new independent R2 audit.
- validation: all generated evidence is under this `STRICT_R1` directory; no project source/state/inventory modification.
- next_action: root assigns one source-writer SA2 to apply the four targeted repairs, rebuild, then launches a fresh independent SA1 round.
