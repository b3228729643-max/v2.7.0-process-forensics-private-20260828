# FIG-P721-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_AND_INDEPENDENT**  
**SPLIT_REQUIRED: NO**

## 根级整合

- 保持 UID `FIG-P721-01`、对象 `FIG-V5-C07-08`、label
  `fig:V5-C07-rank-trajectory`、单一 `figure` 与单一 `tikzpicture`。
- 专用 page/standalone wrapper 已同步为 v2.7.0；page wrapper 固定页码 718、
  图号 36.7，并采用“专属首次引用 -> input -> FloatBarrier -> 读图检查”。
- 图中左栏为 `t=0,...,8` 的 27 个六位小数轨迹点；`t=6` 明示为展示
  截断，并给出非零残差。右栏单独给出精确固定点的六位显示值和
  `3>2>1` 排名。

## 独立数值核对

- 用正文列随机矩阵逐次作有理数乘法，t=0 到 8 的显示坐标与图源逐项一致；
  六位小数最大舍入误差为 `14587/32805000000`
  `=4.4465782655083068e-7`（t=7、网页1）。
- `r^(6)=(6939409,9723979,17508487)/34171875`，且
  `||G r^(6)-r^(6)||_1=229376/512578125`
  `=4.4749471117208e-4>0`，所以该竖线不是停止证书。
- 精确固定点为 `(25/123,35/123,21/41)^T`；有理数回代残差严格为 0，
  排名严格为 `3>2>1`。

## 构建与机器门

- `p721_root_r3_standalone.pdf`：exit 0，1 页，45,626 bytes。
- `p721_root_r3_page.pdf`：exit 0，1 页，66,709 bytes。
- page AUX：`fig:V5-C07-rank-trajectory = 36.7`，页码 718。
- 两份日志的 Overfull、Underfull、undefined、LaTeX/Package Error、Fatal、
  Emergency stop 均为 0。
- standalone/page 的全部列出字体均为 `emb=yes, sub=yes, uni=yes`。

## 根级视觉门

已逐张查看 300 dpi 彩色 page、灰度 page 与 standalone：

- 图、题注、首次引用与读图检查同在单页，无裁切、碰撞或跨页；
- 左栏曲线/点型/标签和橙色展示截断说明净空清楚；残差指数完整可读；
- 右栏三个条形、六位数值和名次完整，颜色之外仍有纹理/结构编码；
- 灰度下三条轨迹仍由实线圆点、虚线方点、点划线三角点区分，三个条形
  仍由斜线、点纹与实灰区分；
- standalone 与 page 中的图内内容一致。

## 清单同步

- V5-C07 `figure_sources.json` 保持 8 条、8 个唯一对象；P721 的 caption、
  teaching objective 与 alt 已同步当前有限轨迹／非停止截断／精确固定点语义。
- `figure_numeric_manifest_v16.json` 保持 36 条、36 个唯一对象；P721 记录冻结
  G、t=0..8 六位轨迹、t=6 精确残差、精确固定点与无 9 倍缩放边界。
- 中央 `figure_manifest.csv` 暂不改为“通过”；须等待最终 SA1 与 SA3 双通过。

最终独立 SA1 与隔离盲审 SA3 均判
`PASS / SPLIT_REQUIRED=NO / BLOCKERS=NONE`；SA3 另对精确清单修正追加
`POST-MANIFEST-CORRECTION CONFIRMATION: PASS`。根线程据此进入正式接受。
