# SUPERSEDED provisional mask calculation

A first provisional color-only implementation rendered PDF drawing 17 as a solid line and therefore reported T05↔V08 overlap=161 px. This is superseded and must not be used: raw R93 vector data shows drawing 17 uses dash array [2.98883 1.99255] 0, and drawing 19 is an opaque white label background painted after the path. The current implementation preserves both facts. Current result: T05↔V08 MASK_OVERLAP_PX=0; NEAREST_DISTANCE_PX=7.000.
