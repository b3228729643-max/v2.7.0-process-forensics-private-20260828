# P654 R13 独立 Root 审计

- 审计日期：2026-08-25（Asia/Shanghai）
- assigned scope：`DIALOGUE_A_VISUAL / FIG-P654-01 / P654 / sealed R13 新增控制层与 R10 基础差分反证`
- 被审根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R13_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- R10 基础根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825`
- 报告路径：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R13_ROOT_AUDIT.md`
- 审计性质：独立、只读、差分接受；没有执行或 import R10/R11/R12/R13 任一脚本，没有运行 TeX、LuaLaTeX 或 latexmk，没有修改 sealed roots、业务源、state、inventory 或 handoff，没有读取旧 R7/R7A 人工结论，没有提交，没有发起 fresh SA1 或 SA3。

## 1. 裁决摘要

R13 已使以下门独立闭合：R10→R13 基础 1052 文件的 path/bytes/SHA-256/NTFS ticks 十进制字符串/7 位 UTC display 全零差；R13 七个新增 payload 全部进入双 manifest；双 manifest 对最终 payload 的 path/bytes/SHA/ticks/display 全零差；provenance 真实绝对根、round 与时间成立且无 `$` 占位符；copy/validator/seal 三阶段静态独立；全部 ordinary CSV/JSON/PNG/PDF 可解析；逐文件 ADS、pyc/cache、只读和封后时序门成立。基础身份成立后，内容层独立分母与系统视觉反证也没有发现新的像素、字号、对象、pair、taxonomy 或 manual 反例。

但 R13 两个终端声明文件分别有三项扩展快照与最终文件系统不一致：

| 声明文件与对象 | 扩展 | 声明 | 最终实际 | 差 |
|---|---:|---:|---:|---:|
| `R13_PRESEAL_VALIDATION.json.expected_final_payload_extensions` | json | 70 | 71 | -1 |
| `R13_PRESEAL_VALIDATION.json.expected_final_control_extensions` | json | 1 | 2 | -1 |
| `R13_PRESEAL_VALIDATION.json.expected_final_ordinary_extensions` | json | 72 | 73 | -1 |
| `WRITE_STOPPED.json.actual_payload_extensions` | json | 70 | 71 | -1 |
| `WRITE_STOPPED.json.actual_control_extensions` | json | 1 | 2 | -1 |
| `WRITE_STOPPED.json.actual_ordinary_extensions` | json | 72 | 73 | -1 |

`R13_PRESEAL_VALIDATION.json` 自身是最终 payload 的 JSON；`WRITE_STOPPED.json` 自身是最终 control 的 JSON，并且也必须进入 ordinary JSON 分母。任务明确要求三个扩展对象分别覆盖最终完整集合并逐扩展满足 `ordinary = payload + control`；命名对象不能用正确的文件总数、其他字段或 PASS 字样补救。因此该声明级硬缺口单独要求拒绝 R13。

## 2. 权威依据、独立性与权限边界

审计前完整读取：

1. `D:\Users\ASUS\.codex\attachments\255038e7-59d5-4cf5-870f-463d35db7f09\goal-objective.md`；
2. `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`；
3. `STRICT_FIGURE_EVIDENCE_SCHEMA.md`。

只把允许读取的 `P654_R10_ROOT_AUDIT.md`、`P654_R11_ROOT_AUDIT.md`、`P654_R12_ROOT_AUDIT.md` 用于定位差分门和已通过内容门；没有把旧最终结论当成本轮证据。所有关键集合、哈希、ticks、解析、ADS、只读、封存时序、内容分母和视觉样本均针对当前文件系统独立复核。

本报告只裁决 R13 是否可作为 `FIG-P654-01` 的本地 SA2 patch 证据。即使控制层正确，也只可能授权后续单源提交、主线集成、官方新候选与 fresh SA1；不等于 `A_LOCAL_PASS`，不授权 SA3，更不是全书发布结论。本轮拒绝不授权原地改写 sealed R13。

## 3. FS ordinary / payload / root controls 三套集合

### 3.1 集合与字节数

| 集合 | 文件数 | 字节数 | 独立结果 |
|---|---:|---:|---|
| payload | 1059 | 117,881,239 | PASS |
| root controls | 3 | 502,501 | PASS |
| ordinary | 1062 | 118,383,740 | `1059 + 3 = 1062`，PASS |
| 根下目录 | 71 | — | 只读枚举 |

