# Unresolved

P654 remains SA2. R14C did not reach preseal validation or seal. The failure is a validator representation/access bug, not duplicate identity data.

A new round, if explicitly authorized by mainline, must:

1. use a fresh nonsealed static directory and a fresh future execution root;
2. leave the failed R14C future root permanently untouched;
3. preserve the accepted R14C token/round/compact-operator/count/self-accounting logic;
4. change only the normalized-row/grouping access required to make uniqueness checks operate on actual key values;
5. statically prove both duplicate detection and unique acceptance on the same normalized representation;
6. rerun the full prepare→validator→seal chain only under a new explicit one-time grant.

No source modification, TeX, commit, official candidate, fresh SA1/SA3, or local-pass promotion is authorized.

