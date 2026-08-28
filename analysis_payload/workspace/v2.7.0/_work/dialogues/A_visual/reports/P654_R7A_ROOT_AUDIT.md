# P654 R7A 独立 Root 审计报告

- 审计对象：`FIG-P654-01`
- sealed root：`A_visual/evidence/figures/FIG-P654-01/STRICT_R7A_SA2_NARROW_R100_EVIDENCE_RESEAL_20260825`
- 审计方式：独立、只读、非 TeX；未 import/执行 sealed root 中任何脚本，未写入 sealed root、业务源、状态、handoff 或 Git。
- 唯一写入：本报告（sealed root 包外）。
- 权威依据：当前 `goal-objective.md`、`STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`、`STRICT_FIGURE_EVIDENCE_SCHEMA.md`、旧 `P654_R7_ROOT_MECHANICAL_AUDIT.md`。

## 1. 裁决

**ROOT_REJECT_R7A_FAIL_TO_SA2_CONTINUE**（决定性原因：`D_E_HARD_GATE_FAIL`）。

R7A 已纠正旧 R7 的批量人工结论问题：935 项 machine reuse、203 项人工账、consumer/finalizer 的当前静态边界、manifest/parse/ADS/seal、目标 `FRM_TRIAL_005` 的几何与 mask 均可复核；实际打开的图像也没有发现目标 `n` 缺笔、foreign pixel、clip、ownership loss 或 design-whitelist 滥用。

但是，按当前包已经冻结的 `PANEL_ID + ROLE + SCRIPT_CLASS` 分组重新计算 native 300 dpi D/E 门，至少 8 个元素越过 `[0.92,1.08]` 硬区间。R7A 的 ratio manual notes 用“自然字形轮廓”解释并写成 `ACCEPT`，不能覆盖协议硬门。整体视觉协调也不能覆盖单元素硬失败。因此本 root 不接受，P654 保持 `SA2`；不得提交源码、不得派 fresh SA1/SA3、不得计 `A_LOCAL_PASS`。

## 2. 身份与 machine reuse

### 2.1 冻结身份

独立读取并重新哈希当前工作树/包内绑定对象：

| 对象 | bytes | SHA-256 | 结论 |
|---|---:|---|---|
| 当前 P654 源 `fig_v5_c05_dependency_graph.tex` | 3,122 | `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D` | 与 R7A 冻结一致 |
| standalone wrapper | 397 | `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1` | 与 R7A 冻结一致 |
| R7 PDF | 43,385 | `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6` | 与 R7A 冻结一致 |

当前 Git 只显示目标单源修改，numstat `1/1`，`git diff --check` 为 0；本审计未改变该状态。

### 2.2 935 项复用逐项复核

`MACHINE_REUSE_IDENTITY_LEDGER.csv` 独立计数为 935 行、935 个唯一 source path、935 个唯一 destination path。逐行检查 source/destination 路径存在性、bytes、SHA-256、mtime 及 source=destination：失败 0；路径映射失败 0；banned artifact 0。

类别分布为：914 machine artifacts、17 ledger/controller、2 pre-manual summaries、1 source snapshot、1 wrapper snapshot。staging allowlist 未迁移旧 R7 的 manual、finalizer、RESULT 或 report；R7A 当前 4 个人工账均是新根对象。

### 2.3 N/C 与目标对象

- 对象：`N=116=95 glyph + 21 graphic`，ID/安全文件名均唯一。
- 对象类型：80 TEXT、15 FORMULA、8 NODE_BORDER、7 LINE_ARROW、5 ARROWHEAD、1 MATH_RULE。
- 全无序 pair：`C(116,2)=6,670`；pair index、pair ID、对象顺序及集合完全一致。
- machine object failures=0；machine pair failures=0；最终非法 intersection=0。
- 设计组成 486 pair；普通清晰关系 6,184 pair。
- 目标 `FRM_TRIAL_005`：native `H=22 px`、area `297 px`、pre-area `297 px`、occluded/missing/foreign/clip/ownership-loss 全为 0。

## 3. 203 项人工账与脚本边界

### 3.1 精确集合

人工账独立计数为 203，且满足唯一精确集合：

- glyph 95
- graphic 21
- critical 50
- view 5
- semantic 3
- D/E 8
- hierarchy 5
- ratio 16

203 个 decision ID 唯一，203 个 subject/pair ID 唯一；subject+evidence/cell locator 唯一。空 note 0、短 note（少于 20 字）0、精确重复 note 0、去 ID/数字归一化重复 0、禁模板命中 0、缺 evidence 0、`OPENED!=TRUE` 0、reviewer 空值 0、裸 `PASS` 0。人工 note 在文字、图形、关系坐标与视觉理由上具有对象特异性，未见旧 R7 的统一 reviewer/default/global boolean 模板。

