# FIG-P580-01 R108 fresh isolated SA1 decision ledger

- Reviewer: `SA1_FRESH_ISOLATED_R108`
- Handoff: `A-R108-P580-SA1-FRESH-ISOLATED-20260826`
- Observation completed no later than: `2026-08-26T19:26:44+08:00`
- Candidate: official R108 main route, physical page 630, printed page 617, Figure 31.6.
- Frozen denominator: 32 visible semantic objects and 496 unordered pairs.
- Observed before decision: full page 200 dpi, full page 300 dpi, figure crop 300 dpi, standalone 300 dpi, grayscale 300 dpi, measurement overlay, critical U+0338/U+226A native 1x and nearest-neighbour 8x crops, plain U+226A control crops, and all 14 relation sheets covering PAIR-0001 through PAIR-0496.

## Manual decisions

- Object coverage: all 32 objects are present, legible, semantically correct, and unclipped.
- Relationship coverage: all 496 pair cells were observed. The 39 broad-bbox intersection candidates were individually adjudicated in `manual_overlap_candidate_adjudication.csv`; none is a true illegal overlap. They are legal mathematical/structural/marker contacts, clear-margin containment, or bbox-taxonomy false positives.
- Critical codepoints: the title contains a visible U+0338 overlay on U+226A and reads as `p not-lessless q_L`; the caption provides a correct plain U+226A control. No replacement glyph or tofu square appears.
- Source font: every ordinary reader-facing role is declared at 9.6 pt or 10.2 pt with no whole-figure shrink; formula subscripts are natural TeX scripts from compliant base formulas.
- Pixel height: native 300 dpi text remains genuinely readable. Raw shape/taxonomy ratio warnings for single digits versus inline fractions, vertical versus horizontal compound blocks, and content-dependent ink contours are advisory under R168 and do not indicate actual unreadability or imbalance.
- Role hierarchy: the 10.2/9.6 title-to-base ratio is 1.0625; remaining ordinary roles use the 9.6 pt base. This is balanced and within the intended hierarchy.
- Minimum distinct-semantic-object text clearance: 16 px at native 300 dpi (left/right y-tick ink to the nearest tick stroke); threshold is met. Multiline components inside one annotation/formula block are not separate semantic objects.
- Clipping: zero visible foreground pixels clipped.
- Grayscale: target curves, dashed proposals, dotted boundary, hatch, three marker shapes, and card border remain distinguishable without color.
- Page integration: the figure and caption fit cleanly between the preceding proof and the following reading check/proposition, with no orphaning or abnormal blank region.
- Mathematical recomputation: each of p, q_L, and q_R integrates to 1 on its stated support; p is not absolutely continuous with respect to q_L because q_L=0 while p>0 on (5/2,5), while p is absolutely continuous with respect to q_R. The displayed weights recompute to 24/25, 3/2, 24/25.
- Text consistency: source, plotted values, caption, and the necessary V5-C02 context agree, including the warning that support coverage alone does not imply low variance or reliability.

## Final SA1 verdict

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

No SA2 or SA3 role was invoked, and no source, TeX, PDF, or Git write was performed.
