# FIG-P630-01 R109 isolated SA1 manual object review

Identity: `C-FIG-P630-01-R109-SA1-FRESH-ISOLATED-V1` / `/root/sa1_fig_p630_r109_fresh_isolated_v1` / `gpt-5.6-sol` / `xhigh` / `fork_turns=none`.

Views opened before these observations were written: physical-PDF-page-680 full page at native 300 dpi; full page at 200 dpi; figure at native 300 dpi/1x; figure plus caption at native 300 dpi/1x; native 300 dpi grayscale; text-measurement overlay; object overlay; semantic overlay; and all four nearest-neighbor 8x critical ROIs (conditional formula, main arrows, side leaders, boundary/caption).

The disjoint visible-object denominator has 36 IDs: nine node borders, five directed flow arrows, two non-directed leaders, and twenty reader-visible text elements. Nested TeX scripts are measured separately as M01S--M05S and are not double-counted as disjoint visible objects.

| ID | Manual observation after opening required views | Hard finding |
|---|---|---|
| B01 | Joint-target core box is fully visible, balanced, and expanded enough for its long one-line label. | none |
| B02 | Full-conditional core box contains two centered lines with clear vertical separation. | none |
| B03 | Coordinate-kernel core box cleanly separates kernel name from the one-coordinate update statement. | none |
| B04 | Scan-kernel core box cleanly separates header from systematic/random alternatives. | none |
| B05 | Related-sample core box is centered and visually subordinate to the directed chain. | none |
| B06 | Diagnostic core box cleanly separates the header from MCSE/ESS/trajectory. | none |
| B07 | Correctness side box is fully visible; all four lines have clear border clearance, including the last line. | none |
| B08 | Mixing-efficiency side box is fully visible and does not compete with the main chain. | none |
| B09 | Gold boundary box is fully visible and intentionally emphasized without dominating the figure. | none |
| F01 | Arrow runs rightward from joint target to full conditional and stops at node boundaries; no text contact. | none |
| F02 | Arrow runs rightward from full conditional to single-coordinate kernel and stops at boundaries. | none |
| F03 | Arrow runs downward from coordinate kernel to scan kernel; arrowhead is intact and clear. | none |
| F04 | Arrow runs leftward from scan kernel to related samples; direction is unambiguous. | none |
| F05 | Arrow runs leftward from related samples to diagnostics; direction is unambiguous. | none |
| L01 | Plain leader joins the correctness box to the joint-target corner; absence of arrowhead correctly marks annotation rather than chain direction. | none |
| L02 | Plain leader joins mixing efficiency to the scan box; it is clear, clipped nowhere, and does not imply generation time. | none |
| T01 | “联合目标 / 局部因子” is sharp, centered, and consistent with the source and adjacent text. | none |
| T02 | “给定 x_{-j} 的满条件” is sharp; the minus and subscript j are the correct visible codepoints. | none |
| T03 | “π_j(·\|x_{-j})” is mathematically correct and visibly separated from T02 by four actual ink pixels. | none |
| T04 | “单坐标核 K_j” uses the correct kernel symbol and legal subscript. | none |
| T05 | “只更新 x_j” states the correct Gibbs-coordinate semantics and is fully readable. | none |
| T06 | “扫描核” is centered and legible. | none |
| T07 | “系统 / 随机” matches the adjacent systematic/random-scan explanation. | none |
| T08 | “相关样本” correctly describes the output of the scan kernel. | none |
| T09 | “诊断” is centered and legible. | none |
| T10 | “MCSE / ESS / 轨迹” is sharp; Latin capitals and Chinese text are balanced. | none |
| T11 | “正确性条件” is sharp and semantically frames T12--T14. | none |
| T12 | “目标保持” is legible and consistent with the adjacent caveat. | none |
| T13 | “支持可达” is legible and correctly distinguishes reachability from mere target preservation. | none |
| T14 | “遍历性” is legible; its measured 8.96 px border clearance exceeds the 5 px node-border requirement. | none |
| T15 | “混合效率” is sharp and correctly frames T16--T17. | none |
| T16 | “自相关长度” is legible and consistent with MCSE/ESS diagnostics. | none |
| T17 | “有效样本量” is legible and correctly complements autocorrelation length. | none |
| T18 | “正确内核 ≠ 快速混合” uses the correct not-equal symbol, is fully visible, and is a justified emphasized boundary statement. | none |
| T19 | Caption label “图 33.1” is complete, sharp, and aligned with the caption text. | none |
| T20 | Caption is a single readable conclusion matching the six-node chain and diagnostic endpoint; it is not clipped. | none |

R168 advisory note: nearest8x inspection shows the low-outline subscript minus/dots as the intended glyphs. Any 1--2 px raster-outline variation is advisory only; there is no missing glyph, tofu, wrong codepoint, unreadability, or semantic corruption.