### 3.2 当前脚本静态审计

sealed root 中只有 2 个 `.py`：

- `tools/consumer_validator.py`：只读 4 个人工账并验证，唯一写入 `CONSUMER_VALIDATION.json`；没有人工账生成/改写路径。
- `tools/package_finalizer.py`：只读 phase/consumer/RESULT/manual identity，写 seal/parse/manifest 元数据；没有人工账生成/改写路径。

`PHASE_IDENTITY_BEFORE_CONSUMER` 冻结 consumer SHA 与 4 个人工账 SHA；当前重新哈希完全一致。consumer 对 203 项做只读消费，37 checks、0 errors。当前脚本没有通过 loop、default decision、global boolean、机器类别或统一 note 生成/改写 manual 的行为。

## 4. D/E 硬门独立重算（决定性失败）

### 4.1 适用规则与分组冻结

协议要求：同面板、同脚本类别、同语义角色，每元素 `H_ink / 角色中位数` 必须位于 `[0.92,1.08]`；不可用 manual note 或整体视觉覆盖硬越界，也不得按精确字形临时拆组规避。

本审计不跨 CJK、Latin/Greek、baseline math、natural TeX script 混比；直接使用包已经写入 `after_pixel_measurements.csv` 的 `PANEL_ID + ROLE + SCRIPT_CLASS` 作为冻结分组，并冻结组内全部成员后重算中位数与比值。

### 4.2 Native D/E 失败组

| 冻结组 | 全部成员 H(px) | median | 硬失败 |
|---|---|---:|---|
| `SINGLE_PANEL/GAMMA/LATIN_GREEK_LOWER` | `a22,m21,m21,a22,e22,t27,a22` | 22 | `TXT_GAMMA_009(t)=27/22=1.227273 > 1.08` |
| `SINGLE_PANEL/POSTERIOR_FORMULA/BASE_MATH_OPERATOR_OR_GLYPH` | `α24,+29,n24` | 24 | `FRM_POSTERIOR_FORMULA_004(+)=29/24=1.208333 > 1.08` |
| `SINGLE_PANEL/PREDICTIVE_FORMULA/BASE_MATH_OPERATOR_OR_GLYPH` | `α24,+29,n24,α24,+29,N33` | 26.5 | 三个 24 px 元素 `0.905660 < 0.92`；两个 `+` 为 `1.094340 > 1.08`；`N` 为 `1.245283 > 1.08`，合计 6 个失败 |

因此共计至少 8 个 native D/E 元素硬失败。`R7A-RATIO-005/009/012` 用“自然上伸部”“自然外形”“大写/运算符轮廓”说明 `ACCEPT`，但这些 note 不能改变该包自己冻结的 script-class/role 分母。若作者认为这些轮廓根本不可比，则当前 `SCRIPT_CLASS` 分类本身不合规，必须在新的 SA2 证据中用协议允许的、非 exact-glyph 规避式 taxonomy 重新建立完整分母，不能由 root 审计临时改组后放行。

`PREDICTIVE_FORMULA/NATURAL_TEX_SCRIPT` 的 `i26,i26,0=24` 对组中位数 26 的逐元素比值为 `1,1,0.923077`，均在区间内；本审计没有把不同自然轮廓的简单 max/min 当作额外硬失败。

### 4.3 Source nominal point size

按真实语义角色读取当前源：普通节点标签 10.1 pt、posterior/predictive formula block 11.6 pt、trial inline formula 10.7 pt、application annotation 10.1 pt。各语义角色内部字号相同；formula/base=`1.148515`、inline/base=`1.059406`、annotation/base=`1.0`，角色层级本身落在协议范围。

注意：`after_pixel_measurements.csv` 的 `ROLE` 实际写成节点位置名（例如 `TRIAL`），而 manual 又把 trial 普通文字与 inline formula 作为两个语义角色。若机械按现有 `ROLE=TRIAL` 合并，10.1/10.7 的 max/min=`1.059406`、绝对差=`0.6pt`，也会违反同角色 `<=1.03` 且 `<=0.25pt`。本报告不依赖这一 taxonomy 歧义作主拒绝，native 8 项失败已经决定性成立。

## 5. Low-profile scoped 证书

