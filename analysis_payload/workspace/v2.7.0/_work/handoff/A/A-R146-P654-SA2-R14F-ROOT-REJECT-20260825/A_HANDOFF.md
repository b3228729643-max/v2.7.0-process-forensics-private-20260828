# Dialogue A handoff — FIG-P654-01 R14F root rejection

- HANDOFF_ID: `A-R146-P654-SA2-R14F-ROOT-REJECT-20260825`
- STATUS: `ROOT_REJECT_R14F_READY_FOR_MAIN_SCOPE_ADJUDICATION`
- FIGURE_ID: `FIG-P654-01`
- CENTRAL_ROLE_REQUEST: keep `SA2` pending mainline adjudication
- SOURCE_SHA256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- COMMIT_CREATED: no
- TEX_REQUIRED: no

## Execution identity

The one-time R14F grant was consumed exactly once with `D:\PowerShell7\pwsh.exe -NoProfile` and token `P654_R14F_COPY_SEAL_EXPLICITLY_GRANTED`.

- reviewed script identity: 3/3
- prepare invocation/exit: 1/0
- validator invocation/exit: 1/0
- seal invocation/exit: 1/0
- retry: 0
- sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14F_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`

The root is permanently read-only. No TeX, source edit, commit, fresh SA1, or fresh SA3 occurred.

## Fresh root verdict

Exactly one fresh isolated root audited the sealed root and issued `ROOT_REJECT_R14F`.

Its sole rejection basis is that the final 1059-row CSV/JSON payload manifests persist five fields — `relative_path`, `bytes`, `sha256`, `mtime_utc_ticks`, and `mtime_utc_7digit` — rather than six. All five persisted fields agree across CSV, JSON, and filesystem with zero differences. The separate 1052-row R10 base-copy identity CSV/JSON tables contain six fields and also agree with zero differences.

All other required mechanical, content-preservation, hygiene, and write-stop gates passed. P654 remains SA2 and no local-pass promotion is claimed.

## Mainline adjudication requested

The latest execution grant asks to report dual-manifest/filesystem `path+bytes+SHA+ticks`; the observed five-field final manifests contain those four identity axes plus the 7-digit UTC display. Earlier six-field wording applies explicitly to the source/destination base-copy identity tables. The fresh-root dispatch nevertheless required six fields for final manifests and therefore produced the formal rejection above.

Please independently decide whether the sixth-field requirement applies to the final payload manifests. This handoff does not override or rewrite the immutable root verdict and does not request an automatic new reseal round.

## Evidence

- root report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R14F_ROOT_AUDIT.md`
- report bytes: 10387
- report SHA-256: `D8BE21514D0EB6DF8DCDC0137C1BBA2C05F3BB3545E69F029FDB24B4532A19A1`
- report read-only: true