仅根目录下以下三个文件被归为 controls；树内同名嵌套 control 为 0：

- `PAYLOAD_MANIFEST.csv`
- `PAYLOAD_MANIFEST.json`
- `WRITE_STOPPED.json`

R11/R12 新增 payload 名单在 R13 整棵树中的命中数为 0；没有把 R11/R12 identity、provenance、validator、seal 或 prevalidation 文件混入 R13。

### 3.2 最终实际扩展快照

| 扩展 | payload | control | ordinary | ordinary = payload + control |
|---|---:|---:|---:|---|
| md | 4 | 0 | 4 | PASS |
| json | 71 | 2 | 73 | PASS |
| csv | 23 | 1 | 24 | PASS |
| py | 4 | 0 | 4 | PASS |
| ps1 | 4 | 0 | 4 | PASS |
| log | 3 | 0 | 3 | PASS |
| idx | 2 | 0 | 2 | PASS |
| aux | 1 | 0 | 1 | PASS |
| fls | 1 | 0 | 1 | PASS |
| pdf | 1 | 0 | 1 | PASS |
| png | 856 | 0 | 856 | PASS |
| lua | 21 | 0 | 21 | PASS |
| luc | 44 | 0 | 44 | PASS |
| gz | 24 | 0 | 24 | PASS |
| 合计 | 1059 | 3 | 1062 | PASS |

三个最终实际集合覆盖全部扩展，没有隐藏的无扩展普通文件。实际逐扩展恒等式全部成立；失败发生在 R13 声明对象没有如实记录该实际集合。

## 4. R10→R13 基础 1052 身份与 R13 新增七文件

R10 当前 ordinary 为 1055，排除同名三个 controls 后基础 payload 为 1052。R13 copy identity CSV/JSON 各 1052 行、重复路径 0、集合缺失 0、集合额外 0；CSV↔JSON 全序列九字段差 0。对 R10 source、R13 destination 和 identity 声明逐项复算：

- relative path 差：0；
- bytes 差：0；
- SHA-256 差：0；
- `.LastWriteTimeUtc.Ticks.ToString(InvariantCulture)` 差：0；
- `yyyy-MM-ddTHH:mm:ss.fffffffZ` 七位 display 差：0；
- source/destination 缺失：0；
- identity 对实际 source/destination 的各字段差：0。

因此可在严格限定下差分接受 R10 报告已经通过的基础内容门，并仍按第 10 节作独立分母和反证抽样。

R13 相对 R10 的 payload 集合差精确为以下七项；七项在 manifest CSV 与 JSON 中均存在：

| 新增 payload | bytes | SHA-256 | ticks | 7 位 UTC display | 双 manifest |
|---|---:|---|---:|---|---|
| `R13_BASE_COPY_IDENTITY.csv` | 321512 | `D0735DC034263C5BE5503546A5A4BFB127EA2498119F4113BAE428D5BC314984` | 639232185729301125 | `2026-08-25T01:36:12.9301125Z` | YES |
| `R13_BASE_COPY_IDENTITY.json` | 576347 | `82189CD31A0B3D7E3C9A4E1823A7E64A236DB7376717E5DDDEEEB494D100DB64` | 639232185729906251 | `2026-08-25T01:36:12.9906251Z` | YES |
| `R13_copy_prepare.ps1` | 2747 | `9D117BE45E0352ECF1D61A4C183EAC98E72A19FA65CF4DB0DB74162A04422135` | 639232185506897871 | `2026-08-25T01:35:50.6897871Z` | YES |
| `R13_COPY_PROVENANCE.json` | 584 | `0D4A51E7141A2C161C11EB16516192C67FE5D23ED3643E24E250E1D4722DC9AF` | 639232185729561158 | `2026-08-25T01:36:12.9561158Z` | YES |
| `R13_PRESEAL_VALIDATION.json` | 1454 | `208A3FFE6EED31D51896C3A53FC666700EE308E4D39FFA0342178791DF41B43E` | 639232186016567778 | `2026-08-25T01:36:41.6567778Z` | YES |
| `R13_preseal_validator.ps1` | 2296 | `B63085CC8FC512F75A0E5A3D3DAB961A07E261CE18D2DBD10E88B5C7DDA9BCBF` | 639232185929589606 | `2026-08-25T01:36:32.9589606Z` | YES |
| `R13_seal.ps1` | 2250 | `A1BF34F31DEDB57D9C90913014013C92664A870BD7C58C56D663D490AE5B8D36` | 639232185513941111 | `2026-08-25T01:35:51.3941111Z` | YES |

