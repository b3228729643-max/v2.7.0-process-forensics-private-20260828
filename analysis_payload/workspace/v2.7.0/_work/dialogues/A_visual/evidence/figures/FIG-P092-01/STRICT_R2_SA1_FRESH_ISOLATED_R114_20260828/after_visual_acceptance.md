# FIG-P092-01 fresh isolated SA1 visual acceptance

## Identity and frozen inputs

- `HANDOFF_ID = A-R114-P092-SA1-FRESH-ISOLATED-20260828`
- `CANONICAL_INSTANCE = /root/p092_r114_fresh_sa1`
- `SA1_MODEL = gpt-5.6-sol`
- `SA1_REASONING = xhigh`
- `UID = FIG-P092-01`
- `PDF_PHYSICAL_PAGE = 96`
- `PDF_BYTES = 4967122`
- `PDF_SHA256 = C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`
- `SOURCE_BYTES = 2094`
- `SOURCE_SHA256 = EA3FB7B92ED3B7B2755D513B5F3DEECF7D7114E8DC711F3AB2FE50E9C7EE8608`

## Evidence actually opened

The reviewer opened the native 300 dpi physical page, 200 dpi full page, native 300 dpi figure crop, native grayscale crop, object overlay, native1x critical ROI, and nearest-neighbor 8x critical ROI. The denominator was independently frozen as 21 reader-visible objects and all 210 unordered pairs were reviewed manually after those views were opened.

## Mathematical and semantic verification

The source plots

\[
H_2(p)=-\frac{p\ln p+(1-p)\ln(1-p)}{\ln 2}.
\]

It satisfies the continuously extended endpoints `H_2(0)=H_2(1)=0`, symmetry `H_2(p)=H_2(1-p)`, derivative `H_2'(p)=log_2((1-p)/p)`, strict concavity on `(0,1)`, and the unique maximum `H_2(1/2)=1` bit. The endpoint markers, maximum marker, dashed guides, axis labels, annotations, caption, and adjacent current V1-C06 prose all agree with those facts.

## R168 hard-gate decision

- `MISSING_TOFU_WRONG_CODEPOINT = false`
- `MATH_MEANING_ERROR = false`
- `ACTUAL_UNREADABILITY = false`
- `OBVIOUS_IMBALANCE = false`
- `TRUE_CLIPPING = false`
- `ILLEGAL_VISIBLE_INK_OVERLAP = false`
- `SEMANTIC_OR_GEOMETRIC_ERROR = false`
- `SOURCE_FONT_REVIEW = PASS_UNDER_R168`
- `PIXEL_READABILITY_REVIEW = PASS_UNDER_R168`
- `SAME_CLASS_HARMONY = PASS_UNDER_R168`
- `ROLE_HARMONY = PASS_UNDER_R168`
- `GRAYSCALE = PASS`
- `PAGE_INTEGRATION = PASS`
- `CAPTION = PASS`
- `MATH_SEMANTICS = PASS`
- `TEXT_CONSISTENCY = PASS`
- `UNRESOLVED_PAIR_COUNT = 0`
- `ADJUDICATION_STATUS = CLEAR`

Older numeric font-size, pixel-height, role-ratio, taxonomy, and microgrid thresholds were retained only as advisory context and were not used alone to cause failure.

## Sealed SA1 decision

`RESULT = PASS`

`OUTCOME = SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
