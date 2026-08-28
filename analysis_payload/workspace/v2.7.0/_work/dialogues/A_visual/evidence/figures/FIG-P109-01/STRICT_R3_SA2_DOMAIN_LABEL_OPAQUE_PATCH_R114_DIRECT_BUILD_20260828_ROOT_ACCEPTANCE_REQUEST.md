# FIG-P109-01 R3 local SA2 acceptance request

- HANDOFF_ID: `A-R114-P109-SA2-DIRECT-BUILD-R3-20260828`
- Requested route: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`
- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828`

## Build identity

The single controlled build used one PowerShell7 controller and one direct LuaLaTeX child, with retry/latexmk/version-probe counts all zero. It ended naturally with exit 0; source, wrapper, controller and engine identities remained unchanged; terminal TeX-family counts were all zero.

The unique PDF is `build\v260_FIG-P109-01_standalone.pdf`, 26,500 bytes, SHA-256 `C615152183FCB524F2B4FBDFB4A69D43C134DCDE20F989BF0050C2D2776A199D`, one A4 page, PDF 1.7 and unencrypted.

## Business result

The only source remains `fig_v1_c07_convex_set.tex`, 1,922 bytes, SHA-256 `887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355`. The live diff is exactly one file and 1+/1-: the existing domain-label node gains `fill=white,fill opacity=1,text opacity=1,inner sep=1.2pt`; its coordinates, anchor, text, font and color are unchanged, as are the set boundary, segment, points, formulas and caption. `git diff --check` passes.

The final non-TeX denominator is N=15 (10 drawing plus 5 text objects), with C=105 all unordered pairs. Genuine post-observation ledgers contain 15 object rows, 105 pair rows, 20 opened-view rows, 8 mathematics/semantic rows and 52 glyph/codepoint rows; identifiers are unique, notes are nonblank and non-PASS rows are zero.

The former hard relationship P013 (set boundary O001 versus domain text O014) now has shared ink 0 and minimum visible-ink distance 9 px. Protective background O009 covers all domain-label glyphs, including mathematical `C`. The boundary is intentionally hidden only behind the label, with clean entry and exit edges and perceptually continuous geometry. Formula/segment, endpoints, interpolation markers, statement box, grayscale and page integration have no hard regression. Machine and manual R168 hard-failure counts are both zero.

The frozen standalone wrapper deliberately suppresses `\caption`, so this standalone PDF does not render a caption; the source caption is unchanged and no caption token was modified.

## Seal and independent audit

- Payload/control/ordinary: 131/4/135; subdirectories below root: 9.
- Both manifests contain 131 payload identities. CSV/JSON/FS path, bytes, SHA-256, CreationTimeUtc ticks and LastWriteTimeUtc ticks differences are zero; duplicate paths are zero.
- All 135 files, all 9 subdirectories and the root carry Windows ReadOnly; missing count zero.
- `WRITE_STOPPED` is unique, has 12 valid unique KEY=VALUE lines, and is strictly later than every other file, directory and root entry by 2,999,610,232 ticks. Excluding-marker at-or-after count is zero.
- Controller double snapshot and independent auditor current snapshot prove postmarker content/attribute mutations zero.
- JSON/CSV parse, ADS, pyc/cache and reparse counts are all zero.

Immutable identities:

- `PAYLOAD_MANIFEST.csv`: 21,803 bytes / `F4C2D2EEADC5806DEF1491B649DA3F3D6ED5E9A2EDF3D19C1FD869581B03FE31`
- `PAYLOAD_MANIFEST.json`: 40,924 bytes / `A3A7D39870AB08A5F821E4CEED471EC027E992ABD6A097BE378AF03C79BC6D36`
- `SEAL_AUDIT.json`: 797 bytes / `A73CDEA4B8C39752308E028558FCDCCBDBEFE02D6614DC2DDD281D285AB49193`
- `WRITE_STOPPED`: 544 bytes / `D4BC98D80D96E0E20CF9F22D5BD795D48C23E839D5673040C166E0208E80DAB7`
- `FINAL_CROSSCHECK.json`: 2,913 bytes / `AA1C12B8031C30E81136473E31F1E6B86583726A10CDAFEF036304E2E58DCF47`
- Root-external controller result: 1,335 bytes / `E0F547EBABD075F94DDB587EFC000BE97409646339B4B0086520099E156D5D8E`
- Root-external independent audit: 1,290 bytes / `0878EB45A058640C6090F4BB8192925460B37D93B741462A2DF936FC8440112E`

No commit or fresh role has been created. Main review and separate atomic-commit authorization are requested.
