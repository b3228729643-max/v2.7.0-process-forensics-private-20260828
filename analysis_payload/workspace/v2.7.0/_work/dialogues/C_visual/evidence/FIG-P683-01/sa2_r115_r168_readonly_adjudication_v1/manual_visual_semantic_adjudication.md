# FIG-P683-01 R115 / R168 manual visual-semantic adjudication

## Identity and fresh location

- Handoff: `C-FIG-P683-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p683_r115_r168_readonly_v1`
- Model / effort: `gpt-5.6-sol / xhigh`
- Candidate: R115, exact allowlisted `main_full.pdf`, 4,967,161 bytes, SHA-256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`
- Freshly located target: physical PDF page 732, printed page 719, Figure 35.2. The `P683` in the UID is legacy identity and is not the current R115 physical page.

## Views actually opened before judgment

- Full page at 200 dpi.
- Full page at 300 dpi.
- Full page grayscale at 300 dpi.
- Native figure-plus-caption crop at 300 dpi.
- Native figure-plus-caption grayscale crop at 300 dpi.
- Semantic-region overlay.
- All-object overlay for O01--O23.
- All-text-span overlay for T001--T032.
- ROI01--ROI10, each at native 1x and nearest-neighbor 8x.

## R168 hard-defect review

### Glyph and codepoint integrity

The native and 8x views show no missing glyph, tofu square, replacement character, or wrong-symbol substitution. PDF Unicode extraction returns the intended mathematical characters for alpha, beta, theta, varphi, z, w, N, M, K and their subscripts, plus the complete Chinese labels and caption. The page fonts are embedded and Unicode-mapped. `varphi_k` is visibly the intended topic-word symbol from the source, not an unknown or damaged character. The white `w_mn` remains legible on the observed-node fill.

### Readability, hierarchy, and balance

At the 200 dpi full-page reading view, graph nodes, plate labels, legend, and caption are all plainly readable. At native 300 dpi and 8x nearest-neighbor inspection, strokes remain complete and distinct. The source uses 9.4/9.6 pt for graph nodes and 9.2 pt for plate/legend text; some legacy nominal values sit slightly below the older 9.5 pt rule, but R168 makes those numeric thresholds advisory. Direct observation shows neither actual unreadability nor severe imbalance. The graph remains the primary visual object, the legend is subordinate, and the caption does not overpower the plate diagram.

### Clipping and page integration

All node circles, plate borders, arrowheads, labels, legend entries, and caption glyphs are complete. No visible foreground stroke is cut by the page, figure crop, plate, or caption region. The figure fits comfortably between the preceding explanatory paragraph and the following learning-strategy paragraph, with stable whitespace and no collision with body text. Manual `CLIP_PIXEL_COUNT=0` for hard-defect purposes.

### Illegal visible-ink overlap

The complete graph denominator is 18 source-visible nodes plus 5 directed draws, N=23; all 253 unordered pairs were manually adjudicated. No pair has a confirmed illegal visible-ink collision. The only visible structural contacts are clean edge-to-node-border attachments and the plate-boundary crossings required for dependencies that enter or exit repetition plates. Those junctions do not obscure any glyph, arrowhead, or plate label. The two arrows entering `w_mn` terminate at distinct border positions, and the incoming/outgoing edges at `varphi_k` use distinct positions. No candidate is unresolved. Manual canonical `OVERLAP_PIXEL_COUNT=0`; `PIXEL_ADJUDICATION_STATUS=CLEAR`.

### Plate, latent/observed, arrows, and replication geometry

- M encloses `theta_m` and the entire N_m plate.
- N_m encloses exactly `z_mn` and `w_mn` and is nested in M.
- K is separate and encloses exactly `varphi_k`.
- `w_mn` alone is observed/filled; `theta_m`, `z_mn`, and `varphi_k` are latent/unfilled.
- `alpha` and `beta` are outside plates and are identified as hyperparameters in the legend.
- Directed dependencies are exactly `alpha -> theta_m`, `theta_m -> z_mn`, `z_mn -> w_mn`, `beta -> varphi_k`, and `varphi_k -> w_mn`.
- Replication labels `N_m 个词位`, `M 篇文档`, and `K 个主题` are attached to the correct plates and do not collide with diagram ink.

No semantic or geometric plate error is present.

### Complete-Bayes versus point-parameter LDA semantics

The current chapter explicitly distinguishes complete-Bayes LDA from the point-parameter LDA variant. Figure 35.2 is explicitly captioned as complete-Bayes and therefore correctly includes random `varphi_k`, the prior edge `beta -> varphi_k`, and a K replication plate. The point-parameter formula immediately above the figure is identified in the surrounding prose as a different variant where `varphi` is fixed. The figure does not conflate the two models: it depicts the complete-Bayes generative graph while the neighboring text contrasts the parameterized variant.

### Caption and chapter consistency

The rendered caption matches the current source caption and accurately states the visual roles: hyperparameters, latent variables, observed variables, per-document `theta_m`, per-word-position `z_mn`, globally shared Dirichlet-prior topic-word distributions, repetition plates, and conditional-dependency arrows. The adjacent chapter equations and prose specify the same complete-Bayes factorization and the same nested N_m/M and separate K plate meanings. No text/figure contradiction was found.

### Grayscale

In grayscale, the observed node remains a dark filled circle with white text, latent nodes remain light circles with dark outlines/text, plate borders remain visible dashed gray, and dependency arrows remain darker than the plates. Legend swatches continue to distinguish observed from latent status without relying on hue alone. No grayscale hierarchy collapse is present.

## Substantive result

No R168 hard defect exists. The older numeric font/pixel/ratio rules are advisory here and do not override the direct observation that all information is readable and balanced. There is no missing/tofu/wrong codepoint, actual unreadability or severe imbalance, true clipping, confirmed illegal visible-ink overlap, or semantic/geometric/mathematical error.

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
