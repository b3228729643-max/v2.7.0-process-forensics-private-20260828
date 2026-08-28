# FIG-P717-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P717-01`
- source object：`FIG-V5-C07-04`
- label：`fig:V5-C07-inbound-contribution`
- 当前正式图仍为单一 `figure`、单一 `tikzpicture`，无需拆图。
- 专属 SA2 只改本图源与 V5-C07 首次引用邻域；根线程只同步两个 wrapper、
  V5-C07 source JSON、中央 CSV 与本 R3 证据。

## 数学与语义检查

- 上部作用域严格限定为“基本 PageRank、无悬挂；此处 `S=M`”。三条来源边
  同为 `.96pt`，各自只表示 `M_{ij_l}r_{j_l}^{(t)}`，没有用线宽、颜色或
  路径长度伪造未给出的贡献大小。
- 公式卡给出
  `r_i^(t+1)=sum_j M_ij r_j^(t)=sum_{j:j->i}M_ij r_j^(t)`，并明确
  `M_ij=A_ij/c_j`；非加权时分母 `deg^+(j)` 属于来源 `j`，不是目标 `i`。
- 下部边界卡给出悬挂修复 `S=M+v a^T` 与
  `G=dS+(1-d)v1^T`。当 `c_j=0` 时，即使无 `j->i` 也可有
  `S_ij=v_i>0`，所以“正元素对应入链”没有被错误外推到修复后的 `S/G`。
- 章节与 page wrapper 均为“首次引用 -> input -> FloatBarrier -> 专属读图检查”；
  已关闭的 P721 邻域未改。

## 构建与机器门

- `p717_root_r3_standalone.pdf`：60,014 bytes，A4 单页。
- `p717_root_r3_page.pdf`：75,621 bytes，A4 单页；AUX 为图 36.4、页 715。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、
  fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0；
  两日志均明确输出 1 页。
- standalone 的 8 个字体与 page 的 9 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source。
- 图源普通可见字号为 9.6pt，标题为 10.2pt；未使用整体缩放、
  `resizebox`、`scalebox` 或 `transform shape`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均为单页、
  无裁切、遮挡、文字碰线或不可读公式。
- 首次彩色实看发现标题与公式卡相碰，且公式卡底边与 boundary 卡相接；
  专属 SA2 的 R2.1/R2.2 只把标题移至 `y=3.10`、boundary 卡移至
  `y=-4.20`。最终三视图中两处均有清晰白色净空。
- 灰度下来源圆、深色目标、实线贡献、实线公式卡和虚线边界卡仍可区分；
  颜色不是唯一语义通道。

## 根级结论

当前 P717 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过
根级局部门。中央 CSV 总体验收仅更新为 `待独立复核`；须等待全新独立 SA1 与
隔离盲审 SA3 双 PASS 后，根线程才能写最终接受报告并关闭该图。
