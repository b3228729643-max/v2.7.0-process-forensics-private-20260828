# P654 R6 direct-controller preflight

- `RESULT`: `PASS`
- `TYPESETTING_INVOCATIONS`: `0`
- `PARENT`: PowerShell 7.6.4, PID `12808`
- `CHILD`: ordinary Windows PowerShell 5.1, PID `15672`
- `CHILD_LAUNCH`: inherited process environment; no explicit `-Environment` override
- `KPSEWHICH`: `D:\texlive\2026\bin\windows\kpsewhich.exe`
- `EXACT_BINDING`: `D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/dialogues/A_visual/evidence/figures/FIG-P654-01/STRICT_R6_SA2_NARROW_R100_DIRECT_PREFLIGHT_20260825/texcache`

## Environment and cache resolution

The parent assigned `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` to the same exact absolute binding. The child captured all three actual process values; their unique-value count is 1 and every value exactly equals `EXACT_BINDING`.

For each of the three variables, the same child ran both `kpsewhich --var-value=<NAME>` and `kpsewhich --expand-var=$<NAME>`:

- rows: `3/3`;
- command exits: `6/6` equal 0;
- raw exact binding matches: `6/6`;
- canonical absolute-path matches: `6/6`.

The first executed harness captured the correct child environment and wrote the probe, but decoded native CP936 `kpsewhich` output as UTF-8; that attempt is retained in `CHILD_PREFLIGHT.json` and `PARENT_PREFLIGHT_RESULT.json` with `pass=false`. The final harness changed only native-output decoding and the forward-slash environment spelling; `CHILD_PREFLIGHT_ATTEMPT2.json` and `PARENT_PREFLIGHT_RESULT_ATTEMPT2.json` are the accepted PASS evidence.

## Child write probe

- `ABSOLUTE_PATH`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R6_SA2_NARROW_R100_DIRECT_PREFLIGHT_20260825\texcache\P654_R6_CHILD_WRITE_PROBE.txt`
- `BYTES`: `42`
- `MTIME_UTC`: `2026-08-24T20:06:34.9690479Z`
- `MTIME_TICKS_UTC`: `639231987949690479`
- `SHA256`: `4ECE7048D6D816959FD437DC55A8C7A3AED6ED6C4320C474F6D5B965225C21C8`
- `TEXCACHE_ENTRY_COUNT`: `1`

The same final child rewrote the retained unique probe path, and no second cache file exists. This proves that the actual child token can write to the resolved `texcache` path.
