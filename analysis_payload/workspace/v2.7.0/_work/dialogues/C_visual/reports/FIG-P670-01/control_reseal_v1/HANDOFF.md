# P670 replacement V2 evidence-only control reseal handoff

## Decision route

- UID: `FIG-P670-01`
- HANDOFF_ID: `C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2-CONTROL-RESEAL-V1`
- Operation: `P670_REPLACEMENT_V2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- Business verdict carried without rerun: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
- Scope: control-only copy/reseal; PDF/render/object/pair/manual/math/semantic rerun count `0`
- TeX/source/PDF/Git/central/process/second UID/second role actions: `0`

## One-shot controller

- Script: `controller/P670_CONTROL_RESEAL_V1.ps1`
- Script bytes/SHA-256: `26504` / `D2FEF2F6756DA6016F0105BAF7C9C798FE775C1209BE2F33EC9F0F7E518A6581`
- Invocation/retry: `1/0`
- Natural exit: `0`
- UTC: `2026-08-27T18:33:53.0457490Z` to `2026-08-27T18:33:54.6062227Z`
- Result: `CONTROLLER_RESULT.json`, bytes/SHA-256 `22046` / `C0AC8629E9393A694C5706001C7DFC18CBE98FA8B11DD66D2BFA69B21C56E753`
- Old-root baseline: `OLD_ROOT_BEFORE.csv`, bytes/SHA-256 `10882` / `6F8A81A95F3BD2860517559B2013F579F2F4A26E612F372A88915367E5E083C2`

## New sealed root

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2_control_reseal_v1`
- Source material copied: `27`
- Old controls copied: `0`
- Added payload: `COPY_IDENTITY.csv` + `COPY_PROVENANCE.json`
- Payload/controls/ordinary: `29/3/32`
- Files ReadOnly: `32/32`
- Directories including root ReadOnly: `4/4`
- Source-root before/after ordinary count: `29/29`
- Source-root identity mismatch: `0`

Control identities:

- `COPY_IDENTITY.csv`: `16613` bytes / `E0E30C2C4544DE1AF79A09D156DDE56911F8FEC09C81FDD2603FB6F3AB4F8C60`
- `COPY_PROVENANCE.json`: `2120` bytes / `6B9E0B0A1990C30F73CB45658C21B338A61F228CF5C005677BB805C6C3B06E98`
- `PAYLOAD_MANIFEST.csv`: `10837` bytes / `F8E8583EC992620732130F887D2EDBC63E5D18AEBD0DFBF285F33C1FE54825F9`
- `SEAL_AUDIT.json`: `1834` bytes / `38A5A7B7E750CCE0CF7C9CE34294ECBA49EAB6CE80D8F61FCA5C843252891A30`
- `WRITE_STOPPED`: `882` bytes / `B544B479D1085D13E176D3C7BA64F9846809D238DA48A0C4A7258DF1A503C82E`

Marker closure:

- Physical lines/unique keys/bad lines/required failures: `13/13/0/0`
- UTF-8 BOM: `false`
- Marker FILETIME: `134323292353104832`
- Max-other FILETIME: `134323292343104832`
- Strict margin: `10000000` ticks
- At-or-after excluding marker: `0`
- Post-marker file identity/attribute mismatch: `0`
- Post-marker directory time/attribute mismatch: `0`

## Independent root-external auditor

- Script: `auditor/P670_CONTROL_RESEAL_AUDITOR_V1.ps1`
- Script bytes/SHA-256: `20106` / `912FDA0AC32AD31B4A3A4FF6AA6B87AE2573912A492CCCCF483FDF6EB1025ECA`
- Invocation/retry: `1/0`
- Natural exit: `0`
- Result: `AUDIT_RESULT.json`, bytes/SHA-256 `1554` / `25251B36128436569F3EF3FF6587D5FEB55D8C5D226B479B1126CDF9A37B0490`
- Old-root mismatch/control mismatch: `0/0`
- Copy identity/provenance failures: `0/0`
- Manifest/FS identity mismatch: `0`
- CSV/JSON parse failures: `0`
- ADS/cache-pyc/reparse: `0/0/0`
- Final auditor failures: `0`

## Unresolved

`NONE`. This handoff requests Main's independent acceptance of the control reseal. It does not migrate P670, start fresh SA1, or update central state/inventory.
