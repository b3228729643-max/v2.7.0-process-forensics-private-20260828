# P608 R12 sealed local SA2 report

Status: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

## Scope and source

- UID: `FIG-P608-01`
- Worktree parent: `f58d80d0550df16b8288e06eb7af00325be3441e`
- Only modified business source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex`
- Diff: one insertion / one deletion, changing the common x domain from `[1,20]` to `[0.5,20.5]`.
- Before SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- After SHA-256: `49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E`
- Data, 15 running means, t20=`2.0000`, ticks, labels, caption, panel structure, and all other sources are unchanged.

## Controlled build

- Exactly one direct LuaLaTeX invocation; no latexmk and no retry.
- PID `19228`, natural exit `0`.
- PDF: 43,012 bytes, SHA-256 `A50EE094843FDA68A3E3CDCFA0F5DC1F4884B1FDA853A6B3BECEE7DB2758452A`, one A4 page, PDF 1.7, unencrypted.
- Source and wrapper hashes were unchanged across the invocation.
- Build slot was released immediately after completion; final TeX process count is zero.

## From-zero regression

- N=128: 68 glyphs + 60 graphics.
- All unordered pairs: 8,128/8,128.
- Empty masks / illegal overlaps / clearance flags / clipping / R168 hard readability failures: `0/0/0/0/0`.
- PAIR-06596 (y-axis vs first upper marker): shared pixels `0`, clearance `16.464 px`, PASS.
- PAIR-06650 (y-arrowhead vs first upper marker): shared pixels `0`, clearance `12.928 px`, PASS.
- Twelve closest critical pairs were opened at native 1x and nearest-neighbor 8x; all preserve visible separation and empty intersections.
- Full page, figure crop, standalone, grayscale, text overlay, four glyph sheets, five graphic sheets, two critical sheets, and the target relation sheet were manually opened after generation. No tofu, wrong semantic glyph, unreadable element, real clipping, or unintended overlap was observed.

## Immutable evidence

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R12_SA2_SOURCE_GEOMETRY_DIRECT_BUILD_20260826`
- Payload / controls / ordinary files: `353 / 3 / 356`.
- CSV manifest / JSON manifest rows: `353 / 353`.
- CSV↔filesystem and JSON↔filesystem path/bytes/SHA/ticks mismatches: `0 / 0`.
- Read-only files: `356/356`; ADS, pyc, Python cache directories: `0/0/0`.
- `WRITE_STOPPED.json` is strictly newest by `10,438,856` ticks; post-seal writes: `0`.
- Manifest CSV SHA-256: `B9538742837F12806B1280686DBF4EAA29D26AEA0879D74AD09499ECFB774BDA`.
- Manifest JSON SHA-256: `D2A0D3AD63C5696BB55F0644E67A126242D393500F5894F7706816C7879C7715`.
- WRITE_STOPPED SHA-256: `920DC3679C873E46507F6F31A035238B96DA56BF16B5FD284565C1438E68D735`.

No commit was created. No fresh SA1/SA3 was started. This is not A_LOCAL_PASS; it is ready for main-thread root review and atomic single-source commit authorization.
