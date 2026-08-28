# FIG-P683-01 R115 fresh isolated SA1 report

## Identity and precreate gate

- HANDOFF: `C-FIG-P683-01-R115-SA1-FRESH-ISOLATED-V1`
- Instance: `/root/sa1_fig_p683_r115_fresh_isolated_v1`
- Model/effort: `gpt-5.6-sol / xhigh`
- Fixed evidence root was proven before creation: `Leaf=false`, `Container=false`, `Any=false`, `Parent=true`.
- The three exact allowlisted candidate/source files matched the required byte sizes and SHA-256 identities. No fallback path, directory search, historical P683 evidence, accepted SA2 evidence, other UID, Git, state, inventory, agent-status, or process-management source was used.

## Independent current-R115 location

Fresh extraction of the current allowlisted PDF located figure 35.2 on physical PDF page 732, printed page 719, under section 35.2 “LDA 生成过程与概率图”. The exact figure source is `fig_v5_c06_plate_graph.tex`; chapter lines 247-260 provide the immediately adjacent context. This location was obtained from the current PDF/source rather than inherited historical page metadata.

## Frozen denominator and exhaustive pair closure

The source semantic lock contains 18 TikZ nodes and 5 explicit directed draws. One additional reader-visible object covers the complete caption, producing a frozen denominator of `N=24`. `machine/pair_denominator.csv` enumerates every unordered pair exactly once: `C(24,2)=276`. The base list and post-observation manual ledger have identical pair identities in identical order, 276 unique IDs, and no omitted or duplicate pair.

The denominator comprises six model-variable objects, three plate borders, three plate labels, six legend objects, five directed dependency edges, and the complete caption. `machine/object_registry.csv` freezes the source line, semantic role, PDF-point box, and native-crop pixel box for every object.

## Machine evidence and actual observation

Machine-only evidence contains the current-page location, full 200/300 dpi render, native 300 dpi figure-plus-caption crop, grayscale crop, foreground view, semantic-class overlay, object-ID overlay, text measurement overlay, 24-object registry, 276-pair base and geometry tables, 32 extracted text spans, and 156 extracted glyph/codepoint rows. The glyph inventory contains zero U+FFFD replacement characters.

Only after those machine artifacts existed, I opened and inspected all 17 views listed in `manual/opened_view_ledger.csv`, including each of five selected critical ROIs at native 1x and nearest-neighbor 8x. I then wrote the 24-row per-object ledger and the 276-row per-pair ledger. Machine generation did not populate manual observations or verdicts.

## Post-observation findings

- Glyphs/codepoints: alpha, beta, theta, phi, z, w, all subscripts, `N_m/M/K`, Chinese labels, `plate`, caption Latin words, punctuation, and all caption Chinese glyphs render as intended. No missing glyph, tofu, replacement character, wrong codepoint, broken subscript, or unreadable span was observed.
- Readability and balance: node labels, plate labels, legend labels, and caption are sharp at native 300 dpi and remain coherent on the full 200 dpi page. Source/PDF numeric sizes around the legacy 9.2-9.6 pt band are recorded as advisory under R168; actual rendering is comfortably readable and not severely imbalanced. No numeric threshold was used alone to accept or reject the figure.
- Geometry: all five arrows have clear direction. Each arrow stops at the intended node boundary without entering label ink. Six source-required plate-boundary crossings were inspected at native pixels and 8x: alpha-to-theta crosses M; theta-to-z crosses N; beta-to-phi crosses K; phi-to-w crosses K, M, and N. These are necessary plate-diagram topology, not illegal overlaps, and none touches text. All 276 pairs are individually closed as `NO_ILLEGAL_OVERLAP`.
- Clipping: no reader-visible text, node border, arrowhead, plate dash, legend marker, or caption glyph is clipped in the native crop or full page.
- Replication geometry: the `N_m` plate contains `z_mn,w_mn`; it is nested in the `M` plate, which also contains `theta_m`; the separate `K` plate contains `phi_k`. Alpha and beta stay outside all plates. Labels are attached to the correct plates.
- Complete-Bayes semantics: `alpha→theta_m`, `theta_m→z_mn`, `z_mn→w_mn`, `beta→phi_k`, and `phi_k→w_mn` match the complete-Bayes LDA factorization. The filled `w_mn` is observed; theta, z, and phi are latent; alpha and beta are hyperparameters. The chapter context separately defines the point-parameter variant by conditioning on phi and explicitly distinguishes complete-Bayes collapsed Gibbs from point-parameter variational EM. The figure and caption do not conflate the two targets.
- Caption/context: the caption accurately states variable roles, sharing, replication, and arrow meaning. The preceding text states the N-in-M and separate-K repetition; the following text consistently contrasts the two inference/model targets.
- Grayscale and page integration: observed fill remains dark, latent nodes remain open, dashed plates remain subordinate, arrows retain priority, and legend encoding remains discriminable. The figure and three-line caption fit the page without crowding, abnormal whitespace, isolated caption lines, or collision with adjacent prose.

## SA1 verdict

No hard R168 defect was found: no missing/tofu/wrong codepoint, actual unreadability or severe imbalance, true clipping, confirmed illegal visible-ink overlap, or semantic/geometric/mathematical error. The post-observation SA1 result is PASS and is ready only for a new fresh isolated SA3. This report does not count local, global, or final acceptance and does not start SA3.
