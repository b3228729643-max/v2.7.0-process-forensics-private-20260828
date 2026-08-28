# FIG-P610-01 R104 independent SA3 result

RESULT: PASS

LOCAL_STATUS: C_LOCAL_PASS_ONLY

TASK_ID: FIG-P610-01

HANDOFF_ID: C-FIG-P610-01-R104-SA3-FRESH-ISOLATED-V1

REVIEWER_TYPE: AI_SA3_VISUAL_REVIEW

HUMAN_CERTIFICATION: false

MODEL: gpt-5.6-sol

REASONING_EFFORT: xhigh

INDEPENDENT_COVERAGE: Independently mapped label `fig:V5-C03-rejection-vs-mh` and its caption to official R104 physical page 662 / printed page 649 / Figure 32.10. Reviewed the current sole figure source, necessary adjacent V5-C03 text, full-page 300 dpi and 200 dpi, figure-with-caption 300 dpi, standalone-equivalent 300 dpi, grayscale 300 dpi, 1x and 8x closest-region views, 77/77 visible non-whitespace glyph IDs, 38/38 actual semantic object IDs, all 703 unordered object pairs, 26 closest pair IDs, peer-role aggregates, text-to-border clearances, clip evidence, formula meaning, geometry, relations, object content, caption, and adjacent-text consistency.

BLOCKERS: none

NEW_REGRESSIONS: none observed on the affected page and figure views.

MATHEMATICAL_FINDINGS: Candidate labels and state sequence are correct. The left panel omits rejected `Y_2`; the MH panel retains `Y_1` after rejecting `Y_2`, giving `Y_1 -> Y_1 -> Y_3`. No wrong mathematical glyph, subscript, direction, or state semantics.

VISUAL_FINDINGS: Two panels are aligned and balanced; solid/dashed/double-ring/`×` encoding survives grayscale. No true clipping, illegal overlap, tofu, wrong code point, actual unreadability, or severe font imbalance. The nearest text-related clearance is 13.560220 px. The right middle proposal connector ends 3 px before the repeated-state double border; this is a legitimate connected-object endpoint and the R168 5 px main-line-gap rule is advisory only.

SOURCE_FONT_AUDIT: Hard gate clear under R168. Source base is 9.2 pt, titles 10.2 pt, rejection signs 14 pt, annotations 8.5 pt, graphics scale 1.0 with no resizebox/scalebox/transform-shape shrinkage in the figure source or adjacent include. The 8.5 pt annotation declaration, natural 4 px horizontal strokes (`–`, `一`), mixed-script bbox taxonomy, and minor peer/font metadata variations are explicitly advisory; direct 300 dpi inspection shows all glyphs readable and correct.

PIXEL_HEIGHT_AUDIT: 77 glyphs individually reviewed. Titles occupy 40 px element height; node labels 37--39 px; rejection marks 34 px; annotation lines 41 px, with ordinary CJK annotation glyphs predominantly 31--33 px and math glyphs/subscripts visibly intact. Natural single-stroke glyphs are interpreted by their actual shape rather than a square-glyph height taxonomy.

SAME_CLASS_RATIO_AUDIT: Left node-label range 37--39 px (max/min 1.054054); right node-label range 37--39 px (1.054054); cross-panel node median 37 px vs 37 px; titles 40 px vs 40 px; annotations 41 px vs 41 px; rejection marks 34 px vs 34 px. No severe imbalance.

ROLE_RATIO_AUDIT: Titles are slightly larger and bold; nodes/formulas remain the main semantic objects; notes are lighter and subordinate. Latin/CJK glyph-height and mixed-script bbox differences are natural and recorded as R168 taxonomy advisories.

OVERLAP_PIXEL_AUDIT: 38 actual objects imply 703 unordered pairs; the raw ledger contains exactly 703 unique rows. `OVERLAP_CANDIDATE_PIXEL_COUNT=0`, `MASK_CONTAMINATION_PIXEL_COUNT=0`, canonical `OVERLAP_PIXEL_COUNT=0`, and `PIXEL_ADJUDICATION_STATUS=CLEAR`. No unresolved cluster exists. All required text-text, text/formula-line/arrow, text/formula-node-border, text/formula-panel-border pairs are present where object classes exist; marker, legend, and data-curve classes are absent from this diagram by actual-object inventory.

CLIP_AUDIT: `CLIP_PIXEL_COUNT=0`. Seventeen reader text/formula elements have explicit page-edge and panel-border measurements; every semantic graphical object and both arrowheads are visibly complete in full-page, figure, standalone, and 8x views.

MIN_TEXT_CLEARANCE_PX: 13.560220

VISUAL_HARMONY_AUDIT: Clear in full page, figure crop, standalone-equivalent, grayscale, 1x, and 8x views. Panel balance, whitespace, line hierarchy, arrow direction, and caption placement are coherent.

HARD_GATE_MATRIX:

- SOURCE_FONT_PASS = true (R168 hard-font interpretation)
- PIXEL_HEIGHT_PASS = true (actual readable/correct glyph gate)
- SAME_CLASS_RATIO_PASS = true (no severe imbalance; minor taxonomy advisory only)
- ROLE_RATIO_PASS = true (no severe hierarchy distortion)
- VISUAL_HARMONY_PASS = true
- MATH_SEMANTICS_PASS = true
- GEOMETRY_PASS = true
- RELATIONSHIPS_PASS = true
- OBJECT_CONTENT_PASS = true
- TEXT_CONSISTENCY_PASS = true
- GRAYSCALE_PASS = true
- PAGE_INTEGRATION_PASS = true
- OVERLAP_CANDIDATE_PIXEL_COUNT = 0
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = CLEAR
- CLIP_PIXEL_COUNT = 0

ADVISORIES:

1. Source annotation style declares 8.5 pt, below the earlier metadata target, but direct native-300-dpi and 8x inspection finds no actual unreadability; R168 makes this advisory.
2. The main vertical connector below the right rejection mark has a measured 3 px true white gap to the double-state border. It has zero overlap, is a legitimate endpoint relation, and R168 makes the designated 5 px main-line gap advisory.
3. One-stroke glyphs `–` and `一` have 4 px measured ink height because their correct glyph geometry is a horizontal stroke; they are clear in 1x/8x and are not missing/tofu/wrong glyphs.

REQUIRED_ACTIONS: none for SA3 hard gates. Main thread must perform its own integration/root acceptance; this local result does not claim global or final acceptance.

EVIDENCE_USED: See sealed manifest after sealing. Principal files are `full_page_native_300dpi.png`, `figure_crop_with_caption_native_300dpi.png`, `standalone_equivalent_native_300dpi.png`, `standalone_equivalent_grayscale_300dpi.png`, `standalone_1x_native_300dpi.png`, `standalone_8x_nearest_inspection.png`, focused 1x/8x critical crops, overlays, per-object masks, raw inventories and pair ledgers, and the manual per-ID review ledgers.
