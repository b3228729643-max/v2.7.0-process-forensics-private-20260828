# FIG-P641-01 R110 fresh-isolated SA1 report

## Identity and scope

- HANDOFF_ID: `C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1`
- Actual instance: `/root/sa1_fig_p641_r110_fresh_isolated_v1`
- Model / effort / fork: `gpt-5.6-sol / xhigh / none`
- Role: the one fresh isolated SA1 for current R110 UID `FIG-P641-01`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P641-01\sa1_r110_fresh_isolated_v1`
- This report judges the current official PDF and current single figure source only. It does not import an old P641 or other-UID conclusion.

## Frozen input identity

| Input | Bytes | SHA-256 | Status |
|---|---:|---|---|
| `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf` | 4,967,063 | `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3` | exact expected identity |
| `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex` | 3,008 | `8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15` | exact expected identity |

The official PDF has 817 physical pages. Independent current-document localization searched for the conjunction of the exact caption fragments `因子图中更新` and `Markov毯变量`; it occurs uniquely on physical page 691. The extracted printed page is 678. Page geometry is 595.276 × 841.890 pt; native grids are 1654 × 2339 at 200 dpi and 2480 × 3508 at 300 dpi.

## Actual views opened

I actually opened and reviewed:

- `full_page_200dpi.png` and `full_page_native300dpi.png`;
- `figure_crop_300dpi.png`, a native 1843 × 738 crop at full-page pixels `[295,2304,2138,3042]`;
- `standalone_300dpi.png`, a native 1472 × 596 body crop at full-page pixels `[487,2304,1959,2900]`;
- `grayscale_300dpi.png`, with geometry unchanged;
- the semantic/object and text-measurement overlays;
- all 17 text-glyph contact sheets and the one graphic contact sheet;
- all 16 critical-relation contact sheets, including native-1x and nearest-neighbor-8x evidence;
- all four exact embedded-font external punctuation calibration sheets.

No native measurement image was resized. Nearest-neighbor 8× images were used for manual viewing only and never for thresholding or pixel measurement.

## Frozen denominator and machine evidence

- Visible text glyphs: 162.
- Visible graphic/path foreground objects: 15.
- Complete visible-object denominator: `N = 177`.
- Complete unordered-pair denominator: `C = N(N-1)/2 = 15,576`.
- Critical manual-review subset: 154 relations.
- Math-rule objects: 0. The current formulas contain no overline, underline, radical bar, fraction rule, cancellation stroke, hat/vector path, or other formula rule; all visible math symbols are PDF text glyphs.
- Text masks: 162 unique, nonempty, pure glyph masks.
- Graphic masks: 15 unique, nonempty, pure foreground masks.
- Critical ROI PNGs: 924 = 154 relations × 6 required views.
- Contact sheets: 17 glyph + 1 graphic + 16 critical.
- Safe filename mapping: 177 unique IDs to 177 unique portable ordinary filenames.

Every one of the 162 glyph IDs, 15 graphic IDs, and 154 critical relation IDs has an explicit manual ledger row. The machine scripts generate geometry, masks, measurements, and pair inventories only; they do not create reviewer decisions or PASS/FAIL notes.

## Glyph and typography adjudication

All glyph contact sheets were opened. Every target matches the current PDF original, every overlay covers the target, every mask-only cell is pure, and each glyph has zero manually observed missing-stroke or foreign-pixel defect. Han, Latin, Greek, math operators, delimiters, and punctuation contain no missing character, tofu, wrong codepoint, or mathematical ambiguity.

Source-level effective sizes are 9.5 pt for node labels, the conditional formula, and the `p(alpha)` irrelevance annotation; 10.0 pt for the caption; and 9.2 pt for the Markov-blanket annotation. Under current R168/R309 policy, the explicit 9.2 pt value is advisory by itself. Native-1x and nearest-neighbor-8x review shows that this annotation is actually readable and balanced: its Chinese text, `Markov`, punctuation, and `alpha,z,y` are all complete. It creates no hard failure.

Low-profile punctuation is closed by seven calibration groups. Three comma groups have same-codepoint peers inside the figure. The four singleton groups were independently rerendered at 300 dpi by glyph index from the exact embedded PDF font program and exact PDF text size, without TeX and without saving a PDF. Current/reference ratios are:

| Codepoint | H ratio | Area ratio | Result |
|---|---:|---:|---|
| U+002E | 1.000000 | 0.976190 | within [0.92,1.08] |
| U+FF0C | 1.000000 | 1.000000 | within [0.92,1.08] |
| U+FF1A | 1.000000 | 1.031250 | within [0.92,1.08] |
| U+FF1B | 1.000000 | 1.076923 | within [0.92,1.08] |

The role/script ledger records effective size, ink-height median, D/E state, crowding, protrusion, cross-role consistency, grayscale preservation, and page fusion. No role is visually too small, too large, or abruptly imbalanced.

## Overlap, clearance, and clipping

Fourteen of 15,576 unordered pairs have at least one common foreground pixel. All fourteen are non-illegal:

- nine required graph edge-to-node-border endpoint joins;
- three graph edges intentionally crossing dashed Markov-blanket boundaries;
- one annotation arrow shaft/head composition;
- one 1-pixel antialias contact between adjacent `k` and `o` masks inside the intact word `Markov`.

The `Markov` contact is internal typography, does not erase or obscure either glyph, and remains plainly legible at native 1× and nearest-neighbor 8×. There is no overlap between independent text objects or between text/formula ink and a line, arrow, node border, or panel border.

Measured hard clearances are conservative and pass: nearest independent text-to-text ink distance 33.0151 px; nearest text-to-node-border distance 15 px; nearest text-to-line/arrow distance 20 px. The complete figure crop has a 23 px minimum foreground margin and the standalone body crop has 21 px, both above the 6 px crop-edge gate. No final-visible foreground is clipped.

## Independent mathematics and semantics

The narrow current chapter context gives

`pi(alpha,theta,z | y) proportional to p(z,y | theta) p(theta | alpha) p(alpha)`.

Conditioning on `alpha,z,y` and updating `theta`, every factor independent of `theta` is absorbed into the normalizer. Thus

`pi(theta | alpha,z,y) proportional to p(theta | alpha) p(z,y | theta)`.

Accordingly, the two factor neighbors of `theta` are exactly `p(theta | alpha)` and `p(z,y | theta)`, the displayed variable blanket is `alpha,z,y`, and `p(alpha)` is correctly shown as irrelevant to the current conditional kernel. Source topology, displayed formula, alt text, annotation, and caption agree. There is no semantic or geometric error.

## Visual harmony and hard gates

- `FONT_VISUAL_HARMONY_PASS = true` by direct manual review.
- Missing/tofu/wrong glyph or wrong math meaning: none.
- Actual unreadability or visibly severe size imbalance: none.
- True clipping: none.
- Illegal overlap: none.
- Semantic/geometric error: none.
- Grayscale hierarchy failure: none.
- Page-integration failure: none.

The 9.2 pt annotation remains advisory only; no R168 hard-failure condition is present.

## Technical validation

`machine_preseal_validation.json` reports `technical_error_count = 0`. It verifies the input hashes; N/C counts and unique IDs; 177 safe filenames; 162/15 masks; 17/1/16 contact-sheet counts; 924 critical ROI PNGs; exact manual-ledger row/ID counts; zero non-PASS manual rows; zero blank/pending manual cells; four external calibration rows with zero ratio violations; 1,170 readable PNGs; zero JSON/CSV parse errors; zero cache/pyc files; zero symlink/reparse candidates; and zero empty/solid masks.

## Isolation and mutation accounting

- Old P641 evidence/report/handoff/state/inventory/acceptance conclusion reads: 0.
- Other UID conclusion reads: 0.
- Agent/thread/task enumeration or identity/status reads: 0.
- Git commands: 0.
- TeX/LuaLaTeX/latexmk commands: 0.
- Official PDF/source/chapter writes: 0.
- Central/shared evidence or state writes: 0.
- Other UID or other-role work: 0.
- External process enumeration/management: 0.
- Two self-created command sessions were interrupted while recovering from an initial dashed-path rendering loop; no external or unrelated process was inspected or controlled.
- One superseded self-created calibration generator was removed after replacement; no user/source file was removed.

All content writes are confined to the assigned fresh evidence root.

## Decision

SA1 hard-gate decision: **PASS**.

Exact outcome token: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

This is an SA1 result only. It does not start SA3 and does not self-count a local, global, or final acceptance pass.
