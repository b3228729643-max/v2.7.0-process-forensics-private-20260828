# FIG-P654-01 R7 local SA2 narrow-patch report

- HANDOFF_ID: `A-R7-P654-SA2-NARROW-DIRECT-20260825`
- MODEL_ROUTE: `SA2=gpt-5.6-sol/max`
- Candidate: the only authorized R7 direct-standalone build from the patched P654 source
- PDF identity: 1 page; 43,385 bytes; SHA256 `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6`
- Source identity: SHA256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`; wrapper SHA256 `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- Object universe: `N=116` = 95 visible glyphs + 21 foreground drawing/path objects
- Exhaustive unordered pairs: `C(116,2)=6,670`, all present exactly once

## Decision

`LOCAL_SA2_PATCH_VERIFIED_REQUEST_FRESH_SA1`

The sole authorized source change raises only `FRM_TRIAL_005` (`𝑛`, U+1D45B, XITSMath-Bold) from a declared 10.1pt to 10.7pt. Its current native 300 dpi final-visible raw mask is complete and pure, with `H_INK=22px >= 22px`, `pre=final=297px`, and zero missing, foreign, clip, or ownership-loss pixels. No threshold, class, mask, geometry, or audit rule was relaxed.

## Full local regression gates

- Source font gate: PASS (`10.1pt` ordinary base, `10.7pt` trial inline formula, `11.6pt` formula blocks; no resize/scale/transform-shape).
- D/E hierarchy: PASS; ordinary same-role source ratios remain 1.0, target-inline-formula/base is 10.7/10.1=1.059406, and formula-block/base is 11.6/10.1=1.148515.
- Low-profile punctuation: N/A; count 0.
- Glyph mapping/manual review: 95/95 current native1x/nearest8x rows opened and individually adjudicated PASS; every mask is complete and pure.
- Drawing/path inventory/manual review: 21/21, including the predictive fraction rule.
- Pair/ownership: 6,670/6,670; canonical final raw overlap 0; clip 0; no illegal independent pre-occlusion contact; 50/50 critical bundles opened.
- LDA border × “应用”: node fill and long-border contamination excluded before adjudication; true separated raw contact is 0.
- Clearance minima: independent text bbox 8px; own node text-border 17px; text-line/arrow 27px; text-math-rule 71px; text-other-node-border 5px; formula-rule-own-border 118px. All applicable thresholds pass.
- Four views/grayscale/page integration: PASS. The trial n is now legible at the hard floor without looking enlarged or shifting the node, edge, or reading hierarchy. The left-to-right backbone, lower branches, line weights, grayscale separation, and page integration remain balanced.
- Mathematics/text semantics: PASS. The local 10.7pt command changes only the rendering of mathematical n; the count meaning, bold-math identity, dependency arrows, posterior alpha+n, predictive fraction, and downstream reading order are unchanged.

This is a local SA2 verification package, not a fresh isolated SA1/SA3 or `STRICT_FINAL`. It requests a new fresh SA1 and does not authorize SA3 by itself.
