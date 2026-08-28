# FIG-P577-01 — SA1 R3 terminal verdict

## Figure hard-gate result: FAIL

Authority is R95 physical page 625 (printed 612), SHA-256 `24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496`. R94 page 625 is a zero-pixel-difference bridge only; it is not an authority. Evidence completeness is reported separately in `machine_integrity.json`.

| Failure | Relationship | Measured hard-gate reason | Native evidence |
|---|---|---|---|
| TG457 | P_TICK_Y_0_8 to G10_ACCEPT_BORDER | 2.000px < required 5px | `critical_TG457_R95/TG457_measurement.csv` |
| OCC_P_LEGEND_BLUE_GROUND | G01_P_CURVE under P_LEGEND_BLUE_GROUND | PRE∩GROUND=302px; semantic final inside ground=0 | `occlusion_R95/P_LEGEND_BLUE_GROUND_G01_P_CURVE_pre_final_covered_overlay_1x.png` |
| OCC_P_MIN_GAP_GROUND | G01_P_CURVE under P_MIN_GAP_GROUND | PRE∩GROUND=304px; semantic final inside ground=0 | `occlusion_R95/P_MIN_GAP_GROUND_G01_P_CURVE_pre_final_covered_overlay_1x.png` |
| OCC_P_FILL_ANNOTATION_GROUND | G01_P_CURVE under P_FILL_ANNOTATION_GROUND | PRE∩GROUND=609px; semantic final inside ground=0 | `occlusion_R95/P_FILL_ANNOTATION_GROUND_G01_P_CURVE_pre_final_covered_overlay_1x.png` |
| OCC_P_ACCEPT_CARD_GROUND | G01_P_CURVE under P_ACCEPT_CARD_GROUND | PRE∩GROUND=1571px; semantic final inside ground=0 | `occlusion_R95/P_ACCEPT_CARD_GROUND_G01_P_CURVE_pre_final_covered_overlay_1x.png` |
| OCC_P_REJECT_CARD_GROUND | G01_P_CURVE under P_REJECT_CARD_GROUND | PRE∩GROUND=1039px; semantic final inside ground=0 | `occlusion_R95/P_REJECT_CARD_GROUND_G01_P_CURVE_pre_final_covered_overlay_1x.png` |

`TG304` and `TG317` are direct R95 PASS replays, not failures. The initial 430 foreign / 392 text-graphic / 17,690 projected-pixel counts are superseded nonterminal diagnostics, not terminal failure statistics.

## Occlusion count definitions

`PRE=11,609` is the extracted R95 p(y) vector before later paint. `COVERED_XOR=PRE∩opaque GROUND=3,825`; six ground intersections are disjoint. `SEMANTIC_FINAL=8,042` uses strict native blue ink within a one-pixel registration dilation of PRE and excludes all opaque label grounds. The scalar 11,609−8,042=3,567 is not a set difference and is not an occlusion metric; exact closure is recorded in `occlusion_R95/P_CURVE_OPAQUE_GROUND_MANUAL_REVIEW.md`.
