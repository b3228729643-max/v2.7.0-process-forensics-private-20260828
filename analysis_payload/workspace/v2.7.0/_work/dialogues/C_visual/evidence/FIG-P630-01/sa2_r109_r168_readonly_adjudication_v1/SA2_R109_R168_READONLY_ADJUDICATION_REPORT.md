# FIG-P630-01 — R109 / R168 read-only SA2 adjudication

## Fixed identity and scope

- `HANDOFF_ID`: `C-FIG-P630-01-R109-SA2-R168-READONLY-ADJUDICATION-V1`
- `actual_instance`: `/root/sa2_fig_p630_r109_r168_readonly_adjudication_v1`
- `model`: `gpt-5.6-sol`
- `reasoning_effort`: `xhigh`
- `fork_turns`: `none`
- `startup_absent`: `true`
- `UID`: `FIG-P630-01`
- `role`: one-and-only read-only R168 adjudication-first SA2
- `source_changes`: `0`
- `TeX/LuaLaTeX/latexmk`: `0`
- `Git`: `0`

## Current-input identity and independent location

The official R109 PDF is 4,967,054 bytes, has SHA-256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`, contains 817 A4 pages, and matches the dispatch identity. The current figure source is 2,342 bytes with SHA-256 `746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`, also an exact match.

The figure was independently located by the current source caption “满条件把联合目标转为单坐标更新，扫描后得到需以 MCSE、ESS 与轨迹诊断的相关样本” and the visible `图 33.1` content on R109 physical PDF page **680** (printed page 667). The historical task-card page number was not used as location evidence.

Necessary adjacent V5-C04 text confirms the intended reading order: given `x_{-j}`, form the full conditional, update only `x_j`, compose the scan kernel, obtain correlated samples, then diagnose MCSE/ESS/trajectory; the arrows are learning/computational dependencies rather than generative-time arrows, and target invariance alone does not establish irreducibility, convergence, or rapid mixing.

## Views actually opened before manual observations

The reviewer opened and inspected:

1. `full_page_native300dpi.png` — complete R109 physical page 680.
2. `figure_caption_native300dpi.png` — widened native 300 dpi figure and caption with all objects and margins.
3. `figure_native1x.png` — native 1× figure view without post-render resizing.
4. `page_integration_native300dpi.png` — figure, caption, and adjacent reading-order text in page context.
5. `grayscale_figure_caption_native300dpi.png` — native grayscale view.
6. `overlay_all_objects_native300dpi.png` — all frozen object IDs and vector bboxes.
7. `semantic_mask_overlay_native300dpi.png` — separated text/geometry semantic-mask overlay.
8. `roi_conditional_math_native1x.png` and `roi_conditional_math_nearest8x.png` — U+2212/U+22C5 and conditioning formula.
9. `roi_not_equal_native1x.png` and `roi_not_equal_nearest8x.png` — U+2260 warning operator.
10. `roi_correctness_bottom_clearance_native1x.png` and `roi_correctness_bottom_clearance_nearest8x.png` — tightest node-text/border clearance.

The first mechanical crop was found to be 5 px too tight on the right. Before any manual observation was written, it was widened and regenerated; the PDF was never clipped.

## Frozen denominator and exhaustive pair universe

`visible_object_denominator.csv` freezes **36** visible foreground objects in deterministic order:

- 20 reader-visible text/formula lines or caption runs (`T01`–`T20`);
- 9 node/boundary borders (`B01`–`B09`);
- 5 directed flow arrows (`A01`–`A05`);
- 2 non-directional leaders (`L01`–`L02`).

Automatic TeX math spans are measured beneath their parent text object, which preserves a stable semantic object denominator while still auditing scripts and mixed-font substrings. `unordered_object_pairs.csv` contains the complete `36 choose 2 = 630` unordered pairs, exactly once each. After all required views were opened, `manual_object_observations.csv` recorded all 36 object IDs and `manual_pair_observations.csv` recorded all 630 pair IDs. Counts and ID sets match with no omission or extra row.

Manual pair note codes:

- `N0`: native view and overlay show no illegal contact or ambiguous interaction;
- `N1`: text bbox is contained by its owning node bbox, but ink and border foregrounds are separated;
- `N2`: `P0036` (`T02`,`T03`) has a 3.613 px vector-bbox line gap, but native 1× and nearest 8× show distinct, fully readable ink; R168 treats this as advisory absent a true overlap or unreadability;
- `N3`: `P0390` (`T14`,`B07`) has 5.792 px minimum inner vector-bbox clearance and the dedicated ROI confirms no contact;
- `N4`: legal flow-arrow or leader endpoint proximity to its intended node perimeter; no text is involved.

Disposition totals are 602 `CLEAR`, 17 `CLEAR_CONTAINED`, 1 `CLEAR_R168_ADVISORY`, 1 `CLEAR_TIGHT`, and 9 `LEGAL_CONTACT`; none is `TRUE_COLLISION`, `UNRESOLVED`, or `DISPUTED`.

## Source font and native-pixel adjudication

The current source explicitly sets core and side text to 9.6 pt and the boundary statement to 10.0 pt bold. There is no `scale`, `transform shape`, `resizebox`, or `scalebox`; cumulative graphics scale is 1.000. PDF vector extraction reports 9.564 pt for the 9.6 pt source text and 9.963 pt for the 10 pt boundary/caption output. All base visible text therefore satisfies the active 9.5 pt requirement.

The native 300 dpi span measurements contain 43 traceable spans. Regular CJK node/side text measures 35–36 ink pixels; the bold boundary text measures 40 px; Latin caps/digits measure 28–33 px; math lowercase `x` measures 20 px and therefore satisfies the lowercase/x-height class; automatic math scripts measure 29 px in the raw span boxes and derive from a compliant 9.6 pt base. Regular CJK same-class ratio is `36/35 = 1.029`, and boundary-to-base role ratio is at most `40/35 = 1.143`; both are visually and numerically stable.

U+2212 in `x_{-j}` and U+22C5 in `π_j(⋅∣x_{-j})` are present, correct, and non-tofu. Their low-pixel outline behavior is R168 advisory only; native 1× and nearest-neighbor 8× views show no wrong codepoint or unreadability. U+2260 in “正确内核 ≠ 快速混合” is also present and clear.

## Pair, geometry, clipping, and semantics adjudication

- Text/geometry separated-mask intersection pixels: `0`.
- `OVERLAP_CANDIDATE_PIXEL_COUNT`: `0`.
- `MASK_CONTAMINATION_PIXEL_COUNT`: `0`.
- Canonical `OVERLAP_PIXEL_COUNT`: `0`.
- `PIXEL_ADJUDICATION_STATUS`: `CLEAR`.
- `CLIP_PIXEL_COUNT`: `0`.
- Minimum node-text/border clearance: `5.792 px` (`T14`–`B07`), confirmed in native and nearest-8× ROI.
- Minimum text-to-arrow/leader gap: `19.204 px` (`T01`–`A01`).
- The only sub-4 px vector-bbox text-line observation is `T02`–`T03` at `3.613 px`; rendered ink is separate and readable, with no actual illegal contact. Under the fixed R168 hard-fail boundary this is advisory rather than a source-change trigger.

The five main arrows form the correct chain: `joint -> conditional -> coordinate kernel -> scan kernel -> correlated sample -> diagnostics`. Arrowheads are singular, visible, stop at the intended node boundaries, and do not cross text. The two side connectors are deliberately non-directional leaders, so they do not introduce false dependency directions. Labels, variables, caption, and adjacent reading-order prose agree. The asymmetric side boxes create a balanced diagonal frame without a naked-eye imbalance; the main chain remains the first visual focus. Grayscale and full-page integration remain clear.

## Manual decision matrix

- `SOURCE_FONT_PASS = true`
- `PIXEL_HEIGHT_PASS = true`
- `SAME_CLASS_RATIO_PASS = true`
- `ROLE_RATIO_PASS = true`
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 0`
- `MASK_CONTAMINATION_PIXEL_COUNT = 0`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = CLEAR`
- `CLIP_PIXEL_COUNT = 0`
- `VISUAL_HARMONY_PASS = true`
- `MATH_SEMANTICS_PASS = true`
- `TEXT_CONSISTENCY_PASS = true`
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true`
- `unresolved = none`

## Sealed decision

No true missing/tofu/wrong codepoint or math semantic defect, actually unreadable text, naked-eye obvious imbalance, true clipping/illegal overlap, or substantive semantic/geometry error exists in the current R109 rendering.

`P630_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

This SA2 made zero source changes and did not start SA1 or any other role.
