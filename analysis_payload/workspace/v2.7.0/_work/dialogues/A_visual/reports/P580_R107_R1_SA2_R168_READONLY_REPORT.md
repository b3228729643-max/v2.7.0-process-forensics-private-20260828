# FIG-P580-01 R107 SA2 R168 read-only report

## Verdict

`P580_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

HANDOFF_ID: `A-R107-P580-SA2-R168-READONLY-20260826`

The current R107 figure on physical page 630 (printed page 617, figure 31.6) has no R168 hard defect. No source change, TeX invocation, commit, fresh role, or second UID was performed.

## Identity

- R107 PDF: 817 pages, 4,967,249 bytes, SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Current source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex`.
- Source SHA-256: `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`.
- Worktree remained clean.

## Current observation and gates

Full-page, figure-crop, standalone, grayscale, native glyph/relationship, and nearest-neighbour 8x views were opened. Both panels, curves, markers, axes, support hatching, formula card, labels, and caption are legible and unclipped. U+0338 and U+226A are present and visibly complete; there is no tofu, wrong codepoint, broken mathematical meaning, true collision, or illegal overlap.

The explicit source font-size minimum is 9.6 pt. The p, q_L, and q_R definitions all normalize to one. The support relations are correct, and `24/25`, `3/2`, `24/25` recompute exactly and match the current body/caption. All R168 hard-gate counts are zero; micro contour/mask/taxonomy differences remain advisory only.

## Seal

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R1_SA2_R168_READONLY_R107_20260826`
- Payload: 15 files.
- Controls: two manifests plus `WRITE_STOPPED`.
- Ordinary files: 18 = 15 + 3.
- Manifest A/B rows: 15/15; A↔B and manifest↔filesystem path/bytes/SHA mismatches: 0.
- Read-only files: 18/18; ADS/cache/pyc/reparse: 0.
- `WRITE_STOPPED` is the unique latest file by 135,928,394 ticks; no root write followed it.

Requested next action: central acceptance and dispatch of one completely fresh isolated R107 SA1 under a new root. This report does not start that role.
