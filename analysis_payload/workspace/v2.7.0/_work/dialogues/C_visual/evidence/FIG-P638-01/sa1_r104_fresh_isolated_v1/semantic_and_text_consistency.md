# Formula, relation, object-content, and text consistency review

## Mathematical semantics

The upper path presents the correct special case of a single-coordinate Metropolis–Hastings update:

1. Propose from the exact full conditional, `q_j = pi(x_j | x_{-j})`.
2. With `y_{-j}=x_{-j}`, the displayed ratio
   `R = pi(y) pi_j(x_j|x_{-j}) / [pi(x) pi_j(y_j|x_{-j})]`
   cancels to 1.
3. Therefore `alpha=1` and the accepted coordinate assignment is `x_j <- y_j`.

The lower exception node correctly says that an approximate full conditional or another proposal must restore the MH acceptance-rate correction, and rejection retains `x_j` as a self-loop. It does not claim that an approximate proposal is automatically accepted.

## Object and relation review

- Four source nodes are present: q, r, a, and w.
- Four source draw paths are present: the q-r-a main flow, the horizontal separator, and two downward warning branches.
- The main path is left-to-right. Although the TikZ path has a terminal arrowhead rather than an arrowhead on each segment, numerals 1, 2, and 3 plus the terminal right arrow make the order unique.
- Both red dashed warning branches point downward into the exception node and do not reverse the implication.
- The pale divider is non-semantic structure; intentional warning-arrow crossings do not hide a relation.
- The fraction rule, node border, arrowheads, and separator are complete; no object is clipped or replaced by a placeholder.

## Source/PDF/body/caption consistency

- Current source label: `fig:V5-C04-gibbs-vs-mh`.
- Current source caption equals the R104 caption in meaning and content.
- The immediately preceding R104 paragraph states `y_{-j}=x_{-j}`, exact full-conditional proposals are always accepted, and approximate/other proposals require MH correction; this is exactly the diagram's content.
- The immediately following figure-aid paragraph assigns Figure 33.5 the role of contrasting exact conditional proposals with general proposals; the diagram does that and does not duplicate the roles of Figures 33.3/33.4.
- Variable names and directions are consistent across source, diagram, caption, and body: q_j, pi, x_j, y_j, x_{-j}, R, alpha, and the assignment arrow all have the expected codepoints and positions.

Conclusion: no mathematical, relationship, formula, object-content, caption, or neighboring-text inconsistency was found.
