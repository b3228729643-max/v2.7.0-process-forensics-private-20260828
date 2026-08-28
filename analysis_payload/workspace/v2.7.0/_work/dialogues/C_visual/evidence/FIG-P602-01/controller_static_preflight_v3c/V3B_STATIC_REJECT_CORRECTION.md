# v3B static rejection and v3C correction

The five files in `controller_static_preflight_v3b` remain byte-identical and OS read-only. v3B is historical `STATIC_REJECT_NO_EXECUTION`, not an authorized controller.

v3C changes only the two rejected control-evidence areas:

| v3B gap | v3C correction |
|---|---|
| Redirected stdout/stderr remained only in memory | Both streams are atomically persisted before RESULT in every build outcome, then recorded by resolved path, bytes and SHA-256 with a second identity recomputation |
| Success used only exit/PDF checks | A single explicit hard gate additionally requires count 1, started/natural exit, exactly one positive-byte expected PDF, post-process count 0, every exception field empty, START present, and both output identities recomputable |

Preserved without relaxation: same-child-environment kpse gate, `openout_any=p`, wrapper cwd and relative inputs, fresh roots, atomic claim/START/RESULT, unique build helper call, no retry, no source or wrapper change, and no execution without a later main grant.

