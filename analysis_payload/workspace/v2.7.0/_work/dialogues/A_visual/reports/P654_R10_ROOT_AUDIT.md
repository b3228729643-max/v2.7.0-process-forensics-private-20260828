# FIG-P654-01 R10 独立 Root 审计

## 裁决

`ROOT_REJECT_R10`

唯一决定性硬缺口是 payload 双 manifest 中的文件级 `mtime_utc` 不能与当前 sealed root 的 NTFS 100 ns 修改时间精确闭合。其余已复核的构建身份、对象与 pair 分母、像素掩膜、R8 taxonomy 重算、源码字号门和人工证据账均闭合；这些通过项不能替代文件级 mtime 身份失败。

本裁决只针对 `STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825` 是否可作为本地图源补丁的 R10 root 接受证据。它不是 `A_LOCAL_PASS` 或 `SA3` 裁决；即使后续修复并重新封存通过，仍须单文件提交、主线集成、官方新候选和 fresh SA1。

## 审计边界与独立性

- 审计前完整读取当前 Goal、`STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md` 和 `STRICT_FIGURE_EVIDENCE_SCHEMA.md`，随后读取当前 P654 图源与 R8 冻结 taxonomy policy。
- 未读取或继承旧 R7/R7A 人工结论、人工账或旧 root 报告；未把 R10 builder/consumer 的 PASS 文本当成通过证据。
- sealed root 全程只读：未 import、未执行其中任何脚本，未运行 TeX，未写源码、state、handoff，未提交。所有数值复核均由外部只读命令重新计算。
- 允许读取的 R8 policy 仅用作预先定义分类身份核对，其 SHA-256 为 `DC81B9ADEF783946FB6DC01E469469B51508EF64755B44D0506CB14F970885DE`。

## 1. Seal、ordinary/payload 与双 manifest

### 1.1 普通文件、payload、解析和污染面

- sealed root 当前普通文件数为 **1055**；payload 为 **1052** 个文件、**116,974,049 bytes**，另有 `PAYLOAD_MANIFEST.csv`、`PAYLOAD_MANIFEST.json`、`WRITE_STOPPED.json` 三个自排除 seal 控制文件。
- 双 manifest 均为 1052 条，路径集合完全相同；相对当前 root 重新逐文件核对，缺失 0、额外 0、重复路径 0、bytes 差异 0、SHA-256 差异 0。CSV/JSON 逐条字段在其共同序列化精度内相同。
- manifest 本体身份：
  - `PAYLOAD_MANIFEST.csv`: 156,573 bytes，SHA-256 `2BF8CB091E7B69D34318C7001252F5A899D5BE128F5F8B8BBE33C1C85C881370`；
  - `PAYLOAD_MANIFEST.json`: 253,617 bytes，SHA-256 `AF5D8B6A62787AC794BC3541107C3B77158DD4633353935865CB1258AE7B1D6E`；
  - `WRITE_STOPPED.json`: 1,965 bytes，SHA-256 `D3900533B167BC75449036E28992FBFEC208572E980296D57A96D5AE72CE1185`。
- 独立打开/解析：23 CSV、70 JSON（含最终 `WRITE_STOPPED.json`）、856 PNG、1 PDF，失败 0。PDF 为单页 A4、未加密、无 JavaScript。
- 对全部 1055 个普通文件枚举非默认 ADS：0；`.pyc` 0，`__pycache__`/`.pytest_cache`/`.mypy_cache`/`.ruff_cache` 0。`texcache` 的 89 个文件是显式隔离并由构建环境绑定的 TeX 缓存，不是遗漏的 Python/cache 污染。

### 1.2 mtime 硬缺口

对 manifest CSV 中 1052 个 `mtime_utc` 逐项解析为 UTC 时间，并与每个文件的 NTFS `LastWriteTimeUtc.Ticks`（100 ns）精确比较：

