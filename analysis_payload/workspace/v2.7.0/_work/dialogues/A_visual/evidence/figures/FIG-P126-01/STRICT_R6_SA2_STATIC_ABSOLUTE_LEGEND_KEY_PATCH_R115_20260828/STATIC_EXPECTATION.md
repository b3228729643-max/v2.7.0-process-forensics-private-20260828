# Static expectation

The edit adds only the absolute `/pgfplots/` prefix to the x2 `legend image code/.code` key. Lines 66--71 remain byte-identical in the live source: four SLTeal horizontal segments with endpoints `[0,.08]`, `[.18,.26]`, `[.36,.44]`, `[.54,.62]` cm, line width 1.05pt, and three designed 0.10cm gaps.

At 300dpi, each 0.10cm gap projects to approximately 11.81 pixels. If the installed handler accepts the absolute key as statically predicted, the new PDF should contain four disconnected sample segments and three clearly nonzero blank runs. The x1 legend sample, legend text/font/position, actual x1/x2 trajectories, contours, q0--q7, markers, numeric labels, axes, math, caption, alt text, shared macros and all other tokens are frozen.

Required new-PDF validation remains: native1x and nearest8x color/grayscale x1-versus-x2 legend topology, all reader-visible objects/all unordered pairs, overlap/clip, math/semantic/caption/page regression and genuine post-observation manual ledgers.

Current status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`.
