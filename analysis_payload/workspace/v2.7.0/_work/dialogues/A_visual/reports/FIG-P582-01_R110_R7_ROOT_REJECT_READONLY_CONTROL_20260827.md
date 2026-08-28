# FIG-P582-01 R110 R7 root audit

## Verdict

`ROOT_REJECT_R7_SA1_CONTROL_LAYER_READONLY_MISMATCH`

The fresh SA1 content direction remains `PASS`, but the sealed evidence root is not mechanically acceptable for routing to SA3 because its persisted NTFS read-only state contradicts the role report.

## Identity

- HANDOFF_ID: `A-R110-P582-SA1-FRESH-ISOLATED-20260827`
- Instance: `/root/p582_r110_fresh_sa1`
- Candidate: official R110, physical page 632 / printed page 619 / Fig. 31.7
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7_SA1_FRESH_ISOLATED_R110_20260827`
- Root audit was read-only. No R7 file or timestamp was modified.

## Preserved content direction

- 139 glyphs, 44 objects, 946 unordered pairs, 35 critical relations, and 13 view/role rows closed.
- Machine final overlap, clip, and clearance hard failures: 0.
- R168 hard failures: 0; four disclosed micro-profile/peer items remain advisory only.
- Manifest rows / actual payload: 140 / 140; normalized missing/extra/duplicate paths: 0 / 0 / 0.
- Manifest-to-filesystem size and SHA-256 mismatches: 0 / 0.
- Payload bytes: 4,733,173.
- Payload-manifest SHA-256: `86228AB04920BF76ED7093C4FF08542629266A6878BE666817569F6CCEA03C50`; checksum control matches.
- Ordinary files: 143 = 140 payload + manifest JSON + manifest checksum + WRITE_STOPPED.
- PNG parse denominator: 116; failures: 0. ADS, pyc, and cache findings: 0.
- WRITE_STOPPED ticks: 639233640795734695; maximum other-file ticks: 639233639654826551; strict-latest margin: 1,140,908,144 ticks; files at/after marker: 0.

## Decisive control failure

The role report states `Final read-only payload check: PASS`, but the independent filesystem audit found:

- payload read-only: 0 / 140;
- control read-only: 0 / 3;
- ordinary-file read-only: 0 / 143.

All files therefore persisted with `IsReadOnly=false`. This is a direct contradiction of the sealed report and the required read-only control gate. The old R7 root must remain untouched; it cannot be repaired or retimestamped in place.

## Route

Keep FIG-P582-01 in SA1 and do not start SA3. Request one fresh evidence-only control reseal that copies the 140 manifest-bound payload files losslessly into a new root, verifies path/bytes/SHA/mtime identity, makes payload and controls read-only, writes WRITE_STOPPED strictly last, and performs the final read-only audit outside the new root. No visual, object, pair, or manual review needs to be rerun unless the mainline requires it.
