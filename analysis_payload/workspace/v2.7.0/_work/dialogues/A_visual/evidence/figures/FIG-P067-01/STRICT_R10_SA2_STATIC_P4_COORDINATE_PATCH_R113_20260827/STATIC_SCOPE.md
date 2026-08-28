# FIG-P067-01 R10 static-only coordinate patch

- Authorization: `MAIN_R392_P067_SA3_FAIL_ACCEPTED_AND_SINGLE_COORDINATE_STATIC_SCOPE`.
- Scope: exactly one source and exactly one coordinate literal.
- Change: `at (axis cs:4.08,.89) {$p_4$};` becomes `at (axis cs:4.08,.85) {$p_4$};`.
- Preserved: x coordinate, visible text, anchor, mass style, font, fill/opacity, inner sep, CDF and PMF curves, endpoints, guides, axes, caption, all other labels, and every other token.
- Git boundary: one file, 1 insertion, 1 deletion; index empty; `git diff --check` passed.

## Static projection

The y displacement is `-0.04` axis units, approximately 8 native 300 dpi pixels. Translating the current final masks for T016/T017 by this displacement predicts zero intersections against all other 128 visible objects. The projected nearest clearances are:

- G008 plateau: center distance 6 px, 5 complete blank pixels.
- G009 y=1 dashed reference: center distance 7 px, 6 complete blank pixels.
- Next nearest unrelated object: 20.10 px.

This is a static projection only. It is not a rendered PASS and does not authorize TeX, commit, a fresh role, or A_LOCAL_PASS.

## Regression risk

Risk is localized to the `p_4` label. The 8 px downward translation is materially smaller than the 20.10 px next-object clearance and does not alter any graph geometry or probability/CDF semantics. A new standalone PDF must independently verify P01916/P01917 and the complete figure before any commit.
