# FIG-P634-01 — fresh isolated R110 SA1 report

- OWNER_DIALOGUE: `C_visual`
- HANDOFF_ID: `C-FIG-P634-01-R110-SA1-FRESH-ISOLATED-V1`
- canonical instance: `/root/sa1_fig_p634_r110_fresh_isolated_v1`
- role: `SA1`
- model / reasoning: `gpt-5.6-sol` / `xhigh`
- fork_turns: `none`
- result: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

## Assigned scope

Perform a completely fresh, read-only SA1 audit of UID `FIG-P634-01` using only the official R110 PDF, the current single figure source, the active Goal/strict protocol, and the necessary current V5-C04 context. No TeX, source, Git, central-state, second-role, or second-UID writes were authorized. Evidence writes were confined to this root.

## Identity and independent location

The official PDF is 4,967,063 bytes with SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`. It has 817 A4 pages. The current source is 4,352 bytes with SHA-256 `903DE12067AF0B33F316EC09D65F6803F6BD212D64EB838F2FD8F264748F520E`.

The figure was independently located from its caption text on physical page 684, printed page 671, as Figure 33.3. The source label is `fig:V5-C04-coordinate-sweep`. Full caption:

> 系统扫描按固定次序即时写回；当前子步的前段使用本轮新值，后段沿用前轮旧值；末位更新结束后，末位状态与本轮样本状态相同并记录为轮末样本。

## Frozen denominators and manual coverage

| Family | Frozen denominator | Manual coverage |
|---|---:|---:|
| Visible semantic-foreground objects | 46 | 46 |
| All unordered object pairs | 1,035 = C(46,2) | all retained; all 56 relevant/close/contained pairs adjudicated individually |
| Text elements | 41 | 41 |
| Critical glyph/codepoint tokens | 15 | 15 |
| Critical ROI families | 6 | 6 native1x + 6 nearest-neighbour8x opened |
| View records | 21 | 21 actually opened |
| Hard-gate families | 22 | 22 |

Machine tables contain only identities, taxonomy, coordinates, measurements, and raw pair metrics. Reviewer decisions are in separate manually authored files under `audit/`; the machine script never generates or overwrites them.

## Visual, pixel, and font results

- Source font range: 9.6–10.6 pt, graphics scale 1.000; source-font gate passes.
- Text measurements: 41/41 meet their hard script-class ink-height floor; 0 same-class ratio outliers.
- Glyph tokens: 15/15 hard tokens pass. Mathematical italic `x` measures 20 px, above the 17 px lowercase/x-height floor; natural scripts are 35–36 px in their own raised clusters.
- Semantic-mask candidate intersection pixels: 0.
- Confirmed mask-contamination pixels: 0.
- Confirmed true illegal overlap pixels: 0.
- Pixel adjudication status: `CLEAR`.
- Clipped foreground pixels: 0.
- Minimum true text-to-node-border clearance: 9 px.
- Minimum arrow-to-text/formula clearance: 16 px.
- Same-class ratio pass: true.
- Role-ratio pass: true. Source-level title/base ratio is 10.6/9.6 = 1.104; formula/base source ratio is 10.0/9.6 = 1.042. Formula composite height includes natural superscripts and is not miscompared against CJK full-height ink.
- Grayscale pass: true. Updated/current/old roles remain distinguishable by hatching, solid/dotted borders, location, and labels rather than color alone.
- Visual harmony and page integration: pass. No obvious imbalance, crowding, clipping, orphaning, or disruptive whitespace is present.

R168 was applied. The low-profile outlines of U+FF1B, U+FF0C, and U+3002 are advisory morphology only: their codepoints are correct, they are readable at native scale, and they are neither tofu nor substitutions.

## Mathematical and instructional semantics

The fixed scan order is left-to-right. At substep `j`, the prefix through the current coordinate carries current-round values, while the suffix after `j` carries previous-round values. The first card correctly names this mixed state `x^[j]`. The final card correctly shows `x^[d]` and `x^(t)` as the same post-sweep state, then uses a distinct one-way arrow to record only that state as the round-end sample. The figure, caption, and V5-C04 lines 218–221 agree. Numeric labels, formulas, brackets, arrow directions, and caption numbering are correct.

## Decision

No hard failure was found under the supplied R168 rule. The SA1 outcome is:

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

## Unresolved

None within the assigned SA1 scope.

## Next action

The owner may initiate one fresh isolated SA3 instance for this UID under its own isolation constraints. This SA1 does not start SA3, modify the source, or update central state.
