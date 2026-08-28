# R354 P067 R3 control-seal retry authorization

## Decision

`P067_R3_PRESEAL_CONTROLLER_FAILURE_ACCEPTED_AS_CONTROL_ONLY`.

The first controller invocation is not a business or visual failure. It exited before any root control file or other root mutation because `Group-Object relative_path` attempted property access on `[ordered]` dictionary rows. Main independently verified:

- R3 still contains exactly 129 ordinary payload files.
- `PAYLOAD_MANIFEST.csv`, `PAYLOAD_MANIFEST.json`, `PRESEAL_VALIDATION.json`, and `WRITE_STOPPED.json` are all absent.
- All 129 current files remain writable preseal payload; no root file has a post-failure timestamp.
- Original controller `P067_R3_SEAL_20260827.ps1` is 8,323 bytes with SHA-256 `A6D959A59D32ED71F1ADE74DF74036EBA77B1AE82B536403D29683E37AC7CAD6`; its single failed invocation is final and must not be retried.
- Frozen content identities remain: `MACHINE_RESULT.json` 424 bytes/SHA `E9D48B3834BAD412B55D973B94F9547CE3E65060EBD2793CB36AD54330EDA6D8`; `FINAL_CROSSCHECK.json` 1,022 bytes/SHA `35B6995A92CD194F3304663910904EADB4DE42360DFF3173E02CEB6B7D9771B4`; `FINAL_RESULT.json` 1,460 bytes/SHA `A681399BE56D3F6FDA4799C94412E92978827C8A86F53FA94829A69A32123D20`; `LOCAL_SA2_PASS_REPORT.md` 2,332 bytes/SHA `22FA464A75C1DB4BA357B6CD1B5F7B177014413943AEB2A1B8D437B3BBEF8D6C`.

## Exactly-once retry grant

A is authorized to create one new root-external sibling controller, preferably `P067_R3_SEAL_RETRY_20260827.ps1`, and invoke it exactly once with PowerShell 7. The old controller is immutable evidence and may not be edited or invoked again.

The new controller must:

1. Have static AST parse errors 0 and disclose bytes/SHA before invocation.
2. Replace property-name grouping with explicit dictionary-key grouping, for example `@($payloadRows | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })`.
3. Under StrictMode, pass isolated microtests for empty input, one unique row, two unique rows, and a duplicate-key pair; all possibly empty pipeline results must be array-wrapped before `.Count`.
4. Before any root write, require the exact R3 root, ordinary count 129, all four control files absent, the four frozen content identities above unchanged, source SHA `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`, PDF 34,208 bytes/SHA `C1C06D877227E407F85678C0842182EE3629AEC78B62A4418C94A1D81860609E`, and terminal TeX-family process count 0.
5. Generate only the declared four controls: two payload manifests, `PRESEAL_VALIDATION.json`, and one final `WRITE_STOPPED.json`; projected final ordinary count is 133.
6. Preserve all 129 payload paths/bytes/SHA/NTFS last-write ticks exactly; manifest CSV, manifest JSON, and live filesystem must agree with duplicate/missing/extra/identity mismatch 0.
7. Set all payload/control files and every directory including the root ReadOnly. The final marker must be built outside the root, made ReadOnly, and moved into the root as the sole final root operation, so post-marker root content and attribute writes are both 0.
8. Produce one root-external read-only audit confirming parse gates, ADS/cache/pyc/reparse 0, WSTOP unique and strictly latest, at-or-after excluding marker 0, and the exact final identities.

No PDF/render/object/pair/manual/semantic rerun, source change, TeX, Git commit, fresh role, second UID, or central state write is authorized. A successful control retry returns `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`; it does not self-authorize a commit.

## Concurrent P660 checkpoint

P660 R111 fresh SA3 independently froze 16 semantic visible objects and all 120 unordered pairs, with 20 reader-visible text measurement elements. It opened all eight pair montages, six native1x/nearest8x ROI families, and the sole candidate P001. P001 is current-source coordinate-layer topology; the other 119 pairs have zero shared foreground and a minimum 26 px gap. Manual ledgers and seal remain pending; no P660 outcome is accepted here.

