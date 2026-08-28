# Overlap and clipping adjudication

## Pixel-mask basis

The mask census uses a direct 300 dpi RGB raster of the official R103 PDF without post-render resize, plus PDF-vector-bounded object masks. All 32 masks were reviewed through four foreground-mask contact sheets, and the semantic-object overlay was opened against the untouched direct render.

## Result

- `RAW_SHARED_FOREGROUND_PIXEL_COUNT=115`
- `RAW_ALLOWED_CONTACT_PIXEL_COUNT=115`
- `OVERLAP_CANDIDATE_PIXEL_COUNT=0`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `PIXEL_ADJUDICATION_STATUS=CLEAR`

The complete 496-pair intersection table contains only two nonzero pairs:

- `PAIR-457 B04/E04`: 58 pixels, all at the expected left accept-branch topological endpoint.
- `PAIR-458 B04/E05`: 57 pixels, all at the expected right reject-branch topological endpoint.

The raw shared-pixel view shows exactly these two tiny endpoint clusters. After permitted endpoint subtraction, the potentially-illegal candidate image is completely black. No text/background leakage remained in any object mask.

## Critical intersections and clip gate

All 24 critical cards were opened at direct 1x and nearest-neighbor 8x. `C14` and `C16` are the two allowed branch contacts above; the other 22 are clear. In particular, edge labels have genuine white-background clearance from the corresponding line, the fraction rule does not touch numerator or denominator glyphs, and the self-loop does not cross its label or the rejected-state text.

All 32 objects fall inside the final direct-PDF crop `(62,345)–(522,719) pt`. Outer minimum margins are 63.29 px left (`B05`), 17.54 px top (`B01`), 63.71 px right (`E06`), and 25.92 px bottom (`T19`). `CLIP_PIXEL_COUNT=0`. The tightest reviewed internal text-to-node clearance is about 9 px at the accepted-result second line, still positive and visibly readable.