95 个 text/formula 的 frozen class 分布为：73 CJK_FULL、10 BASE_MATH_OPERATOR_OR_GLYPH、7 LATIN_GREEK_LOWER、2 LATIN_CAP_DIGIT、3 NATURAL_TEX_SCRIPT。实际字符集合没有 low-profile punctuation；三个 natural script 为 `i26,i26,0=24`，mask 非空、完整、纯净，且高于其门槛。因此 `peer_count=0`、`hard_count=0` 的 scoped 证书与该空集合相符；该证书不能外推替代 95 项 glyph 或本报告的 D/E 裁决。

## 6. 视觉打开、抽样与反证

### 6.1 Glyph

实际打开全部 `16/16` 张 glyph contact sheet，覆盖 95 个 glyph。除逐 sheet 全开外，明确复核的对象样本超过 40 个，包括：

`FRM_TRIAL_005`、`TXT_TRIAL_001/002`、`TXT_GAMMA_001/002/003/006/009`、`TXT_FAMILIES_001/006/007/009/011`、`FRM_POSTERIOR_FORMULA_001/003/004/005`、`TXT_POSTERIOR_001/002/007`、`FRM_PREDICTIVE_FORMULA_001/002/003/004/007/009`、`TXT_PREDICTIVE_001/006/013/015`、`TXT_SIMPLEX_001/003/005`、`TXT_MOM_001/004/009`、`TXT_LDA_001/004/008/012`、`TXT_APPLICATION_001/002`。

目标 `FRM_TRIAL_005` 的 `n` 在 ORIGINAL、红色唯一 mask overlay、mask-only 中均可见完整左竖、拱肩和右脚；没有缺笔、邻字/边框/箭头污染或空 mask。其余抽样也没有发现 note-image 矛盾、missing/foreign/clip/ownership 反例。

### 6.2 Graphic

实际打开 12/21 个 graphic 的 ORIGINAL/overlay/mask triple（contact sheet 同时含 1x 原上下文与 8x-nearest 物理放大）：

`GFX_NODE_BORDER_TRIAL`、`GFX_NODE_BORDER_FAMILIES`、`GFX_NODE_BORDER_POSTERIOR`、`GFX_NODE_BORDER_PREDICTIVE`、`GFX_LINE_TRIAL_TO_FAMILIES`、`GFX_LINE_FAMILIES_TO_POSTERIOR`、`GFX_LINE_POSTERIOR_TO_PREDICTIVE`、`GFX_LINE_PREDICTIVE_TO_LDA`、`GFX_HEAD_TRIAL_TO_FAMILIES`、`GFX_HEAD_FAMILIES_TO_POSTERIOR`、`GFX_HEAD_PREDICTIVE_TO_LDA`、`GFX_MATH_RULE_PREDICTIVE_FRACTION`。

边框、线、箭头和分数横线的 mask 均非空、对象归属清楚；未见文字/邻图形误并入 mask 或裁切。

### 6.3 Critical pair

实际同时打开下列 20/50 pair 的 `bundle_1x.png` 与 `bundle_8x_nearest.png`：

`PAIR_00102, 00103, 00773, 00774, 00893, 02286, 02287, 02288, 02289, 02290, 02291, 02294, 03281, 03340, 03341, 03342, 03343, 03345, 04345, 04385`。

样本覆盖 `ACCEPT_DESIGN` 与 `ACCEPT_CLEAR`、node/line endpoint、node/arrowhead clearance、same-parent typography、formula-rule/own-border 和 independent clearance。主动寻找 intersection、2/3 px 边界误判、所有权丢失、箭头刺框、分数线碰框及 design whitelist 泛化；样本中的红/蓝 raw mask 最终无共有像素，近邻白缝与设计端点和人工 note 一致。50 项人工账只有 15 项写 `ACCEPT_DESIGN`、35 项写 `ACCEPT_CLEAR`，未把所有 machine `DESIGN_COMPOSITION` 自动转为人工设计放行。

### 6.4 五视图与语义

实际打开：`full_page_200dpi`、`figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi`、`after_text_measurement_overlay_300dpi`，5/5 全开。另读取当前源第 21--47 行并对照视图，复核 semantic 3/3：

- 类别计数与 Gamma/Beta 归一化汇入多项/Dirichlet 先验，再到 `α+n` 共轭后验；
- 预测式为 `(α_i+n_i)/(α_0+N)`，与新增观测取指定类别文字一致；
- 阅读方向为左到右主链；simplex/MOM 是无箭头解释支路，LDA 是虚线应用去向。

整图/灰度/整页融合没有发现异常裁切、阅读方向歧义、节点文字溢出或图形所有权问题；但该整体视觉结论不能覆盖第 4 节 D/E 硬失败。

## 7. Manifest、parse、ADS 与停止写入

