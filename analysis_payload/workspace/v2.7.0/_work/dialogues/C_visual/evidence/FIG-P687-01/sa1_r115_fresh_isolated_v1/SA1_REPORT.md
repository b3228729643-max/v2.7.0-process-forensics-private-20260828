# R115 fresh isolated SA1 report — FIG-P687-01

HANDOFF_ID=C-FIG-P687-01-R115-SA1-FRESH-ISOLATED-V1

CANONICAL_ACTUAL=/root/sa1_fig_p687_r115_fresh_isolated_v1

SA1_MODEL=gpt-5.6-sol

SA1_REASONING=xhigh

RESULT=PASS

NEXT_ROUTE=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3

## Fresh localization and fixed identity

The fixed current candidate is `main_full.pdf`, 4,967,161 bytes, SHA-256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`. The fixed figure source is `fig_v5_c06_collapsed_gibbs_counts.tex`, 3,401 bytes, SHA-256 `FEB76B03845B3EA01ECD53768AA99AAF618519268667AA065A29848207AB398A`. The fixed chapter source is `V5-C06.tex`, 120,809 bytes, SHA-256 `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`.

Fresh caption/source/chapter matching locates the current rendered object at PDF physical page 737, printed page 724, Figure 35.4 in Chapter 35, “潜在狄利克雷分配”. This localization follows the exact caption and chapter input; it does not infer the current page from the UID string.

## Reader-visible denominator and pair closure

The frozen denominator contains exactly 24 reader-visible semantic objects:

- O01–O13: step text, five numbered badges, restart note, minus-i note, and the complete two-line caption;
- O14–O18: five rounded node containers;
- O19–O24: all six directed connectors, including the full step-5-to-step-1 loop.

Therefore the complete unordered-pair denominator is `C(24,2)=276`. `pair_skeleton.csv` enumerates P001–P276 exactly once. Post-observation `manual_pair_judgments.csv` contains 276 nonblank judgments with exact skeleton binding: 258 `CLEAR_NO_ILLEGAL_INK`, five `CLEAR_LEGAL_CONTAINMENT`, twelve `CLEAR_LEGAL_ENDPOINT_CONTACT`, and one `CLEAR_NEAR_NO_CONTACT`. `manual_id_judgments.csv` contains 24/24 post-observation PASS judgments. There are zero missing IDs, duplicate pair IDs, blank judgment fields, skeleton mismatches, or non-clear pairs.

## Views actually opened

The audit opened the full page at 200 dpi, the full page at 300 dpi, the full page in 300-dpi grayscale, the native 300-dpi figure+caption crop, its grayscale counterpart, semantic/object/text overlays, all/text/graphics visible-ink masks, and the visible-ink overlay.

Seven critical ROIs were each opened at native 1x and nearest-neighbor 8x: step 1; document-topic counts; topic-word counts; full conditional; sample/restore; loop topology plus restart note; and minus-i safeguard plus caption. `view_opening_ledger.csv` records all 26 actual openings and their post-observation notes.

## Hard-failure closure under R168

GLYPH_CODEPOINT_PASS=true. Native and nearest-8x views show no missing glyph, tofu, replacement character, wrong codepoint, broken fraction rule, or malformed Chinese/math. The observed PDF vector text includes the correct `i`, `k`, `k*`, `α`, `β`, `∝`, conditioning bar, dot totals, subscripts, superscript `-i`, and zeros. The small square above the figure on the full page is the proof-end mark in surrounding chapter content, not a missing glyph in the figure.

CLIPPING_PASS=true. No text, formula, badge, border, arrowhead, connector, note, or caption is clipped in the native crop or full page. Confirmed clipped visible-ink objects: 0.

ILLEGAL_VISIBLE_INK_OVERLAP_PASS=true. All 276 semantic-object pairs were inspected after opening the native image, overlays, masks, and the relevant 8x ROIs. The only visible contacts are the twelve intended arrow-to-node boundary attachments. The five text/container relations retain interior whitespace. The restart note is close to, but visibly separated from, the loop corridor. Confirmed illegal visible-ink overlaps: 0; unresolved pairs: 0.

READABILITY_BALANCE_PASS=true. Every heading, formula, note, badge, and caption is readable at native page/crop scale. The left and right evidence panels are balanced; the conditional formula is dominant without crowding; badges support the reading order; the restart note is subordinate; no text role overwhelms the flow. Source declarations (9.2 pt base, 9.0 pt badges/footer, 8.8 pt loop note) and extracted PDF vector sizes (approximately 9.166 pt base, 8.966 pt badges/footer, 8.767 pt loop note, 9.963 pt caption; 6.416 pt only for naturally derived math scripts) are retained as advisory numeric evidence. Under R168, the legacy numerical font/pixel/ratio thresholds are not used alone to override the directly observed absence of unreadability or severe imbalance.

MATH_SEMANTICS_PASS=true. The diagram correctly performs the collapsed-Gibbs leave-one update: remove token `i` from both consistent count tables; read document-topic factor `(n_mk^{-i}+α_k)/(n_m·^{-i}+α_0)` and topic-word factor `(n_kv^{-i}+β_v)/(n_k·^{-i}+β_0)`; multiply and normalize over `k`; sample `k*`; restore the token to both tables. The document denominator is independent of `k` but is intentionally retained, matching chapter lines 474–498, which state that it exposes the complete posterior-predictive source. The minus-i note correctly prevents self-counting until sampling completes.

ARROW_TOPOLOGY_PASS=true. Step 1 branches to the two count panels; both panels converge on the conditional; the conditional points to sampling/restoration; the loop departs step 5, follows the right corridor, and points back into step 1. Arrowheads are unambiguous in color and grayscale, and no connector crosses text.

TEXT_CONSISTENCY_PASS=true. Figure text and formula agree with the exact figure source. The caption and adjacent chapter lines 504–506 both state: decrement the document-topic and topic-word counts for the old assignment, compute all candidate weights, sample the new topic, then increment both counts. The chapter proposition supplies the same factors and normalization requirement.

GRAYSCALE_PASS=true. In the 300-dpi grayscale page and native grayscale crop, badge order, node boundaries, arrow direction, formula hierarchy, restart loop, note, and caption remain distinguishable without relying on color.

PAGE_INTEGRATION_PASS=true. On the 200- and 300-dpi full page, Figure 35.4 sits directly after its explanatory paragraph and before posterior-mean formulas, with stable horizontal fit, caption wrap, top/bottom whitespace, and no isolated line, overfull edge, or large disruptive void.

## R168 acceptance fields

SOURCE_FONT_PASS=true (direct reader-visible R168 judgment; legacy numeric values retained as advisory)

PIXEL_HEIGHT_PASS=true (native 300-dpi and nearest-8x direct observation; legacy thresholds advisory)

SAME_CLASS_RATIO_PASS=true (paired evidence panels and five badges are visibly consistent)

ROLE_RATIO_PASS=true (formula, node text, note, badge, and caption hierarchy is balanced)

OVERLAP_CANDIDATE_PAIR_COUNT=18 (five containment, twelve legal endpoint contacts, one near adjacency)

OVERLAP_CANDIDATE_PIXEL_COUNT=NOT_USED_AS_STANDALONE_R168_VERDICT

MASK_CONTAMINATION_PIXEL_COUNT=0_CONFIRMED

OVERLAP_PIXEL_COUNT=0_CONFIRMED_ILLEGAL_VISIBLE_INK

PIXEL_ADJUDICATION_STATUS=CLEAR

PIXEL_ARBITER_MODEL=NOT_USED

PIXEL_ARBITER_REASONING=NOT_USED

CLIP_PIXEL_COUNT=0_CONFIRMED

MIN_TEXT_CLEARANCE_PX=ADEQUATE_BY_NATIVE_AND_NEAREST8X_R168_OBSERVATION

VISUAL_HARMONY_PASS=true

MATH_SEMANTICS_PASS=true

TEXT_CONSISTENCY_PASS=true

GRAYSCALE_PASS=true

PAGE_INTEGRATION_PASS=true

## Final SA1 disposition

No R168 hard failure exists: no missing/tofu/wrong codepoint or math, unreadability or severe imbalance, clipping, confirmed illegal visible-ink overlap, semantic error, geometric error, or collapsed-Gibbs/count error was found. The only honest route is:

RESULT=PASS

SEALED_ROUTE=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3
