# FIG-P680-01 fresh isolated SA1 review

HANDOFF_ID=`C-FIG-P680-01-R114-SA1-FRESH-ISOLATED-V1`  
UID=`FIG-P680-01`  
ACTUAL_INSTANCE=`/root/sa1_fig_p680_r114_fresh_isolated_v1`  
MODEL=`gpt-5.6-sol`  
REASONING_EFFORT=`xhigh`

## Frozen inputs

- Official R114 PDF: 4,967,122 bytes; SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`.
- Current figure source: 3,144 bytes; SHA-256 `76474E18D9E735283274AF614DFAE606BA3683BDA2539168AC91920DDE6E22BA`.
- Exact current context: 120,809 bytes; SHA-256 `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`.

All three identities matched before evidence generation. PDF, figure source, and chapter source remained read-only; no TeX, latexmk, build, source write, Git, central state, inventory, or process-management action occurred.

## Independent current-page localization

The legacy UID number was not accepted as a page locator. Searching only the allowlisted R114 PDF for the current caption uniquely located the figure on physical page 729, printed page 716. The preliminary physical-page-680 render showed chapter 33 and was immediately replaced in the same root; no second root, restart, or duplicate role was created.

## Frozen denominators

- Reader-visible objects: 26 (`T01`–`T16`, `N01`–`N06`, `E01`–`E04`). Decorative fills and source-only alt text are excluded because they are not independent reader-visible foreground objects.
- Reader-visible glyphs: 212 (`G001`–`G212`).
- Unordered object pairs: 325 (`P001`–`P325`), exactly `26 choose 2`.

## Views actually opened

`full_page_200dpi.png`, `native_page_300dpi.png`, `figure_caption_300dpi.png`, `grayscale_page_300dpi.png`, `grayscale_figure_caption_300dpi.png`, `object_id_overlay_300dpi.png`, `semantic_class_overlay_300dpi.png`, `critical_roi_native1x.png`, and `critical_roi_nearest8x.png` were each opened and inspected.

## Post-observation findings

- Current-PDF ink heights are 31–33 px for ordinary internal Chinese text, 38 px for the mixed math lines, 34 px for the warning, and 39–41 px for caption lines. The source's 9.4 pt internal setting and 9.2 pt warning are recorded as advisory under the current R114 rule; the actual raster is clear and not materially small.
- Minimum text–text bbox clearance is 7 px, minimum text/formula–arrow bbox clearance is 15 px, and minimum internal text–node-border bbox clearance is 14 px.
- All 325 unordered pairs are adjudicated. There are eight legal incident arrow/node endpoint contacts, zero illegal visible-ink collision pixels, zero unresolved pairs, and zero clipped visible pixels.
- All 212 glyphs are present. `θ` and `φ` retain the intended mathematical italic Unicode codepoints; replacement-character count is zero; no tofu or wrong glyph is visible.
- The full Bayes/collapsed-Gibbs route and point-parameter/mean-field-VEM route are mathematically distinct and correctly labeled. Arrow directions and the caption's limitation are consistent with the source and adjacent chapter text.
- The two route encodings remain distinguishable in grayscale by solid versus dashed strokes and arrowhead style. Page integration and caption wrapping are balanced.

## Decision under the current hard-fail rule

No current-PDF missing glyph, tofu, wrong codepoint, actual unreadability, severe imbalance, true clip, illegal visible-ink overlap, mathematical error, semantic error, or geometry error was found.

RESULT=`PASS`  
RETURN=`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
