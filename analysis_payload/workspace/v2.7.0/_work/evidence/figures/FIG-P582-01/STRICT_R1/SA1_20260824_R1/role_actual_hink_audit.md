# Actual H_INK D/E audit

This audit deliberately replaces the earlier PDF emitted-span / cross-script scale proxy. Every reported height is the median of the actual `final_visible_mask` glyph ink on the native final-PDF 300dpi 1:1 grid. `role_hierarchy_actual_hink_elements.csv` supplies the 65 element/script rows; `role_hierarchy_audit.csv` supplies the 23 panel/role/script groups and same-role rows; `role_e_actual_hink_audit.csv` records every E comparison and every N/A basis. Revision111 low-profile punctuation is split by exact codepoint (`LOW_PROFILE_PUNCTUATION_Uxxxx`) and closed by `low_profile_punctuation_calibration.csv`; mixed comma/dot/semicolon height is never used as a proxy class.

## D result

Three applicable panel/role/script groups fail `[0.92,1.08]`:

| Group | element H_INK medians (px) | group median | extreme ratio |
|---|---:|---:|---:|
| BODY / ANNOTATION / MATH_OPERATOR | 33, 33, 37 | 33 | 1.1212 |
| BODY / AXIS_TITLE / CJK_FULL | 38, 35, 35 | 35 | 1.0857 |
| BODY / FORMULA_SCRIPT / LEGAL_TEX_SCRIPT | 22, 19, 22 | 22 | 0.8636 |

All same-role same-script scopes are single-panel/single-group here, so their result is N/A with an explicit single-group basis rather than a synthetic cross-script comparison.

## E result

Distinct same-script BASE groups are selected only where defensible. The two applicable failures are:

| Rule | target / base actual medians (px) | ratio | required |
|---|---:|---:|---:|
| numeric decimal point / tick decimal point | 5 / 6 | 0.8333 | [0.95,1.10] |
| formula operator / annotation operator | 13 / 33 | 0.3939 | [1.00,1.18] |

The remaining applicable comparisons pass; 15 entries are `N/A_WITH_BASIS` because no distinct ordinary same-script BASE exists, because the group is itself the designated BASE, because low-profile punctuation has no distinct same-codepoint BASE, or because legend/panel labels are absent. In particular, `BODY|ANNOTATION|MATH_OPERATOR` is N/A rather than a self-ratio of 1.0. No PDF span, emitted point size, or cross-script ratio is used to obtain any PASS.

Result: `H_INK_D_PASS=false`; `H_INK_E_PASS=false`; `E_COVERAGE_CLOSED_WITH_BASIS=true`.
