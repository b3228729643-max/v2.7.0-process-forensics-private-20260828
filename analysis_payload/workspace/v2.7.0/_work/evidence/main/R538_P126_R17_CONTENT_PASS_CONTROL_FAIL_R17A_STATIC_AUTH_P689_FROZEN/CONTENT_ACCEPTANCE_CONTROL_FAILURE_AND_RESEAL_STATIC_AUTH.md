# Revision 538 — P126 R17 content acceptance, control failure, and R17A static authorization

Timestamp: `2026-08-28T17:40:56+08:00`

## R17 build and business direction

The unique R17 controller/direct chain completed naturally with invocations `1/1`, exits `0/0`, and retry/latexmk/version-probe/second counts all zero. The slot is released and terminal TeX-family count is zero.

- PDF: 34,138 bytes/SHA-256 `F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73`.
- Source: 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Review: `N=60`, `C(60,2)=1770`, manual objects 60, manual pairs 1770, opened views 20, glyph/codepoints 25, mathematics/semantics/page checks 14, hard/clip/illegal-overlap/unresolved 0.
- Main independently fresh-rendered the PDF at 300 dpi. The x1 legend sample is one 75px occupied run; x2 is four 11px occupied runs with complete internal blanks `11/10/10px`. Digit6/q6 and digit7/q7 shared ink is zero with blank gaps 14px and 30px. The prior `HARD-LEGEND-X2-CONTINUOUS` is absent.

Main preserves the content verdict direction `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`, but it is not yet accepted as a sealed local result.

## Single-seal control failure

- Frozen seal controller: 15,223 bytes/SHA-256 `FBB06AC1B3EF87A60DA82A494600EA999D3ADE0511DF4A71A11C9A52CD500C86`, ReadOnly/AST-clean, invocation1/retry0/exit1.
- First error is line116. The expression combined a `DirectoryInfo` and child array in the same array-addition/pipeline expression; PowerShell precedence attempted unsupported `DirectoryInfo.op_Addition`.
- Before stopping, the controller wrote only `PAYLOAD_MANIFEST.csv` (24,231 bytes/SHA-256 `8E99A474AC7A56401CAB3A6B76A283A97A4868828A70F2C65E43A05A3391C2F6`) and `PAYLOAD_MANIFEST.json` (44,534 bytes/SHA-256 `4BF553CFE0F4C9082393975728B5D332F1540549C2C4F186E386F1C125FA15AF`).
- `SEAL_AUDIT`, ReadOnly freeze, external staged marker, final marker move, controller result and auditor invocation did not occur.
- Frozen scene: 147 files and 11 directories including root, all writable; exact business/material files 145; the two manifests are rejected controls. Marker count 0; terminal TeX0.
- External failure report: 2,002 bytes/SHA-256 `F769514A6A050ABE03E8AE33B42728F390F3F795F37BF7448D1BA7586C2D962A`, ReadOnly.
- External handoff: 498 bytes/SHA-256 `465AC868085B12802737B0694DD62A62FCE1609FA2B16F43D1B86DBBFC02212F`, ReadOnly.

Decision: freeze R17 as `UNSEALED_CONTROL_FAILURE_AFTER_DUAL_MANIFEST_WRITE_BEFORE_SEAL_AUDIT_READONLY_MARKER`. No in-place edit, continuation, retry, cleanup or manual seal is permitted.

## R17A evidence-only control-reseal STATIC PREPARATION

- HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROL-RESEAL-V1-20260828`.
- Operation: `P126_R115_R17_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`.
- Future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17A_SA2_FORGET_PLOT_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`.

Only static preparation is authorized. The future root, external stage and results must remain absent and controller/auditor invocation must remain `0/0`.

Frozen scripts must encode:

- Copy exactly 145 material files and exclude the rejected `PAYLOAD_MANIFEST.csv` and `PAYLOAD_MANIFEST.json`; copy old controls 0.
- Bind canonical relative and resolved source/destination paths, bytes, SHA-256, CreationTimeUtc ticks and LastWriteTimeUtc ticks. Add `COPY_IDENTITY.csv` and resolved `COPY_PROVENANCE.json`, producing payload147.
- Controls exactly `PAYLOAD_MANIFEST.csv`, `SEAL_AUDIT.json`, and multiline no-BOM `WRITE_STOPPED`, producing ordinary150.
- Full source before/after equality; destination manifest/filesystem equality; every file, child directory and root ReadOnly before marker staging.
- Root-external staged marker set future and ReadOnly, then one sole-final move into the destination. Marker must be strictly later than every file/directory/root, with at-or-after excluding marker0 and postmarker content/attribute writes0.
- Independent auditor recomputation, CSV/JSON parse0, non-default ADS0, cache/pyc0 and reparse0.
- Correct the failed reparse expression by first materializing a root-item array and a child-item array, combining those arrays in a separate statement, and only then piping to `Where-Object`. StrictMode microtests must cover empty/scalar/multiple items and the real R17 tree without any `DirectoryInfo` addition.

Return frozen script identities, full diff/site inventory, extracted-function tests, exact future-root/stage/result absence and invocation0/0, then pause for Main. No reseal execution, business evidence read/rerun, TeX, source edit, commit, role, UID or central write is authorized.

P126 remains SA2. P689 remains frozen as C_LOCAL_PASS. Inventory remains `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`; strict final remains `0/99`.
