# FIG-P654-01 SA1 overlap and ownership adjudication

- Objects: 103 glyphs + 21 graphic paths = N124; all 7,626 unordered pairs are present.
- Path ownership: each PDF seqno was replayed alone, official foreground was selected without bbox/component ownership guessing, and later z-order was subtracted. Coverage residual=0, coverage excess=0.
- Graphic masks: all 21 opened at native 1x and 8x; each has foreign=0 and missing=0. P003 no longer contains the old detached left/right arrow fragments.
- Final illegal overlap count: `OVERLAP_PIXEL_COUNT=0`.
- Intentional raw contacts: 19 exact pair-specific source edge connections; every native 1x/8x card was opened and z-order checked. No class-wide exemption was used.
- Text bbox clearance: FAIL. 17 title/formula glyph pairs are below 4px; all corresponding A/B/intersection/native-1x/8x cards were opened.
- Clip count: `CLIP_PIXEL_COUNT=0`; minimum text bbox to analysis image edge is 17px (gate 6px).
- Decision: **FAIL_TO_SA2**.
