# FIG-P654-01｜R15 fresh isolated SA1 formal report

## Verdict

`SA1_FAIL_TO_SA2`

This SA1 does not request SA3 and does not claim `A_LOCAL_PASS`. Six frozen-taxonomy D/E glyph-to-median hard failures remain, even though source font size, per-class hard pixel minima, geometry, overlap, clipping, semantics, grayscale, and page integration otherwise pass.

## Official candidate binding

- Role instance: `A-R102-P654-SA1-FRESH-20260825`
- Main commit identity: `94d1b62b877e80000539879688e6209c09882833`
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r102_fullbook\main_full.pdf`
- PDF identity: 817 pages, all A4 (`595.276 × 841.890 pt`), 4,958,396 bytes
- PDF SHA-256: `60026DE5A4168D6F3B304D1AE59BE68E1F570CD22D992E43FCAD9828E25A1397`
- Target page: physical 704, printed 691
- Figure source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- Source identity: 3,122 bytes; SHA-256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- Native 300 dpi full-page grid: `2481 × 3508 px`
- Integer figure crop in full-page native pixels: `[291,250,2230,875]`; dimensions `1939 × 625 px`
- The 300 dpi measurement crop was rendered directly from the official PDF and was never resized. The 8× images are nearest-neighbour review aids only.

## Closed denominators

- PDF-visible glyphs: 95/95
- Visible foreground drawing/path objects: 21/21, including eight final-visible node borders, seven relation shafts, five arrowheads, and one fraction `GRAPHIC/MATH_RULE`
- Total objects: 116/116
- All unordered pairs: 6,670/6,670; no sampling
- Critical relations with raw/A/B/intersection/overlay/native 1×/8× evidence: 121/121
- Human reviewer ledger: glyph 95/95; graphic 21/21; pair 6,670/6,670; view 5/5
- Glyph/graphic/critical contact sheets actually opened: 5/2/11
- All-pair matrix blocks actually opened: 4/4
- Low-profile punctuation denominator: 0; calibration denominator: 0. The frozen pre-measurement taxonomy found no target punctuation glyph of that class, so calibration is closed `N/A`, not silently omitted.
- Cross-panel denominator: 0 because this is one panel; the `N/A` is explicit.

## Exact hard failures

The frozen grouping key is `PANEL_ID + ROLE + SCRIPT_CLASS`; it was fixed before pixel measurement and was not split by exact glyph after seeing the results.

| ID | Glyph | Parent | Frozen role/class | H ink | Frozen median | Ratio | Gate |
|---|---:|---|---|---:|---:|---:|---|
| `G0005` | `𝑛` | `N_TRIAL_FORMULA` | `FORMULA_BLOCK/BASE_MATH` | 22 px | 24 px | 0.916666666667 | FAIL, `<0.92` |
| `G0014` | `t` | `N_GAMMA_BODY_1` | `NODE_BODY/LATIN_LOWER_GREEK` | 27 px | 22 px | 1.227272727273 | FAIL, `>1.08` |
| `G0042` | `+` | `N_POSTERIOR_FORMULA` | `FORMULA_BLOCK/BASE_MATH` | 29 px | 24 px | 1.208333333333 | FAIL, `>1.08` |
| `G0061` | `+` | `N_PREDICTIVE_FRAC_NUM` | `FORMULA_BLOCK/BASE_MATH` | 29 px | 24 px | 1.208333333333 | FAIL, `>1.08` |
| `G0066` | `+` | `N_PREDICTIVE_FRAC_DEN` | `FORMULA_BLOCK/BASE_MATH` | 29 px | 24 px | 1.208333333333 | FAIL, `>1.08` |
| `G0067` | `𝑁` | `N_PREDICTIVE_FRAC_DEN` | `FORMULA_BLOCK/BASE_MATH` | 33 px | 24 px | 1.375000000000 | FAIL, `>1.08` |

Each failing target was opened independently at native 1× and 8× nearest-neighbour. Its original contour, red target overlay, and mask-only view agree; missing-stroke and foreign-pixel counts are both zero. Therefore these are not empty masks, contamination, clipping, or ownership ambiguity and cannot be reclassified away in SA1.

## Other strict gates

- Source declarations: ordinary text 10.1 pt, trial bold formula 10.7 pt, posterior/predictive formulas 11.6 pt; accumulated graphics scale 1.0. No `resizebox`, `scalebox`, `transform shape`, or overall text shrinkage. `SOURCE_FONT_PASS=true`.
- Every glyph meets its absolute class pixel-height minimum. `PIXEL_HEIGHT_PASS=true`.
- Same-role extreme and role-to-base checks pass under the frozen taxonomy; `ROLE_RATIO_PASS=true`.
- Illegal native-pixel overlap: 0; all 6,670 pair decisions PASS after ownership whitelist for same-formula and designed edge/node connections.
- Clip pixels: 0.
- Minimum independent text–text vector-bbox clearance: 4 px (gate 4).
- Minimum text/formula–graphic raw-mask clearance: 5 px (gate 3).
- Minimum owned node-text–final-visible-border clearance: 18 px (gate 5).
- The one fraction rule is a nonempty `GRAPHIC/MATH_RULE` object, enters the object and pair denominators, and is whitelisted only against components of its own fraction.
- The two native antialias-fringe pixels outside PDF glyph bboxes were each assigned to one unique nearest bbox within 4 px solely for ownership closure; coordinates and target IDs are in provenance. This rule did not relax typography, clip, border, overlap, or clearance gates; an equal-distance ambiguity would have hard-failed.
- `FONT_VISUAL_HARMONY_PASS=true`, `MATH_SEMANTICS_PASS=true`, `TEXT_CONSISTENCY_PASS=true`, `GRAYSCALE_PASS=true`, and `PAGE_INTEGRATION_PASS=true`. These visual passes do not override the six D/E hard failures.

## Evidence and sealing

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R15_SA1_FRESH_R102_20260825`
- Payload manifest rows: 1,494
- Final ordinary-file denominator: 1,497
- Named ADS / `.pyc` / `__pycache__` directories / colon-containing filenames: `0 / 0 / 0 / 0`
- `PAYLOAD_MANIFEST.json` SHA-256: `303D679FFC4F304E2B59BFAC734F68E91D821FB1ACC8688C63DC2B59D0561A9A`
- `SHA256_MANIFEST.csv` SHA-256: `9FE57DD5EEE30F9DEEABAB170F915633C7CDF237A9EE10502D90A3DAC4B077B2`
- Every payload JSON/CSV/PNG/ordinary file was parsed or opened before sealing.
- `WRITE_STOPPED.md` was the strict latest content write. The evidence root was then made fully read-only. No post-seal write, script execution, or import occurred in that root.

## SA2 routing

SA2 must address the six exact D/E IDs above without weakening the frozen strict gates. Any new candidate requires a new official full-book build and a wholly fresh SA1 evidence root; this failed evidence must not be promoted to SA3 or `STRICT_FINAL`.
