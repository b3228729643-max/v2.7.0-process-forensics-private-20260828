# FIG-P547-01 root rejection of first SA2 repair layout

- Root opened the first repaired `standalone_300dpi_native.png` at native resolution before the agent could replace it.
- The central transpose bridge box visibly covered the left and right matrix regions; its second prose line extended beyond the box into both panels, and matrix text/brackets were obscured or clipped by the bridge.
- Eliminating short `=`/`→` glyphs by expanding every relation into prose created new cross-panel overlaps and is not an acceptable repair. Whole-figure shrinking or widening the page is also disallowed.
- Preserved rejected raster: `superseded_first_repair_standalone_300dpi_native.png`, 152,389 bytes, SHA-256 `6F1EEA375F2F2467584C91CA65947FD557751AB24B7B69ED303D843F93D99103`.
- Root also opened and rejected the shortened second repair: the bridge still covered both matrix regions and both bridge arrows ran through matrix/text foreground. Preserved raster: `superseded_second_repair_standalone_300dpi_native.png`, 143,677 bytes, SHA-256 `6D61C325AD1BD4A8841760647FB433FCBCD00EA2CBA5C13E99E2C70C68845B77`.

Verdict: `INTERIM_HARD_FAIL__SUPERSEDED__DO_NOT_SEAL_OR_REUSE`.
