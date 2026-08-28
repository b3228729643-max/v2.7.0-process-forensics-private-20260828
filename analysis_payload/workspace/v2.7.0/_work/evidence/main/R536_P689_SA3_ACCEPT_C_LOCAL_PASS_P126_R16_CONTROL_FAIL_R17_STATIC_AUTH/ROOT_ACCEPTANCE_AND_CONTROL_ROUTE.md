# Revision 536 — P689 SA3 acceptance and P126 R16 control route

Timestamp: `2026-08-28T17:11:09+08:00`

## P689 fresh SA3 independent acceptance

- HANDOFF: `C-FIG-P689-01-R115-SA3-FRESH-ISOLATED-V1`
- Actual: `/root/sa3_fig_p689_r115_fresh_isolated_v1`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa3_r115_fresh_isolated_v1`
- Official input: R115 physical 739 / printed 726 / Fig. 35.5; PDF 4,967,161 bytes/SHA-256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`.
- Current source: 3,425 bytes/SHA-256 `7BAED58EE4634091A2873D84942A2CA4E2C2475D509B2FA5FDCB5A28E5FADE5F`.
- Authoritative exact chapter context: 120,809 bytes/SHA-256 `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`. A prior apparent mismatch came from checking a stale dialogue worktree chapter, not this dispatched authoritative context.

Main independently recomputed:

- `N=33`, `C(33,2)=528`; mechanical objects 33, mechanical pairs 528, manual pairs 528, unique pair IDs 528.
- Manual pair classes are exactly `520 CLEAR + 8 INTENDED_CONTACT_CLEAR`.
- Glyph/codepoint ledger contains 10 actual PASS rows; math/semantics contains 8 PASS rows. The earlier count of 3 was a Main regex error that counted only table rows beginning with backticks.
- Missing/tofu/wrong-codepoint, clip, illegal visible-ink collision, unresolved pair, mask contamination and hard-defect counts are zero.
- Main opened `target_figure_caption_native_300dpi.png`, its grayscale counterpart, the object overlay, KL-inequality NN8x, stationary-curve NN8x and caption-label NN8x. Formulae, double-vs-single bar glyphs, monotone staircase, upper-bound distinction, local/stationary wording, grayscale hierarchy and caption integration show no counterevidence.

Root/control recomputation:

- Files 46, child directories 0, manifest rows 44; manifest-listed set and path/bytes/SHA identities match the filesystem with zero mismatch.
- `seal_manifest.csv` SHA-256: `25DDB17EF0471D667225456B18B42AB936B477D7F67EC55D9F7BE19D3C4BF83D`.
- Marker SHA-256: `955BEF51DA22F4235E332E3F4FAEAF97AB2CA7269B8411D712E37EF98DF7161A`.
- Marker has 24 physical nonempty lines and 24 unique `KEY=VALUE` keys; malformed, duplicate, BOM and binding failures are zero.
- Marker FILETIME ticks `639235045282054306`; maximum other file/root ticks `639235045182600879`; including-root strict margin `99,453,427` ticks; at-or-after excluding marker 0.
- All 46 files and root are ReadOnly. CSV/JSON parse failures, non-default ADS, cache/pyc and reparse entries are all zero. Post-marker content and attribute writes are zero.

Decision: accept `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE` as `C_LOCAL_PASS`. P689 moves `SA3 -> C_LOCAL_PASS`; all P689 source/roles/roots/evidence/reports/handoffs are permanently frozen. No P689 rerun, reseal, migration or new role is authorized.

## P126 R16 build-control failure

- HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R16-20260828`.
- Frozen controller: 7,460 bytes/SHA-256 `6A492CC53285A9CD692C260FE89DB641C0BA49E8B1A97D67C7BB83F077795E81`, ReadOnly/AST clean.
- Sole controller invocation exited naturally with error at line 63: PowerShell 7 does not support `New-Item -ItemType Directory -LiteralPath $root`.
- The failure preceded the first fixed-root, cache, record, child, PDF or typeset write. Direct LuaLaTeX child count is 0; retry/latexmk/version-probe/second counts are 0; current TeX-family process count is 0; the exact R16 root remains absent.
- Immutable failure report: 2,086 bytes/SHA-256 `22791C9DCB36B73BE13F93ECDD47DD525A34CFE6A368DEAA8CC16CEB787C3F53`.
- Immutable handoff: 683 bytes/SHA-256 `B6C4E9AF674F68B6DA2D441389A8F1B24285BBB720F7F8E22E81E15297C89C65`.

Decision: classify and freeze R16 as `BUILD_CONTROL_FAILURE_BEFORE_ANY_ROOT_OR_TYPESET_WRITE`. It is not a candidate build and grants no implicit retry.

## R17 static-only authorization

Only STATIC PREPARATION is authorized:

- HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROLLER-STATIC-20260828`.
- Operation: `P126_R115_R17_DIRECT_BUILD_CONTROLLER_STATIC_PREPARATION`.
- Fixed future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17_SA2_FORGET_PLOT_PATCH_R115_DIRECT_BUILD_20260828`.
- The future root must remain startup-absent during preparation. Freeze one root-external ReadOnly, PowerShell 7 AST-clean controller whose execution path uses exactly one `[IO.Directory]::CreateDirectory($root)` root-creation operation and contains no `New-Item -LiteralPath` site.
- Preserve source 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`, wrapper 395 bytes/SHA-256 `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`, and engine 6,656 bytes/SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`.
- Return controller bytes/SHA, AST/site inventory, an isolated disposable temporary-path microtest of the exact directory-creation primitive, exact future-root absence, TeX-family 0, and controller/direct-child invocation `0/0`, then pause.

No controller execution, LuaLaTeX child, source edit, commit, fresh role, second UID or central write is authorized by this revision.

Inventory after the decision: `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`; strict final remains `0/99`; B remains `66/66`.
