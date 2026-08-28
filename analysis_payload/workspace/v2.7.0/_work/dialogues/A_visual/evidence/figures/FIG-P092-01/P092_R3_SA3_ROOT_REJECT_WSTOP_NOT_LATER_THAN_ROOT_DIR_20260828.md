# FIG-P092-01 R114 fresh SA3 root audit

- HANDOFF_ID: `A-R114-P092-SA3-FRESH-ISOLATED-20260828`
- Canonical instance: `/root/p092_r114_fresh_sa3`
- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R3_SA3_FRESH_ISOLATED_R114_20260828`
- Audit mode: root-external and read-only; no business rerun
- Verdict: `ROOT_REJECT_WSTOP_NOT_STRICTLY_LATER_THAN_ROOT_DIRECTORY`

## Preserved content direction

The fresh SA3 business direction is PASS and remains independently reviewable: reader-visible denominator `N=13`, exhaustive unordered pairs `C=78`, manual object/pair/view/math/semantic ledgers `13/78/11/6/8`, and no R168 true hard failure reported. This control rejection is not a business `FAIL_TO_SA2` and does not authorize source changes.

## Passing mechanical facts

- Root files: `33`; ReadOnly files: `33`; root ReadOnly: `true`.
- `MANIFEST.sha256.csv`: `31` unique rows; missing/bytes/SHA mismatches: `0/0/0`.
- Manifest SHA-256: `4731C0BF65B5649FEFB3CEAC41E2F21D014A26AE0B8A4B8F1A80BD04CAC14156`.
- `WSTOP`: `223` bytes; SHA-256 `EB725C35BC44202A330E847A22DAB0DCFE9ED500C85C285D98799A01CC4FFDDE`.
- WSTOP is later than every non-marker file by `100000000` ticks; file-only at-or-after count is `0`.
- The child reports postmarker root content and attribute writes `0` and attempted no repair, restart, duplicate, or reseal.

## Decisive control failure

- `WSTOP.LastWriteTimeUtc.Ticks = 639234547141924199`.
- `root.LastWriteTimeUtc.Ticks = 639234547750361410`.
- The root directory is later than WSTOP by `608437211` ticks.
- At-or-after count including the root directory is `1`.

The accepted P092 R2A precedent and the current Main sealing contract require the marker to be strictly later than every target file, subdirectory, and the root itself. This root therefore cannot be accepted as a mechanically sealed SA3 result, even though its file-only ordering passes.

## Routing

- R3 is permanently read-only and must not be modified, retimestamped, or resealed in place.
- Preserve the SA3 content-PASS direction and keep the central role at SA3 pending Main adjudication; do not route the figure to SA2 solely for this control defect.
- Do not start a new role or business review.
- Request exactly one fresh sibling evidence-only control reseal that copies only manifest-bound material, preserves source identity, creates new controls, and sets WSTOP sufficiently in the future to be strictly later than the root directory after the final move.
- Parent writes to the rejected R3 root: `0`.
