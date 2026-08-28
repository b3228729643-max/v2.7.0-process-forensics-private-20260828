# P126 R17 single-seal controller failure report

- Business-review direction preserved provisionally: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH` (N60/C1770, manual objects60/pairs1770/views20, glyph25, math-semantic-page14, hard0).
- Control classification: `UNSEALED_CONTROL_FAILURE_AFTER_DUAL_MANIFEST_WRITE_BEFORE_SEAL_AUDIT_READONLY_MARKER`.
- Frozen seal controller: 15,223 bytes/SHA256 `FBB06AC1B3EF87A60DA82A494600EA999D3ADE0511DF4A71A11C9A52CD500C86`, ReadOnly, AST0.
- Controller invocation/retry/exit: 1/0/1.
- Auditor invocation: 0.
- First error: controller line116, where PowerShell parsed `(Get-Item ...) + @(Get-ChildItem ...) | Where-Object ...` such that `DirectoryInfo` received an unsupported `op_Addition` call.
- Failure boundary: after `PAYLOAD_MANIFEST.csv` and `PAYLOAD_MANIFEST.json` writes, before `SEAL_AUDIT.json`, any ReadOnly freeze, external WSTOP stage, marker move, controller result, or auditor call.
- Frozen R17 scene at `2026-08-28T09:38:56.9403153Z`: files147, files ReadOnly0/147; directories including root11, directories ReadOnly0/11; root ReadOnly=false.
- `PAYLOAD_MANIFEST.csv`: 24,231 bytes/SHA256 `8E99A474AC7A56401CAB3A6B76A283A97A4868828A70F2C65E43A05A3391C2F6`, writable.
- `PAYLOAD_MANIFEST.json`: 44,534 bytes/SHA256 `4BF553CFE0F4C9082393975728B5D332F1540549C2C4F186E386F1C125FA15AF`, writable.
- `SEAL_AUDIT.json`, `WRITE_STOPPED`, external marker stage, controller result: absent.
- PDF remains 34,138 bytes/SHA256 `F336C6C8A47B17F18257F5BAFDE58817766D1BEE12C60931857B221C20002A73`.
- Source remains 4,686 bytes/SHA256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Terminal latexmk/lualatex/luatex/luahbtex: 0/0/0/0.

No in-place controller edit, retry, continuation, manifest rewrite, attribute freeze, marker creation/move, auditor call, repair, cleanup, source edit, TeX, commit, new role, second UID, or central-state action followed the first error. The R17 scene is preserved for Main adjudication.
