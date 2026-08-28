# Mathematical and textual semantic audit

The source replaces only the raster-poor *glyph forms* of twelve equality signs
and three right arrows.  Each replacement is a real TikZ path in the same
`\mathrel` position; operands, order, indices, probabilities and direction are
unchanged.

| relation | source context after repair | semantic identity preserved |
|---|---|---|
| EQ01 | left title `a_ij [geom =] P(i [geom →] j)` | definition of row-random entry |
| EQ02 | left focus `a_12 [geom =] 0.3` | highlighted edge probability |
| EQ03 | left return `a_21 [geom =] 0.2` | reverse-edge probability |
| EQ04 | `A [geom =] [[0.7,0.3],[0.2,0.8]]` | full row-random matrix |
| EQ05 | `rho_(t+1) [geom =] rho_t A` | row-vector update |
| EQ06 | `P [geom =] A^T` | transpose bridge |
| EQ07 | `a_ij [geom =] P_ji` | same physical-edge probability under the two conventions |
| EQ08 | right title `P_ji [geom =] P(i [geom →] j)` | definition of column-random entry |
| EQ09 | right focus `P_21 [geom =] 0.3` | highlighted edge probability |
| EQ10 | right return `P_12 [geom =] 0.2` | reverse-edge probability |
| EQ11 | `P [geom =] [[0.7,0.2],[0.3,0.8]]` | full column-random matrix |
| EQ12 | `p^(t+1) [geom =] P p^(t)` | column-vector update |
| AR01 | left title `i [geom →] j` | directed edge from `i` to `j` |
| AR02 | bridge `i [geom →] j` | the same physical directed edge |
| AR03 | right title `i [geom →] j` | directed edge from `i` to `j` |

The former phrase `同一条` was changed to `物理边`; this removes the low-stroke
CJK glyph `一` without deleting information.  The complete bridge now reads
`物理边 i→j：a_ij=P_ji`, which states the same mapping more directly.

The candidate matrices remain `A=[[0.7,0.3],[0.2,0.8]]` and
`P=A^T=[[0.7,0.2],[0.3,0.8]]`; row/column sums remain one.  The direct body and
caption state the same transpose convention and update equations.

The caption word `PageRank` remains ordinary `STIXTwoText-Regular` prose.
Its final `n` is classified as `PROSE_LATIN_X_HEIGHT` (17 px gate), not as a
baseline mathematical character (22 px gate); no font enlargement or bolding
was retained.

Semantic mapping and body/caption consistency: **PASS_TO_LOCAL_PIXEL_GATES**.
