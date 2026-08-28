# R484 — P683 fresh SA3 identity and P126 static acceptance/direct-build authorization

Timestamp: `2026-08-28T08:31:18+08:00`

## P683 role registration

- Accepted actual identity: `C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1` / `/root/sa3_fig_p683_r115_fresh_isolated_v1` / `gpt-5.6-sol/xhigh` / `fork_turns=none`.
- Fixed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1`.
- Parent immediate pre-spawn and child pre-artifact exact gates both returned `Leaf=false / Container=false / Any=false / Parent=true`; the child reported the gate before any input read, artifact, or root creation. Exactly one instance is continuing; no restart, duplicate, or second role.
- P683 therefore transitions `SA1 -> SA3`. Authoritative inventory becomes `31 SA1 / 31 SA2 / 1 SA3 / 37 local pass`; strict-final remains `0/99`.

## P126 independent static acceptance

- A worktree is exactly `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`; Git reports exactly one modified file, 26 insertions/26 deletions, empty index, and `git diff --check` PASS.
- Sole source is `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`.
- Baseline identity independently read from Main and the A HEAD blob: `4093 bytes / 328A61A7C16DC11546BA165D698A22E1431B1B6AA3C04B16A4C40B52E4F3673C`.
- Patched identity independently read from A: `4224 bytes / 366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`.
- The complete diff is confined to the authorized axis limits, four contour parameterizations, q0--q7 coordinates, seven numeric anchors/shifts, square-marker coordinates, and local teal dash pattern/legend sample. Text, caption, alt, font declarations, axis names, figure label, color roles, shared macros, chapter/build entry, and all other sources are unchanged.
- Independent mathematics: Hessian `[[1,1],[1,2]]` has determinant 1 and eigenvalues `0.3819660112501051` and `2.618033988749895`; the off-diagonal term is nonzero. For `x1=r(cos-sin), x2=r sin`, the sampled level-set residual is at most `3.5527136788005009e-15`. q0--q7 objective values independently recompute to `2.92,2.56,1.28,0.64,0.32,0.16,0.08,0.04`; every updated-coordinate stationarity residual is 0 and every drop is strict. q7 remains an approximation, not a relabeling of `x*=(0,0)`.
- Static clearance and dash projections are accepted only as pre-build predictions. They do not count as render or figure PASS and must be remeasured from the new PDF.

## P126 static-root control acceptance

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R2_SA2_STATIC_COORDINATE_QUADRATIC_PATCH_R115_20260828`.
- Independent read-only recomputation: payload 6, controls 3, ordinary files 9, directories including root 1; manifest rows 6, duplicate/set/path/bytes/SHA/Creation/LastWrite mismatch 0; all files and root ReadOnly.
- `WRITE_STOPPED`: 15 physical lines, 15 unique one-key-per-line assignments, bad/duplicate lines 0. Marker ticks `639234733684755519`; maximum non-marker item including root `639234730685612928`; strict margin `2,999,142,591` ticks; at-or-after excluding marker 0.
- Manifest SHA `DD8412EA5A66B90829EBABAA55E6DC9212A23F7077DBCAED6675E1A0D4E2A6DA`; marker SHA `1E14E10414E50E5F626ABEDB7970D6BF749446DA03431150CFCD41BFA92AE743`; JSON/CSV parse, ADS, cache-pyc, and reparse failures all 0. External audit/report/handoff identities match the returned values and are ReadOnly.

## Exactly one controlled direct-build authorization

- Authorized HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R3-20260828`.
- Fixed new root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828`; Main immediate gate was `Leaf=false / Container=false / Any=false / Parent=true`.
- Frozen source: `4224 bytes / 366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`.
- Frozen standalone wrapper: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex`, `395 bytes / 706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`.
- Main pre-authorization TeX-family snapshot: `latexmk/lualatex/luatex/luahbtex = 0/0/0/0`.
- A may run exactly one root-external PowerShell 7 controller invocation and exactly one direct LuaLaTeX child invocation against the frozen standalone wrapper, with retry 0, `latexmk` 0, version-probe 0, and no second engine invocation. The controller must stop on the first error; failure or interruption returns `BUILD_FAIL_NO_CANDIDATE` and does not authorize a retry.
- Source, wrapper, controller, and engine identities must be recorded before and after; the output must be the sole PDF `build/v260_FIG-P126-01_standalone.pdf`. The build slot is released only after the controller naturally returns and the terminal TeX-family snapshot is read.
- Success authorizes only one non-TeX full visual/mechanical/manual regression from that PDF and a single compliant seal. It does not authorize commit, fresh role, second UID, source changes, Main/central writes, or another build. P126 remains SA2 and `STATIC_ONLY_NOT_RENDERED_NOT_PASS` until the new-PDF evidence is accepted.

No other TeX/build, source, Git, process-management, UID, or role action is authorized.
