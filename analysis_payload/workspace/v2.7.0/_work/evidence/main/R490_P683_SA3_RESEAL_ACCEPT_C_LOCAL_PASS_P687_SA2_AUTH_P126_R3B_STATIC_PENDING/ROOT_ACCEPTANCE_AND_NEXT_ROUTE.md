# R490 Main adjudication: P683 SA3 reseal accepted; P687 SA2 authorized

Timestamp: `2026-08-28T09:40:00+08:00`

## P683 decision

- Accepted HANDOFF `C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V2` and operation `P683_R115_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V2`.
- The already accepted fresh-SA3 business result remains `N31/C465`, manual elements `31/31`, manual pairs `465/465`, hard/clip/illegal/unresolved `0`; the V2 operation did not rerun business evidence.
- Main independently recomputed the new root, rather than relying only on the controller/auditor summaries:
  - source material/copy rows `39/39`, copy duplicate and source/destination path/bytes/SHA256/Creation+LastWrite FILETIME mismatch `0`;
  - payload/manifest `41/41`, case-sensitive duplicate/set/identity mismatch `0`; old controls copied `0`;
  - controls exactly `PAYLOAD_MANIFEST.csv`, `SEAL_AUDIT.json`, `WRITE_STOPPED`; ordinary files `44`; directories including root `3`;
  - files ReadOnly `44/44`, directories/root ReadOnly `3/3`;
  - marker physical lines/unique keys/bad lines/BOM `13/13/0/false`; all identity, count, manifest SHA, seal SHA, verdict, control-only and postwrite bindings exact;
  - marker FILETIME `134323543330590419`; maximum other FILETIME including directories/root `134323542730799395` (filesystem readback precision), positive margin `599,791,024` ticks; at-or-after excluding marker `0`;
  - source-before versus current mismatch `0`; postmarker snapshot versus current mismatch `0`;
  - JSON/CSV parse failures, ADS, cache/pyc, and reparse findings all `0`.
- Frozen controller remains `24,300` bytes/SHA256 `0C48B0E09A3416561B632D18F2BE3861959A3C5AD73A7FE5588F48528E456A3F`; frozen auditor remains `19,173` bytes/SHA256 `DAD60C6C2EDC54B10933E766695493EEE0274CC6647506853BABA2691411AD5A`; both ReadOnly. Controller/auditor results are natural success with invocation `1/1`, retry `0/0`, and no second invocation.
- P683 is therefore accepted as `C_LOCAL_PASS` and permanently frozen. Original rejected SA3 root, failed V1 scene, accepted V2 root, scripts and run evidence must not be modified, rerun, resealed, or migrated.

## Inventory and next C route

- Inventory becomes `31 SA1 / 31 SA2 / 0 SA3 / 38 local pass`; strict final remains `0/99`; B remains `66/66`.
- The next C item is authorized, but not yet counted as a role transition until its actual identity returns:
  - UID `FIG-P687-01`;
  - HANDOFF `C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`;
  - requested actual `/root/sa2_fig_p687_r115_r168_readonly_v1`;
  - model/effort/fork `gpt-5.6-sol/xhigh/none`;
  - new root `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1`, with parent and root absent at Main pre-route gate;
  - official R115 `4,967,161` bytes/SHA256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`;
  - current source `3,401` bytes/SHA256 `FEB76B03845B3EA01ECD53768AA99AAF618519268667AA065A29848207AB398A`;
  - exact V5-C06 chapter `120,809` bytes/SHA256 `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`.
- Fresh role must use only exact allowlisted current inputs, independently prove root absence before artifacts, and must not read prior P687/P683/other UID evidence, metrics, verdicts, state/history, directory listings, Git/chat or agent-status tools. PDF/source are read-only; TeX/build/source/Git/central/process/second UID/role actions remain forbidden.

## P126 boundary

- P126 remains SA2. Its R3A root remains `UNSEALED_CONTROL_FAILURE_AFTER_PREMARKER_READONLY_FREEZE`; no LOCAL_SA2 result is counted.
- A has only static-preparation authority for the R3B sibling evidence-only control reseal. Controller/auditor invocation must remain `0/0` and the new evidence root must remain absent until Main reviews the returned frozen scripts.
- No P126 source, build, TeX, commit, fresh role, second UID, or central write is authorized. The eventual lines 63--66 legend source scope remains held until a compliant sealed R3B preservation root is independently accepted.
