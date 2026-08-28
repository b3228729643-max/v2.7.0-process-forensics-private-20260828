# FIG-P608-01 R12 local SA2 decision

Status: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

## Frozen identities

- Source before SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- Source after SHA-256: `49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E`
- Source diff: one file, one insertion, one deletion; shared plot domain `[1,20]` changed to `[0.5,20.5]`.
- Wrapper SHA-256 before/after: `E2FB8001752859933614E085DDEB74538F80C3C8D9C3938E9BB9B2FEF5C937E9`.
- Build PDF: `build/local_wrapper_r12_worktree.pdf`, 43,012 bytes, SHA-256 `A50EE094843FDA68A3E3CDCFA0F5DC1F4884B1FDA853A6B3BECEE7DB2758452A`, one A4 page, PDF 1.7, unencrypted.
- Direct LuaLaTeX: PID 19228, exit 0, one invocation, zero retry, natural completion; final TeX process count zero.

## Regression result

- Objects: N=128 (68 glyphs + 60 graphics).
- All unordered pairs: C(128,2)=8,128, all evaluated.
- Critical pairs: 12 indexed and manually opened.
- Empty masks / illegal overlaps / clearance flags / clip failures / hard readability failures: 0 / 0 / 0 / 0 / 0.
- Former PAIR-06596: 0 shared pixels, 16.464 px clearance, PASS.
- Former PAIR-06650: 0 shared pixels, 12.928 px clearance, PASS.
- Fifteen running-mean values and final `2.0000`: PASS.
- Full page, crop, grayscale, 68-glyph contact sheets, 60-graphic contact sheets, critical sheets, and target relation sheet: manually opened and PASS under R168.

This decision does not authorize a commit, fresh SA1/SA3, or A_LOCAL_PASS. It awaits main-thread acceptance, source integration, an official candidate, and a completely fresh isolated SA1.