## 5. 双 manifest 对最终 payload

| 核验项 | 独立结果 |
|---|---:|
| CSV rows / JSON rows | 1059 / 1059 |
| duplicate relative paths | 0 |
| manifest vs payload missing / extra | 0 / 0 |
| CSV↔JSON ordered-field differences | 0 |
| bytes mismatches | 0 |
| SHA-256 mismatches | 0 |
| ticks decimal-string mismatches | 0 |
| 7 位 UTC display mismatches | 0 |
| 非十进制 ticks / 非字符串 JSON ticks | 0 / 0 |
| 非七位 display | 0 |

三个 controls 的当前普通身份：

| control | bytes | SHA-256 | ticks | display |
|---|---:|---|---:|---|
| `PAYLOAD_MANIFEST.csv` | 190302 | `6058A518AAFF1ED394987AEAA94FBBAC695223DEE3E3D5AD02578F553AC2E265` | 639232186022613536 | `2026-08-25T01:36:42.2613536Z` |
| `PAYLOAD_MANIFEST.json` | 311367 | `8D3246F59A19C0CF350C3F559C902B48DF02D318448A3F094BB2AAA3507A533B` | 639232186022955744 | `2026-08-25T01:36:42.2955744Z` |
| `WRITE_STOPPED.json` | 832 | `7EC72FCF60283F2B5747BDA7DB8AF92E1CFCF2190E02CAE768E09CA52299C4D5` | 639232186034294611 | `2026-08-25T01:36:43.4294611Z` |

## 6. Resolved provenance 与三阶段静态职责

`R13_COPY_PROVENANCE.json` 独立核验：

- `source_root` 精确等于 R10 基础根的 full path；
- `target_root` 精确等于被审 R13 根的 full path；
- 两根均为绝对路径且不相等；
- `round = R13`；
- `created_at = 2026-08-25T01:36:12.9308299Z`，可按 UTC 时间解析；
- 所有字符串值中含 `$` 的项为 0；没有 `$src`、`$dst` 或其他未展开占位符。

只读静态检查三个 R13 脚本：

- `R13_copy_prepare.ps1`：固定 R10/R13 根，只复制排除三个 controls 后的 1052 基础文件，写 identity/provenance；不提及、调用或 import 其他 R13 脚本。
- `R13_preseal_validator.ps1`：只读 identity/provenance 与当时树，写自身预验报告；不提及、调用或 import copy/seal 或其他脚本。
- `R13_seal.ps1`：以 `Get-Content` 只读消费已存在的预验报告，生成双 manifest 和 `WRITE_STOPPED.json`，最后设置只读；没有改写预验报告。
- 三者 `Import-Module`、`Invoke-Expression`、TeX/LuaLaTeX/latexmk 调用均为 0。

阶段职责与不互调结构成立；静态结构正确不能覆盖下述扩展快照实现错误。

## 7. `R13_PRESEAL_VALIDATION.json` 逐字段裁决

### 7.1 文件总数字段

| 字段 | 声明 | 最终实际 | 结果 |
|---|---:|---:|---|
| `expected_final_payload_file_count` | 1059 | 1059 | PASS |
| `expected_final_manifest_control_file_count` | 2 | 2 | PASS |
| `expected_final_write_stopped_control_file_count` | 1 | 1 | PASS |
| `expected_final_control_file_count` | 3 | 3 | PASS |
| `expected_final_ordinary_file_total` | 1062 | 1062 | PASS |

预验报告自身已进入最终 payload 和双 manifest；这正是其 JSON 必须进入最终 payload 扩展快照的原因。

### 7.2 三个扩展对象

- `expected_final_payload_extensions`：除 JSON 外，全部扩展与最终 payload 相等；JSON 声明 70，实际 71，FAIL。
- `expected_final_control_extensions`：CSV 1 正确；JSON 声明 1，只覆盖 manifest JSON，漏掉 `WRITE_STOPPED.json`，实际 2，FAIL。
- `expected_final_ordinary_extensions`：除 JSON 外全部相等；JSON 声明 72，实际 73，FAIL。
- 三个声明对象各自计数求和分别为 1058、2、1061，而命名的最终文件总数分别是 1059、3、1062；各少 1。

