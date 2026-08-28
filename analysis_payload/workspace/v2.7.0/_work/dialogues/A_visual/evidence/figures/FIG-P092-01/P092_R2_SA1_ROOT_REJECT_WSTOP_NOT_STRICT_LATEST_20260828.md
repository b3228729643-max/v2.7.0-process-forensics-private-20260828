# FIG-P092-01 R114 fresh SA1 root audit

- HANDOFF_ID: `A-R114-P092-SA1-FRESH-ISOLATED-20260828`
- Sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R2_SA1_FRESH_ISOLATED_R114_20260828`
- Audit mode: root-external, read-only, no business or visual rerun
- Verdict: `ROOT_REJECT_WSTOP_NOT_STRICT_LATEST`

## Preserved content direction

The fresh SA1 business evidence remains a PASS direction: frozen denominator `N=21`, exhaustive unordered-pair universe `C=210`, completed post-observation object/pair/view/math-semantic ledgers, and no R168 true hard defect reported. This report does not upgrade that direction to an accepted sealed SA1 PASS.

## Mechanical facts that pass

- Root ordinary files: `22`; non-read-only files: `0`; root ReadOnly: `true`.
- `CONTENT_MANIFEST.csv`: `19` `ROOT_CONTENT` rows plus `1` `FINAL_MARKER_EXPECTED` row.
- Manifest-bound content duplicate/missing/bytes/SHA mismatches: `0/0/0/0`.
- Manifest SHA-256: `4DB477C19EE05CE8228BFA65FFC956FFEF3D5E67C131F758A840A267CFFF3E76`.
- `WSTOP`: `283` bytes; SHA-256 `6F2E8FD548248DEECD9580A34DC922D8F7B264FAB1E9F9BFBE608DFA9E29666C`.
- External handoff is ReadOnly and has SHA-256 `72CEF461007864CD4631739C5AAA6EB4F4A08FF0AAC6E6531233593F062FE980`.

## Decisive control failure

`WSTOP.LastWriteTimeUtc.Ticks = 639234517090705074`, but two non-marker root files are later:

1. `CONTENT_MANIFEST.csv`: ticks `639234517862341766`, later by `771636692` ticks.
2. `PREMARKER_AUDIT.md`: ticks `639234518257890719`, later by `1167185645` ticks.

Therefore:

- non-marker files at or after WSTOP: `2`;
- strict-latest margin: `-1167185645` ticks;
- the required `WSTOP strictly latest / at-or-after excluding marker = 0` gate fails.

Moving a pre-timestamped marker into the root as the final membership operation does not satisfy the explicit file-time strict-latest gate when its preserved NTFS mtime is older than existing controls.

## Routing

- The R2 root is permanently read-only and must not be modified, retimestamped, or resealed in place.
- The content PASS direction may be preserved only as material for a separately authorized, fresh sibling evidence-only control reseal.
- No SA3 may start from this rejected root until Main accepts a compliant sibling reseal.
- Parent audit writes to the sealed R2 root: `0`.

Requested next action: Main authorizes exactly one fresh sibling evidence-only control reseal that preserves the manifest-bound material bytes/SHA/mtime, creates compliant new controls, and makes a newly timestamped already-ReadOnly WSTOP the unique strictly latest file before its final move.
