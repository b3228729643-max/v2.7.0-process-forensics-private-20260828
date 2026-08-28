# Revision 154 — C FIG-P602-01 fresh isolated SA3 main acceptance

## Verdict

- Handoff: `C-FIG-P602-01-R101-SA3-FRESH-ISOLATED-V1`.
- C root gate: `ROOT_MECHANICAL_ACCEPT`.
- Main package decision: `ACCEPT`.
- Figure strict result: `FAIL`.
- Central route: `SA2`.
- This is not `C_LOCAL_PASS`, `A_LOCAL_PASS`, global PASS, or authorization to count the figure complete.

## Main independent mechanical check

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa3_r101_fresh_isolated_v1`.
- Ordinary files: 1,020; manifest rows: 1,018; exact unlisted set: `evidence_manifest.csv`, `WRITE_STOPPED.json`.
- Duplicate path, missing file, bytes mismatch, SHA-256 mismatch and NTFS 100-ns mtime mismatch: all 0.
- Manifest SHA-256: `98A0431433333EE55DB8531C2EF8BE8C605A84CC57301D69F42B538F496F2C81`.
- Marker SHA-256: `13A9A1E9667DC1F1621F881E4C6D8E5A26EBDE8010A85CA6B8B19B396761E23C`.
- Files later than marker: 0. ADS: 0.
- Object set: 32 unique IDs. Pair table: 496 unique unordered pairs, exactly `C(32,2)`, missing/extra/duplicate/self pairs all 0.
- Manual ledgers: object 32/32 PASS; glyph 158 PASS + 17 FAIL; pair 496/496 PASS; critical 17/17 PASS; peer 36 PASS + 6 FAIL; role 2 PASS + 1 FAIL; clip 32/32 PASS; view 4/4 PASS; hard gates 8 PASS + 4 FAIL. Every ledger has unique IDs, nonblank evidence and nonblank ID-specific reasons.
- Main opened the full page, native figure/standalone views and representative glyph failure cards (`G007`, `G132`, `G160`, `G167`). The rendered identity is physical R101 page 651 / printed page 638 / figure 32.5; the strict failure evidence is visually consistent with the recorded masks and measurements.

## Dispositive failures and routing

- Glyph failures: 17, including fixed-threshold math/operator and CJK failures plus calibrated punctuation failures.
- Peer failures: 6.
- Role failures: 1 (`ROLE03`, ratio `1.2244897959183674 > 1.18`).
- Hard gates failed: `HARD03`, `HARD07`, `HARD08`, aggregate `HARD12`.
- FIG-P602-01 remains central `SA2`. C may receive a separately scoped single-source SA2 authorization; TeX remains separately gated.

Recorded: 2026-08-25T12:57:06+08:00.
