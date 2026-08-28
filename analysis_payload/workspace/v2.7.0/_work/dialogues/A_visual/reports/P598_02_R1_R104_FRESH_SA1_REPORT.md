# FIG-P598-02 R104 fresh isolated SA1 report

## Assignment identity

- HANDOFF_ID: `A-R104-P598-02-SA1-FRESH-20260826`
- instance: `/root/p598_02_r104_fresh_sa1`
- model/effort: `gpt-5.6-sol/xhigh`
- figure UID: `FIG-P598-02`
- formal evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826`
- isolation: no prior P598-02/P598-01 or other forbidden evidence, state, inventory, acceptance history, dialogue conclusions, or git history was read.

## Candidate and render

The inspected candidate is the official frozen R104 full book, physical page 650: 4,967,222 bytes, SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`, 817 pages. The native 300 dpi page is 2481 x 3508 px; the 200 dpi whole-page context is 1654 x 2339 px. The figure-body crop is `[471,272,2056,807]`, and the standalone figure-plus-caption crop is `[294,272,2234,940]`.

## Denominators and machine checks

- visible glyphs: 137
- visible graphics: 26, including the fraction rule and widehat accent
- total objects: `N=163`
- all unordered pairs: `C=13,203=C(163,2)`
- critical/relationship cases: 22
- hard-applicable pair checks: 9,836, failures 0
- empty masks: 0
- final-visible overlap pixels: 0
- clip pixels: 0
- minimum body and standalone crop clearance: 11 px
- PDF drawing/path coverage: 30/30
- ordinary PNGs machine-opened: 288
- ADS: 0 non-default streams
- pyc/cache: 0

Fifteen pre-occlusion intended shared relations totaling 261 pixels are preserved in the ownership ledger. Final-visible masks assign those pixels by actual paint order; they do not create a reader-visible illegal overlap.

## Manual visual checks

The reviewer opened the native figure, standalone, grayscale, 200 dpi and 300 dpi whole-page views; all 12 glyph sheets; all 7 graphic sheets; all 4 critical overlays; the all-pair matrix; text index; semantic overlay; and page-integration overlay.

- glyph manual denominator: 137/137 PASS
- graphic manual denominator: 26/26 PASS
- critical relationship manual denominator: 22/22 PASS
- view ledger: 15/15 PASS
- panel/role/script ledger: 24/24 PASS
- R168 hard-font gate ledger: 6/6 PASS
- semantic ledger: 13/13 PASS

All target masks match their original rendering, are complete, and remain pure. Missing-stroke/graphic pixels and foreign pixels are both zero.

## R168 adjudication

The source roles below 9.5 pt and four fine pixel-threshold shortfalls are advisory under R168. At native 300 dpi and 8x nearest-neighbor review, none is missing/tofu, wrong in codepoint or math meaning, genuinely unreadable, severely imbalanced, clipped, or overlapped. `FONT_VISUAL_HARMONY_PASS=true`.

## Semantics and integration

All required semantics are visible and correct: three ordered cards; two flow arrows; `pi K = pi`; x/y bidirectional kernel illustration; a hatched and discarded warm-up region; a separately retained chain segment; retained-sample dots; `I-hat_{m,n}=1/n sum_{t=m+1}^{m+n} h(X_t)`; and caption meaning `E_pi[h(X)]`. Curve, dashed divider, dots, borders, arrow continuity, clearance, crop, grayscale, and full-page integration pass.

## Verdict

`SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`

The evidence root is sealed exactly once with two complete cross-checked payload manifests (`MANIFEST.json` and `MANIFEST.sha256`), `SEAL.json`, and a strictly-latest `WRITE_STOPPED` marker. All root files are read-only after sealing; post-seal mutation count is zero.

No source was edited, no TeX engine was invoked, and no commit, state/inventory, second UID, or business-writer action occurred.
