# FIG-P756-01 — R97 independent SA1 strict final report

## Scope, identity, and direct location

This package audits only the locked R97 candidate:

- Candidate: `.../src/build/strict_current_r97_fullbook/main_full.pdf`
- Candidate SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`
- PDF pages: 813.  Figure 37.8 is on physical PDF page 801 / printed page 788,
  at a 300-dpi native raster of 2481 x 3508 px.  The direct page text is in
  `page_801_direct_text.txt`; `candidate_identity.json` records its integer
  crop `[300,700,2150,1995]`.
- Figure source: `.../V5-C08/full_course_synthesis_map.tex`, SHA-256
  `00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA`.
  The candidate's `.aux` contains `fig:V5-C08-course-map` and its `.fls`
  names this source.  This direct R97 locator supersedes the historical
  goal-side page reference that differed from the current 813-page candidate.

I opened the final candidate page in native 300 dpi and full-page 200 dpi,
the 300-dpi figure crop, standalone view, and 300-dpi grayscale view.  The
caption, lead-in, read-figure prose, graph body, and source agree: the top
five-station chain has its stated feedback path; both lower task routes enter
the one shared four-engine pool; the validation-to-report path is one-way.
The signed direct-context rows are in `reviewer_semantic_context_ledger.csv`
and the visual-view rows are in `reviewer_visual_harmony_ledger.csv`.

## Text, masks, and typography

- PDF rawdict has 253 character records: 251 visible mapped glyphs and two
  explicit non-ink whitespace/empty records; unresolved combining or zero-width
  glyphs: 0.  `rawdict_character_reconciliation.csv` closes the two directions
  between rawdict sequence and each `Cxxxx` glyph.
- All 251 glyphs have their own final 300-dpi raw mask, pre-segmentation claim
  mask, and 8x nearest-neighbor card.  The 16 `glyph_contact_sheets` contain
  exactly 251 cells.  Each actual cell was opened and immediately signed in
  `reviewer_glyph_manual_ledger.csv`: original/overlay/mask-only match YES,
  missing pixels 0, foreign glyph pixels 0, and foreign graphic pixels 0.
- Eight low-profile punctuation glyphs have independent same-font/size/colour
  reference calibration, 1x/8x proof, and individual reviewer rows in
  `low_profile_calibration.csv` and
  `reviewer_low_profile_manual_ledger.csv`; all eight are PASS.  No low-profile
  result reuses a parent line or adjacent glyph mask.
- All normal source text is 9.60 pt or greater; panel titles are 10.20 pt.
  `after_font_audit.csv` covers 25 text objects and
  `font_harmony_by_element.csv` covers 37 element/script rows.  Same-role,
  same-panel source sizes are exactly equal (ratio 1.000000); shared
  cross-panel `ANNOTATION` and `PANEL_TITLE` ratios are also 1.000000.
  The page-wide max/min source-size ratio is 1.062500.  The single a/b panel
  labels are recorded as an explicitly non-comparable raw-shape case, not a
  hidden pass; their declared size and opened visual hierarchy are identical.
  The 25 per-object four-view/8x reviewer rows support
  `FONT_VISUAL_HARMONY_PASS: true` in `after_visual_acceptance.md`.

## Complete foreground/path accounting

The current object inventory contains 25 text objects and 44 graphic objects:
69 total.  All 53 page drawings were inspected.  Thirty-nine intersect the
figure and all 39 map to the 44 semantic graphic objects in
`all_pdf_drawing_path_inventory.csv`; the additional five objects are the
separately auditable FILL/BORDER pairs for the five badge `fs` paths.  The
44 graphic card index, manual ledger, and actual card set are each exactly
44.  This includes every visible node/panel border, shaft, arrowhead, opaque
background, badge fill, badge border, double-frame dark component, and white
separator; it is not a semantic aggregation that omits collision objects.

There are no displayed mathematical formula rules in this figure.  Source
lines 35--81 contain no overline, underline, hat/vector accent, radical,
fraction, or cancellation rule; every 39 in-figure path is classified
`NONE_TIKZ_NONFORMULA_PATH`, and the independent `MATH_AND_PATH_RULES` context
row is `NOT_APPLICABLE_NO_MATH_RULE`.  Thus the `GRAPHIC/MATH_RULE` denominator
is explicitly 0 and the drawing/path denominator is completely accounted for,
rather than being inferred from rawdict alone.

The badge split is particularly material.  For each of G014--G018, final
visible BORDER is a unique stroke-only mask and FILL is only its opaque
background geometry.  FILL/BORDER overlap is 0 for all five.  The true
digit-to-stroke clearances, in order, are 19.416488, 19.104973, 19.697716,
19.646883, and 18.973666 px, all over the 5-px node-text gate.  The old
fill-contaminated 1-px conclusion is therefore not used.

G030/G031 are separately evidenced as a blue double-frame plus the intended
white separator: dark final-visible pixels 3890, white separator geometry
pixels 3385, unique-mask intersection 0, and 270 dark candidate pixels
reassigned by paint order to the separator.  Its native, mask, overlay,
8x-nearest, grayscale, and four-view files are named by
`z_order_evidence/G030_G031_zorder_measurement.csv` and are manually signed.

## All unordered relations and critical inspection

All `C(69,2) = 2346` unordered pairs are measured on final visible native
300-dpi masks: TT 300, TG 1100, GG 946.  No pair has overlap pixels, no
crop-edge object has touch pixels, and the report records zero clipping.
There are 1868 ordinary PASS pairs, 455 pairs correctly exempted because the
opaque fill/background is not a competing foreground object, and 23
pair-specific intentional contacts.  The latter are not a class waiver:
each names its source anchor or component relation in `object_pair_report.csv`.

The final critical set is exactly 32 pairs, with 32 review-index rows, 32
manual rows, 32 five-up cards, and 160 constituent native/mask/overlay/8x
cards.  Every card was opened at 1x and 8x nearest with both unique masks and
the original/overlay, then individually signed.  Decisions are: 9 arrow
shaft/head component contacts, 5 badge-to-station intentional overlays, 9
source-anchor endpoint contacts, and 9 no-defect near relations.  The allowed
endpoint contacts are limited to the exact `problem.east` through
`boundary.west`, feedback, route/pool, pool/validation, and validation/report
anchors on source lines 43--53 and 76--79.  There is no evidence of contact
beyond its named endpoint.

Three former 35-set candidates are retained in the full pair table but no
longer meet the critical trigger after final mask ownership: digit--station
rims at 25.079872 px (two) and station--feedback shaft at 17.029386 px.
`critical_set_delta_35_to_32.csv` explains all three; superseded 64-object
cards are isolated under `SUPERSEDED__DO_NOT_USE` and are excluded from every
current index and conclusion.

## Final strict gates and terminal decision

The final machine crosscheck independently verifies candidate/source identity,
all cardinalities, ordinary readable PNG references, 0 mathematical rules
against the complete drawing inventory, glyph/rawdict closure, manual ledger
closure, graphic/card closure, pair partition, current critical-card closure,
badge and z-order evidence, source lines, crop/clip, and font/visual ledgers.
Its pre-terminal result is 0 errors in `FINAL_MACHINE_CROSSCHECK.json`;
the same check is rerun after writing the terminal record.

No unapproved overlap, insufficient non-whitelisted clearance, crop, mask
pollution, empty graphic mask, glyph-size failure, font D/E failure, semantic
contradiction, or visual-hierarchy failure remains in the locked candidate.
The independent SA1 terminal decision is therefore:

`PASS_TO_ROOT`

The manifest is generated only after this completed report and the terminal
records.  `WRITE_STOPPED` is created after the manifest and is the final
workspace write.
