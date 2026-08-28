# Fresh localization and semantic closure

The current figure source supplies the unique visible strings `移除当前词位`, `从两张计数表各减一`, and the current caption beginning `折叠Gibbs更新先临时移除当前词位`. A full text pass over the frozen PDF found those current strings on physical page 737. The page itself prints page number 724 and labels the figure `图 35.4`. No prior page mapping or prior role evidence was used.

The chapter places the source immediately after its explanation that one first subtracts the old topic from the document--topic and topic--word tables, computes all candidate weights, samples the new topic, then adds one back to both tables. Chapter Eq. 35.5 gives

`p(z_i=k | z_-i,w,alpha,beta) proportional to [(n_kv^-i+beta_v)/(n_kdot^-i+beta_0)] [(n_mk^-i+alpha_k)/(n_mdot^-i+alpha_0)]`.

The figure shows the same two factors in the opposite multiplication order, which is mathematically identical. It retains the document marginal denominator even though it is constant in `k`, matching the chapter's stated purpose of showing the complete posterior-predictive source. Every count in the two evidence cards and full conditional carries `-i` until sampling; the footnote explains why. The five numbered stages and all six directed connectors implement the correct remove → two evidence reads → normalized conditional → sample/restore → next-token loop. Caption, source alt text, and adjacent chapter prose are consistent.

SEMANTIC_VERDICT=PASS
