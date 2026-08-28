# P654 R13 root test results

- Root sets: PASS, payload 1059 + controls 3 = ordinary 1062; exactly two manifests and WSTOP are controls.
- Prior-control isolation: PASS, R11/R12-added payload files absent.
- R10→R13 base identity: PASS, 1052 files with path/bytes/SHA-256/NTFS ticks/7-digit display differences all 0.
- R13-added payload: PASS, exactly seven files and all are present in both manifests.
- Manifest identity: PASS, CSV/JSON/current payload counts 1059/1059/1059 with all fields 0 differences.
- Provenance and script separation: PASS, resolved absolute roots, no `$` placeholders, and copy/validator/seal responsibilities are independent.
- Parse/open: PASS, JSON 73/73, CSV 24/24, PNG 856/856 and PDF 1/1.
- ADS: PASS, 1062/1062 ordinary files enumerated individually; only default `:$DATA`, non-default ADS 0 and errors 0.
- PYC/cache/read-only/seal: PASS, cache artifacts 0, all 1062 files read-only, WSTOP uniquely latest and postseal writes 0.
- Content differential audit: PASS, N=116, glyph=95, graphic=21, C=6670, critical=50, taxonomy 95→10, target n H=22/area=297 and manual 192; five views and representative/extreme counterexamples found no new content failure.
- Preseal extension snapshots: FAIL, payload/control/ordinary JSON declared 70/1/72 but final sets are 71/2/73.
- WSTOP extension snapshots: FAIL, the same three actual objects omit the preseal-report payload JSON and WSTOP control JSON.
- Root verdict: `ROOT_REJECT_R13`.
