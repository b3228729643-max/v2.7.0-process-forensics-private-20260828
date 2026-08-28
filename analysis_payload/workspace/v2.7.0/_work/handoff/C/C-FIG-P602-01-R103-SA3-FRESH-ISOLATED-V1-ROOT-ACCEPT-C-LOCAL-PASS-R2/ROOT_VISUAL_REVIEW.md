# Root visual acceptance

- Result: PASS under R168; hard failure IDs: NONE.
- Full-page 300 dpi: printed page 640 and Figure 32.5 integrate cleanly with surrounding equations, prose, caption, reading-order paragraph, and footer.
- Figure crop and standalone views: proposal, ratio, decision, accept branch, reject branch, double reject border, and rejection self-loop are complete and correctly directed.
- Formula semantics: reverse flow appears in the numerator, forward flow in the denominator, U <= alpha is correct, acceptance sets X_{t+1}=Y, rejection keeps X_{t+1}=X_t.
- Grayscale: relationship styles and hierarchy remain readable.
- 717 PNG files parse successfully.
- P0467/P0478/P0488 are only 1/1/2 px raster endpoint gaps and remain visually continuous under R168.
- All non-zero intersections inspected are intended arrow-node endpoints; illegal overlap and true clipping are zero.
