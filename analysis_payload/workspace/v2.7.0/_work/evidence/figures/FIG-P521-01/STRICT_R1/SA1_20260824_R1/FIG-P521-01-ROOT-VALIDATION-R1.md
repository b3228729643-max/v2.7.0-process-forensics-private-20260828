# FIG-P521-01 ROOT VALIDATION R1

## Root verdict

- `RESULT: FAIL`
- `NEXT_ROLE: SA2`
- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 567, printed page 554, figure 29.1.
- Root independently reopened the native color/grayscale crop, text overlay, `phi`/outer-plate ROI, source, and adjacent PLSA text.

## Confirmed hard failures

1. Source-size gate fails for 12/13 semantic objects: primary TikZ text is 9.4 pt and plate/legend text is 8.8 pt, below the 9.5 pt floor.
2. Fifteen of 103 independently measured glyph/operator/punctuation substrings fail native 300 dpi height thresholds. Twenty-six of 103 same-class rows also fall outside `[0.92,1.08]` (observed range `0.3288–1.6744`). Parent formula height was not used for the short operators.
3. Plate/legend versus node-label source ratio is `8.8/9.4=0.9362`, below the `[0.95,1.10]` role interval. The small plate/legend layer is visibly weak in the whole-page view, so `FONT_VISUAL_HARMONY_PASS=false`; further shrinking is not permissible.
4. `phi_z=P(w|z)` is visibly and structurally inside the outer `d=1:D` plate. It is a global topic--word distribution and must not be replicated per document. This is a semantic plate-membership failure, not a pixel-overlap claim.
5. The inner plate uses `n=1:N_d`, while the directly adjacent source defines document `d_j` with length/repetition count `L_j`. The figure and text therefore use inconsistent indexing/length notation.

## Passing/nonblocking findings

- `d -> z -> w`, `w independent of d given z`, and the observed/latent node classes are otherwise coherent.
- All 286 nonexempt independent pairs have zero raw foreground overlap; clip count is 0. Minimum text--text bbox clearance is 19 px and text--graphic raw clearance is 9 px. Four intentional line--node connections are correctly exempted.
- Grayscale redundancy and page integration pass.

The current candidate must not proceed to SA3. SA2 must move the global `phi_z` parameter outside the document plate, unify the document/token indices and length symbol with the adjacent text, repair every source/glyph/role-size failure without whole-figure scaling, and then produce a new frozen candidate for fresh independent SA1.
