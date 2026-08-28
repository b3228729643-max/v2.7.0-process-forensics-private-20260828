# R5 SA1 machine cross-check

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

## Structural assertions

- [PASS] official PDF SHA-256 matches frozen R96
- [PASS] figure source SHA-256 matches frozen source
- [PASS] 175 unique glyph-map rows
- [PASS] 175 unique completed ledger rows
- [PASS] 175 unique after-pixel rows
- [PASS] no pending manual glyph review
- [PASS] 175 raw glyph masks
- [PASS] 175 native original 1x glyph views
- [PASS] 175 native target-overlay 1x glyph views
- [PASS] 20 8x-nearest O/T/M contact sheets
- [PASS] 175-row source-font audit passes
- [PASS] 23 glyph ledger failures retained
- [PASS] 10 mandatory raw pixel-floor failures retained
- [PASS] 15 raw mask-purity failures retained
- [PASS] 35 primary foreground objects
- [PASS] all 595 unordered TT/TG/GG pairs
- [PASS] pair status partition 578/12/5
- [PASS] no nonwhitelisted final foreground overlap
- [PASS] 12 intentional-contact ledger rows
- [PASS] 12 native 8x intentional-contact details
- [PASS] six opaque-background source-order checks pass
- [PASS] six independent low-profile calibrations pass
- [PASS] direct native 300 dpi page dimensions 2481x3508
- [PASS] official crop and grayscale dimensions match
- [PASS] required report exists: reports/GLYPH_REVIEW_SUMMARY.md
- [PASS] required report exists: reports/OVERLAP_AND_OCCLUSION_REVIEW.md
- [PASS] required report exists: reports/D_E_COORDINATION_REVIEW.md
- [PASS] required report exists: reports/MATH_AND_SEMANTICS_REVIEW.md
- [PASS] required report exists: reports/PAGE_VISUAL_INTEGRITY_REVIEW.md
- [PASS] required report exists: reports/CLEANUP_EXCEPTION.md

All structural/integrity assertions passed.  The separate acceptance result is `FAIL_TO_SA2` because the completed glyph ledger contains 23 failures; that is a substantive gate result, not a missing-evidence condition.
