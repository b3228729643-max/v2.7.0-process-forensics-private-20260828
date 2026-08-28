# R305 P049 R1根拒收与唯一控制重封授权

- 时间：`2026-08-27T05:28:16+08:00`
- 原HANDOFF_ID：`A-R110-P049-SA2-R168-READONLY-20260827`
- 业务方向仅保留：`R168_HARD_DEFECT_COUNT_0 / NO_SOURCE_CHANGE_DIRECTION`；fresh SA1尚未授权。

## 根拒收

- old root ordinary9=7 local payload+PREMARKER manifest+WSTOP。
- 主线复算7/7 local path/SHA差0；外部source/PDF identity亦命中，但manifest无bytes字段。
- files readonly0/9、root readonly=false；payload、controls与WSTOP均可写。
- WSTOP严格最后、at-or-after0；ADS/cache/pyc/reparse0。
- 因只读冻结与path/bytes/SHA/ticks闭合缺失，原根不得进入fresh SA1；保持零写、禁止原地修改或重封。

## 唯一授权

- 恰一次全新sibling evidence-only control reseal；仅复制7个manifest-bound payload，保留relative path/bytes/SHA/NTFS ticks，旧controls复制0。
- 新增resolved COPY_IDENTITY/COPY_PROVENANCE，生成path/bytes/SHA/ticks manifest与seal audit。
- 所有payload/control文件及所有目录只读，唯一WSTOP严格最后，postmarker0；root-external PowerShell7 auditor只读复算。
- 禁止PDF/视觉/数学/对象/pair/manual重跑，禁止TeX/source/Git/角色/第二UID/central writes；controller invocation1/retry0。
- inventory保持`31 SA1 / 44 SA2 / 0 SA3 / 24 local pass`。
