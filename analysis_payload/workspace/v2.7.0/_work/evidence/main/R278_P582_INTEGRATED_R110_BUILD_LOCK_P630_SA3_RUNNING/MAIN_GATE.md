# Revision 278 — P582 集成与 R110 唯一全书构建锁

时间：2026-08-27T00:48:20+08:00  
主线：`v2.7.0/integration`

## P582 local SA2 acceptance and integration

- 接受 `A-R109-P582-SA2-DIRECT-BUILD-R6-20260827` 的 LOCAL_SA2_PASS；旧 P05555 在新 standalone PDF 中对应 `PAIR-03495`，native300dpi shared=0、white clearance=27px；上方 plot 最近净距大于90px。
- 主线独立复算 sealed root：payload237/controls3/ordinary240；CSV/JSON/FS path/bytes/SHA/NTFS ticks差0，extra/missing0，240/240文件只读；WSTOP严格最后margin4,254,837 ticks。
- 主线实际打开目标关系 native1x/8x 与上方 plot 回归 native1x/8x，无重叠、裁切或可读性反证。
- A atomic commit=`4a8c489488fd12e5584e2042535fefcd548b62b7`；exact one file / 1+/1-，仅 `(axis cs:3.58,.49)`→`(axis cs:3.58,.53)`。
- 主线从 clean HEAD `59e7afd81ba3171ab9de5c90ed589fed3424155e` cherry-pick 成功；new HEAD=`aa7eb7c4fcf0f702e3e485330c9e02a8304501d6`，worktree clean，main source SHA-256=`989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`。

## R110 unique full-book build lock

- 新官方候选必须来自集成后的 clean HEAD；R109继续只读保留但不再用于P582 fresh角色。
- 唯一父调用计划：`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r110_fullbook -NoPublish`。
- 启动前：R110 output root不存在，latexmk/lualatex/luatex/luahbtex全NONE，main worktree clean。
- 禁止第二父调用、retry、Resume或A/B/C并发TeX；失败或平台中断须先如实冻结再裁决。
- P630 R109 fresh isolated SA3 可继续纯只读并行；不得触碰R110构建链。

## Central accounting

构建前 inventory=`31 SA1 / 47 SA2 / 1 SA3 / 20 local pass`；严格最终`0/99`，B累计`66/66`。
