# FIG-P126-01 R12 local SA2 report

HANDOFF_ID: `A-R115-P126-SA2-DIRECT-BUILD-R12-20260828`

## Formal result

`LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`

The unique authorized R12 direct LuaLaTeX build completed naturally with one PDF, after which the build slot was released and no further TeX occurred. The sole PDF is 34,054 bytes with SHA-256 `F8A9112C51511A96C64855CC8A0B1B69F15C1272804D96EFC7BF8C079E7DF0AA`.

## Fresh denominator and observation

- Reader-visible objects: `N=60` = 25 glyphs + 9 lines + 2 protective backgrounds + 4 square markers + 20 curves.
- All unordered pairs: `C=1,770`; pair IDs and tuples are unique and exact.
- Machine candidates: 211. All eleven candidate sheets were actually opened after the denominator was frozen.
- Manual ledgers: objects 60/60, pairs 1,770/1,770, views 21, glyph/codepoint 25, math/semantic 10, critical measurements 6.
- Pair manual non-PASS: 0. Clip, missing glyph, tofu, and wrong-codepoint counts: 0.

## Hard defect

`HARD-LEGEND-X2-CONTINUOUS`: the current R12 x2 legend key renders as one uninterrupted 73-pixel run with zero internal blank runs at native 300 dpi. Native1x, nearest8x, color, and grayscale views agree. It therefore still fails to visually encode the segmented/dashed x2-update role.

This is not an R168 advisory-size issue. It is a current rendered semantic/role-encoding hard defect.

## Passed regressions

- Digit 6 is readable and has a measured 7-pixel blank gap from other visible ink; it no longer touches its marker, arrow, contour, digit4, or labels5/7.
- Digit 7 remains clear with an 8-pixel blank gap.
- The four contours remain level sets of the same positive-definite quadratic; q0--q7 remain exact alternating coordinate minimizers and the objective values strictly decrease `2.92→2.56→1.28→0.64→0.32→0.16→0.08→0.04`.
- Axis labels, optimum/final-point meanings, caption, grayscale figure, and page integration otherwise pass.

No commit, source edit after the build, second build, fresh role, second UID, Git action, or central-state write was performed.
