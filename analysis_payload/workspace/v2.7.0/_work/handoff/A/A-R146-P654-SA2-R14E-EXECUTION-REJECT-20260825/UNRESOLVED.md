# Unresolved

P654 remains SA2. R14E does not reach preseal report generation or seal.

A new round, only if explicitly authorized, must use a fresh static directory and future root, retain all accepted R14E fixes, and rename only the validator assertion-helper locals so they cannot collide case-insensitively with typed dictionary parameters:

- `Assert-Snapshot`: use distinct value locals instead of `$g/$e`;
- `Assert-Equations`: use distinct value locals instead of `$p/$c/$o`.

Static validation must execute the exact helper bodies against actual final extension dictionaries and synthetic mismatch branches, not an independently rewritten equivalent.

No source modification, TeX, commit, official candidate, fresh SA1/SA3, or local-pass promotion is authorized.

