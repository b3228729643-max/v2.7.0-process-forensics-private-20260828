# FIG-P598-01 — after visual acceptance

## Frozen target

- HANDOFF_ID: `A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825`
- independent role: SA3
- model/effort: `gpt-5.6-sol/xhigh`
- frozen target: R104 `main_full.pdf`, physical page 649
- PDF identity: 817 A4 pages; 4,967,222 bytes; SHA256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- native render: 2481 x 3508 px at 300 dpi
- crop: `[230,2040,2195,2765]`, 1965 x 725 px

## Evidence completion

- visible glyphs: 142/142 manually PASS
- visible graphic/path objects: 26/26 manually PASS
- complete object denominator: 168/168 manually PASS
- all unordered pairs: 14,028/14,028 accounted
- raw intersection pairs: 17/17 intentional and allowed
- critical/nearest relationships: 19/19 manually PASS
- final illegal overlaps: 0
- crop clipping: 0 px
- empty masks: 0
- complete text contact sheets opened: 24/24
- complete graphic contact sheets opened: 5/5
- pair matrices opened: 2/2
- critical relationship sheets opened: 4/4
- white-separator pre/halo/final views opened: 12/12
- native crop, standalone, grayscale, 300-dpi page, and 200-dpi page opened: yes
- terminal machine cross-check: PASS
- machine outputs contain manual fields: false

## Human acceptance

The full figure visibly contains the required state sequence `a,b,b,c,c,b,a` at `t=0,1,2,3,4,5,T`, six continuous directed transitions, a left-to-right time axis with equal state spacing, and the repeated-state/adjacent-correlation cues (`保持` plus the dashed b-to-b arc). The transition kernel is `K(x_t,\mathrm d x_{t+1})`; the caption contains `K(x,\mathrm d y)` and `x→y` with correct semantics. The four intended double-circle nodes retain their wide blue border, genuine white separator, and inner dark ring. The caption and bottom note integrate cleanly with the page.

Under R168, sub-9.5-pt source values, fine taxonomy/ratio checks, naturally short glyph heights, and isolated 1–2 px effects are advisory. They do not cause a hard failure: there is no missing/tofu glyph, wrong codepoint, wrong mathematical meaning, unreadable content, severe visible imbalance, clipping, or illegal overlap. Native 1x, 8x-equivalent, grayscale, and lower-resolution observations agree.

`FONT_VISUAL_HARMONY_PASS=true`

## Decision

`SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`
