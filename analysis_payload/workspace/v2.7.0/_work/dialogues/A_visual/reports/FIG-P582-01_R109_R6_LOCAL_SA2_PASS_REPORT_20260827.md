# FIG-P582-01 R109 R6 local SA2 PASS report

- HANDOFF_ID: `A-R109-P582-SA2-DIRECT-BUILD-R6-20260827`
- Result: `LOCAL_SA2_PASS_AWAIT_ATOMIC_COMMIT_AUTHORIZATION`
- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827`
- Source SHA-256: `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`
- Exact live diff: one source, one insertion, one deletion; only annotation y `.49 -> .53`.

## One-time build identity

- Controller PID: `7712`; child LuaLaTeX PID: `2192`.
- Start/end UTC: `2026-08-26T16:22:23.2630032Z` / `2026-08-26T16:23:26.5380112Z`; duration `63.275s`.
- Exit `0`, natural `true`, interrupted `false`.
- Direct LuaLaTeX invocation count `1`; retry `0`; latexmk `0`.
- New PDF: `build/v260_FIG-P582-01_standalone.pdf`, 31,329 bytes, SHA-256 `2F96CF1B220E0A0A56D264F428D5BCE93005557040D94EB1CBB516D832E2927A`.
- Source before/after SHA identical; wrapper before/after SHA `831360DBDEFA9AF2A45ED120AF4F33E280C342D07DD1136E5FFA0E2BD592A21C` identical.
- Recorded and independently checked post-exit TeX process count: `0`.

## New-PDF denominator and hard gates

- N=95: 78 visible glyphs + 17 foreground graphic paths.
- Complete unordered pairs C=4,465, matching `C(95,2)` with unique IDs and no missing/extra/self pair.
- Empty masks `0`; page-edge clip candidates `0`.
- Machine candidates: 29 intended shared-graphic relations + 3 low-clearance intranumeric relations = 32.
- All 32 candidates were actually opened at native1x and 8x. Shared graphic ink is same-object topology; the three digit gaps (`.640` and `.380`) remain readable and are R168 advisory only.

The former hard failure is closed in the new PDF:

- Legacy route pair `P05555` maps to R6 `PAIR-03495`, `GLYPH-042` U+2193 down arrow versus `GLYPH-062` U+0030 terminal zero in `.380`.
- Native 300dpi shared pixels: `0`.
- Native 300dpi white clearance: `27px`.
- The nearest checked upper plot layers are `90.411159px` and `91.395887px` away, so the upward move creates no upper regression collision.

## Independent real manual closure

Machine scripts emitted or overwrote no reviewer, boolean, decision or note fields. After actual opening of final native/8x views, the root agent wrote:

- 78/78 glyph rows PASS, with codepoint/object-specific notes.
- 17/17 graphic rows PASS, with drawing-specific notes.
- 36 relation rows PASS: all 32 machine candidates plus target, label-spacing and upper-regression checks.
- 9/9 view rows PASS.
- 8/8 semantic recomputation rows PASS.
- Manual timestamp errors: `0`.

Independent semantic recomputation confirms raw squared values `.64,.01,.49,.16`, running means `.64,.325,.38,.325`, direction down/up/down, formula `h(U_i)=U_i^2`, truth reference `1/3`, and unchanged axes/data meanings.

## Seal and root-external audit

- Payload `237`; controls `3`; ordinary files `240`.
- Dual manifests: 237/237 rows; CSV↔JSON↔filesystem path/bytes/SHA/NTFS ticks mismatch `0`; duplicate paths `0`.
- Ordinary files read-only: `240/240`.
- `WRITE_STOPPED.json` is the unique strict-latest root write; margin `4,254,837 ticks`; files at/after marker `0`.
- ADS `0`; pyc `0`; `__pycache__` `0`; reparse points inside root `0`.
- JSON parse failures `0`; CSV parse failures `0`; final TeX processes `0`.
- Manifest CSV SHA-256: `0320F661F6905653DC9E7ED90D149F54C604A894AE8D08D71653EB64BC437BBA`.
- Manifest JSON SHA-256: `2AD4D34658A6D8F140E1C3C8627B6BA1604AEB26CE55C092460F3F8F7724666E`.
- WRITE_STOPPED SHA-256: `5CA3267A96CF2C1D627067B1A7D9748090622CE697D11045585CAE5A3087A0C0`.

The temporary ASCII junction used solely for Poppler output compatibility was verified as a junction to this root and removed; the sealed evidence root remains intact. No second build, source expansion, commit, fresh role, second UID, central state or inventory write occurred.
