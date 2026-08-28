# FIG-P049-01 mathematical and guide-semantic ledger

Observed/recomputed at `2026-08-27T06:00:58+08:00` from the current source and the final R110 native render.

## Core function and contours

For `f(x_1,x_2)=x_1^2/9+x_2^2/3.24`, the three source ellipses have semiaxes `(1.5,0.9)`, `(2.4,1.44)`, and `(3,1.8)`. Substitution gives contour constants `0.25`, `0.64`, and `1.00`; therefore `c_1<c_2<c_3` is correct. At `P=(2.4,1.08)`, `f(P)=1`, so P lies on `c_3`.

The gradient is `(2x_1/9,2x_2/3.24)`, hence `∇f(P)=(0.533333...,0.666666...)`. The plotted arrow vector is `G-P=(0.72,0.90)=1.35∇f(P)`, with positive scale, so it points in the increasing direction.

The plotted tangent direction is `T-Tm=(1.88,-1.50)`. Its dot product with the gradient is `0.0026666667`; the normalized residual is `0.0012987002`, corresponding to `89.9255899°`. P is the exact midpoint of the plotted tangent segment. The right-angle marker uses the source triplet `T--P--G`, and its recomputed angle is also `89.9255899°`; these are acceptable plotting approximations.

## Guide lines

- Guide 2 ends exactly at `G=(3.12,1.98)` and correctly refers to the gradient/increase arrow.
- Guide 3 has visible-mask contact with the right-angle marker and correctly refers to the orthogonality statement.
- Guide 1 ends at `(2.75,1.36)`. It is `0.4482187` axis units (`53.117 px` at 300 dpi) from P, has outer-contour residual `|f-1|=0.41114198`, and is only `0.0983895` axis units (`11.660 px`) from the gradient segment. Thus it does not identify P's contour as its note states.
- The second segment of guide 1 and the second segment of guide 2 intersect internally at `(3.22952321,2.00265997)` with segment parameters `t=0.50564617` and `u=0.81116688`. The final visible masks share 33 pixels at that crossing. These are two distinct callout leaders, so their crossing is a real semantic-routing defect.

Semantic result: core gradient/contour/tangent/right-angle mathematics passes; guide-line semantics fail.
