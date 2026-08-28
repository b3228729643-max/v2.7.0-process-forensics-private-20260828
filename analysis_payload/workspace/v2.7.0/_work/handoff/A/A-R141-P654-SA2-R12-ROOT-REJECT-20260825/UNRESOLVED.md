# Unresolved

P654 remains SA2. R12 proves exact R10 base identity and corrects R11's unresolved provenance and JSON/CSV terminal denominator defects, but R12 introduces two new declaration-level inconsistencies. Under the strict schema, successful manifest identity and content evidence cannot override an incorrectly named or scoped count.

Only after explicit mainline authorization may a new evidence-only reseal be created. It must:

1. derive `ordinary_file_count` from the actual final ordinary set, including all three controls;
2. give every preseal extension-denominator object one explicit collection scope and compute every extension from that same scope;
3. preserve the already correct resolved provenance and zero-tolerance source→destination path/bytes/SHA/ticks identity;
4. include all new control payload in its own manifests and receive another fresh independent root audit.

No TeX, source edit, commit, official candidate, fresh SA1/SA3 or local-pass promotion is authorized by this handoff. R10/R11/R12 remain permanently read-only; the current one-line P654 source patch remains uncommitted.
