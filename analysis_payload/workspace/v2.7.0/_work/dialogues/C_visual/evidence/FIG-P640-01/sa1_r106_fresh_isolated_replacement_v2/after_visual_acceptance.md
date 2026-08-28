# FIG-P640-01 R106 SA1 visual acceptance

HANDOFF_ID: C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-REPLACEMENT-V2  
SA1_MODEL: gpt-5.6-sol  
SA1_REASONING: xhigh  
FORK_TURNS: none  
SA1_REVIEW_OUTCOME: CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE  
LOCAL_PASS_COUNTED: false  
GLOBAL_PASS_COUNTED: false  
SA3_AUTHORIZED: false  
SA2_MODEL: NOT_USED_CURRENT_ROUND  
SA2_REASONING: NOT_USED_CURRENT_ROUND  
SA2_ESCALATED: false  
SA3_MODEL: NOT_RUN  
SA3_REASONING: NOT_RUN  

OFFICIAL_PDF_PAGE_PHYSICAL: 690  
OFFICIAL_PDF_PAGE_PRINTED: 677  
OFFICIAL_PDF_PAGE_COUNT: 817  
OFFICIAL_PDF_BYTES: 4967249  
OFFICIAL_PDF_SHA256: 0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A  
NATIVE_300DPI_GRID_PX: 2481x3508  
FIGURE_CROP_300DPI_PX: 1826x955  
STANDALONE_300DPI_PX: 1826x805  

SOURCE_FONT_PASS: true  
PIXEL_HEIGHT_PASS: true  
SAME_CLASS_RATIO_PASS: true  
ROLE_RATIO_PASS: true  
FONT_VISUAL_HARMONY_PASS: true  
OVERLAP_CANDIDATE_PIXEL_COUNT: 0  
MASK_CONTAMINATION_PIXEL_COUNT: 0  
OVERLAP_PIXEL_COUNT: 0  
PIXEL_ADJUDICATION_STATUS: CLEAR  
PIXEL_ARBITER_MODEL: NOT_USED  
PIXEL_ARBITER_REASONING: NOT_USED  
CLIP_PIXEL_COUNT: 0  
MIN_TEXT_CLEARANCE_PX: 6  
MIN_INDEPENDENT_TEXT_TEXT_CLEARANCE_PX: 15  
MIN_TEXT_GRAPHIC_CLEARANCE_PX: 8  
VISUAL_HARMONY_PASS: true  
MATH_SEMANTICS_PASS: true  
TEXT_CONSISTENCY_PASS: true  
GRAYSCALE_PASS: true  
PAGE_INTEGRATION_PASS: true  

## Independent location and scope

The target was located independently from the current figure source, adjacent chapter, and official PDF. Its unique full-book occurrence is physical PDF page 690, printed page 677. The stale Goal page card was not used as evidence. No prior P640 or P639 evidence, conclusion, handoff, state, inventory, chat, delegation record, or Git history was consulted.

## Machine and manual closure

- Semantic objects: 45 = 32 text + 13 graphic.
- Exhaustive pair ledger: C(45,2) = 990 expected, 990 actual, 990 unique, no unknown object ID.
- Visible non-space glyphs: 242 = 145 figure-body + 97 caption; every glyph has a raw mask, native 1× ROI, 8× nearest ROI, contact-sheet cell, and a unique manual row.
- Foreground drawing primitives: 20, all assigned to semantic graphic objects; one fraction rule is explicitly inventoried as `GRAPHIC/MATH_RULE`.
- Foreground object masks: 43 nonempty; two additional source-proven opaque-background objects are intentionally not foreground masks.
- Critical relations: 37/37 manually reviewed; 19/19 have targeted native 1×/8× ROIs; raw final-visible mask intersections = 0.
- Manual ledgers: glyph 242/242, object 45/45, critical relation 37/37, font element 32/32, peer/role 10/10, view 6/6, hard gate 15/15. All 387 rows are PASS with reviewer and per-ID note present.

## R168 typography ruling

All ordinary source-level text is at least 9.6 pt; axis labels are 9.8 pt and the PDF caption is approximately 9.96 pt. There is no hidden graphics scaling. No glyph is missing, tofu, wrong-codepoint, semantically wrong, unreadable, severely imbalanced, clipped, or illegally overlapped. The 28 rows below legacy pixel micro-thresholds are recorded as advisory only under R168; punctuation/natural-script raster differences and `[0.92,1.08]` micro ratios do not create a hard failure absent a real readability, glyph, clipping, imbalance, or overlap defect.

## Visual and semantic review

The full page, figure crop, standalone figure, both panel crops, and grayscale view were opened. Typography is restrained and harmonious with the page body; no role is conspicuously oversized or cramped. Solid, dashed, and dash-dot lines provide usable non-color redundancy. The long caption remains readable and page-integrated.

Panel A correctly represents the round-end `X_2` chain ACF as `rho^(2k)` and plots squared-correlation rates 0.9025, 0.49, and 0.04. Panel B correctly uses `(1-rho^2)/(1+rho^2)` and places `rho=.99` near 0.01005. The one-sided limit `|rho| -> 1^-` preserves the legal stationary boundary and matches the adjacent chapter.

## Routing conclusion

This SA1 evidence supports a candidate pass, not an accepted local or global pass. The main thread must first accept this sealed handoff; only then may it authorize a different fresh isolated SA3. This SA1 did not start SA3 and did not write central state or inventory.
