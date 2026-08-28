# FIG-P157-01 ROOT OFFICIAL R93 BUILD

RESULT: **OFFICIAL CANDIDATE BUILD PASS — READY FOR FRESH SA1**

## Candidate identity

- PDF: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r93_fullbook/main_full.pdf`
- Size: 4,933,710 bytes
- Pages: 813
- Page size: 595.276 × 841.89 pt (A4)
- PDF version: 1.7
- FIG-P157-01: physical page 170, printed page 157

## Build and hard-log result

- The normal non-resume invocation completed LuaLaTeX generation of the 813-page staged PDF but the outer PowerShell process observed an anomalous child exit `-1` before its publish-copy phase. The child transcript subsequently ended with `Output written on main_full.pdf (813 pages, 4933710 bytes)` and `Latexmk: All targets ... are up-to-date`.
- The documented `-Resume` mode was then run through the same `build.ps1` entry. It verified the existing staging target as up to date, completed the official-copy step, and returned structured `result: PASS` with exit code 0. No source or build script was modified.
- Final official `main_full.log` hard scan: 0 hits for fatal/package errors, undefined control sequences/references, multiply-defined references, rerun requests, overfull/underfull boxes, or lost floats.

## Root visual integration check

- Direct Poppler renders: official page 170 at native 300 dpi and 200 dpi.
- Root opened the full page, the native 300 dpi figure crop, and `official_r93_T04_xaxis_raw_1to1_300dpi.png`.
- `选择复杂度` is visibly separated from the x-axis, aligned with the vertical reference, and does not crowd `合适`, the x-axis title, caption, or page content. The validation annotation remains clear of both curves.

This report authorizes only a fresh independent SA1 on the official R93 candidate. It does not grant final figure PASS.
