# Revision 537 — P126 R17 static controller acceptance and execute-once authorization

Timestamp: `2026-08-28T17:17:42+08:00`

## Frozen artifact

- Static HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROLLER-STATIC-20260828`
- Static operation: `P126_R115_R17_DIRECT_BUILD_CONTROLLER_STATIC_PREPARATION`
- Controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17_DIRECT_BUILD_CONTROLLER_STATIC_20260828.ps1`
- Identity: 7,577 bytes/SHA-256 `4D219649CCE1F55FBBE6D157BD77D7074F79524C5BCCDF428F85D714B487A0F8`, Windows ReadOnly.
- Future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828`.

Main read all 183 lines and independently parsed the PowerShell 7 AST:

- AST errors 0.
- Exact fixed-root `[IO.Directory]::CreateDirectory($root)` site 1; total `CreateDirectory` sites 3 for fixed root, build and texcache.
- Direct `Start-Process -FilePath $engine` site 1.
- `New-Item ... -LiteralPath`, latexmk command, version probe, retry/while/do, Remove and Clear sites 0.
- Root absence is checked before all input identities and creation. Source, wrapper and engine are checked before creation and again after the child; controller identity is checked before/after.
- Preflight and terminal `latexmk/lualatex/luatex/luahbtex` counts must all be zero.
- `TEXMFVAR`, `TEXMFCACHE`, `TEXMFCONFIG` and `TEXMFHOME` are all assigned the same resolved fresh R17 texcache.
- Unique PDF success requires child exit0, exactly one PDF in the build directory, and the exact standalone PDF path.

Independent live gates:

- Source 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Wrapper 395 bytes/SHA-256 `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`.
- Engine 6,656 bytes/SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`.
- Exact R17 root absent; TeX-family process count 0; controller/direct-child invocation `0/0`.
- A's isolated disposable-path microtest used the same `[IO.Directory]::CreateDirectory` primitive, resolved the exact created directory, verified it empty and removed only that exact temporary directory; before/after absent and the fixed R17 root was untouched.

The controller's internal HANDOFF/operation remain the frozen static-package identity. Revision 537 is the separate, explicit execution authority; the script must not be edited to rename those fields.

## Execute-once grant

Authorization token: `MAIN_R537_P126_R17_STATIC_ACCEPTED_EXECUTE_ONCE_GRANTED`.

Exactly one invocation of the immutable controller is allowed. It may launch at most one direct LuaLaTeX child. Required counts are controller/direct `1/1` on actual launch, retry/latexmk/version-probe/second `0/0/0/0`, with first-error stop. No edit, repair, second invocation or alternate root is permitted.

On natural success, A must first report slot release, controller/child timing and exits, terminal TeX0, stable source/wrapper/engine/controller identities and the unique PDF bytes/SHA. Then no more TeX is allowed; A may perform exactly one non-TeX full N/C/manual/native1x+NN8x/color/grayscale/overlap/clip/math/caption/page review and single seal from that PDF, explicitly reporting both legend samples and the x2 internal blank runs.

On any controller or child failure, A must stop at the exact scene, report the first error and preserve all artifacts without edit, retry, cleanup, continuation, second build or business PASS claim.

No source edit, commit, fresh role, second UID or central write is authorized. P126 remains SA2. P689 remains permanently frozen as C_LOCAL_PASS. Inventory remains `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`; strict final remains `0/99`.
