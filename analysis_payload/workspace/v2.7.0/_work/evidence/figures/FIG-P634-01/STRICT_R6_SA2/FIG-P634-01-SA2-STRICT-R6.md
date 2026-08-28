# FIG-P634-01 SA2 strict R6 local repair report

## Disposition

**LOCAL SA2 CANDIDATE PASS — NOT A FORMAL FIGURE ACCEPTANCE.**

The sole authorized business source has been repaired and the locally built candidate clears the requested A/B/C/D/E, separated-geometry, clipping, edge, semantic, and visual-coordination checks.  Root must now build a new official whole-book candidate and obtain independent validation; this report does not promote its local PDF to official status.

## Reproduced R5 failure baseline

The supplied R5 SA1 and root-validation evidence consistently records:

- 11 visible literal CJK `一` raw-pixel failures.
- D failures: 23.
- E failures: 3.
- EL-035 legal script in `x^{[j]}` to first state-card final-visible border: 2.162px.
- Overlap 0 and clip 0 before repair.

## Authorized source changes

Only `fig_v5_c04_coordinate_sweep.tex` was edited.  Changed lines are `16–17`, `21–25`, `35–42`, `45`, `47`, `49`, `56`, and `61`.  Exact hunks are in `source_diff.patch`; semantic justification is in `SOURCE_DIFF_AND_SEMANTIC_PRESERVATION.md`.

- All source and visible literal CJK `一` instances are removed through natural equivalent wording.
- Exact `1,2,…,j−1,j,j+1,…,d`, `x^[j]`, and `x^[d]=x^(t)` semantics remain in alt/state content.
- The only geometry change is first-card title `y=-1.25 -> -1.34`.
- No font was reduced; minimum ordinary explicit base remains 9.6pt.
- No new mask, white patch, occlusion, clipping path, opacity manipulation, or public style change was introduced.

## Local build and render

- LuaLaTeX: figure-only and A4 context wrappers, two successful passes each.
- Local page: one A4 page, `595.276 x 841.890pt`.
- Direct native render: `2481 x 3508` at 300 dpi, no resizing.
- Direct 200 dpi cross-check: `1654 x 2339`.
- Font chain: embedded/subsetted/Unicode Noto Sans SC Bold, Noto Serif SC ExtraLight, STIX Two Math, and STIX Two Text.
- Final logs have no fatal error, undefined reference, missing character, overfull box, or underfull box.

## Strict local machine results

| Item | Result |
|---|---:|
| Literal glyphs | 193 |
| Semantic text elements | 58 |
| Graphics/background objects | 39 |
| Pair objects | 97 |
| Exhaustive unordered pairs | 4656 / 4656 |
| Literal CJK `一` | 0 |
| Raw glyph failures | 0 |
| Semantic-element pixel failures | 0 |
| D failures | 0 |
| E failures | 0 |
| Cross-panel same-role/script failures | 0 |
| Pair failures | 0 |
| Overlap failures | 0 |
| Clearance failures | 0 |
| Clip objects | 0 |
| Edge failures | 0 |
| Empty final-visible graphic masks | 0 |
| Complete critical-pair packs | 17 / 17 |

### Raw pixel classes

| Script class present | Raw height range | Gate | Status |
|---|---:|---:|---|
| CJK full-width | 33–42px | >=30px | PASS |
| Latin uppercase/digit | 28px | >=24px | PASS |
| Math digit | 26px | >=24px | PASS |
| Math lowercase | 20px | >=17px | PASS |
| Legal TeX script | 24–37px | >=15px | PASS |

There is no independent visible base/operator/fraction object in this figure candidate requiring the 22px class gate; no cross-class substitution was used.

### D and E

- D: 52 rows across 21 same-panel + same-role + same-script groups; failure 0.  No exact-glyph grouping and no cross-script grouping.
- E: 21 role rows; 14 PASS and 7 schema-valid N/A; failure 0.  N/A is used only where no genuine same-script NODE_LABEL BASE exists or the caption role has no Goal-defined BASE.
- Cross-panel same-role/same-script: source ratio `<=1.05` and raw-median ratio `<=1.10`; failure 0.  The two comparable formula classes have source ratio 1.0000, while raw ratios are 1.0000 (math lowercase) and 1.0411 (legal script).
- Panel-title CJK ratio is 1.2000 within `[1.05,1.20]`; all comparable CJK/digit roles and card roles remain within their required bands.

### Separated final-visible geometry

| Relation | Minimum measured gap | Gate |
|---|---:|---:|
| Text-text | 15px | >=4px |
| Cross-panel text-text | 36px | >=8px |
| Text-line/arrow | 13.036px | >=3px |
| Text-border | 8px | >=5px |
| Text-final-visible texture | 6px | >=3px |

EL-035 targeted measurements:

- Full legal script `[j]` element to first-card final-visible border: 16px.
- Literal math `j` to the same border: 18px.
- Both exceed the 5px hard gate and the 8px design objective.  Overlap is zero.

All geometry uses independent 1:1 raw masks from `renders/local_page_300dpi.png`; 8x packs are nearest-neighbour human-review witnesses only.

## Human review

Whole page, whole figure, grayscale, overlay, and EL-035 1:1/8x packs were inspected.  The eight slots remain aligned, color/grayscale grouping remains readable, card partitions stay balanced, the shifted title has natural whitespace, caption wrapping is balanced, and Noto/STIX coordination matches the page.  Mathematical and textual consistency is documented separately in `MATH_TEXT_CONSISTENCY.md`.

## Required next action

Stop SA2 writes.  Root should build a new official whole-book candidate from the edited source, locate FIG-P634-01 independently in that PDF, rerun the strict official 300 dpi audit, and commission independent figure validation.  Local page coordinates and page number must not be treated as official evidence.