静态根因可定位于 validator：它先从 `$payload` 排除预验报告，再从该 1058 文件集合生成 `$pe`，随后只把最终 payload 总数加 1，却没有把预验报告自身加到 `$pe.json`；`$ce` 固定为 `{csv=1;json=1}`，没有纳入 WSTOP 自身；`$oe` 从预报告集合只加 manifest CSV 和两个 JSON，仍漏掉预验报告 JSON。禁止用正确总数替代三个对象的逐项真实性。

## 8. `WRITE_STOPPED.json` 逐字段裁决

### 8.1 文件总数字段

| 字段 | 声明 | 最终实际 | 结果 |
|---|---:|---:|---|
| `payload_file_count` | 1059 | 1059 | PASS |
| `manifest_control_file_count` | 2 | 2 | PASS |
| `write_stopped_control_file_count` | 1 | 1 | PASS |
| `control_file_count` | 3 | 3 | PASS |
| `ordinary_file_total` | 1062 | 1062 | PASS |

### 8.2 三个 actual 扩展对象

- `actual_payload_extensions.json = 70`，最终 payload JSON 为 71，FAIL；
- `actual_control_extensions.json = 1`，最终 control JSON 为 2，FAIL；
- `actual_ordinary_extensions.json = 72`，最终 ordinary JSON 为 73，FAIL；
- 其他 13 个扩展均与相应最终集合一致；
- 三个 actual 对象计数和分别为 1058、2、1061，各比同文件的相应总数少 1。

seal 直接把预验报告的三个错误对象复制为 `actual_*`，没有从最终 FS 重新生成。尤其 `WRITE_STOPPED.json` 自身既明确声明为 1 个 control，又没有进入 `actual_control_extensions.json` 或 `actual_ordinary_extensions.json`，构成同一终端文件内部的可证矛盾。

## 9. 全解析、ADS、卫生、只读和封存时序

### 9.1 全部 ordinary 可解析类型

- JSON：73/73 解析成功，错误 0；解析时保留日期字符串，避免类型自动转换造成伪差。
- CSV：24/24 解析成功，错误 0。
- PNG：856/856 用 `System.Drawing.Image.FromFile` 实际解码成功，错误 0，共 271 种原生尺寸。
- PDF：1/1 同时通过 `pdfinfo` 与 PyMuPDF 打开；实际 43,385 bytes、PDF 1.7、1 页、未加密、A4 `595.276 × 841.890 pt`、JavaScript=no。PDF SHA-256 与冻结 R10 内容身份一致。

### 9.2 ADS 方法与结果

对 1062 个 ordinary 文件逐一执行等价只读 NTFS 枚举：

```powershell
Get-Item -LiteralPath <每个普通文件绝对路径> -Stream *
```

1062/1062 文件枚举成功，共返回 1062 条 stream 记录；只把 stream name 不等于 `:$DATA` 的项计为 ADS。非默认 ADS 为 0，枚举错误为 0。没有把未运行或仅枚举根目录写成 PASS。

### 9.3 其他卫生与时序

- `.pyc` 与 `__pycache__/.pytest_cache/.mypy_cache/.ruff_cache`：0。
- 1062/1062 ordinary 均为只读；非只读文件 0。
- `WRITE_STOPPED.json` mtime 为 `2026-08-25T01:36:43.4294611Z`（ticks `639232186034294611`），严格唯一最新。
- 第二最新是 `PAYLOAD_MANIFEST.json`，mtime `2026-08-25T01:36:42.2955744Z`；WSTOP 晚 1.1338867 秒。
- 除 WSTOP 自身外，mtime 大于等于 WSTOP 的文件为 0。
- `sealed_at = 2026-08-25T01:36:43.4282194Z`；除 WSTOP 自身外，晚于 `sealed_at` 的文件为 0。

解析、ADS、只读和封后 0 写均成立，但不修复扩展快照声明错误。

## 10. 基础内容层独立分母与系统反证

在 1052 基础文件身份完全闭合后，没有重跑完整 N/C；以下为当前 R13 文件的独立分母和系统性代表/极端项反证。

### 10.1 独立分母

