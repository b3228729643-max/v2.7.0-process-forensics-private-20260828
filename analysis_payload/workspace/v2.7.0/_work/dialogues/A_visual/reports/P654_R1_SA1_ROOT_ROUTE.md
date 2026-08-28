# FIG-P654-01 SA1 root route

- `HANDOFF_ID`: `A-R130-P654-SA1-RESUME-20260824`
- `DECISION`: `ACCEPT_FAIL_TO_SA2`
- This does not count as `A_LOCAL_PASS` or final PASS.

Root reviewed the sealed SA1 report/handoff, the figure crop, text-measurement overlay and grayscale view, and the absolute-last write-stop ordering. The evidence closes N=124 and all 7,626 pairs, while independently exposing hard failures: three glyph-height failures, five same-class failures, five role-ratio failures, formula/base source ratio 1.229166666667 > 1.18, and 17 independent text-bbox clearances below 4 px. The oversized formula block is also visually apparent.

The SA1 failure route is accepted. FIG-P654-01 must be repaired by the new single source writer `A-R130-P654-SA2-REPAIR-20260824`, rebuilt into a completely fresh local evidence package, and later routed through a fresh independent SA1 before any SA3 review.
