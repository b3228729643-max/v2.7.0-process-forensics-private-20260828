# FIG-P172-01 — root continuity note for official R91

- The independent SA1 audit used the official R90 physical page 187 at native 300 dpi.
- The current R91 physical page 187 was independently rasterized at the same 300 dpi and stored as `official_r91_page_p187_300dpi-187.png`.
- The R90 and R91 native PNG byte sequences are identical (both 781,021 bytes). No resizing, resampling, or hash-based inference was used.
- Therefore the R1 finding remains current for R91: `RESULT: FAIL`. This note does not convert the audit into a PASS and does not waive any source-font, pixel-ratio, or clearance failure.

Root continuity decision: retain `SA1_FAIL_FONT_PIXEL_RATIO_CLEARANCE`; next role is the figure-specific SA2.
