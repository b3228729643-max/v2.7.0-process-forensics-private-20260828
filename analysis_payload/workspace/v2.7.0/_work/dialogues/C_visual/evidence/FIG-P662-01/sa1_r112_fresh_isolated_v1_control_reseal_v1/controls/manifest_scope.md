# Manifest scope and post-marker set rule

`controls/manifest.csv` will close over every regular payload/control file present immediately before it is created, excluding only:

1. `controls/manifest.csv` itself, because a file cannot contain its own stable cryptographic hash;
2. the final root-level `WRITE_STOPPED` marker, because it must be precreated outside the root and moved into the root as the unique last root-content operation.

After the marker move, the expected regular-file set is exactly `manifest rows + controls/manifest.csv + WRITE_STOPPED`. Post-marker verification must find zero additions, removals, or identity differences under that explicit set rule. No post-marker report may be written into the root.
