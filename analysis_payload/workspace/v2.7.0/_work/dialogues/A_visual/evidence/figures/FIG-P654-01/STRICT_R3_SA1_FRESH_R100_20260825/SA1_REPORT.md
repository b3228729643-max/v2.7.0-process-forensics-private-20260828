# FIG-P654-01 fresh isolated SA1 report — official R100

- HANDOFF_ID: `A-R100-P654-SA1-FRESH-20260825`
- MODEL_ROUTE: `SA1=gpt-5.6-sol/xhigh`
- Candidate: frozen official R100 fullbook
- PDF identity: 814 pages; 4,943,206 bytes; SHA256 `5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`
- Independent location: physical page 702; printed page 689; Figure 34.1
- Object universe: `N=116` = 95 visible glyphs + 21 foreground drawing/path objects
- Exhaustive unordered pairs: `C(116,2)=6,670`, all present exactly once

## Decision

`FAIL_TO_SA2`

The sole hard gate failure is `FRM_TRIAL_005` (`𝑛`, U+1D45B, XITSMath-Bold): its native 300 dpi final-visible raw mask is complete and pure, has no missing/foreign/clip/ownership-loss pixels, but `H_INK=21px < 22px`. No tolerance, reclassification, parent-formula height, or visual-harmony override is applied.

## Other gates

- Source font gate: PASS (`10.1pt` base, `11.6pt` formula blocks, no resize/scale/transform-shape).
- D/E hierarchy: PASS; same-role source ratios are 1.0, CJK semantic-element median extreme ratio is 36/35=1.028571, formula/base source ratio is 11.6/10.1=1.148515.
- Low-profile punctuation: N/A; count 0.
- Glyph mapping/manual review: 95/95; all masks complete and pure; the one row above fails only its numeric height floor.
- Drawing/path inventory/manual review: 21/21, including the predictive fraction rule.
- Pair/ownership: 6,670/6,670; canonical final raw overlap 0; clip 0; no illegal independent pre-occlusion contact; 50/50 critical bundles opened.
- LDA border × “应用”: node fill and long-border contamination excluded before adjudication; true separated raw contact is 0.
- Clearance minima: independent text bbox 8px; own node text-border 18px; text-line/arrow 26px; text-math-rule 70px; text-other-node-border 5px; formula-rule-own-border 118px. All applicable thresholds pass.
- Four views/grayscale/page integration: PASS. The left-to-right backbone, lower interpretive branches, dashed application outlet, hierarchy, line weights, and grayscale separation are clear. This does not override the pixel-height failure.
- Mathematics/text semantics: PASS. Counts n and Gamma/Beta normalizers feed the multinomial/Dirichlet family, posterior alpha+n, predictive (alpha_i+n_i)/(alpha_0+N), interpretive branches, and the downstream topic-model application; wording agrees with the adjacent current body.

This failed round is not `STRICT_FINAL` and does not authorize SA3.
