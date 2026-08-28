# FIG-P580-01 — R5 SA1 terminal decision

**RESULT = PASS_TO_SA3**

## Frozen identity

- Authority PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r96_fullbook\main_full.pdf`
- Physical page / printed page / figure: `628 / 615 / 31.6`
- PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`
- FLS-located frozen source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_is_support.tex`
- Source SHA-256: `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`

## Strict-gate closure

- Native final-PDF 300 dpi direct page/crop evidence; 8x-nearest used only for visual inspection.
- Glyph boundary: 235/235 final-PDF glyphs, no body-text entry and no missing in-scope glyph; graphic boundary: 25/25 foreground graphic objects.
- Manual glyph evidence: 30/30 contact sheets and 235/235 Original / Target-overlay / Mask-only cells PASS; low-profile `G0199` eight exact controls PASS.
- Pair universe: all `C(260,2)=33,670` unordered pairs, including `C(25,2)=300` GG pairs, evaluated at native 1x; illegal overlap `0` px / `0` pairs, clipping `0` px, clearance failures `0`.
- Critical-relation manual ledger: 212/212 PASS (`TT=152`, `TG=1`, `GG=59`); the 60 non-TT relations were directly viewed at 8x with native relation evidence, while all TT constituents are closed in the glyph three-view ledger.
- Exact relation classification for the 48 prior raw-overlap candidates: same-parent `0`; named source-intent GG contact `48`; mask artifact `0`; true illegal `0`.  Four separate same-parent glyph ownership allocations are recorded in `reports/same_parent_mask_allocation.csv`; the U+0338/U+226A composite is separately attributed and has no residual raw overlap.
- Font/size D gate: all 235 rows PASS.  There are no final role-ratio failures.  The only low raw-ink diagnostic candidates, `G0085`--`G0088` (`支持不足`, `PANEL_TITLE`), use the source/effective role ratio `10.2/9.6=1.0625`, within required `[1.05,1.20]`; their `1.035` ink diagnostic is not the role-size decision metric.
- D/E semantic, mathematical, font-coordination, full-page, crop, standalone, and grayscale review PASS.  Source/PDF agree on the support gap for `q_L`, support coverage by `q_R`, and weights `24/25, 3/2, 24/25`.
- The 32 abandoned color-projection assertions are `ABORTED_NON_DECISIONAL`, excluded from every R5 numerator, denominator, pair classification, and conclusion.

The evidence package passed `reports/preterminal_integrity_check.json` before this decision.  This terminal conclusion authorizes SA3 review only; it is not a source modification or a build approval.
