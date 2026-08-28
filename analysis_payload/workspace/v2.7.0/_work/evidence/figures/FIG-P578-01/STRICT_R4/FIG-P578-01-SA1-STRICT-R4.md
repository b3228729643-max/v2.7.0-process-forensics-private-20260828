RESULT: FAIL

# FIG-P578-01 SA1 strict R4 independent review — R91 official full-book page

## Scope and isolation

This SA1 review independently read only:

- Official continuous full-book PDF: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r91_fullbook/main_full.pdf`, physical page 626 (printed page 613), figure 31.5.
- Live figure source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`.

No prior FIG-P578-01 SA1/SA2/SA3/root report, conclusion, CSV, JSON/mask, or historical PASS/FAIL was read. No figure source, wrapper, chapter, macro, central inventory, or state file was changed.

The assigned page was directly rendered at 300 dpi as `SA1_R91_page626_300dpi.png`, exactly **2481×3508** pixels. All measurements use that unscaled image or direct 1:1 crops. The 200 dpi fit-page file is visual-only.

## Enumeration and audit coverage

| Object type | Count | Evidence |
|---|---:|---|
| Visible nonempty PDF text spans | 227 | `SA1_R91_pdf_span_inventory.csv` |
| State nodes / borders | 21 | `SA1_R91_object_inventory.csv` |
| Directed arrows plus return loop | 23 | `SA1_R91_object_inventory.csv` and `after_overlap_report.csv` |
| Branch labels | 16 | `SA1_R91_object_inventory.csv` |
| Return-condition labels | 2 lines | `SA1_R91_object_inventory.csv` |
| Caption / page read-guide | 1 / 3 visible lines | text inventory and full-page views |
| Pixel-ledger elements | 552 | 227 parent spans plus individually measured math, scripts, status-code, Latin/Greek, digit/capital, and operator substrings in `after_pixel_measurements.csv` |

Formal source-provenanced masks were made for `precheck`, `init`, `evaluate`, and `countproposal` (cyan=TEXT/FORMULA, magenta=NODE_BORDER, yellow=LINE_ARROW). The four local mask views, figure 100% ROI, full 100% page, fit page, and native grayscale view are in `SA1_R91/`.

## Hard failures

### 1. Base math/operator H_ink failures — 17 distinct glyphs

Goal §9.2.1 requires every base mathematical symbol/operator to have H_ink >=22px. The following native 300dpi glyphs fail. Bboxes are `[x0,y0,x1,y1]` in the unscaled 2481×3508 raster. Each ID is reproducible in `after_pixel_measurements.csv` and marked red in `after_text_measurement_overlay_300dpi.png`.

| ELEMENT_ID | Parent base formula | Source line | Operator | Native bbox px | H_ink px |
|---|---|---:|---|---|---:|
| FSP013-C07 | `1 ≤ c < ∞` | 35 | `∞` | [1333,302,1373,343] | 18 |
| FSP020-C02 | `ρ = p/(cq)` | 36 | `=` | [1067,366,1097,408] | 12 |
| FSP040-C01 | `X_{1:a}=∅, m=a=0` | 40 | `=` | [1680,629,1714,675] | 13 |
| FSP041-C05 | `X_{1:a}=∅, m=a=0` | 40 | `=` | [1833,629,1867,675] | 13 |
| FSP042-C02 | `X_{1:a}=∅, m=a=0` | 40 | `=` | [1921,629,1955,675] | 13 |
| FSP051-C02 | `m=a=0` | 44 | `=` | [1033,712,1067,759] | 13 |
| FSP052-C02 | `m=a=0` | 44 | `=` | [1128,712,1162,759] | 13 |
| FSP058-C01 | `X_{1:a}=∅` | 45 | `=` | [1172,767,1206,814] | 13 |
| FSP059-C02 | `a=N` | 46 | `=` | [1030,913,1064,960] | 13 |
| FSP066-C07 | `X_{1:N},m,a=N` | 48 | `=` | [1848,896,1882,942] | 13 |
| FSP069-C02 | `m=B` | 49 | `=` | [1039,1114,1073,1161] | 13 |
| FSP078-C04 | `X_{1:a},m=B,a<N` | 51 | `=` | [1729,1253,1763,1299] | 13 |
| FSP080-C02 | `Y∼q` | 53 | `∼` | [1037,1314,1071,1360] | 11 |
| FSP100-C02 | `U∼U(0,1)` | 57 | `∼` | [1036,1728,1070,1774] | 11 |
| FSP119-C02 | `ρ=p(Y)/(cq(Y))` | 62 | `=` | [936,1931,970,1977] | 13 |
| FSP187-C02 | return condition `a=N` | 100 | `=` | [603,2158,637,2205] | 13 |
| FSP189-C02 | return condition `m=B` | 100 | `=` | [613,2222,647,2269] | 13 |

This is sufficient by itself for `PIXEL_HEIGHT_PASS=false`. Source line 3 claims 10.7pt compact math clears 22px; the final R91 native raster contradicts that claim for the listed visible operators.

### 2. Precheck formula to outgoing arrow is 2px, not 3px

