# Manual native-pixel overlap and clipping adjudication

The final denominator contains 25 objects and the manual pair ledger contains all 300 unordered pairs exactly once. Every pair was reviewed after opening the native full-page, native figure crop, grayscale variants, two overlays, and all five native1x/nearest8x ROI pairs.

- Candidate pixels in prohibited foreground pair classes: `0`.
- Mask-contamination pixels: `0`.
- Canonical true illegal overlap pixels: `0`.
- Effective clipped pixels: `0`.
- Minimum independent text-to-graphic clearance: approximately `7 px`, between `T10` and `G08`, measured from the final-PDF vector bounds and confirmed in the native/nearest8x brace ROI.
- Pixel adjudication status: `CLEAR`.

Intentional non-errors are exhaustively identified in `09_manual_pair_ledger.csv`: axes share the origin, densities cross each other, the center reference crosses both peaks, fills meet their own curves and the zero baseline, and the opacity grounds B01/B02/B03 occlude underlying data/axis ink to keep direct labels clear. None produces illegal visible-ink contact, clipping, obstruction, or ambiguity.
