# SA1 fresh isolated review report - FIG-P632-01

## assigned_scope

- OWNER_DIALOGUE: C_visual
- HANDOFF_ID: C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-V1
- Canonical instance: /root/sa1_fig_p632_r110_fresh_isolated_v1
- Role/model/effort/fork: SA1 / gpt-5.6-sol / xhigh / none
- Object: Figure 33.2, canonical UID FIG-P632-01
- Allowed reads: official R110 full-book PDF, current single P632 source, active Goal strict visual protocol, and necessary current V5-C04 chapter context
- Allowed writes: only this isolated evidence root
- Prohibited and not performed: prior/parallel P632 conclusions or evidence, SA2 material, main acceptance, other UIDs, task/state/inventory/route logs, Git-history conclusions, source/TeX/LuaLaTeX/latexmk/Git/central writes, agent spawning or status queries

## completed

1. Independently verified the official PDF as 4,967,063 bytes, 817 pages, SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`.
2. Independently verified the current figure source as 9,022 bytes, SHA-256 `1670F496E6CEBBF5636AC5BC97474A50FBA83811FFA2AAAAEF0CF8227BE8C8EB`.
3. Located physical page 682, printed page 669, Figure 33.2, source label `fig:V5-C04-conditional-slice`, and the full caption: “同一二元正态联合密度的两条截面除以相应边缘密度后，得到方差16/25、全实线积分为1的满条件密度；零边缘处须使用预先指定的正则条件版本。”
4. Rendered the full page directly with Poppler at 300 dpi (2481 x 3508 px) and created native figure/caption crops, grayscale, semantic-object overlay, text-measurement overlay, nine critical 1x ROIs and nine nearest-neighbour 8x ROIs.
5. Froze 23 visible semantic objects, all 253 unordered pairs, 29 reader-visible text elements, and 168 extracted PDF text spans.
6. Personally inspected the actual native images before writing any manual decision. Completed per-ID ledgers for 23 objects, 253 pairs, 29 text elements, 9 critical ROIs, 24 glyph/codepoint controls, 9 views, 11 math/probability checks and 22 hard gates.
7. Applied R168: antialiasing, intrinsic glyph-outline and taxonomy differences were treated as advisory; no advisory item was promoted to hard FAIL without a permitted substantive defect.

## files_changed

All mutations are confined to this evidence root. They comprise the Poppler page render; native crops and overlays; 1x/8x ROI images/contact sheets; machine-only identity, object, pair, text, span and ROI tables; the evidence builder; manual object/pair/text/glyph/view/hard-gate ledgers; overlap, font and model-route records; this report; the handoff; and the final manifest/control marker. The official PDF, figure source, chapter source, build tree, Git state, central state and every other UID/role root remain unchanged.

## decisions

- Mathematical and probability semantics: PASS. The joint normalization, quadratic exponent, two conditional means/variance, marginal values, peak, integrals, contour orientation, slice-to-conditional mapping and zero-marginal regular-condition qualification all independently recompute and agree with the page/source.
- Numerical values: PASS. `rho=0.6`, variance `0.64=16/25`, means `0.48=12/25` and `0.6=3/5`, `phi(0.8)=0.2896915528`, `phi(1)=0.2419707245`, peak `0.4986778505=5/(4sqrt(2pi))`.
- Source font: PASS. Figure base text is declared 9.6 TeX pt with cumulative graphics scale 1.0; extracted PDF base spans are 9.5641 bp. Natural math scripts are semantically derived, not whole-formula shrinking.
- Pixel height and ratios: PASS. Smallest audited base-math label is 25 px against a 22 px threshold; CJK labels exceed 30 px; paired top/bottom roles match; map CJK labels are 36/37 px (ratio 1.028).
- Geometry/relationships: PASS. Positive-correlation contours have the correct +45-degree major axis; horizontal/vertical slices map to the correct conditional panels; routing arrows do not cross.
- Overlap/clipping: PASS. `OVERLAP_CANDIDATE_PIXEL_COUNT=0`, `BBOX_CANDIDATE_PAIR_COUNT=46`, `MASK_CONTAMINATION_PIXEL_COUNT=0`, `OVERLAP_PIXEL_COUNT=0`, `PIXEL_ADJUDICATION_STATUS=CLEAR`, `CLIP_PIXEL_COUNT=0`, `MIN_TEXT_CLEARANCE_PX=9`.
- Glyph/readability: PASS. Fonts on page are embedded with Unicode mapping; 24 targeted glyph/vector controls show no tofu, missing character, wrong codepoint or clipped outline.
- Grayscale/harmony/page integration: PASS. Line styles remain distinct without color; hierarchy is balanced; note/caption/following prose have clean separation.
- SA1 result: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

## unresolved

None. Unresolved object/pair/pixel/glyph/hard-gate count is 0. No pixel dispute or max arbitration trigger exists.

## validation

- Object ledger: 23/23 unique IDs.
- Pair ledger: 253/253 unique IDs, exactly matching machine pair order.
- Text ledger: 29/29 unique IDs.
- Critical ROI ledger: 9/9 unique IDs at both 1x and 8x.
- Glyph controls: 24/24 unique IDs.
- View ledger: 9/9 unique IDs.
- Hard gates: 22/22 unique IDs, all PASS.
- Existing JSON and CSV files parse successfully.
- Final one-time seal validation will additionally require manifest/filesystem closure, all JSON/CSV parse, ADS=0, cache=0, pyc=0, reparse=0, staged-marker absence, all files/directories read-only, and postmarker writes=0.

## next_action

Start a completely fresh isolated SA3 for FIG-P632-01 using only the allowed current PDF/source/protocol/context and this SA1 handoff as authorized by the parent. Do not treat this SA1 PASS as final three-role or main acceptance.
