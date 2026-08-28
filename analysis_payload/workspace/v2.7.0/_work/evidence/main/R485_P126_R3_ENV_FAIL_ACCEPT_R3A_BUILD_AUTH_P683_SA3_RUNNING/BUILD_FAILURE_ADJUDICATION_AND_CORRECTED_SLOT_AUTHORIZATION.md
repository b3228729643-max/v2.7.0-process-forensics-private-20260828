# R485 — P126 R3 environment failure adjudication and corrected R3A slot

Timestamp: `2026-08-28T08:41:38+08:00`

## Accepted R3 failure facts

- HANDOFF `A-R115-P126-SA2-DIRECT-BUILD-R3-20260828` consumed exactly one controller and one direct LuaLaTeX child; retry/latexmk/version-probe/second invocation were all 0.
- Controller PID 24456 and child PID 1700 returned naturally, not interrupted; child/controller exit `1/1`; PDF count 0. Terminal `latexmk/lualatex/luatex/luahbtex=0/0/0/0`, so the slot is released.
- Frozen source, wrapper, engine, and controller identities were unchanged. The source remains `4224 bytes / 366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`; Git remains exactly one unstaged target file with 26+/26-, empty index, and diff-check PASS.
- First and only error occurred before document-body processing in luaotfload: `system : no writeable cache path, quiting`; no PDF was produced. R3 is therefore `BUILD_FAIL_NO_CANDIDATE`, not a source, mathematical, visual, or local-pass failure.
- Failure root, report, and handoff identities match the returned values; Main made no write to them.

## Independent root-cause adjudication

- R3 controller created writable `texcache/var`, `texcache/cache`, `texcache/config`, and `texcache/home` directories and assigned `TEXMFVAR`, `TEXMFCACHE`, `TEXMFCONFIG`, and `TEXMFHOME` to four different empty directories.
- ACL and attributes independently show each directory writable by the current host user, so this is not a workspace or NTFS permission denial.
- The same frozen TeX Live 2026 engine has a proven successful direct-build controller pattern in this worktree: create one writable `texcache` directory and assign all four variables to that same directory. R3 deviated from that known-good cache topology.
- The corrected sibling therefore changes only controller cache topology; it does not modify source, wrapper, engine, TeX arguments, business evidence, or the failed root.

## Exactly one corrected R3A build slot

- Authorized HANDOFF: `A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828`.
- Fixed new root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828`; immediate gate `Leaf=false / Container=false / Any=false / Parent=true`.
- Main preauthorization TeX-family snapshot is `0/0/0/0`.
- Frozen source and wrapper remain `4224 / 366C9058...AC20` and `395 / 706312FA...8124`.
- The controller must create exactly one writable `<R3A-root>/texcache` directory and set `TEXMFVAR=TEXMFCACHE=TEXMFCONFIG=TEXMFHOME` to that identical resolved path. It must not create or use separate `var/cache/config/home` environment roots and must not read, modify, reuse, delete, or seal R3.
- Exactly one new root-external controller invocation and one direct LuaLaTeX child are authorized; retry/latexmk/version-probe/second invocation remain 0. First error stops. Failure returns no candidate and no third slot is implied.
- On natural success, only one non-TeX full regression and one compliant seal from the sole new PDF are allowed. Commit, fresh role, second UID, further source edit, Main/central write, and any other TeX/build remain forbidden.

P126 remains SA2. P683 remains the same running fresh SA3. Inventory remains `31 SA1 / 31 SA2 / 1 SA3 / 37 local pass`; strict-final remains `0/99`.
