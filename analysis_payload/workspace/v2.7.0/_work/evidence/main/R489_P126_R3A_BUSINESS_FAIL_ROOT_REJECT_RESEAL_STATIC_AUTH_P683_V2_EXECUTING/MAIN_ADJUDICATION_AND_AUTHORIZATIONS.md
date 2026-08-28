# Revision 489 Main adjudication and authorizations

## P126 R3A

- Main independently opened the R3A native legend ROI, nearest-neighbor 8x ROI, native color figure and native grayscale figure. The four vertical `x_2` trajectory segments remain visibly dashed, while the short `更新 x_2` legend swatch is one continuous run and is indistinguishable from the `x_1` solid swatch in grayscale.
- `LEGEND_GRAYSCALE_PIXEL_RUN_AUDIT.json` independently agrees: each swatch has one long center-row dark run. The unique substantive hard defect is therefore accepted as `HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE`; all other geometry, clipping, codepoint, quadratic, coordinate-update, caption and page checks remain PASS.
- The live A source remains the sole modified file, 4,224 bytes/SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`, with unstaged 26+/26- and `git diff --check` PASS. Current lines 63--66 assign a solid legend image to `x_1` and `dash pattern=on 1.2pt off 1.2pt` to `x_2`.
- Main independently verified the frozen R3A root contains 208 files and 12 directories including root, all ReadOnly; it has exactly the three premarker controls and no WSTOP. The controller stopped after the premarker ReadOnly freeze at line 120 because a hashtable was passed to `Measure-Object -Property`; auditor invocation0 and post-error root writes0.
- Formal classification: `UNSEALED_CONTROL_FAILURE_AFTER_PREMARKER_READONLY_FREEZE`. The preserved business direction is `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`, but no LOCAL_SA2 verdict is counted from this unsealed root.
- The R3A root, controller, auditor and external report/handoff are permanently frozen. No in-place repair, retry, marker insertion, retimestamp, cleanup or business rerun is authorized.
- Main authorizes only STATIC PREPARATION for one new sibling evidence-only control reseal: HANDOFF `A-R115-P126-SA2-DIRECT-BUILD-R3A-CONTROL-RESEAL-V1-20260828`, operation `P126_R115_R3A_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`, destination `...\FIG-P126-01\STRICT_R3B_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`. The old CSV schema is exactly `relative_path,bytes,sha256,creation_time_utc_ticks,last_write_time_utc_ticks`; rows205/unique205/actual payload205/case-sensitive set diff0. Copy only those 205 material files, old controls0; add COPY_IDENTITY and resolved COPY_PROVENANCE for payload207; controls exactly PAYLOAD_MANIFEST, SEAL_AUDIT and WRITE_STOPPED; projected ordinary210. Controller/auditor invocations remain0/0 until a separate Main review.
- The eventual source scope is held, not yet activated: only the `x_2` legend encoding at current lines 63--66 may be changed so native300 and grayscale contain objectively separated strokes (and preferably the matching hollow-square cue). Contours, trajectory, dash rendering in the plot, coordinates, labels, fonts, caption, alt text and every other token remain frozen.

## P683 SA3 control reseal V2

- Main read both frozen V2 scripts completely and independently recomputed their static gates. Controller 24,300 bytes/SHA-256 `0C48B0E09A3416561B632D18F2BE3861959A3C5AD73A7FE5588F48528E456A3F`; auditor 19,173 bytes/SHA-256 `DAD60C6C2EDC54B10933E766695493EEE0274CC6647506853BABA2691411AD5A`; both ReadOnly and AST0.
- Main independently confirmed the old manifest header `TYPE,RELATIVE_PATH,BYTES,SHA256`, rows42=`FILE39+DIRECTORY2+ROOT1`, empty required FILE fields0, old manifest/marker SHA exact, bad `.RelativePath` references0, new root absent and artifacts empty.
- Extracting only each frozen canonicalization function and applying it to the real manifest produced rows39/unique39/actual39/case-sensitive set diff0 and rejected all 8 invalid test paths. The premarker ReadOnly, external future marker, sole final move, postmarker external snapshot and separate auditor order is statically closed.
- Main issued `MAIN_R489_P683_SA3_CONTROL_RESEAL_V2_EXECUTE_ONCE_GRANTED`: controller invocation1/retry0; auditor invocation1/retry0 only after controller natural success; first error stops the chain. No business rerun, V1 change, TeX/source/Git/central/process/new UID or role is authorized. P683 remains SA3 and is not yet C_LOCAL_PASS.

## Global state

- Official candidate remains R115; Main HEAD and inventory remain unchanged: `31 SA1 / 31 SA2 / 1 SA3 / 37 local pass`, strict final `0/99`, B `66/66`.
- TeX/build/commit/fresh-role actions remain prohibited.
