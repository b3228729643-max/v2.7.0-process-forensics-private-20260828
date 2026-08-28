# FIG-P580-01 R108 fresh SA1 parent root audit

- HANDOFF_ID: `A-R108-P580-SA1-FRESH-ISOLATED-20260826`
- Evidence root: `STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826`
- Root treatment: permanently read-only; no in-place repair.
- Parent verdict: `ROOT_REJECT_CONTROL_TIME_TIE_CONTENT_PASS_DIRECTION_PRESERVED`

## Accepted content direction

The fresh instance reports `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3` with the current R108/source identities, physical page 630 / printed page 617 / figure 31.6, frozen `N=32`, complete `C=496`, 14 relation sheets, 32/32 manual objects PASS, 496/496 pairs covered, 39/39 broad-bbox candidates CLEAR, illegal overlap 0, clip 0, minimum distinct-semantic text clearance 16 px, and U+0338/U+226A, semantics, grayscale, and page integration PASS. No TeX, source edit, Git write, second UID, or SA3 occurred.

## Independent mechanical audit

- Payload 45; controls 3; ordinary files 48.
- CSV manifest rows 45; SHA manifest rows 45.
- CSV↔SHA↔filesystem missing, extra, path, byte, and SHA mismatches: 0.
- Read-only files: 48/48.
- ADS/cache/pyc/reparse: 0/0/0/0.
- Manual ledgers: objects 32, relation sheets 14, overlap candidates 39.
- Worktree remains clean.

## Decisive control defect

`WRITE_STOPPED` has NTFS `LastWriteTimeUtc.Ticks=639233406896978700`. `PAYLOAD_MANIFEST.sha256` has exactly the same ticks. Therefore `WRITE_STOPPED` is not strictly later than every other ordinary file, contrary to the explicit authorization requiring `WRITE_STOPPED absolute last`.

The sealed root must not be modified, retimestamped, or re-sealed in place. The content PASS direction may be preserved, but the current root cannot independently authorize fresh SA3. Main should adjudicate or grant one new evidence-only control reseal root that preserves the 45 payload files path/bytes/SHA/mtime and writes all controls before a strictly later final `WRITE_STOPPED`.
