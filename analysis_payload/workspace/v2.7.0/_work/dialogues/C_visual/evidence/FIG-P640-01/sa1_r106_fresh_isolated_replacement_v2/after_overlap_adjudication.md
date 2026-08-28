# FIG-P640-01 R106 overlap adjudication

SA1_REVIEW_OUTCOME: CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE  
LOCAL_PASS_COUNTED: false  
GLOBAL_PASS_COUNTED: false  
SA3_AUTHORIZED: false  

- Reviewer: SA1 (`gpt-5.6-sol`, reasoning `xhigh`)
- Handoff: `C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-REPLACEMENT-V2`
- Native measurement frame: official R106 physical PDF page 690, figure crop at native 300 dpi
- Semantic objects: 45 (32 text, 13 graphic)
- Exhaustive unordered pairs: 990/990, unique 990
- Critical relations: 37/37 manually adjudicated
- Targeted native 1×/8× ROI relations: 19/19
- Final-visible raw-mask intersection rows: 0
- Illegal-overlap decisions: 0

## Targeted ROI adjudications

All listed relations were opened at native 1× and/or 8× nearest-neighbor scale and compared to the figure crop. Per-ID reviewer notes and booleans are in `manual_critical_relation_ledger.csv`.

- `P0007`: independent origin tick labels; 15 empty native pixels; CLEAR.
- `P0576`, `P0605`, `P0633`: legend text to its line sample; 12, 12, and 11 empty native pixels; CLEAR.
- `P0796`: endpoint label to ESS curve; source-proven opaque white label background, 8 empty final-visible pixels; CLEAR_WITH_OPAQUE_BACKGROUND.
- `P0799`: endpoint label to open marker; 11 empty native pixels; CLEAR.
- `P0815`: limit note to ESS curve; source-proven opaque white annotation background, 11 empty final-visible pixels; CLEAR_WITH_OPAQUE_BACKGROUND.
- `P0855`: title prose to numerator; same title parent, 6 empty ink pixels; SAME_TITLE_PARENT.
- `P0885`, `P0899`: numerator/denominator to the fraction rule; one formula parent, respectively 4 and 11 empty native pixels; DESIGNED_MATH_COMPOSITION.
- `P0913`, `P0914`, `P0915`: three ACF curves start at the axis at ACF=1; intentional DESIGN_CONNECTION, no unrelated shared final-visible pixel.
- `P0925`, `P0926`, `P0936`: ACF curves share the mathematically required k=0 initial value before separating; COMMON_INITIAL_VALUE, no unrelated collision.
- `P0976`: ESS curve begins at the y-axis value one; intentional DESIGN_CONNECTION.
- `P0979`: endpoint marker remains separated from the axis in final-visible masks; ADVISORY_RASTER_PROXIMITY only under R168.
- `P0983`: open marker denotes and joins the final ESS endpoint; intentional DESIGN_CONNECTION.

The remaining 18 required semantic combinations (`P0573`, `P0574`, `P0575`, `P0580`, `P0601`, `P0602`, `P0603`, `P0608`, `P0628`, `P0629`, `P0630`, `P0635`, `P0789`, `P0790`, `P0791`, `P0808`, `P0809`, `P0810`) were also manually reviewed and are clear or cross-panel clear. They require no targeted ROI because their measured separation is non-critical.

## Opaque-background and paint-order finding

`G010` and `G011` are genuine opaque white source objects behind the endpoint label and limit annotation. The machine inventory retains them as semantic background objects and keeps the curve's pre-occlusion attribution distinct from its final-visible foreground. Quality decisions use only final-visible foreground; no invented halo or page-background subtraction was used.

## SA1 finding

The evidence supports no illegal text-text, text/formula-line, text/formula-marker, legend-curve, annotation-curve, axis-data, or cross-panel collision. Geometry connections and same-formula composition are explicitly classified rather than silently discarded. SA1 records `OVERLAP_PIXEL_COUNT=0` and `CLIP_PIXEL_COUNT=0`, but this remains a candidate outcome pending main acceptance and an independently authorized SA3.
