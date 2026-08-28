# FIG-P602-01 — root strict requalification decision

- Authority: current Goal SHA-256 `51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`
- Official candidate: R96, physical page 651 / printed page 638 / Figure 32.5
- Official PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`
- Figure source SHA-256: `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`
- SA1 evidence accepted for routing: `STRICT_R5_REQUAL_R96_SA1_CONT_20260824`

## Root evidence-integrity review

- The sealed directory contains 843 files, including 711 PNG files; no alternate data streams were found.
- `TERMINAL_STATUS.md`, the final report, manifest and machine cross-check precede `WRITE_STOPPED`; no later write was found.
- The only two zero-byte files are TeX-generated `low_profile_calibration.idx` and `symbols.idx` intermediates. They are not required masks or review images and do not invalidate the evidence package.
- The authority paths, page identity, official PDF hash and current figure-source hash agree with R96.
- Root opened all 20 glyph contact sheets, the native 1x target views and masks for every one of the 23 failed glyphs, all three 8x-nearest intentional-contact review sheets, and all six occlusion/reverse-render ROIs.
- Root cross-checked the 175-glyph ledger, 35-object / 595-unordered-pair partition, 12 intentional contacts, six opaque-background checks, low-profile calibration, and the page/crop/standalone/grayscale reviews against the terminal summary.

Evidence integrity is **PASS**. The disclosed calibration-cleanup exception did not alter the frozen source or official PDF and is not used to waive a figure gate.

## Decisive hard failures

The R96 final-visible pixels fail mandatory native-300-dpi floors:

- `GLYPH-007`, `021`, `044`, `104`, `118`: `=` has raw ink height 12–14 px, below 22 px.
- `GLYPH-014`: `⋅` has raw ink height 5 px, below 22 px.
- `GLYPH-051`, `062`: `˜` has raw ink height 6 px, below 22 px.
- `GLYPH-077`: `∼` has raw ink height 9 px, below 22 px.
- `GLYPH-160`: CJK `一` has raw ink height 5 px, below 30 px.

The glyph-isolation gate also reports 15 mask-purity failures, yielding 23 unique failed glyphs after overlap with the height failures. Root inspection confirms examples including neighbouring formula ink entering the target isolation and the rule beneath `提/议` entering their masks. Passing geometry, occlusion, mathematical meaning and four-view layout cannot cancel these glyph hard failures.

## Root decision

**FAIL_TO_SA2**

This is a routing acceptance only. FIG-P602-01 remains 0-credit under the current Goal and must not be counted as a final figure. It enters the single-writer SA2 queue; after repair it requires a new official build, a fresh independent SA1, an isolated SA3 and a new root acceptance on the same candidate.
