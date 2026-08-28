# FIG-P684-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**LOCAL_BLOCKERS: NONE**

## 根级整合

- 保持 UID `FIG-P684-01`、对象 `FIG-V5-C06-02`、label
  `fig:V5-C06-generative-process`、单一 figure 与单一 TikZ。
- 保留三泳道四步骤，不复制图 35.2 的完整 plate 图；显式呈现固定超参数、
  随机概率向量、潜在离散变量、观测变量以及每个 m 内的 n 嵌套。
- 五条祖先边为 beta->varphi、alpha->theta、theta->z、z->w、varphi->w；
  后一条保留“按 z_mn 取一行”。点参数侧注明确每个 varphi_k 为待估参数、
  无 beta 先验且不是同一完整 Bayes 后验。
- page/standalone wrapper 已同步 v2.7.0；page wrapper 固定页 681、图 35.3，
  并保持“首次引用 -> input -> FloatBarrier -> 专属读图检查”。
- V5-C06 source JSON 保持 8 条、8 个唯一对象，P684 更正为
  `process_or_algorithm_flow` 并同步当前 caption、teaching objective 与 alt。

## 构建与机器门

- `p684_root_r3_standalone.pdf`：exit 0，1 页 A4，52,914 bytes。
- `p684_root_r3_page.pdf`：exit 0，1 页 A4，68,197 bytes。
- page AUX：图号 35.3、物理页 681。
- 两份日志对 Overfull、Underfull、undefined、LaTeX/Package Error、Fatal、
  Emergency stop、Missing character 的硬扫描均为 0。
- standalone/page 的全部列出字体均为 `emb=yes, sub=yes, uni=yes`。
- 图源只有 9.6/10.2pt 显式字号；未命中 overall scale、resizebox、
  scalebox、transform shape 或低于 9.6pt 字号。

## 根级视觉门

已逐张查看 300 dpi 彩色 page、灰度 page 与 standalone：

- 图、题注、首次引用和读图检查同在页 681，无节点、边、公式、题注或页边界
  碰撞/裁切；三视图内容一致。
- beta/alpha 到 varphi/theta 的先验边、theta 到 z、z 到 w、varphi 到 w
  的五条方向清楚；选行标签与曲线净空充足。
- 灰度下固定超参数/点参数侧注的虚线框、随机向量实线框、潜变量点划椭圆、
  观测变量双线框及角色文字仍可区分，颜色不是唯一编码。
- k=1..K、m=1..M 与“每个 m 内 n=1..N_m”可读；随机 varphi/theta 的
  单纯形维数、z/w 的取值集合完整。

本报告只作根级局部通过；最终独立 SA1 与隔离盲审 SA3 均通过前，不关闭
FIG-P684-01，也不把中央 CSV 更新为“通过”。
