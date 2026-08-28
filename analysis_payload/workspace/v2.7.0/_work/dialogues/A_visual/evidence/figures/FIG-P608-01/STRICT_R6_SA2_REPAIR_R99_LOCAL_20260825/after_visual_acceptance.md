# FIG-P608-01 SA2 R6 local repair verification

HANDOFF_ID: `A-R99-P608-SA2-NARROW-20260825`  
ROUTE: `SA2=gpt-5.6-sol/max`  
RESULT: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

This package verifies the single authorized source repair against a frozen,
one-page local wrapper PDF. It is not an official-candidate review and does
not assert `A_LOCAL_PASS`. A new official candidate and fresh isolated SA1
remain mandatory; SA1 and SA3 were not started by this task.

## Source and local candidate

- Baseline/current HEAD: `e392bd8e5f37dfd49f071f7251c281d46bb68ffd`.
- Sole source change: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex`; 1 insertion, 0 deletions.
- Exact insertion: `+  ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},`.
- Frozen local PDF SHA-256: `638A722CC86D848E6B0FDEB69F08BB6DDBD3F0AD33E262AB36690C2943FD03BB`; bytes: 42989.
- Source SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`; wrapper SHA-256: `A26D55BEF0CB79B95AFF9F7768B87D277894A55BF81B38033A6D1D767A7062C7`.
- Four earlier bootstrap attempts exited 12 at luaotfload cache-path initialization before the P608 source was entered; they produced no candidate PDF and are retained as build history.
- The successful build directly invoked LuaLaTeX from the worktree merge-book directory with one absolute R6 `texcache` shared by TEXMFVAR/TEXMFCACHE/TEXMFCONFIG; latexmk and the temporary junction were not used for the successful candidate.
- Four rendered layout trials were rejected before freezing: direct r1 showed that `rotate=0` did not cancel PGFPlots' default +90 rotation and collided with y ticks; direct r2 exposed rotated-local `xshift` behavior; direct r3 retained a 0.80pt bottom-label/tick overlap; direct r4 cleared position geometry but the full raw-mask audit proved both natural-script t glyphs were still 10px. Direct r5 proved the `rotate=-90` layout but was rejected because the evidence wrapper redundantly forced Noto Sans SC instead of the official `statlearnbook` Noto Serif SC main-font route. Direct r6 removes only that evidence-wrapper override and is the frozen local candidate.

## Bottom-up denominator and findings

- Visible object universe: N=170 (112 glyphs + 58 foreground paths).
- Complete unordered denominator: C(N,2)=14365; emitted pair rows=14365.
- Critical pairs opened and individually reviewed: 13.
- Final illegal overlap pixels: 0; clip pixels: 0.
- Minimum applicable class clearance: 13.0px.
- Design pixel failures: 0.

## Gate matrix

| Gate | Verdict |
|---|---|
| handoff_and_route_exact | PASS |
| frozen_local_identity_current | PASS |
| extractor_used_frozen_local_pdf | PASS |
| build_local_wrapper_pass | PASS |
| source_scope_exact | PASS |
| rawdict_to_texttrace_closed | PASS |
| object_universe_recomputed | PASS |
| ordinary_safe_filenames | PASS |
| all_object_artifacts_exist | PASS |
| character_mapping_closed | PASS |
| all_foreground_paths_accounted | PASS |
| math_rules_accounted | PASS |
| pair_universe_complete | PASS |
| all_pairs_pass | PASS |
| zero_final_illegal_overlap | PASS |
| zero_clip | PASS |
| text_crop_edge_clearance | PASS |
| source_font_pass | PASS |
| source_font_control_coverage | PASS |
| source_scale_control_pass | PASS |
| pixel_height_pass | PASS |
| pixel_rows_cover_all_glyphs | PASS |
| punctuation_calibrated | PASS |
| calibration_artifacts_exist | PASS |
| same_class_d_ratio_pass | PASS |
| role_e_ratio_pass | PASS |
| semantic_consistency_pass | PASS |
| required_views_exist | PASS |
| text_measurement_overlay_exists | PASS |
| contact_coverage_closed | PASS |
| manual_object_review_closed | PASS |
| manual_metric_gate_consistent | PASS |
| critical_pair_review_closed | PASS |
| visual_views_manually_pass | PASS |
| role_panel_manual_pass | PASS |
| manual_open_attestation_closed | PASS |

## Design failures

- None.

## Goal §9.2.1 routing matrix

| Stage | Model / reasoning | State |
|---|---|---|
| SA1 | NOT_RUN_LOCAL_SA2 | Awaiting official candidate and fresh isolated review |
| SA2 | gpt-5.6-sol / max / escalated=false | LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1 |
| SA3 | NOT_RUN | Not started |

## Terminal boundary

`MACHINE_TERMINAL_RECALC.json` is the bottom-up machine result. The manifest,
this report, result token, and handoff report follow it. `WRITE_STOPPED` is the
strictly newest marker and no evidence writes are permitted afterward.
