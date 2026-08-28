# P654 R17 independent sealed-root audit

Decision: **ROOT_ACCEPT_R17_FAIL_TO_SA2_SOURCE_R3_REQUIRED**.

The sealed root contains 2051 payload files + 3 controls = 2054 ordinary files. Both manifests match each other and the final filesystem in path, bytes, SHA-256, exact NTFS ticks, and 7-digit UTC display with zero differences. All JSON/CSV/PNG/PDF payloads parse; ADS, Python cache/bytecode, symlinks, and read-only failures are zero. WRITE_STOPPED is strictly latest and the read-only audit caused zero root writes.

The evidence is accepted as a truthful FAIL route: G0040/G0059/G0064/G0065 fail the frozen D/E gate; P06198/P06219 fail 3px native clearance; the frozen source formula role also fails its source-size gate. P654 remains SA2; no commit, fresh SA1/SA3, LOCAL PASS, or A_LOCAL_PASS is authorized.
