# SA2 R168 human adjudication

## Scope and identity

This is a fresh, isolated, read-only SA2 adjudication of `FIG-P033-01` in the fixed R110 official PDF. The current caption independently identifies physical PDF page 29, printed page 16, Figure 2.1. Candidate and source byte counts and SHA-256 values match the fixed task identities exactly.

## Actual human observations

The full page, native 300 dpi crop, native 300 dpi standalone-with-caption, direct grayscale render, four native 1:1 relationship ROIs, and their 8× nearest-neighbour inspection aids were actually opened. The following visible content was individually checked:

- mathematical text: `x`; `p=P_Sx∈S`; `r=x-p∈S^⊥`; `||x||²=||p||²+||r||²`;
- Chinese text: `子空间 S`, `最短距离`, `图 2.1`, and the complete caption;
- geometry: common origin, solid x vector, solid projection vector, dashed residual vector P→X, arrowheads, subspace band and both edges, projection foot, right-angle marker, distance brace, and equation note box.

No missing glyph, tofu, miscoding, broken mathematical mark, actual unreadability, obvious visual imbalance, real clipping, illegal semantic overlap, or wrong geometry/relation was observed. Contacts at O, P, and X are required by the decomposition; the right-angle marker shares P by design; the two arrows ending at X express `x=p+r`. The white label backings around the residual and shortest-distance annotations preserve readability and do not hide required semantics.

The grayscale view remains legible: line styles and geometry preserve the distinctions even when hue is removed. The figure is balanced on the printed page, its caption is intact, and the transition to the subsequent projection identity and example is visually natural.

## Current V1-C02 semantic check

The current chapter theorem states `x=p+r`, `p∈S`, and `r∈S^⊥`, proves best approximation by the orthogonal Pythagorean decomposition, and the post-figure sentence identifies `p=P_Sx` as the unique minimizer. The figure depicts exactly these relations. The caption and alt text agree with both the theorem and the rendered geometry.

## Advisory only under R168

The source uses 9.4pt globally and 9.2pt for the residual, distance, and norm-identity nodes. These declarations are below the legacy 9.5pt strict-goal threshold, but the R168 instruction explicitly makes micro-raster/font-outline/1–2px-level differences advisory and reserves hard failure for real defects. In the actual R110 render, every affected label and symbol is plainly readable and visually harmonious. This item is therefore recorded as advisory, not promoted to a hard FAIL and not used to request a source change.

## Verdict

- R168 hard FAIL count: `0`
- source changes: `0`
- TeX/build commands: `0`
- route: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
- limitation: this SA2 package does not itself launch or replace fresh SA1/SA3.
