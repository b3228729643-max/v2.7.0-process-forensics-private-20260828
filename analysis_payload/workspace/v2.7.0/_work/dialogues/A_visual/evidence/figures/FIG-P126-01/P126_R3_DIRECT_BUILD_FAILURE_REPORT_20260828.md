# FIG-P126-01 R3 direct build failure

- HANDOFF_ID: `A-R115-P126-SA2-DIRECT-BUILD-R3-20260828`
- verdict: `BUILD_FAIL_NO_CANDIDATE`
- controller invocation: `1`
- direct LuaLaTeX typeset invocation: `1`
- retry / latexmk / version probe / second invocation: `0 / 0 / 0 / 0`
- natural completion: `true`; interrupted: `false`

## Process identity

- controller PID: `24456`
- child PID: `1700`
- controller start UTC: `2026-08-28T00:37:45.4075906Z`
- child start UTC: `2026-08-28T00:37:45.6567812Z`
- child end UTC: `2026-08-28T00:37:46.4378145Z`
- duration: `0.781033 seconds`
- child exit: `1`; controller exit: `1`
- terminal `latexmk/lualatex/luatex/luahbtex`: `0/0/0/0`

## Frozen inputs

- source before/after: `4224 bytes / 366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`
- wrapper before/after: `395 bytes / 706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`
- engine before/after: `6656 bytes / CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`
- controller before/after: `6932 bytes / 03FF45107DC4E127C2F85B8E8E712E1F5B77A3DDC07675CAFD7C6F8278FA9AB2`

## First error

LuaLaTeX stopped before processing the document body while initializing `luaotfload`:

`system : no writeable cache path, quiting`

The fatal error occurred at wrapper line 1 (`\documentclass...`). No PDF was produced. This is a pre-document cache/controller-environment failure; this report makes no source, visual, mathematical, or local-pass adjudication.

## Failure root identity

- root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828`
- files/directories/PDF: `5/7/0`
- `START.json`: 2672 bytes / `BAC820AA1D4B16BCEF18B6E8CFDD3F16A5CD3C26C3189044CE1FD8C76524919D`
- `RESULT.json`: 3714 bytes / `94D1FF79950090C4C64519393317012B9D1222EB806854BF62E35B8B4CAA737C`
- `lualatex.stdout.txt`: 2200 bytes / `B7085DD1156CFDDB5A8CD22F884DAD9886314DA897C59667A4699947A5CC7EF4`
- `lualatex.stderr.txt`: 0 bytes / `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`
- `build/v260_FIG-P126-01_standalone.log`: 2426 bytes / `A85C91BFFF3BF183490C4AA1F55B0DC287F3C1BF23778289D5EA732E475AEEDC`

No retry, repair, cache change, second build, source change, commit, fresh role, second UID, or central write was performed after the failure. Main adjudication is required before any sibling build.
