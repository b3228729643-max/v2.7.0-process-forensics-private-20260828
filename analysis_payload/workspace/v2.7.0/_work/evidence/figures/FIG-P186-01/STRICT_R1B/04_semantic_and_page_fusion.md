# Semantic recomputation and page fusion

The drawn separator is `y=-0.68x+0.2`. In the figure's own label convention the upper side is `w^T x+b>0`, so a compatible score is:

`g(x)=0.68x+y-0.2`.

The normal arrow starts at `(0,0.2)` and has displacement `(0.82,1.205)`. Against normal `(0.68,1)`, its cross product is `-0.000600` and dot product is `1.762600`; it is correctly perpendicular to the separator and points toward score increase.

All five blue disks satisfy `g>0`. Four teal triangles satisfy `g<0`. The fifth teal triangle is the exception:

| Source point | Declared marker/class | `g(x)` | Required | Native side distance |
|---|---|---:|---|---:|
| `(2.10,-1.05)` | teal hollow triangle / negative | `+0.178` | `<0` | 25.110 px into the positive side |

Equivalently, at `x=2.10` the boundary is `y=-1.228`; the triangle's `y=-1.05` lies above it. It contradicts the negative marker encoding and the in-figure label `w^T x+b<0`.

The caption states that the figure explains a hyperplane, normal vector, and two classes of samples, with the normal pointing to the score-increase half-space. The adjacent chapter sentence states that the boundary direction is controlled by `w`. The page has a correctly placed caption and surrounding body text without clipping in whole-page, fit-page, or grayscale review, but the misclassified negative triangle breaks the required semantic fusion. The native ROI is `roi/misclassified_triangle_native_1x.png`.

Detailed values, including every listed sample, are in `metrics/semantic_recompute.csv`.
