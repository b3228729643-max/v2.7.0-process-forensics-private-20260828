# A-R168-P654-R21-SEALED-READY-FOR-MAIN-20260825

## Route

`P654_R21_SEALED_READY_FOR_MAIN`

Main already accepted the R21 lean machine and human terminal review under `USER_FONT_REVIEW_RELAXATION_R168`. This handoff records the authorized minimal seal and atomic single-source commit. It does not claim `A_LOCAL_PASS` and does not dispatch a fresh role.

## Atomic commit

- Branch: `v2.7.0/dialogue-a-visual`
- Commit: `f58d80d0550df16b8288e06eb7af00325be3441e`
- Parent: `697dce292f2c1afca7d02554c3bad987ca84f825`
- Commit subject: `fix(figure): unify P654 formula typography`
- Only committed path: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex`
- Diffstat: `1 file changed, 19 insertions(+), 7 deletions(-)`
- Source SHA-256: `2EF1663B13A7982ACD5835217D0BB317FBF44146B08BE19F439430A2B42FABE7`
- `git diff --cached --check` before commit: PASS
- Worktree status after commit: clean
- Residual `latexmk/lualatex/luatex/luahbtex` process count after commit: 0

## Frozen R21 candidate

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R21_SA2_R20_DIRECT_BUILD_20260825`
- PDF: `build/v260_FIG-P654-01_standalone.pdf`
- PDF identity: 1 A4 page, 43,970 bytes, SHA-256 `3F1D7A22BCA99828074360790CBED5EA755F6A5C27CB1AE821ABB77FE457C241`
- Wrapper SHA-256: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- Build: one direct LuaLaTeX invocation, natural exit 0, exactly one PDF, retry 0, residual TeX 0.

## Accepted gates

- Machine denominator: `93 glyph + 21 graphic = 114`.
- All unordered pairs: `C(114,2)=6,441`, actual 6,441.
- Critical pairs: 174.
- Object / pair / illegal-overlap / clip hard failures: `0 / 0 / 0 / 0`.
- Genuine manual per-ID object ledger: 114/114 PASS.
- Missing/tofu, wrong code point or math meaning, unreadable content, visibly obvious size imbalance, real clipping/overlap, or broken relation: all 0.
- The 1--2px Gamma letter raster spacing is advisory only under R168; it is visibly separated and readable.
- Manual ledger: `MANUAL_R168_VISUAL_LEDGER.md`.
- Local report: `P654_R21_LEAN_LOCAL_PASS_REPORT.md`.
- Machine/result summary: `LEAN_R168_RESULT.json`.

## Seal identity

- Payload files: 2,059.
- Controls: 3 (`PAYLOAD_MANIFEST.json`, `SHA256_MANIFEST.csv`, `WRITE_STOPPED.md`).
- Final ordinary files: 2,062.
- Read-only files: 2,062/2,062.
- ADS / pyc / cache dirs / colon filenames: `0 / 0 / 0 / 0`.
- JSON manifest SHA-256: `C297FC64BFCFD8DD2BC7CCCF39AFD84D8D4DFB64BACE44DA6019A1813C6B310B`.
- CSV manifest SHA-256: `8FABA3A39C36DE3A5EB806E71889F99F1D782193367CC29D1BE12233869AB4DF`.
- Dual manifests and live payload path/bytes/SHA-256/NTFS ticks: zero differences at seal.
- `WRITE_STOPPED` NTFS UTC ticks: `639232454297526544`.
- Files with content/mtime later than or equal to `WRITE_STOPPED`: 0.
- Post-seal writes/imports/execution inside the root: forbidden.

## Main integration action

Cherry-pick only commit `f58d80d0550df16b8288e06eb7af00325be3441e`, independently confirm the sole path and source SHA, then freeze the next official full-book candidate. Until main dispatches the candidate-bound fresh role, P654 remains outside `A_LOCAL_PASS`; A will not start TeX, a second commit, SA1, or SA3.
