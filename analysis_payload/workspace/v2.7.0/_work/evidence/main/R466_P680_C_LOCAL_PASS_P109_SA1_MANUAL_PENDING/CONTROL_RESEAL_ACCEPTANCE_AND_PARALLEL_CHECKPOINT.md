# R466 P680 control-reseal acceptance and P109 checkpoint

Timestamp: `2026-08-28T05:50:43+08:00`

## P680 acceptance

Main accepts `C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1` and the preserved fresh SA3 result as `C_LOCAL_PASS`.

- New sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1_control_reseal_v1`
- Copy identity: 37 rows; source/destination relative/resolved path, bytes, SHA-256, Creation and LastWrite FILETIME mismatch 0.
- Payload/manifest: 39/39; ordinary files 42; directories including root 5.
- All files and directories including root are ReadOnly.
- Manifest duplicate/set/identity mismatch: 0.
- WSTOP: 12 physical lines, 12 unique keys, bad/duplicate/required failures 0, BOM absent.
- Manifest SHA-256: `4CC41E1B8BD9E405AF1B72BE5F82867AC927B1C7D6AA4F69B0FEC3874C01426D`.
- Marker SHA-256: `5F0E0F0F1A8DE0E0659E3A31F934B7529FE785FA98FB5F3FCFD1D122A22E6A4D`.
- Marker is strictly later than all files/directories/root by 297,278,304 FILETIME ticks; at-or-after excluding marker is 0.
- Postmarker root snapshot mismatch 0; rejected old-root before/after mismatch 0.
- JSON/CSV/ADS/cache-pyc/reparse failures: 0.
- Controller result SHA-256: `15E4B8D36D79167DCA5121C9278063D143D49967BE6AFAB5920A7E79DE73CE2A`.
- Auditor result SHA-256: `45CD3D00E8822D66FAED7B4699F8090AD9C2EBE8F056D5FC18280B9C9E223E53`.
- Immutable handoff: 3,235 bytes, SHA-256 `1B111B13D10D959A89B0DC3067112C8ECF6E3699F1EBDBC3D2C66E2631A9982C`, ReadOnly.

The original rejected root and accepted sibling reseal root are both permanently frozen. No business evidence was rerun.

## P109 parallel checkpoint

The accepted fresh R115 SA1 instance `/root/p109_r115_fresh_sa1` independently located physical page 116 and froze a current-input denominator of 15 reader-visible semantic objects with all 105 unordered pairs. Before manual authoring it opened full-page300, native300 crop, whole nearest8x, grayscale, page-integration200, object/text overlays, and six native1x plus six nearest8x critical ROI images. Manual ledgers remain pending; hard blocker is 0 and no PASS is claimed.

Inventory: `32 SA1 / 32 SA2 / 0 SA3 / 36 local pass`; strict final `0/99`; B `66/66`.
