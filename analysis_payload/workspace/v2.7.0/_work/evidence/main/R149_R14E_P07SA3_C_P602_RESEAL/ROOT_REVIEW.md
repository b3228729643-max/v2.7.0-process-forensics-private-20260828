# Revision 149 root review

## Fixed identities

- Goal SHA-256: `4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- main HEAD: `eea4060c5229168e2b973bbaea81cf391e7a9dfd`
- official R101: 814 A4 pages, 4,947,496 bytes, SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`
- inventory: `43 SA1 / 55 SA2 / 0 SA3 / 1 A_LOCAL_PASS`
- strict final: `0/99`

## P654 R14E static acceptance

- R14D was not executed. Its full no-write remainder evaluator correctly found JSON DateTime coercion and live-key mutation.
- R14E five frozen files matched their reported bytes/SHA and were read-only; the future sealed root did not exist.
- Main independently parsed all three drafts with zero AST errors and compared R14D→R14E. The only semantic deltas were the new round/root/token, one identity JSON `-DateKind String`, and frozen key snapshots in validator and seal.
- Count-model sums independently reproduced as payload/control/ordinary `1059/3/1062`, JSON `71+2=73`, CSV `23+1=24`.
- One PowerShell 7 prepare→validator→seal chain was granted. Any nonzero step must stop without patch/retry. P654 remains SA2 until a fresh independent root accepts the immutable result.

## P07 route

- Fresh post-fix SA1 was accepted: mathematics `10/10`, stages `70/70`, four-file scope PASS, R2 identity 817 pages/4,958,381 bytes, and 23/23 independently rendered pages PASS.
- A separate fresh isolated SA3 is authorized and running. No TeX, source write, commit or P08 is authorized before its result and B root seal.

## P602 package rejection

- Content-layer spot mechanics remain internally consistent: glyph ledger 175 rows/175 unique/all PASS; pair ledger 325 rows/325 unique/all PASS; C worktree clean; source SHA unchanged at `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`.
- The first package is rejected only as an immutable evidence package: ordinary files 492, manifest rows 490; `_audit_tools/build_p602_r101_measurements.py` and `_audit_tools/inspect_p602_page.py` are omitted; manifest self-size declares 22,692 but actual is 22,780; four files are later than WRITE_STOPPED; and the marker still says the manual ledgers are unadjudicated.
- The old root is permanently read-only. C may only create a new evidence-only reseal with complete provenance/manifests/counts, strict final marker, ADS/cache/parse checks and an independent root handoff. No source, TeX or SA3 is authorized yet.

## Resource and completion boundary

- `latexmk`, `lualatex`, `luatex`, and `luahbtex`: none at checkpoint.
- R101 gates were not repeated. Main source remains clean.
- This checkpoint changes no central role count and declares no whole-book or release completion.
