# Seal contract

- `SEALED_MANIFEST.csv` enumerates every payload file recursively except itself and `WRITE_STOPPED`.
- Each manifest row contains relative path, fully resolved absolute path, byte count, SHA-256, UTC mtime, Windows FILETIME in 100 ns units, and read-only state.
- `SEALED_MANIFEST.csv` is intentionally excluded because a file cannot contain its own stable hash/size/mtime.
- `WRITE_STOPPED` is intentionally excluded because it is created strictly after the manifest and after all payload/manifest files have been made read-only.
- No payload file may be changed after the manifest is created. No file at all may be written after `WRITE_STOPPED` is created.
- The pre-manifest payload was checked recursively for alternate data streams (excluding the ordinary unnamed `$DATA` stream), `__pycache__`, `.cache`, and `.pyc`; all counts were zero.