- **117/1052** 时间值精确相等；
- **935/1052** 时间值不相等；
- 最大绝对偏差 **600 ns**；
- **12** 项绝对偏差大于 0.5 µs；
- 若比较完整字符串，实际 7 位小数表示与 manifest 6 位小数表示为 **1052/1052 不同**。

12 个大于 0.5 µs 的路径为：

1. `contact_sheets/graphics/GFX_LINE_TRIAL_TO_FAMILIES__8x_nearest.png` (+600 ns)
2. `objects/pre_masks/TXT_MOM_009.png` (-600 ns)
3. `objects/pre_masks/TXT_POSTERIOR_006.png` (+600 ns)
4. `objects/pre_masks/TXT_TRIAL_003.png` (-600 ns)
5. `objects/raw_masks/TXT_TRIAL_003.png` (-600 ns)
6. `pairs/critical/PAIR_03281/raw_mask_A_1x.png` (+600 ns)
7. `pairs/critical/PAIR_03281/raw_mask_B_1x.png` (+600 ns)
8. `pairs/critical/PAIR_03340/pair.json` (-600 ns)
9. `pairs/critical/PAIR_04538/bundle_1x.png` (-600 ns)
10. `pairs/critical/PAIR_06343/bundle_1x.png` (+600 ns)
11. `pairs/critical/PAIR_06343/overlay_1x.png` (+600 ns)
12. `pairs/critical/PAIR_06343/pre_intersection_1x.png` (+600 ns)

根因可由 sealed root 中 `seal_r10.py` 的只读源码定位：第 30–31 行把 `st_mtime` 浮点值交给 `datetime.fromtimestamp(...).isoformat()`，只序列化到微秒；第 169–180 行仅把 CSV manifest 与 JSON manifest 相互比较，没有把 manifest mtime 回读后同 NTFS 原始时间核对。bytes 和 SHA-256 则确实回读闭合。

Goal/protocol/schema 没有定义 mtime 的允许量化精度或“按微秒 round-trip 即视为相同”的例外。schema 第 64 行只要求 manifest 终检完全一致；protocol 第 7、9、22 行要求候选身份明确，无法锁定时 FAIL；本轮审计任务又明确要求独立复核双 manifest 的 bytes、mtime、SHA。因此不能自行引入亚微秒容差，也不能以 bytes/SHA 闭合代替 mtime 精确闭合。该项单独触发 `ROOT_REJECT_R10`。

### 1.3 WRITE_STOPPED 时序

- direct LuaLaTeX 单次调用开始 `2026-08-24T23:09:08.4089195Z`，自然结束 `23:10:17.2383848Z`，exit 0；记录中无 latexmk、无重试。
- PDF mtime 为 `23:10:15.9320991Z`。人工账依次写入于 `23:24:22.9036103Z` 至 `23:28:34.1751709Z`；后续 consumer/report/manifest 在其后。
- `WRITE_STOPPED.json` 文件 mtime 为 `23:40:33.2458474Z`；其前最新普通文件是 `PAYLOAD_MANIFEST.csv`，mtime `23:40:31.7925092Z`，相差 1.4533382 s。除 `WRITE_STOPPED.json` 自身外，mtime 位于或晚于它的文件为 0。
- `CURRENT_TEX_NONE` 是构建完成后的点时观察，不是连续遥测；但 direct 结果有自然退出记录，且审计时未发现后续 root 写入。此项没有另行触发拒绝。

## 2. PDF/source/wrapper 构建绑定

