# FIG-P577-01 root evidence rejection

Status: **CURRENT SA1 TERMINAL REJECTED / CORRECTED R2 REQUIRED**.

The existing `STRICT_R1_FINAL.md`, `machine_terminal.json`, glyph totals, pixel
totals, D/E totals and their PASS/FAIL summaries are not admissible as terminal
evidence. They remain historical files and must be marked `SUPERSEDED` by the
replacement audit; this root note does not erase them.

## Decisive evidence defect

- Registered record: `T022_G01`, declared `CHAR=（` (`U+FF08`).
- Existing manifest: `glyph_evidence/T022_G01/manifest.json`.
- Existing native mask: `glyph_evidence/T022_G01/raw_mask.png`.
- Existing 8× nearest-neighbour view: `glyph_evidence/T022_G01/roi_8x_nearest.png`.
- The manifest reports `H_ink_px=3`, while the mask is only a small solid block
  (approximately 2×3 native pixels) and does not have the outline of a
  full-width left parenthesis. Therefore the claimed
  `CHAR ↔ actual shape ↔ parent ↔ bbox ↔ mask` mapping is false.

One false mapping invalidates the claimed exact 342/342 mapping coverage and all
derived glyph-height, D/E and aggregate terminal counts. Unknown or
unisolated glyphs must be recorded as FAIL, never converted into pseudo-exact
measurements.

## Replacement requirements

1. Build a new non-overwriting R2 evidence directory from the frozen official
   R94 PDF, physical page 625 / printed page 612, at native 300 dpi; 1:1 is the
   sole measurement grid and 8× nearest-neighbour is visual-only.
2. Revalidate all 342 candidate glyphs, especially all 110 SVG `<use>` glyphs
   and formula characters, using glyph-only masks derived from a traceable PDF
   glyph/path isolation method.
3. Produce 100% contact sheets containing the original context, a uniquely
   coloured target-mask overlay and mask-only view. Manually inspect every
   cell at 8× and retain the review ledger.
4. Machine-check that every target glyph mask contains no texture, background,
   neighbouring glyph, line, arrow, marker or border pixels; contamination,
   empty masks, mismatches and unknowns are evidence FAIL.
5. Recompute all H/D/E, unordered pairs, required relations, clipping and
   clearance results from the corrected active masks. CSV, JSON, Markdown and
   final result must agree exactly, with a unique active evidence lifecycle.
6. Apply the current `STRICT_FIGURE_EVIDENCE_SCHEMA.md` and
   `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`, including source `>=9.5pt` (natural
   TeX script exception only), glyph pixel thresholds, classified clearances
   and `FONT_VISUAL_HARMONY_PASS`.

## Findings retained only for independent revalidation

Root inspected the existing 1:1/8× packages for `TG304`, `TG317` and `TG457`.
They visually support candidate clearances of respectively 1px, 1px and 2px,
all below their applicable hard thresholds. The corrected R2 audit must retain
and independently remeasure these relations; their existence does not make the
rest of the invalid mapping evidence acceptable and does not permit early stop.

Until corrected R2 evidence passes root integrity review, FIG-P577-01 must not
be registered as a valid SA1 result or sent to SA2/SA3 on the strength of the
current terminal files.
