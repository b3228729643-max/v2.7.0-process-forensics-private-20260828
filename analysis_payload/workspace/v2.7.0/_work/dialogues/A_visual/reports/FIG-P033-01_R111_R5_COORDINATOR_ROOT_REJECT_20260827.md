# FIG-P033-01 R111 R5 coordinator root audit

Verdict: `CONTENT_PASS_DIRECTION_PRESERVED / ROOT_REJECT_WRITE_STOPPED_PLACEHOLDERS / NO_SA3`.

## Accepted content direction

- HANDOFF_ID: `A-R111-P033-SA1-FRESH-ISOLATED-20260827`.
- Actual instance: `/root/p033_r111_fresh_sa1`, `gpt-5.6-sol/xhigh`, `fork_turns=none`.
- Official R111 SHA-256: `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`.
- Current P033 source SHA-256: `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`.
- Frozen denominator: N=99 (85 glyph + 14 graphic atoms); all unordered pairs C=4,851.
- Pair closure: 4,770 machine-disposed + 81 individually observed focused relations = 4,851; unresolved 0.
- Manual relation notes are pair- and object-specific; native1x/nearest8x sheets and all seven focused ROIs were opened before ledger closure.
- Canonical illegal overlap 0, clipping 0, R168 hard failures 0. The 9.2/9.4 pt declarations are advisory only.

These facts preserve the SA1 content-PASS direction but do not establish a protocol-valid sealed root.

## Mechanical facts that pass

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827`.
- Manifest-bound payload: 43; controls: 3; ordinary files: 46.
- Manifest-to-filesystem path set difference: 0; bytes/SHA-256 mismatch: 0; duplicate manifest paths: 0.
- Read-only files: 46/46; read-only directories including root: 7/7.
- `WRITE_STOPPED.md` is strictly latest by 859,637 ticks; files at or after marker excluding marker: 0.
- Manifest SHA-256: `1F8C11FDCD4C10B43D14DE4CE5839EB8696A259321B630E568D317E0E793F9E9`.
- `SEAL.json` SHA-256: `F329A9BCC473AFB8F4F388590DC1EE4FDEA4105CE157B35DD8A0751CABF966A2`.
- `WRITE_STOPPED.md` SHA-256: `4AC8F831E79AB02F4ABC28D145F4F6180988756061A861A2755AD8A04B5D9EF0`.

## Decisive control failure

The sealed `seal/WRITE_STOPPED.md` contains seven unresolved variable placeholders instead of their resolved values:

- `$sealedAt`
- `$manifestHash`
- `$sealHash`
- `$reportPath`
- `$reportHash`
- `$handoffPath`
- `$handoffHash`

Its three boolean declarations are also corrupted: PowerShell interpreted the backtick before `true` as a tab escape, so each line persists a tab followed by `rue`, not the declared value `true`.

The frozen `seal/seal_once.ps1` shows the cause: the expandable here-string wrapped each value in Markdown backticks, escaping the `$` variables and the leading `t` in `true`. Consequently, the final sentinel is not self-contained and its claimed identity/closure fields do not bind the actual report, handoff, manifests or seal values. A strictly latest mtime cannot cure unresolved control content.

## Route

R5 remains permanently read-only and must not be modified, retimestamped or resealed in place. Do not start SA3 and do not count SA1 PASS yet. If main accepts this audit, the narrow next action is a single newly authorized evidence-only control reseal into a new root, preserving the 43 R5 payload files byte-for-byte while generating resolved control metadata and a final placeholder-free `WRITE_STOPPED`.
