# P654 R12 root test results

- Sealed root: PASS, 1062 ordinary files = 1059 payload + 3 root controls; all 1062 files read-only.
- R11 control isolation: PASS, all five R11-added files absent.
- R10→R12 base identity: PASS, 1052 source/destination relative paths; missing/extra/bytes/SHA-256/NTFS ticks/7-digit display differences all 0.
- R12 added payload: PASS, exactly seven new R12 files; all are present in both manifests.
- R12 manifest identity: PASS, CSV/JSON/current-filesystem counts 1059/1059/1059; missing/extra/duplicate/path/bytes/SHA-256/ticks/display differences 0.
- Provenance: PASS, resolved absolute R10/R12 roots, round and timestamp present; `$src`, `$dst` and generic `$` placeholders 0.
- Script responsibility separation: PASS, copy/validator/seal stages do not call or import one another; validator report is included in payload and seal consumes its PASS status read-only.
- Parse/open: PASS, 73/73 JSON, 24/24 CSV, 856/856 PNG and 1/1 PDF.
- ADS/PYC/cache: PASS, non-default ADS 0, `.pyc` 0 and named cache directories 0.
- Seal order: PASS, `WRITE_STOPPED.json` uniquely latest, files at or after it excluding itself 0.
- Content differential audit: PASS, N=116, glyph=95, graphic=21, C=6670, critical=50, taxonomy 95→10 groups, target `FRM_TRIAL_005` H=22/area=297 and 192 manual decisions; systematic representative/extreme samples found no new content contradiction.
- Terminal ordinary denominator: FAIL, `ordinary_file_count=1059` but actual ordinary is 1062.
- Preseal extension denominator: FAIL, declared `ordinary_extension_denominator={json:71,csv:24,png:856,pdf:1}` mixes payload and ordinary scopes; neither collection matches the complete object.
- Root verdict: `ROOT_REJECT_R12`.
