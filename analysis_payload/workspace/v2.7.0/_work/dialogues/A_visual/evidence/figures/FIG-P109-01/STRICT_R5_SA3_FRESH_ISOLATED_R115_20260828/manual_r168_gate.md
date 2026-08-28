# R168 manual hard-gate ledger

Reviewer identity: `A-R115-P109-SA3-FRESH-ISOLATED-20260828`  
Canonical UID: `FIG-P109-01`  
Candidate: official R115, physical page 116  
Observation time: `2026-08-28T06:25:00+08:00`

R168 treatment was applied exactly as assigned: legacy numerical font, pixel-height, ratio, and clearance thresholds were used only as advisory context. They were not converted into hard failures. In particular, the current figure source declares 9.2 pt for the figure labels; this is below the older 9.5 pt numeric rule but is not itself a failure under R168. The direct page view, raw 300 dpi figure, grayscale render, native-1x view, nearest-8x enlargement, page-integration view, and every critical ROI were all opened before the following manual hard-gate decisions were authored.

HARD_MISSING_GLYPH_TOFU_WRONG_CODEPOINT=PASS  
Evidence: all six frozen reader-visible objects render complete; PDF text extraction agrees with current TeX semantics, including mathematical italic x/y/z/C, lambda, membership, interval delimiters, and implication arrow.

HARD_UNREADABLE_OR_OBVIOUSLY_IMBALANCED=PASS  
Evidence: all labels, formulas, note text, and caption are immediately readable at full-page and native figure scale. No label dominates the segment/region geometry, and grayscale preserves the intended hierarchy.

HARD_TRUE_CLIP=PASS  
Evidence: no glyph, contour, line segment, endpoint, interpolation marker, note border, caption, or adjacent page text loses visible ink at its intended boundary.

HARD_ILLEGAL_VISIBLE_INK_OVERLAP=PASS  
Evidence: the six-object denominator and all 15 unordered text pairs were individually reviewed in raw 300 dpi and relevant ROI views. Text backings create clean separation from nearby graphics; no independent reader-visible semantic inks touch or merge illegally.

HARD_SEMANTIC_MATH_GEOMETRY=PASS  
Evidence: x and y lie inside C; the entire connecting segment and all interpolation markers remain in C; the displayed convex-combination formula, implication statement, caption, and adjacent prose agree.

R168_FINAL_DECISION=PASS  
This is an SA3 fresh-isolated local review conclusion only. It awaits Main's A_LOCAL acceptance and is not self-counted as A_LOCAL, global, or final completion.
