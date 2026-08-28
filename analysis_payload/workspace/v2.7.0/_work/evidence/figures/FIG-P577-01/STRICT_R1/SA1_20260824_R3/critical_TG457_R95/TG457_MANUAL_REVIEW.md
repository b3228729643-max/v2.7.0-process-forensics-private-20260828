# TG457 R95 native critical review

The original 1:1 crop and its 8× nearest-neighbour view were opened. `0.8` is visibly separate from the teal card edge, but the exact visible-ink nearest pair is only `2.000px` at text `391,1200` to border `391,1202`. The mandatory TEXT_NODE_BORDER clearance is `>=5px`; overlap is `0px`. Therefore this is a real **FAIL** by the stated hard gate, not a projection-contamination artefact. The target overlay colours only the text object red; the two component-only masks exclude all neighbours.

Required review artifacts are the five named 1× files and their paired `8x_nearest` files in this directory.
