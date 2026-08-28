# FIG-P609-01 SA1 visual acceptance

`RESULT=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

- `HANDOFF_ID=C-FIG-P609-01-R108-SA1-FRESH-ISOLATED-V1`
- `ACTUAL_INSTANCE=/root/sa1_fig_p609_r108_fresh_isolated_v1`
- `SA1_MODEL=gpt-5.6-sol`
- `SA1_REASONING=xhigh`
- `FORK_TURNS=none`
- `CANDIDATE=R108`
- `PHYSICAL_PAGE=661`
- `PRINTED_PAGE=648`
- `FIGURE_NUMBER=32.9`
- `SOURCE_FONT_PASS=true`
- `PIXEL_HEIGHT_PASS=true`
- `SAME_CLASS_RATIO_PASS=true`
- `ROLE_RATIO_PASS=true`
- `OVERLAP_CANDIDATE_PIXEL_COUNT=0`
- `MASK_CONTAMINATION_PIXEL_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `PIXEL_ADJUDICATION_STATUS=CLEAR`
- `PIXEL_ARBITER_MODEL=NOT_USED`
- `PIXEL_ARBITER_REASONING=NOT_USED`
- `CLIP_PIXEL_COUNT=0`
- `MIN_TEXT_CLEARANCE_PX=3.25` (vector-bbox advisory for T19-T20; actual ink has 20 white rows and 49.4 px nearest-ink distance)
- `VISUAL_HARMONY_PASS=true`
- `MATH_SEMANTICS_PASS=true`
- `TEXT_CONSISTENCY_PASS=true`
- `GRAYSCALE_PASS=true`
- `PAGE_INTEGRATION_PASS=true`

## Manual decision

Source inspection finds explicit general-visible sizes of 9.6 pt, axis labels 9.8 pt, and titles 10.4 pt, with no resizebox, scalebox, or text-transform scale. PDF font metadata reports 9.564/9.763/10.361 pt because of TeX/PDF unit conversion; this metadata-level delta is advisory under R168 and does not change the source effective-size pass.

At native 300 dpi, meaningful minimum ink heights are: CJK 34 px (threshold 30), digits 26 px (24), Latin uppercase 29 px (24), lowercase n 20 px (17), base math 27 px (22), and naturally derived scripts 21 px (15). Repeated-role ratios pass: x ticks 26-27 px, y ticks 26-27 px, both panel titles have CJK 41 px / Latin uppercase 30 px / number 29 px, repeated tau glyphs 35-36 px, and repeated K,n scripts are 26 px.

The native and nearest8x ROIs show no tofu, wrong codepoint, missing hat/subscript/limit, true clipping, text-line collision, curve-through-text, or panel-border collision. Grayscale preserves the dark stem/marker series, pale window fill, dashed cutoff, and left-to-right connector without relying on color alone. The full-page views show a complete caption and following read-order paragraph, balanced page occupation, and no orphaned or clipped material.

No hard failure was found. No SA2 repair is requested. The only allowed next role is a new fresh isolated SA3 review of the unchanged official R108 candidate.

