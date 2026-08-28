# FIG-P610-01 — R104 fresh-isolated SA1 report

## Disposition

`SA1_PASS_REQUEST_FRESH_ISOLATED_SA3`

No SA1 hard failure was found. This is an AI SA1 visual-review result requesting a separate, fully fresh and isolated SA3. It is not `C_LOCAL_PASS`, not a global PASS, and not a human certification.

## Identity and review disclosure

- HANDOFF_ID: `C-FIG-P610-01-R104-SA1-FRESH-ISOLATED-V1`
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P610-01\sa1_r104_fresh_isolated_v1`
- reviewer_type: `AI_SA1_VISUAL_REVIEW`
- reviewer_instance: `/root/sa1_fig_p610_r104_fresh_isolated`
- human_certification: `false`
- decision_basis: every final glyph cell, every final pair cell, all final render views, and all final dedicated critical views were actually opened and visually adjudicated.
- “manual ledger” means per-ID decisions were authored with `apply_patch`, not generated, populated, defaulted, or bulk-decided by machine code. It does not mean a human performed or certified the review.
- TeX: `DISABLED`; no LuaLaTeX, latexmk, texlua, or other TeX engine was run.
- source_writer: `NONE`; official PDF, figure source, and main source were not mutated.
- subagents: none.

## Allowed inputs and isolation

The review used only the authorized official R104 PDF, the current P610 figure source, the goal objective, the strict pixel/typography protocol, and the strict figure evidence schema. The chapter source was not needed. No old P610 evidence, central report/state/inventory/routing material, other UID evidence, agent output, chat history, or Git history was read.

## Official artifact identity and independent locator

Official PDF:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`

- pages: 817
- media size: A4, 595.276 × 841.890 pt
- bytes: 4,967,222
- SHA256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`

A fresh full-PDF caption/label search located exactly one matching figure:

- physical PDF page: 662
- printed page: 649
- figure number: 32.10
- caption: `接受–拒绝抽样拒绝候选后不输出该候选；MH 拒绝候选后把当前状态再次记入链，因此输出通常相关而非独立`

Current single-source figure file:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_rejection_sampling_comparison.tex`

- bytes: 2,834
- SHA256: `3E3B5CB5604EB0945F77850B1350ABD946FA592D78AF0983AB04EDDACB5D84EE`

## Render evidence

- full page 300dpi: 2481 × 3508 px
- full page 200dpi: 1654 × 2339 px
- figure crop: full-page pixel box `[291,2050,2230,2742]`, 1939 × 692 px
- standalone figure body: full-page pixel box `[454,2050,2071,2600]`, 1617 × 550 px
- additional opened views: grayscale 300dpi and after-text-measurement object overlay 300dpi

The full page shows clean integration with the surrounding paragraph and following example. The figure crop contains both complete panels and caption. The standalone body contains every in-scope graphical and text element. Grayscale preserves the hierarchy and semantic distinctions.

## Inventory and coverage

- text parent objects: 18
- graphic foreground objects: 22
- semantic foreground objects: 40
- in-scope PDF drawing references: 24/24 mapped; 0 unmapped
- glyph IDs: 132/132 reviewed, 132/132 nonempty masks
- glyph 1x evidence: 132/132
- glyph 8x evidence: 132/132
- all semantic pairs: `C(40,2)=780/780`
- pair contact sheets: 39, 20 cells each
- manual AI pair ledger: 780 unique IDs; 0 missing, 0 extra, 0 member/metric mismatches against machine inventory
- critical/near pairs: 11/11 with final dedicated 1x and 8x evidence
- raw overlap count: 0
- overlap pixel sum: 0
- figure-crop edge-contact pixel sum: 0
- minimum semantic-object figure-crop edge clearance: 11 px
- standalone edge-contact pixel sum: 0
- standalone missing in-scope objects: 0
- machine-generated manual-review fields: none

## Actual AI visual adjudication

All 11 final glyph sheets were opened at original detail. Every glyph’s original/overlay/mask-only cell was inspected. All 132 glyphs are legible and codepoint-correct. Mathematical italic `𝑌` and subscripts 1/2/3 retain their intended semantics. No tofu, wrong CJK form, wrong punctuation codepoint, unreadable glyph, severe font imbalance, or clipped glyph was observed.

All 39 final pair contact sheets were opened at original detail. Every one of the 780 cells was inspected. Red and blue masks remained visibly distinct; no magenta intersection or illegal occlusion appeared. The ledger records every pair ID, members, exact observed overlap/clearance, evidence sheet/cell, AI reviewer identity, decision basis, decision, and pair-specific observation.

Each of the 11 dedicated final critical 1x/8x views was separately opened. All participating node rings, double rings, connectors, and arrows remain complete. The smallest real gap is 5px for PAIR-0748; the remaining critical gaps are 8px or 9px. No critical pair touches or hides another object.

## Hard-gate findings

- typography/font under R168: no hard failure
- actual readability: no hard failure
- geometry/alignment: no hard failure
- object content and relationships: no hard failure
- mathematical semantics: no hard failure
- accept-reject semantics: no hard failure
- MH repeated-state semantics: no hard failure
- caption and nearby-body consistency: no hard failure
- actual clip: no hard failure
- illegal overlap/occlusion: no hard failure
- role/peer consistency: no hard failure
- full-page integration: no hard failure

The left panel correctly proposes Y1,Y2,Y3, rejects Y2, and outputs Y1,Y3. The right panel correctly proposes Y1,Y2,Y3, rejects Y2, repeats the current Y1 state, and then outputs Y3, producing Y1,Y1,Y3. Caption and nearby text state the same distinction.

## Advisories under R168

1. PAIR-0748 has a close 5px gap between the lower Y2 proposal segment and the outer repeated-state ring. The final 8x view shows a real gap and complete contours, so this is advisory only.
2. A few mathematical italic `𝑌` evidence overlays omit tiny antialias fringe at the crop boundary while the actual render remains complete and readable. This is mask/evidence micro-geometry only.
3. En dashes, decimal point, fullwidth comma/semicolon/colon, and CJK `一` naturally have low ink profiles. Their codepoints and rendered forms are correct.

## Final request

Request another fully fresh isolated SA3 instance using the sealed evidence package. Do not infer `C_LOCAL_PASS` or global PASS from this SA1 result.
