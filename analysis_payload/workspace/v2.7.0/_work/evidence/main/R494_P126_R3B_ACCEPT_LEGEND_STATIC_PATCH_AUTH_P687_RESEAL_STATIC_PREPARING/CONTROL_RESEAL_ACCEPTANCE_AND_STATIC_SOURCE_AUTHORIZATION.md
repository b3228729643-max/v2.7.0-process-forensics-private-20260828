# R494 — P126 R3B control reseal acceptance and narrow static source authorization

Timestamp: `2026-08-28T10:19:35+08:00`

## Decision

- Accept HANDOFF `A-R115-P126-SA2-DIRECT-BUILD-R3A-CONTROL-RESEAL-V1-20260828` and operation `P126_R115_R3A_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1` as a compliant one-shot evidence-only control reseal.
- Preserve and activate the sealed business verdict `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`; P126 remains SA2 and is not counted as a local pass.
- The only accepted hard defect is `HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE`: the short `更新 x_2` legend swatch is rendered as a continuous line indistinguishable from the `x_1` solid swatch. The actual teal coordinate-update trajectory remains visibly dashed; all other geometry, clipping, codepoint, mathematics, caption, and page checks pass.

## Independent R3B control checks

- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3B_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`.
- Unique frozen V2 controller/auditor invocations: `1/1`, retries `0/0`, both natural exit `0`; auditor `errors=[]`, `hard_gate=true`.
- Copy material `205`, old controls copied `0`, payload `207`, controls `3`, ordinary files `210`, directories including root `12`; every file and directory/root is ReadOnly.
- Old-manifest-to-copy and live source/destination canonical path, bytes, SHA-256, Creation FILETIME and LastWrite FILETIME mismatch counts are all zero. Manifest rows/payload FS are `207/207`; duplicate/missing/extra/set/identity differences are zero.
- `WRITE_STOPPED` has `22` physical lines and `22` unique keys, with bad/duplicate/BOM/key/binding mismatches all zero. Marker ticks are `639234800712805063`; maximum other entry including root is `639234794713221234`; strict-latest margin is `5,999,583,829` ticks and at-or-after excluding marker is zero.
- Source-root snapshot before/after is `58CB675701E319C180CF069D335FF46C825A81301629C15AE82B73AF0311CF39`; destination postmarker snapshot is `C895BF74CA5C3E3BBBC807CEDC2F5217584E41C8FCCFF69B416457E78047D057`, matching the frozen controller/auditor results. Postmarker mutation, old-root mutation, CSV/JSON parse, ADS, cache/pyc and reparse failures are all zero; external stage is absent.

## Static-only source authorization

- HANDOFF: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828`.
- Sole source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`.
- Authorized starting identity: `4,224` bytes, SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`; current worktree scope is exactly this one modified source, `26+/26-`, index empty and `git diff --check` clean.
- The only permitted semantic edit is replacement of the current line 65 `x_2` `\addlegendimage` declaration with a local custom legend-image code that draws at least three objectively disconnected `SLTeal` horizontal segments across the normal legend sample width. Each designed blank gap must be at least `0.05cm` (about `5.9` pixels at 300 dpi).
- Freeze line 63 (`x_1` legend swatch), line 64/66 legend text, all four actual teal trajectory dash declarations, axis limits, contours, q0--q7, markers, numeric labels, fonts, colors, legend position/layout, mathematics, caption, alt text, shared macros, chapter/build entry, and every other source token.
- This authorization is `STATIC_ONLY_NOT_RENDERED_NOT_PASS`. It permits source edit plus static projection/diff checks and one sealed static evidence root only. It does not permit TeX/build, process management, commit, fresh role, second UID, central-state write, or any claim of visual PASS.
- Return the exact before/after source identities, single-source Git boundaries, literal diff, static segment/gap projection, frozen-token audit, sealed root identities, and a request for one controlled direct LuaLaTeX build slot.

## Parallel route

- P687 remains SA2. Its business `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1` is accepted, but its original root remains permanently rejected for missing per-file bytes/SHA and manifest-SHA binding.
- C is authorized only to prepare the frozen sibling control-reseal scripts and static gates at invocation `0/0`, then pause. No execution or fresh SA1 is authorized at R494.

Inventory remains `30 SA1 / 32 SA2 / 0 SA3 / 38 local pass`; strict final remains `0/99`; B remains `66/66`.
