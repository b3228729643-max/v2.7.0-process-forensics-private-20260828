# SA3 report: FIG-P630-01 against official R109

REPORT_ID: C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1-REPORT

HANDOFF_ID: C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1

## Assigned scope

Perform one completely fresh, isolated, read-only SA3 review of current UID `FIG-P630-01` against official R109. Independently locate the current figure, render and open the required views, establish a complete visible-object denominator and all unordered pairs, verify semantics/geometry/fonts/pixels/clipping/readability/page integration, and seal one noncircular evidence root.

## Completed

- Confirmed the startup root was absent and created only the assigned root.
- Confirmed official R109 identity: 817 A4 pages, 4,967,054 bytes, SHA-256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`.
- Confirmed current source identity: 2,342 bytes, SHA-256 `746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`.
- Located the exact current caption uniquely at physical page 680 (printed page 667).
- Rendered official full-page views at native 300 dpi and 200 dpi; created figure+caption, grayscale, semantic/object, text-measurement, page-integration, native1x critical-ROI, and nearest8x critical-ROI views.
- Actually opened every required view before creating any manual reviewer/decision/boolean fields.
- Established 17 visible semantic objects and reviewed all 136 unordered pairs manually, with per-ID observations.
- Audited 26 text/formula elements including five natural TeX script substrings and the not-equal operator.
- Verified the six-node directed dependency chain, two callouts, all arrow directions, formulas, caption consistency, geometry, grayscale hierarchy, page integration, zero true collision, zero clipping, and minimum text clearance.

## Decisions

- Main chain direction and Gibbs semantics are correct.
- `OVERLAP_CANDIDATE_PIXEL_COUNT=0`, `MASK_CONTAMINATION_PIXEL_COUNT=0`, `OVERLAP_PIXEL_COUNT=0`, `PIXEL_ADJUDICATION_STATUS=CLEAR`.
- `CLIP_PIXEL_COUNT=0`; `MIN_TEXT_CLEARANCE_PX=4`.
- All source-level ordinary text is at least 9.6 pt with graphics scale 1.0. Natural scripts are permitted and visibly exceed their pixel threshold.
- The only R168 advisory is 1 px glyph-outline/class variation; it is not unreadable or imbalanced and is not a hard failure.
- SA3 result: `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`.

## Files changed

Only files inside the assigned evidence root were created. Official PDF, current source, adjacent chapter text, central state/inventory, Git, and all other UID/reviewer evidence remained untouched.

## Unresolved

NONE within assigned SA3 scope. Main must still perform its own C_LOCAL acceptance and any broader integration decision.

## Validation

- Official input identities matched expected bytes, page count, format, and SHA-256.
- Caption hit count was exactly one.
- Visible-object denominator count: 17.
- Expected/reviewed unordered pairs: 136/136.
- Text elements audited: 26/26.
- Critical ROIs inspected at native1x and nearest8x: 10/10.
- All manual PASS booleans in `after_pixel_measurements.csv`: 26/26.
- All pair decisions in `after_overlap_report.csv`: 136/136, unresolved false, true collision pixels zero.

## Next action

Main C_visual coordinator should read this sealed handoff and independently decide C_LOCAL acceptance. Do not inherit this SA3-only result as global or final acceptance.