- 当前普通文件总数 978；manifest payload 973。
- `PACKAGE_MANIFEST.json` 973 entries、CSV 973 rows、SHA sums 973 rows，三者与实际 payload 集合、bytes、SHA-256 全部 0 差异。
- mtime 按 manifest 的微秒表示精度归一后 0 差异；与 NTFS 100ns 原值的剩余差仅 0--0.6 微秒，属于表示精度，不是 payload 变更。
- 当前独立只读解析：73 JSON、18 CSV、856 PNG，解析/verify/load 失败 0。
- 唯一 JSON decode fallback 是 `CURRENT_EXTERNAL_CHILD_STDOUT.json`；raw SHA-256=`FFBF3EB5BB693538C55BD6BCBB68FA6FDA9C8F2A28101B1349BC74BB5AFD0E98`，只对该 exact raw bytes 使用 GBK/CP936 后可复算为合法 JSON；没有第二个 fallback。
- ADS 独立枚举 0；sealed root 中没有 `.pyc` 或 `__pycache__`。
- payload 最新文件为 `ADS_CHECK_R2.json`；manifest 三文件随后生成；`TERMINAL_VALIDATION_R2.json` mtime=`2026-08-24T22:07:41.5670706Z`；`WRITE_STOPPED` mtime=`2026-08-24T22:07:41.5919276Z`，严格领先 24.857 ms；封后普通文件写入 0。

## 8. R2 finalizer 历史的严肃裁决

### 8.1 诚实保留的事实

attempt 1 的 `PARSE_CHECK.json` 原样保留，状态 `FAIL`，明确记录 UTF-8 解码 `CURRENT_EXTERNAL_CHILD_STDOUT.json` 失败。`PARSE_CHECK_R2.json` 只对上述 exact raw SHA 使用 GBK/CP936 fallback，JSON errors=0；本审计独立复算一致。因此 parse fallback 范围是闭合且诚实的。

### 8.2 未闭合的历史代码内容

attempt 1 的 `tools/package_finalizer.py` 原内容没有保留。只剩 `PHASE_IDENTITY_BEFORE_FINALIZER.json` 证明当时文件为 9,640 bytes、SHA-256=`8FAA5A2583FE6962245C43ECAEB7FA0340A329551489212E2C683F9A3C979BAD`。当前同路径是 R2 版本 10,315 bytes、SHA-256=`F20FCACEA4C52FBFC5CBDB04ACC7E11CAC8376AD749EB0953E7655E031ECDB54`，由 `PHASE_IDENTITY_BEFORE_FINALIZER_R2.json` 冻结；其声明的行为差异是 JSON UTF-8-SIG→GBK fallback 和 R2 独立 seal 文件名。

因此，本审计不能静态重建或逐行审查 attempt 1 的代码内容；这是必须保留的 provenance gap，不能写成“attempt 1 脚本已静态审计通过”。

### 8.3 该缺口是否单独足以拒收

本报告判断：**该历史源码缺失是保留意见，但在已有身份链下不单独构成对 203 项人工账的污染证据。** 理由是：

- 4 个人工账 mtime 均早于 consumer/finalizer，当前 bytes/SHA 与 consumer 前冻结完全一致；attempt 1 后没有 manual mtime/identity 变化。
- consumer、RESULT、SA2_REPORT 均在 attempt 1 前已存在并被 phase identity 冻结；当前 SHA 与 pre-finalizer 相同。
- attempt 1 的可见产物是诚实的 parse `FAIL`；R2 当前脚本不生成/改写 manual。

这只能证明受保护对象没有被 attempt 1 改写，不能证明已丢失脚本的全部源代码行为。若没有其他硬失败，root 仍应把它作为限定义的历史 provenance 保留意见交主线决定；本轮无需以它作为唯一拒绝依据，因为第 4 节存在明确、可复算的 D/E 硬失败。

## 9. 后续路由

1. 中央角色保持 `P654=SA2`；R7A sealed root 永久只读。
2. 不提交当前源码，不启动 fresh SA1/SA3，不宣称 local pass/A_LOCAL_PASS。
3. 回到 P654 SA2：必须修复或重新建立符合协议的 D/E taxonomy 与全量证据。禁止按 exact glyph 临时拆组，也禁止继续用 manual note 覆盖硬比值。
4. 若需要改业务源或构建新候选，必须等待主线单写授权和显式 TeX slot；本报告不授权 TeX。
5. 新候选完成全量 N/C、native 300 dpi、1x/8x、人工账、manifest 与 root 接受后，才可提交并等待主线候选/fresh isolated SA1；即使后续 root ACCEPT，也不能直接转 SA3 或 A_LOCAL_PASS。
