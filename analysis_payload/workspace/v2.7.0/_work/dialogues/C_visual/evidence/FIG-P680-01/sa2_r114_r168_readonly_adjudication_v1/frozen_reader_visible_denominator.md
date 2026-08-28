# Frozen reader-visible denominator

The denominator was frozen before manual adjudication from the current R114 page, current figure source, caption, extracted glyphs, and current vector drawings. It contains 25 reader-visible semantic objects: 15 text objects and 10 graphic objects. Caption label and caption body are included.

| ID | class | frozen object |
|---|---|---|
| T01 | text | shared conditional-structure heading |
| T02 | text | shared-structure subtitle |
| T03 | text | row label “模型目标” |
| T04 | text | “完整 Bayes LDA” |
| T05 | text/math | “theta, phi 均为随机变量” |
| T06 | text | “点参数 LDA 变体” |
| T07 | text/math | “phi 作为待估参数” |
| T08 | text | row label “推断方法” |
| T09 | text | “折叠 Gibbs” |
| T10 | text/math | “积分消去 theta, phi” |
| T11 | text | “平均场变分 EM” |
| T12 | text/math | “ELBO 坐标上升” |
| T13 | text | posterior-comparison warning |
| T14 | text | caption label “图 35.1” |
| T15 | text | complete two-line caption body |
| G01 | graphic | shared-structure node container |
| G02 | graphic | full-Bayes node container |
| G03 | graphic | point-parameter node container |
| G04 | graphic | collapsed-Gibbs node container |
| G05 | graphic | variational-EM node container |
| G06 | graphic | solid teal shared-to-full arrow |
| G07 | graphic | dashed gold shared-to-point arrow |
| G08 | graphic | solid teal full-to-Gibbs arrow |
| G09 | graphic | dashed gold point-to-VEM arrow |
| G10 | graphic | warning node container |

The canonical object order is `T01..T15,G01..G10`. All unordered pairs in that order are frozen in `machine/all_unordered_pairs_geometry.csv`. Count: `C(25,2)=300`; the machine row count and independently computed expected count are both 300.

No title, row label, node line, mathematical symbol line, warning, caption component, node boundary, or learning-dependency arrow visible to a reader was omitted.

