# FIG-P683-01 isolated fresh SA3 visual acceptance

HANDOFF_ID = C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1

SA3_MODEL = gpt-5.6-sol

SA3_REASONING = xhigh

SA1_MODEL = NOT_OBSERVED_BY_ISOLATED_SA3

SA1_REASONING = NOT_OBSERVED_BY_ISOLATED_SA3

SA2_MODEL = NOT_OBSERVED_BY_ISOLATED_SA3

SA2_REASONING = NOT_OBSERVED_BY_ISOLATED_SA3

SA2_ESCALATED = NOT_OBSERVED_BY_ISOLATED_SA3

SOURCE_FONT_PASS = true

PIXEL_HEIGHT_PASS = true

SAME_CLASS_RATIO_PASS = true

ROLE_RATIO_PASS = true

OVERLAP_CANDIDATE_PIXEL_COUNT = 0

MASK_CONTAMINATION_PIXEL_COUNT = 0

OVERLAP_PIXEL_COUNT = 0

PIXEL_ADJUDICATION_STATUS = CLEAR

PIXEL_ARBITER_MODEL = NOT_USED

PIXEL_ARBITER_REASONING = NOT_USED

CLIP_PIXEL_COUNT = 0

MIN_TEXT_CLEARANCE_PX = 4

VISUAL_HARMONY_PASS = true

MATH_SEMANTICS_PASS = true

TEXT_CONSISTENCY_PASS = true

GRAYSCALE_PASS = true

PAGE_INTEGRATION_PASS = true

GLYPH_CODEPOINT_PASS = true

DENOMINATOR_N = 31

UNORDERED_PAIR_EXPECTED = 465

UNORDERED_PAIR_MANUALLY_JUDGED = 465

UNRESOLVED_PAIR_COUNT = 0

## Manual basis

The official R115 input identity matched the fixed byte counts and SHA-256 values. The target was independently located by current caption text on physical PDF page 732 (printed page 719). I opened the full page at native 300 dpi, the native 300 dpi figure+caption crop, grayscale crop, text/object/semantic overlays, and native1x plus nearest8x versions of every one of the nine selected critical ROIs.

Every visible glyph/codepoint in the 17 text/formula IDs is present and correct; no tofu, missing character, substituted codepoint, or wrong mathematical index is visible. The legacy declared sizes range from 9.0 to 9.6 pt, but under R168 those numeric thresholds are advisory rather than autonomous hard failures. Actual native300 ink, full-page reading, and nearest8x inspection show no genuinely unreadable text or severe role imbalance. Lowercase Greek α measures 20 ink pixels; mixed node formulas measure 28–38; CJK plate/legend text measures 34–40; caption lines measure 38–43. All are visibly readable in page context and close inspection.

The diagram preserves the complete Bayes LDA semantics: α→θ_m, θ_m→z_mn, z_mn→w_mn, β→φ_k, φ_k→w_mn; N_m is nested in M; K is separate; hyperparameters are outside plates; observed/latent/hyperparameter encodings agree with the legend and survive grayscale. The caption and adjacent chapter equations agree with the graph.

All 465 unordered pairs were manually judged after observation. Arrow-to-node endpoint contacts and arrow crossings of replication boundaries are required topology, not illegal text or object collisions. No arrow enters text ink; no label touches a node/plate border; no caption line touches another; no clipping or unresolved overlap candidate remains.

## Isolated role verdict

SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE
