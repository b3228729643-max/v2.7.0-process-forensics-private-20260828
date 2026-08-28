# Independent strict requalification: FIG-P504-01

Decision: FAIL; route to SA2.

Fresh source and frozen-PDF evidence only. No former review conclusion or screenshot was used.

Identity: figure 28.1, label fig:V4-C05-two-geometries; PDF physical page 550, printed page 537.

Gate summary: SOURCE_FONT_PASS=false (11/14 visible semantic objects below 9.5pt); PIXEL_HEIGHT_PASS=false (13 individual raw glyph-floor failures); SAME_CLASS_RATIO_PASS=true; ROLE_RATIO_PASS=false (formula/base lower=1.325 >1.18); OVERLAP_PIXEL_COUNT=0; CLIP_PIXEL_COUNT=0; MIN_TEXT_CLEARANCE_PX=0.00; GRAYSCALE_PASS=true; PAGE_INTEGRATION_PASS=true.

FONT_VISUAL_HARMONY_PASS = false. At 1:1 native 300dpi, the undersized text, 13 glyph-floor failures, role-ratio excess and 0px title/w2 vector-bbox clearance fail the schema's combined visual-harmony condition. No apparent visual coherence in the colour/greyscale views can waive those gates; an acceptable size reduction would require every size, pixel, ratio, clearance and full-page gate to remain true.

Collision finding: R_TITLE/w2 has exactly 0 separated raw-ink intersection pixels and 14.00px raw-ink clearance, so it is not an overlap-pixel failure. Its final PDF/vector bboxes touch/overlap, giving 0.00px bbox clearance against the mandatory 4px text-text minimum. All other recorded critical pairs have zero overlap and pass their stated clearance thresholds.

Mathematical finding: LSA is described as K=2, with u1/u2 spanning the displayed two-dimensional plane. Therefore the labelled projection U2 U2 transpose x cannot differ from x there. The nonzero residual and separate projection point instead depict a K=1 projection. NMF's rank-two nonnegative cone is otherwise consistent with W two columns and h two nonnegative coordinates.

Required SA2 correction: either show a genuine ambient 3D vector and K=2 plane, or make the LSA drawing a K=1 projection; do not retain K=2, two in-plane bases, and a nonzero residual together. Raise all reader-visible source effective sizes to at least 9.5pt and rerun the full audit.

See after_visual_acceptance.md and all CSV, raw, mask, overlay and critical-pair artifacts in this directory.
