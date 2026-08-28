# FIG-P745-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P745-01`
- legacy/source object：`FIG-V5-C08-05`
- label：`fig:V5-C08-validation`
- 当前正式图保持单一 `figure`、单一 `tikzpicture`；协议A与协议B必须并排比较其估计对象、合法数据流和禁止反馈，拆图会削弱对照，故无需拆图。
- 专属 SA2 只改本图源、V5-C08 首次引用邻域及 R2 报告；根线程同步两个 wrapper、V5-C08 source JSON、中央 CSV 的 C076/C106 与本 R3 证据。本图无 numeric manifest 记录。

## 协议语义与关系检查

- 协议A从开发数据 `D` 经 `C_in` 折候选拟合、仅凭开发证据选择并冻结候选、完整 `D` 重训，到锁定测试 `T` 只开封一次；与算法37.1的作用域一致。
- 协议B明确命名为嵌套交叉验证：对每个外层折 `c`，均在 `D_{-c}` 内重新执行 `C_in` 折拟合和候选选择，冻结该折候选后在完整 `D_{-c}` 重训，仅用 `D_c` 产生外层损失并汇总 `C_out` 个损失；图和正文均明确它不是算法37.1的隐藏外循环。
- 两条禁止返回路径分别从最终评价有向返回各自选择节点；路径在选择节点前物理断开并以白底 X 标记。合法前向流、虚线/双线数据框、有向虚线回箭头、X 与文字说明形成不依赖颜色的冗余编码。
- 图、caption、源级 alt、对象级 JSON、首次引用和图后读图检查均明确：任何使用锁定测试或外层评价结果回调候选、超参数或停止规则的行为都属于信息泄漏。
- 全图协议变量统一为 `c/C_out`；旧 `D_{-k}/D_k/K` 协议记号已从图、对象级 alt 与中央读图记录清除。正文中的秩 `K` 是一般模型复杂度符号，不承担外层折计数语义。
- 章节与 page wrapper 均满足“首次引用及协议边界 -> input -> FloatBarrier -> P745 专属读图检查 -> 后续命题”。

## 构建与机器门

- 使用项目已有、不会自动安装宏包的 TeX Live 2026 LuaLaTeX 工具链定向构建。
- `p745_root_r3_page.pdf`：89,465 bytes，A4 单页；AUX 为图 37.5、页 742。
- `p745_root_r3_standalone.pdf`：58,510 bytes，A4 单页。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0。
- page 的 6 个字体与 standalone 的 5 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata 均为 v2.7.0。
- 图源普通可见字号为 9.6pt、泳道标题为 10.2pt、关键 `D/T/D_{-c}/D_c/c/C_in/C_out/X` 为 12pt；未使用整体缩放、`resizebox`、`scalebox`、`transform shape` 或 `scale=`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均无裁切、遮挡、文字碰线、箭头丢失、标签溢出或节点越界。
- 两泳道标题、数据框、十条合法前向边、两条分段禁止回路与两个 X 均有足够净空；箭头方向可从最终评价明确读回选择节点，X 位于物理断口。
- caption 与图后读图检查同页且换行自然；协议A/B的变量与节点层级清楚，关键符号明显高于普通文字层。
- 灰度下仍可凭实线/虚线、虚线框/双线框、箭头、X 和文字图例辨认合法与禁止关系；颜色不是唯一语义通道。

## 根级结论

当前 P745 源码、正文、wrapper、source JSON、中央 C076/C106 记录、双 PDF、机器证据与三视图均通过根级局部门。中央 CSV 总体验收更新为 `待独立复核`；须等待独立 SA1 与隔离盲审 SA3 双 PASS 后，根线程才能写最终接受报告并关闭本图。tagged PDF/ActualText 不属于本轮权威硬门；对象级语义替代说明以图源和 source JSON 为证。

