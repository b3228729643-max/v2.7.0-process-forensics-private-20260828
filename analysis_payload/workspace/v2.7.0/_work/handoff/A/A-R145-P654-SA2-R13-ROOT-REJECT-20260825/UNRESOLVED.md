# Unresolved

P654 remains SA2. R13's total file counts and actual filesystem sets are correct, but its per-extension declarations omit the final preseal report and WSTOP JSON files. Under the strict schema, correct totals and manifests cannot override false extension snapshots.

Only after explicit mainline authorization may a new evidence-only reseal be created. It must:

1. include the preseal report itself in the expected final payload JSON snapshot;
2. include WSTOP itself in the expected and actual control JSON snapshot;
3. derive ordinary extensions from the complete final payload plus all three controls and independently assert every extension and each snapshot sum;
4. preserve resolved provenance, exact R10 base identity, manifests, parse/ADS/cache and zero-postseal-write gates;
5. receive another fresh independent root audit.

No source edit, TeX, commit, official candidate, fresh SA1/SA3 or local-pass promotion is authorized. R10/R11/R12/R13 remain permanently read-only and the current one-line P654 source patch remains uncommitted.
