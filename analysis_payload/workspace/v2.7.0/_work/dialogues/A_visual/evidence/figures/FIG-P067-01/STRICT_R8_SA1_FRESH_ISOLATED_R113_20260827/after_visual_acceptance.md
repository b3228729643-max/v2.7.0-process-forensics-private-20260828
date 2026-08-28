# FIG-P067-01 fresh isolated SA1 visual acceptance

## Identity

- Reviewer identity: `/root/p067_r113_fresh_sa1`
- Handoff ID: `A-R113-P067-SA1-FRESH-ISOLATED-20260827`
- Role: single fresh isolated SA1 only
- Official candidate: frozen R113 `main_full.pdf`, physical page 69, printed page 56, Figure 4.1
- Current source: `fig_v1_c04_cdf.tex`; read-only and unchanged

## Frozen denominator and evidence closure

- Visible glyphs: 95/95, G001-G095; all contact originals/overlays/masks opened.
- Foreground drawings: 35/35, D001-D035; all drawing records mapped.
- Real opaque text backgrounds: 5/5 separately inventoried with paint-order effect.
- Math-rule paths: 0, after PDF text-trace and drawing-path reconciliation; the figure contains no fraction/radical/accent/overline/underline rule.
- Final visible-object denominator: N=130.
- Unordered pairs: C(130,2)=8,385; enumerated 8,385/8,385.
- Independent near/overlap-candidate pairs: 99/99 opened in five overview sheets; all manual outcomes recorded.
- Native views: page 300 dpi, figure crop 300 dpi, standalone 300 dpi, grayscale 300 dpi, full page 200 dpi, four 8x nearest-neighbour ROIs.

## R168 real hard gates

| Hard gate | Result | Evidence-based conclusion |
|---|---|---|
| Missing/tofu/wrong codepoint | PASS | 95/95 glyphs present; replacement count 0; tofu suspects 0; caption/axis/note codepoints agree with source. |
| Mathematical meaning | PASS | PMF masses 0.15+0.30+0.35+0.20=1; cumulative plateaus 0.15/0.45/0.80/1; nondecreasing right-continuous CDF. |
| Actual unreadability | PASS | Every label, tick, annotation, endpoint and caption is readable at native 300 dpi and in grayscale. |
| Obvious imbalance | PASS | Panels, label hierarchy, annotations, caption and page placement are visually balanced. |
| Real clipping | PASS | No foreground reaches a page or frozen crop edge; `CLIP_PIXEL_COUNT=0`. |
| Illegal overlap | PASS | Manual adjudication finds no illegal independent-object collision; `OVERLAP_PIXEL_COUNT=0`. |
| Semantic/geometric error | PASS | Open/filled endpoints encode right continuity correctly; PMF stems align with CDF jumps; axes and caption are correct. |

## R168 advisories, not hard failures

The local source declares 8.6-9.4 pt plot typography, and nine machine glyph rows fall below a legacy strict-reference pixel/taxonomy threshold. All were manually opened and are actually readable. Several glyph bbox masks contain tiny adjacent/context antialias pixels; the three resulting low-clearance candidates R00229, R00230 and R01219 were inspected in native originals and 8x nearest-neighbour overlays and are not real collisions. These micro font/pixel/taxonomy and extraction-fringe differences are recorded, not hidden, and are advisory under the task's R168 rule.

`FONT_VISUAL_HARMONY_PASS=true`

`OVERLAP_PIXEL_COUNT=0`

`CLIP_PIXEL_COUNT=0`

## Decision

This is a local fresh isolated SA1 decision only. It does not claim SA3, A_LOCAL, root acceptance, global pass, or final project completion.

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

