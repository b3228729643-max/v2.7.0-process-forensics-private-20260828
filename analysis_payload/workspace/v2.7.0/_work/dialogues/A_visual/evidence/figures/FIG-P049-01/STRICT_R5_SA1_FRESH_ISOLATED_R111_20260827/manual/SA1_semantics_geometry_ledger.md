# SA1 mathematics, geometry, guide, and text-consistency ledger

## Function and level sets

The plotted function is

`f(x_1,x_2)=x_1^2/9+x_2^2/3.24`.

The three source parametrizations are `(a cos t, 0.6 a sin t)` with `a=1.5, 2.4, 3.0`. Substitution gives constant level `a^2/9`, hence

- inner dash-dot contour: `c_1=1.5^2/9=0.25`;
- middle dashed contour: `c_2=2.4^2/9=0.64`;
- outer solid contour: `c_3=3^2/9=1`.

Therefore `c_1<c_2<c_3` is correct, the nesting is correct, and the line-style ordering remains distinguishable in grayscale.

## Point, gradient, tangent, and orthogonality

For `P=(2.4,1.08)`,

`f(P)=2.4^2/9+1.08^2/3.24=0.64+0.36=1`,

so P lies on the outer `c_3` contour exactly.

The gradient is

`nabla f(P)=(2*2.4/9, 2*1.08/3.24)=(8/15,2/3)`.

The plotted gradient displacement is `G-P=(3.12-2.4,1.98-1.08)=(0.72,0.90)=1.35*(8/15,2/3)`, so its direction is exactly the gradient direction and points toward larger values.

The displayed tangent endpoints are `Tm=(1.46,1.83)` and `T=(3.34,0.33)`, symmetric about P. Their plotted direction `(0.94,-0.75)` has slope `-0.797872...`, while the analytic tangent slope is `-0.8`. The angular discrepancy is about `0.075 degree`, caused by two-decimal endpoint rounding; it is below line/outline resolution, does not change the relation, and is advisory under R168. The right-angle marker, caption, note 3, and adjacent正文 all communicate the correct exact mathematical statement `nabla f(P)^T v_tan=0`.

## Guides and directional cue

- Note 1 leader ends at `(0.84,1.728)`, and `0.84^2/9+1.728^2/3.24=1`, so it correctly locates the outer contour containing P.
- Note 2 leader ends at G, the gradient arrow tip, so the reading cue is unambiguous.
- Note 3 leader ends in the P/right-angle region and does not cross equation ink.
- The gold horizontal arrow is at positive `x_1`; moving right with `x_2` fixed increases `f`, so the `f 增大` cue is correct.
- Axis directions and labels `x_1`, `x_2` are conventional and correct.

## Figure-caption-body consistency

The visible caption states that the gradient arrow is perpendicular to the local tangent and points in the direction of increasing function value. The necessary V1-C03正文 immediately below independently states `nabla f^T v_tan=0` and distinguishes the tangent vector from the steepest-ascent unit vector. The figure symbols, caption, and正文 use the same `P`, `v_tan`, `nabla f`, `x_1`, and `x_2` semantics with no contradiction.

## Manual result

- `MATH_SEMANTICS_PASS=true`.
- `TEXT_CONSISTENCY_PASS=true`.
- `GEOMETRY_SEMANTICS_PASS=true`.
- R168 hard failures for wrong meaning, wrong codepoint, or geometry/semantic error: none.
