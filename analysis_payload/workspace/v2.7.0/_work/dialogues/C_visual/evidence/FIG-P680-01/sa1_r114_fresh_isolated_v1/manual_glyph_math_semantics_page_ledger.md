# Post-observation glyph, math, semantics, and page ledger

## Glyph denominator

`frozen_reader_visible_glyphs.csv` freezes 212 current-PDF glyphs. Each glyph ID was reviewed in the native 300 dpi figure+caption crop; the critical branch/glyph region was additionally opened at native 1x and nearest-neighbor 8x.

| Object | Glyph IDs | Count | Post-observation |
|---|---:|---:|---|
| T01 | G001–G016 | 16 | all present and readable |
| T02 | G017–G030 | 14 | all present and readable |
| T03 | G031–G034 | 4 | all present and readable |
| T04 | G035–G044 | 10 | all present and readable |
| T05 | G045–G053 | 9 | all present and readable |
| T06 | G054–G061 | 8 | all present and readable |
| T07 | G062–G068 | 7 | all present and readable |
| T08 | G069–G072 | 4 | all present and readable |
| T09 | G073–G079 | 7 | all present and readable |
| T10 | G080–G086 | 7 | all present and readable |
| T11 | G087–G093 | 7 | all present and readable |
| T12 | G094–G101 | 8 | all present and readable |
| T13 | G102–G122 | 21 | all present and readable |
| T14 | G123–G127 | 5 | all present and readable |
| T15 | G128–G172 | 45 | all present and readable |
| T16 | G173–G212 | 40 | all present and readable |

Special-codepoint checks: `G003=U+201C`, `G012=U+201D`; `G006/G009/G136/G139=U+2013`, the expected visible en dash produced by TeX `--`; `G045/G084=U+1D703` (mathematical italic theta); `G047/G062/G086=U+1D711` (mathematical italic phi). Replacement-character count is 0. Visual inspection found no tofu box, missing glyph, wrong codepoint, duplicated glyph, or broken combining mark.

## Math ledger

| ID | Object/glyphs | Independent check | Post-observation |
|---|---|---|---|
| M01 | T05 / G045–G053 | Full Bayes LDA treats document-topic `θ` and topic-word `φ` as random variables. | correct |
| M02 | T07 / G062–G068 | The point-parameter variant treats `φ` as an estimated parameter while retaining local latent structure. | correct |
| M03 | T10 / G080–G086 | Collapsed Gibbs integrates out `θ,φ` and updates topic assignments from collapsed counts. | correct |
| M04 | T11–T12 / G087–G101 | Mean-field variational EM alternates local variational updates with parameter updates and performs ELBO coordinate ascent. | correct |
| M05 | T13 / G102–G122 | The two routes target different posterior/parameter objects, so algorithm-name-only comparison is invalid. | correct |

## Semantic and geometry ledger

| ID | Check | Post-observation |
|---|---|---|
| S01 | Shared structure | Both routes share the conditional document–topic–word factorization and bag-of-words counting structure. |
| S02 | Full Bayes route | `N01 → N02 → N04` correctly maps shared structure to full Bayes LDA and then collapsed Gibbs. |
| S03 | Point-parameter route | `N01 → N03 → N05` correctly maps shared structure to a point-parameter LDA variant and then mean-field VEM. |
| S04 | Arrow meaning | Arrows encode learning/inference dependency, not generative time and not equality of posterior distributions. |
| S05 | Direction | All four arrowheads point from prerequisite/model target toward the corresponding downstream model/inference method. |
| S06 | Route encoding | Left route uses solid teal; right route uses dashed gold/open arrowhead, so the routes remain distinguishable in grayscale. |
| S07 | Warning | N06 prevents the specific misconception that identical algorithm names imply comparable posteriors. |
| S08 | Caption | T14–T16 exactly summarize the two routes and repeat the arrow-semantics limitation without contradiction. |

## Page ledger

| ID | Check | Post-observation |
|---|---|---|
| PG01 | Current location | Unique caption text locates the figure on physical PDF page 729, printed page 716. The legacy UID page number is not used as current location evidence. |
| PG02 | Full-page integration | The figure sits after the dependency box and before the data-direction bridge with balanced whitespace. |
| PG03 | Figure/caption | Figure and two-line caption are centered, complete, and do not collide. |
| PG04 | Grayscale | Solid/dashed line styles and the warning bar remain legible; no route depends on color alone. |
| PG05 | Clip | Text, borders, strokes, arrowheads, caption, and page content have 0 clipped visible pixels. |
| PG06 | Visual balance | Symmetric two-column layout, aligned row labels, subordinate warning strip, and restrained caption show no severe imbalance. |
