# FIG-P756-01 SA3 final visual acceptance

Candidate identity independently verified: official PDF SHA-256
'062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814',
813 physical pages, Figure 37.8 on physical page 801 / printed page 788. Current
source SHA-256 is
'00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA'.

I opened the final native 300 dpi full page, figure crop, standalone figure,
grayscale figure, and text-measurement overlay. I also opened all 19 glyph
contact sheets (378 visible cells), all 5 graphic contact sheets (58 cells), all
11 critical-relation contact sheets (129 cells), the three same-codepoint
calibration contact sheets, GLY0215's original/overlay/mask/8x cards, both
CAL02 reference instances' original/overlay/mask/8x cards, and the specially
selected endpoint/border 8x cards for badge, feedback, route, engine-pool,
validation, report separator, and all four lower-arrow shaft/head joins.

Visual findings:

- Native 1x masks are complete and pure for every visible glyph; no missing
  stroke, neighboring glyph capture, same-color graphic capture, or foreign
  pixel was found. Seven raw-bbox shared boundary pixels were deterministically
  assigned at native 1x by raw floating-bbox pixel-cell coverage; reconciliation
  is 7 resolved / 0 remaining.
- Node, badge, line, arrowhead, opaque fill, white label, and report-separator
  masks are visually complete. Opaque fills and the white separator are
  noncompeting layers only where documented by the object/pair ledger.
- The full-page, crop, standalone and grayscale views are legible, balanced,
  and uncropped. The five-station loop, feedback route, supervised and
  unsupervised ingress, engine pool, isolation validation, and one-way report
  outlet are visually unambiguous.
- GLY0215 itself is visually a complete clean two-dot colon; this does not
  override its quantitative low-profile punctuation failure.

FONT_VISUAL_HARMONY_PASS: true

The ordinary visual, overlap, clipping, gray-readability, semantic, and font
harmony checks pass. The strict terminal visual gate nevertheless fails because
GLY0215's independently calibrated same-codepoint area ratio is
34 / 37 = 0.9189, below the inclusive lower bound 0.92.

FINAL_VISUAL_GATE: FAIL_TO_SA2
