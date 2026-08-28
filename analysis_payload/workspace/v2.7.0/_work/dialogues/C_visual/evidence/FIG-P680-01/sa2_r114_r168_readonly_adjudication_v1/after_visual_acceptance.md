# SA2 R114/R168 read-only visual acceptance

- HANDOFF_ID = C-FIG-P680-01-R114-SA2-R168-READONLY-ADJUDICATION-V1
- UID = FIG-P680-01
- ROLE = SA2_READONLY_ADJUDICATOR
- SA2_MODEL = gpt-5.6-sol
- SA2_REASONING = xhigh
- SOURCE_WRITE_COUNT = 0
- TEX_OR_BUILD_COUNT = 0
- SECOND_UID_COUNT = 0

Current-location identity:

- physical PDF page = 729
- zero-based page index = 728
- printed page = 716
- current figure number = 35.1

R168 hard-defect matrix:

| hard-defect class | post-observation result |
|---|---|
| current missing glyph / tofu / wrong codepoint | none; U+FFFD=0, U+0000=0, mathematical theta/phi and typographic dashes are correct |
| actual unreadability or severe imbalance | none at full page, native crop, grayscale, native1x, or NN8x |
| real clip | CLIP_PIXEL_COUNT=0 |
| illegal visible-ink overlap | OVERLAP_PIXEL_COUNT=0; unresolved=0 |
| mathematical / semantic / geometric error | none; both model/inference branches and the arrow disclaimer agree with current source, caption, and chapter context |

Advisory numeric observations, not independent hard-fail grounds under R168:

- current source normal node text declares 9.4 pt; row labels 9.8 pt; warning 9.2 pt; no graphics scale is applied.
- current PDF text spans are approximately 9.364880 pt for normal nodes, 9.763390 pt for row labels, and 9.165630 pt for the warning.
- Chinese reader glyph ink is generally 34-39 px; theta/phi are 28-29 px; Latin x-height/cap glyphs are visibly complete. Small punctuation ink is not a missing semantic glyph.
- the slight source-size hierarchy produces no actual unreadability or severe imbalance in the current PDF.

Current pair/clearance facts:

- reader-visible objects = 25
- all unordered pairs = 300 / 300
- minimum text-text bbox gap = 5.530037 px
- minimum text-arrow bbox gap = 17.238004 px
- minimum text-to-own-node-border inset = 21.800504 px
- OVERLAP_CANDIDATE_PIXEL_COUNT = 0
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = CLEAR
- CLIP_PIXEL_COUNT = 0

Visual and semantic outcomes:

- full-page integration: clear; no severe whitespace or caption orphaning.
- figure/caption: complete and mutually consistent.
- grayscale: left solid and right dashed/open branches remain distinguishable.
- reading path: shared conditional structure -> model target -> matching inference method -> posterior warning.
- caption: conveys the branch distinction and states that arrows are learning dependencies, not posterior identity.

SEALED VERDICT: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

