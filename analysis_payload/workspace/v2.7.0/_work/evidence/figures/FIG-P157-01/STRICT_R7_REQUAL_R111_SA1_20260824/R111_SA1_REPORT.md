# FIG-P157-01 — R111 independent SA1 requalification report

`RESULT: FAIL → SA2`

Candidate reviewed: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf`, physical page 170 / printed page 157. This SA1 performed no source, build, central-state, inventory, or candidate-PDF writes.

## EVIDENCE_INTEGRITY: PASS

The final evidence chain is independently requalified and registered in `R111_CANONICAL_EVIDENCE_REGISTER.csv`.

- The candidate’s direct 300 dpi render is identified in `render_manifest.json`.
- All 80 visible glyphs have a new SA1 manual ledger: native original, target overlay, and mask each opened at 1×, plus every 8× contact-sheet cell. Machine integrity reports zero missing/foreign glyph-mask pixels.
- All 20 foreground semantic objects generate exactly 190 unordered pairs; all 154 mandatory text relations are present and pass. Every critical/failure relationship package was personally opened at 1× and 8×.
- Curve evidence was recomputed from peer-independent raw final-visible masks on the same native grid. The partial first attempt is preserved but explicitly noncanonical; the `r111_curve_raw_recheck_v2` package is the sole authority.
- Calibration validity—not merely its conclusion—was rechecked for font, weight, colour, effective size, native 300 dpi, component count, crop and mask purity. All five methods are valid.
- D/E were recomputed from the actual 1× final-PDF masks. The four required whole-figure views and each panel/role/script font/weight/colour judgement are separately logged by this reviewer.
- Corrected source locations are supplied in `R111_SEMANTIC_SOURCE_MAP.csv`; stale raw baseline locators and preliminary PENDING measurements are expressly not final authority.

No evidence-integrity defect blocks SA2 from using this package. Evidence integrity does not mean the figure passes its hard gates.

## FIGURE_HARD_GATES: FAIL

| Gate | Result | Exact finding |
| --- | --- | --- |
| Source font size | PASS | All effective reader-visible text sizes are at least 9.5 pt; minimum region-label effective size is 9.8192 pt. |
| Pixel / calibrated low profiles | FAIL | G0005, G0014, G0050, G0068, and G0080 each fail valid same-codepoint H-ink and area ratio `[0.92,1.08]`. |
| D same-class ratio | PASS | All 80 native 1× glyph rows are within `[0.92,1.08]` against their same-panel/same-role/same-script median. |
| E role hierarchy | FAIL | Region-label CJK median 35 px / annotation CJK base 37 px = 0.9459, strictly below `[0.95,1.10]`; eight glyph rows affected. |
| All unordered pairs | FAIL | 189/190 PASS; `P0155` (`O-G001`/`O-G002`) is the one unapproved pair failure. |
| Independent curve masks | FAIL | Canonical raw final-visible masks share 139 px and clearance 0; source functions do not algebraically cross. |
| Clip and text clearance | PASS | `CLIP_PIXEL_COUNT=0`; 20/20 object clip rows pass; all 154 mandatory text relations pass; minimum text relation clearance is 16 px. |
| Font size/weight/colour visual coordination | PASS | Human per-role/script review finds no oversized, undersized, abrupt-weight, abrupt-colour, grayscale, density, or page-fusion defect. This visual PASS does not waive numeric pixel/D/E failures. |
| Mathematical and text semantics | FAIL / PASS | Labels, caption, formulas, marker and reading order are correct, but the visibly merged independent curves fail representation-semantic fidelity. |
| Grayscale and page integration | PASS | Solid/dashed/marker/reference hierarchy remains readable in grayscale; full-page placement and caption integration are balanced. |

## Required SA2 actions

1. Separate the training and validation stroke envelopes so peer-independent final-visible raw masks have zero unapproved intersection and a positive visible gap; preserve the source functions and rerender from the modified source.
2. Correct the five valid low-profile calibration failures rather than treating punctuation as exempt; regenerate target/calibration masks and 300 dpi evidence.
3. Adjust the region-label/ordinary-annotation actual pixel hierarchy so the region-label median meets the strict 0.95 lower bound without making labels visually jarring or less readable.
4. After any source change, rebuild the official full book and rerun all glyph, D/E, pair, raw-mask, draw-order, clip, grayscale, and page-integration gates from the new candidate. A prior PASS cannot be inherited.

## Required acceptance fields

```text
FIGURE_ID: FIG-P157-01
SOURCE_FONT_AUDIT: PASS
PIXEL_HEIGHT_AUDIT: FAIL (5 calibrated low-profile glyphs)
SAME_CLASS_RATIO_AUDIT: PASS
ROLE_RATIO_AUDIT: FAIL (35/37 = 0.9459)
OVERLAP_PIXEL_COUNT: 139 (P0155)
CLIP_PIXEL_COUNT: 0
MIN_TEXT_CLEARANCE_PX: 16
VISUAL_HARMONY: PASS
MATH_SEMANTICS: FAIL (visible curve-envelope merge)
TEXT_CONSISTENCY: PASS
GRAYSCALE: PASS
PAGE_INTEGRATION: PASS
```

## Explicit retractions and handoff boundary

The preliminary 37 px P0155 removal-contribution count is invalid because it modifies a curve relative to its peer. The 516 px claim is unverified and was not reproduced by the R111 method. Neither is used here. The sole canonical curve finding is 139 px final-visible raw-mask intersection with 0 px clearance.

This is an independent SA1 FAIL handoff to SA2, not a source-edit instruction execution. `WRITE_STOPPED.json` will be written only after the machine final check and no further evidence writes may follow it.
