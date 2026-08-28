# R493 Main decision: P687 content accepted, original root rejected, control-reseal static preparation authorized

Timestamp: `2026-08-28T10:09:37+08:00`

## P687 substantive acceptance

Main independently recomputed and visually reviewed the same sealed P687 root.

- Official R115 SHA256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F` and current source SHA256 `FEB76B03845B3EA01ECD53768AA99AAF618519268667AA065A29848207AB398A` remain exact.
- Current caption localization at physical page `737`/printed `724` is correct; literal physical page 687 is an unrelated Fig. 33.4 and is retained only as disambiguation evidence.
- Denominator objects `19`, machine pairs `171`, manual pairs `171`; object/pair duplicates, self-pairs, bad references, sequence differences and required blanks are all `0`.
- Manual results are exactly `159 CLEAR + 12 ALLOWED_TOPOLOGY_CONTACT`; illegal visible-ink overlap and pair clipping are `0`; opened-view ledger is `26/26`.
- Main actually opened the native color figure+caption, grayscale figure+caption, formula/connectors NN8x ROI, loop-return NN8x ROI and full-page 200 dpi. Glyphs, formulas, arrow direction/topology, grayscale, caption, adjacent derivation and page integration show no hard counterevidence.

The preserved business verdict `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1` is accepted.

## Original-root control rejection

The root has `40` files and only the root directory; all `40/40` files and the root are ReadOnly. WSTOP has `37` physical lines, `37` unique keys, bad/duplicate/BOM `0`, is later than every file/directory/root by `191,080,843` FILETIME ticks, and has at-or-after excluding marker `0`. CSV parse, ADS, cache/pyc and reparse failures are `0`.

However, `MANIFEST_CONTROL.txt` contains only object path/type/description rows. It does not bind per-file bytes or SHA256, and WSTOP has no `MANIFEST_SHA256` binding. Thus the final control cannot cryptographically bind the 40-file payload and is rejected under the same rule previously applied to P683 SA1.

The original root is permanently frozen as `ROOT_REJECT_MANIFEST_BYTES_SHA_BINDING_MISSING`; it must not be edited, retimestamped, resealed, renamed, deleted or used directly to start SA1. P687 remains SA2 and no pass is counted.

## Static-only sibling reseal authorization

C may prepare, but not execute, one root-external controller and one independent auditor for:

- HANDOFF `C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V1`
- operation `P687_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- new root `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v1`

The new root must copy exactly the 37 business/material files while copying old controls `MANIFEST_CONTROL.txt`, `root_external_readonly_audit.txt` and `WSTOP` zero times. It must preserve canonical relative/resolved path, bytes, SHA256, CreationTimeUtc and LastWriteTimeUtc; add `COPY_IDENTITY` and resolved `COPY_PROVENANCE` for payload `39`; add exactly `PAYLOAD_MANIFEST`, `SEAL_AUDIT` and multiline no-BOM `WRITE_STOPPED` controls for ordinary `42`; set all files/directories/root ReadOnly before staging; move the prevalidated ReadOnly future marker into the root as the sole final root operation; and independently verify strict-latest including root, at-or-after `0`, postmarker `0`, old-root `0`, all CSV/JSON parse, ADS, cache/pyc and reparse gates.

Scripts must be frozen ReadOnly with PowerShell 7 AST errors `0`, controller Move-Item exactly `1`, auditor Move-Item `0`, and no destructive/process/TeX/retry-loop sites. C must return static identities, extracted-function microtests, exact new-root/stage/result absence and invocation `0/0`, then pause. No business evidence rerun, source/build/Git/central/new UID/role action is authorized.

P126 R3B V2 remains in its separately authorized one-shot execution chain. Inventory remains `30 SA1 / 32 SA2 / 0 SA3 / 38 local pass`; strict final remains `0/99`; B remains `66/66`.
