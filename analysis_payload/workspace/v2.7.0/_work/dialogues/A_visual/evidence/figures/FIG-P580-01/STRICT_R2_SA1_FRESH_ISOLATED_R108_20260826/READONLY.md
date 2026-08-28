# Sealed evidence root

This root is the frozen evidence payload for `A-R108-P580-SA1-FRESH-ISOLATED-20260826`.

After the dual payload manifests are emitted, every existing file is set read-only and the pre-created read-only `WRITE_STOPPED` marker is moved into this directory as the final root mutation. No subsequent root write is permitted.
