# P602 R3 controller static handoff

Status: `P602_R3_CONTROLLER_STATIC_READY_REQUEST_BUILD_SLOT`.

- The accepted v3C controller package remains permanently read-only and unchanged.
- This R3 v1 controller was not executed; kpsewhich, texlua, LuaLaTeX, latexmk, luatex, and luahbtex remain disabled.
- Future candidate root `sa2_r3_controlled_build_v1` and ASCII cache root `codex_v270_p602_texcache_r3_v1` do not exist.
- Frozen source SHA256 is `6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D`; wrapper, engine, and kpsewhich identities are unchanged from accepted v3C.
- Redirected stdout/stderr persistence, RESULT exception separation, single Process.Start site, single build helper callsite, compound SUCCESS hard gate, and no-retry control flow are unchanged.
- The future authorization token is frozen as `P602_R3_V1_ONE_DIRECT_LUALATEX_SLOT_GRANTED`; static acceptance alone does not authorize execution.
- Main review and a separate explicit build-slot grant remain mandatory.
