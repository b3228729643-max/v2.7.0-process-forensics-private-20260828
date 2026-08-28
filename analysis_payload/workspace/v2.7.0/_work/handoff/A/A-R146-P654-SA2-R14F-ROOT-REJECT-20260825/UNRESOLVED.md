# Unresolved

P654 remains central SA2. The sealed R14F root and fresh-root report are immutable.

The only unresolved issue is scope interpretation:

- final 1059-row manifests contain five fields: one relative path plus bytes/SHA/ticks/7-digit display;
- the latest mainline execution grant explicitly requests final-manifest/filesystem path+bytes+SHA+ticks, all of which pass;
- six-field equality is present and passes in the 1052-row source/destination base-copy identity tables;
- the unique fresh root was dispatched with a stricter six-field final-manifest instruction and therefore rejected R14F.

Mainline must adjudicate this mismatch. Do not patch or rerun R14F, start a second root, create R14G, modify the source, run TeX, commit, or dispatch fresh SA1/SA3 without a new explicit authorization.