- `object_manifest.csv`：116 行、116 唯一 ID、index 1..116；95 glyph（80 TEXT + 15 FORMULA）和 21 graphic（8 NODE_BORDER + 7 LINE_ARROW + 5 ARROWHEAD + 1 MATH_RULE）。raw/pre mask 缺失 0，machine FAIL 0。
- `after_pixel_measurements.csv`：95 行、95 唯一 glyph，与 object manifest glyph 集合差 0；effective pt `<9.5` 为 0，H 低于对应 threshold 为 0，missing/foreign 合计均 0，非 PASS 0。
- `all_unordered_pairs.csv`：6670 行，精确等于 `116×115/2`；唯一 pair ID 6670、唯一对象对 6670、预期组合缺失/额外 0、未知对象 0、索引顺序错误 0、final raw intersection 非零 0、非 PASS 0。
- `after_overlap_report.csv`：6019 行、唯一 6019。相对全 pair 排除 651，精确由 intended endpoint 15、math-rule composition 9、other-independent 180、same-parent typography 447 组成；排除项 final intersection 非零 0。
- critical：50 对、50 个目录、每目录 8 文件，共 400 文件；覆盖全部 11 relation classes。
- taxonomy：95 行、唯一 95，与 glyph 集合差 0；10 个非空组，成员计数和 95，失败 0。
- manual 八账：`95+21+50+5+3+10+4+4=192`；全局 `DECISION_ID` 唯一 192，空 NOTE 0，精确 NOTE 重复 0，去 Unicode 标点/符号/数字/空白后的归一化 NOTE 重复 0；glyph/graphic/critical 集合差均为 0；五个 view path 全存在；`MANUAL_LEDGER_IDENTITY.json` 对八账 rows/bytes/SHA/七位 mtime 差 0。
- 对当前根 4 个 Python 与 4 个 PowerShell 文本扫描，八个 manual 文件名只出现在 `consumer_validator.py` 的读取/验证清单，未发现生产或改写八账的脚本反例。此项只证明“未发现静态自动生成反证”，不声称对作者身份作密码学证明。

### 10.2 PDF、五视图与 target `n`

实际打开五视图：

| 视图 | 原生尺寸 | 独立观察 |
|---|---:|---|
| `full_page_200dpi.png` | 1654×2339 | 图位于 standalone A4 上部，未见裁切或碰撞；下部大块留白属于无题注 wrapper，不冒充官方集成页通过。 |
| `figure_crop_300dpi.png` | 1985×705 | 左至右主链、两条下方解释支线和虚线应用支路清楚；边端点、标签、公式未见遮挡。 |
| `standalone_300dpi.png` | 1985×624 | 与 crop 同一候选内容，边界紧而未裁切。 |
| `grayscale_300dpi.png` | 1985×705 | 主链、辅助线、虚线应用边和节点层级在灰度下仍可区分。 |
| `after_text_measurement_overlay_300dpi.png` | 1985×705 | 95 glyph 与 21 graphics 编号覆盖可追溯，未见明显漏标或跨对象 bbox 替代。 |

目标 `FRM_TRIAL_005` 是 trial 节点内独立粗斜体数学 `n`：declared/effective `10.7/10.7 pt`，threshold 22，`H_INK_PX=22`，ink area 297，missing/foreign/clip 均 0。独立打开 1× original/overlay/mask 三联，并逐像素计数 raw/pre 两张 22×22 mask，非黑前景均为 297，raw=pre；stem、arch 和 terminal curl 完整，未见邻字、边框或箭线污染。

### 10.3 glyph、graphic 与 taxonomy 极端代表

实际打开 glyph sheets 001、002、003、006、008、010、011、012、016，覆盖：

- target `FRM_TRIAL_005`：H=22，trial inline singleton；
- binary operator `+`：H=29；
- natural script 最小 `FRM_PREDICTIVE_FORMULA_007`（0）：H=24，组 median 26，ratio `0.923076923077`，仍高于 0.92；
- natural script 代表 `i`：H=26；
- upper variable singleton `N`：H=33；
- node CJK 最小 `TXT_LDA_010`：H=34，最大 `TXT_PREDICTIVE_009`：H=36；
- Latin ascender 最小 `t`：H=27，最大 `G`：H=29；
- Latin x-height 最小 `m`：H=21，代表 `a`：H=22；
- annotation `应`：H=35。

三联图中 target overlay 均落在对应唯一字形，mask-only 未见明显邻字/曲线/边框污染或缺笔。另实际打开四类 graphic 代表：预测公式分数横线、LDA 节点边框、trial 箭杆、trial 箭头；各自 original/target overlay/mask-only 对象边界清楚，分数规则没有被误并入文字，线杆与箭头保持独立对象。

