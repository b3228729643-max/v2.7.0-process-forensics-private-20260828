# R467 P109 preseal control hold

Timestamp: `2026-08-28T05:58:11+08:00`

P109's same fresh R115 SA1 instance reports complete post-observation manual coverage and a provisional hard PASS direction, but no seal has been accepted.

Main's read-only preseal observation of the fixed R4 root found:

- files: 39; directories including root: 1;
- `WRITE_STOPPED`: absent;
- one and only one ReadOnly file: `WSTOP` inside the evidence root;
- `WSTOP`: 985 bytes, CreationTimeUtc and LastWriteTimeUtc both `2099-12-31T23:59:59Z`;
- the other 38 files are writable;
- the root directory is writable.

This is inconsistent with the stated remaining control sequence, which described a root-external prebuilt ReadOnly future-FILETIME WSTOP entering the root as the sole final move after all premarker files/directories/root were made ReadOnly. Main therefore issued an urgent HOLD before any further root content or attribute operation.

A must not seal, rename, move, delete, move out, rewrite, retimestamp, repair, retry, start a sibling/replacement, or create another role. It may only return a factual disclosure of the in-root WSTOP creation mechanism and time, intended role, invocation counts, manifest binding, and post-HOLD zero-write status. P109 remains SA1 and no PASS is counted.

Inventory remains `32 SA1 / 32 SA2 / 0 SA3 / 36 local pass`; strict final remains `0/99`.
