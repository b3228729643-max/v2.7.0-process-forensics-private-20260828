# P632 R110 SA1 evidence-only readonly reseal handoff

- Handoff ID: `C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-READONLY-RESEAL-V1`
- Authorization: `MAIN_R286_P632_SA1_ROOT_REJECT_ONE_CONTROL_RESEAL_AUTHORIZATION`
- Outcome: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3` content direction preserved; control-only readonly reseal PASS; main acceptance still required.
- Original root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa1_r110_fresh_isolated_v1`
- New root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa1_r110_fresh_isolated_v1_readonly_reseal_v1`
- Control root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa1_r110_fresh_isolated_v1_readonly_reseal_control_v1`

## Controller identity and execution

- PowerShell 7 static preflight: PASS; controller/auditor/preflight AST errors `0/0/0`; new root absent; existing invocation/result absent; TeX/Start-Process/retry-loop tokens 0.
- Controller: 19,969 bytes; SHA-256 `AF13A71A2994F228FD84B0F96D308ECEB7F52DEDE3F4D74F8E43979D2A1B5DFE`.
- Invocation: ordinal `1`, limit `1`, retry `0`.
- Start: `2026-08-26T18:43:37.3059425Z`.
- Finish: `2026-08-26T18:43:39.1164331Z`.
- Duration: `1.810491` seconds.
- Exit: `0`; failure: `null`.
- No TeX, source, Git, central-state, visual, object, pair, manual, semantic, role, or second-UID operation occurred.

## Copy provenance and closure

- Source manifest-bound material payload: `46`.
- Old `MANIFEST.json` copied: `0`.
- Old `WRITE_STOPPED` copied: `0`.
- Added payload: `COPY_IDENTITY.csv` and `COPY_PROVENANCE.json`, exactly `2`.
- Final payload: `48`; controls: `3`; ordinary files: `51`; directories: `1`.
- Source-to-destination relative path/bytes/SHA-256/NTFS mtime-ticks mismatch: `0/0/0/0`.
- Payload manifest duplicate/missing/extra/bytes/SHA-256/mtime-ticks mismatch: `0/0/0/0/0/0`.
- Readonly: files `51/51`; directories `1/1`.
- JSON/CSV parse failures: `0/0`.
- ADS/cache-pyc-pyo/reparse: `0/0/0`.
- `WRITE_STOPPED` is the unique strict latest file; at-or-after excluding marker `0`; postmarker content writes `0`.

## New-root immutable identities

- `COPY_IDENTITY.csv`: 26,927 bytes; SHA-256 `61F1EDAB14A1E8CAE203A3D591606397400D852F5AF51DE0EDB19FAF8D80089B`.
- `COPY_PROVENANCE.json`: 1,563 bytes; SHA-256 `02CE90E3A72F5C5953499F0BE558819654A0D68D4CF0F9B6FE5B48A6177D1EFF`.
- `PAYLOAD_MANIFEST.json`: 12,728 bytes; SHA-256 `71CE104CF63B628A936B5E206281F4E8A896EEBED0E958657C448B96632EA4DA`.
- `SEAL_AUDIT.json`: 1,205 bytes; SHA-256 `8EA0A076855B492119F5903779BB6C46EE0BC023A25AF83CD35FA6818C0FEAB0`.
- `WRITE_STOPPED`: 701 bytes; SHA-256 `352A4B58EFCADDF2F194541134F24E47E97F17925601BE16ACC055D7457E94AA`; mtime ticks `639233666201022209`.

## Root-external evidence

- `STATIC_PREFLIGHT.json`: 2,087 bytes; SHA-256 `A8D1C83D790D9416AB5E534354385891350191BAD985F654C6582EDB6B1D41DA`.
- `CONTROLLER_INVOCATION.json`: 1,095 bytes; SHA-256 `4AC445ED6B11F0573422D0E603C0A65473E76EBDF9CBAE1B09BF3990FF630806`.
- `CONTROLLER_RESULT.json`: 583 bytes; SHA-256 `479BBADAED5182F4B9DAFBC5C3D646EECFEC73469E3A1BD6081CA4D189CA4894`.
- `EXTERNAL_AUDIT.json`: 1,994 bytes; SHA-256 `697FA58C7CC7C9214A62BFFD665D016DAFA7C444905A91BF4532BEDB9A0B5E60`; result PASS.

## Next action

Main must independently accept this control-only reseal before authorizing a different completely fresh isolated SA3. C has not started SA3 or another UID.
