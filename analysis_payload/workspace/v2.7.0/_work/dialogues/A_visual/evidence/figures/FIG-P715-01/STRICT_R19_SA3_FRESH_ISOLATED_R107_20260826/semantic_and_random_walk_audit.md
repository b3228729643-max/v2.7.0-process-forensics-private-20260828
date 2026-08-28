# Mathematical and random-walk semantic audit

The left graph has exactly four directed edges: `i→j`, `j→i`, `j→h`, and `h→i`. Arrowheads are at the correct destination-node borders, and the reciprocal `i↔j` edges remain visually distinct.

With row/column order `(i,j,h)` and the convention `A_ij>0 ⇔ j→i`, the displayed adjacency matrix is

`A = [[0,1,1],[1,0,0],[0,1,0]]`.

Its column sums are `(c_i,c_j,c_h)=(1,2,1)`. Dividing each nonzero column by `c_j` gives

`M = [[0,1/2,1],[1,0,0],[0,1/2,0]]`,

so every column sums to one and the displayed identities `M_:j=A_:j/c_j`, `1^T M=1^T`, and `p^(t+1)=Mp^(t)` are mutually consistent.

The right panel displays the transpose

`P=M^T=[[0,1,0],[1/2,0,1/2],[1,0,0]]`.

Therefore `P_ji=M_ij=Pr(X_(t+1)=i | X_t=j)`, `P1=1`, `rho_(t+1)=rho_t P`, and `rho_t=(p^(t))^T` are all correct under the same node order. The three orange focus frames select `A_ij=1`, the corresponding normalized `M_ij=1/2`, and the transposed `P_ji=1/2`.

The visible `1/2` entries are slash-form fractions, not missing fraction-bar graphics. No overbar, radical bar, fraction rule, or other mathematical rule object is expected or absent. No wrong symbol, wrong index, wrong matrix entry, reversed direction, or random-walk semantic error was found.

`MATH_SEMANTICS_PASS=true`  
`GRAPH_GEOMETRY_PASS=true`  
`MATRIX_CONTENT_PASS=true`  
`RANDOM_WALK_CONVENTION_PASS=true`
