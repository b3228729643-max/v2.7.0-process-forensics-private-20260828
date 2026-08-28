# FIG-P657-01 independent semantic, geometry, caption, and alt-text review

## Independent recomputation

This review used only the current figure source, official R111 page 706 (printed folio 693), and the narrowly read V5-C05 context at the figure call site. It was written after opening the native figure/page/ROI evidence.

1. For `K=2`, a Dirichlet vector is `(theta_1, theta_2)` with `theta_2=1-theta_1`; its density reduces to `theta_1^(alpha_1-1)(1-theta_1)^(alpha_2-1)`, exactly the Beta family. Thus the general-to-special arrow Dirichlet→Beta is correct.
2. For `K=2`, a multinomial count vector is `(x,N-x)` and its mass is proportional to `p^x(1-p)^(N-x)`, exactly the binomial family. Thus multinomial→binomial is correct.
3. Setting `N=1` in the multinomial leaves one categorical outcome. Thus multinomial→categorical is correct.
4. Setting `N=1` in the binomial leaves a Bernoulli outcome. Thus binomial→Bernoulli is correct.
5. Setting `K=2` in the categorical family leaves a two-outcome Bernoulli variable. Thus categorical→Bernoulli is correct.
6. A Dirichlet prior contributes `prod_k theta_k^(alpha_k-1)` and a multinomial likelihood contributes `prod_k theta_k^n_k`; multiplication gives `Dirichlet(alpha+n)`. The thick Dirichlet→multinomial arrow therefore denotes conjugate prior/likelihood, not set inclusion.
7. A Beta prior contributes `p^(alpha-1)(1-p)^(beta-1)` and a binomial likelihood contributes `p^x(1-p)^(N-x)`; multiplication gives `Beta(alpha+x,beta+N-x)`. The thick Beta→binomial arrow is the second correct conjugacy relation.

## Per-object manual judgments

- O01 `先验族`: correct row label for Dirichlet and Beta; left alignment and emphasis identify role without entering node/edge space.
- O02 `Dirichlet分布`: correct general prior-family node; no false independence claim is made inside the node.
- O03 `Beta分布; K=2`: correct two-parameter special case of Dirichlet; `K=2` is visibly bound to the Beta node.
- O04 `似然族`: correct row label for multinomial and binomial families.
- O05 `多项分布`: correct general likelihood-family node and correct target of the Dirichlet conjugacy arrow.
- O06 `二项分布; K=2`: correct two-category multinomial special case and correct target of the Beta conjugacy arrow.
- O07 `单次试验`: correct row label for categorical and Bernoulli single-trial distributions.
- O08 `类别分布; N=1`: correct one-trial multinomial special case; the `N=1` qualifier is legibly inside the node.
- O09 `Bernoulli分布; K=2,N=1`: correct intersection of the two-category and one-trial specializations.
- O10 Dirichlet→multinomial: correct downward conjugacy direction from prior family to likelihood family; thick filled arrow ends at node boundaries and does not cross text.
- O11 Beta→binomial: correct downward conjugacy direction and same geometry/weight as O10.
- O12 Dirichlet→Beta: correct left-to-right general-to-special direction; thin open arrow and label `特殊情形` distinguish it from conjugacy.
- O13 multinomial→binomial: correct left-to-right general-to-special direction with the same thin/open encoding as O12.
- O14 multinomial→categorical: correct downward specialization labeled `N=1`; line is thin/open and label is offset, so it cannot be mistaken for O10.
- O15 binomial→Bernoulli: correct downward specialization labeled `N=1`; line weight and arrowhead are visibly different from O11.
- O16 categorical→Bernoulli: correct left-to-right specialization labeled `K=2`, with no crossing or ambiguous endpoint.
- O17 conjugacy legend sample: thick blue line with filled arrowhead matches O10/O11. In grayscale the greater stroke width and filled tip remain visible.
- O18 special-case legend sample: thin gray line with open arrowhead matches O12--O16. It remains distinct from O17 in grayscale without relying on hue.
- O19 caption: names all five special-case relations and the conjugacy interpretation accurately. The explicit clause `粗箭头表示共轭先验而不是集合包含` blocks the principal ambiguity.

## Source, caption, alt text, and page integration

- The source caption and the rendered two-line caption state the same single reading conclusion; spelling and Latin distribution names `Beta`, `Dirichlet`, and `Bernoulli` are consistent.
- The source `alt={对象—关系—结论：...}` contains the same six distributions, five special-case assertions, and the thick-arrow conjugacy warning as the caption. The alt prefix adds structure but changes no mathematical content.
- Narrow V5-C05 context states that the figure distinguishes categorical/multinomial, Bernoulli/binomial, and Dirichlet/Beta dimensional relations and conjugacy, matching the diagram. The later local clarification that a two-dimensional Dirichlet is Beta, not independent components, is not contradicted by the figure.
- Full-page 200/300 dpi and page-integration views show the figure following its introducing paragraph and preceding section 34.2 with balanced whitespace. There is no orphan caption, large anomalous blank block, page-edge clipping, or collision with adjacent text.
- Reading order is unambiguous: read rows top-to-bottom for prior→likelihood→single-trial structure, left-to-right for general→special relations, and use the right legend to distinguish thick conjugacy from thin specialization.

Hard semantic/geometry defects found: none.
