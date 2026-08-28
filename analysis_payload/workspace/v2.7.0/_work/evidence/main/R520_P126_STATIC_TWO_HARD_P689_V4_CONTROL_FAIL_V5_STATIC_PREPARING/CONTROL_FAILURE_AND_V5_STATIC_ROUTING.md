# R520 — P689 V4 control failure and V5 static routing

Timestamp: `2026-08-28T13:38:38+08:00`

## P126

P126 remains SA2. Main's R519 acceptance of the R9 sealed business result remains authoritative: `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`, N60/C1770, only P00541 failed, with the remaining hard defects limited to the continuous x2 legend sample and the digit-6/marker contact. The only active source authorization remains STATIC_ONLY: replace the x2 legend sample with three disconnected horizontal `mark=-` bars and change only digit 6 `yshift=10pt` to `15pt`. No TeX/build, commit, fresh role, or other source delta is authorized.

## P689 V4 failure acceptance

Main accepts the reported and independently checked V4 scene as `UNSEALED_CONTROL_FAILURE_AT_PREMARKER_MARKER_PARSE`:

- frozen controller `38,494` bytes / SHA-256 `331517AF72979D4B07B1E134992E888436A8F556F1ED0355C414D7240308E0FE`, invocation1/retry0/exit1;
- frozen auditor `39,674` bytes / SHA-256 `56FF00BA9CAE30021C64C32D2A8CEAA45A4D462AA71F1F302A61617FA8166DDF`, invocation0;
- first error: the single `=` match from `Where-Object` was a scalar under StrictMode, so direct `.Count` access failed;
- partial destination contains 47 files and no child directories; all files and the root are ReadOnly; the in-root marker and all postmarker/results artifacts are absent;
- external staged marker is preserved ReadOnly/future-dated at 924 bytes / SHA-256 `4C33E0552BF6C518B7DB6B28CCD991CFD69C9ED18EE891714AD091ACB0BD164E`.

The V4 partial root, staged marker, scripts, and failure scene are frozen. No reuse, cleanup, retimestamp, move, retry, repair, or reseal is authorized.

## V5 static-only authorization

Only startup-absent V5 STATIC PREPARATION is authorized:

- HANDOFF: `C-FIG-P689-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V3`
- OPERATION: `P689_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V3`
- fixed destination: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P689-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v3`
- fixed static directory: sibling `control_reseal_static_v5`.

V5 must preserve the accepted clean-material contract and all V4 ADS, stage, four-snapshot, dynamic CSV/JSON, ReadOnly, strict-latest, postmarker-zero, and old-root-zero-write gates. It must change both the controller and auditor equals-sign count sites to the array-closed form `@(...).Count`, classify every `.Count` site in both scripts with unsafe sites equal to zero, and test the frozen parser under StrictMode using root-external temporary marker files: exactly one equals sign must pass without a property error; zero/two equals signs, blank lines, and duplicate keys must fail. File/root/directory ADS tests, exact delta, frozen bytes/SHA, AST/sites, new-root/stage/result absence, and invocation0/0 must be returned before pausing.

No V5 controller/auditor execution, business rerun, P689 fresh SA1, TeX/build, source/Git/central/process action, second UID, or second role is authorized.
