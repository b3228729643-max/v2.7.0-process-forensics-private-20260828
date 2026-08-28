# FIG-P309-01 ROOT VALIDATION — STRICT R1

RESULT: **SA1 FAIL CONFIRMED**

- Frozen candidate: official R92, physical page 334 (printed page 321).
- Root opened the native 300 dpi figure crop, full measurement overlay, and the raw 1:1 ROIs for `H_-`, `2/||w||`, and `w` versus its nearby marker/arrow.
- Geometry is accepted for this SA1 candidate: illegal overlap=0, clipping=0, minimum text–graphic foreground clearance=8.8489 px, and minimum text–text clearance=28 px. Math, caption/body consistency, reading order, grayscale encoding and page integration pass.
- Mandatory typography remains a hard failure: seven visible tokens are 9.2 pt below the 9.5 pt floor; the natural subscript minus in `H_-` is visibly tiny and measures 3 px versus the 15 px floor; same-class ratios 0.9167, 1.7273 and 0.2727 are outside [0.92,1.08].

Disposition: keep FIG-P309-01 open for a unique SA2 repair; do not launch SA3. Preserve the current zero-overlap geometry while raising the local fonts and replacing/reworking the tiny `H_+`/`H_-` script encoding and margin formula so all pixel and ratio gates pass without visually oversized labels.
