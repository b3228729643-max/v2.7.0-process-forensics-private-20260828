# FIG-P608-01 root finding — rotation-normalized font hierarchy failure

- Decision: `REJECT_CURRENT_AFTER_FINAL_CONTINUE_SA2`
- Inspected render: `STRICT_R4_SA2_REPAIR_R98_LOCAL_20260824/after_final/final_local_lua_official_stack_300dpi.png`
- Inspected machine table: `after_final_glyph_metrics_machine.csv`
- Inspected original/mask/nearest cards for G031, G035, G062, and G074.

## Finding

The current audit applied the glyph-height gate to page-axis bounding-box height even though G031 and G062 are rotated with the vertical axis labels. That measurement is not a local glyph-height measurement and caused an unnecessary enlargement via `\slfigTraceScriptT` to effective 14.3462 pt.

Observed official-stack 300 dpi metrics:

| Glyph | Role | effective pt | page H x W (px) | rotation-normalized local ink height |
|---|---|---:|---:|---:|
| G030 `X` | upper y-axis base | 10.75965 | 29 x 30 | about 30 px |
| G031 `t` | upper y-axis script | 14.3462 | 16 x 37 | 37 px |
| G035 `t` | upper title natural script | 7.53172 | 21 x 9 | 21 px |
| G062 `t` | lower y-axis script | 14.3462 | 16 x 37 | 37 px |
| G074 `t` | lower title natural script | 7.53172 | 21 x 9 | 21 px |

Thus the supposed script glyph is locally taller than the base `X` (`37/30 > 1`) and is `37/21 = 1.7619...` times the same mathematical script glyph in the panel title. This violates script semantics, same-role consistency, and the visual-harmony gate even though the page-axis bbox height happens to be 16 px.

## Required repair and evidence

- This current `after_final` result cannot pass or be sealed as final.
- Measure all rotated glyphs in both page coordinates and inverse-rotated local text coordinates. Apply the glyph-height gate to the glyph's local text axis; retain page coordinates for overlap and clipping.
- Restore a natural script or choose the smallest local adjustment that remains at least 15 px after rotation normalization while keeping the script visibly smaller than its base glyph and consistent with the same-role title scripts.
- Rebuild all official Noto/STIX 300 dpi glyph, object, pair, font-ratio, overlap, gray/color-vision, opened-register, and sealing evidence. Mark the present `after_final` tree as superseded; do not reuse its PASS labels.
