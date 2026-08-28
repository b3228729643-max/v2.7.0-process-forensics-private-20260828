# FIG-P602-01 — R5 independent SA1 terminal report

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

Frozen official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf`  
PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`  
Frozen figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex`  
Source SHA-256: `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`  
Identity: physical page 651 / printed page 638 / Figure 32.5.

| Gate | Result | Evidence |
|---|---|---|
| Frozen PDF/source identity | PASS | `evidence_manifest.json`, `reports/MACHINE_CROSSCHECK.md` |
| Source >=9.5 pt proof | PASS | `after_font_audit.csv`, `reports/D_E_COORDINATION_REVIEW.md` |
| 175-glyph native 1x+8x review and pixel floors | FAIL | `glyph_reviewer_ledger.csv`, `after_pixel_measurements.csv`, `reports/GLYPH_REVIEW_SUMMARY.md` |
| Low-profile same-codepoint calibration | PASS | `calibration/low_profile_calibration.csv` |
| 35 objects / 595 unordered pairs / intent whitelist | PASS | `after_overlap_report.csv`, `intentional_contact_ledger.csv` |
| Opaque-background inverse/source-order review | PASS | `occlusion_inversion.csv`, `occlusion/occlusion_reverse_render_manifest.json` |
| D/E coordination | PASS, no waiver of C | `reports/D_E_COORDINATION_REVIEW.md` |
| Mathematical/semantic review | PASS | `reports/MATH_AND_SEMANTICS_REVIEW.md` |
| Full page/crop/grayscale visual integrity | PASS | `reports/PAGE_VISUAL_INTEGRITY_REVIEW.md` |
| Calibration cleanup process exception | RECORDED, separate | `reports/CLEANUP_EXCEPTION.md` |

## Terminal decision

**FAIL_TO_SA2**

The decision is required by the final-PDF glyph gate: 10 mandatory raw-ink floor failures and 15 raw mask-purity failures, with 23 unique failed glyphs.  No business source, central state, build entry, or other evidence directory was changed by this R5 SA1 review.  The cleanup exception is fully disclosed and is not used to suppress or create the figure verdict.
