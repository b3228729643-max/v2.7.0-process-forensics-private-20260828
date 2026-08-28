# 持久决策

## D-001

- status: active
- date: 2026-08-25
- decision: 图面对象分母采用 19 个独立 TEXT/FORMULA 语义对象与 13 个 GRAPHIC/MATH_RULE 对象，共 32 个；glyph 分母独立于对象分母。
- reason: 同一公式内部 glyph 由 glyph ledger 覆盖，而公式父对象与其他独立对象进入全部 pair；分数线仍作为独立 MATH_RULE 进入对象和 pair 分母。
- affected_scope: object manifest, C(32,2), glyph parent mapping
- affected_files: objects/*, glyphs/*, pairs/*
- supersedes: none

## D-003

- status: active
- date: 2026-08-25
- decision: Aggregate strict figure result is FAIL even though object, pair, critical, clip and four-view gates pass.
- reason: 17 glyph threshold/calibration rows fail, six peer rows fail, and the formula-block role ratio 1.22449 exceeds the allowed maximum 1.18. The protocol allows no visual-shape waiver for these rows.
- affected_scope: manual ledgers, hard gates, final report, final marker
- affected_files: ledgers/*, SA3_REVIEW.md, WRITE_STOPPED.json
- supersedes: none

## D-002

- status: active
- date: 2026-08-25
- decision: figure_crop 包含题注；standalone 只含图体与自环标签。所有 175 个有墨迹 glyph（含题注）均纳入逐 glyph 分母。
- reason: 任务要求每个可见 glyph；题注是目标 figure 的可见组成。
- affected_scope: render crop, glyph denominator
- affected_files: render/*, glyphs/*
- supersedes: none
