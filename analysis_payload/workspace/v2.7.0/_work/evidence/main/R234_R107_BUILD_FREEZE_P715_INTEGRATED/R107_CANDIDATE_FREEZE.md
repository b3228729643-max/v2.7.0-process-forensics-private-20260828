# R234 — R107 official candidate freeze with FIG-P715-01 integrated

- Status: `OFFICIAL_CANDIDATE_FROZEN / R107_BUILD_LOCK_RELEASED`
- Main branch: `v2.7.0/integration`
- Main commit: `9fad2af933911092f4a494d66fd607cdb94264cc`
- Main worktree: clean
- Integrated P715 source commit: main `9fad2af` from A atomic commit `7a0c4f4`
- Integrated source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C07/web_random_walk.tex`
- Integrated source SHA-256: `900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87`

## Single official build identity

- Invocation: one `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r107_fullbook -NoPublish` parent chain.
- Result: natural exit 0; `latexmk` reported all targets up to date; no manual retry, second parent invocation, interruption, or concurrent TeX chain.
- Terminal process gate: `latexmk/lualatex/luatex/luahbtex = NONE`.
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf`
- PDF identity: 817 pages; 4,967,249 bytes; SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Format: every page A4 `595.276 × 841.890 pt`; rotation 0; PDF 1.7; unencrypted.
- Final log: 258,877 bytes.

## Final mechanical gates

- Hard TeX errors, package errors, undefined control sequences, emergency/fatal exits: 0.
- Missing files/I/O, memory exhaustion, undefined references/citations, missing characters: 0.
- Duplicate destinations/labels, final rerun requests, overfull and underfull hbox/vbox: 0.
- Main index: 731 accepted, 0 rejected, 0 warnings.
- Symbol index: 355 accepted, 0 rejected, 0 warnings.

## FIG-P715-01 official-page verification

- Independent text lookup locates Figure 36.2 on physical page 765 (printed page 752); physical page 764 contains the lead-in text and both pages were rendered at native 300 dpi and opened.
- The official R107 figure crop was opened at 300 dpi. The two panels, graph, matrices `A/M/P`, formula stacks, caption and surrounding page are complete and readable; no crop, broken glyph, wrong code point, illegal overlap, or page-integration regression was observed.
- On the official PDF page, the node-j circle right edge is `x=188.503 pt`; the moved line `矩阵行、列顺序` starts at `x=210.654 pt`. The exact geometric gap is `22.151 pt`, approximately `92.30 px` at 300 dpi. The prior R106 37-pixel collision is absent.
- The local R17 all-pair evidence previously closed `N=259`, `C=33,411`, protocol intersections 0 and under-threshold relations 0. This local result authorized integration only; it is not substituted for the mandatory R107 fresh SA1 and fresh isolated SA3.
- Rendered evidence: `p715_page-764.png`, `p715_page-765.png`, and `p715_figure_300dpi.png` in this directory.

## Routing boundary

R107 now replaces R106 as the sole official candidate. FIG-P715-01 remains `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_FRESH_SA1`; it is not yet `A_LOCAL_PASS`. The next legal route is a completely fresh `gpt-5.6-sol/xhigh` SA1 on R107, followed only after an accepted PASS by a different fresh isolated SA3. Strict final completion remains `0/99`.

- Frozen at: `2026-08-26T13:38:05.9538126+08:00`
