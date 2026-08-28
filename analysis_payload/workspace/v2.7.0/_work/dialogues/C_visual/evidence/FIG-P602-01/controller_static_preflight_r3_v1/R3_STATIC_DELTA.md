# P602 accepted v3C to R3 v1 static delta

The accepted `controller_static_preflight_v3c` package remains byte-identical, read-only, and historical. This new package is static-only and has not executed any child process.

Authorized R3 substitutions are limited to:

| Field | v3C | R3 v1 |
|---|---|---|
| expected source SHA256 | `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349` | `6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D` |
| future candidate root | `sa2_r2_controlled_build_v3c` | `sa2_r3_controlled_build_v1` |
| ASCII cache root | `codex_v270_p602_texcache_v3c` | `codex_v270_p602_texcache_r3_v1` |
| authorization/record schemas | `P602_V3C_*` | `P602_R3_V1_*` |
| cache probe prefix | `.p602_v3c_probe_` | `.p602_r3_v1_probe_` |

Preserved without relaxation: wrapper path/SHA and working directory, engine path/SHA, kpsewhich path/SHA, same-child four-variable environment, `openout_any=p`, path containment, fresh-root gates, atomic kpse/claim/START/RESULT records, stdout/stderr persistence before RESULT, six separate exception fields, single generic Process.Start site, single build helper callsite, post-process-zero SUCCESS gate, and no retry.

Static equivalence is checked by reversing only the authorized substitutions in memory and requiring the reconstructed controller bytes to match the accepted v3C controller SHA256 exactly. No draft execution is part of that check.
