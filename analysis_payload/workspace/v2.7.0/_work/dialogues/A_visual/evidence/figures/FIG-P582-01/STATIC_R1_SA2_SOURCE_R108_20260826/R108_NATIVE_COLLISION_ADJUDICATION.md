# FIG-P582-01 R108 native collision adjudication

The R108 figure was independently located on physical page 632, printed page 619, figure 31.7. The full page, 300 dpi figure crop, standalone crop, grayscale crop, the three value/arrow native ROIs, and their nearest-neighbour 8x views were actually opened.

The old arrow/value collision is not a current R108 hard defect. The first `.640`/down-arrow pair has no shared native pixels and about 18.5858 clear pixels after edge correction. The tighter `.380`/down-arrow pair also has no shared native pixels; its nearest classified ink-center distance is 5 px, corresponding to about 3.5858 white pixels. At 1x and 8x both glyphs remain separately readable, and no curve, marker, axis, tick, formula, label, or caption is clipped or illegally overlapped.

Therefore the static patch does not move any annotation, coordinate, marker, curve, or axis. The `.380`/down-arrow ROI is instead frozen as the first regression check for the new build because the mandatory font increase may consume part of its current clearance.
