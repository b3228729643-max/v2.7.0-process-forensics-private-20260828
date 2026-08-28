# FIG-P656-01 SA3 independent R108 review

## Result

`SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

This is an independent SA3 result only. It does not claim `C_LOCAL_PASS`, integration acceptance, global acceptance, or final release acceptance.

## Assigned identity and boundaries

- HANDOFF_ID: `C-FIG-P656-01-R108-SA3-FRESH-ISOLATED-V1`
- Actual instance: `/root/sa3_fig_p656_r108_fresh_isolated_v1`
- Model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Fork turns: `none`
- Role: one and only fresh isolated SA3 for `FIG-P656-01` against official R108
- TeX/LuaLaTeX/latexmk/texlua executions: `0`
- Business-source writes: `0`
- Commits: `0`
- Central state/inventory writes: `0`
- Other UID/role reviews: `0`
- Agents started: `0`

## Frozen identity and route

Official R108 PDF:

- Path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf`
- Pages: `817`
- Bytes: `4,967,161`
- SHA256: `C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78`

Sole current source:

- Path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_multinomial_counts.tex`
- Bytes: `2,854`
- SHA256: `9D404ED0694D575DE89038D3D6485C49AA4C60DCC3238AD8318CADACF810B381`

Target routing was independently established with four current caption/source strings. Exactly one hit occurred: physical page `705`, printed page `692`, `Fig. 34.2`.

The only adjacent business context read was current `V5-C05.tex` around the definition and figure inclusion. Exact provenance and hashes are in `identity_provenance.json`. The active Goal itself contains the relevant strict protocol/schema in sections 9.2.1 and 9.5 and task card B67; it does not directly reference an additional external protocol/schema path for this figure.

## Denominator and complete all-pair audit

Granularity deliberately separates visible semantic text, token circle/rim/fill objects, token numeral objects, flow arrows, node boundaries, node labels/formulas, caption number, and caption text. Natural math scripts are font subruns of their parent formula rather than separate semantic objects.

- Semantic object denominator: `N=50`
- Expected unordered pair count: `C(50,2)=1,225`
- Recorded pair rows: `1,225`
- Unique pair IDs: `1,225`
- Unique object IDs: `50`
- Empty object masks: `0`
- Separate-pair overlap candidate pixels: `0`
- Pairs requiring adjudication: `0`

Every pair has a classification for separation, intended containment, intended attachment, or required related clearance. Legal node containment and source-anchored arrow attachments were not converted into false failures.

## Images and manual coverage

Actual images were opened before manual records were written.

- Native 300 dpi full page: color and grayscale
- Native 300 dpi figure+caption: color and grayscale
- Native 300 dpi tight figure body
- Object overlay
- 50 independent object masks
- Five native 1x critical ROIs and five nearest-neighbor 8x versions
- Manual object reviews: `50/50`
- Manual critical-relation reviews: `29/29`
- Manual view records: `13/13`
- Manual hard-gate records: `27/27`

## Mathematical and textual result

The displayed rows recompute as follows:

- `(1,1,1,2,3,3) -> (3,1,2)`
- `(1,3,1,2,1,3) -> (3,1,2)`
- `(3,1,2,1,3,1) -> (3,1,2)`

Thus `N=6`, and the multinomial coefficient is

`6!/(3!1!2!) = 60`.

The support `n_k in Z_{>=0}` and `sum_k n_k=N` is correct. The warning is correct because the entries of the count vector sum to `6`, not `1`; the probability vector is the separate parameter `theta`. The first arrow correctly performs sequence-to-count compression, and the second correctly associates the count with the number of distinct orderings. Caption, figure, equations (34.1)-(34.2), and adjacent definition agree.

## Font, pixel, overlap, and geometry result

- General effective source size: `9.5 TeX pt`
- Title: `9.9 TeX pt`
- Cumulative graphics scale: `1.0`
- Caption: `9.96 PDF bp`, equivalent to about `9.997 TeX pt`
- PDF-reported internal size: `9.46 bp`, equivalent to about `9.495 TeX pt`; this is normal TeX-pt/PDF-bp conversion
- Font runs measured: `37`
- Font runs below applicable ink floor: `0`
- CJK ink minimum: `32 px`
- Token-digit ink range: `26-29 px`
- Base-math ink range: `38-47 px`
- Natural script/limit ink range: `19-23 px`

The small 26-29 px digit and 35-39 px caption-line outline variation is caused by glyph/raster/peer taxonomy and is advisory under user R168. Native and 8x views show no conspicuous imbalance, unreadability, missing glyph, wrong codepoint, or semantic distortion.

- OVERLAP_CANDIDATE_PIXEL_COUNT: `0`
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT: `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `7`

The canonical 7 px minimum is the coefficient label-to-formula text clearance, above the 4 px text-text floor. Token labels have at least 13.892 px clearance to the true circle boundary. Category-2 hatch texture may approach a digit by 1 px, but it is legal internal fill texture, not a node border or independent line/arrow collision; the black digits remain readable and their masks were separated by color.

Rendered arrow attachment gaps are 8 px at the left arrow tip, 2 px at the right arrow tail, and 7 px at the right arrow tip. Source anchors are explicit and native/8x views make the attachments unambiguous. No arrow crosses text.

## Gate conclusions

- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true` with R168 advisory documented
- ROLE_RATIO_PASS: `true`
- VISUAL_HARMONY_PASS: `true`
- MATH_SEMANTICS_PASS: `true`
- TEXT_CONSISTENCY_PASS: `true`
- GRAYSCALE_PASS: `true`
- PAGE_INTEGRATION_PASS: `true`

No hard blocker or unresolved item remains within SA3 scope.

## Next action

Main/Dialogue-C coordinator should independently inspect this sealed SA3 payload and decide whether to accept it toward `C_LOCAL_PASS`. This SA3 result alone does not make that decision.
