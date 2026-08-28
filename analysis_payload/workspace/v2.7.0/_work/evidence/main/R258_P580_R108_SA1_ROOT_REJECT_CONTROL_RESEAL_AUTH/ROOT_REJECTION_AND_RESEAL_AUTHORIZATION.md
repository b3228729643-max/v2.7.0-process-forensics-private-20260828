# R258 — P580 R108 fresh SA1 root rejection and one control reseal authorization

- Actual role: `A-R108-P580-SA1-FRESH-ISOLATED-20260826` / `/root/p580_r108_fresh_sa1` / `gpt-5.6-sol/xhigh/fork_turns=none`.
- Content direction is preserved as PASS: physical 630 / Fig. 31.6, `N=32`, `C=496`, 14 relation sheets, 32 objects, 39 broad candidates, illegal overlap 0, clip 0, minimum distinct-semantic clearance 16 px, Unicode/semantics/grayscale/page integration PASS.
- R2 mechanical identity otherwise closes: payload45/controls3/ordinary48, dual manifests45, filesystem path/bytes/SHA mismatches0, readonly48/48, ADS/cache/pyc/reparse0.
- Decisive rejection: `WRITE_STOPPED` and `PAYLOAD_MANIFEST.sha256` both have NTFS ticks `639233406896978700`; WSTOP is not strictly later. R2 is permanently read-only and cannot authorize SA3.
- Main independently confirmed report SHA `44082B1A177C0DB1C426BA4DC043638B91ECEBC24DF4764319A346CB6C4CB34C` and handoff SHA `1438BE4C68FA35EAA703A94AEFFB9A5B8088DEE6CB20A9C5CF84D241EC03C92F`.

Exactly one new evidence-only control reseal is authorized. It must copy the R2 manifest intersection's exact 45 payload with relative paths/bytes/SHA/NTFS ticks unchanged; add resolved `COPY_IDENTITY.csv` and `COPY_PROVENANCE.md` as two new payload files; create dual manifests over all 47 payload; and finally write WSTOP only after current FILETIME is strictly greater than the maximum prior tick. Final model is 47 payload + 2 manifests + WSTOP = 50 ordinary files. No post-WSTOP root files or writes are allowed. External read-only audit must prove 50/50 readonly, copy identity0 mismatch, manifest/FS0 mismatch, WSTOP strictly latest, postmarker0, and ADS/cache/pyc/reparse0.

No SA1 content rerun, visual rerun, denominator/pair/manual rewrite, TeX, source edit, Git write, second UID, or SA3 is authorized. Any failure stops the chain; no automatic second reseal.

- P580 remains `SA1`; inventory remains `33 SA1 / 49 SA2 / 0 SA3 / 17 A_LOCAL_PASS`.
- Strict final completion remains `0/99`.
- Authorized: `2026-08-26T19:35:15+08:00`.
