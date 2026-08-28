# FIG-P695-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与结构

- canonical UID：`FIG-P695-01`
- source object：`FIG-V5-C06-08`
- label：`fig:V5-C06-method-comparison`
- 当前正式图为单一 `figure`、单一 `tikzpicture`、固定五行三列表；比较项必须
  横向对照，拆图会破坏同一行的模型—推断差异，故无需拆图。

## 模型与推断契约

- 左列是完整 Bayes LDA：`theta_m~Dir(alpha)`、`varphi_k~Dir(beta)`，折叠
  两类概率向量后抽样 `p(z|w,alpha,beta)`；链状态为 `z_i` 与三类一致计数，
  更新为留一满条件和“减—算—抽—加”。
- 右列是无 `beta` 先验的点参数 LDA：`varphi_k` 为待估参数；只有局部 E 步
  固定当前 `varphi` 并更新 `(gamma_m,eta_m)`，全局再用成功文档的期望计数
  更新 `varphi`、以受保护 Newton 更新 `alpha`。
- Gibbs 的输出/适用性是相关后验样本、不确定性与多峰信息；点参数 VEM 的输出
  是 `(varphi,alpha,{q_m})` 点参数/近似，适合大语料、批量化或预算敏感情形。
- ELBO 只在同一点参数模型的可行块更新下逐块非降；图内明确 ELBO 不等于真实
  证据，未声称无偏或全局最优。
- 公平比较条冻结同一训练/验证/测试切分、词表与预处理、主题数、计算预算和评价
  口径，并要求同时登记模型差异与推断差异。

## 构建与机器门

- `p695_root_r3_standalone.pdf`：90,482 bytes，A4 单页。
- `p695_root_r3_page.pdf`：102,925 bytes，A4 单页；AUX 为图 35.8、页 692。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、
  fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0；
  两日志均明确输出 1 页。
- 两份 PDF 各 7 个字体，全部 `emb/sub/uni=yes`；FLS 均回指各自 v2.7.0
  wrapper 与当前 canonical source。
- 图源普通可见字号 9.6pt、表头 10.2pt；未使用整体缩放、`resizebox`、
  `scalebox` 或 `transform shape`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；五行三列、长公式、
  风险条与公平比较条均完整可读，无碰撞、裁切、框线穿字或页面越界。
- 灰度下 Gibbs 的实线浅底列与 VEM 的虚线白底列可独立区分；表头、行标签和列
  标题形成冗余编码，不依赖颜色。
- page 中首次引用、图、题注与图后读图检查同页且顺序正确。

## 根级结论

当前 P695 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过
根级局部门。中央 CSV 总体验收仅更新为 `待独立复核`；须等待最终独立 SA1 与
隔离盲审 SA3 双 PASS 后才能关闭。
