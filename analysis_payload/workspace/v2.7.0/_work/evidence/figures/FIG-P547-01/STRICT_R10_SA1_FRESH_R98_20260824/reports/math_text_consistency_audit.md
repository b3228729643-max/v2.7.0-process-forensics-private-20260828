# Mathematical and text consistency audit

- Left graph is row-stochastic: A=[[0.7,0.3],[0.2,0.8]], so each row sums to 1; directed physical edge i->j is recorded by a_ij.
- Right graph is column-stochastic P=A^T=[[0.7,0.2],[0.3,0.8]], so each column sums to 1 and the same physical edge i->j is P_ji.
- Highlight mapping is exact: left a_12=0.3 maps to right P_21=0.3; the return edge a_21=0.2 maps to P_12=0.2.
- Update conventions are dimensionally and semantically correct: row vector rho advances as rho_(t+1)=rho_t A; column vector p advances as p^(t+1)=P p^(t).
- The central bridge P=A^T and a_ij=P_ji is the unique reading bridge. Directional arrows, subscripts, transpose, equality rules, brackets, and bold vector notation were checked glyph/path by glyph/path.
- Figure caption and surrounding paragraph describe the same row-to-column transpose and do not introduce a competing conclusion.

RESULT: true
