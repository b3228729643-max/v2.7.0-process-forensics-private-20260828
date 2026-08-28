# R116 fresh isolated SA1 manual verdict

- Canonical UID: `FIG-P126-01`
- Handoff: `A-R116-P126-SA1-FRESH-ISOLATED-20260828`
- Current PDF physical page: `137`
- Verdict: **FAIL**

The figure's mathematics, coordinate-descent semantics, step order, legend mapping, codepoints, caption, grayscale distinction, page integration, and clipping state are correct. The failure is independent of the advisory legacy numeric font/pixel/ratio thresholds.

Two hard visible-ink collisions are present in the current R116 300 dpi native rendering:

1. `PAIR-0085` / `O003-O015`: the outer gray contour crosses and visually merges with the top of the superscript `(0)` in `x^(0)`. This is visible in both the native 1× crop and the unresized nearest-neighbor 8× crop for `ROI-10`.
2. `PAIR-0189` / `O006-O020`: the inner gray contour crosses and visually merges with the lower ink of step label `5`. This is visible in both the native 1× crop and the unresized nearest-neighbor 8× crop for `ROI-13`.

The star covering the two axes at the origin, arrow-to-marker contacts, and trajectory/contour crossings are intended semantic geometry, not illegal text collisions. Digit `7` remains separated from the horizontal axis in `ROI-11`, and digit `6` remains separated from the nearby contour in `ROI-12`.

Because a single true illegal reader-visible text/curve collision is hard-failing, these two confirmed collisions require an honest SA1 `FAIL` route back to Main/SA2. This SA1 does not modify TeX or self-count any local/global/final acceptance.
