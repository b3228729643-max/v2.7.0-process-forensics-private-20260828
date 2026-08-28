# FIG-P654-01 SA2 overlap, clearance and ownership adjudication

- Foreground denominator: 95 glyphs + 21 PDF seqno graphic/path objects = N=116; the rawdict-external fraction rule is P006 and is counted separately.
- Complete unordered-pair ledger: `C(116,2)=6,670`; all endpoints resolve and every row has an object-specific manual decision.
- Ownership closure: unassigned text=0, coverage residual=0, coverage excess=0, empty glyph masks=0, empty graphic masks=0; every object has foreign=0/missing=0 after native-1x/nearest-8x inspection.
- Pair-specific contact policy: 19 exact source-semantic definitions only; 17 actual-contact pairs were opened at native 1x and 8x with A/B/intersection and z-order checks. No class-wide exemption is used.
- Illegal exclusive-mask overlap: `OVERLAP_PIXEL_COUNT=0`; machine/pair failures=0.
- Independent parent text bbox audit: 55 pairs, minimum clearance 7.0px against 4px; failures=0.
- Final crop foreground margins L/T/R/B=10/10/37/11px; text edge minimum=30px; `CLIP_PIXEL_COUNT=0`.

The page PDF itself was complete throughout. The rejected trial was only an evidence crop `(326,435,2237,1025)` with foreground margins `0/3/29/4px`; it is preserved under `trials/crop_clipped_r3` and excluded. The final crop `(310,428,2245,1032)` rebuilt all N=116 objects and all 6,670 pairs.

Decision: **LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1**.
