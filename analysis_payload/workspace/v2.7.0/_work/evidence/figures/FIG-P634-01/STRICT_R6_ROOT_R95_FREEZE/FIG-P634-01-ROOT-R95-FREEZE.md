# FIG-P634-01 official R95 freeze

- Root built `strict_current_r95_fullbook/main_full.pdf` through the authoritative entry point with `-NoPublish`; the process exited 0 and `latexmk` reported all targets up to date.
- Independent PDF parsing found 813 pages, one media/crop geometry `595.276 × 841.89 pt`, rotation 0, PDF 1.7, no encryption, and 4,934,184 bytes. All 14 `pdffonts` rows are embedded, subset, and Unicode-enabled.
- The final log has zero matches in all 19 hard categories recorded in `R95_BUILD_AND_PAGE_FREEZE.json`, including TeX/LaTeX/package/fatal errors, undefined controls/references/citations, multiply-defined or duplicate destinations, overfull/underfull boxes, missing characters, and rerun requests.
- `FIG-P634-01` independently resolves to physical page 682, printed page 669, figure 33.3. Root rendered that official page directly at 300 dpi (`2481 × 3508`) and viewed the full page plus native color and grayscale figure/caption crops.
- No visible overlap, clipping, anomalous line break, or abrupt font hierarchy was found in this root precheck. This is only `PRECHECK_PASS_TO_FRESH_SA1_NOT_FINAL`; it does not count toward the strict 4/99 total and cannot replace a new independent SA1, isolated SA3, and root acceptance.