- 当前图源：3,122 bytes，SHA-256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`；冻结前后记录和当前文件重算一致。
- standalone wrapper：397 bytes，SHA-256 `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`；冻结前后和当前文件一致。wrapper 只输入指定 P654 图源并抑制 standalone caption。
- 新 PDF：43,385 bytes，SHA-256 `86712CDD98EC92AF1A2D274D4E4E987E6AE8338064FD4A3339D2761737A87260`。
- `.fls` 同时记录该 wrapper、该当前图源为 INPUT，并记录 sealed root 中上述 PDF 为 OUTPUT；未发现错误源或错误 wrapper 绑定。`TEXMFVAR/TEXMFCACHE/TEXMFCONFIG` 均指向本轮 root 的隔离 `texcache`。
- PDF 是本地 standalone patch 验证产物，不是已经集成到主线的官方全书新候选；这一边界与允许的本地 R10 裁决范围一致。

## 3. 116 对象、6670 pair 与像素门

### 3.1 分母和原生渲染

- `object_manifest.csv` 有 **116** 个唯一 `ELEMENT_ID` 和 116 个唯一连续 `OBJECT_INDEX`：95 glyph（80 TEXT + 15 FORMULA）和 21 graphic（8 NODE_BORDER + 7 LINE_ARROW + 5 ARROWHEAD + 1 MATH_RULE）。
- `all_unordered_pairs.csv/json` 有 **6670 = 116×115/2** 个唯一无序 pair；独立生成全部 `i<j` 组合后，缺失 0、额外 0、自配对 0、未知对象 0，pair index 1..6670 连续。
- 原生 300 dpi 页面网格为 **2481×3508**；未做 post-render resize。figure crop 为 `[270,254,2255,959]`、1985×705；standalone crop 为 `[270,254,2255,878]`、1985×624。另有 200 dpi 整页 1654×2339。
- 实际打开整页、300 dpi figure crop、standalone、grayscale 和对象总 overlay。布局为清晰的左至右主链、两条下方解释支线和一条虚线应用支路；彩色与灰度下均可区分，未见裁切、文字压线或关系歧义。standalone 下半页的大块空白属于无题注 wrapper，不被误判为官方集成页排版通过。

### 3.2 raw/pre mask、目标 n 和全部 graphic

- 对 116 个 `raw_masks` 与 `pre_masks` 逐像素重新计算：PNG 尺寸与 page bbox 差异 0；raw 面积、pre 面积、`pre-raw=OCCLUDED_PX`、95 个 glyph 的 `H_INK_PX` 与 CSV 差异均为 0；空 mask 0。
- 95 个 glyph 全部 `EFFECTIVE_PT >= 9.5`、高度阈值失败 0；`MISSING_STROKE_PX`、`FOREIGN_PIXEL_PX`、`CLIP_PIXEL_COUNT` 总和均为 0。
- 目标 `FRM_TRIAL_005` 的 1×、8×、raw、pre 均实际打开：raw mask 为 22×22，前景 297 px，bbox 高 **22 px**，精确满足 `H_INK_PX >= 22`；字形是 trial 节点中的独立数学 `n`，无邻字污染。
- 实际打开 glyph contact sheets **16/16**，系统覆盖全部 95 个 glyph；各 sheet 的原图、红色 overlay、mask-only 三联均检查。另反证打开唯一有 1 px pre-occlusion 的 `TXT_GAMMA_002` 的 1×/8×/raw/pre；最终 raw 的 `a` 闭合，邻接字不进入 mask。
- graphic contact **21/21** 全部实际打开，覆盖 8 border、7 line、5 head、1 fraction rule。独立像素重算与 ledger 的面积/遮挡差一致；最终 mask 无空对象、无 foreign/missing/clip。

### 3.3 全 pair 与 critical 50

- 独立把 116 个 cropped raw mask 按 page bbox 重建到同一页面坐标，并重新计算全部 **6670** pair 的最终共享像素：与 CSV 的 `FINAL_RAW_INTERSECTION_PX` 差异 0，所有 pair 最终交集均为 0。
- 对全部 6670 个 CSV 最近点坐标验证：A/B 坐标确为各自前景像素，且最近点欧氏距离减 1 与 `RAW_MIN_CLEARANCE_PX` 的差异为 0。
- `manual_critical_pair_review.csv` 的 50 个 pair 与 machine critical 集合完全相同；每个目录 8 个证据文件，共 400 个文件。
- 50 个 critical 覆盖全部 11 个 relation class：5 ARROW_COMPOSITION、1 FORMULA_RULE_OWN_NODE_BORDER、4 INDEPENDENT_TEXT_TEXT、24 INTENDED_EDGE_NODE_ENDPOINT、9 MATH_RULE_COMPOSITION、1 OTHER_INDEPENDENT、1 OWN_NODE_TEXT_BORDER、1 SAME_PARENT_TYPOGRAPHY、1 TEXT_LINE_OR_ARROWHEAD、1 TEXT_MATH_RULE、2 TEXT_OTHER_NODE_BORDER。
- 实际打开 11/11 relation class 的最小净空代表 8× bundle；另打开 `PAIR_06580`、`PAIR_00102`、`PAIR_00893` 的 original/pre-intersection/overlay，分别复核箭杆—箭头组合共享像素、节点—出边预遮挡接触和相邻同父文字的 1 px 预遮挡边界。
- 各类全分母最小 raw clearance/critical 捕获：0/5（ARROW_COMPOSITION，5 个最小全捕获）、118/1、27/1、0/9（INTENDED endpoint，9 个最小全捕获）、6/2、30/1、17/1、0/1（SAME_PARENT，pre intersection 1）、27/1、71/4（4 个并列最小中捕获 1）、5/2。所有 relation class 的最终 raw intersection 最大值为 0；组合/端点的 pre-intersection 是设计接触而非最终像素碰撞。

## 4. R8 冻结 taxonomy 的独立重算

只使用当前 R10 `after_pixel_measurements.csv` 的 `PANEL_ID`、冻结 location `ROLE`、`SCRIPT_CLASS` 和 `TEXT_SAMPLE` 的预定义字符类别重新映射；分类阶段未读取 `ELEMENT_ID`、`H_INK_PX`、`INK_AREA_PX`、`PASS_FAIL` 或 measurement rank。其后才读取 H 做组内 median/ratio。

- 输入 95/唯一 95，输出 95/唯一 95，映射与 R10 taxonomy element ledger 差异 **0**。
- 得到 **10/10 非空组**：ANNOTATION/CJK 2；FORMULA/CJK 2；FORMULA/binary operator 3；FORMULA/lower variable 5；FORMULA/upper variable 1；FORMULA/natural script 3；NODE_BASE/CJK 69；NODE_BASE/Latin cap-or-ascender 3；NODE_BASE/Latin x-height 6；TRIAL_INLINE/lower variable 1。
- 组 median/ratio 与 ledger 差异 0。全局 hard range `[0.92,1.08]` 下失败 0；最紧边界是 NATURAL_TEX_SCRIPT 的 24/26 = 0.923076923077，仍高于 0.92。两个 singleton 是预定义类型的实际单例：FORMULA upper variable `FRM_PREDICTIVE_FORMULA_009` 与 TRIAL inline lower variable `FRM_TRIAL_005`，不是按 ID/H/area/PASS/rank 事后拆组。
- 已实际打开 10 组的极值/单例代表，包括 annotation CJK、formula CJK、`+`、base lower variable、uppercase `N` 单例、natural script 24/26、node CJK 34/36、Latin ascender 27/29、Latin x-height 21/22 和目标 `n` 单例；未发现污染或通过逃逸。
- 源级 same-role 独立重算：NODE_BASE 78@10.1 pt、FORMULA_BLOCK 14@11.6 pt、TRIAL_INLINE_FORMULA 1@10.7 pt、ANNOTATION 2@10.1 pt；每个角色 min=max、ratio=1。
- hierarchy 相对 10.1 pt base 的比值为 1、1.148514851485、1.059405940594、1；分别落在 source gate 的固定 1、`[1.00,1.18]`、`[1.00,1.18]`、`[0.95,1.10]` 内。当前源未用 resize/scalebox/shape transform 绕过字体门。

## 5. 八类人工账（192 行）

行数精确为 **95/21/50/5/3/10/4/4 = 192**。跨八账 `DECISION_ID` 唯一 192，glyph、graphic、critical pair、taxonomy key、same-role、hierarchy 与相应 machine denominator 的集合差均为 0；5 个 view path 全部存在。

- 所有字段空白数 0；所有 `NOTE` 非空。
- 单账和跨账的 NOTE 精确重复均为 0；对 NOTE 做小写化并去除 Unicode 标点、符号、数字、空白后的归一化重复仍为 0。
- binary `OPENED*` 字段在 glyph/graphic/critical/view 账中全部为 YES；semantic/taxonomy/source 两账的 opened evidence 字段全部为非空的具体文件、sheet/cell 或 source/view 范围。
- 所有 decision/opened/match/purity 值确实为全局 YES/PASS，所有 missing/foreign 为 0。全局布尔本身不能证明人工检查，因此本审计没有用它们作为 PASS 依据，而是按上文实际打开 16 glyph sheets、21 graphics、11 relation classes/共享边界、10 taxonomy 极值/单例和 5 views 重新裁决。
- 对 sealed root 的 4 个 Python 和 1 个 PowerShell 文件扫描，未发现任何脚本写出 `manual_*.csv`；`consumer_validator.py` 只读取八账并检查分母。八账 mtime 彼此分离，NOTE 均为元素/关系特定描述；未发现复制模板、空 note、重复 note 或脚本自动生成账目的文件内迹象。无法从静态文件密码学证明作者身份，但现有账结构没有自动生成反证。
- `MANUAL_LEDGER_IDENTITY.json` 的八项 rows/bytes/SHA 与当前账精确一致；其 7 位 mtime 与 NTFS 100 ns ticks 也 8/8 精确一致。这反过来说明 payload manifest 的 6 位 mtime 不是文件系统精度限制，而是 seal 序列化选择。

## 6. 旧 R7/R7A 迁移检查

- 未读取旧 R7/R7A 人工账或结论。当前 root 的非二进制文本中，除“不继承旧结论”的声明、R8 policy 的冻结来源标签和 manifest 路径外，唯一显著 R7A 命名产物是 `FROZEN_R7A_GROUP_RECOMPUTE.csv`。
- 只读检查当前 `build_r10_taxonomy.py` 的数据流表明：该 CSV 由**当前 R10** `after_pixel_measurements.csv` 与当前 R10 object rows 重新计算旧分组，仅作反证诊断；不是从旧 R7A 文件复制或导入。
- 当前通过 taxonomy ledger 由 R8 policy 的 global role/class 映射生成；`consumer_validator.py` 不读取 `FROZEN_R7A_GROUP_RECOMPUTE.csv`。因此该文件名本身不构成旧人工结论迁移，也不是当前 PASS 依赖。
- R8 policy 内 `measurement_input` 保留旧 `R7A machine_reuse/...` 文本标签，但当前 R10 taxonomy 脚本的实际 INPUT 明确指向当前 root 的 `after_pixel_measurements.csv`；该旧标签只作为冻结 policy provenance，不被当作 R10 测量输入。

## 最终结论与修复门

机械对象、像素、taxonomy 和人工视觉证据足以支持图源补丁内容本身；但本轮 seal 声称的文件级 mtime 身份没有精确闭合。按照本任务明确的 bytes+mtime+SHA 复核要求以及 protocol 的明确身份/不可补写原则，不能把 935 个原始时间值差异降格为容差警告。

因此最终且唯一裁决为：

`ROOT_REJECT_R10`

后续若要重新申请 root 接受，须创建全新轮次/sealed root，并用能够无损记录和回读 NTFS 100 ns mtime（或由上位协议预先明确定义的规范化精度）的 manifest 方案重新封存；不得改写本 R10 sealed root。
