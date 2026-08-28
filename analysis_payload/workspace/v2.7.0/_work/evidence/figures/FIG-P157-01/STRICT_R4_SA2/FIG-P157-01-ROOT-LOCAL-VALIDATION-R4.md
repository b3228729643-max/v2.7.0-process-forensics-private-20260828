# FIG-P157-01 ROOT LOCAL VALIDATION — SA2 STRICT R4

RESULT: **LOCAL CANDIDATE ACCEPTED FOR OFFICIAL REBUILD**

- Authorized source delta is limited to `T04_SELECTION_KEY`: y coordinate `-.02` to `-.07`; anchor, font, text and all other objects remain unchanged.
- Root opened the native 300 dpi full figure, full-page context, `T04_selection_vs_xaxis_raw_1to1_300dpi.png`, the T04/G06 nearest-pixel ROI, and the T02 validation-label ROI.
- The repaired label has visible breathing room and remains aligned with the selection reference. Independent semantic masks measure overlap=0 and T04–G06 foreground clearance=19.0000 px (target >=8 px; hard floor >=3 px), versus the reproduced R92 baseline 1.2361 px.
- Local matrix: 12 text objects, 7 graphic objects, 162/162 relations PASS; overlap=0, clipping=0, minimum text–text clearance=14.00 px, minimum text–graphic clearance=13.04 px, and minimum figure-edge clearance=28.00 px.
- Both local build logs have zero hard-pattern hits. Source-font, native-pixel, ratio, math, text, caption, grayscale, visual-harmony and page-integration checks pass locally.

This accepts only the SA2 local candidate for integration. It is not a final figure PASS. A new official full-book PDF, fresh independent SA1, isolated SA3, and root acceptance remain mandatory.
