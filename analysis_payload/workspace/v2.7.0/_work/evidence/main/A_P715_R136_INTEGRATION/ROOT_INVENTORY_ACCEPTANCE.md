# FIG-P715-01 R99 fresh SA1 失败：主线队列接受

- 时间：`2026-08-24T23:55:58+08:00`
- A handoff：`_work/handoff/A/A-R99-P715-SA1-FAIL-20260824/`
- 接受包：`STRICT_R1C_SA1_FRESH_R99_METADATA_RESEAL_20260824`
- 官方候选：R99，814页，4,940,207 bytes，SHA-256 `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`
- 主线结论：`FAIL_TO_SA2_MAIN_QUEUE_ACCEPTED`

## 角色与隔离

- 有效 SA1 路由为 `gpt-5.6-terra/max`，只读 R99/当前源/protocol/schema；首个误读 state/inventory 的实例继续作废。
- R1B 的底层证据保留，但因模型路由元数据错误及终止时间并列而隔离；R1C 仅作 metadata/terminal reseal，没有重渲染、重测或放宽结论。
- SA2 未启动，SA3 不获授权；本结果不计 `A_LOCAL_PASS`。

## 主线独立机械复核

- manifest 声明833行，实际833行且路径唯一；路径逃逸0、missing0、bytes mismatch0、SHA mismatch0。
- 实际普通文件835，恰为833个manifest成员加manifest自身和`WRITE_STOPPED`；extra0。
- NTFS非默认ADS=0。
- `WRITE_STOPPED`严格最新，领先次新文件1,201.212ms。
- `RESULT.json`、`machine_terminal_check.json`和handoff均为`FAIL_TO_SA2`。

## 失败事实

- 分母 N=298：255 glyphs + 43 paths；无序pair 44,253/44,253；对象review 298/298；critical pair 20/20。
- 44个glyph失败；代表性硬失败为G0012 CJK_FULL `一`，R99原生300dpi H_INK=6px<30px，并伴随同类/角色比例失败。
- 19项非白名单critical关系：16个raw collision、共943原生像素，另有3项clearance-only失败。
- clip=0、mask contamination=0；数学语义、文字一致性、灰度、页面融合通过，但不能抵消上述硬失败。

## 中央路由

- 权威inventory将FIG-P715-01从SA1更新为SA2；中央分布变为44 SA1 / 54 SA2 / 0 SA3 / 1 A_LOCAL_PASS。
- P715进入单一图源写者队列，不得在显式授权前改源。当前优先完成P654封存；P608完整FAIL包一旦主线接受，按既有队列先于P715处理。
- 严格最终仍为0/99。
