# Unresolved

P654 remains SA2. R11 fixes R10's lossy mtime serialization and proves exact 100 ns source→destination identity, but its own provenance and terminal parse-count declarations are not self-consistent. Under the strict root gate, those two new-control defects prevent acceptance.

The next permitted action, only after explicit mainline authorization, is a new evidence-only reseal root that:

1. copies the sealed R11/R10-backed payload without modifying either old root;
2. records the resolved source and destination roots in provenance;
3. uses unambiguous, independently validated total/control/payload parse denominators;
4. keeps exact decimal-string NTFS ticks and zero-tolerance path/bytes/SHA/ticks validation;
5. receives another fresh independent root audit.

No TeX, source edit, commit, fresh SA1/SA3 or local-pass promotion is authorized by this handoff. The current one-line P654 source patch remains uncommitted.
