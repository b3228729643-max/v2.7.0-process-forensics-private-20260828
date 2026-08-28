# 当前问题与阻塞

## I-001：H_INK 三项硬失败

- status: closed_for_audit_route_to_sa2
- objects: GLYPH-013、GLYPH-022、GLYPH-025
- evidence: `glyphs/cards_8x/`、`critical/glyphs/`、`after_pixel_measurements.csv`
- consequence: `SA1_FAIL_ROUTE_SA2`

## I-002：三个 glyph 候选边界像素

- status: resolved_manual_confirmed
- objects: GLYPH-025 / GLYPH-026
- evidence: `glyph_ambiguity_resolution.csv`
- resolution: 三个像素均属下标 j 左下 descender 抗锯齿边缘，唯一分配给 GLYPH-026；无污染或漏笔。

当前无未决人工状态或外部阻塞。
