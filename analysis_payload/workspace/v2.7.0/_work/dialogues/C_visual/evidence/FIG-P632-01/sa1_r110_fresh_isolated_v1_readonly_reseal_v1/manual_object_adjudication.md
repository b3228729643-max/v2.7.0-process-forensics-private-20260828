# FIG-P632-01 manual visible-object adjudication

Reviewer identity: SA1, gpt-5.6-sol, xhigh. Each entry below was written after direct inspection of the native 300 dpi full page, figure crop, grayscale crop, semantic overlay, text overlay, and applicable 1x/8x ROI. The frozen denominator is `object_denominator_machine.csv` (23 objects).

- O01 — The three-line joint-model formula block is complete and sharp: rho=3/5, a=1, b=4/5; the normalized joint density and quadratic form are all present. Fractions, subscripts, superscripts, brackets, exponential and minus sign are intact. No clipping or crowding. Decision: PASS.
- O02 — The joint panel has one horizontal x1 axis and one vertical x2 axis with intact arrowheads and labels. The axes cross only as coordinate axes; neither arrowhead reaches a label. Decision: PASS.
- O03 — The pale dotted outer ellipse is continuous, centered on the same origin as the other contours, elongated along +45 degrees, and remains distinguishable in grayscale. Its crossings with axes/slices are intended geometry. Decision: PASS.
- O04 — The middle green dashed ellipse is continuous, shares the joint center/orientation, and is distinct from both outer dotted and inner solid contours in color and grayscale. Decision: PASS.
- O05 — The inner blue solid ellipse is smooth, closed, centered correctly and visually dominant among the three contours without obscuring axes or labels. Decision: PASS.
- O06 — The horizontal dashed slice is visibly fixed at x2=b=4/5, crosses the joint point, and continues rightward toward the upper normalization map. The two-line fraction label has clear separation from the stroke. Decision: PASS.
- O07 — The vertical dotted slice is visibly fixed at x1=a=1, crosses the same joint point, and routes downward for the lower normalization map. Its short leader and x1=a=1 label are separated from formula and contour ink. Decision: PASS.
- O08 — The filled point is exactly at the horizontal/vertical slice intersection; the leader points to an intact (a,b) label. The marker’s contact with both slice strokes is intended semantic coincidence, not illegal overlap. Decision: PASS.
- O09 — The blue conclusion line states the +45-degree principal axis and c*sqrt(1±rho) semiaxes. It is legible, baseline-aligned, clear of the vertical-map route, and not clipped. Decision: PASS.
- O10 — The green horizontal-slice normalization label and two-segment arrow read left-to-right and terminate before the upper density axes. The arrowhead is intact and has a large white gap to the upper y-axis. Decision: PASS.
- O11 — The upper conditional formula block shows pi1(t|X2=b)=pi(t,b)/m2(b), N(12/25,16/25), m2(b)=phi(4/5)≈0.29>0, unit integral, and the correct peak. Every numerator, denominator, integral limit and radical is present. Decision: PASS.
- O12 — The upper density axes are complete; the y-axis arrowhead, x-axis arrowhead and t label are intact. The curve meets the baseline at tails by design, and the t label remains clear of the arrowhead. Decision: PASS.
- O13 — The upper solid conditional-density curve is smooth, unimodal and centered at 12/25. It is not hidden by formulas or the mapping arrow and remains distinct in grayscale. Decision: PASS.
- O14 — The upper dashed mean guide reaches the curve peak and baseline, with 12/25 centered below. Guide/curve contact at the peak and guide/axis contact at the baseline are intended; the fraction is separated below the axis. Decision: PASS.
- O15 — The blue vertical-slice normalization label and routed arrow proceed down/right without crossing O10, the joint conclusion, or the lower axes. The arrowhead ends before the lower y-axis with clear whitespace. Decision: PASS.
- O16 — The lower conditional formula block shows pi2(t|X1=a)=pi(a,t)/m1(a), N(3/5,16/25), m1(a)=phi(1)≈0.242>0, unit integral, and the same correct peak. The apparent bbox proximity to O14 is whitespace-only, confirmed in R09 at 8x. Decision: PASS.
- O17 — The lower density axes and t label mirror the upper panel. Both arrowheads are intact, and the x-axis/t-label clearance is visually comfortable. Decision: PASS.
- O18 — The lower dashed conditional-density curve is smooth, unimodal and centered at 3/5. The dash pattern remains distinguishable from O13 in grayscale. Decision: PASS.
- O19 — The lower dotted mean guide reaches the curve peak and baseline, with 3/5 centered below. The two intended contacts do not interfere with the fraction glyphs. Decision: PASS.
- O20 — The three-line regular-conditional note is complete: it handles zero marginal denominators, measurable version selection, marginal-a.e. uniqueness, and positivity in this Gaussian example. All Chinese and mathematical glyphs are present. Decision: PASS.
- O21 — The rounded red note border and pale fill fully enclose O20 with interior padding; the bottom border is intact and has a visible gap above the caption. Decision: PASS.
- O22 — The bold caption number “图 33.2” is complete, aligned to the caption body, and contains no tofu, substitution or clipped stroke. Decision: PASS.
- O23 — The two-line caption body is complete and agrees with the figure: slice normalization, variance 16/25, integration over the real line, and the zero-marginal regular-condition qualification. Wrapping is natural and clear of O21. Decision: PASS.

Object count adjudicated: 23/23. Hard-failing object count: 0.
