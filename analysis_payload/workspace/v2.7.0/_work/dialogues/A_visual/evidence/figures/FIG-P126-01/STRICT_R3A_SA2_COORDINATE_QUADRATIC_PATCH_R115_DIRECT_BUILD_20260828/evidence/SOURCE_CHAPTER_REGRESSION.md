# P126 R3A source/chapter regression

- Official standalone candidate: `build/v260_FIG-P126-01_standalone.pdf`, 33,952 bytes, SHA-256 `19F221487DB1930170608EAE0E09F019313791D808C724D05DBAC23465F746B2`.
- Frozen source: 4,224 bytes, SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`.
- Current V1-C08 chapter: 59,218 bytes, SHA-256 `3C60FABCACA8BFC390323033F3CF6539CA5497EBF5A09641B8C4B78E81A0816C`.
- The shared contour expression has Hessian `[[1,1],[1,2]]`, determinant 1 and positive eigenvalues approximately 0.381966 and 2.618034. The contour principal axes are therefore rotated relative to `x_1/x_2`.
- The rendered q0--q7 path alternates vertical and horizontal coordinate updates. Each updated coordinate satisfies its corresponding zero partial derivative. Objective values are 2.92, 2.56, 1.28, 0.64, 0.32, 0.16, 0.08 and 0.04.
- The true optimum remains `x^*=(0,0)` while q7 is visibly a distinct approximation.
- The source caption and alt text retain the statement that every substep changes one coordinate and that the axis-aligned polyline approaches the optimum. This agrees with V1-C08 lines 338--353.
- The standalone wrapper does not typeset the book caption on its one-page PDF; caption/chapter consistency was therefore checked against the exact current source and exact current chapter rather than inferred from absent standalone text.
- Hard regression: source lines 63--66 assign a solid sample to `x_1` and a dashed sample to `x_2`, but native grayscale and nearest8x evidence render both legend swatches as one continuous horizontal run. This is a semantic role failure and not an R168 font/pixel advisory.

