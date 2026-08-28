# FIG-P608-01 R104 fresh replacement SA1 visual acceptance

- HANDOFF_ID: `A-R104-P608-SA1-FRESH-REPLACEMENT-20260826`
- role: isolated read-only SA1 replacement
- candidate: `strict_current_r104_fullbook/main_full.pdf`
- candidate SHA-256: `e5c871642fbddbec6508be1b61bd911fe281ca5acfbd16b0449b13357770a641`
- source SHA-256: `78c30f4a934f63e0ef1bbacf400a24f22477d38589f99503ae468f7024a35c05`
- independently located physical page: 661 (zero-based PDF page index 660)
- decision time: `2026-08-25T19:11:22.5813379Z`
- report assembly time: `2026-08-25T19:18:03.1541131Z`
- result: `FAIL_TO_SA2`

## Fresh location and candidate identity

The page was located from the R104 candidate itself by the unique co-occurrence of `预热段`, `运行均值`, and `本图仅作诊断`. No prior P608 page number, report, handoff, root conclusion, or evidence directory was used. The PDF page is A4 at 595.276 x 841.890 pt.

The page-native views are:

- `views/full_page_200dpi.png`: 1654 x 2339 px.
- `views/figure_crop_300dpi.png`: 1855 x 951 px, direct PDF render from global integer pixel rectangle `[291,916,2146,1867]`.
- `views/standalone_300dpi.png`: 1605 x 897 px, direct PDF render from global integer pixel rectangle `[416,895,2021,1792]`.
- `views/grayscale_300dpi.png`: direct grayscale PDF render of the figure crop.

No post-render resize was used for measurement images. Nearest-neighbour enlargements appear only in review sheets.

## Object and relationship denominator

The fixed denominator is 128 objects:

- 68 visible glyph objects, each with a unique `TXT-nnn` ID and ordinary PNG mask.
- 60 graphic objects: 58 PDF drawing/path objects and two explicitly identified warm-up pattern aggregates.
- The graphic denominator includes six `GRAPHIC/MATH_RULE` objects: four horizontal rules composing the two visible equals signs and two overline rules.

All unordered pairs were enumerated exactly once: `C(128,2) = 8,128`. `machine/all_unordered_pairs.csv` contains 8,128 rows. Object IDs are unique; all 128 ordinary mask PNG files exist and open; no NTFS alternate-stream naming is used.

## Source fonts and R168 treatment

The whitelisted source declares 9.6 pt for the base/tick/annotation roles and 10.8 pt for axis labels and titles, with no `resizebox`, `scalebox`, `scale=`, or `transform shape`. The subscript `t`, `6`, and `6:t` contours are natural formula scripts. The small PDF metadata difference between declared TeX points and PDF points is advisory under R168.

All 68 glyph contact cells were opened and reviewed. There is no tofu, wrong codepoint, missing stroke, foreign-pixel contamination in the glyph masks, or actually unreadable glyph. The machine table's four legacy pixel/taxonomy advisories concern natural subscript `6` and `:` contours; manual review classifies them as intact and readable natural scripts under R168. They are not hard failures.

`FONT_VISUAL_HARMONY_PASS=true`: title, annotation, tick, axis-label, and formula roles are balanced across the two panels; no text is visibly too small, oversized, crowded, or dominant.

## Semantic and visual checks

The lower series was recomputed from the upper retained samples in the whitelisted TeX source. All 15 plotted running means agree at the stated source precision and the final mean is 2.0000. The caption's diagnostic-only statement is consistent with the plotted content. The equals signs and overlines are visually present and semantically attached to their formulas.

The figure remains readable in color and grayscale, and its page placement, caption, margins, and surrounding prose are balanced. Text clipping count is zero. The smallest displayed independent text-to-line/arrow critical clearances are 14 px or more against the 3 px hard threshold.

## Hard failures

The upper-panel first circular marker at `t=1` is centered on the independent y-axis and occupies the y-axis arrowhead base. Native 1x and 8x evidence is in the first three rows of `views/critical_pair_sheet_01.png`:

- `PAIR-06596` (`GFX-D010` y-axis versus `GFX-D019` first marker): true visible overlap/occlusion; hard FAIL.
- `PAIR-06650` (`GFX-D011` y-arrowhead versus `GFX-D019` first marker): true visible contact and merge; hard FAIL.

This is a geometric relationship failure, not a micro-pixel typography advisory. Axis components and a data marker are independent foreground objects; the marker is not an axis arrowhead component. Therefore `OVERLAP_PIXEL_COUNT=0` is not satisfied.

The current evidence extraction also cannot clear `PAIR-06428`: the aggregate y-tick mask contains unrelated same-color pixels near the first marker. Both warm-up pattern aggregate masks likewise include foreground curve/marker pixels. These mask-purity failures independently prohibit PASS for this evidence round; they do not create or erase the visually confirmed marker-axis-arrow collision.

## SA2 direction

Preserve the fixed data values and running-mean semantics, but give the first sample native separation from the y-axis and its arrowhead. A direct source-level option is to extend the x-domain below 1 (and preferably symmetrically above 20) while retaining ticks at 1, 5, 10, 15, and 20; the exact repair must be re-rendered and re-audited. The next fresh SA1 evidence generator must also isolate tick and pattern masks without same-color foreground contamination.

## Verdict

`FAIL_TO_SA2`

SA3 must not start from this result. This report does not declare `A_LOCAL_PASS`.
