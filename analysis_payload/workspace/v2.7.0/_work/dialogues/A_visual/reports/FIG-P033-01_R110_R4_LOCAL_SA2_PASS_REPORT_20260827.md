# FIG-P033-01 R110 R4 local SA2 PASS report

## Verdict

`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

Requested route: `P033_R4_SEALED_LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`.

This does not claim `A_LOCAL_PASS`; no commit or fresh role has been started.

## Build

- HANDOFF_ID `A-R110-P033-SA2-DIRECT-BUILD-R4-20260827`
- controller PID 20052; sole direct LuaLaTeX child PID 26468
- exit 0, natural true, interrupted false; invocation1/retry0/latexmk0
- duration 121.918 s
- PDF `v260_FIG-P033-01_standalone.pdf`: 31,553 bytes; SHA-256 `CECFB8085EE0DB6327607879DE4600A45F4F8B312D4E1B2A9BAE9B675156153A`
- source before/after: 2,383 bytes; SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`
- wrapper before/after: 394 bytes; SHA-256 `6D5CAFA79EC5F2939FEE2A73A7360F1E5C3D88C522F2C6044905D4160B3C90F6`
- terminal TeX-family processes 0

## New-PDF evidence

- complete denominator N52 = 38 visible glyphs + 14 drawings
- all unordered pairs C52,2 = 1,326/1,326 unique rows
- clip/empty/tofu or replacement-character failures 0
- manual glyph 38/38 PASS, drawing 14/14 PASS, critical semantic groups 16/16 PASS, opened views 6/6 PASS
- manual non-PASS 0, blank notes 0, script-generated manual fields 0
- R168 true hard failures 0

Former R2886 maps independently to new `G0001` 子 versus `D0003` lower plane boundary. The PDF bbox clearance is conservatively 9 px. Direct native-300dpi scan detects the lower boundary at rows 902–915 and glyph ink at rows 937–972, leaving 21 empty rows and zero shared ink. The upper boundary ends at row 853, leaving 83 empty rows. Native1x and nearest-neighbor 8x were opened and agree with the machine result.

The R110 integrated-page label-to-caption gap was independently measured as 85 empty rows before the verified 27.401575 px shift; the conservative projected post-patch gap is 57.598425 px. It remains an official-candidate confirmation item, not a local hard failure.

## Sealed root

- root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827`
- payload122 + controls3 = ordinary125
- CSV/JSON manifest 122/122; CSV↔JSON↔FS path/bytes/SHA/NTFS ticks mismatch 0
- files read-only 125/125; directories read-only 13/13
- ADS0, pyc0, `__pycache__`0, reparse0
- `WRITE_STOPPED.json` is uniquely strictly latest by 4,715,821 ticks; at-or-after excluding marker 0; postmarker root writes 0
- manifest CSV SHA `3D9FEB33F5114B8D39ED3D974F62AC872E97DC4F11C907581AAEAA6A9F34FA5B`
- manifest JSON SHA `82CC454038DFF72C546D27A3F95065D15C317932792677B6DBF98ECF39C4B9D6`
- WSTOP SHA `DB29767B8123D785BCEC6FE6E559201D9CECEA2C713D45CDF221175206DBEC62`

## Git scope

The worktree has exactly one unstaged source change, 1+/1-, and `git diff --check` passes. The index is empty. The only diff remains:

`at (-.18,-.23)` → `at (-.18,-.39)`

No other source, evidence root, state, inventory, or UID is modified by Git.
