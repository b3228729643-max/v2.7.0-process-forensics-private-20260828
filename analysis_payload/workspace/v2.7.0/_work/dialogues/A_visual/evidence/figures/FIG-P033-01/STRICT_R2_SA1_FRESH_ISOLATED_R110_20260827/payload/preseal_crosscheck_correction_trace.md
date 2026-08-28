# Pre-seal crosscheck correction trace

The first final-crosscheck invocation exited 1 because of three assertions in the newly written crosscheck itself. It did not rerun the selector scan, change any final object mask, change any relation measurement, or change any manual ledger.

1. The crosscheck incorrectly treated `foreign_pixel_px_removed_by_vector_selector` as residual foreign pixels. That field records pixels successfully removed during exact selector assignment; final residual foreign/unassigned objects remain 0.
2. The crosscheck searched only the top level of `payload/masks`, while the 99 final masks are organized under `masks/glyph` and `masks/drawing` together with retained pre-selector and pre-occlusion artifacts.
3. The crosscheck hard-coded ten PNGs per critical-relation directory. The actual closed format is six per relation (`raw_1x`, `mask_A_1x`, `mask_B_1x`, `intersection_1x`, `overlay_1x`, `overlay_8x_nearest`), with the corresponding final contact sheet providing the combined 8x raw/mask/intersection/overlay panels.

The assertions were corrected to the actual frozen schema and dynamic denominator. The corrected rerun is the sole seal crosscheck. Final candidate identity remains N=99, C=4,851, machine hard=1 (`R2886`), critical=10; manual counts and the R2886 FAIL decision are unchanged.
