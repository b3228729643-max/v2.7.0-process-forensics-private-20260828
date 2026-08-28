# FIG-P598-01 R4 R104 fresh isolated SA3 report

## assigned_scope

- HANDOFF_ID: `A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825`
- instance: `/root/p598_01_r104_fresh_sa3_restart2`
- model/effort: `gpt-5.6-sol/xhigh`
- figure UID: `FIG-P598-01`
- role: independent SA3 visual/pixel/semantic adjudication of frozen R104 physical page 649
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R4_SA3_FRESH_ISOLATED_R104_R168_RESTART2_20260825`
- isolation: fresh R4 evidence only; no prior role verdict, denominator, crop, object model, or conclusion was used

## completed

- Verified the frozen PDF identity: 817 A4 pages, 4,967,222 bytes, SHA256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`.
- Rendered physical page 649 at native 300 dpi (2481 x 3508) and lower-resolution 200 dpi (1654 x 2339).
- Independently selected crop `[230,2040,2195,2765]`, producing a 1965 x 725 native crop; created standalone and grayscale views.
- Rebuilt the complete visible denominator from PDF text and drawings: 142 visible non-whitespace glyphs plus 26 visible graphic/path objects, total 168.
- Built a unique safe filename and mask for every object. All 168 final masks are nonempty, complete, pure, ordinary-file/openable, and free of manual decision fields.
- Enumerated all `168 choose 2 = 14,028` unordered pairs in JSON and CSV; built full overlap and clearance matrices.
- Built 24 text contact sheets, 5 graphic contact sheets, and 4 critical relationship sheets. Opened every final sheet and both matrices, as well as all four opaque-white separator paths at pre/halo/final stages.
- Manually adjudicated 168/168 object IDs and 19/19 critical/nearest relationship IDs after visual observation. Scripts never created or overwrote the manual fields.
- Inspected the native crop, standalone, grayscale, 300-dpi full page, 200-dpi full page, and complete overlay.
- Performed R168 typography, math, state-sequence, transition, axis/spacing, repeated-state correlation, double-circle, clearance, arrow-continuity, crop, grayscale, and page-integration checks.
- Ran a terminal cross-check confirming object JSON/CSV/manual counts `168/168/168`, pair JSON/CSV counts `14,028/14,028`, 168 unique object IDs, 14,028 unique pair IDs, 168 openable masks, zero empty masks, zero final illegal overlaps, and zero crop clipping.
- Prepared a one-time seal containing complete dual manifests and a final `WSTOP`; all payload/report/handoff files are read-only and the post-seal write count is zero.

## files_changed

- New sealed evidence tree: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R4_SA3_FRESH_ISOLATED_R104_R168_RESTART2_20260825`
- This report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P598_01_R4_R104_FRESH_SA3_REPORT.md`
- Formal handoff: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825.md`
- No TeX/source, build, state, inventory, task, git, or acceptance file was changed.

## decisions

- `FONT_VISUAL_HARMONY_PASS=true` under R168. The source/PDF sizes and isolated native-pixel threshold exceptions are advisory because every affected glyph is complete, pure, readable, correctly encoded, visually balanced, and unclipped. There is no missing/tofu content, wrong codepoint, wrong math meaning, genuinely unreadable content, severe visible imbalance, clipping, or illegal overlap.
- State semantics PASS: `a,b,b,c,c,b,a` at `t=0,1,2,3,4,5,T`.
- Transition semantics PASS: six directed transitions, six shafts, six own arrowheads, and a continuous left-to-right time axis.
- Equal-spacing and adjacent-correlation semantics PASS: seven centers are visually and geometrically evenly spaced; b→b and c→c retention and the dashed repeated-b relation are clear.
- Math semantics PASS: figure `K(x_t,\mathrm d x_{t+1})`; caption `K(x,\mathrm d y)` with `x→y`.
- Double-circle semantics PASS: four middle nodes visibly retain wide blue outer ring, opaque white separator, and dark inner ring; the bottom note explains the convention.
- Pairwise geometry PASS: 17 raw intersections are all intentional ring, anchor, axis, or shaft-to-own-arrowhead relationships. The other 14,009 pairs are non-overlapping; final illegal overlap count is 0.
- Crop, arrow continuity, grayscale, and page integration PASS; crop-boundary clip count is 0.
- Final decision: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`.

## unresolved

- None within the assigned SA3 scope.
- Advisory-only measurements remain recorded transparently in `after_font_audit.csv`, the object ledger, and the manual visual adjudication; none reaches an R168 hard-fail condition.

## validation

- frozen identity: PASS
- page/crop/render dimensions: PASS
- complete object denominator: `168/168`
- complete unordered-pair denominator: `14,028/14,028`
- manual object adjudication: `168/168 PASS`
- manual critical relationship adjudication: `19/19 PASS`
- final illegal overlap: `0`
- crop clipping: `0 px`
- opened final contact sheets: `29/29`
- opened final matrices: `2/2`
- opened final relationship sheets: `4/4`
- terminal cross-check: PASS
- dual manifests: complete
- read-only payload/report/handoff: PASS
- ADS / pyc / cache: `0 / 0 / 0`
- WSTOP: strictly latest
- post-seal writes: `0`

## next_action

- Main A may inspect the sealed R4 evidence, report, and handoff and decide whether to issue its own local pass acceptance.
- SA3 does not write the main-A acceptance marker.
