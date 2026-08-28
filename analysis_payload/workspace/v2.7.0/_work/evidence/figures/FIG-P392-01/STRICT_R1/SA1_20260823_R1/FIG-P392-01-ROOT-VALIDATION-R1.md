# FIG-P392-01 root validation — STRICT R1

ROOT_RESULT: CONFIRM_SA1_FAIL

- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 428, printed page 415, 图 22.1.
- Source audit independently confirmed explicit 9.2 pt figure/node bases and a 9.0 pt brace-label base in `fig_v3_c06_chain.tex`; these are below the mandatory 9.5 pt effective-source floor. SA1 records 85/98 source-font rows failing.
- Native 300 dpi substring audit reports 12 glyph failures. The failure set includes independently measured base operators; composite formula height was not accepted as a substitute.
- Root inspected the native figure crop plus the raw, overlay, and exact overlap-mask evidence for terminal `y_{n+1}`. The text visibly crosses both rings. Independent masks report 31 pixels against the outer ring and 8 pixels against the inner ring, total illegal foreground overlap 39 pixels and clearance 0 px. This is not a dilated-mask or antialias-contamination false positive.
- Clip count is 0. Same-class and role-ratio audits pass, but visual harmony fails because the terminal node is crowded and colliding.

Disposition: candidate is rejected. `FIG-P392-01` returns to SA2; SA3 is prohibited until a rebuilt candidate has new strict evidence and a fresh independent SA1 PASS.
