# FIG-P657-01 — source and candidate identity audit

- HANDOFF_ID: `C-FIG-P657-01-R111-SA1-FRESH-ISOLATED-V1`
- SA1 route: `gpt-5.6-sol`, reasoning `xhigh`, fresh isolated instance `sa1_fig_p657_r111_fresh_isolated_v1`
- Official candidate: `main_full.pdf`, 4,967,076 bytes, SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`
- Current figure source: `fig_v5_c05_distribution_relations.tex`, 2,927 bytes, SHA-256 `B2B3A8748133B55169F08A543DF39E238E2FB3DFFF67EA0067C543CD9FDE31D2`
- Independent location: official PDF physical page 706, printed page 693, figure 34.3. Caption-text search located the only page containing the six-distribution sentence; the full page was then rendered directly.
- Native render geometry: 2,481 × 3,508 pixels at 300 dpi from a 595.276 × 841.89 pt page; no post-render resizing was used for measurements.

## Source audit

- Line 3 declares a 9.2 pt figure default, line 9 overrides ordinary nodes to 9.4 pt, line 16 declares 8.8 pt edge/legend labels, lines 18/21/24 use 9.5 pt bold row headings, and node labels inherit 9.4 pt.
- No `resizebox`, `scalebox`, `transform shape`, or other cumulative text reduction exists; `GRAPHICS_SCALE=1.0` throughout.
- Under the supplied R168 policy, the 8.8/9.2/9.4 pt declarations below the old 9.5 pt threshold are advisory and cannot alone fail the figure. The native 300 dpi inspection therefore governs hard failure.
- Source line 2 freezes six node objects, seven semantic relations, and two legend samples. Lines 28–29 are the two thick conjugacy arrows; lines 30–34 are the five thin/open special-case arrows; lines 35–38 reproduce both styles in the legend.

## Manual identity decision

`PASS`. The rendered candidate, source UID, caption, node labels, relation count, and legend topology all identify the same FIG-P657-01 object. No alternate candidate, prior evidence, or historical conclusion was used.

