# FIG-P067-01 R3 root audit and local SA2 verdict

- HANDOFF_ID: `A-R111-P067-SA2-DIRECT-BUILD-R3-20260827`
- UID: `FIG-P067-01`
- Verdict: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827`

## Build identity

- Direct LuaLaTeX typeset invocation: 1; retry: 0; latexmk: 0.
- Engine-version probe: 1, separately disclosed and classified by Main R351 as a non-typesetting probe.
- Child/controller exit: 0/0; natural exit true; interrupted false.
- PDF: 34,208 bytes; SHA-256 `C1C06D877227E407F85678C0842182EE3629AEC78B62A4418C94A1D81860609E`.
- Source: 4,015 bytes; SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0` before and after.
- Wrapper: 388 bytes; SHA-256 `ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF` before and after.
- Terminal TeX-family process count: 0.

## Content closure

- Final denominator: N=115 = 65 glyph + 50 foreground path; 5 white-fill/no-stroke background rectangles are rationally excluded.
- All unordered pairs: C(115,2)=6,555; duplicate=0; self=0.
- Critical relationships: 16.
- Machine hard failures, clip, empty foreground atoms, unresolved assignments: 0.
- Genuine post-open manual coverage: 115/115 object IDs and 16/16 critical relationships; blank/nonpass/hard-fail=0; object notes unique 115, relationship notes unique 16.
- Machine scripts generated or overwrote no manual reviewer, timestamp, state, decision, or note fields.
- Actual views opened before ledger creation: full standalone page, native figure, grayscale figure, atomic overlay, both critical tick crops, all three glyph sheets, and all three path sheets.
- Former `0.35`↔`0.3`: foreground intersection 0, native rounded bbox clearance 1 px, nearest-8x clearance 8 px.
- `0.3`↔`0.15` regression: foreground intersection 0, native rounded bbox clearance 1 px, nearest-8x clearance 8 px.
- The 1 px rounded native gaps are R168 advisory only; the labels are complete, readable, and visibly separated. PMF/CDF probability, cumulative monotonic/right-continuous behavior, endpoint semantics, axes, guides, notes, grayscale, caption, and page integration have no hard failure.

## Seal history and final mechanical audit

The first root-external seal controller is permanently frozen at 8,323 bytes/SHA-256 `A6D959A59D32ED71F1ADE74DF74036EBA77B1AE82B536403D29683E37AC7CAD6`. Its only invocation exited 1 before any root write because `Group-Object relative_path` did not dereference ordered-dictionary keys. At that point R3 remained 129 ordinary files and all four controls were absent.

Main R354 authorized exactly one sibling controller. `P067_R3_SEAL_RETRY_20260827.ps1` is 11,738 bytes/SHA-256 `60E08739F266CF6F7BD189BDF2FE6B0C02B1AD329455491BDC087BC4248C4703`, AST errors 0. It used explicit dictionary-key grouping and passed StrictMode empty/one/two-unique/duplicate microtests before root writes. Invocation count 1, retry 0, exit 0.

Final root audit:

- payload=129, controls=4, ordinary=133;
- CSV manifest rows=129 and JSON manifest rows=129;
- duplicate paths=0; CSV↔JSON↔filesystem path/bytes/SHA-256/NTFS ticks errors=0;
- read-only files=133/133; read-only directories=13/13 including root;
- `WRITE_STOPPED.json` unique and strictly latest by 51,106,683 ticks;
- files at/after marker excluding marker=0; post-marker content or attribute writes=0;
- JSON parse failures=0; ADS=0; reparse=0; unexpected cache/pyc outside the authorized build `texcache`=0;
- authorized `texcache` files=89 and are manifest-bound/read-only.

Control identities:

- `PAYLOAD_MANIFEST.csv`: SHA-256 `7366A04331AC5E4F020113F3BBB4ED2DCAEEA5DDEC282F4826255DFA8E738C9B`
- `PAYLOAD_MANIFEST.json`: SHA-256 `6FB9980790A801A7EECF247D46B549AC0FA01B79F29E186E0E0D5A94E73F927E`
- `PRESEAL_VALIDATION.json`: SHA-256 `42E16880EF8CCB6970F728C1C35C51B4199623520A84AA8F440739D7A5D60AFB`
- `WRITE_STOPPED.json`: SHA-256 `E8D4ABB67837CE0770D4D230D140BBB2940A5F2D2BF93ABC213084A13634F43E`

## Git boundary

- Branch: `v2.7.0/dialogue-a-visual`; parent HEAD before any authorized commit: `d8f1e5fb15abdf09ce5ead5245c270b43abd5741`.
- Working tree diff: exactly one source, 3 insertions / 1 deletion; index empty; `git diff --check` exit 0.
- No commit is made by this report. Main atomic commit authorization is requested.
