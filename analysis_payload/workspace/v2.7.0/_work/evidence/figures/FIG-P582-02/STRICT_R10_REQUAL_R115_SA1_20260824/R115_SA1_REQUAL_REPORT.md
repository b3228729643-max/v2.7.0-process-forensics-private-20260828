# FIG-P582-02 — R115 independent SA1 requalification

**Final result: `FAIL_TO_SA2`.** This is an independent current-identity review of the official R95 PDF only; no legacy FIG-P582-02 evidence/PASS/terminal outcome and no FIG-P580 outcome was read.

## Separated conclusions

- `FIGURE_HARD_GATES = FAIL`
  - Font effective size: **67/149** visible glyphs are below 9.5pt.
  - Strict native-300 raw-height gate: **3** failures — `F582_G011` `=` is 12px < 22px; `F582_G012` `≈` is 18px < 22px; `F582_G084` caption `一` is 9px < 30px.
  - `FONT_VISUAL_HARMONY = FAIL`: size is visibly undersized; weight and color are separately PASS.
- `EVIDENCE_INTEGRITY = FAIL`
  - **21** low-profile punctuation rows lack the mandated *independent*, same-codepoint/font/weight/effective-pt calibration closure. The staged direct target-mask samples are recorded but are not misrepresented as the required calibration.
- Physical non-fail findings are preserved independently: 149 raw glyph masks have zero recorded missing/foreign ink; strict E has 0 failures; 125 un-ordered text/text or text/graphic relations have 0 failing rows and 0 nonzero-overlap rows; 10 edge checks pass (minimum raw clearance 32px); three pre/opaque/final-visible checks pass with XOR=0; mathematical and neighboring-text semantics pass.

## Manual evidence actually opened

The current reviewer opened every cell in CS001–CS015 at 8× nearest, all 9 table-designated critical relation packages plus R0085, three occlusion packages, 12 low-profile samples, all 8 graphic masks, and the four required final views. The actual-open ledgers identify each sheet/cell/package and distinguish native 1× measurement from 8× visual confirmation.

## Required repair handoff

SA2 must make a white-list source repair: raise all ordinary visible chart text to >=9.5pt in the final PDF, restore base math `=`/`≈` and CJK `一` to their true required native-pixel thresholds, provide valid independent punctuation calibration, build a new official candidate PDF, then regenerate all masks/relations/visual views before a new independent SA1. No source, central state, inventory, or official build was modified in this review.
