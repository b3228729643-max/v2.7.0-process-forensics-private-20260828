# FIG-P598-01 — R104 fresh isolated SA3 manual visual and semantic adjudication

- HANDOFF_ID: `A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825`
- reviewer role: SA3, independent human visual adjudication after machine extraction
- model/effort: `gpt-5.6-sol/xhigh`
- target: frozen R104 physical page 649, crop `[230,2040,2195,2765]` at native 300 dpi
- source PDF identity: 817 pages; 4,967,222 bytes; SHA256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- crop dimensions: 1965 x 725 px; RGB; native 300 dpi

## Actually opened evidence

Every item below was opened and visually observed; no manual conclusion was produced by a script.

- full page: `render/full_page_300dpi.png`, `render/full_page_200dpi.png`
- figure views: `render/figure_crop_300dpi.png`, `render/standalone_300dpi.png`, `render/grayscale_300dpi.png`
- complete overlay: `machine/after_text_and_graphic_overlay_300dpi.png`
- all text-object contact sheets: `machine/contact_sheets/glyph_contacts_01.png` through `glyph_contacts_24.png`
- all graphic-object contact sheets: `machine/contact_sheets/graphic_contacts_01.png` through `graphic_contacts_05.png`
- both complete pair matrices: `machine/matrices/all_pairs_clearance_matrix.png`, `machine/matrices/all_pairs_overlap_matrix.png`
- all relationship sheets: `machine/relationship_sheets/critical_relationships_01.png` through `critical_relationships_04.png`
- opaque-white double-circle separator evidence, each opened at pre/halo/final stages: G005, G007, G009, G011 under `machine/occlusion_masks/`

The final rebuilt object masks, contact sheets, matrices, and relationship sheets were the versions observed. Earlier unsealed diagnostic renderings were replaced before this adjudication.

## Complete visible-object denominator

| class | count | manual outcome |
|---|---:|---|
| visible non-whitespace text glyphs | 142 | 142 PASS |
| visible graphic/path objects | 26 | 26 PASS |
| complete visible denominator | 168 | 168 PASS |
| unordered pairs, 168 choose 2 | 14,028 | 14,028 disposition complete |

All 168 IDs are individually adjudicated in `manual_object_adjudication.md`. The final masks are complete and pure. No mask is empty. Machine extraction wrote no manual decision field and did not overwrite either manual ledger.

The bidirectional PDF text/path inspection accounts for every visible object. There are zero separate graphic math-rule paths: the displayed equations are text glyphs, while the 26 drawing objects are the axis, nodes, separators, transition shafts/arrowheads, and repeated-state arc. Four white paths (G005, G007, G009, G011) are intentional opaque separators between the wide blue and inner dark rings; the opened pre/halo/final evidence proves that they are visible construction layers rather than blank artifacts.

## R168 typography adjudication

Hard-fail typography criteria are limited to missing/tofu content, wrong glyph or codepoint, wrong math semantics, genuinely unreadable text, obvious severe visible imbalance, and real clipping/overlap. None occurs.

- missing/tofu glyphs: 0
- wrong glyph/codepoint: 0
- wrong mathematical meaning: 0
- genuinely unreadable glyphs: 0
- severe visible font imbalance: 0
- text clipping or illegal overlap: 0
- `FONT_VISUAL_HARMONY_PASS=true`

The source/PDF audit reports local 8.6 pt text, 9.2 pt figure text, 9.4 pt nodes, natural 5.9975 pt scripts, and a small set of native-pixel glyph-height exceptions. Under R168 these are advisory only because each affected glyph was opened, is complete and pure, and is comfortably readable at native 300 dpi and in the lower-resolution page view. In particular, the low-height single-stroke Chinese glyph `一`, short equals signs, small script digits, plus sign, and arrow are shape-driven measurements, not missing or clipped content. The 1x crop and 8x-equivalent inspection lead to the same PASS decision.

## Pixel geometry and overlap adjudication

- crop-boundary clip pixels: 0
- minimum crop-edge clearance: 21 px
- minimum independent text-to-text clearance: 25.5707 px
- minimum independent text-to-graphic clearance: 8.4340 px
- state-label to node clearances: 26.5862, 20.0238, 20.0238, 25.4008, 25.6271, 23.3516, 27.0179 px
- raw geometric overlap pairs: 17; all visually explained and allowed
- final illegal overlap pairs: 0

The 17 raw overlaps comprise one axis shaft/own arrowhead joint; four wide-blue/white separator ring pairs; four repeated-arc or transition-shaft contacts at their source nodes; and six transition-shaft/own-arrowhead joints, plus the remaining intended ring/anchor contacts enumerated in `manual_pair_adjudication.md`. The two nearest non-overlap relationships (T017/G026 and T016/G026) retain clear white separation. Every critical relationship overlay was opened and adjudicated per ID.

## Hard semantic and relationship checks

| requirement | observation | decision |
|---|---|---|
| state sequence | `a,b,b,c,c,b,a` at `t=0,1,2,3,4,5,T` | PASS |
| transitions | six continuous transition shafts, each with its own arrowhead | PASS |
| time axis | left-to-right time axis with arrowhead and label `时间 t` | PASS |
| equal spacing | seven centers are equally spaced at approximately 53.859 pt; no visible drift | PASS |
| repeated states | b→b and c→c are labeled `保持`; adjacent-state correlation is legible | PASS |
| repeated-state arc | dashed arc cleanly connects the repeated b states and clears nearby labels | PASS |
| transition kernel | figure reads `K(x_t,\mathrm d x_{t+1})` with correct subscripts and differential | PASS |
| caption kernel | caption reads `K(x,\mathrm d y)` and describes `x→y` correctly | PASS |
| double circles | four middle nodes visibly use wide blue outer ring, white separator, and dark inner ring; bottom note explains adjacent same-state retention | PASS |
| arrow continuity | all arrow shafts and heads join at intended anchors; no accidental breaks | PASS |
| crop/clearance | no visible clipping; labels, arcs, arrows, caption, and bottom note have adequate whitespace | PASS |
| grayscale | hierarchy, arrows, rings, labels, and caption remain distinguishable | PASS |
| page integration | figure sits cleanly in the page column, neither cramped nor overpowering; caption and surrounding body remain balanced | PASS |

## Final human decision

All required native-300-dpi, lower-resolution, 1x, 8x-equivalent, object-level, pairwise, critical-relationship, semantic, grayscale, crop, and page-integration checks pass under R168. Advisory font ratios and isolated 1–2 px measurements do not create a hard visual defect.

`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`
