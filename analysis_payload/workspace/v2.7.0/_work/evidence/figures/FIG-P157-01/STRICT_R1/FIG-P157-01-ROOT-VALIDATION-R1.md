# FIG-P157-01 — root validation of independent SA1 R1

Root reviewed the native, unresampled `roi_05_validation_label_curve_conflict_100pct.png` and the full 300 dpi figure crop.

- The dashed validation curve visibly crosses the ink of `验证误差：先降后升`; this is a real semantic-object collision, not a pale antialiasing edge.
- The independent mask count of 134 illegal overlap pixels and 0 px clearance is therefore accepted as a hard FAIL.
- Direct source/context review also confirms that the adjacent sentence promises solid-circle and dashed-triangle encodings, while the source draws neither series marker; only the gold minimum point exists.

Root decision: retain `SA1_FAIL_OVERLAP_TEXT_SEMANTICS`; next role is the figure-specific SA2. The repair must move the label to an empty region and make the prose match the actual solid/dashed/gold-point encoding, then rebuild the official PDF and repeat all strict measurements.
