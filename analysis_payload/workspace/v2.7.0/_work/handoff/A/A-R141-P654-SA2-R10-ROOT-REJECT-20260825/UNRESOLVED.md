# Unresolved

P654 remains SA2 because the R10 payload manifests do not preserve the sealed files' NTFS 100 ns mtimes exactly. The difference is a serialization defect, not a figure-content failure, but the explicit bytes+mtime+SHA identity gate cannot be replaced by bytes/SHA alone.

The next permitted action is a new, evidence-only reseal root that losslessly records and read-backs file mtimes, followed by a fresh independent root audit. The existing R10 root is permanently read-only and must not be patched in place. No TeX, source change or fresh SA1/SA3 is needed or permitted for this correction unless mainline separately expands scope.

The current one-line P654 source patch remains uncommitted and must not be integrated from this rejected handoff.
