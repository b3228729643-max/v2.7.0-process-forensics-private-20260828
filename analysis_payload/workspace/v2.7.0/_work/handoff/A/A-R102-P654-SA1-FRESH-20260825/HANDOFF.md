# A-R102-P654-SA1-FRESH-20260825 handoff

- OWNER_ROLE: `FIG-P654-01 / fresh isolated SA1`
- STATUS: `SA1_FAIL_TO_SA2`
- OFFICIAL_COMMIT: `94d1b62b877e80000539879688e6209c09882833`
- OFFICIAL_PDF_SHA256: `60026DE5A4168D6F3B304D1AE59BE68E1F570CD22D992E43FCAD9828E25A1397`
- PDF_IDENTITY: `817 pages / all A4 / 4,958,396 bytes`
- TARGET: `physical 704 / printed 691 / FIG-P654-01`
- SOURCE_SHA256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- DENOMINATORS: `95 glyph / 21 graphic / 116 object / 6670 unordered pair / 121 critical`
- MANUAL_ROWS: `95 glyph / 21 graphic / 6670 pair / 5 view`
- GEOMETRY: `illegal overlap 0 / clip 0 / min text-text 4 / min text-graphic 5 / min node-border 18`
- HARD_FAILURE_IDS: `G0005,G0014,G0042,G0061,G0066,G0067`
- HARD_FAILURE_GATE: `frozen PANEL_ID+ROLE+SCRIPT_CLASS glyph-to-median ratio must lie in [0.92,1.08]`
- EVIDENCE_ROOT: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R15_SA1_FRESH_R102_20260825`
- ROLE_REPORT: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R15_SA1_FRESH_R102_REPORT.md`
- PAYLOAD_MANIFEST_SHA256: `303D679FFC4F304E2B59BFAC734F68E91D821FB1ACC8688C63DC2B59D0561A9A`
- SHA256_MANIFEST_SHA256: `9FE57DD5EEE30F9DEEABAB170F915633C7CDF237A9EE10502D90A3DAC4B077B2`
- SEAL: `1497 ordinary files; ADS/pyc/cache/colon = 0/0/0/0; all read-only; WRITE_STOPPED latest; post-seal writes/execution/imports = 0`

Required main action: route exactly these six hard failures to SA2. Do not start SA3 and do not claim `A_LOCAL_PASS` for R102.
