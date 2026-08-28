# Revision 155 — FIG-P654-01 R102 fresh SA1 main acceptance

## Verdict

- Handoff: `A-R102-P654-SA1-FRESH-20260825`.
- Main package decision: `ACCEPT`.
- Fresh SA1 result: `FAIL_TO_SA2`.
- Central route: `SA2`.
- SA3 is not authorized and this is not `A_LOCAL_PASS` or global PASS.

## Candidate binding and sealed package

- Official main commit: `94d1b62b877e80000539879688e6209c09882833`.
- Official R102 PDF: 817 A4 pages, 4,958,396 bytes, SHA-256 `60026DE5A4168D6F3B304D1AE59BE68E1F570CD22D992E43FCAD9828E25A1397`.
- Target: physical page 704 / printed page 691 / FIG-P654-01.
- Source SHA-256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`.
- Evidence root ordinary files: 1,497; payload manifest rows: 1,494; exact excluded controls: `PAYLOAD_MANIFEST.json`, `SHA256_MANIFEST.csv`, `WRITE_STOPPED.md`.
- Duplicate/missing/bytes/SHA mismatch: all 0. Payload manifest SHA `303D679FFC4F304E2B59BFAC734F68E91D821FB1ACC8688C63DC2B59D0561A9A`; CSV manifest SHA `9FE57DD5EEE30F9DEEABAB170F915633C7CDF237A9EE10502D90A3DAC4B077B2`.
- All 1,497 files are read-only; ADS 0; files later than `WRITE_STOPPED.md` 0.

## Denominators and failures

- Objects: 116 unique = 95 glyph + 21 graphic.
- Unordered pairs: 6,670, exactly `C(116,2)`; missing/extra/duplicate/self pairs all 0.
- Critical relations: 121.
- Manual ledgers: glyph 95 unique with nonblank per-ID notes; graphic 21; pair 6,670 unique with nonblank notes; views 5/5 PASS.
- Pair and geometry gates: illegal overlap 0, clip 0; text-text minimum 4 px, text-graphic 5 px, node-border 18 px.
- Exact hard failures: `G0005,G0014,G0042,G0061,G0066,G0067`. The glyph ledger has exactly 89 PASS and 6 FAIL, matching `failing_hard_gates.csv`, `final_gate_summary.json`, `RESULT.txt`, the role report and handoff.
- Dispositive gate: frozen `PANEL_ID + ROLE + SCRIPT_CLASS` glyph-to-median ratio `[0.92,1.08]`. Ratios are respectively `0.916667`, `1.227273`, `1.208333`, `1.208333`, `1.208333`, `1.375000`.
- Main opened the R102 full page, native figure crop and glyph contact sheets containing all six failures; contour/overlay/mask evidence is consistent with the recorded measurements.

## Routing

- FIG-P654-01 returns to central SA2. Any source change remains limited to the single P654 figure source and requires a later official candidate plus a wholly fresh SA1.
- R15 is immutable evidence and cannot be promoted to SA3.

Recorded: 2026-08-25T13:18:00+08:00.
