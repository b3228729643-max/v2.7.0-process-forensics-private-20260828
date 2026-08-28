# FIG-P582-01 R2 local SA2 PASS report

## Verdict

`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

This is a local single-figure candidate and evidence verdict only. No commit, central inventory update, fresh SA1, or fresh SA3 has been performed.

## Authorized source scope

- Sole source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`
- Before SHA-256: `C075D4A44A60B95848614543D1D2DBCCCB53F1F776FFDD79A3BF1FEAE3F6550C`
- After SHA-256: `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`
- Exact worktree diff: one file, 12 insertions / 12 deletions; `git diff --check` PASS
- Change class: fontsize/leading declarations only. Data, coordinates, curves, ticks, styles, colors, formulas, labels, caption semantics, and geometry are unchanged.
- All 14 explicit visible fontsize declarations are now at least 9.5pt; resize/scalebox/transform tokens remain zero.

## One controlled build

- HANDOFF_ID: `A-R108-P582-SA2-DIRECT-BUILD-20260826`
- Controller PID / direct LuaLaTeX child PID: `19496 / 23084`
- UTC interval: `2026-08-26T13:14:12.8569568Z` to `2026-08-26T13:15:09.4964861Z`
- Duration: `56.64 s`
- Exit/natural/interrupted: `0 / true / false`
- Invocation/retry/latexmk: `1 / 0 / 0`
- PDF: `build/v260_FIG-P582-01_standalone.pdf`, 31,330 bytes, SHA-256 `988E672096CC34E5A9B1634D84D150C644A0E07B049D81A92FACFE7276269F5B`
- Source before=after: `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`
- Wrapper before=after: `831360DBDEFA9AF2A45ED120AF4F33E280C342D07DD1136E5FFA0E2BD592A21C`
- Post-exit `latexmk/lualatex/luatex/luahbtex`: all none

The build slot was released to main before any non-TeX evidence processing. No later TeX invocation occurred.

## Fresh-PDF denominator and hard gates

- Rendered nonblank glyphs: 78
- Foreground graphic paths: 17
- Total objects: `N=95`
- Complete unordered pairs: `C=4,465 = choose(95,2)`
- Empty masks: 0
- Page-edge clip candidates: 0
- Shared-ink relation candidates: 29, all visually accepted as intended graph construction/data relations
- Low-clearance glyph candidates: 4, all manually reviewed at native1x and 8x
- Manual rows: 95 object + 33 candidate-relation + 15 view/semantic
- Machine-generated manual reviewer/boolean/decision/note fields: 0
- Manual time-integrity failures: 0
- R168 true hard failures: 0

The old `.640`/first-down-arrow and `.380`/second-down-arrow risk areas were opened at native 300 dpi and 8x nearest-neighbor scale. The `.380` terminal zero and the arrow have zero shared pixels; their pixel-level adjacency is advisory under R168 and does not impair reading. `.640`, both `.325` labels, the four raw markers, the four running-mean markers, axes, ticks, truth line, and grayscale view show no real clipping, unreadability, or illegal text/geometry overlap.

Semantics remain exact: raw values `.64,.01,.49,.16`, running means `.640,.325,.380,.325`, truth `1/3`, formula `h(U_i)=U_i^2`, and axis meanings sample index `i`, sample count `N`, and value.

## Immutable root

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826`
- Payload / controls / ordinary: `239 / 3 / 242`
- CSV manifest: 239 rows, SHA-256 `7EF6AF221CE4A83885CAB85D8939A01D7BFD88F64DB5BFFA19CCFF24DB1C599A`
- JSON manifest: 239 rows, SHA-256 `D14673F0E695B18575F4C0EDC9384256DEAFEE26A7FBB93E98AAC05B8F11AF8F`
- Manifest CSV/JSON/FS path+bytes+SHA+ticks differences: 0
- Read-only ordinary files: `242/242`
- ADS / `.pyc` / `__pycache__` / reparse: `0 / 0 / 0 / 0`
- `WRITE_STOPPED.json` SHA-256: `F4E09D5DF5AD50B8A22D2658DCCA7277AB307A5AB0A471B0AB1AD2F5010A3840`
- WSTOP ticks: `639233478952158132`
- Maximum other ticks: `639233478951901170`
- Strict-latest margin: `256,962 ticks`
- Files at or after WSTOP: 0
- Root-external audit: `P582_R108_R2_ROOT_AUDIT.json`, SHA-256 `3917C7896431DA922288CAA20DFF3715AFB80554D207DE8159BB7CA5D54182E9`, hard gate PASS

The root is frozen. Main must authorize the single-source atomic commit before any integration or new official candidate work.
