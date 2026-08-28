# Manual visible-object denominator freeze

The subject denominator is frozen at **25 composite visible semantic objects**. Composite nodes include their fill, border, and contained text because they are perceived as one node; the separate 21-row text ledger still checks every text-bearing component against its border and neighboring graphics. This prevents double-counting an intended node as several unrelated semantic objects while preserving text/border scrutiny.

| ID | Visible semantic object |
|---|---|
| O01 | `Y_1` Gamma input node |
| O02 | `Y_2` Gamma input node |
| O03 | vertical continuation ellipsis |
| O04 | `Y_K` Gamma input node |
| O05 | step badge 1 |
| O06 | common-rate independence note |
| O07 | total/sum node |
| O08 | step badge 2 |
| O09 | divide-by-`S` operator node |
| O10 | normalized-ratio node |
| O11 | step badge 3 |
| O12 | Dirichlet result node |
| O13 | simplex triangle and interior point icon |
| O14 | simplex-point note |
| O15 | total/proportion independence result node |
| O16 | `K=2` Beta special-case node |
| O17 | main arrow `Y_1 -> S` |
| O18 | main arrow `Y_2 -> S` |
| O19 | main arrow `Y_K -> S` |
| O20 | main arrow `S -> divide` |
| O21 | main arrow `divide -> ratio` |
| O22 | main arrow `ratio -> Dirichlet` |
| O23 | dashed evidence path `S -> independence result` |
| O24 | dashed evidence path `ratio -> independence result` |
| O25 | figure label and complete two-line caption |

All `25 choose 2 = 300` unordered pairs are enumerated in `machine_all_unordered_pairs.csv` and manually adjudicated per ID in `manual_pair_ledger.md`. No object was added or removed after this freeze.
