# FIG-P033-01 R111 R5A evidence-only control reseal audit

Verdict: `ROOT_ACCEPT_R5A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

## Scope

This was the one authorized evidence-only control reseal after R5's placeholder-corrupted sentinel. No PDF render, object/pair analysis, manual/semantic review, TeX, source, Git, central state, SA3, second UID or second role was run or modified.

- Rejected read-only source root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827`.
- New sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5A_SA1_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`.
- Root-external controller: 15,183 bytes, SHA-256 `A0A543BA10B1819E105AED6AE919536B81EA164C6F3C15C057B23480A132BB14`, AST errors 0, invocation 1, retry 0, exit 0.
- Root-external read-only auditor: 10,626 bytes, SHA-256 `0CD64FAC739BA66E2FAE2674BDB6D4D9C6EB5E08105524DE76200E9B273D114D`, AST errors 0.

## Lossless copy identity

- R5 manifest-bound source material: 43 unique paths.
- R5 old controls copied: 0.
- `COPY_IDENTITY.csv` rows: 43.
- Source-to-R5A relative path, bytes, SHA-256 and NTFS LastWriteTime ticks set difference/mismatch: 0/0.
- New payload records: `COPY_IDENTITY.csv` and resolved `COPY_PROVENANCE.json` only.
- Final payload: 45.

## Final control model and filesystem

- Controls: `PAYLOAD_MANIFEST.csv`, `SEAL_AUDIT.json`, `WRITE_STOPPED.json` = 3.
- Ordinary files: 48.
- Payload manifest rows/files: 45/45.
- Manifest-to-filesystem path set difference and path/bytes/SHA-256/ticks mismatch: 0/0.
- Read-only files: 48/48.
- Read-only directories including root: 7/7.
- Parse failures / ADS / cache-or-pyc / reparse: 0 / 0 / 0 / 0.
- Unresolved `$...` placeholders / TAB+`rue` corruptions / resolved identity failures / boolean type failures: 0 / 0 / 0 / 0.
- `WRITE_STOPPED` ticks: `639233892202670546`.
- Maximum other-file ticks: `639233892202044116`.
- Strict-latest margin: 626,430 ticks.
- Files at or after marker excluding marker: 0.

## Frozen identities

- Payload manifest SHA-256: `052055BE08EA5F1E13877D4580256C2E4E2AA80FC2EA5F58859D4F5583FD531A`.
- Seal audit SHA-256: `AC6BF877DAE5CB6FE30DF9BC72A09F74DF24135E816104E06D02E6F9CF0F75FB`.
- `WRITE_STOPPED` SHA-256: `25F8E15210FCC9E6D7175AEB6B12EB08AF921E6A08B0A183D6690DD38FA13940`.
- Bound coordinator report: 3,149 bytes, SHA-256 `933BD513B0B09644CCCA93DD7C724F950AF12982782F7F08CA9D9550B2F0DB7F`.
- Bound coordinator handoff: 1,559 bytes, SHA-256 `463F5C12584DF8E8338A0D4E24810E1F434DE855209FB1773C100123DADB5D04`.

R5A repairs only the control layer. The independently observed R5 content direction remains N=99, C=4,851, unresolved/illegal overlap/clip/R168 hard failures 0. P033 is ready for main acceptance of SA1 content PASS and authorization of a different completely fresh isolated SA3; A has not started SA3.
