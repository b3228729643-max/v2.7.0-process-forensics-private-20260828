# FIG-P157-01 — root validation of independent official-R92 SA1 R3

Root rejected the superseded 21:49 preflight because it used broad/combined graphic masks. The independent reviewer rebuilt separate G01/G02 curve masks, oriented text measurements, and focused nearest-pixel evidence.

- The repaired validation annotation now passes: T02 versus each curve has 0 overlap and 163.125 px foreground clearance.
- The remaining blocker is `T04_SELECTION_KEY` (`选择复杂度`, source lines 8--9 and 51--52) versus `G06_X_AXIS_ARROW` (lines 24 and 59): 0 overlap but only 1.2361 px foreground clearance, below the 3 px minimum.
- Root viewed `T04_selection_vs_xaxis_raw_1to1_300dpi.png` and its nearest-pixel overlay; the x-axis visibly crowds the top of the label. The focused ledger gives nearest foreground coordinates `(1438,1189)` and `(1437,1187)`.
- Source font, native pixel heights, same-class/role ratios, illegal overlap, clipping, semantics, caption, grayscale, and page integration otherwise pass.

Root decision: the corrected independent `RESULT: FAIL` is confirmed on official R92 physical page 170. No SA3 is permitted. Return only the T04/G06 clearance issue to the figure-specific SA2.
