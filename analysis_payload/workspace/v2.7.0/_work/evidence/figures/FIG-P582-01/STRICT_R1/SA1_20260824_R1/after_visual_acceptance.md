# FIG-P582-01 SA1 strict visual acceptance

## Candidate and coordinate convention

The frozen candidate is `main_full.pdf`, physical page 630 / printed page 617 / 图 31.7. All counting uses the direct-final-PDF native 300dpi 1:1 raw-mask coordinate. Nearest-8× files are human-observation only. Identity and render provenance are in `identity_and_anchor.md` and `render_manifest.json`.

## Manual views and content

The four schema views were opened and recorded in `four_view_reviewer_ledger.csv`: full-page 200dpi, native figure crop 300dpi, standalone body 300dpi, and grayscale body 300dpi. The separately mandated native full-page 300dpi view was also opened and recorded there as `FULL_PAGE_NATIVE_300DPI`; it is `renders/full_page_native_300dpi.png`. The overlay `after_text_measurement_overlay_300dpi.png` was also opened.

The visible mathematics, plot values, adjacent prose and caption are consistent: `h(U_i)=U_i^2`; sample sequence 0.8, 0.1, 0.7, 0.4; values `.640`, `.325`, `.380`, `.325`; target `1/3`; and the caption's down-up-down description. Grayscale distinction and page integration pass. Actual final-mask H_INK D has three failures and actual same-script E has two failures; neither result uses a PDF-span or cross-script font proxy.

## Strict gate matrix

| Gate | Result | Evidence |
|---|---:|---|
| Source effective general-reader font >=9.5pt | false | 29 elements fail in `after_font_audit.csv` |
| Native 300dpi glyph gates | false | revision111 leaves 6 calibrated/native glyph failures in `after_pixel_measurements.csv`: G0009, G0014, G0047, G0056, G0082, G0114 |
| Low-profile punctuation calibration | false | 21 same-codepoint raw-mask calibrations in `low_profile_punctuation_calibration.csv`; G0082 and G0114 fail H_INK/ink-area ratios, and 11 otherwise-calibrated dots remain below 9.5pt |
| Actual H_INK D ratio | false | 3 failures in `role_hierarchy_audit.csv`; native final-mask 1:1 only |
| Actual H_INK E ratio | false | 2 applicable failures in `role_e_actual_hink_audit.csv`; all other groups are PASS or N/A with an explicit same-script basis |
| Font visual harmony | false | four-view ledger: sub-9.5pt ticks/values/formula/annotations are a hard failure even where locally legible |
| Required-pair overlap and clearance | false | P0717: E014↓ ↔ E016 `.380`, overlap 3px, clearance 0px |
| Clip | true | `clip_report.csv`: 0 pixels |
| Glyph final-mask integrity | true | all 11 raw candidates resolved: nine detached-component projections and G0029/G0036 independent object replay; P0717 remains a relation failure, not mask contamination |
| Math/text/caption consistency | true | `semantic_reviewer_ledger.csv` |
| Grayscale distinction | true | four-view ledger |
| Page integration | true | four-view ledger |

## P0717 visual finding

The down-arrow tip of `E014` reaches the terminal `0` of `E016` `.380`. Direct 1:1 original/raw masks/intersection/overlay and their nearest-8× views were opened individually. The overlay shows three shared native pixels; no white clearance remains. This is a real rendered collision, not anti-aliasing and not an exempt intended relation.

## Glyph-mask integrity resolution

`glyph_reviewer_ledger.csv` and `glyph_machine_integrity.csv` are retained only as `SUPERSEDED_INITIAL_RAW` diagnostics. The active manual record is `glyph_final_reviewer_ledger.csv`: 139/139 unique final glyph IDs, all cells individually completed, with `glyph_final_*` paths and all twelve final contact sheets opened. Eleven initial candidate foreign-pixel cases are closed in `glyph_isolation_ledger.csv` and `glyph_final_mask_integrity.csv`: nine by detached-component projection; G0029/G0036 by complete pure independent object replay. Their three shared visible pixels are preserved in P0717 relation evidence, never trimmed or recast as contamination. Each special case has a native 1× and nearest-8× original/overlay/mask package under `glyph_integrity_packages/`. Evidence integrity is therefore true, while the true collision and other hard gates still make the figure fail.

## Result

`SOURCE_FONT_PASS=false`

`PIXEL_HEIGHT_PASS=false`

`LOW_PROFILE_CALIBRATION_PASS=false`

`FONT_VISUAL_HARMONY_PASS=false`

`H_INK_D_PASS=false`

`H_INK_E_PASS=false`

`REQUIRED_OVERLAP_CLEARANCE_PASS=false`

`CLIP_PASS=true`

`EVIDENCE_INTEGRITY_PASS=true`

`RESULT: FAIL→SA2`

This is an SA1 handoff verdict only; it is not a final publication approval.
