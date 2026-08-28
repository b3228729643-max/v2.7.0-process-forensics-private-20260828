# 持久决策

## D-001

- status: active
- date: 2026-08-24
- decision: 以 aux 的印刷页665与 PDF page label 映射确定物理页678；不使用 UID 中的 P630 作为页码。
- reason: 用户明确禁止假设 UID 即页码，官方 PDF 页标签给出可复核映射。
- affected_scope: 本轮所有页面与图框坐标。
- affected_files: 本目录全部证据。
- supersedes: 无。

## D-002

- status: active
- date: 2026-08-24
- decision: 所有像素计量均以官方 PDF 物理页678的原生300dpi渲染为唯一计数坐标；独立编译 standalone 只作视觉交叉检查。
- reason: 严格协议要求像素计数绑定官方候选且禁止二次 resize。
- affected_scope: glyph/path masks、pair overlap/clearance、critical cards。
- affected_files: 本目录 `render/`、`glyphs/`、`graphics/`、`pairs/`、`critical/`。
- supersedes: 无。

## D-003

- status: terminal
- date: 2026-08-24
- decision: 本轮终态固定为 `SA1_FAIL_ROUTE_SA2`；不得因 geometry、语义、灰度或整体观感 PASS 而进入 SA3。
- reason: GLYPH-013 与 GLYPH-025 的 `U+2212` 分别 H=3px，GLYPH-022 的 `U+22C5` H=5px；三者均是语义 operator，严格门为22px且禁止降格或四舍五入。
- affected_scope: 本轮 SA1 terminal conclusion 与 SA2 路由。
- affected_files: `after_pixel_measurements.csv`、`glyph_manual_review.csv`、`after_visual_acceptance.md`、`RESULT.txt`。
- supersedes: 无。
