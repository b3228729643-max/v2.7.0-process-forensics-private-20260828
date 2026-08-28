# FIG-P687-01 R115 SA3 overlap adjudication

The frozen collision denominator contains 20 reader-visible semantic objects. The all-pairs ledger contains exactly 190 unordered pairs, matching `C(20,2)`. Every row was judged only after the native figure+caption view, grayscale view, semantic overlay, text overlay, and visible-ink masks had been opened. The six geometrically critical regions were additionally opened at native 1x and nearest-neighbor 8x.

No candidate cluster remains. There is no true text-text, text/formula-line, text/formula-marker, text/formula-border, arrowhead-text, footnote-caption, or annotation-return-line collision. The only visible-ink contacts are the designed connector endpoint attachments to their own card borders: O01-O11, O01-O12, O01-O16, O03-O11, O03-O13, O05-O12, O05-O14, O07-O13, O07-O14, O07-O15, O09-O15, and O09-O16. Each arrow stops at or leaves the intended boundary and never enters card text or formula ink; these are topology, not illegal overlap.

The minimum observed reader-text gap is the vertical gap between the explanatory footnote and caption band, approximately 21 px at the direct 300 dpi render. The return-loop vertical segment stays visibly left of the three-line loop annotation. No reader-visible ink is clipped by the PDF page, node boundaries, or caption crop.

`OVERLAP_CANDIDATE_PIXEL_COUNT=0`, `MASK_CONTAMINATION_PIXEL_COUNT=0`, `OVERLAP_PIXEL_COUNT=0`, `UNRESOLVED_PAIR_COUNT=0`, `CLIP_PIXEL_COUNT=0`, and `PIXEL_ADJUDICATION_STATUS=CLEAR`.

Under the assigned R168 rule, legacy numeric font/pixel/ratio thresholds are advisory. The hard questions were independently closed: no missing/tofu/wrong codepoint or math, no genuine unreadability or severe imbalance, no true clipping, no confirmed illegal visible-ink overlap, and no semantic/geometric/math error.