`EDGE_TEXT_precheck_to_valid` uses formal masks for the bottom `supp(q)` formula portion (`FSP028`, source line 37) and the R91 vector arrow drawn at source line 77. It has:

- overlap: 0 pixels;
- nearest ink-centre distance: 3.000px;
- strict pixel-edge clearance: `floor(3.000)-1 = 2px`;
- required text/formula-to-arrow clearance: >=3px.

Therefore the relation fails even without an overlap. See `SA1_R91_precheck_formal_masks_300dpi.png` and the corresponding row in `after_overlap_report.csv`.

### 3. Abnormal wrap in a central state label

At source line 56, `候选生成成功：立即令…` appears as **“候选生成成功：立 / 即令 …”**. Splitting the lexical unit “立即” across two visual lines is visibly abrupt and violates the requested abnormal-wrap/visual-harmony check. Its hard geometry itself is not the failure: text-to-border=8px, text-to-outgoing-arrow=9px, and line gap=29px all pass. The wrap must be reflowed, not merely accepted because it is legible.

## Other strict checks

| Check | Result | Measurement / basis |
|---|---:|---|
| Source effective font floor | PASS | 227 source-audit rows; normal reader text 9.6pt, compact formula blocks 10.7pt, natural scripts derived from legal bases; no whole-graphic scale detected. |
| Same-role source/pixel consistency | PASS | Uniform declared role/font cohorts; one state-machine panel, so cross-panel test is N/A. |
| Role hierarchy | PASS | Formula block 10.7/9.6=1.115, within [1.00,1.18]. |
| Illegal foreground overlaps | PASS | 0 pixels across 96 formal relations. |
| Text-to-node-border | PASS except no failed row | All 21 checked; minimum shown in ledger. `init` 8px, `evaluate` 9px, `countproposal` 8px. |
| Init four borders | PASS | top/bottom/left/right = 8/17/56/56px; threshold 5px. |
| Evaluate four borders | PASS | top/bottom/left/right = 9/17/113/117px; threshold 5px. |
| Init arrows and lines | PASS | inbound/outbound 27/13px; adjacent line gap 19px. |
| Evaluate arrows and lines | PASS | inbound/outbound 23/7px; adjacent line gap 12px. |
| Natural script | PASS | Init `X_{1:a}`: subscript `a`=17px (minimum), `∶`=18px, `1`=21px; threshold 15px. |
| Text-to-image edge / clipping | PASS | 283px to closest page edge; `CLIP_PIXEL_COUNT=0`. |
| Grayscale | PASS | State distinctions retain shape, dash, textual code, arrow direction, and location; not color-only. |
| Full-page integration | PASS | Caption/read-guide stay associated with the figure; no edge clipping. |

## Semantic and text audit

The algorithmic semantics are correct in the current source and page:

1. The contract checks scalar/domain/support/envelope conditions before any random call.
2. `a=N` is checked before `m=B`; hence zero target, including `N=B=0`, exits via `completed` before the budget branch.
3. Only a successful proposal advances `m`; uniform and numerical failures retain the last legal prefix and report a position.
4. Only the acceptance branch appends `Y` and advances `a`; ordinary rejection preserves `X_{1:a}` and `a`.
5. Envelope failure returns `invalid_input` and the `envelope_condition_failure` diagnostic.

The caption and page read-guide make the same distinctions (ordinary rejection, target completion, unfilled-budget stop, and envelope certification failure). Thus `MATH_SEMANTICS_PASS=true` and `TEXT_CONSISTENCY_PASS=true`; neither rescues the hard visual failures.

## Required repair direction

1. Rework the base-math treatment at source lines 35, 36, 40, 44–46, 48–49, 51, 53, 57, 62, and 100 so each listed operator has H_ink >=22px in an unscaled native 300dpi rebuild. Widen/reflow nodes as necessary; shrinking cannot resolve the deficiency.
2. Add at least one more blank native pixel between the precheck bottom formula and the line-77 outgoing arrow, then remeasure.
3. Reflow line 56 so “立即” remains intact while retaining its current clearance minima.
4. Rebuild a fresh continuous full-book candidate and repeat isolated SA1/SA3/root review. This FAILED SA1 result must not proceed to SA3 as a candidate pass.

## Required artifacts delivered

All paths below are inside the permitted SA1-only subdirectory `STRICT_R4/SA1_R91/`:

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `after_visual_acceptance.md`
- `SA1_R91_page626_300dpi.png`, `SA1_R91_figure_100pct_roi.png`, `SA1_R91_page626_fitview_200dpi.png`, `SA1_R91_page626_grayscale_300dpi.png`
- `SA1_R91_precheck_formal_masks_300dpi.png`, `SA1_R91_init_formal_masks_300dpi.png`, `SA1_R91_evaluate_formal_masks_300dpi.png`, `SA1_R91_countproposal_formal_masks_300dpi.png`
- `SA1_R91_pdf_span_inventory.csv`, `SA1_R91_object_inventory.csv`, and `SA1_R91_generate_strict_evidence.py` (reproducible independent measurement method)

This is an SA1 strict FAIL only; it is not an SA3 or root signature.
