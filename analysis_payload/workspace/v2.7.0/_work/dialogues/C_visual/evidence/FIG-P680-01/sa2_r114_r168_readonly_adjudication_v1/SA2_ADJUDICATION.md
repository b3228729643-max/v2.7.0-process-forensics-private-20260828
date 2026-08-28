# FIG-P680-01 SA2 adjudication

The current official R114 page, current figure source, exact chapter context, caption, full-page views, native 300 dpi views, grayscale view, object/semantic overlays, and all critical native1x/nearest-neighbor8x ROIs show no R168 hard defect.

The shared “document--topic--word” conditional structure correctly branches to:

1. complete Bayes LDA, with theta and phi random, followed by collapsed Gibbs integrating out theta and phi; and
2. a point-parameter LDA variant, with phi estimated, followed by mean-field variational EM using ELBO coordinate ascent.

The arrows express learning dependence. The warning and caption correctly deny that the two posteriors are the same. The solid-versus-dashed branch coding survives grayscale. No reader-visible glyph is missing or substituted; no text or semantic object is clipped; no arrow, line, border, or other object illegally overlaps text; and no mathematical, semantic, or geometric error is present.

R168 makes the historical numeric font/pixel/ratio values advisory. The current 9.4 pt normal-node setting and 9.2 pt warning setting do not create actual unreadability or severe imbalance in the observed PDF, so they are not a hard failure.

No source change is warranted or authorized.

VERDICT=`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

Main may authorize a completely fresh SA1. This SA2 instance does not create that role, start another UID, or write any central inventory/state.

