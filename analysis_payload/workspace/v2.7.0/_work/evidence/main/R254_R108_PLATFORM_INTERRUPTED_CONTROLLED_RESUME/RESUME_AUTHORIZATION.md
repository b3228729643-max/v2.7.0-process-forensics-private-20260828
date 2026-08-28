# R254 R108平台中断与受控Resume

- Main commit：`e33a3b7490ba39304181c25f775221e63a35b6a4`。
- Initial invocation：`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r108_fullbook -NoPublish`。
- External event：Codex turn/platform abort caused the unified exec parent to disappear before natural completion.
- Read-only postcheck：`latexmk/lualatex/luatex/luahbtex=NONE`；log停约480页；partial PDF=2,303,591 bytes；无最终Output/PASS/exit身份。
- Decision：`PLATFORM_INTERRUPTED_NO_CANDIDATE`；partial PDF不得作为官方候选或角色输入。
- One controlled recovery authorized：同一输出根、无Clean，执行一次`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r108_fullbook -Resume -NoPublish`。
- Boundaries：不从零构建、不自动retry；A/C保持R108 TeX锁冻结。
- Goal SHA-256：`4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`。
