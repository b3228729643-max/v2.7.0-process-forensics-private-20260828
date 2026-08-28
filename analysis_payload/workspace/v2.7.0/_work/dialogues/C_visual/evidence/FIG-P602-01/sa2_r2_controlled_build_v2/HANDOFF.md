# P602 controlled-build v2 immutable handoff

Handoff status: `BUILD_FAIL_NO_CANDIDATE`.

- Authorization used: `P602_ASCII_CACHE_DIRECT_RETRY_SLOT_GRANTED`.
- New evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v2`.
- Pre-build ASCII probe and resolution gate: PASS.
- Direct LuaLaTeX invocations: 1 of 1 allowed.
- Invocation PID: 16572.
- Natural exit: yes; exit code: 1.
- Candidate PDF: absent.
- Post-exit TeX processes: 0.
- Build slot: released immediately after natural exit.
- Failure locus: luaotfload initialization at wrapper line 1, before the P602 figure source was read.
- Business source changed during build chain: no.
- Second invocation or automatic retry: no.
- Native evidence rebuilt: no, because no candidate PDF exists.
- Commit / central state / inventory / next figure / fresh role: none.

The root must remain read-only after `WRITE_STOPPED.json`. The manifest intentionally excludes itself and the final write-stop marker; this avoids self-referential manifest mutation. All other ordinary files are listed with path, byte length, SHA-256, and NTFS last-write time in 100 ns ticks.

