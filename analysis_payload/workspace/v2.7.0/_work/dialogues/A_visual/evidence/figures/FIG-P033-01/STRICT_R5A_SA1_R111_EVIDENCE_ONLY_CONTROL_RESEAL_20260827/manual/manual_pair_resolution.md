# FIG-P033-01 manual pair resolution - 81 observed rows

This ledger was authored after actually opening the final native1x and nearest8x evidence. Each row preserves the frozen pair ID and records the object-specific visual observation. `illegal px` is the canonical count of real, disallowed foreground collision pixels; intended geometric endpoints and opaque support fills are not counted as illegal foreground collisions.

| pair_id | object A | object B | opened evidence | object-specific observation | decision | illegal px |
|---|---|---|---|---|---|---:|
| PAIR-0469 | GLYPH-005 `𝑥` | PATH-003 x shaft | ROI-06 1x/8x | The `𝑥` glyph sits above-left of the blue shaft; the long slanted shaft bbox reaches its bbox, but blue pixels do not enter the black glyph. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0560 | GLYPH-006 projection `𝑝` | PATH-001 upper S edge | ROI-05 1x/8x | The leading `𝑝` is below the band; the upper S edge is visibly above it and never meets the glyph ink. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0561 | GLYPH-006 projection `𝑝` | PATH-002 lower S edge | ROI-05 1x/8x | The lower S edge passes just above the label line; a white gap remains above the `𝑝` ascender. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0562 | GLYPH-006 projection `𝑝` | PATH-003 x shaft | ROI-05/06 1x/8x | The blue x shaft is far above-left at this x-position; only its axis-aligned bbox covers the `𝑝`. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0563 | GLYPH-006 projection `𝑝` | PATH-004 p shaft | ROI-05 1x/8x | The teal p shaft is above the projection formula; the leading `𝑝` remains fully black and uncut. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0652 | GLYPH-007 projection `=` | PATH-001 upper S edge | ROI-05 1x/8x | The upper band edge is well above the equals bars; neither gray stroke crosses either black bar. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0653 | GLYPH-007 projection `=` | PATH-002 lower S edge | ROI-05 1x/8x | The lower band edge ends above the equals sign; both horizontal bars are complete. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0654 | GLYPH-007 projection `=` | PATH-003 x shaft | ROI-05/06 1x/8x | The x shaft bbox spans this location, but the actual blue diagonal is remote from the equals sign. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0655 | GLYPH-007 projection `=` | PATH-004 p shaft | ROI-05 1x/8x | Teal p pixels stay above the black equals bars; the formula remains visually continuous. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0743 | GLYPH-008 projection `𝑃` | PATH-001 upper S edge | ROI-05 1x/8x | The capital `𝑃` is below the plane; its ink has no contact with the upper boundary. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0744 | GLYPH-008 projection `𝑃` | PATH-002 lower S edge | ROI-05 1x/8x | The lower gray edge runs above the `𝑃`; the top serif/curve remains separated. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0745 | GLYPH-008 projection `𝑃` | PATH-003 x shaft | ROI-05/06 1x/8x | Actual x-shaft ink is near the left triangle, not on the `𝑃`; bbox overlap is purely geometric-envelope inflation. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0746 | GLYPH-008 projection `𝑃` | PATH-004 p shaft | ROI-05 1x/8x | The teal projection arrow stays above the formula and leaves the `𝑃` intact. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0833 | GLYPH-009 projection subscript `𝑆` | PATH-001 upper S edge | ROI-05 1x/8x | The subscript `𝑆` is below the band; the upper boundary is remote. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0834 | GLYPH-009 projection subscript `𝑆` | PATH-002 lower S edge | ROI-05 1x/8x | The nearest gray edge remains above the subscript; every `𝑆` stroke is visible. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0835 | GLYPH-009 projection subscript `𝑆` | PATH-003 x shaft | ROI-05/06 1x/8x | The 2.7416 px bbox advisory is caused by the long x-shaft envelope; actual blue pixels are far above the subscript. | CLEAR_NEAR_BBOX_ADVISORY | 0 |
| PAIR-0836 | GLYPH-009 projection subscript `𝑆` | PATH-004 p shaft | ROI-05 1x/8x | The p shaft is above the formula baseline and does not touch the lowered subscript `𝑆`. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0922 | GLYPH-010 projection `𝑥` | PATH-001 upper S edge | ROI-05 1x/8x | The formula's `𝑥` is below the plane and wholly separated from the upper edge. | CLEAR_FALSE_BBOX | 0 |
| PAIR-0923 | GLYPH-010 projection `𝑥` | PATH-002 lower S edge | ROI-05 1x/8x | A visible white strip separates the lower S edge from the formula `𝑥`. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-0925 | GLYPH-010 projection `𝑥` | PATH-004 p shaft | ROI-05 1x/8x | The teal shaft lies above; the black `𝑥` is complete and unobscured. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-1010 | GLYPH-011 projection `∈` | PATH-001 upper S edge | ROI-05 1x/8x | The membership sign is far below the upper plane boundary. | CLEAR_FALSE_BBOX | 0 |
| PAIR-1011 | GLYPH-011 projection `∈` | PATH-002 lower S edge | ROI-05 1x/8x | The lower gray edge stays above the `∈`; all three sign strokes are visible. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-1013 | GLYPH-011 projection `∈` | PATH-004 p shaft | ROI-05 1x/8x | Teal arrow pixels do not enter the membership sign. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-1097 | GLYPH-012 terminal `𝑆` | PATH-001 upper S edge | ROI-05 1x/8x | The final `𝑆` of `∈S` is below and right of the upper edge with no contact. | CLEAR_FALSE_BBOX | 0 |
| PAIR-1098 | GLYPH-012 terminal `𝑆` | PATH-002 lower S edge | ROI-05 1x/8x | The lower plane edge remains above the final `𝑆`; its curved ink is complete. | CLEAR_WITH_VISIBLE_GAP | 0 |
| PAIR-1187 | GLYPH-013 residual `𝑟` | PATH-005 residual shaft | ROI-03 1x/8x | The dashed residual is left of the label; no gray dash crosses the black `𝑟`. | CLEAR_FALSE_BBOX | 0 |
| PAIR-1188 | GLYPH-013 residual `𝑟` | PATH-006 residual white support | ROI-03 1x/8x | The `𝑟` is intentionally printed on the white label support; the support is background and has no visible foreground border. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1195 | GLYPH-013 residual `𝑟` | PATH-013 distance brace | ROI-03 1x/8x | The brace is left of the `𝑟`; its nearest gray curve stops before the glyph. | CLEAR_FALSE_BBOX | 0 |
| PAIR-1273 | GLYPH-014 residual `=` | PATH-006 residual white support | ROI-03 1x/8x | Both equals bars sit on the intended opaque white background; no independent foreground crosses them. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1280 | GLYPH-014 residual `=` | PATH-013 distance brace | ROI-03 1x/8x | The brace's concave turn is left of the equals sign; the bars remain isolated. | CLEAR_FALSE_BBOX | 0 |
| PAIR-1357 | GLYPH-015 residual `𝑥` | PATH-006 residual white support | ROI-03 1x/8x | The residual-formula `𝑥` is fully rendered on its white support with no visible border contact. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1440 | GLYPH-016 residual minus `−` | PATH-006 residual white support | ROI-03 1x/8x | The minus stroke is complete and centered on the intentional white support. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1522 | GLYPH-017 residual `𝑝` | PATH-006 residual white support | ROI-03 1x/8x | The `𝑝` descender and bowl are complete; the white rectangle is only support fill. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1603 | GLYPH-018 residual `∈` | PATH-006 residual white support | ROI-03 1x/8x | The membership sign is intact on the opaque support and not crossed by the dashed residual. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1683 | GLYPH-019 residual `𝑆` | PATH-006 residual white support | ROI-03 1x/8x | The `𝑆` before the perpendicular superscript is fully visible on the support. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1762 | GLYPH-020 residual `⟂` | PATH-006 residual white support | ROI-03 1x/8x | The orthogonal-complement symbol is small but complete; the white support contains no competing foreground. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1835 | GLYPH-021 `最` | PATH-001 upper S edge | ROI-04 1x/8x | The plane edge approaches from the right but is hidden by the opaque label support before reaching `最`; no glyph ink is crossed. | CLEAR_BY_OPAQUE_LABEL_SUPPORT | 0 |
| PAIR-1841 | GLYPH-021 `最` | PATH-007 distance-label support | ROI-04 1x/8x | `最` is intentionally on a white support rectangle; its ink is complete. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1847 | GLYPH-021 `最` | PATH-013 distance brace | ROI-04 1x/8x | The brace remains left of `最`; the 6.7832 px bbox advisory does not correspond to visible ink contact. | CLEAR_NEAR_BBOX_ADVISORY | 0 |
| PAIR-1912 | GLYPH-022 `短` | PATH-001 upper S edge | ROI-04 1x/8x | The upper S edge is suppressed beneath the label support and does not cross `短`. | CLEAR_BY_OPAQUE_LABEL_SUPPORT | 0 |
| PAIR-1918 | GLYPH-022 `短` | PATH-007 distance-label support | ROI-04 1x/8x | `短` is fully formed on its intentional support fill. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-1988 | GLYPH-023 `距` | PATH-001 upper S edge | ROI-04 1x/8x | The gray plane edge reappears only to the right of the support; `距` remains untouched. | CLEAR_BY_OPAQUE_LABEL_SUPPORT | 0 |
| PAIR-1994 | GLYPH-023 `距` | PATH-007 distance-label support | ROI-04 1x/8x | `距` is complete; the intersecting rectangle is non-foreground support. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-2063 | GLYPH-024 `离` | PATH-001 upper S edge | ROI-04 1x/8x | The visible plane boundary begins to the right of `离`; no gray pixel crosses its strokes. | CLEAR_BY_OPAQUE_LABEL_SUPPORT | 0 |
| PAIR-2069 | GLYPH-024 `离` | PATH-007 distance-label support | ROI-04 1x/8x | `离` is intact on the white support, with no support border present. | ALLOWED_SUPPORT_BACKGROUND | 0 |
| PAIR-2150 | GLYPH-025 first `‖` | PATH-014 equation note box | ROI-01 1x/8x | The left norm bar pair has broad white clearance from the rounded box's left and top borders. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2223 | GLYPH-026 equation `𝑥` | PATH-014 equation note box | ROI-01 1x/8x | The `𝑥` is centered inside the box and does not approach any visible border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2295 | GLYPH-027 closing `‖` for x | PATH-014 equation note box | ROI-01 1x/8x | Both closing norm strokes are complete and separated from the rounded border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2366 | GLYPH-028 first superscript `2` | PATH-014 equation note box | ROI-01 1x/8x | The superscript `2` is fully visible below the top border with a clear white gap. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2436 | GLYPH-029 equation `=` | PATH-014 equation note box | ROI-01 1x/8x | The equals sign is centered and isolated from the container border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2505 | GLYPH-030 opening `‖` for p | PATH-014 equation note box | ROI-01 1x/8x | The p-term opening bars remain internal to the box with no border contact. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2573 | GLYPH-031 equation `𝑝` | PATH-014 equation note box | ROI-01 1x/8x | The `𝑝` bowl and descender are complete inside the note box. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2640 | GLYPH-032 closing `‖` for p | PATH-014 equation note box | ROI-01 1x/8x | The p-term closing norm bars are fully separated from the border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2706 | GLYPH-033 second superscript `2` | PATH-014 equation note box | ROI-01 1x/8x | The p-term superscript has clear top clearance and no clipping. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2771 | GLYPH-034 equation `+` | PATH-014 equation note box | ROI-01 1x/8x | The plus sign is centered in open white space, not touching the container. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2835 | GLYPH-035 opening `‖` for r | PATH-014 equation note box | ROI-01 1x/8x | The r-term opening bars remain distinct from the rounded border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2898 | GLYPH-036 equation `𝑟` | PATH-014 equation note box | ROI-01 1x/8x | The final variable `𝑟` is complete, legible, and internal to the box. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-2960 | GLYPH-037 closing `‖` for r | PATH-014 equation note box | ROI-01 1x/8x | The last norm bars have visible white space before the right border. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-3021 | GLYPH-038 final superscript `2` | PATH-014 equation note box | ROI-01 1x/8x | The final superscript is complete and remains below/left of the rounded corner. | CLEAR_CONTAINER_BORDER | 0 |
| PAIR-4762 | PATH-001 upper S edge | PATH-003 x shaft | ROI-06 1x/8x | The blue x shaft crosses the depicted upper band edge once while leaving S from O toward X; both strokes remain traceable. | INTENDED_VECTOR_EXIT_FROM_S | 0 |
| PAIR-4763 | PATH-001 upper S edge | PATH-004 p shaft | ROI-05/06 1x/8x | The teal p shaft stays inside the band below its upper edge; their large bboxes overlap without a native-pixel crossing. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4764 | PATH-001 upper S edge | PATH-005 residual shaft | ROI-04/05 1x/8x | The dashed residual exits the depicted S band on its way from P to X; crossing the band edge expresses the intended geometry. | INTENDED_RESIDUAL_EXIT_FROM_S | 0 |
| PAIR-4769 | PATH-001 upper S edge | PATH-010 p arrowhead | ROI-04/05 1x/8x | The teal arrowhead at P remains below the upper edge; its tip is not merged with the boundary. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4771 | PATH-001 upper S edge | PATH-012 right-angle marker | ROI-04/05 1x/8x | The marker's outer corner visually converges at the S-surface region near P, but each gray stroke is separately traceable and the orthogonality cue is unambiguous. | INTENDED_PROJECTION_CONSTRUCTION_CONTACT | 0 |
| PAIR-4772 | PATH-001 upper S edge | PATH-013 distance brace | ROI-04 1x/8x | The lower brace portion passes across the band edge because it measures P-to-X distance out of S; no text is obscured. | INTENDED_DISTANCE_FROM_S_CONTACT | 0 |
| PAIR-4774 | PATH-002 lower S edge | PATH-003 x shaft | ROI-06 1x/8x | The blue shaft begins at O inside the band and stays above the lower edge; no native-pixel contact is visible. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4775 | PATH-002 lower S edge | PATH-004 p shaft | ROI-05/06 1x/8x | The teal p shaft lies inside the band with a visible gap above the lower boundary. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4776 | PATH-002 lower S edge | PATH-005 residual shaft | ROI-04/05 1x/8x | The residual starts near the upper side of the band; the lower edge is remote and untouched. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4781 | PATH-002 lower S edge | PATH-010 p arrowhead | ROI-05 1x/8x | The p arrowhead at P is visibly above the lower boundary. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4783 | PATH-002 lower S edge | PATH-012 right-angle marker | ROI-05 1x/8x | The right-angle marker sits near the upper band region; it does not meet the lower edge. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4784 | PATH-002 lower S edge | PATH-013 distance brace | ROI-04/05 1x/8x | The brace remains near/above P and is visibly separated from the lower S edge. | CLEAR_FALSE_PATH_BBOX | 0 |
| PAIR-4786 | PATH-003 x shaft | PATH-004 p shaft | ROI-06 1x/8x | Blue x and teal p share exactly the origin O, then diverge; the shared endpoint is required by x=p+r. | INTENDED_SHARED_ENDPOINT_O | 0 |
| PAIR-4797 | PATH-004 p shaft | PATH-005 residual shaft | ROI-04/05 1x/8x | The p shaft terminates at P and the residual begins there; the 3.8962 px bbox advisory reflects this required endpoint relation. | INTENDED_SHARED_ENDPOINT_P | 0 |
| PAIR-4804 | PATH-004 p shaft | PATH-012 right-angle marker | ROI-05 1x/8x | One leg of the right-angle certificate is aligned to p at P, an intentional construction contact. | INTENDED_ORTHOGONALITY_CONTACT | 0 |
| PAIR-4811 | PATH-005 residual shaft | PATH-010 p arrowhead | ROI-04/05 1x/8x | The residual begins at the p arrow tip P; the near-bbox condition is the intended shared projection point. | INTENDED_SHARED_ENDPOINT_P | 0 |
| PAIR-4813 | PATH-005 residual shaft | PATH-012 right-angle marker | ROI-04/05 1x/8x | The other marker leg follows the residual direction at P, correctly certifying p perpendicular to r. | INTENDED_ORTHOGONALITY_CONTACT | 0 |
| PAIR-4814 | PATH-005 residual shaft | PATH-013 distance brace | ROI-03/04 1x/8x | The brace runs parallel and to the right of the dashed residual; their visible strokes do not merge. | CLEAR_PARALLEL_SEPARATION | 0 |
| PAIR-4838 | PATH-009 x arrowhead | PATH-011 residual arrowhead | ROI-02 1x/8x | The two arrowheads meet at X but approach from distinct blue/gray directions; the common tip is the required equality x=p+r. | INTENDED_SHARED_ENDPOINT_X | 0 |
| PAIR-4843 | PATH-010 p arrowhead | PATH-012 right-angle marker | ROI-05 1x/8x | The marker is anchored immediately at the p arrow endpoint P; the teal head and gray marker remain distinguishable. | INTENDED_PROJECTION_POINT_CONTACT | 0 |
| PAIR-4844 | PATH-010 p arrowhead | PATH-013 distance brace | ROI-04/05 1x/8x | The brace's lower end is offset right/up from the teal p arrowhead; the 7.5128 px advisory has no visible stroke collision. | CLEAR_NEAR_BBOX_ADVISORY | 0 |
| PAIR-4849 | PATH-012 right-angle marker | PATH-013 distance brace | ROI-04/05 1x/8x | The small right-angle marker is left of the brace; their broad curve bboxes intersect but the native gray strokes remain separate. | CLEAR_FALSE_PATH_BBOX | 0 |

## Closure

- Rows observed and decided: 81/81.
- Real illegal foreground collision pixels across these rows: 0.
- Unresolved rows: 0.
- Machine-disposed rows outside this manual queue: 4,770.
- Total frozen unordered-pair coverage: 4,851/4,851.