### 10.4 11 类 critical 反证样本

每类各实际打开一个 `bundle_8x_nearest.png`，同时核对相应 `pair.json` 与对象特异 manual note：

| relation class | pair | final / pre intersection | raw clearance / required | 观察 |
|---|---|---:|---:|---|
| ARROW_COMPOSITION | `PAIR_06580` | 0 / 24 | 0 / N/A | 24 px 是同一箭边 shaft→head 的设计性 pre 联结；最终对象分离。 |
| FORMULA_RULE_OWN_NODE_BORDER | `PAIR_04345` | 0 / 0 | 118 / 5 | 分数横线位于预测框内部，远离边框。 |
| INDEPENDENT_TEXT_TEXT | `PAIR_04538` | 0 / 0 | 27 / 4 | 不同文字行间无接触；记录的 vector bbox gap 为 8。 |
| INTENDED_EDGE_NODE_ENDPOINT | `PAIR_00102` | 0 / 10 | 0 / N/A | pre 接触是 trial 右边框的出边端点，无文字参与。 |
| MATH_RULE_COMPOSITION | `PAIR_04478` | 0 / 0 | 6 / N/A | 自然下标与同父分数线分离、可辨。 |
| OTHER_INDEPENDENT | `PAIR_03281` | 0 / 0 | 30 / N/A | posterior/predictive 两大节点边框独立。 |
| OWN_NODE_TEXT_BORDER | `PAIR_06331` | 0 / 0 | 17 / 5 | LDA 末字到自有边框净空充足。 |
| SAME_PARENT_TYPOGRAPHY | `PAIR_00893` | 0 / 1 | 0 / N/A | 1 px pre 位于 Gamma 内 a/m 字距接缝；最终两 glyph 完整。 |
| TEXT_LINE_OR_ARROWHEAD | `PAIR_06668` | 0 / 0 | 27 / 3 | application 箭头与 `应` 分离。 |
| TEXT_MATH_RULE | `PAIR_05245` | 0 / 0 | 71 / 3 | 文本与分数横线远离。 |
| TEXT_OTHER_NODE_BORDER | `PAIR_06344` | 0 / 0 | 5 / 3 | `应` 到另一 LDA 边框达到门槛以上。 |

所有 11 个抽样 bundle 的原图、A/B mask、intersection 与 overlay 未显示 ledger/机器度量以外的真实碰撞或裁切反例。

### 10.5 manual 对象特异性

除全量重复检查外，实际核对 12 个 glyph note 与 11 个 critical note：target `n` 描述 stem/arch/curl；`G` 描述 open bowl 与 horizontal spur；`a` 描述 closed counter；`m` 描述 two arches；`t` 描述 stem/crossbar/curl；`+` 描述双向笔画；natural zero 描述 closed oval 并排除 alpha/fraction；`N` 描述双竖与对角线；CJK `观/与/应` 分别描述其特有部件。critical notes 分别引用 24/10/1 px 设计接缝、118/27/30/17/71/5 px 净空及具体对象。没有观察到用统一模板替换对象身份或用全局 PASS 代替逐对象描述的反证。

内容层反证结论：没有发现新失败；这不覆盖控制声明硬缺口，也不把 standalone 页冒充主线官方候选。

## 11. 硬缺口、修复门与最终权限

本轮硬缺口是两个终端声明文件的三个扩展对象均漏计最终 JSON 自身：预验报告漏进 payload 快照，WSTOP 漏进 control 快照，两者共同使 ordinary 快照也少 1。任务明确禁止用总数或其他字段补救单项错误，且 `WRITE_STOPPED` 的 actual 对象必须逐项与最终 FS 一致；因此即使其余身份、manifest、解析、ADS、封存和内容反证全部闭合，也不能签发本地 root 接受。

若另行申请新轮次，必须创建全新 sealed root：预验阶段把预验报告自身作为最终 payload JSON 纳入，control 快照必须是 `{csv:1,json:2}`，ordinary JSON 必须由最终 payload 71 加 control 2 得到 73；seal 必须从最终 FS 或语义等价的完整最终集合生成并复核三个对象。不得原地修补 R13。

本裁决不授权 `A_LOCAL_PASS`、SA3、提交、主线集成、官方候选或 fresh SA1。

`ROOT_REJECT_R13`
