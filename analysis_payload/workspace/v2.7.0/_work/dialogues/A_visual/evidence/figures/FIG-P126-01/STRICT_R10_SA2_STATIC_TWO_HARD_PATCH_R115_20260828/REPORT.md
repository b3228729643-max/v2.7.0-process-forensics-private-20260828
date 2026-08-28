# P126 R10 static two-hard patch review

HANDOFF_ID=`A-R115-P126-SA2-STATIC-TWO-HARD-PATCH-R10-20260828`  
STATUS=`STATIC_ONLY_NOT_RENDERED_NOT_PASS`  
STATIC_SCOPE_RESULT=`BLOCKED_BY_PREDICTED_DIGIT4_OCCLUSION`

The authorized two substitutions were applied to the sole P126 source. Before identity is 4,361 bytes/SHA256 `85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81`; after identity is 4,391 bytes/SHA256 `E8803BC9E2347840D7EA0D482D83C20F43FD62DA8023F37C49168241B48AAF81`. In-memory reversal of only those substitutions exactly reconstructs the authorized before identity. Git remains one modified target, 29+/26- aggregate, index empty, and diff-check PASS.

The x2 legend edit has a closed static mechanism: the installed line-legend handler provides three points at 0, 0.3, and 0.6cm; `only marks` removes the connector; plot mark `-` draws a horizontal bar of length 3.6pt. The predicted internal blank is 4.903937pt/20.433px at 300dpi.

The exact digit-6 edit is not safe enough to request a build. Translating the node and its opaque protection background upward by 5pt predicts q4-marker bbox clearance of 1.967915pt/8.200px, but also moves that opaque background across digit 4: bbox overlap 25.619449pt^2 and 88 current dark digit-4 pixels inside the new background. `STATIC_LABEL6_SHIFT_PROJECTION_NATIVE1X.png` and its nearest8x counterpart visualize the unchanged R9 node (blue box) and translated node (red box). This is a static projection only, not a rendered candidate.

No TeX/build, commit, second source, role, UID, Git history mutation, or central write was performed. Main rescoping is required before any build slot should be granted.
