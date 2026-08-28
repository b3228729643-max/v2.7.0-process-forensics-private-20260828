# FIG-P610-01 R104 SA3 独立语义、公式、几何与关系复核

- reviewer_type: `AI_SA3_VISUAL_REVIEW`
- human_certification: `false`
- handoff_id: `C-FIG-P610-01-R104-SA3-FRESH-ISOLATED-V1`
- PDF identity: official R104 `main_full.pdf`, physical page 662, printed header page 649, Figure 32.10.
- source identity: `fig_v5_c03_rejection_sampling_comparison.tex`, label `fig:V5-C03-rejection-vs-mh`.
- isolation: no SA1/SA2/old P610 evidence, central state, inventory, git history, prior report, result, handoff, or old conclusion was read.

| Review ID | Gate | Independently checked object or relation | Actual finding | Hard finding |
|---|---|---|---|---|
| SEM-001 | formula/codepoint | All eleven node labels | Candidate rows are `Y_1,Y_2,Y_3` in both panels; left outputs are `Y_1,Y_3`; right states are `Y_1,Y_1,Y_3`. Glyph inventory confirms mathematical italic `Y` U+1D44C and digits U+0031/U+0032/U+0033. | CLEAR |
| SEM-002 | formula meaning | Repeated right state | Rejection of proposal `Y_2` repeats the current state `Y_1`; the middle lower node is explicitly double-ringed and still labeled `Y_1`. | CLEAR |
| SEM-003 | rejection symbol | Both crosses | Both are multiplication sign U+00D7, visually used as rejection marks; neither is the letter `x`, tofu, or a wrong code point. | CLEAR |
| SEM-004 | left relation | Acceptance--rejection panel | Proposal `Y_2` has a rejection mark and no output node below it; accepted `Y_1` and `Y_3` remain as the output sequence. | CLEAR |
| SEM-005 | right relation | MH panel | Proposal `Y_2` is rejected, but the state sequence continues `Y_1 -> Y_1 -> Y_3`; two solid right arrows provide unambiguous temporal direction. | CLEAR |
| SEM-006 | comparison semantics | Cross-panel contrast | Left panel encodes an accepted-value output list with a gap at rejected `Y_2`; right panel encodes a Markov chain with a repeated current state. This is the intended conceptual distinction. | CLEAR |
| SEM-007 | note content | Left note | Extracted and visually verified text is “拒绝 `Y_2`：输出序列留空”, matching the left object relation. | CLEAR |
| SEM-008 | note content | Right note | Extracted and visually verified text is “拒绝 `Y_2`：下一时刻仍记录当前 `Y_1`”, matching the repeated-state geometry. | CLEAR |
| SEM-009 | title content | Panel titles | Left title identifies acceptance--rejection sampling; right title identifies Metropolis--Hastings. No swapped panel or mislabeled method. | CLEAR |
| SEM-010 | caption consistency | Figure 32.10 caption | Caption states that acceptance--rejection emits no rejected candidate and MH records the current state again, so outputs are generally correlated. The panels instantiate exactly those statements. | CLEAR |
| SEM-011 | adjacent-text consistency | V5-C03 lines 617--628 and page 662 paragraph | Adjacent text says the former re-proposes independently and outputs only accepted values, whereas the latter copies the current state to the next time. This agrees with panel objects, notes, arrows, and caption. | CLEAR |
| GEO-001 | panel geometry | Two rounded panels | Panel rectangles are equal height and width; titles, candidate rows, output rows, and notes share aligned baselines. | CLEAR |
| GEO-002 | divider geometry | Central dashed divider | Divider lies between panels, does not touch titles, nodes, notes, or caption, and preserves an unmistakable two-panel reading. | CLEAR |
| GEO-003 | candidate/output alignment | Vertical correspondences | Accepted candidates and their output/state nodes share vertical axes; the rejected middle candidate aligns with the cross and, in MH, with the repeated-state node. | CLEAR |
| GEO-004 | dashed path geometry | Five semantic dashed connectors | All dashed proposal connectors terminate outside node borders. The right middle path is split above and below the rejection mark rather than drawn through it. | CLEAR |
| GEO-005 | state-arrow geometry | Two horizontal solid arrows | Both arrows run left-to-right, stop outside node borders, retain visible arrowheads in grayscale, and do not intersect any label. | CLEAR |
| GEO-006 | double-node geometry | Repeated `Y_1` node | Two concentric blue rings are clearly separated; the label remains centered with 16.204651 px minimum text-to-border blank clearance. | CLEAR |
| GEO-007 | zero collision | All 703 unordered pairs | Raw isolated semantic masks cover 38 actual objects, with exactly 703 `n choose 2` rows; every row has `mask_overlap_pixel_count=0`. | CLEAR |
| GEO-008 | closest hard text pair | Right rejection mark vs double node | The closest text-related pair has 13.560220 px blank clearance and zero overlap. The rejection mark vs split connector has 13.866069 px and zero overlap. | CLEAR |
| GEO-009 | closest non-text connection | Middle dashed path vs double node | The endpoint has 3 px true white gap and zero overlap. This is a legitimate connected-object endpoint and, under R168, the designated 5 px main-line gap is advisory only. | CLEAR; ADVISORY RECORDED |
| GEO-010 | clip | All reader elements and semantic objects | No text, formula, arrowhead, marker, node border, panel border, or caption-related foreground is cut by the physical page or figure crop. | CLEAR |
| VIS-001 | grayscale | Structural encoding | Candidate nodes use light single circles, output states use dark circles, the repeated state uses a double circle, proposal paths are dashed, state transitions solid with arrowheads, and rejection uses `×`; meaning does not depend on color alone. | CLEAR |
| VIS-002 | visual hierarchy | Full page and standalone | Main flow and node relationships dominate. Titles are slightly larger; explanatory notes are lighter and do not obscure the process. | CLEAR |
| VIS-003 | R168 font gate | All 77 glyph IDs | No tofu, missing glyph, wrong code point, mathematical-symbol error, actual unreadability, or severe font imbalance was found. The source note style declares 8.5 pt and natural single-stroke glyphs have low bbox height; those are advisories under R168, not hard failures. | CLEAR; ADVISORIES RECORDED |
| VIS-004 | page integration | Physical page 662 | Figure follows its introduction, caption is complete, and Example 32.1 follows without overlap, clipping, or abnormal whitespace. | CLEAR |

The per-ID visual record is in `manual_object_review.csv` (38/38 objects) and `manual_glyph_review.csv` (77/77 non-whitespace glyphs). The 26 closest pairs (all raw blank clearances <=20 px) are individually adjudicated in `manual_critical_pair_review.csv`; the complete 703-pair raw ledger remains `all_unordered_object_pairs_raw.csv`.
