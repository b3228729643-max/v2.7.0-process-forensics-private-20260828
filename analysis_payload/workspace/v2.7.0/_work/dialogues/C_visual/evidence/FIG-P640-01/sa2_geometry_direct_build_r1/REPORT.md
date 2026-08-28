# FIG-P640-01 SA2 geometry direct build R1

HANDOFF_ID: `C-FIG-P640-01-SA2-GEOMETRY-DIRECT-BUILD-R1`

Result: **FAIL_TO_SA2**. No local pass is claimed.

## Candidate identity

- Source: 2,717 bytes; SHA-256 `FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`.
- Wrapper: 402 bytes; SHA-256 `495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C`.
- Source change from the accepted static baseline is only the right-panel `ymin=0` to `ymin=-.04` line. The true point `(.99,0.0100499975)`, displayed `(.99,.010)` label, functions, curves, nodes, mathematics, caption and all other layout remain unchanged.
- Direct LuaLaTeX invocation: PID 24496; invocation count 1; retry count 0; natural exit 0; post-process count 0. The build slot was released immediately after the natural exit.
- PDF: one A4 page; 40,373 bytes; SHA-256 `0ECC4B13E75A981AD23E7EBCA1CB2BAEBEF83D85EEE3A4518395C54AC296B87A`.

## Fresh non-TeX denominators

- Objects: 40 unique objects: 30 text objects followed by 10 vector objects.
- Glyphs: 160 including spaces; 145 nonspace glyphs.
- Unordered pairs: all `C(40,2)=780` pairs exactly once.
- Critical pairs: 76 candidates selected by bounding-box intersection or gap at most 8 pt; all received per-ID manual review.
- Clip ledger: all 40 objects; minimum page-edge distance 71.781509 pt.
- Views: full page; native and grayscale figure crops; right panel; PAIR_0779 native and overlay at 1x and 8x; all object and critical-pair contact sheets.

Machine scripts generated only geometry inventories, masks, crops and contact sheets. They did not generate or overwrite any manual reviewer, decision, Boolean or note field. The manual ledgers were authored after viewing the rendered evidence.

## Decisive regression

The patch successfully moved the horizontal x-axis below the open endpoint marker. It did not move the `.99` vertical x tick. In the new PDF:

- `.99` tick: x = 501.820190 pt; y = 182.267090 to 186.518951 pt.
- Open marker rectangle: x = 500.029419 to 503.616028 pt; y = 179.027756 to 182.614349 pt.
- `PAIR_0779 = G08/G10` bounding boxes overlap by 1.790771 pt × 3.586593 pt.
- Independently reconstructed 300 dpi axis and marker masks share 6 rendered pixels, with inclusive overlap box x=2090..2091 and y=759..761.
- The native 8x view and blue/amber/magenta overlay show the vertical tick penetrating the lower marker ring.

This is a genuine geometric collision, not a font-metadata, 1–2 px advisory, or taxonomy issue. It remains hard under R168. The only legal result is return to SA2; this evidence does not authorize another TeX invocation, a source commit, a fresh role, or a central state/inventory update.

## Other gates

All other reviewed relationships are legal: tick labels remain outside axes; legend samples precede their labels; left curves share the theoretical origin and diverge; the right curve intentionally terminates at the true-point marker; point and limit annotations remain readable; no object clips; color and grayscale views preserve distinction. R168 glyph review found no tofu, wrong codepoint, wrong mathematics, unreadability, severe size imbalance, real clipping or illegal text overlap.

The standalone A4 page is intact. No full-book rebuild or official candidate-page replacement was authorized in this round, and no such identity is claimed.
