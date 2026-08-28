# FIG-P067-01 fresh SA3 result

- Status: `SA3_FAIL_RETURN_TO_SA2`
- Reviewer identity: `/root/p067_r113_fresh_sa3`
- Handoff ID: `A-R113-P067-SA3-FRESH-ISOLATED-20260827`
- Frozen official candidate: R113 `main_full.pdf`, physical page 69, printed page 56, Figure 4.1.
- Caption: 离散随机变量的分布函数：跳跃高度等于对应点的概率质量
- Visible-object denominator: 130 = 95 glyphs + 35 final-visible foreground graphics. Five real white occluders are tracked separately.
- Complete unordered relationships: 8,385/8,385.
- Manually opened critical ROIs: 71 in six latest 8x contact sheets.
- Hard failures: P01916 (T016 p in p4 vs G008 y=1 CDF plateau) and P01917 (T016 vs G009 dashed y=1 reference), each 34 native final-visible intersection pixels and 0 px clearance.
- Advisory typography: nine source font declarations below the protocol 9.5pt numeric value and nine small-profile glyph measurements; all are actually readable, complete, and harmonious under R168 and do not determine the failure.
- Mathematics/semantics: PMF/CDF values, normalization, jump equivalence, monotonicity, terminal value, right continuity, open/filled endpoints, labels, and caption all pass.
- Page integration/grayscale: pass.
- Missing/tofu/wrong codepoint: none.
- Clipping: none.

The two p4 overlaps are real illegal overlaps under the R168 hard gate. They cannot be overridden by the advisory-only micro typography observations. This role makes no source patch. SA2 should reposition p4 or increase/reposition its real background so the p glyph has at least 3 px final-visible clearance from both G008 and G009, rebuild a new official candidate, then route through fresh SA1 and fresh SA3.
