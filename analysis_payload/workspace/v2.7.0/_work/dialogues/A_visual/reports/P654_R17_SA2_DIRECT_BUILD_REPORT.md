# FIG-P654-01 R17 SA2 direct-build report

## Decision

`ROOT_ACCEPT_R17_FAIL_TO_SA2_SOURCE_R3_REQUIRED`.

P654 remains `SA2`. This round does not authorize a commit, fresh SA1, fresh SA3, LOCAL PASS, or A_LOCAL_PASS.

## Authorized build

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825`
- Direct LuaLaTeX invocations: 1; `latexmk`: 0; retries: 0.
- PowerShell controller PID: 21832; LuaLaTeX PID: 14728; natural exit code: 0; duration: 60.981 s.
- Source: 3,334 bytes; SHA-256 `0A7CAAA49978AA6193BA4DC4CB90845981599DFC161F5A8BD6B9143A1EA4C2EB`.
- Wrapper: 397 bytes; SHA-256 `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`.
- PDF: 1 A4 page, 43,510 bytes; SHA-256 `D83D577DEE19C1B279E7FE93DFFE99F67C3C1C49784392A490F1A79515C2311B`.
- Build slot was released immediately after the natural exit; the current TeX process count is zero.

## New-PDF evidence

- 93 glyphs + 21 foreground drawings = 114 objects.
- All 6,441 = C(114,2) unordered pairs are present.
- 173 critical pairs have dedicated raw/mask/overlay bundles and ten opened navigation sheets.
- Five glyph contact sheets, six graphic sheets, four all-pair matrices, and all five required views were opened.
- Target G0005 (`n`) is fixed: H=24px, absolute minimum=22px, frozen-group ratio=1.0000.
- Literal authoritative `N` remains in source and the three plus signs remain mathematical glyphs.
- Clip failures: 0. Illegal overlaps after semantic line-node adjudication: 0.

## Hard failures

- G0040/G0059/G0064 (`+`): H=26px, frozen median=24px, ratio=1.083333 > 1.08.
- G0065 (`N`): H=27px, frozen median=24px, ratio=1.125 > 1.08.
- P06198/P06219: G0092 `应` and G0093 `用` have 0px native clearance to D0009 node border, below the 3px gate.
- Frozen source formula role spans 11.6pt to 9.5pt: ratio=1.221053 and absolute difference=2.1pt, failing the 1.03 / 0.25pt gates.

P06240/P06261/P06285/P06347 were individually opened and adjudicated PASS as intentional line-to-node endpoints; their 1–2 shared antialias pixels are not illegal collisions.

## Seal and independent audit

- Payload: 2,051; controls: 3; ordinary files: 2,054.
- Manifest CSV: SHA-256 `93E0A4165E6608E75DAA6230E949FE722C52F50C23053C071B5278FAABA288F3`.
- Manifest JSON: SHA-256 `4FC7E4754C4F50C6C9286720DEC77C9B2F8460D11EE2B7F848D8646155CCD021`.
- `WRITE_STOPPED.json`: SHA-256 `4CEC30A27AA77BA328757E41D8BC4F50F61FFDB7E833255C3C83A7E46B38C7F9`; strictly latest.
- Independent root audit: manifest↔manifest↔filesystem identity differences 0; parse failures 0; ADS 0; Python bytecode/cache 0; symlinks 0; read-only failures 0; post-seal writes 0.
- Independent report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R17_ROOT_AUDIT.md`.

The working tree still contains exactly the authorized single P654 source patch (4 insertions, 4 deletions) and no commit was created.
